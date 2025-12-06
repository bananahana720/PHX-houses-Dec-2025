"""PhoenixMLS Search extractor using nodriver stealth browser.

Extracts property data from phoenixmlssearch.com via Simple Search.
Uses stealth browser automation to navigate search form and extract
listing metadata + images from SparkPlatform CDN.

Key Features:
- Simple Search form navigation
- Address-to-listing matching
- MLS# discovery and persistence
- Kill-switch field extraction
- SparkPlatform CDN image URL transformation
- Full gallery modal extraction (all 43+ photos, not just visible thumbnails)
- Dual extraction strategy: JavaScript DOM query + HTML parsing

Architecture:
- Extends StealthBrowserExtractor for WAF bypass
- Uses nodriver stealth browser to avoid detection
- Opens photo gallery modal to load all images dynamically
- Combines JavaScript-based and HTML-based extraction for completeness
- Returns (urls, metadata) tuple for orchestrator integration

Image Extraction Strategy:
1. Navigate to listing detail page via direct URL
2. Click gallery/photo element to open full photo modal
3. Wait for lazy-loaded images to render
4. Extract via JavaScript (dynamic DOM) + BeautifulSoup (static HTML)
5. Deduplicate and transform thumbnail URLs to full-size (-o.jpg)
"""

import asyncio
import logging
import random
import re
from typing import Any

import httpx
import nodriver as uc
from bs4 import BeautifulSoup

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from .stealth_base import StealthBrowserExtractor

logger = logging.getLogger(__name__)


class PhoenixMLSSearchExtractor(StealthBrowserExtractor):
    """Extract property data from phoenixmlssearch.com via Simple Search.

    Uses nodriver stealth browser to:
    1. Navigate to Simple Search page
    2. Search by property address
    3. Parse results to find matching listing
    4. Extract metadata (kill-switch fields) and images
    5. Store MLS# for future direct access

    Attributes:
        SITE_URL: Base URL for phoenixmlssearch.com
        SIMPLE_SEARCH_PATH: Path to Simple Search form
        SEARCH_DELAY_MIN: Minimum delay between search operations (seconds)
        SEARCH_DELAY_MAX: Maximum delay between search operations (seconds)
        RESULT_WAIT_SECONDS: Time to wait for search results to load
        CDN_DELAY_MIN: Minimum delay between CDN image downloads
        CDN_DELAY_MAX: Maximum delay between CDN image downloads
    """

    # Site URLs
    SITE_URL = "https://phoenixmlssearch.com"
    SIMPLE_SEARCH_PATH = "/simple-search/"

    # Rate limiting constants (optimized based on real-world testing)
    SEARCH_DELAY_MIN: float = 0.3
    SEARCH_DELAY_MAX: float = 0.5
    RESULT_WAIT_SECONDS: float = 1.0
    CDN_DELAY_MIN: float = 0.5
    CDN_DELAY_MAX: float = 1.0

    # Compiled regex patterns (avoid recompilation)
    # Multiple MLS patterns to handle format variations:
    # - "Address / 6937912 (MLS #)" - standard format
    # - "Address / 6937912 (MLS#)" - no space before hash
    # - "Address #6937912" - hash prefix only
    # - "MLS# 6937912" - MLS prefix with number
    MLS_PATTERNS = [
        re.compile(r"/\s*(\d{7})\s*\(MLS\s*#?\)", re.IGNORECASE),  # Primary: / 6937912 (MLS #)
        re.compile(r"#\s*(\d{7})", re.IGNORECASE),                  # Fallback: #6937912
        re.compile(r"MLS\s*#?\s*(\d{7})", re.IGNORECASE),          # Fallback: MLS 6937912
        re.compile(r"(\d{7})\s*\(MLS", re.IGNORECASE),             # Fallback: 6937912 (MLS
    ]
    # Keep MLS_PATTERN for backward compatibility
    MLS_PATTERN = MLS_PATTERNS[0]
    ADDRESS_PATTERN = re.compile(r"^(.+?)\s*/\s*\d{7}")
    HOA_PATTERN = re.compile(r"Association Fee Incl[:\s]*(.+?)(?:\n|$)", re.IGNORECASE)
    BEDS_PATTERN = re.compile(r"#\s*Bedrooms[:\s]*(\d+)", re.IGNORECASE)
    BATHS_PATTERN = re.compile(r"Full\s*Bathrooms[:\s]*([\d.]+)", re.IGNORECASE)
    SQFT_PATTERN = re.compile(r"Approx\s*SQFT[:\s]*([\d,]+)", re.IGNORECASE)
    LOT_SQFT_PATTERN = re.compile(r"Approx\s*Lot\s*SqFt[:\s]*([\d,]+)", re.IGNORECASE)
    ACRES_PATTERN = re.compile(r"Lot\s*Size[:\s]*([\d.]+)\s*[Aa]cres?")
    GARAGE_PATTERN = re.compile(r"Garage\s*Spaces[:\s]*(\d+)", re.IGNORECASE)
    SEWER_PATTERN = re.compile(r"Sewer[:\s]*(.+?)(?:\n|$)", re.IGNORECASE)
    YEAR_PATTERN = re.compile(r"Year\s*Built[:\s]*(\d{4})", re.IGNORECASE)
    STREET_NUM_PATTERN = re.compile(r"(\d+)")

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize PhoenixMLS Search extractor.

        Args:
            http_client: Shared httpx client (maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction config (loaded from env if not provided)
        """
        super().__init__(http_client=http_client, timeout=timeout, config=config)

        # Store metadata for orchestrator retrieval
        self.last_metadata: dict = {}

        # Lock to protect metadata writes (ISSUE 1 FIX - race condition)
        self._metadata_lock = asyncio.Lock()

        # Current property being processed (set in extract_image_urls)
        self._current_property: Property | None = None

        logger.info(
            "%s initialized for Simple Search extraction",
            self.name,
        )

    @property
    def source(self) -> ImageSource:
        """Image source identifier."""
        return ImageSource.PHOENIX_MLS_SEARCH

    def can_handle(self, property: Property) -> bool:
        """Check if extractor can handle this property.

        Args:
            property: Property to check

        Returns:
            True if property is in Phoenix metro area
        """
        # Import PHOENIX_METRO_CITIES from phoenix_mls module
        from .phoenix_mls import PHOENIX_METRO_CITIES

        city_normalized = property.city.lower().strip()
        return city_normalized in PHOENIX_METRO_CITIES

    def _build_search_url(self, property: Property) -> str:
        """Build PhoenixMLS Simple Search URL.

        Args:
            property: Property to build URL for

        Returns:
            Simple Search page URL
        """
        return f"{self.SITE_URL}{self.SIMPLE_SEARCH_PATH}"

    async def _rate_limit_search(self) -> None:
        """Apply rate limiting delay between search operations."""
        delay = random.uniform(self.SEARCH_DELAY_MIN, self.SEARCH_DELAY_MAX)
        logger.debug("%s rate limit delay: %.2fs", self.name, delay)
        await asyncio.sleep(delay)

    async def _navigate_to_simple_search(self, tab: uc.Tab) -> bool:
        """Navigate to Simple Search page.

        Args:
            tab: Browser tab

        Returns:
            True if navigation succeeded
        """
        try:
            search_url = f"{self.SITE_URL}{self.SIMPLE_SEARCH_PATH}"
            logger.info("%s navigating to: %s", self.name, search_url)
            await tab.get(search_url)
            await self._human_delay()
            return True
        except Exception as e:
            logger.error("%s navigation failed: %s", self.name, e)
            return False

    async def _search_for_property(self, tab: uc.Tab, property: Property) -> bool:
        """Fill search form and extract MLS# to navigate directly to listing.

        CRITICAL FIX (2025-12-06): PhoenixMLS Search button shows ALL listings
        instead of filtering to the autocomplete selection. The autocomplete text
        contains both address and MLS#, so we extract them and construct the direct
        listing URL instead of using the broken search results page.

        Autocomplete text format:
            "5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)"
            Address: everything before " / "
            MLS#: 7-digit number before "(MLS #)"

        Direct URL format:
            /mls/{address-slug}-mls_{mls_number}
            Example: /mls/5219-W-EL-CAMINITO-Drive-Glendale-AZ-85302-mls_6937912

        NEW Workflow:
        1. Find and focus search input (combobox)
        2. Type address character-by-character
        3. Wait for autocomplete dropdown to appear
        4. Find best matching autocomplete suggestion
        5. Extract MLS# and address from autocomplete text
        6. Construct direct listing URL and navigate (skip search results entirely)

        Args:
            tab: Browser tab with Simple Search page loaded
            property: Property to search for

        Returns:
            True if MLS# was extracted and direct navigation succeeded
        """
        # Timeout constants for element selection
        OPERATION_TIMEOUT = 5.0  # seconds for selector waits
        AUTOCOMPLETE_WAIT_SECONDS = 1.0  # Wait for dropdown to appear (optimized from 2.0)

        try:
            # Build search query: "123 Main St, Phoenix, AZ 85001"
            search_query = (
                f"{property.street}, {property.city}, {property.state} {property.zip_code}"
            )

            logger.debug("%s searching for: %s", self.name, search_query)

            # Step 1: Find location input (combobox with autocomplete)
            # OPTIMIZED: Reduced from 5 to 2 selectors (Strategies 2-5 never triggered)
            # Tested via Playwright on phoenixmlssearch.com/simple-search/
            # Confirmed: textbox has placeholder "Enter an Address, City, Zip or MLS#"
            input_selectors = [
                "input[placeholder*='Address' i]",  # Primary: matches "Enter an Address, City, Zip or MLS#"
                "input[type='text']",  # Fallback: generic text input
            ]

            input_element = None
            for selector in input_selectors:
                try:

                    # Wrap tab.select() with timeout protection
                    input_element = await asyncio.wait_for(
                        tab.select(selector), timeout=OPERATION_TIMEOUT
                    )

                    if input_element:
                        logger.debug("%s found input with selector: %s", self.name, selector)
                        break

                except asyncio.TimeoutError:
                    logger.debug("%s selector timeout: %s", self.name, selector)
                    continue
                except Exception as e:
                    logger.debug("%s selector failed: %s - %s", self.name, selector, e)
                    continue

            if not input_element:
                logger.warning(
                    "%s could not find search input after trying %d selectors",
                    self.name,
                    len(input_selectors),
                )
                return False

            # Step 2: Clear and type address
            logger.debug("%s clearing input and typing address", self.name)
            await asyncio.wait_for(input_element.clear_input(), timeout=5.0)
            await self._human_delay()

            # Type address with human-like speed
            for char in search_query:
                await input_element.send_keys(char)
                await asyncio.sleep(random.uniform(0.01, 0.03))

            logger.debug("%s typed address, waiting for autocomplete dropdown", self.name)
            await asyncio.sleep(AUTOCOMPLETE_WAIT_SECONDS)

            # Step 3: Wait for and find autocomplete suggestions
            # The dropdown appears as a list of <li> or <div> elements with address text
            logger.info("%s waiting for autocomplete dropdown to appear", self.name)

            # CRITICAL: Maximum total time to spend searching for autocomplete
            AUTOCOMPLETE_MAX_TOTAL_SECONDS = 10.0
            autocomplete_start_time = asyncio.get_event_loop().time()

            autocomplete_found = False
            autocomplete_selectors = [
                # OPTIMIZED: Reduced from 7 to 2 primary selectors
                # Strategies 3-7 rarely triggered; batch JS extraction (Strategy 0) is most reliable
                "[role='tree'] [role='treeitem']",  # ARIA tree with treeitem (PhoenixMLS primary)
                "[role='treeitem']",  # ARIA treeitem (fallback)
            ]

            max_attempts = 2  # Reduced from 3 to 2 attempts

            for attempt in range(max_attempts):
                # Check if we've exceeded total timeout
                elapsed = asyncio.get_event_loop().time() - autocomplete_start_time
                if elapsed > AUTOCOMPLETE_MAX_TOTAL_SECONDS:
                    logger.warning(
                        "%s autocomplete timeout after %.1fs, falling back to Enter",
                        self.name,
                        elapsed,
                    )
                    break

                logger.debug(
                    "%s autocomplete detection attempt %d/%d (%.1fs elapsed)",
                    self.name,
                    attempt + 1,
                    max_attempts,
                    elapsed,
                )

                for selector in autocomplete_selectors:
                    # Check timeout before each selector attempt
                    if (
                        asyncio.get_event_loop().time() - autocomplete_start_time
                        > AUTOCOMPLETE_MAX_TOTAL_SECONDS
                    ):
                        logger.warning(
                            "%s autocomplete timeout, stopping selector search", self.name
                        )
                        break

                    try:
                        # CRITICAL: Wrap select_all() with timeout to prevent WebSocket hangs
                        results = await asyncio.wait_for(
                            tab.select_all(selector), timeout=OPERATION_TIMEOUT
                        )
                        if results and len(results) > 0:
                            logger.info(
                                "%s found %d autocomplete suggestions with selector: %s",
                                self.name,
                                len(results),
                                selector,
                            )

                            # Find best matching result
                            best_score = 0.0
                            best_match_text_from_js = ""

                            logger.debug(
                                "%s processing %d autocomplete results for query: %s",
                                self.name,
                                len(results),
                                search_query,
                            )

                            # STRATEGY 0 (2025-12-06): HTML parsing from DOM snapshot instead of tab.evaluate()
                            # Using BeautifulSoup on tab.get_content() is more reliable than tab.evaluate() with nodriver
                            try:
                                # Get current page HTML content
                                page_html = await asyncio.wait_for(
                                    tab.get_content(),
                                    timeout=OPERATION_TIMEOUT,
                                )

                                if page_html:
                                    # Parse HTML to find all treeitem elements
                                    soup = BeautifulSoup(str(page_html), "html.parser")
                                    treeitem_elements = soup.select('[role="treeitem"]')

                                    if treeitem_elements:
                                        all_texts = []
                                        for el in treeitem_elements:
                                            # Try innerText equivalent: get_text()
                                            text = el.get_text(strip=True)
                                            if text:
                                                all_texts.append(text)

                                        logger.info(
                                            "%s found %d treeitem elements via HTML parsing: %r",
                                            self.name,
                                            len(all_texts),
                                            all_texts[:3],  # Show first 3 items
                                        )

                                        # Process texts for matching
                                        for idx, text in enumerate(all_texts):
                                            if not text:
                                                continue
                                            score = self._score_autocomplete_match(search_query, text)
                                            logger.debug(
                                                "%s HTML result %d scored %.2f: %s",
                                                self.name,
                                                idx + 1,
                                                score,
                                                text[:80],
                                            )
                                            if score > best_score:
                                                best_score = score
                                                best_match_text_from_js = text

                                        if best_match_text_from_js and best_score >= 0.5:
                                            # We have the text, now extract MLS# and navigate directly
                                            logger.info(
                                                "%s using HTML text with score %.2f",
                                                self.name,
                                                best_score,
                                            )
                                            autocomplete_found = True

                                            # Extract MLS# from the text (try all patterns)
                                            mls_number = None
                                            for pattern in self.MLS_PATTERNS:
                                                mls_match = pattern.search(best_match_text_from_js)
                                                if mls_match:
                                                    mls_number = mls_match.group(1)
                                                    logger.info(
                                                        "%s extracted MLS# %s using pattern: %s",
                                                        self.name,
                                                        mls_number,
                                                        pattern.pattern,
                                                    )
                                                    break

                                            if mls_number:
                                                logger.info(
                                                    "%s extracted MLS#: %s from HTML parsing",
                                                    self.name,
                                                    mls_number,
                                                )

                                                # Extract address from autocomplete text
                                                address_match = self.ADDRESS_PATTERN.match(best_match_text_from_js)
                                                if address_match:
                                                    autocomplete_address = address_match.group(
                                                        1
                                                    ).strip()
                                                    logger.info(
                                                        "%s extracted address: %s",
                                                        self.name,
                                                        autocomplete_address,
                                                    )

                                                    # Construct direct listing URL
                                                    address_slug = autocomplete_address.replace(
                                                        ",", ""
                                                    ).replace(" ", "-")
                                                    direct_url = f"{self.SITE_URL}/mls/{address_slug}-mls_{mls_number}/"

                                                    logger.info(
                                                        "%s navigating directly to listing: %s",
                                                        self.name,
                                                        direct_url,
                                                    )

                                                    # Navigate directly to listing page
                                                    await tab.get(direct_url)
                                                    await self._rate_limit_search()
                                                    await asyncio.sleep(self.RESULT_WAIT_SECONDS * 1.5)

                                                    # Verify navigation succeeded
                                                    current_url = (
                                                        str(tab.target.url)
                                                        if hasattr(tab, "target")
                                                        else ""
                                                    )
                                                    if (
                                                        "/mls/" in current_url
                                                        and "-mls_" in current_url
                                                    ):
                                                        # Verify it's actually a listing page (not 404)
                                                        page_html_detail = await tab.get_content()
                                                        if page_html_detail and (
                                                            "cdn.photos.sparkplatform.com" in page_html_detail
                                                            or "listing" in page_html_detail.lower()
                                                        ):
                                                            logger.info(
                                                                "%s SUCCESS - valid listing page loaded",
                                                                self.name,
                                                            )
                                                            return True
                                                        else:
                                                            logger.warning(
                                                                "%s URL worked but page appears to be 404 or error page",
                                                                self.name,
                                                            )
                                                            # Don't return True - fall through to fail

                                            # If HTML found text but couldn't extract MLS#, log failure details
                                            if not mls_number:
                                                logger.error(
                                                    "%s MLS# extraction FAILED for text: %r (tried %d patterns)",
                                                    self.name,
                                                    best_match_text_from_js[:100],
                                                    len(self.MLS_PATTERNS),
                                                )
                                            logger.warning(
                                                "%s HTML text found but MLS# extraction failed",
                                                self.name,
                                            )
                                            autocomplete_found = False
                                    else:
                                        logger.warning(
                                            "%s no treeitem elements found in HTML via selector [role='treeitem']",
                                            self.name,
                                        )
                                else:
                                    logger.warning("%s get_content() returned empty/None", self.name)

                            except asyncio.TimeoutError:
                                logger.warning(
                                    "%s HTML parsing timed out after %.1fs",
                                    self.name,
                                    OPERATION_TIMEOUT,
                                )
                            except Exception as e:
                                logger.warning(
                                    "%s HTML parsing failed: %s (type=%s)",
                                    self.name,
                                    e,
                                    type(e).__name__,
                                )

                            # REMOVED (2025-12-06): Element-by-element fallback was complex and unreliable
                            # Batch JS extraction (Strategy 0 above) handles all real-world cases

                    except asyncio.TimeoutError:
                        logger.debug(
                            "%s timeout selecting autocomplete with selector: %s",
                            self.name,
                            selector,
                        )
                        continue
                    except Exception as e:
                        logger.debug("%s selector %s failed: %s", self.name, selector, e)
                        continue

                if autocomplete_found:
                    break

                # Wait before retrying (only if not at last attempt)
                if attempt < max_attempts - 1:
                    remaining_time = AUTOCOMPLETE_MAX_TOTAL_SECONDS - (
                        asyncio.get_event_loop().time() - autocomplete_start_time
                    )
                    if remaining_time > 1.0:
                        await asyncio.sleep(1.0)
                    else:
                        logger.debug("%s skipping retry wait, timeout approaching", self.name)
                        break

            # Step 4: If no autocomplete found or MLS# extraction failed, return failure
            if not autocomplete_found:
                logger.error(
                    "%s autocomplete search failed - no MLS# found to construct direct URL",
                    self.name,
                )
                return False

            # If we got here, autocomplete was found but direct navigation failed
            # (The successful path returns True early at line 602)
            logger.error("%s autocomplete found but direct navigation failed", self.name)
            return False

        except asyncio.TimeoutError:
            logger.error("%s search form interaction timeout", self.name)
            return False
        except Exception as e:
            logger.error("%s search form interaction failed: %s", self.name, e)
            return False


    def _addresses_match(self, card_text: str, property: Property) -> bool:
        """Check if card text contains property address.

        Args:
            card_text: Text content from listing card
            property: Property to match

        Returns:
            True if addresses match
        """
        card_lower = card_text.lower()
        street_lower = property.street.lower()

        # Simple substring match
        if street_lower in card_lower:
            return True

        # Try numeric match (e.g., "123" from "123 Main St")
        street_num = re.match(r"(\d+)", property.street)
        if street_num and street_num.group(1) in card_lower:
            return True

        return False

    def _score_autocomplete_match(self, query: str, option_text: str) -> float:
        """Score autocomplete option for match quality.

        Scoring considers:
        - MLS# listing format (highest priority): "ADDRESS / MLS_NUMBER (MLS #)"
        - Exact substring matches
        - Street number matches
        - Partial address matches
        - Case-insensitive matching

        Args:
            query: Original search query (e.g., "123 Main St, Phoenix, AZ 85001")
            option_text: Autocomplete suggestion text

        Returns:
            Score from 0.0 to 1.0 (1.0 = exact match)
        """
        if not option_text:
            return 0.0

        query_lower = query.lower()
        option_lower = option_text.lower()

        # Exact match (highest score)
        if query_lower == option_lower:
            return 1.0

        # Prefer options with "(MLS #)" pattern (specific listings)
        # Format: "4560 E SUNRISE Drive, Phoenix, AZ 85044 / 6948863 (MLS #)"
        has_mls_pattern = "(mls #)" in option_lower or "/ " in option_lower

        # Substring match with MLS bonus
        if query_lower in option_lower or option_lower in query_lower:
            return 0.95 if has_mls_pattern else 0.8

        # Try to extract street number and match
        street_num = self.STREET_NUM_PATTERN.match(query)
        if street_num and street_num.group(1) in option_lower:
            # Check if major address components are present
            query_parts = query_lower.split(",")
            if any(part.strip() in option_lower for part in query_parts[:2]):
                return 0.85 if has_mls_pattern else 0.7

        # Partial component match
        query_parts_set = set(query_lower.split())
        option_parts_set = set(option_lower.split())
        if query_parts_set and option_parts_set:
            overlap = len(query_parts_set & option_parts_set)
            score = min(overlap / len(query_parts_set), 0.6)
            if score > 0:
                # Boost score if has MLS pattern
                return min(score + 0.15, 0.75) if has_mls_pattern else score

        return 0.0

    async def _navigate_to_detail_page(self, tab: uc.Tab, listing_url: str) -> str:
        """Navigate to listing detail page and return HTML.

        Args:
            tab: Browser tab from search results
            listing_url: URL to listing detail page

        Returns:
            HTML content of detail page
        """
        await self._rate_limit_search()
        await tab.get(listing_url)
        await asyncio.sleep(self.RESULT_WAIT_SECONDS)
        content = await tab.get_content()
        return str(content) if content else ""

    def _extract_kill_switch_fields(self, html: str) -> dict[str, Any]:
        """Extract kill-switch fields from listing detail page.

        Args:
            html: HTML content of listing detail page

        Returns:
            Dict with kill-switch fields (hoa_fee, beds, baths, sqft,
            lot_sqft, garage_spaces, sewer_type, year_built)
        """
        soup = BeautifulSoup(html, "html.parser")
        metadata: dict[str, Any] = {}

        # Get full text for regex searching
        page_text = soup.get_text()

        # HOA Fee
        hoa_match = self.HOA_PATTERN.search(page_text)
        if hoa_match:
            metadata["hoa_fee"] = self._parse_hoa(hoa_match.group(1))
        else:
            # Check for explicit "No HOA" or similar
            if re.search(r"No\s+(?:HOA|Association|Fees)", page_text, re.IGNORECASE):
                metadata["hoa_fee"] = 0.0

        # Beds
        beds_match = self.BEDS_PATTERN.search(page_text)
        if beds_match:
            metadata["beds"] = int(beds_match.group(1))

        # Baths
        baths_match = self.BATHS_PATTERN.search(page_text)
        if baths_match:
            metadata["baths"] = float(baths_match.group(1))

        # SqFt
        sqft_match = self.SQFT_PATTERN.search(page_text)
        if sqft_match:
            metadata["sqft"] = int(sqft_match.group(1).replace(",", ""))

        # Lot SqFt
        lot_match = self.LOT_SQFT_PATTERN.search(page_text)
        if lot_match:
            metadata["lot_sqft"] = int(lot_match.group(1).replace(",", ""))
        else:
            # Try acres format
            acres_match = self.ACRES_PATTERN.search(page_text)
            if acres_match:
                acres = float(acres_match.group(1))
                metadata["lot_sqft"] = int(acres * 43560)

        # Garage Spaces
        garage_match = self.GARAGE_PATTERN.search(page_text)
        if garage_match:
            metadata["garage_spaces"] = int(garage_match.group(1))

        # Sewer
        sewer_match = self.SEWER_PATTERN.search(page_text)
        if sewer_match:
            metadata["sewer_type"] = self._parse_sewer(sewer_match.group(1))

        # Year Built
        year_match = self.YEAR_PATTERN.search(page_text)
        if year_match:
            metadata["year_built"] = int(year_match.group(1))

        logger.debug("%s extracted %d kill-switch fields", self.name, len(metadata))
        return metadata

    def _parse_hoa(self, value: str) -> float | None:
        """Parse HOA fee from text value.

        Args:
            value: HOA text (e.g., "No Fees", "$150/month", "$1,200/year")

        Returns:
            Monthly HOA fee as float, or None if unparseable
        """
        value_lower = value.lower().strip()

        # Check for no HOA
        if any(x in value_lower for x in ["no fee", "none", "n/a", "$0"]):
            return 0.0

        # Extract dollar amount
        amount_match = re.search(r"\$?([\d,]+(?:\.\d{2})?)", value)
        if not amount_match:
            # ISSUE 2 FIX - log parse failures
            logger.debug("%s failed to parse HOA from: %r", self.name, value)
            return None

        amount = float(amount_match.group(1).replace(",", ""))

        # Check if yearly and convert to monthly
        if "year" in value_lower or "annual" in value_lower:
            amount = amount / 12.0

        return amount

    def _parse_sewer(self, value: str) -> str | None:
        """Parse sewer type from text value.

        Args:
            value: Sewer text (e.g., "Sewer - Public", "Septic Tank")

        Returns:
            "city" or "septic", or None if unparseable
        """
        value_lower = value.lower().strip()

        if any(x in value_lower for x in ["public", "city", "municipal"]):
            return "city"
        elif "septic" in value_lower:
            return "septic"

        # ISSUE 2 FIX - log parse failures
        logger.debug("%s failed to parse sewer from: %r", self.name, value)
        return None

    async def _open_photo_gallery(self, tab: uc.Tab) -> bool:
        """Open photo gallery modal to load all images.

        PhoenixMLS shows only ~7 thumbnail images on the initial page load.
        The full gallery (all 43+ photos) is loaded when the user clicks on
        the main image or a "View Photos" button, which opens a modal/lightbox.

        This method attempts multiple strategies to open the gallery:
        1. Click on the main carousel/hero image
        2. Click on any element with 'gallery', 'photo', or 'image' in class/aria-label
        3. Look for explicit "View Photos" or similar buttons

        Args:
            tab: Browser tab with listing detail page loaded

        Returns:
            True if gallery was successfully opened, False otherwise
        """
        logger.info("%s attempting to open photo gallery modal", self.name)

        # Strategy 1: Click main image (most common pattern)
        try:
            # Use JavaScript to find and click the main image
            clicked = await tab.evaluate("""() => {
                // Try to find main image by common selectors
                const selectors = [
                    'img[src*="sparkplatform"]',  // Main SparkPlatform image
                    '.carousel img',              // Carousel image
                    '.hero-image img',            // Hero image
                    '.listing-image img',         // Listing image
                    '[class*="photo"] img',       // Any photo container
                    '[class*="gallery"] img',     // Any gallery container
                ];

                for (const selector of selectors) {
                    const img = document.querySelector(selector);
                    if (img && img.offsetParent !== null) {  // Check if visible
                        img.click();
                        return true;
                    }
                }
                return false;
            }""")

            if clicked:
                logger.info("%s clicked main image to open gallery", self.name)
                await asyncio.sleep(2)  # Wait for modal to open
                return True
        except Exception as e:
            logger.debug("%s Strategy 1 (main image click) failed: %s", self.name, e)

        # Strategy 2: Look for "View Photos" or similar button
        try:
            clicked = await tab.evaluate("""() => {
                // Look for buttons/links with photo-related text
                const patterns = [
                    /view.*photos?/i,
                    /see.*photos?/i,
                    /all.*photos?/i,
                    /photo.*gallery/i,
                ];

                const selector = 'button, a, [role="button"]';
                const elements = Array.from(document.querySelectorAll(selector));
                for (const el of elements) {
                    const text = el.textContent || el.getAttribute('aria-label') || '';
                    for (const pattern of patterns) {
                        if (pattern.test(text)) {
                            el.click();
                            return true;
                        }
                    }
                }
                return false;
            }""")

            if clicked:
                logger.info("%s clicked 'View Photos' button to open gallery", self.name)
                await asyncio.sleep(2)  # Wait for modal to open
                return True
        except Exception as e:
            logger.debug("%s Strategy 2 (button click) failed: %s", self.name, e)

        # Strategy 3: Try clicking any element with gallery/photo in class name
        try:
            clicked = await tab.evaluate("""() => {
                const selectors = [
                    '[class*="gallery"]',
                    '[class*="photo"]',
                    '[class*="image-viewer"]',
                    '[class*="lightbox"]',
                    '[aria-label*="photo"]',
                    '[aria-label*="gallery"]',
                ];

                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    if (el && el.offsetParent !== null) {  // Check if visible
                        el.click();
                        return true;
                    }
                }
                return false;
            }""")

            if clicked:
                logger.info("%s clicked gallery element to open modal", self.name)
                await asyncio.sleep(2)  # Wait for modal to open
                return True
        except Exception as e:
            logger.debug("%s Strategy 3 (gallery element click) failed: %s", self.name, e)

        logger.warning("%s all gallery opening strategies failed", self.name)
        return False

    async def _extract_images_via_javascript(self, tab: uc.Tab) -> list[str]:
        """Extract all SparkPlatform image URLs via DOM query with fallback.

        Since tab.evaluate() is unreliable with nodriver, this method now uses
        BeautifulSoup on tab.get_content() to parse the HTML for image URLs.

        Args:
            tab: Browser tab with listing page loaded

        Returns:
            List of full-size SparkPlatform image URLs
        """
        try:
            # Get page HTML and parse for image URLs using BeautifulSoup
            page_html = await tab.get_content()
            if not page_html:
                logger.debug("%s no HTML content from page", self.name)
                return []

            soup = BeautifulSoup(str(page_html), "html.parser")
            urls: list[str] = []
            seen: set[str] = set()

            # Find all image elements with SparkPlatform URLs
            for img in soup.find_all("img"):
                for attr in ["src", "data-src", "data-original", "data-lazy-src"]:
                    src = img.get(attr)
                    if not src:
                        continue

                    src = str(src)
                    if "cdn.photos.sparkplatform.com" not in src:
                        continue

                    # Transform to full-size
                    full_url = src
                    for suffix in ["-t.jpg", "-m.jpg", "-l.jpg", "-t.png", "-m.png", "-l.png"]:
                        if suffix in full_url:
                            full_url = full_url.replace(suffix, "-o" + suffix[-4:])
                            break

                    if full_url not in seen:
                        urls.append(full_url)
                        seen.add(full_url)

            # Also check anchor tags for image links
            for a in soup.find_all("a", href=True):
                href = str(a.get("href", ""))
                if "cdn.photos.sparkplatform.com" in href and href.endswith((".jpg", ".png", ".jpeg")):
                    # Transform to full-size
                    full_url = href
                    for suffix in ["-t.jpg", "-m.jpg", "-l.jpg", "-t.png", "-m.png", "-l.png"]:
                        if suffix in full_url:
                            full_url = full_url.replace(suffix, "-o" + suffix[-4:])
                            break

                    if full_url not in seen:
                        urls.append(full_url)
                        seen.add(full_url)

            logger.info("%s extracted %d image URLs via HTML parsing", self.name, len(urls))
            return urls

        except Exception as e:
            logger.warning("%s HTML-based image extraction failed: %s", self.name, e)
            return []

    def _extract_gallery_images(self, html: str) -> list[str]:
        """Extract image URLs from gallery, transforming to full-size.

        SparkPlatform CDN URL transformation:
            Thumbnail: https://cdn.photos.sparkplatform.com/az/{id}-t.jpg
            Full-size: https://cdn.photos.sparkplatform.com/az/{id}-o.jpg

        Args:
            html: HTML content of listing detail page

        Returns:
            List of full-size image URLs
        """
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        # Find all images
        for img in soup.find_all("img"):
            for attr in ["src", "data-src", "data-original", "data-lazy-src"]:
                src = img.get(attr)
                if not src:
                    continue

                src = str(src)

                # Only process SparkPlatform CDN URLs
                if "cdn.photos.sparkplatform.com" not in src:
                    continue

                # Transform to full-size
                full_url = src
                for suffix in ["-t.jpg", "-m.jpg", "-l.jpg", "-t.png", "-m.png", "-l.png"]:
                    if suffix in full_url:
                        full_url = full_url.replace(suffix, "-o" + suffix[-4:])
                        break

                # Deduplicate
                if full_url not in seen:
                    urls.append(full_url)
                    seen.add(full_url)

        # Also check anchor tags for image links
        for a in soup.find_all("a", href=True):
            href = str(a.get("href", ""))
            if "cdn.photos.sparkplatform.com" in href and href.endswith((".jpg", ".png", ".jpeg")):
                # Transform to full-size
                full_url = href
                for suffix in ["-t.jpg", "-m.jpg", "-l.jpg", "-t.png", "-m.png", "-l.png"]:
                    if suffix in full_url:
                        full_url = full_url.replace(suffix, "-o" + suffix[-4:])
                        break

                if full_url not in seen:
                    urls.append(full_url)
                    seen.add(full_url)

        logger.info("%s extracted %d SparkPlatform image URLs", self.name, len(urls))
        return urls

    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract image URLs from PhoenixMLS via direct listing navigation.

        UPDATED WORKFLOW (2025-12-06):
        1. Perform search with property address (fills input + finds autocomplete)
        2. Extract MLS# and address from autocomplete text
        3. Construct direct listing URL and navigate (skip broken search results)
        4. Extract metadata from detail page
        5. Open photo gallery modal to load ALL images (not just ~7 visible thumbnails)
        6. Extract images via JavaScript (dynamic DOM) + HTML parsing (static content)
        7. Deduplicate and combine results from both extraction methods
        8. Store MLS# and return all image URLs

        Gallery Opening Strategy:
        - Tries 3 strategies: main image click, "View Photos" button, gallery elements
        - Falls back to static page extraction if gallery modal cannot be opened
        - Waits 3 seconds after opening gallery for lazy-loaded images to render

        Args:
            tab: Browser tab with Simple Search page loaded

        Returns:
            List of image URLs found (typically 40+ for full gallery, 7 without modal)
        """
        # Get property from context (stored in self._current_property)
        property = self._current_property

        if not property:
            logger.error("%s no property set for extraction", self.name)
            return []

        # Step 1: Perform search and navigate directly to listing
        # NOTE: _search_for_property now extracts MLS# and navigates directly to detail page
        search_success = await self._search_for_property(tab, property)
        if not search_success:
            logger.warning("%s direct navigation failed for %s", self.name, property.full_address)
            return []

        # Step 2: We're already on the detail page (no need to navigate from search results)
        # Verify we're on the correct page
        current_url = str(tab.target.url) if hasattr(tab, "target") else ""
        if "/mls/" not in current_url or "-mls_" not in current_url:
            logger.error("%s not on listing detail page after search: %s", self.name, current_url)
            return []

        logger.info("%s verified on listing detail page: %s", self.name, current_url)

        # Step 3: Get detail page HTML
        detail_html = await tab.get_content()
        if not detail_html:
            logger.error("%s no HTML content from detail page", self.name)
            return []

        # Extract MLS# from current URL (pattern: /mls/{address-slug}-mls_{mls_number}/)
        current_url = str(tab.target.url) if hasattr(tab, "target") else ""
        mls_number = ""
        mls_match = re.search(r"-mls_(\d+)", current_url)
        if mls_match:
            mls_number = mls_match.group(1)
            logger.info("%s extracted MLS# %s from URL", self.name, mls_number)
        else:
            logger.warning("%s could not extract MLS# from URL: %s", self.name, current_url)

        # Step 4: Extract metadata
        metadata = self._extract_kill_switch_fields(str(detail_html))
        metadata["mls_number"] = mls_number
        metadata["listing_url"] = current_url

        # Step 5: Open photo gallery to load all images (not just visible ones)
        gallery_opened = await self._open_photo_gallery(tab)
        if gallery_opened:
            logger.info("%s successfully opened photo gallery modal", self.name)
            # Wait for images to load in gallery
            await asyncio.sleep(3)
        else:
            logger.warning(
                "%s could not open photo gallery; extracting from static page only", self.name
            )

        # Step 6: Extract images (from expanded gallery if opened, otherwise from static page)
        # Use both JavaScript (for dynamic content) and HTML parsing (for static content)
        js_image_urls = await self._extract_images_via_javascript(tab)
        detail_html_after_gallery = await tab.get_content()
        html_image_urls = self._extract_gallery_images(str(detail_html_after_gallery))

        # Combine and deduplicate both sources
        all_image_urls = list(set(js_image_urls + html_image_urls))
        logger.info(
            "%s extracted %d images (JS: %d, HTML: %d, unique: %d)",
            self.name,
            len(all_image_urls),
            len(js_image_urls),
            len(html_image_urls),
            len(all_image_urls),
        )
        image_urls = all_image_urls

        # Step 7: Store metadata for orchestrator (ISSUE 1 FIX - thread-safe write)
        async with self._metadata_lock:
            self.last_metadata = metadata

        logger.info(
            "%s extracted %d images and %d metadata fields for %s",
            self.name,
            len(image_urls),
            len(metadata),
            property.full_address,
        )

        return image_urls

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract image URLs using stealth browser navigation.

        This is the main entry point called by the orchestrator.
        Stores metadata in self.last_metadata for orchestrator retrieval.

        Args:
            property: Property to find images for

        Returns:
            List of image URLs (metadata stored in self.last_metadata)
        """
        # Store property for _extract_urls_from_page to access
        self._current_property = property

        # Call parent implementation which handles navigation and CAPTCHA
        # This will call _extract_urls_from_page internally which populates last_metadata
        urls = await super().extract_image_urls(property)

        # Return URLs only (metadata accessible via self.last_metadata)
        return urls

    def get_cached_metadata(self, property: Property) -> dict[str, Any] | None:
        """Retrieve cached metadata from last extraction.

        After extract_image_urls() is called, metadata is stored in
        self.last_metadata for orchestrator retrieval.

        Args:
            property: Property object (not used, kept for interface compatibility)

        Returns:
            Dict of metadata fields or None if not cached
        """
        return self.last_metadata if self.last_metadata else None

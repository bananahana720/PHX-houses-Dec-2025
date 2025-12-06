"""Zillow image extractor using nodriver for stealth browser automation.

Zillow is a JavaScript-heavy site with anti-bot protection requiring stealth
browser automation to properly load images from dynamic galleries and carousels.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from typing import Any
from urllib.parse import quote_plus

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from .stealth_base import StealthBrowserExtractor

logger = logging.getLogger(__name__)


class ZillowExtractor(StealthBrowserExtractor):
    """Zillow image extractor using nodriver stealth browser automation.

    Zillow requires stealth browser automation because:
    - Heavy JavaScript rendering for image galleries
    - Lazy-loaded images in carousels
    - Dynamic content based on viewport/interactions
    - PerimeterX anti-bot protection blocking simple HTTP requests
    - Press & Hold CAPTCHA challenges for detected automation

    Extracts high-resolution images from property detail pages using
    nodriver for undetectable Chrome automation and curl_cffi for
    bot-resistant HTTP downloads.

    SECURITY: This extractor includes multiple safeguards against search result
    contamination (extracting images from wrong properties):
    - Strict zpid validation in JSON extraction
    - URL-based zpid filtering for all extracted images
    - Page type validation before and after extraction
    - High URL count threshold triggering re-validation

    Example:
        ```python
        async with ZillowExtractor() as extractor:
            urls = await extractor.extract_image_urls(property)
            for url in urls:
                image_bytes, content_type = await extractor.download_image(url)
        ```
    """

    # Maximum number of images expected from a single property listing
    # Exceeding this suggests search result contamination
    MAX_EXPECTED_IMAGES_PER_PROPERTY = 50

    # Patterns that indicate search result or carousel URLs (to be rejected)
    SEARCH_RESULT_URL_PATTERNS = [
        "/search/",
        "/homes-for-sale/",
        "searchResultsMap",
        "carousel",
        "similar-homes",
        "nearby",
        "recommendation",
    ]

    # Placeholder URL patterns indicating "No Photo Available" images
    PLACEHOLDER_URL_PATTERNS = [
        "no-photo",
        "no-image",
        "placeholder",
        "unavailable",
        "default-image",
        "missing-photo",
        "no_photo",
    ]

    # Keys in __NEXT_DATA__ JSON that contain images from OTHER properties (contamination sources)
    CONTAMINATION_KEYS = frozenset({
        "similarHomes",
        "nearbyHomes",
        "recommendedHomes",
        "otherListings",
        "searchResults",
        "carousel",
    })

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize Zillow extractor with stealth configuration.

        Args:
            http_client: Shared httpx client (maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction configuration (loaded from env if not provided)
        """
        super().__init__(http_client=http_client, timeout=timeout, config=config)

        # Store metadata from last extraction for orchestrator retrieval
        self.last_metadata: dict = {}

        logger.info(
            "%s initialized for stealth extraction",
            self.name,
        )

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.ZILLOW
        """
        return ImageSource.ZILLOW

    def _build_search_url(self, property: Property) -> str:
        """Build Zillow search URL from property address.

        Zillow search URL format:
            /homes/{street}-{city}-{state}-{zip}_rb/

        Each component is URL-encoded and spaces replaced with dashes.

        Args:
            property: Property entity with address components

        Returns:
            Full Zillow search URL for the property

        Example:
            Input: "4732 W Davis Rd", "Glendale", "AZ", "85306"
            Output: "https://www.zillow.com/homes/4732-W-Davis-Rd-Glendale-AZ-85306_rb/"
        """
        # URL-encode address components and replace spaces with dashes
        street = quote_plus(property.street.replace(" ", "-"))
        city = quote_plus(property.city.replace(" ", "-"))
        state = property.state
        zip_code = property.zip_code

        # Construct search path
        search_path = f"{street}-{city}-{state}-{zip_code}_rb"

        # Build full URL
        url = f"{self.source.base_url}/homes/{search_path}/"

        logger.debug("%s built search URL: %s", self.name, url)
        return url

    def _build_detail_url(self, property: Property) -> str:
        """Build Zillow detail URL when zpid-based slug is available.

        Tries to format: /homedetails/{street-city-state-zip}/{zpid}_zpid/
        Falls back to search URL if zpid not supplied.
        """
        street = property.street.replace(" ", "-")
        city = property.city.replace(" ", "-")
        slug = f"{street}-{city}-{property.state}-{property.zip_code}"

        # If property has a zpid attribute in extra metadata, use it
        zpid = getattr(property, "zpid", None)
        if zpid:
            return f"{self.source.base_url}/homedetails/{slug}/{zpid}_zpid/"

        # Fallback: use search URL
        return self._build_search_url(property)

    # =========================================================================
    # Task 1: ZPID Extraction Helpers (Story E2.R1)
    # =========================================================================

    def _extract_zpid_from_listing_url(self, url: str) -> str | None:
        """Extract zpid from a listing URL string.

        Parses zpid from various Zillow URL formats:
        - /homedetails/{slug}/{zpid}_zpid/
        - /{zpid}_zpid/
        - /homedetails/{zpid}_zpid/#image-lightbox

        Args:
            url: Zillow listing URL

        Returns:
            zpid string if found, None otherwise
        """
        if not url:
            return None

        # Pattern 1: Standard homedetails path with slug
        # Example: /homedetails/4732-W-Davis-Rd/7686459_zpid/
        patterns = [
            r"/homedetails/[^/]+/(\d{6,10})_zpid",  # With slug
            r"/homedetails/(\d{6,10})_zpid",  # Without slug
            r"/(\d{6,10})_zpid",  # Minimal
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                zpid = match.group(1)
                logger.debug("%s extracted zpid %s from URL: %s", self.name, zpid, url[:80])
                return zpid

        logger.debug("%s no zpid found in URL: %s", self.name, url[:80])
        return None

    def _extract_zpid_from_json(self, json_content: str) -> str | None:
        """Extract zpid from Zillow JSON response content.

        Parses zpid from __NEXT_DATA__ JSON structure:
        - {"zpid": 123456}
        - {"props": {"pageProps": {"zpid": 123456}}}

        Args:
            json_content: JSON string from Zillow page

        Returns:
            zpid string if found, None otherwise
        """
        if not json_content:
            return None

        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            logger.debug("%s failed to parse JSON for zpid extraction", self.name)
            return None

        # Try direct zpid key
        if "zpid" in data:
            zpid = str(data["zpid"])
            logger.debug("%s extracted zpid %s from direct JSON key", self.name, zpid)
            return zpid

        # Try nested paths
        zpid_paths = [
            lambda d: d.get("props", {}).get("pageProps", {}).get("zpid"),
            lambda d: d.get("props", {}).get("zpid"),
            lambda d: d.get("pageProps", {}).get("zpid"),
            lambda d: d.get("propertyZpid"),
        ]

        for path_func in zpid_paths:
            try:
                extracted = path_func(data)
                if extracted:
                    zpid = str(extracted)
                    logger.debug("%s extracted zpid %s from nested JSON", self.name, zpid)
                    return zpid
            except (AttributeError, TypeError):
                continue

        logger.debug("%s no zpid found in JSON content", self.name)
        return None

    # =========================================================================
    # Task 1b: Discover ZPID from Address (Story E2.R1 Enhancement)
    # =========================================================================

    async def _discover_zpid_from_address(
        self, property: Property, tab: uc.Tab
    ) -> str | None:
        """Discover zpid by navigating to Zillow with address search.

        When no zpid or listing_url is available, this method:
        1. Navigates to Zillow direct URL with address slug
        2. Extracts zpid from resulting page URL or __NEXT_DATA__

        Args:
            property: Property with full_address
            tab: Browser tab to use

        Returns:
            zpid string if discovered, None otherwise
        """
        logger.info("%s discovering zpid from address: %s", self.name, property.full_address)

        try:
            # Build address-based URL (same as _build_search_url but simpler)
            address_slug = property.full_address.lower()
            address_slug = address_slug.replace(",", "").replace(".", "")
            address_slug = "-".join(address_slug.split())
            direct_url = f"{self.source.base_url}/homes/{address_slug}_rb/"

            logger.info("%s navigating to: %s", self.name, direct_url)
            await tab.get(direct_url)
            await self._human_delay()

            # Check for CAPTCHA first
            if await self._check_for_captcha(tab):
                logger.warning("%s CAPTCHA detected during zpid discovery", self.name)
                return None

            # Try to extract zpid from current URL
            current_url = str(tab.url) if hasattr(tab, "url") else ""
            zpid = self._extract_zpid_from_listing_url(current_url)
            if zpid:
                logger.info("%s discovered zpid %s from URL: %s", self.name, zpid, current_url)
                return zpid

            # Try to extract from __NEXT_DATA__
            try:
                next_data_script = await tab.query_selector("script#__NEXT_DATA__")
                if next_data_script:
                    json_content = await tab.evaluate(
                        "(el) => el.textContent", next_data_script
                    )
                    zpid = self._extract_zpid_from_json(json_content)
                    if zpid:
                        logger.info("%s discovered zpid %s from __NEXT_DATA__", self.name, zpid)
                        return zpid
            except Exception as e:
                logger.debug("%s failed to extract __NEXT_DATA__: %s", self.name, e)

            logger.warning("%s could not discover zpid from address", self.name)
            return None

        except Exception as e:
            logger.warning("%s zpid discovery failed: %s", self.name, e)
            return None

    # =========================================================================
    # Task 2: Gallery URL Builder and Navigation (Story E2.R1)
    # =========================================================================

    def _build_gallery_url(self, property: Property) -> str | None:
        """Build direct gallery URL with #image-lightbox hash.

        Creates URL format: zillow.com/homedetails/{zpid}_zpid/#image-lightbox

        Args:
            property: Property with zpid attribute

        Returns:
            Gallery URL if zpid available, None otherwise
        """
        zpid = getattr(property, "zpid", None)
        if not zpid:
            logger.debug("%s cannot build gallery URL without zpid", self.name)
            return None

        url = f"{self.source.base_url}/homedetails/{zpid}_zpid/#image-lightbox"
        logger.debug("%s built gallery URL: %s", self.name, url)
        return url

    async def _is_gallery_page(self, tab: uc.Tab) -> bool:
        """Detect if current page is a photo gallery/lightbox.

        Checks for photo carousel elements indicating gallery view.

        Args:
            tab: Browser tab to check

        Returns:
            True if gallery elements detected, False otherwise
        """
        gallery_selectors = [
            '[data-testid="media-carousel"]',
            '[data-testid="lightbox-container"]',
            ".photo-carousel",
            ".media-lightbox",
            '[role="dialog"] img[src*="photos.zillowstatic.com"]',
            ".lightbox-modal",
        ]

        for selector in gallery_selectors:
            try:
                elements = await tab.query_selector_all(selector)
                if elements:
                    logger.debug("%s gallery detected via selector: %s", self.name, selector)
                    return True
            except Exception:
                continue

        logger.debug("%s no gallery elements found", self.name)
        return False

    async def _navigate_to_gallery_direct(
        self, property: Property, tab: uc.Tab
    ) -> bool:
        """Navigate directly to gallery URL using zpid.

        Attempts to bypass search by navigating directly to:
        zillow.com/homedetails/{zpid}_zpid/#image-lightbox

        Args:
            property: Property with zpid
            tab: Browser tab

        Returns:
            True if navigation succeeded and gallery detected, False otherwise
        """
        gallery_url = self._build_gallery_url(property)
        if not gallery_url:
            logger.warning("%s no gallery URL available (zpid missing)", self.name)
            return False

        try:
            logger.info("%s navigating directly to gallery: %s", self.name, gallery_url)
            await tab.get(gallery_url)
            await self._human_delay()

            # Check for CAPTCHA
            if await self._check_for_captcha(tab):
                logger.warning("%s CAPTCHA on gallery page, attempting solve", self.name)
                if not await self._attempt_captcha_solve_v2(tab):
                    logger.error("%s CAPTCHA solve failed on gallery", self.name)
                    return False
                await self._human_delay()

            # Validate gallery loaded
            if await self._is_gallery_page(tab):
                logger.info("%s gallery page loaded successfully", self.name)
                return True

            logger.warning("%s gallery navigation did not reach expected page", self.name)
            return False

        except Exception as e:
            logger.error("%s gallery navigation failed: %s", self.name, e)
            return False

    # =========================================================================
    # Task 3: Screenshot Fallback (Story E2.R1)
    # =========================================================================

    async def _capture_gallery_screenshots(
        self, tab: uc.Tab, max_images: int = 30
    ) -> list[str]:
        """Capture gallery screenshots by cycling through thumbnail gallery.

        Opens gallery and captures each image by clicking thumbnails in sequence
        until a duplicate is detected.

        Args:
            tab: Browser tab with property page loaded
            max_images: Maximum screenshots to capture

        Returns:
            List of saved screenshot file paths
        """
        screenshots: list[str] = []
        prev_hash: str | None = None

        logger.info("%s starting thumbnail screenshot capture (max=%d)", self.name, max_images)

        # Click hero image to open gallery
        try:
            hero = await tab.query_selector("img[src*='photos.zillowstatic.com']")
            if hero:
                logger.info("%s clicking hero image to open gallery", self.name)
                await hero.click()
                await asyncio.sleep(1.5)  # Wait for gallery to open
        except Exception as e:
            logger.warning("%s could not click hero image: %s", self.name, e)

        # Reset thumbnail index for this property
        self._thumbnail_index = 0

        for i in range(max_images):
            try:
                # Step 1: Capture screenshot of current carousel view
                screenshot_bytes = await self._capture_carousel_screenshot(tab)
                if not screenshot_bytes:
                    logger.warning("%s failed to capture at frame %d", self.name, i)
                    break

                # Step 2: Check for duplicate (end of gallery)
                content_hash = hashlib.md5(screenshot_bytes).hexdigest()
                if content_hash == prev_hash:
                    logger.info("%s duplicate frame at %d, carousel complete", self.name, i)
                    break

                # Step 3: Save screenshot
                path = self._save_screenshot(screenshot_bytes, content_hash)
                screenshots.append(path)
                prev_hash = content_hash

                logger.debug("%s captured frame %d: %s", self.name, i, content_hash[:8])

                # Step 4: Advance to next image
                await self._advance_carousel(tab)

            except Exception as e:
                logger.warning("%s capture error at frame %d: %s", self.name, i, e)
                break

        logger.info("%s captured %d carousel screenshots", self.name, len(screenshots))
        return screenshots

    async def _capture_carousel_screenshot(self, tab: uc.Tab) -> bytes | None:
        """Capture screenshot of current carousel view.

        Returns:
            Screenshot bytes if successful, None otherwise
        """
        try:
            await asyncio.sleep(0.3)  # Brief wait for image to load
            temp_path = await tab.save_screenshot(format="png")

            if not temp_path or not os.path.exists(temp_path):
                return None

            with open(temp_path, "rb") as f:
                screenshot_bytes = f.read()

            try:
                os.unlink(temp_path)
            except Exception:
                pass

            return screenshot_bytes

        except Exception as e:
            logger.error("%s screenshot failed: %s", self.name, e)
            return None

    async def _advance_carousel(self, tab: uc.Tab) -> bool:
        """Advance to next image by clicking next thumbnail.

        Zillow uses a thumbnail-based gallery. We track which thumbnail
        we've clicked and click the next one each iteration.

        Returns:
            True if successfully clicked next thumbnail, False if no more
        """
        try:
            # Track which thumbnail we're on
            if not hasattr(self, '_thumbnail_index'):
                self._thumbnail_index = 0

            current_index = self._thumbnail_index

            # Embed index directly in JS (nodriver doesn't support evaluate params)
            js_click_next_thumbnail = f"""
            (() => {{
                const currentIndex = {current_index};

                // Find thumbnail container - try multiple selectors
                const thumbContainers = [
                    document.querySelectorAll('[data-testid="hollywood-vertical-media-stream"] button'),
                    document.querySelectorAll('.media-stream-tile'),
                    document.querySelectorAll('[aria-label*="photo" i]'),
                    document.querySelectorAll('button img[src*="photos.zillowstatic.com"]'),
                ];

                let thumbnails = [];
                for (const container of thumbContainers) {{
                    if (container.length > 0) {{
                        thumbnails = Array.from(container);
                        break;
                    }}
                }}

                if (thumbnails.length === 0) {{
                    // Fallback: find all small Zillow images (likely thumbnails)
                    const allImages = document.querySelectorAll('img[src*="photos.zillowstatic.com"]');
                    thumbnails = Array.from(allImages).filter(img => {{
                        const rect = img.getBoundingClientRect();
                        // Thumbnails are typically smaller than main image
                        return rect.width < 300 && rect.height < 200 && rect.width > 50;
                    }});
                }}

                // Click the next thumbnail (currentIndex + 1)
                const nextIndex = currentIndex + 1;
                if (nextIndex < thumbnails.length) {{
                    const thumb = thumbnails[nextIndex];
                    // Click the thumbnail or its parent button
                    const clickTarget = thumb.closest('button') || thumb;
                    clickTarget.click();
                    return nextIndex;  // Return the index we clicked
                }}

                return -1;  // No more thumbnails
            }})()
            """

            result = await tab.evaluate(js_click_next_thumbnail)

            if result is not None and result >= 0:
                self._thumbnail_index = result
                await asyncio.sleep(0.8)  # Wait for image to load
                logger.debug("%s clicked thumbnail %d", self.name, result)
                return True
            else:
                logger.debug("%s no more thumbnails", self.name)
                return False

        except Exception as e:
            logger.warning("%s thumbnail advance failed: %s", self.name, e)
            return False

    def _save_screenshot(self, screenshot_bytes: bytes, content_hash: str) -> str:
        """Save screenshot to content-addressed storage.

        Args:
            screenshot_bytes: PNG screenshot data
            content_hash: MD5 hash of content

        Returns:
            Path where screenshot was saved
        """
        # Use content-addressed path structure
        subdir = content_hash[:8]
        filename = f"{content_hash}.png"

        # Determine base directory from config or default
        base_dir = os.environ.get(
            "SCREENSHOT_DIR", "data/property_images/screenshots"
        )
        full_dir = os.path.join(base_dir, subdir)
        os.makedirs(full_dir, exist_ok=True)

        path = os.path.join(full_dir, filename)

        # Write atomically
        with open(path, "wb") as f:
            f.write(screenshot_bytes)

        logger.debug("%s saved screenshot: %s", self.name, path)
        return path

    def _build_screenshot_metadata(self, content_hash: str) -> dict:
        """Build metadata dict for screenshot images.

        Args:
            content_hash: MD5 hash of screenshot content

        Returns:
            Metadata dict with screenshot markers
        """
        return {
            "screenshot": True,
            "content_hash": content_hash,
            "source": "screenshot_capture",
            "confidence": 0.8,  # Lower confidence than URL-extracted
        }

    def _set_extraction_method(self, method: str | None) -> None:
        """Set extraction method in last_metadata for tracking.

        P0-1 FIX: Track which fallback method succeeded for debugging
        and metrics.

        Args:
            method: One of "zpid-direct", "screenshot", "google-images", "search", or None
        """
        if method:
            self.last_metadata["extraction_method"] = method
            logger.info("%s extraction method: %s", self.name, method)

    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """DEPRECATED: Screenshot-only extraction - this method is no longer used.

        Wave 3 Screenshot-Only Refactoring: This method is now a no-op stub
        to satisfy the StealthBrowserExtractor abstract method requirement.
        All image extraction is done via _capture_gallery_screenshots() which
        returns file paths, not URLs.

        Args:
            tab: Browser tab (unused)

        Returns:
            Empty list (URLs no longer extracted)
        """
        logger.warning(
            "%s _extract_urls_from_page called but deprecated in screenshot-only mode",
            self.name,
        )
        return []

    # =========================================================================
    # Task 4: Google Images Fallback (Story E2.R1)
    # =========================================================================

    # =========================================================================
    # Original _extract_zpid_from_url (async, uses tab)
    # =========================================================================

    async def _extract_zpid_from_url(self, tab: uc.Tab) -> str | None:
        """Extract zpid from current URL if present.

        FIX: Enhanced with multiple extraction patterns and fallback to __NEXT_DATA__.
        Tries in order:
        1. URL path patterns (/123456_zpid/, /homedetails/.../123456_zpid/)
        2. Query parameters (?zpid=123456, &zpid=123456)
        3. Fallback to window.__NEXT_DATA__
        """
        try:
            href = await tab.evaluate("() => window.location.href")

            # Pattern 1: Path-based zpid (original pattern plus variations)
            path_patterns = [
                r"/(\d{8,10})_zpid",  # Standard: /123456789_zpid
                r"_zpid/(\d{8,10})",  # Variation: _zpid/123456789
                r"/homedetails/[^/]+/(\d{8,10})_zpid",  # Full homedetails path
            ]

            for pattern in path_patterns:
                match = re.search(pattern, href)
                if match:
                    zpid = match.group(1)
                    logger.debug("%s extracted zpid %s from URL path", self.name, zpid)
                    return zpid

            # Pattern 2: Query parameter zpid
            query_match = re.search(r"[?&]zpid=(\d{8,10})", href)
            if query_match:
                zpid = query_match.group(1)
                logger.debug("%s extracted zpid %s from query param", self.name, zpid)
                return zpid

            # Pattern 3: Fallback to __NEXT_DATA__ window object
            try:
                window_zpid = await tab.evaluate(
                    "() => window.__NEXT_DATA__?.props?.pageProps?.zpid || null"
                )
                if window_zpid:
                    zpid = str(window_zpid)
                    logger.debug("%s extracted zpid %s from __NEXT_DATA__", self.name, zpid)
                    return zpid
            except Exception as e:
                logger.debug("%s could not access __NEXT_DATA__.zpid: %s", self.name, e)

        except Exception as e:
            logger.debug("%s could not parse zpid from URL: %s", self.name, e)
        return None

    async def extract_listing_metadata(self, tab: uc.Tab) -> dict:
        """Extract comprehensive listing metadata from loaded Zillow page.

        Extracts property details, market data, and features including:

        **Property Details**:
        - beds, baths, sqft, lot_sqft, year_built
        - property_type, garage_spaces, parking_spaces, pool, stories

        **Listing Metadata**:
        - list_price, hoa_fee, days_on_market
        - original_list_price, price_reduced, price_reduced_pct

        **Features**:
        - cooling_type, heating_type, flooring_types, appliances_included
        - sewer_type, water_source

        Args:
            tab: Browser tab with loaded Zillow property page

        Returns:
            Dictionary with all extracted fields (empty dict if extraction fails)

        Note:
            Returns None for unavailable fields (doesn't fail).
        """
        logger.info("%s extracting comprehensive listing metadata", self.name)
        metadata: dict = {}

        try:
            # Get page content for extraction
            content = await tab.get_content()

            # Extract property details (core attributes)
            metadata.update(self._extract_property_details(content))

            # Extract property features (systems and amenities)
            metadata.update(self._extract_property_features(content))

            # Extract market data (pricing and timeline)
            metadata["days_on_market"] = self._extract_days_on_market(content)
            metadata.update(self._extract_price_info(content))

            # Extract HOA if present (backup extraction)
            hoa = self._extract_hoa_fee(content)
            if hoa is not None:
                metadata["hoa_fee"] = hoa

            # Count how many fields were successfully extracted
            non_none_count = sum(1 for v in metadata.values() if v is not None)
            logger.info(
                "%s extracted %d metadata fields (beds=%s, baths=%s, sqft=%s, DOM=%s)",
                self.name,
                non_none_count,
                metadata.get("beds"),
                metadata.get("baths"),
                metadata.get("sqft"),
                metadata.get("days_on_market"),
            )

            return metadata

        except Exception as e:
            logger.error("%s failed to extract metadata: %s", self.name, e)
            return {}

    def _extract_days_on_market(self, content: str) -> int | None:
        """Extract days on market from page content.

        Zillow patterns:
        - "X days on Zillow"
        - "Listed X hours ago"
        - "Just listed"
        """
        content_lower = content.lower()

        # Pattern: "X days on zillow"
        match = re.search(r"(\d+)\s+days?\s+on\s+zillow", content_lower)
        if match:
            return int(match.group(1))

        # Pattern: "Listed X hours ago" = 0 days
        if re.search(r"listed\s+\d+\s+hours?\s+ago", content_lower):
            return 0

        # Pattern: "Just listed"
        if "just listed" in content_lower:
            return 0

        # Try JSON-LD structured data
        match = re.search(r'"daysOnZillow"\s*:\s*(\d+)', content)
        if match:
            return int(match.group(1))

        return None

    def _extract_price_info(self, content: str) -> dict:
        """Extract price history and reduction info.

        Returns:
            Dict with original_list_price, price_reduced, price_reduced_pct
        """
        result: dict = {
            "original_list_price": None,
            "price_reduced": None,
            "price_reduced_pct": None,
        }

        # Look for price cut indicator
        content_lower = content.lower()

        # Pattern: "Price cut: -$X,XXX" or "Reduced $X,XXX"
        if "price cut" in content_lower or "price drop" in content_lower:
            result["price_reduced"] = True

            # Try to extract amount
            cut_match = re.search(
                r"(?:price\s+cut|reduced)[:\s]*-?\$?([\d,]+)",
                content_lower,
            )
            if cut_match:
                try:
                    cut_amount = int(cut_match.group(1).replace(",", ""))
                    result["price_reduced_amount"] = cut_amount
                except ValueError:
                    pass
        elif "price increased" in content_lower:
            result["price_reduced"] = False

        # Try to extract price history from JSON-LD
        # Pattern: "priceHistory":[{"date":"2025-01-15","price":450000}...]
        history_match = re.search(
            r'"priceHistory"\s*:\s*\[(.*?)\]',
            content,
            re.DOTALL,
        )
        if history_match:
            try:
                # Extract all prices from history
                prices = re.findall(r'"price"\s*:\s*(\d+)', history_match.group(1))
                if len(prices) >= 2:
                    prices_int = [int(p) for p in prices]
                    result["original_list_price"] = max(prices_int)
                    current_price = prices_int[-1]
                    if result["original_list_price"] > current_price:
                        result["price_reduced"] = True
                        result["price_reduced_pct"] = round(
                            (1 - current_price / result["original_list_price"]) * 100, 1
                        )
            except (ValueError, IndexError):
                pass

        return result

    def _extract_hoa_fee(self, content: str) -> int | None:
        """Extract HOA fee from page content.

        Patterns:
        - "HOA: $X/mo"
        - "HOA fee: $X monthly"
        - "No HOA" = 0
        """
        content_lower = content.lower()

        # No HOA
        if "no hoa" in content_lower:
            return 0

        # Pattern: "HOA: $XXX/mo"
        match = re.search(r"hoa[:\s]*\$?([\d,]+)\s*/?\s*mo", content_lower)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass

        # Pattern from JSON-LD: "monthlyHoaFee":XXX
        match = re.search(r'"monthlyHoaFee"\s*:\s*(\d+)', content)
        if match:
            return int(match.group(1))

        return None

    def _safe_extract(
        self,
        html: str,
        field_name: str,
        patterns: list[str],
        parser: Any = str,
        result: dict[str, Any] | None = None,
    ) -> Any | None:
        """Extract field value using regex patterns with fallback chain.

        Args:
            html: HTML content to search
            field_name: Name of field (for logging)
            patterns: List of regex patterns to try in order
            parser: Function to parse matched value (default: str)
            result: Optional dict to check if field already set

        Returns:
            Parsed value if found, None otherwise
        """
        # Skip if field already set in result dict
        if result is not None and result.get(field_name) is not None:
            return result[field_name]

        # Try each pattern in order
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                try:
                    # Apply parser to extracted value
                    value = parser(match.group(1))
                    logger.debug(
                        "%s extracted %s=%s using pattern: %s",
                        self.name,
                        field_name,
                        value,
                        pattern[:50],
                    )
                    return value
                except (ValueError, TypeError) as e:
                    logger.debug(
                        "%s failed to parse %s value '%s': %s",
                        self.name,
                        field_name,
                        match.group(1),
                        e,
                    )
                    continue

        # No pattern matched
        logger.debug("%s could not extract %s from content", self.name, field_name)
        return None

    def _extract_from_json_ld(self, html: str) -> dict[str, Any]:
        """Extract property details from JSON-LD structured data.

        Args:
            html: HTML content containing JSON-LD script tags

        Returns:
            Dict with extracted fields (beds, baths, sqft, etc.)
        """
        result: dict[str, Any] = {
            "beds": None,
            "baths": None,
            "sqft": None,
            "lot_sqft": None,
            "year_built": None,
            "property_type": None,
            "garage_spaces": None,
            "parking_spaces": None,
            "pool": None,
            "stories": None,
            "list_price": None,
        }

        # Search for JSON-LD structured data in script tags
        json_ld_match = re.search(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL | re.IGNORECASE,
        )

        if json_ld_match:
            try:
                json_data = json.loads(json_ld_match.group(1))

                # Beds (numberOfRooms, numberOfBedrooms)
                if "numberOfRooms" in json_data:
                    result["beds"] = int(json_data["numberOfRooms"])
                elif "numberOfBedrooms" in json_data:
                    result["beds"] = int(json_data["numberOfBedrooms"])

                # Baths (numberOfBathroomsTotal)
                if "numberOfBathroomsTotal" in json_data:
                    result["baths"] = float(json_data["numberOfBathroomsTotal"])

                # Sqft (floorSize value)
                if "floorSize" in json_data:
                    floor_size = json_data["floorSize"]
                    if isinstance(floor_size, dict) and "value" in floor_size:
                        result["sqft"] = int(floor_size["value"])
                    elif isinstance(floor_size, (int, float)):
                        result["sqft"] = int(floor_size)

                # List price (price)
                if "price" in json_data:
                    result["list_price"] = int(json_data["price"])

                logger.debug("%s JSON-LD extraction successful", self.name)

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.debug("%s JSON-LD parsing partial failure: %s", self.name, e)

        return result

    def _extract_from_regex_fallback(
        self,
        html: str,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract property details using regex patterns as fallback.

        Only fills fields that are still None in result dict.

        Args:
            html: HTML content to search
            result: Existing result dict (may have values from JSON-LD)

        Returns:
            Updated result dict with fallback extractions
        """
        content_lower = html.lower()

        # Define parsers for field value conversion
        def parse_int(val: str) -> int:
            """Parse integer, removing commas."""
            return int(val.replace(",", ""))

        def parse_float(val: str) -> float:
            """Parse float, removing commas."""
            return float(val.replace(",", ""))

        def parse_acres_to_sqft(val: str) -> int:
            """Parse acres and convert to sqft."""
            return int(float(val) * 43560)

        # Beds - patterns: "4 bd", "4 beds", "Bedrooms: 4"
        beds = self._safe_extract(
            content_lower,
            "beds",
            [r"(\d+)\s*(?:bd|beds?|bedrooms?)[:\s]"],
            parser=int,
            result=result,
        )
        if beds is not None:
            result["beds"] = beds

        # Baths - patterns: "2 ba", "2.5 baths", "Bathrooms: 2"
        baths = self._safe_extract(
            content_lower,
            "baths",
            [r"(\d+(?:\.\d+)?)\s*(?:ba|baths?|bathrooms?)[:\s]"],
            parser=float,
            result=result,
        )
        if baths is not None:
            result["baths"] = baths

        # Sqft - patterns: "2,400 sqft", "2400 square feet"
        sqft = self._safe_extract(
            content_lower,
            "sqft",
            [r"([\d,]+)\s*(?:sqft|square\s*(?:feet|ft))"],
            parser=parse_int,
            result=result,
        )
        if sqft is not None:
            result["sqft"] = sqft

        # Lot size - patterns: "7,500 sqft lot", "0.17 acres"
        lot_sqft = self._safe_extract(
            content_lower,
            "lot_sqft",
            [
                r"([\d,]+)\s*sqft\s*lot",  # Direct sqft
                r"([\d.]+)\s*acres?",  # Acres (converted to sqft)
            ],
            parser=lambda v: parse_int(v) if "," in v else parse_acres_to_sqft(v),
            result=result,
        )
        if lot_sqft is not None:
            result["lot_sqft"] = lot_sqft

        # Year built - patterns: "Built in 2020", "Year built: 2020"
        year_built = self._safe_extract(
            content_lower,
            "year_built",
            [r"(?:built\s*in|year\s*built)[:\s]*(\d{4})"],
            parser=int,
            result=result,
        )
        if year_built is not None:
            result["year_built"] = year_built

        # Property type - patterns: "Single Family", "Townhouse", "Condo"
        type_patterns = [
            (r"single[\s-]family", "Single Family"),
            (r"townhouse", "Townhouse"),
            (r"condo(?:minium)?", "Condo"),
            (r"multi[\s-]family", "Multi Family"),
            (r"manufactured", "Manufactured"),
            (r"apartment", "Apartment"),
        ]
        for pattern, prop_type in type_patterns:
            if re.search(pattern, content_lower):
                result["property_type"] = prop_type
                break

        # Garage spaces - patterns: "2 car garage", "Garage spaces: 2"
        garage_spaces = self._safe_extract(
            content_lower,
            "garage_spaces",
            [
                r"(\d+)[\s-]?car\s*garage",  # "2 car garage"
                r"garage[:\s]*(\d+)",  # "Garage: 2"
            ],
            parser=int,
            result=result,
        )
        if garage_spaces is not None:
            result["garage_spaces"] = garage_spaces

        # Parking spaces - patterns: "Parking: 3 spaces"
        parking_spaces = self._safe_extract(
            content_lower,
            "parking_spaces",
            [r"parking[:\s]*(\d+)"],
            parser=int,
            result=result,
        )
        if parking_spaces is not None:
            result["parking_spaces"] = parking_spaces

        # Pool - detect presence
        if "pool" in content_lower or "swimming pool" in content_lower:
            result["pool"] = True
        elif "no pool" in content_lower:
            result["pool"] = False

        # Stories - patterns: "2 stories", "Single story"
        if "single story" in content_lower or "one story" in content_lower:
            result["stories"] = 1
        else:
            match = re.search(r"(\d+)\s*stor(?:y|ies)", content_lower)
            if match:
                result["stories"] = int(match.group(1))

        # List price - patterns: "$450,000", "Price: $450000"
        if result["list_price"] is None:
            match = re.search(r"\$\s*([\d,]+)(?:\s*(?:usd)?)?", content_lower)
            if match:
                try:
                    price_str = match.group(1).replace(",", "")
                    price = int(price_str)
                    # Sanity check: price should be reasonable (50k-10M)
                    if 50000 <= price <= 10000000:
                        result["list_price"] = price
                except ValueError:
                    pass

        return result

    def _extract_property_details(self, content: str) -> dict:
        """Extract core property details from page content.

        Extracts:
        - beds (bedrooms count)
        - baths (bathrooms count)
        - sqft (interior square footage)
        - lot_sqft (lot size)
        - year_built
        - property_type (Single Family, Townhouse, etc.)
        - garage_spaces
        - parking_spaces
        - pool (boolean)
        - stories (number of floors)
        - list_price

        Returns:
            Dictionary with extracted property details (None for missing fields)
        """
        # Try JSON-LD first (most reliable)
        result = self._extract_from_json_ld(content)

        # Fill gaps with regex fallback
        result = self._extract_from_regex_fallback(content, result)

        return result

    def _extract_property_features(self, content: str) -> dict:
        """Extract property features and systems from page content.

        Extracts:
        - cooling_type (Central, Evaporative, None)
        - heating_type (Gas, Electric, etc.)
        - flooring_types (Tile, Carpet, Hardwood, etc.)
        - appliances_included (list)
        - sewer_type (City, Septic)
        - water_source (City, Well)

        Returns:
            Dictionary with extracted features (None for missing fields)
        """
        result: dict = {
            "cooling_type": None,
            "heating_type": None,
            "flooring_types": None,
            "appliances_included": None,
            "sewer_type": None,
            "water_source": None,
        }

        content_lower = content.lower()

        # Cooling type
        if "central air" in content_lower or "central cooling" in content_lower:
            result["cooling_type"] = "Central"
        elif "evaporative cooling" in content_lower or "swamp cooler" in content_lower:
            result["cooling_type"] = "Evaporative"
        elif "no cooling" in content_lower or "none" in content_lower:
            result["cooling_type"] = "None"

        # Heating type
        if "gas heat" in content_lower or "natural gas" in content_lower:
            result["heating_type"] = "Gas"
        elif "electric heat" in content_lower:
            result["heating_type"] = "Electric"
        elif "heat pump" in content_lower:
            result["heating_type"] = "Heat Pump"
        elif "forced air" in content_lower:
            result["heating_type"] = "Forced Air"

        # Flooring types - collect all mentioned
        flooring_types = []
        if "tile" in content_lower:
            flooring_types.append("Tile")
        if "carpet" in content_lower:
            flooring_types.append("Carpet")
        if "hardwood" in content_lower or "wood floor" in content_lower:
            flooring_types.append("Hardwood")
        if "laminate" in content_lower:
            flooring_types.append("Laminate")
        if "vinyl" in content_lower:
            flooring_types.append("Vinyl")
        if "concrete" in content_lower:
            flooring_types.append("Concrete")
        if flooring_types:
            result["flooring_types"] = flooring_types

        # Appliances included
        appliances = []
        if "refrigerator" in content_lower or "fridge" in content_lower:
            appliances.append("Refrigerator")
        if "dishwasher" in content_lower:
            appliances.append("Dishwasher")
        if "microwave" in content_lower:
            appliances.append("Microwave")
        if "washer" in content_lower:
            appliances.append("Washer")
        if "dryer" in content_lower:
            appliances.append("Dryer")
        if "stove" in content_lower or "range" in content_lower or "oven" in content_lower:
            appliances.append("Stove/Oven")
        if appliances:
            result["appliances_included"] = appliances

        # Sewer type
        if "city sewer" in content_lower or "public sewer" in content_lower:
            result["sewer_type"] = "City"
        elif "septic" in content_lower:
            result["sewer_type"] = "Septic"

        # Water source
        if "city water" in content_lower or "public water" in content_lower:
            result["water_source"] = "City"
        elif "well" in content_lower and "water" in content_lower:
            result["water_source"] = "Well"

        return result

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract images via screenshot-only approach.

        Screenshot-only mode (E2.R1 refactoring):
        1. Discover/extract zpid if not available
        2. Navigate directly to gallery using zpid
        3. Capture lightbox screenshots of each image
        4. Return screenshot file paths

        Args:
            property: Property to extract images for

        Returns:
            List of screenshot file paths (local paths, not URLs)
        """
        logger.info("%s extracting images for: %s", self.name, property.full_address)

        # Initialize metadata
        self.last_metadata = {}

        # Get/extract zpid
        zpid = getattr(property, "zpid", None)
        if not zpid and hasattr(property, "listing_url"):
            listing_url = getattr(property, "listing_url", None)
            if listing_url:
                zpid = self._extract_zpid_from_listing_url(listing_url)
                if zpid:
                    property.zpid = zpid
                    logger.info("%s extracted zpid %s from listing_url", self.name, zpid)

        # Get browser and tab
        browser = await self._browser_pool.get_browser()
        tab = await browser.get("about:blank")

        try:
            screenshots: list[str] = []

            # ZPID Discovery if not available
            if not zpid:
                logger.info("%s discovering zpid from address", self.name)
                zpid = await self._discover_zpid_from_address(property, tab)
                if zpid:
                    property.zpid = zpid

            # Navigate to gallery (zpid-based or address-based)
            if zpid:
                gallery_success = await self._navigate_to_gallery_direct(property, tab)
                if gallery_success:
                    screenshots = await self._capture_gallery_screenshots(tab)
                    if screenshots:
                        self._set_extraction_method("screenshot")
                        logger.info("%s captured %d screenshots", self.name, len(screenshots))

            # Fallback: Navigate via address slug if no zpid
            if not screenshots:
                logger.info("%s trying address-based navigation", self.name)
                address_url = self._build_search_url(property)
                await tab.get(address_url)
                await self._human_delay()

                # Check for CAPTCHA
                if await self._check_for_captcha(tab):
                    if not await self._attempt_captcha_solve_v2(tab):
                        logger.error("%s CAPTCHA solving failed", self.name)
                        return []

                # Try screenshot capture from current page
                screenshots = await self._capture_gallery_screenshots(tab)
                if screenshots:
                    self._set_extraction_method("screenshot-address")

            # Store metadata
            self.last_metadata["screenshot_count"] = len(screenshots)
            self.last_metadata["zpid"] = zpid

            return screenshots

        except Exception as e:
            logger.error("%s extraction failed: %s", self.name, e)
            return []
        finally:
            try:
                await tab.close()
            except Exception:
                pass


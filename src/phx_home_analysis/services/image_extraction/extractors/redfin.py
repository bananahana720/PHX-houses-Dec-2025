"""Redfin image extractor using nodriver for stealth browser automation.

Redfin is a JavaScript-heavy real estate listing site with anti-bot protection
(PerimeterX). This extractor uses nodriver with stealth techniques to navigate
property pages and extract high-resolution image URLs from the DOM.
"""

import asyncio
import logging
import re

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from .stealth_base import StealthBrowserExtractor

logger = logging.getLogger(__name__)


class RedfinExtractor(StealthBrowserExtractor):
    """Extract property images from Redfin using stealth browser automation.

    Redfin's property pages use JavaScript to render image galleries and employ
    PerimeterX anti-bot protection. The extractor:
    1. Builds search URL from property address
    2. Navigates with stealth techniques and human-like delays
    3. Detects and attempts to solve Press & Hold CAPTCHAs
    4. Extracts high-res image URLs from gallery using multiple strategies
    5. Downloads images via stealth HTTP client

    Browser Context Management:
    - Uses nodriver with undetected-chromedriver techniques
    - Shared browser pool for efficiency
    - Automatic cleanup on close()

    Example:
        ```python
        async with RedfinExtractor() as extractor:
            urls = await extractor.extract_image_urls(property)
            for url in urls:
                image_data, content_type = await extractor.download_image(url)
        ```
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize Redfin extractor with stealth browser automation.

        Args:
            http_client: Shared httpx client (not used - maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction configuration (loaded from env if not provided)
        """
        super().__init__(http_client=http_client, timeout=timeout, config=config)
        logger.info("RedfinExtractor initialized with stealth configuration")

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.REDFIN
        """
        return ImageSource.REDFIN

    async def _navigate_with_stealth(self, url: str) -> uc.Tab:
        """Navigate to Redfin property via interactive search.

        Redfin's search URL doesn't automatically execute searches - it just
        shows the homepage. Instead, we need to:
        1. Visit homepage to establish session
        2. Find and interact with search input
        3. Type the property address
        4. Wait for autocomplete results
        5. Click on the first matching result
        6. Wait for property page to load

        Args:
            url: Search URL containing the property address (will extract address from it)

        Returns:
            Browser tab ready for interaction
        """
        logger.info("Redfin: warming up with homepage visit")

        # Add initial delay
        await self._human_delay()

        # Get browser
        browser = await self._browser_pool.get_browser()

        # Visit homepage to establish session/cookies
        tab = await browser.get("https://www.redfin.com")
        await asyncio.sleep(3)  # Wait for homepage to load
        logger.info("Redfin: homepage loaded")

        # Extract address from search URL: https://www.redfin.com/search?q=...
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        address = query_params.get("q", [""])[0]

        if not address:
            logger.error("Redfin: Could not extract address from search URL: %s", url)
            return tab

        logger.info("Redfin: Starting interactive search for: %s", address)

        # Find search input - try multiple selectors
        search_input = None
        search_selectors = [
            'input[name="searchInputBox"]',
            'input[type="search"]',
            '#search-box-input',
            '.search-input-box',
            'input[placeholder*="Address"]',
            'input[placeholder*="address"]',
        ]

        for selector in search_selectors:
            try:
                search_input = await tab.query_selector(selector)
                if search_input:
                    logger.info("Redfin: Found search input with selector: %s", selector)
                    break
            except Exception as e:
                logger.debug("Redfin: Selector %s failed: %s", selector, e)
                continue

        if not search_input:
            logger.error("Redfin: Could not find search input box")
            return tab

        # Click on the search input to focus it
        try:
            await search_input.click()
            await asyncio.sleep(0.5)  # Brief pause after click
            logger.info("Redfin: Clicked search input")
        except Exception as e:
            logger.warning("Redfin: Could not click search input: %s", e)

        # Type the address character by character for more realistic behavior
        try:
            await search_input.send_keys(address)
            logger.info("Redfin: Typed address: %s", address)
            # Wait longer for autocomplete dropdown to appear
            await asyncio.sleep(3)
        except Exception as e:
            logger.error("Redfin: Failed to type address: %s", e)
            return tab

        # Wait for autocomplete results to appear
        logger.info("Redfin: Waiting for autocomplete results...")

        # Try to find autocomplete results with multiple attempts
        result_clicked = False
        max_attempts = 3

        for attempt in range(max_attempts):
            logger.debug("Redfin: Autocomplete detection attempt %d/%d", attempt + 1, max_attempts)

            result_selectors = [
                '.SearchDropDown a',  # Autocomplete dropdown links
                '[data-rf-test-id="search-result"]',  # Test ID selector
                '.autosuggest-result',
                '.search-result-item',
                '[role="option"]',  # ARIA role
                '.HomeCardContainer a',  # Home card links
            ]

            for selector in result_selectors:
                try:
                    results = await tab.query_selector_all(selector)
                    if results and len(results) > 0:
                        logger.info("Redfin: Found %d autocomplete results with selector: %s",
                                  len(results), selector)

                        # Log the first few results for debugging
                        for i, result in enumerate(results[:3]):
                            try:
                                text = result.text_all if hasattr(result, 'text_all') else str(result.attrs)
                                logger.debug("  Result %d: %s", i, text[:100])
                            except Exception:
                                pass

                        # Extract street portion from address for matching
                        street_match = address.split(',')[0].lower().strip()

                        # Find result containing property address
                        matched_result = None
                        for result in results:
                            try:
                                result_text = result.text_all if hasattr(result, 'text_all') else str(result)
                                if street_match in result_text.lower():
                                    matched_result = result
                                    logger.info("Redfin: Found matching result containing: %s", street_match)
                                    break
                            except Exception:
                                continue

                        # Click matched result or fall back to first with warning
                        if matched_result:
                            await matched_result.click()
                            logger.info("Redfin: Clicked matching autocomplete result")
                            result_clicked = True
                            break
                        else:
                            logger.warning("Redfin: No exact match found, clicking first result")
                            await results[0].click()
                            logger.info("Redfin: Clicked first autocomplete result (fallback)")
                            result_clicked = True
                            break
                except Exception as e:
                    logger.debug("Redfin: Result selector %s failed: %s", selector, e)
                    continue

            if result_clicked:
                break

            # Wait a bit before trying again
            if attempt < max_attempts - 1:
                logger.debug("Redfin: No results found, waiting before retry...")
                await asyncio.sleep(2)

        if not result_clicked:
            # Try pressing Enter as fallback
            logger.warning("Redfin: Could not find autocomplete results, trying Enter key")
            try:
                # Press Enter on the search input element
                await search_input.send_keys("\n")
                logger.info("Redfin: Pressed Enter key")
            except Exception as e:
                logger.error("Redfin: Failed to press Enter: %s", e)
                return tab

        # Wait for property page to load
        await asyncio.sleep(4)
        logger.info("Redfin: Property page should be loaded")

        # Validate we landed on a property page, not city/county page
        try:
            current_url = tab.target.url if hasattr(tab, 'target') else ""
            logger.info("Redfin: Final URL: %s", current_url)

            street_match = address.split(',')[0].lower().strip()
            if '/home/' not in current_url:
                logger.warning("Redfin: Navigation may have failed - URL doesn't contain /home/: %s", current_url)
            elif street_match.replace(' ', '-') not in current_url.lower():
                logger.warning("Redfin: URL may not match property address: %s", current_url)
            else:
                logger.info("Redfin: Successfully navigated to property page")
        except Exception as e:
            logger.error("Redfin: Error validating final URL: %s", e)

        return tab

    def _build_search_url(self, property: Property) -> str:
        """Build Redfin search URL from address.

        Redfin property URLs require a property ID we don't have:
        https://www.redfin.com/{STATE}/{City}/{Street-Address-Zip}/home/{id}

        Instead, we use Redfin's search with the full address, which will
        show matching properties that we can then navigate to.

        Args:
            property: Property to search for

        Returns:
            Redfin search URL

        Example:
            >>> property = Property(street="4732 W Davis Rd", city="Glendale", state="AZ", zip_code="85306", ...)
            >>> extractor._build_search_url(property)
            "https://www.redfin.com/AZ/Glendale/filter/property-type=house,include=sold-3yr/page-1"
        """
        from urllib.parse import quote

        # Build full address for search
        full_address = f"{property.street}, {property.city}, {property.state} {property.zip_code}"

        # Redfin search URL with address query
        search_url = f"https://www.redfin.com/search?q={quote(full_address)}"

        logger.debug("Built Redfin search URL: %s", search_url)
        return search_url

    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract image URLs from Redfin property page.

        Uses nodriver's native DOM methods (like Zillow extractor) for reliable
        extraction. Strategies:
        1. All img elements - check src and srcset attributes
        2. Background images in style attributes
        3. Meta og:image tag

        All thumbnail URLs are converted to high-resolution versions.

        Args:
            tab: Browser tab with loaded Redfin property page

        Returns:
            List of unique high-resolution image URLs
        """
        logger.info("Extracting image URLs from Redfin page")
        image_urls: set[str] = set()

        try:
            # Wait for content to load (critical for nodriver)
            await asyncio.sleep(3)

            # Check page content for bot detection
            page_content = await tab.get_content()
            if page_content:
                content_lower = page_content.lower()
                content_len = len(page_content)

                # Log page title for debugging
                if "<title>" in content_lower:
                    start = content_lower.find("<title>") + 7
                    end = content_lower.find("</title>", start)
                    if end > start:
                        title = page_content[start:end].strip()
                        logger.info("Page title: %s", title)

                # Check for 404 / not found page
                if "page not found" in content_lower or "not found | redfin" in content_lower:
                    logger.warning(
                        "Property not found on Redfin (404). "
                        "The listing may not exist or URL format is incorrect."
                    )
                    return []

                # Check for bot detection (rate limiting)
                if "are you a robot" in content_lower or "ratelimited.redfin" in content_lower:
                    logger.warning(
                        "Bot detection page encountered (content: %d chars). "
                        "Redfin may be blocking the proxy IP. "
                        "Try: 1) Different proxy 2) Residential proxy 3) No proxy",
                        content_len,
                    )
                    return []
                logger.debug("Page content length: %d chars", content_len)
            else:
                logger.warning("Could not get page content")
                return []

            # Strategy 1: Get all img elements using native selector
            imgs = await tab.query_selector_all("img")
            logger.debug("Found %d img elements", len(imgs) if imgs else 0)

            if imgs:
                for img in imgs:
                    # Check srcset first (contains high-res URLs)
                    srcset = img.attrs.get("srcset", "")
                    if srcset:
                        # Parse srcset: "url1 1x, url2 2x"
                        urls_in_srcset = re.findall(r"(https://[^\s,]+)", srcset)
                        for url in urls_in_srcset:
                            if self._is_redfin_image(url):
                                image_urls.add(url)

                    # Check src attribute
                    src = img.attrs.get("src", "")
                    if src and src.startswith("http") and self._is_redfin_image(src):
                        image_urls.add(src)

            # Strategy 2: Check for background images
            divs = await tab.query_selector_all('[style*="background-image"]')
            logger.debug("Found %d elements with background-image", len(divs) if divs else 0)

            if divs:
                for div in divs:
                    style = div.attrs.get("style", "")
                    match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if match:
                        url = match.group(1)
                        if url.startswith("http") and self._is_redfin_image(url):
                            image_urls.add(url)

            # Strategy 3: Check meta og:image (with filter)
            og_images = await tab.query_selector_all('meta[property="og:image"]')
            if og_images:
                for og in og_images:
                    content = og.attrs.get("content", "")
                    if content and content.startswith("http") and self._is_redfin_image(content):
                        image_urls.add(content)

            logger.debug("Found %d raw image URLs", len(image_urls))

            if not image_urls:
                logger.warning("No Redfin images found on page")
                return []

            # Log raw URLs for debugging
            for url in image_urls:
                logger.debug("Raw Redfin URL: %s", url[:100])

            # Skip conversion for URLs that already have high-res suffix
            high_res_urls = []
            for url in image_urls:
                if "_1024" in url or "/1024x" in url:
                    # Already high-res, use as-is
                    high_res_urls.append(url)
                else:
                    high_res_urls.append(self._convert_to_highres(url))

            # Remove duplicates (may occur after conversion)
            unique_urls = sorted(set(high_res_urls))

            logger.info(
                "Extracted %d unique high-resolution URLs from Redfin",
                len(unique_urls),
            )

            return unique_urls

        except Exception as e:
            logger.error("Error extracting URLs from Redfin page: %s", e)
            # Return empty list rather than failing - some URLs is better than none
            return []

    def _is_redfin_image(self, url: str) -> bool:
        """Check if URL is a valid Redfin property image.

        Filters out non-property images like icons, logos, homepage promos,
        and app badges. Only accepts actual property listing photos.

        Args:
            url: Image URL to check

        Returns:
            True if URL appears to be a property image
        """
        url_lower = url.lower()

        # Exclude non-property images (icons, logos, badges, promos)
        exclude_patterns = [
            "icon",
            "logo",  # Catches both "logo" and "logos"
            "avatar",
            "placeholder",
            ".svg",
            "map",
            "badge",
            "flag",
            "hpwidget",  # Homepage widgets
            "homepageimage",  # Homepage promos
            "cop-assets",  # All Redfin static assets
            "equal-housing",  # Footer images
            "app-download",  # App badges
            "data:image",  # Base64 inline images
            "/images/",  # Static images folder
            "vLATEST",  # Versioned static assets
        ]
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False

        # Property photos have specific patterns in the URL
        property_patterns = [
            "/photo/",  # Property photos: /photo/68/bcsphoto/471/
            "genbcs.",  # Generated property photos: genBcs.12523471
            "/bigphoto/",  # Large photos
            "ssl.cdn-redfin.com/photo",  # CDN property photos
        ]
        for pattern in property_patterns:
            if pattern in url_lower:
                return True

        return False

    def _convert_to_highres(self, thumbnail_url: str) -> str:
        """Convert Redfin thumbnail URL to high-resolution version.

        Redfin uses size parameters in URLs that can be replaced for better quality.

        Transformations:
        - /300x200/ -> /1024x768/ (path-based size)
        - _300x200.jpg -> _1024.jpg (suffix-based size)

        Args:
            thumbnail_url: Thumbnail image URL

        Returns:
            High-resolution image URL

        Example:
            >>> extractor._convert_to_highres("https://redfin.com/photo/300x200/abc.jpg")
            "https://redfin.com/photo/1024x768/abc.jpg"
        """
        # Pattern 1: Replace /WIDTHxHEIGHT/ in path
        high_res = re.sub(r"/\d+x\d+/", "/1024x768/", thumbnail_url)

        # Pattern 2: Replace _WIDTHxHEIGHT.jpg or _WIDTH.jpg suffix
        # This handles both _300x200.jpg and ensures we get _1024.jpg
        high_res = re.sub(r"_\d+(?:x\d+)?\.jpg", "_1024.jpg", high_res)

        # Log conversion if URL changed
        if high_res != thumbnail_url:
            logger.debug("Converted thumbnail to high-res: %s -> %s", thumbnail_url, high_res)

        return high_res

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Redfin covers most US properties, but this implementation is optimized
        for Phoenix metro area where anti-bot measures are consistent.

        Supported cities:
        - Phoenix, Scottsdale, Tempe, Mesa, Chandler, Gilbert
        - Glendale, Peoria, Surprise, Avondale, Goodyear

        Args:
            property: Property to check

        Returns:
            True if property is in supported Phoenix metro cities
        """
        phoenix_cities = {
            "phoenix",
            "scottsdale",
            "tempe",
            "mesa",
            "chandler",
            "gilbert",
            "glendale",
            "peoria",
            "surprise",
            "avondale",
            "goodyear",
        }

        can_handle = property.city.lower() in phoenix_cities

        if not can_handle:
            logger.debug(
                "RedfinExtractor cannot handle city: %s (not in Phoenix metro)",
                property.city,
            )

        return can_handle

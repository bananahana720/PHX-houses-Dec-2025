"""Redfin image extractor using Playwright for browser automation.

Redfin is a JavaScript-heavy real estate listing site requiring browser automation
to access image galleries. This extractor uses Playwright to navigate property pages
and extract high-resolution image URLs from the DOM.
"""

import asyncio
import logging
import re

import httpx
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from ....domain.entities import Property
from ....domain.enums import ImageSource
from .base import (
    ExtractionError,
    ImageExtractor,
    SourceUnavailableError,
)

logger = logging.getLogger(__name__)


class RedfinExtractor(ImageExtractor):
    """Extract property images from Redfin using Playwright.

    Redfin's property pages use JavaScript to render image galleries,
    so we need browser automation to extract URLs. The extractor:
    1. Searches for property by address
    2. Navigates to property detail page
    3. Extracts high-res image URLs from gallery
    4. Downloads images via HTTP (images themselves are static)

    Browser Context Management:
    - Uses headless Chrome by default
    - Shared browser context for efficiency
    - Automatic cleanup on close()
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        headless: bool = True,
    ):
        """Initialize Redfin extractor with browser automation.

        Args:
            http_client: Shared httpx client for image downloads
            timeout: Request timeout in seconds
            headless: Run browser in headless mode
        """
        super().__init__(http_client, timeout)
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.REDFIN
        """
        return ImageSource.REDFIN

    async def _ensure_browser(self) -> BrowserContext:
        """Ensure browser context is initialized.

        Returns:
            Browser context for page operations

        Raises:
            ExtractionError: If browser initialization fails
        """
        if self._context:
            return self._context

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless
            )
            self._context = await self._browser.new_context(
                user_agent=self.USER_AGENT,
                viewport={"width": 1920, "height": 1080},
            )
            logger.info("Browser context initialized for Redfin extraction")
            return self._context

        except Exception as e:
            raise ExtractionError(f"Failed to initialize browser: {e}")

    async def close(self) -> None:
        """Close browser and HTTP client resources."""
        # Close browser context
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        # Close HTTP client if we own it
        await super().close()

        logger.info("Browser resources cleaned up")

    def _build_search_url(self, property: Property) -> str:
        """Build Redfin search URL from property address.

        Redfin search format:
        https://www.redfin.com/city/{state}/{city}/{street-address}

        Args:
            property: Property to search for

        Returns:
            Redfin search URL
        """
        # Normalize address components for URL
        street_slug = re.sub(r"[^\w\s-]", "", property.street.lower())
        street_slug = re.sub(r"[-\s]+", "-", street_slug).strip("-")

        city_slug = property.city.lower().replace(" ", "-")
        state_slug = property.state.lower()

        # Build search URL
        base_url = self.source.base_url
        search_url = f"{base_url}/city/{state_slug}/{city_slug}/{street_slug}"

        logger.debug(f"Built Redfin search URL: {search_url}")
        return search_url

    async def _find_property_page(self, page: Page, property: Property) -> str | None:
        """Navigate to property page from search results.

        Args:
            page: Playwright page object
            property: Property to find

        Returns:
            Property page URL if found, None otherwise

        Raises:
            SourceUnavailableError: If Redfin is down or rate limiting
        """
        search_url = self._build_search_url(property)

        try:
            # Navigate to search results
            response = await page.goto(search_url, wait_until="networkidle", timeout=30000)

            if response and response.status == 429:
                raise SourceUnavailableError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=60,
                )

            if response and response.status >= 500:
                raise SourceUnavailableError(
                    self.source,
                    f"Server error: {response.status}",
                )

            # Wait for page to load
            await asyncio.sleep(2)

            # Check if we landed directly on property page (best case)
            current_url = page.url
            if "/home/" in current_url:
                logger.info(f"Landed directly on property page: {current_url}")
                return current_url

            # Otherwise, search for property link in results
            # Redfin uses data-url attributes on property cards
            property_links = await page.locator('[data-url*="/home/"]').all()

            if not property_links:
                logger.warning(f"No property links found for {property.full_address}")
                return None

            # Click first matching property
            first_link = property_links[0]
            await first_link.click()
            await page.wait_for_load_state("networkidle", timeout=30000)

            property_url = page.url
            logger.info(f"Navigated to property page: {property_url}")
            return property_url

        except asyncio.TimeoutError:
            logger.warning(f"Timeout finding property page for {property.full_address}")
            return None

    async def _extract_gallery_urls(self, page: Page) -> list[str]:
        """Extract high-resolution image URLs from Redfin gallery.

        Redfin stores image URLs in various places:
        - Meta tags (og:image)
        - JSON-LD structured data
        - Gallery thumbnails with data attributes
        - JavaScript variables

        Args:
            page: Playwright page on property detail page

        Returns:
            List of high-resolution image URLs
        """
        urls: set[str] = set()

        try:
            # Strategy 1: Extract from meta tags
            og_image = await page.locator('meta[property="og:image"]').get_attribute(
                "content"
            )
            if og_image:
                urls.add(og_image)
                logger.debug(f"Found og:image: {og_image}")

            # Strategy 2: Extract from JSON-LD structured data
            json_ld_scripts = await page.locator('script[type="application/ld+json"]').all()
            for script in json_ld_scripts:
                content = await script.inner_text()
                # Extract image URLs from JSON (simple regex approach)
                image_urls = re.findall(r'"image":\s*"([^"]+)"', content)
                urls.update(image_urls)
                logger.debug(f"Found {len(image_urls)} URLs in JSON-LD")

            # Strategy 3: Extract from gallery images
            # Redfin uses various selectors for gallery images
            gallery_selectors = [
                'img[class*="gallery"]',
                'img[class*="photo"]',
                'div[class*="MediaCarousel"] img',
                'button[class*="photo"] img',
            ]

            for selector in gallery_selectors:
                images = await page.locator(selector).all()
                for img in images:
                    src = await img.get_attribute("src")
                    if src and "redfin" in src and not src.endswith(".svg"):
                        # Convert thumbnail URL to high-res
                        high_res_url = self._convert_to_highres(src)
                        urls.add(high_res_url)

            # Strategy 4: Look for data attributes with full-size URLs
            data_url_elements = await page.locator('[data-url*=".jpg"]').all()
            data_url_elements.extend(await page.locator('[data-url*=".jpeg"]').all())
            data_url_elements.extend(await page.locator('[data-url*=".png"]').all())

            for element in data_url_elements:
                data_url = await element.get_attribute("data-url")
                if data_url:
                    urls.add(data_url)

            logger.info(f"Extracted {len(urls)} unique image URLs from Redfin")
            return sorted(urls)

        except Exception as e:
            logger.error(f"Error extracting gallery URLs: {e}")
            return []

    def _convert_to_highres(self, thumbnail_url: str) -> str:
        """Convert Redfin thumbnail URL to high-resolution version.

        Redfin uses size parameters in URLs (e.g., /300x200/).
        Replace with larger dimensions for better quality.

        Args:
            thumbnail_url: Thumbnail image URL

        Returns:
            High-resolution image URL
        """
        # Redfin URL pattern: .../300x200/...jpg
        # Replace with larger size: 1024x768 or max available
        high_res = re.sub(r"/\d+x\d+/", "/1024x768/", thumbnail_url)

        # Some Redfin URLs use 'genImageId' with size suffix
        high_res = re.sub(r"(_\d+x\d+)?\.jpg", "_1024.jpg", high_res)

        return high_res

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract all image URLs for a property from Redfin.

        Args:
            property: Property entity to find images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If Redfin is down or rate limited
            ExtractionError: For other extraction failures
        """
        context = await self._ensure_browser()
        page = await context.new_page()

        try:
            # Find property page
            property_url = await self._find_property_page(page, property)

            if not property_url:
                logger.warning(f"Could not find Redfin listing for {property.full_address}")
                return []

            # Extract gallery URLs
            urls = await self._extract_gallery_urls(page)

            # Apply rate limiting
            await self._rate_limit()

            return urls

        except SourceUnavailableError:
            raise

        except Exception as e:
            raise ExtractionError(f"Failed to extract Redfin images: {e}")

        finally:
            await page.close()

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image from URL.

        Uses standard HTTP client since Redfin images are static once
        we have the URL (no JavaScript needed).

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: If download fails
        """
        return await self._download_with_retry(url)

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Redfin covers most US properties, but primarily serves major metros.
        For Phoenix area, should be available.

        Args:
            property: Property to check

        Returns:
            True for Phoenix area properties
        """
        # Redfin covers Phoenix metro area
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

        return property.city.lower() in phoenix_cities

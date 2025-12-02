"""Zillow image extractor using Playwright for browser automation.

Zillow is a JavaScript-heavy site requiring browser automation to properly
load images from their dynamic galleries and carousels.
"""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

from playwright.async_api import Browser, Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from ....domain.entities import Property
from ....domain.enums import ImageSource
from .base import (
    ExtractionError,
    ImageDownloadError,
    ImageExtractor,
    SourceUnavailableError,
)

logger = logging.getLogger(__name__)


class ZillowExtractor(ImageExtractor):
    """Zillow image extractor using Playwright browser automation.

    Zillow requires browser automation because:
    - Heavy JavaScript rendering for image galleries
    - Lazy-loaded images in carousels
    - Dynamic content based on viewport/interactions
    - Anti-scraping detection for simple HTTP requests

    Extracts high-resolution images from property detail pages.
    """

    def __init__(
        self,
        http_client: Optional[object] = None,
        timeout: float = 30.0,
        headless: bool = True,
    ):
        """Initialize Zillow extractor.

        Args:
            http_client: Shared httpx client for image downloads
            timeout: Request timeout in seconds
            headless: Run browser in headless mode (no visible window)
        """
        super().__init__(http_client, timeout)
        self._headless = headless
        self._browser: Optional[Browser] = None
        self._playwright = None

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.ZILLOW
        """
        return ImageSource.ZILLOW

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is initialized and return it.

        Returns:
            Active Playwright browser instance

        Raises:
            ExtractionError: If browser initialization fails
        """
        if self._browser is not None:
            return self._browser

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
            logger.info(f"Initialized Playwright browser (headless={self._headless})")
            return self._browser
        except Exception as e:
            raise ExtractionError(f"Failed to initialize browser: {e}")

    async def close(self) -> None:
        """Close browser and HTTP client."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.debug("Closed Playwright browser")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        await super().close()

    def _build_search_url(self, property: Property) -> str:
        """Build Zillow search URL from property address.

        Args:
            property: Property entity with address

        Returns:
            Zillow search URL for the property
        """
        # Zillow search format: /homes/{street}-{city}-{state}-{zip}_rb/
        # URL-encode the address components
        street = quote_plus(property.street.replace(" ", "-"))
        city = quote_plus(property.city.replace(" ", "-"))
        state = property.state
        zip_code = property.zip_code

        # Construct search URL
        search_path = f"{street}-{city}-{state}-{zip_code}_rb"
        return f"{self.source.base_url}/homes/{search_path}/"

    async def _extract_urls_from_page(self, page: Page) -> list[str]:
        """Extract high-resolution image URLs from Zillow page.

        Handles:
        - Photo carousel/gallery patterns
        - Lazy-loaded images
        - High-res vs thumbnail URLs

        Args:
            page: Playwright page object

        Returns:
            List of high-resolution image URLs

        Raises:
            ExtractionError: If image extraction fails
        """
        try:
            # Wait for photo gallery to load (Zillow uses various selectors)
            # Try multiple common selectors for the photo viewer
            gallery_selectors = [
                '[data-test="hdp-gallery-photo"]',  # Main gallery photos
                'picture[data-test="media-photo"] img',  # Media carousel
                '.media-stream img',  # Stream view
                'img[class*="photo"]',  # Generic photo class
            ]

            image_urls: set[str] = set()

            # Wait for any gallery element to appear
            try:
                await page.wait_for_selector(
                    ", ".join(gallery_selectors),
                    timeout=10000,
                )
            except PlaywrightTimeoutError:
                logger.warning("No gallery elements found on Zillow page")
                return []

            # Extract URLs from all matching image elements
            for selector in gallery_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    # Try srcset first (contains high-res URLs)
                    srcset = await element.get_attribute("srcset")
                    if srcset:
                        # Parse srcset: "url1 1x, url2 2x, url3 3x"
                        # Extract highest resolution URL
                        urls_in_srcset = re.findall(r'(https://[^\s,]+)', srcset)
                        if urls_in_srcset:
                            # Take last URL (usually highest res)
                            image_urls.add(urls_in_srcset[-1])
                            continue

                    # Fallback to src attribute
                    src = await element.get_attribute("src")
                    if src and src.startswith("http"):
                        # Filter out placeholder/loading images
                        if "loading" not in src.lower() and "placeholder" not in src.lower():
                            image_urls.add(src)

            # Convert set to list and filter for quality
            filtered_urls = [
                url for url in image_urls
                if self._is_high_quality_url(url)
            ]

            logger.info(f"Extracted {len(filtered_urls)} high-quality image URLs from Zillow")
            return filtered_urls

        except Exception as e:
            raise ExtractionError(f"Failed to extract image URLs from page: {e}")

    def _is_high_quality_url(self, url: str) -> bool:
        """Check if URL points to high-quality image.

        Filters out:
        - Thumbnails (contain 'thumb' or 'small')
        - Placeholder images
        - Map tiles
        - Icon images

        Args:
            url: Image URL to check

        Returns:
            True if URL appears to be high-quality property photo
        """
        url_lower = url.lower()

        # Exclude patterns
        exclude_patterns = [
            "thumb",
            "small",
            "icon",
            "logo",
            "map",
            "placeholder",
            "loading",
            "avatar",
        ]

        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False

        # Include patterns (Zillow-specific CDN paths)
        include_patterns = [
            "photos.zillowstatic.com",
            "ssl.cdn-redfin.com",
            "uncrate",  # High-res image indicator
        ]

        for pattern in include_patterns:
            if pattern in url_lower:
                return True

        # Default: accept if it's an image URL
        return any(ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".webp"])

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract all image URLs for a property from Zillow.

        Args:
            property: Property entity to find images for

        Returns:
            List of high-resolution image URLs discovered

        Raises:
            SourceUnavailableError: If Zillow is down or blocks requests
            ExtractionError: For other extraction failures
        """
        browser = await self._ensure_browser()
        page: Optional[Page] = None

        try:
            # Create new page context
            page = await browser.new_page()

            # Set user agent to avoid detection
            await page.set_extra_http_headers({
                "User-Agent": self.USER_AGENT,
            })

            # Build search URL and navigate
            search_url = self._build_search_url(property)
            logger.info(f"Navigating to Zillow: {search_url}")

            # Navigate and wait for network idle
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
            except PlaywrightTimeoutError:
                # Page may load but not reach network idle - continue anyway
                logger.warning("Page did not reach networkidle, continuing anyway")

            # Check if we hit a CAPTCHA or block page
            content = await page.content()
            if "captcha" in content.lower() or "blocked" in content.lower():
                raise SourceUnavailableError(
                    self.source,
                    "Zillow CAPTCHA or block page detected",
                    retry_after=300,  # 5 minutes
                )

            # Apply rate limiting
            await self._rate_limit()

            # Extract image URLs from page
            image_urls = await self._extract_urls_from_page(page)

            if not image_urls:
                logger.warning(f"No images found for {property.full_address} on Zillow")

            return image_urls

        except SourceUnavailableError:
            raise

        except PlaywrightTimeoutError as e:
            raise SourceUnavailableError(
                self.source,
                f"Page load timeout: {e}",
                retry_after=60,
            )

        except Exception as e:
            raise ExtractionError(f"Zillow extraction failed: {e}")

        finally:
            if page:
                await page.close()

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image from URL using httpx.

        Image URLs from Zillow are static CDN URLs, so we can use
        simple HTTP requests rather than browser automation.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: If download fails
        """
        try:
            return await self._download_with_retry(url)
        except Exception as e:
            raise ImageDownloadError(
                url,
                None,
                f"Failed to download Zillow image: {e}",
            )

"""Zillow image extractor using nodriver for stealth browser automation.

Zillow is a JavaScript-heavy site with anti-bot protection requiring stealth
browser automation to properly load images from dynamic galleries and carousels.
"""

import asyncio
import logging
import re
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

    Example:
        ```python
        async with ZillowExtractor() as extractor:
            urls = await extractor.extract_image_urls(property)
            for url in urls:
                image_bytes, content_type = await extractor.download_image(url)
        ```
    """

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

    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract high-resolution image URLs from loaded Zillow page.

        Uses nodriver's native element selection methods to extract all image URLs from:
        - srcset attributes (highest resolution)
        - img src attributes
        - background-image CSS properties

        Filters results through _is_high_quality_url() to exclude thumbnails,
        icons, placeholders, and other low-quality images.

        Args:
            tab: Browser tab with loaded Zillow property page

        Returns:
            List of high-resolution image URLs

        Raises:
            ExtractionError: If element selection or URL extraction fails
        """
        logger.info("%s extracting image URLs from page", self.name)
        image_urls: set[str] = set()

        try:
            # Wait for content to load
            await asyncio.sleep(2)

            # Strategy 1: Get all img elements using native selector
            imgs = await tab.query_selector_all("img")
            logger.debug("%s found %d img elements", self.name, len(imgs))

            for img in imgs:
                # Check srcset first (contains high-res URLs)
                srcset = img.attrs.get("srcset", "")
                if srcset:
                    # Parse srcset: "url1 1x, url2 2x"
                    urls_in_srcset = re.findall(r"(https://[^\s,]+)", srcset)
                    for url in urls_in_srcset:
                        image_urls.add(url)

                # Fallback to src
                src = img.attrs.get("src", "") or getattr(img, "src", "")
                if src and src.startswith("http"):
                    image_urls.add(src)

            # Strategy 2: Check for background images in divs
            divs = await tab.query_selector_all('[style*="background-image"]')
            logger.debug("%s found %d elements with background-image", self.name, len(divs))

            for div in divs:
                style = div.attrs.get("style", "")
                match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                if match:
                    url = match.group(1)
                    if url.startswith("http"):
                        image_urls.add(url)

            logger.debug(
                "%s found %d raw URLs from page",
                self.name,
                len(image_urls),
            )

            # Filter through quality check
            if not image_urls:
                logger.warning("%s no image URLs found on page", self.name)
                return []

            # Filter for high-quality URLs only
            filtered_urls = [url for url in image_urls if self._is_high_quality_url(url)]

            logger.info(
                "%s filtered to %d high-quality URLs from %d total",
                self.name,
                len(filtered_urls),
                len(image_urls),
            )

            return filtered_urls

        except Exception as e:
            logger.error("%s failed to extract URLs: %s", self.name, e)
            # Return empty list rather than raising - some extractions may find nothing
            return []

    def _is_high_quality_url(self, url: str) -> bool:
        """Check if URL points to high-quality property image.

        Filters out low-quality images by:
        1. Excluding URLs with quality-indicating keywords (thumbnails, icons, etc.)
        2. Including URLs from known high-quality CDN domains
        3. Accepting URLs with standard image extensions

        Args:
            url: Image URL to validate

        Returns:
            True if URL appears to be high-quality property photo, False otherwise

        Example exclusions:
            - "thumb_320.jpg" -> False (thumbnail)
            - "map_tile.png" -> False (map image)
            - "loading.gif" -> False (placeholder)

        Example inclusions:
            - "photos.zillowstatic.com/...uncrate.jpg" -> True (Zillow CDN)
            - "ssl.cdn-redfin.com/photo/123.jpg" -> True (Redfin CDN)
        """
        url_lower = url.lower()

        # Exclude low-quality patterns
        exclude_patterns = [
            "thumb",  # Thumbnails
            "small",  # Small-sized images
            "icon",  # Icon images
            "logo",  # Logos
            "map",  # Map tiles
            "placeholder",  # Placeholder images
            "loading",  # Loading spinners
            "avatar",  # User avatars
        ]

        for pattern in exclude_patterns:
            if pattern in url_lower:
                logger.debug(
                    "%s excluding URL (contains '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return False

        # Include high-quality CDN patterns
        include_patterns = [
            "photos.zillowstatic.com",  # Zillow CDN
            "ssl.cdn-redfin.com",  # Redfin CDN (cross-listed properties)
            "uncrate",  # Zillow high-res indicator
        ]

        for pattern in include_patterns:
            if pattern in url_lower:
                logger.debug(
                    "%s including URL (matches '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return True

        # Default: accept if it has a standard image extension
        has_image_ext = any(
            ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".webp"]
        )

        if has_image_ext:
            logger.debug("%s including URL (has image extension): %s", self.name, url[:80])
        else:
            logger.debug("%s excluding URL (no image extension): %s", self.name, url[:80])

        return has_image_ext

"""Phoenix MLS image extractor implementation.

Extracts property images from phoenixmlssearch.com using BeautifulSoup
for HTML parsing. Handles search by address and gallery image extraction.
"""

import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from ....domain.entities import Property
from ....domain.enums import ImageSource
from .base import (
    ExtractionError,
    ImageExtractor,
    SourceUnavailableError,
)

logger = logging.getLogger(__name__)


# Phoenix metro area cities that Phoenix MLS covers
PHOENIX_METRO_CITIES = {
    "anthem",
    "apache junction",
    "avondale",
    "buckeye",
    "carefree",
    "casa grande",
    "cave creek",
    "chandler",
    "el mirage",
    "fountain hills",
    "gilbert",
    "glendale",
    "gold canyon",
    "goodyear",
    "laveen",
    "litchfield park",
    "maricopa",
    "mesa",
    "new river",
    "paradise valley",
    "peoria",
    "phoenix",
    "queen creek",
    "rio verde",
    "san tan valley",
    "scottsdale",
    "sun city",
    "sun city west",
    "sun lakes",
    "surprise",
    "tempe",
    "tolleson",
    "wickenburg",
}


class PhoenixMLSExtractor(ImageExtractor):
    """Extract property images from Phoenix MLS Search website.

    Uses BeautifulSoup to parse HTML and extract image URLs from property
    listings. Searches by address to find property pages, then extracts
    gallery images.

    Note: This implementation provides a reasonable skeleton based on common
    MLS website patterns. May require refinement based on actual site structure.
    """

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.PHOENIX_MLS
        """
        return ImageSource.PHOENIX_MLS

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Phoenix MLS only covers Phoenix metropolitan area cities.

        Args:
            property: Property to check

        Returns:
            True if property is in Phoenix metro area
        """
        city_normalized = property.city.lower().strip()
        return city_normalized in PHOENIX_METRO_CITIES

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract all image URLs for a property from Phoenix MLS.

        Strategy:
        1. Search for property by address
        2. Find property listing page URL
        3. Parse listing page for image gallery
        4. Extract all image URLs from gallery

        Args:
            property: Property entity to find images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If site is down or rate limited
            ExtractionError: If property not found or parsing fails
        """
        try:
            # Step 1: Search for property
            listing_url = await self._search_property(property)

            if not listing_url:
                logger.warning(
                    f"Property not found on {self.name}: {property.full_address}"
                )
                return []

            # Step 2: Fetch listing page
            await self._rate_limit()
            listing_html = await self._fetch_listing_page(listing_url)

            # Step 3: Extract image URLs
            image_urls = self._parse_image_gallery(listing_html, listing_url)

            logger.info(
                f"Extracted {len(image_urls)} images from {self.name} for {property.short_address}"
            )
            return image_urls

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise SourceUnavailableError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=int(e.response.headers.get("Retry-After", 60)),
                ) from e
            elif e.response.status_code >= 500:
                raise SourceUnavailableError(
                    self.source,
                    f"Server error: {e.response.status_code}",
                ) from e
            else:
                raise ExtractionError(
                    f"HTTP error {e.response.status_code} accessing {self.name}"
                ) from e

        except httpx.TimeoutException as e:
            raise SourceUnavailableError(
                self.source,
                "Request timeout",
            ) from e

        except Exception as e:
            logger.exception(f"Unexpected error extracting from {self.name}")
            raise ExtractionError(f"Failed to extract images: {str(e)}") from e

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image and return (data, content_type).

        Uses standard HTTP download with retry logic from base class.

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
            logger.error(f"Failed to download image from {url}: {e}")
            raise

    async def _search_property(self, property: Property) -> str | None:
        """Search for property on Phoenix MLS and return listing URL.

        Phoenix MLS search patterns (common approaches):
        - City-specific search pages (e.g., /phoenix-homes/)
        - Search form with address input
        - Direct listing URLs with MLS numbers

        This implementation tries multiple approaches to find the property.

        Args:
            property: Property to search for

        Returns:
            Listing page URL if found, None otherwise
        """
        # Try city-specific search page
        city_slug = property.city.lower().replace(" ", "-")
        search_url = f"{self.source.base_url}/{city_slug}-homes/"

        try:
            response = await self._http_client.get(search_url)

            if response.status_code == 404:
                # City page doesn't exist, try alternative search
                logger.debug(f"City page not found: {search_url}")
                return await self._advanced_search(property)

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Look for property listings matching the address
            listing_url = self._find_matching_listing(soup, property)

            if listing_url:
                return listing_url

            # If not found on first page, try advanced search
            return await self._advanced_search(property)

        except httpx.HTTPError as e:
            logger.warning(f"Error searching for property: {e}")
            return None

    async def _advanced_search(self, property: Property) -> str | None:
        """Perform advanced search for property.

        Common MLS sites have search endpoints that accept address parameters.
        This is a placeholder for more sophisticated search logic.

        Args:
            property: Property to search for

        Returns:
            Listing page URL if found, None otherwise
        """
        # Phoenix MLS may have a search endpoint - this would need to be
        # discovered through site inspection
        logger.debug(
            f"Advanced search not yet implemented for {property.full_address}"
        )
        return None

    def _find_matching_listing(
        self, soup: BeautifulSoup, property: Property
    ) -> str | None:
        """Find listing URL matching the property address in search results.

        Common patterns:
        - <a> tags with property addresses in text or data attributes
        - Property cards/tiles with address information
        - Links containing street names or MLS numbers

        Args:
            soup: BeautifulSoup object of search results page
            property: Property to match

        Returns:
            Absolute URL to listing page if found, None otherwise
        """
        # Normalize street name for matching
        street_normalized = property.street.lower()

        # Extract street number and name (e.g., "1234 Main St" -> "1234", "main")
        street_match = re.match(r"(\d+)\s+(.+)", street_normalized)
        if not street_match:
            logger.warning(f"Could not parse street address: {property.street}")
            return None

        street_number = street_match.group(1)
        street_name_parts = street_match.group(2).split()[:2]  # First 2 words

        # Common selectors for MLS listing links
        # This is a generic pattern - would need refinement based on actual site
        for link in soup.find_all("a", href=True):
            link_text = link.get_text(strip=True).lower()
            href_attr = link.get("href")

            # href can be None or a list in BeautifulSoup
            if not href_attr:
                continue
            if isinstance(href_attr, list):
                href = href_attr[0] if href_attr else ""
            else:
                href = str(href_attr)
            if not href:
                continue

            # Check if link text contains street number and name
            if street_number in link_text and any(
                part in link_text for part in street_name_parts
            ):
                # Convert relative URL to absolute
                absolute_url = urljoin(self.source.base_url, href)
                logger.debug(f"Found matching listing: {absolute_url}")
                return absolute_url

        logger.debug(f"No matching listing found for {property.street}")
        return None

    async def _fetch_listing_page(self, url: str) -> str:
        """Fetch HTML content of listing page.

        Args:
            url: Listing page URL

        Returns:
            HTML content as string

        Raises:
            httpx.HTTPError: If request fails
        """
        response = await self._http_client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_image_gallery(self, html: str, base_url: str) -> list[str]:
        """Parse image gallery from listing page HTML.

        Common MLS image gallery patterns:
        - <img> tags in gallery containers (class/id with "gallery", "photos", etc.)
        - Data attributes with image URLs (data-src, data-image-url)
        - JavaScript arrays with image URLs in <script> tags
        - Thumbnail links (<a> tags pointing to full-size images)

        Args:
            html: HTML content of listing page
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute image URLs
        """
        soup = BeautifulSoup(html, "html.parser")
        image_urls: list[str] = []
        seen_urls: set[str] = set()

        # Pattern 1: Look for common gallery containers
        gallery_containers = soup.find_all(
            ["div", "section"],
            class_=re.compile(r"(gallery|photos|images|slideshow)", re.IGNORECASE),
        )

        for container in gallery_containers:
            # Find all images in container
            for img in container.find_all("img"):
                url = self._extract_image_url(img, base_url)
                if url and url not in seen_urls:
                    image_urls.append(url)
                    seen_urls.add(url)

        # Pattern 2: Look for image links (thumbnail -> full size)
        for link in soup.find_all("a", href=True):
            href_attr = link.get("href")
            # href can be None or a list in BeautifulSoup
            if not href_attr:
                continue
            if isinstance(href_attr, list):
                href = href_attr[0] if href_attr else ""
            else:
                href = str(href_attr)
            if not href:
                continue
            # Check if href points to an image file
            if self._is_image_url(href):
                absolute_url = urljoin(base_url, href)
                if absolute_url not in seen_urls:
                    image_urls.append(absolute_url)
                    seen_urls.add(absolute_url)

        # Pattern 3: Look for script tags with image arrays
        # Many MLS sites embed image URLs in JavaScript
        for script in soup.find_all("script"):
            script_text = script.string
            if script_text:
                js_image_urls = self._extract_urls_from_script(script_text)
                for url in js_image_urls:
                    absolute_url = urljoin(base_url, url)
                    if absolute_url not in seen_urls:
                        image_urls.append(absolute_url)
                        seen_urls.add(absolute_url)

        logger.debug(f"Parsed {len(image_urls)} image URLs from gallery")
        return image_urls

    def _extract_image_url(self, img_tag: object, base_url: str) -> str | None:
        """Extract image URL from <img> tag.

        Checks multiple attributes: src, data-src, data-original, data-lazy-src.

        Args:
            img_tag: BeautifulSoup <img> tag
            base_url: Base URL for resolving relative URLs

        Returns:
            Absolute image URL or None
        """
        # img_tag is a BeautifulSoup Tag object - type as Any for attribute access
        from typing import Any
        tag: Any = img_tag

        # Try common image URL attributes
        for attr in ["src", "data-src", "data-original", "data-lazy-src", "data-url"]:
            url = tag.get(attr)
            if url:
                # Skip placeholder/loading images
                if "placeholder" in str(url).lower() or "loading" in str(url).lower():
                    continue
                # Skip data URIs
                if str(url).startswith("data:"):
                    continue
                # Convert to absolute URL
                return str(urljoin(base_url, str(url)))
        return None

    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image file.

        Args:
            url: URL to check

        Returns:
            True if URL has image file extension
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in image_extensions)

    def _extract_urls_from_script(self, script_text: str) -> list[str]:
        """Extract image URLs from JavaScript code.

        Looks for common patterns:
        - Array literals: ["url1.jpg", "url2.jpg"]
        - String literals with image extensions

        Args:
            script_text: JavaScript code as string

        Returns:
            List of image URLs found
        """
        urls: list[str] = []

        # Pattern: URLs in quotes with image extensions
        url_pattern = r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp)(?:\?[^"\']*)?)["\']'
        matches = re.findall(url_pattern, script_text, re.IGNORECASE)

        for match in matches:
            # Skip very short URLs (likely not real images)
            if len(match) > 10:
                urls.append(match)

        return urls

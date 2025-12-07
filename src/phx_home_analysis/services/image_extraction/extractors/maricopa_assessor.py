"""Maricopa County Assessor image extractor.

Extracts property images from the Maricopa County Assessor's Office API.
Requires API token for authentication.
"""

import logging
import os
from urllib.parse import quote

import httpx

from ....domain.entities import Property
from ....domain.enums import ImageSource
from .base import (
    AuthenticationError,
    ImageExtractor,
    RateLimitError,
    SourceUnavailableError,
)

logger = logging.getLogger(__name__)


# Maricopa County cities for can_handle validation
MARICOPA_COUNTY_CITIES = {
    "phoenix",
    "scottsdale",
    "tempe",
    "mesa",
    "chandler",
    "glendale",
    "peoria",
    "gilbert",
    "surprise",
    "avondale",
    "goodyear",
    "buckeye",
    "el mirage",
    "tolleson",
    "litchfield park",
    "youngtown",
    "guadalupe",
    "fountain hills",
    "paradise valley",
    "cave creek",
    "carefree",
    "queen creek",
    "anthem",
    "sun city",
    "sun city west",
}


class MaricopaAssessorExtractor(ImageExtractor):
    """Extractor for Maricopa County Assessor property images.

    Uses the Maricopa County Assessor API to:
    1. Search by full address to find APN (Assessor Parcel Number)
    2. Retrieve parcel details by APN
    3. Extract image URLs from parcel data
    4. Download images with authentication

    Requires MARICOPA_ASSESSOR_TOKEN environment variable or token passed to constructor.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        token: str | None = None,
    ):
        """Initialize Maricopa Assessor extractor.

        Args:
            http_client: Shared httpx client (created if not provided)
            timeout: Request timeout in seconds
            token: API token (defaults to MARICOPA_ASSESSOR_TOKEN env var)
        """
        super().__init__(http_client, timeout)
        self._token = token or os.getenv("MARICOPA_ASSESSOR_TOKEN")

        if not self._token:
            logger.warning("MARICOPA_ASSESSOR_TOKEN not set - extractor will fail authentication")

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.MARICOPA_ASSESSOR
        """
        return ImageSource.MARICOPA_ASSESSOR

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Only handles properties in Maricopa County, Arizona cities.

        Args:
            property: Property to check

        Returns:
            True if property is in Maricopa County, AZ
        """
        if property.state.upper() != "AZ":
            return False

        city_normalized = property.city.lower().strip()
        return city_normalized in MARICOPA_COUNTY_CITIES

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract all image URLs for a property from Maricopa Assessor.

        Process:
        1. Search by full_address to get APN
        2. Get parcel details by APN
        3. Extract image URLs from parcel data

        Args:
            property: Property entity to find images for

        Returns:
            List of image URLs discovered

        Raises:
            AuthenticationError: If API token is missing/invalid
            SourceUnavailableError: If API is down or rate limited
            ExtractionError: For other extraction failures
        """
        if not self._token:
            raise AuthenticationError(
                self.source,
                "MARICOPA_ASSESSOR_TOKEN environment variable not set",
            )

        # Rate limiting before search
        await self._rate_limit()

        # Step 1: Search by address to get APN
        # Note: Maricopa API requires street-only format, not full address with city/state/zip
        apn = await self._search_for_apn(property.street)
        if not apn:
            logger.info(f"No APN found for {property.street}")
            return []

        # Rate limiting before parcel lookup
        await self._rate_limit()

        # Step 2: Get parcel details
        parcel_data = await self._get_parcel_details(apn)
        if not parcel_data:
            logger.info(f"No parcel data found for APN {apn}")
            return []

        # Step 3: Extract image URLs from parcel data
        image_urls = self._extract_image_urls_from_parcel(parcel_data)

        logger.info(f"Found {len(image_urls)} images for {property.short_address} (APN: {apn})")
        return image_urls

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image with Authorization header.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            AuthenticationError: If API token is missing/invalid
            ImageDownloadError: If download fails
        """
        if not self._token:
            raise AuthenticationError(
                self.source,
                "MARICOPA_ASSESSOR_TOKEN environment variable not set",
            )

        headers = {"AUTHORIZATION": self._token}

        # Apply rate limiting before download
        await self._rate_limit()

        return await self._download_with_retry(url, headers=headers)

    async def _search_for_apn(self, address: str) -> str | None:
        """Search for property by address to get APN.

        Args:
            address: Full property address

        Returns:
            APN if found, None otherwise

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            SourceUnavailableError: If API is unavailable
        """
        query_encoded = quote(address)
        url = f"{self.source.base_url}/search/property/?q={query_encoded}"

        headers = {k: v for k, v in {"AUTHORIZATION": self._token}.items() if v is not None}

        try:
            response = await self._http_client.get(url, headers=headers)

            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError(
                    self.source,
                    f"Authentication failed: {response.status_code}",
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=retry_after,
                )

            response.raise_for_status()

            data = response.json()

            # Extract APN from search results
            # Response structure: {"TOTAL": N, "Results": [...]}
            results = data.get("Results", [])

            if not results:
                return None

            # Take first result's APN
            first_result = results[0]
            apn = first_result.get("APN") or first_result.get("apn")

            from typing import cast

            return cast(str | None, apn)

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise AuthenticationError(
                    self.source,
                    f"Authentication failed: {e.response.status_code}",
                )
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=retry_after,
                )
            else:
                raise SourceUnavailableError(
                    self.source,
                    f"Search failed: {e.response.status_code}",
                )

        except httpx.TimeoutException:
            raise SourceUnavailableError(
                self.source,
                "Request timeout during search",
            )

        except httpx.NetworkError as e:
            raise SourceUnavailableError(
                self.source,
                f"Network error during search: {e}",
            )

    async def _get_parcel_details(self, apn: str) -> dict | None:
        """Get parcel details by APN.

        Args:
            apn: Assessor Parcel Number

        Returns:
            Parcel data dictionary if found, None otherwise

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            SourceUnavailableError: If API is unavailable
        """
        # APN can be formatted with or without spaces/dashes/dots
        url = f"{self.source.base_url}/parcel/{apn}"

        headers = {k: v for k, v in {"AUTHORIZATION": self._token}.items() if v is not None}

        try:
            response = await self._http_client.get(url, headers=headers)

            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError(
                    self.source,
                    f"Authentication failed: {response.status_code}",
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=retry_after,
                )

            if response.status_code == 404:
                logger.warning(f"Parcel not found for APN {apn}")
                return None

            response.raise_for_status()

            from typing import Any, cast

            return cast(dict[Any, Any] | None, response.json())

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise AuthenticationError(
                    self.source,
                    f"Authentication failed: {e.response.status_code}",
                )
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    self.source,
                    "Rate limit exceeded",
                    retry_after=retry_after,
                )
            elif e.response.status_code == 404:
                return None
            else:
                raise SourceUnavailableError(
                    self.source,
                    f"Parcel lookup failed: {e.response.status_code}",
                )

        except httpx.TimeoutException:
            raise SourceUnavailableError(
                self.source,
                "Request timeout during parcel lookup",
            )

        except httpx.NetworkError as e:
            raise SourceUnavailableError(
                self.source,
                f"Network error during parcel lookup: {e}",
            )

    def _extract_image_urls_from_parcel(self, parcel_data: dict) -> list[str]:
        """Extract image URLs from parcel data.

        Looks for image URLs in various fields of the parcel response.
        Common fields: images, photos, photo_urls, image_urls, etc.

        Args:
            parcel_data: Parcel details dictionary from API

        Returns:
            List of image URLs found
        """
        image_urls = []

        # Check common image fields
        for field in ["images", "photos", "photo_urls", "image_urls", "img_urls"]:
            if field in parcel_data:
                value = parcel_data[field]
                if isinstance(value, list):
                    image_urls.extend(value)
                elif isinstance(value, str):
                    image_urls.append(value)

        # Check for nested image data
        if "property_info" in parcel_data:
            prop_info = parcel_data["property_info"]
            if isinstance(prop_info, dict):
                for field in ["images", "photos", "photo_urls"]:
                    if field in prop_info:
                        value = prop_info[field]
                        if isinstance(value, list):
                            image_urls.extend(value)
                        elif isinstance(value, str):
                            image_urls.append(value)

        # Filter out empty strings and ensure absolute URLs
        filtered_urls = []
        for url in image_urls:
            if not url or not isinstance(url, str):
                continue

            # Make relative URLs absolute
            if url.startswith("/"):
                url = f"{self.source.base_url}{url}"

            filtered_urls.append(url)

        return filtered_urls

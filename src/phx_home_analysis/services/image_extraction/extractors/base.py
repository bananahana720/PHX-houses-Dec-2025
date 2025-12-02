"""Abstract base class for image extractors.

Defines the interface that all source-specific extractors must implement.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from ....domain.entities import Property
from ....domain.enums import ImageSource

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class SourceUnavailableError(ExtractionError):
    """Source is temporarily or permanently unavailable."""

    def __init__(
        self,
        source: ImageSource,
        reason: str,
        retry_after: Optional[int] = None,
    ):
        self.source = source
        self.reason = reason
        self.retry_after = retry_after
        super().__init__(f"{source.display_name}: {reason}")


class RateLimitError(SourceUnavailableError):
    """Rate limit exceeded for a source."""

    pass


class AuthenticationError(SourceUnavailableError):
    """Authentication failed for a source."""

    pass


class ImageDownloadError(ExtractionError):
    """Failed to download an image."""

    def __init__(
        self,
        url: str,
        status_code: Optional[int],
        message: str,
    ):
        self.url = url
        self.status_code = status_code
        self.message = message
        super().__init__(f"Failed to download {url}: {message}")


class ImageExtractor(ABC):
    """Abstract base class for source-specific image extraction.

    Each extractor handles a single image source with its specific
    authentication, rate limiting, and URL discovery logic.
    """

    # Default user agent for HTTP requests
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        timeout: float = 30.0,
    ):
        """Initialize extractor with optional HTTP client.

        Args:
            http_client: Shared httpx client (created if not provided)
            timeout: Request timeout in seconds
        """
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": self.USER_AGENT},
        )

    async def close(self) -> None:
        """Close HTTP client if we own it."""
        if self._owns_client and self._http_client:
            await self._http_client.aclose()

    @property
    @abstractmethod
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource enum value
        """
        pass

    @property
    def name(self) -> str:
        """Human-readable extractor name.

        Returns:
            Display name for logging/UI
        """
        return self.source.display_name

    @property
    def rate_limit_delay(self) -> float:
        """Delay between requests in seconds.

        Returns:
            Delay based on source configuration
        """
        return self.source.rate_limit_seconds

    @abstractmethod
    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract all image URLs for a property from this source.

        Args:
            property: Property entity to find images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If source is down or rate limited
            ExtractionError: For other extraction failures
        """
        pass

    @abstractmethod
    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image and return (data, content_type).

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: If download fails
        """
        pass

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Some extractors may only work for certain cities or address formats.
        Default implementation returns True for all properties.

        Args:
            property: Property to check

        Returns:
            True if extractor can attempt extraction
        """
        return True

    async def _rate_limit(self) -> None:
        """Apply rate limiting delay."""
        await asyncio.sleep(self.rate_limit_delay)

    async def _download_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        headers: Optional[dict] = None,
    ) -> tuple[bytes, str]:
        """Download with exponential backoff retry.

        Args:
            url: URL to download
            max_retries: Maximum retry attempts
            headers: Additional headers to include

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: After all retries exhausted
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                response = await self._http_client.get(url, headers=headers)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        self.source,
                        "Rate limit exceeded",
                        retry_after=retry_after,
                    )

                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "image/jpeg")
                return response.content, content_type

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (401, 403):
                    raise AuthenticationError(
                        self.source,
                        f"Authentication failed: {e.response.status_code}",
                    )
                if e.response.status_code == 404:
                    raise ImageDownloadError(url, 404, "Image not found")

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Timeout downloading {url}, attempt {attempt + 1}")

            except httpx.NetworkError as e:
                last_error = e
                logger.warning(f"Network error downloading {url}, attempt {attempt + 1}")

            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                await asyncio.sleep(wait_time)

        raise ImageDownloadError(
            url,
            None,
            f"Failed after {max_retries} attempts: {last_error}",
        )

"""Stealth HTTP client using curl_cffi for TLS fingerprint matching.

This module provides a StealthHttpClient that uses curl_cffi to make HTTP requests
with Chrome TLS fingerprinting, making requests harder to detect and block.
Primarily used for image extraction from real estate listing sites.

Security: All URLs are validated against SSRF attacks before fetching.
"""

from __future__ import annotations

import asyncio
import logging

from curl_cffi.requests import AsyncSession

from .url_validator import URLValidator

logger = logging.getLogger(__name__)

# Module-level singleton for URL validation (lazy-initialized)
_url_validator: URLValidator | None = None


def get_url_validator() -> URLValidator:
    """Get the shared URL validator instance.

    Returns:
        URLValidator instance configured for real estate CDN hosts
    """
    global _url_validator
    if _url_validator is None:
        _url_validator = URLValidator(strict_mode=True, resolve_dns=True)
    return _url_validator


class StealthDownloadError(Exception):
    """Failed to download content via stealth HTTP client.

    This is a local exception to avoid circular imports. It mirrors
    StealthDownloadError from extractors.base but is defined here for
    infrastructure layer independence.
    """

    def __init__(self, url: str, status_code: int | None, message: str):
        self.url = url
        self.status_code = status_code
        self.message = message
        super().__init__(f"Failed to download {url}: {message}")


class StealthHttpClient:
    """HTTP client with Chrome TLS fingerprint matching for stealth requests.

    Uses curl_cffi's AsyncSession with Chrome 120 impersonation to match
    browser TLS fingerprints and bypass basic bot detection.

    Example:
        ```python
        async with StealthHttpClient(proxy_url="http://proxy:8080") as client:
            image_data, content_type = await client.download_image(
                url="https://example.com/image.jpg",
                referer="https://example.com"
            )
        ```
    """

    # Chrome-like headers for image requests
    DEFAULT_IMAGE_HEADERS = {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    def __init__(
        self,
        proxy_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize stealth HTTP client.

        Args:
            proxy_url: Optional proxy URL (e.g., "http://user:pass@proxy:8080")
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: AsyncSession | None = None

    async def _get_session(self) -> AsyncSession:
        """Get or create the curl_cffi session.

        Returns:
            Configured AsyncSession instance
        """
        if self._session is None:
            session_kwargs = {
                "impersonate": "chrome120",
                "timeout": self.timeout,
            }
            if self.proxy_url:
                session_kwargs["proxy"] = self.proxy_url

            self._session = AsyncSession(**session_kwargs)  # type: ignore[arg-type]

        return self._session

    # Security constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max download size
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/jpg",  # Non-standard but common alias
    }

    async def download_image(
        self,
        url: str,
        headers: dict | None = None,
        referer: str | None = None,
    ) -> tuple[bytes, str]:
        """Download an image with retry logic and exponential backoff.

        Security controls:
        - SSRF validation: All URLs validated against internal networks
        - Content-Type validation: Only image types accepted
        - File size limits: Maximum 50MB to prevent resource exhaustion

        Args:
            url: Image URL to download
            headers: Optional custom headers (merged with defaults)
            referer: Optional referer URL to set in headers

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            StealthDownloadError: If URL validation fails, Content-Type is invalid,
                file size exceeds limit, or download fails after all retries
        """
        # SSRF Protection: Always validate URL before fetching (no bypass option)
        validator = get_url_validator()
        validation_result = validator.validate_url(url)
        if not validation_result.is_valid:
            logger.warning(
                "SSRF Protection: Blocked download from %s - %s",
                url[:100],
                validation_result.error_message,
            )
            raise StealthDownloadError(
                url=url,
                status_code=None,
                message=f"URL validation failed (SSRF protection): {validation_result.error_message}",
            )

        # Build headers
        request_headers = self.DEFAULT_IMAGE_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        if referer:
            request_headers["Referer"] = referer

        session = await self._get_session()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Downloading image from {url} (attempt {attempt + 1}/{self.max_retries})"
                )

                response = await session.get(url, headers=request_headers)

                # Check status code
                if response.status_code == 404:
                    raise StealthDownloadError(
                        url=url,
                        status_code=404,
                        message="Image not found (404)",
                    )

                if response.status_code == 403:
                    raise StealthDownloadError(
                        url=url,
                        status_code=403,
                        message="Access forbidden (403) - possible bot detection",
                    )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(
                        f"Rate limited downloading {url}, retry after {retry_after}s"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise StealthDownloadError(
                        url=url,
                        status_code=429,
                        message=f"Rate limit exceeded (retry after {retry_after}s)",
                    )

                if not (200 <= response.status_code < 300):
                    raise StealthDownloadError(
                        url=url,
                        status_code=response.status_code,
                        message=f"HTTP {response.status_code}",
                    )

                # Extract and validate content type
                content_type = response.headers.get("Content-Type", "")
                # Parse content type (strip charset and parameters)
                base_content_type = content_type.split(";")[0].strip().lower()

                if base_content_type not in self.ALLOWED_CONTENT_TYPES:
                    logger.warning(
                        "Security: Rejected non-image Content-Type '%s' from %s",
                        content_type[:50],
                        url[:100],
                    )
                    raise StealthDownloadError(
                        url=url,
                        status_code=response.status_code,
                        message=f"Invalid Content-Type: {base_content_type}. "
                        f"Only image types allowed: {self.ALLOWED_CONTENT_TYPES}",
                    )

                # Check Content-Length header before reading body
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        declared_size = int(content_length)
                        if declared_size > self.MAX_FILE_SIZE:
                            logger.warning(
                                "Security: Rejected oversized image (%d bytes) from %s",
                                declared_size,
                                url[:100],
                            )
                            raise StealthDownloadError(
                                url=url,
                                status_code=response.status_code,
                                message=f"File too large: {declared_size} bytes "
                                f"exceeds limit of {self.MAX_FILE_SIZE} bytes",
                            )
                    except ValueError:
                        pass  # Invalid Content-Length header, proceed with download

                # Get image bytes
                image_data = response.content

                # Validate actual size (defense in depth)
                if len(image_data) > self.MAX_FILE_SIZE:
                    logger.warning(
                        "Security: Downloaded image exceeded size limit (%d bytes) from %s",
                        len(image_data),
                        url[:100],
                    )
                    raise StealthDownloadError(
                        url=url,
                        status_code=response.status_code,
                        message=f"Downloaded file too large: {len(image_data)} bytes "
                        f"exceeds limit of {self.MAX_FILE_SIZE} bytes",
                    )

                if not image_data:
                    raise StealthDownloadError(
                        url=url,
                        status_code=response.status_code,
                        message="Empty response body",
                    )

                logger.debug(
                    f"Successfully downloaded {len(image_data)} bytes from {url}"
                )
                return image_data, base_content_type

            except StealthDownloadError:
                # Don't retry on 404/403/429 - re-raise immediately
                raise

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout downloading {url} (attempt {attempt + 1}/{self.max_retries})"
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Error downloading {url} (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                wait_time = 2**attempt  # 1s, 2s, 4s, etc.
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        # All retries exhausted
        raise StealthDownloadError(
            url=url,
            status_code=None,
            message=f"Failed after {self.max_retries} attempts: {last_error}",
        )

    async def close(self) -> None:
        """Close the HTTP session and clean up resources."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            logger.debug("Stealth HTTP client session closed")

    async def __aenter__(self) -> StealthHttpClient:
        """Enter async context manager.

        Returns:
            Self for use in async with statement
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and close session.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        await self.close()

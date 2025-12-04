"""Base API client with authentication, rate limiting, caching, and retry.

Subclasses inherit all protection automatically, making it easy to add
new API integrations with consistent behavior.

Features:
    - Authentication via environment variables (never logged)
    - Proactive rate limiting with throttling
    - Response caching with configurable TTL
    - Automatic retry with exponential backoff for transient errors
    - Retry-After header support for 429 responses
    - Cache-first pattern for efficient API usage

Usage:
    from phx_home_analysis.services.api_client import APIClient, RateLimit

    class GreatSchoolsClient(APIClient):
        def __init__(self):
            super().__init__(
                service_name="greatschools",
                base_url="https://gs-api.greatschools.org",
                env_key="GREATSCHOOLS_API_KEY",
                rate_limit=RateLimit(requests_per_day=1000),
                cache_ttl_days=30,
            )

        async def get_schools(self, lat: float, lng: float) -> list[dict]:
            return await self.get(
                "/schools/nearby",
                params={"lat": lat, "lng": lng}
            )
"""

import logging
import os
from typing import Any

import httpx

from phx_home_analysis.errors import retry_with_backoff

from .rate_limiter import RateLimit, RateLimiter
from .response_cache import CacheConfig, ResponseCache

logger = logging.getLogger(__name__)


class APIClient:
    """Base class for API clients with built-in protection.

    Provides authentication, rate limiting, caching, and retry logic
    that subclasses inherit automatically. Subclasses only need to
    implement service-specific request methods.

    Authentication:
        Credentials are loaded from environment variables and are NEVER logged.
        Supports both API key (query param) and Bearer token (header) auth.

    Rate Limiting:
        Proactive throttling at 80% of limit prevents 429 responses.
        Supports per-second, per-minute, and per-day limits.

    Caching:
        Responses are cached to disk with configurable TTL.
        Cache key is SHA256 hash of URL + sorted params.

    Retry:
        Uses exponential backoff with jitter for transient errors.
        Respects Retry-After header on 429 responses.

    Example Subclass:
        class CountyAPIClient(APIClient):
            def __init__(self):
                super().__init__(
                    service_name="maricopa_county",
                    base_url="https://mcassessor.maricopa.gov",
                    env_token="MARICOPA_ASSESSOR_TOKEN",
                    rate_limit=RateLimit(requests_per_second=2.0),
                    cache_ttl_days=7,
                )

            async def get_parcel(self, apn: str) -> dict:
                return await self.get(f"/parcel/{apn}")
    """

    def __init__(
        self,
        service_name: str,
        base_url: str = "",
        env_key: str | None = None,
        env_token: str | None = None,
        rate_limit: RateLimit | None = None,
        cache_ttl_days: int = 7,
        cache_enabled: bool = True,
        timeout: float = 30.0,
    ) -> None:
        """Initialize API client.

        Args:
            service_name: Name for cache directory and logging (e.g., "google_maps").
            base_url: Base URL for API requests (e.g., "https://api.example.com").
            env_key: Environment variable for API key (e.g., "GOOGLE_MAPS_API_KEY").
                     If set, key is added to request params as "key=<value>".
            env_token: Environment variable for Bearer token (e.g., "MARICOPA_ASSESSOR_TOKEN").
                       If set, token is added to request header as "Authorization: Bearer <value>".
            rate_limit: Rate limiting configuration. Defaults to 0.1s min delay.
            cache_ttl_days: Cache TTL in days (default 7).
            cache_enabled: Whether to enable response caching (default True).
            timeout: Request timeout in seconds (default 30).

        Raises:
            ValueError: If env_key or env_token specified but not set in environment.
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.timeout = timeout

        # Load credentials from environment (NEVER log these)
        self._api_key: str | None = None
        self._bearer_token: str | None = None

        if env_key:
            self._api_key = os.getenv(env_key)
            if not self._api_key:
                raise ValueError(
                    f"Missing required environment variable: {env_key}. Add it to your .env file."
                )

        if env_token:
            self._bearer_token = os.getenv(env_token)
            if not self._bearer_token:
                raise ValueError(
                    f"Missing required environment variable: {env_token}. Add it to your .env file."
                )

        # Rate limiting
        self._rate_limit = rate_limit or RateLimit(min_delay=0.1)
        self._rate_limiter = RateLimiter(self._rate_limit)

        # Caching
        cache_config = CacheConfig(ttl_days=cache_ttl_days, enabled=cache_enabled)
        self._cache = ResponseCache(service_name, cache_config)

        # HTTP client (initialized on context manager entry)
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "APIClient":
        """Async context manager entry.

        Creates HTTP client with connection pooling and timeout settings.

        Example:
            async with GreatSchoolsClient() as client:
                schools = await client.get_schools(lat, lng)
        """
        self._http = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            ),
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit.

        Closes HTTP client and releases connections.
        """
        if self._http:
            await self._http.aclose()
            self._http = None

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with authentication.

        Returns:
            Headers dict with Authorization header if Bearer token configured.
        """
        headers: dict[str, str] = {}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        return headers

    def _build_params(self, params: dict | None) -> dict:
        """Build request params with API key if configured.

        Args:
            params: User-provided params.

        Returns:
            Merged params dict with API key if configured.
        """
        result = dict(params) if params else {}
        if self._api_key:
            result["key"] = self._api_key
        return result

    def _safe_log_error(self, error: Exception) -> str:
        """Create error message with credentials redacted.

        SECURITY: Never log API keys or tokens. This method ensures
        any error message containing credentials is sanitized.

        Args:
            error: The exception to format.

        Returns:
            Error message string with credentials replaced by [REDACTED_*].
        """
        msg = str(error)
        if self._api_key and self._api_key in msg:
            msg = msg.replace(self._api_key, "[REDACTED_KEY]")
        if self._bearer_token and self._bearer_token in msg:
            msg = msg.replace(self._bearer_token, "[REDACTED_TOKEN]")
        return msg

    @retry_with_backoff(max_retries=5, min_delay=1.0, max_delay=60.0)
    async def get(
        self,
        path: str,
        params: dict | None = None,
        skip_cache: bool = False,
    ) -> Any:
        """Make GET request with caching and retry.

        Cache-first pattern:
        1. Check cache for existing valid response
        2. If cache miss, apply rate limiting
        3. Make HTTP request
        4. Cache successful response
        5. Return response data

        Retry behavior:
        - Retries on transient errors (5xx, 429, timeouts)
        - Exponential backoff: 1s, 2s, 4s, 8s, 16s (capped at 60s)
        - Respects Retry-After header on 429 responses

        Args:
            path: URL path (appended to base_url).
            params: Query parameters (API key added automatically if configured).
            skip_cache: If True, bypass cache for this request.

        Returns:
            Response JSON data.

        Raises:
            httpx.HTTPStatusError: On non-2xx response after retries.
            RuntimeError: If client not used as context manager.

        Example:
            data = await client.get("/geocode/json", params={"address": "123 Main St"})
        """
        url = f"{self.base_url}{path}" if self.base_url else path

        # Build cache key from user params ONLY (excludes API key for security)
        # This prevents API keys from being stored in cache keys/files
        cache_params = dict(params) if params else {}

        # Check cache first (unless skipped)
        if not skip_cache:
            cached = self._cache.get(url, cache_params)
            if cached is not None:
                return cached

        # Build full request params (includes API key) AFTER cache lookup
        request_params = self._build_params(params)

        # Apply rate limiting
        await self._rate_limiter.acquire()

        # Make request
        if not self._http:
            raise RuntimeError(
                f"{self.__class__.__name__} must be used as async context manager. "
                f"Use: async with {self.__class__.__name__}() as client: ..."
            )

        try:
            response = await self._http.get(
                url,
                params=request_params,
                headers=self._build_headers(),
            )

            # Handle rate limit response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    logger.warning(
                        f"Rate limited by {self.service_name}. Retry-After: {retry_after}s"
                    )
                raise httpx.HTTPStatusError(
                    f"Rate limited (429) by {self.service_name}",
                    request=response.request,
                    response=response,
                )

            response.raise_for_status()
            data = response.json()

            # Cache successful response (use cache_params without API key)
            if not skip_cache:
                self._cache.set(url, cache_params, data)

            return data

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.error(f"{self.service_name} GET error: {self._safe_log_error(e)}")
            raise

    @retry_with_backoff(max_retries=5, min_delay=1.0, max_delay=60.0)
    async def post(
        self,
        path: str,
        json_data: dict | None = None,
        form_data: dict | None = None,
    ) -> Any:
        """Make POST request with retry (no caching for POST).

        POST requests are not cached because they typically modify state.
        Rate limiting and retry logic still apply.

        Args:
            path: URL path (appended to base_url).
            json_data: JSON body data.
            form_data: Form data.

        Returns:
            Response JSON data.

        Raises:
            httpx.HTTPStatusError: On non-2xx response after retries.
            RuntimeError: If client not used as context manager.
        """
        url = f"{self.base_url}{path}" if self.base_url else path

        # Apply rate limiting
        await self._rate_limiter.acquire()

        if not self._http:
            raise RuntimeError(
                f"{self.__class__.__name__} must be used as async context manager. "
                f"Use: async with {self.__class__.__name__}() as client: ..."
            )

        try:
            response = await self._http.post(
                url,
                json=json_data,
                data=form_data,
                headers=self._build_headers(),
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    logger.warning(
                        f"Rate limited by {self.service_name}. Retry-After: {retry_after}s"
                    )
                raise httpx.HTTPStatusError(
                    f"Rate limited (429) by {self.service_name}",
                    request=response.request,
                    response=response,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.error(f"{self.service_name} POST error: {self._safe_log_error(e)}")
            raise

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache hit/miss statistics:
                - total_requests: Total cache lookups
                - cache_hits: Successful cache retrievals
                - cache_misses: Cache misses
                - hit_rate_percent: Hit rate as percentage
                - cache_dir: Path to cache directory
        """
        return self._cache.get_stats()

    def get_rate_limit_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dict with rate limit statistics:
                - requests_last_minute: Requests in last 60 seconds
                - requests_today: Requests since midnight
                - last_request_age_seconds: Seconds since last request
        """
        return self._rate_limiter.get_stats()

    def clear_cache(self) -> int:
        """Clear all cached entries for this service.

        Returns:
            Number of entries cleared.
        """
        return self._cache.clear()


__all__ = ["APIClient"]

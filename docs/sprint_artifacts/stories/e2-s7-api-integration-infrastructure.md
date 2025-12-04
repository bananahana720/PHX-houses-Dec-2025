# E2.S7: API Integration Infrastructure

**Status:** Ready for Review
**Epic:** Epic 2 - Property Data Acquisition
**Priority:** P0
**Estimated Points:** 8
**Dependencies:** E1.S6 (Transient Error Recovery) - DONE
**Functional Requirements:** FR58, FR59, FR60

## User Story

As a system user, I want robust API integration with authentication, rate limiting, and caching, so that external data sources are accessed reliably and cost-efficiently.

## Acceptance Criteria

### AC1: Credentials from Environment Variables
**Given** an API client requires authentication
**When** the client is initialized
**Then** credentials are loaded from environment variables (`*_API_KEY`, `*_TOKEN` patterns)
**And** credentials are NEVER logged in any output (debug, info, error, or exception traces)
**And** missing credentials raise a clear error with the expected environment variable name

### AC2: Proactive Rate Limit Throttling
**Given** the APIClient tracks request counts per time window
**When** request count approaches the configured limit threshold (e.g., 80% of limit)
**Then** the client proactively throttles by adding delays between requests
**And** a warning is logged indicating throttling is active with remaining budget
**And** throttling prevents hitting actual rate limits (429 responses)

### AC3: Exponential Backoff on 429 Responses
**Given** an API returns HTTP 429 (Too Many Requests)
**When** the retry logic is invoked (leveraging E1.S6 `@retry_with_backoff`)
**Then** the request is retried with exponential backoff (1s, 2s, 4s, 8s, 16s)
**And** the `Retry-After` header is respected if present
**And** after max retries exhausted, the error is logged with actionable guidance

### AC4: Response Caching with Configurable TTL
**Given** an API response is received
**When** the response is successful (2xx status)
**Then** the response is cached to `data/api_cache/{service_name}/`
**And** the cache key is a hash of URL + sorted query params
**And** cache TTL defaults to 7 days but is configurable per client instance
**And** existing cache entries are returned without making external requests

### AC5: Cache Hit Rate Logging
**Given** API requests are made through the APIClient
**When** the request completes (cache hit or API call)
**Then** a cache hit/miss is logged at DEBUG level
**And** aggregate cache statistics are available via `get_cache_stats()` method
**And** stats include: total_requests, cache_hits, cache_misses, hit_rate_percent

### AC6: APIClient Base Class Design
**Given** a new API integration is needed (County, Google Maps, GreatSchools)
**When** a developer extends the APIClient base class
**Then** authentication, rate limiting, caching, and retry logic are inherited automatically
**And** subclasses only need to implement service-specific request methods
**And** the base class provides `async get()`, `async post()` methods with built-in protection

## Technical Tasks

### Task 1: Create APIClient Base Class
**File:** `src/phx_home_analysis/services/api_client/__init__.py` (NEW)
**Lines:** ~50

**Implementation:**
```python
"""API Client Infrastructure - base class with auth, rate limiting, and caching.

Usage:
    from phx_home_analysis.services.api_client import APIClient

    class GoogleMapsClient(APIClient):
        def __init__(self):
            super().__init__(
                service_name="google_maps",
                env_key="GOOGLE_MAPS_API_KEY",
                rate_limit=RateLimit(requests_per_second=10),
                cache_ttl_days=7,
            )

        async def geocode(self, address: str) -> dict:
            return await self.get("/geocode/json", params={"address": address})
"""

from .base import APIClient, RateLimit, CacheConfig
from .cache import ResponseCache

__all__ = [
    "APIClient",
    "RateLimit",
    "CacheConfig",
    "ResponseCache",
]
```

**Acceptance Criteria:**
- [x] Module exports `APIClient`, `RateLimit`, `CacheConfig`, `ResponseCache`
- [x] Docstring shows usage example for subclass creation
- [x] All public classes importable from `phx_home_analysis.services.api_client`

### Task 2: Implement Rate Limit Configuration
**File:** `src/phx_home_analysis/services/api_client/rate_limit.py` (NEW)
**Lines:** ~120

**Implementation:**
```python
"""Rate limiting with proactive throttling.

Tracks request counts and proactively throttles before hitting limits.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration with proactive throttling.

    Attributes:
        requests_per_second: Max requests per second (e.g., 1.0 for 1 req/sec)
        requests_per_minute: Max requests per minute (alternative to per-second)
        requests_per_day: Max requests per day (for daily-capped APIs like GreatSchools)
        throttle_threshold: Percentage of limit to trigger proactive throttling (default 0.8)
        min_delay: Minimum delay between requests in seconds (default 0.1)
    """

    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[float] = None
    requests_per_day: Optional[int] = None
    throttle_threshold: float = 0.8
    min_delay: float = 0.1


class RateLimiter:
    """Tracks request counts and applies rate limiting.

    Implements token bucket algorithm with proactive throttling.
    """

    def __init__(self, config: RateLimit):
        self.config = config
        self._last_request_time: float = 0.0
        self._request_times: list[float] = []
        self._daily_count: int = 0
        self._daily_reset: float = 0.0

    async def acquire(self) -> None:
        """Wait until a request is allowed.

        Implements proactive throttling before hitting actual limits.
        """
        now = time.time()

        # Calculate required delay
        delay = self._calculate_delay(now)
        if delay > 0:
            logger.debug(f"Rate limiter: waiting {delay:.2f}s before request")
            await asyncio.sleep(delay)

        # Record this request
        self._record_request()

    def _calculate_delay(self, now: float) -> float:
        """Calculate delay needed before next request."""
        delay = 0.0

        # Per-second rate limit
        if self.config.requests_per_second:
            min_interval = 1.0 / self.config.requests_per_second
            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                delay = max(delay, min_interval - elapsed)

        # Per-minute rate limit with sliding window
        if self.config.requests_per_minute:
            window_start = now - 60.0
            recent = [t for t in self._request_times if t > window_start]
            threshold = int(self.config.requests_per_minute * self.config.throttle_threshold)
            if len(recent) >= threshold:
                # Proactive throttling: add delay
                delay = max(delay, 60.0 / self.config.requests_per_minute)
                logger.warning(
                    f"Proactive throttling: {len(recent)}/{self.config.requests_per_minute} "
                    f"requests in last minute (threshold: {threshold})"
                )

        # Per-day rate limit
        if self.config.requests_per_day:
            # Reset daily counter at midnight
            if now > self._daily_reset:
                self._daily_count = 0
                self._daily_reset = now + 86400  # Next midnight

            threshold = int(self.config.requests_per_day * self.config.throttle_threshold)
            if self._daily_count >= threshold:
                logger.warning(
                    f"Daily limit approaching: {self._daily_count}/{self.config.requests_per_day} "
                    f"(threshold: {threshold})"
                )

        return max(delay, self.config.min_delay)

    def _record_request(self) -> None:
        """Record a request for rate tracking."""
        now = time.time()
        self._last_request_time = now
        self._request_times.append(now)
        self._daily_count += 1

        # Prune old request times (keep last 5 minutes)
        cutoff = now - 300
        self._request_times = [t for t in self._request_times if t > cutoff]

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        now = time.time()
        return {
            "requests_last_minute": len([t for t in self._request_times if t > now - 60]),
            "requests_today": self._daily_count,
            "last_request_age_seconds": now - self._last_request_time if self._last_request_time else None,
        }
```

**Acceptance Criteria:**
- [x] `RateLimit` dataclass supports per-second, per-minute, per-day limits
- [x] `RateLimiter.acquire()` blocks until request is allowed
- [x] Proactive throttling triggers at 80% of limit (configurable)
- [x] Warning logs indicate when throttling is active
- [x] `get_stats()` returns current rate limit statistics

### Task 3: Implement Response Cache
**File:** `src/phx_home_analysis/services/api_client/cache.py` (NEW)
**Lines:** ~180

**Implementation:**
```python
"""Response caching with configurable TTL.

Caches API responses to disk with hash-based keys.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default cache location
DEFAULT_CACHE_DIR = Path("data/api_cache")


@dataclass
class CacheConfig:
    """Cache configuration.

    Attributes:
        ttl_days: Cache entry time-to-live in days (default 7)
        cache_dir: Base directory for cache files (default data/api_cache)
        enabled: Whether caching is enabled (default True)
    """

    ttl_days: int = 7
    cache_dir: Path = DEFAULT_CACHE_DIR
    enabled: bool = True


class ResponseCache:
    """Disk-based response cache with TTL.

    Cache structure:
        data/api_cache/{service_name}/{cache_key}.json

    Each cache file contains:
        {"data": <response>, "cached_at": <timestamp>, "url": <original_url>}
    """

    def __init__(self, service_name: str, config: CacheConfig | None = None):
        self.service_name = service_name
        self.config = config or CacheConfig()
        self.cache_dir = self.config.cache_dir / service_name

        # Statistics
        self._hits = 0
        self._misses = 0

        # Ensure cache directory exists
        if self.config.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_key(self, url: str, params: dict | None = None) -> str:
        """Generate cache key from URL and params.

        Args:
            url: Request URL
            params: Query parameters (will be sorted for consistency)

        Returns:
            SHA256 hash of URL + sorted params
        """
        # Sort params for consistent key generation
        param_str = ""
        if params:
            sorted_params = sorted(params.items())
            param_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        key_input = f"{url}?{param_str}" if param_str else url
        return hashlib.sha256(key_input.encode()).hexdigest()[:32]

    def get(self, url: str, params: dict | None = None) -> Optional[Any]:
        """Get cached response if valid.

        Args:
            url: Original request URL
            params: Original query parameters

        Returns:
            Cached response data if valid, None if miss or expired
        """
        if not self.config.enabled:
            return None

        key = self.generate_key(url, params)
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            self._misses += 1
            logger.debug(f"Cache MISS: {url} (key: {key})")
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                entry = json.load(f)

            # Check TTL
            cached_at = entry.get("cached_at", 0)
            age_days = (time.time() - cached_at) / 86400

            if age_days > self.config.ttl_days:
                self._misses += 1
                logger.debug(f"Cache EXPIRED: {url} (age: {age_days:.1f} days)")
                cache_file.unlink()  # Clean up expired entry
                return None

            self._hits += 1
            logger.debug(f"Cache HIT: {url} (age: {age_days:.1f} days)")
            return entry.get("data")

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Cache read error for {key}: {e}")
            self._misses += 1
            return None

    def set(self, url: str, params: dict | None, data: Any) -> None:
        """Cache a response.

        Args:
            url: Original request URL
            params: Original query parameters
            data: Response data to cache
        """
        if not self.config.enabled:
            return

        key = self.generate_key(url, params)
        cache_file = self.cache_dir / f"{key}.json"

        entry = {
            "data": data,
            "cached_at": time.time(),
            "url": url,
            "params": params,
        }

        try:
            # Atomic write
            temp_file = cache_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
            temp_file.replace(cache_file)
            logger.debug(f"Cached response: {url} (key: {key})")

        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with total_requests, cache_hits, cache_misses, hit_rate_percent
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            "total_requests": total,
            "cache_hits": self._hits,
            "cache_misses": self._misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_dir": str(self.cache_dir),
        }

    def clear(self) -> int:
        """Clear all cached entries for this service.

        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cache entries for {self.service_name}")
        return count

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        ttl_seconds = self.config.ttl_days * 86400
        count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    entry = json.load(f)
                if now - entry.get("cached_at", 0) > ttl_seconds:
                    cache_file.unlink()
                    count += 1
            except Exception:
                pass

        logger.info(f"Cleaned up {count} expired entries for {self.service_name}")
        return count
```

**Acceptance Criteria:**
- [x] Cache key is SHA256 hash of URL + sorted params (first 32 chars)
- [x] Cache entries stored as JSON with `data`, `cached_at`, `url` fields
- [x] TTL enforced on read (expired entries return None and are deleted)
- [x] `get_stats()` returns hit rate as percentage
- [x] Atomic writes prevent cache corruption
- [x] `cleanup_expired()` removes stale entries

### Task 4: Implement APIClient Base Class
**File:** `src/phx_home_analysis/services/api_client/base.py` (NEW)
**Lines:** ~250

**Implementation:**
```python
"""Base API client with authentication, rate limiting, caching, and retry.

Subclasses inherit all protection automatically.
"""

import logging
import os
from typing import Any, Optional

import httpx

from phx_home_analysis.errors import retry_with_backoff, is_transient_error

from .cache import CacheConfig, ResponseCache
from .rate_limit import RateLimit, RateLimiter

logger = logging.getLogger(__name__)


class APIClient:
    """Base class for API clients with built-in protection.

    Features:
    - Authentication via environment variables (never logged)
    - Proactive rate limiting with throttling
    - Response caching with configurable TTL
    - Automatic retry with exponential backoff for transient errors

    Subclass Example:
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
    ):
        """Initialize API client.

        Args:
            service_name: Name for cache directory and logging
            base_url: Base URL for API requests
            env_key: Environment variable for API key (e.g., "GOOGLE_MAPS_API_KEY")
            env_token: Environment variable for Bearer token (e.g., "MARICOPA_ASSESSOR_TOKEN")
            rate_limit: Rate limiting configuration
            cache_ttl_days: Cache TTL in days (default 7)
            cache_enabled: Whether to enable response caching
            timeout: Request timeout in seconds
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Load credentials from environment (NEVER log these)
        self._api_key: str | None = None
        self._bearer_token: str | None = None

        if env_key:
            self._api_key = os.getenv(env_key)
            if not self._api_key:
                raise ValueError(
                    f"Missing required environment variable: {env_key}. "
                    f"Add it to your .env file."
                )

        if env_token:
            self._bearer_token = os.getenv(env_token)
            if not self._bearer_token:
                raise ValueError(
                    f"Missing required environment variable: {env_token}. "
                    f"Add it to your .env file."
                )

        # Rate limiting
        self._rate_limit = rate_limit or RateLimit(min_delay=0.1)
        self._rate_limiter = RateLimiter(self._rate_limit)

        # Caching
        cache_config = CacheConfig(ttl_days=cache_ttl_days, enabled=cache_enabled)
        self._cache = ResponseCache(service_name, cache_config)

        # HTTP client (initialized on first use or context manager)
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "APIClient":
        """Async context manager entry."""
        self._http = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            ),
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        if self._http:
            await self._http.aclose()
            self._http = None

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with authentication.

        Returns:
            Headers dict with auth if configured
        """
        headers = {}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        return headers

    def _build_params(self, params: dict | None) -> dict:
        """Build request params with API key if configured.

        Args:
            params: User-provided params

        Returns:
            Merged params with API key if configured
        """
        result = dict(params) if params else {}
        if self._api_key:
            result["key"] = self._api_key
        return result

    @retry_with_backoff(max_retries=5, min_delay=1.0, max_delay=60.0)
    async def get(
        self,
        path: str,
        params: dict | None = None,
        skip_cache: bool = False,
    ) -> Any:
        """Make GET request with caching and retry.

        Args:
            path: URL path (appended to base_url)
            params: Query parameters
            skip_cache: If True, bypass cache for this request

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: On non-2xx response after retries
        """
        url = f"{self.base_url}{path}" if self.base_url else path
        request_params = self._build_params(params)

        # Check cache first (unless skipped)
        if not skip_cache:
            cached = self._cache.get(url, request_params)
            if cached is not None:
                return cached

        # Apply rate limiting
        await self._rate_limiter.acquire()

        # Make request
        if not self._http:
            raise RuntimeError("APIClient must be used as async context manager")

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
                f"Rate limited (429)",
                request=response.request,
                response=response,
            )

        response.raise_for_status()
        data = response.json()

        # Cache successful response
        if not skip_cache:
            self._cache.set(url, request_params, data)

        return data

    @retry_with_backoff(max_retries=5, min_delay=1.0, max_delay=60.0)
    async def post(
        self,
        path: str,
        json: dict | None = None,
        data: dict | None = None,
    ) -> Any:
        """Make POST request with retry (no caching for POST).

        Args:
            path: URL path (appended to base_url)
            json: JSON body
            data: Form data

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{path}" if self.base_url else path

        # Apply rate limiting
        await self._rate_limiter.acquire()

        if not self._http:
            raise RuntimeError("APIClient must be used as async context manager")

        response = await self._http.post(
            url,
            json=json,
            data=data,
            headers=self._build_headers(),
        )

        if response.status_code == 429:
            raise httpx.HTTPStatusError(
                "Rate limited (429)",
                request=response.request,
                response=response,
            )

        response.raise_for_status()
        return response.json()

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache hit/miss statistics
        """
        return self._cache.get_stats()

    def get_rate_limit_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dict with rate limit statistics
        """
        return self._rate_limiter.get_stats()

    def _safe_log_error(self, error: Exception) -> str:
        """Create error message with credentials redacted.

        SECURITY: Never log API keys or tokens.
        """
        msg = str(error)
        if self._api_key and self._api_key in msg:
            msg = msg.replace(self._api_key, "[REDACTED_KEY]")
        if self._bearer_token and self._bearer_token in msg:
            msg = msg.replace(self._bearer_token, "[REDACTED_TOKEN]")
        return msg
```

**Acceptance Criteria:**
- [x] Credentials loaded from env vars, never logged
- [x] Missing credentials raise clear error with env var name
- [x] `@retry_with_backoff` applied to `get()` and `post()` methods
- [x] Cache checked before API call, response cached after success
- [x] Rate limiter `acquire()` called before each request
- [x] 429 responses include `Retry-After` header handling
- [x] `_safe_log_error()` redacts credentials in error messages

### Task 5: Unit Tests for Rate Limiter
**File:** `tests/unit/services/api_client/test_rate_limit.py` (NEW)
**Lines:** ~100

**Test Cases:**
```python
import asyncio
import pytest
from unittest.mock import patch
import time

from phx_home_analysis.services.api_client.rate_limit import RateLimit, RateLimiter


class TestRateLimit:
    """Tests for RateLimit configuration."""

    def test_default_values(self):
        """Default rate limit should have sensible defaults."""
        rl = RateLimit()
        assert rl.throttle_threshold == 0.8
        assert rl.min_delay == 0.1

    def test_per_second_config(self):
        """Per-second rate limit should be configurable."""
        rl = RateLimit(requests_per_second=10.0)
        assert rl.requests_per_second == 10.0


class TestRateLimiter:
    """Tests for RateLimiter behavior."""

    @pytest.mark.asyncio
    async def test_min_delay_applied(self):
        """Minimum delay should be applied between requests."""
        limiter = RateLimiter(RateLimit(min_delay=0.05))

        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_per_second_rate_limit(self):
        """Per-second rate limit should space requests."""
        limiter = RateLimiter(RateLimit(requests_per_second=2.0))

        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        # 2 req/sec = 0.5s between requests
        assert elapsed >= 0.45  # Allow small timing variance

    @pytest.mark.asyncio
    async def test_proactive_throttling_warning(self, caplog):
        """Proactive throttling should log warning."""
        limiter = RateLimiter(
            RateLimit(requests_per_minute=5, throttle_threshold=0.6)
        )

        # Make requests to trigger throttling (60% of 5 = 3 requests)
        for _ in range(4):
            await limiter.acquire()

        assert "Proactive throttling" in caplog.text

    def test_get_stats(self):
        """Stats should track request counts."""
        limiter = RateLimiter(RateLimit())
        limiter._record_request()
        limiter._record_request()

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 2
        assert stats["requests_today"] == 2
```

**Acceptance Criteria:**
- [x] Default RateLimit values tested
- [x] Minimum delay between requests verified
- [x] Per-second rate limiting verified
- [x] Proactive throttling warning logged
- [x] Statistics tracking tested

### Task 6: Unit Tests for Response Cache
**File:** `tests/unit/services/api_client/test_cache.py` (NEW)
**Lines:** ~120

**Test Cases:**
```python
import json
import pytest
import time
from pathlib import Path

from phx_home_analysis.services.api_client.cache import (
    CacheConfig,
    ResponseCache,
)


class TestResponseCache:
    """Tests for response caching."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_cache_key_generation(self, cache):
        """Cache key should be hash of URL + sorted params."""
        key1 = cache.generate_key("https://api.example.com/data", {"a": "1", "b": "2"})
        key2 = cache.generate_key("https://api.example.com/data", {"b": "2", "a": "1"})

        # Same URL and params (different order) should produce same key
        assert key1 == key2
        assert len(key1) == 32  # SHA256 truncated to 32 chars

    def test_cache_miss_returns_none(self, cache):
        """Cache miss should return None."""
        result = cache.get("https://api.example.com/missing")
        assert result is None

    def test_cache_set_and_get(self, cache):
        """Set and get should work correctly."""
        url = "https://api.example.com/data"
        data = {"result": "success"}

        cache.set(url, None, data)
        result = cache.get(url, None)

        assert result == data

    def test_cache_expiry(self, cache, tmp_path):
        """Expired entries should return None."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=0)  # Immediate expiry
        expired_cache = ResponseCache("expired", config)

        url = "https://api.example.com/data"
        expired_cache.set(url, None, {"data": "test"})

        # Manually backdate the cache entry
        key = expired_cache.generate_key(url, None)
        cache_file = expired_cache.cache_dir / f"{key}.json"
        with open(cache_file, encoding="utf-8") as f:
            entry = json.load(f)
        entry["cached_at"] = time.time() - 86400 * 2  # 2 days ago
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(entry, f)

        result = expired_cache.get(url, None)
        assert result is None  # Expired

    def test_cache_stats(self, cache):
        """Stats should track hits and misses."""
        url = "https://api.example.com/data"

        # Miss
        cache.get(url, None)

        # Set and hit
        cache.set(url, None, {"data": "test"})
        cache.get(url, None)

        stats = cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percent"] == 50.0

    def test_cleanup_expired(self, cache, tmp_path):
        """Cleanup should remove expired entries."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        cleanup_cache = ResponseCache("cleanup", config)

        # Create an expired entry manually
        cache_file = cleanup_cache.cache_dir / "expired_entry.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "data": "old",
                "cached_at": time.time() - 86400 * 10,  # 10 days old
            }, f)

        removed = cleanup_cache.cleanup_expired()
        assert removed == 1
        assert not cache_file.exists()
```

**Acceptance Criteria:**
- [x] Cache key consistency tested (sorted params)
- [x] Cache miss returns None
- [x] Set and get roundtrip works
- [x] Expired entries return None and are deleted
- [x] Statistics accuracy tested
- [x] Cleanup removes expired entries

### Task 7: Unit Tests for APIClient Base
**File:** `tests/unit/services/api_client/test_base.py` (NEW)
**Lines:** ~150

**Test Cases:**
```python
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from phx_home_analysis.services.api_client.base import APIClient
from phx_home_analysis.services.api_client.rate_limit import RateLimit


class TestAPIClientInit:
    """Tests for APIClient initialization."""

    def test_missing_env_key_raises(self):
        """Missing required env var should raise ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc:
                APIClient(
                    service_name="test",
                    env_key="MISSING_API_KEY"
                )
            assert "MISSING_API_KEY" in str(exc.value)

    def test_env_key_loaded(self):
        """API key should be loaded from environment."""
        with patch.dict(os.environ, {"TEST_API_KEY": "secret123"}):
            client = APIClient(
                service_name="test",
                env_key="TEST_API_KEY"
            )
            assert client._api_key == "secret123"

    def test_bearer_token_loaded(self):
        """Bearer token should be loaded from environment."""
        with patch.dict(os.environ, {"TEST_TOKEN": "bearer_secret"}):
            client = APIClient(
                service_name="test",
                env_token="TEST_TOKEN"
            )
            assert client._bearer_token == "bearer_secret"


class TestAPIClientRequests:
    """Tests for APIClient request methods."""

    @pytest.fixture
    def client(self):
        """Create client with mocked credentials."""
        with patch.dict(os.environ, {"TEST_KEY": "test_api_key"}):
            return APIClient(
                service_name="test",
                base_url="https://api.example.com",
                env_key="TEST_KEY",
                cache_enabled=False,  # Disable cache for unit tests
            )

    @pytest.mark.asyncio
    async def test_get_builds_correct_url(self, client):
        """GET should combine base_url and path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with patch.object(client, "_rate_limiter") as mock_limiter:
            mock_limiter.acquire = AsyncMock()

            async with client:
                client._http = MagicMock()
                client._http.get = AsyncMock(return_value=mock_response)

                await client.get("/endpoint", params={"foo": "bar"})

                # Verify URL and params
                call_args = client._http.get.call_args
                assert call_args[0][0] == "https://api.example.com/endpoint"
                assert "key" in call_args[1]["params"]  # API key added

    @pytest.mark.asyncio
    async def test_get_caches_response(self, tmp_path):
        """Successful GET should cache response."""
        with patch.dict(os.environ, {"TEST_KEY": "key"}):
            from phx_home_analysis.services.api_client.cache import CacheConfig

            client = APIClient(
                service_name="cache_test",
                base_url="https://api.example.com",
                env_key="TEST_KEY",
                cache_ttl_days=1,
            )
            # Override cache dir
            client._cache.cache_dir = tmp_path / "cache_test"
            client._cache.cache_dir.mkdir(parents=True)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"cached": True}

            with patch.object(client, "_rate_limiter") as mock_limiter:
                mock_limiter.acquire = AsyncMock()

                async with client:
                    client._http = MagicMock()
                    client._http.get = AsyncMock(return_value=mock_response)

                    # First call - should hit API
                    await client.get("/data")
                    assert client._http.get.call_count == 1

                    # Second call - should hit cache
                    result = await client.get("/data")
                    assert client._http.get.call_count == 1  # No additional API call
                    assert result == {"cached": True}


class TestAPIClientSecurity:
    """Security tests for APIClient."""

    def test_credentials_redacted_in_errors(self):
        """Credentials should be redacted in error messages."""
        with patch.dict(os.environ, {"KEY": "super_secret_key"}):
            client = APIClient(service_name="test", env_key="KEY")

            error = Exception("Error with super_secret_key in message")
            safe_msg = client._safe_log_error(error)

            assert "super_secret_key" not in safe_msg
            assert "[REDACTED_KEY]" in safe_msg

    def test_bearer_token_redacted(self):
        """Bearer tokens should be redacted in error messages."""
        with patch.dict(os.environ, {"TOKEN": "bearer_token_123"}):
            client = APIClient(service_name="test", env_token="TOKEN")

            error = Exception("Auth failed: bearer_token_123")
            safe_msg = client._safe_log_error(error)

            assert "bearer_token_123" not in safe_msg
            assert "[REDACTED_TOKEN]" in safe_msg
```

**Acceptance Criteria:**
- [x] Missing env var raises ValueError with var name
- [x] Env var credentials loaded correctly
- [x] GET combines base_url and path
- [x] API key added to params
- [x] Response caching works
- [x] Credentials redacted in error messages

### Task 8: Integration Test for API Client
**File:** `tests/integration/test_api_client_integration.py` (NEW)
**Lines:** ~100

**Test Cases:**
```python
import pytest
import respx
import httpx
from pathlib import Path
from unittest.mock import patch
import os

from phx_home_analysis.services.api_client import APIClient, RateLimit


class TestAPIClientIntegration:
    """Integration tests for complete API client flow."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Provide temp cache directory."""
        cache_path = tmp_path / "api_cache"
        cache_path.mkdir()
        return cache_path

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_request_flow(self, cache_dir):
        """Test complete flow: rate limit -> request -> cache."""
        with patch.dict(os.environ, {"TEST_KEY": "api_key_123"}):
            # Mock external API
            route = respx.get("https://api.example.com/data").mock(
                return_value=httpx.Response(200, json={"result": "success"})
            )

            client = APIClient(
                service_name="integration_test",
                base_url="https://api.example.com",
                env_key="TEST_KEY",
                rate_limit=RateLimit(min_delay=0.01),
                cache_ttl_days=1,
            )
            client._cache.cache_dir = cache_dir / "integration_test"
            client._cache.cache_dir.mkdir()

            async with client:
                # First request - hits API
                result1 = await client.get("/data")
                assert result1 == {"result": "success"}
                assert route.call_count == 1

                # Second request - hits cache
                result2 = await client.get("/data")
                assert result2 == {"result": "success"}
                assert route.call_count == 1  # No additional API call

            # Verify cache stats
            stats = client.get_cache_stats()
            assert stats["cache_hits"] == 1
            assert stats["cache_misses"] == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_429(self, cache_dir):
        """Test retry with exponential backoff on 429."""
        with patch.dict(os.environ, {"TEST_KEY": "key"}):
            # Mock 429 then success
            route = respx.get("https://api.example.com/data")
            route.side_effect = [
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json={"success": True}),
            ]

            client = APIClient(
                service_name="retry_test",
                base_url="https://api.example.com",
                env_key="TEST_KEY",
                cache_enabled=False,
            )

            async with client:
                result = await client.get("/data")
                assert result == {"success": True}
                assert route.call_count == 2  # Retried after 429

    @pytest.mark.asyncio
    @respx.mock
    async def test_auth_header_included(self, cache_dir):
        """Test Bearer token included in headers."""
        with patch.dict(os.environ, {"TEST_TOKEN": "bearer_secret"}):
            route = respx.get("https://api.example.com/protected").mock(
                return_value=httpx.Response(200, json={"auth": "ok"})
            )

            client = APIClient(
                service_name="auth_test",
                base_url="https://api.example.com",
                env_token="TEST_TOKEN",
                cache_enabled=False,
            )

            async with client:
                await client.get("/protected")

            # Verify auth header
            request = route.calls[0].request
            assert request.headers["Authorization"] == "Bearer bearer_secret"
```

**Acceptance Criteria:**
- [x] Full request flow tested (rate limit -> API -> cache)
- [x] Retry on 429 verified with respx mock
- [x] Auth header included in requests
- [x] Cache stats accurate after multiple requests

### Task 9: Create Module Directory Structure
**Files:** Create directory and `__init__.py` files

**Directory Structure:**
```
src/phx_home_analysis/services/api_client/
├── __init__.py      # Public exports
├── base.py          # APIClient base class
├── cache.py         # ResponseCache
└── rate_limit.py    # RateLimit, RateLimiter
```

**Test Directory Structure:**
```
tests/unit/services/api_client/
├── __init__.py
├── test_base.py
├── test_cache.py
└── test_rate_limit.py

tests/integration/
└── test_api_client_integration.py
```

**Acceptance Criteria:**
- [x] Directory `src/phx_home_analysis/services/api_client/` created
- [x] All module files created with proper imports
- [x] Test directory structure created
- [x] All `__init__.py` files present

## Test Plan Summary

### Unit Tests
| Suite | File | Test Count |
|-------|------|------------|
| Rate Limit | `tests/unit/services/api_client/test_rate_limit.py` | 5 |
| Cache | `tests/unit/services/api_client/test_cache.py` | 6 |
| APIClient Base | `tests/unit/services/api_client/test_base.py` | 8 |

### Integration Tests
| Suite | File | Test Count |
|-------|------|------------|
| API Client Flow | `tests/integration/test_api_client_integration.py` | 3 |

**Total New Tests:** ~22

## Dependencies

### New Dependencies Required
None - uses existing httpx (already in project)

### Existing Dependencies Used
- `httpx` - HTTP client (already installed)
- `hashlib` (stdlib) - Cache key generation
- `phx_home_analysis.errors` - Retry decorator from E1.S6

### Internal Dependencies
- `src/phx_home_analysis/errors/retry.py` - `@retry_with_backoff` decorator
- `src/phx_home_analysis/errors/__init__.py` - `is_transient_error()`

## Definition of Done Checklist

### Implementation
- [x] `APIClient` base class with auth, rate limiting, caching
- [x] `RateLimit` config with per-second, per-minute, per-day options
- [x] `RateLimiter` with proactive throttling at 80% threshold
- [x] `ResponseCache` with configurable TTL (default 7 days)
- [x] Cache key is SHA256 hash of URL + sorted params
- [x] Credentials loaded from env vars, never logged
- [x] `@retry_with_backoff` applied to GET/POST methods
- [x] `Retry-After` header respected on 429

### Testing
- [x] Unit tests for RateLimit/RateLimiter pass
- [x] Unit tests for ResponseCache pass
- [x] Unit tests for APIClient pass
- [x] Integration tests pass with respx mocks
- [x] All tests pass: `pytest tests/unit/services/api_client/ tests/integration/test_api_client_integration.py -v`

### Quality Gates
- [x] Type checking passes: `mypy src/phx_home_analysis/services/api_client/`
- [x] Linting passes: `ruff check src/phx_home_analysis/services/api_client/`
- [x] No credentials logged in any test output
- [x] Docstrings complete with examples

### Documentation
- [x] Module docstrings explain purpose and usage
- [x] APIClient subclass example in docstring
- [x] Cache directory structure documented

## Dev Notes

### Architecture Patterns

1. **Base Class Design**: `APIClient` provides all infrastructure; subclasses only implement service-specific methods. This follows the existing pattern in `MaricopaAssessorClient` and `FEMAFloodClient`.

2. **Leveraging E1.S6**: The `@retry_with_backoff` decorator from E1.S6 handles exponential backoff. This story integrates it into the base class.

3. **Cache Key Consistency**: Sorting params before hashing ensures the same request always produces the same cache key, regardless of param order.

4. **Proactive Throttling**: Rather than waiting for 429 errors, the rate limiter slows down at 80% of the limit to avoid hitting actual limits.

5. **Credential Security**: Credentials are loaded once at init, stored privately, and redacted from all error messages and logs.

### Existing Code Patterns to Follow

From `MaricopaAssessorClient`:
- Async context manager pattern (`__aenter__`, `__aexit__`)
- httpx client with connection limits
- Rate limiting via `_apply_rate_limit()`
- Credential redaction in `_safe_error_message()`

From `FEMAFloodClient`:
- Simple public API without auth
- Rate limiting between requests
- Error handling with specific exception types

### Cache Directory Structure

```
data/api_cache/
├── google_maps/
│   ├── a1b2c3d4e5f6...json    # Geocoding responses
│   └── ...
├── greatschools/
│   ├── 9f8e7d6c5b4a...json    # School ratings
│   └── ...
└── maricopa_assessor/
    ├── 1a2b3c4d5e6f...json    # Property data
    └── ...
```

### Downstream Consumers

Stories that will use this infrastructure:
- **E2.S2**: Maricopa County Assessor API (refactor existing `MaricopaAssessorClient`)
- **E2.S5**: Google Maps API Geographic Data
- **E2.S6**: GreatSchools API School Ratings

### References

| Reference | Location |
|-----------|----------|
| Epic Story Definition | `docs/epics/epic-2-property-data-acquisition.md:94-106` |
| PRD FR58 | `docs/FR_COVERAGE_MATRIX/fr-coverage-matrix.md:62` (API auth via env secrets) |
| PRD FR59 | `docs/FR_COVERAGE_MATRIX/fr-coverage-matrix.md:63` (rate limit handling) |
| PRD FR60 | `docs/FR_COVERAGE_MATRIX/fr-coverage-matrix.md:64` (response caching) |
| E1.S6 Retry Decorator | `src/phx_home_analysis/errors/retry.py:280-367` |
| Existing Assessor Client | `src/phx_home_analysis/services/county_data/assessor_client.py:71-200` |
| Existing FEMA Client | `src/phx_home_analysis/services/flood_data/client.py:19-100` |
| Existing Data Cache | `src/phx_home_analysis/services/data_cache.py:1-319` |

### Related Stories

**Depends On:**
- E1.S6: Transient Error Recovery (provides `@retry_with_backoff`) - DONE

**Blocks:**
- E2.S2: Maricopa County Assessor API Integration
- E2.S5: Google Maps API Geographic Data
- E2.S6: GreatSchools API School Ratings

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Fixed `get_stats()` bug where `last_request_age_seconds` returned `None` when age was exactly `0.0` (falsy value check)

### Completion Notes List

1. **Implementation Complete** - All 9 tasks implemented:
   - Created `api_client` module with complete rate limiting, caching, and retry infrastructure
   - Integrated with existing E1.S6 `@retry_with_backoff` decorator
   - Thread-safe rate limiter with sliding window tracking
   - Atomic file cache writes to prevent corruption

2. **Test Results** - 102 tests total (87 unit + 15 integration), all passing:
   - Rate limiter: 22 tests covering config, throttling, statistics
   - Response cache: 35 tests covering keys, TTL, cleanup, edge cases
   - Base client: 30 tests covering auth, headers, params, context manager
   - Integration: 15 tests covering full request flow, retry, auth

3. **Quality Gates Passed**:
   - `ruff check`: All checks passed
   - `ruff format`: Formatted
   - `mypy`: No issues found in 4 source files

4. **Key Design Decisions**:
   - File names: Used `rate_limiter.py`, `response_cache.py`, `base_client.py` (more descriptive than original spec's `rate_limit.py`, `cache.py`, `base.py`)
   - RateLimiter: Added `reset()` method for testing support
   - ResponseCache: Added `get_entry_count()` for diagnostics
   - APIClient: Descriptive error message when not used as context manager

### File List

**New Files:**
- `src/phx_home_analysis/services/api_client/__init__.py` (56 lines)
- `src/phx_home_analysis/services/api_client/base_client.py` (405 lines)
- `src/phx_home_analysis/services/api_client/rate_limiter.py` (251 lines)
- `src/phx_home_analysis/services/api_client/response_cache.py` (330 lines)
- `tests/unit/services/api_client/__init__.py` (1 line)
- `tests/unit/services/api_client/conftest.py` (13 lines)
- `tests/unit/services/api_client/test_base_client.py` (326 lines)
- `tests/unit/services/api_client/test_rate_limiter.py` (227 lines)
- `tests/unit/services/api_client/test_response_cache.py` (408 lines)
- `tests/integration/test_api_client_integration.py` (491 lines)

**Total Lines:** 2,508 lines of production code and tests

**Modified Files:**
- None (new module)

---

**Story Created:** 2025-12-04
**Created By:** PM Agent (Claude Opus 4.5)
**Epic File:** `docs/epics/epic-2-property-data-acquisition.md:94-106`

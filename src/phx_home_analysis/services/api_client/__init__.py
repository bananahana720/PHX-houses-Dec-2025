"""API Client Infrastructure - base class with auth, rate limiting, and caching.

This module provides a robust base class for API clients that handles:
- Authentication via environment variables (never logged)
- Proactive rate limiting with configurable thresholds
- Response caching with TTL and SHA256-based cache keys
- Automatic retry with exponential backoff for transient errors

Usage:
    from phx_home_analysis.services.api_client import APIClient, RateLimit

    class GoogleMapsClient(APIClient):
        def __init__(self):
            super().__init__(
                service_name="google_maps",
                base_url="https://maps.googleapis.com/maps/api",
                env_key="GOOGLE_MAPS_API_KEY",
                rate_limit=RateLimit(requests_per_second=10),
                cache_ttl_days=7,
            )

        async def geocode(self, address: str) -> dict:
            return await self.get("/geocode/json", params={"address": address})

    # Usage
    async with GoogleMapsClient() as client:
        location = await client.geocode("123 Main St, Phoenix, AZ")

Cache Structure:
    data/api_cache/{service_name}/{cache_key}.json

Each cache file contains:
    {"data": <response>, "cached_at": <timestamp>, "url": <original_url>}

Rate Limiting:
    - Per-second, per-minute, and per-day limits supported
    - Proactive throttling at 80% of limit (configurable)
    - Thread-safe with sliding window tracking

Retry Behavior:
    - Transient errors (5xx, 429, timeouts) retried automatically
    - Exponential backoff: 1s, 2s, 4s, 8s, 16s (capped at 60s)
    - Retry-After header respected on 429 responses
"""

from .base_client import APIClient
from .rate_limiter import RateLimit, RateLimiter
from .response_cache import CacheConfig, ResponseCache

__all__ = [
    "APIClient",
    "RateLimit",
    "RateLimiter",
    "CacheConfig",
    "ResponseCache",
]

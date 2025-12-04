"""Response caching with configurable TTL.

Caches API responses to disk with hash-based keys for efficient retrieval.
Supports atomic writes to prevent cache corruption.

Cache structure:
    data/api_cache/{service_name}/{cache_key}.json

Each cache file contains:
    {"data": <response>, "cached_at": <timestamp>, "url": <original_url>, "params": <params>}

Usage:
    from phx_home_analysis.services.api_client import ResponseCache, CacheConfig

    cache = ResponseCache("google_maps", CacheConfig(ttl_days=30))

    # Check cache first
    cached = cache.get(url, params)
    if cached is not None:
        return cached

    # Make request and cache result
    response = await http_client.get(url, params=params)
    cache.set(url, params, response.json())
"""

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Default cache location relative to project root
DEFAULT_CACHE_DIR = Path("data/api_cache")


@dataclass
class CacheConfig:
    """Cache configuration.

    Attributes:
        ttl_days: Cache entry time-to-live in days (default 7).
        cache_dir: Base directory for cache files (default data/api_cache).
        enabled: Whether caching is enabled (default True).

    Example:
        # 30-day cache for slow-changing data
        config = CacheConfig(ttl_days=30)

        # Disable caching for testing
        config = CacheConfig(enabled=False)
    """

    ttl_days: int = 7
    cache_dir: Path = field(default_factory=lambda: DEFAULT_CACHE_DIR)
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        if self.ttl_days < 0:
            raise ValueError("ttl_days must be non-negative")
        # Ensure cache_dir is a Path
        if isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)


class ResponseCache:
    """Disk-based response cache with TTL.

    Caches API responses to disk with configurable time-to-live.
    Uses SHA256 hashes of URL + sorted params for cache keys.

    Cache structure:
        {cache_dir}/{service_name}/{cache_key}.json

    Features:
        - SHA256-based cache keys for URL deduplication
        - Configurable TTL with automatic expiry on read
        - Atomic writes to prevent corruption
        - Cache hit/miss statistics tracking (thread-safe)
        - Automatic expired entry cleanup

    Thread Safety:
        Individual cache operations are atomic (via temp file + rename).
        Concurrent reads are safe. Concurrent writes to same key
        result in last-write-wins behavior.
        Statistics counters are protected by a lock.

    Example:
        cache = ResponseCache("county_api", CacheConfig(ttl_days=7))

        # Cache hit returns data immediately
        data = cache.get("https://api.example.com/data", {"id": "123"})
        if data is not None:
            return data

        # Cache miss returns None
        response = await fetch_from_api(url, params)
        cache.set(url, params, response)
        return response
    """

    def __init__(self, service_name: str, config: CacheConfig | None = None) -> None:
        """Initialize response cache.

        Args:
            service_name: Name for cache subdirectory (e.g., "google_maps").
            config: Cache configuration (uses defaults if not provided).
        """
        self.service_name = service_name
        self.config = config or CacheConfig()
        self.cache_dir = self.config.cache_dir / service_name

        # Statistics (protected by lock for thread-safety)
        self._stats_lock = threading.Lock()
        self._hits = 0
        self._misses = 0

        # Ensure cache directory exists
        if self.config.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _safe_url(self, url: str) -> str:
        """Extract URL path without query parameters for safe logging.

        SECURITY: Query parameters may contain API keys or other credentials.
        This method returns only the URL path for logging purposes.

        Args:
            url: Full URL that may contain query parameters.

        Returns:
            URL path only (e.g., "https://api.example.com/data" -> "/data").
        """
        parsed = urlparse(url)
        return parsed.path or url

    def generate_key(self, url: str, params: dict | None = None) -> str:
        """Generate cache key from URL and params.

        Uses SHA256 hash of URL + sorted query params for consistent key generation.
        Sorting params ensures same params in different order produce same key.

        Args:
            url: Request URL.
            params: Query parameters (will be sorted for consistency).

        Returns:
            First 32 characters of SHA256 hash (128 bits, collision-resistant).

        Example:
            >>> cache = ResponseCache("test")
            >>> cache.generate_key("https://api.example.com/data", {"b": "2", "a": "1"})
            'a1b2c3...'  # Same key regardless of param order
        """
        # Sort params for consistent key generation
        param_str = ""
        if params:
            # Filter out None values and sort
            filtered_params = {k: v for k, v in params.items() if v is not None}
            sorted_params = sorted(filtered_params.items())
            param_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        key_input = f"{url}?{param_str}" if param_str else url
        return hashlib.sha256(key_input.encode()).hexdigest()[:32]

    def get(self, url: str, params: dict | None = None) -> Any | None:
        """Get cached response if valid.

        Returns cached data if:
        - Caching is enabled
        - Cache file exists
        - Entry has not expired (within TTL)

        Expired entries are automatically deleted on access.

        Args:
            url: Original request URL.
            params: Original query parameters.

        Returns:
            Cached response data if valid, None if miss or expired.
        """
        if not self.config.enabled:
            return None

        key = self.generate_key(url, params)
        cache_file = self.cache_dir / f"{key}.json"
        safe_url = self._safe_url(url)

        if not cache_file.exists():
            with self._stats_lock:
                self._misses += 1
            logger.debug(f"Cache MISS: {safe_url} (key: {key[:8]}...)")
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                entry = json.load(f)

            # Check TTL
            cached_at = entry.get("cached_at", 0)
            age_seconds = time.time() - cached_at
            age_days = age_seconds / 86400

            if age_days > self.config.ttl_days:
                with self._stats_lock:
                    self._misses += 1
                logger.debug(f"Cache EXPIRED: {safe_url} (age: {age_days:.1f} days)")
                # Clean up expired entry
                try:
                    cache_file.unlink()
                except OSError:
                    pass
                return None

            with self._stats_lock:
                self._hits += 1
            logger.debug(f"Cache HIT: {safe_url} (age: {age_days:.1f} days, key: {key[:8]}...)")
            return entry.get("data")

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Cache read error for {key[:8]}: {type(e).__name__}: {e}")
            with self._stats_lock:
                self._misses += 1
            return None

    def set(self, url: str, params: dict | None, data: Any) -> None:
        """Cache a response.

        Uses atomic write (temp file + rename) to prevent corruption
        from interrupted writes or concurrent access.

        Args:
            url: Original request URL.
            params: Original query parameters.
            data: Response data to cache (must be JSON-serializable).
        """
        if not self.config.enabled:
            return

        key = self.generate_key(url, params)
        cache_file = self.cache_dir / f"{key}.json"
        safe_url = self._safe_url(url)

        entry = {
            "data": data,
            "cached_at": time.time(),
            "url": url,
            "params": params,
        }

        try:
            # Atomic write: write to temp file, then rename
            temp_file = cache_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            temp_file.replace(cache_file)
            logger.debug(f"Cached response: {safe_url} (key: {key[:8]}...)")

        except (OSError, TypeError) as e:
            logger.warning(f"Cache write error for {key[:8]}: {type(e).__name__}: {e}")
            # Clean up temp file if it exists
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except OSError:
                pass

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache performance metrics:
                - total_requests: Total get() calls
                - cache_hits: Successful cache retrievals
                - cache_misses: Cache misses (not found or expired)
                - hit_rate_percent: Hit rate as percentage (0-100)
                - cache_dir: Path to cache directory
        """
        with self._stats_lock:
            hits = self._hits
            misses = self._misses

        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0.0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_dir": str(self.cache_dir),
        }

    def clear(self) -> int:
        """Clear all cached entries for this service.

        Returns:
            Number of entries cleared.
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass
        logger.info(f"Cleared {count} cache entries for {self.service_name}")
        return count

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Scans all cache entries and removes those past their TTL.
        This is a maintenance operation that can be run periodically.

        Returns:
            Number of entries removed.
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
            except (json.JSONDecodeError, KeyError, OSError):
                # Remove corrupted entries
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass

        if count > 0:
            logger.info(f"Cleaned up {count} expired entries for {self.service_name}")
        return count

    def get_entry_count(self) -> int:
        """Get count of cached entries.

        Returns:
            Number of cache files in the cache directory.
        """
        return len(list(self.cache_dir.glob("*.json")))


__all__ = ["CacheConfig", "ResponseCache", "DEFAULT_CACHE_DIR"]

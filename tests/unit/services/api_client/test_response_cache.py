"""Unit tests for ResponseCache and CacheConfig.

Tests cover:
- Cache key generation with SHA256 hashing
- Cache set/get with TTL enforcement
- Expired entry cleanup
- Cache statistics tracking
- Atomic write safety
"""

import json
import time
from pathlib import Path

import pytest

from phx_home_analysis.services.api_client.response_cache import (
    CacheConfig,
    ResponseCache,
)


class TestCacheConfig:
    """Tests for CacheConfig configuration dataclass."""

    def test_default_values(self) -> None:
        """Default cache config should have sensible defaults."""
        config = CacheConfig()
        assert config.ttl_days == 7
        assert config.enabled is True

    def test_custom_ttl(self) -> None:
        """TTL should be configurable."""
        config = CacheConfig(ttl_days=30)
        assert config.ttl_days == 30

    def test_custom_cache_dir(self, tmp_path: Path) -> None:
        """Cache directory should be configurable."""
        config = CacheConfig(cache_dir=tmp_path)
        assert config.cache_dir == tmp_path

    def test_disabled_cache(self) -> None:
        """Cache can be disabled."""
        config = CacheConfig(enabled=False)
        assert config.enabled is False

    def test_invalid_ttl_negative(self) -> None:
        """Negative TTL should raise ValueError."""
        with pytest.raises(ValueError, match="ttl_days"):
            CacheConfig(ttl_days=-1)

    def test_string_cache_dir_converted_to_path(self) -> None:
        """String cache_dir should be converted to Path."""
        config = CacheConfig(cache_dir="/tmp/test_cache")  # type: ignore[arg-type]
        assert isinstance(config.cache_dir, Path)


class TestResponseCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_cache_key_is_32_chars(self, cache: ResponseCache) -> None:
        """Cache key should be first 32 chars of SHA256 hash."""
        key = cache.generate_key("https://api.example.com/data")
        assert len(key) == 32
        assert key.isalnum()

    def test_cache_key_consistent(self, cache: ResponseCache) -> None:
        """Same URL + params should produce same key."""
        key1 = cache.generate_key("https://api.example.com/data", {"a": "1"})
        key2 = cache.generate_key("https://api.example.com/data", {"a": "1"})
        assert key1 == key2

    def test_cache_key_sorted_params(self, cache: ResponseCache) -> None:
        """Params should be sorted for consistent key generation."""
        key1 = cache.generate_key("https://api.example.com/data", {"a": "1", "b": "2"})
        key2 = cache.generate_key("https://api.example.com/data", {"b": "2", "a": "1"})
        assert key1 == key2

    def test_different_urls_different_keys(self, cache: ResponseCache) -> None:
        """Different URLs should produce different keys."""
        key1 = cache.generate_key("https://api.example.com/data1")
        key2 = cache.generate_key("https://api.example.com/data2")
        assert key1 != key2

    def test_different_params_different_keys(self, cache: ResponseCache) -> None:
        """Different params should produce different keys."""
        key1 = cache.generate_key("https://api.example.com/data", {"id": "1"})
        key2 = cache.generate_key("https://api.example.com/data", {"id": "2"})
        assert key1 != key2

    def test_none_params_handled(self, cache: ResponseCache) -> None:
        """None params should work without error."""
        key = cache.generate_key("https://api.example.com/data", None)
        assert len(key) == 32

    def test_empty_params_handled(self, cache: ResponseCache) -> None:
        """Empty params dict should work."""
        key1 = cache.generate_key("https://api.example.com/data", {})
        key2 = cache.generate_key("https://api.example.com/data", None)
        assert key1 == key2

    def test_none_param_values_filtered(self, cache: ResponseCache) -> None:
        """None values in params should be filtered out."""
        key1 = cache.generate_key("https://api.example.com/data", {"a": "1", "b": None})
        key2 = cache.generate_key("https://api.example.com/data", {"a": "1"})
        assert key1 == key2


class TestResponseCacheOperations:
    """Tests for cache set/get operations."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_cache_miss_returns_none(self, cache: ResponseCache) -> None:
        """Cache miss should return None."""
        result = cache.get("https://api.example.com/missing")
        assert result is None

    def test_set_and_get_roundtrip(self, cache: ResponseCache) -> None:
        """Set and get should work correctly."""
        url = "https://api.example.com/data"
        data = {"result": "success", "items": [1, 2, 3]}

        cache.set(url, None, data)
        result = cache.get(url, None)

        assert result == data

    def test_set_and_get_with_params(self, cache: ResponseCache) -> None:
        """Set and get with params should work correctly."""
        url = "https://api.example.com/data"
        params = {"id": "123", "format": "json"}
        data = {"id": 123, "name": "Test"}

        cache.set(url, params, data)
        result = cache.get(url, params)

        assert result == data

    def test_cache_file_created(self, cache: ResponseCache) -> None:
        """Cache file should be created in cache directory."""
        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        cache_files = list(cache.cache_dir.glob("*.json"))
        assert len(cache_files) == 1

    def test_cache_file_contains_metadata(self, cache: ResponseCache) -> None:
        """Cache file should contain data, cached_at, url fields."""
        url = "https://api.example.com/data"
        params = {"key": "value"}
        data = {"test": True}

        cache.set(url, params, data)

        key = cache.generate_key(url, params)
        cache_file = cache.cache_dir / f"{key}.json"

        with open(cache_file) as f:
            entry = json.load(f)

        assert entry["data"] == data
        assert "cached_at" in entry
        assert entry["url"] == url
        assert entry["params"] == params

    def test_expired_entry_returns_none(self, cache: ResponseCache) -> None:
        """Expired cache entry should return None."""
        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        # Manually expire the entry by backdating cached_at
        key = cache.generate_key(url, None)
        cache_file = cache.cache_dir / f"{key}.json"

        with open(cache_file) as f:
            entry = json.load(f)

        entry["cached_at"] = time.time() - (cache.config.ttl_days * 86400 + 1)

        with open(cache_file, "w") as f:
            json.dump(entry, f)

        result = cache.get(url, None)
        assert result is None

    def test_expired_entry_deleted_on_access(self, cache: ResponseCache) -> None:
        """Expired cache entry should be deleted when accessed."""
        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        # Manually expire the entry
        key = cache.generate_key(url, None)
        cache_file = cache.cache_dir / f"{key}.json"

        with open(cache_file) as f:
            entry = json.load(f)
        entry["cached_at"] = time.time() - (cache.config.ttl_days * 86400 + 1)
        with open(cache_file, "w") as f:
            json.dump(entry, f)

        # Access the cache (triggers deletion)
        cache.get(url, None)

        # File should be deleted
        assert not cache_file.exists()

    def test_disabled_cache_returns_none(self, tmp_path: Path) -> None:
        """Disabled cache should always return None."""
        config = CacheConfig(cache_dir=tmp_path, enabled=False)
        cache = ResponseCache("test_service", config)

        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        result = cache.get(url, None)
        assert result is None

    def test_disabled_cache_no_files_created(self, tmp_path: Path) -> None:
        """Disabled cache should not create files."""
        config = CacheConfig(cache_dir=tmp_path, enabled=False)
        cache = ResponseCache("test_service", config)

        cache.set("https://api.example.com/data", None, {"test": True})

        cache_files = list(tmp_path.glob("**/*.json"))
        assert len(cache_files) == 0


class TestResponseCacheStatistics:
    """Tests for cache statistics tracking."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_initial_stats_zero(self, cache: ResponseCache) -> None:
        """Initial stats should show zero requests."""
        stats = cache.get_stats()
        assert stats["total_requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percent"] == 0.0

    def test_cache_miss_increments_misses(self, cache: ResponseCache) -> None:
        """Cache miss should increment miss count."""
        cache.get("https://api.example.com/missing")

        stats = cache.get_stats()
        assert stats["total_requests"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_hits"] == 0

    def test_cache_hit_increments_hits(self, cache: ResponseCache) -> None:
        """Cache hit should increment hit count."""
        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        cache.get(url, None)  # Hit

        stats = cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0

    def test_hit_rate_calculation(self, cache: ResponseCache) -> None:
        """Hit rate should be calculated correctly."""
        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        # 1 miss, 1 hit = 50% hit rate
        cache.get("https://api.example.com/miss")  # Miss
        cache.get(url, None)  # Hit

        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 50.0

    def test_stats_include_cache_dir(self, cache: ResponseCache) -> None:
        """Stats should include cache directory path."""
        stats = cache.get_stats()
        assert "cache_dir" in stats
        assert cache.service_name in stats["cache_dir"]


class TestResponseCacheCleanup:
    """Tests for cache cleanup operations."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_clear_removes_all_entries(self, cache: ResponseCache) -> None:
        """Clear should remove all cache entries."""
        cache.set("https://api.example.com/1", None, {"data": 1})
        cache.set("https://api.example.com/2", None, {"data": 2})
        cache.set("https://api.example.com/3", None, {"data": 3})

        count = cache.clear()

        assert count == 3
        assert cache.get_entry_count() == 0

    def test_cleanup_expired_removes_old_entries(self, cache: ResponseCache) -> None:
        """Cleanup should remove expired entries."""
        # Create an expired entry
        url = "https://api.example.com/old"
        cache.set(url, None, {"old": True})

        key = cache.generate_key(url, None)
        cache_file = cache.cache_dir / f"{key}.json"

        with open(cache_file) as f:
            entry = json.load(f)
        entry["cached_at"] = time.time() - (cache.config.ttl_days * 86400 + 1)
        with open(cache_file, "w") as f:
            json.dump(entry, f)

        # Create a fresh entry
        cache.set("https://api.example.com/new", None, {"new": True})

        # Cleanup
        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get_entry_count() == 1

    def test_get_entry_count(self, cache: ResponseCache) -> None:
        """Entry count should reflect cached entries."""
        assert cache.get_entry_count() == 0

        cache.set("https://api.example.com/1", None, {"data": 1})
        assert cache.get_entry_count() == 1

        cache.set("https://api.example.com/2", None, {"data": 2})
        assert cache.get_entry_count() == 2


class TestResponseCacheEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> ResponseCache:
        """Create cache with temp directory."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=1)
        return ResponseCache("test_service", config)

    def test_corrupted_cache_file_handled(
        self, cache: ResponseCache, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Corrupted cache file should be handled gracefully."""
        url = "https://api.example.com/data"
        key = cache.generate_key(url, None)
        cache_file = cache.cache_dir / f"{key}.json"

        # Write corrupted JSON
        with open(cache_file, "w") as f:
            f.write("not valid json{{{")

        result = cache.get(url, None)
        assert result is None
        assert "Cache read error" in caplog.text

    def test_cache_directory_created_on_init(self, tmp_path: Path) -> None:
        """Cache directory should be created on initialization."""
        cache_dir = tmp_path / "new_cache"
        config = CacheConfig(cache_dir=cache_dir)
        cache = ResponseCache("test_service", config)

        assert cache.cache_dir.exists()

    def test_complex_data_cached(self, cache: ResponseCache) -> None:
        """Complex nested data should be cached correctly."""
        url = "https://api.example.com/complex"
        data = {
            "list": [1, 2, {"nested": True}],
            "dict": {"a": {"b": {"c": 3}}},
            "unicode": "Hello, World!",
            "null": None,
            "bool": True,
        }

        cache.set(url, None, data)
        result = cache.get(url, None)

        assert result == data

    def test_special_characters_in_url(self, cache: ResponseCache) -> None:
        """URLs with special characters should be cached correctly."""
        url = "https://api.example.com/data?query=hello world&filter=a+b"
        data = {"result": "ok"}

        cache.set(url, None, data)
        result = cache.get(url, None)

        assert result == data

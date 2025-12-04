---
last_updated: 2025-12-04
updated_by: Claude (Main)
staleness_hours: 24
flags: []
---
# api_client

## Purpose

Provides rate limiting and response caching infrastructure for API clients. Offers token bucket-based rate limiting with proactive throttling and disk-based response cache with TTL support for efficient API integration across external data sources (County Assessor, GreatSchools, etc.).

## Contents

| Path | Purpose |
|------|---------|
| `rate_limiter.py` | Token bucket rate limiter with proactive throttling; RateLimit config, RateLimiter class |
| `response_cache.py` | Disk-based response cache with SHA256 keys and TTL; CacheConfig, ResponseCache classes |

## Public Interfaces

### rate_limiter.py
- `RateLimit` - Configuration dataclass (requests_per_second, requests_per_minute, requests_per_day, throttle_threshold, min_delay)
- `RateLimiter` - Main rate limiter (acquire(), get_stats(), reset())

### response_cache.py
- `CacheConfig` - Configuration dataclass (ttl_days, cache_dir, enabled)
- `ResponseCache` - Caching implementation (get(), set(), generate_key(), get_stats(), clear(), cleanup_expired())
- `DEFAULT_CACHE_DIR` - Default cache location (data/api_cache)

## Tasks
- [x] Document rate limiting architecture (token bucket, proactive throttling)
- [x] Document response cache architecture (SHA256 keys, atomic writes, TTL)
- [ ] Add examples for usage with httpx/aiohttp clients P:M
- [ ] Integrate cache prewarming for high-latency APIs P:L

## Learnings
- **Token bucket + proactive throttling**: RateLimiter triggers at configurable threshold (default 80%) before hitting hard limits to prevent rate limit errors
- **Atomic cache writes**: Uses temp file + rename pattern to prevent corruption from concurrent writes or interruptions
- **Per-second/minute/day limits**: Flexible configuration supports sliding windows (per-minute) and daily resets (per-day)
- **Thread-safe operations**: Lock-protected state in RateLimiter; atomic ops in ResponseCache
- **Cache key deduplication**: SHA256 hashing of URL + sorted params ensures consistent keys regardless of parameter order

## Refs
- Rate limiter token bucket: `rate_limiter.py:61-187`
- Proactive throttling logic: `rate_limiter.py:143-156`
- Cache TTL expiry: `response_cache.py:186-199`
- Atomic write pattern: `response_cache.py:234-249`
- Cache statistics: `rate_limiter.py:205-232`, `response_cache.py:251-271`

## Deps

← Imports from:
  - `asyncio` (async sleep)
  - `threading` (locks)
  - `pathlib` (cache directory)
  - `json` (cache serialization)
  - `hashlib` (SHA256 keys)
  - `time` (timestamps)

→ Imported by:
  - `src/phx_home_analysis/services/image_extraction/extractors/` (rate limit error handling)
  - Potential: County API clients, GreatSchools clients, external data sources

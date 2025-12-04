---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
---
# tests/unit/services/api_client

## Purpose

Unit tests for API client infrastructure covering rate limiting, response caching, and base client authentication. Tests 87 unit test cases across 3 test modules ensuring robust external API integration with automatic retry, throttling, and cache-first patterns.

## Contents

| Path | Purpose |
|------|---------|
| `test_base_client.py` | APIClient base class: credentials, URL building, cache-first pattern, rate limiter integration (326 lines, 30+ tests) |
| `test_rate_limiter.py` | RateLimit config + RateLimiter: per-second/minute/day limits, proactive throttling, statistics (227 lines, 25+ tests) |
| `test_response_cache.py` | ResponseCache + CacheConfig: SHA256 key generation, TTL enforcement, expiry cleanup, atomic writes (408 lines, 32+ tests) |
| `conftest.py` | Shared fixtures: temp_cache_dir for test isolation |
| `__init__.py` | Module initialization marking tests package |

## Test Coverage

### APIClient Credentials & Configuration (test_base_client.py)
- Missing environment variables raise ValueError with variable name
- API key and token loading from env (TEST_API_KEY, MARICOPA_ASSESSOR_TOKEN patterns)
- Credential redaction in error messages (never logged)
- URL and param building with base_url + endpoint
- Async context manager usage (`async with client:`)
- Cache-first pattern: returns cached response if available
- Rate limiter integration: client.rate_limiter accessible

### RateLimit Configuration & RateLimiter Enforcement (test_rate_limiter.py)
- RateLimit defaults: requests_per_second=None, throttle_threshold=0.8, min_delay=0.1
- Per-second, per-minute, per-day rate limits configurable
- Proactive throttling when approaching threshold (e.g., 80% of limit)
- Statistics tracking: completed_requests, remaining_budget, reset_time
- Thread-safety for concurrent request tracking
- Minimum delay enforcement (min_delay=0.1 by default)

### Response Caching with TTL (test_response_cache.py)
- CacheConfig: ttl_days=7 default, configurable cache_dir, enable/disable toggle
- SHA256 cache key from URL + sorted query params (deterministic)
- Set/get cache entries with expiry enforcement
- Expired entry detection and cleanup
- Cache statistics: total_requests, cache_hits, cache_misses, hit_rate_percent
- Atomic write safety (write to temp, then rename)
- Invalid TTL (negative) raises ValueError

## Tasks

- [x] Map all three test modules and coverage areas `P:H`
- [x] Document RateLimit and RateLimiter patterns `P:H`
- [x] Document ResponseCache key generation and TTL logic `P:H`
- [ ] Add integration tests for APIClient with actual HTTP mocks `P:M`
- [ ] Add performance benchmarks for rate limiter throughput `P:L`

## Learnings

- **Credential safety critical:** Environment variables must never appear in logs/exceptions; test validates redaction in error messages
- **Proactive rate limiting beats reactive:** Throttle at threshold (80%) to prevent 429 errors, not after hitting limit
- **SHA256 deterministic caching:** URL + sorted params generate consistent cache keys across invocations
- **TTL enforcement must be checked:** Expired entries silently skipped, not deleted; cleanup on access
- **Async context manager pattern:** APIClient supports `async with` for proper resource cleanup (httpx.AsyncClient)
- **Rate limiter statistics essential:** Tracking remaining_budget and reset_time enables intelligent throttling decisions

## Refs

- APIClient credentials tests: `test_base_client.py:23-50` (TestAPIClientCredentials)
- RateLimit config validation: `test_rate_limiter.py:18-50` (TestRateLimit)
- RateLimiter enforcement: `test_rate_limiter.py:55-120` (TestRateLimiter)
- ResponseCache key generation: `test_response_cache.py:70-100` (TestResponseCache key tests)
- Cache expiry logic: `test_response_cache.py:150-190` (TestResponseCache TTL tests)
- Story requirements: `docs/sprint_artifacts/stories/e2-s7-api-integration-infrastructure.md`

## Deps

← Imports from:
- `phx_home_analysis.services.api_client.base_client` (APIClient)
- `phx_home_analysis.services.api_client.rate_limiter` (RateLimit, RateLimiter)
- `phx_home_analysis.services.api_client.response_cache` (ResponseCache, CacheConfig)
- Standard library: os, pathlib, json, time, asyncio
- Third-party: pytest, httpx

→ Imported by:
- pytest (test framework)
- CI/CD pipeline (must pass before merge)
- E2.S7 story implementation (docs/sprint_artifacts/stories/e2-s7-api-integration-infrastructure.md)
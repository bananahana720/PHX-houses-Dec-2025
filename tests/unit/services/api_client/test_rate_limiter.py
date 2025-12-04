"""Unit tests for RateLimit and RateLimiter.

Tests cover:
- RateLimit configuration and validation
- Per-second, per-minute, and per-day rate limiting
- Proactive throttling at configurable thresholds
- Thread-safety and statistics tracking
"""

import asyncio
import time

import pytest

from phx_home_analysis.services.api_client.rate_limiter import RateLimit, RateLimiter


class TestRateLimit:
    """Tests for RateLimit configuration dataclass."""

    def test_default_values(self) -> None:
        """Default rate limit should have sensible defaults."""
        rl = RateLimit()
        assert rl.requests_per_second is None
        assert rl.requests_per_minute is None
        assert rl.requests_per_day is None
        assert rl.throttle_threshold == 0.8
        assert rl.min_delay == 0.1

    def test_per_second_config(self) -> None:
        """Per-second rate limit should be configurable."""
        rl = RateLimit(requests_per_second=10.0)
        assert rl.requests_per_second == 10.0

    def test_per_minute_config(self) -> None:
        """Per-minute rate limit should be configurable."""
        rl = RateLimit(requests_per_minute=60.0)
        assert rl.requests_per_minute == 60.0

    def test_per_day_config(self) -> None:
        """Per-day rate limit should be configurable."""
        rl = RateLimit(requests_per_day=1000)
        assert rl.requests_per_day == 1000

    def test_custom_throttle_threshold(self) -> None:
        """Throttle threshold should be configurable."""
        rl = RateLimit(throttle_threshold=0.9)
        assert rl.throttle_threshold == 0.9

    def test_custom_min_delay(self) -> None:
        """Minimum delay should be configurable."""
        rl = RateLimit(min_delay=0.5)
        assert rl.min_delay == 0.5

    def test_invalid_throttle_threshold_zero(self) -> None:
        """Throttle threshold of 0 should raise ValueError."""
        with pytest.raises(ValueError, match="throttle_threshold"):
            RateLimit(throttle_threshold=0)

    def test_invalid_throttle_threshold_negative(self) -> None:
        """Negative throttle threshold should raise ValueError."""
        with pytest.raises(ValueError, match="throttle_threshold"):
            RateLimit(throttle_threshold=-0.1)

    def test_invalid_throttle_threshold_over_one(self) -> None:
        """Throttle threshold over 1 should raise ValueError."""
        with pytest.raises(ValueError, match="throttle_threshold"):
            RateLimit(throttle_threshold=1.1)

    def test_invalid_min_delay_negative(self) -> None:
        """Negative min_delay should raise ValueError."""
        with pytest.raises(ValueError, match="min_delay"):
            RateLimit(min_delay=-0.1)

    def test_combined_limits(self) -> None:
        """Multiple limits can be configured together."""
        rl = RateLimit(
            requests_per_second=5.0,
            requests_per_minute=100.0,
            requests_per_day=10000,
        )
        assert rl.requests_per_second == 5.0
        assert rl.requests_per_minute == 100.0
        assert rl.requests_per_day == 10000


class TestRateLimiter:
    """Tests for RateLimiter behavior."""

    @pytest.mark.asyncio
    async def test_min_delay_applied(self) -> None:
        """Minimum delay should be applied between requests."""
        limiter = RateLimiter(RateLimit(min_delay=0.05))

        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        # Second request should wait at least min_delay
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_per_second_rate_limit(self) -> None:
        """Per-second rate limit should space requests appropriately."""
        # 2 requests per second = 0.5s minimum interval
        limiter = RateLimiter(RateLimit(requests_per_second=2.0, min_delay=0.0))

        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        # 2 req/sec = 0.5s between requests (allow small timing variance)
        assert elapsed >= 0.45

    @pytest.mark.asyncio
    async def test_proactive_throttling_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Proactive throttling should log warning when approaching limit."""
        # 5 requests per minute, throttle at 60% = 3 requests
        limiter = RateLimiter(
            RateLimit(requests_per_minute=5, throttle_threshold=0.6, min_delay=0.0)
        )

        # Make 4 requests to trigger throttling
        for _ in range(4):
            await limiter.acquire()

        # Check for throttling warning in logs
        assert "Proactive throttling" in caplog.text

    @pytest.mark.asyncio
    async def test_daily_limit_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Daily limit should log warning when approaching threshold."""
        # 10 requests per day, throttle at 80% = 8 requests
        limiter = RateLimiter(
            RateLimit(requests_per_day=10, throttle_threshold=0.8, min_delay=0.0)
        )

        # Make 9 requests to trigger warning
        for _ in range(9):
            await limiter.acquire()

        assert "Daily limit approaching" in caplog.text

    def test_get_stats_initial(self) -> None:
        """Initial stats should show zero requests."""
        limiter = RateLimiter(RateLimit())
        stats = limiter.get_stats()

        assert stats["requests_last_minute"] == 0
        assert stats["requests_today"] == 0
        assert stats["last_request_age_seconds"] is None

    def test_get_stats_after_requests(self) -> None:
        """Stats should track request counts correctly."""
        limiter = RateLimiter(RateLimit())
        limiter._record_request()
        limiter._record_request()

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 2
        assert stats["requests_today"] == 2
        assert stats["last_request_age_seconds"] is not None

    def test_get_stats_with_daily_limit(self) -> None:
        """Stats should include remaining daily requests when limit set."""
        limiter = RateLimiter(RateLimit(requests_per_day=100))
        limiter._record_request()
        limiter._record_request()

        stats = limiter.get_stats()
        assert stats["daily_limit_remaining"] == 98

    def test_reset(self) -> None:
        """Reset should clear all tracking state."""
        limiter = RateLimiter(RateLimit(requests_per_day=100))
        limiter._record_request()
        limiter._record_request()

        limiter.reset()

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 0
        assert stats["requests_today"] == 0
        assert stats["last_request_age_seconds"] is None

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self) -> None:
        """Concurrent acquire calls should be handled safely."""
        limiter = RateLimiter(RateLimit(min_delay=0.01))

        # Run multiple concurrent acquires
        async def acquire_and_record() -> None:
            await limiter.acquire()

        tasks = [acquire_and_record() for _ in range(5)]
        await asyncio.gather(*tasks)

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 5

    def test_request_times_pruning(self) -> None:
        """Old request times should be pruned to prevent memory growth."""
        limiter = RateLimiter(RateLimit())

        # Simulate old requests by directly modifying internal state
        old_time = time.time() - 400  # 400 seconds ago (outside 5-min window)
        limiter._request_times = [old_time] * 10

        # Record a new request, which should prune old times
        limiter._record_request()

        # Only the new request should remain
        assert len(limiter._request_times) == 1

    @pytest.mark.asyncio
    async def test_zero_delay_when_not_rate_limited(self) -> None:
        """First request should have only min_delay."""
        limiter = RateLimiter(RateLimit(requests_per_minute=1000, min_delay=0.0))

        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # First request should be nearly instant
        assert elapsed < 0.05

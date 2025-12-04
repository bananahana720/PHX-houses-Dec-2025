"""Rate limiting with proactive throttling.

Tracks request counts and proactively throttles before hitting limits.
Implements token bucket algorithm with sliding windows for accurate rate tracking.

Usage:
    from phx_home_analysis.services.api_client import RateLimit, RateLimiter

    limiter = RateLimiter(RateLimit(requests_per_second=10.0))

    async def make_request():
        await limiter.acquire()  # Blocks until request is allowed
        # Make API call...
"""

import asyncio
import datetime
import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration with proactive throttling.

    Supports per-second, per-minute, and per-day rate limits.
    Proactive throttling triggers at configurable threshold before hitting limits.

    Attributes:
        requests_per_second: Max requests per second (e.g., 1.0 for 1 req/sec).
        requests_per_minute: Max requests per minute (alternative to per-second).
        requests_per_day: Max requests per day (for daily-capped APIs like GreatSchools).
        throttle_threshold: Percentage of limit to trigger proactive throttling (default 0.8).
        min_delay: Minimum delay between requests in seconds (default 0.1).

    Example:
        # 10 requests per second with proactive throttling at 80%
        limit = RateLimit(requests_per_second=10.0)

        # Daily limit for GreatSchools API
        limit = RateLimit(requests_per_day=1000, throttle_threshold=0.9)
    """

    requests_per_second: float | None = None
    requests_per_minute: float | None = None
    requests_per_day: int | None = None
    throttle_threshold: float = 0.8
    min_delay: float = 0.1

    def __post_init__(self) -> None:
        """Validate rate limit configuration."""
        if self.throttle_threshold <= 0 or self.throttle_threshold > 1:
            raise ValueError("throttle_threshold must be between 0 (exclusive) and 1 (inclusive)")
        if self.min_delay < 0:
            raise ValueError("min_delay must be non-negative")


class RateLimiter:
    """Tracks request counts and applies rate limiting.

    Implements token bucket algorithm with proactive throttling.
    Thread-safe for concurrent access.

    Features:
        - Per-second rate limiting with minimum interval enforcement
        - Per-minute rate limiting with sliding window tracking
        - Per-day rate limiting with automatic daily reset
        - Proactive throttling before hitting actual limits
        - Thread-safe operations with lock protection

    Usage:
        limiter = RateLimiter(RateLimit(requests_per_minute=60))

        async def make_request():
            await limiter.acquire()  # Blocks until allowed
            response = await http_client.get(url)
            return response
    """

    def __init__(self, config: RateLimit) -> None:
        """Initialize rate limiter with configuration.

        Args:
            config: Rate limit configuration specifying limits and thresholds.
        """
        self.config = config
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._last_request_time: float = 0.0
        self._request_times: list[float] = []
        self._daily_count: int = 0
        self._daily_reset: float = self._calculate_next_midnight()

    def _calculate_next_midnight(self) -> float:
        """Calculate timestamp for next midnight (local time)."""

        now = datetime.datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow += datetime.timedelta(days=1)
        return tomorrow.timestamp()

    async def acquire(self) -> None:
        """Wait until a request is allowed.

        Implements proactive throttling before hitting actual limits.
        Blocks the caller until the rate limit permits a new request.

        This method is safe to call concurrently from multiple coroutines.
        Uses asyncio.Lock to ensure atomic delay calculation and request recording.
        """
        async with self._async_lock:
            now = time.time()

            # Calculate required delay
            delay = self._calculate_delay(now)
            if delay > 0:
                logger.debug(f"Rate limiter: waiting {delay:.2f}s before request")
                await asyncio.sleep(delay)

            # Record this request (atomically with delay calculation)
            self._record_request()

    def _calculate_delay(self, now: float) -> float:
        """Calculate delay needed before next request.

        Args:
            now: Current timestamp.

        Returns:
            Delay in seconds (0.0 if no delay needed).
        """
        delay = 0.0

        with self._lock:
            # Per-second rate limit: enforce minimum interval
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
                    # Proactive throttling: add delay proportional to congestion
                    congestion_delay = 60.0 / self.config.requests_per_minute
                    delay = max(delay, congestion_delay)
                    logger.warning(
                        f"Proactive throttling: {len(recent)}/{int(self.config.requests_per_minute)} "
                        f"requests in last minute (threshold: {threshold})"
                    )

                # Hard limit: if at capacity, wait for oldest request to expire
                if len(recent) >= int(self.config.requests_per_minute):
                    oldest = min(recent)
                    wait_until = oldest + 60.0
                    delay = max(delay, wait_until - now)

            # Per-day rate limit
            if self.config.requests_per_day:
                # Reset daily counter at midnight
                if now >= self._daily_reset:
                    self._daily_count = 0
                    self._daily_reset = self._calculate_next_midnight()

                threshold = int(self.config.requests_per_day * self.config.throttle_threshold)
                if self._daily_count >= threshold:
                    logger.warning(
                        f"Daily limit approaching: {self._daily_count}/{self.config.requests_per_day} "
                        f"(threshold: {threshold})"
                    )

                # Hard limit: block if at daily capacity
                if self._daily_count >= self.config.requests_per_day:
                    wait_until_reset = self._daily_reset - now
                    logger.error(
                        f"Daily limit reached ({self._daily_count}/{self.config.requests_per_day}). "
                        f"Requests blocked until midnight ({wait_until_reset:.0f}s)."
                    )
                    delay = max(delay, wait_until_reset)

        return max(delay, self.config.min_delay)

    def _record_request(self) -> None:
        """Record a request for rate tracking.

        Thread-safe operation protected by lock.
        """
        now = time.time()

        with self._lock:
            self._last_request_time = now
            self._request_times.append(now)
            self._daily_count += 1

            # Prune old request times (keep last 5 minutes for sliding window)
            cutoff = now - 300
            self._request_times = [t for t in self._request_times if t > cutoff]

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dict with current rate limit statistics:
                - requests_last_minute: Requests in the last 60 seconds
                - requests_today: Requests since midnight
                - last_request_age_seconds: Seconds since last request (or None)
                - daily_limit_remaining: Remaining daily requests (if daily limit set)
        """
        now = time.time()

        with self._lock:
            requests_last_minute = len([t for t in self._request_times if t > now - 60])

            # Calculate last request age (None if no requests made)
            if self._last_request_time > 0:
                last_age: float | None = round(now - self._last_request_time, 2)
            else:
                last_age = None

            stats = {
                "requests_last_minute": requests_last_minute,
                "requests_today": self._daily_count,
                "last_request_age_seconds": last_age,
            }

            if self.config.requests_per_day:
                stats["daily_limit_remaining"] = max(
                    0, self.config.requests_per_day - self._daily_count
                )

            return stats

    def reset(self) -> None:
        """Reset all rate limiter state.

        Useful for testing or when rate limit windows should be cleared.
        Note: This creates a new async lock to ensure clean state.
        """
        with self._lock:
            self._last_request_time = 0.0
            self._request_times = []
            self._daily_count = 0
            self._daily_reset = self._calculate_next_midnight()
        # Create new async lock to ensure clean state
        self._async_lock = asyncio.Lock()


__all__ = ["RateLimit", "RateLimiter"]

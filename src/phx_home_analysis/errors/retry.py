"""Retry decorator with exponential backoff for transient errors.

Provides a decorator for async functions that automatically retries
on transient errors with configurable exponential backoff.

Usage:
    from phx_home_analysis.errors.retry import retry_with_backoff

    @retry_with_backoff(max_retries=5, min_delay=1.0)
    async def fetch_data(url: str) -> dict:
        response = await http_client.get(url)
        return response.json()

The decorator respects the tenacity library patterns but is
implemented standalone for control and testing.
"""

import asyncio
import functools
import logging
import os
import random
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from . import format_error_message, is_transient_error

# Environment variable defaults (can be overridden by env vars)
DEFAULT_MAX_RETRIES = 5
DEFAULT_MIN_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0
DEFAULT_JITTER = 0.5


def _get_env_int(name: str, default: int) -> int:
    """Get integer from environment variable with fallback."""
    value = os.environ.get(name)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            logging.getLogger(__name__).warning(
                f"Invalid integer for {name}={value!r}, using default={default}"
            )
    return default


def _get_env_float(name: str, default: float) -> float:
    """Get float from environment variable with fallback."""
    value = os.environ.get(name)
    if value is not None:
        try:
            return float(value)
        except ValueError:
            logging.getLogger(__name__).warning(
                f"Invalid float for {name}={value!r}, using default={default}"
            )
    return default


logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def retry_with_backoff(
    max_retries: int | None = None,
    min_delay: float | None = None,
    max_delay: float | None = None,
    jitter: float | None = None,
    retry_on: Callable[[Exception], bool] | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for async functions with exponential backoff retry.

    Automatically retries the decorated function when transient errors occur,
    using exponential backoff with jitter to prevent thundering herd.

    Args:
        max_retries: Maximum number of retry attempts. Defaults to RETRY_MAX_RETRIES env var
                     or 5 if not set.
        min_delay: Initial delay between retries in seconds. Defaults to RETRY_MIN_DELAY
                   env var or 1.0 if not set.
        max_delay: Maximum delay cap in seconds. Defaults to RETRY_MAX_DELAY env var
                   or 60.0 if not set.
        jitter: Randomization factor for delays, 0-1. Defaults to RETRY_JITTER env var
                or 0.5 if not set.
        retry_on: Optional custom function to determine if error is retryable.
                  Defaults to is_transient_error().

    Environment Variables:
        RETRY_MAX_RETRIES: Override default max_retries (integer)
        RETRY_MIN_DELAY: Override default min_delay (float, seconds)
        RETRY_MAX_DELAY: Override default max_delay (float, seconds)
        RETRY_JITTER: Override default jitter (float, 0-1)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_retries=3, min_delay=2.0)
        async def call_api():
            ...

    Backoff sequence (with jitter=0.5):
        Attempt 1 failure: wait 1.0-1.5s
        Attempt 2 failure: wait 2.0-3.0s
        Attempt 3 failure: wait 4.0-6.0s
        Attempt 4 failure: wait 8.0-12.0s
        Attempt 5 failure: wait 16.0-24.0s (capped at max_delay)
    """
    # Resolve defaults from environment variables or hardcoded defaults
    resolved_max_retries = (
        max_retries
        if max_retries is not None
        else _get_env_int("RETRY_MAX_RETRIES", DEFAULT_MAX_RETRIES)
    )
    resolved_min_delay = (
        min_delay if min_delay is not None else _get_env_float("RETRY_MIN_DELAY", DEFAULT_MIN_DELAY)
    )
    resolved_max_delay = (
        max_delay if max_delay is not None else _get_env_float("RETRY_MAX_DELAY", DEFAULT_MAX_DELAY)
    )
    resolved_jitter = (
        jitter if jitter is not None else _get_env_float("RETRY_JITTER", DEFAULT_JITTER)
    )

    should_retry = retry_on or is_transient_error

    def decorator(
        func: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None

            for attempt in range(resolved_max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Check if we should retry
                    if not should_retry(e):
                        logger.warning(
                            f"{func.__name__} failed with permanent error: "
                            f"{format_error_message(e)}"
                        )
                        raise

                    # Check if retries exhausted
                    if attempt >= resolved_max_retries:
                        logger.error(
                            f"{func.__name__} failed after {resolved_max_retries + 1} attempts: "
                            f"{format_error_message(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        min_delay=resolved_min_delay,
                        max_delay=resolved_max_delay,
                        jitter=resolved_jitter,
                    )

                    logger.info(
                        f"{func.__name__} transient error (attempt {attempt + 1}/"
                        f"{resolved_max_retries + 1}), retrying in {delay:.1f}s: {type(e).__name__}"
                    )

                    await asyncio.sleep(delay)

            # Should not reach here, but handle edge case
            if last_error:
                raise last_error
            raise RuntimeError(f"{func.__name__} failed with no error recorded")

        return wrapper

    return decorator


def retry_with_backoff_sync(
    max_retries: int | None = None,
    min_delay: float | None = None,
    max_delay: float | None = None,
    jitter: float | None = None,
    retry_on: Callable[[Exception], bool] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for synchronous functions with exponential backoff retry.

    Automatically retries the decorated function when transient errors occur,
    using exponential backoff with jitter to prevent thundering herd.

    This is the synchronous counterpart to retry_with_backoff() for use with
    non-async functions. It uses time.sleep() instead of asyncio.sleep().

    Args:
        max_retries: Maximum number of retry attempts. Defaults to RETRY_MAX_RETRIES env var
                     or 5 if not set.
        min_delay: Initial delay between retries in seconds. Defaults to RETRY_MIN_DELAY
                   env var or 1.0 if not set.
        max_delay: Maximum delay cap in seconds. Defaults to RETRY_MAX_DELAY env var
                   or 60.0 if not set.
        jitter: Randomization factor for delays, 0-1. Defaults to RETRY_JITTER env var
                or 0.5 if not set.
        retry_on: Optional custom function to determine if error is retryable.
                  Defaults to is_transient_error().

    Environment Variables:
        RETRY_MAX_RETRIES: Override default max_retries (integer)
        RETRY_MIN_DELAY: Override default min_delay (float, seconds)
        RETRY_MAX_DELAY: Override default max_delay (float, seconds)
        RETRY_JITTER: Override default jitter (float, 0-1)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff_sync(max_retries=3, min_delay=2.0)
        def fetch_data(url: str) -> dict:
            response = requests.get(url)
            return response.json()

    Backoff sequence (with jitter=0.5):
        Attempt 1 failure: wait 1.0-1.5s
        Attempt 2 failure: wait 2.0-3.0s
        Attempt 3 failure: wait 4.0-6.0s
        Attempt 4 failure: wait 8.0-12.0s
        Attempt 5 failure: wait 16.0-24.0s (capped at max_delay)
    """
    # Resolve defaults from environment variables or hardcoded defaults
    resolved_max_retries = (
        max_retries
        if max_retries is not None
        else _get_env_int("RETRY_MAX_RETRIES", DEFAULT_MAX_RETRIES)
    )
    resolved_min_delay = (
        min_delay if min_delay is not None else _get_env_float("RETRY_MIN_DELAY", DEFAULT_MIN_DELAY)
    )
    resolved_max_delay = (
        max_delay if max_delay is not None else _get_env_float("RETRY_MAX_DELAY", DEFAULT_MAX_DELAY)
    )
    resolved_jitter = (
        jitter if jitter is not None else _get_env_float("RETRY_JITTER", DEFAULT_JITTER)
    )

    should_retry = retry_on or is_transient_error

    def decorator(
        func: Callable[P, T],
    ) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: Exception | None = None

            for attempt in range(resolved_max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Check if we should retry
                    if not should_retry(e):
                        logger.warning(
                            f"{func.__name__} failed with permanent error: "
                            f"{format_error_message(e)}"
                        )
                        raise

                    # Check if retries exhausted
                    if attempt >= resolved_max_retries:
                        logger.error(
                            f"{func.__name__} failed after {resolved_max_retries + 1} attempts: "
                            f"{format_error_message(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        min_delay=resolved_min_delay,
                        max_delay=resolved_max_delay,
                        jitter=resolved_jitter,
                    )

                    logger.info(
                        f"{func.__name__} transient error (attempt {attempt + 1}/"
                        f"{resolved_max_retries + 1}), retrying in {delay:.1f}s: {type(e).__name__}"
                    )

                    time.sleep(delay)

            # Should not reach here, but handle edge case
            if last_error:
                raise last_error
            raise RuntimeError(f"{func.__name__} failed with no error recorded")

        return wrapper

    return decorator


def calculate_backoff_delay(
    attempt: int,
    min_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.5,
) -> float:
    """Calculate delay for exponential backoff with jitter.

    Uses the formula: delay = min(min_delay * 2^attempt, max_delay)
    Then applies jitter: delay += delay * jitter * random()

    Args:
        attempt: Current attempt number (0-indexed)
        min_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter: Randomization factor (0-1)

    Returns:
        Delay in seconds

    Examples:
        >>> calculate_backoff_delay(0, 1.0, 60.0, 0.0)  # No jitter
        1.0
        >>> calculate_backoff_delay(3, 1.0, 60.0, 0.0)  # No jitter
        8.0
    """
    # Exponential backoff: min_delay * 2^attempt
    base_delay = min_delay * (2**attempt)

    # Cap at max_delay
    delay: float = min(base_delay, max_delay)

    # Add jitter to prevent thundering herd
    if jitter > 0:
        jitter_amount: float = delay * jitter * random.random()
        delay = min(delay + jitter_amount, max_delay)

    return delay


class RetryContext:
    """Context manager for retry operations with state tracking.

    Useful for operations that need to track retry state across
    multiple calls or report retry statistics.

    Usage:
        ctx = RetryContext(max_retries=5)
        while ctx.should_retry():
            try:
                result = await operation()
                ctx.mark_success()
                break
            except Exception as e:
                if not ctx.handle_error(e):
                    raise
    """

    def __init__(
        self,
        max_retries: int = 5,
        min_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: float = 0.5,
    ) -> None:
        self.max_retries = max_retries
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.jitter = jitter

        self.attempt = 0
        self.last_error: Exception | None = None
        self.succeeded = False
        self.total_delay = 0.0

    def should_retry(self) -> bool:
        """Check if another retry attempt should be made."""
        return not self.succeeded and self.attempt <= self.max_retries

    def handle_error(self, error: Exception) -> bool:
        """Handle an error and determine if retry is appropriate.

        Returns:
            True if should retry, False if should raise
        """
        self.last_error = error
        self.attempt += 1

        if not is_transient_error(error):
            return False

        if self.attempt > self.max_retries:
            return False

        return True

    def get_delay(self) -> float:
        """Get the delay for the current retry attempt."""
        delay = calculate_backoff_delay(
            attempt=max(0, self.attempt - 1),
            min_delay=self.min_delay,
            max_delay=self.max_delay,
            jitter=self.jitter,
        )
        self.total_delay += delay
        return delay

    def mark_success(self) -> None:
        """Mark the operation as successful."""
        self.succeeded = True


__all__ = [
    "retry_with_backoff",
    "retry_with_backoff_sync",
    "calculate_backoff_delay",
    "RetryContext",
]

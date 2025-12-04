"""Unit tests for retry decorator and backoff calculation.

Tests verify:
- Exponential backoff delay calculation
- Retry decorator behavior with transient/permanent errors
- Max retry exhaustion
- Custom retry predicates
- RetryContext state management
"""

from unittest.mock import AsyncMock, patch

import pytest

from phx_home_analysis.errors.retry import (
    RetryContext,
    calculate_backoff_delay,
    retry_with_backoff,
)


class TestCalculateBackoffDelay:
    """Tests for backoff delay calculation."""

    def test_initial_delay(self) -> None:
        """First attempt should use min_delay."""
        delay = calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.0)
        assert delay == 1.0

    def test_exponential_growth(self) -> None:
        """Delay should double with each attempt."""
        delays = [
            calculate_backoff_delay(i, min_delay=1.0, max_delay=60.0, jitter=0.0)
            for i in range(5)
        ]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_max_delay_cap(self) -> None:
        """Delay should not exceed max_delay."""
        delay = calculate_backoff_delay(10, min_delay=1.0, max_delay=60.0, jitter=0.0)
        assert delay == 60.0

    def test_jitter_adds_randomness(self) -> None:
        """Jitter should add randomness to delay."""
        with patch("random.random", return_value=1.0):
            delay = calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.5)
            assert delay == 1.5  # 1.0 + (1.0 * 0.5 * 1.0)

    def test_no_jitter_when_zero(self) -> None:
        """No jitter should be added when jitter=0."""
        delays = [
            calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.0)
            for _ in range(10)
        ]
        assert all(d == 1.0 for d in delays)

    def test_custom_min_delay(self) -> None:
        """Should use custom min_delay as base."""
        delay = calculate_backoff_delay(0, min_delay=2.0, max_delay=60.0, jitter=0.0)
        assert delay == 2.0

    def test_custom_max_delay_caps_at_limit(self) -> None:
        """Should cap at custom max_delay."""
        delay = calculate_backoff_delay(5, min_delay=1.0, max_delay=10.0, jitter=0.0)
        assert delay == 10.0  # 32.0 capped to 10.0

    def test_jitter_partial_randomness(self) -> None:
        """Partial jitter should add proportional randomness."""
        with patch("random.random", return_value=0.5):
            delay = calculate_backoff_delay(1, min_delay=2.0, max_delay=60.0, jitter=0.5)
            # Base: 4.0, jitter: 4.0 * 0.5 * 0.5 = 1.0
            assert delay == 5.0


class TestRetryWithBackoff:
    """Tests for retry decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self) -> None:
        """Function should return immediately on success."""
        mock_func = AsyncMock(return_value="success")

        @retry_with_backoff(max_retries=3)
        async def func() -> str:
            return await mock_func()

        result = await func()
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self) -> None:
        """Function should retry on transient error."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self) -> None:
        """Function should not retry on permanent error."""
        mock_func = AsyncMock(side_effect=ValueError("Bad input"))

        @retry_with_backoff(max_retries=3)
        async def func() -> str:
            return await mock_func()

        with pytest.raises(ValueError, match="Bad input"):
            await func()

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self) -> None:
        """Function should raise after exhausting retries."""
        mock_func = AsyncMock(side_effect=ConnectionError("Connection failed"))

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func() -> str:
            return await mock_func()

        with pytest.raises(ConnectionError, match="Connection failed"):
            await func()

        assert mock_func.call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_custom_retry_predicate(self) -> None:
        """Custom retry_on predicate should control retry behavior."""

        def custom_retry(e: Exception) -> bool:
            return isinstance(e, RuntimeError)

        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01, retry_on=custom_retry)
        async def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary")
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_http_429_transient_retried(self) -> None:
        """HTTP 429 (rate limit) should be retried."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = Exception("Rate limited")
                error.status_code = 429  # type: ignore[attr-defined]
                raise error
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_http_401_permanent_not_retried(self) -> None:
        """HTTP 401 (unauthorized) should not be retried."""
        error = Exception("Unauthorized")
        error.status_code = 401  # type: ignore[attr-defined]
        mock_func = AsyncMock(side_effect=error)

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func() -> str:
            return await mock_func()

        with pytest.raises(Exception, match="Unauthorized"):
            await func()

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_preserves_function_name(self) -> None:
        """Decorator should preserve original function name."""

        @retry_with_backoff(max_retries=3)
        async def my_named_function() -> str:
            return "success"

        assert my_named_function.__name__ == "my_named_function"

    @pytest.mark.asyncio
    async def test_preserves_function_docstring(self) -> None:
        """Decorator should preserve original function docstring."""

        @retry_with_backoff(max_retries=3)
        async def documented_function() -> str:
            """This is my docstring."""
            return "success"

        assert documented_function.__doc__ == "This is my docstring."

    @pytest.mark.asyncio
    async def test_timeout_error_retried(self) -> None:
        """TimeoutError should be retried."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Request timed out")
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 2


class TestRetryContext:
    """Tests for RetryContext state management."""

    def test_initial_state(self) -> None:
        """Context should start with clean state."""
        ctx = RetryContext(max_retries=3)
        assert ctx.attempt == 0
        assert ctx.succeeded is False
        assert ctx.should_retry() is True
        assert ctx.last_error is None
        assert ctx.total_delay == 0.0

    def test_handle_transient_error(self) -> None:
        """Transient error should allow retry."""
        ctx = RetryContext(max_retries=3)
        result = ctx.handle_error(ConnectionError("Failed"))
        assert result is True
        assert ctx.attempt == 1
        assert ctx.last_error is not None

    def test_handle_permanent_error(self) -> None:
        """Permanent error should not allow retry."""
        ctx = RetryContext(max_retries=3)
        result = ctx.handle_error(ValueError("Bad input"))
        assert result is False
        assert ctx.attempt == 1

    def test_exhausted_retries(self) -> None:
        """Should not allow retry after max attempts."""
        ctx = RetryContext(max_retries=2)

        # Exhaust retries
        ctx.handle_error(ConnectionError("1"))
        ctx.handle_error(ConnectionError("2"))
        result = ctx.handle_error(ConnectionError("3"))

        assert result is False
        assert ctx.should_retry() is False

    def test_mark_success(self) -> None:
        """Should mark as succeeded and stop retrying."""
        ctx = RetryContext(max_retries=3)
        ctx.handle_error(ConnectionError("Failed"))
        ctx.mark_success()

        assert ctx.succeeded is True
        assert ctx.should_retry() is False

    def test_get_delay_tracks_total(self) -> None:
        """get_delay should track total delay time."""
        ctx = RetryContext(max_retries=3, min_delay=1.0, jitter=0.0)

        ctx.handle_error(ConnectionError("1"))
        delay1 = ctx.get_delay()
        assert delay1 == 1.0

        ctx.handle_error(ConnectionError("2"))
        delay2 = ctx.get_delay()
        assert delay2 == 2.0

        assert ctx.total_delay == 3.0

    def test_should_retry_starts_true(self) -> None:
        """should_retry should return True initially."""
        ctx = RetryContext(max_retries=3)
        assert ctx.should_retry() is True

    def test_should_retry_false_after_success(self) -> None:
        """should_retry should return False after success."""
        ctx = RetryContext(max_retries=3)
        ctx.mark_success()
        assert ctx.should_retry() is False

    def test_should_retry_false_after_exhaustion(self) -> None:
        """should_retry should return False after exhausting retries."""
        ctx = RetryContext(max_retries=1)
        ctx.handle_error(ConnectionError("1"))
        ctx.handle_error(ConnectionError("2"))
        assert ctx.should_retry() is False

    def test_custom_parameters(self) -> None:
        """Should accept custom parameters."""
        ctx = RetryContext(
            max_retries=10,
            min_delay=2.0,
            max_delay=120.0,
            jitter=0.25,
        )
        assert ctx.max_retries == 10
        assert ctx.min_delay == 2.0
        assert ctx.max_delay == 120.0
        assert ctx.jitter == 0.25

    def test_http_transient_error_allows_retry(self) -> None:
        """HTTP transient error should allow retry."""
        ctx = RetryContext(max_retries=3)
        error = Exception("Service unavailable")
        error.status_code = 503  # type: ignore[attr-defined]
        result = ctx.handle_error(error)
        assert result is True

    def test_http_permanent_error_prevents_retry(self) -> None:
        """HTTP permanent error should prevent retry."""
        ctx = RetryContext(max_retries=3)
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]
        result = ctx.handle_error(error)
        assert result is False

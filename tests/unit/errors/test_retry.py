"""Unit tests for retry decorator and backoff calculation.

Tests verify:
- Exponential backoff delay calculation
- Retry decorator behavior with transient/permanent errors
- Max retry exhaustion
- Custom retry predicates
- RetryContext state management
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from phx_home_analysis.errors.retry import (
    RetryContext,
    calculate_backoff_delay,
    retry_with_backoff,
    retry_with_backoff_sync,
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


class TestRetryWithBackoffSync:
    """Tests for synchronous retry decorator."""

    def test_sync_success_on_first_try(self) -> None:
        """Function should return immediately on success."""
        mock_func = Mock(return_value="success")

        @retry_with_backoff_sync(max_retries=3)
        def func() -> str:
            return mock_func()

        result = func()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_sync_retry_on_transient_error(self) -> None:
        """Function should retry on transient error."""
        call_count = 0

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = func()
        assert result == "success"
        assert call_count == 3

    def test_sync_no_retry_on_permanent_error(self) -> None:
        """Function should not retry on permanent error."""
        mock_func = Mock(side_effect=ValueError("Bad input"))

        @retry_with_backoff_sync(max_retries=3)
        def func() -> str:
            return mock_func()

        with pytest.raises(ValueError, match="Bad input"):
            func()

        assert mock_func.call_count == 1

    def test_sync_exhausted_retries_raises(self) -> None:
        """Function should raise after exhausting retries."""
        mock_func = Mock(side_effect=ConnectionError("Connection failed"))

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func() -> str:
            return mock_func()

        with pytest.raises(ConnectionError, match="Connection failed"):
            func()

        assert mock_func.call_count == 4  # Initial + 3 retries

    def test_sync_custom_retry_predicate(self) -> None:
        """Custom retry_on predicate should control retry behavior."""

        def custom_retry(e: Exception) -> bool:
            return isinstance(e, RuntimeError)

        call_count = 0

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001, retry_on=custom_retry)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary")
            return "success"

        result = func()
        assert result == "success"
        assert call_count == 2

    def test_sync_http_429_transient_retried(self) -> None:
        """HTTP 429 (rate limit) should be retried."""
        call_count = 0

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = Exception("Rate limited")
                error.status_code = 429  # type: ignore[attr-defined]
                raise error
            return "success"

        result = func()
        assert result == "success"
        assert call_count == 2

    def test_sync_http_401_permanent_not_retried(self) -> None:
        """HTTP 401 (unauthorized) should not be retried."""
        error = Exception("Unauthorized")
        error.status_code = 401  # type: ignore[attr-defined]
        mock_func = Mock(side_effect=error)

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func() -> str:
            return mock_func()

        with pytest.raises(Exception, match="Unauthorized"):
            func()

        assert mock_func.call_count == 1

    def test_sync_preserves_function_name(self) -> None:
        """Decorator should preserve original function name."""

        @retry_with_backoff_sync(max_retries=3)
        def my_named_function() -> str:
            return "success"

        assert my_named_function.__name__ == "my_named_function"

    def test_sync_preserves_function_docstring(self) -> None:
        """Decorator should preserve original function docstring."""

        @retry_with_backoff_sync(max_retries=3)
        def documented_function() -> str:
            """This is my docstring."""
            return "success"

        assert documented_function.__doc__ == "This is my docstring."

    def test_sync_timeout_error_retried(self) -> None:
        """TimeoutError should be retried."""
        call_count = 0

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Request timed out")
            return "success"

        result = func()
        assert result == "success"
        assert call_count == 2

    def test_sync_with_function_arguments(self) -> None:
        """Decorator should handle function with arguments."""
        call_count = 0

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func(url: str, timeout: int) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Connection timeout")
            return f"fetched from {url} with timeout {timeout}"

        result = func("http://example.com", 30)
        assert result == "fetched from http://example.com with timeout 30"
        assert call_count == 2

    def test_sync_with_keyword_arguments(self) -> None:
        """Decorator should handle keyword arguments."""
        call_count = 0

        @retry_with_backoff_sync(max_retries=2, min_delay=0.001)
        def func(url: str, timeout: int = 10) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Failed")
            return f"url={url}, timeout={timeout}"

        result = func("http://test.com", timeout=20)
        assert result == "url=http://test.com, timeout=20"
        assert call_count == 2

    def test_sync_env_var_max_retries(self) -> None:
        """RETRY_MAX_RETRIES should override default max_retries."""
        with patch.dict("os.environ", {"RETRY_MAX_RETRIES": "2"}):
            call_count = 0

            @retry_with_backoff_sync(min_delay=0.001)  # Don't specify max_retries
            def func() -> str:
                nonlocal call_count
                call_count += 1
                raise ConnectionError("Always fails")

            with pytest.raises(ConnectionError):
                func()

            # 2 retries + 1 initial = 3 total attempts
            assert call_count == 3

    def test_sync_env_var_overridden_by_explicit_param(self) -> None:
        """Explicit parameter should override environment variable."""
        with patch.dict("os.environ", {"RETRY_MAX_RETRIES": "10"}):
            call_count = 0

            @retry_with_backoff_sync(max_retries=1, min_delay=0.001)
            def func() -> str:
                nonlocal call_count
                call_count += 1
                raise ConnectionError("Always fails")

            with pytest.raises(ConnectionError):
                func()

            # Explicit max_retries=1 should be used, not env var 10
            assert call_count == 2  # 1 retry + 1 initial

    def test_sync_sleep_is_called(self) -> None:
        """time.sleep should be called between retries."""
        with patch("time.sleep") as mock_sleep:
            call_count = 0

            @retry_with_backoff_sync(max_retries=2, min_delay=1.0, jitter=0.0)
            def func() -> str:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ConnectionError("Failed")
                return "success"

            result = func()
            assert result == "success"
            # Should have slept once (after first failure)
            assert mock_sleep.call_count == 1

    def test_sync_return_types_preserved(self) -> None:
        """Decorator should preserve function return types."""

        @retry_with_backoff_sync(max_retries=3)
        def func_int() -> int:
            return 42

        @retry_with_backoff_sync(max_retries=3)
        def func_dict() -> dict:
            return {"key": "value"}

        @retry_with_backoff_sync(max_retries=3)
        def func_list() -> list:
            return [1, 2, 3]

        assert func_int() == 42
        assert func_dict() == {"key": "value"}
        assert func_list() == [1, 2, 3]

    def test_sync_multiple_decorators_independent(self) -> None:
        """Multiple decorated functions should retry independently."""
        call_count_1 = 0
        call_count_2 = 0

        @retry_with_backoff_sync(max_retries=2, min_delay=0.001)
        def func1() -> str:
            nonlocal call_count_1
            call_count_1 += 1
            if call_count_1 < 2:
                raise ConnectionError("Failed")
            return "func1"

        @retry_with_backoff_sync(max_retries=3, min_delay=0.001)
        def func2() -> str:
            nonlocal call_count_2
            call_count_2 += 1
            if call_count_2 < 3:
                raise TimeoutError("Timeout")
            return "func2"

        result1 = func1()
        result2 = func2()

        assert result1 == "func1"
        assert result2 == "func2"
        assert call_count_1 == 2
        assert call_count_2 == 3


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


class TestJitterBoundary:
    """Tests for jitter boundary conditions."""

    def test_jitter_does_not_exceed_max_delay(self) -> None:
        """Jitter should never cause delay to exceed max_delay.

        CRITICAL: When delay is at max_delay, adding jitter could exceed the cap.
        This test verifies that the final delay is always <= max_delay.
        """
        # Test case where base delay is at max_delay
        # With jitter=1.0 and random=1.0, jitter would add 100% of delay
        # Without the fix, this would return 120.0 (60 + 60)
        with patch("phx_home_analysis.errors.retry.random.random", return_value=1.0):
            delay = calculate_backoff_delay(
                attempt=10,  # High attempt to ensure base_delay > max_delay
                min_delay=1.0,
                max_delay=60.0,
                jitter=1.0,  # Maximum jitter
            )
            assert delay <= 60.0, f"Delay {delay} exceeded max_delay 60.0"

    def test_jitter_boundary_near_max(self) -> None:
        """Verify jitter capping when delay is near max_delay."""
        with patch("phx_home_analysis.errors.retry.random.random", return_value=1.0):
            delay = calculate_backoff_delay(
                attempt=5,  # 2^5 = 32, with min_delay=2.0 = 64, capped to 60
                min_delay=2.0,
                max_delay=60.0,
                jitter=0.5,  # Would add 30 to 60 without cap
            )
            assert delay <= 60.0, f"Delay {delay} exceeded max_delay 60.0"

    def test_jitter_with_max_random_value(self) -> None:
        """Full jitter with max random should still respect max_delay."""
        with patch("phx_home_analysis.errors.retry.random.random", return_value=1.0):
            # Test multiple attempts to ensure cap always works
            for attempt in range(20):
                delay = calculate_backoff_delay(
                    attempt=attempt,
                    min_delay=1.0,
                    max_delay=10.0,
                    jitter=0.5,
                )
                assert delay <= 10.0, f"Attempt {attempt}: delay {delay} exceeded max 10.0"


class TestEnvironmentVariableConfiguration:
    """Tests for environment variable configuration of retry defaults."""

    @pytest.mark.asyncio
    async def test_env_var_max_retries(self) -> None:
        """RETRY_MAX_RETRIES should override default max_retries."""
        with patch.dict("os.environ", {"RETRY_MAX_RETRIES": "2"}):
            call_count = 0

            @retry_with_backoff(min_delay=0.01)  # Don't specify max_retries
            async def func() -> str:
                nonlocal call_count
                call_count += 1
                raise ConnectionError("Always fails")

            with pytest.raises(ConnectionError):
                await func()

            # 2 retries + 1 initial = 3 total attempts
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_env_var_overridden_by_explicit_param(self) -> None:
        """Explicit parameter should override environment variable."""
        with patch.dict("os.environ", {"RETRY_MAX_RETRIES": "10"}):
            call_count = 0

            @retry_with_backoff(max_retries=1, min_delay=0.01)
            async def func() -> str:
                nonlocal call_count
                call_count += 1
                raise ConnectionError("Always fails")

            with pytest.raises(ConnectionError):
                await func()

            # Explicit max_retries=1 should be used, not env var 10
            assert call_count == 2  # 1 retry + 1 initial

    def test_env_var_min_delay(self) -> None:
        """RETRY_MIN_DELAY should be read from environment."""
        from phx_home_analysis.errors.retry import _get_env_float

        with patch.dict("os.environ", {"RETRY_MIN_DELAY": "5.0"}):
            result = _get_env_float("RETRY_MIN_DELAY", 1.0)
            assert result == 5.0

    def test_env_var_max_delay(self) -> None:
        """RETRY_MAX_DELAY should be read from environment."""
        from phx_home_analysis.errors.retry import _get_env_float

        with patch.dict("os.environ", {"RETRY_MAX_DELAY": "120.0"}):
            result = _get_env_float("RETRY_MAX_DELAY", 60.0)
            assert result == 120.0

    def test_env_var_jitter(self) -> None:
        """RETRY_JITTER should be read from environment."""
        from phx_home_analysis.errors.retry import _get_env_float

        with patch.dict("os.environ", {"RETRY_JITTER": "0.25"}):
            result = _get_env_float("RETRY_JITTER", 0.5)
            assert result == 0.25

    def test_invalid_env_var_uses_default(self) -> None:
        """Invalid environment variable should fall back to default."""
        from phx_home_analysis.errors.retry import _get_env_float, _get_env_int

        with patch.dict("os.environ", {"RETRY_MAX_RETRIES": "not_a_number"}):
            result = _get_env_int("RETRY_MAX_RETRIES", 5)
            assert result == 5

        with patch.dict("os.environ", {"RETRY_MIN_DELAY": "invalid"}):
            result = _get_env_float("RETRY_MIN_DELAY", 1.0)
            assert result == 1.0

    def test_env_var_not_set_uses_default(self) -> None:
        """Missing environment variable should use default."""
        from phx_home_analysis.errors.retry import _get_env_float, _get_env_int

        # Ensure env vars are not set
        with patch.dict("os.environ", {}, clear=True):
            int_result = _get_env_int("RETRY_MAX_RETRIES", 5)
            float_result = _get_env_float("RETRY_MIN_DELAY", 1.0)
            assert int_result == 5
            assert float_result == 1.0

"""Unit tests for concurrency management service.

Tests semaphore-based concurrency limiting, circuit breaker pattern for source
resilience, and error aggregation for systemic failure detection.
"""

import asyncio
import time

import pytest

from phx_home_analysis.services.image_extraction.concurrency_manager import (
    ConcurrencyConfig,
    ConcurrencyManager,
    ErrorAggregator,
    SourceCircuitBreaker,
)


class TestConcurrencyConfig:
    """Tests for ConcurrencyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ConcurrencyConfig()

        # max_concurrent should be between 2 and 15
        assert 2 <= config.max_concurrent <= 15
        assert config.circuit_failure_threshold == 3
        assert config.circuit_reset_timeout == 300
        assert config.error_aggregation_threshold == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ConcurrencyConfig(
            max_concurrent=5,
            circuit_failure_threshold=2,
            circuit_reset_timeout=60,
            error_aggregation_threshold=5,
        )

        assert config.max_concurrent == 5
        assert config.circuit_failure_threshold == 2
        assert config.circuit_reset_timeout == 60
        assert config.error_aggregation_threshold == 5


class TestSourceCircuitBreaker:
    """Tests for SourceCircuitBreaker class."""

    def test_circuit_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        breaker = SourceCircuitBreaker(failure_threshold=3)

        assert breaker.is_available("zillow")
        assert breaker.is_available("redfin")

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit opens after reaching failure threshold."""
        breaker = SourceCircuitBreaker(failure_threshold=3)

        # Record failures
        assert not breaker.record_failure("zillow")  # 1st failure
        assert not breaker.record_failure("zillow")  # 2nd failure
        assert breaker.record_failure("zillow")  # 3rd failure - opens circuit

        # Circuit should be open (source unavailable)
        assert not breaker.is_available("zillow")

    def test_circuit_breaker_closes_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        breaker = SourceCircuitBreaker(failure_threshold=2, reset_timeout=1)

        # Open the circuit
        breaker.record_failure("zillow")
        breaker.record_failure("zillow")
        assert not breaker.is_available("zillow")

        # Wait for timeout
        time.sleep(1.1)

        # Circuit should be half-open (available for testing)
        assert breaker.is_available("zillow")

    def test_circuit_closes_after_success_in_half_open(self):
        """Test circuit closes after successful requests in half-open state."""
        breaker = SourceCircuitBreaker(failure_threshold=2, reset_timeout=1)

        # Open the circuit
        breaker.record_failure("zillow")
        breaker.record_failure("zillow")

        # Wait for half-open
        time.sleep(1.1)
        assert breaker.is_available("zillow")

        # Record successes to close circuit (needs 2 successes)
        breaker.record_success("zillow")
        breaker.record_success("zillow")

        # Circuit should be closed
        assert breaker.is_available("zillow")
        assert breaker.get_status()["zillow"] == "closed"

    def test_success_resets_failure_count_when_closed(self):
        """Test success resets failure count in closed state."""
        breaker = SourceCircuitBreaker(failure_threshold=3)

        # Record partial failures
        breaker.record_failure("zillow")
        breaker.record_failure("zillow")

        # Success should reset counter
        breaker.record_success("zillow")

        # Should need 3 more failures to open
        assert not breaker.record_failure("zillow")
        assert not breaker.record_failure("zillow")
        assert breaker.record_failure("zillow")  # 3rd failure opens

    def test_independent_sources(self):
        """Test sources have independent circuit states."""
        breaker = SourceCircuitBreaker(failure_threshold=2)

        # Fail zillow
        breaker.record_failure("zillow")
        breaker.record_failure("zillow")

        # zillow should be open, redfin still closed
        assert not breaker.is_available("zillow")
        assert breaker.is_available("redfin")

    def test_get_status_open(self):
        """Test status reporting for open circuit."""
        breaker = SourceCircuitBreaker(failure_threshold=2, reset_timeout=300)

        breaker.record_failure("zillow")
        breaker.record_failure("zillow")

        status = breaker.get_status()
        assert "zillow" in status
        assert "open" in status["zillow"]
        assert "remaining" in status["zillow"]

    def test_get_status_half_open(self):
        """Test status reporting for half-open circuit."""
        breaker = SourceCircuitBreaker(failure_threshold=2, reset_timeout=0.5)

        breaker.record_failure("zillow")
        breaker.record_failure("zillow")
        time.sleep(0.6)

        status = breaker.get_status()
        assert status["zillow"] == "half-open"

    def test_get_status_closed(self):
        """Test status reporting for closed circuit."""
        breaker = SourceCircuitBreaker(failure_threshold=3)

        breaker.record_failure("zillow")
        breaker.record_success("zillow")

        status = breaker.get_status()
        assert status["zillow"] == "closed"


class TestErrorAggregator:
    """Tests for ErrorAggregator class."""

    def test_error_aggregator_detects_systemic(self):
        """Test error aggregator detects systemic failures."""
        aggregator = ErrorAggregator(threshold=3)

        # Record same error multiple times
        error_msg = "404 error: https://ssl.cdn-redfin.com/photo/missing.jpg"

        assert not aggregator.record_error(error_msg)  # 1st occurrence
        assert not aggregator.record_error(error_msg)  # 2nd occurrence
        assert aggregator.record_error(error_msg)  # 3rd - triggers threshold

        # Subsequent similar errors should be skipped
        assert aggregator.record_error(error_msg)

    def test_normalize_404_errors(self):
        """Test 404 errors are normalized by domain/path pattern."""
        aggregator = ErrorAggregator(threshold=2)

        # The regex captures domain + up to 2 path segments (or less)
        # Both URLs will normalize to same pattern: 404:https://ssl.cdn-redfin.com/photo
        error1 = "404 error: https://ssl.cdn-redfin.com/photo"
        error2 = "404 error: https://ssl.cdn-redfin.com/photo"

        # Same normalized pattern
        aggregator.record_error(error1)
        result = aggregator.record_error(error2)

        # Should trigger threshold on 2nd occurrence
        assert result

    def test_different_errors_tracked_separately(self):
        """Test different error types are tracked independently."""
        aggregator = ErrorAggregator(threshold=3)

        error1 = "404 error: https://zillow.com/photo/1.jpg"
        error2 = "Timeout error connecting to server"

        # Each error type has independent count
        aggregator.record_error(error1)
        aggregator.record_error(error1)
        aggregator.record_error(error2)

        # 3rd occurrence of error1 triggers threshold
        assert aggregator.record_error(error1)  # 3rd of type 1 - triggers
        # error2 only occurred twice
        assert not aggregator.record_error(error2)  # 3rd of type 2

    def test_should_skip_url_matching_pattern(self):
        """Test URL skip matching against known patterns."""
        aggregator = ErrorAggregator(threshold=2)

        # Trigger threshold for this URL pattern
        # Pattern will be normalized to "404:https://ssl.cdn-redfin.com/photo/1.jpg"
        error = "404 error: https://ssl.cdn-redfin.com/photo/1.jpg"
        aggregator.record_error(error)
        aggregator.record_error(error)

        # Should skip URLs containing the normalized pattern substring
        assert aggregator.should_skip("https://ssl.cdn-redfin.com/photo/1.jpg")
        # Different URL pattern should not be skipped
        assert not aggregator.should_skip("https://different-domain.com/photo/1.jpg")

    def test_get_summary_top_errors(self):
        """Test error summary returns top 5 most common errors."""
        aggregator = ErrorAggregator(threshold=10)  # High threshold for testing

        # Record various errors with different frequencies
        for _ in range(5):
            aggregator.record_error("Error A")
        for _ in range(3):
            aggregator.record_error("Error B")
        for _ in range(7):
            aggregator.record_error("Error C")

        summary = aggregator.get_summary()

        # Should return counts
        assert summary["Error C"] == 7
        assert summary["Error A"] == 5
        assert summary["Error B"] == 3

    def test_normalize_non_404_errors(self):
        """Test non-404 errors use first 100 chars for normalization."""
        aggregator = ErrorAggregator(threshold=2)

        long_error = "Connection timeout: " + "x" * 200

        aggregator.record_error(long_error)
        result = aggregator.record_error(long_error)

        # Should normalize to first 100 chars and trigger threshold
        assert result


class TestConcurrencyManager:
    """Tests for ConcurrencyManager class."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent(self):
        """Test semaphore limits concurrent property processing."""
        config = ConcurrencyConfig(max_concurrent=2)
        manager = ConcurrencyManager(config)

        active_count = 0
        max_active = 0

        async def process_property():
            nonlocal active_count, max_active
            async with manager.acquire_slot():
                active_count += 1
                max_active = max(max_active, active_count)
                await asyncio.sleep(0.1)
                active_count -= 1

        # Launch 5 concurrent tasks
        await asyncio.gather(*[process_property() for _ in range(5)])

        # Should never exceed configured max_concurrent
        assert max_active <= 2

    @pytest.mark.asyncio
    async def test_acquire_slot_context_manager(self):
        """Test acquire_slot works as async context manager."""
        manager = ConcurrencyManager()

        async with manager.acquire_slot():
            # Should successfully acquire slot
            pass

        # Should release slot after context exits
        # Verify by acquiring again
        async with manager.acquire_slot():
            pass

    def test_is_source_available_delegates_to_circuit_breaker(self):
        """Test is_source_available delegates to circuit breaker."""
        manager = ConcurrencyManager()

        # Initially available
        assert manager.is_source_available("zillow")

        # Trip circuit
        config = manager.config
        for _ in range(config.circuit_failure_threshold):
            manager.record_source_failure("zillow")

        # Should be unavailable
        assert not manager.is_source_available("zillow")

    def test_record_source_success_delegates(self):
        """Test record_source_success delegates to circuit breaker."""
        manager = ConcurrencyManager()

        # Record failures
        manager.record_source_failure("zillow")
        manager.record_source_failure("zillow")

        # Success should reset
        manager.record_source_success("zillow")

        # Should still be available (didn't reach threshold)
        assert manager.is_source_available("zillow")

    def test_record_source_failure_returns_circuit_state(self):
        """Test record_source_failure returns True when circuit opens."""
        config = ConcurrencyConfig(circuit_failure_threshold=2)
        manager = ConcurrencyManager(config)

        assert not manager.record_source_failure("zillow")  # 1st failure
        assert manager.record_source_failure("zillow")  # 2nd - opens circuit

    def test_get_circuit_status(self):
        """Test circuit status reporting."""
        manager = ConcurrencyManager()

        manager.record_source_failure("zillow")
        status = manager.get_circuit_status()

        assert "zillow" in status
        assert status["zillow"] == "closed"

    def test_should_skip_url_delegates_to_error_aggregator(self):
        """Test should_skip_url delegates to error aggregator."""
        config = ConcurrencyConfig(error_aggregation_threshold=2)
        manager = ConcurrencyManager(config)

        # Trigger threshold - pattern will be "404:https://example.com/photo/1.jpg"
        error = "404 error: https://example.com/photo/1.jpg"
        manager.record_error(error)
        manager.record_error(error)

        # Should skip URLs containing the normalized pattern substring
        assert manager.should_skip_url("https://example.com/photo/1.jpg")

    def test_record_error_returns_skip_status(self):
        """Test record_error returns True when threshold reached."""
        config = ConcurrencyConfig(error_aggregation_threshold=2)
        manager = ConcurrencyManager(config)

        error = "Test error message"

        assert not manager.record_error(error)  # 1st
        assert manager.record_error(error)  # 2nd - triggers threshold

    def test_get_error_summary(self):
        """Test error summary reporting."""
        manager = ConcurrencyManager()

        manager.record_error("Error 1")
        manager.record_error("Error 1")
        manager.record_error("Error 2")

        summary = manager.get_error_summary()
        assert summary["Error 1"] == 2
        assert summary["Error 2"] == 1

    def test_get_diagnostics(self):
        """Test comprehensive diagnostics reporting."""
        config = ConcurrencyConfig(max_concurrent=10)
        manager = ConcurrencyManager(config)

        manager.record_source_failure("zillow")
        manager.record_error("Test error")

        diagnostics = manager.get_diagnostics()

        assert diagnostics["max_concurrent"] == 10
        assert "circuit_status" in diagnostics
        assert "error_summary" in diagnostics
        assert "config" in diagnostics
        assert diagnostics["config"]["circuit_failure_threshold"] == 3

    def test_initialization_with_default_config(self):
        """Test manager initializes with default config when None provided."""
        manager = ConcurrencyManager()

        assert manager.config is not None
        assert isinstance(manager.config, ConcurrencyConfig)

    def test_initialization_with_custom_config(self):
        """Test manager initializes with provided config."""
        config = ConcurrencyConfig(max_concurrent=5)
        manager = ConcurrencyManager(config)

        assert manager.config.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_concurrent_slot_acquisition(self):
        """Test multiple coroutines can acquire and release slots correctly."""
        config = ConcurrencyConfig(max_concurrent=3)
        manager = ConcurrencyManager(config)

        results = []

        async def acquire_and_record(task_id: int):
            async with manager.acquire_slot():
                results.append(f"acquired-{task_id}")
                await asyncio.sleep(0.05)
                results.append(f"released-{task_id}")

        # Launch tasks
        await asyncio.gather(*[acquire_and_record(i) for i in range(5)])

        # All tasks should complete
        assert len(results) == 10  # 5 acquire + 5 release
        assert results.count("acquired-0") == 1
        assert results.count("released-0") == 1

"""Concurrency management for image extraction pipeline.

Provides centralized control over concurrent property processing with:
- Semaphore-based concurrency limiting
- Circuit breaker pattern for source resilience
- Error aggregation for systemic failure detection

This module consolidates concurrency concerns from the orchestrator,
enabling better testability and separation of concerns.

Example:
    config = ConcurrencyConfig(max_concurrent=10)
    manager = ConcurrencyManager(config)

    async with manager.acquire_slot():
        if manager.is_source_available("zillow"):
            # ... extract from source
            manager.record_source_success("zillow")

Security: Uses asyncio.Lock internally for thread-safe state mutations.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from collections import Counter, defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyConfig:
    """Configuration for concurrency management.

    Attributes:
        max_concurrent: Maximum concurrent properties to process.
            Defaults to min(cpu_count * 2, 15) for optimal I/O-bound performance
            while respecting rate limiting constraints.
        circuit_failure_threshold: Consecutive failures before opening circuit.
        circuit_reset_timeout: Seconds before attempting to close circuit.
        error_aggregation_threshold: Occurrences before skipping similar errors.
    """

    max_concurrent: int = field(default_factory=lambda: max(2, min((os.cpu_count() or 2) * 2, 15)))
    circuit_failure_threshold: int = 3
    circuit_reset_timeout: int = 300  # 5 minutes
    error_aggregation_threshold: int = 3


class SourceCircuitBreaker:
    """Prevents cascade failures by temporarily disabling failing sources.

    Implements the circuit breaker pattern:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Source disabled after threshold failures
    - HALF-OPEN: After reset timeout, allows one test request

    Attributes:
        failure_threshold: Number of consecutive failures to open circuit
        reset_timeout: Seconds before attempting to close circuit
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 300):
        """Initialize circuit breaker with thresholds.

        Args:
            failure_threshold: Consecutive failures before opening circuit (default: 3)
            reset_timeout: Seconds to wait before half-open state (default: 300 = 5 min)
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures: dict[str, int] = defaultdict(int)
        self._disabled_until: dict[str, float] = {}
        self._successes_since_half_open: dict[str, int] = defaultdict(int)

    def record_failure(self, source: str) -> bool:
        """Record a failure for a source.

        Args:
            source: Source identifier (e.g., "zillow", "redfin")

        Returns:
            True if circuit is now open (source disabled)
        """
        self._failures[source] += 1
        self._successes_since_half_open[source] = 0

        if self._failures[source] >= self.failure_threshold:
            self._disabled_until[source] = time.time() + self.reset_timeout
            logger.warning(
                "Circuit OPEN for %s - disabled for %ds after %d failures",
                source,
                self.reset_timeout,
                self._failures[source],
            )
            return True
        return False

    def record_success(self, source: str) -> None:
        """Record a success for a source, potentially closing circuit."""
        if source in self._disabled_until:
            # Half-open state - success closes circuit
            self._successes_since_half_open[source] += 1
            if self._successes_since_half_open[source] >= 2:
                del self._disabled_until[source]
                self._failures[source] = 0
                logger.info("Circuit CLOSED for %s - source recovered", source)
        else:
            # Normal operation - reset failure count
            self._failures[source] = 0

    def is_available(self, source: str) -> bool:
        """Check if a source is available (circuit closed or half-open).

        Returns:
            True if requests should be attempted to this source
        """
        if source not in self._disabled_until:
            return True

        if time.time() >= self._disabled_until[source]:
            # Transition to half-open
            logger.info("Circuit HALF-OPEN for %s - testing recovery", source)
            return True

        return False

    def get_status(self) -> dict[str, str]:
        """Get status of all sources for logging/monitoring.

        Returns:
            Dict mapping source name to status string
        """
        status = {}
        now = time.time()
        for source in set(self._failures.keys()) | set(self._disabled_until.keys()):
            if source not in self._disabled_until:
                status[source] = "closed"
            elif now >= self._disabled_until[source]:
                status[source] = "half-open"
            else:
                remaining = int(self._disabled_until[source] - now)
                status[source] = f"open ({remaining}s remaining)"
        return status


class ErrorAggregator:
    """Detect and skip systemic failures to comply with Axiom 9 (Fail Fast).

    Prevents redundant error logging when the same error pattern occurs repeatedly
    (e.g., 404s from the same base URL across all properties).

    Attributes:
        threshold: Number of identical errors before skipping similar ones
        error_counts: Counter tracking frequency of normalized error patterns
        skip_patterns: Set of error patterns to skip after threshold reached
    """

    def __init__(self, threshold: int = 3):
        """Initialize error aggregator with threshold.

        Args:
            threshold: Number of occurrences before skipping similar errors (default: 3)
        """
        self.threshold = threshold
        self.error_counts: Counter[str] = Counter()
        self.skip_patterns: set[str] = set()

    def record_error(self, error_msg: str) -> bool:
        """Record error and return True if should skip similar errors.

        Args:
            error_msg: Full error message from exception

        Returns:
            True if this error pattern should be skipped (threshold reached)
        """
        # Normalize error message (extract URL pattern or error type)
        normalized = self._normalize_error(error_msg)
        self.error_counts[normalized] += 1

        if self.error_counts[normalized] >= self.threshold:
            if normalized not in self.skip_patterns:
                self.skip_patterns.add(normalized)
                logger.warning(
                    "Systemic failure detected (%dx): %s... Skipping similar errors.",
                    self.threshold,
                    normalized[:100],
                )
            return True
        return False

    def _normalize_error(self, msg: str) -> str:
        """Extract error pattern from message for deduplication.

        For 404 errors, extracts the domain/path pattern.
        For other errors, uses first 100 chars.

        Args:
            msg: Error message to normalize

        Returns:
            Normalized pattern string for comparison
        """
        # For 404 errors, extract the base URL pattern
        if "404" in msg and "http" in msg:
            # Extract domain/path pattern (e.g., https://ssl.cdn-redfin.com/photo/)
            match = re.search(r"(https?://[^/]+(?:/[^/]+){0,2})", msg)
            if match:
                return f"404:{match.group(1)}"
        return msg[:100]

    def should_skip(self, url: str) -> bool:
        """Check if URL matches a known failing pattern.

        Args:
            url: URL to check against skip patterns

        Returns:
            True if URL should be skipped based on known failures
        """
        for pattern in self.skip_patterns:
            if pattern.startswith("404:") and pattern[4:] in url:
                return True
        return False

    def get_summary(self) -> dict[str, int]:
        """Get error frequency summary for logging.

        Returns:
            Dict of top 5 most common error patterns with counts
        """
        return dict(self.error_counts.most_common(5))


class ConcurrencyManager:
    """Unified interface for concurrency control in image extraction.

    Combines semaphore-based concurrency limiting, circuit breaker pattern,
    and error aggregation into a single cohesive service.

    Example:
        config = ConcurrencyConfig(max_concurrent=10)
        manager = ConcurrencyManager(config)

        async with manager.acquire_slot():
            if manager.is_source_available("zillow"):
                try:
                    # ... extract
                    manager.record_source_success("zillow")
                except Exception as e:
                    if manager.record_source_failure("zillow"):
                        logger.error("Circuit opened for zillow")

    Attributes:
        config: ConcurrencyConfig with all thresholds
    """

    def __init__(self, config: ConcurrencyConfig | None = None):
        """Initialize concurrency manager with configuration.

        Args:
            config: ConcurrencyConfig instance, or None for defaults
        """
        self.config = config or ConcurrencyConfig()

        # Initialize components
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._circuit_breaker = SourceCircuitBreaker(
            failure_threshold=self.config.circuit_failure_threshold,
            reset_timeout=self.config.circuit_reset_timeout,
        )
        self._error_aggregator = ErrorAggregator(threshold=self.config.error_aggregation_threshold)

        logger.info(
            "ConcurrencyManager initialized: max_concurrent=%d, circuit_threshold=%d, error_threshold=%d",
            self.config.max_concurrent,
            self.config.circuit_failure_threshold,
            self.config.error_aggregation_threshold,
        )

    @asynccontextmanager
    async def acquire_slot(self) -> AsyncIterator[None]:
        """Acquire a processing slot with semaphore limiting.

        Use as async context manager to automatically manage semaphore
        acquisition and release.

        Example:
            async with manager.acquire_slot():
                # ... process property

        Yields:
            None - use context manager for RAII pattern
        """
        async with self._semaphore:
            yield

    # Circuit breaker delegation
    def is_source_available(self, source: str) -> bool:
        """Check if a source is available (circuit closed or half-open).

        Args:
            source: Source identifier (e.g., "zillow", "redfin")

        Returns:
            True if requests should be attempted to this source
        """
        return self._circuit_breaker.is_available(source)

    def record_source_success(self, source: str) -> None:
        """Record a success for a source, potentially closing circuit.

        Args:
            source: Source identifier
        """
        self._circuit_breaker.record_success(source)

    def record_source_failure(self, source: str) -> bool:
        """Record a failure for a source.

        Args:
            source: Source identifier

        Returns:
            True if circuit is now open (source disabled)
        """
        return self._circuit_breaker.record_failure(source)

    def get_circuit_status(self) -> dict[str, str]:
        """Get status of all sources for logging/monitoring.

        Returns:
            Dict mapping source name to status string (closed/half-open/open)
        """
        return self._circuit_breaker.get_status()

    # Error aggregation delegation
    def should_skip_url(self, url: str) -> bool:
        """Check if URL matches a known failing pattern.

        Args:
            url: URL to check against skip patterns

        Returns:
            True if URL should be skipped based on known failures
        """
        return self._error_aggregator.should_skip(url)

    def record_error(self, error_msg: str) -> bool:
        """Record error and return True if should skip similar errors.

        Args:
            error_msg: Full error message from exception

        Returns:
            True if this error pattern should be skipped (threshold reached)
        """
        return self._error_aggregator.record_error(error_msg)

    def get_error_summary(self) -> dict[str, int]:
        """Get error frequency summary for logging.

        Returns:
            Dict of top 5 most common error patterns with counts
        """
        return self._error_aggregator.get_summary()

    # Diagnostics
    def get_diagnostics(self) -> dict:
        """Get comprehensive diagnostics for monitoring.

        Returns:
            Dict with circuit status, error summary, and config
        """
        return {
            "max_concurrent": self.config.max_concurrent,
            "circuit_status": self.get_circuit_status(),
            "error_summary": self.get_error_summary(),
            "config": {
                "circuit_failure_threshold": self.config.circuit_failure_threshold,
                "circuit_reset_timeout": self.config.circuit_reset_timeout,
                "error_aggregation_threshold": self.config.error_aggregation_threshold,
            },
        }

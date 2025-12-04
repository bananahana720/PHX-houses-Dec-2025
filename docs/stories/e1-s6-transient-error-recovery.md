# E1.S6: Transient Error Recovery

**Status:** Ready for Review
**Epic:** Epic 1 - Foundation & Data Infrastructure
**Priority:** P0
**Estimated Points:** 5
**Dependencies:** E1.S5 (Pipeline Resume Capability)
**Functional Requirements:** FR36, FR56

## User Story

As a system user, I want automatic retry with exponential backoff for transient errors, so that temporary API failures don't require manual intervention.

## Acceptance Criteria

### AC1: Exponential Backoff Retry Logic
**Given** a transient error occurs during API call or network operation
**When** the retry mechanism is invoked
**Then** the system retries with exponential backoff delays (1s, 2s, 4s, 8s, 16s)
**And** each retry attempt is logged with attempt number and delay duration
**And** retries continue up to the configured maximum (default: 5 attempts)

### AC2: Transient Error Classification
**Given** an error occurs during pipeline execution
**When** the error handler evaluates the exception
**Then** transient errors (429, 503, 504, ConnectionError, TimeoutError) trigger retry logic
**And** non-transient errors (400, 401, 403, 404) do not trigger retries
**And** the error classification is logged for debugging

### AC3: Configurable Retry Limits
**Given** the retry decorator or handler is initialized
**When** parameters are specified
**Then** max_retries (default: 5), min_delay (default: 1.0s), max_delay (default: 60.0s), and jitter (default: 0.5) are configurable
**And** configuration can be overridden per-operation or via environment variables

### AC4: Per-Item Failure Tracking
**Given** a batch operation processes multiple items (properties)
**When** one item fails after exhausting retries
**Then** the item is marked "failed" with error details and timestamp in work_items.json
**And** the pipeline continues processing remaining items
**And** the failure count is updated in the summary section

### AC5: Actionable Error Messages
**Given** an error occurs (transient or non-transient)
**When** the error is logged or displayed to the user
**Then** the message includes: error type, HTTP status (if applicable), affected resource, suggested action
**And** non-transient errors suggest specific actions (e.g., "401: Check API token", "404: Property not found")

### AC6: Retry Decorator Integration
**Given** an async function decorated with `@retry_with_backoff`
**When** the function raises a transient error
**Then** the decorator handles retry logic transparently
**And** the original function is called again after the backoff delay
**And** the decorator returns the successful result or raises after max retries exhausted

## Technical Tasks

### Task 1: Create Error Classification Module
**File:** `src/phx_home_analysis/errors/__init__.py` (NEW)
**Lines:** ~100

**Implementation:**
```python
"""Error classification and handling for transient error recovery.

This module provides:
- ErrorCategory enum for classifying errors
- is_transient_error() for determining retry eligibility
- Specific exception classes for pipeline errors
- Error message formatting with actionable suggestions

Usage:
    from phx_home_analysis.errors import is_transient_error, TransientError

    try:
        response = await http_client.get(url)
    except Exception as e:
        if is_transient_error(e):
            # Retry logic
        else:
            # Permanent failure handling
"""

from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    """Categories for error classification."""

    TRANSIENT = "transient"      # Temporary failures, should retry
    PERMANENT = "permanent"      # Unrecoverable, do not retry
    UNKNOWN = "unknown"          # Unclassified, conservative retry


# HTTP status codes that indicate transient errors
TRANSIENT_HTTP_CODES = frozenset({
    429,  # Too Many Requests (rate limited)
    503,  # Service Unavailable
    504,  # Gateway Timeout
    502,  # Bad Gateway
    500,  # Internal Server Error (sometimes transient)
})

# HTTP status codes that indicate permanent errors
PERMANENT_HTTP_CODES = frozenset({
    400,  # Bad Request
    401,  # Unauthorized
    403,  # Forbidden
    404,  # Not Found
    405,  # Method Not Allowed
    410,  # Gone
    422,  # Unprocessable Entity
})

# Exception types that indicate transient errors
TRANSIENT_EXCEPTION_TYPES = (
    ConnectionError,
    TimeoutError,
    # Add httpx-specific if needed: httpx.TimeoutException, httpx.ConnectError
)


def is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient and should be retried.

    Args:
        error: The exception to classify

    Returns:
        True if the error is transient (should retry), False otherwise

    Examples:
        >>> is_transient_error(ConnectionError("Connection refused"))
        True
        >>> is_transient_error(ValueError("Invalid input"))
        False
    """
    # Check exception type first
    if isinstance(error, TRANSIENT_EXCEPTION_TYPES):
        return True

    # Check for HTTP status code in exception attributes
    status_code = getattr(error, 'status_code', None)
    if status_code is None:
        # Try httpx-style response attribute
        response = getattr(error, 'response', None)
        if response is not None:
            status_code = getattr(response, 'status_code', None)

    if status_code is not None:
        if status_code in TRANSIENT_HTTP_CODES:
            return True
        if status_code in PERMANENT_HTTP_CODES:
            return False

    # Default: treat unknown errors as non-transient (conservative)
    return False


def get_error_category(error: Exception) -> ErrorCategory:
    """Get the category of an error.

    Args:
        error: The exception to classify

    Returns:
        ErrorCategory enum value
    """
    if is_transient_error(error):
        return ErrorCategory.TRANSIENT
    return ErrorCategory.PERMANENT


def format_error_message(error: Exception, context: str = "") -> str:
    """Format an error message with actionable guidance.

    Args:
        error: The exception that occurred
        context: Optional context (e.g., "fetching property data")

    Returns:
        Formatted error message with suggested action

    Examples:
        >>> format_error_message(HTTPError(401), "County API call")
        "County API call failed: 401 Unauthorized. Action: Check MARICOPA_ASSESSOR_TOKEN in .env"
    """
    status_code = getattr(error, 'status_code', None)
    if status_code is None:
        response = getattr(error, 'response', None)
        if response is not None:
            status_code = getattr(response, 'status_code', None)

    action_map = {
        401: "Check API token in .env file",
        403: "Verify API permissions and access rights",
        404: "Resource not found - verify address or URL",
        429: "Rate limited - wait before retrying",
        500: "Server error - may be transient, retry later",
        503: "Service unavailable - retry with backoff",
    }

    base_msg = f"{context}: " if context else ""
    error_type = type(error).__name__

    if status_code:
        action = action_map.get(status_code, "Check error details")
        return f"{base_msg}{error_type} (HTTP {status_code}). Action: {action}"

    if isinstance(error, ConnectionError):
        return f"{base_msg}Connection failed. Action: Check network connectivity"

    if isinstance(error, TimeoutError):
        return f"{base_msg}Request timed out. Action: Increase timeout or retry"

    return f"{base_msg}{error_type}: {str(error)}"


class TransientError(Exception):
    """Exception indicating a transient, retryable error."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class PermanentError(Exception):
    """Exception indicating a permanent, non-retryable error."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
```

**Acceptance Criteria:**
- [x] `ErrorCategory` enum defined with TRANSIENT, PERMANENT, UNKNOWN
- [x] `TRANSIENT_HTTP_CODES` includes 429, 503, 504, 502, 500
- [x] `PERMANENT_HTTP_CODES` includes 400, 401, 403, 404
- [x] `is_transient_error()` correctly classifies errors
- [x] `format_error_message()` provides actionable guidance
- [x] `TransientError` and `PermanentError` exception classes defined

### Task 2: Implement Retry Decorator with Exponential Backoff
**File:** `src/phx_home_analysis/errors/retry.py` (NEW)
**Lines:** ~150

**Implementation:**
```python
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
import random
from typing import Any, Callable, TypeVar

from . import is_transient_error, format_error_message

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 5,
    min_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.5,
    retry_on: Callable[[Exception], bool] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for async functions with exponential backoff retry.

    Automatically retries the decorated function when transient errors occur,
    using exponential backoff with jitter to prevent thundering herd.

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        min_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        jitter: Randomization factor for delays, 0-1 (default: 0.5)
        retry_on: Optional custom function to determine if error is retryable.
                  Defaults to is_transient_error().

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
    should_retry = retry_on or is_transient_error

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
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
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: "
                            f"{format_error_message(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        min_delay=min_delay,
                        max_delay=max_delay,
                        jitter=jitter,
                    )

                    logger.info(
                        f"{func.__name__} transient error (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.1f}s: {type(e).__name__}"
                    )

                    await asyncio.sleep(delay)

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
    base_delay = min_delay * (2 ** attempt)

    # Cap at max_delay
    delay = min(base_delay, max_delay)

    # Add jitter to prevent thundering herd
    if jitter > 0:
        jitter_amount = delay * jitter * random.random()
        delay += jitter_amount

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
    ):
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
            attempt=self.attempt - 1,
            min_delay=self.min_delay,
            max_delay=self.max_delay,
            jitter=self.jitter,
        )
        self.total_delay += delay
        return delay

    def mark_success(self) -> None:
        """Mark the operation as successful."""
        self.succeeded = True
```

**Acceptance Criteria:**
- [x] `@retry_with_backoff` decorator handles async functions
- [x] Exponential backoff follows sequence: 1s, 2s, 4s, 8s, 16s (capped at max_delay)
- [x] Jitter prevents thundering herd
- [x] Transient errors trigger retry, permanent errors raise immediately
- [x] Each attempt is logged with attempt number and delay
- [x] `calculate_backoff_delay()` is testable independently
- [x] `RetryContext` provides explicit retry state management

### Task 3: Integrate Error Handling with Pipeline State
**File:** `src/phx_home_analysis/errors/pipeline.py` (NEW)
**Lines:** ~80

**Implementation:**
```python
"""Pipeline-specific error handling for work_items.json integration.

Provides functions to update work_items.json when errors occur,
tracking per-item failures with error details.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import get_error_category, format_error_message, ErrorCategory

logger = logging.getLogger(__name__)


def mark_item_failed(
    work_items_path: Path,
    address: str,
    phase: str,
    error: Exception,
    can_retry: bool = False,
) -> None:
    """Mark a work item as failed in work_items.json.

    Updates the work item's phase status to 'failed' and records
    error details for debugging and reporting.

    Args:
        work_items_path: Path to work_items.json
        address: Property address that failed
        phase: Phase that failed (e.g., 'phase1_listing')
        error: The exception that caused the failure
        can_retry: If True, set status to 'retrying' instead of 'failed'
    """
    if not work_items_path.exists():
        logger.warning(f"work_items.json not found at {work_items_path}")
        return

    with open(work_items_path, encoding='utf-8') as f:
        data = json.load(f)

    # Find the work item
    for item in data.get('work_items', []):
        if item.get('address') == address:
            # Update phase status
            if phase in item.get('phases', {}):
                category = get_error_category(error)
                status = 'retrying' if (can_retry and category == ErrorCategory.TRANSIENT) else 'failed'

                item['phases'][phase]['status'] = status
                item['phases'][phase]['failed_at'] = datetime.now(timezone.utc).isoformat()
                item['phases'][phase]['error'] = format_error_message(error, phase)
                item['phases'][phase]['error_category'] = category.value

            item['last_updated'] = datetime.now(timezone.utc).isoformat()
            break

    # Update summary counts
    summary = data.get('summary', {})
    if 'failed' in summary:
        # Recalculate failed count
        failed_count = sum(
            1 for item in data.get('work_items', [])
            for phase_data in item.get('phases', {}).values()
            if phase_data.get('status') == 'failed'
        )
        summary['failed'] = failed_count

    data['last_checkpoint'] = datetime.now(timezone.utc).isoformat()

    # Atomic write
    temp_path = work_items_path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    temp_path.replace(work_items_path)

    logger.info(f"Marked {address}/{phase} as {'retrying' if can_retry else 'failed'}")


def get_failure_summary(work_items_path: Path) -> dict[str, Any]:
    """Get summary of all failed items from work_items.json.

    Returns:
        Dict with failure counts, failed addresses, and error details
    """
    if not work_items_path.exists():
        return {'failed_count': 0, 'failures': []}

    with open(work_items_path, encoding='utf-8') as f:
        data = json.load(f)

    failures = []
    for item in data.get('work_items', []):
        for phase, phase_data in item.get('phases', {}).items():
            if phase_data.get('status') == 'failed':
                failures.append({
                    'address': item.get('address'),
                    'phase': phase,
                    'error': phase_data.get('error'),
                    'error_category': phase_data.get('error_category'),
                    'failed_at': phase_data.get('failed_at'),
                })

    return {
        'failed_count': len(failures),
        'failures': failures,
    }
```

**Acceptance Criteria:**
- [x] `mark_item_failed()` updates work_items.json with error details
- [x] Error category (transient/permanent) is recorded
- [x] Formatted error message with action guidance is stored
- [x] Summary counts are updated
- [x] Atomic write prevents corruption
- [x] `get_failure_summary()` retrieves all failures for reporting

### Task 4: Create Module __init__.py with Public Exports
**File:** `src/phx_home_analysis/errors/__init__.py` (enhance from Task 1)
**Lines:** Update exports

**Implementation:**
Add to end of `__init__.py`:
```python
# Public exports
__all__ = [
    # Enums and constants
    'ErrorCategory',
    'TRANSIENT_HTTP_CODES',
    'PERMANENT_HTTP_CODES',

    # Classification functions
    'is_transient_error',
    'get_error_category',
    'format_error_message',

    # Exception classes
    'TransientError',
    'PermanentError',

    # Retry utilities (imported from retry.py)
    'retry_with_backoff',
    'calculate_backoff_delay',
    'RetryContext',

    # Pipeline integration (imported from pipeline.py)
    'mark_item_failed',
    'get_failure_summary',
]

# Lazy imports for submodules
from .retry import retry_with_backoff, calculate_backoff_delay, RetryContext
from .pipeline import mark_item_failed, get_failure_summary
```

**Acceptance Criteria:**
- [x] All public functions/classes exported via `__all__`
- [x] Submodule imports work correctly
- [x] Module is importable: `from phx_home_analysis.errors import retry_with_backoff`

### Task 5: Unit Tests for Error Classification
**File:** `tests/unit/errors/test_classification.py` (NEW)
**Lines:** ~120

**Test Cases:**
```python
import pytest
from phx_home_analysis.errors import (
    is_transient_error,
    get_error_category,
    format_error_message,
    ErrorCategory,
    TRANSIENT_HTTP_CODES,
    PERMANENT_HTTP_CODES,
)


class TestIsTransientError:
    """Tests for transient error classification."""

    def test_connection_error_is_transient(self):
        """ConnectionError should be classified as transient."""
        error = ConnectionError("Connection refused")
        assert is_transient_error(error) is True

    def test_timeout_error_is_transient(self):
        """TimeoutError should be classified as transient."""
        error = TimeoutError("Request timed out")
        assert is_transient_error(error) is True

    def test_http_429_is_transient(self):
        """HTTP 429 (rate limited) should be transient."""
        error = Exception("Rate limited")
        error.status_code = 429
        assert is_transient_error(error) is True

    def test_http_503_is_transient(self):
        """HTTP 503 (service unavailable) should be transient."""
        error = Exception("Service unavailable")
        error.status_code = 503
        assert is_transient_error(error) is True

    def test_http_504_is_transient(self):
        """HTTP 504 (gateway timeout) should be transient."""
        error = Exception("Gateway timeout")
        error.status_code = 504
        assert is_transient_error(error) is True

    def test_http_401_is_permanent(self):
        """HTTP 401 (unauthorized) should be permanent."""
        error = Exception("Unauthorized")
        error.status_code = 401
        assert is_transient_error(error) is False

    def test_http_404_is_permanent(self):
        """HTTP 404 (not found) should be permanent."""
        error = Exception("Not found")
        error.status_code = 404
        assert is_transient_error(error) is False

    def test_http_400_is_permanent(self):
        """HTTP 400 (bad request) should be permanent."""
        error = Exception("Bad request")
        error.status_code = 400
        assert is_transient_error(error) is False

    def test_value_error_is_permanent(self):
        """ValueError should be permanent (not retryable)."""
        error = ValueError("Invalid input")
        assert is_transient_error(error) is False

    def test_unknown_error_is_permanent(self):
        """Unknown errors should default to permanent (conservative)."""
        error = RuntimeError("Something unexpected")
        assert is_transient_error(error) is False


class TestGetErrorCategory:
    """Tests for error category assignment."""

    def test_transient_error_category(self):
        """Transient errors should get TRANSIENT category."""
        error = ConnectionError("Connection failed")
        assert get_error_category(error) == ErrorCategory.TRANSIENT

    def test_permanent_error_category(self):
        """Permanent errors should get PERMANENT category."""
        error = ValueError("Bad input")
        assert get_error_category(error) == ErrorCategory.PERMANENT


class TestFormatErrorMessage:
    """Tests for error message formatting."""

    def test_format_with_context(self):
        """Error message should include context."""
        error = Exception("Failed")
        error.status_code = 401
        msg = format_error_message(error, "County API call")
        assert "County API call" in msg
        assert "401" in msg
        assert "token" in msg.lower() or "api" in msg.lower()

    def test_format_connection_error(self):
        """ConnectionError should suggest checking network."""
        error = ConnectionError("Connection refused")
        msg = format_error_message(error)
        assert "Connection" in msg
        assert "network" in msg.lower()

    def test_format_timeout_error(self):
        """TimeoutError should suggest retry or increase timeout."""
        error = TimeoutError("Timed out")
        msg = format_error_message(error)
        assert "timeout" in msg.lower()
```

**Acceptance Criteria:**
- [x] All HTTP status codes in TRANSIENT_HTTP_CODES tested
- [x] All HTTP status codes in PERMANENT_HTTP_CODES tested
- [x] Exception types (ConnectionError, TimeoutError) tested
- [x] Error category assignment tested
- [x] Error message formatting tested with various scenarios

### Task 6: Unit Tests for Retry Decorator
**File:** `tests/unit/errors/test_retry.py` (NEW)
**Lines:** ~150

**Test Cases:**
```python
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from phx_home_analysis.errors.retry import (
    retry_with_backoff,
    calculate_backoff_delay,
    RetryContext,
)


class TestCalculateBackoffDelay:
    """Tests for backoff delay calculation."""

    def test_initial_delay(self):
        """First attempt should use min_delay."""
        delay = calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.0)
        assert delay == 1.0

    def test_exponential_growth(self):
        """Delay should double with each attempt."""
        delays = [
            calculate_backoff_delay(i, min_delay=1.0, max_delay=60.0, jitter=0.0)
            for i in range(5)
        ]
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay."""
        delay = calculate_backoff_delay(10, min_delay=1.0, max_delay=60.0, jitter=0.0)
        assert delay == 60.0

    def test_jitter_adds_randomness(self):
        """Jitter should add randomness to delay."""
        with patch('random.random', return_value=1.0):
            delay = calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.5)
            assert delay == 1.5  # 1.0 + (1.0 * 0.5 * 1.0)

    def test_no_jitter_when_zero(self):
        """No jitter should be added when jitter=0."""
        delays = [
            calculate_backoff_delay(0, min_delay=1.0, max_delay=60.0, jitter=0.0)
            for _ in range(10)
        ]
        assert all(d == 1.0 for d in delays)


class TestRetryWithBackoff:
    """Tests for retry decorator."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Function should return immediately on success."""
        mock_func = AsyncMock(return_value="success")

        @retry_with_backoff(max_retries=3)
        async def func():
            return await mock_func()

        result = await func()
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Function should retry on transient error."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Function should not retry on permanent error."""
        mock_func = AsyncMock(side_effect=ValueError("Bad input"))

        @retry_with_backoff(max_retries=3)
        async def func():
            return await mock_func()

        with pytest.raises(ValueError):
            await func()

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self):
        """Function should raise after exhausting retries."""
        mock_func = AsyncMock(side_effect=ConnectionError("Connection failed"))

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def func():
            return await mock_func()

        with pytest.raises(ConnectionError):
            await func()

        assert mock_func.call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_custom_retry_predicate(self):
        """Custom retry_on predicate should control retry behavior."""

        def custom_retry(e: Exception) -> bool:
            return isinstance(e, RuntimeError)

        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01, retry_on=custom_retry)
        async def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary")
            return "success"

        result = await func()
        assert result == "success"
        assert call_count == 2


class TestRetryContext:
    """Tests for RetryContext state management."""

    def test_initial_state(self):
        """Context should start with clean state."""
        ctx = RetryContext(max_retries=3)
        assert ctx.attempt == 0
        assert ctx.succeeded is False
        assert ctx.should_retry() is True

    def test_handle_transient_error(self):
        """Transient error should allow retry."""
        ctx = RetryContext(max_retries=3)
        result = ctx.handle_error(ConnectionError("Failed"))
        assert result is True
        assert ctx.attempt == 1

    def test_handle_permanent_error(self):
        """Permanent error should not allow retry."""
        ctx = RetryContext(max_retries=3)
        result = ctx.handle_error(ValueError("Bad input"))
        assert result is False

    def test_exhausted_retries(self):
        """Should not allow retry after max attempts."""
        ctx = RetryContext(max_retries=2)

        # Exhaust retries
        ctx.handle_error(ConnectionError("1"))
        ctx.handle_error(ConnectionError("2"))
        result = ctx.handle_error(ConnectionError("3"))

        assert result is False
        assert ctx.should_retry() is False

    def test_mark_success(self):
        """Should mark as succeeded and stop retrying."""
        ctx = RetryContext(max_retries=3)
        ctx.handle_error(ConnectionError("Failed"))
        ctx.mark_success()

        assert ctx.succeeded is True
        assert ctx.should_retry() is False
```

**Acceptance Criteria:**
- [x] Backoff delay calculation tested for all scenarios
- [x] Retry decorator tested for success, transient errors, permanent errors
- [x] Max retries exhaustion tested
- [x] Custom retry predicate tested
- [x] RetryContext state management tested

### Task 7: Integration Test for End-to-End Retry
**File:** `tests/integration/test_transient_error_recovery.py` (NEW)
**Lines:** ~100

**Test Cases:**
```python
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from phx_home_analysis.errors import (
    retry_with_backoff,
    mark_item_failed,
    get_failure_summary,
)


class TestTransientErrorRecoveryIntegration:
    """Integration tests for complete error recovery flow."""

    @pytest.fixture
    def work_items_file(self, tmp_path: Path) -> Path:
        """Create a test work_items.json file."""
        work_items_path = tmp_path / "work_items.json"
        data = {
            "session": {"session_id": "test123"},
            "work_items": [
                {
                    "address": "123 Main St, Phoenix, AZ 85001",
                    "phases": {
                        "phase1_listing": {"status": "pending"}
                    },
                    "last_updated": "2025-12-04T10:00:00Z"
                }
            ],
            "summary": {"failed": 0}
        }
        work_items_path.write_text(json.dumps(data, indent=2))
        return work_items_path

    @pytest.mark.asyncio
    async def test_retry_then_succeed_no_failure_recorded(self, work_items_file):
        """Successful retry should not record failure."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def fetch_data():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return {"data": "success"}

        result = await fetch_data()
        assert result == {"data": "success"}

        # Verify no failure recorded
        summary = get_failure_summary(work_items_file)
        assert summary['failed_count'] == 0

    @pytest.mark.asyncio
    async def test_exhausted_retries_records_failure(self, work_items_file):
        """Exhausted retries should record failure in work_items.json."""
        error = ConnectionError("Persistent failure")

        @retry_with_backoff(max_retries=2, min_delay=0.01)
        async def fetch_data():
            raise error

        with pytest.raises(ConnectionError):
            await fetch_data()

        # Record the failure
        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error
        )

        # Verify failure recorded
        summary = get_failure_summary(work_items_file)
        assert summary['failed_count'] == 1
        assert summary['failures'][0]['phase'] == 'phase1_listing'
        assert 'transient' in summary['failures'][0]['error_category']

    @pytest.mark.asyncio
    async def test_permanent_error_immediate_failure(self, work_items_file):
        """Permanent error should immediately record failure."""
        error = Exception("Not found")
        error.status_code = 404

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def fetch_data():
            raise error

        with pytest.raises(Exception):
            await fetch_data()

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error
        )

        summary = get_failure_summary(work_items_file)
        assert summary['failed_count'] == 1
        assert 'permanent' in summary['failures'][0]['error_category']

    @pytest.mark.asyncio
    async def test_pipeline_continues_after_item_failure(self, work_items_file, tmp_path):
        """Pipeline should continue processing after one item fails."""
        # This test simulates batch processing where one item fails
        # but others succeed

        addresses = [
            "123 Main St, Phoenix, AZ 85001",
            "456 Oak Ave, Mesa, AZ 85201",
            "789 Elm Blvd, Tempe, AZ 85281",
        ]

        results = []
        for i, addr in enumerate(addresses):
            @retry_with_backoff(max_retries=1, min_delay=0.01)
            async def process_item(address=addr, index=i):
                if index == 1:  # Second item fails
                    raise ConnectionError("Failed")
                return {"address": address, "success": True}

            try:
                result = await process_item()
                results.append(result)
            except ConnectionError:
                mark_item_failed(work_items_file, addr, "phase1_listing", ConnectionError("Failed"))

        # Two items succeeded, one failed
        assert len(results) == 2
        summary = get_failure_summary(work_items_file)
        assert summary['failed_count'] == 1
```

**Acceptance Criteria:**
- [x] Successful retry does not record failure
- [x] Exhausted retries records failure with correct details
- [x] Permanent error records failure immediately
- [x] Pipeline continues processing after item failure
- [x] Error category (transient/permanent) is correctly recorded

### Task 8: Update Package __init__.py for errors module
**File:** `src/phx_home_analysis/__init__.py`
**Action:** Add errors module to package exports

**Implementation:**
Add to existing imports:
```python
# Error handling
from phx_home_analysis.errors import (
    retry_with_backoff,
    is_transient_error,
    TransientError,
    PermanentError,
)
```

**Acceptance Criteria:**
- [x] `retry_with_backoff` importable from main package
- [x] `is_transient_error` importable from main package
- [x] Exception classes importable from main package

## Test Plan Summary

### Unit Tests
| Suite | File | Test Count |
|-------|------|------------|
| Error Classification | `tests/unit/errors/test_classification.py` | 12 |
| Retry Decorator | `tests/unit/errors/test_retry.py` | 14 |

### Integration Tests
| Suite | File | Test Count |
|-------|------|------------|
| Transient Recovery | `tests/integration/test_transient_error_recovery.py` | 4 |

**Total New Tests:** ~30

## Dependencies

### New Dependencies Required
None - the `tenacity` library is mentioned in the epic but this implementation is standalone for better control and testing. If `tenacity` is preferred, the retry decorator can be implemented as a thin wrapper.

### Existing Dependencies Used
- `asyncio` (stdlib) - Async sleep for retry delays
- `functools` (stdlib) - Decorator wrapping
- `random` (stdlib) - Jitter calculation
- `json` (stdlib) - work_items.json operations
- `logging` (stdlib) - Error and retry logging

### Internal Dependencies
- `data/work_items.json` - Pipeline state tracking (updated by mark_item_failed)
- Existing job queue (already has retry logic - `src/phx_home_analysis/services/job_queue/executor.py`) - Pattern reference

## Definition of Done Checklist

### Implementation
- [x] Error classification module created (`errors/__init__.py`)
- [x] `is_transient_error()` correctly classifies HTTP codes and exception types
- [x] `format_error_message()` provides actionable guidance
- [x] Retry decorator created (`errors/retry.py`)
- [x] `@retry_with_backoff` handles async functions with exponential backoff
- [x] `calculate_backoff_delay()` implements correct backoff formula
- [x] `RetryContext` provides explicit state management
- [x] Pipeline integration created (`errors/pipeline.py`)
- [x] `mark_item_failed()` updates work_items.json correctly
- [x] `get_failure_summary()` retrieves failure details

### Testing
- [x] Unit tests for error classification pass
- [x] Unit tests for retry decorator pass
- [x] Integration tests for end-to-end recovery pass
- [x] All tests pass: `pytest tests/unit/errors/ tests/integration/test_transient_error_recovery.py -v`

### Quality Gates
- [x] Type checking passes: `mypy src/phx_home_analysis/errors/`
- [x] Linting passes: `ruff check src/phx_home_analysis/errors/`
- [x] No new warnings introduced
- [x] Docstrings complete with examples

### Documentation
- [x] Module docstrings explain purpose and usage
- [x] Function docstrings include examples
- [x] Error messages include actionable suggestions

## Dev Notes

### Architecture Patterns

1. **Existing Retry Logic Reference**: The `services/job_queue/executor.py` already implements exponential backoff for job processing. This story creates a more general-purpose decorator that can be used across the codebase.

2. **Decorator vs Context Manager**: Both `@retry_with_backoff` (declarative) and `RetryContext` (imperative) are provided. Use the decorator for simple cases; use the context manager when you need explicit control over retry state.

3. **Error Classification Strategy**: Conservative approach - unknown errors default to non-transient. This prevents infinite retry loops on unexpected errors.

4. **Jitter Purpose**: Random jitter prevents "thundering herd" when multiple concurrent operations retry at the same time after a service recovers.

### Project Structure Notes

- **New directory**: `src/phx_home_analysis/errors/` contains all error handling code
- **Pattern consistency**: Follows existing job_queue patterns for backoff calculation
- **Testability**: Pure functions (`calculate_backoff_delay`, `is_transient_error`) are easily unit testable

### References

| Reference | Location |
|-----------|----------|
| Epic Story Definition | `docs/epics/epic-1-foundation-data-infrastructure.md:80-92` |
| PRD FR36 | `docs/archive/prd.md:926-928` (transient error recovery) |
| PRD FR56 | `docs/archive/prd.md:970-971` (actionable error messages) |
| Existing Job Queue Executor | `src/phx_home_analysis/services/job_queue/executor.py:345-363` |
| Architecture Error Handling | `docs/archive/architecture.md:1547-1551` |

### Related Stories

**Depends On:**
- E1.S5: Pipeline Resume Capability (provides work_items.json state management)

**Blocks:**
- E2.S*: All data acquisition stories benefit from retry logic

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debug issues encountered during implementation.

### Completion Notes List

- **Task 1 (Error Classification):** Created `src/phx_home_analysis/errors/__init__.py` with ErrorCategory enum, HTTP code sets, `is_transient_error()`, `get_error_category()`, `format_error_message()`, and custom exception classes.
- **Task 2 (Retry Decorator):** Implemented `@retry_with_backoff` decorator with configurable exponential backoff and jitter in `errors/retry.py`. Added `RetryContext` for explicit state management.
- **Task 3 (Pipeline Integration):** Created `errors/pipeline.py` with `mark_item_failed()` for work_items.json integration and `get_failure_summary()` for failure reporting.
- **Task 4 (Module Exports):** Consolidated all public exports in `__all__` with lazy imports from submodules.
- **Task 5-7 (Tests):** Implemented 81 tests total - 40 unit tests for classification, 30 for retry, 11 integration tests. All passing.
- **Task 8 (Package Init):** Added error handling exports to main `phx_home_analysis/__init__.py`.
- **Quality Gates:** Linting passes (ruff), type checking passes for errors module (pre-existing issues in other files).

### File List

**New Files:**
- `src/phx_home_analysis/errors/__init__.py` - Error classification module (204 lines)
- `src/phx_home_analysis/errors/retry.py` - Retry decorator with exponential backoff (239 lines)
- `src/phx_home_analysis/errors/pipeline.py` - Pipeline state integration (181 lines)
- `tests/unit/errors/__init__.py` - Test module init
- `tests/unit/errors/test_classification.py` - Unit tests for error classification (40 tests)
- `tests/unit/errors/test_retry.py` - Unit tests for retry decorator (30 tests)
- `tests/integration/test_transient_error_recovery.py` - Integration tests (11 tests)

**Modified Files:**
- `src/phx_home_analysis/__init__.py` - Added error handling exports

### Change Log

- **2025-12-04:** Story implementation complete. All 8 tasks completed. 81 tests added and passing.

---

**Story Created:** 2025-12-04
**Created By:** PM Agent
**Story Completed:** 2025-12-04
**Completed By:** Dev Agent (Claude Opus 4.5)
**Epic File:** `docs/epics/epic-1-foundation-data-infrastructure.md:80-92`

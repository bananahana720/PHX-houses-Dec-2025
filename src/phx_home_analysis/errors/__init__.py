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


class ErrorCategory(str, Enum):
    """Categories for error classification."""

    TRANSIENT = "transient"  # Temporary failures, should retry
    PERMANENT = "permanent"  # Unrecoverable, do not retry
    UNKNOWN = "unknown"  # Unclassified, conservative retry


# HTTP status codes that indicate transient errors
TRANSIENT_HTTP_CODES: frozenset[int] = frozenset(
    {
        429,  # Too Many Requests (rate limited)
        503,  # Service Unavailable
        504,  # Gateway Timeout
        502,  # Bad Gateway
        500,  # Internal Server Error (sometimes transient)
    }
)

# HTTP status codes that indicate permanent errors
PERMANENT_HTTP_CODES: frozenset[int] = frozenset(
    {
        400,  # Bad Request
        401,  # Unauthorized
        403,  # Forbidden
        404,  # Not Found
        405,  # Method Not Allowed
        410,  # Gone
        422,  # Unprocessable Entity
    }
)

# Exception types that indicate transient errors
TRANSIENT_EXCEPTION_TYPES: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    # httpx-specific exceptions will be handled via status_code check
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
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        # Try httpx-style response attribute
        response = getattr(error, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)

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
        ErrorCategory enum value (TRANSIENT, PERMANENT, or UNKNOWN)
    """
    # Check exception type first
    if isinstance(error, TRANSIENT_EXCEPTION_TYPES):
        return ErrorCategory.TRANSIENT

    # Check for HTTP status code in exception attributes
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        # Try httpx-style response attribute
        response = getattr(error, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)

    if status_code is not None:
        if status_code in TRANSIENT_HTTP_CODES:
            return ErrorCategory.TRANSIENT
        if status_code in PERMANENT_HTTP_CODES:
            return ErrorCategory.PERMANENT

    # Unknown errors: Not in TRANSIENT or PERMANENT lists
    return ErrorCategory.UNKNOWN


def format_error_message(error: Exception, context: str = "") -> str:
    """Format an error message with actionable guidance.

    Args:
        error: The exception that occurred
        context: Optional context (e.g., "fetching property data")

    Returns:
        Formatted error message with suggested action

    Example:
        >>> # format_error_message(HTTPError(401), "County API call")
        >>> # Returns: "County API call: HTTPError (HTTP 401). Action: Check API token..."
    """
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        response = getattr(error, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)

    action_map: dict[int, str] = {
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

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class PermanentError(Exception):
    """Exception indicating a permanent, non-retryable error."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


# Import from submodules for convenient access
# Note: These imports are placed after class definitions to avoid circular imports
# ruff: noqa: E402
from .pipeline import clear_failure_status, get_failure_summary, mark_item_failed
from .retry import RetryContext, calculate_backoff_delay, retry_with_backoff

# Public exports
__all__ = [
    # Enums and constants
    "ErrorCategory",
    "TRANSIENT_HTTP_CODES",
    "PERMANENT_HTTP_CODES",
    # Classification functions
    "is_transient_error",
    "get_error_category",
    "format_error_message",
    # Exception classes
    "TransientError",
    "PermanentError",
    # Retry utilities (from retry.py)
    "retry_with_backoff",
    "calculate_backoff_delay",
    "RetryContext",
    # Pipeline integration (from pipeline.py)
    "mark_item_failed",
    "get_failure_summary",
    "clear_failure_status",
]

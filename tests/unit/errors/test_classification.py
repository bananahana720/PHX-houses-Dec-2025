"""Unit tests for error classification module.

Tests verify:
- Transient error detection (HTTP codes, exception types)
- Permanent error detection
- Error category assignment
- Error message formatting
"""


from phx_home_analysis.errors import (
    PERMANENT_HTTP_CODES,
    TRANSIENT_HTTP_CODES,
    ErrorCategory,
    PermanentError,
    TransientError,
    format_error_message,
    get_error_category,
    is_transient_error,
)


class TestIsTransientError:
    """Tests for transient error classification."""

    def test_connection_error_is_transient(self) -> None:
        """ConnectionError should be classified as transient."""
        error = ConnectionError("Connection refused")
        assert is_transient_error(error) is True

    def test_timeout_error_is_transient(self) -> None:
        """TimeoutError should be classified as transient."""
        error = TimeoutError("Request timed out")
        assert is_transient_error(error) is True

    def test_http_429_is_transient(self) -> None:
        """HTTP 429 (rate limited) should be transient."""
        error = Exception("Rate limited")
        error.status_code = 429  # type: ignore[attr-defined]
        assert is_transient_error(error) is True

    def test_http_500_is_transient(self) -> None:
        """HTTP 500 (internal server error) should be transient."""
        error = Exception("Internal server error")
        error.status_code = 500  # type: ignore[attr-defined]
        assert is_transient_error(error) is True

    def test_http_502_is_transient(self) -> None:
        """HTTP 502 (bad gateway) should be transient."""
        error = Exception("Bad gateway")
        error.status_code = 502  # type: ignore[attr-defined]
        assert is_transient_error(error) is True

    def test_http_503_is_transient(self) -> None:
        """HTTP 503 (service unavailable) should be transient."""
        error = Exception("Service unavailable")
        error.status_code = 503  # type: ignore[attr-defined]
        assert is_transient_error(error) is True

    def test_http_504_is_transient(self) -> None:
        """HTTP 504 (gateway timeout) should be transient."""
        error = Exception("Gateway timeout")
        error.status_code = 504  # type: ignore[attr-defined]
        assert is_transient_error(error) is True

    def test_http_401_is_permanent(self) -> None:
        """HTTP 401 (unauthorized) should be permanent."""
        error = Exception("Unauthorized")
        error.status_code = 401  # type: ignore[attr-defined]
        assert is_transient_error(error) is False

    def test_http_403_is_permanent(self) -> None:
        """HTTP 403 (forbidden) should be permanent."""
        error = Exception("Forbidden")
        error.status_code = 403  # type: ignore[attr-defined]
        assert is_transient_error(error) is False

    def test_http_404_is_permanent(self) -> None:
        """HTTP 404 (not found) should be permanent."""
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]
        assert is_transient_error(error) is False

    def test_http_400_is_permanent(self) -> None:
        """HTTP 400 (bad request) should be permanent."""
        error = Exception("Bad request")
        error.status_code = 400  # type: ignore[attr-defined]
        assert is_transient_error(error) is False

    def test_value_error_is_permanent(self) -> None:
        """ValueError should be permanent (not retryable)."""
        error = ValueError("Invalid input")
        assert is_transient_error(error) is False

    def test_unknown_error_is_permanent(self) -> None:
        """Unknown errors should default to permanent (conservative)."""
        error = RuntimeError("Something unexpected")
        assert is_transient_error(error) is False

    def test_httpx_style_response_attribute(self) -> None:
        """Should handle httpx-style errors with response.status_code."""

        class MockResponse:
            status_code = 503

        error = Exception("Service unavailable")
        error.response = MockResponse()  # type: ignore[attr-defined]
        assert is_transient_error(error) is True


class TestTransientHttpCodes:
    """Tests to verify TRANSIENT_HTTP_CODES contains expected values."""

    def test_contains_429(self) -> None:
        """429 (Too Many Requests) should be in transient codes."""
        assert 429 in TRANSIENT_HTTP_CODES

    def test_contains_500(self) -> None:
        """500 (Internal Server Error) should be in transient codes."""
        assert 500 in TRANSIENT_HTTP_CODES

    def test_contains_502(self) -> None:
        """502 (Bad Gateway) should be in transient codes."""
        assert 502 in TRANSIENT_HTTP_CODES

    def test_contains_503(self) -> None:
        """503 (Service Unavailable) should be in transient codes."""
        assert 503 in TRANSIENT_HTTP_CODES

    def test_contains_504(self) -> None:
        """504 (Gateway Timeout) should be in transient codes."""
        assert 504 in TRANSIENT_HTTP_CODES


class TestPermanentHttpCodes:
    """Tests to verify PERMANENT_HTTP_CODES contains expected values."""

    def test_contains_400(self) -> None:
        """400 (Bad Request) should be in permanent codes."""
        assert 400 in PERMANENT_HTTP_CODES

    def test_contains_401(self) -> None:
        """401 (Unauthorized) should be in permanent codes."""
        assert 401 in PERMANENT_HTTP_CODES

    def test_contains_403(self) -> None:
        """403 (Forbidden) should be in permanent codes."""
        assert 403 in PERMANENT_HTTP_CODES

    def test_contains_404(self) -> None:
        """404 (Not Found) should be in permanent codes."""
        assert 404 in PERMANENT_HTTP_CODES


class TestGetErrorCategory:
    """Tests for error category assignment."""

    def test_transient_error_category(self) -> None:
        """Transient errors should get TRANSIENT category."""
        error = ConnectionError("Connection failed")
        assert get_error_category(error) == ErrorCategory.TRANSIENT

    def test_unknown_error_category(self) -> None:
        """Unknown errors should get UNKNOWN category (not PERMANENT).

        This tests that unclassified errors (not in TRANSIENT or PERMANENT lists)
        get the UNKNOWN category for conservative handling.
        """
        # ValueError is not in TRANSIENT or PERMANENT HTTP code lists
        # and is not a TRANSIENT_EXCEPTION_TYPE, so it should be UNKNOWN
        error = ValueError("Bad input")
        assert get_error_category(error) == ErrorCategory.UNKNOWN

    def test_runtime_error_unknown_category(self) -> None:
        """RuntimeError should get UNKNOWN category."""
        error = RuntimeError("Something unexpected")
        assert get_error_category(error) == ErrorCategory.UNKNOWN

    def test_http_transient_error_category(self) -> None:
        """HTTP transient errors should get TRANSIENT category."""
        error = Exception("Rate limited")
        error.status_code = 429  # type: ignore[attr-defined]
        assert get_error_category(error) == ErrorCategory.TRANSIENT

    def test_http_permanent_error_category(self) -> None:
        """HTTP permanent errors should get PERMANENT category."""
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]
        assert get_error_category(error) == ErrorCategory.PERMANENT

    def test_timeout_error_transient_category(self) -> None:
        """TimeoutError should get TRANSIENT category (it's in TRANSIENT_EXCEPTION_TYPES)."""
        error = TimeoutError("Timed out")
        assert get_error_category(error) == ErrorCategory.TRANSIENT

    def test_unclassified_http_code_unknown_category(self) -> None:
        """HTTP codes not in TRANSIENT or PERMANENT lists should get UNKNOWN."""
        # HTTP 418 "I'm a teapot" is not in either list
        error = Exception("I'm a teapot")
        error.status_code = 418  # type: ignore[attr-defined]
        assert get_error_category(error) == ErrorCategory.UNKNOWN


class TestFormatErrorMessage:
    """Tests for error message formatting."""

    def test_format_with_context(self) -> None:
        """Error message should include context."""
        error = Exception("Failed")
        error.status_code = 401  # type: ignore[attr-defined]
        msg = format_error_message(error, "County API call")
        assert "County API call" in msg
        assert "401" in msg
        assert "token" in msg.lower() or "api" in msg.lower()

    def test_format_without_context(self) -> None:
        """Error message should work without context."""
        error = Exception("Failed")
        error.status_code = 401  # type: ignore[attr-defined]
        msg = format_error_message(error)
        assert "401" in msg
        assert not msg.startswith(":")

    def test_format_connection_error(self) -> None:
        """ConnectionError should suggest checking network."""
        error = ConnectionError("Connection refused")
        msg = format_error_message(error)
        assert "Connection" in msg
        assert "network" in msg.lower()

    def test_format_timeout_error(self) -> None:
        """TimeoutError should suggest retry or increase timeout."""
        error = TimeoutError("Timed out")
        msg = format_error_message(error)
        assert "timeout" in msg.lower()
        assert "retry" in msg.lower() or "increase" in msg.lower()

    def test_format_404_error(self) -> None:
        """HTTP 404 should suggest verifying address/URL."""
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]
        msg = format_error_message(error, "Property lookup")
        assert "404" in msg
        assert "not found" in msg.lower() or "verify" in msg.lower()

    def test_format_429_rate_limit(self) -> None:
        """HTTP 429 should suggest waiting before retry."""
        error = Exception("Rate limited")
        error.status_code = 429  # type: ignore[attr-defined]
        msg = format_error_message(error)
        assert "429" in msg
        assert "wait" in msg.lower() or "rate" in msg.lower()

    def test_format_generic_error(self) -> None:
        """Generic error should include error type and message."""
        error = RuntimeError("Something went wrong")
        msg = format_error_message(error)
        assert "RuntimeError" in msg
        assert "Something went wrong" in msg


class TestExceptionClasses:
    """Tests for custom exception classes."""

    def test_transient_error_creation(self) -> None:
        """TransientError should store message and original error."""
        original = ConnectionError("Connection refused")
        error = TransientError("Retryable error", original_error=original)
        assert str(error) == "Retryable error"
        assert error.original_error is original

    def test_transient_error_without_original(self) -> None:
        """TransientError should work without original error."""
        error = TransientError("Retryable error")
        assert str(error) == "Retryable error"
        assert error.original_error is None

    def test_permanent_error_creation(self) -> None:
        """PermanentError should store message and original error."""
        original = ValueError("Invalid input")
        error = PermanentError("Unrecoverable error", original_error=original)
        assert str(error) == "Unrecoverable error"
        assert error.original_error is original

    def test_permanent_error_without_original(self) -> None:
        """PermanentError should work without original error."""
        error = PermanentError("Unrecoverable error")
        assert str(error) == "Unrecoverable error"
        assert error.original_error is None

    def test_transient_error_is_exception(self) -> None:
        """TransientError should be an Exception."""
        error = TransientError("Test")
        assert isinstance(error, Exception)

    def test_permanent_error_is_exception(self) -> None:
        """PermanentError should be an Exception."""
        error = PermanentError("Test")
        assert isinstance(error, Exception)

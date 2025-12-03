"""Unit tests for logging utilities.

Tests credential sanitization functions to ensure sensitive data
is properly masked before logging.
"""

import pytest

from phx_home_analysis.services.infrastructure.logging_utils import (
    sanitize_proxy_config_for_logging,
    sanitize_url_for_logging,
)


class TestSanitizeUrlForLogging:
    """Test URL credential sanitization."""

    def test_url_with_credentials(self):
        """Test URL with username and password is sanitized."""
        url = "http://myuser:secret123@proxy.example.com:8080"
        result = sanitize_url_for_logging(url)
        assert result == "http://***:***@proxy.example.com:8080"
        assert "myuser" not in result
        assert "secret123" not in result

    def test_url_with_special_chars_in_password(self):
        """Test URL with special characters in password."""
        url = "http://user:p@ss:w0rd!@proxy.example.com:8080"
        result = sanitize_url_for_logging(url)
        assert result == "http://***:***@proxy.example.com:8080"
        assert "p@ss:w0rd!" not in result

    def test_url_without_credentials(self):
        """Test URL without credentials is unchanged."""
        url = "http://proxy.example.com:8080"
        result = sanitize_url_for_logging(url)
        assert result == url

    def test_url_without_port(self):
        """Test URL with credentials but no port."""
        url = "http://user:pass@proxy.example.com"
        result = sanitize_url_for_logging(url)
        assert result == "http://***:***@proxy.example.com"

    def test_https_url_with_credentials(self):
        """Test HTTPS URL with credentials."""
        url = "https://admin:secure@proxy.example.com:443"
        result = sanitize_url_for_logging(url)
        assert result == "https://***:***@proxy.example.com:443"

    def test_none_url(self):
        """Test None input returns placeholder."""
        result = sanitize_url_for_logging(None)
        assert result == "<none>"

    def test_empty_string(self):
        """Test empty string returns placeholder."""
        result = sanitize_url_for_logging("")
        assert result == "<none>"

    def test_invalid_url(self):
        """Test malformed URL returns error placeholder."""
        # This should trigger the exception handler
        result = sanitize_url_for_logging("not a valid url at all")
        # Since it doesn't have :// it will fail parsing
        assert "not a valid url" in result or result == "<invalid-url>"

    def test_url_with_path_and_credentials(self):
        """Test URL with path and credentials."""
        url = "http://user:pass@proxy.example.com:8080/path/to/resource"
        result = sanitize_url_for_logging(url)
        assert result == "http://***:***@proxy.example.com:8080/path/to/resource"
        assert "user" not in result
        assert "pass" not in result

    def test_url_with_query_params_and_credentials(self):
        """Test URL with query parameters and credentials."""
        url = "http://user:pass@proxy.example.com:8080?param=value"
        result = sanitize_url_for_logging(url)
        assert result == "http://***:***@proxy.example.com:8080?param=value"


class TestSanitizeProxyConfigForLogging:
    """Test proxy configuration sanitization."""

    def test_proxy_with_credentials(self):
        """Test proxy URL with credentials returns full config."""
        url = "http://user:pass@proxy.example.com:8080"
        result = sanitize_proxy_config_for_logging(url)
        assert result["status"] == "enabled"
        assert result["url"] == "http://***:***@proxy.example.com:8080"
        assert result["auth"] == "yes"

    def test_proxy_without_credentials(self):
        """Test proxy URL without credentials."""
        url = "http://proxy.example.com:8080"
        result = sanitize_proxy_config_for_logging(url)
        assert result["status"] == "enabled"
        assert result["url"] == "http://proxy.example.com:8080"
        assert result["auth"] == "no"

    def test_none_proxy(self):
        """Test None proxy returns disabled status."""
        result = sanitize_proxy_config_for_logging(None)
        assert result == {"status": "disabled"}
        assert "url" not in result
        assert "auth" not in result

    def test_empty_string_proxy(self):
        """Test empty string proxy returns disabled status."""
        result = sanitize_proxy_config_for_logging("")
        assert result == {"status": "disabled"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

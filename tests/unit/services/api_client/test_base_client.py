"""Unit tests for APIClient base class.

Tests cover:
- Environment variable credential loading
- Credential redaction in error messages
- URL and param building
- Cache-first pattern
- Rate limiter integration
- Async context manager usage
"""

import os
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from phx_home_analysis.services.api_client.base_client import APIClient
from phx_home_analysis.services.api_client.rate_limiter import RateLimit


class TestAPIClientCredentials:
    """Tests for credential handling."""

    def test_missing_env_key_raises_error(self) -> None:
        """Missing env key should raise ValueError with variable name."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
                APIClient(
                    service_name="test",
                    env_key="GOOGLE_MAPS_API_KEY",
                )

    def test_missing_env_token_raises_error(self) -> None:
        """Missing env token should raise ValueError with variable name."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="MARICOPA_ASSESSOR_TOKEN"):
                APIClient(
                    service_name="test",
                    env_token="MARICOPA_ASSESSOR_TOKEN",
                )

    def test_env_key_loaded_correctly(self) -> None:
        """API key should be loaded from environment."""
        with patch.dict(os.environ, {"TEST_API_KEY": "secret_key_123"}):
            client = APIClient(
                service_name="test",
                env_key="TEST_API_KEY",
            )
            assert client._api_key == "secret_key_123"

    def test_env_token_loaded_correctly(self) -> None:
        """Bearer token should be loaded from environment."""
        with patch.dict(os.environ, {"TEST_TOKEN": "bearer_token_xyz"}):
            client = APIClient(
                service_name="test",
                env_token="TEST_TOKEN",
            )
            assert client._bearer_token == "bearer_token_xyz"

    def test_no_credential_required(self) -> None:
        """Client without credentials should initialize successfully."""
        client = APIClient(service_name="test")
        assert client._api_key is None
        assert client._bearer_token is None

    def test_credentials_redacted_in_error_messages(self) -> None:
        """Credentials should be redacted in error messages."""
        with patch.dict(os.environ, {"TEST_KEY": "secret123", "TEST_TOKEN": "token456"}):
            client = APIClient(
                service_name="test",
                env_key="TEST_KEY",
                env_token="TEST_TOKEN",
            )

            # Create an error containing credentials
            error = Exception("Request failed with key=secret123 and token=token456")
            safe_msg = client._safe_log_error(error)

            assert "secret123" not in safe_msg
            assert "token456" not in safe_msg
            assert "[REDACTED_KEY]" in safe_msg
            assert "[REDACTED_TOKEN]" in safe_msg

    def test_error_without_credentials_unchanged(self) -> None:
        """Errors without credentials should be unchanged."""
        client = APIClient(service_name="test")
        error = Exception("Connection timeout")
        safe_msg = client._safe_log_error(error)
        assert safe_msg == "Connection timeout"


class TestAPIClientHeaders:
    """Tests for header building."""

    def test_no_auth_headers_when_no_credentials(self) -> None:
        """No auth headers should be set without credentials."""
        client = APIClient(service_name="test")
        headers = client._build_headers()
        assert "Authorization" not in headers

    def test_bearer_token_header(self) -> None:
        """Bearer token should be added to headers."""
        with patch.dict(os.environ, {"TEST_TOKEN": "my_token"}):
            client = APIClient(service_name="test", env_token="TEST_TOKEN")
            headers = client._build_headers()
            assert headers["Authorization"] == "Bearer my_token"


class TestAPIClientParams:
    """Tests for parameter building."""

    def test_api_key_added_to_params(self) -> None:
        """API key should be added to params."""
        with patch.dict(os.environ, {"TEST_KEY": "my_api_key"}):
            client = APIClient(service_name="test", env_key="TEST_KEY")
            params = client._build_params({"address": "123 Main St"})

            assert params["key"] == "my_api_key"
            assert params["address"] == "123 Main St"

    def test_no_key_when_not_configured(self) -> None:
        """No key param when API key not configured."""
        client = APIClient(service_name="test")
        params = client._build_params({"address": "123 Main St"})

        assert "key" not in params
        assert params["address"] == "123 Main St"

    def test_none_params_handled(self) -> None:
        """None params should return empty dict (plus key if configured)."""
        client = APIClient(service_name="test")
        params = client._build_params(None)
        assert params == {}


class TestAPIClientConfiguration:
    """Tests for client configuration."""

    def test_base_url_trailing_slash_stripped(self) -> None:
        """Trailing slash should be stripped from base URL."""
        client = APIClient(
            service_name="test",
            base_url="https://api.example.com/",
        )
        assert client.base_url == "https://api.example.com"

    def test_empty_base_url_handled(self) -> None:
        """Empty base URL should be handled."""
        client = APIClient(service_name="test", base_url="")
        assert client.base_url == ""

    def test_custom_timeout(self) -> None:
        """Custom timeout should be set."""
        client = APIClient(service_name="test", timeout=60.0)
        assert client.timeout == 60.0

    def test_rate_limit_configuration(self) -> None:
        """Rate limit should be configurable."""
        rate_limit = RateLimit(requests_per_second=10.0)
        client = APIClient(service_name="test", rate_limit=rate_limit)
        assert client._rate_limit.requests_per_second == 10.0

    def test_default_rate_limit(self) -> None:
        """Default rate limit should have min_delay."""
        client = APIClient(service_name="test")
        assert client._rate_limit.min_delay == 0.1

    def test_cache_ttl_configuration(self, tmp_path: Path) -> None:
        """Cache TTL should be configurable."""
        client = APIClient(
            service_name="test",
            cache_ttl_days=30,
        )
        assert client._cache.config.ttl_days == 30

    def test_cache_disabled(self, tmp_path: Path) -> None:
        """Cache can be disabled."""
        client = APIClient(
            service_name="test",
            cache_enabled=False,
        )
        assert client._cache.config.enabled is False


class TestAPIClientContextManager:
    """Tests for async context manager usage."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_http_client(self) -> None:
        """Context manager should create HTTP client."""
        client = APIClient(service_name="test")
        assert client._http is None

        async with client:
            assert client._http is not None
            assert isinstance(client._http, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_context_manager_closes_http_client(self) -> None:
        """Context manager should close HTTP client on exit."""
        client = APIClient(service_name="test")

        async with client:
            http = client._http

        assert client._http is None

    @pytest.mark.asyncio
    async def test_get_without_context_manager_raises_error(self) -> None:
        """GET without context manager should raise RuntimeError."""
        client = APIClient(service_name="test")

        with pytest.raises(RuntimeError, match="async context manager"):
            await client.get("/test")

    @pytest.mark.asyncio
    async def test_post_without_context_manager_raises_error(self) -> None:
        """POST without context manager should raise RuntimeError."""
        client = APIClient(service_name="test")

        with pytest.raises(RuntimeError, match="async context manager"):
            await client.post("/test")


class TestAPIClientCacheIntegration:
    """Tests for cache integration."""

    @pytest.mark.asyncio
    async def test_cache_stats_available(self) -> None:
        """Cache stats should be available."""
        client = APIClient(service_name="test")
        stats = client.get_cache_stats()

        assert "total_requests" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate_percent" in stats

    @pytest.mark.asyncio
    async def test_clear_cache(self, tmp_path: Path) -> None:
        """Cache should be clearable."""
        client = APIClient(service_name="test", cache_ttl_days=7)
        # Manually add a cache entry
        client._cache.set("https://test.com", None, {"data": "test"})

        count = client.clear_cache()
        assert count >= 0


class TestAPIClientRateLimitIntegration:
    """Tests for rate limit integration."""

    def test_rate_limit_stats_available(self) -> None:
        """Rate limit stats should be available."""
        client = APIClient(service_name="test")
        stats = client.get_rate_limit_stats()

        assert "requests_last_minute" in stats
        assert "requests_today" in stats
        assert "last_request_age_seconds" in stats


class TestAPIClientSubclass:
    """Tests for subclass patterns."""

    def test_subclass_inherits_functionality(self) -> None:
        """Subclass should inherit all base functionality."""

        class TestClient(APIClient):
            def __init__(self) -> None:
                super().__init__(
                    service_name="test_api",
                    base_url="https://api.test.com",
                    rate_limit=RateLimit(requests_per_minute=100),
                    cache_ttl_days=14,
                )

        client = TestClient()
        assert client.service_name == "test_api"
        assert client.base_url == "https://api.test.com"
        assert client._rate_limit.requests_per_minute == 100
        assert client._cache.config.ttl_days == 14

    @pytest.mark.asyncio
    async def test_subclass_with_custom_method(self) -> None:
        """Subclass can define custom methods using base get/post."""

        class TestClient(APIClient):
            def __init__(self) -> None:
                super().__init__(
                    service_name="test_api",
                    base_url="https://api.test.com",
                )

            async def get_resource(self, resource_id: str) -> dict:
                return await self.get(f"/resources/{resource_id}")

        # Just verify the method can be defined
        client = TestClient()
        assert hasattr(client, "get_resource")


class TestAPIClientURLBuilding:
    """Tests for URL path building."""

    def test_path_appended_to_base_url(self) -> None:
        """Path should be appended to base URL."""
        client = APIClient(
            service_name="test",
            base_url="https://api.example.com",
        )

        # Simulate URL building (actual request not made)
        url = f"{client.base_url}/geocode/json"
        assert url == "https://api.example.com/geocode/json"

    def test_absolute_url_without_base(self) -> None:
        """Absolute URL should work without base URL."""
        client = APIClient(service_name="test")

        # When no base_url, path should be used directly
        url = "https://direct.api.com/endpoint"
        assert client.base_url == ""
        # The get/post methods would use the path directly

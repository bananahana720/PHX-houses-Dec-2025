"""Integration tests for API client infrastructure.

Tests cover:
- Full request flow: rate limit -> API -> cache
- Retry on 429 responses
- Auth header inclusion
- Cache statistics accuracy
- End-to-end subclass usage
"""

import os
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from phx_home_analysis.services.api_client import (
    APIClient,
    CacheConfig,
    RateLimit,
    RateLimiter,
    ResponseCache,
)


class TestFullRequestFlow:
    """Tests for full request flow: rate limit -> API -> cache."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_makes_request_and_caches(self, tmp_path: Path) -> None:
        """GET should make request and cache response."""
        # Mock the API endpoint
        respx.get("https://api.test.com/data").mock(
            return_value=httpx.Response(200, json={"result": "success"})
        )

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
        )
        # Point cache to temp directory
        client._cache = ResponseCache(
            "test", CacheConfig(cache_dir=tmp_path, ttl_days=1)
        )

        async with client:
            # First request - should hit API
            result1 = await client.get("/data")
            assert result1 == {"result": "success"}

            # Second request - should hit cache
            result2 = await client.get("/data")
            assert result2 == {"result": "success"}

        # Verify cache was used
        stats = client.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_skip_cache_bypasses_cache(self, tmp_path: Path) -> None:
        """skip_cache=True should bypass cache."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={"count": call_count})

        respx.get("https://api.test.com/data").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
        )
        client._cache = ResponseCache(
            "test", CacheConfig(cache_dir=tmp_path, ttl_days=1)
        )

        async with client:
            # First request
            result1 = await client.get("/data")
            assert result1["count"] == 1

            # Second request with skip_cache
            result2 = await client.get("/data", skip_cache=True)
            assert result2["count"] == 2  # New API call

    @pytest.mark.asyncio
    @respx.mock
    async def test_params_included_in_request(self) -> None:
        """Query params should be included in request."""
        route = respx.get("https://api.test.com/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            await client.get("/search", params={"q": "test", "limit": "10"})

        # Verify params were sent
        assert route.called
        request = route.calls[0].request
        assert "q=test" in str(request.url)
        assert "limit=10" in str(request.url)


class TestRetryBehavior:
    """Tests for retry behavior on transient errors."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_429(self, tmp_path: Path) -> None:
        """429 response should trigger retry."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call returns 429
                return httpx.Response(
                    429,
                    headers={"Retry-After": "1"},
                )
            # Subsequent calls succeed
            return httpx.Response(200, json={"success": True})

        respx.get("https://api.test.com/data").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            result = await client.get("/data")
            assert result == {"success": True}

        # Verify retry occurred
        assert call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_503(self, tmp_path: Path) -> None:
        """503 response should trigger retry."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(503)
            return httpx.Response(200, json={"success": True})

        respx.get("https://api.test.com/data").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            result = await client.get("/data")
            assert result == {"success": True}

        assert call_count == 2


class TestAuthenticationIntegration:
    """Tests for authentication header integration."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_bearer_token_sent_in_header(self) -> None:
        """Bearer token should be sent in Authorization header."""
        route = respx.get("https://api.test.com/protected").mock(
            return_value=httpx.Response(200, json={"data": "protected"})
        )

        with patch.dict(os.environ, {"TEST_TOKEN": "my_secret_token"}):
            client = APIClient(
                service_name="test",
                base_url="https://api.test.com",
                env_token="TEST_TOKEN",
                rate_limit=RateLimit(min_delay=0.0),
                cache_enabled=False,
            )

            async with client:
                await client.get("/protected")

        # Verify Authorization header was sent
        assert route.called
        request = route.calls[0].request
        assert request.headers.get("Authorization") == "Bearer my_secret_token"

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_key_sent_in_params(self) -> None:
        """API key should be sent as query param."""
        route = respx.get("https://api.test.com/data").mock(
            return_value=httpx.Response(200, json={"data": "value"})
        )

        with patch.dict(os.environ, {"TEST_KEY": "api_key_123"}):
            client = APIClient(
                service_name="test",
                base_url="https://api.test.com",
                env_key="TEST_KEY",
                rate_limit=RateLimit(min_delay=0.0),
                cache_enabled=False,
            )

            async with client:
                await client.get("/data")

        # Verify key was sent in URL
        assert route.called
        request = route.calls[0].request
        assert "key=api_key_123" in str(request.url)


class TestCacheStatisticsIntegration:
    """Tests for cache statistics accuracy."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_cache_stats_after_multiple_requests(self, tmp_path: Path) -> None:
        """Cache stats should be accurate after multiple requests."""
        respx.get("https://api.test.com/a").mock(
            return_value=httpx.Response(200, json={"id": "a"})
        )
        respx.get("https://api.test.com/b").mock(
            return_value=httpx.Response(200, json={"id": "b"})
        )

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
        )
        client._cache = ResponseCache(
            "test", CacheConfig(cache_dir=tmp_path, ttl_days=1)
        )

        async with client:
            # 2 misses
            await client.get("/a")
            await client.get("/b")

            # 3 hits
            await client.get("/a")
            await client.get("/a")
            await client.get("/b")

        stats = client.get_cache_stats()
        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 2
        assert stats["hit_rate_percent"] == 60.0


class TestRateLimiterIntegration:
    """Tests for rate limiter integration."""

    @pytest.mark.asyncio
    async def test_rate_limiter_stats_updated(self) -> None:
        """Rate limiter stats should be updated after requests."""
        limiter = RateLimiter(RateLimit(min_delay=0.0))

        # Simulate requests
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 3


class TestSubclassIntegration:
    """Tests for subclass integration patterns."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_subclass_with_custom_methods(self, tmp_path: Path) -> None:
        """Subclass with custom methods should work correctly."""

        class MockAPIClient(APIClient):
            """Example API client subclass."""

            def __init__(self, cache_dir: Path) -> None:
                super().__init__(
                    service_name="mock_api",
                    base_url="https://mockapi.test.com",
                    rate_limit=RateLimit(min_delay=0.0),
                    cache_ttl_days=1,
                )
                # Use temp cache dir for testing
                self._cache = ResponseCache(
                    "mock_api", CacheConfig(cache_dir=cache_dir, ttl_days=1)
                )

            async def get_user(self, user_id: str) -> dict:
                """Get user by ID."""
                return await self.get(f"/users/{user_id}")

            async def search_users(self, query: str) -> list:
                """Search users."""
                result = await self.get("/users/search", params={"q": query})
                return result.get("users", [])

        # Mock endpoints
        respx.get("https://mockapi.test.com/users/123").mock(
            return_value=httpx.Response(200, json={"id": "123", "name": "Test User"})
        )
        respx.get("https://mockapi.test.com/users/search").mock(
            return_value=httpx.Response(
                200, json={"users": [{"id": "1"}, {"id": "2"}]}
            )
        )

        async with MockAPIClient(tmp_path) as client:
            # Test custom methods
            user = await client.get_user("123")
            assert user["id"] == "123"
            assert user["name"] == "Test User"

            users = await client.search_users("test")
            assert len(users) == 2

            # Verify caching works for custom methods
            user_again = await client.get_user("123")
            assert user_again == user

        # Verify cache was used
        assert client.get_cache_stats()["cache_hits"] >= 1


class TestPOSTIntegration:
    """Tests for POST request integration."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_with_json_body(self) -> None:
        """POST with JSON body should work correctly."""
        route = respx.post("https://api.test.com/create").mock(
            return_value=httpx.Response(201, json={"id": "new-123"})
        )

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            result = await client.post("/create", json_data={"name": "New Item"})
            assert result == {"id": "new-123"}

        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_with_form_data(self) -> None:
        """POST with form data should work correctly."""
        route = respx.post("https://api.test.com/submit").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            result = await client.post("/submit", form_data={"field": "value"})
            assert result == {"status": "ok"}

        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_not_cached(self, tmp_path: Path) -> None:
        """POST responses should not be cached."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json={"count": call_count})

        respx.post("https://api.test.com/action").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
        )
        client._cache = ResponseCache(
            "test", CacheConfig(cache_dir=tmp_path, ttl_days=1)
        )

        async with client:
            result1 = await client.post("/action", json_data={"data": "1"})
            result2 = await client.post("/action", json_data={"data": "2"})

            # Each POST should make a new request
            assert result1["count"] == 1
            assert result2["count"] == 2

        assert call_count == 2


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_400_error_not_retried(self) -> None:
        """400 Bad Request should not be retried."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(400, json={"error": "Bad Request"})

        respx.get("https://api.test.com/data").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get("/data")

            assert exc_info.value.response.status_code == 400

        # 400 is permanent error - should not retry
        assert call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_404_error_not_retried(self) -> None:
        """404 Not Found should not be retried."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(404, json={"error": "Not Found"})

        respx.get("https://api.test.com/missing").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get("/missing")

            assert exc_info.value.response.status_code == 404

        assert call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_exhaustion_raises_error(self) -> None:
        """When all retries are exhausted, error should propagate."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            # Always return 503 to exhaust retries
            return httpx.Response(503, json={"error": "Service Unavailable"})

        respx.get("https://api.test.com/data").mock(side_effect=mock_response)

        client = APIClient(
            service_name="test",
            base_url="https://api.test.com",
            rate_limit=RateLimit(min_delay=0.0),
            cache_enabled=False,
        )

        async with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get("/data")

            assert exc_info.value.response.status_code == 503

        # Should have retried max_retries (5) + 1 initial = 6 attempts
        assert call_count == 6


class TestZeroTTLCache:
    """Tests for zero TTL cache behavior."""

    def test_zero_ttl_expires_immediately(self, tmp_path: Path) -> None:
        """Cache with ttl_days=0 should expire entries immediately."""
        config = CacheConfig(cache_dir=tmp_path, ttl_days=0)
        cache = ResponseCache("test_service", config)

        url = "https://api.example.com/data"
        cache.set(url, None, {"test": True})

        # Entry should immediately be considered expired
        result = cache.get(url, None)
        assert result is None

        # Stats should show a miss (expired entry counts as miss)
        stats = cache.get_stats()
        assert stats["cache_misses"] == 1


class TestPOSTWithAuthHeaders:
    """Tests for POST requests with authentication headers."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_includes_bearer_token(self) -> None:
        """POST request should include Authorization header with Bearer token."""
        route = respx.post("https://api.test.com/create").mock(
            return_value=httpx.Response(201, json={"id": "new-123"})
        )

        with patch.dict(os.environ, {"TEST_TOKEN": "my_post_token"}):
            client = APIClient(
                service_name="test",
                base_url="https://api.test.com",
                env_token="TEST_TOKEN",
                rate_limit=RateLimit(min_delay=0.0),
                cache_enabled=False,
            )

            async with client:
                result = await client.post("/create", json_data={"name": "Test"})
                assert result == {"id": "new-123"}

        # Verify Authorization header was sent
        assert route.called
        request = route.calls[0].request
        assert request.headers.get("Authorization") == "Bearer my_post_token"

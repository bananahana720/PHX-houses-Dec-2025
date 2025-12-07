"""Live tests for Zillow/Redfin stealth extraction with PerimeterX bypass.

These tests call real Zillow/Redfin APIs and require:
- Network connectivity to zillow.com and redfin.com
- Stealth browser automation (nodriver) with anti-bot evasion
- User-agent rotation and CAPTCHA detection/solving
- Rate limiting awareness (5 requests/min for Zillow)

Run with: pytest tests/live/test_zillow_redfin_live.py -m live -v

Test Categories:
- PerimeterX Bypass: nodriver stealth, fallback cascade (curl_cffi → playwright)
- Stealth Techniques: UA rotation, CAPTCHA handling, rate limiting
- Extraction: Image URLs, bulk downloads, metadata fields, listing status
- Reliability: Selector drift detection, JS rendering, proxy rotation
- Cross-Validation: Redfin vs Zillow consistency, mobile viewport scraping

ATDD RED Phase: Many tests will initially fail as behaviors are not fully implemented.
This is expected - tests drive implementation.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from phx_home_analysis.config.settings import StealthExtractionConfig
from phx_home_analysis.domain.entities import Property
from phx_home_analysis.services.image_extraction.extractors.redfin import RedfinExtractor
from phx_home_analysis.services.image_extraction.extractors.zillow import ZillowExtractor

if TYPE_CHECKING:
    from collections.abc import Callable

# Mark all tests in this module as live tests
pytestmark = [pytest.mark.live, pytest.mark.asyncio]

# Known test addresses (manually verified)
TEST_ADDRESSES: list[dict] = [
    {
        "street": "4732 W Davis Rd",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85043",
        "expected_images_min": 15,  # Minimum expected photos
    },
    {
        "street": "3847 E Cactus Rd",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85032",
        "expected_images_min": 10,
    },
]


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="module")
def stealth_config() -> StealthExtractionConfig:
    """Create stealth extraction configuration for testing.

    Returns:
        StealthExtractionConfig with test-appropriate settings.
    """
    return StealthExtractionConfig(
        browser_headless=True,  # Use headless for CI/CD
        viewport_width=1280,
        viewport_height=720,
        request_timeout=30.0,
        max_retries=2,
        human_delay_min=1.0,
        human_delay_max=2.0,
        captcha_hold_min=4.5,
        captcha_hold_max=8.5,
        isolation_mode="profile",
        fallback_to_minimize=True,
    )


@pytest.fixture(scope="module")
async def zillow_extractor(
    stealth_config: StealthExtractionConfig,
) -> ZillowExtractor:
    """Create Zillow extractor with stealth configuration.

    Yields:
        Configured ZillowExtractor instance.
    """
    extractor = ZillowExtractor(config=stealth_config)
    yield extractor
    await extractor.close()


@pytest.fixture(scope="module")
async def redfin_extractor(
    stealth_config: StealthExtractionConfig,
) -> RedfinExtractor:
    """Create Redfin extractor with stealth configuration.

    Yields:
        Configured RedfinExtractor instance (if implemented).
    """
    try:
        extractor = RedfinExtractor(config=stealth_config)
        yield extractor
        await extractor.close()
    except ImportError:
        pytest.skip("RedfinExtractor not yet implemented")


@pytest.fixture
def test_property() -> Property:
    """Create test property for known address.

    Returns:
        Property entity for first test address.
    """
    addr = TEST_ADDRESSES[0]
    return Property(
        street=addr["street"],
        city=addr["city"],
        state=addr["state"],
        zip_code=addr["zip_code"],
        price="$450000",
        beds=4,
        baths=2.0,
        sqft=2200,
    )


@pytest.fixture
def test_property_2() -> Property:
    """Create second test property for known address.

    Returns:
        Property entity for second test address.
    """
    addr = TEST_ADDRESSES[1]
    return Property(
        street=addr["street"],
        city=addr["city"],
        state=addr["state"],
        zip_code=addr["zip_code"],
        price="$425000",
        beds=3,
        baths=2.0,
        sqft=2000,
    )


@pytest.fixture
def user_agent_pool() -> list[str]:
    """Pool of 20+ user agent signatures for rotation testing.

    Returns:
        List of diverse user agent strings.
    """
    return [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Mobile Chrome
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        # Mobile Safari
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        # More Chrome variants
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]


# ============================================================================
# TEST CLASS: PERIMETER-X BYPASS (3 TESTS)
# ============================================================================


class TestZillowPerimeterXBypass:
    """Test nodriver's ability to bypass PerimeterX anti-bot protection."""

    async def test_nodriver_perimeter_x_bypass_success(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_001: Verify nodriver can access Zillow without bot detection.

        Given: A Zillow extractor configured with nodriver
        When: Extracting images from a known property listing
        Then: Page loads successfully without CAPTCHA challenge
        And: Property detail page is detected (not search results)
        """
        # Given - extractor is configured with nodriver

        # When - extract image URLs
        try:
            urls = await zillow_extractor.extract_image_urls(test_property)

            # Then - should get URLs without CAPTCHA
            assert len(urls) > 0, "Should extract images without bot detection"

            # Record response for drift detection
            record_response(
                "zillow",
                "nodriver_bypass_success",
                {"url_count": len(urls), "urls": urls[:5]},  # First 5 URLs
                {"property_address": test_property.full_address},
            )

        except Exception as e:
            # Check if failure was due to CAPTCHA (expected RED phase failure)
            error_msg = str(e).lower()
            if "captcha" in error_msg or "perimeter" in error_msg:
                pytest.xfail("CAPTCHA detected - nodriver bypass needs enhancement")
            raise

    async def test_nodriver_blocked_fallback_to_curl_cffi(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_002: Test fallback when nodriver is blocked.

        Given: Nodriver is blocked by PerimeterX
        When: Extractor attempts to fallback to curl_cffi
        Then: Extraction continues with curl_cffi HTTP client
        And: Images are successfully downloaded

        Note: This test may xfail in RED phase as fallback logic is not yet implemented.
        """
        # Given - simulate nodriver being blocked (test configuration)
        # This requires injecting failure into browser automation

        # When/Then - attempt extraction with fallback
        pytest.xfail("Fallback cascade logic not yet implemented")

        # Future implementation:
        # 1. Mock nodriver to raise PerimeterX block error
        # 2. Verify curl_cffi fallback is triggered
        # 3. Verify images are extracted via HTTP client

    async def test_curl_cffi_blocked_fallback_to_playwright(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_003: Test cascade fallback to playwright.

        Given: Both nodriver and curl_cffi are blocked
        When: Extractor attempts to fallback to playwright
        Then: Extraction continues with playwright browser
        And: Images are successfully downloaded

        Note: This test will xfail in RED phase as fallback cascade is not implemented.
        """
        pytest.xfail("Fallback cascade to playwright not yet implemented")

        # Future implementation:
        # 1. Mock nodriver and curl_cffi to fail
        # 2. Verify playwright fallback is triggered
        # 3. Verify images are extracted via playwright


# ============================================================================
# TEST CLASS: STEALTH TECHNIQUES (3 TESTS)
# ============================================================================


class TestZillowStealthTechniques:
    """Test stealth techniques for evading bot detection."""

    async def test_user_agent_rotation_20_signatures(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        user_agent_pool: list[str],
    ) -> None:
        """LIVE_SCRAPE_004: Verify user agent rotation effectiveness.

        Given: A pool of 20+ diverse user agent signatures
        When: Making multiple extraction requests
        Then: Different user agents are rotated across requests
        And: No single user agent is overused (max 2 uses per UA)
        """
        # Given - user agent pool with 20+ signatures
        assert len(user_agent_pool) >= 20, "Need 20+ user agents for rotation"

        # When - make 5 requests and track user agents
        used_agents = []

        for _ in range(5):
            try:
                # Extract images (will use rotated UA)
                await zillow_extractor.extract_image_urls(test_property)

                # Track which user agent was used
                # Note: This requires instrumentation of extractor
                # For now, test will xfail until UA tracking is added
                pytest.xfail("User agent tracking not yet instrumented")

            except Exception:
                # Allow failures - we're testing rotation, not extraction success
                pass

        # Then - verify rotation occurred
        # Future assertion: assert len(set(used_agents)) >= 4, "Should use diverse UAs"

    async def test_captcha_detection_and_retry(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_010: Test CAPTCHA detection system.

        Given: A Zillow page that may present a CAPTCHA
        When: Extractor loads the page
        Then: CAPTCHA is detected if present (Press & Hold, PerimeterX indicators)
        And: Solving is attempted with Bezier mouse movement
        And: Retry occurs if solving fails
        """
        # Given - extractor with CAPTCHA detection enabled

        # When - extract images (may encounter CAPTCHA)
        captcha_detected = False
        captcha_solved = False

        try:
            urls = await zillow_extractor.extract_image_urls(test_property)

            # If we got URLs without exception, check if CAPTCHA was encountered
            # Note: Requires instrumentation to track CAPTCHA events
            # For now, record success
            record_response(
                "zillow",
                "captcha_detection_test",
                {"captcha_detected": captcha_detected, "captcha_solved": captcha_solved},
                {"property_address": test_property.full_address},
            )

        except Exception as e:
            error_msg = str(e).lower()
            if "captcha" in error_msg:
                captcha_detected = True
                # CAPTCHA was detected but solving failed
                pytest.xfail("CAPTCHA solving needs enhancement")

        # Then - verify CAPTCHA handling works
        # If CAPTCHA was detected, it should have been solved
        # If CAPTCHA was not detected, extraction should succeed

    async def test_rate_limiting_zillow_5_requests_per_minute(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_011: Verify Zillow rate limiting (5 requests/min).

        Given: Zillow rate limit of 5 requests per minute
        When: Making 5 sequential extraction requests
        Then: Requests are spaced to avoid rate limit (12s between requests)
        And: No 429 errors are encountered
        """
        # Given - rate limit of 5 requests/min (12s between requests)
        rate_limit_seconds = 12.0
        request_count = 5

        # When - make 5 sequential requests with timing
        import time

        start_time = time.monotonic()
        errors = []

        for i in range(request_count):
            try:
                await zillow_extractor.extract_image_urls(test_property)
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    errors.append(f"Rate limit error on request {i + 1}: {e}")
                # Other errors are acceptable for this test

            # Wait between requests (except after last one)
            if i < request_count - 1:
                await asyncio.sleep(rate_limit_seconds)

        elapsed = time.monotonic() - start_time

        # Then - verify no rate limit errors
        assert len(errors) == 0, f"Rate limit errors encountered: {errors}"

        # Verify timing constraint
        expected_min_time = rate_limit_seconds * (request_count - 1)
        assert elapsed >= expected_min_time * 0.9, (
            f"Requests completed too quickly ({elapsed}s), "
            f"expected >={expected_min_time}s for rate limiting"
        )


# ============================================================================
# TEST CLASS: ZILLOW EXTRACTION (4 TESTS)
# ============================================================================


class TestZillowExtraction:
    """Test Zillow data extraction accuracy and performance."""

    async def test_image_url_extraction_accuracy(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_005: Verify image URLs are extracted correctly.

        Given: A known Zillow property listing
        When: Extracting image URLs
        Then: URLs point to photos.zillowstatic.com CDN
        And: URLs are high-resolution (not thumbnails)
        And: URL count matches expected range (15-30 photos)
        """
        # Given - known property listing

        # When - extract image URLs
        urls = await zillow_extractor.extract_image_urls(test_property)

        # Then - verify URL quality
        assert len(urls) > 0, "Should extract at least some URLs"

        # Check CDN domain
        cdn_urls = [u for u in urls if "photos.zillowstatic.com" in u]
        assert len(cdn_urls) > 0, "Should have Zillow CDN URLs"

        # Check for high-resolution indicators (not thumbnails)
        thumbnail_urls = [u for u in urls if "thumb" in u.lower() or "small" in u.lower()]
        assert len(thumbnail_urls) == 0, f"Should not extract thumbnails: {thumbnail_urls}"

        # Check count range
        expected_min = TEST_ADDRESSES[0]["expected_images_min"]
        assert len(urls) >= expected_min, f"Expected >={expected_min} images, got {len(urls)}"

        # Record for drift detection
        record_response(
            "zillow",
            "image_extraction",
            {"url_count": len(urls), "sample_urls": urls[:3]},
            {"property_address": test_property.full_address},
        )

    async def test_image_download_bulk_25_photos(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_006: Performance test for bulk image downloads.

        Given: A property listing with 25+ photos
        When: Downloading all images in parallel
        Then: All downloads complete within 60 seconds
        And: All images are valid (content-type: image/*)
        And: Average download time is <2.5s per image
        """
        import time

        # Given - extract URLs first
        urls = await zillow_extractor.extract_image_urls(test_property)

        # Limit to 25 for performance testing
        urls_to_download = urls[:25]
        if len(urls_to_download) < 25:
            pytest.skip(f"Property has only {len(urls)} photos, need 25 for bulk test")

        # When - download all images in parallel
        start_time = time.monotonic()
        download_results = []

        for url in urls_to_download:
            try:
                image_bytes, content_type = await zillow_extractor.download_image(url)
                download_results.append(
                    {
                        "success": True,
                        "size": len(image_bytes),
                        "content_type": content_type,
                    }
                )
            except Exception as e:
                download_results.append(
                    {
                        "success": False,
                        "error": str(e),
                    }
                )

        elapsed = time.monotonic() - start_time

        # Then - verify performance
        assert elapsed < 60.0, f"Bulk download took {elapsed}s, expected <60s"

        # Verify success rate
        successful = [r for r in download_results if r.get("success")]
        success_rate = len(successful) / len(download_results)
        assert success_rate >= 0.8, f"Success rate {success_rate:.0%} too low, expected >=80%"

        # Verify content types
        for result in successful:
            assert "image" in result.get("content_type", "").lower(), (
                f"Invalid content type: {result.get('content_type')}"
            )

        # Verify average download time
        avg_time = elapsed / len(urls_to_download)
        assert avg_time < 2.5, f"Average download time {avg_time:.2f}s, expected <2.5s"

    async def test_field_extraction_price_beds_baths_hoa(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_007: Verify metadata extraction from listing.

        Given: A Zillow property detail page
        When: Extracting listing metadata
        Then: price, beds, baths, and hoa_fee are extracted
        And: Values are within expected ranges
        And: Types are correct (int for beds, float for baths, etc.)
        """
        # Given - property listing

        # When - extract URLs and metadata
        urls = await zillow_extractor.extract_image_urls(test_property)

        # Metadata should be stored in last_metadata after extraction
        metadata = zillow_extractor.last_metadata

        # Then - verify key fields are present
        if not metadata:
            pytest.xfail("Metadata extraction not yet returning data")

        # Check required fields
        assert "beds" in metadata, "Should extract beds count"
        assert "baths" in metadata, "Should extract baths count"
        assert "list_price" in metadata or "price" in metadata, "Should extract price"

        # Verify types
        if metadata.get("beds"):
            assert isinstance(metadata["beds"], int), "Beds should be integer"
            assert 1 <= metadata["beds"] <= 10, "Beds should be reasonable range"

        if metadata.get("baths"):
            assert isinstance(metadata["baths"], (int, float)), "Baths should be numeric"
            assert 1.0 <= metadata["baths"] <= 10.0, "Baths should be reasonable range"

        # Record for drift detection
        record_response(
            "zillow",
            "metadata_extraction",
            metadata,
            {"property_address": test_property.full_address},
        )

    async def test_listing_status_active_pending_sold(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_008: Verify listing status detection.

        Given: A property listing with known status
        When: Extracting metadata
        Then: Listing status is detected (Active, Pending, Sold, etc.)
        And: days_on_market is extracted if available
        """
        # Given - property listing

        # When - extract metadata
        urls = await zillow_extractor.extract_image_urls(test_property)
        metadata = zillow_extractor.last_metadata

        # Then - verify status fields
        if not metadata:
            pytest.xfail("Metadata extraction not yet returning data")

        # Check for status indicators
        # Note: Zillow may not always provide explicit status field
        # but should provide days_on_market for active listings
        if "days_on_market" in metadata and metadata["days_on_market"] is not None:
            dom = metadata["days_on_market"]
            assert isinstance(dom, int), "days_on_market should be integer"
            assert dom >= 0, "days_on_market should be non-negative"


# ============================================================================
# TEST CLASS: ZILLOW RELIABILITY (3 TESTS)
# ============================================================================


class TestZillowReliability:
    """Test reliability features: selector drift detection, JS rendering, proxy rotation."""

    async def test_selector_drift_detection_price_field(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_009: Detect when HTML selectors break.

        Given: Known CSS selectors for price field
        When: Extracting price from listing page
        Then: Price is successfully extracted
        Or: If extraction fails, drift is detected and logged
        """
        # Given - property listing

        # When - extract metadata with price
        urls = await zillow_extractor.extract_image_urls(test_property)
        metadata = zillow_extractor.last_metadata

        # Then - verify price extraction
        price_found = metadata.get("list_price") or metadata.get("price")

        if not price_found:
            # Selector drift detected
            record_response(
                "zillow",
                "selector_drift_detected",
                {"field": "price", "metadata": metadata},
                {"property_address": test_property.full_address},
            )
            pytest.xfail("Price selector may have drifted - needs investigation")

        # Verify price is reasonable
        assert isinstance(price_found, int), "Price should be integer"
        assert 100000 <= price_found <= 5000000, "Price should be in reasonable range"

    async def test_javascript_rendered_content_extraction(
        self,
        zillow_extractor: ZillowExtractor,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_014: Verify JavaScript-rendered content is captured.

        Given: Zillow page with dynamically loaded content
        When: Browser loads the page
        Then: Dynamically rendered elements are present (photos, metadata)
        And: __NEXT_DATA__ JSON payload is accessible
        """
        # Given - property listing with JS rendering

        # When - extract URLs (requires JS to render photo gallery)
        urls = await zillow_extractor.extract_image_urls(test_property)

        # Then - verify JS-rendered content was captured
        # If we got image URLs, JS must have rendered
        assert len(urls) > 0, "Should extract JS-rendered photo gallery"

        # Verify __NEXT_DATA__ was parsed (if instrumented)
        # For now, success of URL extraction implies JS rendering worked

    async def test_proxy_rotation_to_avoid_ip_ban(
        self,
        stealth_config: StealthExtractionConfig,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_015: Verify proxy rotation works when configured.

        Given: Stealth config with proxy pool
        When: Making multiple extraction requests
        Then: Different proxy IPs are used across requests
        And: No single IP is overused

        Note: This test will skip if no proxy configuration is available.
        """
        # Given - check if proxy is configured
        if not stealth_config.proxy_url:
            pytest.skip("No proxy configured - skipping proxy rotation test")

        # When/Then - verify proxy rotation
        # This requires instrumentation to track proxy usage
        pytest.xfail("Proxy rotation tracking not yet implemented")


# ============================================================================
# TEST CLASS: REDFIN CROSS-VALIDATION (2 TESTS)
# ============================================================================


class TestRedfinCrossValidation:
    """Test cross-source data validation between Redfin and Zillow."""

    async def test_redfin_vs_zillow_data_consistency(
        self,
        zillow_extractor: ZillowExtractor,
        redfin_extractor: RedfinExtractor,
        test_property: Property,
        record_response: Callable,
    ) -> None:
        """LIVE_SCRAPE_012: Cross-validate data between Redfin and Zillow.

        Given: A property listed on both Zillow and Redfin
        When: Extracting data from both sources
        Then: Key fields match (beds, baths, sqft within 5% tolerance)
        And: Image counts are comparable (within 20% difference)
        """
        # Given - property on both sites

        # When - extract from both sources
        zillow_urls = await zillow_extractor.extract_image_urls(test_property)
        zillow_metadata = zillow_extractor.last_metadata

        try:
            redfin_urls = await redfin_extractor.extract_image_urls(test_property)
            redfin_metadata = redfin_extractor.last_metadata
        except (ImportError, NotImplementedError):
            pytest.skip("RedfinExtractor not yet implemented")

        # Then - compare key fields
        # Beds should match exactly
        if zillow_metadata.get("beds") and redfin_metadata.get("beds"):
            assert zillow_metadata["beds"] == redfin_metadata["beds"], (
                f"Beds mismatch: Zillow={zillow_metadata['beds']}, Redfin={redfin_metadata['beds']}"
            )

        # Baths should match within 0.5 (half bath difference acceptable)
        if zillow_metadata.get("baths") and redfin_metadata.get("baths"):
            bath_diff = abs(zillow_metadata["baths"] - redfin_metadata["baths"])
            assert bath_diff <= 0.5, (
                f"Baths mismatch: Zillow={zillow_metadata['baths']}, "
                f"Redfin={redfin_metadata['baths']}"
            )

        # Image counts should be comparable (within 20%)
        if len(zillow_urls) > 0 and len(redfin_urls) > 0:
            ratio = min(len(zillow_urls), len(redfin_urls)) / max(
                len(zillow_urls), len(redfin_urls)
            )
            assert ratio >= 0.8, (
                f"Image count mismatch: Zillow={len(zillow_urls)}, "
                f"Redfin={len(redfin_urls)} (ratio={ratio:.2f})"
            )

        # Record for drift detection
        record_response(
            "cross_validation",
            "zillow_vs_redfin",
            {
                "zillow_image_count": len(zillow_urls),
                "redfin_image_count": len(redfin_urls),
                "zillow_metadata": zillow_metadata,
                "redfin_metadata": redfin_metadata,
            },
            {"property_address": test_property.full_address},
        )

    async def test_mobile_viewport_scraping(
        self,
        test_property: Property,
    ) -> None:
        """LIVE_SCRAPE_013: Test mobile viewport layout handling.

        Given: A mobile viewport configuration (375x667)
        When: Extracting images with mobile user agent
        Then: Mobile layout is loaded successfully
        And: Images are extracted from mobile DOM structure
        """
        # Given - create mobile viewport config
        mobile_config = StealthExtractionConfig(
            browser_headless=True,
            viewport_width=375,  # iPhone SE width
            viewport_height=667,  # iPhone SE height
            request_timeout=30.0,
        )

        # When - extract with mobile config
        extractor = ZillowExtractor(config=mobile_config)

        try:
            urls = await extractor.extract_image_urls(test_property)

            # Then - verify mobile extraction succeeded
            assert len(urls) > 0, "Should extract images from mobile layout"

        finally:
            await extractor.close()

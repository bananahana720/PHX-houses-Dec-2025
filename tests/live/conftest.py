"""Live test fixtures with response recording support.

Provides:
- Real API client factories (with credential validation)
- Response recording fixture for drift detection
- Rate limiter integration fixtures
- Skip decorators for missing credentials
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from phx_home_analysis.services.api_client.rate_limiter import RateLimit, RateLimiter
from phx_home_analysis.services.county_data import MaricopaAssessorClient

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from _pytest.config import Config
    from _pytest.config.argparsing import Parser

    from phx_home_analysis.config.settings import StealthExtractionConfig
    from phx_home_analysis.services.image_extraction.browser_pool import BrowserPool

# Directory for recorded API responses
RECORDED_DIR = Path(__file__).parent.parent / "fixtures" / "recorded"


def pytest_addoption(parser: Parser) -> None:
    """Add custom pytest command-line options for live tests.

    Options:
        --record-responses: Record API responses to tests/fixtures/recorded/
        --live-rate-limit: Override rate limit seconds (default: 0.5)
    """
    parser.addoption(
        "--record-responses",
        action="store_true",
        default=False,
        help="Record live API responses to tests/fixtures/recorded/",
    )
    parser.addoption(
        "--live-rate-limit",
        type=float,
        default=0.5,
        help="Rate limit seconds between API calls (default: 0.5)",
    )


def pytest_configure(config: Config) -> None:
    """Register custom markers for live tests."""
    config.addinivalue_line(
        "markers",
        "live: marks tests as requiring real API calls (deselect with '-m \"not live\"')",
    )
    config.addinivalue_line(
        "markers",
        "requires_token: marks tests as requiring MARICOPA_ASSESSOR_TOKEN",
    )


@pytest.fixture(scope="module")
def live_rate_limit(request: pytest.FixtureRequest) -> float:
    """Get rate limit from command line or use default.

    Returns:
        Rate limit in seconds between API calls.
    """
    return request.config.getoption("--live-rate-limit")


@pytest.fixture(scope="module")
def assessor_token() -> str | None:
    """Get Maricopa Assessor API token from environment.

    Returns:
        Token string if available, None otherwise.
    """
    return os.getenv("MARICOPA_ASSESSOR_TOKEN")


@pytest.fixture(scope="module")
def assessor_client(
    assessor_token: str | None,
    live_rate_limit: float,
) -> Generator[MaricopaAssessorClient, None, None]:
    """Create real API client for live testing.

    Skips test if MARICOPA_ASSESSOR_TOKEN not available.

    Yields:
        Configured MaricopaAssessorClient instance.
    """
    if not assessor_token:
        pytest.skip("MARICOPA_ASSESSOR_TOKEN not set - skipping live test")

    # Create client with configured rate limit
    client = MaricopaAssessorClient(
        token=assessor_token,
        rate_limit_seconds=live_rate_limit,
    )
    yield client


@pytest.fixture(scope="module")
def shared_rate_limiter() -> RateLimiter:
    """Shared rate limiter for sequential live tests.

    Ensures all live tests respect API rate limits collectively.
    Uses conservative settings to prevent 429 errors.

    Returns:
        Configured RateLimiter instance.
    """
    return RateLimiter(
        RateLimit(
            requests_per_minute=60,  # Conservative limit
            throttle_threshold=0.7,  # Proactive throttling at 70%
            min_delay=0.5,
        )
    )


@pytest.fixture
def record_response(
    request: pytest.FixtureRequest,
) -> Generator[Callable[[str, str, dict, dict | None], None], None, None]:
    """Fixture to record API responses for mock drift detection.

    Usage in test:
        async def test_example(record_response, assessor_client):
            response = await api_call()
            record_response("county_assessor", "parcel_lookup", response)

    Recordings are saved to tests/fixtures/recorded/ with timestamp.

    Yields:
        Recording function: (api_name, operation, response, metadata) -> None
    """
    recordings: list[dict[str, Any]] = []
    should_record = request.config.getoption("--record-responses", default=False)

    def _record(
        api_name: str,
        operation: str,
        response: dict,
        metadata: dict | None = None,
    ) -> None:
        """Record an API response.

        Args:
            api_name: API identifier (e.g., "county_assessor")
            operation: Operation name (e.g., "parcel_lookup")
            response: API response data (dict or dataclass-converted dict)
            metadata: Optional metadata (e.g., input parameters)
        """
        if should_record:
            recordings.append(
                {
                    "api": api_name,
                    "operation": operation,
                    "response": response,
                    "metadata": metadata or {},
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "schema_version": "1.0",
                    "test_name": request.node.name,
                }
            )

    yield _record

    # Save recordings after test completes
    if recordings:
        RECORDED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        output_file = RECORDED_DIR / f"recording_{test_name}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(recordings, f, indent=2, default=str, ensure_ascii=False)


# Mark all tests in this module as live tests
pytestmark = pytest.mark.live


# =============================================================================
# Zillow/Redfin Extraction Fixtures
# Added: 2025-12-04 for Epic 2 ATDD
# =============================================================================


@pytest.fixture(scope="module")
def stealth_extraction_config() -> StealthExtractionConfig:
    """Load stealth extraction configuration with conservative test timeouts.

    Configures:
    - Browser timeouts (10s instead of 30s for faster test failures)
    - Human delays (0.5-1s instead of 1-3s for faster tests)
    - CAPTCHA hold times (conservative but realistic)

    Returns:
        StealthExtractionConfig instance configured for testing

    Note:
        Tests can override individual fields for specific scenarios.
        Use from_env() to load from environment variables (proxy, isolation mode, etc.).
    """
    from phx_home_analysis.config.settings import StealthExtractionConfig

    return StealthExtractionConfig(
        # Browser settings - test-optimized
        browser_headless=True,  # Headless for CI/CD environments
        viewport_width=1366,  # Most common laptop resolution
        viewport_height=768,
        # Request settings - faster timeouts for tests
        request_timeout=10.0,  # 10s instead of 30s
        max_retries=2,  # Reduced retries for faster failure
        # Human behavior - faster for tests
        human_delay_min=0.5,
        human_delay_max=1.0,
        # CAPTCHA handling - conservative for live testing
        captcha_hold_min=4.5,
        captcha_hold_max=6.5,
    )


@pytest.fixture(scope="module")
def browser_pool(stealth_extraction_config: StealthExtractionConfig) -> Generator:
    """Create and manage a browser pool for live extraction tests.

    Creates a nodriver browser pool shared across tests within the module.
    Automatically cleans up browsers after tests complete.

    Args:
        stealth_extraction_config: Stealth configuration with browser settings

    Yields:
        BrowserPool instance ready for test use

    Note:
        This fixture creates real browser instances. Tests should skip gracefully
        if browser cannot be launched (e.g., in headless CI without display).
    """
    from phx_home_analysis.services.image_extraction.browser_pool import BrowserPool

    # Create pool with module-level configuration
    pool = BrowserPool(config=stealth_extraction_config)

    yield pool

    # Cleanup after tests
    try:
        pool.close()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Error closing browser pool: %s", e)


@pytest.fixture(scope="function")
def zillow_extractor(
    browser_pool: BrowserPool,
    stealth_extraction_config: StealthExtractionConfig,
) -> Generator:
    """Create ZillowExtractor instance for live testing.

    Creates a fresh extractor for each test using the shared browser pool.

    Args:
        browser_pool: Shared browser pool from module fixture
        stealth_extraction_config: Stealth configuration

    Yields:
        ZillowExtractor instance configured for testing
    """
    from phx_home_analysis.services.image_extraction.extractors.zillow import (
        ZillowExtractor,
    )

    extractor = ZillowExtractor(config=stealth_extraction_config)
    # Inject the shared browser pool
    extractor._browser_pool = browser_pool

    yield extractor

    # Cleanup
    try:
        extractor.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def redfin_extractor(
    browser_pool: BrowserPool,
    stealth_extraction_config: StealthExtractionConfig,
) -> Generator:
    """Create RedfinExtractor instance for live testing.

    Creates a fresh extractor for each test using the shared browser pool.

    Args:
        browser_pool: Shared browser pool from module fixture
        stealth_extraction_config: Stealth configuration

    Yields:
        RedfinExtractor instance configured for testing
    """
    from phx_home_analysis.services.image_extraction.extractors.redfin import (
        RedfinExtractor,
    )

    extractor = RedfinExtractor(config=stealth_extraction_config)
    # Inject the shared browser pool
    extractor._browser_pool = browser_pool

    yield extractor

    # Cleanup
    try:
        extractor.close()
    except Exception:
        pass


@pytest.fixture(scope="module")
def extraction_rate_limiter() -> RateLimiter:
    """Configure rate limiter for Zillow/Redfin live extraction tests.

    Uses conservative settings to prevent 429 rate limit errors:
    - 5 requests/minute (conservative for live sites)
    - 0.7 throttle threshold (proactive throttling at 70%)
    - 1.0s minimum delay between requests

    This ensures tests respect site rate limits even in parallel execution.

    Returns:
        Configured RateLimiter instance
    """
    return RateLimiter(
        RateLimit(
            requests_per_minute=5,  # Very conservative for live sites
            throttle_threshold=0.7,  # Proactive throttling at 70%
            min_delay=1.0,  # 1s minimum between requests
        )
    )


@pytest.fixture(scope="session")
def known_zillow_urls() -> dict[str, str]:
    """Known working Zillow property URLs for regression testing.

    Provides a dictionary of addresses mapped to known working Zillow URLs
    for validation that extraction still works against real Zillow pages.

    Returns:
        Dictionary mapping addresses to Zillow property URLs

    Note:
        These URLs are for testing only. Actual extraction tests should use
        the extract_image_urls() method which handles URL discovery internally.

        Format:
            {
                "address": "https://www.zillow.com/homedetails/..._zpid/",
                ...
            }

        All URLs must be verified working before use. Update if Zillow
        restructures property pages or changes URL formats.
    """
    return {
        "123 Desert Rose Ln, Phoenix, AZ 85001": (
            "https://www.zillow.com/homedetails/"
            "123-Desert-Rose-Ln-Phoenix-AZ-85001/2040000000_zpid/"
        ),
        "456 North Avenue, Scottsdale, AZ 85251": (
            "https://www.zillow.com/homedetails/"
            "456-North-Avenue-Scottsdale-AZ-85251/2050000000_zpid/"
        ),
    }

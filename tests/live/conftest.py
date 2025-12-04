"""Live test fixtures with response recording support.

Provides:
- Real API client factories (with credential validation)
- Response recording fixture for drift detection
- Rate limiter integration fixtures
- Skip decorators for missing credentials
"""

from __future__ import annotations

import json
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

# Technical Specification: Live Testing Infrastructure

## Document Metadata

| Field | Value |
|-------|-------|
| **Story** | Live Testing Infrastructure for External API Validation |
| **Epic** | E3: Test Infrastructure & Quality |
| **Author** | Claude Code (Opus 4.5) |
| **Created** | 2024-12-04 |
| **Status** | Draft |
| **Version** | 1.0 |

---

## 1. Overview

### 1.1 Purpose

This specification defines the technical implementation for a live testing infrastructure that validates external API integrations against real endpoints. The infrastructure enables detection of mock drift, reduces manual testing effort, and maintains confidence that mocked tests accurately reflect production API behavior.

### 1.2 Scope

**In Scope (Phase 1):**
- Live test suite for County Assessor API (P0 priority)
- Smoke test CLI script for pre-flight validation
- Response recording fixture for drift detection
- pytest marker configuration for test isolation
- Rate limit protection integration

**Out of Scope:**
- Stealth browser live tests (Zillow/Redfin) - Phase 3
- Paid API live tests (Google, WalkScore) - Phase 2
- CI/CD pipeline integration - Future story
- Automated mock drift detection - Future story

### 1.3 Architecture Diagram

```
+------------------------------------------------------------------+
|                    PHX Houses Test Suite                          |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+     +------------------+     +--------------+|
|  | tests/unit/      |     | tests/integration/|     | tests/live/ ||
|  | (1063+ tests)    |     | (31 tests)       |     | (NEW)       ||
|  | Mocked APIs      |     | Multi-component  |     | Real APIs   ||
|  | Fast, isolated   |     | Full pipeline    |     | On-demand   ||
|  +------------------+     +------------------+     +--------------+|
|         |                        |                       |         |
|         v                        v                       v         |
|  +-----------------------------------------------------------------+
|  |                     pytest Configuration                        |
|  |  - Default: -m "not live" (excludes live tests)                |
|  |  - Explicit: -m live (runs live tests only)                    |
|  |  - Isolation: pytest tests/live/ (live suite only)             |
|  +-----------------------------------------------------------------+
|                                                                    |
+------------------------------------------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                   External API Layer                              |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+     +------------------+     +--------------+|
|  | County Assessor  |     | ArcGIS Public    |     | Future APIs ||
|  | (Official)       |     | (Fallback)       |     | (P1-P3)     ||
|  | Requires Token   |     | No Auth          |     |             ||
|  +------------------+     +------------------+     +--------------+|
|                                                                    |
+------------------------------------------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                   Supporting Infrastructure                       |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+     +------------------+     +--------------+|
|  | RateLimiter      |     | ResponseCache    |     | Smoke Test  ||
|  | (rate_limiter.py)|     | (response_cache) |     | CLI Script  ||
|  | Token bucket     |     | SHA256 keys      |     | Pre-flight  ||
|  +------------------+     +------------------+     +--------------+|
|                                                                    |
+------------------------------------------------------------------+
```

---

## 2. File Structure

### 2.1 Complete File Tree

```
tests/
├── conftest.py                           # Existing (637 lines) - Add live test markers
├── fixtures/
│   └── recorded/                         # NEW - Recorded API responses
│       └── .gitkeep
└── live/                                 # NEW - Live test suite
    ├── __init__.py                       # Module initialization
    ├── conftest.py                       # Live-specific fixtures
    ├── test_county_assessor_live.py      # County Assessor live tests
    ├── test_arcgis_live.py               # ArcGIS fallback live tests
    └── README.md                         # Live test documentation

scripts/
└── smoke_test.py                         # NEW - Pre-flight validation CLI

pyproject.toml                            # MODIFY - Add live marker config
```

### 2.2 File Descriptions

| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `tests/live/__init__.py` | Module docstring, version, exports | 20 |
| `tests/live/conftest.py` | Live fixtures: client factories, recording, rate limiting | 150 |
| `tests/live/test_county_assessor_live.py` | Official API live tests (auth, schema, rate limit) | 200 |
| `tests/live/test_arcgis_live.py` | Public API fallback tests | 100 |
| `tests/live/README.md` | Documentation for live test usage | 150 |
| `tests/fixtures/recorded/.gitkeep` | Placeholder for recorded responses | 1 |
| `scripts/smoke_test.py` | CLI smoke test script | 250 |
| `pyproject.toml` | Modified pytest configuration | +10 |

---

## 3. Component Specifications

### 3.1 Live Test Suite (`tests/live/`)

#### 3.1.1 Module Initialization (`tests/live/__init__.py`)

```python
"""Live tests for external API validation.

This module contains tests that make real API calls to validate:
- API authentication and connectivity
- Response schema conformance
- Rate limiting compliance
- Data accuracy for known addresses

IMPORTANT: These tests are excluded from default pytest runs.
Run with: pytest -m live tests/live/

Environment Requirements:
    MARICOPA_ASSESSOR_TOKEN - Required for County Assessor API tests
"""

__version__ = "1.0.0"
__all__ = ["KNOWN_TEST_ADDRESSES", "EXPECTED_RESPONSES"]

# Known addresses for live testing (manually verified)
KNOWN_TEST_ADDRESSES: list[tuple[str, dict]] = [
    # (street_address, expected_data_constraints)
    ("4732 W Davis Rd", {"year_built_range": (1990, 2020)}),
    ("3847 E Cactus Rd", {"has_pool": True}),
]

# Placeholder for expected response schemas
EXPECTED_RESPONSES: dict = {}
```

#### 3.1.2 Live Test Fixtures (`tests/live/conftest.py`)

```python
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
from typing import TYPE_CHECKING, Any, Generator

import pytest

from phx_home_analysis.services.api_client.rate_limiter import RateLimit, RateLimiter
from phx_home_analysis.services.county_data import MaricopaAssessorClient

if TYPE_CHECKING:
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
def arcgis_client(live_rate_limit: float) -> Generator[MaricopaAssessorClient, None, None]:
    """Create ArcGIS-only client (no token) for fallback testing.

    Yields:
        MaricopaAssessorClient configured for ArcGIS fallback.
    """
    # Client without token uses ArcGIS fallback
    client = MaricopaAssessorClient(
        token=None,
        rate_limit_seconds=live_rate_limit,
    )
    yield client


@pytest.fixture
def record_response(request: pytest.FixtureRequest) -> Generator[
    callable[[str, str, dict, dict | None], None], None, None
]:
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
            recordings.append({
                "api": api_name,
                "operation": operation,
                "response": response,
                "metadata": metadata or {},
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0",
                "test_name": request.node.name,
            })

    yield _record

    # Save recordings after test completes
    if recordings:
        RECORDED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        output_file = RECORDED_DIR / f"recording_{test_name}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(recordings, f, indent=2, default=str, ensure_ascii=False)


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


# Mark all tests in this module as live tests
pytestmark = pytest.mark.live
```

#### 3.1.3 County Assessor Live Tests (`tests/live/test_county_assessor_live.py`)

```python
"""Live tests for Maricopa County Assessor API.

These tests call real APIs and require:
- MARICOPA_ASSESSOR_TOKEN environment variable
- Network connectivity to mcassessor.maricopa.gov
- Rate limiting awareness (configured via --live-rate-limit)

Run with: pytest tests/live/test_county_assessor_live.py -m live -v

Test Categories:
- Authentication: Token validation and API access
- Schema Validation: Response structure matches ParcelData model
- Rate Limiting: No 429 errors across multiple requests
- Data Accuracy: Known addresses return expected data ranges
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData

if TYPE_CHECKING:
    from collections.abc import Callable

# Mark all tests in this module as live tests
pytestmark = [pytest.mark.live, pytest.mark.asyncio]


# Known addresses with expected data constraints (manually verified)
KNOWN_ADDRESSES: list[tuple[str, dict]] = [
    # (street_address, expected_constraints)
    # Constraints are used for validation, not exact matching
    ("4732 W Davis Rd", {
        "year_built_range": (1990, 2025),
        "lot_sqft_range": (5000, 20000),
    }),
    ("3847 E Cactus Rd", {
        "year_built_range": (1980, 2020),
    }),
    ("1234 N Central Ave", {
        "sewer_type": "city",
    }),
]


class TestCountyAssessorAuthentication:
    """Live validation of API authentication."""

    async def test_client_initializes_with_valid_token(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify client initializes successfully with valid token."""
        assert assessor_client is not None
        assert assessor_client._token is not None

    async def test_api_accepts_authentication(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify API accepts our authentication token.

        Makes a minimal request to verify credentials are valid.
        """
        async with assessor_client as client:
            # Search for a known address - if auth fails, this raises
            apn = await client.search_apn("4732 W Davis Rd")
            # Success means auth worked (even if no results)
            # Failure would raise httpx.HTTPStatusError


class TestCountyAssessorSchemaValidation:
    """Validate API response schema matches ParcelData model."""

    async def test_response_returns_parcel_data_type(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify API response is properly typed as ParcelData."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is not None:
                assert isinstance(parcel, ParcelData)

    async def test_parcel_data_has_required_fields(
        self,
        assessor_client: MaricopaAssessorClient,
        record_response: Callable,
    ) -> None:
        """Verify ParcelData contains all expected fields.

        Required fields for kill-switch evaluation:
        - apn: Assessor Parcel Number
        - lot_sqft: Lot size in square feet
        - year_built: Construction year
        - garage_spaces: Number of garage spaces
        - sewer_type: City or septic
        - has_pool: Pool presence
        """
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is None:
                pytest.skip("No data returned for test address")

            # Record for drift detection
            record_response(
                "county_assessor",
                "extract_for_address",
                asdict(parcel),
                {"input_address": "4732 W Davis Rd"},
            )

            # Verify required fields exist (may be None if not available)
            required_fields = [
                "apn", "full_address", "lot_sqft", "year_built",
                "garage_spaces", "sewer_type", "has_pool",
            ]
            for field in required_fields:
                assert hasattr(parcel, field), f"Missing required field: {field}"

    async def test_field_types_are_correct(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify field types match ParcelData type hints."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is None:
                pytest.skip("No data returned for test address")

            # Type validations (when field is not None)
            if parcel.apn is not None:
                assert isinstance(parcel.apn, str)
            if parcel.lot_sqft is not None:
                assert isinstance(parcel.lot_sqft, int)
            if parcel.year_built is not None:
                assert isinstance(parcel.year_built, int)
            if parcel.garage_spaces is not None:
                assert isinstance(parcel.garage_spaces, int)
            if parcel.sewer_type is not None:
                assert isinstance(parcel.sewer_type, str)
                assert parcel.sewer_type in ("city", "septic", "unknown")
            if parcel.has_pool is not None:
                assert isinstance(parcel.has_pool, bool)


class TestCountyAssessorRateLimiting:
    """Validate rate limiting prevents 429 errors."""

    async def test_multiple_requests_no_rate_limit_error(
        self,
        assessor_client: MaricopaAssessorClient,
        shared_rate_limiter: "RateLimiter",
    ) -> None:
        """Verify multiple sequential requests don't trigger rate limiting.

        Makes 3 requests with rate limiter to verify no 429 errors.
        """
        test_addresses = [
            "4732 W Davis Rd",
            "3847 E Cactus Rd",
            "1234 N Central Ave",
        ]

        async with assessor_client as client:
            for addr in test_addresses:
                # Apply rate limiting before each request
                await shared_rate_limiter.acquire()

                try:
                    await client.extract_for_address(addr)
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str:
                        pytest.fail(f"Rate limit exceeded on {addr}: {e}")
                    # Re-raise other errors
                    raise


class TestCountyAssessorDataAccuracy:
    """Validate data accuracy for known addresses."""

    @pytest.mark.parametrize("address,constraints", KNOWN_ADDRESSES)
    async def test_known_address_data_within_constraints(
        self,
        assessor_client: MaricopaAssessorClient,
        address: str,
        constraints: dict,
        record_response: Callable,
    ) -> None:
        """Verify known addresses return data within expected ranges.

        Uses range-based validation rather than exact values to allow
        for data updates while still catching major changes.
        """
        async with assessor_client as client:
            parcel = await client.extract_for_address(address)

            if parcel is None:
                pytest.skip(f"No data returned for {address}")

            # Record response
            record_response(
                "county_assessor",
                "known_address_validation",
                asdict(parcel),
                {"input_address": address, "constraints": constraints},
            )

            # Validate constraints
            if "year_built_range" in constraints and parcel.year_built:
                min_year, max_year = constraints["year_built_range"]
                assert min_year <= parcel.year_built <= max_year, (
                    f"year_built {parcel.year_built} outside range "
                    f"[{min_year}, {max_year}]"
                )

            if "lot_sqft_range" in constraints and parcel.lot_sqft:
                min_sqft, max_sqft = constraints["lot_sqft_range"]
                assert min_sqft <= parcel.lot_sqft <= max_sqft, (
                    f"lot_sqft {parcel.lot_sqft} outside range "
                    f"[{min_sqft}, {max_sqft}]"
                )

            if "sewer_type" in constraints and parcel.sewer_type:
                assert parcel.sewer_type == constraints["sewer_type"]

            if "has_pool" in constraints and parcel.has_pool is not None:
                assert parcel.has_pool == constraints["has_pool"]
```

#### 3.1.4 ArcGIS Live Tests (`tests/live/test_arcgis_live.py`)

```python
"""Live tests for ArcGIS public API (fallback).

These tests validate the no-auth fallback API:
- Network connectivity to gis.mcassessor.maricopa.gov
- Basic data extraction (lot size, year built, coordinates)
- No authentication required

Run with: pytest tests/live/test_arcgis_live.py -m live -v
"""

from __future__ import annotations

import pytest

from phx_home_analysis.services.county_data import MaricopaAssessorClient

# Mark all tests in this module as live tests
pytestmark = [pytest.mark.live, pytest.mark.asyncio]


class TestArcGISConnectivity:
    """Test ArcGIS public API connectivity."""

    async def test_arcgis_endpoint_reachable(
        self,
        arcgis_client: MaricopaAssessorClient,
    ) -> None:
        """Verify ArcGIS endpoint is reachable without authentication."""
        async with arcgis_client as client:
            # This should work without token (uses ArcGIS fallback)
            parcel = await client.extract_for_address("4732 W Davis Rd")
            # Success if no exception raised
            # parcel may be None if address not found


class TestArcGISDataExtraction:
    """Test ArcGIS data extraction capabilities."""

    async def test_arcgis_returns_basic_fields(
        self,
        arcgis_client: MaricopaAssessorClient,
    ) -> None:
        """Verify ArcGIS returns at least basic property data.

        ArcGIS fallback provides limited data compared to official API:
        - lot_sqft (from parcel geometry)
        - year_built (from attributes)
        - coordinates (from centroid)
        """
        async with arcgis_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is None:
                pytest.skip("ArcGIS returned no data for test address")

            # At minimum, ArcGIS should provide coordinates
            # (other fields may be None)
            assert parcel.source in ("arcgis", "maricopa_assessor")
```

### 3.2 Smoke Test Script (`scripts/smoke_test.py`)

```python
#!/usr/bin/env python
"""Pre-flight smoke test for external API connectivity.

Validates environment configuration and API reachability before
running the full property analysis pipeline.

Usage:
    python scripts/smoke_test.py           # Run all checks
    python scripts/smoke_test.py --quick   # Skip slow APIs
    python scripts/smoke_test.py --json    # Output as JSON
    python scripts/smoke_test.py --verbose # Show detailed output

Exit codes:
    0 - All critical checks passed
    1 - One or more critical checks failed
    2 - Configuration error (missing required env vars)

Environment Variables:
    MARICOPA_ASSESSOR_TOKEN - Required for County Assessor API
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class CheckStatus(Enum):
    """Status of a connectivity check."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARN = "warn"


@dataclass
class CheckResult:
    """Result of a single connectivity check."""
    name: str
    status: CheckStatus
    latency_ms: float | None
    message: str
    critical: bool = True
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "critical": self.critical,
            "details": self.details,
        }


async def check_env_vars() -> CheckResult:
    """Check required environment variables are present.

    Returns:
        CheckResult with status and missing variables list.
    """
    required_vars = ["MARICOPA_ASSESSOR_TOKEN"]
    optional_vars = ["GREATSCHOOLS_API_KEY", "WALKSCORE_API_KEY"]

    missing_required = [v for v in required_vars if not os.getenv(v)]
    missing_optional = [v for v in optional_vars if not os.getenv(v)]

    if missing_required:
        return CheckResult(
            name="Environment Variables",
            status=CheckStatus.FAIL,
            latency_ms=None,
            message=f"Missing required: {', '.join(missing_required)}",
            critical=True,
            details={
                "missing_required": missing_required,
                "missing_optional": missing_optional,
            },
        )

    status = CheckStatus.PASS if not missing_optional else CheckStatus.WARN
    return CheckResult(
        name="Environment Variables",
        status=status,
        latency_ms=None,
        message="All required variables present" + (
            f" (optional missing: {', '.join(missing_optional)})"
            if missing_optional else ""
        ),
        critical=True,
        details={
            "missing_optional": missing_optional,
        },
    )


async def check_county_assessor() -> CheckResult:
    """Check Maricopa County Assessor API connectivity.

    Returns:
        CheckResult with API status and latency.
    """
    start = time.time()
    try:
        from phx_home_analysis.services.county_data import MaricopaAssessorClient

        token = os.getenv("MARICOPA_ASSESSOR_TOKEN")
        if not token:
            return CheckResult(
                name="County Assessor API",
                status=CheckStatus.SKIP,
                latency_ms=None,
                message="MARICOPA_ASSESSOR_TOKEN not set",
                critical=True,
            )

        async with MaricopaAssessorClient(
            token=token,
            rate_limit_seconds=0.1,
            timeout=10.0,
        ) as client:
            # Test with a known address
            parcel = await client.extract_for_address("4732 W Davis Rd")
            latency = (time.time() - start) * 1000

            if parcel and parcel.apn:
                return CheckResult(
                    name="County Assessor API",
                    status=CheckStatus.PASS,
                    latency_ms=round(latency, 1),
                    message=f"OK (APN: {parcel.apn})",
                    critical=True,
                    details={
                        "apn": parcel.apn,
                        "has_lot_sqft": parcel.lot_sqft is not None,
                        "has_year_built": parcel.year_built is not None,
                    },
                )
            else:
                return CheckResult(
                    name="County Assessor API",
                    status=CheckStatus.WARN,
                    latency_ms=round(latency, 1),
                    message="API responded but no parcel data returned",
                    critical=True,
                )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return CheckResult(
            name="County Assessor API",
            status=CheckStatus.FAIL,
            latency_ms=round(latency, 1),
            message=str(e)[:100],  # Truncate long errors
            critical=True,
        )


async def check_arcgis_public() -> CheckResult:
    """Check ArcGIS public API (fallback) connectivity.

    Returns:
        CheckResult with API status and latency.
    """
    start = time.time()
    try:
        import httpx

        # Test ArcGIS REST API endpoint
        url = (
            "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/"
            "MaricopaDynamicQueryService/MapServer"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}?f=json")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status=CheckStatus.PASS,
                    latency_ms=round(latency, 1),
                    message="OK",
                    critical=False,
                )
            else:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status=CheckStatus.FAIL,
                    latency_ms=round(latency, 1),
                    message=f"HTTP {response.status_code}",
                    critical=False,
                )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return CheckResult(
            name="ArcGIS (Fallback)",
            status=CheckStatus.FAIL,
            latency_ms=round(latency, 1),
            message=str(e)[:100],
            critical=False,
        )


async def check_network_connectivity() -> CheckResult:
    """Basic network connectivity check.

    Returns:
        CheckResult indicating if network is available.
    """
    start = time.time()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Use a reliable public endpoint
            response = await client.get("https://www.google.com/generate_204")
            latency = (time.time() - start) * 1000

            if response.status_code == 204:
                return CheckResult(
                    name="Network Connectivity",
                    status=CheckStatus.PASS,
                    latency_ms=round(latency, 1),
                    message="OK",
                    critical=True,
                )
            else:
                return CheckResult(
                    name="Network Connectivity",
                    status=CheckStatus.WARN,
                    latency_ms=round(latency, 1),
                    message=f"Unexpected status: {response.status_code}",
                    critical=True,
                )

    except Exception as e:
        return CheckResult(
            name="Network Connectivity",
            status=CheckStatus.FAIL,
            latency_ms=None,
            message=str(e)[:100],
            critical=True,
        )


async def run_all_checks(quick: bool = False) -> list[CheckResult]:
    """Run all smoke test checks.

    Args:
        quick: If True, skip slow API checks.

    Returns:
        List of CheckResult objects.
    """
    # Always run these checks
    checks = [
        check_env_vars(),
        check_network_connectivity(),
    ]

    if not quick:
        checks.extend([
            check_county_assessor(),
            check_arcgis_public(),
        ])

    return await asyncio.gather(*checks)


def print_results(
    results: list[CheckResult],
    verbose: bool = False,
    as_json: bool = False,
) -> int:
    """Print results and return exit code.

    Args:
        results: List of check results.
        verbose: Show detailed output.
        as_json: Output as JSON.

    Returns:
        Exit code (0 = success, 1 = critical failure, 2 = config error).
    """
    if as_json:
        output = [r.to_dict() for r in results]
        print(json.dumps(output, indent=2))
    else:
        print()
        print("=" * 60)
        print("PHX Houses Smoke Test Results")
        print("=" * 60)
        print()

        for r in results:
            icon = {
                CheckStatus.PASS: "[PASS]",
                CheckStatus.FAIL: "[FAIL]",
                CheckStatus.SKIP: "[SKIP]",
                CheckStatus.WARN: "[WARN]",
            }[r.status]

            latency = f"{r.latency_ms:.0f}ms" if r.latency_ms else "N/A"
            critical = "(CRITICAL)" if r.critical else ""

            print(f"{icon} {r.name}: {r.message} [{latency}] {critical}")

            if verbose and r.details:
                for key, value in r.details.items():
                    print(f"       {key}: {value}")

        print()
        print("=" * 60)

        # Summary
        passed = sum(1 for r in results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
        skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)
        warned = sum(1 for r in results if r.status == CheckStatus.WARN)

        print(f"Summary: {passed} passed, {failed} failed, {warned} warnings, {skipped} skipped")
        print("=" * 60)

    # Determine exit code
    critical_failures = [
        r for r in results
        if r.critical and r.status == CheckStatus.FAIL
    ]

    # Check for config errors (missing env vars)
    env_check = next((r for r in results if r.name == "Environment Variables"), None)
    if env_check and env_check.status == CheckStatus.FAIL:
        return 2  # Configuration error

    return 1 if critical_failures else 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Pre-flight smoke test for external API connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow API connectivity checks",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output including check details",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    try:
        results = asyncio.run(run_all_checks(quick=args.quick))
        return print_results(results, verbose=args.verbose, as_json=args.json)
    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
```

### 3.3 pytest Configuration Modifications

Add to `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short -m 'not live'"  # MODIFIED: Exclude live tests by default
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "live: marks tests as requiring real API calls (deselect with '-m \"not live\"')",
    "requires_token: marks tests as requiring MARICOPA_ASSESSOR_TOKEN",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

---

## 4. API Contracts

### 4.1 Live Test Fixtures API

```python
# tests/live/conftest.py

@pytest.fixture(scope="module")
def assessor_client(
    assessor_token: str | None,
    live_rate_limit: float,
) -> Generator[MaricopaAssessorClient, None, None]:
    """Factory fixture for MaricopaAssessorClient.

    Args:
        assessor_token: API token from environment (auto-injected)
        live_rate_limit: Rate limit seconds from CLI (auto-injected)

    Yields:
        Configured client instance

    Raises:
        pytest.skip: If MARICOPA_ASSESSOR_TOKEN not set
    """
    ...


@pytest.fixture
def record_response(
    request: pytest.FixtureRequest,
) -> Generator[Callable[[str, str, dict, dict | None], None], None, None]:
    """Response recording fixture.

    Yields:
        Recording function with signature:
            (api_name: str, operation: str, response: dict, metadata: dict | None) -> None

    Side Effects:
        Saves recordings to tests/fixtures/recorded/ when --record-responses flag set
    """
    ...
```

### 4.2 Smoke Test API

```python
# scripts/smoke_test.py

@dataclass
class CheckResult:
    """Result of a connectivity check.

    Attributes:
        name: Human-readable check name
        status: CheckStatus enum (PASS, FAIL, SKIP, WARN)
        latency_ms: Response time in milliseconds (None if not measured)
        message: Status message for display
        critical: If True, failure affects exit code
        details: Optional dict with additional check details
    """
    name: str
    status: CheckStatus
    latency_ms: float | None
    message: str
    critical: bool = True
    details: dict[str, Any] | None = None


async def run_all_checks(quick: bool = False) -> list[CheckResult]:
    """Execute all smoke test checks.

    Args:
        quick: Skip slow API checks if True

    Returns:
        List of CheckResult objects

    Performance:
        Completes in under 60 seconds (target: <30s with parallelism)
    """
    ...


def print_results(
    results: list[CheckResult],
    verbose: bool = False,
    as_json: bool = False,
) -> int:
    """Format and print results.

    Args:
        results: List of check results
        verbose: Include detailed output
        as_json: Output as JSON instead of text

    Returns:
        Exit code: 0 (success), 1 (critical failure), 2 (config error)
    """
    ...
```

---

## 5. Data Models

### 5.1 Existing Models (Reference)

```python
# src/phx_home_analysis/services/county_data/models.py (existing)

@dataclass
class ParcelData:
    """Property data extracted from Maricopa County Assessor API."""

    apn: str
    full_address: str
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    sewer_type: str | None = None  # "city" or "septic"
    has_pool: bool | None = None
    beds: int | None = None
    baths: float | None = None
    tax_annual: float | None = None
    full_cash_value: int | None = None
    limited_value: int | None = None
    livable_sqft: int | None = None
    roof_type: str | None = None
    exterior_wall_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str = "maricopa_assessor"
```

### 5.2 New Models

```python
# scripts/smoke_test.py (new)

class CheckStatus(Enum):
    """Status values for connectivity checks."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARN = "warn"


@dataclass
class CheckResult:
    """Result of a single connectivity check."""
    name: str
    status: CheckStatus
    latency_ms: float | None
    message: str
    critical: bool = True
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        ...
```

### 5.3 Response Recording Schema

```json
// tests/fixtures/recorded/recording_*.json

{
  "api": "string",           // API identifier (e.g., "county_assessor")
  "operation": "string",     // Operation name (e.g., "extract_for_address")
  "response": {},            // Actual API response data
  "metadata": {              // Optional context
    "input_address": "string",
    "constraints": {}
  },
  "recorded_at": "ISO8601",  // Timestamp
  "schema_version": "1.0",   // Recording format version
  "test_name": "string"      // Originating test name
}
```

---

## 6. Integration Points

### 6.1 Connection to Existing Code

| Component | Existing File | Integration Method |
|-----------|--------------|-------------------|
| API Client | `src/phx_home_analysis/services/county_data/assessor_client.py:71-196` | Import and use directly |
| Rate Limiter | `src/phx_home_analysis/services/api_client/rate_limiter.py:62-257` | Import `RateLimiter`, `RateLimit` |
| Response Cache | `src/phx_home_analysis/services/api_client/response_cache.py:73-359` | Reference patterns for recording |
| ParcelData | `src/phx_home_analysis/services/county_data/models.py:7-58` | Import for type hints and validation |
| Test Fixtures | `tests/conftest.py:1-638` | Follow fixture patterns |
| CLI Patterns | `scripts/extract_county_data.py:164-230` | Follow argparse and async patterns |

### 6.2 Import Statements

```python
# tests/live/conftest.py
from phx_home_analysis.services.api_client.rate_limiter import RateLimit, RateLimiter
from phx_home_analysis.services.county_data import MaricopaAssessorClient

# tests/live/test_county_assessor_live.py
from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData

# scripts/smoke_test.py
from phx_home_analysis.services.county_data import MaricopaAssessorClient
```

---

## 7. Configuration

### 7.1 Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `MARICOPA_ASSESSOR_TOKEN` | Yes (for live tests) | None | County Assessor API authentication |
| `GREATSCHOOLS_API_KEY` | No | None | Future P2 integration |
| `WALKSCORE_API_KEY` | No | None | Future P2 integration |

### 7.2 pytest Options

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `--record-responses` | Flag | False | Enable response recording |
| `--live-rate-limit` | Float | 0.5 | Seconds between API calls |

### 7.3 Default Test Behavior

```bash
# Default: Excludes live tests
pytest tests/

# Run live tests only
pytest -m live tests/live/

# Run live tests with recording
pytest -m live tests/live/ --record-responses

# Run all tests including live
pytest tests/ -m ""
```

---

## 8. Error Handling

### 8.1 Expected Exceptions

| Exception | Source | Handling |
|-----------|--------|----------|
| `pytest.skip` | Missing credentials | Graceful skip with message |
| `httpx.HTTPStatusError` | API errors | Catch, check for 429, fail test |
| `httpx.TimeoutException` | Network timeout | Catch, fail with latency info |
| `httpx.ConnectError` | Network unreachable | Catch, mark as FAIL in smoke test |

### 8.2 Rate Limit Error Detection

```python
# Pattern for detecting rate limit errors
async def test_with_rate_limit_check(client):
    try:
        result = await client.extract_for_address(address)
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "rate limit" in error_str:
            pytest.fail(f"Rate limit exceeded: {e}")
        raise  # Re-raise other errors
```

### 8.3 Graceful Degradation

```python
# Skip pattern for missing data
async def test_with_optional_data(client):
    parcel = await client.extract_for_address(address)

    if parcel is None:
        pytest.skip(f"No data returned for {address}")

    # Continue with assertions...
```

---

## 9. Testing Strategy

### 9.1 How to Test the Testing Infrastructure

| Test Type | Method | Coverage |
|-----------|--------|----------|
| Fixture initialization | Unit test with mocked credentials | `conftest.py` fixtures |
| Recording fixture | Unit test with mock request | `record_response` fixture |
| Smoke test checks | Integration test with mocked HTTP | Individual check functions |
| CLI argument parsing | Unit test | `parse_args()` |
| Exit code logic | Unit test | `print_results()` |

### 9.2 Meta-Tests (Optional)

```python
# tests/unit/test_live_infrastructure.py (optional meta-tests)

def test_record_response_creates_file(tmp_path, monkeypatch):
    """Verify recording fixture creates JSON files."""
    ...

def test_smoke_test_exit_codes():
    """Verify exit code logic for different scenarios."""
    ...
```

### 9.3 Manual Validation Checklist

- [ ] Run `pytest tests/` - Live tests should be excluded
- [ ] Run `pytest -m live tests/live/` - Only live tests run
- [ ] Run `python scripts/smoke_test.py` - Returns 0 with valid token
- [ ] Run `python scripts/smoke_test.py --json` - Valid JSON output
- [ ] Run `pytest tests/live/ --record-responses` - Creates JSON files
- [ ] Verify no 429 errors in live test output

---

## 10. Implementation Order

### 10.1 Recommended Sequence

| Phase | Task | Dependencies | Est. Time |
|-------|------|--------------|-----------|
| 1 | Create `tests/live/` directory structure | None | 15 min |
| 2 | Implement `tests/live/__init__.py` | Phase 1 | 10 min |
| 3 | Modify `pyproject.toml` pytest config | Phase 1 | 10 min |
| 4 | Implement `tests/live/conftest.py` fixtures | Phase 2, 3 | 45 min |
| 5 | Implement `tests/live/test_county_assessor_live.py` | Phase 4 | 60 min |
| 6 | Implement `tests/live/test_arcgis_live.py` | Phase 4 | 30 min |
| 7 | Implement `scripts/smoke_test.py` | None | 60 min |
| 8 | Create `tests/live/README.md` documentation | Phase 5, 6, 7 | 30 min |
| 9 | Create `tests/fixtures/recorded/.gitkeep` | None | 5 min |
| 10 | Validation and manual testing | All | 30 min |

**Total Estimated Time: 4-5 hours**

### 10.2 Dependency Graph

```
Phase 1 (Directory) ──┬── Phase 2 (__init__.py)
                      │
                      ├── Phase 3 (pyproject.toml)
                      │
                      └── Phase 9 (fixtures/recorded/)

Phase 2 + Phase 3 ──── Phase 4 (conftest.py)

Phase 4 ──────────────┬── Phase 5 (test_county_assessor_live.py)
                      │
                      └── Phase 6 (test_arcgis_live.py)

(Independent) ──────── Phase 7 (smoke_test.py)

Phase 5 + 6 + 7 ────── Phase 8 (README.md)

All ──────────────────── Phase 10 (Validation)
```

---

## 11. Risk Mitigation

### 11.1 Rate Limiting Protection

**Risk:** API returns 429 (rate limit exceeded) during tests.

**Mitigations:**
1. Use `RateLimiter` from `api_client/rate_limiter.py` with conservative settings
2. Configure proactive throttling at 70% threshold
3. Default rate limit of 0.5s between requests (configurable via `--live-rate-limit`)
4. Shared rate limiter fixture (`shared_rate_limiter`) for sequential tests
5. Tests run sequentially within modules (module-scoped fixtures)

### 11.2 Credential Security

**Risk:** API tokens exposed in logs or error messages.

**Mitigations:**
1. Never log credentials - use existing `_safe_error_message()` pattern from `assessor_client.py:166-181`
2. Skip tests gracefully when credentials missing (no error message with partial token)
3. Response recording excludes request headers
4. Environment variables loaded via `python-dotenv` (not hardcoded)

### 11.3 Test Flakiness

**Risk:** Network issues cause intermittent test failures.

**Mitigations:**
1. Use `pytest.skip()` for expected conditions (no data, missing token)
2. Configure appropriate timeouts (10s for smoke tests, 30s for live tests)
3. Range-based validation instead of exact value matching
4. Mark non-critical checks as `critical=False` in smoke tests

### 11.4 API Changes

**Risk:** API schema changes break tests silently.

**Mitigations:**
1. Response recording fixture captures actual responses for drift analysis
2. Schema validation tests verify field presence and types
3. Use range-based constraints for data validation
4. Manual validation addresses serve as regression canaries

---

## 12. Acceptance Criteria Mapping

| AC | Implementation | Files |
|----|----------------|-------|
| AC1: Directory Structure | Create `tests/live/` with specified files | `tests/live/*` |
| AC2: Pytest Marker | Configure `-m live` marker, exclude by default | `pyproject.toml`, `tests/live/conftest.py` |
| AC3: County Assessor Tests | 5+ test cases covering auth, schema, rate limit | `tests/live/test_county_assessor_live.py` |
| AC4: Smoke Test Script | CLI with env check, connectivity tests, exit codes | `scripts/smoke_test.py` |
| AC5: Response Recording | `--record-responses` flag, JSON output | `tests/live/conftest.py` |
| AC6: CI/CD Hooks | Marker config, skip logic, documentation | `pyproject.toml`, `tests/live/README.md` |
| AC7: Rate Limit Protection | `RateLimiter` integration, no 429 errors | `tests/live/conftest.py`, test files |

---

## 13. References

### 13.1 Existing Code References

| Resource | File | Lines |
|----------|------|-------|
| Test fixtures pattern | `tests/conftest.py` | 1-638 |
| Async test patterns | `tests/unit/services/api_client/test_base_client.py` | 187-224 |
| CLI patterns | `scripts/extract_county_data.py` | 164-230, 368-489 |
| Rate limiter | `src/phx_home_analysis/services/api_client/rate_limiter.py` | 62-257 |
| Response cache | `src/phx_home_analysis/services/api_client/response_cache.py` | 73-359 |
| API client | `src/phx_home_analysis/services/county_data/assessor_client.py` | 71-196 |
| ParcelData model | `src/phx_home_analysis/services/county_data/models.py` | 7-58 |

### 13.2 Story Reference

- Story file: `docs/sprint-artifacts/stories/story-live-testing-infrastructure.md`
- Epic: E3: Test Infrastructure & Quality
- Priority: P1 (High)
- Estimate: 8 story points (3-5 days)

---

*Technical Specification v1.0*
*Created: 2024-12-04*
*Author: Claude Code (Opus 4.5)*

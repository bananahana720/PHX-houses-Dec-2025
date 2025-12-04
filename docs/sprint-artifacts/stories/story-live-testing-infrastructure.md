# Story: Live Testing Infrastructure

## Story Header

| Field | Value |
|-------|-------|
| **Title** | Live Testing Infrastructure for External API Validation |
| **Epic** | E3: Test Infrastructure & Quality |
| **Priority** | P1 (High) |
| **Estimate** | 8 story points (3-5 days) |
| **Status** | Draft |
| **Created** | 2024-12-04 |
| **Dependencies** | E2.S7 (API Client Infrastructure) - Completed |

---

## User Story

**As a** developer maintaining the PHX Houses property analysis pipeline,

**I want** a live testing infrastructure that validates external API integrations against real endpoints,

**So that** I can detect mock drift, reduce manual alpha/beta testing effort, and maintain confidence that mocked tests accurately reflect production API behavior.

---

## Background / Context

### Current State Analysis

The PHX Houses test suite has evolved to 65 test files with approximately 25,000 lines of test code and 1,063+ test cases. However, a critical gap exists:

**Mock Coverage Statistics:**
- 43.8% of test infrastructure relies on mocking
- **100% of external API calls are mocked** (no live validation exists)
- Mocked APIs include:
  - Maricopa County Assessor API (official + ArcGIS fallback)
  - Zillow/Redfin listing data extraction
  - FEMA flood zone API
  - GreatSchools rating API
  - WalkScore API
  - Google Maps/Geocoding APIs

**Pain Points:**
1. **Mock Drift Risk**: Mocked responses may no longer match actual API responses as APIs evolve
2. **False Confidence**: All 1,063 tests passing does not guarantee production readiness
3. **Manual Testing Burden**: Each deployment requires manual verification of external integrations
4. **Regression Blindness**: API contract changes are not detected until production failures occur
5. **No Smoke Tests**: No quick pre-flight validation before running full pipeline

### Desired State

A tiered testing strategy with:
1. **Unit tests (existing)**: Fast, isolated, mocked - run on every commit
2. **Live tests (new)**: Real API calls - run on demand or nightly
3. **Smoke tests (new)**: Quick validation script - run before pipeline execution

---

## Acceptance Criteria

### AC1: Live Test Directory Structure
**Given** the existing test suite in `tests/`
**When** live testing infrastructure is implemented
**Then** a new `tests/live/` directory exists with:
- `__init__.py` with module documentation
- `conftest.py` with live-specific fixtures (API clients, credentials, rate limiting)
- `test_county_assessor_live.py` for Maricopa County API validation
- `test_external_apis_live.py` for other external APIs
- `README.md` documenting usage and requirements

### AC2: Pytest Marker for Live Tests
**Given** live tests exist in `tests/live/`
**When** running `pytest tests/`
**Then** live tests are excluded by default (via `pytest.ini` marker configuration)
**And** live tests can be explicitly included with `pytest -m live`
**And** live tests can be run in isolation with `pytest tests/live/`

### AC3: County Assessor Live Test Coverage
**Given** the Maricopa County Assessor API client (`MaricopaAssessorClient`)
**When** live tests execute against the real API
**Then** the following validations occur:
- Authentication succeeds with `MARICOPA_ASSESSOR_TOKEN`
- Response schema matches `ParcelData` model fields
- Rate limiting is respected (no 429 errors)
- At least 3 known addresses return valid parcel data
- ArcGIS fallback API returns data for sample coordinates

### AC4: Smoke Test Script
**Given** a developer wants to verify API connectivity before pipeline execution
**When** running `python scripts/smoke_test.py`
**Then** the script:
- Validates all required environment variables are present
- Tests connectivity to each external API (timeout: 10s each)
- Reports pass/fail status for each API with latency metrics
- Returns exit code 0 if all critical APIs pass, 1 otherwise
- Completes in under 60 seconds total

### AC5: Response Recording Fixture
**Given** live tests that call real APIs
**When** the `--record-responses` flag is passed to pytest
**Then** actual API responses are saved to `tests/fixtures/recorded/`
**And** recorded responses include timestamp and schema version
**And** existing mocks can be compared against recorded responses for drift detection

### AC6: CI/CD Integration Hooks
**Given** the live testing infrastructure
**When** integrated into CI/CD (future)
**Then** the following configuration exists:
- `pytest.ini` marker configuration for `@pytest.mark.live`
- Skip logic for CI runs without API credentials
- Documentation for manual trigger of live test runs
- Warning annotations when live tests are skipped

### AC7: Rate Limit Protection
**Given** live tests that call rate-limited APIs
**When** multiple live tests execute sequentially
**Then** the `RateLimiter` from `api_client/rate_limiter.py` is used
**And** no API returns 429 (rate limit exceeded) responses
**And** tests include appropriate delays between API calls

---

## Test Matrix

| API | Current State | Live Test Priority | Mock File | Notes |
|-----|--------------|-------------------|-----------|-------|
| Maricopa County Assessor (Official) | 100% mocked | **P0 (Critical)** | `test_county_pipeline.py` | Requires `MARICOPA_ASSESSOR_TOKEN` |
| Maricopa ArcGIS (Public) | 100% mocked | **P0 (Critical)** | `test_county_pipeline.py` | No auth required, fallback API |
| FEMA Flood Zone | 100% mocked | P1 (High) | N/A | Free public API |
| GreatSchools | 100% mocked | P2 (Medium) | N/A | Daily rate limit |
| WalkScore | 100% mocked | P2 (Medium) | N/A | API key required |
| Google Geocoding | 100% mocked | P2 (Medium) | N/A | Pay-per-use API |
| Zillow/Redfin Extraction | 100% mocked | P3 (Low - Special) | `test_zillow_extractor_validation.py` | Requires stealth browser, complex setup |

**Phase 1 Scope (This Story):** P0 (County Assessor) + Smoke Test
**Phase 2 Scope (Future):** P1-P2 APIs
**Phase 3 Scope (Future):** P3 (Stealth browser tests, integration environment)

---

## Technical Notes

### Test Pattern: Live Test Structure

```python
# tests/live/test_county_assessor_live.py
"""Live tests for Maricopa County Assessor API.

These tests call real APIs and require:
- MARICOPA_ASSESSOR_TOKEN environment variable
- Network connectivity to mcassessor.maricopa.gov
- Rate limiting awareness (max 2 requests/second)

Run with: pytest tests/live/ -m live -v
"""

import os
import pytest
from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData


# Mark all tests in this module as live tests
pytestmark = pytest.mark.live


@pytest.fixture
def assessor_client():
    """Create real API client for live testing."""
    # Skip if credentials not available
    if not os.getenv("MARICOPA_ASSESSOR_TOKEN"):
        pytest.skip("MARICOPA_ASSESSOR_TOKEN not set")

    return MaricopaAssessorClient(rate_limit_seconds=0.5)


class TestCountyAssessorLive:
    """Live validation of County Assessor API."""

    # Known addresses with expected data (manually verified)
    KNOWN_ADDRESSES = [
        ("4732 W Davis Rd", {"year_built_min": 1990, "year_built_max": 2020}),
        ("3847 E Cactus Rd", {"has_pool": True}),
        ("1234 N Central Ave", {"sewer_type": "city"}),
    ]

    @pytest.mark.asyncio
    async def test_authentication_succeeds(self, assessor_client):
        """Verify API authentication with real token."""
        async with assessor_client as client:
            # Simple health check - should not raise
            stats = client.get_rate_limit_stats()
            assert "requests_today" in stats

    @pytest.mark.asyncio
    async def test_known_address_returns_valid_data(self, assessor_client):
        """Verify known address returns expected parcel data."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            # Schema validation
            assert isinstance(parcel, ParcelData)
            assert parcel.apn is not None
            assert parcel.lot_sqft is None or parcel.lot_sqft > 0
            assert parcel.year_built is None or 1900 < parcel.year_built < 2025

    @pytest.mark.asyncio
    async def test_response_schema_matches_model(self, assessor_client):
        """Verify API response fields match ParcelData model."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            # Verify all expected fields are present
            expected_fields = [
                "apn", "lot_sqft", "year_built", "garage_spaces",
                "sewer_type", "has_pool", "tax_annual"
            ]
            for field in expected_fields:
                assert hasattr(parcel, field), f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_rate_limiting_respected(self, assessor_client):
        """Verify rate limiting prevents 429 errors."""
        async with assessor_client as client:
            # Make several requests in quick succession
            addresses = ["4732 W Davis Rd", "3847 E Cactus Rd", "1234 N Central Ave"]

            for addr in addresses:
                try:
                    await client.extract_for_address(addr)
                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        pytest.fail(f"Rate limit exceeded: {e}")
                    raise
```

### Smoke Test Script Pattern

```python
# scripts/smoke_test.py
"""Pre-flight smoke test for external API connectivity.

Validates environment configuration and API reachability before
running the full property analysis pipeline.

Usage:
    python scripts/smoke_test.py           # Run all checks
    python scripts/smoke_test.py --quick   # Skip slow APIs
    python scripts/smoke_test.py --json    # Output as JSON

Exit codes:
    0 - All critical checks passed
    1 - One or more critical checks failed
    2 - Configuration error (missing env vars)
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class CheckResult:
    """Result of a single connectivity check."""
    name: str
    status: str  # "pass", "fail", "skip"
    latency_ms: float | None
    message: str
    critical: bool = True


async def check_county_assessor() -> CheckResult:
    """Check Maricopa County Assessor API connectivity."""
    start = time.time()
    try:
        from phx_home_analysis.services.county_data import MaricopaAssessorClient

        if not os.getenv("MARICOPA_ASSESSOR_TOKEN"):
            return CheckResult(
                name="County Assessor",
                status="skip",
                latency_ms=None,
                message="MARICOPA_ASSESSOR_TOKEN not set",
                critical=True
            )

        async with MaricopaAssessorClient(rate_limit_seconds=0.1) as client:
            # Test with a known address
            parcel = await client.extract_for_address("4732 W Davis Rd")
            latency = (time.time() - start) * 1000

            if parcel and parcel.apn:
                return CheckResult(
                    name="County Assessor",
                    status="pass",
                    latency_ms=latency,
                    message=f"OK (APN: {parcel.apn})"
                )
            else:
                return CheckResult(
                    name="County Assessor",
                    status="fail",
                    latency_ms=latency,
                    message="No parcel data returned"
                )
    except Exception as e:
        return CheckResult(
            name="County Assessor",
            status="fail",
            latency_ms=(time.time() - start) * 1000,
            message=str(e)
        )


async def check_arcgis_public() -> CheckResult:
    """Check ArcGIS public API (fallback) connectivity."""
    start = time.time()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test ArcGIS geocoding endpoint
            url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"
            response = await client.get(f"{url}?f=json")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status="pass",
                    latency_ms=latency,
                    message="OK",
                    critical=False
                )
            else:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status="fail",
                    latency_ms=latency,
                    message=f"HTTP {response.status_code}",
                    critical=False
                )
    except Exception as e:
        return CheckResult(
            name="ArcGIS (Fallback)",
            status="fail",
            latency_ms=(time.time() - start) * 1000,
            message=str(e),
            critical=False
        )


async def run_all_checks() -> list[CheckResult]:
    """Run all smoke test checks."""
    checks = [
        check_county_assessor(),
        check_arcgis_public(),
        # Add more checks as APIs are added to live tests
    ]
    return await asyncio.gather(*checks)


def print_results(results: list[CheckResult], as_json: bool = False) -> int:
    """Print results and return exit code."""
    if as_json:
        output = [
            {
                "name": r.name,
                "status": r.status,
                "latency_ms": r.latency_ms,
                "message": r.message,
                "critical": r.critical
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "=" * 60)
        print("PHX Houses Smoke Test Results")
        print("=" * 60 + "\n")

        for r in results:
            icon = {"pass": "[OK]", "fail": "[FAIL]", "skip": "[SKIP]"}[r.status]
            latency = f"{r.latency_ms:.0f}ms" if r.latency_ms else "N/A"
            critical = "(CRITICAL)" if r.critical else ""
            print(f"{icon} {r.name}: {r.message} [{latency}] {critical}")

        print("\n" + "=" * 60)

    # Exit code: fail if any critical check failed
    critical_failures = [r for r in results if r.critical and r.status == "fail"]
    return 1 if critical_failures else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pre-flight API smoke tests")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quick", action="store_true", help="Skip slow checks")
    args = parser.parse_args()

    results = asyncio.run(run_all_checks())
    sys.exit(print_results(results, as_json=args.json))
```

### Response Recording Pattern

```python
# tests/live/conftest.py
"""Live test fixtures with response recording support."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest


RECORDED_DIR = Path(__file__).parent.parent / "fixtures" / "recorded"


@pytest.fixture
def record_response(request):
    """Fixture to record API responses for mock drift detection.

    Usage in test:
        def test_example(record_response):
            response = await api_call()
            record_response("county_assessor", "parcel_lookup", response)
    """
    recordings = []

    def _record(api_name: str, operation: str, response: dict):
        if request.config.getoption("--record-responses", default=False):
            recordings.append({
                "api": api_name,
                "operation": operation,
                "response": response,
                "recorded_at": datetime.utcnow().isoformat(),
                "schema_version": "1.0"
            })

    yield _record

    # Save recordings after test completes
    if recordings:
        RECORDED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = RECORDED_DIR / f"recording_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(recordings, f, indent=2, default=str)


def pytest_addoption(parser):
    """Add --record-responses option to pytest."""
    parser.addoption(
        "--record-responses",
        action="store_true",
        default=False,
        help="Record live API responses to tests/fixtures/recorded/"
    )
```

### pytest.ini Configuration

```ini
# pytest.ini additions
[pytest]
markers =
    live: marks tests as requiring real API calls (deselect with '-m "not live"')
    slow: marks tests as slow (deselect with '-m "not slow"')

# Default: exclude live tests from normal runs
addopts = -m "not live"
```

### Environment Requirements

```bash
# Required environment variables for live tests
MARICOPA_ASSESSOR_TOKEN=<token>  # Required for County Assessor live tests

# Optional (for future P1-P2 APIs)
GREATSCHOOLS_API_KEY=<key>
WALKSCORE_API_KEY=<key>
GOOGLE_MAPS_API_KEY=<key>
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API Rate Limiting** | High | Medium | Use `RateLimiter` class, add delays between tests, run live tests in sequence not parallel |
| **API Credential Exposure** | Low | High | Never log credentials, use pytest skip when creds missing, document secure handling |
| **Flaky Tests from Network Issues** | Medium | Medium | Implement retry logic, set appropriate timeouts, mark as `xfail` on transient errors |
| **API Changes Break Live Tests** | Medium | Low | Record responses for drift detection, design tests to validate schema not exact values |
| **Cost Accumulation (Paid APIs)** | Low | Medium | Start with free APIs (County, ArcGIS), defer paid API tests to Phase 2 with budget controls |

---

## Definition of Done

### Code Deliverables
- [ ] `tests/live/` directory created with proper structure
- [ ] `tests/live/__init__.py` with module documentation
- [ ] `tests/live/conftest.py` with live-specific fixtures
- [ ] `tests/live/test_county_assessor_live.py` with 5+ test cases
- [ ] `tests/live/README.md` documenting usage
- [ ] `scripts/smoke_test.py` with CLI interface
- [ ] `pytest.ini` updated with `live` marker configuration

### Test Coverage
- [ ] All AC1-AC7 acceptance criteria have corresponding tests
- [ ] Live tests pass when run with valid credentials
- [ ] Live tests skip gracefully when credentials missing
- [ ] Smoke test completes in under 60 seconds

### Documentation
- [ ] `tests/live/README.md` includes:
  - Purpose and scope
  - Environment setup requirements
  - How to run live tests
  - How to add new live tests
  - Response recording instructions
- [ ] `scripts/smoke_test.py` includes comprehensive docstring
- [ ] CLAUDE.md files updated for new directories

### Quality Gates
- [ ] `ruff check tests/live/` passes with no errors
- [ ] `ruff format --check tests/live/` passes
- [ ] `mypy tests/live/` passes (if type hints present)
- [ ] No credentials or secrets in committed code
- [ ] Rate limiting verified (no 429 errors in CI logs)

### Integration
- [ ] `pytest tests/` runs without executing live tests (marker exclusion works)
- [ ] `pytest -m live` runs only live tests
- [ ] `pytest tests/live/` runs all live tests
- [ ] Smoke test exit codes verified (0 on success, 1 on failure)

---

## Out of Scope

The following items are explicitly **NOT** part of this story:

1. **Stealth Browser Live Tests (Zillow/Redfin)**
   - Requires complex infrastructure (nodriver, proxy rotation)
   - Deferred to dedicated story focused on browser automation testing

2. **Paid API Live Tests (Google, WalkScore)**
   - Requires budget allocation and usage monitoring
   - Deferred to Phase 2 after free API validation proven

3. **Continuous Integration Pipeline**
   - Live test CI/CD integration (scheduled runs, secrets management)
   - Deferred to infrastructure story

4. **Mock Drift Automated Detection**
   - Automated comparison of recorded vs mocked responses
   - Deferred to follow-up story after recording mechanism proven

5. **Performance Benchmarking**
   - API latency benchmarks and regression detection
   - Separate concern from functional validation

6. **Multi-Environment Testing**
   - Staging vs production API endpoint validation
   - Out of scope (single production environment)

---

## References

| Resource | Location |
|----------|----------|
| Existing test fixtures | `tests/conftest.py:1-638` |
| API client base class | `src/phx_home_analysis/services/api_client/base_client.py:1-412` |
| Rate limiter implementation | `src/phx_home_analysis/services/api_client/rate_limiter.py:1-257` |
| Response cache implementation | `src/phx_home_analysis/services/api_client/response_cache.py:1-359` |
| County data extraction | `scripts/extract_county_data.py:1-489` |
| Maricopa API client | `src/phx_home_analysis/services/county_data.py` |
| Test CLAUDE.md | `tests/CLAUDE.md` |
| API client tests | `tests/unit/services/api_client/test_base_client.py:1-327` |

---

*Story created: 2024-12-04*
*Last updated: 2024-12-04*
*Author: Claude Code (Opus 4.5)*

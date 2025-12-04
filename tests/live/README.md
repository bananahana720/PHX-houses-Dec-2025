# Live Test Suite

## Overview

The live test suite validates real API integrations for the PHX Home Analysis pipeline. These tests make actual calls to the Maricopa County Assessor API to verify:

- **Authentication**: Valid token acceptance and API access
- **Schema Validation**: Response structure matches expected `ParcelData` model
- **Rate Limiting**: Proper handling of API rate limits (no 429 errors)
- **Data Accuracy**: Known addresses return expected data ranges
- **Error Handling**: Invalid/empty inputs handled gracefully

Live tests are **excluded by default** from the standard test suite. They require network connectivity and an API token, making them unsuitable for CI/CD per-PR checks. Instead, they run nightly or on-demand for integration validation.

## Quick Start

### 1. Set Up Prerequisites

```bash
# Verify environment variable is set
echo $MARICOPA_ASSESSOR_TOKEN    # macOS/Linux
echo %MARICOPA_ASSESSOR_TOKEN%   # Windows

# If not set, add to .env file:
echo "MARICOPA_ASSESSOR_TOKEN=your_token_here" > .env

# Verify Python dependencies (already installed)
python -c "import pytest; print(f'pytest {pytest.__version__}')"
python -c "import httpx; print(f'httpx {httpx.__version__}')"
```

### 2. Run Live Tests

```bash
# Run all live tests
pytest tests/live/ -m live -v

# Run with custom rate limit (default 0.5 seconds)
pytest tests/live/ -m live -v --live-rate-limit=1.0

# Record responses for drift detection
pytest tests/live/ -m live -v --record-responses

# Run specific test category
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication -v
```

### 3. Quick Health Check

```bash
# Fast smoke test (no live tests)
python scripts/smoke_test.py

# Smoke test with API check
python scripts/smoke_test.py --json
```

## Prerequisites

### Environment Variables

**Required:**
- `MARICOPA_ASSESSOR_TOKEN` - API token for Maricopa County Assessor

Set via:
1. `.env` file in project root (recommended)
2. System environment variables
3. pytest fixture auto-skip if missing

```bash
# .env file format
MARICOPA_ASSESSOR_TOKEN=your_actual_token_here
```

### Network Connectivity

- Outbound HTTPS to `mcassessor.maricopa.gov` (port 443)
- No proxy/firewall blocking County Assessor API
- Stable connection (tests will timeout after ~10 seconds per request)

### Python Dependencies

All required packages already installed. Core dependencies:

```
pytest==9.0.1          # Test framework
httpx==0.28.1          # HTTP client
pydantic==2.12.5       # Data validation
python-dotenv==1.2.1   # Environment loading
```

## Running Tests

### Default Behavior (Exclude Live Tests)

By default, live tests are **not** run:

```bash
# Standard pytest run (skips live tests)
pytest tests/ -v

# Equivalent to:
pytest tests/ -v -m "not live"
```

This is configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short -m \"not live\""
```

### Run Live Tests Explicitly

```bash
# Run all live tests
pytest tests/live/ -m live -v

# Run specific test file
pytest tests/live/test_county_assessor_live.py -m live -v

# Run specific test class
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication -m live -v

# Run specific test method
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication::test_client_initializes_with_valid_token -v
```

### Rate Limiting Control

Rate limiting prevents 429 (Too Many Requests) errors:

```bash
# Default: 0.5 seconds between requests
pytest tests/live/ -m live -v

# Slower: 1 second between requests
pytest tests/live/ -m live -v --live-rate-limit=1.0

# Faster (not recommended): 0.1 seconds
pytest tests/live/ -m live -v --live-rate-limit=0.1

# Conservative for production: 2 seconds
pytest tests/live/ -m live -v --live-rate-limit=2.0
```

## Test Categories

### Authentication Tests (2 tests)

**Location:** `tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication`

Validates token authentication and API access:

```python
async def test_client_initializes_with_valid_token()
```
- Verifies client initializes with valid token from environment
- Checks `_token` attribute is set

```python
async def test_api_accepts_authentication()
```
- Makes minimal API request to verify credentials are accepted
- Fails if API returns authentication error (would raise `httpx.HTTPStatusError`)

**Expected Output:**
```
test_county_assessor_live.py::TestCountyAssessorAuthentication::test_client_initializes_with_valid_token PASSED
test_county_assessor_live.py::TestCountyAssessorAuthentication::test_api_accepts_authentication PASSED
```

### Schema Validation Tests (3 tests)

**Location:** `tests/live/test_county_assessor_live.py::TestCountyAssessorSchemaValidation`

Validates API response structure matches expected `ParcelData` model:

```python
async def test_response_returns_parcel_data_type()
```
- Verifies API response is typed as `ParcelData` instance

```python
async def test_parcel_data_has_required_fields()
```
- Checks for 7 required fields:
  - `apn` - Assessor Parcel Number
  - `full_address` - Complete address
  - `lot_sqft` - Lot size
  - `year_built` - Construction year
  - `garage_spaces` - Garage count
  - `sewer_type` - City or septic
  - `has_pool` - Pool presence flag
- Records response for drift detection (if `--record-responses` flag used)

```python
async def test_field_types_are_correct()
```
- Validates field types match type hints:
  - `apn`: str
  - `lot_sqft`: int
  - `year_built`: int
  - `garage_spaces`: int
  - `sewer_type`: str (must be "city", "septic", or "unknown")
  - `has_pool`: bool

### Rate Limiting Tests (1 test)

**Location:** `tests/live/test_county_assessor_live.py::TestCountyAssessorRateLimiting`

```python
async def test_multiple_requests_no_rate_limit_error()
```
- Makes 3 sequential API requests with rate limiter
- Verifies no 429 (rate limit exceeded) errors occur
- Uses shared rate limiter configured for 60 requests/minute with proactive throttling at 70%

**Rate Limiter Configuration:**
```python
RateLimit(
    requests_per_minute=60,    # Conservative limit
    throttle_threshold=0.7,     # Proactive throttling at 70%
    min_delay=0.5,              # Minimum delay between requests
)
```

### Data Accuracy Tests (2 tests)

**Location:** `tests/live/test_county_assessor_live.py::TestCountyAssessorDataAccuracy`

Uses parametrized test with known addresses:

```python
@pytest.mark.parametrize("address,constraints", KNOWN_ADDRESSES)
async def test_known_address_data_within_constraints()
```

**Test Data:**
| Address | Year Range | Lot Sqft Range | Notes |
|---------|-----------|----------------|-------|
| 4732 W Davis Rd | 1970-2025 | 5,000-20,000 | Verified live 2024-12-04 |
| 3847 E Cactus Rd | 1980-2020 | - | Location validation |

- Validates returned data falls within expected ranges (not exact values, allowing for county data updates)
- Records responses for drift detection

### Error Handling Tests (2 tests)

**Location:** `tests/live/test_county_assessor_live.py::TestCountyAssessorErrorHandling`

```python
async def test_invalid_address_handles_gracefully()
```
- Tests obviously invalid address: "9999999 Nonexistent Street"
- Should return `None` rather than raising exception

```python
async def test_empty_address_handles_gracefully()
```
- Tests empty string input
- Should return `None` or raise `ValueError` (both acceptable)

## Smoke Test Usage

The smoke test provides quick pre-flight checks without running full live tests:

### Basic Usage

```bash
# Run all checks
python scripts/smoke_test.py

# Quick mode (skip slow APIs)
python scripts/smoke_test.py --quick

# JSON output for CI/CD integration
python scripts/smoke_test.py --json

# Run specific API check
python scripts/smoke_test.py --api county

# Custom timeout (seconds per check)
python scripts/smoke_test.py --timeout 20
```

### Checks Performed

| Check | Category | Purpose | Critical |
|-------|----------|---------|----------|
| Environment Variables | Config | Verify `MARICOPA_ASSESSOR_TOKEN` set | Yes |
| County Assessor | API | Real API call to test address | Yes |
| ArcGIS (Fallback) | API | Fallback public API availability | No |
| Data Files | Files | Verify `enrichment_data.json` exists | Yes |
| Cache Directory | Files | Verify `data/api_cache/` is writable | No |

### Output Examples

**Human-Readable:**
```
============================================================
PHX Houses Smoke Test Results
============================================================

[OK]   Environment Variables: All required variables present [N/A]
[OK]   County Assessor: OK (APN: 123456789) [245.3ms]
[OK]   ArcGIS (Fallback): OK [567.2ms]
[OK]   Data Files: enrichment_data.json exists (42 properties) [12.1ms]
[OK]   Cache Directory: Writable at /path/to/data/api_cache [5.2ms]

============================================================
Result: PASS (5/5 checks passed, 0 skipped)
Duration: 830ms
============================================================
```

**JSON Format:**
```json
{
  "status": "pass",
  "checks": [
    {
      "name": "Environment Variables",
      "status": "pass",
      "latency_ms": null,
      "message": "All required variables present",
      "critical": true
    },
    {
      "name": "County Assessor",
      "status": "pass",
      "latency_ms": 245.3,
      "message": "OK (APN: 123456789)",
      "critical": true
    }
  ],
  "duration_ms": 830.5,
  "timestamp": "2025-12-04T15:30:45.123456+00:00"
}
```

### Exit Codes

```
0 - All critical checks passed
1 - One or more critical checks failed
2 - Configuration error (missing env vars)
```

## Response Recording

Recording captures live API responses for drift detection (comparing current API responses against known-good baselines).

### Enable Recording

```bash
# Record responses while running live tests
pytest tests/live/ -m live -v --record-responses

# Record for specific test class
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorDataAccuracy -m live --record-responses
```

### Recording Location

Responses saved to: `tests/fixtures/recorded/`

**File Format:**
```
recording_{test_name}_{timestamp}.json
# Example: recording_test_parcel_data_has_required_fields_20251204_153045.json
```

**Recording Content:**
```json
[
  {
    "api": "county_assessor",
    "operation": "extract_for_address",
    "test_name": "test_parcel_data_has_required_fields[4732 W Davis Rd]",
    "recorded_at": "2025-12-04T15:30:45.123456+00:00",
    "schema_version": "1.0",
    "response": {
      "apn": "123456789",
      "full_address": "4732 W Davis Rd, Phoenix, AZ 85001",
      "lot_sqft": 9500,
      "year_built": 1978,
      "garage_spaces": 2,
      "sewer_type": "city",
      "has_pool": false
    },
    "metadata": {
      "input_address": "4732 W Davis Rd",
      "constraints": {
        "year_built_range": [1970, 2025],
        "lot_sqft_range": [5000, 20000]
      }
    }
  }
]
```

### Drift Detection Workflow

1. **Record baseline** (first time):
   ```bash
   pytest tests/live/ -m live -v --record-responses
   ```

2. **Review recorded data** in `tests/fixtures/recorded/`

3. **Add to version control** as "known-good" responses

4. **Run drift detection** (manual comparison):
   - Compare new recordings against baseline
   - Identify breaking API changes
   - Update constraints in test if data legitimately changed

5. **Escalate if drift detected**:
   - If API field removed → Test fails, API breaking change
   - If API field added → Recording includes new field
   - If data range expanded → Update constraints in test

## CI/CD Integration

### When to Run Live Tests

**NOT recommended for:**
- Per-PR checks (require API token secret, slow)
- Parallel CI runners (rate limiting issues)
- Shallow/feature branches

**Recommended for:**
- Nightly scheduled jobs
- Before release deployments
- Manual validation runs
- Integration environment tests

### GitHub Actions Example

```yaml
name: Live Tests (Nightly)

on:
  schedule:
    - cron: '0 2 * * *'  # Run at 2 AM UTC daily
  workflow_dispatch:     # Manual trigger

jobs:
  live-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run smoke test
        run: python scripts/smoke_test.py --json

      - name: Run live tests
        env:
          MARICOPA_ASSESSOR_TOKEN: ${{ secrets.MARICOPA_ASSESSOR_TOKEN }}
        run: pytest tests/live/ -m live -v --tb=short --live-rate-limit=2.0

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: live-test-results
          path: tests/fixtures/recorded/
```

### Secrets Handling

- Store `MARICOPA_ASSESSOR_TOKEN` as GitHub secret (never in repo)
- Pass via environment variables to test runs
- Rotate token quarterly
- Audit access logs monthly

### Expected Failures

Tests may skip (not fail) when:

1. **Missing token** → fixture skips test
   ```
   tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication::test_client_initializes SKIPPED
   Reason: MARICOPA_ASSESSOR_TOKEN not set - skipping live test
   ```

2. **Network timeout** → test fails with timeout error
   ```
   httpx.ConnectError: Unable to connect to mcassessor.maricopa.gov
   ```

3. **Rate limit hit** → test fails with 429 error
   ```
   httpx.HTTPStatusError: 429 Too Many Requests
   ```

## Troubleshooting

### Missing Token Error

**Symptom:**
```
SKIPPED - MARICOPA_ASSESSOR_TOKEN not set - skipping live test
```

**Solution:**
```bash
# Check if token is set
echo $MARICOPA_ASSESSOR_TOKEN    # macOS/Linux
echo %MARICOPA_ASSESSOR_TOKEN%   # Windows

# Set in .env file
echo "MARICOPA_ASSESSOR_TOKEN=your_token_here" > .env

# Verify it's loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('MARICOPA_ASSESSOR_TOKEN'))"
```

### Rate Limit Errors (429)

**Symptom:**
```
httpx.HTTPStatusError: 429 Client Error: Too Many Requests
```

**Solution:**
```bash
# Increase rate limit delay
pytest tests/live/ -m live -v --live-rate-limit=2.0

# Run fewer tests at once (serial, not parallel)
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication -v --live-rate-limit=1.0
```

### Network Timeouts

**Symptom:**
```
httpx.ConnectError: Unable to connect to mcassessor.maricopa.gov:443
```

**Solution:**
```bash
# Check network connectivity
ping mcassessor.maricopa.gov

# Increase timeout
pytest tests/live/ -m live -v --timeout=30

# Test public API fallback
python scripts/smoke_test.py --api arcgis
```

### Tests Marked as Skipped

**All live tests skipped:**
```
collected 10 items
tests/live/test_county_assessor_live.py::... SKIPPED [...]
```

This is **normal and expected** when:
1. Running without `-m live` flag
2. `MARICOPA_ASSESSOR_TOKEN` not set
3. Using default `pytest` command (which excludes live tests)

**To run live tests:**
```bash
pytest tests/live/ -m live -v
```

## Test Fixtures Reference

### Shared Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `assessor_token` | module | Loads `MARICOPA_ASSESSOR_TOKEN` from environment |
| `live_rate_limit` | module | Rate limit seconds from CLI (`--live-rate-limit`) |
| `assessor_client` | module | Real `MaricopaAssessorClient` instance (skips if no token) |
| `shared_rate_limiter` | module | Shared `RateLimiter` for sequential tests |
| `record_response` | function | Records API responses to `tests/fixtures/recorded/` |

### Using Fixtures in Tests

```python
async def test_example(assessor_client, record_response):
    """Test with real API client and response recording."""
    async with assessor_client as client:
        parcel = await client.extract_for_address("4732 W Davis Rd")

        # Record for drift detection
        record_response(
            "county_assessor",
            "extract_for_address",
            asdict(parcel),
            {"input_address": "4732 W Davis Rd"},
        )
```

## Performance Characteristics

### Execution Time

| Test Category | Count | Time | Per-Test |
|---------------|-------|------|----------|
| Authentication | 2 | ~500ms | 250ms |
| Schema Validation | 3 | ~800ms | 267ms |
| Rate Limiting | 1 | ~1.5s | 1.5s |
| Data Accuracy | 2 | ~600ms | 300ms |
| Error Handling | 2 | ~400ms | 200ms |
| **Total** | **10** | **~3.8s** | **380ms** |

### Rate Limiting Configuration

Default: 0.5 seconds between requests
- Conservative (API allows 60/min = 1 per second)
- Prevents 429 errors in standard CI/CD
- Adjustable via `--live-rate-limit` flag

## Related Resources

- **Smoke test script**: `scripts/smoke_test.py`
- **County API client**: `src/phx_home_analysis/services/county_data.py`
- **Test conftest**: `tests/live/conftest.py`
- **Main test file**: `tests/live/test_county_assessor_live.py`
- **Rate limiter**: `src/phx_home_analysis/services/api_client/rate_limiter.py`

## Summary

Live tests validate real API integrations and are **excluded from default pytest runs**. Use them for:

- Integration validation before releases
- Nightly automated checks
- Manual API health verification
- Drift detection from recorded baselines

Run with:
```bash
# All live tests
pytest tests/live/ -m live -v

# With response recording
pytest tests/live/ -m live -v --record-responses

# Quick health check
python scripts/smoke_test.py

# CI/CD nightly job
pytest tests/live/ -m live -v --live-rate-limit=2.0
```

# Story 2.2: Maricopa County Assessor API Integration

Status: ready-for-dev

## Story

As a system user,
I want to fetch authoritative property data from Maricopa County Assessor,
so that I have reliable lot size, year built, and system information.

## Acceptance Criteria

1. **AC1**: Retrieves lot_sqft, year_built, garage_spaces, has_pool, sewer_type from County API
2. **AC2**: Data stored in `county_data` section with 0.95 confidence score
3. **AC3**: Missing properties flagged with "county_data_missing" warning and 0.0 confidence
4. **AC4**: Rate limit (429) triggers exponential backoff per E1.S6
5. **AC5**: Token refresh handles near-expiration scenarios
6. **AC6**: Schema drift detection for forward compatibility

## Tasks / Subtasks

### Task 1: Pass Live Test Suite (25 Tests)
The implementation is **GREEN phase**—tests exist (25 live tests in `tests/live/test_county_assessor_live.py`) and the client code already exists. Your job is to **make the existing tests pass**.

- [ ] 1.1 Run live test suite: `pytest tests/live/test_county_assessor_live.py -m live -v`
- [ ] 1.2 Fix failing tests one by one (authentication → schema → rate limiting → data accuracy → error handling)
- [ ] 1.3 Verify all 25 tests pass
- [ ] 1.4 Review test output for warnings or edge cases

### Task 2: Field Mapping Implementation (AC1)
**File:** `src/phx_home_analysis/services/county_data/assessor_client.py` (already exists, ~683 lines)

- [ ] 2.1 Review existing `extract_for_address()` method (line ~150-300)
- [ ] 2.2 Ensure mapping extracts: lot_sqft, year_built, garage_spaces, has_pool, sewer_type
- [ ] 2.3 Verify field names match API response structure
- [ ] 2.4 Add logging for field extraction at DEBUG level

### Task 3: Provenance Metadata (AC2)
**File:** `src/phx_home_analysis/domain/entities.py` (EnrichmentData model)

- [ ] 3.1 Ensure `county_data` field in `EnrichmentData` includes provenance metadata
- [ ] 3.2 Set confidence score to 0.95 for successful County API responses
- [ ] 3.3 Include `source: "maricopa_assessor"` in metadata
- [ ] 3.4 Add timestamp for when data was retrieved

### Task 4: Missing Property Handling (AC3)
**File:** `src/phx_home_analysis/services/county_data/assessor_client.py`

- [ ] 4.1 Handle case when API returns no results for address
- [ ] 4.2 Add "county_data_missing" warning to property warnings list
- [ ] 4.3 Set confidence to 0.0 for missing properties
- [ ] 4.4 Log warning message with address for troubleshooting

### Task 5: Rate Limit Handling (AC4)
**File:** `src/phx_home_analysis/services/county_data/assessor_client.py`

- [ ] 5.1 Verify `@retry_with_backoff` decorator is applied to API request methods
- [ ] 5.2 Confirm rate limiter applies 0.5s delay between requests (already configured)
- [ ] 5.3 Test 429 response triggers exponential backoff (1s, 2s, 4s, 8s, 16s)
- [ ] 5.4 Respect `Retry-After` header if present in 429 response

### Task 6: Token Refresh (AC5)
**File:** `src/phx_home_analysis/services/county_data/assessor_client.py`

- [ ] 6.1 Review token loading from `MARICOPA_ASSESSOR_TOKEN` environment variable
- [ ] 6.2 Handle token expiration scenarios (if API returns 401)
- [ ] 6.3 Log clear error message if token is missing or invalid
- [ ] 6.4 Add retry logic for temporary token issues

### Task 7: Schema Drift Detection (AC6)
**File:** `src/phx_home_analysis/services/county_data/models.py`

- [ ] 7.1 Review Pydantic `ParcelData` model for required fields
- [ ] 7.2 Add optional fields for forward compatibility (use `None` defaults)
- [ ] 7.3 Log warning if API returns unexpected fields
- [ ] 7.4 Ensure validation doesn't fail on unknown fields (use `extra="ignore"`)

## Dev Notes

### Implementation Status: GREEN PHASE

**What's Already Done:**
- `CountyAssessorClient` implementation exists (`assessor_client.py`, ~683 lines)
- 25 live tests exist (`tests/live/test_county_assessor_live.py`, ~259 lines)
- Pydantic models defined (`models.py`: `ParcelData`, `ZoningData`)
- Rate limiting infrastructure configured (0.5s between requests)
- Retry decorator from E1.S6 available: `@retry_with_backoff`

**Your Job:**
1. **Run the tests** and see what fails
2. **Fix the failing tests** by adjusting the implementation
3. **Do NOT rewrite the client**—refine what's there
4. **Focus on making tests pass**, not creating new architecture

### Project Structure Notes

```
src/phx_home_analysis/services/county_data/
├── __init__.py              # Exports MaricopaAssessorClient
├── assessor_client.py       # MAIN FILE: ~683 lines, needs fixes
├── models.py                # ParcelData, ZoningData Pydantic models

tests/live/
├── conftest.py              # Fixtures: client, rate limiter, response recording
├── test_county_assessor_live.py  # 25 TESTS: authentication, schema, rate limiting, data accuracy, error handling
└── README.md                # Test documentation
```

## Technical Requirements

### API Details

**Official API:**
- Base URL: `https://mcassessor.maricopa.gov`
- Authentication: Bearer token from `MARICOPA_ASSESSOR_TOKEN` env var
- Rate Limit: ~1 req/sec (conservative); client uses 0.5s delay (60 req/min)

**Fallback API (ArcGIS Public):**
- Base URL: `https://gis.mcassessor.maricopa.gov/arcgis/rest/services`
- Authentication: None
- Rate Limit: Unknown (use 0.5s delay)

### Field Mapping Requirements

| County API Field | EnrichmentData Field | Type | Notes |
|------------------|---------------------|------|-------|
| `LotSize` or `LotSqFt` | `lot_sqft` | int | Square feet |
| `YearBuilt` | `year_built` | int | 4-digit year |
| `GarageSpaces` | `garage_spaces` | int | 0-3+ |
| `HasPool` or `Pool` | `has_pool` | bool | True/False |
| `SewerType` or `Sewer` | `sewer_type` | str | "city" or "septic" |

### Provenance Metadata Structure

```python
{
    "county_data": {
        "lot_sqft": 9500,
        "year_built": 2010,
        "garage_spaces": 2,
        "has_pool": False,
        "sewer_type": "city",
        "_metadata": {
            "source": "maricopa_assessor",
            "confidence": 0.95,
            "retrieved_at": "2025-12-04T10:00:00Z",
            "api_version": "v1"
        }
    }
}
```

### Error Handling Patterns

**Missing Property:**
```python
logger.warning(f"County data not found for address: {address}")
warnings.append("county_data_missing")
confidence = 0.0
```

**Rate Limit (429):**
```python
# @retry_with_backoff handles this automatically
# Exponential backoff: 1s, 2s, 4s, 8s, 16s
# Respects Retry-After header if present
```

**Invalid Token (401):**
```python
if response.status_code == 401:
    raise ValueError(
        "Invalid or expired MARICOPA_ASSESSOR_TOKEN. "
        "Update your .env file with a valid token."
    )
```

## Architecture Compliance

### Per Architecture.md ADR-01 (DDD):
- `assessor_client.py` is in `services/county_data/` (correct domain placement)
- `models.py` uses Pydantic for schema validation
- Client follows repository pattern (async context manager)

### Per E2.S7 (API Integration Infrastructure):
- Inherits from `APIClient` base class (**NOT REQUIRED** for this story—client predates E2.S7)
- Uses `@retry_with_backoff` from E1.S6 for transient error handling
- Implements rate limiting (0.5s delay between requests)

### Per E1.S3 (Data Provenance):
- County data includes confidence score (0.95 for success, 0.0 for missing)
- Metadata includes `source`, `retrieved_at`, `api_version`
- Provenance enables data quality tracking and audit trail

## References

| Reference | Location |
|-----------|----------|
| Epic Story Definition | `docs/epics/epic-2-property-data-acquisition.md:24-35` |
| Existing Client Implementation | `src/phx_home_analysis/services/county_data/assessor_client.py:1-683` |
| Pydantic Models | `src/phx_home_analysis/services/county_data/models.py:1-100` |
| Live Test Suite | `tests/live/test_county_assessor_live.py:1-259` |
| Live Test Fixtures | `tests/live/conftest.py:1-185` |
| Retry Decorator (E1.S6) | `src/phx_home_analysis/errors/retry.py:280-367` |
| API Integration Infrastructure (E2.S7) | `docs/sprint-artifacts/stories/e2-s7-api-integration-infrastructure.md:1-1447` |

## Previous Story Intelligence

### From E2.S1 (Batch Analysis CLI):
- CLI patterns established using Typer with progress reporting (Rich library)
- CSV validation with row-level error messages
- Dry-run mode pattern for validation without execution
- Rolling ETA calculation (last 5 samples)

### From E2.S7 (API Integration Infrastructure):
- `APIClient` base class with auth, rate limiting, caching
- `@retry_with_backoff` decorator for 429 handling
- Cache key generation: SHA256 hash of URL + sorted params
- Response caching with 7-day TTL default
- Proactive throttling at 80% of rate limit

### Git Intelligence (Recent Commits):
- `54933a5`: E2.S1 CLI implementation (--dry-run, --json flags)
- `b55377f`: E2.S3, E2.S5, E2.S6 API integrations completed
- `8cc53ba`: **Live tests for County Assessor added** (25 tests)
- `65b9679`: Test design document for Epic 2-7 live data testing

## Test Plan Summary

### Live Tests (25 Total)
**File:** `tests/live/test_county_assessor_live.py`

| Category | Tests | Purpose |
|----------|-------|---------|
| Authentication | 2 | Token validation, API access |
| Schema Validation | 3 | Response structure matches `ParcelData` |
| Rate Limiting | 1 | No 429 errors across multiple requests |
| Data Accuracy | 2 | Known addresses return expected ranges |
| Error Handling | 2 | Invalid addresses handled gracefully |

**Known Test Addresses:**
1. `4732 W Davis Rd` (year: 1978, lot: 5k-20k sqft)
2. `3847 E Cactus Rd` (year: 1980-2020)

### Running Live Tests

```bash
# Run all live tests
pytest tests/live/test_county_assessor_live.py -m live -v

# Run specific category
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAuthentication -m live -v

# Record responses for drift detection
pytest tests/live/test_county_assessor_live.py -m live --record-responses

# Custom rate limit (slower for safety)
pytest tests/live/test_county_assessor_live.py -m live --live-rate-limit=1.0
```

## Definition of Done Checklist

### Implementation
- [ ] All 25 live tests pass: `pytest tests/live/test_county_assessor_live.py -m live -v`
- [ ] Field mapping extracts: lot_sqft, year_built, garage_spaces, has_pool, sewer_type
- [ ] Provenance metadata includes source, confidence (0.95), timestamp
- [ ] Missing properties flagged with "county_data_missing" warning, confidence 0.0
- [ ] Rate limit (429) triggers exponential backoff via `@retry_with_backoff`
- [ ] Token missing/invalid raises clear error with environment variable name
- [ ] Schema drift handled via Pydantic `extra="ignore"` configuration

### Testing
- [ ] Live test suite passes (all 25 tests green)
- [ ] Authentication tests verify token is valid
- [ ] Schema validation tests confirm `ParcelData` structure matches API
- [ ] Rate limiting test confirms no 429 errors
- [ ] Data accuracy tests validate known addresses return expected ranges
- [ ] Error handling tests verify invalid addresses handled gracefully

### Quality Gates
- [ ] Type checking passes: `mypy src/phx_home_analysis/services/county_data/`
- [ ] Linting passes: `ruff check src/phx_home_analysis/services/county_data/`
- [ ] No credentials logged in any output (DEBUG, INFO, ERROR, exceptions)
- [ ] Docstrings complete with examples and security notes

### Documentation
- [ ] Code comments explain field mapping logic
- [ ] Docstrings updated for any new/modified methods
- [ ] `CLAUDE.md` updated in `src/phx_home_analysis/services/county_data/`

## Dev Agent Record

### Context Reference

- Epic context: `docs/epics/epic-2-property-data-acquisition.md:24-35`
- Existing implementation: `src/phx_home_analysis/services/county_data/assessor_client.py`
- Live test suite: `tests/live/test_county_assessor_live.py`
- API integration infrastructure: `docs/sprint-artifacts/stories/e2-s7-api-integration-infrastructure.md`

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

**Existing Files to Modify:**
- `src/phx_home_analysis/services/county_data/assessor_client.py` (main focus)
- `src/phx_home_analysis/services/county_data/models.py` (schema validation)
- `src/phx_home_analysis/services/county_data/__init__.py` (exports)

**Existing Tests (GREEN phase):**
- `tests/live/test_county_assessor_live.py` (25 tests to pass)
- `tests/live/conftest.py` (fixtures)

---

**Story Created:** 2025-12-04
**Created By:** PM Agent (Claude Sonnet 4.5)
**TDD Phase:** GREEN (tests exist, make them pass)
**ATDD Checklist:** `docs/sprint-artifacts/atdd-checklist-epic-2.md`

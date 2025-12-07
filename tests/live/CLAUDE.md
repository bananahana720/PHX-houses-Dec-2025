---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
flags: []
---

# tests/live

## Purpose
Live API and integration tests requiring real external services. Makes HTTP calls to Maricopa County Assessor API and validates E2-R3 data flow. Excluded from default pytest runs (use `-m live` flag).

## Contents
| Path | Purpose |
|------|---------|
| `conftest.py` | Live test fixtures: token loading, API client factory, rate limiter |
| `test_county_assessor_live.py` | 10 tests: auth, schema, rate limiting, data accuracy, errors |
| `test_zillow_redfin_live.py` | Live extraction tests for Zillow/Redfin sources |
| `test_e2r3_data_flow.py` | 12 tests: E2-R3 field mapping, persistence, round-trip validation |
| `README.md` | Prerequisites, running tests, troubleshooting |

## Test Summary

| File | Tests | Purpose |
|------|-------|---------|
| `test_county_assessor_live.py` | 10 | Maricopa County API validation |
| `test_zillow_redfin_live.py` | 8 | Listing extraction validation |
| `test_e2r3_data_flow.py` | 12 | E2-R3 extraction → storage flow |
| **Total** | **30** | |

## E2-R3 Data Flow Tests (NEW)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| `TestE2R3FieldMappingValidation` | 5 | MLS_FIELD_MAPPING completeness |
| `TestE2R3ExtractionToStorage` | 3 | MetadataPersister integration |
| `TestE2R3ExtractionPatterns` | 2 | Regex pattern validation |
| `TestE2R3Statistics` | 2 | Coverage metrics |

## Commands
```bash
# All live tests
pytest tests/live/ -m live -v

# E2-R3 data flow only
pytest tests/live/test_e2r3_data_flow.py -v

# County assessor only
pytest tests/live/test_county_assessor_live.py -m live -v

# Record responses for drift detection
pytest tests/live/ -m live --record-responses
```

## Tasks
- [x] County Assessor live tests (10 tests)
- [x] Zillow/Redfin live tests (8 tests)
- [x] E2-R3 data flow validation (12 tests)
- [ ] Add PhoenixMLS live extraction tests `P:M`

## Learnings
- E2-R3 validation caught JSON serialization gap before production
- Live tests catch mock drift between recorded and real API behavior
- Rate limiter at 60 req/min prevents 429 errors
- Tests skip gracefully when tokens missing (pytest auto-skip)

## Refs
- E2-R3 tests: `test_e2r3_data_flow.py:1-180`
- County tests: `test_county_assessor_live.py:57-277`
- Fixtures: `conftest.py:33-185`

## Deps
- **← Imports:** phx_home_analysis.services, phx_home_analysis.repositories
- **→ Run by:** CI/CD nightly jobs, manual integration validation

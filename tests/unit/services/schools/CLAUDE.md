---
last_updated: 2025-12-04T12:00:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# tests/unit/services/schools

## Purpose
Unit tests for SchoolRatingsClient service covering API client functionality, school search, composite rating calculation with Arizona weighting, and Google Places fallback behavior.

## Contents
| File | Purpose |
|------|---------|
| `test_ratings_client.py` | SchoolRatingsClient tests: haversine distance, school search, composite ratings, fallback (25 tests) |
| `__init__.py` | Package marker |

## Key Patterns
- **Haversine distance:** Great-circle distance calculation for school proximity filtering
- **Arizona weighting:** High school rated 40%, elementary/middle 30% each (reflects market priorities)
- **Normalized composites:** Missing school levels auto-normalize weights to sum 1.0
- **API fallback:** Google Places provides names only (confidence 0.5) when SchoolDigger fails

## Tasks
- [x] Implement 25 comprehensive mocked tests `P:H`
- [x] Cover haversine distance, search, assigned schools, composite ratings `P:H`
- [x] Test Google Places fallback path `P:H`
- [x] Validate error handling (returns None, never raises) `P:H`
- [ ] Add live integration test with real SchoolDigger API `P:M`

## Learnings
- **Grade level detection:** SchoolDigger uses lowGrade/highGrade ranges (e.g., "K"-"5" = elementary)
- **Composite normalization critical:** Missing middle school produces weights 0.43/0.57, NOT 0.5/0.5
- **Mocked test coverage:** 25 tests cover all code paths without real API calls (fast, deterministic)
- **Confidence metadata:** Models track provenance (0.95 SchoolDigger, 0.5 Google fallback)

## Refs
- SchoolRatingsClient: `src/phx_home_analysis/services/schools/ratings_client.py`
- API models: `src/phx_home_analysis/services/schools/api_models.py`
- Story requirements: `docs/sprint-artifacts/stories/E2-S6-greatschools-api-school-ratings.md`
- Parent service: `src/phx_home_analysis/services/schools/CLAUDE.md`

## Deps
← Imports from:
  - `phx_home_analysis.services.schools` (SchoolRatingsClient, models, haversine_distance)
  - pytest, unittest.mock
  - Standard library: math

→ Imported by:
  - CI/CD pipeline (must pass before merge)
  - Service integration tests


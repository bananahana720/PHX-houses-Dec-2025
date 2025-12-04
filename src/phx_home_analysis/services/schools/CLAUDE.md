---
last_updated: 2025-12-04T12:00:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# schools

## Purpose
School ratings extraction providing elementary, middle, and high school quality scores via SchoolDigger API with Google Places fallback. Calculates Arizona-weighted composite ratings (high school 40%, elem/mid 30% each) for property value assessment.

## Contents
| File | Purpose |
|------|---------|
| `ratings_client.py` | SchoolRatingsClient: search_schools_by_location(), get_assigned_schools(), calculate_composite_rating() |
| `api_models.py` | Pydantic models: SchoolResult, AssignedSchoolsResult, SchoolFallbackResult (with to_enrichment_dict()) |
| `extractor.py` | Legacy GreatSchools scraper (deprecated) |
| `models.py` | Legacy SchoolData model (backward compatibility) |

## Key Patterns
- **Haversine distance:** Great-circle distance for school-to-property filtering
- **Arizona weighting:** High school 40%, elem/mid 30% each (reflects AZ market priorities)
- **Normalized composites:** Missing levels auto-normalize weights to sum 1.0
- **Graceful fallback:** Google Places (confidence 0.5) used when SchoolDigger fails (names only, no ratings)

## API Configuration
| Setting | Value |
|---------|-------|
| Base URL | `https://schooldigger.p.rapidapi.com` (RapidAPI) |
| Auth | `SCHOOLDIGGER_API_KEY` via X-RapidAPI-Key header |
| Rate limit | 1000 req/day (free tier) |
| Cache | 30-day TTL in `data/api_cache/schooldigger/` |
| Timeout | 30 seconds |
| Cost | Free (SchoolDigger), $0.032/property fallback (Google) |

## Tasks
- [x] Implement SchoolRatingsClient extending APIClient `P:H`
- [x] Create models with to_enrichment_dict() `P:H`
- [x] Add haversine distance + composite rating `P:H`
- [x] Write 25 comprehensive mocked tests `P:H`
- [ ] Add live integration test with real API `P:M`

## Learnings
- **Grade level detection:** SchoolDigger lowGrade/highGrade (e.g., "K"-"5" = elementary)
- **Normalization critical:** Missing middle school → 0.43/0.57 weights, NOT 0.5/0.5
- **RapidAPI pattern:** API key in X-RapidAPI-Key header, NOT query params
- **Confidence tracking:** 0.95 SchoolDigger, 0.5 Google fallback (provenance metadata)

## Refs
- API client base: `src/phx_home_analysis/services/api_client/base_client.py:1-412`
- Google Maps fallback: `src/phx_home_analysis/services/maps/client.py:270-334`
- Story: `docs/sprint-artifacts/stories/E2-S6-greatschools-api-school-ratings.md`
- Tests: `tests/unit/services/schools/test_ratings_client.py` (25 tests)

## Deps
← `phx_home_analysis.services.api_client`, `phx_home_analysis.services.maps`, pydantic, math
→ Pipeline orchestrator (Phase 1), property enrichment, tests


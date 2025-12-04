# schools

## Purpose
School ratings extraction providing elementary, middle, and high school quality scores via SchoolDigger API with Google Places fallback. Calculates Arizona-weighted composite ratings prioritizing high school quality for property value assessment.

## Contents
| File | Purpose |
|------|---------|
| `ratings_client.py` | SchoolDigger API client with 30-day cache, 1000/day quota, Google Places fallback |
| `api_models.py` | Pydantic models (SchoolResult, AssignedSchoolsResult, SchoolFallbackResult) |
| `extractor.py` | Legacy browser-based GreatSchools scraper (deprecated, use ratings_client) |
| `models.py` | Legacy SchoolData model (kept for backward compatibility) |

## Public Interface

### SchoolRatingsClient

**Methods:**
- `search_schools_by_location(lat, lng, radius_meters=8046) -> list[SchoolResult]` - Search schools within 5-mile radius (default)
- `get_assigned_schools(lat, lng) -> AssignedSchoolsResult | None` - Get elementary/middle/high with composite rating
- `calculate_composite_rating(elem, mid, high) -> float | None` - Arizona-weighted: (elem×0.3) + (mid×0.3) + (high×0.4)
- `_fallback_to_google_places(lat, lng) -> SchoolFallbackResult | None` - Fallback when API fails (names only)

**Configuration:**
- Base URL: `https://schooldigger.p.rapidapi.com` (RapidAPI)
- Auth: `SCHOOLDIGGER_API_KEY` via X-RapidAPI-Key header
- Rate limit: 1000 requests/day (free tier)
- Cache: 30-day TTL in `data/api_cache/schooldigger/`
- Timeout: 30 seconds
- Fallback: Google Places API (requires `GOOGLE_MAPS_API_KEY`)

**Cost:** Free (0-2,000 calls/month SchoolDigger), Google Places fallback $0.032/property if needed

### Models

All models include `to_enrichment_dict()` for `enrichment_data.json` integration.

**SchoolLevel (Enum):**
- ELEMENTARY, MIDDLE, HIGH, UNKNOWN

**SchoolResult:**
- Fields: name, address, latitude, longitude, rating (0-10), level, distance_meters, is_assigned, confidence, source
- Provenance: confidence=0.95 (SchoolDigger), source="schooldigger_api"

**AssignedSchoolsResult:**
- Fields: elementary, middle, high (each SchoolResult | None), composite_rating, confidence, source
- Composite formula: Arizona-weighted (high school 40%, elementary/middle 30% each)
- Normalized weights when levels missing (e.g., if only elem+high: weights become 0.43 + 0.57)

**SchoolFallbackResult:**
- Fields: school_names (list), school_count, confidence=0.5, source="google_places_fallback"
- Used when SchoolDigger fails - provides names only, NO ratings

## Key Patterns

- **Haversine distance**: Great-circle distance calculation for school-to-property distances
- **Assigned school heuristic**: Nearest school of each level within 2 miles (SchoolDigger lacks boundary data)
- **Arizona weighting**: High school weighted 40% reflects AZ market priorities (college readiness, long-term value)
- **Normalized composites**: When levels missing, weights normalize to sum 1.0 (maintains fair comparison)
- **Error handling**: All methods return None on failure, never raise exceptions to pipeline

## Tasks
- [x] Implement SchoolRatingsClient extending APIClient `P:H`
- [x] Create Pydantic models with to_enrichment_dict() `P:H`
- [x] Add haversine distance calculation `P:H`
- [x] Implement composite rating with Arizona weighting `P:H`
- [x] Add Google Places fallback `P:H`
- [x] Write comprehensive mocked tests (25 tests, all passing) `P:H`
- [ ] Add live integration test with real API `P:M`
- [ ] Document SchoolDigger API response schema changes `P:L`

## Learnings

- **SchoolDigger grade levels**: Determine school type from lowGrade/highGrade (e.g., "K"-"5" = elementary)
- **Composite normalization critical**: Missing middle school changes weights from 0.3/0.3/0.4 to 0.43/0.57 (NOT 0.5/0.5)
- **RapidAPI auth pattern**: API key goes in X-RapidAPI-Key header, NOT query params (override _build_params)
- **Distance filtering**: API distance param is approximate, must apply haversine post-filter for accuracy
- **Google Places limitations**: Provides school names/locations only - NO ratings available (hence 0.5 confidence)
- **Arizona market**: High school quality weighted 40% (vs standard 33.3%) reflects buyer priorities

## Refs

- API client base: `src/phx_home_analysis/services/api_client/base_client.py:1-412`
- Google Maps fallback: `src/phx_home_analysis/services/maps/client.py:270-334`
- Story requirements: `docs/sprint-artifacts/stories/E2-S6-greatschools-api-school-ratings.md`
- Tests: `tests/unit/services/schools/test_ratings_client.py` (25 tests)

## Deps

← Imports from:
  - `phx_home_analysis.services.api_client` (APIClient, RateLimit)
  - `phx_home_analysis.services.maps` (GoogleMapsClient - fallback)
  - `pydantic` (BaseModel, Field)
  - `enum` (Enum)
  - `math` (haversine calculation)

→ Imported by:
  - Pipeline orchestrator (Phase 1: school ratings extraction)
  - Property enrichment services
  - Tests: `tests/unit/services/schools/test_ratings_client.py`


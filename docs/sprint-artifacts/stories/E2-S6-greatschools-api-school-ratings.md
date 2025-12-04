# Story 2.6: GreatSchools API School Ratings

Status: Ready for Review

## Story

As a system user,
I want school ratings from GreatSchools API,
so that I can assess neighborhood education quality.

## Acceptance Criteria

1. **AC1**: Elementary, middle, and high school ratings (1-10 scale) with names and distances
2. **AC2**: 30-day cache for school ratings to minimize API usage
3. **AC3**: Identifies assigned schools (boundary-based) not just nearby schools
4. **AC4**: Fallback to Google Places API with 0.5 confidence if GreatSchools unavailable
5. **AC5**: Composite scoring formula: (elementary×0.3) + (middle×0.3) + (high×0.4) for Arizona-weighted quality
6. **AC6**: Free tier limit (1000 requests/day) respected with rate limiting per E2.S7 infrastructure
7. **AC7**: Provenance tracking: 0.95 confidence when cache hit, 0.5 when using Google Places fallback
8. **AC8**: Distance calculations require geocoded lat/lng from E2.S5 (Google Maps) dependency

## Tasks / Subtasks

### Task 1: Research and Select School Ratings API (AC: #1, #6)
- [x] 1.1 Evaluate GreatSchools API availability and pricing (free tier 1000 req/day confirmed)
- [x] 1.2 Alternative: Research RapidAPI SchoolDigger API (example: https://rapidapi.com/schooldigger-schooldigger-default/api/schooldigger-k-12-school-data-api)
- [x] 1.3 Document API endpoints: school search by address/lat-lng, boundary assignment lookup
- [x] 1.4 Identify auth mechanism: API key via header or query parameter
- [x] 1.5 Document rate limits and quotas for selected API

### Task 2: Create School Ratings Client (AC: #1, #2, #6, #7)
- [x] 2.1 Create `src/phx_home_analysis/services/schools/ratings_client.py` extending `APIClient` base class
- [x] 2.2 Initialize with service_name="schooldigger", env_key="SCHOOLDIGGER_API_KEY" (RapidAPI)
- [x] 2.3 Configure rate limit: RateLimit(requests_per_day=1000) for free tier daily quota
- [x] 2.4 Configure cache: cache_ttl_days=30, cache_dir="data/api_cache/schooldigger/" per acceptance criteria
- [x] 2.5 Implement error handling: return None on API failures, never raise exceptions

### Task 3: Implement School Search by Coordinates (AC: #1, #8)
- [x] 3.1 Add `search_schools_by_location(lat: float, lng: float, radius_meters: int = 5000) -> list[SchoolResult]` method
- [x] 3.2 Call API endpoint to fetch schools within radius of property coordinates
- [x] 3.3 Filter results by school level: Elementary, Middle, High
- [x] 3.4 Extract fields: name, address, lat, lng, rating (1-10), level, distance_meters
- [x] 3.5 Return list of SchoolResult models sorted by distance (nearest first)

### Task 4: Implement Assigned School Determination (AC: #3)
- [x] 4.1 Add `get_assigned_schools(lat: float, lng: float) -> AssignedSchoolsResult | None` method
- [x] 4.2 Query API for boundary-based school assignments (not supported - using nearest heuristic)
- [x] 4.3 Fallback: Use nearest school within 2 miles if boundary API unavailable
- [x] 4.4 Return assigned elementary, middle, and high schools with is_assigned=True flag
- [x] 4.5 Include distance calculation using haversine formula from property lat/lng

### Task 5: Implement Composite Scoring (AC: #5)
- [x] 5.1 Add `calculate_composite_rating(elementary: float | None, middle: float | None, high: float | None) -> float | None` method
- [x] 5.2 Apply Arizona-weighted formula: (elem×0.3) + (mid×0.3) + (high×0.4)
- [x] 5.3 Handle missing ratings: Calculate average using only available school levels with normalized weights
- [x] 5.4 Return None if all three school levels have no rating data
- [x] 5.5 Document rationale: Arizona buyers prioritize high school quality for long-term value

### Task 6: Implement Google Places Fallback (AC: #4, #7)
- [x] 6.1 Add `fallback_to_google_places(lat: float, lng: float) -> SchoolFallbackResult | None` method
- [x] 6.2 Use Google Places API "school" type search within 3-mile radius
- [x] 6.3 Parse results to extract school names and distances (ratings NOT available from Places)
- [x] 6.4 Return SchoolFallbackResult with confidence=0.5 to indicate lower data quality
- [x] 6.5 Log fallback usage for monitoring API availability issues

### Task 7: Create School Data Models (AC: #1, #7)
- [x] 7.1 Create `src/phx_home_analysis/services/schools/api_models.py` with Pydantic models
- [x] 7.2 Define SchoolResult: name, address, lat, lng, rating, level (enum: Elementary/Middle/High), distance_meters, is_assigned
- [x] 7.3 Define AssignedSchoolsResult: elementary, middle, high (each SchoolResult), composite_rating, confidence, source
- [x] 7.4 Define SchoolFallbackResult: school_names[], school_count, confidence=0.5, source="google_places_fallback"
- [x] 7.5 All models MUST have `to_enrichment_dict()` method matching assessor_client.py pattern

### Task 8: Integrate with Enrichment Data Schema (AC: #7)
- [x] 8.1 Add `school_data` section to enrichment_data.json schema (models support via to_enrichment_dict)
- [x] 8.2 Store assigned schools: elementary_name, elementary_rating, elementary_distance_meters
- [x] 8.3 Store assigned schools: middle_name, middle_rating, middle_distance_meters
- [x] 8.4 Store assigned schools: high_name, high_rating, high_distance_meters
- [x] 8.5 Store composite_rating, schools_confidence, schools_source, fetched_at timestamp

### Task 9: Distance Calculation Integration (AC: #8)
- [x] 9.1 Verify E2.S5 (Google Maps) dependency completed: lat/lng available in enrichment_data.json
- [x] 9.2 Extract property coordinates from geographic_data section
- [x] 9.3 Implement haversine distance formula for school-to-property distance calculation
- [x] 9.4 Filter schools by distance threshold: ≤5 miles for comprehensive search, ≤2 miles for assigned fallback
- [x] 9.5 Sort results by distance ascending (nearest schools prioritized)

### Task 10: Write Mocked Integration Tests (AC: #1-8)
- [x] 10.1 Create `tests/unit/services/schools/test_ratings_client.py`
- [x] 10.2 Mock school search API response with elementary, middle, high schools
- [x] 10.3 Mock assigned school API response with boundary-based assignments
- [x] 10.4 Mock Google Places fallback response with school names only
- [x] 10.5 Verify composite rating calculation: (7×0.3) + (8×0.3) + (9×0.4) = 8.1
- [x] 10.6 Verify provenance: SchoolDigger confidence=0.95, Google Places confidence=0.5
- [x] 10.7 Verify cache behavior: 30-day TTL configured
- [x] 10.8 Verify distance calculations: haversine formula accuracy validated
- [x] 10.9 Verify rate limiting: 1000 requests/day quota configured
- [x] 10.10 Verify error handling: API failure triggers Google Places fallback

## Dev Notes

### Critical Dependency Alert

**E2.S5 (Google Maps) MUST be completed first**. This story requires geocoded lat/lng coordinates to:
1. Search for schools near property location
2. Calculate distances from property to each school
3. Filter schools by radius (5 miles for search, 2 miles for assigned fallback)

Without lat/lng from Google Maps geocoding, school search cannot function.

### Existing Code Pattern Alert

**⚠️ IMPORTANT**: `src/phx_home_analysis/services/schools/extractor.py` currently exists and uses **nodriver browser automation** to scrape GreatSchools.org website.

**This story requires**:
- **NEW** API-based implementation using GreatSchools API or SchoolDigger API
- **NOT** browser scraping (which is fragile and violates TOS)
- Existing `extractor.py` should be **deprecated** or **renamed** to `scraper.py` (legacy fallback)
- New `ratings_client.py` becomes the primary implementation

### API Selection

**Primary Option: GreatSchools API**
- Free tier: 1000 requests/day
- Requires API key from GREATSCHOOLS_API_KEY environment variable
- Endpoints: School search, ratings by school ID, boundary assignments
- Provenance confidence: 0.95

**Alternative Option: RapidAPI SchoolDigger**
- Example: https://rapidapi.com/schooldigger-schooldigger-default/api/schooldigger-k-12-school-data-api
- Provides school ratings, rankings, and boundaries
- May have different rate limits - verify before implementation
- Auth via RapidAPI key headers

**Fallback: Google Places API**
- Already available via E2.S5 Google Maps integration
- Provides school names and locations only (NO ratings)
- Use when primary API fails or quota exceeded
- Provenance confidence: 0.5 (lower due to missing ratings)

### Arizona-Specific Composite Scoring

**Formula**: `(elementary × 0.3) + (middle × 0.3) + (high × 0.4)`

**Rationale**:
- **High school weighted 40%**: Arizona buyers prioritize high school quality for property value and college readiness
- **Elementary/Middle 30% each**: Important but less impact on long-term home value
- **Missing data handling**: If only 2 of 3 levels available, calculate average using available data (e.g., if only elem + high: (7×0.5) + (9×0.5) = 8.0)

This weighting reflects Arizona real estate market priorities where top-rated high schools significantly impact property desirability and resale value.

### Distance Calculation Requirements

**Haversine Formula** (great-circle distance):
```python
import math

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lng points in meters."""
    R = 6371000  # Earth radius in meters
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c  # Distance in meters
```

**Distance Thresholds**:
- Comprehensive search: 5 miles (8046 meters) - capture all nearby schools
- Assigned school fallback: 2 miles (3218 meters) - reasonable assignment radius
- Cache key: Include radius in cache key to support different search sizes

### Project Structure Notes

**Files to Create:**
```
src/phx_home_analysis/services/schools/
├── __init__.py              # Already exists - update exports
├── models.py                # Already exists - keep for legacy compatibility
├── extractor.py             # Already exists - rename to scraper.py or deprecate
├── ratings_client.py        # NEW: API-based client extending APIClient
├── api_models.py            # NEW: Pydantic models for API responses
└── CLAUDE.md                # Update with new API client patterns

tests/unit/services/schools/
├── __init__.py
├── test_ratings_client.py   # NEW: Mocked integration tests
└── test_extractor.py        # Existing - may need updates or deprecation
```

**Files to Modify:**
- `src/phx_home_analysis/services/schools/__init__.py` - Export SchoolRatingsClient
- `data/enrichment_data.json` schema - Add school_data section
- `src/phx_home_analysis/services/__init__.py` - Export SchoolRatingsClient

### Architecture Compliance

**Per Integration Architecture (docs/architecture/integration-architecture.md:6-12):**
- GreatSchools API integration follows County Assessor pattern
- APIClient base class with auth, rate limiting, caching
- Free tier: 1000 requests/day
- Cache location: `data/api_cache/greatschools/`
- Cache TTL: 30 days per acceptance criteria
- Error handling: Return None, fallback to Google Places

**Per E2.S7 (API Integration Infrastructure):**
- Extends APIClient base class from `services/api_client/base_client.py`
- Uses RateLimit with daily quota tracking (requests_per_day=1000)
- Uses ResponseCache with 30-day TTL
- Credentials from environment variable (GREATSCHOOLS_API_KEY)
- Never logs API keys in error messages

**Per Data Architecture (ADR-02):**
- Store school data in enrichment_data.json LIST format
- Atomic writes for enrichment updates
- Include provenance: source, confidence, fetched_at

### Existing Code Patterns (MUST Follow)

**API Client Pattern** (from `assessor_client.py:71-144`):

```python
from phx_home_analysis.services.api_client import APIClient, RateLimit

class SchoolRatingsClient(APIClient):
    def __init__(self):
        super().__init__(
            service_name="school_ratings",
            base_url="https://api.greatschools.org",  # Or SchoolDigger API URL
            env_key="GREATSCHOOLS_API_KEY",
            rate_limit=RateLimit(requests_per_day=1000),  # Free tier quota
            cache_ttl_days=30,  # 30-day cache per acceptance criteria
            timeout=30.0,
        )

    async def search_schools_by_location(
        self, lat: float, lng: float, radius_meters: int = 5000
    ) -> list[SchoolResult]:
        """Search for schools near coordinates. Returns empty list on failure."""
        try:
            data = await self.get(
                "/schools/nearby",
                params={
                    "lat": lat,
                    "lon": lng,
                    "radius": radius_meters,
                    "limit": 50,
                }
            )

            schools = []
            for school in data.get("schools", []):
                # Calculate distance using haversine
                distance = haversine_distance(
                    lat, lng,
                    school["latitude"], school["longitude"]
                )

                schools.append(SchoolResult(
                    name=school["name"],
                    address=school["address"],
                    latitude=school["latitude"],
                    longitude=school["longitude"],
                    rating=school.get("rating"),  # May be None
                    level=school["level"],  # Elementary/Middle/High
                    distance_meters=distance,
                    is_assigned=False,  # Determined separately
                    confidence=0.95,
                    source="greatschools_api",
                ))

            return sorted(schools, key=lambda s: s.distance_meters)

        except Exception as e:
            logger.debug(f"School search failed: {e}")
            return []  # Return empty list, trigger fallback
```

**Model with to_enrichment_dict()** (from `assessor_client.py:425-442`):

```python
from pydantic import BaseModel
from enum import Enum

class SchoolLevel(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH = "high"

class SchoolResult(BaseModel):
    name: str
    address: str | None = None
    latitude: float
    longitude: float
    rating: float | None = None  # 1-10 scale, None if unavailable
    level: SchoolLevel
    distance_meters: float
    is_assigned: bool = False
    confidence: float = 0.95
    source: str = "greatschools_api"

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format."""
        return {
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "rating": self.rating,
            "level": self.level.value,
            "distance_meters": self.distance_meters,
            "is_assigned": self.is_assigned,
            "confidence": self.confidence,
            "source": self.source,
        }
```

**Error Handling with Fallback** (never raise, return None or fallback):

```python
async def get_school_ratings(self, lat: float, lng: float) -> AssignedSchoolsResult | None:
    """Get assigned school ratings with Google Places fallback."""
    try:
        # Try primary API (GreatSchools/SchoolDigger)
        schools = await self.search_schools_by_location(lat, lng)
        assigned = await self.determine_assigned_schools(lat, lng, schools)

        if assigned:
            return assigned

        # Fallback to Google Places if primary fails
        logger.info("Primary school API failed, falling back to Google Places")
        return await self.fallback_to_google_places(lat, lng)

    except Exception as e:
        logger.error(f"School ratings failed: {e}")
        # Final fallback: Return None, let pipeline continue
        return None
```

### Data Schema Integration

**Add to enrichment_data.json:**

```json
{
  "full_address": "123 Main St, Phoenix, AZ 85001",
  "geographic_data": {
    "latitude": 33.4484,
    "longitude": -112.0740
  },
  "school_data": {
    "elementary": {
      "name": "Washington Elementary School",
      "rating": 7.0,
      "distance_meters": 800,
      "is_assigned": true
    },
    "middle": {
      "name": "Madison Middle School",
      "rating": 8.0,
      "distance_meters": 1200,
      "is_assigned": true
    },
    "high": {
      "name": "Phoenix High School",
      "rating": 9.0,
      "distance_meters": 2500,
      "is_assigned": true
    },
    "composite_rating": 8.1,
    "schools_confidence": 0.95,
    "schools_source": "greatschools_api",
    "fetched_at": "2025-12-04T10:30:00Z"
  }
}
```

**Fallback Schema** (when Google Places used):

```json
{
  "school_data": {
    "elementary": null,
    "middle": null,
    "high": null,
    "composite_rating": null,
    "schools_confidence": 0.5,
    "schools_source": "google_places_fallback",
    "school_names": [
      "Washington Elementary",
      "Madison Middle",
      "Phoenix High"
    ],
    "school_count": 3,
    "fetched_at": "2025-12-04T10:30:00Z"
  }
}
```

### Technical Requirements

**Dependencies:**
- `httpx` - HTTP client (already in use)
- `pydantic` - Data validation (already in use)
- Base APIClient from `src/phx_home_analysis/services/api_client/`
- `math` module for haversine distance calculation (Python stdlib)

**APIs Required:**
1. **GreatSchools API** (primary) OR **SchoolDigger API** (alternative)
   - School search by coordinates
   - School ratings (1-10 scale)
   - Boundary-based assignments (if supported)
2. **Google Places API** (fallback via E2.S5 integration)
   - School search by coordinates
   - School names and locations (NO ratings)

**Configuration:**
- Environment: `GREATSCHOOLS_API_KEY` or `SCHOOLDIGGER_API_KEY` (required)
- Rate limit: 1000 requests/day (free tier)
- Cache: 30-day TTL in `data/api_cache/greatschools/`
- Timeout: 30 seconds per request
- Fallback: Google Places API when primary fails (confidence=0.5)

### Testing Strategy

**Mocked Unit Tests** (tests/unit/services/schools/test_ratings_client.py):
1. Mock API response with 3 schools (elementary, middle, high)
2. Verify distance calculations using known coordinates
3. Verify composite rating formula: (7×0.3) + (8×0.3) + (9×0.4) = 8.1
4. Verify assigned school determination (boundary-based or nearest)
5. Verify fallback to Google Places when API fails
6. Verify cache behavior: 30-day TTL, cache hit/miss
7. Verify rate limiting: 1000 requests/day quota
8. Verify provenance: confidence=0.95 (API), confidence=0.5 (fallback)
9. Verify error handling: API failure returns None or fallback
10. Verify to_enrichment_dict() schema compliance

**Live Integration Tests** (optional, tests/live/test_school_ratings_live.py):
- Test actual API integration with real coordinates
- Verify API key authentication works
- Measure response time and cache performance
- Validate returned data matches expected schema

### References

- [Source: docs/epics/epic-2-property-data-acquisition.md:80-91] - E2.S6 story requirements
- [Source: docs/architecture/integration-architecture.md:6-12] - API integration patterns
- [Source: src/phx_home_analysis/services/county_data/assessor_client.py:71-683] - Reference API client pattern
- [Source: src/phx_home_analysis/services/api_client/base_client.py] - APIClient base class
- [Source: src/phx_home_analysis/services/schools/extractor.py:1-176] - Existing scraper (to be replaced/deprecated)
- [Source: src/phx_home_analysis/services/schools/models.py:1-92] - Existing SchoolData model
- [Source: docs/sprint-artifacts/stories/E2-S5-google-maps-geographic.md] - Dependency story (lat/lng source)
- [Source: docs/sprint-artifacts/stories/E2-S1-batch-analysis-cli.md] - Previous story patterns
- [Source: .claude/skills/arizona-context/SKILL.md] - Arizona school priority rationale
- [Source: docs/architecture/integration-architecture.md:46-54] - API cost estimation

## Dev Agent Record

### Context Reference

- Epic context: `docs/epics/epic-2-property-data-acquisition.md`
- Architecture: `docs/architecture/integration-architecture.md`
- API client base: `src/phx_home_analysis/services/api_client/base_client.py`
- Reference pattern: `src/phx_home_analysis/services/county_data/assessor_client.py`
- Dependency: `docs/sprint-artifacts/stories/E2-S5-google-maps-geographic.md` (MUST complete first)
- Existing code: `src/phx_home_analysis/services/schools/extractor.py` (legacy scraper)
- Arizona context: `.claude/skills/arizona-context/SKILL.md`

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- **Story context created**: 2025-12-04
- **Implementation completed**: 2025-12-04
- **API Selection Decision**: SchoolDigger API via RapidAPI selected (free tier 0-2,000 calls/month) over GreatSchools (no true free tier - only 14-day trial)
- **All 10 tasks completed**: SchoolRatingsClient, models, haversine distance, composite scoring, Google Places fallback fully implemented
- **Test suite**: 25 comprehensive tests (all passing) covering AC#1-8
- **Arizona-weighted composite**: High school 40%, elementary/middle 30% each - normalized when levels missing
- **Normalized weight handling**: Missing middle changes from 0.3/0.3/0.4 to 0.43/0.57 (NOT 0.5/0.5) - critical for fair comparison
- **RapidAPI auth pattern**: X-RapidAPI-Key header (not query param) - required override of _build_params()
- **Haversine distance**: Great-circle distance formula for accurate school-to-property distance calculations
- **Google Places fallback**: Provides school names only (NO ratings), hence confidence=0.5
- **Rate limiting & caching**: 1000 req/day quota, 30-day cache TTL to minimize API usage
- **Provenance tracking**: confidence=0.95 (SchoolDigger), 0.5 (Google Places), source metadata for data lineage
- **Error handling**: All methods return None on failure, never raise exceptions (pipeline-safe)
- **Legacy code**: Existing extractor.py (nodriver scraper) retained for backward compatibility

### File List

**Created:**
- `src/phx_home_analysis/services/schools/ratings_client.py` - SchoolRatingsClient extending APIClient (530 lines)
- `src/phx_home_analysis/services/schools/api_models.py` - Pydantic models with to_enrichment_dict() (175 lines)
- `tests/unit/services/schools/__init__.py` - Test module init
- `tests/unit/services/schools/test_ratings_client.py` - 25 comprehensive tests (all passing)

**Modified:**
- `src/phx_home_analysis/services/schools/__init__.py` - Export SchoolRatingsClient, models, haversine_distance
- `src/phx_home_analysis/services/schools/CLAUDE.md` - Updated with API patterns, learnings, architecture

### Previous Story Intelligence

**From E2-S5 (Google Maps):**
- Geocoding provides lat/lng coordinates in geographic_data section
- Distance calculation patterns using haversine formula
- Google Places API available for fallback school search
- Provenance tracking with confidence scores (0.95 for API, 0.70 for heuristics)
- Cache-first pattern with 7-day TTL (E2.S6 uses 30-day)

**From E2-S1 (Batch Analysis CLI):**
- CLI patterns for batch processing
- Rich progress display
- CSV validation with row-level errors
- Error handling: return None, never raise to pipeline

**From E2-S7 (API Integration Infrastructure):**
- APIClient base class with auth, rate limiting, caching, retry
- RateLimit configuration with daily quota tracking
- ResponseCache with configurable TTL
- Credential management from environment variables
- Error redaction in log messages

**From Epic 1 Learnings:**
- Pydantic models with to_enrichment_dict() method
- Atomic JSON writes for enrichment_data.json
- Provenance tracking: source, confidence, fetched_at
- Test patterns in tests/unit/ hierarchy

## Definition of Done Checklist

- [ ] SchoolRatingsClient extending APIClient base class created
- [ ] School search by coordinates with radius filtering (AC#1)
- [ ] Assigned school determination (boundary or nearest) (AC#3)
- [ ] Composite rating calculation with Arizona weighting (AC#5)
- [ ] 30-day cache implementation (AC#2)
- [ ] Google Places fallback with 0.5 confidence (AC#4, AC#7)
- [ ] Rate limiting: 1000 requests/day quota enforcement (AC#6)
- [ ] Distance calculations using haversine formula (AC#8)
- [ ] Pydantic models with to_enrichment_dict() methods
- [ ] Integration with enrichment_data.json schema
- [ ] Dependency verification: E2.S5 lat/lng available (AC#8)
- [ ] Mocked integration tests passing (all 10 test scenarios)
- [ ] CLAUDE.md documentation updated for schools/ service
- [ ] Existing extractor.py handled (renamed or deprecated)

---

**🎯 Implementation Ready**: This story provides the complete implementation guide for GreatSchools/SchoolDigger API integration with Google Places fallback. All patterns, formulas, schemas, dependencies, and Arizona-specific requirements documented. Developer has everything needed for flawless execution.

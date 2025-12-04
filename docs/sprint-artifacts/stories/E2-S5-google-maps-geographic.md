# Story 2.5: Google Maps API Geographic Data

Status: ready-for-dev

## Story

As a system user,
I want geographic data from Google Maps API,
so that I have accurate geocoding, distances, and orientation.

## Acceptance Criteria

1. **AC1**: Geocoding returns lat/lng and formatted address, cached to minimize API costs
2. **AC2**: Distances computed to work location, supermarket, and park (nearest of each type)
3. **AC3**: Sun orientation inferred from satellite imagery with Arizona-optimized scoring:
   - N (North) = 25pts (best for Arizona - minimizes afternoon sun exposure)
   - E (East) = 18.75pts (good - morning sun only)
   - S (South) = 12.5pts (moderate - all-day sun)
   - W (West) = 0pts (worst - intense afternoon heat in Arizona)
4. **AC4**: Cache checked before external requests with 7-day TTL default
5. **AC5**: API cost tracking enabled: ~$0.05-0.10 per property (geocode + distance + places)
6. **AC6**: Rate limiting per E2.S7 infrastructure prevents hitting API quotas
7. **AC7**: Provenance tracking with 0.95 confidence for all Google Maps data
8. **AC8**: Fallback to cached data on API failures - never raise exceptions to pipeline

## Tasks / Subtasks

### Task 1: Create Google Maps Client with Base Infrastructure (AC: #1, #4, #6, #8)
- [ ] 1.1 Create `src/phx_home_analysis/services/maps/client.py` extending `APIClient` base class
- [ ] 1.2 Initialize with service_name="google_maps", env_key="GOOGLE_MAPS_API_KEY"
- [ ] 1.3 Configure rate limit: RateLimit(requests_per_second=50/60=0.83) for free tier burst limit
- [ ] 1.4 Configure cache: cache_ttl_days=7, cache_dir="data/api_cache/google_maps/"
- [ ] 1.5 Implement error handling: return None on API failures, never raise exceptions

### Task 2: Implement Geocoding Service (AC: #1, #7)
- [ ] 2.1 Add `geocode_address(address: str) -> GeocodeResult | None` method
- [ ] 2.2 Call Geocoding API: GET "/maps/api/geocode/json?address={address}&key={api_key}"
- [ ] 2.3 Extract lat, lng, formatted_address from response["results"][0]["geometry"]["location"]
- [ ] 2.4 Create GeocodeResult model with fields: latitude, longitude, formatted_address, confidence=0.95
- [ ] 2.5 Add `to_enrichment_dict()` method returning dict for enrichment_data.json integration

### Task 3: Implement Distance Matrix Service (AC: #2, #5)
- [ ] 3.1 Add `calculate_distances(origin_lat: float, origin_lng: float, poi_config: dict) -> DistanceResult | None` method
- [ ] 3.2 Define POI configuration in config: work location (Phoenix downtown), supermarket category, park category
- [ ] 3.3 Call Distance Matrix API: GET "/maps/api/distancematrix/json" with origins and destinations
- [ ] 3.4 Extract distance_meters and duration_seconds for each destination from response["rows"][0]["elements"]
- [ ] 3.5 Create DistanceResult model with fields: work_distance_meters, supermarket_distance_meters, park_distance_meters, confidence=0.95

### Task 4: Implement Places Nearby Search for POIs (AC: #2)
- [ ] 4.1 Add `find_nearest_poi(lat: float, lng: float, place_type: str, radius_meters: int = 5000) -> PlaceResult | None` method
- [ ] 4.2 Call Places API: GET "/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={place_type}"
- [ ] 4.3 Parse response["results"][0] to extract name, location, and distance
- [ ] 4.4 Support place_types: "supermarket", "park" per acceptance criteria
- [ ] 4.5 Return PlaceResult model with name, lat, lng, distance_meters, place_type

### Task 5: Implement Static Maps Satellite Imagery for Orientation (AC: #3)
- [ ] 5.1 Add `fetch_satellite_image(lat: float, lng: float, zoom: int = 20) -> bytes | None` method
- [ ] 5.2 Call Static Maps API: GET "/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size=600x600&maptype=satellite"
- [ ] 5.3 Download satellite image bytes and cache locally in property_images/{address}/satellite.jpg
- [ ] 5.4 Return raw bytes for later AI analysis (orientation determination happens in Phase 2 image assessment)
- [ ] 5.5 Add cost tracking: Static Maps API costs ~$0.002 per image request

### Task 6: Implement Orientation Determination Logic (AC: #3)
- [ ] 6.1 Add `determine_orientation(lat: float, lng: float, satellite_image: bytes | None) -> OrientationResult` method
- [ ] 6.2 **Placeholder implementation**: Extract primary backyard orientation from satellite imagery analysis
- [ ] 6.3 Detect house shape and backyard direction using basic image analysis (or AI vision model in future)
- [ ] 6.4 Map orientation to Arizona-optimized scoring: N=25pts, E=18.75pts, S=12.5pts, W=0pts
- [ ] 6.5 Return OrientationResult model with orientation enum (N/E/S/W), score, confidence=0.70 (lower for image-inferred)

### Task 7: Create Data Models (AC: #7)
- [ ] 7.1 Create `src/phx_home_analysis/services/maps/models.py` with Pydantic models
- [ ] 7.2 Define GeocodeResult: latitude, longitude, formatted_address, confidence, source="google_maps_geocoding"
- [ ] 7.3 Define DistanceResult: work_distance_meters, supermarket_distance_meters, park_distance_meters, confidence, source="google_maps_distance"
- [ ] 7.4 Define PlaceResult: name, lat, lng, distance_meters, place_type, confidence, source="google_maps_places"
- [ ] 7.5 Define OrientationResult: orientation (Enum: N/E/S/W), score_points, confidence, source="google_maps_satellite"
- [ ] 7.6 All models MUST have `to_enrichment_dict()` method matching assessor_client.py pattern

### Task 8: Integrate with Enrichment Data Schema (AC: #7)
- [ ] 8.1 Add `geographic_data` section to enrichment_data.json schema
- [ ] 8.2 Store geocode results: latitude, longitude, formatted_address, geocode_confidence
- [ ] 8.3 Store distance results: work_distance_meters, supermarket_distance_meters, park_distance_meters
- [ ] 8.4 Store orientation results: backyard_orientation (N/E/S/W), orientation_score, orientation_confidence
- [ ] 8.5 Add provenance metadata: source="google_maps", fetched_at timestamp, api_cost_usd

### Task 9: Add API Cost Tracking (AC: #5)
- [ ] 9.1 Track API costs per request type: geocode=$0.005, distance=$0.005, places=$0.032, static_map=$0.002
- [ ] 9.2 Log cumulative costs to enrichment_data.json in api_costs section
- [ ] 9.3 Calculate total Google Maps cost per property: ~$0.05-0.10 depending on requests
- [ ] 9.4 Add cache hit/miss tracking to reduce repeat API calls
- [ ] 9.5 Report cost savings from cache hits in logs

### Task 10: Write Mocked Integration Tests (AC: #1-8)
- [ ] 10.1 Create `tests/unit/services/maps/test_google_maps_client.py`
- [ ] 10.2 Mock geocoding response with sample lat/lng/formatted_address
- [ ] 10.3 Mock distance matrix response with work/supermarket/park distances
- [ ] 10.4 Mock places nearby response with nearest POI results
- [ ] 10.5 Mock static map response with sample satellite image bytes
- [ ] 10.6 Verify orientation scoring: N=25, E=18.75, S=12.5, W=0
- [ ] 10.7 Verify provenance: all results have confidence=0.95, source="google_maps_*"
- [ ] 10.8 Verify cache behavior: second request uses cache, no API call
- [ ] 10.9 Verify rate limiting: 50 requests within 60 seconds triggers throttling
- [ ] 10.10 Verify error handling: API failure returns None, does not raise exception

## Dev Notes

### Arizona-Specific Orientation Context

**Critical**: Orientation scoring is Arizona-optimized for extreme heat management:

- **North (25pts)**: Best orientation - backyard shaded in afternoon, minimizes AC costs and pool heating
- **East (18.75pts)**: Good - morning sun only, cooler afternoons
- **South (12.5pts)**: Moderate - all-day sun exposure, higher cooling costs
- **West (0pts)**: Worst - intense 3-7pm sun during peak heat (110°F+), highest AC costs, unusable backyard afternoons

This is NOT a cardinal direction preference - it's a climate-specific thermal comfort optimization. Buyers in Arizona specifically avoid west-facing backyards.

### Google Maps API Usage & Costs

**API Costs (per property):**
- Geocoding API: $0.005 per request
- Distance Matrix API: $0.005 per element (3 elements = $0.015)
- Places Nearby Search: $0.032 per request (2 calls for supermarket + park = $0.064)
- Static Maps API: $0.002 per request
- **Total per property**: ~$0.086 (within $0.05-0.10 budget per acceptance criteria)

**Rate Limits:**
- Free tier: No daily limit, but burst limit of 50 requests/second
- Recommended: Configure RateLimit(requests_per_second=0.83) for safety margin
- Cache aggressively: 7-day TTL prevents re-requesting same data

**Required Environment Variable:**
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here  # From Google Cloud Console
```

### Existing Code Patterns (MUST Follow)

**API Client Pattern** (from `assessor_client.py` and `base_client.py`):

```python
from phx_home_analysis.services.api_client import APIClient, RateLimit

class GoogleMapsClient(APIClient):
    def __init__(self):
        super().__init__(
            service_name="google_maps",
            base_url="https://maps.googleapis.com",
            env_key="GOOGLE_MAPS_API_KEY",  # API key auth (query param)
            rate_limit=RateLimit(requests_per_second=0.83),  # 50/60s burst limit
            cache_ttl_days=7,
            timeout=30.0,
        )

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        """Geocode address to lat/lng. Returns None on failure."""
        try:
            data = await self.get(
                "/maps/api/geocode/json",
                params={"address": address}
            )
            if data.get("status") != "OK":
                return None

            result = data["results"][0]
            location = result["geometry"]["location"]

            return GeocodeResult(
                latitude=location["lat"],
                longitude=location["lng"],
                formatted_address=result["formatted_address"],
                confidence=0.95,
                source="google_maps_geocoding",
            )
        except Exception:
            return None  # Never raise, return None per pattern
```

**Model with to_enrichment_dict()** (from `assessor_client.py:425-442`):

```python
from pydantic import BaseModel

class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    confidence: float = 0.95
    source: str = "google_maps_geocoding"

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "formatted_address": self.formatted_address,
            "geocode_confidence": self.confidence,
            "geocode_source": self.source,
        }
```

**Error Handling Pattern** (never raise, return None):
```python
async def some_api_method(self, param: str) -> Result | None:
    try:
        data = await self.get("/endpoint", params={"q": param})
        return self._parse_response(data)
    except Exception as e:
        logger.debug(f"API call failed: {e}")
        return None  # Pipeline continues with missing data
```

### Project Structure Notes

**Files to Create:**
```
src/phx_home_analysis/services/maps/
├── __init__.py              # Exports GoogleMapsClient
├── client.py                # Main API client extending APIClient
├── models.py                # Pydantic models (GeocodeResult, DistanceResult, etc.)
└── CLAUDE.md                # Module documentation

tests/unit/services/maps/
├── __init__.py
└── test_google_maps_client.py  # Mocked integration tests
```

**Files to Modify:**
- `data/enrichment_data.json` schema - add `geographic_data` section
- `src/phx_home_analysis/services/__init__.py` - export GoogleMapsClient

### Architecture Compliance

**Per Integration Architecture (docs/architecture/integration-architecture.md:1-57):**
- Use APIClient base class from `services/api_client/base_client.py`
- Implement rate limiting via RateLimit configuration
- Enable response caching with 7-day TTL
- Track API costs in logs and enrichment data
- Return None on errors, never raise exceptions to pipeline

**Per Data Architecture (ADR-02):**
- Store geographic data in enrichment_data.json LIST format
- Use atomic writes for enrichment updates
- Include provenance metadata: source, confidence, fetched_at

**Per Security Architecture:**
- Load GOOGLE_MAPS_API_KEY from environment, never hardcode
- Use base_client's credential redaction in error messages
- Never log API keys in error messages or stack traces

### Technical Requirements

**Dependencies:**
- `httpx` - HTTP client (already in use)
- `pydantic` - Data validation (already in use)
- Base APIClient from `src/phx_home_analysis/services/api_client/`

**Google Maps APIs Required:**
1. **Geocoding API**: Address → lat/lng
2. **Distance Matrix API**: Origin/destination distances
3. **Places API**: Nearby POI search (supermarket, park)
4. **Static Maps API**: Satellite imagery download

**Configuration:**
- Environment: `GOOGLE_MAPS_API_KEY` (required)
- Rate limit: 0.83 requests/second (50/60s burst limit with margin)
- Cache: 7-day TTL in `data/api_cache/google_maps/`
- Timeout: 30 seconds per request

**Orientation Determination Approach:**

**Phase 1 (This Story - Simple Heuristic):**
- Fetch satellite image via Static Maps API
- Store image bytes for later AI analysis
- **Placeholder**: Return default orientation based on lat/lng or manual config
- Use lower confidence (0.70) since this is not AI-inferred yet

**Phase 2 (Future - AI Vision):**
- Use Claude Vision or GPT-4 Vision to analyze satellite image
- Detect house footprint and backyard direction
- Determine primary sun exposure direction
- Upgrade confidence to 0.90+ with AI inference

For this story, we implement the foundation (API calls, image storage) and use a placeholder heuristic. Full AI vision analysis can be added in Epic 6 (Visual Analysis).

### Data Schema Integration

**Add to enrichment_data.json:**

```json
{
  "full_address": "123 Main St, Phoenix, AZ 85001",
  "geographic_data": {
    "latitude": 33.4484,
    "longitude": -112.0740,
    "formatted_address": "123 Main St, Phoenix, AZ 85001, USA",
    "geocode_confidence": 0.95,
    "geocode_source": "google_maps_geocoding",
    "work_distance_meters": 8500,
    "supermarket_distance_meters": 1200,
    "park_distance_meters": 800,
    "distance_confidence": 0.95,
    "distance_source": "google_maps_distance",
    "backyard_orientation": "N",
    "orientation_score": 25.0,
    "orientation_confidence": 0.70,
    "orientation_source": "google_maps_satellite_heuristic",
    "fetched_at": "2025-12-04T10:30:00Z",
    "api_cost_usd": 0.086
  }
}
```

### References

- [Source: docs/epics/epic-2-property-data-acquisition.md:66-77] - E2.S5 story requirements
- [Source: docs/architecture/integration-architecture.md:1-57] - API integration patterns
- [Source: src/phx_home_analysis/services/county_data/assessor_client.py:1-683] - Reference API client pattern
- [Source: src/phx_home_analysis/services/api_client/base_client.py:1-412] - APIClient base class
- [Source: docs/sprint-artifacts/stories/E2-S1-batch-analysis-cli.md] - Previous story (E2-S1) patterns
- [Source: .claude/skills/arizona-context/SKILL.md] - Arizona orientation scoring rationale
- [Source: docs/architecture/integration-architecture.md:46-54] - API cost estimation

## Dev Agent Record

### Context Reference

- Epic context: `docs/epics/epic-2-property-data-acquisition.md`
- Architecture: `docs/architecture/integration-architecture.md`
- API client base: `src/phx_home_analysis/services/api_client/base_client.py`
- Reference pattern: `src/phx_home_analysis/services/county_data/assessor_client.py`
- Arizona context: `.claude/skills/arizona-context/SKILL.md`

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- **Story context created**: 2025-12-04
- **Ultimate context engine**: Comprehensive developer guide with all patterns, costs, and Arizona-specific requirements
- **Dependency**: Requires E2.S7 (API Integration Infrastructure) completed for APIClient base class
- **Cost optimization**: 7-day cache TTL critical to stay within $0.05-0.10 per property budget
- **Orientation placeholder**: Initial heuristic implementation; AI vision upgrade deferred to Epic 6

### File List

**To be created:**
- `src/phx_home_analysis/services/maps/__init__.py`
- `src/phx_home_analysis/services/maps/client.py`
- `src/phx_home_analysis/services/maps/models.py`
- `src/phx_home_analysis/services/maps/CLAUDE.md`
- `tests/unit/services/maps/test_google_maps_client.py`

### Previous Story Intelligence

**From E2-S1 (Batch Analysis CLI):**
- Typer CLI patterns established for entry points
- Rich progress display patterns
- --dry-run and --json flags patterns for testing
- CSV validation with row-level error reporting
- Rolling ETA calculation (last 5 samples)

**From E2-S7 (API Integration Infrastructure):**
- APIClient base class with auth, rate limiting, caching, retry
- RateLimit configuration with proactive throttling at 80% threshold
- ResponseCache with SHA256 keys and 7-day TTL
- Error handling: return None on failures, never raise to pipeline
- Credential redaction in error messages

**From Epic 1 Learnings:**
- Pydantic models for data validation
- Atomic JSON writes for enrichment_data.json
- Provenance tracking with confidence scores and source metadata
- Test patterns in `tests/unit/` hierarchy

## Definition of Done Checklist

- [ ] GoogleMapsClient extending APIClient base class
- [ ] Geocoding with caching and provenance (AC#1, AC#7)
- [ ] Distance calculations to work, supermarket, park (AC#2)
- [ ] Orientation determination with Arizona scoring (AC#3)
- [ ] Cache-first pattern with 7-day TTL (AC#4)
- [ ] API cost tracking at ~$0.05-0.10 per property (AC#5)
- [ ] Rate limiting configured per E2.S7 infrastructure (AC#6)
- [ ] Error handling returns None, never raises (AC#8)
- [ ] Pydantic models with to_enrichment_dict() methods
- [ ] Integration with enrichment_data.json schema
- [ ] Mocked integration tests passing (all 10 test scenarios)
- [ ] CLAUDE.md documentation for maps/ service
- [ ] Cache hit/miss stats logging enabled

---

**🎯 Implementation Ready**: This story provides the complete implementation guide for Google Maps API integration. All patterns, costs, schemas, and Arizona-specific requirements documented. Developer has everything needed for flawless execution.

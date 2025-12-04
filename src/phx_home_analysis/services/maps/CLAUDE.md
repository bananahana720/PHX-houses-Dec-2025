---
last_updated: 2025-12-04
updated_by: dev-agent
staleness_hours: 168
flags: []
---
# maps

## Purpose

Google Maps API integration for property geographic data extraction including geocoding, distance calculations, POI search, and backyard orientation determination with Arizona-optimized scoring.

## Contents

| Path | Purpose |
|------|---------|
| `client.py` | GoogleMapsClient extending APIClient; geocode, distance, places, satellite imagery |
| `models.py` | Pydantic models (GeocodeResult, DistanceResult, PlaceResult, OrientationResult) |
| `__init__.py` | Module exports |

## Public Interface

### GoogleMapsClient

**Methods:**
- `geocode_address(address: str) -> GeocodeResult | None` - Address → lat/lng ($0.005/request)
- `calculate_distances(origin_lat, origin_lng) -> DistanceResult | None` - Work/supermarket/park distances ($0.079/request)
- `find_nearest_poi(lat, lng, place_type, radius=5000) -> PlaceResult | None` - Nearest POI search ($0.032/request)
- `fetch_satellite_image(lat, lng, zoom=20) -> bytes | None` - Satellite imagery download ($0.002/request)
- `determine_orientation(lat, lng) -> OrientationResult | None` - Backyard orientation with AZ scoring (placeholder heuristic)

**Configuration:**
- Base URL: `https://maps.googleapis.com`
- Rate limit: 0.83 req/sec (50/60s burst limit with margin)
- Cache: 7-day TTL in `data/api_cache/google_maps/`
- Timeout: 30 seconds
- Auth: `GOOGLE_MAPS_API_KEY` environment variable

**Cost per property:** ~$0.086 (geocode + distance + 2× places + satellite)

### Models

All models include `to_enrichment_dict()` for `enrichment_data.json` integration.

**GeocodeResult:**
- Fields: latitude, longitude, formatted_address, confidence=0.95, source
- Enrichment keys: latitude, longitude, formatted_address, geocode_confidence, geocode_source

**DistanceResult:**
- Fields: work_distance_meters, supermarket_distance_meters, park_distance_meters, confidence=0.95, source
- Enrichment keys: work_distance_meters, supermarket_distance_meters, park_distance_meters, distance_confidence, distance_source

**PlaceResult:**
- Fields: name, latitude, longitude, distance_meters, place_type, confidence=0.95, source
- Enrichment keys: {place_type}_name, {place_type}_distance_meters, {place_type}_lat, {place_type}_lng

**OrientationResult:**
- Fields: orientation (Enum: N/E/S/W), score_points (0-25), confidence=0.70, source
- Enrichment keys: backyard_orientation, orientation_score, orientation_confidence, orientation_source

**Orientation Enum:**
- NORTH = "N" → 25pts (best - minimizes afternoon sun)
- EAST = "E" → 18.75pts (good - morning sun only)
- SOUTH = "S" → 12.5pts (moderate - all-day sun)
- WEST = "W" → 0pts (worst - intense afternoon heat in AZ)

## Tasks

- [x] Implement GoogleMapsClient extending APIClient
- [x] Implement Pydantic models with to_enrichment_dict()
- [x] Add geocoding with 7-day cache
- [x] Add distance calculations (work + POI)
- [x] Add Places API nearby search
- [x] Add Static Maps satellite imagery
- [x] Add orientation placeholder (heuristic)
- [ ] Upgrade orientation to AI vision analysis (Claude/GPT-4) P:M
- [ ] Add cost tracking metadata to enrichment_data.json P:L

## Learnings

- **Arizona orientation scoring:** Not cardinal direction preference, but climate-specific thermal comfort optimization (N best, W worst)
- **Cache-first pattern:** 7-day TTL critical to stay within $0.05-0.10/property budget
- **Error handling:** All methods return None on failure, never raise exceptions to pipeline
- **Provenance tracking:** All models include confidence=0.95 (except orientation=0.70 for heuristic) and source metadata
- **Haversine distance:** Used for POI distance calculation when not provided by API

## Refs

- API client base: `src/phx_home_analysis/services/api_client/base_client.py:1-412`
- Rate limiting: `src/phx_home_analysis/services/api_client/rate_limiter.py:1-233`
- Arizona context: `.claude/skills/arizona-context/SKILL.md`
- Story: `docs/sprint-artifacts/stories/E2-S5-google-maps-geographic.md`

## Deps

← Imports from:
  - `phx_home_analysis.services.api_client` (APIClient, RateLimit)
  - `pydantic` (BaseModel, Field)
  - `enum` (Enum)
  - `pathlib` (Path)
  - `math` (haversine calculation)

→ Imported by:
  - Pipeline orchestrator (Phase 1: geographic data extraction)
  - Property enrichment services
  - Tests: `tests/unit/services/maps/test_google_maps_client.py`

# Data Source Integration Architecture

**Last Updated:** 2025-12-07
**Status:** Planning - Wave 1 Complete, Implementation Pending
**Owner:** PHX Houses Pipeline

## Executive Summary

This document defines the integration architecture for 5 external data sources (OpenStreetMap, Google Places API, Google Air Quality API, SchoolDigger API, Census Bureau ACS) into the PHX Houses analysis pipeline. The architecture extends the existing `APIClient` base class pattern and integrates with the current enrichment data schema.

**Key Metrics:**
- **Cost Estimate:** $3.70/100 properties (Phase 1 only)
- **Latency:** <5 seconds per property (parallel requests)
- **Cache Hit Rate Target:** 80% after initial warmup
- **Rate Limit Compliance:** 100% (proactive throttling at 80%)

---

## 1. Integration Priority Matrix

### Phase 1: Completed
**Priority 1 - High ROI, Low Cost**

| API | Priority | Impact | Cost/100 Props | Rationale |
|-----|----------|--------|----------------|-----------|
| **SchoolDigger** | HIGH | Location scoring (up to 80/250 pts) | $0 (free tier) | ✅ COMPLETED: Implemented via RapidAPI integration; enhances school rating accuracy; 30-day cache TTL minimizes API calls |
| **Google Places** | HIGH | Proximity scoring (up to 50/250 pts) | $3.20 | Critical for grocery/highway distances; used as SchoolDigger fallback; high cache efficiency |

**Phase 1 Total Cost:** $3.20/100 properties
**Expected Benefits:**
- SchoolDigger: 95% confidence school ratings vs 50% Google fallback
- Google Places: Accurate POI distances for location scoring (grocery, highway, amenities)

### Phase 2: Next Sprint
**Priority 2 - Medium ROI, Low Cost**

| API | Priority | Impact | Cost/100 Props | Rationale |
|-----|----------|--------|----------------|-----------|
| **Census ACS** | MEDIUM | Demographics for area quality analysis | $0 (free) | Tract-level income/population enhances location scoring; annual updates sufficient |
| **Google Air Quality** | MEDIUM | Environmental quality scoring | $0.50 | Low cost; health-conscious buyers value AQI data; cache per ZIP reduces cost |

**Phase 2 Total Cost:** $0.50/100 properties
**Expected Benefits:**
- Census: Demographic indicators for neighborhood quality assessment
- Air Quality: Environmental health scoring (AQI) for location section

### Phase 3: Backlog
**Priority 3 - High Setup Cost, Long-term Value**

| API | Priority | Impact | Cost/100 Props | Rationale |
|-----|----------|--------|----------------|-----------|
| **OpenStreetMap** | LOW | Local POI processing (offline) | $0 (one-time setup) | 270MB Arizona extract requires osmium tooling; deferred until scale justifies infrastructure |

**Phase 3 Benefits:**
- Zero recurring cost (offline processing)
- Full control over POI data
- Requires: osmium setup, pyosmium integration, periodic PBF updates

---

## 2. Client Architecture

### Base Client Pattern (Existing)

The project already implements a robust `APIClient` base class with:
- Authentication via environment variables (API key or Bearer token)
- Proactive rate limiting at 80% threshold
- Response caching with configurable TTL (SHA256 keys)
- Automatic retry with exponential backoff (5 retries, 1-60s delay)
- Retry-After header support for 429 responses
- Credential redaction in logs

**Reference:** `src/phx_home_analysis/services/api_client/base_client.py`

### New Client Implementations

#### 2.1 Google Places Client

```python
"""Google Places API client for POI proximity scoring."""

from phx_home_analysis.services.api_client import APIClient, RateLimit

GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"

class GooglePlacesClient(APIClient):
    """Google Places API v1 client for nearby POI search.

    Rate Limits:
        - 6000 QPM (100 requests/second)
        - Configured at 80 req/sec for safety margin

    Cost:
        - $0.032 per searchNearby request
        - Cache TTL: 30 days (POI locations rarely change)

    Example:
        async with GooglePlacesClient() as client:
            result = await client.search_nearby(
                lat=33.4484,
                lng=-112.0740,
                included_types=["grocery_store"],
                radius_meters=8046  # 5 miles
            )
    """

    def __init__(self) -> None:
        super().__init__(
            service_name="google_places",
            base_url=GOOGLE_PLACES_BASE_URL,
            env_key="GOOGLE_MAPS_API_KEY",  # Reuse existing key
            rate_limit=RateLimit(requests_per_second=80.0),  # 80% of 100/s limit
            cache_ttl_days=30,
            timeout=30.0,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build headers with X-Goog-FieldMask for optimized responses."""
        headers = super()._build_headers()
        # Field mask reduces response size and cost
        headers["X-Goog-FieldMask"] = "places.displayName,places.location"
        return headers

    async def search_nearby(
        self,
        lat: float,
        lng: float,
        included_types: list[str],
        radius_meters: int = 8046,  # 5 miles default
        max_results: int = 10,
    ) -> list[dict]:
        """Search for nearby places by type.

        Args:
            lat: Property latitude
            lng: Property longitude
            included_types: Place types (e.g., ["grocery_store", "gas_station"])
                           See: https://developers.google.com/maps/documentation/places/web-service/place-types
            radius_meters: Search radius (default 5 miles)
            max_results: Maximum results to return (default 10)

        Returns:
            List of place dicts with displayName, location
        """
        data = await self.post(
            "/places:searchNearby",
            json_data={
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lng},
                        "radius": radius_meters,
                    }
                },
                "includedTypes": included_types,
                "maxResultCount": max_results,
            },
        )

        return data.get("places", [])
```

#### 2.2 Google Air Quality Client

```python
"""Google Air Quality API client for environmental scoring."""

from phx_home_analysis.services.api_client import APIClient, RateLimit

AIR_QUALITY_BASE_URL = "https://airquality.googleapis.com/v1"

class AirQualityClient(APIClient):
    """Google Air Quality API client for current AQI conditions.

    Rate Limits:
        - 100 QPM (1.67 requests/second)
        - Configured at 1.3 req/sec for safety margin

    Cost:
        - $0.005 per currentConditions:lookup request
        - Cache strategy: Per-ZIP, 1-day TTL (AQI changes daily)

    Example:
        async with AirQualityClient() as client:
            aqi = await client.get_current_aqi(lat=33.4484, lng=-112.0740)
            # Returns: {"aqi": 45, "category": "Good", "dominant_pollutant": "pm25"}
    """

    def __init__(self) -> None:
        super().__init__(
            service_name="google_air_quality",
            base_url=AIR_QUALITY_BASE_URL,
            env_key="GOOGLE_MAPS_API_KEY",  # Same key as Places/Maps
            rate_limit=RateLimit(requests_per_second=1.3),  # 80% of 1.67/s limit
            cache_ttl_days=1,  # AQI changes daily
            timeout=30.0,
        )

    async def get_current_aqi(self, lat: float, lng: float) -> dict | None:
        """Get current air quality index for coordinates.

        Args:
            lat: Property latitude
            lng: Property longitude

        Returns:
            Dict with aqi (int), category (str), dominant_pollutant (str),
            or None on failure
        """
        try:
            data = await self.post(
                "/currentConditions:lookup",
                json_data={
                    "location": {"latitude": lat, "longitude": lng},
                },
            )

            indexes = data.get("indexes", [])
            if not indexes:
                return None

            # Use first index (typically US AQI)
            index = indexes[0]
            return {
                "aqi": index.get("aqi"),
                "category": index.get("category"),
                "dominant_pollutant": index.get("dominantPollutant"),
            }

        except Exception:
            return None  # Graceful degradation
```

#### 2.3 Census Bureau ACS Client

```python
"""Census Bureau American Community Survey (ACS) client."""

from phx_home_analysis.services.api_client import APIClient, RateLimit

CENSUS_BASE_URL = "https://api.census.gov/data/2022/acs/acs5"

class CensusACSClient(APIClient):
    """Census Bureau ACS 5-year estimates client.

    Rate Limits:
        - No official limit, but recommended <100 req/sec
        - Configured at 10 req/sec for courtesy

    Cost:
        - FREE with API key
        - Cache: 365-day TTL (annual updates)

    Data:
        - Tract-level demographics, income, population
        - Variables: B19013_001E (median household income)
                     B01003_001E (total population)

    Example:
        async with CensusACSClient() as client:
            data = await client.get_tract_data(
                state="04",  # Arizona
                county="013",  # Maricopa
                tract="123456"
            )
    """

    def __init__(self) -> None:
        super().__init__(
            service_name="census_acs",
            base_url=CENSUS_BASE_URL,
            env_key="CENSUS_API_KEY",
            rate_limit=RateLimit(requests_per_second=10.0),
            cache_ttl_days=365,  # Annual updates
            timeout=30.0,
        )

    async def get_tract_data(
        self,
        state: str,
        county: str,
        tract: str,
        variables: list[str] | None = None,
    ) -> dict | None:
        """Get ACS data for census tract.

        Args:
            state: 2-digit state FIPS (04 for Arizona)
            county: 3-digit county FIPS (013 for Maricopa)
            tract: 6-digit tract code
            variables: List of ACS variables (default: income, population)

        Returns:
            Dict with variable values, or None on failure
        """
        if variables is None:
            variables = [
                "B19013_001E",  # Median household income
                "B01003_001E",  # Total population
            ]

        params = {
            "get": ",".join(variables),
            "for": f"tract:{tract}",
            "in": f"state:{state} county:{county}",
        }

        data = await self.get("", params=params)

        if not data or len(data) < 2:
            return None

        # Data format: [["NAME", "B19013_001E", ...], ["tract name", "value", ...]]
        headers = data[0]
        values = data[1]

        return dict(zip(headers, values, strict=True))
```

### Circuit Breaker Integration

**Status:** PLANNED for Phase 3 (not currently implemented)

The existing `retry_with_backoff` decorator provides sufficient protection for Phase 1-2 operations via exponential backoff and max retries. For enhanced reliability in future phases, a full circuit breaker pattern can be implemented in the orchestration layer.

**Reference:** See ADR-10 (Pipeline & Orchestration Patterns) for detailed retry and resilience strategies.

**Proposed implementation for Phase 3:**

```python
"""Circuit breaker pattern for API resilience."""

from datetime import datetime, timedelta
from typing import Callable, TypeVar

T = TypeVar("T")

class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    States:
        - CLOSED: Normal operation
        - OPEN: Too many failures, reject requests
        - HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        result = await breaker.call(lambda: client.get_schools(lat, lng))
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_max_calls = half_open_max_calls

        self._failures = 0
        self._state = "CLOSED"
        self._opened_at: datetime | None = None
        self._half_open_calls = 0

    async def call(self, func: Callable[[], T]) -> T:
        """Execute function with circuit breaker protection."""
        if self._state == "OPEN":
            if datetime.now() - self._opened_at > self.timeout:
                self._state = "HALF_OPEN"
                self._half_open_calls = 0
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")

        if self._state == "HALF_OPEN":
            if self._half_open_calls >= self.half_open_max_calls:
                raise Exception(f"Circuit breaker HALF_OPEN limit reached")

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            self._failures = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failures += 1

        if self._failures >= self.failure_threshold:
            self._state = "OPEN"
            self._opened_at = datetime.now()
```

---

## 3. Data Flow Diagrams

### 3.1 API Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Property Address Input                   │
│                      (lat, lng from CSV)                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Parallel API Requests                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ SchoolDigger │  │Google Places │  │  Air Quality │      │
│  │  (30d cache) │  │  (30d cache) │  │  (1d cache)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    APIClient Base Class                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Cache Lookup (SHA256 key: URL + params)          │   │
│  │    └─> HIT: Return cached JSON                       │   │
│  │    └─> MISS: Continue to step 2                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Rate Limiter (Token Bucket, 80% threshold)        │   │
│  │    └─> Acquire token or wait                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. HTTP Request (httpx.AsyncClient)                  │   │
│  │    └─> Auth: API key (header/param) or Bearer token  │   │
│  │    └─> Retry: Exponential backoff (5x, 1-60s)        │   │
│  │    └─> 429 Handling: Respect Retry-After header      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Cache Write (Atomic: tempfile + os.replace)       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Response Transformers                       │
│  - SchoolDigger → AssignedSchoolsResult                     │
│  - Google Places → POI distances (meters)                   │
│  - Air Quality → AQI category (Good/Moderate/Unhealthy)     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              enrichment_data.json Update                     │
│  [                                                           │
│    {                                                         │
│      "full_address": "123 Main St, Phoenix, AZ",            │
│      "school_rating": 8.1,  // SchoolDigger composite       │
│      "distance_to_grocery_miles": 0.8,  // Google Places    │
│      "air_quality_index": 45,  // Air Quality API           │
│      "api_cost_total_usd": 0.037,  // Cumulative API costs  │
│      "api_calls_made": 3,  // Total API calls for property  │
│      "api_last_fetch_at": "2025-12-07T10:30:00Z",  // ISO   │
│      ...                                                     │
│    }                                                         │
│  ]                                                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Cost Tracking Metadata Fields

**Schema Addition to `enrichment_data.json`:**

Each property record tracks API usage for cost monitoring and cache efficiency analysis:

```yaml
# Cost tracking fields (added to each property in enrichment_data.json)
api_cost_total_usd: float | None     # Cumulative API cost for this property
                                      # Incremented on each API call
                                      # Example: 0.037 (1 Places + 1 AQI call)

api_calls_made: int | None           # Total API calls made for this property
                                      # Tracks cache miss count
                                      # Example: 3 (SchoolDigger, Places, AQI)

api_last_fetch_at: str | None        # ISO 8601 timestamp of last API call
                                      # Used for cache invalidation logic
                                      # Example: "2025-12-07T10:30:00Z"
```

**Usage Example:**
```python
# After successful API call
property_data["api_cost_total_usd"] = (property_data.get("api_cost_total_usd", 0.0) + 0.032)
property_data["api_calls_made"] = (property_data.get("api_calls_made", 0) + 1)
property_data["api_last_fetch_at"] = datetime.utcnow().isoformat() + "Z"
```

**Monitoring Requirements:**
- Track aggregate costs: `sum(api_cost_total_usd)` across all properties
- Monitor cache hit rate: `1 - (api_calls_made / expected_calls_without_cache)`
- Alert if actual costs exceed budgeted costs by >20%
- Validate 90% cache hit rate assumption (see Section 6 for budget impact)

**Reference:** See `docs/specs/schema-evolution-plan.md` for complete field definitions and migration procedures.

### 3.2 Cache Hit Rate Monitoring

**Assumption:** 90% cache hit rate after initial warmup period (30 days)

**Validation Required:** The cost estimates in Section 6 assume a 90% cache hit rate. This assumption MUST be validated through monitoring once the system is operational.

**Metrics to Track:**
```python
cache_metrics = {
    "cache_hits": 0,           # Requests served from cache
    "cache_misses": 0,         # Requests requiring API calls
    "cache_hit_rate": 0.0,     # cache_hits / (cache_hits + cache_misses)
}
```

**Monitoring Implementation:**
- Log cache hit/miss on every API request
- Calculate daily/weekly cache hit rates
- Alert if cache hit rate drops below 80% (indicates cache TTL issues or new properties)
- Adjust cost budgets if sustained hit rate differs from 90% assumption

**Impact of Cache Hit Rate on Costs:**
| Hit Rate | Cost/100 Props (Phase 1) | Cost/100 Props (Phase 1+2) | Monthly (3K props) |
|----------|--------------------------|----------------------------|-------------------|
| 70% | $0.96 | $1.11 | $33.30 |
| 80% | $0.64 | $0.74 | $22.20 |
| 90% | $0.32 | $0.37 | $11.10 |
| 95% | $0.16 | $0.19 | $5.55 |

**Action Thresholds:**
- Hit rate <80%: Investigate cache TTL settings, consider increasing TTLs
- Hit rate <70%: STOP THE LINE - Review caching strategy, costs may exceed budget

### 3.3 Caching Strategy

**Cache Directory Structure:**
```
data/api_cache/
├── schooldigger/
│   ├── cache_stats.json
│   └── <sha256_hash>.json  # 30-day TTL
├── google_places/
│   ├── cache_stats.json
│   └── <sha256_hash>.json  # 30-day TTL
├── google_air_quality/
│   ├── cache_stats.json
│   └── <sha256_hash>.json  # 1-day TTL
└── census_acs/
    ├── cache_stats.json
    └── <sha256_hash>.json  # 365-day TTL
```

**Cache Key Generation:**
```python
# Example cache key for Google Places searchNearby
url = "https://places.googleapis.com/v1/places:searchNearby"
params = {
    "locationRestriction.circle.center.latitude": 33.4484,
    "locationRestriction.circle.center.longitude": -112.0740,
    "includedTypes": ["grocery_store"],
    "radius": 8046,
}

# SHA256(url + sorted params) = cache filename
# API key NOT included in cache key (security)
cache_key = "a3f8b92c...4d1e.json"
```

**Refresh Policies:**

| API | TTL | Rationale | Refresh Trigger |
|-----|-----|-----------|-----------------|
| SchoolDigger | 30 days | School ratings change annually | Manual or annual batch |
| Google Places | 30 days | POI locations stable | Manual or quarterly |
| Air Quality | 1 day | AQI fluctuates daily | Daily batch or on-demand |
| Census ACS | 365 days | Annual updates | Manual after Census release |

**Cache Warming Strategy:**
```python
"""Pre-warm cache for known ZIP codes before batch processing."""

async def warm_cache_for_zip(zip_code: str, clients: dict) -> None:
    """Pre-fetch data for all properties in ZIP code.

    Benefits:
        - Reduces latency during actual property analysis
        - Amortizes API costs across multiple properties
        - Identifies API issues before production run
    """
    # Get all properties in ZIP
    properties = get_properties_by_zip(zip_code)

    # Batch fetch with concurrency limit
    async with clients["places"] as places_client:
        tasks = [
            places_client.search_nearby(
                lat=prop.latitude,
                lng=prop.longitude,
                included_types=["grocery_store"],
            )
            for prop in properties
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 4. API Key Management

### Environment Variables

**Required Additions to `.env`:**
```bash
# Google APIs (shared key for Places, Air Quality, Maps)
GOOGLE_MAPS_API_KEY=your_key_here

# SchoolDigger (RapidAPI)
SCHOOLDIGGER_API_KEY=your_rapidapi_key_here

# Census Bureau (free)
CENSUS_API_KEY=your_census_key_here
```

**Validation on Startup:**
```python
"""Validate all required API keys before pipeline execution."""

import os
import sys

REQUIRED_KEYS = {
    "GOOGLE_MAPS_API_KEY": "Google Places/Air Quality/Maps API",
    "SCHOOLDIGGER_API_KEY": "SchoolDigger via RapidAPI",
    "CENSUS_API_KEY": "Census Bureau ACS API",
}

def validate_api_keys() -> list[str]:
    """Validate all required API keys are present.

    Returns:
        List of missing API keys (empty list if all keys present).

    Raises:
        SystemExit: If any required keys are missing.
    """
    missing = []

    for key, service in REQUIRED_KEYS.items():
        if not os.getenv(key):
            missing.append(f"  - {key} ({service})")

    if missing:
        print("ERROR: Missing required API keys:")
        print("\n".join(missing))
        print("\nAdd these to your .env file.")
        sys.exit(1)

    return missing
```

**Integration Point:**
Call `validate_api_keys()` in pipeline startup scripts (e.g., `scripts/analyze_properties.py`, orchestration layer) before any API clients are instantiated.

### Secret Rotation

**Google API Keys:**
- Rotation frequency: Every 90 days (recommended)
- Process:
  1. Generate new key in Google Cloud Console
  2. Update `.env` with new key
  3. Test with sample property
  4. Delete old key after 24-hour grace period

**SchoolDigger (RapidAPI):**
- Rotation: Not required (subscription-based)
- Monitoring: Check RapidAPI dashboard for usage

**Census Bureau:**
- Rotation: Not required (low security risk, free tier)

### Cost Monitoring Alerts

**Budget Thresholds:**
```python
"""Cost monitoring for API usage."""

COST_THRESHOLDS = {
    "google_places": {
        "daily_limit": 100,  # $3.20/day max
        "monthly_budget": 96.00,  # $96/month = ~3000 properties
        "alert_percent": 80,  # Alert at 80% budget
    },
    "google_air_quality": {
        "daily_limit": 100,
        "monthly_budget": 15.00,  # $15/month
        "alert_percent": 80,
    },
}

async def check_api_budget(service_name: str, client: APIClient) -> None:
    """Alert if API usage exceeds budget threshold."""
    stats = client.get_rate_limit_stats()
    threshold = COST_THRESHOLDS[service_name]

    daily_requests = stats["requests_today"]
    if daily_requests > threshold["daily_limit"]:
        logger.warning(
            f"{service_name} exceeded daily limit: "
            f"{daily_requests}/{threshold['daily_limit']}"
        )
```

**Google Cloud Billing Alerts:**
- Set budget alerts in Google Cloud Console
- Alert at: $50, $75, $100 (50%, 75%, 100% of monthly budget)
- Webhook integration for automated alerts

---

## 5. Error Handling

### Error Classification by API

#### 5.1 SchoolDigger (RapidAPI)

**Transient Errors (Retry):**
- 429 Too Many Requests (respect Retry-After header)
- 500/502/503 Server errors
- Network timeouts

**Permanent Errors (Fail Gracefully):**
- 401 Unauthorized (invalid API key)
- 403 Forbidden (subscription expired)
- 404 Not Found (no schools in area)

**Fallback Strategy:**
```python
async def get_schools_with_fallback(lat: float, lng: float):
    """Get school data with Google Places fallback."""
    try:
        async with SchoolRatingsClient() as client:
            result = await client.get_assigned_schools(lat, lng)
            if result:
                return result
    except Exception as e:
        logger.warning(f"SchoolDigger failed: {e}, trying Google Places")

    # Fallback to Google Places (lower confidence)
    async with SchoolRatingsClient() as client:
        return await client._fallback_to_google_places(lat, lng)
```

#### 5.2 Google Places API

**Transient Errors (Retry):**
- 429 Resource Exhausted (QPM limit)
- 500/503 Server errors
- Network timeouts

**Permanent Errors (Fail Gracefully):**
- 400 Invalid Request (bad coordinates)
- 401 Unauthorized (invalid API key)
- 404 Zero Results (no POIs found)

**Fallback Strategy:**
```python
async def get_grocery_distance_with_fallback(lat: float, lng: float):
    """Get grocery distance with static estimate fallback."""
    try:
        async with GooglePlacesClient() as client:
            places = await client.search_nearby(
                lat, lng, included_types=["grocery_store"]
            )
            if places:
                # Calculate distance to nearest
                return calculate_distance(lat, lng, places[0])
    except Exception as e:
        logger.warning(f"Google Places failed: {e}, using default")

    # Fallback: Urban average (Phoenix)
    return 2.5  # miles (reasonable urban estimate)
```

#### 5.3 Google Air Quality API

**Transient Errors (Retry):**
- 429 Resource Exhausted (QPM limit)
- 500/503 Server errors

**Permanent Errors (Fail Gracefully):**
- 400 Invalid Request
- 404 No Data Available (rural areas)

**Fallback Strategy:**
```python
async def get_aqi_with_fallback(lat: float, lng: float):
    """Get AQI with Phoenix metro default fallback."""
    try:
        async with AirQualityClient() as client:
            aqi_data = await client.get_current_aqi(lat, lng)
            if aqi_data:
                return aqi_data["aqi"]
    except Exception as e:
        logger.warning(f"Air Quality API failed: {e}, using metro default")

    # Fallback: Phoenix metro average
    return 50  # AQI 50 = "Good" (annual average)
```

#### 5.4 Census Bureau ACS

**Transient Errors (Retry):**
- 500/503 Server errors
- Network timeouts

**Permanent Errors (Fail Gracefully):**
- 400 Invalid Geography (bad tract code)
- 404 No Data Available

**Fallback Strategy:**
```python
async def get_tract_income_with_fallback(state: str, county: str, tract: str):
    """Get tract median income with county average fallback."""
    try:
        async with CensusACSClient() as client:
            data = await client.get_tract_data(state, county, tract)
            if data:
                return int(data.get("B19013_001E", 0))
    except Exception as e:
        logger.warning(f"Census API failed: {e}, using county average")

    # Fallback: Maricopa County median income
    return 72254  # 2022 ACS county median
```

### Alerting Thresholds

**Failure Rate Alerts:**
```python
"""Alert on high API failure rates."""

ALERT_THRESHOLDS = {
    "error_rate_percent": 10,  # Alert if >10% requests fail
    "consecutive_failures": 5,  # Alert after 5 consecutive failures
    "circuit_breaker_open": True,  # Alert when circuit opens
}

def monitor_api_health(service_name: str, stats: dict) -> None:
    """Monitor API health and trigger alerts."""
    total = stats.get("total_requests", 0)
    errors = stats.get("error_count", 0)

    if total == 0:
        return

    error_rate = (errors / total) * 100

    if error_rate > ALERT_THRESHOLDS["error_rate_percent"]:
        logger.critical(
            f"HIGH ERROR RATE: {service_name} at {error_rate:.1f}% "
            f"({errors}/{total} requests failed)"
        )
        # TODO: Send email/Slack alert
```

---

## 6. Cost Budget

### Per-Property Cost Breakdown

**Phase 1 APIs (High Priority):**

| API | Requests/Property | Cost/Request | Cost/Property | Cache Hit Rate | Effective Cost |
|-----|------------------|--------------|---------------|----------------|----------------|
| SchoolDigger | 1 | $0.000 | $0.00 | 95% (30d TTL) | $0.00 |
| Google Places | 1 | $0.032 | $0.032 | 90% (30d TTL) | $0.0032 |
| **Phase 1 Total** | | | **$0.032** | | **$0.0032** |

**Phase 2 APIs (Medium Priority):**

| API | Requests/Property | Cost/Request | Cost/Property | Cache Hit Rate | Effective Cost |
|-----|------------------|--------------|---------------|----------------|----------------|
| Air Quality | 1 | $0.005 | $0.005 | 80% (1d TTL) | $0.0010 |
| Census ACS | 1 | $0.000 | $0.00 | 99% (365d TTL) | $0.00 |
| **Phase 2 Total** | | | **$0.005** | | **$0.0010** |

**Combined Total:**

| Scale | Properties | Phase 1 Cost | Phase 2 Cost | Total Cost | With Cache (90%) |
|-------|-----------|--------------|--------------|------------|------------------|
| Small Batch | 100 | $3.20 | $0.50 | $3.70 | $0.37 |
| Medium Batch | 500 | $16.00 | $2.50 | $18.50 | $1.85 |
| Large Batch | 1,000 | $32.00 | $5.00 | $37.00 | $3.70 |
| Monthly (3K) | 3,000 | $96.00 | $15.00 | $111.00 | $11.10 |

### Monthly Budget Allocation

**Recommended Budget: $120/month**

| Service | Monthly Budget | Usage Assumption |
|---------|---------------|------------------|
| Google Places | $96 | ~3,000 properties (10% cache miss) |
| Google Air Quality | $15 | ~3,000 properties (20% cache miss) |
| SchoolDigger | $0 | Free tier (2,000 req/month limit) |
| Census ACS | $0 | Free unlimited |
| **Total** | **$111** | |
| Buffer (10%) | $9 | Contingency for cache misses |
| **Grand Total** | **$120** | |

### Cost Optimization Strategies

**1. Cache Warming by ZIP Code**
```python
"""Pre-warm cache for entire ZIP codes to maximize cache hits."""

async def warm_zip_cache(zip_code: str) -> None:
    """Fetch data for all properties in ZIP, maximizing cache hits.

    Example: 100 properties in ZIP 85001
    - First property: 100% API calls ($0.037)
    - Next 99 properties: 99% cache hits ($0.00037 each)
    - Total: $0.037 + $0.037 = $0.074 (vs $3.70 without caching)
    - Savings: 98%
    """
    properties = get_properties_by_zip(zip_code)
    # Fetch data for first property (seeds cache)
    await fetch_all_apis(properties[0])
    # Subsequent properties hit cache
```

**2. Batch Processing with Rate Awareness**
```python
"""Process properties in batches to stay within free tiers."""

# SchoolDigger free tier: 2,000 req/month
# Batch size: 60 properties/day = 1,800/month (90% of limit)

async def process_daily_batch(max_properties: int = 60) -> None:
    """Process properties in daily batches to stay within API limits."""
    pending = get_pending_properties()[:max_properties]

    for prop in pending:
        await enrich_property(prop)
        await asyncio.sleep(0.1)  # 10 req/sec = 600 req/min < limits
```

**3. Incremental Enrichment**
```python
"""Only fetch missing fields to avoid redundant API calls."""

async def enrich_property_incremental(prop: dict) -> None:
    """Enrich only missing fields.

    Example: Property already has school_rating from previous run
    - Skip: SchoolDigger API call
    - Fetch: Only Google Places for grocery distance
    - Savings: $0.032 → $0.032 (SchoolDigger free)
    """
    if not prop.get("school_rating"):
        await fetch_schools(prop)

    if not prop.get("distance_to_grocery_miles"):
        await fetch_grocery_distance(prop)
```

---

## 7. Testing Strategy

### Mock Response Fixtures

**Directory Structure:**
```
tests/fixtures/api_responses/
├── schooldigger/
│   ├── schools_near_phoenix.json
│   ├── schools_near_scottsdale.json
│   └── no_schools_found.json
├── google_places/
│   ├── grocery_stores_5mi.json
│   ├── gas_stations_2mi.json
│   └── zero_results.json
├── google_air_quality/
│   ├── good_aqi_45.json
│   ├── moderate_aqi_75.json
│   └── no_data_rural.json
└── census_acs/
    ├── tract_high_income.json
    ├── tract_low_income.json
    └── invalid_geography.json
```

**Example Fixture (SchoolDigger):**
```json
{
  "schools": [
    {
      "schoolName": "Desert View Elementary School",
      "address": {
        "street": "123 N Main St",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85001"
      },
      "latitude": 33.4484,
      "longitude": -112.0740,
      "lowGrade": "K",
      "highGrade": "5",
      "schoolDiggerRating": 75
    }
  ]
}
```

### Unit Tests

**Test Coverage Requirements:**
- APIClient subclasses: 100% (critical infrastructure)
- Response transformers: 100% (data integrity)
- Error handling: 90% (edge cases)
- Fallback logic: 100% (graceful degradation)

**Example Test (Google Places):**
```python
"""Unit tests for GooglePlacesClient."""

import pytest
from unittest.mock import AsyncMock, patch
from phx_home_analysis.services.google_places import GooglePlacesClient

@pytest.mark.asyncio
async def test_search_nearby_grocery_stores(mock_places_response):
    """Test searching for nearby grocery stores."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_places_response("grocery_stores_5mi.json")

        async with GooglePlacesClient() as client:
            places = await client.search_nearby(
                lat=33.4484,
                lng=-112.0740,
                included_types=["grocery_store"],
                radius_meters=8046,
            )

        assert len(places) == 5
        assert places[0]["displayName"]["text"] == "Safeway"
        assert "location" in places[0]

@pytest.mark.asyncio
async def test_search_nearby_zero_results(mock_places_response):
    """Test graceful handling of zero results."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = mock_places_response("zero_results.json")

        async with GooglePlacesClient() as client:
            places = await client.search_nearby(
                lat=33.4484,
                lng=-112.0740,
                included_types=["grocery_store"],
            )

        assert places == []

@pytest.mark.asyncio
async def test_rate_limit_respected():
    """Test that rate limiter throttles requests."""
    async with GooglePlacesClient() as client:
        start = time.time()

        # Make 5 requests
        for _ in range(5):
            await client.search_nearby(33.4484, -112.0740, ["grocery_store"])

        elapsed = time.time() - start
        # Should take at least 0.05s (5 requests at 80 req/sec = 0.0125s each)
        assert elapsed >= 0.05
```

### Integration Tests with Mocked Responses

**respx Integration (httpx mocking):**
```python
"""Integration tests using respx for httpx mocking."""

import respx
import httpx
import pytest
from phx_home_analysis.services.google_places import GooglePlacesClient

@pytest.mark.asyncio
@respx.mock
async def test_places_integration_with_cache(tmp_path):
    """Test full request flow with caching."""
    # Mock Google Places API
    respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
        return_value=httpx.Response(
            200,
            json={"places": [{"displayName": {"text": "Safeway"}}]},
        )
    )

    async with GooglePlacesClient() as client:
        # Override cache dir for test
        client._cache._cache_dir = tmp_path / "cache"

        # First call: API hit
        places1 = await client.search_nearby(33.4484, -112.0740, ["grocery_store"])

        # Second call: Cache hit
        places2 = await client.search_nearby(33.4484, -112.0740, ["grocery_store"])

        # Verify cache worked
        stats = client.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert places1 == places2
```

### Rate Limit Simulation

**Load Testing with Rate Limits:**
```python
"""Simulate high-load scenarios to test rate limiting."""

import pytest
import asyncio
from phx_home_analysis.services.google_places import GooglePlacesClient

@pytest.mark.asyncio
async def test_rate_limit_burst_handling():
    """Test handling of burst requests at rate limit threshold."""
    async with GooglePlacesClient() as client:
        # Simulate 200 concurrent requests (exceeds 80 req/sec limit)
        tasks = [
            client.search_nearby(33.4484, -112.0740, ["grocery_store"])
            for _ in range(200)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        # Should throttle to 80 req/sec
        min_expected_time = 200 / 80.0  # 2.5 seconds
        assert elapsed >= min_expected_time

        # All requests should succeed (no rate limit errors)
        assert all(not isinstance(r, Exception) for r in results)

@pytest.mark.asyncio
async def test_429_retry_behavior(respx_mock):
    """Test handling of 429 responses with Retry-After header."""
    # First call: 429 with Retry-After: 5
    respx_mock.post("https://places.googleapis.com/v1/places:searchNearby").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "5"}),
            httpx.Response(200, json={"places": []}),
        ]
    )

    async with GooglePlacesClient() as client:
        start = time.time()
        places = await client.search_nearby(33.4484, -112.0740, ["grocery_store"])
        elapsed = time.time() - start

        # Should retry after 5 seconds
        assert elapsed >= 5.0
        assert places == []
```

### End-to-End Integration Tests (Optional)

**Live API Testing (CI/CD only):**
```python
"""E2E tests with real APIs (requires API keys)."""

import os
import pytest

@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_API_TESTS"),
    reason="Live API tests disabled (set RUN_LIVE_API_TESTS=1)",
)
@pytest.mark.asyncio
async def test_schooldigger_live_api():
    """Test SchoolDigger API with real request (CI only)."""
    from phx_home_analysis.services.schools import SchoolRatingsClient

    async with SchoolRatingsClient() as client:
        # Phoenix coordinates
        result = await client.get_assigned_schools(33.4484, -112.0740)

        assert result is not None
        assert result.elementary is not None
        assert result.composite_rating > 0
        assert result.source == "schooldigger_api"
```

---

## Implementation Checklist

### Phase 1: SchoolDigger + Google Places
- [x] SchoolDigger client implemented (`ratings_client.py`)
- [x] SchoolDigger API models (`api_models.py`)
- [x] SchoolDigger unit tests (25 tests)
- [ ] Google Places client implementation
- [ ] Google Places response transformers
- [ ] Google Places unit tests (20+ tests)
- [ ] Integration tests (SchoolDigger + Places)
- [ ] Update enrichment_data.json schema
- [ ] Add environment variable validation
- [ ] Document cache warming strategy

### Phase 2: Air Quality + Census
- [ ] Air Quality client implementation
- [ ] Air Quality response transformers
- [ ] Air Quality unit tests (15+ tests)
- [ ] Census ACS client implementation
- [ ] Census tract lookup logic
- [ ] Census unit tests (15+ tests)
- [ ] Update scoring logic to use new fields
- [ ] Add cost monitoring alerts

### Phase 3: OpenStreetMap
- [ ] Research osmium installation (Windows/Linux)
- [ ] Download Arizona PBF extract (270MB)
- [ ] Implement pyosmium filtering
- [ ] Create POI extraction pipeline
- [ ] Benchmark vs Google Places API
- [ ] Decide on long-term strategy

---

## References

### API Documentation
- **SchoolDigger:** https://developer.schooldigger.com/
- **Google Places API:** https://developers.google.com/maps/documentation/places/web-service/place-types
- **Google Air Quality:** https://developers.google.com/maps/documentation/air-quality
- **Census Bureau ACS:** https://www.census.gov/data/developers/data-sets/acs-5year.html
- **OpenStreetMap:** https://wiki.openstreetmap.org/wiki/Overpass_API

### Internal Documentation
- Base client: `src/phx_home_analysis/services/api_client/base_client.py`
- SchoolDigger implementation: `src/phx_home_analysis/services/schools/ratings_client.py`
- Error handling: `src/phx_home_analysis/errors/retry.py`
- Enrichment schema: `docs/schemas/enrichment_data.json`
- Integration architecture: `docs/architecture/integration-architecture.md`
- **See also:** ADR-10 (Pipeline & Orchestration Patterns)
- **See also:** ADR-11 (Entity Model & Schema Conventions)
- **See also:** `docs/specs/schema-evolution-plan.md` for new field definitions

### Cost Calculators
- Google Cloud Pricing: https://cloud.google.com/maps-platform/pricing
- RapidAPI SchoolDigger: https://rapidapi.com/schooldigger/api/schooldigger

---

## Approvals Required

Before implementation:
1. **API Key Budget:** Approve $120/month allocation for Google APIs
2. **Environment Variables:** Add `GOOGLE_MAPS_API_KEY`, `SCHOOLDIGGER_API_KEY`, `CENSUS_API_KEY` to .env
3. **Schema Changes:** Review enrichment_data.json field additions:
   - `air_quality_index` (int)
   - `air_quality_category` (str)
   - `tract_median_income` (int)
   - `tract_population` (int)
4. **Dependency Additions:** None (httpx already in use)

---

**Document Status:** READY FOR REVIEW
**Next Steps:** Implement Phase 1 (Google Places client), write tests, update enrichment schema

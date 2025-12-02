---
name: map-analysis
description: Analyze geographic data via Google Maps, GreatSchools, crime statistics, and satellite imagery. Use for Phase 1 map analysis, orientation determination, school ratings, safety scoring, and proximity calculations.
allowed-tools: Read, Bash(python:*), mcp__playwright__*, WebSearch, WebFetch
---

# Map Analysis Skill

Expert at geographic and location analysis for Phoenix area property evaluation.

## Data Collection Targets

| Field | Source | Method | Points |
|-------|--------|--------|--------|
| `school_rating` | GreatSchools | Web scrape | 50 pts |
| `orientation` | Google Maps Satellite | Visual | 30 pts |
| `safety_neighborhood_score` | BestPlaces/Crime stats | Web search | 50 pts |
| `distance_to_grocery_miles` | Google Maps | Calculate | 40 pts |
| `distance_to_park_miles` | Google Maps | Calculate | 30 pts |
| `distance_to_highway_miles` | Google Maps | Calculate | 50 pts |
| `commute_minutes` | Google Maps | Calculate | Info |

## Geocoding Workflow

Before performing any geographic analysis, ensure the property has valid coordinates.

### Fallback Chain

```
1. CHECK CACHE FIRST
   └─ Load data/geocoded_homes.json
   └─ Search for address match
   └─ If found with valid lat/lon → Use cached coordinates

2. USE PROJECT SCRIPT
   └─ python scripts/geocode_homes.py --address "{address}"
   └─ Script handles rate limiting and caching
   └─ If successful → Use returned coordinates

3. FALLBACK: GOOGLE MAPS URL PARSE
   └─ Navigate to https://www.google.com/maps/search/{encoded_address}
   └─ Wait for redirect to maps/@{lat},{lon}
   └─ Extract coordinates from URL
   └─ Example: /@33.5384,-112.0844 → lat=33.5384, lon=-112.0844

4. FALLBACK: ZIP CODE CENTROID
   └─ Extract ZIP code from address
   └─ Use known Phoenix metro centroids:
      - 85001: 33.4484, -112.0740 (Downtown)
      - 85016: 33.5064, -112.0449 (Biltmore)
      - 85028: 33.5842, -111.9956 (Paradise Valley)
      - 85032: 33.6132, -111.9852 (Paradise Valley Village)
      - 85050: 33.6580, -111.9644 (Desert Ridge)
      - 85086: 33.8333, -112.1333 (Anthem)
      - 85301: 33.5406, -112.1838 (Glendale)
   └─ Flag as "estimated_location" with low confidence

5. FINAL FALLBACK: FLAG FOR MANUAL
   └─ Add to research_tasks.json with priority="high"
   └─ Return partial data with coordinates=null
   └─ Skip orientation analysis (requires coordinates)
```

### Geocoding Output Format

```json
{
  "coordinates": {
    "lat": 33.5384,
    "lon": -112.0844,
    "source": "cache|script|maps_parse|zip_centroid|manual",
    "confidence": "high|medium|low",
    "verified": true
  },
  "geocoding_errors": []
}
```

### When to Skip Geocoding

Skip geocoding attempts if:
- coordinates already exist in enrichment_data.json with confidence="high"
- property marked as "geocoding_failed" with retry_count >= 3

### Error Recovery

| Error | Recovery Action |
|-------|-----------------|
| Script timeout | Try Google Maps URL fallback |
| Google Maps redirect blocked | Use ZIP centroid + flag |
| Invalid coordinates returned | Validate: lat in [31, 37], lon in [-115, -109] for AZ |
| All fallbacks failed | Flag for manual, proceed with partial data |

## School Rating Analysis

### GreatSchools Lookup

```
URL: https://www.greatschools.org/search/search.page?q={address}

1. Navigate to GreatSchools
2. Search for property address
3. Extract assigned schools:
   - Elementary (K-5)
   - Middle (6-8)
   - High (9-12)
4. Get rating for each (1-10 scale)
5. Calculate weighted average
```

### Playwright Flow

```python
# Navigate
mcp__playwright__browser_navigate(url="https://www.greatschools.org/search/search.page?q={encoded_address}")

# Wait for results
mcp__playwright__browser_wait_for(text="Schools near")

# Snapshot for element refs
mcp__playwright__browser_snapshot()

# Extract via evaluate
mcp__playwright__browser_evaluate(function=`() => {
  const schools = document.querySelectorAll('.school-card');
  return Array.from(schools).map(s => ({
    name: s.querySelector('.school-name')?.textContent,
    rating: s.querySelector('.rating')?.textContent,
    level: s.querySelector('.school-level')?.textContent
  }));
}`)
```

### Scoring

```python
def calculate_school_score(rating: float) -> int:
    """Convert GreatSchools 1-10 to points (max 50)."""
    return int(rating * 5)  # 10 rating = 50 pts
```

## Orientation Analysis

### Google Maps Satellite

```
URL: https://www.google.com/maps/@{lat},{lng},19z/data=!3m1!1e3

1. Navigate to satellite view
2. Identify property lot boundaries
3. Determine front-of-house direction (facing street)
4. Map to compass direction
```

### Orientation Determination Protocol

Follow this systematic approach to determine property orientation:

#### Step 1: Satellite View Setup

```
1. Navigate to satellite view with property centered:
   URL: https://www.google.com/maps/@{lat},{lon},19z/data=!3m1!1e3

2. Zoom level guide:
   - 19z: Ideal for single property lot boundaries
   - 18z: Better for neighborhood context
   - 17z: Too zoomed out for orientation

3. Take screenshot for documentation
```

#### Step 2: Property Identification

```
1. Locate the property lot:
   - Match to address using street names visible
   - Identify lot boundaries (fence lines, yard edges)
   - Note surrounding lots for reference

2. Identify front of house:
   - Driveway connects to which street?
   - Front door location (usually faces street)
   - Garage door orientation
```

#### Step 3: Compass Direction Mapping

```
GOOGLE MAPS ORIENTATION:
- TOP of screen = NORTH
- BOTTOM = SOUTH
- LEFT = WEST
- RIGHT = EAST

DETERMINE FRONT-FACING DIRECTION:
1. Find the street the front door faces
2. Draw imaginary line perpendicular from front door to street
3. That direction is the "facing" direction

Example: If front door faces toward TOP of screen → North-facing
```

#### Step 4: Backyard Sun Exposure (Critical for AZ)

```
After determining front direction, assess backyard:

| Front Faces | Backyard Faces | Sun Exposure |
|-------------|----------------|--------------|
| North | South | Moderate all-day |
| South | North | Minimal (shaded) |
| East | West | Brutal PM sun |
| West | East | Morning only |

For AZ scoring, backyard exposure matters most for:
- Pool usage comfort
- Outdoor living space
- Covered patio effectiveness
```

#### Step 5: Document and Score

```json
{
  "orientation": "north",
  "front_faces": "north",
  "backyard_faces": "south",
  "determination_method": "satellite_visual",
  "confidence": "high",
  "screenshot": "satellite_{hash}.png",
  "notes": "Clear lot boundaries, driveway visible, definitive orientation"
}
```

### Orientation Fallback Options

If satellite view unclear:

```
1. CHECK EXISTING DATA
   └─ data/orientation_estimates.json may have estimate
   └─ If exists with confidence >= medium → Use existing

2. STREET VIEW ASSIST
   └─ Navigate to street view of property
   └─ Identify which direction camera faces
   └─ House front visible = facing toward camera direction

3. LOT SHAPE ANALYSIS
   └─ Most lots have front narrower than depth
   └─ Driveway connects to public street
   └─ Typical AZ lot: 60ft front x 120ft deep

4. FLAG FOR RESEARCH
   └─ orientation is CRITICAL for AZ scoring (30 pts)
   └─ Never default orientation to neutral
   └─ Add to research_tasks.json with priority="high"
```

## Safety/Crime Analysis

### Primary Method: WebSearch

```python
# Search for crime statistics
query = f"{zip_code} {city} AZ crime rate safety statistics site:bestplaces.net"

# Parse results for crime indices
# National averages: violent=22.7, property=35.4
```

### Scoring Algorithm

```python
def calculate_safety_score(violent_index: float, property_index: float) -> int:
    """Calculate safety score from crime indices.

    Lower indices = safer = higher score
    """
    avg_index = (violent_index + property_index) / 2
    us_avg = 29.05  # Average of national averages

    ratio = avg_index / us_avg

    if ratio < 0.5:
        return 10  # Very safe
    elif ratio < 0.75:
        return 8
    elif ratio < 1.0:
        return 6  # Average
    elif ratio < 1.5:
        return 4
    elif ratio < 2.0:
        return 3
    else:
        return 1  # High crime
```

### Data Sources

| Source | URL | Data |
|--------|-----|------|
| BestPlaces | bestplaces.net/crime | Crime indices by ZIP |
| SpotCrime | spotcrime.com/az/{city} | Incident map |
| CrimeMapping | crimemapping.com | Police reports |
| Phoenix Open Data | phoenixopendata.com | Official stats |

## Distance Calculations

### Google Maps Method

```python
# Via Playwright
mcp__playwright__browser_navigate(url=f"https://www.google.com/maps/search/grocery+stores+near+{encoded_address}")

# Or via Directions API (requires key)
# Calculate driving distance to:
# - Nearest grocery (Fry's, Safeway, Walmart, etc.)
# - Nearest highway on-ramp
# - Desert Ridge (commute reference)
# - Nearest park
```

### Reference Points (Phoenix)

| Destination | Coordinates | Purpose |
|-------------|-------------|---------|
| Desert Ridge | 33.6823, -111.9244 | Commute reference |
| Sky Harbor | 33.4373, -112.0078 | Airport access |
| Downtown Phoenix | 33.4484, -112.0740 | Urban center |

### Distance Scoring

```python
def score_grocery_distance(miles: float) -> int:
    """Score based on grocery proximity (max 40 pts)."""
    if miles < 0.5:
        return 10  # Walkable
    elif miles < 1.0:
        return 9
    elif miles < 2.0:
        return 7
    elif miles < 3.0:
        return 5
    else:
        return 3

def score_highway_distance(miles: float) -> int:
    """Score based on highway distance (max 50 pts).

    Note: Further is BETTER (less noise).
    """
    if miles > 1.0:
        return 10  # Quiet
    elif miles > 0.5:
        return 8
    elif miles > 0.25:
        return 5
    else:
        return 2  # Too close, noisy
```

## Parks Analysis

### Google Maps Search

```
URL: https://www.google.com/maps/search/parks+near+{encoded_address}

Extract:
- Nearest park name
- Distance
- Rating (if available)
```

### Scoring

```python
def score_parks(distance_miles: float) -> int:
    """Score based on park proximity (max 30 pts)."""
    if distance_miles < 0.25:
        return 10  # Walking distance
    elif distance_miles < 0.5:
        return 8
    elif distance_miles < 1.0:
        return 6
    elif distance_miles < 2.0:
        return 4
    else:
        return 2
```

## Error Handling Matrix

### Geocoding Errors

| Error Type | Detection | Recovery | Escalation |
|------------|-----------|----------|------------|
| Rate limited | HTTP 429 or "too many requests" | Exponential backoff: 2s, 4s, 8s, 16s | After 4 retries, use fallback |
| Invalid address | "Address not found" response | Try alternate format (remove unit #, etc.) | ZIP centroid fallback |
| Network timeout | No response in 30s | Retry once, then fallback | Skip to next fallback |
| Blocked/CAPTCHA | Redirect to verification page | Switch to script method | Manual flag |
| Coordinates outside AZ | lat/lon validation fails | Re-attempt with verified address | Manual research |

### Map Analysis Errors

| Error Type | Detection | Recovery | Impact |
|------------|-----------|----------|--------|
| GreatSchools blocked | No school results | WebSearch for "{address} school ratings" | Lose 50 pts confidence |
| Google Maps blocked | Redirect to login | Use cached coordinates only | Skip orientation |
| Crime stats unavailable | No results for ZIP | Use city-wide average | Flag as estimated |
| Satellite view unclear | Cannot determine lot | Try street view | Manual orientation |

### Exponential Backoff Implementation

```python
def with_backoff(operation, max_retries=4):
    """Execute operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return operation()
        except RateLimitError:
            wait_time = 2 ** attempt  # 2, 4, 8, 16 seconds
            time.sleep(wait_time)
    raise MaxRetriesExceeded()
```

### Partial Success Handling

When some data collection succeeds but others fail:

```json
{
  "status": "partial",
  "data": {
    "school_rating": 7.5,
    "orientation": null,
    "safety_neighborhood_score": 6,
    "distance_to_grocery_miles": 0.8
  },
  "errors": [
    {"field": "orientation", "error": "satellite_view_blocked", "fallback_attempted": "street_view"}
  ],
  "missing_fields": ["orientation"],
  "points_at_risk": 30,
  "recommendation": "Manual orientation research required for complete scoring"
}
```

### Never Fail Silently

For each error:
1. Log the specific error type and attempted recovery
2. Document which fallback was used
3. Flag fields that used fallbacks in output
4. Calculate "points at risk" for missing/uncertain data

## Existing Project Resources

### Geocoding Script

```bash
python scripts/geocode_homes.py
```

Output: `data/geocoded_homes.json` with lat/lon coordinates.

### Sun Orientation Script

```bash
python scripts/sun_orientation_analysis.py
```

Output: `data/orientation_estimates.json` with estimated orientations.

## Output Format

```json
{
  "address": "123 Main St, Phoenix, AZ 85001",
  "status": "success|partial|failed",
  "data": {
    "school_rating": 7.5,
    "school_district": "Washington Elementary",
    "schools_assigned": {
      "elementary": "Madison Heights (8/10)",
      "middle": "Royal Palm (7/10)",
      "high": "Shadow Mountain (7/10)"
    },
    "orientation": "north",
    "orientation_source": "satellite_verified",
    "safety_neighborhood_score": 6,
    "safety_source": "bestplaces.net ZIP 85028",
    "distance_to_grocery_miles": 0.8,
    "nearest_grocery": "Fry's Food Store",
    "distance_to_highway_miles": 1.2,
    "nearest_highway": "SR-51",
    "distance_to_park_miles": 0.4,
    "nearest_park": "Rose Lane Park (4.3 stars)",
    "parks_walkability_score": 8,
    "commute_minutes": 22,
    "commute_destination": "Desert Ridge"
  },
  "screenshots": ["satellite.png", "school_map.png"],
  "errors": [],
  "files_updated": ["enrichment_data.json"]
}
```

## Best Practices

1. **Required fields** - Safety and parks are 80 pts combined, never skip
2. **Multiple sources** - Cross-reference school ratings
3. **Visual verification** - Satellite view for orientation accuracy
4. **Save screenshots** - Evidence for later review
5. **Use existing data** - Check geocoded_homes.json and orientation_estimates.json first
6. **Geocoding first** - Always establish coordinates before map analysis
7. **Error transparency** - Document all fallbacks and failures in output
8. **Rate limiting** - Use exponential backoff for API calls

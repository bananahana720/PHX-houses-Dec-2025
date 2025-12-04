---
name: map-analysis
description: Analyze geographic data for Phoenix properties. Extract school ratings (GreatSchools), determine sun orientation (satellite), calculate safety scores (crime stats), and measure proximity distances. Section A scores 230pts. Use for Phase 1 location analysis, orientation determination, or proximity calculations.
allowed-tools: Read, Bash(python:*), mcp__playwright__*, WebSearch, WebFetch
---

# Map Analysis Skill

Geographic and location analysis for Phoenix area property evaluation (Section A: 230 pts).

## Data Collection Targets

| Field | Source | Points | Method |
|-------|--------|--------|--------|
| `school_rating` | GreatSchools | 50 | Web scrape |
| `orientation` | Google Maps Satellite | 30 | Visual (CRITICAL) |
| `safety_neighborhood_score` | BestPlaces/Crime | 50 | Web search |
| `distance_to_grocery_miles` | Google Maps | 30 | Distance calc |
| `distance_to_park_miles` | Google Maps | 30 | Distance calc |
| `distance_to_highway_miles` | Google Maps | 40 | Distance calc (further=better) |

## Helper Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/geocode_homes.py` | Get lat/lon coordinates | `python scripts/geocode_homes.py --address "123 Main"` |
| `scripts/sun_orientation_analysis.py` | Orientation estimation | `python scripts/sun_orientation_analysis.py` |

**Outputs:**
- `data/geocoded_homes.json` - Cached coordinates
- `data/orientation_estimates.json` - Orientation estimates

## Geocoding Fallback Chain

```
1. CHECK CACHE → data/geocoded_homes.json
2. USE SCRIPT → scripts/geocode_homes.py
3. FALLBACK: Google Maps URL → Extract from /@{lat},{lon}
4. FALLBACK: ZIP centroid → Use known Phoenix ZIP centers
5. FLAG FOR MANUAL → research_tasks.json
```

**AZ Coordinate Validation:** lat in [31, 37], lon in [-115, -109]

## Orientation Protocol (30 pts - NEVER DEFAULT)

```
1. SATELLITE VIEW: https://www.google.com/maps/@{lat},{lon},19z/data=!3m1!1e3
2. IDENTIFY: Front door / driveway → which street?
3. MAP: Top=North, Bottom=South, Left=West, Right=East
4. SCORE: Front facing direction
```

| Direction | Points | Reason |
|-----------|--------|--------|
| **North** | 30 | Minimal sun, lowest cooling |
| NE/NW | 25 | Near-optimal |
| East | 20 | Morning sun only |
| South | 10 | Moderate exposure |
| SE/SW | 5 | High cooling |
| **West** | 0 | Brutal PM sun |

**CRITICAL:** Orientation is NEVER defaulted. If unclear, flag for manual research.

## School Rating (50 pts)

```
URL: https://www.greatschools.org/search/search.page?q={encoded_address}
Extract: Elementary, Middle, High school ratings (1-10 scale)
Score: rating * 5 = points (10 rating → 50 pts)
```

## Safety Score (50 pts)

```
Search: "{zip} {city} AZ crime rate site:bestplaces.net"
National avg: violent=22.7, property=35.4

Ratio = crime_index / 29.05
< 0.5  → 10 pts (very safe)
< 1.0  → 6 pts (average)
< 2.0  → 3 pts (concerning)
> 2.0  → 1 pt (high crime)
```

## Distance Scoring

| Type | Close = Better | Scoring |
|------|----------------|---------|
| Grocery | Yes | <0.5mi=10, <1mi=9, <2mi=7, <3mi=5 |
| Parks | Yes | <0.25mi=10, <0.5mi=8, <1mi=6 |
| Highway | **No** (noise) | >1mi=10, >0.5mi=8, <0.25mi=2 |

## Playwright Pattern

```python
# Navigate to satellite
mcp__playwright__browser_navigate(url=f"https://www.google.com/maps/@{lat},{lon},19z/data=!3m1!1e3")
mcp__playwright__browser_wait_for(time=3)
mcp__playwright__browser_snapshot()

# Or for school ratings
mcp__playwright__browser_navigate(url=f"https://www.greatschools.org/search/search.page?q={address}")
mcp__playwright__browser_wait_for(text="Schools near")
```

## Error Handling

| Error | Recovery | Escalation |
|-------|----------|------------|
| Rate limited | Backoff: 2s, 4s, 8s, 16s | After 4 retries → fallback |
| GreatSchools blocked | WebSearch for school ratings | Flag as estimated |
| Satellite unclear | Try street view | Manual research (orientation CRITICAL) |
| Crime stats missing | Use city-wide average | Flag as estimated |

## Output Format

```json
{
  "status": "success|partial|failed",
  "data": {
    "school_rating": 7.5,
    "orientation": "north",
    "safety_neighborhood_score": 6,
    "distance_to_grocery_miles": 0.8,
    "distance_to_highway_miles": 1.2,
    "parks_walkability_score": 8
  },
  "errors": [],
  "missing_fields": [],
  "points_at_risk": 0
}
```

## Best Practices

1. **Check cache first** - Use geocoded_homes.json and orientation_estimates.json
2. **Never default orientation** - It's 30 pts and critical for AZ cooling costs
3. **Cross-reference schools** - Verify GreatSchools data
4. **Document fallbacks** - Track which sources used for each field
5. **Screenshot evidence** - Save satellite view for orientation verification

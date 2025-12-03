---
name: map-analyzer
description: Analyze geographic and map data including satellite views, school districts, crime heat maps, and topography. Uses Playwright MCP for visual data capture.
model: haiku
skills: property-data, state-management, map-analysis, arizona-context, scoring
---

# Map Analyzer Agent

Analyze geographic data for property evaluation including schools, safety, orientation, and proximity metrics.

## STEP 0: GET YOUR BEARINGS (MANDATORY)

Before ANY map analysis, orient yourself:

```bash
# 1. Confirm working directory
pwd

# 2. Get target property address
echo "Target: $TARGET_ADDRESS"

# 3. Check phase status
cat data/property_images/metadata/extraction_state.json | python -c "
import json,sys
state = json.load(sys.stdin)
props = state.get('properties', {})
addr = '$TARGET_ADDRESS'
if addr in props:
    phase = props[addr].get('phase_status', {})
    print(f'phase1_map: {phase.get(\"phase1_map\", \"pending\")}')
    if phase.get('phase1_map') == 'complete':
        print('SKIP: Map analysis already complete')
else:
    print('PROCEED: No phase status yet')
"

# 4. Check what location data already exists
cat data/enrichment_data.json | python -c "
import json,sys
data = json.load(sys.stdin)
addr = '$TARGET_ADDRESS'
if addr in data:
    loc_fields = ['school_rating', 'orientation', 'safety_neighborhood_score',
                  'distance_to_grocery_miles', 'distance_to_highway_miles', 'parks_walkability_score']
    for f in loc_fields:
        val = data[addr].get(f, 'MISSING')
        print(f'{f}: {val}')
else:
    print('No existing data - full extraction needed')
"

# 5. Check for cached geocoding
cat data/geocoded_homes.json 2>/dev/null | python -c "
import json,sys
try:
    geo = json.load(sys.stdin)
    addr = '$TARGET_ADDRESS'
    if addr in geo:
        print(f'Cached coords: {geo[addr]}')
    else:
        print('No cached coordinates - will geocode')
except: print('No geocoding cache')
"

# 6. Check orientation estimates
cat data/orientation_estimates.json 2>/dev/null | head -10 || echo "No orientation estimates file"
```

**DO NOT PROCEED** if:
- phase1_map already "complete"
- All 6 required location fields already populated

## Required Skills

Load these skills for detailed instructions:
- **property-data** - Data access patterns
- **state-management** - Triage & checkpointing
- **map-analysis** - Data sources & scoring
- **arizona-context** - Orientation impacts
- **scoring** - Point calculations

## Pre-Task Checklist (Quick Reference)

1. **Load state**: Check extraction_state.json
2. **Triage**: Skip if phase1_map complete
3. **Check enrichment**: Identify missing fields only
4. **Update phase**: Mark `phase1_map = "in_progress"`

## Required Fields (Do Not Skip)

| Field | Points | Source |
|-------|--------|--------|
| `school_rating` | 50 | GreatSchools |
| `safety_neighborhood_score` | 50 | BestPlaces/Crime stats |
| `orientation` | 30 | Google Maps Satellite |
| `parks_walkability_score` | 30 | Google Maps |
| `distance_to_grocery_miles` | 40 | Google Maps |
| `distance_to_highway_miles` | 50 | Google Maps |

## Data Sources

1. **GreatSchools**: `greatschools.org/search/search.page?q={address}`
2. **Google Maps Satellite**: `google.com/maps/@{lat},{lng},18z/data=!3m1!1e3`
3. **Crime Stats**: WebSearch for `"{zip} {city} AZ crime statistics"`
4. **Parks**: `google.com/maps/search/parks+near+{address}`

## Orientation Scoring (AZ-Specific)

| Direction | Points | Reason |
|-----------|--------|--------|
| North | 30 | Lowest cooling |
| East | 20 | Morning sun only |
| South | 10 | Moderate |
| West | 0 | Highest cooling |

## Return Format

```json
{
  "address": "full property address",
  "status": "success|partial|failed",
  "data": {
    "school_rating": 7.5,
    "school_district": "Washington Elementary",
    "orientation": "north",
    "safety_neighborhood_score": 6,
    "distance_to_grocery_miles": 0.8,
    "distance_to_highway_miles": 1.2,
    "distance_to_park_miles": 0.4,
    "parks_walkability_score": 8,
    "commute_minutes": 22
  },
  "screenshots": ["satellite.png", "school_map.png"],
  "errors": [],
  "files_updated": ["enrichment_data.json"]
}
```

## Post-Task

1. Update `enrichment_data.json` with collected fields
2. Update `extraction_state.json` phase1_map status
3. Save screenshots to property folder

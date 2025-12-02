# Property Visualizations Guide

Comprehensive guide to all property analysis visualizations in the Phoenix home buying pipeline.

## Overview

The project generates multiple interactive HTML visualizations to help analyze properties across different dimensions:

| Visualization | Purpose | New in Phase 6 |
|--------------|---------|----------------|
| Golden Zone Map | Shows all properties with kill-switch status and tier | No |
| Flood Zone Map | Displays flood risk zones and insurance requirements | **Yes** |
| Crime Heatmap | Maps crime safety indices by area | **Yes** |
| Value Spotter Chart | Identifies undervalued properties | No |
| Radar Comparison | Compares properties across scoring dimensions | No |

## Quick Start

### Generate All Visualizations

```bash
# Generate all visualizations at once
python scripts/generate_all_visualizations.py

# Generate only new Phase 6 visualizations
python scripts/generate_all_visualizations.py --only flood,crime

# Skip certain visualizations
python scripts/generate_all_visualizations.py --skip golden,value
```

### Generate Individual Visualizations

```bash
# Golden Zone Map (existing)
python scripts/golden_zone_map.py

# Interactive Property Map (existing)
python scripts/generate_map.py

# Flood Zone Map (new)
python scripts/generate_flood_map.py
python scripts/generate_flood_map.py --zip 85306
python scripts/generate_flood_map.py --tier CONTENDER

# Crime Heatmap (new)
python scripts/generate_crime_heatmap.py
python scripts/generate_crime_heatmap.py --zip 85306
python scripts/generate_crime_heatmap.py --tier UNICORN

# Value Spotter Chart (existing)
python scripts/value_spotter.py

# Radar Comparison Chart (existing)
python scripts/radar_charts.py
```

## Visualization Details

### 1. Flood Zone Map

**File:** `reports/html/flood_zone_map.html`
**Script:** `scripts/generate_flood_map.py`

Interactive Folium map showing FEMA flood zone classifications for each property.

**Color Coding:**
- 🟢 Green: Zone X (Minimal Risk) - No flood insurance required
- 🟡 Yellow: Zone X-Shaded (Moderate Risk) - 500-year floodplain
- 🟠 Orange: Zone A/AH/AO (High Risk) - Flood insurance required
- 🔴 Red: Zone AE (High Risk + BFE) - Flood insurance required, base flood elevation defined
- 🔴 Dark Red: Zone VE (Coastal High Hazard) - Highest risk, wave action expected
- ⚪ Gray: Unknown/Not Determined

**Popup Information:**
- Flood zone classification
- Flood insurance requirement (Yes/No)
- Property price and tier
- Full address

**Filtering:**
```bash
# Filter to specific ZIP code
python scripts/generate_flood_map.py --zip 85306

# Filter to specific tier
python scripts/generate_flood_map.py --tier CONTENDER
```

**Data Requirements:**
- `enrichment_data.json` must contain:
  - `flood_zone`: FEMA flood zone code (e.g., "X", "AE", "A")
  - `flood_insurance_required`: Boolean or "Yes"/"No"
  - `latitude` / `lat`: Property latitude
  - `longitude` / `lng`: Property longitude

---

### 2. Crime Heatmap

**File:** `reports/html/crime_heatmap.html`
**Script:** `scripts/generate_crime_heatmap.py`

Interactive Folium map showing crime safety indices grouped by ZIP code.

**Color Coding:**
- 🟢 Green: SAFE (70-100) - Low crime, high safety
- 🟡 Yellow: AVERAGE (50-70) - Typical crime levels
- 🟠 Orange: BELOW AVERAGE (30-50) - Elevated crime
- 🔴 Red: DANGEROUS (<30) - High crime rates

**Crime Index Scale:**
- 100 = Safest possible
- 0 = Most dangerous
- Higher numbers = SAFER neighborhoods

**Composite Index Calculation:**
```
Composite = (Violent Crime Index × 0.6) + (Property Crime Index × 0.4)
```

**Popup Information:**
- ZIP code
- Violent crime index (0-100)
- Property crime index (0-100)
- Composite safety index (0-100)
- Risk level (SAFE/AVERAGE/BELOW AVG/DANGEROUS)
- Property price and tier

**Filtering:**
```bash
# Filter to specific ZIP code
python scripts/generate_crime_heatmap.py --zip 85306

# Filter to specific tier
python scripts/generate_crime_heatmap.py --tier UNICORN
```

**Data Requirements:**
- `enrichment_data.json` must contain:
  - `violent_crime_index`: 0-100 safety index (higher = safer)
  - `property_crime_index`: 0-100 safety index (higher = safer)
  - `crime_risk_level`: Text label (optional)
  - `zip_code` / `zip`: Property ZIP code
  - `latitude` / `lat`: Property latitude
  - `longitude` / `lng`: Property longitude

---

### 3. Golden Zone Map (Existing)

**File:** `reports/html/golden_zone_map.html`
**Script:** `scripts/golden_zone_map.py`

Interactive Folium map showing properties with kill-switch status and tier classification.

**Features:**
- Color-coded markers by pass/fail status
- Marker size scaled by total score
- Grocery proximity zones (1.5 mi radius)
- Highway buffer zones (1 mi radius)
- Tier classification (Unicorn/Contender/Pass)

---

### 4. Interactive Property Map (Existing)

**File:** `reports/html/golden_zone_map.html`
**Script:** `scripts/generate_map.py`

Lightweight Leaflet.js map with property markers colored by tier and score.

---

### 5. Value Spotter Chart (Existing)

**File:** `reports/html/value_spotter.html`
**Script:** `scripts/value_spotter.py`

Scatter plot identifying undervalued properties based on price vs. score ratio.

---

### 6. Radar Comparison Chart (Existing)

**File:** `reports/html/radar_comparison.html`
**Script:** `scripts/radar_charts.py`

Radar charts comparing top properties across all scoring dimensions.

---

## Deal Sheet Integration

The new location data is automatically integrated into deal sheets generated by `scripts/deal_sheets/generator.py`.

### New Deal Sheet Sections

#### Location Risk Assessment
- Flood zone classification
- Flood insurance requirement
- Violent crime index (0-100)
- Property crime index (0-100)
- Crime risk level
- Zoning code and description

#### Walkability & Transit
- Walk Score (0-100)
- Transit Score (0-100)
- Bike Score (0-100)
- Description for each score

#### Neighborhood Demographics
- Census tract
- Median household income
- Median home value

### Regenerate Deal Sheets

After populating location data in `enrichment_data.json`:

```bash
# Regenerate all deal sheets with new location sections
python -m scripts.deal_sheets
```

---

## Data Population Workflow

To populate the new location fields, follow this workflow:

### 1. Collect Flood Zone Data

**Source:** FEMA Flood Map Service Center (https://msc.fema.gov/)

**API/Scraping Strategy:** TBD - Phase 5 implementation

**Fields to populate:**
- `flood_zone`: "X", "X-Shaded", "A", "AE", "AH", "AO", "VE", "V", etc.
- `flood_insurance_required`: Boolean or "Yes"/"No"

### 2. Collect Crime Data

**Source:**
- City-Data.com
- NeighborhoodScout.com
- Local police department crime statistics APIs

**Fields to populate:**
- `violent_crime_index`: 0-100 (higher = safer)
- `property_crime_index`: 0-100 (higher = safer)
- `crime_risk_level`: "SAFE", "AVERAGE", "BELOW AVERAGE", "DANGEROUS"

### 3. Collect Walkability Scores

**Source:** Walk Score API (https://www.walkscore.com/professional/api.php)

**Fields to populate:**
- `walk_score`: 0-100
- `walk_score_description`: Text description
- `transit_score`: 0-100
- `transit_score_description`: Text description
- `bike_score`: 0-100
- `bike_score_description`: Text description

### 4. Collect Zoning Data

**Source:** Maricopa County GIS / City zoning maps

**Fields to populate:**
- `zoning_code`: "R1-6", "R1-8", etc.
- `zoning_description`: Human-readable description

### 5. Collect Demographics

**Source:** US Census Bureau API

**Fields to populate:**
- `census_tract`: Census tract identifier
- `median_household_income`: Dollar amount
- `median_home_value`: Dollar amount

---

## Troubleshooting

### Missing Coordinates

**Symptom:** "Warning: No coordinates found for [address]"

**Solution:**
1. Check `enrichment_data.json` for `latitude`/`lat` and `longitude`/`lng` fields
2. Run geocoding: `python scripts/geocode_homes.py`
3. Check `data/geocoded_homes.json` as fallback source

### Missing Location Data

**Symptom:** Properties show "Unknown" or "N/A" for flood/crime/walkability

**Solution:**
1. Data has not been populated yet in `enrichment_data.json`
2. Implement data collection scripts (Phase 5)
3. Visualizations gracefully degrade - show gray/unknown markers

### Folium Not Installed

**Symptom:** `ModuleNotFoundError: No module named 'folium'`

**Solution:**
```bash
uv pip install folium
```

### Map Not Loading in Browser

**Symptom:** Blank page or CORS errors

**Solution:**
1. Open HTML file directly in browser (file:// protocol)
2. Or serve via local web server:
   ```bash
   cd reports/html
   python -m http.server 8000
   # Navigate to http://localhost:8000/flood_zone_map.html
   ```

---

## Output Location

All visualizations are saved to:

```
reports/html/
├── golden_zone_map.html       # Golden zone map (existing)
├── flood_zone_map.html        # Flood risk map (new)
├── crime_heatmap.html         # Crime safety map (new)
├── value_spotter.html         # Value opportunities chart (existing)
└── radar_comparison.html      # Property comparison radar (existing)
```

---

## Future Enhancements

### Phase 7+ Potential Additions

1. **School Ratings Overlay**
   - Color-code properties by school district
   - Show school locations and ratings
   - Display elementary, middle, high school boundaries

2. **Commute Time Heatmap**
   - Isochrone maps showing drive time zones
   - Color-coded by commute time to work location
   - Filter by time of day (rush hour vs. off-peak)

3. **Property Tax Heatmap**
   - Visualize effective property tax rates by area
   - Show assessment ratios and mil rates
   - Identify tax-efficient neighborhoods

4. **Combined Risk Score Map**
   - Composite risk score: flood + crime + other factors
   - Single view for all location-based risks
   - Filterable by individual risk components

5. **3D Elevation Maps**
   - Terrain visualization for flood risk context
   - Identify properties on higher ground
   - Show elevation differences across neighborhoods

---

## Related Documentation

- `CLAUDE.md` - Project overview and quick reference
- `docs/SCORING_SYSTEM.md` - Scoring methodology
- `docs/KILL_SWITCH_SPEC.md` - Kill-switch criteria
- `scripts/deal_sheets/README.md` - Deal sheet generation guide

---

*Last Updated: December 2025*
*Phase: 6 - Location Data Visualizations*

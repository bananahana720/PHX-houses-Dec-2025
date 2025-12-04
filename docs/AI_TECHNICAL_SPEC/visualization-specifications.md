# VISUALIZATION SPECIFICATIONS

### 1. Golden Zone Heatmap (`golden_zone_map.py` → `golden_zone_map.html`)

**Library**: `folium`

**Requirements**:
```python
import folium
import pandas as pd
import json

# Load data
geocoded = json.load(open('geocoded_homes.json'))
ranked = pd.read_csv('phx_homes_ranked.csv')
enrichment = json.load(open('enrichment_data.json'))

# Merge on full_address
```

**Map Configuration**:
- Center: `[33.55, -112.05]` (Phoenix metro)
- Zoom: `10`
- Tiles: `'OpenStreetMap'`

**Marker Specifications**:
- **GREEN** (`#22c55e`): `kill_switch_passed == 'PASS'`
- **RED** (`#ef4444`): `kill_switch_passed == 'FAIL'`
- Radius: `5 + (total_score / 500) * 10` (proportional to score)

**Popup Content**:
```html
<b>{full_address}</b><br>
Price: ${price:,}<br>
Score: {total_score}/500 ({tier})<br>
Status: {kill_switch_passed}<br>
{beds}bd/{baths}ba | {sqft:,} sqft
```

**Overlay Layers** (toggleable via `folium.LayerControl()`):
1. **Grocery Proximity Circles**: 1.5-mile radius from each PASS property, blue fill, 0.1 opacity
2. **Highway Buffer Zones**: Orange shaded polygons within 1 mile of I-17, I-10, Loop 101 corridors

**Output**: Self-contained HTML file with embedded CSS/JS

---

### 2. Value Spotter Scatter Plot (`value_spotter.py` → `value_spotter.html`, `value_spotter.png`)

**Library**: `plotly.express`, `plotly.graph_objects`

**Data Preparation**:
```python
import plotly.express as px
import pandas as pd

df = pd.read_csv('phx_homes_ranked.csv')
enrichment = pd.DataFrame(json.load(open('enrichment_data.json')))
df = df.merge(enrichment[['full_address', 'lot_sqft']], on='full_address')

# Calculate value ratio
df['value_ratio'] = df['total_score'] / (df['price'] / 1000)
```

**Plot Configuration**:
- X-axis: `total_score` (label: "Total Score (out of 500)")
- Y-axis: `price` (label: "List Price ($)")
- Color: `lot_sqft` (colorscale: `'Blues'` for PASS, `'Reds'` for FAIL)
- Symbol: `'circle'` for PASS, `'x'` for FAIL
- Size: Fixed at 12

**Annotations**:
1. **Median Lines**: Dashed gray lines at median score and median price
2. **Value Zone**: Green shaded rectangle for `score > 365` AND `price < 550000`
3. **Top 3 Labels**: Gold star markers on highest `value_ratio` PASS properties

**Hover Template**:
```
%{customdata[0]}<br>
Score: %{x}<br>
Price: $%{y:,}<br>
Lot: %{customdata[1]:,} sqft
```

**Output**:
- `value_spotter.html`: Interactive Plotly HTML
- `value_spotter.png`: Static export via `kaleido` (1200x800px)

---

### 3. Radar Comparison Charts (`radar_charts.py` → `radar_comparison.html`, `radar_comparison.png`)

**Library**: `plotly.graph_objects`

**Property Selection**: Top 3 PASSING properties by `total_score`

**Radar Axes** (5 dimensions, normalized 0-10):
```python
axes = {
    'Price Value': 10 - (price - min_price) / (max_price - min_price) * 10,
    'Location': score_location / 19,  # max ~190
    'Lot & Systems': score_lot_systems / 16,  # max ~160
    'Interior': score_interior / 19,  # max ~190
    'Schools': school_rating  # already 0-10
}
```

**Trace Configuration**:
```python
fig = go.Figure()
colors = ['#636EFA', '#EF553B', '#00CC96']

for i, prop in enumerate(top_3):
    fig.add_trace(go.Scatterpolar(
        r=[values],
        theta=['Price Value', 'Location', 'Lot & Systems', 'Interior', 'Schools'],
        fill='toself',
        fillcolor=f'rgba({rgb}, 0.25)',
        line=dict(color=colors[i]),
        name=prop['full_address'][:30]
    ))
```

**Layout**:
- Polar radialaxis range: `[0, 10]`
- Legend position: bottom
- Title: "Top 3 Properties: Trade-Off Comparison"

**Analysis Box** (annotation below chart):
```
Most Balanced: [property with lowest std dev across 5 axes]
Location Winner: [highest location score]
Value Leader: [highest value_ratio]
```

---

### 4. Sun Orientation Analysis (`sun_orientation_analysis.py` → `sun_orientation.png`, `orientation_estimates.json`, `orientation_impact.csv`)

**Library**: `matplotlib`, `pandas`

**Orientation Estimation Logic** (from address patterns):
```python
def estimate_orientation(address):
    street = address.split(',')[0]

    # N/S numbered streets run north-south, houses face E or W
    if re.match(r'^\d+\s+[NS]\s+\d+', street):
        return random.choice(['E', 'W'])

    # W/E named streets run east-west, houses face N or S
    if re.match(r'^\d+\s+[WE]\s+', street):
        return random.choice(['N', 'S'])  # bias toward N for AZ

    return 'Unknown'
```

**Cooling Cost Lookup Table**:
```python
COOLING_COSTS = {
    'N': 0,      # Best - minimal direct sun
    'NE': 100,
    'NW': 100,
    'E': 200,    # Morning sun
    'S': 300,    # Moderate
    'SE': 400,
    'SW': 400,
    'W': 600,    # Worst - afternoon sun in AZ
    'Unknown': 250
}
```

**Bar Chart Specification**:
- X-axis: Orientations in compass order `['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'Unknown']`
- Y-axis: Count of properties
- Colors: Gradient from green (N) to red (W) using colormap
- Title: "Property Distribution by Sun Orientation"
- Subtitle: "Estimated Annual Cooling Cost Impact"

---

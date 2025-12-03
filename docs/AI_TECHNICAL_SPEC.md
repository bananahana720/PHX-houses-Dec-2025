# PHX Home Analysis - AI-Optimized Technical Specification

> **Purpose**: This document enables an AI agent to fully recreate all visualizations and reports from the December 2025 Phoenix home buying analysis project. Copy this entire document into a prompt to regenerate all outputs.

---

## PROJECT OVERVIEW

**Domain**: Real estate analysis for first-time home buyers in Phoenix, AZ metro area
**Dataset**: 33 residential properties across Glendale, Phoenix, Peoria, Scottsdale
**Analysis Type**: Two-stage filtering (kill switches) + weighted scoring (500 points max)
**Output**: Interactive visualizations, automated reports, risk assessments, cost projections

---

## ENVIRONMENT SETUP

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Unix

# Install all dependencies
uv pip install pandas folium plotly kaleido geopy jinja2 matplotlib
```

**Working Directory**: Project root containing `phx_homes.csv` and `enrichment_data.json`

---

## DATA SCHEMA

### Input File 1: `phx_homes.csv`
```csv
street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address
4732 W Davis Rd,Glendale,AZ,85306,"$475,000",475000,4,2.0,2241,211.96,"4732 W Davis Rd, Glendale, AZ 85306"
```

**Required Columns**:
- `street`, `city`, `state`, `zip`: Address components
- `price_num`: Integer price in dollars
- `beds`: Integer bedroom count
- `baths`: Float bathroom count (2.5 = 2 full + 1 half)
- `sqft`: Integer living area
- `price_per_sqft`: Float calculated field
- `full_address`: Complete formatted address (used as primary key)

### Input File 2: `enrichment_data.json`
```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "lot_sqft": 8712,
    "year_built": 1973,
    "garage_spaces": 2,
    "sewer_type": "city",
    "tax_annual": 1850,
    "hoa_fee": 0,
    "commute_minutes": 35,
    "school_district": "Deer Valley Unified District",
    "school_rating": 8.1,
    "orientation": null,
    "distance_to_grocery_miles": 1.2,
    "distance_to_highway_miles": 2.5,
    "solar_status": null,
    "solar_lease_monthly": null,
    "has_pool": true,
    "pool_equipment_age": null,
    "roof_age": null,
    "hvac_age": null
  }
]
```

**Field Definitions**:
- `lot_sqft`: Total lot size from county assessor
- `year_built`: Construction year
- `garage_spaces`: Number of garage spaces (2 minimum required)
- `sewer_type`: "city" or "septic" (city required)
- `tax_annual`: Annual property tax in dollars
- `hoa_fee`: Monthly HOA fee (0 = no HOA, required for pass)
- `commute_minutes`: Drive time to Desert Ridge
- `school_rating`: GreatSchools 1-10 rating
- `orientation`: Cardinal direction house faces (N, S, E, W, NE, NW, SE, SW)
- `distance_to_grocery_miles`: Miles to nearest grocery store
- `distance_to_highway_miles`: Miles to nearest major highway
- `solar_status`: "owned", "leased", "none", or null
- `has_pool`: Boolean
- `pool_equipment_age`, `roof_age`, `hvac_age`: Integer years or null

---

## KILL SWITCH CRITERIA (HARD FILTERS)

Properties must pass ALL criteria or be excluded:

| Criterion | Rule | Failure Message |
|-----------|------|-----------------|
| HOA | `hoa_fee == 0 or hoa_fee is None` | "Must be NO HOA" |
| Sewer | `sewer_type == "city" or sewer_type is None` | "Must be City Sewer" |
| Garage | `garage_spaces >= 2 or garage_spaces is None` | "Minimum 2-Car Garage" |
| Beds | `beds >= 4` | "Minimum 4 Bedrooms" |
| Baths | `baths >= 2` | "Minimum 2 Bathrooms" |
| Lot Size | `7000 <= lot_sqft <= 15000 or lot_sqft is None` | "Lot 7,000-15,000 sqft" |
| Year Built | `year_built < 2024 or year_built is None` | "No New Builds (< 2024)" |

---

## SCORING SYSTEM (500 POINTS MAX)

### Section A: Location & Environment (150 points max)

| Factor | Weight | Scoring Function |
|--------|--------|------------------|
| School District | 5 | `school_rating` directly (1-10 scale) |
| Quietness | 5 | `>2mi: 10, 1-2mi: 7, 0.5-1mi: 5, <0.5mi: 3` |
| Safety | 5 | Default 5.0 (manual assessment) |
| Supermarket | 4 | `<=1mi: 10, 1-2mi: 8, 2-3mi: 6, >3mi: 4` |
| Walkability | 3 | Default 5.0 (manual assessment) |
| Orientation | 3 | `N:10, S:9, NE/NW:8, E:7, SE:6, SW:5, W:3` |

**Formula**: `sum(weight * score)` where score is 0-10

### Section B: Lot & Systems (160 points max)

| Factor | Weight | Scoring Function |
|--------|--------|------------------|
| Roof | 5 | `<=5yr: 10, 5-10yr: 8, 10-15yr: 6, 15-20yr: 4, >20yr: 2` |
| Backyard | 4 | `estimated_backyard = lot_sqft - (sqft * 0.6)`, then `>5000: 10, 3000-5000: 7, 1500-3000: 5, <1500: 3` |
| Plumbing/Elec | 4 | `>=2000: 9, 1990-1999: 7, 1980-1989: 5, <1980: 4` |
| Pool | 3 | If no pool: 5. If pool: `equip <=3yr: 9, 3-7yr: 7, >7yr: 4` |

### Section C: Interior & Features (190 points max)

| Factor | Weight | Default |
|--------|--------|---------|
| Kitchen | 4 | 5.0 (visual inspection) |
| Master Suite | 4 | 5.0 (visual inspection) |
| Natural Light | 3 | 5.0 (visual inspection) |
| High Ceilings | 3 | 5.0 (visual inspection) |
| Fireplace | 2 | 5.0 (check photos) |
| Laundry | 2 | 5.0 (check photos) |
| Aesthetics | 1 | 5.0 (subjective) |

### Tier Classification

- **Unicorn**: `total_score > 400`
- **Contender**: `300 <= total_score <= 400`
- **Pass**: `total_score < 300`

---

## VISUALIZATION SPECIFICATIONS

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

## REPORT SPECIFICATIONS

### 5. Traffic Light Deal Sheets (`deal_sheets.py` → `deal_sheets/*.html`)

**Library**: `jinja2`, `pandas`

**Output Structure**:
```
deal_sheets/
├── index.html           # Master list with links
├── 01_address_slug.html # Rank 1 property
├── 02_address_slug.html # Rank 2 property
└── ...                  # All 33 properties
```

**Deal Sheet HTML Template**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ address }} - Deal Sheet</title>
    <style>
        /* Traffic light colors */
        .pass { background: #d4edda; color: #155724; }
        .fail { background: #f8d7da; color: #721c24; }
        .unknown { background: #fff3cd; color: #856404; }

        /* Progress bars for scores */
        .score-bar {
            height: 20px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <h1>{{ address }}</h1>
    <div class="stats">
        <span>${{ price | format_number }}</span>
        <span>{{ total_score }}/500</span>
        <span class="tier-badge {{ tier.lower() }}">{{ tier }}</span>
    </div>

    <!-- SECTION 1: KILL SWITCH TABLE -->
    <table class="kill-switch">
        <tr>
            <th>Criterion</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
        {% for criterion in kill_switches %}
        <tr>
            <td>{{ criterion.name }}</td>
            <td class="{{ criterion.status }}">{{ criterion.status | upper }}</td>
            <td>{{ criterion.details }}</td>
        </tr>
        {% endfor %}
    </table>

    <!-- SECTION 2: SCORECARD -->
    <div class="scorecard">
        <div class="score-row">
            <span>Location</span>
            <div class="score-bar" style="width: {{ (score_location/150)*100 }}%"></div>
            <span>{{ score_location }}/150</span>
        </div>
        <!-- Repeat for Systems (160 max) and Interior (190 max) -->
    </div>

    <!-- SECTION 3: KEY METRICS -->
    <div class="metrics-grid">
        <div>Price/sqft: ${{ price_per_sqft }}</div>
        <div>Commute: {{ commute_minutes }} min</div>
        <div>Schools: {{ school_rating }}/10</div>
        <div>Tax: ${{ tax_annual }}/yr</div>
    </div>

    <!-- SECTION 4: FEATURES -->
    <div class="features">
        <h3>Present</h3>
        <ul>{% for f in features_present %}<li>{{ f }}</li>{% endfor %}</ul>
        <h3>Missing/Unknown</h3>
        <ul>{% for f in features_missing %}<li>{{ f }}</li>{% endfor %}</ul>
    </div>
</body>
</html>
```

**Kill Switch Evaluation**:
```python
def evaluate_kill_switches(prop):
    switches = [
        {'name': 'HOA', 'check': prop['hoa_fee'] == 0, 'details': f"${prop['hoa_fee']}/mo"},
        {'name': 'Sewer', 'check': prop['sewer_type'] == 'city', 'details': prop['sewer_type']},
        {'name': 'Garage', 'check': prop['garage_spaces'] >= 2, 'details': f"{prop['garage_spaces']} spaces"},
        {'name': 'Beds', 'check': prop['beds'] >= 4, 'details': f"{prop['beds']} beds"},
        {'name': 'Baths', 'check': prop['baths'] >= 2, 'details': f"{prop['baths']} baths"},
        {'name': 'Lot Size', 'check': 7000 <= prop['lot_sqft'] <= 15000, 'details': f"{prop['lot_sqft']:,} sqft"},
        {'name': 'Year Built', 'check': prop['year_built'] < 2024, 'details': str(prop['year_built'])}
    ]
    for s in switches:
        s['status'] = 'pass' if s['check'] else 'fail'
    return switches
```

---

### 6. Renovation Gap Report (`renovation_gap.py` → `renovation_gap_report.html`, `renovation_gap_report.csv`)

**Cost Estimation Rules** (Arizona-specific):
```python
def calculate_renovation_costs(prop):
    costs = {}

    # ROOF
    if prop['roof_age'] is None:
        costs['roof'] = 8000  # Contingency
    elif prop['roof_age'] <= 10:
        costs['roof'] = 0
    elif prop['roof_age'] <= 15:
        costs['roof'] = 5000
    elif prop['roof_age'] <= 20:
        costs['roof'] = 10000
    else:
        costs['roof'] = 18000

    # HVAC (Arizona: 12-15 year lifespan)
    if prop['hvac_age'] is None:
        costs['hvac'] = 4000
    elif prop['hvac_age'] <= 8:
        costs['hvac'] = 0
    elif prop['hvac_age'] <= 12:
        costs['hvac'] = 3000
    else:
        costs['hvac'] = 8000

    # POOL
    if not prop.get('has_pool'):
        costs['pool'] = 0
    elif prop.get('pool_equipment_age') is None:
        costs['pool'] = 5000
    elif prop['pool_equipment_age'] <= 5:
        costs['pool'] = 0
    elif prop['pool_equipment_age'] <= 10:
        costs['pool'] = 3000
    else:
        costs['pool'] = 8000

    # PLUMBING/ELECTRICAL (by year_built)
    if prop['year_built'] >= 2000:
        costs['plumbing'] = 0
    elif prop['year_built'] >= 1990:
        costs['plumbing'] = 2000
    elif prop['year_built'] >= 1980:
        costs['plumbing'] = 5000
    else:
        costs['plumbing'] = 10000

    # KITCHEN (older homes with neutral interior score)
    if prop['year_built'] < 1990 and prop.get('score_interior', 95) == 95:
        costs['kitchen'] = 15000
    else:
        costs['kitchen'] = 0

    costs['total'] = sum(costs.values())
    costs['true_cost'] = prop['price'] + costs['total']
    costs['delta_pct'] = (costs['total'] / prop['price']) * 100

    return costs
```

**HTML Report Features**:
- Sortable table columns
- Color coding: Green (<5%), Yellow (5-10%), Red (>10%) delta
- Bold highlight on "Best True Value" (lowest `true_cost` among PASS)
- Summary statistics at top

---

### 7. Due Diligence Risk Report (`risk_report.py` → `risk_report.html`, `risk_report.csv`, `risk_checklists/*.txt`)

**Risk Categories and Scoring**:
```python
def assess_risks(prop):
    risks = {}

    # NOISE RISK
    dist = prop.get('distance_to_highway_miles', 999)
    if dist < 0.5:
        risks['noise'] = {'level': 'HIGH', 'score': 3, 'desc': 'Highway noise likely audible'}
    elif dist < 1.0:
        risks['noise'] = {'level': 'MEDIUM', 'score': 1, 'desc': 'Some highway noise possible'}
    else:
        risks['noise'] = {'level': 'LOW', 'score': 0, 'desc': 'Quiet location'}

    # INFRASTRUCTURE RISK
    year = prop.get('year_built', 2000)
    if year < 1970:
        risks['infrastructure'] = {'level': 'HIGH', 'score': 3, 'desc': 'Pre-modern building codes'}
    elif year < 1990:
        risks['infrastructure'] = {'level': 'MEDIUM', 'score': 1, 'desc': 'May have dated systems'}
    else:
        risks['infrastructure'] = {'level': 'LOW', 'score': 0, 'desc': 'Modern construction'}

    # SOLAR RISK
    solar = prop.get('solar_status')
    if solar == 'leased':
        risks['solar'] = {'level': 'HIGH', 'score': 3, 'desc': 'Lease transfer required'}
    elif solar == 'owned':
        risks['solar'] = {'level': 'POSITIVE', 'score': 0, 'desc': 'Value-add, transferable'}
    else:
        risks['solar'] = {'level': 'LOW', 'score': 0, 'desc': 'No complications'}

    # COOLING COST RISK (orientation)
    orient = prop.get('orientation', 'Unknown')
    if orient in ['W', 'SW']:
        risks['cooling'] = {'level': 'HIGH', 'score': 3, 'desc': 'West-facing, high cooling'}
    elif orient in ['S', 'SE']:
        risks['cooling'] = {'level': 'MEDIUM', 'score': 1, 'desc': 'Moderate cooling impact'}
    else:
        risks['cooling'] = {'level': 'LOW', 'score': 0, 'desc': 'Favorable orientation'}

    # SCHOOL STABILITY
    rating = prop.get('school_rating', 7)
    if rating < 6.0:
        risks['schools'] = {'level': 'HIGH', 'score': 3, 'desc': 'Below-average schools'}
    elif rating < 7.5:
        risks['schools'] = {'level': 'MEDIUM', 'score': 1, 'desc': 'Average schools'}
    else:
        risks['schools'] = {'level': 'LOW', 'score': 0, 'desc': 'Strong school district'}

    # LOT SIZE MARGIN
    lot = prop.get('lot_sqft', 10000)
    if 7000 <= lot <= 7500:
        risks['lot_margin'] = {'level': 'MEDIUM', 'score': 1, 'desc': 'Near minimum requirement'}
    else:
        risks['lot_margin'] = {'level': 'LOW', 'score': 0, 'desc': 'Comfortable lot size'}

    risks['total_score'] = sum(r['score'] for r in risks.values())
    return risks
```

**Risk Tier Classification**:
- Low Risk: `total_score <= 2`
- Medium Risk: `3 <= total_score <= 5`
- High Risk: `total_score >= 6`

**Checklist Generation** (for properties with `total_score > 5`):
```python
def generate_checklist(prop, risks):
    checklist = []

    if risks['noise']['level'] == 'HIGH':
        checklist.append("[ ] Visit property during rush hour to assess noise levels")
        checklist.append("[ ] Check for sound-dampening windows")

    if risks['infrastructure']['level'] == 'HIGH':
        checklist.append("[ ] Order professional electrical inspection")
        checklist.append("[ ] Verify plumbing material (copper/PEX vs galvanized)")
        checklist.append("[ ] Check for asbestos/lead paint disclosures")

    if risks['solar']['level'] == 'HIGH':
        checklist.append("[ ] Request solar lease agreement copy")
        checklist.append("[ ] Calculate lease transfer fees")
        checklist.append("[ ] Verify remaining lease term")

    # ... additional checklist items per risk category

    return checklist
```

---

### 8. Master Dashboard (`dashboard.py` → `dashboard.html`)

**Purpose**: Single-page hub linking all visualizations and reports

**Layout Structure**:
```
┌─────────────────────────────────────────────────────────────┐
│                    HEADER + QUICK STATS                      │
├─────────────────────────────────────────────────────────────┤
│  TOP PICK  │  RUNNER UP  │  BUDGET PICK  │  KEY INSIGHT     │
├──────────────────────┬──────────────────────────────────────┤
│  Golden Zone Map     │  Value Spotter                       │
│  [iframe preview]    │  [iframe preview]                    │
│  [View Full Map]     │  [Analyze Values]                    │
├──────────────────────┼──────────────────────────────────────┤
│  Radar Comparison    │  Deal Sheets                         │
│  [thumbnail]         │  [icon]                              │
│  [Compare Top 3]     │  [Browse All 33]                     │
├──────────────────────┼──────────────────────────────────────┤
│  Renovation Gap      │  Risk Report                         │
│  [cost icon]         │  [warning icon]                      │
│  [Calculate Costs]   │  [View Risks]                        │
├─────────────────────────────────────────────────────────────┤
│                    TOP 5 PROPERTIES TABLE                    │
├─────────────────────────────────────────────────────────────┤
│                  KILL SWITCH SUMMARY TABLE                   │
├─────────────────────────────────────────────────────────────┤
│              [▶ Methodology Notes (collapsible)]             │
├─────────────────────────────────────────────────────────────┤
│                          FOOTER                              │
│              Download: CSV | JSON | PNG exports              │
└─────────────────────────────────────────────────────────────┘
```

**CSS Grid Layout**:
```css
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.card-header {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 15px;
    font-weight: bold;
}
```

**Executive Summary Logic**:
```python
def get_recommendations(df):
    passing = df[df['kill_switch_passed'] == 'PASS']

    # TOP PICK: Best balance of score and value
    top_pick = passing.nlargest(3, 'total_score').iloc[1]  # 2nd highest (often better value)

    # RUNNER UP: Highest score
    runner_up = passing.nlargest(1, 'total_score').iloc[0]

    # BUDGET PICK: Best score under $500k
    budget = passing[passing['price'] < 500000].nlargest(1, 'total_score').iloc[0]

    return top_pick, runner_up, budget
```

---

## GEOCODING SPECIFICATION

### Geocoder Implementation (`geocode_homes.py` → `geocoded_homes.json`)

**Library**: `geopy`

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
import pandas as pd
import time

class HomeGeocoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="phx_home_analyzer")
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=1.0  # Respect rate limits
        )
        self.cache_file = 'geocoded_homes.json'
        self.cache = self._load_cache()

    def _load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return {item['full_address']: item for item in data}
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(list(self.cache.values()), f, indent=2)

    def geocode_address(self, address):
        if address in self.cache:
            return self.cache[address]

        try:
            location = self.geocode(address)
            if location:
                result = {
                    'full_address': address,
                    'lat': location.latitude,
                    'lng': location.longitude
                }
                self.cache[address] = result
                self._save_cache()
                return result
        except Exception as e:
            print(f"Geocoding failed for {address}: {e}")

        return None

    def geocode_csv(self, csv_file):
        df = pd.read_csv(csv_file)
        results = []

        for address in df['full_address']:
            result = self.geocode_address(address)
            if result:
                results.append(result)
            time.sleep(0.1)  # Additional safety delay

        return results
```

**Expected Output** (`geocoded_homes.json`):
```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "lat": 33.6314,
    "lng": -112.1998
  }
]
```

**Phoenix Metro Coordinate Bounds** (for validation):
- Latitude: 33.3 - 33.75
- Longitude: -112.3 - -111.8

---

## DATA QUALITY VALIDATION

### Validation Script (`data_quality_report.py`)

```python
import json
import pandas as pd

def validate_enrichment_data(filepath):
    with open(filepath) as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    report = {
        'total_properties': len(df),
        'field_completeness': {},
        'critical_issues': [],
        'warnings': []
    }

    # Field completeness
    fields = ['lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
              'tax_annual', 'hoa_fee', 'commute_minutes', 'school_rating',
              'orientation', 'distance_to_grocery_miles', 'distance_to_highway_miles',
              'solar_status', 'has_pool', 'pool_equipment_age', 'roof_age', 'hvac_age']

    for field in fields:
        non_null = df[field].notna().sum()
        report['field_completeness'][field] = {
            'count': non_null,
            'percentage': round(non_null / len(df) * 100, 1)
        }

    # Kill switch violations
    hoa_violations = df[df['hoa_fee'] > 0]
    for _, row in hoa_violations.iterrows():
        report['critical_issues'].append({
            'address': row['full_address'],
            'issue': f"HOA fee ${row['hoa_fee']}/month"
        })

    # Lot size warnings
    small_lots = df[(df['lot_sqft'] < 7000) & (df['lot_sqft'].notna())]
    for _, row in small_lots.iterrows():
        report['warnings'].append({
            'address': row['full_address'],
            'issue': f"Lot size {row['lot_sqft']} sqft below 7,000 minimum"
        })

    return report
```

---

## REGENERATION COMMAND SEQUENCE

To recreate all outputs from scratch:

```bash
# 1. Validate data quality
python data_quality_report.py

# 2. Geocode addresses (cached, only runs once)
python geocode_homes.py

# 3. Run main analysis pipeline
python phx_home_analyzer.py

# 4. Generate visualizations
python golden_zone_map.py
python value_spotter.py
python radar_charts.py
python sun_orientation_analysis.py

# 5. Generate reports
python deal_sheets.py
python renovation_gap.py
python risk_report.py

# 6. Build master dashboard
python dashboard.py

# 7. Open dashboard
start dashboard.html
```

---

## FILE MANIFEST

After full regeneration, the following files should exist:

```
PHX-houses-Dec-2025/
├── phx_homes.csv                    # Input: Raw listings
├── enrichment_data.json             # Input: Manual enrichment
├── phx_home_analyzer.py             # Core analysis pipeline
├── phx_homes_ranked.csv             # Output: Ranked properties
│
├── data_quality_report.py           # Data validation script
├── data_quality_report.txt          # Validation output
│
├── geocode_homes.py                 # Geocoding script
├── geocoded_homes.json              # Geocoded coordinates
│
├── golden_zone_map.py               # Map generator
├── golden_zone_map.html             # Interactive map (124 KB)
│
├── value_spotter.py                 # Scatter plot generator
├── value_spotter.html               # Interactive plot (4.7 MB)
├── value_spotter.png                # Static image (86 KB)
│
├── radar_charts.py                  # Radar chart generator
├── radar_comparison.html            # Interactive radar (4.6 MB)
├── radar_comparison.png             # Static image (109 KB)
│
├── sun_orientation_analysis.py      # Orientation analyzer
├── sun_orientation.png              # Bar chart (168 KB)
├── orientation_estimates.json       # Estimated orientations
├── orientation_impact.csv           # Cooling cost impacts
│
├── deal_sheets.py                   # Deal sheet generator
├── deal_sheets/
│   ├── index.html                   # Master list
│   └── *.html                       # 33 individual sheets
│
├── renovation_gap.py                # Cost calculator
├── renovation_gap_report.html       # Interactive table (34 KB)
├── renovation_gap_report.csv        # Cost data
│
├── risk_report.py                   # Risk assessor
├── risk_report.html                 # Risk table (52 KB)
├── risk_report.csv                  # Risk data
├── risk_checklists/
│   └── *.txt                        # Checklists for high-risk properties
│
├── dashboard.py                     # Dashboard generator
├── dashboard.html                   # Master hub (25 KB)
│
└── AI_TECHNICAL_SPEC.md             # This document
```

---

## VERIFICATION CHECKLIST

After regeneration, verify:

- [ ] `phx_homes_ranked.csv` has 33 rows with scores and kill switch results
- [ ] `geocoded_homes.json` has 28+ entries with valid Phoenix-area coordinates
- [ ] `golden_zone_map.html` opens in browser with green/red markers
- [ ] `value_spotter.html` shows scatter plot with "Value Zone" shading
- [ ] `radar_comparison.html` shows 3 overlapping radar traces
- [ ] `deal_sheets/` contains 34 HTML files (33 sheets + index)
- [ ] `renovation_gap_report.html` shows sortable table with cost estimates
- [ ] `risk_report.html` shows 6-column risk assessment
- [ ] `dashboard.html` links to all other files correctly
- [ ] All iframe previews load in dashboard

---

## EXTENSION POINTS

To add new properties:

1. Add row to `phx_homes.csv` with listing data
2. Add entry to `enrichment_data.json` with research data
3. Run `python geocode_homes.py` to geocode new address
4. Run `python phx_home_analyzer.py` to recalculate scores
5. Regenerate all visualizations and reports

To modify scoring weights:

1. Edit `phx_home_analyzer.py` section constants
2. Adjust weight tuples in `section_a`, `section_b`, `section_c`
3. Regenerate `phx_homes_ranked.csv`
4. Regenerate visualizations that depend on scores

To add new risk category:

1. Edit `risk_report.py` `assess_risks()` function
2. Add new risk evaluation logic
3. Update HTML template to include new column
4. Update checklist generation for new risk type

---

*Document Version: 1.0 | Generated: November 2025 | Compatible with Python 3.10+*

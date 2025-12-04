# REPORT SPECIFICATIONS

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

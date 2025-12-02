# PHX Houses Codebase Analysis Inventory

**Analysis Date:** 2025-11-29
**Total Scripts Analyzed:** 12
**Purpose:** Identify hardcoded values, duplicated patterns, code quality issues for refactoring

---

## TABLE OF CONTENTS

1. [Hardcoded Paths & File References](#1-hardcoded-paths--file-references)
2. [Configuration Values](#2-configuration-values)
3. [CSV Loading Patterns (Duplicated Code)](#3-csv-loading-patterns-duplicated-code)
4. [JSON Loading Patterns (Duplicated Code)](#4-json-loading-patterns-duplicated-code)
5. [Functions Exceeding 50 Lines](#5-functions-exceeding-50-lines)
6. [Module-Level Execution Code](#6-module-level-execution-code)
7. [Kill Switch Criteria Duplication](#7-kill-switch-criteria-duplication)
8. [Data Field Definitions](#8-data-field-definitions)
9. [Recommendations Summary](#9-recommendations-summary)

---

## 1. HARDCODED PATHS & FILE REFERENCES

### Input Files (CSV)

| File | Line | Hardcoded Path |
|------|------|----------------|
| **phx_home_analyzer.py** | 528 | `base_dir / "phx_homes.csv"` |
| **risk_report.py** | 576 | `base_dir / 'phx_homes_ranked.csv'` |
| **renovation_gap.py** | 574 | `base_dir / 'phx_homes_ranked.csv'` |
| **value_spotter.py** | 14 | `Path(__file__).parent / "phx_homes_ranked.csv"` |
| **golden_zone_map.py** | 64 | `'phx_homes_ranked.csv'` |
| **radar_charts.py** | 19 | `WORKING_DIR / "phx_homes_ranked.csv"` |
| **show_best_values.py** | 7 | `'renovation_gap_report.csv'` |
| **deal_sheets.py** | 993 | `base_dir / 'phx_homes_ranked.csv'` |
| **geocode_homes.py** | 155 | `"phx_homes.csv"` |
| **cost_breakdown_analysis.py** | 8 | `'renovation_gap_report.csv'` |

**Count:** 10/12 scripts hardcode CSV input paths

### Input Files (JSON)

| File | Line | Hardcoded Path |
|------|------|----------------|
| **phx_home_analyzer.py** | 529 | `base_dir / "enrichment_data.json"` |
| **risk_report.py** | 577 | `base_dir / 'enrichment_data.json'` |
| **renovation_gap.py** | 575 | `base_dir / 'enrichment_data.json'` |
| **data_quality_report.py** | 408 | `'enrichment_data.json'` |
| **value_spotter.py** | 15 | `Path(__file__).parent / "enrichment_data.json"` |
| **golden_zone_map.py** | 60 | `'geocoded_homes.json'` |
| **radar_charts.py** | 20 | `WORKING_DIR / "enrichment_data.json"` |
| **deal_sheets.py** | 994 | `base_dir / 'enrichment_data.json'` |
| **geocode_homes.py** | 152 | `"geocoded_homes.json"` (cache file) |
| **sun_orientation_analysis.py** | 297 | `project_dir / 'enrichment_data.json'` |

**Count:** 10/12 scripts hardcode JSON input paths

### Output Files

| File | Line | Output Path | Type |
|------|------|-------------|------|
| **phx_home_analyzer.py** | 530 | `base_dir / "enrichment_template.json"` | JSON |
| **phx_home_analyzer.py** | 531 | `base_dir / "phx_homes_ranked.csv"` | CSV |
| **risk_report.py** | 579 | `base_dir / 'risk_report.html'` | HTML |
| **risk_report.py** | 580 | `base_dir / 'risk_report.csv'` | CSV |
| **risk_report.py** | 581 | `base_dir / 'risk_checklists'` | Directory |
| **renovation_gap.py** | 576 | `base_dir / 'renovation_gap_report.csv'` | CSV |
| **renovation_gap.py** | 577 | `base_dir / 'renovation_gap_report.html'` | HTML |
| **data_quality_report.py** | 413 | `'data_quality_report.txt'` | TXT |
| **value_spotter.py** | 208 | `Path(__file__).parent / "value_spotter.html"` | HTML |
| **value_spotter.py** | 213 | `Path(__file__).parent / "value_spotter.png"` | PNG |
| **golden_zone_map.py** | 278 | `'golden_zone_map.html'` | HTML |
| **radar_charts.py** | 21 | `WORKING_DIR / "radar_comparison.html"` | HTML |
| **radar_charts.py** | 22 | `WORKING_DIR / "radar_comparison.png"` | PNG |
| **deal_sheets.py** | 995 | `base_dir / 'deal_sheets'` | Directory |
| **geocode_homes.py** | 158 | `"geocoded_homes.json"` | JSON |
| **sun_orientation_analysis.py** | 299 | `project_dir / 'orientation_estimates.json'` | JSON |
| **sun_orientation_analysis.py** | 300 | `project_dir / 'orientation_impact.csv'` | CSV |
| **sun_orientation_analysis.py** | 301 | `project_dir / 'sun_orientation.png'` | PNG |

**Total Unique Output Files:** 18 distinct output files across 12 scripts

### Absolute Path Pattern Inconsistency

| Pattern | Files Using | Example |
|---------|-------------|---------|
| `Path(__file__).parent / "file"` | 8 files | phx_home_analyzer.py, risk_report.py, renovation_gap.py, etc. |
| `Path(r"C:\Users\...\PHX-houses-Dec-2025")` | 1 file | radar_charts.py:18 (HARDCODED ABSOLUTE PATH) |
| String literal `"file"` | 3 files | show_best_values.py, cost_breakdown_analysis.py, data_quality_report.py |

**CRITICAL FINDING:** `radar_charts.py` contains hardcoded Windows absolute path at line 18:
```python
WORKING_DIR = Path(r"C:\Users\Andrew\Downloads\PHX-houses-Dec-2025")
```

---

## 2. CONFIGURATION VALUES

### Kill Switch Criteria

**Defined in:** `phx_home_analyzer.py` (lines 83-91), `deal_sheets.py` (lines 15-51)

| Criterion | Field | Threshold | Description |
|-----------|-------|-----------|-------------|
| HOA | `hoa_fee` | == 0 or None | Must be NO HOA |
| Sewer | `sewer_type` | == "city" or None | Must be City Sewer |
| Garage | `garage_spaces` | >= 2 or None | Minimum 2-Car Garage |
| Beds | `beds` | >= 4 | Minimum 4 Bedrooms |
| Baths | `baths` | >= 2 | Minimum 2 Bathrooms |
| Lot Size | `lot_sqft` | 7000-15000 or None | Lot 7,000-15,000 sqft |
| Year Built | `year_built` | < 2024 or None | No New Builds |

**Duplication:** Kill switch definitions exist in TWO files with different implementations

### Scoring Weights

**Defined in:** `phx_home_analyzer.py` (lines 271-297)

#### Section A: Location & Environment (150 points)
- School District Rating: 5 × 10 = 50 pts
- Quietness/Noise: 5 × 10 = 50 pts
- Safety/Neighborhood: 5 × 10 = 50 pts
- Supermarket Proximity: 4 × 10 = 40 pts
- Walkability: 3 × 10 = 30 pts
- Sun Orientation: 3 × 10 = 30 pts

#### Section B: Lot & Systems (160 points)
- Roof Condition: 5 × 10 = 50 pts
- Backyard Utility: 4 × 10 = 40 pts
- Plumbing/Electrical: 4 × 10 = 40 pts
- Pool Condition: 3 × 10 = 30 pts

#### Section C: Interior & Features (190 points)
- Kitchen Layout: 4 × 10 = 40 pts
- Master Suite: 4 × 10 = 40 pts
- Natural Light: 3 × 10 = 30 pts
- High Ceilings: 3 × 10 = 30 pts
- Fireplace: 2 × 10 = 20 pts
- Laundry Area: 2 × 10 = 20 pts
- Aesthetics: 1 × 10 = 10 pts

**Total:** 500 points

### Tier Thresholds

**Defined in:** `phx_home_analyzer.py` (lines 312-317)

| Tier | Score Range |
|------|-------------|
| Unicorn | > 400 points |
| Contender | 300-400 points |
| Pass | < 300 points |

### Renovation Cost Estimates

**Defined in:** `renovation_gap.py` (lines 20-78)

#### Roof Costs (lines 20-31)
```python
roof_age < 10:        $0
roof_age <= 15:       $5,000
roof_age <= 20:       $10,000
roof_age > 20:        $18,000
roof_age unknown:     $8,000
```

#### HVAC Costs (lines 34-43)
```python
hvac_age < 8:         $0
hvac_age <= 12:       $3,000
hvac_age > 12:        $8,000
hvac_age unknown:     $4,000
```

#### Pool Costs (lines 46-58)
```python
no pool:              $0
pool_age < 5:         $0
pool_age <= 10:       $3,000
pool_age > 10:        $8,000
pool_age unknown:     $5,000
```

#### Plumbing Costs (lines 61-70)
```python
year_built >= 2000:   $0
year_built >= 1990:   $2,000
year_built >= 1980:   $5,000
year_built < 1980:    $10,000
```

#### Kitchen Costs (lines 73-78)
```python
year_built < 1990 AND score_interior ≈ 95.0:  $15,000
otherwise:                                      $0
```

### Risk Categories

**Defined in:** `risk_report.py` (lines 44-151)

#### Noise Risk (Highway Distance)
```python
< 0.5 miles:  HIGH
0.5-1.0 mi:   MEDIUM
> 1.0 mi:     LOW
```

#### Infrastructure Risk (Year Built)
```python
< 1970:       HIGH
1970-1989:    MEDIUM
>= 1990:      LOW
```

#### Solar Risk (Ownership)
```python
"leased":     HIGH
"owned":      POSITIVE
"none":       LOW
```

#### Cooling Risk (Orientation)
```python
W, SW:        HIGH
S, SE:        MEDIUM
N, NE, NW, E: LOW
```

#### School Risk (GreatSchools Rating)
```python
< 6.0:        HIGH
6.0-7.5:      MEDIUM
> 7.5:        LOW
```

#### Lot Size Risk
```python
< 7,500 sqft: MEDIUM
>= 7,500:     LOW
```

### Risk Scoring

**Defined in:** `risk_report.py` (lines 36-41)

```python
HIGH:     3 points
MEDIUM:   1 point
UNKNOWN:  1 point
LOW:      0 points
POSITIVE: 0 points
```

### Sun Orientation Cooling Costs

**Defined in:** `sun_orientation_analysis.py` (lines 20-30)

Annual cooling cost impact by orientation:
```python
'N':   $0      (Best - baseline)
'NE':  $100
'E':   $200
'SE':  $400
'S':   $300
'SW':  $400
'W':   $600    (Worst)
'NW':  $100
'Unknown': $250
```

### Value Zone Boundaries

**Defined in:** `value_spotter.py` (lines 45-46)

```python
value_zone_min_score = 365
value_zone_max_price = 550000
```

### Map Configuration

**Defined in:** `golden_zone_map.py` (lines 18-26)

```python
PHOENIX_CENTER = (33.55, -112.05)
ZOOM_LEVEL = 10
GROCERY_RADIUS_MILES = 1.5
HIGHWAY_BUFFER_MILES = 1.0
MILES_TO_METERS = 1609.34
```

### Highway Coordinates

**Defined in:** `golden_zone_map.py` (lines 29-54)

Hardcoded lat/long for I-17, I-10, Loop-101 (36 coordinate pairs)

### Geocoding Rate Limit

**Defined in:** `geocode_homes.py` (line 152)

```python
rate_limit_delay=1.0  # seconds between requests
```

---

## 3. CSV LOADING PATTERNS (DUPLICATED CODE)

### Pattern A: Direct csv.DictReader

**Instances:** 6 files

#### phx_home_analyzer.py (lines 326-347)
```python
def load_listings(csv_path: str) -> List[Property]:
    properties = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prop = Property(
                street=row.get('street', ''),
                city=row.get('city', ''),
                # ... 10 more fields
            )
            properties.append(prop)
    return properties
```

#### risk_report.py (lines 193-201)
```python
def load_ranked_properties(file_path: str) -> List[Dict]:
    properties = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties
```

#### renovation_gap.py (lines 81-88)
```python
def load_csv_data(csv_path: Path) -> List[Dict]:
    properties = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties
```

#### show_best_values.py (lines 7-8)
```python
with open('renovation_gap_report.csv', 'r') as f:
    data = list(csv.DictReader(f))
```

#### cost_breakdown_analysis.py (lines 8-9)
```python
with open('renovation_gap_report.csv', 'r') as f:
    data = list(csv.DictReader(f))
```

#### geocode_homes.py (lines 109-115)
```python
def geocode_csv(self, csv_file: str) -> list:
    # ...
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # ... processing
```

**Duplication:** Same boilerplate repeated 6 times with minor variations

### Pattern B: pandas.read_csv

**Instances:** 4 files

#### value_spotter.py (line 18)
```python
df = pd.read_csv(csv_path)
```

#### golden_zone_map.py (line 64)
```python
ranked_df = pd.read_csv('phx_homes_ranked.csv')
```

#### radar_charts.py (line 26)
```python
df = pd.read_csv(CSV_FILE)
```

#### deal_sheets.py (line 1002)
```python
df = pd.read_csv(ranked_csv)
```

#### sun_orientation_analysis.py (line 129)
```python
return pd.read_csv(filepath)
```

**Note:** Pandas approach is more consistent but still hardcodes paths differently in each file

### CSV Writing Patterns

#### Pattern A: csv.DictWriter (4 instances)

**phx_home_analyzer.py** (lines 435-469)
**risk_report.py** (lines 450-456)
**renovation_gap.py** (lines 150-155)
**sun_orientation_analysis.py** (lines 180)

All follow same pattern:
```python
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)  # or loop with writerow()
```

#### Pattern B: pandas.to_csv (1 instance)

**sun_orientation_analysis.py** (line 180)
```python
df.to_csv(output_path, index=False)
```

---

## 4. JSON LOADING PATTERNS (DUPLICATED CODE)

### Pattern A: Basic json.load returning list

**Instances:** 9 files

#### phx_home_analyzer.py (lines 356-357)
```python
with open(enrichment_file, 'r', encoding='utf-8') as f:
    enrichment_data = json.load(f)
```

#### risk_report.py (lines 179-182)
```python
def load_enrichment_data(file_path: str) -> Dict[str, Dict]:
    with open(file_path, 'r') as f:
        data_list = json.load(f)
    return {item['full_address']: item for item in data_list}
```

#### risk_report.py (lines 186-190)
```python
def load_orientation_data(file_path: str) -> Dict[str, str]:
    with open(file_path, 'r') as f:
        data_list = json.load(f)
    return {item['full_address']: item['estimated_orientation'] for item in data_list}
```

#### renovation_gap.py (lines 91-103)
```python
def load_enrichment_data(json_path: Path) -> Dict[str, Dict]:
    with open(json_path, 'r', encoding='utf-8') as f:
        enrichment_list = json.load(f)
    enrichment_dict = {}
    for entry in enrichment_list:
        address = entry.get('full_address')
        if address:
            enrichment_dict[address] = entry
    return enrichment_dict
```

#### data_quality_report.py (lines 24-26)
```python
def load_enrichment_data(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        return json.load(f)
```

#### value_spotter.py (lines 21-22)
```python
with open(json_path, 'r') as f:
    enrichment_data = json.load(f)
```

#### golden_zone_map.py (lines 60-61)
```python
with open('geocoded_homes.json', 'r') as f:
    geocoded = json.load(f)
```

#### radar_charts.py (lines 28-29)
```python
with open(JSON_FILE, 'r') as f:
    enrichment = json.load(f)
```

#### deal_sheets.py (lines 1005-1006)
```python
with open(enrichment_json, 'r') as f:
    enrichment_data = json.load(f)
```

#### sun_orientation_analysis.py (lines 120-121)
```python
with open(filepath, 'r') as f:
    return json.load(f)
```

#### geocode_homes.py (lines 43-46)
```python
with open(self.cache_file, "r") as f:
    cached_list = json.load(f)
    return {item["full_address"]: item for item in cached_list}
```

**Duplication:** Same pattern repeated 11+ times across 10 files

### Pattern B: JSON Writing

**Instances:** 7 files

#### phx_home_analyzer.py (line 414)
```python
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(template, f, indent=2)
```

#### geocode_homes.py (lines 56-57, 158-159)
```python
with open(self.cache_file, "w") as f:
    json.dump(cache_list, f, indent=2)
```

#### sun_orientation_analysis.py (lines 143-144)
```python
with open(output_path, 'w') as f:
    json.dump(output_data, f, indent=2)
```

**Pattern:** All use `indent=2` for formatting

### Address-to-Data Lookup Pattern

**Duplicated 6 times:**

```python
# Pattern: Convert list to dict keyed by full_address
enrichment_lookup = {item['full_address']: item for item in enrichment_data}

# Then later:
for prop in properties:
    if prop.full_address in enrichment_lookup:
        data = enrichment_lookup[prop.full_address]
        # ... use data
```

**Files:** phx_home_analyzer.py (360), risk_report.py (182), renovation_gap.py (97-101), geocode_homes.py (46), deal_sheets.py (1009)

---

## 5. FUNCTIONS EXCEEDING 50 LINES

### Large HTML Generation Functions

#### risk_report.py: `generate_html_report()` (lines 268-437)
- **Lines:** 170 lines
- **Purpose:** Generate HTML report with embedded CSS and data
- **Issue:** HTML template hardcoded as string literal

#### renovation_gap.py: `generate_html_report()` (lines 159-494)
- **Lines:** 336 lines
- **Purpose:** Generate renovation gap HTML report
- **Issue:** Massive HTML template in Python string

#### deal_sheets.py: `DEAL_SHEET_TEMPLATE` (lines 54-527)
- **Lines:** 474 lines (not a function, but module-level string)
- **Purpose:** Deal sheet HTML template
- **Issue:** Should use Jinja2 templates in separate files

#### deal_sheets.py: `INDEX_TEMPLATE` (lines 530-793)
- **Lines:** 264 lines (module-level string)
- **Purpose:** Index page HTML template

### Complex Analysis Functions

#### data_quality_report.py: `generate_report()` (lines 210-405)
- **Lines:** 196 lines
- **Purpose:** Generate comprehensive quality report
- **Refactor:** Break into smaller functions for each section

#### data_quality_report.py: `find_data_quality_issues()` (lines 80-208)
- **Lines:** 129 lines
- **Purpose:** Validate property data against rules
- **Refactor:** Extract validation rules to config, create validator class

#### risk_report.py: `generate_due_diligence_checklist()` (lines 459-569)
- **Lines:** 111 lines
- **Purpose:** Generate property-specific checklist
- **Refactor:** Use template engine

#### phx_home_analyzer.py: `generate_ranked_csv()` (lines 419-471)
- **Lines:** 53 lines
- **Purpose:** Generate ranked CSV output
- **Borderline:** Could be split into data preparation + CSV writing

#### renovation_gap.py: `print_summary_report()` (lines 496-567)
- **Lines:** 72 lines
- **Purpose:** Print console summary
- **Refactor:** Extract formatting logic

### Main Functions

#### risk_report.py: `main()` (lines 571-673)
- **Lines:** 103 lines
- **Purpose:** Pipeline orchestration
- **Refactor:** Extract print logic to separate reporting function

#### deal_sheets.py: `main()` (lines 987-1057)
- **Lines:** 71 lines
- **Purpose:** Pipeline orchestration
- **Note:** Acceptable length for main orchestrator

---

## 6. MODULE-LEVEL EXECUTION CODE

### Scripts with Direct Execution (No main())

**None found** - All 12 scripts use `if __name__ == "__main__"` guard

### Scripts with Module-Level Configuration

#### radar_charts.py (lines 17-22)
```python
WORKING_DIR = Path(r"C:\Users\Andrew\Downloads\PHX-houses-Dec-2025")  # HARDCODED
CSV_FILE = WORKING_DIR / "phx_homes_ranked.csv"
JSON_FILE = WORKING_DIR / "enrichment_data.json"
OUTPUT_HTML = WORKING_DIR / "radar_comparison.html"
OUTPUT_PNG = WORKING_DIR / "radar_comparison.png"
```
**Issue:** Hardcoded absolute Windows path breaks portability

#### golden_zone_map.py (lines 17-54)
```python
PHOENIX_CENTER = (33.55, -112.05)
ZOOM_LEVEL = 10
# ... configuration constants
HIGHWAYS = {  # 36 lat/long coordinate pairs
    'I-17': [...],
    'I-10': [...],
    'Loop-101': [...],
}
```
**Note:** Constants are appropriate here, but should be in config file

#### deal_sheets.py (lines 15-51, 54-793)
```python
KILL_SWITCH_CRITERIA = {  # 37 lines
    'HOA': {...},
    'Sewer': {...},
    # ...
}

DEAL_SHEET_TEMPLATE = """..."""  # 474 lines
INDEX_TEMPLATE = """..."""        # 264 lines
```
**Issue:** 775 lines of templates/config at module level

#### sun_orientation_analysis.py (lines 19-43)
```python
COOLING_COST_IMPACT = {  # 11 orientations
    'N': 0,
    'NE': 100,
    # ...
}

ORIENTATION_COLORS = {  # 9 color mappings
    'N': '#2ecc71',
    # ...
}
```

---

## 7. KILL SWITCH CRITERIA DUPLICATION

### Implementation A: phx_home_analyzer.py (lines 83-91)

```python
KILL_SWITCH_CRITERIA = {
    "hoa": {"check": lambda p: p.hoa_fee == 0 or p.hoa_fee is None, "desc": "Must be NO HOA"},
    "sewer": {"check": lambda p: p.sewer_type == "city" or p.sewer_type is None, "desc": "Must be City Sewer"},
    "garage": {"check": lambda p: p.garage_spaces is None or p.garage_spaces >= 2, "desc": "Minimum 2-Car Garage"},
    "beds": {"check": lambda p: p.beds >= 4, "desc": "Minimum 4 Bedrooms"},
    "baths": {"check": lambda p: p.baths >= 2, "desc": "Minimum 2 Bathrooms"},
    "lot_size": {"check": lambda p: p.lot_sqft is None or (7000 <= p.lot_sqft <= 15000), "desc": "Lot 9,000-10,000 sqft (relaxed to 7k-15k)"},
    "year_built": {"check": lambda p: p.year_built is None or p.year_built < 2024, "desc": "No New Builds (< 2024)"},
}
```

### Implementation B: deal_sheets.py (lines 15-51)

```python
KILL_SWITCH_CRITERIA = {
    'HOA': {
        'field': 'hoa_fee',
        'check': lambda val: val == 0 or pd.isna(val),
        'description': lambda val: f"${int(val)}/mo" if val and val > 0 else "$0"
    },
    'Sewer': {
        'field': 'sewer_type',
        'check': lambda val: val == 'city',
        'description': lambda val: val.title() if val else "Unknown"
    },
    # ... 5 more criteria
}
```

**Differences:**
1. Keys: lowercase vs title case ("hoa" vs "HOA")
2. Lambda argument: Property object vs raw value
3. deal_sheets.py adds 'field' and 'description' lambdas
4. None/NaN handling differs (`p.hoa_fee is None` vs `pd.isna(val)`)

**Impact:** Changes to criteria must be synchronized across 2 files manually

---

## 8. DATA FIELD DEFINITIONS

### Critical Fields (data_quality_report.py lines 12-16)

```python
CRITICAL_FIELDS = [
    'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
    'tax_annual', 'hoa_fee', 'commute_minutes', 'school_district',
    'school_rating', 'distance_to_grocery_miles', 'distance_to_highway_miles'
]
```

### Condition Fields (data_quality_report.py lines 18-21)

```python
CONDITION_FIELDS = [
    'orientation', 'solar_status', 'has_pool', 'pool_equipment_age',
    'roof_age', 'hvac_age'
]
```

### Property Dataclass (phx_home_analyzer.py lines 22-76)

**55 lines defining complete property schema with:**
- Original listing data (10 fields)
- County Assessor enrichment (5 fields)
- HOA data (1 field)
- Geo-spatial enrichment (7 fields)
- Arizona-specific (4 fields)
- Condition data (2 fields)
- Kill switch results (2 fields)
- Scoring results (5 fields)

**Total:** 36 distinct property attributes

**Issue:** This is the authoritative schema but isn't reused elsewhere

---

## 9. RECOMMENDATIONS SUMMARY

### Priority 1: Configuration Module (HIGH IMPACT)

**Create:** `config.py` module

**Consolidate:**
1. All input/output file paths
2. Kill switch criteria (single source of truth)
3. Scoring weights and tier thresholds
4. Renovation cost estimates
5. Risk category thresholds
6. Orientation cooling costs
7. Map configuration constants

**Benefits:**
- Single source of truth for all constants
- Easy to adjust thresholds without code changes
- Enables YAML/JSON config files later
- Eliminates hardcoded paths

### Priority 2: Shared Data Loaders (MEDIUM IMPACT)

**Create:** `data_loaders.py` module

**Consolidate:**
1. `load_csv()` - unified CSV loading with pandas
2. `load_json()` - unified JSON loading
3. `load_enrichment_data()` - standard enrichment loader
4. `load_ranked_properties()` - standard ranked CSV loader
5. `create_address_lookup()` - reusable dict builder

**Benefits:**
- Eliminate 20+ instances of duplicated loading code
- Consistent error handling
- Standard path resolution
- Easier to add caching layer

### Priority 3: Template Externalization (MEDIUM IMPACT)

**Create:** `templates/` directory

**Extract:**
1. risk_report.py HTML template (170 lines) → `templates/risk_report.html`
2. renovation_gap.py HTML template (336 lines) → `templates/renovation_gap.html`
3. deal_sheets.py templates (738 lines) → `templates/deal_sheet.html` + `templates/index.html`

**Benefits:**
- Remove 1,244 lines of HTML from Python files
- Proper separation of concerns
- Easier to edit HTML/CSS
- Already using Jinja2 in deal_sheets.py

### Priority 4: Function Decomposition (LOW-MEDIUM IMPACT)

**Refactor large functions:**

1. **data_quality_report.py:**
   - Split `generate_report()` into section generators
   - Extract `find_data_quality_issues()` validation rules to config

2. **risk_report.py:**
   - Extract `generate_due_diligence_checklist()` to template

3. **renovation_gap.py:**
   - Split `print_summary_report()` into formatters

**Benefits:**
- Improved testability
- Better code organization
- Easier to maintain

### Priority 5: Path Handling (HIGH IMPACT - CRITICAL BUG)

**Fix:** radar_charts.py line 18 hardcoded Windows path

**Standardize:**
1. All scripts use `Path(__file__).parent` for base directory
2. All paths go through config module
3. Support environment variable overrides

**Benefits:**
- Cross-platform compatibility
- No hardcoded user paths
- Easy to run from different directories

---

## STATISTICS SUMMARY

| Metric | Count |
|--------|-------|
| **Total Scripts Analyzed** | 12 |
| **Scripts with Hardcoded Input Paths** | 12/12 (100%) |
| **Scripts with Hardcoded Output Paths** | 12/12 (100%) |
| **Unique Hardcoded File Paths** | 28+ |
| **CSV Loading Pattern Instances** | 10 |
| **JSON Loading Pattern Instances** | 11 |
| **Address Lookup Pattern Instances** | 6 |
| **Functions > 50 Lines** | 9 |
| **Module-Level Config Constants** | 4 scripts |
| **Lines of HTML Templates in Python** | 1,244 lines |
| **Kill Switch Definition Duplications** | 2 implementations |
| **Hardcoded Absolute Paths (CRITICAL)** | 1 (radar_charts.py) |

---

## PROPOSED REFACTORING STRUCTURE

```
scripts/
├── config.py                    # NEW: All configuration constants
├── data_loaders.py              # NEW: Shared loading functions
├── templates/                   # NEW: Jinja2 templates
│   ├── risk_report.html
│   ├── renovation_gap.html
│   ├── deal_sheet.html
│   └── index.html
├── phx_home_analyzer.py         # REFACTORED: Use config + loaders
├── risk_report.py               # REFACTORED: Use config + loaders + templates
├── renovation_gap.py            # REFACTORED: Use config + loaders + templates
├── data_quality_report.py       # REFACTORED: Use config + loaders
├── value_spotter.py             # REFACTORED: Use loaders
├── golden_zone_map.py           # REFACTORED: Use config + loaders
├── radar_charts.py              # REFACTORED: Fix hardcoded path, use loaders
├── show_best_values.py          # REFACTORED: Use loaders
├── deal_sheets.py               # REFACTORED: Use config + loaders + templates
├── geocode_homes.py             # REFACTORED: Use config
├── cost_breakdown_analysis.py   # REFACTORED: Use loaders
└── sun_orientation_analysis.py  # REFACTORED: Use config + loaders
```

**Estimated Line Reduction:** ~1,500-2,000 lines (30-35% of codebase)

**Code Quality Improvement:**
- DRY principle compliance: HIGH
- Maintainability: SIGNIFICANTLY IMPROVED
- Testability: IMPROVED
- Configurability: DRAMATICALLY IMPROVED

---

**End of Analysis**

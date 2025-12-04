# 3. CSV LOADING PATTERNS (DUPLICATED CODE)

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

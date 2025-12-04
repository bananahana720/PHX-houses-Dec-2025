# 4. JSON LOADING PATTERNS (DUPLICATED CODE)

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

# 6. MODULE-LEVEL EXECUTION CODE

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

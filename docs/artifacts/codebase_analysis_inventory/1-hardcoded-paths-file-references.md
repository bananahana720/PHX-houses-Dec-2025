# 1. HARDCODED PATHS & FILE REFERENCES

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

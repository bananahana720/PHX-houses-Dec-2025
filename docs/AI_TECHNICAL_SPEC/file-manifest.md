# FILE MANIFEST

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

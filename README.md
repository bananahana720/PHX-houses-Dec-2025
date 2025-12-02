# PHX Houses Dec 2025

First-time home buyer analysis for Phoenix metropolitan area.

## Quick Start

```bash
# Run the main analysis
python scripts/phx_home_analyzer.py

# View results
open reports/html/dashboard.html
```

## Directory Structure

```
PHX-houses-Dec-2025/
├── data/                    # Input data files
│   ├── phx_homes.csv           # Listing data (address, price, beds, baths)
│   ├── enrichment_data.json    # Manual research data (county, schools, commute)
│   ├── enrichment_template.json # Template for new properties
│   ├── geocoded_homes.json     # Lat/long coordinates
│   └── orientation_estimates.json # Sun orientation data
│
├── scripts/                 # Analysis scripts
│   ├── phx_home_analyzer.py    # Main analysis pipeline
│   ├── deal_sheets.py          # Generate per-property deal sheets
│   ├── risk_report.py          # Risk assessment report
│   ├── renovation_gap.py       # Renovation potential analysis
│   ├── golden_zone_map.py      # Interactive map visualization
│   ├── radar_charts.py         # Property comparison charts
│   ├── value_spotter.py        # Value analysis
│   ├── sun_orientation_analysis.py # Arizona sun exposure
│   ├── geocode_homes.py        # Address geocoding
│   ├── data_quality_report.py  # Data validation
│   ├── cost_breakdown_analysis.py # Monthly cost breakdown
│   └── show_best_values.py     # Quick value summary
│
├── reports/                 # Generated outputs
│   ├── html/                   # Interactive HTML reports
│   │   ├── dashboard.html         # Main dashboard
│   │   ├── golden_zone_map.html   # Interactive map
│   │   ├── radar_comparison.html  # Property comparisons
│   │   ├── renovation_gap_report.html
│   │   ├── risk_report.html
│   │   └── value_spotter.html
│   ├── csv/                    # Tabular data exports
│   │   ├── phx_homes_ranked.csv   # Final ranked properties
│   │   ├── risk_report.csv
│   │   ├── renovation_gap_report.csv
│   │   └── orientation_impact.csv
│   └── images/                 # Static visualizations
│       ├── radar_comparison.png
│       ├── sun_orientation.png
│       └── value_spotter.png
│
├── deal_sheets/             # Per-property summary sheets
│   ├── index.html              # Deal sheets directory
│   └── XX_address.html         # Individual property sheets
│
├── risk_checklists/         # Property-specific risk checklists
│   └── address_checklist.txt
│
├── raw_exports/             # Original Zillow exports (reference only)
│   └── My Favorite Homes*.htm
│
├── docs/                    # Technical documentation
│   ├── AI_TECHNICAL_SPEC.md    # Detailed system specification
│   └── RENOVATION_GAP_README.md # Renovation analysis docs
│
└── CLAUDE.md                # Project overview & buyer criteria
```

## Key Reports

| Report | Description | Location |
|--------|-------------|----------|
| **Dashboard** | Main overview with all properties | `reports/html/dashboard.html` |
| **Ranked List** | Properties sorted by score | `reports/csv/phx_homes_ranked.csv` |
| **Golden Zone Map** | Interactive map visualization | `reports/html/golden_zone_map.html` |
| **Deal Sheets** | Per-property summaries | `deal_sheets/index.html` |
| **Risk Report** | Risk assessment by property | `reports/html/risk_report.html` |
| **Renovation Gap** | Renovation potential analysis | `reports/html/renovation_gap_report.html` |

## Adding New Properties

1. Add listing to `data/phx_homes.csv`
2. Add enrichment data to `data/enrichment_data.json`
3. Run `python scripts/phx_home_analyzer.py`

See `CLAUDE.md` for detailed buyer criteria and data sources.

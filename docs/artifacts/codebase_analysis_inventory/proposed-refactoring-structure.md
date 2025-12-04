# PROPOSED REFACTORING STRUCTURE

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

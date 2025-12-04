# 5. Proposed Architecture

```
phx_home_analysis/
├── config/
│   ├── __init__.py
│   ├── settings.py         # All configuration
│   └── weights.py          # Scoring weights
├── domain/
│   ├── __init__.py
│   ├── entities.py         # Property dataclass
│   ├── enums.py            # RiskLevel, Tier, etc.
│   └── value_objects.py    # Address, Score, etc.
├── repositories/
│   ├── __init__.py
│   ├── base.py             # Abstract repository
│   ├── csv_repository.py   # CSV implementation
│   └── json_repository.py  # JSON implementation
├── services/
│   ├── __init__.py
│   ├── kill_switch.py      # Kill switch filter
│   ├── scorer.py           # Property scoring
│   ├── risk_assessor.py    # Risk assessment
│   └── renovation_estimator.py
├── reporters/
│   ├── __init__.py
│   ├── html_reporter.py    # HTML generation
│   ├── csv_reporter.py     # CSV export
│   └── console_reporter.py # Terminal output
├── visualizations/
│   ├── __init__.py
│   ├── radar_chart.py
│   ├── golden_zone_map.py
│   └── value_spotter.py
├── templates/
│   ├── risk_report.html
│   └── renovation_report.html
├── tests/
│   ├── test_kill_switch.py
│   ├── test_scorer.py
│   └── test_risk_assessor.py
└── main.py                 # CLI entry point
```

---

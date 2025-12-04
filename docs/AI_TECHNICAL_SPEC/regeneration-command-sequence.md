# REGENERATION COMMAND SEQUENCE

To recreate all outputs from scratch:

```bash
# 1. Validate data quality
python data_quality_report.py

# 2. Geocode addresses (cached, only runs once)
python geocode_homes.py

# 3. Run main analysis pipeline
python phx_home_analyzer.py

# 4. Generate visualizations
python golden_zone_map.py
python value_spotter.py
python radar_charts.py
python sun_orientation_analysis.py

# 5. Generate reports
python deal_sheets.py
python renovation_gap.py
python risk_report.py

# 6. Build master dashboard
python dashboard.py

# 7. Open dashboard
start dashboard.html
```

---

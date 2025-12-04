# EXTENSION POINTS

To add new properties:

1. Add row to `phx_homes.csv` with listing data
2. Add entry to `enrichment_data.json` with research data
3. Run `python geocode_homes.py` to geocode new address
4. Run `python phx_home_analyzer.py` to recalculate scores
5. Regenerate all visualizations and reports

To modify scoring weights:

1. Edit `phx_home_analyzer.py` section constants
2. Adjust weight tuples in `section_a`, `section_b`, `section_c`
3. Regenerate `phx_homes_ranked.csv`
4. Regenerate visualizations that depend on scores

To add new risk category:

1. Edit `risk_report.py` `assess_risks()` function
2. Add new risk evaluation logic
3. Update HTML template to include new column
4. Update checklist generation for new risk type

---

*Document Version: 1.0 | Generated: November 2025 | Compatible with Python 3.10+*

# 8. DATA FIELD DEFINITIONS

### Critical Fields (data_quality_report.py lines 12-16)

```python
CRITICAL_FIELDS = [
    'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
    'tax_annual', 'hoa_fee', 'commute_minutes', 'school_district',
    'school_rating', 'distance_to_grocery_miles', 'distance_to_highway_miles'
]
```

### Condition Fields (data_quality_report.py lines 18-21)

```python
CONDITION_FIELDS = [
    'orientation', 'solar_status', 'has_pool', 'pool_equipment_age',
    'roof_age', 'hvac_age'
]
```

### Property Dataclass (phx_home_analyzer.py lines 22-76)

**55 lines defining complete property schema with:**
- Original listing data (10 fields)
- County Assessor enrichment (5 fields)
- HOA data (1 field)
- Geo-spatial enrichment (7 fields)
- Arizona-specific (4 fields)
- Condition data (2 fields)
- Kill switch results (2 fields)
- Scoring results (5 fields)

**Total:** 36 distinct property attributes

**Issue:** This is the authoritative schema but isn't reused elsewhere

---

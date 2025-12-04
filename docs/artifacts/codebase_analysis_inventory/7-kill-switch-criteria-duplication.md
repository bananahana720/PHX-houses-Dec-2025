# 7. KILL SWITCH CRITERIA DUPLICATION

### Implementation A: phx_home_analyzer.py (lines 83-91)

```python
KILL_SWITCH_CRITERIA = {
    "hoa": {"check": lambda p: p.hoa_fee == 0 or p.hoa_fee is None, "desc": "Must be NO HOA"},
    "sewer": {"check": lambda p: p.sewer_type == "city" or p.sewer_type is None, "desc": "Must be City Sewer"},
    "garage": {"check": lambda p: p.garage_spaces is None or p.garage_spaces >= 2, "desc": "Minimum 2-Car Garage"},
    "beds": {"check": lambda p: p.beds >= 4, "desc": "Minimum 4 Bedrooms"},
    "baths": {"check": lambda p: p.baths >= 2, "desc": "Minimum 2 Bathrooms"},
    "lot_size": {"check": lambda p: p.lot_sqft is None or (7000 <= p.lot_sqft <= 15000), "desc": "Lot 9,000-10,000 sqft (relaxed to 7k-15k)"},
    "year_built": {"check": lambda p: p.year_built is None or p.year_built < 2024, "desc": "No New Builds (< 2024)"},
}
```

### Implementation B: deal_sheets.py (lines 15-51)

```python
KILL_SWITCH_CRITERIA = {
    'HOA': {
        'field': 'hoa_fee',
        'check': lambda val: val == 0 or pd.isna(val),
        'description': lambda val: f"${int(val)}/mo" if val and val > 0 else "$0"
    },
    'Sewer': {
        'field': 'sewer_type',
        'check': lambda val: val == 'city',
        'description': lambda val: val.title() if val else "Unknown"
    },
    # ... 5 more criteria
}
```

**Differences:**
1. Keys: lowercase vs title case ("hoa" vs "HOA")
2. Lambda argument: Property object vs raw value
3. deal_sheets.py adds 'field' and 'description' lambdas
4. None/NaN handling differs (`p.hoa_fee is None` vs `pd.isna(val)`)

**Impact:** Changes to criteria must be synchronized across 2 files manually

---

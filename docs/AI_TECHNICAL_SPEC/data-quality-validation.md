# DATA QUALITY VALIDATION

### Validation Script (`data_quality_report.py`)

```python
import json
import pandas as pd

def validate_enrichment_data(filepath):
    with open(filepath) as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    report = {
        'total_properties': len(df),
        'field_completeness': {},
        'critical_issues': [],
        'warnings': []
    }

    # Field completeness
    fields = ['lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
              'tax_annual', 'hoa_fee', 'commute_minutes', 'school_rating',
              'orientation', 'distance_to_grocery_miles', 'distance_to_highway_miles',
              'solar_status', 'has_pool', 'pool_equipment_age', 'roof_age', 'hvac_age']

    for field in fields:
        non_null = df[field].notna().sum()
        report['field_completeness'][field] = {
            'count': non_null,
            'percentage': round(non_null / len(df) * 100, 1)
        }

    # Kill switch violations
    hoa_violations = df[df['hoa_fee'] > 0]
    for _, row in hoa_violations.iterrows():
        report['critical_issues'].append({
            'address': row['full_address'],
            'issue': f"HOA fee ${row['hoa_fee']}/month"
        })

    # Lot size warnings
    small_lots = df[(df['lot_sqft'] < 7000) & (df['lot_sqft'].notna())]
    for _, row in small_lots.iterrows():
        report['warnings'].append({
            'address': row['full_address'],
            'issue': f"Lot size {row['lot_sqft']} sqft below 7,000 minimum"
        })

    return report
```

---

# Complete Quality Workflow Example

This reference file contains the complete workflow example for quality metrics.

```python
from src.phx_home_analysis.services.quality import (
    QualityMetricsCalculator,
    LineageTracker,
    DataSource,
)
import hashlib

# 1. Setup
tracker = LineageTracker()
calculator = QualityMetricsCalculator()

# 2. Property hash
address = "123 Main St, Phoenix, AZ 85001"
prop_hash = hashlib.md5(address.lower().encode()).hexdigest()[:8]

# 3. Record lineage as data is collected
tracker.record_batch(
    property_hash=prop_hash,
    source=DataSource.CSV,
    fields={"address": address, "beds": 4, "baths": 2.0, "sqft": 2200, "price": 475000},
)

tracker.record_batch(
    property_hash=prop_hash,
    source=DataSource.ASSESSOR_API,
    fields={"lot_sqft": 9500, "year_built": 2010, "garage_spaces": 2},
    confidence=0.95,
)

tracker.record_field(
    property_hash=prop_hash,
    field_name="sewer_type",
    source=DataSource.MANUAL,
    confidence=0.85,
    original_value="city",
)

tracker.save()

# 4. Build property data
property_data = {
    "address": address,
    "beds": 4,
    "baths": 2.0,
    "sqft": 2200,
    "price": 475000,
    "lot_sqft": 9500,
    "year_built": 2010,
    "garage_spaces": 2,
    "sewer_type": "city",
}

# 5. Calculate quality
confidences = tracker.get_all_confidences(prop_hash)
score = calculator.calculate(property_data, confidences)

# 6. Report
print(f"Quality Score: {score.overall_score:.1%} ({score.quality_tier})")
if score.missing_fields:
    print(f"Missing: {', '.join(score.missing_fields)}")
if score.low_confidence_fields:
    print(f"Low Confidence: {', '.join(score.low_confidence_fields)}")

# 7. Quality gate
if score.is_high_quality:
    print("PASSED - Ready for production")
else:
    for suggestion in calculator.get_improvement_suggestions(score):
        print(f"  TODO: {suggestion}")
```

## File Locations

| File | Purpose |
|------|---------|
| `data/field_lineage.json` | Persistent lineage storage |
| `data/enrichment_data.json` | Property data (input) |
| `data/phx_homes.csv` | Listing data (fallback input) |
| `scripts/quality_check.py` | CI/CD quality gate script |
| `scripts/data_quality_report.py` | Detailed quality report generator |

## Lineage File Format (field_lineage.json)

```json
{
  "ef7cd95f": {
    "lot_sqft": {
      "field_name": "lot_sqft",
      "source": "assessor_api",
      "confidence": 0.95,
      "updated_at": "2024-01-15T10:30:00.000000",
      "original_value": 9500,
      "notes": "Maricopa County API"
    },
    "year_built": {
      "field_name": "year_built",
      "source": "assessor_api",
      "confidence": 0.95,
      "updated_at": "2024-01-15T10:30:00.000000",
      "original_value": 2010
    }
  }
}
```

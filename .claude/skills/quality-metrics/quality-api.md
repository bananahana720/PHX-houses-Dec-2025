# Quality Metrics API Reference

This reference file contains detailed API documentation for quality metrics classes.

## QualityMetricsCalculator

Calculate quality scores for individual properties or batches.

```python
from src.phx_home_analysis.services.quality import QualityMetricsCalculator

calculator = QualityMetricsCalculator()

# Single property
property_data = {
    "address": "123 Main St, Phoenix, AZ 85001",
    "beds": 4,
    "baths": 2.0,
    "sqft": 2200,
    "price": 475000,
    "lot_sqft": 9500,
    "year_built": 2010,
    "garage_spaces": 2,
    "sewer_type": "city",
}

field_confidences = {
    "address": 0.95,
    "beds": 0.90,
    "lot_sqft": 0.95,
    "year_built": 0.95,
}

score = calculator.calculate(property_data, field_confidences)

print(f"Completeness: {score.completeness:.0%}")         # 100%
print(f"High Confidence: {score.high_confidence_pct:.0%}")  # 100%
print(f"Overall: {score.overall_score:.0%}")             # 100%
print(f"Tier: {score.quality_tier}")                     # excellent
print(f"Is High Quality: {score.is_high_quality}")       # True
```

### Batch Calculation

```python
# Multiple properties
properties = [property1, property2, property3]
confidences = {
    "123 Main St": {"address": 0.95, "beds": 0.90},
    "456 Oak Ave": {"address": 0.95, "lot_sqft": 0.75},
}

individual_scores, aggregate = calculator.calculate_batch(properties, confidences)

print(f"Properties: {len(individual_scores)}")
print(f"Average Quality: {aggregate.overall_score:.0%}")
print(f"Missing Fields: {aggregate.missing_fields}")
print(f"Low Confidence: {aggregate.low_confidence_fields}")
```

### Custom Configuration

```python
# Custom required fields
calculator = QualityMetricsCalculator(
    required_fields=["address", "price", "beds", "baths"],
    high_confidence_threshold=0.9,  # Stricter threshold
)
```

## LineageTracker

Track the provenance and confidence of each field value.

```python
from src.phx_home_analysis.services.quality import LineageTracker, DataSource

# Initialize (auto-loads from data/field_lineage.json if exists)
tracker = LineageTracker()

# Record single field
property_hash = "ef7cd95f"  # MD5 hash of address[:8]
tracker.record_field(
    property_hash=property_hash,
    field_name="lot_sqft",
    source=DataSource.ASSESSOR_API,
    confidence=0.95,
    original_value=9500,
    notes="Maricopa County API - MCAS_ID: 12345678"
)

# Record batch from same source
tracker.record_batch(
    property_hash=property_hash,
    source=DataSource.ASSESSOR_API,
    fields={
        "year_built": 2010,
        "garage_spaces": 2,
        "has_pool": True,
    },
    confidence=0.95,  # Optional, uses source.default_confidence if omitted
)

# Persist to disk
tracker.save()
```

### Querying Lineage

```python
# Get single field lineage
lineage = tracker.get_field_lineage("ef7cd95f", "lot_sqft")
if lineage:
    print(f"Source: {lineage.source.value}")       # assessor_api
    print(f"Confidence: {lineage.confidence}")     # 0.95
    print(f"Updated: {lineage.updated_at}")        # 2024-01-15T10:30:00

# Get all lineage for property
all_lineage = tracker.get_property_lineage("ef7cd95f")
print(f"Tracked fields: {len(all_lineage)}")

# Get confidence scores for quality calculation
confidences = tracker.get_all_confidences("ef7cd95f")
# Returns: {"lot_sqft": 0.95, "year_built": 0.95, ...}

# Find fields needing verification
low_conf = tracker.get_low_confidence_fields("ef7cd95f", threshold=0.8)
print(f"Fields below 80% confidence: {low_conf}")
```

## QualityScore Object

```python
from src.phx_home_analysis.services.quality import QualityScore

score = QualityScore(
    completeness=0.9,
    high_confidence_pct=0.85,
    overall_score=0.88,
    missing_fields=["sewer_type"],
    low_confidence_fields=["year_built"],
)

# Properties
score.is_high_quality      # False (< 0.95)
score.quality_tier         # "good" (0.80-0.95)

# Serialization
data = score.to_dict()
# {
#     "completeness": 0.9,
#     "high_confidence_pct": 0.85,
#     "overall_score": 0.88,
#     "quality_tier": "good",
#     "missing_fields": ["sewer_type"],
#     "low_confidence_fields": ["year_built"]
# }
```

## Improvement Suggestions

```python
calculator = QualityMetricsCalculator()
score = calculator.calculate(property_data, confidences)

suggestions = calculator.get_improvement_suggestions(score)
for suggestion in suggestions:
    print(f"  - {suggestion}")

# Example output:
# - Add missing required fields: sewer_type
# - Verify low-confidence fields with authoritative sources: year_built
# - Improve completeness from 89% to 90%+
```

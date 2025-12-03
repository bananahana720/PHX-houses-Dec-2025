---
name: quality-metrics
description: Track data quality, lineage, and CI/CD gates. Use for quality scoring, field provenance tracking, or automated quality gate enforcement.
allowed-tools: Read, Bash(python:*)
---

# Quality Metrics Skill

Expert at measuring data quality, tracking field-level lineage, and enforcing CI/CD quality gates for the PHX houses analysis project.

## Module Location

```
src/phx_home_analysis/services/quality/
    __init__.py           # Package exports
    models.py             # DataSource, FieldLineage, QualityScore
    metrics.py            # QualityMetricsCalculator
    lineage.py            # LineageTracker
```

## Core Concepts

### Quality Formula

```
overall_score = (completeness * 0.6) + (high_confidence_pct * 0.4)
```

Where:
- **completeness** = present_required_fields / total_required_fields
- **high_confidence_pct** = fields_with_confidence >= 0.8 / total_tracked_fields

### Quality Tiers

| Tier | Score Range | CI/CD Status |
|------|-------------|--------------|
| Excellent | >= 95% | Pass (production-ready) |
| Good | 80-94% | Pass (acceptable) |
| Fair | 60-79% | Warning (review needed) |
| Poor | < 60% | Fail (blocked) |

### Required Fields (Kill Switches & Core)

```python
REQUIRED_FIELDS = [
    "address",
    "beds",
    "baths",
    "sqft",
    "price",
    "lot_sqft",
    "year_built",
    "garage_spaces",
    "sewer_type",
]
```

## Data Sources & Default Confidence

| Source | Enum Value | Default Confidence | Use Case |
|--------|------------|-------------------|----------|
| County API | `ASSESSOR_API` | 0.95 | Official records (lot, year_built) |
| CSV Import | `CSV` | 0.90 | User-provided listing data |
| Manual Entry | `MANUAL` | 0.85 | Human inspection results |
| Web Scraping | `WEB_SCRAPE` | 0.75 | Zillow/Redfin data (may be stale) |
| AI Inference | `AI_INFERENCE` | 0.70 | Estimated values (age, condition) |
| Default | `DEFAULT` | 0.50 | Assumed/placeholder values |

## Core Classes

### QualityMetricsCalculator

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

### LineageTracker

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

### QualityScore Object

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

## CI/CD Quality Gate

### Script Usage

```bash
# Basic usage (95% threshold)
python scripts/quality_check.py

# Custom threshold
python scripts/quality_check.py --threshold 0.90

# Verbose output with suggestions
python scripts/quality_check.py --verbose

# Fail on missing data
python scripts/quality_check.py --fail-on-missing
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Quality gate PASSED |
| 1 | Quality gate FAILED (below threshold) |
| 2 | Configuration or data loading error |

### CI/CD Integration (GitHub Actions)

```yaml
- name: Check Data Quality
  run: |
    python scripts/quality_check.py --threshold 0.95 --fail-on-missing
  continue-on-error: false
```

### Programmatic Check

```python
calculator = QualityMetricsCalculator()

# Quick pass/fail check
if calculator.meets_threshold(property_data, confidences, threshold=0.95):
    print("Ready for production")
else:
    print("Quality gate failed")
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

## Complete Workflow Example

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

## Best Practices

1. **Record lineage at collection time** - Don't wait until scoring
2. **Use appropriate data sources** - Match confidence to actual source
3. **Track original values** - Enables audit trail for transformations
4. **Save frequently** - Prevent data loss on crash
5. **Run quality checks in CI** - Catch regressions before merge
6. **Set realistic thresholds** - Start at 80%, work toward 95%
7. **Address missing fields first** - Higher impact than confidence improvements

## Integration with Other Skills

| Skill | Integration Point |
|-------|-------------------|
| `property-data` | Source of property data for quality scoring |
| `state-management` | Track quality metrics as pipeline phase |
| `county-assessor` | High-confidence data source (0.95) |
| `listing-extraction` | Web scrape source (0.75 confidence) |
| `image-assessment` | AI inference source (0.70 confidence) |
| `deal-sheets` | Include quality tier in reports |

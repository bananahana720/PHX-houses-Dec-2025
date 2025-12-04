---
name: quality-metrics
description: Measure property data quality using completeness (60%) + confidence (40%) formula. Quality tiers are Excellent (95%+), Good (80-94%), Fair (60-79%), Poor (<60%). Track field lineage by source (Assessor 0.95, CSV 0.90, Web 0.75, AI 0.70). Use when calculating data completeness, tracking field provenance, enforcing CI/CD quality gates, or generating data quality reports.
allowed-tools: Read, Bash(python:*)
---

# Quality Metrics Skill

Measure data quality, track field-level lineage, and enforce CI/CD quality gates.

## Quick Reference

### Quality Formula

```
overall_score = (completeness * 0.6) + (high_confidence_pct * 0.4)
```

### Quality Tiers

| Tier | Score Range | CI/CD Status |
|------|-------------|--------------|
| Excellent | >= 95% | Pass (production-ready) |
| Good | 80-94% | Pass (acceptable) |
| Fair | 60-79% | Warning (review needed) |
| Poor | < 60% | Fail (blocked) |

### Required Fields

```python
REQUIRED_FIELDS = [
    "address", "beds", "baths", "sqft", "price",
    "lot_sqft", "year_built", "garage_spaces", "sewer_type"
]
```

### Data Source Confidence

| Source | Default Confidence |
|--------|-------------------|
| Assessor API | 0.95 |
| CSV Import | 0.90 |
| Manual Entry | 0.85 |
| Web Scraping | 0.75 |
| AI Inference | 0.70 |
| Default | 0.50 |

## CLI Usage

```bash
# Basic usage (95% threshold)
python scripts/quality_check.py

# Custom threshold
python scripts/quality_check.py --threshold 0.90

# Verbose output with suggestions
python scripts/quality_check.py --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Quality gate PASSED |
| 1 | Quality gate FAILED |
| 2 | Configuration error |

## Module Location

```
src/phx_home_analysis/services/quality/
    __init__.py    # Package exports
    models.py      # DataSource, FieldLineage, QualityScore
    metrics.py     # QualityMetricsCalculator
    lineage.py     # LineageTracker
```

## Reference Files

| File | Content |
|------|---------|
| `quality-api.md` | Detailed class API documentation |
| `quality-workflow.md` | Complete workflow example |

**Load detail:** `Read .claude/skills/quality-metrics/quality-api.md`

## Best Practices

1. Record lineage at collection time
2. Use appropriate data sources for confidence
3. Run quality checks in CI
4. Address missing fields first (higher impact)

## Integration

| Skill | Integration Point |
|-------|-------------------|
| `property-data` | Source of property data |
| `county-assessor` | High-confidence source (0.95) |
| `listing-extraction` | Web scrape source (0.75) |

---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# quality

## Purpose
Data quality services for tracking field provenance, calculating completeness/confidence metrics, and assessing data lineage across the property analysis pipeline. Supports CI/CD quality gates with field-level confidence tracking.

## Contents
| Path | Purpose |
|------|---------|
| `models.py` | DataSource enum (18 sources), FieldLineage, QualityScore dataclasses |
| `lineage.py` | LineageTracker: persistent field-level provenance tracking with JSON storage |
| `metrics.py` | QualityMetricsCalculator: completeness (60%) + confidence (40%) scoring |
| `provenance_service.py` | ProvenanceService: high-level API for recording field updates with source tracking |
| `confidence_display.py` | ConfidenceLevel enum, format/HTML utilities for reports |
| `__init__.py` | Package exports (9 public APIs) |

## Tasks
- [x] Document quality system (lineage, metrics, provenance) P:H
- [x] Map DataSource confidence defaults (18 sources) P:H
- [x] Document QualityScore formula (completeness 60% + confidence 40%) P:H
- [ ] Add integration tests for atomic lineage writes P:M
- [ ] Add snapshot testing for lineage report generation P:L

## Learnings
- **Quality Formula:** overall_score = (completeness × 0.6) + (high_confidence_pct × 0.4)
- **18 Data Sources:** CSV (0.90), AssessorAPI (0.95), WebScrape (0.75), AI (0.70), Manual (0.85), plus 13 specialized sources (GreatSchools 0.90, FEMA 0.95, Census 0.95)
- **Atomic Writes:** LineageTracker uses atomic_json_save with backup for crash recovery
- **Confidence Levels:** HIGH (≥0.90), MEDIUM (≥0.70), LOW (<0.70) for UI display

## Refs
- DataSource enum & defaults: `models.py:13-66`
- FieldLineage validation: `models.py:69-135`
- QualityScore formula: `metrics.py:20-27`
- Required fields list: `metrics.py:45-55`
- Atomic lineage persistence: `lineage.py:81-104`
- ProvenanceService batch API: `provenance_service.py:96-140`

## Deps
← Imports from:
  - `python 3.10+` (dataclasses, typing, enum)
  - `phx_home_analysis.domain.entities` (EnrichmentData)
  - `phx_home_analysis.utils.file_ops` (atomic_json_save)

→ Imported by:
  - `services/__init__.py` - Package exports
  - `pipeline/orchestrator.py` - Quality gates
  - Scripts for data enrichment & validation
  - CI/CD gates (meets_threshold API)

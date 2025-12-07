---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
flags: []
---
# quality

## Purpose
Data quality services for tracking field provenance, calculating completeness/confidence metrics, and assessing data lineage. Supports CI/CD quality gates with field-level confidence tracking (19 data sources).

## Contents
| Path | Purpose |
|------|---------|
| `models.py` | DataSource enum (19 sources), FieldLineage, QualityScore dataclasses |
| `lineage.py` | LineageTracker: persistent field-level provenance tracking |
| `metrics.py` | QualityMetricsCalculator: completeness (60%) + confidence (40%) |
| `provenance_service.py` | ProvenanceService: high-level API for field update tracking |
| `confidence_display.py` | ConfidenceLevel enum, format/HTML report utilities |
| `audit_log.py` | AuditLog: immutable event logging for quality events |
| `__init__.py` | Package exports (9 public APIs) |

## Recent Changes
- **Added PHOENIX_MLS** to DataSource enum (confidence: 0.87) - authoritative listing data source

## DataSource Confidence Map
| Source | Confidence | Notes |
|--------|------------|-------|
| ASSESSOR_API | 0.95 | Official county records |
| FEMA | 0.95 | Official flood zone data |
| CENSUS | 0.95 | Official census data |
| MARICOPA_GIS | 0.95 | Official county GIS |
| CSV | 0.90 | User-provided listings |
| WALKSCORE | 0.90 | Walk/transit scores |
| GREATSCHOOLS | 0.90 | School ratings |
| GOOGLE_MAPS | 0.90 | Google Maps API |
| PHOENIX_MLS | 0.87 | Phoenix regional MLS (NEW) |
| ZILLOW / REDFIN | 0.85 | Web scraping |
| MANUAL | 0.85 | Human inspection |
| BESTPLACES / AREAVIBES | 0.80 | Crime/neighborhood data |
| IMAGE_ASSESSMENT | 0.80 | AI image analysis |
| WEB_SCRAPE | 0.75 | Web data (may be stale) |
| HOWLOUD | 0.75 | Noise score estimates |
| AI_INFERENCE | 0.70 | AI estimates |
| DEFAULT | 0.50 | Default/assumed values |

## Quality Scoring Formula
- **Overall Score** = (completeness × 0.6) + (high_confidence_pct × 0.4)
- **Quality Tiers**: Excellent (≥0.95), Good (≥0.80), Fair (≥0.60), Poor (<0.60)

## Key Features
- Atomic JSON writes with crash recovery (LineageTracker)
- Field-level provenance tracking via FieldLineage dataclass
- QualityScore with missing/low-confidence field detection

## Refs
- DataSource enum: `models.py:13-68`
- FieldLineage class: `models.py:71-136`
- QualityScore class: `models.py:139-204`

## Deps
← python 3.10+, dataclasses, enum, Pydantic 2.12.5
→ services/__init__.py, pipeline/orchestrator.py, CI/CD gates

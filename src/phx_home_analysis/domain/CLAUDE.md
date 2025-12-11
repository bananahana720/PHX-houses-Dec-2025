---
last_updated: 2025-12-10
updated_by: agent
---

# domain

## Purpose
Core domain entities, value objects, and enums that establish ubiquitous language. Encapsulates business logic and immutability for Property, EnrichmentData, Score, and classifications.

## Contents
| File | Purpose |
|------|---------|
| `entities.py` | Property (160+ fields), EnrichmentData (with provenance), FieldProvenance |
| `value_objects.py` | Address, Score (605-point), ScoreBreakdown, RiskAssessment |
| `enums.py` | Tier, Orientation, SolarStatus, SewerType, RiskLevel, PhaseStatus |
| `entities_provenance.py` | Provenance tracking methods (pending merge) |
| `__init__.py` | Package exports (15 items) |

## Key Patterns
- **FieldProvenance**: Tracks data source (0.95=Assessor, 0.90=CSV, 0.75=Web, 0.70=AI), confidence, timestamp
- **Immutable value objects**: Score, ScoreBreakdown computed properties prevent mutation
- **Behavioral enums**: RiskLevel.score, Tier.next_tier encapsulate business rules
- **160+ property fields**: Organized by domain (location, systems, interior, financials)

## Exports
| Export | Type |
|--------|------|
| Property, EnrichmentData, FieldProvenance | Entities |
| Address, Score, ScoreBreakdown, RiskAssessment, RenovationEstimate | Value objects |
| Tier, Orientation, SolarStatus, SewerType, RiskLevel, PhaseStatus | Enums |

## Refs
- Property entity: `entities.py:100-450` (160+ fields)
- FieldProvenance: `entities.py:14-41` (data lineage tracking)
- Score value object: `value_objects.py:1-80` (0-10 base, weighted calculation)
- Tier enum: `enums.py:440-500` (Unicorn/Contender/Pass classification)

## Deps
← imports: dataclasses, enum, typing
→ used by: services, repositories, validation, quality-metrics

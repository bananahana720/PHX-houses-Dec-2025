---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
---

# domain

## Purpose

Defines core domain entities (Property, EnrichmentData, FieldProvenance) and immutable value objects (Address, Score, ScoreBreakdown) that encapsulate business logic and establish ubiquitous language for the analysis pipeline.

## Contents

| Path | Purpose |
|------|---------|
| `entities.py` | Property (160+ fields), EnrichmentData, FieldProvenance (lines 14-41) |
| `enums.py` | Tier, Orientation, SolarStatus, SewerType, RiskLevel, PhaseStatus, WorkItemStatus |
| `value_objects.py` | Address, Score, ScoreBreakdown (605-point: 250/175/180), RiskAssessment, RenovationEstimate |
| `__init__.py` | Package exports (14 items) |
| `entities_provenance.py` | Provenance methods (pending merge into entities.py) |

## Key Changes

- **New fields**: Added `beds`, `baths`, `sqft` to EnrichmentData (lines 497-500)
- **FieldProvenance**: New dataclass (lines 14-41 in entities.py) tracks data source, confidence, timestamp, agent_id, phase, derived_from
- **Provenance methods**: set_field_provenance(), get_field_provenance(), get_low_confidence_fields() (entities_provenance.py)

## Exports

| Export | Type |
|--------|------|
| Property, EnrichmentData, FieldProvenance | Entities |
| Address, Score, ScoreBreakdown, RiskAssessment, RenovationEstimate | Value objects |
| Tier, Orientation, SolarStatus, SewerType, RiskLevel, PhaseStatus, WorkItemStatus | Enums |

## Tasks

- [x] Add FieldProvenance dataclass to track field-level data lineage
- [ ] Merge entities_provenance.py methods into EnrichmentData class
- [ ] Add validation tests for provenance tracking

## Learnings

- **FieldProvenance pattern**: Enables quality-metrics scoring (completeness + confidence formula)
- **Provenance metadata**: data_source (0.95=Assessor, 0.90=CSV, 0.75=Web, 0.70=AI), confidence (0.0-1.0), timestamps for crash recovery
- **New listing fields**: beds, baths, sqft align with kill-switch criteria validation

## Refs

- FieldProvenance: `entities.py:14-41` (provenance tracking)
- EnrichmentData: `entities.py:450-600` (160+ fields)
- Provenance methods: `entities_provenance.py:18-77` (pending merge)

## Deps

← Imports from: Standard library (dataclasses, enum, typing)
→ Imported by: Services, repositories, validation, quality-metrics

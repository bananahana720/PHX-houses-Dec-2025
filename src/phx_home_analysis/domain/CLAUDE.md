---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---

# domain

## Purpose

Defines core domain entities (Property, EnrichmentData) and immutable value objects (Address, Score, RiskAssessment, ScoreBreakdown) that encapsulate business logic and establish ubiquitous language for the analysis pipeline. Domain-driven design prevents logic duplication across services.

## Contents

| Path | Purpose |
|------|---------|
| `entities.py` | Property (156+ fields), EnrichmentData (DTO) |
| `enums.py` | Tier, Orientation (Arizona-specific), SolarStatus, SewerType, RiskLevel, ImageSource, ImageStatus, FloodZone, CrimeRiskLevel |
| `value_objects.py` | Address, Score, ScoreBreakdown (605-point: 250/175/180), RiskAssessment, RenovationEstimate, PerceptualHash, ImageMetadata |
| `__init__.py` | Package exports (45 items) |

## Tasks

- [x] ScoreBreakdown: Fixed percentages to 250/175/180/605 (was 230/180/190/600) `P:H`
- [ ] Add validation tests for percentage calculations `P:M`

## Learnings

- **ScoreBreakdown rebalanced**: Section A (250), Section B (175), Section C (180) = 605 total. Percentage calculations now accurate per `value_objects.py:138-231`
- **DDD patterns**: Property is aggregate root; EnrichmentData is external DTO. Enums carry domain logic (Orientation.base_score, SolarStatus.is_problematic)
- **Immutability**: All value objects frozen=True (Address, Score, RiskAssessment, ScoreBreakdown, RenovationEstimate, PerceptualHash, ImageMetadata)
- **Orientation AZ-specific**: North=10 pts (best cooling), West=0 pts (worst); used across services without hardcoding

## Refs

- ScoreBreakdown: `value_objects.py:138-231` (605-point system with section maxes)
- Property: `entities.py:13-385` (156+ fields, aggregate root)
- Score: `value_objects.py:47-100` (weighted scoring, computed percentage)
- Package exports: `__init__.py:1-45`

## Deps

← Imports from: Standard library only (dataclasses, enum, typing)
→ Imported by: All services, repositories, validation, pipeline, test suite

---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# scoring

## Purpose

Property scoring service implementing the 605-point weighted system. Orchestrates scoring strategies across three dimensions (Location 230pts, Systems 180pts, Interior 195pts) and assigns tier classifications (Unicorn, Contender, Pass).

## Contents

| Path | Purpose |
|------|---------|
| `scorer.py` | PropertyScorer orchestrator; applies strategies, groups by category, assigns tiers |
| `base.py` | ScoringStrategy abstract base class; defines interface (name, category, weight, calculate_base_score) |
| `explanation.py` | Score explanation generator; produces human-readable scoring rationale |
| `strategies/` | Location, Systems, Interior, CostEfficiency strategy implementations (18 total) |

## Key Updates

- **Dimension-level scoring:** Added `score_location()`, `score_systems()`, `score_interior()` methods for independent section scoring
- **Strategy registry:** `ALL_STRATEGIES` imported from strategies/ module; auto-instantiated with weights
- **Tier logic:** Tier.from_score() applies kill-switch status + score thresholds

## Tasks

- [x] Implement dimension-level scoring methods
- [ ] Add scoring explanation caching for performance `P:M`
- [ ] Document strategy composition patterns `P:L`

## Learnings

- Score aggregation uses category-based filtering on strategy.category ("location", "systems", "interior")
- Weighted score delegates to Score value object; strategies return Score not float
- TYPE_CHECKING import avoids circular dependency with explanation module

## Refs

- Orchestrator: `scorer.py:22-288`
- Dimension methods: `scorer.py:77-132` (score_location, score_systems, score_interior)
- Strategy interface: `base.py:13-104`
- Strategies index: `strategies/__init__.py:ALL_STRATEGIES`

## Deps

← Imports from:
  - `domain/entities.py` (Property)
  - `domain/value_objects.py` (Score, ScoreBreakdown)
  - `domain/enums.py` (Tier)
  - `config/scoring_weights.py` (ScoringWeights, TierThresholds)
  - `.base.ScoringStrategy` (abstract base)

→ Imported by:
  - `services/__init__.py` (public export)
  - `pipeline/orchestrator.py` (AnalysisPipeline.score_properties)
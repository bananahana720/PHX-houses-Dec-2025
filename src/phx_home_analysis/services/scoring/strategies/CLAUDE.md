---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# Scoring Strategies

## Purpose
Implements composable scoring strategy classes for each of the 600-point system's three dimensions: Location (250pts), Systems (175pts), and Interior (180pts). Each strategy encapsulates a single scoring criterion and its weighted calculation logic.

## Contents
| Path | Purpose |
|------|---------|
| `location.py` | Section A: School rating, noise, crime, supermarket, parks, orientation, flood, walk/transit (250pts total) |
| `systems.py` | Section B: Roof, backyard, plumbing/electrical, pool, solar (175pts) |
| `interior.py` | Section C: Kitchen, master suite, light, ceilings, fireplace, laundry, aesthetics (180pts) |
| `cost_efficiency.py` | Cost efficiency scorer for Section B (35pts component) |
| `__init__.py` | Strategy exports and factory patterns |

## Tasks
- [x] Correct interior.py docstring to 180pts (was 190) P:H
- [ ] Add strategy factory examples P:M

## Learnings
- **Section A:** 250pts (location.py) - school + safety + walkability + orientation focus
- **Section B:** 175pts (systems.py + cost_efficiency.py) - roof/systems/efficiency/pool focus
- **Section C:** 180pts (interior.py) - kitchen/master/light/aesthetics focus
- **Total:** 250 + 175 + 180 = 605pts (note: cap applied in scoring logic)

## Refs
- Location docstring: `location.py:1-14`
- Systems docstring: `systems.py:1-12`
- Interior docstring: `interior.py:1-13` (updated to 180pts)
- Cost efficiency: `cost_efficiency.py:1-6`

## Deps
← `base.py` (ScoringStrategy base class)
← `config.scoring_weights.py` (ScoringWeights)
← `domain.entities.py` (Property)
→ Imported by `scorer.py` (PropertyScorer orchestration)
---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# Scoring Skill

## Purpose
Implements the 605-point weighted scoring system for property evaluation. Calculates Location (250 pts), Systems (175 pts), and Interior (180 pts) scores to tier properties as UNICORN (≥484), CONTENDER (363-483), or PASS (<363).

## Contents
| Path | Purpose |
|------|---------|
| `SKILL.md` | Complete scoring reference, tier thresholds, helper scripts, defaults, and sanity checks |
| `src/phx_home_analysis/services/scoring.py` | PropertyScorer service layer |
| `src/phx_home_analysis/services/classification.py` | TierClassifier enum and logic |
| `src/phx_home_analysis/config/constants.py` | Scoring constants (TIER_UNICORN_MIN=484, TIER_CONTENDER_MIN=363, MAX_POSSIBLE_SCORE=605) |

## Tasks
- [x] Update score totals from 600 to 605 (250+175+180) `P:H`
- [x] Update TIER_UNICORN_MIN to 484 (80% of 605) `P:H`
- [x] Update TIER_CONTENDER_MIN to 363 (60% of 605) `P:H`

## Learnings
- Scoring system changed from 600 to 605 points total
- New thresholds: UNICORN ≥484, CONTENDER 363-483, PASS <363
- Tier classification is 60% (PASS), 60-80% (CONTENDER), ≥80% (UNICORN)
- Default value for missing criteria: 5/10 (neutral); flag >5 defaulted

## Refs
- Scoring constants: `src/phx_home_analysis/config/constants.py:50-60`
- Tier logic: `src/phx_home_analysis/services/classification.py:1-50`
- Detailed tables: `.claude/skills/_shared/scoring-tables.md`

## Deps
← property-data, state-management
→ kill-switch, visualizations, deal-sheets
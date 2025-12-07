---
last_updated: 2025-12-07T19:00:00Z
updated_by: agent
staleness_hours: 168
---
# _shared

## Purpose
Shared reference tables and data used across multiple skills. Provides consistent values for scoring, kill-switches, and Arizona-specific factors.

## Contents
| File | Purpose |
|------|---------|
| `scoring-tables.md` | 605-point scoring breakdown, tier thresholds |
| `arizona-factors.md` | AZ-specific: HVAC lifespan, pool costs, orientation |

## Key Values
| Metric | Value |
|--------|-------|
| Scoring Total | 605 pts |
| Kill-Switches | 5 HARD + 4 SOFT |
| Unicorn Tier | >=484 pts |
| Contender Tier | 363-483 pts |

## Usage
Skills import shared tables via markdown includes or direct reference.

## Refs
- Skills: `../` (parent skills directory)
- Scoring: `../../agents/image-assessor/`

## Deps
← Used by: scoring, kill-switch, arizona-context, image-assessment skills
→ Imports from: Architecture docs (authoritative values)

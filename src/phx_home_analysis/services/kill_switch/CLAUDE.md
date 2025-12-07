---
last_updated: 2025-12-07T22:37:37Z
updated_by: agent
staleness_hours: 24
flags: []
---
# kill_switch

## Purpose
Buyer qualification filtering with 5 HARD (instant fail) + 4 SOFT (severity-based) criteria. Accumulates severity scores; thresholds determine FAIL/WARNING/PASS verdicts.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | KillSwitchCriterion abstract base; KillSwitchVerdict enum (PASS/WARNING/FAIL) |
| `constants.py` | 5 HARD + 4 SOFT criteria definitions with severity weights |
| `criteria.py` | 9 concrete implementations (NoHoaKillSwitch, MinBedroomsKillSwitch, etc.) |
| `filter.py` | KillSwitchFilter orchestrator: applies criteria, accumulates severity, returns verdict |
| `explanation.py` | ExplanationGenerator: human-readable failure reasons per property |
| `__init__.py` | Package exports (KillSwitchFilter, Verdict, Criterion, ExplanationGenerator) |

## Key Patterns
- **HARD criteria (5)**: HOA=$0, beds≥4, baths≥2, sqft>1800, solar≠lease → instant FAIL
- **SOFT criteria (4)**: City sewer (2.5), year≤2023 (2.0), garage≥2 (1.5), lot 7k-15k (1.0) → accumulate severity
- **Verdict logic**: FAIL if any HARD fails OR severity ≥3.0; WARNING if severity ≥1.5; else PASS
- **Explanation generation**: Human-readable reasons for filtering decisions

## Tasks
- [ ] Add multi-language support for explanations `P:M`
- [ ] Add buyer profile customization (threshold tuning) `P:L`

## Learnings
- **HARD non-negotiable**: Instant fail prevents wasted analysis on disqualified properties
- **SOFT accumulation**: Multiple minor issues combine (e.g., 2.5+1.5=4.0 → FAIL)
- **Verdict boundaries**: FAIL ≥3.0, WARNING ≥1.5; tests must validate exact thresholds

## Refs
- Criteria definitions: `constants.py:1-80`
- Base class: `base.py:1-50`
- Orchestration: `filter.py:1-150`
- Explanations: `explanation.py:1-200`

## Deps
← imports: `..domain.entities` (Property), `..config.constants`
→ used by: `pipeline/orchestrator.py` (Phase 1), tests, `/analyze-property` command

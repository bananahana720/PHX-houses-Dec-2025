---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---

# kill_switch

## Purpose
Buyer qualification filtering with 5 HARD (instant fail) + 4 SOFT (severity-based) criteria. Accumulates severity scores for SOFT failures; thresholds determine FAIL/WARNING/PASS verdicts. Supports explanation generation for filtering decisions.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | KillSwitchCriterion abstract base class; KillSwitchVerdict enum (PASS, WARNING, FAIL) |
| `constants.py` | Criteria definitions: 5 HARD (hoa, beds, baths, sqft, lot) + 4 SOFT (sewer, year, garage, lot) with severity weights |
| `criteria.py` | Concrete criterion implementations: NoHoaKillSwitch, MinBedroomsKillSwitch, etc. (9 classes) |
| `filter.py` | KillSwitchFilter orchestrator: applies all criteria, accumulates severity, returns verdict |
| `explanation.py` | ExplanationGenerator: human-readable failure reasons for each property |
| `__init__.py` | Package exports (KillSwitchFilter, Verdict, Criterion, ExplanationGenerator) |

## Architecture
**HARD Criteria (5):** HOA=$0, beds≥4, baths≥2, sqft ≤ 1800 (lot range ≥7k-≤15k also in some)
- Instant FAIL if any violated; no accumulation

**SOFT Criteria (4):** City sewer (2.5), year <2024 (2.0), garage ≥2 (1.5), lot size (1.0)
- Severity accumulates: ≥3.0 → FAIL, ≥1.5 → WARNING, <1.5 → PASS

## Tasks
- [x] Implement 5 HARD + 4 SOFT criteria architecture `P:H`
- [x] Implement severity accumulation system `P:H`
- [x] Generate human-readable explanations `P:H`
- [ ] Add multi-language support for explanations `P:M`
- [ ] Add buyer profile customization (threshold tuning) `P:L`

## Learnings
- **HARD criteria non-negotiable:** Instant fail prevents wasted analysis on disqualified properties
- **SOFT severity accumulation:** Multiple minor issues combine; e.g., 2.5 (sewer) + 1.5 (garage) = 4.0 → FAIL
- **Verdict logic critical:** FAIL threshold is ≥3.0; WARNING ≥1.5; tests must validate exact boundaries
- **Explanations improve UX:** Agents need clear reasons for filtering decisions

## Refs
- HARD/SOFT definitions: `constants.py:1-80`
- Criterion base class: `base.py:1-50`
- Filter orchestration: `filter.py:1-150`
- Explanation generation: `explanation.py:1-200`

## Deps
← Imports from:
  - `..domain.entities` (Property)
  - `..config.constants` (criteria definitions)

→ Imported by:
  - `pipeline/orchestrator.py` (Phase 1 filtering)
  - Tests (unit/integration kill-switch validation)
  - `/analyze-property` command
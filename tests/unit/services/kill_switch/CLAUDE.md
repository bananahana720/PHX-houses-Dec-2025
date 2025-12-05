---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
---
# tests/unit/services/kill_switch

## Purpose
Unit tests for kill-switch verdict explanation module covering criterion results, verdict explanations, severity calculations, and text/dict serialization. Validates HARD vs SOFT failure categorization and human-readable verdict narratives.

## Contents
| File | Purpose |
|------|---------|
| `test_explanation.py` | CriterionResult, VerdictExplanation, VerdictExplainer classes (20+ test classes, 150+ tests) |
| `__init__.py` | Package initialization |

## Key Patterns
- **Criterion result model**: name, passed, is_hard, severity, message dataclass for each criteria
- **Verdict types**: PASS (all criteria pass), WARNING (soft severity <3.0), FAIL (hard fail or soft ≥3.0)
- **Severity accumulation**: SOFT criteria accumulate severity, HARD criteria instant fail
- **Markdown output**: to_text() generates formatted verdict with sections (Hard Failures, Soft Failures, Warnings)

## Tasks
- [x] Map test coverage for verdict explanation classes `P:H`
- [x] Document test patterns (criterion results, verdict logic, formatting) `P:H`
- [ ] Add edge case tests for very long failure messages `P:M`
- [ ] Add special character escaping tests `P:L`

## Learnings
- **Severity threshold rule**: Failures ≥3.0 fail, warnings 1.5-3.0, pass <1.5 (thresholds inclusive)
- **HARD vs SOFT logic**: HARD failures take precedence in summary (instant fail), SOFT accumulate with threshold check
- **Message preservation**: Original criterion messages preserved in output and dict serialization
- **Multiple failure types**: Verdict can have hard + soft + warning failures; text output structures each section separately

## Refs
- CriterionResult: `test_explanation.py:20-78` (HARD/SOFT distinction)
- VerdictExplanation: `test_explanation.py:85-350` (verdict structure, to_text, to_dict)
- VerdictExplainer: `test_explanation.py:356-633` (explain logic, summary generation)
- Severity calculation: `test_explanation.py:727-883` (threshold testing, edge cases)

## Deps
← imports: KillSwitchVerdict enum, Pydantic dataclasses
→ used by: pytest, CI/CD pipeline (must pass before merge)

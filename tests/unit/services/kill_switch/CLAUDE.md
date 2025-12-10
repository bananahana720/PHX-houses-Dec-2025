---
last_updated: 2025-12-10
updated_by: agent
staleness_hours: 24
---
# tests/unit/services/kill_switch

## Purpose
Unit tests for kill-switch services: verdict explanations, severity evaluation, and criterion results. 200+ tests covering HARD/SOFT categorization, threshold boundaries, and human-readable narratives.

## Contents
| File | Purpose |
|------|---------|
| `test_explanation.py` | CriterionResult, VerdictExplanation, VerdictExplainer (20+ classes, 150+ tests) |
| `test_severity.py` | SoftSeverityEvaluator, SoftSeverityResult, CSV loading (10 classes, 54 tests) - E3.S2 |
| `__init__.py` | Package initialization |

## Test Classes (test_severity.py - E3.S2)
| Class | Tests | Coverage |
|-------|-------|----------|
| `TestSoftSeverityResult` | 6 | Dataclass fields, defaults |
| `TestSoftSeverityEvaluator` | 7 | Evaluate method, threshold info |
| `TestSeverityAccumulation` | 5 | Multi-criteria accumulation |
| `TestThresholdBoundaries` | 4 | Exact boundary (2.9999 vs 3.0) |
| `TestPassVerdict` | 4 | severity < 1.5 |
| `TestWarningVerdict` | 5 | 1.5 <= severity < 3.0 |
| `TestFailVerdict` | 5 | severity >= 3.0 |
| `TestSoftCriterionConfig` | 9 | Pydantic CSV model validation |
| `TestLoadSoftCriteriaConfig` | 7 | CSV file loading |
| `TestKillSwitchFilterIntegration` | 2 | Filter integration |

## Key Patterns
- **Severity thresholds**: FAIL >= 3.0, WARNING >= 1.5, PASS < 1.5
- **HARD vs SOFT**: HARD instant fail, SOFT accumulate with threshold check
- **Boundary testing**: Exact threshold values tested (2.9999 vs 3.0)
- **CSV validation**: SoftCriterionConfig uses Pydantic for row validation

## Commands
```bash
pytest tests/unit/services/kill_switch/ -v           # All tests (200+)
pytest tests/unit/services/kill_switch/test_severity.py -v  # Severity tests (54)
pytest tests/unit/services/kill_switch/ --cov=src/   # With coverage
```

## Tasks
- [x] Map test coverage for verdict explanation classes `P:H`
- [x] Add SoftSeverityEvaluator tests (E3.S2) `P:H`
- [ ] Add test for actual config/kill_switch.csv loading `P:H`
- [ ] Add edge case tests for very long failure messages `P:M`

## Learnings
- **Severity accumulation**: SOFT criteria add up (2.5 + 1.5 = 4.0 -> FAIL)
- **Float precision**: Review noted potential issues at exact boundaries
- **CSV loader tests**: All use tmp_path fixtures, not actual config file

## Refs
- SoftSeverityEvaluator: `test_severity.py:1-400` (E3.S2 implementation)
- CriterionResult: `test_explanation.py:20-78` (HARD/SOFT distinction)
- VerdictExplanation: `test_explanation.py:85-350` (verdict structure)
- VerdictExplainer: `test_explanation.py:356-633` (explain logic)

## Deps
<- imports: phx_home_analysis.services.kill_switch (severity, explanation modules)
-> used by: pytest, CI/CD pipeline (must pass before merge)

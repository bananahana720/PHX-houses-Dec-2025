---
last_updated: 2025-12-10
updated_by: agent
staleness_hours: 24
flags: []
---
# kill_switch

## Purpose
Buyer qualification filtering with 5 HARD (instant fail) + 4 SOFT (severity-based) criteria. Complete implementation of Epic 3 (FR9-14).

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | KillSwitch ABC, KillSwitchVerdict enum, severity thresholds |
| `constants.py` | 5 HARD + 4 SOFT criteria definitions with severity weights |
| `criteria.py` | 9 concrete implementations (NoHoa, MinBedrooms, CitySewerKillSwitch, etc.) |
| `filter.py` | KillSwitchFilter orchestrator: applies criteria, returns verdict |
| `result.py` | KillSwitchResult, FailedCriterion dataclasses (E3.S3) |
| `formatting.py` | format_verdict(), format_result(), format_severity_bar() (E3.S3) |
| `severity.py` | SoftSeverityEvaluator: SOFT criteria evaluation with breakdown (E3.S2) |
| `explanation.py` | VerdictExplainer: human-readable failure reasons |
| `consequences.py` | ConsequenceMapper, FailureExplanation, HTML warning cards (E3.S4) |
| `config_loader.py` | KillSwitchConfig, load_kill_switch_config() from CSV (E3.S5) |
| `config_factory.py` | create_kill_switch_from_config() factory (E3.S5) |
| `config_watcher.py` | ConfigWatcher for hot-reload in dev mode (E3.S5) |
| `__init__.py` | Package exports (45+ symbols) |

## Key Patterns
- **HARD criteria (5)**: HOA=$0, beds>=4, baths>=2, sqft>1800, solar!=lease -> instant FAIL
- **SOFT criteria (4)**: City sewer (2.5), year<=2023 (2.0), garage>=2 (1.5), lot 7k-15k (1.0)
- **Verdict logic**: FAIL if any HARD fails OR severity >= 3.0; WARNING if >= 1.5; else PASS
- **Config-driven**: CSV file defines criteria, hot-reload via ConfigWatcher

## Key Exports
| Export | Module | Purpose |
|--------|--------|---------|
| `KillSwitchFilter` | filter.py | Main orchestrator |
| `KillSwitchResult` | result.py | Complete evaluation result |
| `format_verdict()` | formatting.py | Emoji + text verdict display |
| `ConsequenceMapper` | consequences.py | Human-readable failure impacts |
| `KillSwitchConfig` | config_loader.py | Pydantic model for CSV rows |
| `ConfigWatcher` | config_watcher.py | Hot-reload support |

## Tasks
- [x] Implement SoftSeverityEvaluator (E3.S2)
- [x] Implement KillSwitchResult (E3.S3)
- [x] Implement ConsequenceMapper (E3.S4)
- [x] Implement config hot-reload (E3.S5)
- [ ] Add multi-language support for explanations `P:M`
- [ ] Add buyer profile customization (threshold tuning) `P:L`

## Learnings
- **HARD non-negotiable**: Instant fail prevents wasted analysis on disqualified properties
- **SOFT accumulation**: Multiple minor issues combine (e.g., 2.5+1.5=4.0 -> FAIL)
- **Verdict boundaries**: FAIL >= 3.0, WARNING >= 1.5; tests validate exact thresholds
- **Config validation**: Pydantic ensures HARD has severity=0.0, SOFT >= 0.1

## Refs
- Base class: `base.py:1-50`
- Criteria: `criteria.py:1-300`
- Results: `result.py:1-215`
- Formatting: `formatting.py:1-205`
- Consequences: `consequences.py:1-500`
- Config: `config_loader.py:1-287`

## Deps
<- imports: `..domain.entities` (Property), `..config.constants`
-> used by: `pipeline/orchestrator.py`, tests, `/analyze-property` command

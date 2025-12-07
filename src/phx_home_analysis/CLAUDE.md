---
last_updated: 2025-12-07T22:37:37Z
updated_by: agent
staleness_hours: 24
flags: []
---
# src/phx_home_analysis

## Purpose
Core analysis library for Phoenix home evaluation. Domain-driven architecture with 605-point scoring, kill-switch filtering, data persistence, and pipeline orchestration.

## Module Structure
| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `config/` | App config, scoring weights (605pts), buyer profile | `AppConfig`, `ScoringWeights`, `TierThresholds` |
| `domain/` | Entities, value objects, enums | `Property`, `EnrichmentData`, `Score`, `Tier` |
| `repositories/` | Data persistence (CSV/JSON) | `PropertyRepository`, `JsonEnrichmentRepository` |
| `services/` | Business logic: kill-switch, scoring, enrichment | `KillSwitchFilter`, `PropertyScorer` |
| `validation/` | Pydantic schemas, validators, normalizers | `PropertySchema`, `normalizer` |
| `pipeline/` | Main orchestrator: load → filter → score → report | `AnalysisPipeline`, `PipelineResult` |
| `reporters/` | Output formatters (console, CSV, HTML) | `ConsoleReporter`, `HtmlReporter` |
| `visualizations/` | Chart generation (radar, scatter plots) | `RadarChartGenerator` |
| `errors/` | Error classification, retry logic, pipeline integration | `is_transient_error()`, `@retry_with_backoff` |
| `utils/` | Shared utilities (file ops, address normalization) | `atomic_json_save()`, `normalize_address()` |

## Scoring System (605 Points)
- **Location** (250pts): Schools, crime, walk score, orientation, flood risk
- **Systems** (175pts): Roof, plumbing/electrical, pool, cost efficiency, backyard
- **Interior** (180pts): Kitchen, master suite, light, ceilings, fireplace, laundry, aesthetics

**Tiers**: Unicorn ≥484pts (80%+) | Contender 363-483pts (60-80%) | Pass <363pts (<60%)

## Kill-Switch (5 HARD + 4 SOFT)
**HARD (instant fail)**: HOA=$0, solar≠lease, beds≥4, baths≥2, sqft>1800
**SOFT (severity)**: Sewer=city (2.5), year≤2023 (2.0), garage≥2 (1.5), lot 7k-15k (1.0)
**Verdict**: FAIL if any HARD fails OR severity ≥3.0

## Package Exports
| Import | Purpose |
|--------|---------|
| `AnalysisPipeline` | Main orchestrator |
| `Property`, `EnrichmentData` | Domain entities |
| `PropertyScorer`, `KillSwitchFilter` | Analysis services |
| `retry_with_backoff` | Transient error recovery |
| `JsonEnrichmentRepository` | Data persistence |

## Key Files
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 185 | Package exports + version |
| `config/scoring_weights.py` | 366 | 605-point system definition |
| `domain/entities.py` | ~500 | Property, EnrichmentData dataclasses |
| `services/kill_switch/` | ~300 | Kill-switch criteria |
| `services/scoring/` | ~800 | 18 scoring strategies |
| `errors/__init__.py` | 234 | Error classification |
| `errors/retry.py` | 407 | Retry decorator with backoff |
| `pipeline/orchestrator.py` | ~400 | Pipeline orchestration |

## Tasks
- [ ] Create examples for custom scorer extension `P:M`
- [ ] Add architecture diagram for domain → services → pipeline flow `P:L`

## Learnings
- **605-point confirmed**: Location 250 + Systems 175 + Interior 180 = 605
- **18 scoring strategies**: 7 Location + 4 Systems + 7 Interior composable via `PropertyScorer`
- **Atomic architecture**: Repository pattern decouples data; services use DI; pipeline orchestrates

## Refs
- Version: `__init__.py:110`
- Scoring: `config/scoring_weights.py:1-100`
- Kill-switch: `services/kill_switch/constants.py:1-89`
- Error handling: `errors/__init__.py:1-234`
- Retry: `errors/retry.py:1-407`
- Domain: `domain/entities.py`

## Deps
← imports: `python 3.11+`, `pydantic==2.12.5`, external APIs (GreatSchools, WalkScore, FEMA)
→ used by: `scripts/phx_home_analyzer.py`, `scripts/extract_*.py`, `.claude/agents/`, tests

---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---
# src/phx_home_analysis

## Purpose

Core analysis library for Phoenix home evaluation. Implements domain-driven architecture with scoring logic (600-point system), kill-switch filtering, data persistence, and orchestration for the PHX Houses pipeline.

## Module Structure

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `config/` | Application configuration, scoring weights (230+180+190=600pts), buyer profile | `AppConfig`, `ScoringWeights`, `TierThresholds` |
| `domain/` | Domain entities, value objects, enums | `Property`, `EnrichmentData`, `Score`, `Tier`, `Orientation` |
| `repositories/` | Data persistence layer - CSV and JSON | `PropertyRepository`, `JsonEnrichmentRepository` |
| `services/` | Business logic: kill-switch, scoring, enrichment | `KillSwitchFilter`, `PropertyScorer`, `ClassificationService` |
| `validation/` | Pydantic schemas, validators, normalizers | `PropertySchema`, `normalizer`, `deduplication` |
| `pipeline/` | Main orchestrator: load → enrich → filter → score → report | `AnalysisPipeline`, `PipelineResult` |
| `reporters/` | Output formatters: console, CSV, HTML | `ConsoleReporter`, `HtmlReporter` |
| `visualizations/` | Chart generation: radar, scatter plots | `RadarChartGenerator`, `ScatterPlotGenerator` |
| `errors/` | Error classification, retry logic, pipeline integration | `is_transient_error()`, `@retry_with_backoff`, `mark_item_failed()` |
| `utils/` | Shared utilities: file ops, address normalization | `atomic_json_save()`, `normalize_address()` |

## Scoring System (600 Points)

**Section A: Location & Environment (230pts)** - GreatSchools, crime, walk score, orientation, flood risk
**Section B: Systems (180pts)** - Roof, plumbing/electrical, pool, cost efficiency, backyard
**Section C: Interior (190pts)** - Kitchen, master suite, natural light, ceilings, fireplace, laundry, aesthetics

**Tier Thresholds:**
- Unicorn: >480pts (80%+)
- Contender: 360-480pts (60-80%)
- Pass: <360pts (<60%)

## Kill-Switch Architecture

**HARD Criteria (Instant Fail):** HOA fee > $0, beds < 4, baths < 2
**SOFT Criteria (Severity):** Sewer (2.5), year (2.0), garage (1.5), lot (1.0)
**Verdict:** HARD fail OR severity ≥3.0 → FAIL | 1.5-3.0 → WARNING | <1.5 → PASS

## Package Exports

| Import | Purpose |
|--------|---------|
| `from phx_home_analysis import AnalysisPipeline` | Main pipeline orchestrator |
| `from phx_home_analysis import Property, EnrichmentData` | Domain entities |
| `from phx_home_analysis import PropertyScorer, KillSwitchFilter` | Analysis services |
| `from phx_home_analysis import retry_with_backoff` | Transient error recovery |
| `from phx_home_analysis import JsonEnrichmentRepository` | Data persistence |

## Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 185 | Package exports and version |
| `config/scoring_weights.py` | 366 | 600-point system definition |
| `domain/entities.py` | ~500 | Property, EnrichmentData dataclasses |
| `services/kill_switch/` | ~300 | Kill-switch criteria implementations |
| `services/scoring/` | ~800 | Scoring strategies (18 total) |
| `errors/__init__.py` | 234 | Error classification module |
| `errors/retry.py` | 407 | Retry decorator with exponential backoff |
| `pipeline/orchestrator.py` | ~400 | AnalysisPipeline orchestration |

## Tasks

- [x] Document module structure and exports (10 modules)
- [x] Update 600-point scoring system documentation
- [x] Document kill-switch HARD/SOFT criteria architecture
- [x] Add error handling module (errors/) to structure
- [x] Map all domain entities and value objects
- [ ] Create examples for custom scorer extension P:M
- [ ] Add architecture diagram for domain → services → pipeline flow P:L

## Learnings

- **600-point confirmed:** Location 230 + Systems 180 + Interior 190 = 600 (not 605)
- **Error module new:** `errors/` module (classify/retry/pipeline) newly added for E1.S6
- **18 scoring strategies:** 7 Location + 4 Systems + 7 Interior strategies composable via `PropertyScorer`
- **Atomic architecture:** Repository pattern decouples data access; services use dependency injection; pipeline orchestrates composition

## Refs

- Package version: `__init__.py:110`
- Scoring system: `config/scoring_weights.py:1-100`
- Kill-switch: `services/kill_switch/constants.py:1-89`
- Error handling: `errors/__init__.py:1-234` (new)
- Retry decorator: `errors/retry.py:1-407` (new)
- Domain entities: `domain/entities.py`

## Deps

← Imports from:
  - `python 3.11+` (dataclasses, typing)
  - `pydantic==2.12.5` (validation)
  - External APIs (GreatSchools, WalkScore, FEMA) via scripts

→ Imported by:
  - `scripts/phx_home_analyzer.py` - Main scoring CLI
  - `scripts/extract_*.py` - Data extraction scripts
  - `.claude/agents/` - Multi-agent pipeline
  - Tests (unit/integration)

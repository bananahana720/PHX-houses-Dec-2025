---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
---

# tests/unit

## Purpose
Comprehensive unit tests for PHX Home Analysis pipeline covering domain models, services, kill-switches, scoring, and repositories in isolation. 189+ test classes across 20+ modules with focus on critical domain logic and kill-switch boundaries.

## Contents
| Path | Purpose |
|------|---------|
| `test_domain.py` | Domain entities, enums, value objects (67 tests) |
| `test_kill_switch.py` | Kill-switch criteria filtering (75 tests) |
| `test_scorer.py` | Property scoring & tier classification (46 tests) |
| `test_repositories.py` | CSV/JSON data persistence (50+ tests) |
| `test_validation.py` | Pydantic schema validation |
| `test_config_*.py` | Configuration loading & validation |
| `test_cost_estimation.py` | Monthly cost calculations |
| `test_deduplicator.py` | Address fuzzy matching & LSH |
| `test_standardizer.py` | Address canonicalization |
| `test_quality_metrics.py` | Data quality scoring (completeness + confidence) |

## Test Categories
- **Domain (test_domain.py):** 9 classes - Entities, enums (9), value objects (7), computed properties (12+)
- **Kill-Switch (test_kill_switch.py, test_lib_kill_switch.py):** 28 classes - HARD criteria (instant fail), SOFT criteria (severity 1.0-2.5), boundary testing (6999 vs 7000 sqft, 2023 vs 2024, 1.9 vs 2.0 baths, $0 vs $1 HOA)
- **Scoring (test_scorer.py):** 8 classes - 7 location strategies, 4 systems, 7 interior strategies, tier assignment
- **Repositories (test_repositories.py):** 11 classes - CSV parsing (50 fields), JSON atomic writes, caching, error handling
- **Config (test_config_*.py):** 22 classes - Schema validation, YAML loading, environment overrides

## Commands
```bash
pytest tests/unit/ -v                           # All unit tests
pytest tests/unit/test_kill_switch.py -v        # Kill-switch tests
pytest tests/unit/ -k "boundary" -v             # Pattern matching
pytest tests/unit/ --cov=src --cov-report=term-missing  # Coverage
```

## Key Patterns
- **Boundary testing:** Lot size 6999 (fail) vs 7000 (pass); year 2023 (pass) vs 2024 (fail); baths 1.9 (fail) vs 2.0 (pass)
- **Severity accumulation:** SOFT criteria add (2.5 + 1.5 = 4.0); ≥3.0 fails, ≥1.5 warns
- **Fixture isolation:** Function-scoped fixtures; mutations don't affect other tests; enables parallel execution
- **Floating-point comparison:** Use `abs(a - b) < epsilon` not `==`

## Learnings
- Boundary testing critical for kill-switches (exact thresholds)
- Severity accumulation complex—tests must validate totals, not individual sums
- Enum case sensitivity (SewerType.CITY vs "city") requires explicit conversion
- None handling everywhere—domain logic gracefully handles missing values
- CSV parsing robustness (Windows line endings, type coercion from strings)

## Refs
- Kill-switch criteria: `src/phx_home_analysis/config/constants.py:1-80`
- Scoring weights: `src/phx_home_analysis/config/scoring_weights.py:1-150`
- Domain models: `src/phx_home_analysis/domain/entities.py:1-400`
- Shared fixtures: `tests/conftest.py:1-638`

## Deps
**← Imports:** pytest 9.0.1+, pytest-cov 7.0.0+, conftest.py fixtures, pathlib, tempfile, typing
**→ Imported by:** CI/CD pipeline (must pass before PR merge), pre-commit hooks, local development
**Execution:** ~0.2-0.3 seconds; 189+ test classes; 1000+ test methods; target 95%+ coverage (kill-switch, scoring)

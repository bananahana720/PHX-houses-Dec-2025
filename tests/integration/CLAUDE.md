---
last_updated: 2025-12-05T18:00:00Z
updated_by: agent
staleness_hours: 24
---
# tests/integration

## Purpose
Integration tests validating multi-component workflows end-to-end: pipeline execution, kill-switch filtering, error recovery, cache integration, and report generation.

## Contents
| File | Tests | Focus |
|------|-------|-------|
| `test_pipeline.py` | 31 | Full pipeline: load → enrich → filter → score → report |
| `test_kill_switch_chain.py` | 27 | HARD/SOFT severity accumulation, thresholds |
| `test_api_client_integration.py` | 18 | HTTP client: caching, retries, auth |
| `test_cached_data_integration.py` | 12 | CachedDataManager pipeline integration |
| `test_transient_error_recovery.py` | 11 | Exponential backoff, work_items tracking |
| `test_resume_workflow.py` | 9 | Pipeline resume, stale detection, fresh start |
| `test_crash_recovery.py` | 8 | Atomic writes, backup/restore, corruption |
| `test_deal_sheets_simple.py` | 5 | HTML report generation |
| `test_checkpoint_workflow.py` | 5 | State persistence and recovery |
| `test_proxy_extension.py` | 4 | Stealth browser proxy config |

## Commands
```bash
pytest tests/integration/ -v              # All integration tests
pytest tests/integration/ -k "pipeline"   # Pipeline tests only
pytest tests/integration/ -k "kill_switch" # Kill-switch tests
pytest tests/integration/ --tb=short -x   # Stop on first failure
```

## Key Patterns
- **Real vs Mock**: Uses real repositories (CSV/JSON), mocks external APIs (GreatSchools, FEMA)
- **Fixtures**: `sample_property`, `sample_unicorn_property`, `sample_failed_property`, `sample_property_minimal`
- **State validation**: Tests work_items.json transitions (pending → done/failed)
- **Atomic writes**: Backup creation, restore from corruption, timestamped naming

## Severity System (Kill-Switch)
| Verdict | Condition |
|---------|-----------|
| FAIL | Any HARD fail OR total severity ≥ 3.0 |
| WARNING | Severity 1.5 - 3.0 |
| PASS | Severity < 1.5 |

## Tasks
- [ ] Add performance benchmarks for large batches `P:M`
- [ ] CI/CD gates for integration test coverage `P:H`

## Learnings
- Boundary testing critical: 2.9 → PASS, 3.0 → FAIL
- Stale detection: Items in_progress >30 min auto-reset
- Atomic writes prevent corruption on crash

## Deps
← `src/phx_home_analysis/pipeline/`, `services/`, `repositories/`, `conftest.py`
→ CI/CD pipeline, pre-merge validation

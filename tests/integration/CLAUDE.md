---
last_updated: 2025-12-10T14:30:00Z
updated_by: agent
staleness_hours: 24
---
# tests/integration

## Purpose
Integration tests validating multi-component workflows end-to-end: pipeline execution, kill-switch filtering, image extraction, error recovery, and report generation. 26 kill-switch chain tests, 19 test files total.

## Contents
| File | Focus |
|------|-------|
| `conftest.py` | Shared fixtures (sample_property with kill-switch fields: sewer_type, hoa_fee, solar_status) |
| `test_kill_switch_chain.py` | HARD/SOFT severity accumulation, thresholds (26 tests) |
| `test_pipeline.py` | Full pipeline: load -> enrich -> filter -> score -> report |
| `test_e2e_pipeline.py` | End-to-end pipeline validation |
| `test_phoenixmls_extraction.py` | PhoenixMLS listing extraction + metadata |
| `test_multi_source_extraction.py` | Multi-source (PhoenixMLS + Zillow + Redfin) |
| `test_orchestrator_integration.py` | ImageProcessor orchestration workflows |
| `test_listing_extraction.py` | Listing browser extraction validation |
| `test_state_persistence.py` | work_items.json state management |
| `test_transient_error_recovery.py` | Exponential backoff, retry logic |

## Artifacts
| File | Purpose |
|------|---------|
| `live_test_results_phoenixmls.yaml` | E2-R2 live testing results (5 properties, 94% coverage) |

## Commands
```bash
pytest tests/integration/ -v              # All integration tests
pytest tests/integration/ -k "phoenixmls" # PhoenixMLS tests only
pytest tests/integration/ -k "pipeline"   # Pipeline tests only
pytest tests/integration/ --tb=short -x   # Stop on first failure
```

## Key Patterns
- **Real vs Mock**: Real repositories (CSV/JSON), mocked external APIs
- **Fixtures**: `sample_property`, `minimal_html`, `full_listing_html`
- **State validation**: work_items.json transitions (pending -> done/failed)
- **Atomic writes**: Backup creation, restore from corruption

## Severity System (Kill-Switch)
| Verdict | Condition |
|---------|-----------|
| FAIL | Any HARD fail OR total severity >= 3.0 |
| WARNING | Severity 1.5 - 3.0 |
| PASS | Severity < 1.5 |

## Tasks
- [ ] Add performance benchmarks for large batches `P:M`
- [ ] CI/CD gates for integration test coverage `P:H`

## Deps
- `src/phx_home_analysis/pipeline/`, `services/`, `repositories/`
- `conftest.py` (shared fixtures)

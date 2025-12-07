---
last_updated: 2025-12-06T19:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit/services/image_extraction

## Purpose
Unit tests for image extraction services, including 93 new tests for decomposed components.

## Contents
| File | Purpose |
|------|---------|
| `test_concurrency_manager.py` | Circuit breaker, error aggregation, semaphore (30 tests) |
| `test_image_processor.py` | Content hash, dedup, storage (33 tests) |
| `test_state_manager.py` | State persistence, checkpoints (30 tests) |
| `test_phoenix_mls_search.py` | PhoenixMLS extractor tests (52 tests) |
| `test_validators.py` | Image quality, metadata completeness (19 tests) |

## Common Commands
```bash
pytest tests/unit/services/image_extraction/ -v           # All tests
pytest tests/unit/services/image_extraction/ -k concurrency  # Specific module
pytest tests/unit/services/image_extraction/ --cov        # With coverage
```

## Test Categories
- **ConcurrencyManager**: Semaphore limits, circuit breaker state transitions, error patterns
- **ImageProcessor**: MD5 determinism, duplicate detection, content-addressed paths
- **StateTracker**: Checkpoint intervals, atomic writes, manifest operations

## Learnings
- Mock deduplicator/standardizer with pytest fixtures
- Use tmp_path for file operation tests
- Time-based tests for circuit breaker timeout

## Deps
← src/.../image_extraction/ (code under test)
→ CI/CD pipeline (runs on every PR)

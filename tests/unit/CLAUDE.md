---
last_updated: 2025-12-10T15:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit

## Purpose
Unit tests for phx_home_analysis package, mirroring src/ structure with isolated, mocked tests. 110+ kill-switch tests including boundary conditions.

## Contents
| Path | Purpose |
|------|---------|
| `conftest.py` | Shared pytest fixtures |
| `test_kill_switch.py` | Kill-switch criteria tests (110 tests: 5 HARD + 4 SOFT) |
| `test_domain.py` | Entity and value object tests |
| `test_scorer.py` | 605-point scoring system tests |
| `test_validation.py` | Pydantic schema validation |
| `test_repositories.py` | Repository layer tests |
| `services/` | Service layer tests (scoring, image_extraction) |

## Key Test Classes (test_kill_switch.py)
| Class | Tests | Coverage |
|-------|-------|----------|
| `TestMinSqftKillSwitch` | 10 | HARD: sqft > 1800 boundary |
| `TestNoSolarLeaseKillSwitch` | 11 | HARD: solar != lease |
| `TestNoHoaKillSwitch` | 10+ | HARD: hoa_fee = 0 |
| `TestMinBedroomsKillSwitch` | 10+ | HARD: beds >= 4 |
| `TestMinBathroomsKillSwitch` | 10+ | HARD: baths >= 2 |

## Commands
```bash
pytest tests/unit/ -v                    # All unit tests
pytest tests/unit/test_kill_switch.py -v # Kill-switch tests (110)
pytest tests/unit/ --cov=src/            # With coverage
```

## Learnings
- E3-S1 added 22 new tests (TestMinSqftKillSwitch, TestNoSolarLeaseKillSwitch)
- Boundary tests critical: 1800 fails, 1801 passes (sqft > 1800)
- Tests follow Arrange-Act-Assert pattern

## Deps
← src/phx_home_analysis/ (code under test)
→ CI/CD pipeline, pre-commit hooks

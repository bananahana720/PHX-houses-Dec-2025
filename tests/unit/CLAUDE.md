---
last_updated: 2025-12-06T19:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit

## Purpose
Unit tests for phx_home_analysis package, mirroring src/ structure with isolated, mocked tests.

## Contents
| Path | Purpose |
|------|---------|
| `conftest.py` | Shared pytest fixtures |
| `domain/` | Entity and value object tests |
| `repositories/` | Repository layer tests |
| `services/` | Service layer tests (scoring, kill-switch, image_extraction) |

## Common Commands
```bash
pytest tests/unit/ -v                    # Run all unit tests
pytest tests/unit/ -k "test_name"        # Run specific test
pytest tests/unit/ --cov=src/            # With coverage
pytest tests/unit/services/ -v           # Service tests only
```

## Testing Patterns
- Use `pytest.fixture` for test data and mocks
- Mock external dependencies (APIs, file I/O)
- Use `tmp_path` fixture for file operations
- Use `@pytest.mark.asyncio` for async tests

## Learnings
- 93 new tests added for decomposed image extraction services
- Tests follow Arrange-Act-Assert pattern
- Mock deduplicator/standardizer for ImageProcessor isolation

## Deps
← src/phx_home_analysis/ (code under test)
→ CI/CD pipeline, pre-commit hooks

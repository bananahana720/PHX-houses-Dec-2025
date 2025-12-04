# 8. Quality Gate Criteria

### 8.1 PR Gate (Merge to feature branch)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| Unit tests pass | 100% | Yes |
| Integration tests pass | 95% | Yes |
| Coverage (changed files) | >= 80% | Yes |
| No new security vulnerabilities | 0 high/critical | Yes |
| Linting (ruff) | 0 errors | Yes |
| Type checking (mypy) | 0 errors | Yes |

### 8.2 Merge Gate (PR to main)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| All P0 tests pass | 100% | Yes |
| All P1 tests pass | >= 95% | Yes |
| Overall coverage | >= 80% | Yes |
| No security vulnerabilities | 0 high/critical | Yes |
| pip-audit clean | 0 high/critical | Yes |
| No hardcoded secrets | 0 detections | Yes |

### 8.3 Release Gate (Tag creation)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| All tests pass (P0 + P1 + P2) | >= 95% | Yes |
| Coverage | >= 80% | Yes |
| Performance benchmarks | Within 10% of baseline | No (warning) |
| Documentation coverage | >= 80% docstrings | No (warning) |
| CHANGELOG updated | Required | Yes |

---

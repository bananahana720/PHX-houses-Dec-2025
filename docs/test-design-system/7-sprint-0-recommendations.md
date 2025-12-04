# 7. Sprint 0 Recommendations

### 7.1 Test Framework Setup

| Action | Priority | Effort |
|--------|----------|--------|
| Configure pytest with coverage reporting | P0 | 2 hours |
| Set up pytest-asyncio for async tests | P0 | 1 hour |
| Install respx for HTTP mocking | P0 | 1 hour |
| Configure pytest-benchmark for performance tests | P1 | 1 hour |
| Set up pytest markers (unit, integration, e2e, slow) | P0 | 1 hour |
| Create conftest.py with shared fixtures | P0 | 4 hours |

**Total Setup:** 10 hours

### 7.2 Initial Test Suite Structure

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (requires fixtures)",
    "e2e: End-to-end tests (full pipeline)",
    "slow: Tests that take >10 seconds",
    "security: Security-related tests",
]
addopts = "--strict-markers -v"

[tool.coverage.run]
source = ["src/phx_home_analysis"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### 7.3 CI/CD Test Integration

**Recommended GitHub Actions Workflow:**

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run unit tests
        run: pytest tests/unit -m unit --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run integration tests
        run: pytest tests/integration -m integration

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
      - name: Run secret detection
        uses: gitleaks/gitleaks-action@v2
```

### 7.4 Fixture Creation Priorities

| Fixture | Priority | Effort |
|---------|----------|--------|
| `tests/fixtures/sample_property.json` | P0 | 1 hour |
| `tests/fixtures/sample_enrichment_data.json` | P0 | 2 hours |
| `tests/fixtures/kill_switch_edge_cases.csv` | P0 | 1 hour |
| `tests/fixtures/scoring_scenarios.json` | P1 | 2 hours |
| `tests/fixtures/sample_work_items.json` | P1 | 1 hour |
| Mock HTTP response fixtures (County API) | P1 | 2 hours |
| Mock HTTP response fixtures (GreatSchools) | P2 | 1 hour |

**Total Fixture Creation:** 10 hours

---

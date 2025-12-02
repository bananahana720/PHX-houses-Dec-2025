# Image Deduplicator Unit Tests - Usage Guide

## Quick Start

### Run All Tests
```bash
python -m pytest tests/unit/test_deduplicator.py -v
```

**Expected Output:**
```
53 passed in 1.24s
```

### Run with Coverage Report
```bash
python -m pytest tests/unit/test_deduplicator.py \
  --cov=phx_home_analysis.services.image_extraction.deduplicator \
  --cov-report=term-missing
```

**Expected Output:**
```
src\phx_home_analysis\services\image_extraction\deduplicator.py: 93%
53 passed in 2.07s
```

---

## Selective Test Execution

### Run Specific Test Class
```bash
# Test only duplicate detection
python -m pytest tests/unit/test_deduplicator.py::TestDuplicateDetection -v

# Test only LSH optimization
python -m pytest tests/unit/test_deduplicator.py::TestLSHOptimization -v

# Test only persistence
python -m pytest tests/unit/test_deduplicator.py::TestPersistence -v
```

### Run Specific Test
```bash
# Test exact duplicate detection
python -m pytest tests/unit/test_deduplicator.py::TestDuplicateDetection::test_detects_exact_duplicate -v

# Test hash computation
python -m pytest tests/unit/test_deduplicator.py::TestHashComputation::test_compute_hash_returns_perceptual_hash -v
```

### Run Tests Matching Pattern
```bash
# Run all persistence tests
python -m pytest tests/unit/test_deduplicator.py -k persistence -v

# Run all LSH tests
python -m pytest tests/unit/test_deduplicator.py -k lsh -v

# Run all registration tests
python -m pytest tests/unit/test_deduplicator.py -k register -v
```

---

## Useful Pytest Options

### Verbose Output
```bash
python -m pytest tests/unit/test_deduplicator.py -vv
```

Shows:
- Full test names with parameters
- Detailed assertion information
- Timing for each test

### Show Print Statements
```bash
python -m pytest tests/unit/test_deduplicator.py -s
```

Useful for debugging - shows any `print()` statements in tests.

### Stop on First Failure
```bash
python -m pytest tests/unit/test_deduplicator.py -x
```

Stops test execution at first failure (useful during debugging).

### Show Slowest Tests
```bash
python -m pytest tests/unit/test_deduplicator.py --durations=5
```

Shows the 5 slowest tests (useful for performance tuning).

### Parallel Execution
```bash
# Requires: pip install pytest-xdist
python -m pytest tests/unit/test_deduplicator.py -n auto
```

Runs tests in parallel using all available CPU cores (~3x faster).

---

## Test Categories

### 1. Hash Computation Tests (9 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestHashComputation -v
```

Tests hash generation for various image formats.

### 2. Duplicate Detection Tests (6 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestDuplicateDetection -v
```

Tests core duplicate detection logic with LSH optimization.

### 3. LSH Optimization Tests (9 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestLSHOptimization -v
```

Tests Locality Sensitive Hashing bucket structure and performance.

### 4. Registration Tests (6 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestHashRegistration -v
```

Tests hash registration and removal lifecycle.

### 5. Persistence Tests (5 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestPersistence -v
```

Tests disk I/O and index recovery.

### 6. Statistics Tests (6 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestStatistics -v
```

Tests metrics and statistics reporting.

### 7. Clear Index Tests (3 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestClearIndex -v
```

Tests index reset functionality.

### 8. Error Handling Tests (4 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestErrorHandling -v
```

Tests error scenarios and graceful degradation.

### 9. Threshold Tests (2 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestThresholdBehavior -v
```

Tests similarity threshold configuration.

### 10. Integration Tests (3 tests)
```bash
python -m pytest tests/unit/test_deduplicator.py::TestIntegration -v
```

Tests end-to-end workflows.

---

## CI/CD Integration Examples

### GitHub Actions
```yaml
name: Test Deduplicator

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install -e .
        pip install pytest pytest-cov

    - name: Run deduplicator tests
      run: |
        python -m pytest tests/unit/test_deduplicator.py \
          --cov=phx_home_analysis.services.image_extraction.deduplicator \
          --cov-fail-under=90 \
          -v
```

### GitLab CI
```yaml
test:deduplicator:
  image: python:3.12

  script:
    - pip install -e .
    - pip install pytest pytest-cov
    - python -m pytest tests/unit/test_deduplicator.py \
        --cov=phx_home_analysis.services.image_extraction.deduplicator \
        --cov-fail-under=90 \
        -v

  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

python -m pytest tests/unit/test_deduplicator.py -q

if [ $? -ne 0 ]; then
    echo "Deduplicator tests failed. Aborting commit."
    exit 1
fi
```

---

## Debugging Failed Tests

### Get More Details
```bash
# Show full traceback
python -m pytest tests/unit/test_deduplicator.py::TestDuplicateDetection::test_detects_exact_duplicate -vv --tb=long

# Show assertion details
python -m pytest tests/unit/test_deduplicator.py -vv --tb=short
```

### Add Debugging
```bash
# Run test with pdb debugger on failure
python -m pytest tests/unit/test_deduplicator.py --pdb

# Run test with pdb on first failure
python -m pytest tests/unit/test_deduplicator.py --pdb -x

# Drop into debugger at specific point
# (add breakpoint() in test code)
```

### Capture Output
```bash
# Show all print/logging output
python -m pytest tests/unit/test_deduplicator.py -s

# Log to file
python -m pytest tests/unit/test_deduplicator.py --log-file=test.log --log-level=DEBUG
```

---

## Performance Profiling

### Measure Test Time
```bash
python -m pytest tests/unit/test_deduplicator.py --durations=10
```

Shows 10 slowest tests with timing.

### Profile with Flame Graph
```bash
# Requires: pip install pytest-flamegraph
python -m pytest tests/unit/test_deduplicator.py --flamegraph
```

Generates flame graph for performance analysis.

### Memory Profiling
```bash
# Requires: pip install pytest-memray
python -m pytest tests/unit/test_deduplicator.py --memray
```

Profiles memory usage during tests.

---

## Test Development

### Add a New Test
```python
# In test_deduplicator.py, add to appropriate test class:

def test_new_feature(self, deduplicator):
    """Test description."""
    # Arrange
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    # Act
    result = deduplicator.compute_hash(buffer.getvalue())

    # Assert
    assert result is not None
    assert isinstance(result, PerceptualHash)
```

### Run Only New Tests
```bash
python -m pytest tests/unit/test_deduplicator.py -k test_new -v
```

### Mark Test as Expected Failure
```python
@pytest.mark.xfail(reason="Not implemented yet")
def test_future_feature(self, deduplicator):
    pass
```

### Skip Test
```python
@pytest.mark.skip(reason="Requires external service")
def test_external_api(self, deduplicator):
    pass
```

---

## Continuous Monitoring

### Watch Tests During Development
```bash
# Requires: pip install pytest-watch
ptw tests/unit/test_deduplicator.py
```

Auto-reruns tests whenever files change.

### Generate HTML Coverage Report
```bash
python -m pytest tests/unit/test_deduplicator.py \
  --cov=phx_home_analysis.services.image_extraction.deduplicator \
  --cov-report=html

# Open htmlcov/index.html in browser
```

---

## Test Maintenance

### Update Snapshot Tests
```bash
# Some tests may have snapshots - update if intentional
python -m pytest tests/unit/test_deduplicator.py --snapshot-update
```

### Clear Test Cache
```bash
# Clear pytest cache if tests are stale
rm -rf .pytest_cache
python -m pytest tests/unit/test_deduplicator.py -v
```

### Regenerate Fixtures
If test fixtures get corrupted, delete them:
```bash
rm -rf tests/unit/__pycache__
python -m pytest tests/unit/test_deduplicator.py -v
```

---

## Expected Results

### All Tests Pass
```
============================= test session starts =============================
...
======================== 53 passed in 1.24s ========================
```

### Coverage Report
```
src\phx_home_analysis\services\image_extraction\deduplicator.py: 93%
======================== 53 passed in 2.07s ========================
```

### Detailed Test Info
```
TestHashComputation::test_compute_hash_returns_perceptual_hash PASSED
TestHashComputation::test_phash_is_valid_hex_string PASSED
TestHashComputation::test_dhash_is_valid_hex_string PASSED
...
======================== 53 passed in 1.24s ========================
```

---

## Troubleshooting

### Tests Won't Run
```bash
# Ensure test file exists
ls tests/unit/test_deduplicator.py

# Ensure dependencies installed
pip install -e .
pip install pytest pillow imagehash
```

### Import Errors
```bash
# Make sure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m pytest tests/unit/test_deduplicator.py -v
```

### File Permission Issues
```bash
# On Windows, check temp directory writable
mkdir -p %TEMP%/pytest
python -m pytest tests/unit/test_deduplicator.py --basetemp=%TEMP%/pytest -v
```

---

## Summary of Commands

| Task | Command |
|------|---------|
| Run all tests | `pytest tests/unit/test_deduplicator.py -v` |
| Run with coverage | `pytest tests/unit/test_deduplicator.py --cov=... --cov-report=term-missing` |
| Run specific class | `pytest tests/unit/test_deduplicator.py::TestClassName -v` |
| Run matching pattern | `pytest tests/unit/test_deduplicator.py -k pattern -v` |
| Show timing | `pytest tests/unit/test_deduplicator.py --durations=10` |
| Debug on failure | `pytest tests/unit/test_deduplicator.py --pdb` |
| Run in parallel | `pytest tests/unit/test_deduplicator.py -n auto` |
| Generate HTML report | `pytest tests/unit/test_deduplicator.py --cov=... --cov-report=html` |
| Stop on first failure | `pytest tests/unit/test_deduplicator.py -x` |

---

## Resources

- **Test File:** `tests/unit/test_deduplicator.py` (825 lines)
- **Coverage Report:** `docs/TEST_COVERAGE_DEDUPLICATOR.md`
- **Summary:** `DEDUPLICATOR_UNIT_TESTS_SUMMARY.md`
- **Source:** `src/phx_home_analysis/services/image_extraction/deduplicator.py`
- **pytest Documentation:** https://docs.pytest.org/
- **Coverage.py:** https://coverage.readthedocs.io/

---

**Last Updated:** 2025-12-02

# How to Use

### Run All Tests
```bash
python -m pytest tests/unit/test_deduplicator.py -v
```

### Run with Coverage
```bash
python -m pytest tests/unit/test_deduplicator.py \
  --cov=phx_home_analysis.services.image_extraction.deduplicator \
  --cov-report=term-missing
```

### Run Specific Test Class
```bash
python -m pytest tests/unit/test_deduplicator.py::TestLSHOptimization -v
```

### Run Specific Test
```bash
python -m pytest \
  "tests/unit/test_deduplicator.py::TestDuplicateDetection::test_detects_exact_duplicate" \
  -v
```

### Run Tests Matching Pattern
```bash
python -m pytest tests/unit/test_deduplicator.py -k "lsh" -v
```

### Generate HTML Coverage Report
```bash
python -m pytest tests/unit/test_deduplicator.py \
  --cov=phx_home_analysis.services.image_extraction.deduplicator \
  --cov-report=html
# Open htmlcov/index.html
```

---

# Wave 0: Baseline & Pre-Processing

### Session 0.1: Quality Baseline (2-3 hours)

**Entry Criteria:**
- Access to `data/phx_homes.csv`
- Access to `data/enrichment_data.json`
- All existing tests passing

**Tasks:**
1. Create `scripts/quality_baseline.py`
2. Run baseline measurement
3. Review output, identify gaps
4. Save `data/quality_baseline.json`

**Commands:**
```bash
# Create baseline script
# (Use implementation-spec.md Wave 0.1 code)

# Run baseline
python scripts/quality_baseline.py

# Verify output
cat data/quality_baseline.json
```

**Exit Criteria:**
- [ ] Script runs without errors
- [ ] Console report displays field completeness
- [ ] `data/quality_baseline.json` created
- [ ] Identified fields <95% documented

**Verification:**
```bash
# Check file exists
ls -lh data/quality_baseline.json

# Validate JSON structure
python -c "import json; json.load(open('data/quality_baseline.json'))"
```

**Rollback:** Delete `scripts/quality_baseline.py` and `data/quality_baseline.json`

---

### Session 0.2: Data Normalizer (2-3 hours)

**Entry Criteria:**
- Session 0.1 complete
- Quality gaps identified

**Tasks:**
1. Create `src/phx_home_analysis/validation/normalizer.py`
2. Create `tests/validation/test_normalizer.py`
3. Run tests, achieve 100% coverage

**Commands:**
```bash
# Create normalizer module
# (Use implementation-spec.md Wave 0.2 code)

# Run tests
pytest tests/validation/test_normalizer.py -v --cov

# Check coverage
pytest tests/validation/test_normalizer.py --cov-report=html
```

**Exit Criteria:**
- [ ] All normalizer tests pass
- [ ] 100% code coverage achieved
- [ ] Address normalization works for common variations
- [ ] Type inference handles strings, numbers, booleans

**Verification:**
```python
# Manual verification in Python REPL
from src.phx_home_analysis.validation.normalizer import normalize_address, generate_property_hash

# Test cases
assert normalize_address("123 N Main St") == "123 North Main Street"
assert generate_property_hash("123 N Main St") == generate_property_hash("123 North Main Street")
```

**Rollback:** Delete normalizer files, remove from git

---

### Session 0.3: Regression Baseline (1-2 hours)

**Entry Criteria:**
- Sessions 0.1, 0.2 complete
- Current system functional

**Tasks:**
1. Create `tests/regression/test_baseline.py`
2. Run regression tests
3. Save output for post-Wave 6 comparison

**Commands:**
```bash
# Create regression tests
# (Use implementation-spec.md Wave 0.3 code)

# Run and save results
pytest tests/regression/test_baseline.py -v | tee tests/regression/baseline_results.txt

# Store in git for comparison
git add tests/regression/
git commit -m "Add regression baseline for scoring improvements"
```

**Exit Criteria:**
- [ ] Regression tests capture current behavior
- [ ] Output saved to `baseline_results.txt`
- [ ] Committed to version control

**Verification:**
```bash
# Verify file exists and has content
wc -l tests/regression/baseline_results.txt  # Should have >50 lines
```

**Rollback:** Delete `tests/regression/` directory

---

### Wave 0 Summary

**Total Sessions:** 3 (6-8 hours)
**Pause Points:** After each session
**Critical Path:** Session 0.1 → 0.2 → 0.3

**Prerequisites for Wave 1:**
- [ ] Quality baseline established
- [ ] Data normalizer functional
- [ ] Regression baseline captured

---

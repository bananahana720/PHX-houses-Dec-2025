# Testing & Quality References

### 20. Existing Test Structure

**Directory:** `tests/`
**Total Tests:** ~50 (to be expanded to ~200)

**Current Structure:**
```
tests/
├── services/
│   ├── scoring/         # 15 tests
│   └── kill_switch/     # 10 tests (to be expanded)
├── repositories/        # 8 tests
├── domain/              # 5 tests
└── integration/         # 3 tests (to be expanded)
```

**New Tests to Add:**
- Wave 0: `tests/validation/test_normalizer.py` (15 tests)
- Wave 0: `tests/regression/test_baseline.py` (10 tests)
- Wave 1: `tests/services/kill_switch/test_weighted_threshold.py` (20 tests)
- Wave 2: `tests/services/cost_estimation/test_*.py` (30 tests)
- Wave 3: `tests/validation/test_schemas.py` (25 tests)
- Wave 4: `tests/services/ai_enrichment/test_*.py` (20 tests)
- Wave 5: `tests/services/quality/test_*.py` (15 tests)
- Wave 6: `tests/integration/test_*.py` (25 tests)

**Total Target:** ~210 tests

---

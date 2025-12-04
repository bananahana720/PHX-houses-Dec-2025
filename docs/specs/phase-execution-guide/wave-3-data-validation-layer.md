# Wave 3: Data Validation Layer

### Session 3.1: Pydantic Schemas (3-4 hours)

**Entry Criteria:**
- Wave 0 complete (can run parallel to Wave 1-2)
- Understanding of Property entity structure

**Tasks:**
1. Create `src/phx_home_analysis/validation/schemas.py`
2. Define PropertyData Pydantic model
3. Add validators for cross-field checks
4. Create unit tests

**Commands:**
```bash
# Create schemas.py
# (Follow PropertyData model structure)

# Create tests
touch tests/validation/test_schemas.py

# Run tests
pytest tests/validation/test_schemas.py -v
```

**Exit Criteria:**
- [ ] PropertyData model validates all fields
- [ ] Type enforcement works (int, float, enums)
- [ ] Range validation works (beds >= 0, year_built <= 2025)
- [ ] Cross-field checks work (pool_age requires has_pool)

**Verification:**
```python
# Test validation
from src.phx_home_analysis.validation.schemas import PropertyData

# Valid data
valid = PropertyData(
    address="123 Main St",
    beds=4,
    baths=2.5,
    lot_sqft=8000,
    year_built=2010
)
print("✓ Valid data accepted")

# Invalid data (should raise ValidationError)
try:
    invalid = PropertyData(address="123 Main St", beds=-1, baths=2)
    assert False, "Should have raised ValidationError"
except Exception as e:
    print(f"✓ Invalid data rejected: {e}")
```

**Rollback:** Delete `validation/schemas.py`

---

### Session 3.2: Repository Integration (2-3 hours)

**Entry Criteria:**
- Session 3.1 complete
- Pydantic schemas working

**Tasks:**
1. Update `csv_repository.py` to validate on load
2. Update `json_repository.py` to validate on load
3. Add error handling for validation failures
4. Test with actual data files

**Commands:**
```bash
# Update repositories
# Add validation in _load() methods

# Test with real data
python -c "
from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository

repo = CsvPropertyRepository('data/phx_homes.csv')
props = repo.find_all()
print(f'Loaded {len(props)} properties (validation successful)')
"
```

**Exit Criteria:**
- [ ] CSV repository validates on load
- [ ] JSON repository validates on load
- [ ] Validation errors logged, not crashed
- [ ] Real data loads successfully

**Verification:**
```bash
# Run full pipeline with validation
python scripts/phx_home_analyzer.py --validate

# Check logs for validation warnings
grep -i "validation" logs/*.log
```

**Rollback:**
```bash
git checkout src/phx_home_analysis/repositories/
```

---

### Wave 3 Summary

**Total Sessions:** 2 (5-7 hours)
**Pause Points:** After session 3.1
**Critical Path:** 3.1 → 3.2

**Prerequisites for Wave 4:**
- [ ] Pydantic validation working
- [ ] Repositories integrated
- [ ] Validation errors handled gracefully

---

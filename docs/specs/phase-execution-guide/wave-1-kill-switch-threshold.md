# Wave 1: Kill-Switch Threshold

### Session 1.1: Weighted Threshold Logic (3-4 hours)

**Entry Criteria:**
- Wave 0 complete
- All existing tests passing
- Familiarity with `scripts/lib/kill_switch.py`

**Tasks:**
1. Update `scripts/lib/kill_switch.py` with weighted logic for 5 HARD + 4 SOFT criteria
2. Add `HARD_SEVERITY` and `SEVERITY_WEIGHTS` constants
3. Create `evaluate_kill_switches_weighted()` function
4. Maintain backward compatibility

**Commands:**
```bash
# Backup current file
cp scripts/lib/kill_switch.py scripts/lib/kill_switch.py.bak

# Edit file
# (Use implementation-spec.md Wave 1.1 code)

# Run existing tests (should still pass)
pytest tests/ -k kill_switch -v

# Verify backward compatibility
python -c "
from scripts.lib.kill_switch import evaluate_kill_switches
data = {'beds': 4, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 2, 'lot_sqft': 8000, 'year_built': 2010}
passed, failures, results = evaluate_kill_switches(data)
print(f'Passed: {passed}, Failures: {len(failures)}')
"
```

**Exit Criteria:**
- [ ] New constants added
- [ ] `evaluate_kill_switches_weighted()` implemented
- [ ] Backward compatibility maintained
- [ ] Existing tests pass

**Verification:**
```python
# Test new weighted logic
from scripts.lib.kill_switch import evaluate_kill_switches_weighted

# HARD failure test
data_hard_fail = {'beds': 3, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 2, 'lot_sqft': 8000, 'year_built': 2010}
verdict = evaluate_kill_switches_weighted(data_hard_fail)
assert verdict.verdict == 'FAIL', "HARD failure not working"

# SOFT warning test
data_soft_warn = {'beds': 4, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 1, 'lot_sqft': 8000, 'year_built': 2010}
verdict = evaluate_kill_switches_weighted(data_soft_warn)
assert verdict.verdict == 'WARNING', "SOFT warning not working"

print("✓ Weighted threshold logic working correctly")
```

**Rollback:**
```bash
# Restore backup
mv scripts/lib/kill_switch.py.bak scripts/lib/kill_switch.py
```

---

### Session 1.2: Unit Tests (2-3 hours)

**Entry Criteria:**
- Session 1.1 complete
- Weighted threshold logic implemented

**Tasks:**
1. Create `tests/services/kill_switch/test_weighted_threshold.py`
2. Test all HARD criteria
3. Test SOFT threshold scenarios
4. Test example scenarios from plan

**Commands:**
```bash
# Create test file
# (Use implementation-spec.md Wave 1.1 tests)

# Run tests
pytest tests/services/kill_switch/test_weighted_threshold.py -v

# Check coverage
pytest tests/services/kill_switch/ --cov=scripts.lib.kill_switch --cov-report=term-missing
```

**Exit Criteria:**
- [ ] All test classes pass (TestHardCriteria, TestSoftCriteriaThreshold, TestExampleScenarios)
- [ ] 95%+ code coverage for kill_switch.py
- [ ] All documented scenarios verified

**Verification:**
```bash
# Run full test suite
pytest tests/ -v

# Ensure no regressions
pytest tests/regression/test_baseline.py -v
```

**Rollback:** Delete test file, restore kill_switch.py from backup

---

### Session 1.3: Deal Sheets Integration (2-3 hours)

**Entry Criteria:**
- Sessions 1.1, 1.2 complete
- All tests passing

**Tasks:**
1. Update `scripts/deal_sheets/renderer.py`
2. Add verdict badge rendering
3. Update `scripts/deal_sheets/templates.py` with CSS
4. Generate sample deal sheet

**Commands:**
```bash
# Backup deal sheets
cp scripts/deal_sheets/renderer.py scripts/deal_sheets/renderer.py.bak
cp scripts/deal_sheets/templates.py scripts/deal_sheets/templates.py.bak

# Edit files
# (Use implementation-spec.md Wave 1.2 code)

# Generate test deal sheet
python -m scripts.deal_sheets --single "4732 W Davis Rd, Glendale, AZ 85306"

# Open in browser to verify
open deal_sheets/4732_W_Davis_Rd_Glendale_AZ_85306.html
```

**Exit Criteria:**
- [ ] Deal sheets display verdict badges (PASS/WARNING/FAIL)
- [ ] [H]/[S] markers visible
- [ ] Severity score displayed
- [ ] CSS styling applied (green/yellow/red)
- [ ] Manual visual verification passed

**Verification:**
- Open generated HTML in browser
- Verify verdict badge color
- Check [H]/[S] markers present
- Confirm severity score displays for WARNING/FAIL

**Rollback:**
```bash
mv scripts/deal_sheets/renderer.py.bak scripts/deal_sheets/renderer.py
mv scripts/deal_sheets/templates.py.bak scripts/deal_sheets/templates.py
```

---

### Wave 1 Summary

**Total Sessions:** 3 (7-10 hours)
**Pause Points:** After each session
**Critical Path:** Session 1.1 → 1.2 → 1.3

**Prerequisites for Wave 2:**
- [ ] Weighted threshold logic working
- [ ] All tests passing
- [ ] Deal sheets display verdicts correctly

---

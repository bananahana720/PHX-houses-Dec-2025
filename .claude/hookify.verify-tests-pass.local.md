---
name: verify-tests-pass
enabled: true
event: stop
conditions:
  - field: transcript
    operator: regex_match
    pattern: (pytest|python\s+-m\s+pytest|npm\s+test|jest|test suite)
action: warn
---

## 🧪 Test Verification Required

Tests were executed in this session. **Confirm they PASSED before declaring work complete.**

### Required Checks

Before stopping work, verify:

- [ ] Tests PASSED (look for "passed" count in output)
- [ ] No test FAILURES (failed count = 0)
- [ ] No ERROR conditions (pytest errors or test collection failures)
- [ ] Coverage acceptable (if coverage reports shown)

### Test Output Signs

**Good signs (tests passed):**
```
===== X passed in Y.XXs =====
All tests passed!
✅ Tests: 15 passed
```

**Red flags (tests failed):**
```
===== X failed, Y passed =====
FAILED test_name.py::test_func
ERROR collecting test
⚠️ Test failures detected
```

### Action If Tests Failed

If tests failed:
1. **Do NOT mark work as complete**
2. Fix the failing tests
3. Re-run the full test suite
4. Confirm all tests pass
5. Then declare work done

### Reference

- Test framework: pytest 9.0.1 (from CLAUDE.md)
- Test location: `tests/unit/` and `tests/integration/`
- Run tests: `pytest tests/unit/ -v`

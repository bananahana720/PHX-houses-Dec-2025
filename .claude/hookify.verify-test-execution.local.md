---
name: verify-test-execution
enabled: true
event: stop
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
action: warn
---

## 🧪 Test Execution Verification Required

**Python files were modified. Verify tests were run before completing.**

### Quick Verification

Did you run tests after code changes?

| If Modified | Test Command |
|-------------|--------------|
| Any `.py` file | `pytest tests/ -v` |
| `services/scoring/` | `pytest tests/unit/services/scoring/ -v` |
| `services/kill_switch/` | `pytest tests/unit/services/kill_switch/ -v` |
| `domain/` | `pytest tests/unit/domain/ -v` |

### Pre-Stop Checklist

Before declaring work complete:

- [ ] **Tests run?** `pytest` executed after code changes
- [ ] **Tests pass?** All green, no failures
- [ ] **Coverage maintained?** No significant drops
- [ ] **Lint clean?** `ruff check` passes

### Common Oversights

| Problem | Solution |
|---------|----------|
| Forgot to run tests | Run `pytest tests/ -v` now |
| Tests not updated | Add/update tests for new behavior |
| New code, no tests | Write tests before completing |

### Quick Commands

```bash
# Full test suite
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=src/phx_home_analysis --cov-report=term-missing
```

### Exception

This warning does NOT apply if:
- Only modified documentation/comments
- Changes were to test files themselves
- Working on test infrastructure

**If tests were run and passed, proceed with confidence. If not, run them now.**

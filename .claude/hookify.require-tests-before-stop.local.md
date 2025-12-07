---
name: require-tests-before-stop
enabled: true
event: stop
pattern: .*
action: warn
---

## ⚠️ Pre-Stop Verification Checklist

Before stopping, verify these quality gates:

### Required Checks
- [ ] **Tests run**: Did you run `pytest` for affected areas?
- [ ] **Lint check**: Did you run `ruff check --fix`?
- [ ] **Type check**: Did you run `mypy` on changed files?
- [ ] **Build clean**: No errors in test output?

### Verification Commands
```bash
pytest tests/unit/ -v --tb=short
ruff check src/phx_home_analysis/
mypy src/phx_home_analysis/
```

### If Tests Were Skipped
- Run the verification suite before marking work complete
- Document any known test failures in the story file
- Never skip tests for production code changes

**Reminder**: The `/bmad:bmm:workflows:code-review` workflow validates these automatically.

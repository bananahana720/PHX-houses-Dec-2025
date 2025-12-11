---
name: precommit-hygiene
enabled: true
event: bash
pattern: git commit
action: warn
---

## 🔍 Pre-Commit Hygiene Checklist

**Before committing, verify code quality gates.**

### Required Checks

Run these before `git commit`:

```bash
# 1. Linting
ruff check src/ tests/ scripts/

# 2. Formatting
ruff format --check src/ tests/ scripts/

# 3. Type checking
mypy src/

# 4. Tests
pytest tests/ -v
```

### Quick All-in-One

```bash
ruff check --fix && ruff format && mypy src/ && pytest tests/ -v
```

### No-Go Patterns

Before committing, verify NONE of these exist:

| Pattern | Check Command |
|---------|---------------|
| TODO/FIXME comments | `rg "TODO\|FIXME" src/` |
| Debug prints | `rg "print\(" src/` |
| Commented code blocks | Visual inspection |
| Hardcoded secrets | `rg "(api_key\|password\|secret)" src/` |

### Commit Message Format

Use Conventional Commits:
```
feat: Add new scoring dimension
fix: Correct kill-switch threshold calculation
refactor: Extract validation logic to separate module
docs: Update CLAUDE.md with new patterns
test: Add integration tests for image assessment
```

### Pre-Commit Hooks

The repository has pre-commit hooks. If commit fails:
1. Review the hook output
2. Fix the issues
3. Re-stage files (`git add`)
4. Retry commit

**Do NOT use `--no-verify` to bypass hooks unless explicitly approved.**

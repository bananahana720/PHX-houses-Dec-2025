---
name: warn-precommit-verification
enabled: true
event: bash
pattern: git\s+commit\b
action: warn
---

## ⚠️ Pre-Commit Verification Reminder

**You are about to create a git commit.**

### Verification Checklist

Before committing, confirm you've run:

- [ ] **Tests**: `pytest tests/unit/ -v --tb=short`
- [ ] **Lint**: `ruff check src/phx_home_analysis/`
- [ ] **Format**: `ruff format --check src/`
- [ ] **Types**: `mypy src/phx_home_analysis/`

### Quick Verification Command
```bash
pytest tests/unit/ -v --tb=short && ruff check src/ && mypy src/phx_home_analysis/
```

### Commit Best Practices
- Use Conventional Commits format: `feat:`, `fix:`, `docs:`, `refactor:`
- Include "why" not just "what" in commit message
- Keep commits atomic (one logical change)
- Reference story/ticket if applicable (e.g., `E2-R3`)

### If Verification Was Already Done
Proceed with the commit - this is just a reminder.

### If Skipping Verification
- Document why in commit message
- Add `[skip-verify]` tag if intentional
- Be prepared for CI failures

**The `/commit` command runs verification automatically.**

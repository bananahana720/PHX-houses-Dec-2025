# Claude Code Hooks

## Purpose
Pre/post execution hooks for the PHX Houses Analysis Pipeline to enforce code quality, safety, and architecture consistency.

## Available Hooks

### architecture-consistency-check.py
**Purpose:** Prevents documentation drift by verifying key architectural values match across documentation files.

**Checks:**
- Scoring Total: 605 points
- HARD Kill-Switch Count: 5
- SOFT Kill-Switch Count: 4
- Unicorn Threshold: 480-509 range

**Files Checked:**
- `CLAUDE.md`
- `docs/architecture/scoring-system-architecture.md`
- `docs/architecture/executive-summary.md`
- `docs/architecture/kill-switch-architecture.md`
- `docs/architecture/core-architectural-decisions.md`

**Usage:**
```bash
# Manual run
python .claude/hooks/architecture-consistency-check.py

# Automatic via pre-commit (configured in .pre-commit-config.yaml)
git commit -m "message"  # Hook runs automatically
```

**Exit Codes:**
- `0` - All checks passed
- `1` - Inconsistencies found (blocks commit)

**Integration:**
This hook is configured in `.pre-commit-config.yaml` and runs automatically on commit when any architecture documentation files are modified.

**Example Output:**
```
🔍 Architecture Consistency Check
==================================================

📋 Scoring Total (expected: 605)
  ✅ CLAUDE.md: Found '605'
  ✅ docs/architecture/executive-summary.md: Found '605'

📋 HARD Kill-Switch Count (expected: 5)
  ✅ CLAUDE.md: Found '5'
  ✅ docs/architecture/kill-switch-architecture.md: Found '5'

📋 SOFT Kill-Switch Count (expected: 4)
  ✅ CLAUDE.md: Found '4'
  ✅ docs/architecture/kill-switch-architecture.md: Found '4'

📋 Unicorn Threshold (expected: 48)
  ✅ CLAUDE.md: Found '48'
  ✅ docs/architecture/scoring-system-architecture.md: Found '48'

==================================================
Summary:
  ✅ Scoring Total
  ✅ HARD Kill-Switch Count
  ✅ SOFT Kill-Switch Count
  ✅ Unicorn Threshold

✅ All architecture consistency checks passed!
```

## Adding New Consistency Checks

To add a new architectural value to verify:

1. Edit `architecture-consistency-check.py`
2. Add a new `ConsistencyCheck` to the `CHECKS` list:

```python
ConsistencyCheck(
    name="Your Check Name",
    pattern=r"regex-pattern-to-match",
    expected="expected-value",
    files=[
        "path/to/file1.md",
        "path/to/file2.md",
    ],
)
```

3. Test the updated hook:
```bash
python .claude/hooks/architecture-consistency-check.py
```

## Pre-Commit Setup

If pre-commit hooks are not installed:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks from .pre-commit-config.yaml
pre-commit install

# Test all hooks manually
pre-commit run --all-files
```

## Refs
- Pre-commit config: `../../.pre-commit-config.yaml`
- Project docs: `../../CLAUDE.md`
- Architecture docs: `../../docs/architecture/`

---
name: cross-reference-consistency
enabled: true
event: bash
pattern: git\s+(commit|add).*\.(md|yaml)
action: warn
---

## ⚠️ Cross-Reference Consistency Check Required

**You are staging/committing documentation. Verify cross-references match.**

### Before Committing Docs

Run the architecture consistency hook:

```bash
python .claude/hooks/architecture-consistency-check.py
```

### Manual Verification Commands

**Kill-switch references (should ALL show "5 HARD"):**
```bash
rg -i "(\d+)\s*HARD" CLAUDE.md docs/architecture/*.md .claude/CLAUDE.md
```

**Scoring references (605 max, 484 unicorn, 363 contender):**
```bash
rg -i "(605|484|363)" CLAUDE.md docs/architecture/*.md
```

**Data source hierarchy:**
```bash
rg -i "phoenixmls|canonical|primary.*source" docs/architecture/*.md
```

### Known Cross-Reference Points

| Value | Expected | Files That Must Match |
|-------|----------|----------------------|
| Kill-switch count | 5 HARD + 4 SOFT | CLAUDE.md, kill-switch-architecture.md, ADR-04 |
| Scoring total | 605 pts | CLAUDE.md, scoring-system-architecture.md |
| Unicorn threshold | >=484 | CLAUDE.md, scoring-system-architecture.md |
| Primary data source | PhoenixMLS | data-source-architecture.md |

### If Inconsistencies Found

1. **STOP** - Do not commit
2. **Identify authoritative source** (usually code)
3. **Update ALL references** to match
4. **Re-run consistency check**
5. **Then commit**

**Inconsistent documentation is technical debt that compounds rapidly.**

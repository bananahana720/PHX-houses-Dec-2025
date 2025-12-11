---
name: require-claude-md-update
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (services/scoring/|services/kill_switch/|domain/entities|domain/enums).*\.py$
action: warn
---

## 📚 CLAUDE.md Documentation Sync Required

**This warning fires once per file per session - acknowledge and continue.**

**You are modifying a file that is referenced in documentation.**

### Files That Require Doc Updates
| Code Path | Documentation References |
|-----------|-------------------------|
| `services/scoring/` | `CLAUDE.md` scoring section, `docs/architecture/scoring-system-architecture.md` |
| `services/kill_switch/` | `CLAUDE.md` kill-switch section, `docs/architecture/kill-switch-architecture.md` |
| `domain/entities.py` | Schema evolution plan, data architecture docs |
| `domain/enums.py` | Tier definitions, scoring documentation |

### Documentation Sync Checklist
- [ ] Does root `CLAUDE.md` reflect the change?
- [ ] Does `docs/architecture/` need updates?
- [ ] Are kill-switch count/criteria still accurate (5 HARD + 4 SOFT)?
- [ ] Are scoring totals/thresholds still accurate (605 max)?
- [ ] Do directory CLAUDE.md files need updates?

### Key Documentation Files
```
CLAUDE.md                                    # Root project docs
docs/architecture/CLAUDE.md                  # Architecture directory
docs/architecture/scoring-system-architecture.md
docs/architecture/kill-switch-architecture.md
docs/architecture/core-architectural-decisions.md
```

### Why This Matters
Per sync wave learnings:
- **98% consistency** achieved through systematic updates
- **Documentation drift** causes agent confusion
- **CLAUDE.md files** are read at session start
- **Outdated counts** (e.g., 7 vs 8 kill-switches) create bugs

### Quick Verification
After making changes, verify consistency:
```bash
# Check kill-switch references
grep -r "HARD" CLAUDE.md docs/architecture/*.md | grep -E "[78]\s*(HARD|criteria)"

# Check scoring references
grep -r "605\|484\|363" CLAUDE.md docs/architecture/*.md
```

**Update documentation before marking this change complete.**

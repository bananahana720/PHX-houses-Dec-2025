---
name: detect-stale-documentation
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(according to|based on|CLAUDE\.md says|documentation says|docs show|the docs|per the|see @)
action: warn
---

## ⚠️ Documentation May Be Stale - Verify Before Trusting

**You referenced documentation content. Treat ALL docs as potentially outdated.**

### Verification Protocol

When citing documentation, ALWAYS:

1. **Check against code**: Does doc match current implementation?
2. **Cross-check related docs**: Do all references agree?
3. **Cite source files**: Include file:line for verifiable claims

### Known Drift-Prone Areas

| Topic | Authoritative Source | Common Drift |
|-------|---------------------|--------------|
| Kill-switch count | `services/kill_switch/constants.py` | Docs may say 7/8 when code has 5+4 |
| Scoring total | `services/scoring/constants.py` | Check MAX_SCORE, tier thresholds |
| Schema fields | `domain/entities.py` | Field counts change frequently |

### Red Flags 🚩

- Numeric claims without source citations
- "According to CLAUDE.md..." without verification
- Docs updated >7 days ago for active areas
- Contradictory values across different docs

### Verification Command

```bash
# Check consistency before trusting docs
python .claude/hooks/architecture-consistency-check.py
```

**Never answer "the docs say X" - always verify X is current.**

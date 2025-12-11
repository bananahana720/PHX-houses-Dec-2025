---
name: detect-stale-documentation
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(the\s+(docs?|documentation)\s+say|according\s+to\s+(the\s+)?(docs?|documentation)|docs?\s+mention|documentation\s+says|README\s+says)
action: warn
---

## 📚 Documentation Reference Detected - Verify Before Trusting

**You cited documentation. Treat ALL docs as potentially outdated—verify against code.**

### Verification Protocol

Before trusting a documentation claim:

1. **Check freshness**: Look for `last_updated` or commit date in relevant CLAUDE.md files
2. **Cross-check code**: Compare doc claims against actual implementation
3. **Cite sources**: Include file:line references for verifiable claims

### High-Risk Documentation Areas

| Topic | Authoritative Source | Stale Risk |
|-------|---------------------|-----------|
| Kill-switch count/criteria | `services/kill_switch/constants.py` | High—criteria change frequently |
| Scoring weights/totals | `services/scoring/constants.py` | High—thresholds modified per analysis |
| Schema fields | `domain/entities.py` | High—enrichment schema evolves |
| Phase requirements | Pipeline code in `scripts/` | Medium—phase definitions stable |
| Tool requirements | `.claude/CLAUDE.md` | Low—version table updated regularly |

### Red Flags 🚩

- Numeric claims (e.g., "605 points total") without code citation
- "CLAUDE.md says..." statements made from memory (not fresh read)
- Docs modified >7 days ago for active feature areas
- Contradictory values across CLAUDE.md, README, code

### Verification Checklist

- [ ] Read the actual file referenced (don't trust memory)
- [ ] Cross-check numeric claims against code (constants, thresholds)
- [ ] If docs conflict with code, cite the code as authoritative
- [ ] Document any drift you find as a follow-up issue

**Always verify. Never assume docs are current.**

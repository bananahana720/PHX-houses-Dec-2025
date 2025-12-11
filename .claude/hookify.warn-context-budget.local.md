---
name: warn-context-budget
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (continue|step\s+\d{2,}|keep\s+going|more\s+help|next\s+\d+|resume|part\s+[3-9]|phase\s+[4-9]|implement|code|refactor|large|multi-file|batch)
action: warn
---

## 📊 Context Budget Check

**Extended session detected. Verify context headroom before continuing.**

This prompt matches patterns indicating an extended work session. **Maintain 30% context headroom per CLAUDE.md protocol.**

### Quick Checks

- [ ] Estimate remaining context budget (tokens or % headroom)
- [ ] If <30% headroom, trigger `/compact` before next large operation
- [ ] Review earlier decisions—are you aligned with project requirements?

### When to Compact

Consider `/compact` if you're about to:
- Analyze multiple large files (>5 files or >50KB total)
- Perform multi-file patches or refactors
- Delegate to subagents (summarize their findings first)
- Start a new major feature

### Compaction Template

```
/compact

Goal: [Next step]
Must retain: Requirements, decisions, key file paths, open questions
Summarize: Goal, assumptions, constraints, entry points, pending risks
Exclude: Rejected options, obsolete logs, intermediate attempts
```

**If headroom uncertain, ask user: "Should we /compact before proceeding with [next step]?"**

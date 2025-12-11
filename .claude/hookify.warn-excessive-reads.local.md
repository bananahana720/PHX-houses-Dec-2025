---
name: warn-excessive-reads
enabled: true
event: all
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(read.*file|examine.*code|look at|check.*implementation|analyze.*source)
action: warn
---

## 📖 Consider Delegating Exploration to Subagent

**Multiple file reads detected. Orchestrators should delegate exploration.**

### Pattern Detected

You're doing (or about to do) exploratory file reading. As the orchestrator, consider:
- Is this a one-off quick lookup? → Do it yourself
- Is this multi-file exploration? → Delegate to subagent

### Decision Guide

| Scenario | Action |
|----------|--------|
| Check single config value | Read it yourself |
| Find implementation of feature | Task(Explore): "Find how X works" |
| Understand codebase area | Task(Explore): "Analyze Y subsystem" |
| Review multiple files | Task(Explore): "Survey files in Z/" |

### Task(Explore) Pattern

For exploration, use:
```
Task(Explore): "Investigate [area] to understand [goal].
Focus on [specific files/patterns].
Report back: [what you need to know]"
```

### Benefits of Delegation

1. **Preserves your context** - Subagent reads don't consume your budget
2. **Structured results** - Subagent summarizes findings
3. **Parallel work** - Launch multiple explorers if needed
4. **Focused expertise** - Subagent can dive deep

### When to Read Yourself

- Single file, <100 lines
- Quick verification of known location
- User explicitly asked you to read specific file
- Following up on subagent's specific file reference

### Token Budget

Remember:
- Main agent: ~1-2k tokens per turn
- Each Read adds to your context
- Multiple Reads = delegate instead

**If you're about to Read 3+ files, use Task(Explore) instead.**

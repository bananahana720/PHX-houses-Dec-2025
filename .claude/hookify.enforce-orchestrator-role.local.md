---
name: enforce-orchestrator-role
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (?s)(.{500,})
action: warn
---

## 🛑 ORCHESTRATOR ROLE VIOLATION - Large Edit Detected

**Main agent should DELEGATE, not IMPLEMENT.**

### What Triggered This

You (the main agent) are attempting to make a large file edit (>500 characters).
As the orchestrator, you should be delegating this work to a subagent.

### Orchestrator Principle

```
Main Agent = Orchestrator = Coordinator
├── Plan and delegate work
├── Summarize results for user
├── Manage todo tracking
└── Small fixes only (~10 lines max)

Subagents = Workers = Implementers
├── File exploration and analysis
├── Code implementation
├── Test writing
└── Large refactors
```

### Acceptable Main Agent Actions

| Allowed | Not Allowed |
|---------|-------------|
| Fix typos (<5 lines) | New feature implementation |
| Update single config value | Multi-file refactors |
| Add single import | Writing new modules |
| Quick doc correction | Test suite creation |

### Correct Approach

Instead of making this edit yourself:

1. **Use Task tool** to delegate to appropriate subagent:
   ```
   Task(dev): "Implement [feature] in [file]..."
   Task(Explore): "Analyze [codebase area] for..."
   ```

2. **Provide context** to subagent:
   - What needs to change
   - Acceptance criteria
   - Related files to consider

3. **Wait and summarize** when subagent returns

### Token Budget Reminder

- Main agent turns: **~1-2k tokens max**
- Large edits: **Delegate via Task()**
- File exploration: **Delegate via Task(Explore)**

### Override

If this is truly a small fix that was misclassified, proceed with caution.
For large implementations, **ALWAYS delegate to subagents**.

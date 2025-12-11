---
name: enforce-task-delegation
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(implement|create|add feature|fix bug|write.*code|build|develop|refactor|update.*to)
action: warn
---

## 🤖 ORCHESTRATOR REMINDER - Delegate Complex Work

**User request suggests implementation work. Use Task() to delegate.**

### Orchestrator Protocol

You are the **orchestrator**. Your job:
1. **Understand** the user's request
2. **Plan** the approach (briefly)
3. **Delegate** to appropriate subagent via Task()
4. **Summarize** results for user
5. **Coordinate** multi-step workflows

### Task Delegation Patterns

| User Request | Delegate To |
|--------------|-------------|
| "implement X" | Task(dev): "Implement X with tests..." |
| "fix bug in Y" | Task(dev): "Fix Y, root cause analysis..." |
| "create feature Z" | Task(dev): "Create Z following patterns in..." |
| "refactor A" | Task(dev): "Refactor A, maintain tests..." |
| "understand how B works" | Task(Explore): "Analyze B subsystem..." |
| "review code in C" | Task(Explore): "Review C for issues..." |

### Task() Format

```
Task(agent_type): "[Clear instruction]

Context:
- [Relevant background]
- [Files to focus on]

Acceptance Criteria:
- [What must be true when done]
- [Tests to pass]

Constraints:
- [Quality standards]
- [Patterns to follow]"
```

### Available Agents

| Agent | Use For |
|-------|---------|
| `dev` | Code implementation, bug fixes, refactoring |
| `Explore` | Code analysis, understanding, investigation |
| `listing-browser` | Property listing extraction |
| `map-analyzer` | Location/geographic analysis |
| `image-assessor` | Visual property assessment |

### Main Agent Limits

- **Do NOT** implement features yourself
- **Do NOT** write large code blocks
- **Do NOT** read many files for exploration
- **DO** plan, delegate, summarize, coordinate

### Exception

Small fixes (<10 lines) that you're confident about can be done directly.
For anything substantial, **ALWAYS delegate via Task()**.

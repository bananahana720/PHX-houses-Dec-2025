---
name: track-subagent-completions
enabled: true
event: stop
action: warn
---

## 🤖 Subagent Work Complete - Orchestrator Checklist

**A Task() subagent has returned. As the orchestrator, you MUST now:**

### Immediate Actions

1. **Summarize for User**
   - Provide a concise summary of what the subagent accomplished
   - Highlight key changes, files modified, or decisions made
   - Report any issues or blockers encountered

2. **Update Task Tracking**
   - Mark the relevant todo item as `completed`
   - If subagent identified new work, add todos for it
   - Do NOT re-delegate the same work that was just completed

3. **Verify Completion**
   - Check if subagent's output satisfies the original requirement
   - If incomplete, create a NEW follow-up task (don't re-run same task)

### Anti-Patterns to Avoid

| Don't Do This | Do This Instead |
|---------------|-----------------|
| Re-delegate same work | Create follow-up task for gaps |
| Skip summarization | Always explain results to user |
| Leave todos in_progress | Update status immediately |
| Read files subagent just read | Trust subagent's analysis |

### Token Budget Reminder

As orchestrator, your response should be ~500-1000 tokens:
- Brief summary of subagent result
- Status update
- Next step (if any)

**Do NOT perform large implementations yourself - delegate to another subagent if more work needed.**

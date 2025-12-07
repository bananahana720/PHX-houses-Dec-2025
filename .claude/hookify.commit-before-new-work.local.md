---
name: commit-before-new-work
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (?i)(create|implement|add|build|develop|start|begin|new feature|new story|E\d+-[SR]\d+)
action: warn
---

## 💾 Commit Check Before New Work

**You may be starting new work. Check for uncommitted changes first.**

### Git Safety Protocol

Before starting significant new work:

1. **Check status**: `git status`
2. **Review changes**: `git diff --stat`
3. **Commit if needed**: `/commit` or `git commit -m "..."`

### Why This Matters
- Atomic commits enable easy rollback
- Uncommitted work can be lost or conflated
- Clean working tree makes debugging easier
- Follows BMAD best practices

### Quick Commands
```bash
git status                    # See what's changed
git diff --stat               # Summary of changes
git add -A && git commit -m "wip: checkpoint before new work"
```

### Exceptions
- If you're resuming existing work, ignore this warning
- If changes are intentionally uncommitted for review, proceed
- Use `/commit` when ready to commit properly

**This is a reminder, not a blocker. Proceed if appropriate.**

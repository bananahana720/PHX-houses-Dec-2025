---
name: block-shortcut-comments
enabled: true
event: file
pattern: \b(TODO|FIXME|HACK|XXX|TEMP|TEMPORARY)\b[:\s]
action: block
---

## 🛑 Shortcut Comment Blocked

**You attempted to add a shortcut/placeholder comment.**

### Detected Patterns
- `TODO:` - Deferred implementation
- `FIXME:` - Known broken code
- `HACK:` - Temporary workaround
- `XXX:` - Needs attention
- `TEMP/TEMPORARY:` - Placeholder code

### Why This Is Blocked
Per CLAUDE.md "No shortcuts or placeholders" policy:
- Deliver complete, working implementations
- Never add stubs, TODOs, or partial implementations
- Every deliverable must be production-ready

### What To Do Instead

1. **Implement it now** - Complete the feature before moving on
2. **Create a ticket** - Track in sprint backlog if deferral is approved
3. **Document in story** - Add to acceptance criteria if follow-up needed

### If This Is A Genuine Exception
- Get explicit user approval first
- Create a tracking ticket with timebox
- Disable this rule temporarily with `enabled: false`

**Remember**: Clean code ships without debugging artifacts.

# Claude Code Context Management Hooks

> Design specification for a complete context management lifecycle across Claude Code sessions.

---

## Overview

This document consolidates overlapping hook ideas into a unified system covering:

| Phase | Hook | Purpose |
|-------|------|---------|
| Pre-Read | CLAUDE.md Discovery | Ensure context files exist and are fresh |
| Pre-Read | Reference Validator | Catch stale line-number references |
| Post-Write | Delta Tracker | Track file changes for session wrap-up |
| Post-Task | Subagent Learnings | Extract subagent discoveries to main context |
| Stop | Session Checkpoint | Validate context updates before exit |

---

## 1. CLAUDE.md Discovery Hook

**Event:** `pretooluse`  
**Tool:** `Read`  
**Template:** `@.claude/templates/CLAUDE.md.template`

### Purpose

Ensure context files exist and are fresh before Claude reads into a directory.

### Flow

```
Read(file) triggered
        │
        ▼
Extract target_dir from file path
        │
        ▼
Check: {target_dir}/CLAUDE.md exists?
        │
        ├─► NO ──► Create template ──► exit 0 (silent)
        │
        ▼ YES
        │
        ├─► Check: mtime > STALE_THRESHOLD (24h)?
        │       └─► YES ──► exit 1 + warn "CLAUDE.md stale"
        │
        └─► Check: is_naked_template()?
                └─► YES ──► exit 1 + warn "CLAUDE.md unfilled"
        │
        ▼
exit 0 (proceed)
```

### Config

```yaml
STALE_THRESHOLD_HOURS: 24
TEMPLATE_MARKER: "<!-- TEMPLATE:UNFILLED -->"
```

### Hook Script

```bash
#!/bin/bash
# .claude/hooks/claude-md-check.sh

TARGET_DIR=$(dirname "$CLAUDE_TOOL_ARG_PATH")
CLAUDE_MD="$TARGET_DIR/CLAUDE.md"
STALE_HOURS=24

# Check existence
if [[ ! -f "$CLAUDE_MD" ]]; then
  cat > "$CLAUDE_MD" << 'EOF'
<!-- TEMPLATE:UNFILLED -->
<!-- Updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ") -->

# [Directory Name]

## What
[PURPOSE]

## Why
[ROLE]

## Structure
| Path | Description |
|------|-------------|

## Context Refs

## Pending
EOF
  exit 0
fi

# Check staleness
MTIME=$(stat -c %Y "$CLAUDE_MD" 2>/dev/null || stat -f %m "$CLAUDE_MD")
NOW=$(date +%s)
AGE_HOURS=$(( (NOW - MTIME) / 3600 ))

if (( AGE_HOURS > STALE_HOURS )); then
  echo "⚠️ CLAUDE.md in $TARGET_DIR is ${AGE_HOURS}h old. Consider refresh."
  exit 1
fi

# Check naked template
if grep -q "TEMPLATE:UNFILLED" "$CLAUDE_MD"; then
  echo "⚠️ CLAUDE.md in $TARGET_DIR is unfilled template."
  exit 1
fi

exit 0
```

### Template Detection

```bash
# Matches unfilled if:
grep -q "TEMPLATE:UNFILLED" "$CLAUDE_MD"

# OR all placeholder brackets remain:
grep -qE "^\[.+\]$" "$CLAUDE_MD"
```

---

## 2. Reference Validator Hook

**Event:** `pretooluse`  
**Tool:** `Read | View`

### Purpose

Catch stale line-number references before reads.

### Trigger

Path contains `:L` line reference (e.g., `src/main.py:L42`)

### Actions

1. Parse `file:line` from reference
2. Check if file modified since reference created
3. If `mtime > ref_time` → warn "lines may have shifted"
4. Suggest re-grep to validate

### Exit Codes

| Code | Action |
|------|--------|
| 0 | Proceed |
| 1 | Warn with suggestion |

---

## 3. Delta Tracker Hook

**Event:** `posttooluse`  
**Tool:** `Write | Edit | MultiEdit`

### Purpose

Track file changes for session wrap-up.

### Actions

- Append to `.claude/session-delta.log`:
  - `timestamp`
  - `file_path`
  - `change_type` (create | modify | delete)
  - `line_count_delta`
- If new file in dir without CLAUDE.md → flag

### Output

Silent (logging only)

---

## 4. Subagent Learnings Capture Hook

**Event:** `posttooluse`  
**Tool:** `Task`

### Purpose

Extract subagent discoveries back to main context.

### Actions

1. Parse task output for:
   - New patterns/anti-patterns
   - File references created
   - Pending items returned
2. Update `toolkit.json` if new tool usage patterns

### Output

```
[subagent] returned: [summary]
```

---

## 5. Session Stop Checkpoint Hook

**Event:** `Stop | Subagent-stop`

### Purpose

Validate context hygiene before session exit.

### Prompt Injection

```markdown
STOP CHECK — Answer JSON only:

Criteria (Y/N each):
- child CLAUDE.md(s) updated in touched dirs?
- Pending work documented?
- Session learnings captured?

{"pass": bool, "block": "reason | null"}
```

---

## Exit Code Reference

| Code | Meaning | Claude Action |
|------|---------|---------------|
| 0 | OK | Proceed |
| 1 | Warning | Show message, proceed |
| 2 | Block | Halt, require action |

---

## Implementation Checklist

- [ ] Create `.claude/hooks/` directory structure
- [ ] Implement `claude-md-check.sh`
- [ ] Implement `delta-tracker.sh`
- [ ] Implement `reference-validator.sh`
- [ ] Implement `subagent-capture.sh`
- [ ] Implement `stop-checkpoint.sh`
- [ ] Register hooks in `.claude/settings.json`
- [ ] Sanity check CLAUDE.md template at `.claude/templates/CLAUDE.md.template`
- [ ] Test each hook in isolation
- [ ] Integration test full session lifecycle

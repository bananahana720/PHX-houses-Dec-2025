---
last_updated: 2025-12-04T10:32:00Z
updated_by: agent
staleness_hours: 24
line_target: 70
flags: []
---
# .claude/hooks

## Purpose
Hook system for stop-the-line quality gates, tool usage enforcement, session hygiene, and security constraints.

## Contents
| File | Purpose |
|------|---------|
| `stop_hygiene_hook.py` | Block exit if CLAUDE.md missing/stale/oversized; auto-approve agents |
| `bash_hook.py` | Block unsafe bash (cat, grep, find) → enforce proper tools |
| `env_file_protection_hook.py` | Block .env access (security) |
| `git_add_block_hook.py` | Prevent secrets in commits |
| `rm_block_hook.py` | Require approval for destructive ops |
| `delta_tracker_hook.py` | Track file mods via session-delta.log |
| `format_python_hook.py` | Auto-format Python with ruff |
| `lib/claude_md_utils.py` | Shared: check_claude_md_exists(), is_stale() |
| `lib/delta_logger.py` | Shared: get_modified_directories(), skip patterns |

## Key Patterns
- **Stop-the-line**: Hooks block actions until issues resolved
- **Agent detection**: agent-*.jsonl auto-approve, UUID.jsonl blocked
- **JSON protocol**: stdin=event data, stdout=decision, stderr=logs

## Hook Categories
| Category | Hooks | Action |
|----------|-------|--------|
| **Session hygiene** | stop_hygiene_hook | Block if CLAUDE.md incomplete |
| **Tool enforcement** | bash_hook, grep_block | Redirect to Read/Grep/Glob |
| **Security** | env_file_protection, git_add_block | Block secrets exposure |
| **Cleanup** | session_cleanup, delta_tracker | Manage transient state |

## Excluded Directories (no CLAUDE.md tracking)
`__pycache__`, `.mypy_cache`, `.venv`, `.git`, `.claude/audio`, `.claude/logs`, `.agentvibes`, `.playwright-mcp`, `data/api_cache`, `TRASH`, `archive`, `reports`

## Tasks
- [ ] Add pre-commit lint/type-check hooks `P:M`
- [ ] Add hook effectiveness telemetry `P:L`

## Learnings
- Agent sessions auto-approve (don't manage CLAUDE.md)
- Oversized detection: >100 lines triggers distillation prompt
- Exit code always 0; decision in JSON stdout

## Refs
- Stop logic: `stop_hygiene_hook.py:137-240`
- Exclusions: `stop_hygiene_hook.py:73-109`
- Delta tracking: `lib/delta_logger.py:121-158`

## Deps
← `lib/claude_md_utils.py`, `lib/delta_logger.py`, `session-delta.log`
→ Claude Code hook system, git operations, bash execution

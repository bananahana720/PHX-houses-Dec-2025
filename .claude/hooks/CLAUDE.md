---
last_updated: 2025-12-05T11:30:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# .claude/hooks

## Purpose
Quality gate and safety constraint system enforcing stop-the-line compliance checks, tool usage redirection, session hygiene, and security boundaries.

## Core Python Hooks
| File | Purpose | Category |
|------|---------|----------|
| `stop_hygiene_hook.py` | Block exit if CLAUDE.md missing/stale/oversized; auto-approve agent sessions | Session hygiene |
| `bash_hook.py` | Block unsafe bash (cat, grep, find, head, tail) → redirect to Read/Grep/Glob tools | Tool enforcement |
| `env_file_protection_hook.py` | Block .env file access (cat, vi, nano, grep) | Security |
| `git_add_block_hook.py` | Prevent wildcards in git add commands | Security |
| `git_commit_block_hook.py` | Block commits during active work phases | Session control |
| `delta_tracker_hook.py` | Log file modifications to session-delta.log for wrap-up context | Delta tracking |
| `format_python_hook.py` | Auto-format Python with ruff on edit | Code quality |
| `rm_block_hook.py` | Require approval for rm/rmdir commands | Safety |
| `session_cleanup_hook.py` | Clean transient state on session exit | Cleanup |
| `file_size_conditional_hook.py` | Warn/block operations on large files | Performance |

## Shared Libraries
| File | Purpose |
|------|---------|
| `lib/claude_md_utils.py` | Validators: check_claude_md_exists(), is_stale(), validate_line_count() |
| `lib/delta_logger.py` | File tracking: log_delta(), get_modified_directories(), skip patterns |

## Key Patterns
- **Stop-the-line enforcement**: Blocks until issues resolved; exit code always 0, decision in JSON stdout
- **Agent detection**: agent-*.jsonl auto-approve; UUID.jsonl subject to full checks
- **JSON protocol**: stdin receives hook event with transcript_path, stdout returns decision struct
- **Graceful degradation**: Import failures don't cascade; individual check failures contained

## Excluded Directories (no CLAUDE.md tracking)
`__pycache__`, `.mypy_cache`, `.venv`, `.git`, `.claude/audio`, `.claude/logs`, `.agentvibes`, `.playwright-mcp`, `data/api_cache`, `TRASH`, `archive`, `reports`

## Tasks
- [ ] Add pre-commit lint/type-check hooks `P:M`
- [ ] Document hook registration in main CLAUDE.md `P:M`
- [ ] Add hook telemetry/effectiveness metrics `P:L`

## Learnings
- Agent sessions bypass CLAUDE.md checks (auto-approve agent-*.jsonl)
- Oversized detection: >100 lines triggers distillation prompt to user
- Deleted files don't generate delta entries (safety pattern)

## Refs
- Session hygiene: `stop_hygiene_hook.py:37-95`
- Delta logging: `lib/delta_logger.py:50-120`
- Exclusion list: `stop_hygiene_hook.py:73-109`

## Deps
← `lib/claude_md_utils.py`, `lib/delta_logger.py`, `session-delta.log`
→ Claude Code hook system, git operations, bash execution, tool redirection

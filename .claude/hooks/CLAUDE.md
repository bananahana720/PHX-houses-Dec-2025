---
last_updated: 2025-12-07T16:00:00Z
updated_by: Claude Code
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
| `session_start_hook.py` | Inject orchestration protocol at session start | Orchestration |
| `stop_hygiene_hook.py` | Block exit if CLAUDE.md missing/stale/oversized | Session hygiene |
| `bash_hook.py` | Block unsafe bash (cat, grep, find, head, tail) → redirect to Read/Grep/Glob | Tool enforcement |
| `env_file_protection_hook.py` | Block .env file access (cat, vi, nano, grep) | Security |
| `git_add_block_hook.py` | Prevent wildcards in git add commands | Security |
| `git_commit_block_hook.py` | Speed bump for commits (first block, second allow) | Session control |
| `git_checkout_safety_hook.py` | Warn about uncommitted changes before checkout | Safety |
| `delta_tracker_hook.py` | Log file modifications to session-delta.log | Delta tracking |
| `format_python_hook.py` | Auto-format Python with `ruff format` + `ruff check --fix` | Code quality |
| `rm_block_hook.py` | Redirect rm to TRASH directory | Safety |
| `session_cleanup_hook.py` | Clean transient state on session exit | Cleanup |
| `file_size_conditional_hook.py` | Block large file reads (>750 lines main, >10k subagent) | Performance |
| `precompact_hook.py` | Generate context optimization template for /compact | Context mgmt |
| `security_reminder_hook.py` | Warn about security patterns (eval, innerHTML, etc.) | Security |
| `architecture-consistency-check.py` | Verify key architecture values match across docs (pre-commit) | Documentation |

## Orchestration Hooks
| File | Purpose | Category |
|------|---------|----------|
| `user_prompt_submit_hook.py` | Inject orchestration guidelines on every prompt | Orchestration |

## Shared Libraries
| File | Purpose |
|------|---------|
| `lib/config.py` | Centralized thresholds: FILE_SIZE, CLAUDE_MD, SESSION, SECURITY configs |
| `lib/hook_io.py` | JSON I/O: read_hook_input(), write_hook_output(), approve(), block() |
| `lib/claude_md_utils.py` | Validators: check_claude_md_exists(), is_stale(), create_from_template() |
| `lib/delta_logger.py` | File tracking: log_delta(), get_modified_directories() |
| `lib/exclusions.py` | Path filtering: should_exclude_directory(), EXCLUDED_DIRS |
| `lib/reference_parser.py` | Line reference validation: validate_line_reference() |

## Key Patterns
- **Stop-the-line enforcement**: Blocks until issues resolved; exit code always 0, decision in JSON stdout
- **Agent detection**: agent-*.jsonl auto-approve; UUID.jsonl subject to full checks
- **JSON protocol**: stdin receives hook event with transcript_path, stdout returns decision struct
- **Graceful degradation**: Import failures don't cascade; individual check failures contained

## Excluded Directories (no CLAUDE.md tracking)
`__pycache__`, `.mypy_cache`, `.venv`, `.git`, `.claude/audio`, `.claude/logs`, `.agentvibes`, `.playwright-mcp`, `data/api_cache`, `TRASH`, `archive`, `reports`

## Tasks
- [ ] Add hook telemetry/effectiveness metrics `P:L`
- [x] Create lib/config.py for centralized thresholds `P:M` ✓ 2025-12-07
- [x] Create lib/hook_io.py for standardized I/O `P:M` ✓ 2025-12-07
- [x] Fix bash_hook.py to block cat/head/tail `P:H` ✓ 2025-12-07
- [x] Remove /compact duplication from user_prompt_submit `P:M` ✓ 2025-12-07
- [x] Add architecture consistency pre-commit hook `P:M` ✓ 2025-12-07

## Learnings
- Agent sessions bypass CLAUDE.md checks (auto-approve agent-*.jsonl)
- Oversized detection: >100 lines triggers distillation prompt to user
- Deleted files don't generate delta entries (safety pattern)
- Removed broken grep_block_hook.py, bash_grep_check.py (2025-12-07)
- format_python_hook uses ruff only (black removed 2025-12-07)
- Architecture consistency hook catches doc drift early (Epic 2 Audit 2025-12-07)

## Refs
- Centralized config: `lib/config.py` (all thresholds)
- Hook I/O utilities: `lib/hook_io.py` (JSON protocol helpers)
- Session hygiene: `stop_hygiene_hook.py:60-208`
- Delta logging: `lib/delta_logger.py:147-202`
- Exclusion list: `lib/exclusions.py:23-59`

## Deps
← `lib/*.py` (config, hook_io, claude_md_utils, delta_logger, exclusions, reference_parser)
→ Claude Code hook system, git operations, bash execution, tool redirection

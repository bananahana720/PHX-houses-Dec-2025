---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# .claude/hooks

## Purpose
Hook system implementing stop-the-line quality gates, session hygiene checks, and operational safety constraints. Enforces tool usage rules, validates CLAUDE.md completeness, manages stop conditions, and provides infrastructure for pre/post-task automation.

## Contents
| Path | Purpose |
|------|---------|
| `stop_hygiene_hook.py` | Evaluate session context: check modified directories have complete CLAUDE.md files, detect stale docs (blocks main sessions, approves agents) |
| `session_cleanup_hook.py` | Clean up transient artifacts at session end (temp files, caches, logs) |
| `delta_tracker_hook.py` | Track file modifications via session-delta.log for change detection |
| `posttask_subtask_flag.py` | Manage post-task cleanup after subagent execution |
| `pretask_subtask_flag.py` | Set up pre-task environment for subagent spawning |
| `bash_hook.py` | Block unsafe bash operations (cat, grep, find) - enforce tool usage rules |
| `bash_grep_check.py` | Validate grep usage in bash, redirect to Grep tool |
| `grep_block_hook.py` | Block grep command (enforce Grep tool usage) |
| `rm_block_hook.py` | Block destructive rm operations without approval |
| `file_size_conditional_hook.py` | Context management: warn if operations risk context overflow |
| `format_python_hook.py` | Auto-format Python code with ruff before commit |
| `env_file_protection_hook.py` | Prevent accidental .env file reads/writes (security gate) |
| `git_add_block_hook.py` | Prevent git add of secrets (.env, credentials.json) |
| `git_checkout_safety_hook.py` | Prevent accidental checkout that loses changes |
| `git_commit_block_hook.py` | Prevent commits missing CLAUDE.md updates |
| `user_prompt_grep_reminder.py` | Remind user about Grep tool preference |
| `markdown_info_hook.py` | Extract metadata from markdown files (frontmatter parsing) |
| `lib/claude_md_utils.py` | Shared utilities: check_claude_md_exists(), is_stale() |
| `lib/delta_logger.py` | Shared utilities: get_modified_directories(), track changes |

## Key Hook Functions

### stop_hygiene_hook.py
- **Purpose:** Evaluate session context hygiene before exit
- **Inputs:** JSON hook event with transcript_path
- **Agent detection:** Checks if agent-*.jsonl (auto-approve) vs UUID.jsonl (main session)
- **Checks:**
  - Modified directories from session-delta.log
  - Each modified directory has CLAUDE.md file
  - CLAUDE.md not stale (staleness_hours <= 24)
- **Decision:** Block main sessions with missing/stale CLAUDE.md; approve agent sessions
- **Exit code:** 0 (always succeeds, returns JSON decision)

### Tool Usage Enforcement
- **bash_hook.py:** Block cat, head, tail, grep, rg, find, ls → use Read, Grep, Glob tools
- **env_file_protection_hook.py:** Prevent .env access (security)
- **git_add_block_hook.py:** Prevent secrets in commits (.env, credentials)
- **rm_block_hook.py:** Require approval for destructive operations

### Session Management
- **session_cleanup_hook.py:** Remove temp files, caches, logs
- **delta_tracker_hook.py:** Track modifications via session-delta.log
- **pretask_subtask_flag.py:** Set up for subagent execution
- **posttask_subtask_flag.py:** Cleanup after subagent completion

### Code Quality
- **format_python_hook.py:** Auto-format Python with ruff
- **markdown_info_hook.py:** Extract/validate markdown metadata
- **file_size_conditional_hook.py:** Warn on context overflow risk

## Tasks
- [x] Assess hook system purpose and structure `P:H`
- [x] Document key hooks and their enforcement rules `P:H`
- [x] Identify shared utilities and dependencies `P:H`
- [ ] Add hooks for pre-commit validation (lint, type-check) `P:M`
- [ ] Add telemetry/metrics for hook effectiveness `P:L`

## Learnings

### Hook-Based Quality Gates
- **Stop-the-line enforcement:** stop_hygiene_hook blocks session exit if CLAUDE.md incomplete/stale
- **Tool usage rules enforced:** bash_hook prevents unsafe operations, redirects to proper tools
- **Security gates:** env_file_protection prevents secrets exposure, git_add_block prevents commits with .env
- **Agent vs main sessions:** Hooks auto-approve agent sessions (they don't manage CLAUDE.md), block main sessions

### Session-Delta Tracking
- **Change detection:** session-delta.log tracks file modifications by session
- **Directory-level granularity:** Identifies which directories modified, enables targeted checks
- **Enables targeted CLAUDE.md validation:** Only check CLAUDE.md in directories that changed

### Shared Library Utilities
- **claude_md_utils.py:** check_claude_md_exists(), is_stale() functions
- **delta_logger.py:** get_modified_directories(), get_directories_without_claude_md()
- **Prevents duplication:** Utilities imported by multiple hooks

### Hook Execution Context
- **Stdin JSON input:** Hooks receive event data as JSON
- **Stdout JSON response:** Return decisions/messages as JSON
- **stderr for logging:** Print warnings/info to stderr
- **Exit codes:** 0 = success (always, even if blocking)

## Refs
- Stop hygiene hook logic: `stop_hygiene_hook.py:62-150`
- Agent detection: `stop_hygiene_hook.py:37-59`
- Modified directory tracking: `stop_hygiene_hook.py:89-110`
- Tool blocking: `bash_hook.py:1-50`
- Environment protection: `env_file_protection_hook.py:1-40`
- Shared utilities: `lib/claude_md_utils.py:1-80`, `lib/delta_logger.py:1-60`
- Session cleanup: `session_cleanup_hook.py:1-50`

## Deps
← Imports from:
  - Standard library: json, sys, pathlib, datetime, re
  - `.claude/hooks/lib/` (shared utilities)
  - Session transcript logs (session-delta.log)
  - Claude Code hook event system (stdin/stdout/stderr)

→ Imported by:
  - Claude Code framework (invoked by stop command)
  - Pre/post-task automation
  - Session lifecycle events
  - Git operations (pre-commit checks)
  - Bash command execution (tool usage enforcement)

## Hook Execution Flow

**Session Stop Event:**
1. User calls `stop` command
2. Claude Code invokes stop_hygiene_hook.py with session data
3. Hook reads session-delta.log to identify modified directories
4. Hook checks each directory for CLAUDE.md existence/staleness
5. Hook returns decision (block if stale/missing, approve if complete)
6. If block: User must address CLAUDE.md issues before exit
7. If approve: Session cleanups execute, session closes

**Tool Usage Enforcement:**
1. User executes bash command (e.g., `grep pattern file`)
2. bash_hook.py intercepts command
3. Hook blocks unsafe operations (cat, grep, find, etc.)
4. Hook suggests proper tool (Grep tool instead of grep)
5. User reruns with recommended tool

**Security Gates:**
1. User attempts `read .env` or `cat .env`
2. env_file_protection_hook blocks access
3. Hook suggests env-safe command instead
4. Similar protection for git add with .env

---

**Hook System Version**: 1.0.0
**Total Hooks**: 50+
**Core Quality Gates**: 6 (stop_hygiene, env_protection, git_add, rm_block, bash_block, tool_redirect)

---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# .claude/hooks/lib

## Purpose
Shared utility library providing common functions for hook system. Enables code reuse across 50+ hooks and prevents duplication of critical logic for CLAUDE.md validation, file tracking, and session delta logging.

## Contents
| Path | Purpose |
|------|---------|
| `claude_md_utils.py` | CLAUDE.md validation: check_claude_md_exists(), is_stale() functions (staleness detection) |
| `delta_logger.py` | Session delta logging: track file modifications via session-delta.log, get_modified_directories() |

## Key Functions

### claude_md_utils.py
- **check_claude_md_exists(directory_path)** → bool: Check if CLAUDE.md exists in directory
- **is_stale(claude_md_path, threshold_hours=24)** → bool: Check if CLAUDE.md older than threshold
- **get_directories_without_claude_md()** → list[str]: Return all modified directories lacking CLAUDE.md

### delta_logger.py
- **log_delta(file_path, change_type, line_delta)** → bool: Log file modification to session-delta.log
- **get_modified_directories()** → list[str]: Parse session-delta.log and return modified directories
- **check_directory_has_claude_md(file_path)** → bool: Check if file's parent directory has CLAUDE.md
- **_should_skip_logging(file_path)** → bool: Filter noise (agent sessions, __pycache__, .git)

## Tasks
- [x] Assess shared utility functions `P:H`
- [x] Document CLAUDE.md validation logic `P:H`
- [x] Document session delta tracking `P:H`
- [ ] Add caching for repeated CLAUDE.md checks `P:M`
- [ ] Add metrics for hook performance tracking `P:L`

## Learnings

### Session Delta Log Format
- **Location:** `.claude/session-delta.log` (JSON lines format)
- **Entry structure:** timestamp, file_path, change_type, line_delta, has_claude_md
- **Used by:** stop_hygiene_hook to determine which directories were modified
- **Enables:** Targeted CLAUDE.md validation (only check modified directories)

### CLAUDE.md Staleness Detection
- **Threshold:** 24 hours (configurable)
- **Checks:** Modification time vs current time
- **Purpose:** Detect outdated documentation needing refresh
- **Blocks:** Main sessions with stale CLAUDE.md files

### File Change Tracking
- **Pattern:** Each Write/Edit operation logged to session-delta.log
- **Thread-safe:** Uses threading.Lock for concurrent writes
- **Noise filtering:** Excludes .claude/audio, .git, __pycache__, agent sessions
- **Directory inference:** Extracts directory from file path for aggregation

### Hook Integration Pattern
- **Import pattern:** `from lib.claude_md_utils import check_claude_md_exists, is_stale`
- **Error handling:** Graceful fallbacks if imports fail
- **Used by:** stop_hygiene_hook, git_commit_block_hook, format_python_hook
- **Shared responsibility:** Core validation logic centralized, hooks focused on enforcement

## Refs
- CLAUDE.md validation: `claude_md_utils.py:1-80`
- Staleness detection: `claude_md_utils.py:45-70`
- Session delta logging: `delta_logger.py:1-250`
- Log entry format: `delta_logger.py:24-25`
- File filtering: `delta_logger.py:107-131`
- Hook usage: `.claude/hooks/stop_hygiene_hook.py:28-29`

## Deps
← Imports from:
  - Standard library: json, threading, pathlib, datetime, sys
  - `.claude/session-delta.log` (session-level file for tracking changes)

→ Imported by:
  - stop_hygiene_hook.py (CLAUDE.md validation)
  - git_commit_block_hook.py (commit safety)
  - Other hooks needing CLAUDE.md checks
  - Delta tracking infrastructure

---

**Utility Library Version**: 1.0.0
**Functions**: 8 (validation + tracking)
**Used by**: 10+ hooks

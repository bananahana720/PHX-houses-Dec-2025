---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
---

# .claude/hooks/lib

## Purpose
Shared utility library providing validation, tracking, and filtering logic for 50+ hooks. Enables code reuse across hook system for CLAUDE.md checks, session delta logging, and exclusion patterns.

## Contents
| File | Purpose | Key Functions |
|------|---------|----------------|
| `__init__.py` | Package exports | Exposes 11 utilities to hooks |
| `claude_md_utils.py` | CLAUDE.md validation | check_claude_md_exists(), is_stale(), parse_frontmatter(), create_from_template() |
| `reference_parser.py` | Line reference validation | parse_line_reference(), check_reference_freshness(), validate_line_reference() |
| `delta_logger.py` | Session delta tracking | log_delta_async(), check_directory_has_claude_md(), get_modified_directories() |
| `exclusions.py` | Exclusion patterns | should_exclude_directory(), should_skip_logging(), normalize_path() |

## Key Utilities

### CLAUDE.md Validation (claude_md_utils.py)
- `check_claude_md_exists(directory)` - Check if CLAUDE.md exists
- `is_stale(file_path, threshold_hours=24)` - Detect outdated CLAUDE.md
- `is_naked_template(file_path)` - Detect unfilled template placeholders
- `parse_frontmatter(file_path)` - Extract YAML metadata (last_updated, staleness_hours)
- `create_from_template(directory)` - Generate CLAUDE.md from template

### Line Reference Validation (reference_parser.py)
- `parse_line_reference(path)` - Parse file:L42-L100 patterns
- `check_reference_freshness(file_path)` - Warn if file modified recently (4h default)
- `validate_line_reference(path)` - Full validation (exists + freshness)

### Session Delta Tracking (delta_logger.py)
- `log_delta_async(file_path, change_type, line_delta)` - Log file modification to session-delta.log
- `check_directory_has_claude_md(file_path)` - Check parent directory for CLAUDE.md
- `get_modified_directories()` - Parse log and return directories with changes

### Exclusion Patterns (exclusions.py)
- `should_exclude_directory(directory)` - Filter CLAUDE.md validation scopes
- `should_skip_logging(file_path)` - Filter noise from delta tracking
- `normalize_path(path)` - POSIX-normalize for cross-platform comparison

## Excluded Directories
Caches: `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `node_modules`
Build: `dist`, `build`, `.egg-info`, `htmlcov`
Env: `.venv`, `venv`, `env`
System: `.git`
Claude: `.claude/audio`, `.claude/logs`, `.agentvibes`, `.playwright-mcp`
Project: `data/api_cache`, `data/archive`, `data/property_images/processed`, `TRASH`, `archive`, `reports`

## Session Delta Log Format
Location: `.claude/session-delta.log` (JSON lines, one entry per modification)
```json
{
  "timestamp": "2025-12-07T10:30:00Z",
  "file_path": "src/main.py",
  "change_type": "modify",
  "line_delta": 15,
  "has_claude_md": true
}
```

## Usage Pattern
```python
# Import in hooks
from lib.claude_md_utils import check_claude_md_exists, is_stale
from lib.exclusions import should_exclude_directory
from lib.delta_logger import log_delta_async

# Validate CLAUDE.md exists and is current
if not check_claude_md_exists(dir):
    print("Missing CLAUDE.md")
if is_stale(path, threshold_hours=24):
    print("CLAUDE.md stale")

# Filter excluded directories
if should_exclude_directory(dir):
    continue

# Track changes
await log_delta_async(file_path, "modify", line_count)
```

## Integration Points
- **stop_hygiene_hook.py**: Uses claude_md_utils + exclusions for validation
- **delta_tracker_hook.py**: Uses delta_logger for file change tracking
- **git_commit_block_hook.py**: Uses claude_md_utils for CLAUDE.md checks
- **10+ other hooks**: Import utilities as needed

## Deps
← Imports: pathlib, json, threading, datetime, re (stdlib only)
← Data: `.claude/session-delta.log` (session-level change tracking)
→ Imported by: all hook modules requiring CLAUDE.md, delta, or exclusion logic

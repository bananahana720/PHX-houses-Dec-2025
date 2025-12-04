#!/usr/bin/env python3
"""
PostToolUse hook for Edit|Write tools: Session delta tracking.

Logs all file modifications to .claude/session-delta.log for:
- Session wrap-up context
- CLAUDE.md update reminders
- Change history tracking

This hook is non-blocking (always exits 0) and uses async logging
to minimize impact on edit operations.

Exit codes:
- 0: Always (logging is non-blocking)
"""

import json
import sys
from pathlib import Path

# Import shared utilities
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.delta_logger import check_directory_has_claude_md, log_delta_async

    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False

# Load input from stdin
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# If lib not available, skip logging
if not LIB_AVAILABLE:
    sys.exit(0)

# Get file path and tool name
tool_name = data.get("tool_name", "")
file_path = data.get("tool_input", {}).get("file_path", "")

if not file_path:
    sys.exit(0)

# Determine change type based on tool and file existence
path = Path(file_path)

if tool_name == "Write":
    # Write tool: could be create or overwrite
    # We can't easily tell, so mark as "write"
    change_type = "write"
elif tool_name == "Edit":
    change_type = "modify"
else:
    change_type = "unknown"

# Log the delta asynchronously (non-blocking)
try:
    thread = log_delta_async(file_path, change_type, line_delta=None)

    # Check if directory has CLAUDE.md
    if not check_directory_has_claude_md(file_path):
        dir_path = path.parent
        # Only warn if it's not an excluded directory
        excluded = {
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            ".claude/audio",
            "TRASH",
        }
        if not any(part in excluded for part in dir_path.parts):
            print(
                f"INFO: File modified in directory without CLAUDE.md: {dir_path}",
                file=sys.stderr,
            )
except Exception as e:
    # Logging failure is not critical - don't block the operation
    print(f"DEBUG: Delta logging failed: {e}", file=sys.stderr)

# Always allow the operation to proceed
sys.exit(0)

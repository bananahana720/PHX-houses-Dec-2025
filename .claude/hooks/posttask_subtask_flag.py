#!/usr/bin/env python3
"""
PostToolUse hook for Task tool: Removes flag file after subtask completes.
Cleanup ensures main agent context is restored after subagent finishes.
"""
import os
import sys

# Remove the flag file when exiting the subtask
flag_file = '.claude_in_subtask.flag'
try:
    if os.path.exists(flag_file):
        os.remove(flag_file)
    sys.exit(0)
except Exception as e:
    # If we can't remove the flag, still allow (non-critical)
    print(f"Warning: Could not remove subtask flag: {e}", file=sys.stderr)
    sys.exit(0)
#!/usr/bin/env python3
"""
PreToolUse hook for Task tool: Creates flag file to indicate we're in a subtask.
This allows other hooks to adjust their behavior for subagents vs main agent.
"""
import sys

# Create a flag file indicating we're entering a subtask
flag_file = '.claude_in_subtask.flag'
try:
    with open(flag_file, 'w') as f:
        f.write('1')
    # Exit 0 to allow Task tool execution
    sys.exit(0)
except Exception as e:
    # If we can't create the flag, still allow (non-critical)
    print(f"Warning: Could not create subtask flag: {e}", file=sys.stderr)
    sys.exit(0)

#!/usr/bin/env python3
"""
Check for grep usage in bash commands.
Should be imported by bash_hook.py.
"""
import re


def check_grep_usage(command: str):
    """
    Check if bash command uses grep instead of rg.
    Returns tuple: (should_block: bool, reason: str or None)
    """
    # Don't block grep in git commands (git grep is fine)
    if 'git' in command.lower():
        return False, None

    # Check for standalone grep command
    # Match: grep as word boundary (not part of another word)
    if re.search(r'\bgrep\b', command):
        reason = """Use 'rg' (ripgrep) instead of 'grep' for faster and better search results.

The Grep tool (capital G) uses ripgrep internally and is preferred.
If you need bash grep for specific reasons, use 'git grep' or explain why."""
        return True, reason

    return False, None


if __name__ == "__main__":
    import json
    import sys

    data = json.load(sys.stdin)
    command = data.get("tool_input", {}).get("command", "")

    should_block, reason = check_grep_usage(command)

    if should_block:
        print(reason, file=sys.stderr)
        sys.exit(2)
    else:
        sys.exit(0)

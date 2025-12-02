#!/usr/bin/env python3
"""
Unified Bash hook that combines all bash command safety checks.
This ensures that if ANY check wants to block, the command is blocked.
"""
import json
import sys
import os

# Add hooks directory to Python path so we can import the other modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import check functions from other hooks
from git_add_block_hook import check_git_add_command
from git_checkout_safety_hook import check_git_checkout_command
from git_commit_block_hook import check_git_commit_command
from rm_block_hook import check_rm_command
from env_file_protection_hook import check_env_file_access
from bash_grep_check import check_grep_usage


def main():
    data = json.load(sys.stdin)
    
    # Check if this is a Bash tool call
    tool_name = data.get("tool_name")
    if tool_name != "Bash":
        # Not a Bash command, allow
        sys.exit(0)
    
    # Get the command being executed
    command = data.get("tool_input", {}).get("command", "")
    
    # Run all checks - collect all blocking reasons
    checks = [
        check_rm_command,
        check_git_add_command,
        check_git_checkout_command,
        check_git_commit_command,
        check_env_file_access,
        check_grep_usage,
    ]
    
    blocking_reasons = []
    
    for check_func in checks:
        should_block, reason = check_func(command)
        if should_block:
            blocking_reasons.append(reason)
    
    # If any check wants to block, block the command
    if blocking_reasons:
        # If multiple checks want to block, combine the reasons
        if len(blocking_reasons) == 1:
            combined_reason = blocking_reasons[0]
        else:
            combined_reason = "Multiple safety checks failed:\n\n"
            for i, reason in enumerate(blocking_reasons, 1):
                combined_reason += f"{i}. {reason}\n\n"

        # Exit code 2 blocks execution, stderr is shown to Claude
        print(combined_reason, file=sys.stderr)
        sys.exit(2)
    else:
        # Exit code 0 allows execution
        sys.exit(0)


if __name__ == "__main__":
    main()
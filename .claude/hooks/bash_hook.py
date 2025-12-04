#!/usr/bin/env python3
"""
Unified Bash hook that combines all bash command safety checks.
This ensures that if ANY check wants to block, the command is blocked.

Each check module is imported with error handling so a single broken
module doesn't disable all safety checks.
"""
import json
import os
import sys

# Add hooks directory to Python path so we can import the other modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import check functions from other hooks with graceful degradation
# If a module fails to import, log the error and use a no-op function


def _noop_check(command: str) -> tuple[bool, str | None]:
    """No-op check function used when a module fails to import."""
    return (False, None)


def _safe_import(module_name: str, func_name: str):
    """Safely import a check function, returning noop on failure."""
    try:
        module = __import__(module_name)
        return getattr(module, func_name)
    except (ImportError, SyntaxError, AttributeError) as e:
        print(f"ERROR: bash_hook: Failed to import {func_name} from {module_name}: {e}", file=sys.stderr)
        return _noop_check


check_grep_usage = _safe_import("bash_grep_check", "check_grep_usage")
check_env_file_access = _safe_import("env_file_protection_hook", "check_env_file_access")
check_git_add_command = _safe_import("git_add_block_hook", "check_git_add_command")
check_git_checkout_command = _safe_import("git_checkout_safety_hook", "check_git_checkout_command")
check_git_commit_command = _safe_import("git_commit_block_hook", "check_git_commit_command")
check_rm_command = _safe_import("rm_block_hook", "check_rm_command")


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

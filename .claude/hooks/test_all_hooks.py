#!/usr/bin/env python3
"""
Comprehensive test suite for all Claude Code hooks.
Tests executability, basic functionality, and error handling.
"""
import json
import subprocess
import sys
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def test_hook(hook_path, test_input, test_name, expect_block=False):
    """Test a hook script with given input."""
    print(f"\n{BLUE}Testing: {test_name}{RESET}")
    print(f"  Hook: {hook_path.name}")

    try:
        # Run the hook with JSON input
        result = subprocess.run(
            ["python", str(hook_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=5
        )

        # Check execution
        if result.returncode == 0 and not expect_block:
            print(f"  {GREEN}✓ PASS{RESET} - Hook allowed operation (exit 0)")
            if result.stdout:
                print(f"    Output: {result.stdout.strip()[:100]}")
            return True
        elif result.returncode != 0 and expect_block:
            print(f"  {GREEN}✓ PASS{RESET} - Hook blocked operation (exit {result.returncode})")
            if result.stderr:
                print(f"    Reason: {result.stderr.strip()[:150]}")
            return True
        elif result.returncode != 0 and not expect_block:
            print(f"  {RED}✗ FAIL{RESET} - Unexpected block (exit {result.returncode})")
            print(f"    Error: {result.stderr.strip()}")
            return False
        else:
            print(f"  {RED}✗ FAIL{RESET} - Expected block but got allow (exit 0)")
            return False

    except subprocess.TimeoutExpired:
        print(f"  {RED}✗ FAIL{RESET} - Hook timed out (>5s)")
        return False
    except Exception as e:
        print(f"  {RED}✗ FAIL{RESET} - Exception: {e}")
        return False

def main():
    """Run all hook tests."""
    hooks_dir = Path(__file__).parent

    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Claude Code Hooks Test Suite - WSL Runtime{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    results = []

    # Test 1: bash_hook.py - Safe command (should allow)
    results.append(test_hook(
        hooks_dir / "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo 'hello world'"},
            "session_id": "test",
            "cwd": "/test"
        },
        "bash_hook.py - Safe command (echo)",
        expect_block=False
    ))

    # Test 2: bash_hook.py - Dangerous rm (should block)
    results.append(test_hook(
        hooks_dir / "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf important.txt"},
            "session_id": "test",
            "cwd": "/test"
        },
        "bash_hook.py - Dangerous rm command",
        expect_block=True
    ))

    # Test 3: bash_hook.py - Dangerous git add (should block)
    results.append(test_hook(
        hooks_dir / "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git add -A"},
            "session_id": "test",
            "cwd": "/test"
        },
        "bash_hook.py - Dangerous git add -A",
        expect_block=True
    ))

    # Test 4: file_size_conditional_hook.py - Small file (should allow)
    results.append(test_hook(
        hooks_dir / "file_size_conditional_hook.py",
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/small.txt", "limit": 100},
            "session_id": "test",
            "cwd": "/test"
        },
        "file_size_conditional_hook.py - Small file read",
        expect_block=False
    ))

    # Test 5: bash_hook.py - Bash grep usage (should block)
    results.append(test_hook(
        hooks_dir / "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "grep 'pattern' file.txt"},
            "session_id": "test",
            "cwd": "/test"
        },
        "bash_hook.py - Block bash grep, suggest rg",
        expect_block=True
    ))

    # Test 6: pretask_subtask_flag.py - Task start (should allow + create flag)
    results.append(test_hook(
        hooks_dir / "pretask_subtask_flag.py",
        {
            "tool_name": "Task",
            "tool_input": {"prompt": "test task"},
            "session_id": "test",
            "cwd": "/test"
        },
        "pretask_subtask_flag.py - Create subagent flag",
        expect_block=False
    ))

    # Test 7: posttask_subtask_flag.py - Task end (should allow + remove flag)
    results.append(test_hook(
        hooks_dir / "posttask_subtask_flag.py",
        {
            "tool_name": "Task",
            "tool_input": {"prompt": "test task"},
            "session_id": "test",
            "cwd": "/test"
        },
        "posttask_subtask_flag.py - Remove subagent flag",
        expect_block=False
    ))

    # Test 8: format_python_hook.py - Non-Python file (should allow, no action)
    results.append(test_hook(
        hooks_dir / "format_python_hook.py",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "session_id": "test",
            "cwd": "/test"
        },
        "format_python_hook.py - Non-Python file",
        expect_block=False
    ))

    # Test 9: markdown_info_hook.py - Non-markdown file (should allow)
    results.append(test_hook(
        hooks_dir / "markdown_info_hook.py",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "session_id": "test",
            "cwd": "/test"
        },
        "markdown_info_hook.py - Non-markdown file",
        expect_block=False
    ))

    # Test 10: user_prompt_grep_reminder.py - User input (should allow)
    results.append(test_hook(
        hooks_dir / "user_prompt_grep_reminder.py",
        {
            "user_message": "search for something",
            "session_id": "test",
            "cwd": "/test"
        },
        "user_prompt_grep_reminder.py - User prompt",
        expect_block=False
    ))

    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Test Results{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    passed = sum(results)
    total = len(results)

    print(f"\nTotal: {total} tests")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {total - passed}{RESET}")

    if passed == total:
        print(f"\n{GREEN}✓ ALL TESTS PASSED{RESET}")
        print(f"{GREEN}All hooks are executable and functional in WSL runtime!{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED{RESET}")
        print(f"{YELLOW}Review errors above and check hook implementations{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate hook behavior with proper exit codes.
Run this to verify hooks are working as expected.
"""
import json
import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def test_hook(hook_script: str, test_data: dict, expected_exit_code: int, test_name: str):
    """Test a hook script with given input data."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Hook: {hook_script}")
    print(f"Expected exit code: {expected_exit_code}")

    hook_path = Path(__file__).parent / hook_script

    if not hook_path.exists():
        print(f"❌ SKIP: Hook script not found: {hook_path}")
        return False

    try:
        result = subprocess.run(
            ["python", str(hook_path)],
            input=json.dumps(test_data),
            capture_output=True,
            text=True,
            timeout=5
        )

        print(f"Actual exit code: {result.returncode}")

        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        if result.returncode == expected_exit_code:
            print(f"✅ PASS")
            return True
        else:
            print(f"❌ FAIL: Expected {expected_exit_code}, got {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ FAIL: Hook timed out")
        return False
    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")
        return False


def main():
    """Run all hook tests."""
    print("Hook Validation Test Suite")
    print("="*60)

    tests = []

    # Test 1: bash_hook.py - should allow safe command
    tests.append(test_hook(
        "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"}
        },
        0,
        "bash_hook.py: Allow safe command (ls)"
    ))

    # Test 2: bash_hook.py - should block git add with wildcard
    tests.append(test_hook(
        "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git add *.py"}
        },
        2,
        "bash_hook.py: Block git add with wildcard"
    ))

    # Test 3: bash_hook.py - should block grep usage
    tests.append(test_hook(
        "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "grep -r 'pattern' src/"}
        },
        2,
        "bash_hook.py: Block grep usage (suggest rg)"
    ))

    # Test 4: bash_hook.py - should allow git grep
    tests.append(test_hook(
        "bash_hook.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git grep 'pattern'"}
        },
        0,
        "bash_hook.py: Allow git grep"
    ))

    # Test 5: file_size_conditional_hook.py - should allow small file
    tests.append(test_hook(
        "file_size_conditional_hook.py",
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "bash_hook.py"}  # Small file
        },
        0,
        "file_size_conditional_hook.py: Allow small file"
    ))

    # Test 6: pretask_subtask_flag.py - should create flag
    tests.append(test_hook(
        "pretask_subtask_flag.py",
        {
            "tool_name": "Task",
            "tool_input": {}
        },
        0,
        "pretask_subtask_flag.py: Create subtask flag"
    ))

    # Test 7: posttask_subtask_flag.py - should remove flag
    tests.append(test_hook(
        "posttask_subtask_flag.py",
        {
            "tool_name": "Task",
            "tool_input": {}
        },
        0,
        "posttask_subtask_flag.py: Remove subtask flag"
    ))

    # Summary
    print(f"\n{'='*60}")
    print(f"Test Results: {sum(tests)}/{len(tests)} passed")

    if all(tests):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

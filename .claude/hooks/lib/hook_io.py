#!/usr/bin/env python3
"""
Standardized I/O utilities for Claude Code hooks.

Provides consistent JSON input/output handling with proper
error handling and graceful degradation.
"""

import json
import sys
from typing import Any


def read_hook_input() -> dict[str, Any]:
    """
    Read and parse JSON input from stdin.

    Returns:
        Parsed hook input data, or empty dict on error.

    Example input structure:
        {
            "tool_name": "Bash",
            "tool_input": {"command": "..."},
            "session_id": "...",
            "transcript_path": "..."
        }
    """
    try:
        if sys.stdin.isatty():
            return {}
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            return {}
        return json.loads(stdin_data)
    except json.JSONDecodeError as e:
        print(f"WARN: hook_io: Invalid JSON input: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"WARN: hook_io: Failed to read input: {e}", file=sys.stderr)
        return {}


def write_hook_output(data: dict[str, Any]) -> None:
    """
    Write JSON output to stdout.

    Args:
        data: Dictionary to output (typically {"decision": "...", "reason": "..."})
    """
    try:
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: hook_io: Failed to write output: {e}", file=sys.stderr)
        # Fallback to simple approve to avoid blocking
        print('{"decision": "approve"}')


def get_tool_name(data: dict[str, Any]) -> str:
    """Extract tool name from hook input."""
    return data.get("tool_name", "")


def get_tool_input(data: dict[str, Any]) -> dict[str, Any]:
    """Extract tool input from hook input."""
    return data.get("tool_input", {})


def get_file_path(data: dict[str, Any]) -> str | None:
    """Extract file path from tool input (for Edit/Write/Read tools)."""
    return data.get("tool_input", {}).get("file_path")


def get_command(data: dict[str, Any]) -> str:
    """Extract command from tool input (for Bash tool)."""
    return data.get("tool_input", {}).get("command", "")


def get_session_id(data: dict[str, Any]) -> str:
    """Extract session ID from hook input."""
    return data.get("session_id", "default")


def approve(reason: str | None = None) -> None:
    """Output approve decision and exit."""
    output = {"decision": "approve"}
    if reason:
        output["reason"] = reason
    write_hook_output(output)
    sys.exit(0)


def block(reason: str) -> None:
    """Output block decision and exit."""
    write_hook_output({"decision": "block", "reason": reason})
    sys.exit(2)


def warn(message: str) -> None:
    """Output warning to stderr and exit with code 1."""
    print(message, file=sys.stderr)
    sys.exit(1)

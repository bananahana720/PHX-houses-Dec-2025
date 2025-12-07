#!/usr/bin/env python3
"""
PreToolUse Hook: Auto-activate Python venv on Windows.

Intercepts Bash tool calls and prepends venv activation for Python commands.
Runs headlessly (no terminal window on Windows).
"""

import json
import os
import re
import sys
from pathlib import Path


def main():
    """Process Bash command and prepend venv activation if needed."""
    try:
        # Read JSON input from stdin
        stdin_data = ""
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read()

        if not stdin_data:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return 0

        try:
            event_data = json.loads(stdin_data)
        except json.JSONDecodeError:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return 0

        # Extract the command from tool_input
        command = event_data.get("tool_input", {}).get("command", "")

        if not command:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return 0

        # Check if command involves Python execution
        python_pattern = r'(^|\s|&&|;|\|)(python|python3|py|pip|pip3|pytest|poetry run)'
        if not re.search(python_pattern, command):
            # Not a Python command, allow without modification
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return 0

        # Determine project directory
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        project_path = Path(project_dir)

        # Check for venv existence (common names)
        venv_path = None
        for venv_name in ["venv", ".venv", "env", ".env", "virtualenv"]:
            candidate = project_path / venv_name
            # Windows uses Scripts directory
            if (candidate / "Scripts").is_dir():
                venv_path = candidate
                break

        # If no venv found, allow original command
        if not venv_path:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return 0

        # Construct activation command for Windows
        # Use the activate.bat or activate script
        activate_script = venv_path / "Scripts" / "activate"

        # For Git Bash compatibility, use source with Unix-style path
        venv_path_str = str(venv_path).replace("\\", "/")
        activation_cmd = f'source "{venv_path_str}/Scripts/activate"'

        # Prepend activation to original command
        modified_command = f"{activation_cmd} && {command}"

        # Return JSON with updated input
        response = {
            "hookSpecificOutput": {
                "permissionDecision": "allow",
                "updatedInput": {
                    "command": modified_command
                }
            },
            "suppressOutput": True
        }

        print(json.dumps(response, indent=2))
        return 0

    except Exception as e:
        # Graceful degradation - allow original command
        response = {
            "hookSpecificOutput": {
                "permissionDecision": "allow"
            },
            "error": str(e)
        }
        print(json.dumps(response))
        return 0


if __name__ == "__main__":
    sys.exit(main())

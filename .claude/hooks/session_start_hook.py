#!/usr/bin/env python3
"""
Session Start Hook - Injects orchestration protocol at session start.

Triggered by: SessionStart event
Purpose: Read and inject the claude-agent-orchestration-protocols.md into context
"""

import json
import sys
from pathlib import Path


def main():
    """Read orchestration protocol and inject at session start."""
    # Get project root (2 levels up from .claude/hooks/)
    hook_dir = Path(__file__).parent
    project_root = hook_dir.parent.parent

    protocol_file = project_root / "claude-agent-orchestration-protocols.md"

    if protocol_file.exists():
        try:
            protocol_content = protocol_file.read_text(encoding="utf-8")

            # Output JSON response with protocol content
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"""Called the Read tool with the following input: {{"file_path":"{protocol_file}"}}""",
                },
                "result": f"""Result of calling the Read tool: "{protocol_content.replace('"', '\\"').replace(chr(10), '\\n')[:8000]}" """
            }

            print(json.dumps(response, indent=2))

        except Exception as e:
            # Graceful degradation - don't block session
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"Note: Could not load orchestration protocol: {e}"
                }
            }
            print(json.dumps(response, indent=2))
    else:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "Note: claude-agent-orchestration-protocols.md not found in project root."
            }
        }
        print(json.dumps(response, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
UserPromptSubmit Hook - Orchestration Guidelines

Runs headlessly (no terminal window on Windows).

Purpose:
Inject orchestration principles at every prompt submission.
(precompact_hook.py handles /compact context optimization)

Source: claude-agent-orchestration-protocols.md
"""

import json
import sys


def get_orchestration_context() -> str:
    """Return standard orchestration guidelines."""
    return (
        "We are initiating a structured, multi-wave AI-agent orchestration workflow.\n"
        "Your responsibility: coordinate, delegate, and sequence agent waves.\n\n"
        "RULE:\n"
        "  → Delegate **all** non-trivial work to sub-agents. "
        "** This is a repo that abides by the BMAD principles and SDLC framework → Inform them to execute appropriate bmad custom slash commands when  applicable.**\n"
        "  → Only perform small tasks yourself (~1k–2k tokens max **with read operations considered**).\n"
        "  → For planning and architecture design tasks, instruct sub-agents to use mcp__context7__* mcp tools for up-to-date tech-reference documentation.\n\n"
    )


def main():
    """Process user prompt and inject orchestration context."""
    try:
        # Always return orchestration context
        # (precompact_hook.py handles /compact requests)
        context = get_orchestration_context()

        response = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context
            }
        }

        print(json.dumps(response, indent=2))
        return 0

    except Exception as e:
        # Graceful degradation - still provide basic context
        response = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": get_orchestration_context(),
                "error": str(e)
            }
        }
        print(json.dumps(response, indent=2))
        return 0


if __name__ == "__main__":
    sys.exit(main())

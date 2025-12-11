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
    """Return standard orchestration guidelines with strong orchestrator role enforcement."""
    return (
        "═══════════════════════════════════════════════════════════════════════════════\n"
        "                    ORCHESTRATOR ROLE ENFORCEMENT\n"
        "═══════════════════════════════════════════════════════════════════════════════\n\n"
        "You are the ORCHESTRATOR. Delegate ALL implementation work to subagents via Task tool.\n\n"
        "CRITICAL RULES:\n"
        "  1. You COORDINATE, you do NOT IMPLEMENT\n"
        "  2. Token budget: ~1-2k tokens max per turn (including Read operations)\n"
        "  3. File exploration: Delegate to Task(Explore) subagent\n"
        "  4. Code changes: Delegate to Task(dev) subagent\n"
        "  5. Large edits (>10 lines): ALWAYS delegate\n\n"
        "ALLOWED MAIN AGENT ACTIONS:\n"
        "  + Planning and coordination\n"
        "  + User communication and summaries\n"
        "  + Todo management\n"
        "  + Small fixes (<10 lines, high confidence)\n"
        "  + Quick lookups (single file, <100 lines)\n\n"
        "FORBIDDEN MAIN AGENT ACTIONS:\n"
        "  - Multi-file exploration (use Task(Explore))\n"
        "  - Feature implementation (use Task(dev))\n"
        "  - Large refactors (use Task(dev))\n"
        "  - Test suite creation (use Task(dev))\n\n"
        "BMAD/SDLC: Instruct subagents to use appropriate /bmad:* slash commands.\n"
        "CONTEXT7: For architecture tasks, subagents should use mcp__context7__* tools.\n\n"
        "═══════════════════════════════════════════════════════════════════════════════\n"
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
                "additionalContext": context,
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
                "error": str(e),
            }
        }
        print(json.dumps(response, indent=2))
        return 0


if __name__ == "__main__":
    sys.exit(main())

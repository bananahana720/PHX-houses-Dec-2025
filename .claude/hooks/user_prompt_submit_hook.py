#!/usr/bin/env python3
"""
UserPromptSubmit Hook - Orchestration Guidelines + PreCompact Context Optimization

Runs headlessly (no terminal window on Windows).

Purpose:
1. Inject orchestration principles at every prompt submission
2. Detect /compact commands and inject context optimization template

Source: claude-agent-orchestration-protocols.md
"""

import json
import sys


def get_precompact_context() -> str:
    """Return context optimization guidance for /compact commands."""
    return (
        "📦 **Context Optimization for Next Session**\n\n"
        "When compacting context, preserve these elements:\n\n"
        "## MUST RETAIN\n"
        "1. **Final Requirements & Decisions** - Approved specs, acceptance criteria, key decisions with rationale\n"
        "2. **Active Work State** - Current TodoWrite items, modified files, open blockers\n"
        "3. **Critical References** - File paths with line numbers, interface contracts, kill-switch thresholds\n"
        "4. **Session Learnings** - Novel discoveries, patterns found, risks identified\n\n"
        "## SUMMARIZE (reduce verbosity)\n"
        "- Exploration results → key findings only\n"
        "- Intermediate attempts → final working approach only\n"
        "- Verbose tool outputs → essential lines only\n\n"
        "## EXCLUDE ENTIRELY\n"
        "- Rejected approaches and dead ends\n"
        "- Obsolete error logs\n"
        "- Repetitive confirmations\n"
        "- Tool response boilerplate\n\n"
        "## ORCHESTRATION STATE (for multi-wave work)\n"
        "- Completed waves and outputs\n"
        "- Current wave and agent assignments\n"
        "- Pending waves and dependencies\n"
        "- Adaptation notes from previous waves\n\n"
        "## FORMAT TEMPLATE\n"
        "```yaml\n"
        "session_summary:\n"
        "  goal: [Current objective]\n"
        "  phase: [Discovery|Design|Implementation|Validation]\n\n"
        "active_work:\n"
        "  in_progress: [Current task with file:line refs]\n"
        "  pending: [Remaining tasks]\n"
        "  blockers: [Any blocking issues]\n\n"
        "key_decisions:\n"
        "  - decision: [What]\n"
        "    rationale: [Why]\n"
        "    files: [Affected]\n\n"
        "modified_files:\n"
        "  - path: [file path]\n"
        "    changes: [Brief description]\n"
        "```"
    )


def get_orchestration_context() -> str:
    """Return standard orchestration guidelines."""
    return (
        "We are initiating a structured, multi-wave AI-agent orchestration workflow.\n"
        "Your responsibility: coordinate, delegate, and sequence agent waves.\n\n"
        "RULE:\n"
        "  → Delegate **all** non-trivial work to sub-agents. "
        "**Inform them to execute appropriate bmad custom slash commands.**\n"
        "  → Only perform small tasks yourself (~1k–2k tokens max with read operations considered)."
    )


def main():
    """Process user prompt and inject appropriate context."""
    try:
        # Read stdin to get hook event data
        stdin_data = ""
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read()

        # Check if this is a /compact request
        is_compact = False
        if stdin_data:
            try:
                event_data = json.loads(stdin_data)
                user_prompt = event_data.get("user_prompt", "")
                if "/compact" in user_prompt.lower():
                    is_compact = True
            except json.JSONDecodeError:
                # If not JSON, check raw text
                if "/compact" in stdin_data.lower():
                    is_compact = True

        # Select appropriate context
        context = get_precompact_context() if is_compact else get_orchestration_context()

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

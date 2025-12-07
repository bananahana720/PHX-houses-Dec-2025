#!/usr/bin/env python3
"""
PreCompact Hook - Optimizes context carried over to Claude in the next session.

Triggered by: Stop event (when /compact is invoked)
Purpose: Generate optimized context summary for session continuation.

This hook detects when /compact is being used and generates a structured
context preservation format that retains critical information while
removing noise.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_compact_template() -> str:
    """Generate the context optimization template."""
    return """
📦 **Context Optimization for Next Session**

When compacting context for the next session, preserve these elements:

## MUST RETAIN
1. **Final Requirements & Decisions**
   - Approved specifications and acceptance criteria
   - Key decisions made with rationale

2. **Active Work State**
   - Current TodoWrite items (in_progress, pending)
   - Files modified in this session
   - Open blockers or questions

3. **Critical References**
   - File paths with line numbers for key code
   - Interface contracts and API shapes
   - Kill-switch thresholds and scoring weights (if modified)

4. **Session Learnings**
   - Novel discoveries that changed the plan
   - Patterns found in codebase
   - Risks identified

## SUMMARIZE (reduce verbosity)
1. Exploration results → key findings only
2. Intermediate attempts → final working approach only
3. Verbose tool outputs → essential lines only
4. Conversation flow → decisions and outcomes

## EXCLUDE ENTIRELY
1. Rejected approaches and dead ends
2. Obsolete error logs
3. Repetitive confirmations
4. Tool response boilerplate
5. Intermediate file reads (keep only final state)

## ORCHESTRATION STATE
For multi-wave work, preserve:
- Completed waves and their outputs
- Current wave and agent assignments
- Pending waves and their dependencies
- Adaptation notes from previous waves

## FORMAT TEMPLATE
```yaml
session_summary:
  goal: [Current objective]
  phase: [Discovery|Design|Implementation|Validation]

active_work:
  in_progress: [Current task with file:line refs]
  pending: [Remaining tasks]
  blockers: [Any blocking issues]

key_decisions:
  - decision: [What was decided]
    rationale: [Why]
    files: [Affected files]

modified_files:
  - path: [file path]
    changes: [Brief description]

risks_and_followups:
  - [Risk or follow-up item]
```
"""


def main():
    """Output precompact optimization guidance."""
    try:
        # Read stdin to get hook event data (if any)
        stdin_data = ""
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read()

        # Parse event data if present
        is_compact_request = False
        if stdin_data:
            try:
                event_data = json.loads(stdin_data)
                # Check if this is a /compact command
                user_prompt = event_data.get("user_prompt", "")
                if "/compact" in user_prompt.lower():
                    is_compact_request = True
            except json.JSONDecodeError:
                pass

        # Generate response
        template = generate_compact_template()

        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreCompact",
                "additionalContext": template if is_compact_request else "",
                "timestamp": datetime.now().isoformat(),
            }
        }

        # Only output if this is a compact request or always provide minimal output
        if is_compact_request:
            print(json.dumps(response, indent=2))
        else:
            # Silent for non-compact scenarios
            print(json.dumps({"decision": "continue"}))

        return 0

    except Exception as e:
        # Graceful degradation
        error_response = {
            "decision": "continue",
            "error": str(e)
        }
        print(json.dumps(error_response))
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Stop hook: Evaluate session context hygiene before exit.

Command-based hook that checks:
1. Which directories had files modified (from session-delta.log)
2. Whether those directories have CLAUDE.md files
3. Whether CLAUDE.md files are stale

Reads JSON input from stdin with hook event data including transcript_path.
Detects agent sessions (agent-*.jsonl) vs main sessions (UUID.jsonl).
Only blocks main sessions; agent sessions auto-approve.

Returns JSON with decision and systemMessage.

Exit codes:
- 0: Hygiene check complete (decision in stdout)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import shared utilities
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.claude_md_utils import check_claude_md_exists, is_stale
    from lib.delta_logger import get_modified_directories, get_directories_without_claude_md

    LIB_AVAILABLE = True
except ImportError as e:
    LIB_AVAILABLE = False
    IMPORT_ERROR = str(e)


def is_agent_session(transcript_path: str | None) -> bool:
    """
    Detect if this is an agent/subagent session based on transcript filename.

    Agent sessions: agent-*.jsonl (e.g., agent-e8765739.jsonl)
    Main sessions: UUID.jsonl (e.g., efd54b1a-d40f-4583-9e0f-a64c78188aff.jsonl)

    Args:
        transcript_path: Path to the transcript file from hook input

    Returns:
        True if agent session, False if main session or unknown
    """
    if not transcript_path:
        return False

    filename = Path(transcript_path).name

    # Agent session pattern: agent-<hex>.jsonl
    if filename.startswith("agent-"):
        return True

    return False


def evaluate_hygiene(is_agent: bool = False) -> dict[str, str]:
    """
    Evaluate session context hygiene.

    For agent sessions: Always approve (agents shouldn't manage CLAUDE.md).
    For main sessions: Block if directories have missing/stale CLAUDE.md.

    Args:
        is_agent: True if this is a subagent session, False for main session

    Returns:
        dict with 'decision' ('approve' or 'block') and 'reason' per Claude Code Stop hook spec
    """
    # Agent sessions auto-approve - they shouldn't manage CLAUDE.md files
    if is_agent:
        return {
            "decision": "approve",
            "reason": "Agent session - CLAUDE.md management delegated to main session."
        }

    if not LIB_AVAILABLE:
        print(f"WARN: stop_hygiene_hook: hygiene check skipped (lib unavailable: {IMPORT_ERROR})", file=sys.stderr)
        return {
            "decision": "approve",
            "reason": "Context hygiene check skipped (lib not available)."
        }

    # Get directories that had modifications
    modified_dirs = get_modified_directories()

    if not modified_dirs:
        return {
            "decision": "approve",
            "reason": "No files modified this session. Safe to exit."
        }

    # Filter out noise directories
    excluded = {".claude/audio", ".claude/logs", "node_modules", "__pycache__", ".git", ".venv", "venv"}

    def should_exclude(d: str) -> bool:
        """Check if directory should be excluded from hygiene check."""
        # Standard exclusions
        if any(ex in d for ex in excluded):
            return True
        # Exclude Claude session files in ~/.claude/projects/ (agent-*, transcript files)
        if "/.claude/projects/" in d or "\\.claude\\projects\\" in d:
            # Check if it's an agent session directory
            path_parts = Path(d).parts
            for part in path_parts:
                if part.startswith("agent-"):
                    return True
        return False

    relevant_dirs = sorted([d for d in modified_dirs if not should_exclude(d)])

    if not relevant_dirs:
        return {
            "decision": "approve",
            "reason": "Only non-code directories modified. Safe to exit."
        }

    # Check which directories lack CLAUDE.md
    dirs_without_claude_md = get_directories_without_claude_md()
    missing_claude_md = [d for d in dirs_without_claude_md if d in relevant_dirs]

    # Check for stale CLAUDE.md files (>24h)
    stale_dirs = []
    for dir_path in relevant_dirs:
        claude_md = Path(dir_path) / "CLAUDE.md"
        if claude_md.exists() and is_stale(claude_md, threshold_hours=24):
            stale_dirs.append(dir_path)

    # Build directory list for message
    dir_list = "\n".join(f"  - {d}" for d in relevant_dirs[:10])
    if len(relevant_dirs) > 10:
        dir_list += f"\n  ... and {len(relevant_dirs) - 10} more"

    # Build issues summary
    issues = []
    if missing_claude_md:
        issues.append(f"{len(missing_claude_md)} missing CLAUDE.md")
    if stale_dirs:
        issues.append(f"{len(stale_dirs)} stale CLAUDE.md (>24h)")

    issues_text = f" Issues: {', '.join(issues)}." if issues else ""

    # Only block if there are actual issues (missing or stale CLAUDE.md)
    # Otherwise just approve with informational message to avoid infinite loops
    if issues:
        return {
            "decision": "block",
            "reason": (
                f"Session modified {len(relevant_dirs)} directories:{issues_text}\n{dir_list}\n\n"
                "Spawn Task(model=haiku) subagent(s) to assess changes and update CLAUDE.md files "
                "using the '.claude/templates/CLAUDE.md.template' template."
            )
        }
    else:
        # All directories have up-to-date CLAUDE.md - approve
        return {
            "decision": "approve",
            "reason": f"Session modified {len(relevant_dirs)} directories."
        }


def main():
    """Main entry point."""
    # Read hook event data from stdin
    transcript_path = None
    try:
        stdin_data = sys.stdin.read()
        if stdin_data.strip():
            hook_input = json.loads(stdin_data)
            transcript_path = hook_input.get("transcript_path")
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARN: stop_hygiene_hook: failed to parse stdin: {e}", file=sys.stderr)

    # Detect if this is an agent session
    is_agent = is_agent_session(transcript_path)

    result = evaluate_hygiene(is_agent=is_agent)

    # Output JSON for Claude Code to parse
    print(json.dumps(result))

    # Always exit 0 - the decision is in the JSON output
    sys.exit(0)


if __name__ == "__main__":
    main()

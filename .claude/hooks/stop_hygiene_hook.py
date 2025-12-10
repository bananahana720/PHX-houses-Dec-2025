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
from pathlib import Path

# Import shared utilities
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.claude_md_utils import check_claude_md_exists, is_stale
    from lib.delta_logger import get_directories_without_claude_md, get_modified_directories
    from lib.exclusions import should_exclude_directory

    LIB_AVAILABLE = True
except ImportError as e:
    LIB_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Configuration
CONFIG = {
    "oversized_threshold_lines": 100,
    "stale_threshold_hours": 24,
    "display_limit": 5,
}


def _load_prompt_template() -> str:
    """Load hygiene prompt from external template."""
    template_path = Path(__file__).parent.parent / "templates" / "hygiene-prompt.md"
    if template_path.exists():
        try:
            return template_path.read_text(encoding="utf-8")
        except OSError:
            pass
    # Fallback: minimal directive
    return """
**Action Required:** **UTILIZE TASK() TOOL AND SUBAGENT TASK BUCKETING-DELEGATION** to Update CLAUDE.md files for directories listed above.
Use `.claude/templates/CLAUDE.md.template` for format guidance.
Ensure: ≤100 lines, frontmatter with `last_updated`, bullets/tables only.
"""


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

    # Filter out noise directories using shared exclusions module
    relevant_dirs = sorted([d for d in modified_dirs if not should_exclude_directory(d)])

    if not relevant_dirs:
        # Show which non-code dirs were modified for transparency
        excluded_list = "\n".join(f"  - {d}" for d in sorted(modified_dirs)[:5])
        if len(modified_dirs) > 5:
            excluded_list += f"\n  ... and {len(modified_dirs) - 5} more"
        return {
            "decision": "approve",
            "reason": f"Only non-code directories modified ({len(modified_dirs)} total). Safe to exit.\n\n**Modified (excluded):**\n{excluded_list}"
        }

    # Check which directories lack CLAUDE.md
    dirs_without_claude_md = get_directories_without_claude_md()
    missing_claude_md = [d for d in dirs_without_claude_md if d in relevant_dirs]

    # Check for stale CLAUDE.md files (using configured threshold)
    stale_dirs: list[str] = []
    for dir_path in relevant_dirs:
        claude_md = Path(dir_path) / "CLAUDE.md"
        if claude_md.exists() and is_stale(claude_md, threshold_hours=CONFIG["stale_threshold_hours"]):
            stale_dirs.append(dir_path)

    # Check for oversized CLAUDE.md files - need distillation
    oversized_dirs: list[tuple[str, int]] = []
    oversized_threshold = CONFIG["oversized_threshold_lines"]
    for dir_path in relevant_dirs:
        claude_md = Path(dir_path) / "CLAUDE.md"
        if claude_md.exists():
            try:
                line_count = sum(1 for _ in claude_md.open(encoding="utf-8"))
                if line_count > oversized_threshold:
                    oversized_dirs.append((dir_path, line_count))
            except OSError:
                pass

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
    if oversized_dirs:
        issues.append(f"{len(oversized_dirs)} oversized CLAUDE.md (>{oversized_threshold} lines)")

    issues_text = f" Issues: {', '.join(issues)}." if issues else ""

    # Only block if there are actual issues (missing or stale CLAUDE.md)
    # Otherwise just approve with informational message to avoid infinite loops
    if issues:
        # Build detailed lists for each issue type
        missing_list = ""
        if missing_claude_md:
            missing_list = "\n**MISSING** (create new):\n" + "\n".join(f"  - `{d}`" for d in missing_claude_md[:5])
            if len(missing_claude_md) > 5:
                missing_list += f"\n  ... +{len(missing_claude_md) - 5} more"

        stale_list = ""
        if stale_dirs:
            stale_list = "\n**STALE** (>24h, refresh):\n" + "\n".join(f"  - `{d}`" for d in stale_dirs[:5])
            if len(stale_dirs) > 5:
                stale_list += f"\n  ... +{len(stale_dirs) - 5} more"

        oversized_list = ""
        if oversized_dirs:
            oversized_list = "\n**OVERSIZED** (>100 lines, distill):\n" + "\n".join(
                f"  - `{d}` ({lines} lines)" for d, lines in oversized_dirs[:5]
            )
            if len(oversized_dirs) > 5:
                oversized_list += f"\n  ... +{len(oversized_dirs) - 5} more"

        # Build directory lists for template
        all_dirs_to_process: list[str] = missing_claude_md + stale_dirs + [d for d, _ in oversized_dirs]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_dirs: list[str] = []
        for d in all_dirs_to_process:
            if d not in seen:
                seen.add(d)
                unique_dirs.append(d)

        directories_text = "\n".join(f"- {d}" for d in unique_dirs) if unique_dirs else "(none)"

        # Standard file extensions for code analysis
        file_extensions_text = ".py, .ts, .tsx, .js, .jsx, .md, .json, .yaml, .yml, .toml"

        # Load action directive from external template (P0 fix: ~3500 tokens saved)
        action_directive = _load_prompt_template().format(
            directories=directories_text,
            file_extensions=file_extensions_text,
        )

        return {
            "decision": "block",
            "reason": (
                f"Session modified {len(relevant_dirs)} directories.{issues_text}"
                f"{missing_list}{stale_list}{oversized_list}\n\n"
                f"{action_directive}"
            )
        }
    else:
        # All directories have up-to-date CLAUDE.md - approve
        # Include directory list so Claude can track what was touched
        return {
            "decision": "approve",
            "reason": f"Session modified {len(relevant_dirs)} directories. All CLAUDE.md files are current.\n\n**Modified directories:**\n{dir_list}"
        }


def main() -> None:
    """Main entry point."""
    # Read hook event data from stdin
    transcript_path = None
    session_id = None
    tool_name = None
    stop_hook_active = False
    try:
        stdin_data = sys.stdin.read()
        if stdin_data.strip():
            hook_input = json.loads(stdin_data)
            transcript_path = hook_input.get("transcript_path")
            session_id = hook_input.get("session_id")
            tool_name = hook_input.get("hook_event_name")
            stop_hook_active = hook_input.get("stop_hook_active", False)
            # Debug: log what we received
            print(f"DEBUG stop_hygiene_hook: transcript_path={transcript_path}, session_id={session_id}, tool_name={tool_name}, stop_hook_active={stop_hook_active}", file=sys.stderr)
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARN: stop_hygiene_hook: failed to parse stdin: {e}", file=sys.stderr)

    # Prevent infinite loops: if we're already continuing from a stop hook, approve immediately
    if stop_hook_active:
        print(json.dumps({
            "decision": "approve",
            "reason": "Stop hook already active - approving to prevent infinite loop."
        }))
        sys.exit(0)

    # Detect if this is an agent session by checking tool_name
    is_agent = tool_name == "SubagentStop"

    result = evaluate_hygiene(is_agent=is_agent)

    # Output JSON for Claude Code to parse
    print(json.dumps(result))

    # Always exit 0 - the decision is in the JSON output
    sys.exit(0)


if __name__ == "__main__":
    main()

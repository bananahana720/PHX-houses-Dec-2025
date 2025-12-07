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

    # Filter out noise directories - these don't need CLAUDE.md tracking
    # Categories: caches, generated output, personal config, transient state
    excluded = {
        # Caches (binary/generated, no context value)
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".pip-audit-cache",
        "node_modules",
        # Build artifacts (generated)
        "dist",
        "build",
        ".egg-info",
        "htmlcov",
        # Virtual environments
        ".venv",
        "venv",
        "env",
        # Git internals
        ".git",
        # Claude Code session data (personal, transient)
        ".claude/audio",
        ".claude/logs",
        # Personal config (API keys, preferences)
        ".agentvibes",
        ".playwright-mcp",
        # Data caches and archives (stale, redundant)
        "data/api_cache",
        "data/archive",
        "api_cache",
        # Project trash/archive (explicitly unwanted)
        "TRASH",
        "archive",
        # Generated reports (output, not source)
        "reports",
    }

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

    # Check for stale CLAUDE.md files (>24h)
    stale_dirs: list[str] = []
    for dir_path in relevant_dirs:
        claude_md = Path(dir_path) / "CLAUDE.md"
        if claude_md.exists() and is_stale(claude_md, threshold_hours=24):
            stale_dirs.append(dir_path)

    # Check for oversized CLAUDE.md files (>100 lines) - need distillation
    oversized_dirs: list[tuple[str, int]] = []
    OVERSIZED_THRESHOLD = 100
    for dir_path in relevant_dirs:
        claude_md = Path(dir_path) / "CLAUDE.md"
        if claude_md.exists():
            try:
                line_count = sum(1 for _ in claude_md.open(encoding="utf-8"))
                if line_count > OVERSIZED_THRESHOLD:
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
        issues.append(f"{len(oversized_dirs)} oversized CLAUDE.md (>{OVERSIZED_THRESHOLD} lines)")

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

        # Model type for CLAUDE.md generation
        model_type_text = "haiku"

        # Build explicit Haiku instructions
        haiku_instructions = f"""
            You are an AI orchestrator responsible for coordinating the creation and maintenance of CLAUDE.md documentation files across a codebase. You will simulate multiple sub-agents, each processing one directory to create or update its CLAUDE.md file.

            Here are the directories you need to process:

            <directories_to_process>
            {directories_text}
            </directories_to_process>

            Here are the file extensions to analyze in each directory:

            <file_extensions>
            {file_extensions_text}
            </file_extensions>

            Here is the model type being used:

            <model_type>
            {model_type_text}
            </model_type>

            ## Your Task

            You will coordinate multiple sub-agents to process each directory listed above. Follow these rules:
            - Assign exactly ONE agent to each directory (create a 1:1 mapping)
            - Batch agents into groups of 5 for resource efficiency
            - Process batches sequentially

            ## Agent Instructions

            Each agent you simulate will follow this workflow:

            **Step 1: Select Template**
            - For project root directories: read `claude.md.project-root.template`
            - For sub-directories: read `.claude/templates/CLAUDE.md.template`

            **Step 2: Analyze Directory**
            - Glob all files matching the specified file extensions
            - Read 2-3 representative files to understand the directory's purpose
            - Identify how this directory fits into the larger codebase

            **Step 3: Generate CLAUDE.md**

            Create a CLAUDE.md file with these sections:

            - **Frontmatter**: Include `last_updated` timestamp and `updated_by: agent`
            - **Purpose**: 1-2 sentences maximum describing the directory's function
            - **Contents Table**: List up to 10 key files only
            - **Common Commands**: Relevant bash commands for this directory
            - **Core Files**: Important files and utility functions
            - **Code Style**: Guidelines specific to this directory
            - **Testing**: How to run tests for code in this directory
            - **Repository Etiquette**: Branch naming conventions, merge vs. rebase preferences
            - **Warnings**: Unexpected behaviors or gotchas
            - **Critical Context**: Other important information

            **Formatting Rules:**
            - Use bullets and tables ONLY (no prose paragraphs)
            - Keep information concise and scannable
            - Focus on high-signal, non-obvious information
            - Eliminate redundancy and obvious details

            **Step 4: Validate**

            Check that the CLAUDE.md meets ALL criteria:
            - ≤100 lines total
            - Frontmatter includes `last_updated` and `updated_by: agent`
            - Purpose is 1-2 sentences maximum
            - Contents table lists ≤10 key files
            - Uses only bullets and tables (no prose paragraphs)

            **Step 5: Distill if Necessary**

            If the file exceeds 100 lines:
            - Reduce to 50-80 lines
            - Keep only the highest-signal content
            - Merge similar items
            - Remove obvious or redundant information
            - Preserve: non-obvious details, error-prevention info, time-saving tips

            ## Your Process

            Work through this task inside a thinking block with two subsections:

            **In `<planning>` tags:**
            1. List every directory from the input explicitly
            2. Assign exactly one agent to each directory
            3. Group agents into batches of 5
            4. Define the execution order

            It's OK for this section to be quite long if there are many directories.

            **In `<execution_log>` tags:**
            For each agent, document the following in detail:
            - Which directory it's processing
            - Which template it used
            - List the specific files it globbed (not just the count)
            - List the 2-3 representative files it selected to read
            - Quote key code patterns, imports, or structural elements observed in those files
            - Based on those observations, state the directory's purpose (1-2 sentences)
            - Count the total lines in the generated CLAUDE.md explicitly
            - Validate each criterion individually:
            * Check: Is it ≤100 lines? (state the actual line count)
            * Check: Does frontmatter include `last_updated` and `updated_by: agent`?
            * Check: Is Purpose 1-2 sentences maximum?
            * Check: Does Contents table list ≤10 key files?
            * Check: Uses only bullets and tables (no prose paragraphs)?
            * Check: Is content concise with no redundancy and only high-signal information?
            - Overall validation result: PASSED or FAILED (with specific failures noted)
            - If distillation was needed: list what specific content was removed/merged, and state the final line count

            It's OK for this section to be quite long since you're processing multiple directories with detailed validation steps.

            The execution log ensures thoroughness but will not appear in your final output.

            **After your thinking block**, provide a summary in `<summary>` tags with:
            - Total directories processed
            - Number of files created vs. updated
            - List of directories that required distillation (if any)
            - Any issues encountered and their resolutions

            ## Output Example

            Your final output structure should look like this:

            <summary>
            Processed 8 directories total
            - Created: 5 new CLAUDE.md files
            - Updated: 3 existing CLAUDE.md files
            - Distilled: 1 file (/src/legacy - reduced from 127 lines to 68 lines)
            - All files validated successfully
            - No issues encountered
            </summary>

            Your final output should contain ONLY the summary in the format shown above. Do not duplicate or repeat any of the planning or execution log details that you worked through in your thinking block."""

        return {
            "decision": "block",
            "reason": (
                f"Session modified {len(relevant_dirs)} directories.{issues_text}"
                f"{missing_list}{stale_list}{oversized_list}"
                f"{haiku_instructions}"
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

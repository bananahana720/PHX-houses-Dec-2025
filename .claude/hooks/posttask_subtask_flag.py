#!/usr/bin/env python3
"""
PostToolUse hook for Task tool: Subtask cleanup and learnings capture.

Performs two functions:
1. Removes subtask flag file after Task completes
2. Captures subagent learnings to session-learnings.json

The learnings capture extracts patterns from task output:
- Error patterns discovered
- File references created
- Anti-patterns identified
- New tool usage patterns

Exit codes:
- 0: Always (cleanup is non-blocking)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Subtask flag file
FLAG_FILE = ".claude_in_subtask.flag"

# Session learnings log location
LEARNINGS_LOG = ".claude/session-learnings.json"


def _get_project_root() -> Path:
    """Get project root by looking for .claude directory or .git."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _extract_file_references(text: str) -> list[str]:
    """Extract file path references from text."""
    # Common file path patterns
    patterns = [
        r"(?:^|\s)([A-Za-z]:[/\\][\w./\\-]+\.\w+)",  # Windows paths
        r"(?:^|\s)(/[\w./\\-]+\.\w+)",  # Unix paths
        r"(?:^|\s)(\.?\.?/[\w./\\-]+\.\w+)",  # Relative paths
    ]

    refs = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        refs.update(matches)

    return list(refs)[:20]  # Limit to 20 references


def _extract_error_patterns(text: str) -> list[str]:
    """Extract error patterns from text."""
    patterns = []

    # Common error indicators
    error_markers = [
        r"(?:Error|Exception|Failed|Failure):\s*(.+?)(?:\n|$)",
        r"(?:TypeError|ValueError|KeyError|AttributeError):\s*(.+?)(?:\n|$)",
        r"(?:BLOCKED|FAILED|CRITICAL):\s*(.+?)(?:\n|$)",
    ]

    for marker in error_markers:
        matches = re.findall(marker, text, re.IGNORECASE)
        patterns.extend(matches[:5])  # Limit per pattern

    return patterns[:10]  # Total limit


def _extract_learnings(text: str) -> list[str]:
    """Extract learning patterns from text."""
    learnings = []

    # Look for explicit learning markers
    learning_markers = [
        r"(?:Learned|Discovery|Pattern|Insight|Found):\s*(.+?)(?:\n|$)",
        r"(?:Note|Important|Remember):\s*(.+?)(?:\n|$)",
        r"(?:Best practice|Anti-pattern):\s*(.+?)(?:\n|$)",
    ]

    for marker in learning_markers:
        matches = re.findall(marker, text, re.IGNORECASE)
        learnings.extend(matches[:3])

    return learnings[:10]


def _save_learnings(learnings_data: dict) -> bool:
    """Append learnings to session-learnings.json."""
    try:
        log_path = _get_project_root() / LEARNINGS_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing learnings or create new
        existing = []
        if log_path.exists():
            try:
                with open(log_path, encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, Exception):
                existing = []

        # Append new learnings
        existing.append(learnings_data)

        # Write back
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        return True
    except Exception:
        return False


def capture_learnings(data: dict) -> None:
    """
    Capture learnings from task output.

    Args:
        data: The hook input data containing task output
    """
    try:
        # Get task output/result if available
        task_output = data.get("tool_output", "")
        task_input = data.get("tool_input", {})

        # Also check for result in different locations
        if not task_output:
            task_output = str(task_input.get("prompt", ""))

        if not task_output:
            return

        # Truncate very large outputs
        if len(task_output) > 10240:
            task_output = task_output[:10240] + "\n[TRUNCATED]"

        # Extract patterns
        file_refs = _extract_file_references(task_output)
        error_patterns = _extract_error_patterns(task_output)
        learnings = _extract_learnings(task_output)

        # Only save if we found something interesting
        if file_refs or error_patterns or learnings:
            learnings_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "subagent_type": task_input.get("subagent_type", "unknown"),
                "file_references": file_refs,
                "error_patterns": error_patterns,
                "learnings": learnings,
            }
            _save_learnings(learnings_data)

    except Exception as e:
        # Non-critical - don't fail the hook
        print(f"DEBUG: Learnings capture failed: {e}", file=sys.stderr)


# Load input from stdin
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    data = {}

# ============================================================================
# STEP 1: Remove subtask flag file
# ============================================================================
try:
    if os.path.exists(FLAG_FILE):
        os.remove(FLAG_FILE)
except Exception as e:
    print(f"Warning: Could not remove subtask flag: {e}", file=sys.stderr)

# ============================================================================
# STEP 2: Capture learnings from task output
# ============================================================================
capture_learnings(data)

# Always allow
sys.exit(0)

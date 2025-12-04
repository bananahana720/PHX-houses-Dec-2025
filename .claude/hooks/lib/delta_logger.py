#!/usr/bin/env python3
"""
Async session delta logging for context management hooks.

Tracks file changes (Edit/Write operations) to a session log file
for wrap-up context and CLAUDE.md update reminders.

Log format: JSON lines (one JSON object per line)
{
    "timestamp": "2025-12-03T10:30:00Z",
    "file_path": "src/main.py",
    "change_type": "modify",
    "line_delta": 15,
    "has_claude_md": true
}
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

# Session delta log location (relative to project root)
SESSION_DELTA_LOG = ".claude/session-delta.log"

# Lock for thread-safe log writes
_log_lock = threading.Lock()


def _get_project_root() -> Path:
    """Get project root by looking for .claude directory or .git."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _get_log_path() -> Path:
    """Get the full path to the session delta log."""
    return _get_project_root() / SESSION_DELTA_LOG


def check_directory_has_claude_md(file_path: str | Path) -> bool:
    """
    Check if the directory containing a file has a CLAUDE.md.

    Args:
        file_path: Path to the file being modified

    Returns:
        True if directory has CLAUDE.md, False otherwise
    """
    try:
        dir_path = Path(file_path).parent
        claude_md = dir_path / "CLAUDE.md"
        return claude_md.exists()
    except Exception:
        return False


def _count_file_lines(file_path: str | Path) -> int | None:
    """Count lines in a file."""
    try:
        with open(file_path, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return None


def _write_log_entry(entry: dict, debug: bool = False) -> bool:
    """
    Write a log entry to the session delta log.

    Thread-safe append operation.

    Args:
        entry: Dictionary to write as JSON
        debug: If True, print errors to stderr

    Returns:
        True if write succeeded, False otherwise
    """
    import sys

    try:
        log_path = _get_log_path()

        if debug:
            print(f"DEBUG: delta_logger: writing to {log_path}", file=sys.stderr)

        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with _log_lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

        return True
    except Exception as e:
        if debug:
            print(f"ERROR: delta_logger._write_log_entry: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def _should_skip_logging(file_path: str | Path) -> bool:
    """
    Check if file should be skipped from delta logging.

    Skips agent session directories and other noise.
    """
    path_str = str(file_path)

    # Skip agent session directories (subagent transcripts)
    if "/.claude/projects/" in path_str or "\\.claude\\projects\\" in path_str:
        return True
    if "/agent-" in path_str or "\\agent-" in path_str:
        return True

    # Skip noise directories - these don't need delta tracking
    # Categories: caches, generated output, personal config, transient state
    skip_patterns = [
        # Caches (binary/generated, no context value)
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".pip-audit-cache",
        "node_modules",
        # Build artifacts (generated)
        "dist/",
        "build/",
        ".egg-info",
        "htmlcov/",
        # Virtual environments
        ".venv/",
        "venv/",
        "env/",
        # Git internals
        ".git/",
        # Claude Code session data (personal, transient)
        ".claude/audio",
        ".claude/logs",
        # Personal config (API keys, preferences)
        ".agentvibes/",
        ".playwright-mcp/",
        # Data caches and archives (stale, redundant)
        "data/api_cache",
        "data/archive",
        "api_cache/",
        # Project trash/archive (explicitly unwanted)
        "TRASH/",
        "archive/",
        # Generated reports (output, not source)
        "reports/",
    ]
    return any(pat in path_str for pat in skip_patterns)


def log_delta(
    file_path: str,
    change_type: str,
    line_delta: int | None = None,
    previous_line_count: int | None = None,
    debug: bool = False,
) -> bool:
    """
    Log a file change to the session delta log (synchronous).

    Args:
        file_path: Path to the modified file
        change_type: Type of change ("create", "modify", "delete")
        line_delta: Change in line count (optional)
        previous_line_count: Line count before change (for delta calculation)
        debug: If True, print errors to stderr

    Returns:
        True if logging succeeded, False otherwise
    """
    import os
    import sys

    # Enable debug via environment variable
    debug = debug or os.environ.get("CLAUDE_DELTA_DEBUG", "").lower() in ("1", "true")

    # Skip agent session directories and other noise
    if _should_skip_logging(file_path):
        if debug:
            print(f"DEBUG: delta_logger: skipping {file_path} (filtered)", file=sys.stderr)
        return True

    try:
        path = Path(file_path)

        # Calculate line delta if not provided
        if line_delta is None and previous_line_count is not None:
            current_lines = _count_file_lines(path)
            if current_lines is not None:
                line_delta = current_lines - previous_line_count

        # Build log entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_path": str(path),
            "change_type": change_type,
            "line_delta": line_delta,
            "has_claude_md": check_directory_has_claude_md(path),
            "directory": str(path.parent),
        }

        return _write_log_entry(entry, debug=debug)
    except Exception as e:
        if debug:
            print(f"ERROR: delta_logger.log_delta: {type(e).__name__}: {e}", file=sys.stderr)
        return False


def log_delta_async(
    file_path: str,
    change_type: str,
    line_delta: int | None = None,
) -> threading.Thread:
    """
    Log a file change asynchronously (non-blocking).

    Spawns a daemon thread to write the log entry.

    Args:
        file_path: Path to the modified file
        change_type: Type of change ("create", "modify", "delete")
        line_delta: Change in line count (optional)

    Returns:
        The spawned thread (for testing/joining if needed)
    """
    thread = threading.Thread(
        target=log_delta,
        args=(file_path, change_type, line_delta),
        daemon=True,
    )
    thread.start()
    return thread


def get_session_deltas() -> list[dict]:
    """
    Read all deltas from the current session log.

    Returns:
        List of delta entries as dictionaries
    """
    try:
        log_path = _get_log_path()
        if not log_path.exists():
            return []

        entries = []
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return entries
    except Exception:
        return []


def get_directories_without_claude_md() -> set[str]:
    """
    Get directories from session that don't have CLAUDE.md.

    Useful for session wrap-up reminders.

    Returns:
        Set of directory paths that had changes but no CLAUDE.md
    """
    deltas = get_session_deltas()
    return {d["directory"] for d in deltas if not d.get("has_claude_md", True)}


def get_modified_directories() -> set[str]:
    """
    Get all directories that had file modifications this session.

    Returns:
        Set of directory paths with changes
    """
    deltas = get_session_deltas()
    return {d["directory"] for d in deltas}


def clear_session_log() -> bool:
    """
    Clear the session delta log (typically on SessionStart).

    Returns:
        True if cleared successfully, False otherwise
    """
    try:
        log_path = _get_log_path()
        if log_path.exists():
            log_path.unlink()
        return True
    except Exception:
        return False


def archive_session_log(archive_dir: str | Path | None = None) -> str | None:
    """
    Archive the current session log with timestamp.

    Args:
        archive_dir: Directory for archives (default: .claude/logs/)

    Returns:
        Path to archived file, or None if archive failed
    """
    try:
        log_path = _get_log_path()
        if not log_path.exists():
            return None

        # Default archive directory
        if archive_dir is None:
            archive_dir = _get_project_root() / ".claude" / "logs"

        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)

        # Create timestamped archive name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = archive_path / f"session-delta-{timestamp}.log"

        # Move current log to archive
        log_path.rename(archive_file)

        return str(archive_file)
    except Exception:
        return None

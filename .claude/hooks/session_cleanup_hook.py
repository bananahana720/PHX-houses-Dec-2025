#!/usr/bin/env python3
"""
SessionEnd hook: Cleanup session artifacts.

Performs cleanup tasks when a Claude Code session ends:
1. Archive session-delta.log to .claude/logs/
2. Clean up stale .claude_*.flag files
3. Rotate logs if they exceed size threshold

Exit codes:
- 0: Always (cleanup is non-blocking)
"""

import glob
import os
import sys
from pathlib import Path

# Import shared utilities
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.delta_logger import archive_session_log, clear_session_log

    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False

# Configuration
MAX_LOG_SIZE_MB = 1
FLAG_PATTERN = ".claude_*.flag"
LOGS_DIR = ".claude/logs"


def _get_project_root() -> Path:
    """Get project root by looking for .claude directory or .git."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def cleanup_flag_files() -> int:
    """
    Remove stale .claude_*.flag files from project root.

    Returns:
        Number of files removed
    """
    removed = 0
    try:
        project_root = _get_project_root()
        flag_files = glob.glob(str(project_root / FLAG_PATTERN))

        for flag_file in flag_files:
            try:
                os.remove(flag_file)
                removed += 1
            except Exception:
                pass

    except Exception:
        pass

    return removed


def archive_logs() -> str | None:
    """
    Archive session logs if available.

    Returns:
        Path to archived file, or None
    """
    if not LIB_AVAILABLE:
        return None

    try:
        return archive_session_log()
    except Exception:
        return None


def rotate_old_logs() -> int:
    """
    Remove old log archives if total size exceeds threshold.

    Keeps the 10 most recent archives.

    Returns:
        Number of old logs removed
    """
    removed = 0
    try:
        project_root = _get_project_root()
        logs_dir = project_root / LOGS_DIR

        if not logs_dir.exists():
            return 0

        # Get all session delta archives
        archives = sorted(logs_dir.glob("session-delta-*.log"), key=lambda p: p.stat().st_mtime)

        # Keep only the 10 most recent
        if len(archives) > 10:
            for old_archive in archives[:-10]:
                try:
                    old_archive.unlink()
                    removed += 1
                except Exception:
                    pass

    except Exception:
        pass

    return removed


def main():
    """Main cleanup routine."""
    # Step 1: Archive current session log
    archived = archive_logs()

    # Step 2: Clean up flag files
    flags_removed = cleanup_flag_files()

    # Step 3: Rotate old logs
    logs_rotated = rotate_old_logs()

    # Report cleanup results (debug output)
    if archived or flags_removed or logs_rotated:
        report = []
        if archived:
            report.append(f"Archived session log to {archived}")
        if flags_removed:
            report.append(f"Removed {flags_removed} flag files")
        if logs_rotated:
            report.append(f"Rotated {logs_rotated} old log archives")

        print(f"DEBUG: Session cleanup: {'; '.join(report)}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)

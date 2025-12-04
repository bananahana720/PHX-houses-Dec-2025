#!/usr/bin/env python3
"""
Line reference validation for context management hooks.

Detects and validates file:line references like:
- src/main.py:L42
- src/main.py:42
- path/to/file.ts:L100-L150

Warns when referenced files have been modified since the reference
was likely created, indicating line numbers may have shifted.
"""

import re
import time
from pathlib import Path

# Patterns for line references
# Matches: file.py:L42, file.py:42, file.py:L10-L20
LINE_REF_PATTERN = re.compile(r":L?(\d+)(?:-L?(\d+))?$")

# Alternative pattern for explicit line markers
EXPLICIT_LINE_PATTERN = re.compile(r":L(\d+)")

# Reference freshness threshold (assume references older than this many hours may be stale)
REFERENCE_FRESHNESS_HOURS = 4


def parse_line_reference(path: str) -> tuple[str, int | None, int | None]:
    """
    Parse a file path that may contain line references.

    Args:
        path: File path potentially containing line reference (e.g., "src/main.py:L42")

    Returns:
        Tuple of (file_path, start_line, end_line)
        - file_path: The actual file path without line reference
        - start_line: Starting line number, or None if no reference
        - end_line: Ending line number (for ranges), or None
    """
    # Check for :L pattern first (explicit line marker)
    if ":L" in path:
        match = LINE_REF_PATTERN.search(path)
        if match:
            file_path = path[: match.start()]
            start_line = int(match.group(1))
            end_line = int(match.group(2)) if match.group(2) else None
            return (file_path, start_line, end_line)

    # Check for plain :number pattern (less common)
    # Be careful not to match Windows drive letters like C:
    if ":" in path:
        parts = path.rsplit(":", 1)
        if len(parts) == 2 and parts[1].isdigit():
            # Make sure it's not a Windows drive letter
            if len(parts[0]) > 1:  # Not just "C" or "D"
                return (parts[0], int(parts[1]), None)

    return (path, None, None)


def has_line_reference(path: str) -> bool:
    """
    Check if a path contains a line reference.

    Args:
        path: File path to check

    Returns:
        True if path contains :L or :number pattern
    """
    _, start_line, _ = parse_line_reference(path)
    return start_line is not None


def get_file_mtime(file_path: str | Path) -> float | None:
    """
    Get file modification time.

    Args:
        file_path: Path to the file

    Returns:
        Modification time as Unix timestamp, or None if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_mtime
    except Exception:
        return None


def check_reference_freshness(
    file_path: str | Path,
    reference_age_hours: float = REFERENCE_FRESHNESS_HOURS,
) -> tuple[bool, str]:
    """
    Check if a file reference might be stale.

    Compares file modification time against reference_age_hours to determine
    if the file has been modified recently enough that line references
    may have shifted.

    Args:
        file_path: Path to the referenced file
        reference_age_hours: Hours within which references are considered fresh

    Returns:
        Tuple of (is_stale, message)
        - is_stale: True if file was modified recently (references may be stale)
        - message: Human-readable explanation
    """
    path = Path(file_path)

    if not path.exists():
        return (True, f"Referenced file not found: {file_path}")

    mtime = get_file_mtime(path)
    if mtime is None:
        return (False, "Could not determine file modification time")

    # Calculate how recently the file was modified
    age_hours = (time.time() - mtime) / 3600

    if age_hours < reference_age_hours:
        # File was modified recently - line references may be stale
        if age_hours < 1:
            age_str = f"{int(age_hours * 60)} minutes"
        else:
            age_str = f"{age_hours:.1f} hours"

        return (
            True,
            f"File modified {age_str} ago - line numbers may have shifted. "
            f"Consider re-verifying with `rg` or `Grep` tool.",
        )

    return (False, "Reference appears current")


def validate_line_reference(path: str) -> tuple[bool, str | None]:
    """
    Validate a path with line reference.

    Full validation:
    1. Parse the line reference
    2. Check if file exists
    3. Check if file was recently modified

    Args:
        path: File path with potential line reference

    Returns:
        Tuple of (has_warning, warning_message)
        - has_warning: True if there's a warning to show
        - warning_message: The warning message, or None
    """
    file_path, start_line, _ = parse_line_reference(path)

    if start_line is None:
        # No line reference, nothing to validate
        return (False, None)

    # Check if file exists
    if not Path(file_path).exists():
        return (True, f"Referenced file not found: {file_path}")

    # Check freshness
    is_stale, message = check_reference_freshness(file_path)
    if is_stale:
        return (True, f"Line reference {path} - {message}")

    return (False, None)

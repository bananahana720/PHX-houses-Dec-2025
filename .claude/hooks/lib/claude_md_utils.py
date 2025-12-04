#!/usr/bin/env python3
"""
CLAUDE.md file operations for context management hooks.

Provides:
- Discovery: Check if CLAUDE.md exists in a directory
- Staleness: Check if CLAUDE.md is stale (>24h by default)
- Templates: Detect unfilled templates, create from template
- Frontmatter: Parse YAML frontmatter for metadata
"""

import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Directories to skip CLAUDE.md checks
EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".claude/audio",
        "TRASH",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".tox",
        ".eggs",
    }
)

# Template marker for unfilled CLAUDE.md files
TEMPLATE_MARKER = "<!-- TEMPLATE:UNFILLED -->"

# Default staleness threshold in hours
DEFAULT_STALE_HOURS = 24

# Template file location (relative to project root)
TEMPLATE_PATH = ".claude/templates/CLAUDE.md.template"


def _get_project_root() -> Path:
    """Get project root by looking for .claude directory or .git."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def is_excluded_directory(directory: str | Path) -> bool:
    """Check if directory should be excluded from CLAUDE.md checks."""
    dir_path = Path(directory)
    parts = dir_path.parts

    # Check if any part of the path is an excluded directory
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True

    # Also check for hidden directories (starting with .)
    # except .claude which we explicitly manage
    for part in parts:
        if part.startswith(".") and part not in {".claude"}:
            if part in {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache"}:
                return True

    return False


def check_claude_md_exists(directory: str | Path) -> bool:
    """
    Check if CLAUDE.md exists in the given directory.

    Args:
        directory: Path to the directory to check

    Returns:
        True if CLAUDE.md exists, False otherwise
    """
    claude_md_path = Path(directory) / "CLAUDE.md"
    return claude_md_path.exists()


def parse_frontmatter(file_path: str | Path) -> dict[str, Any]:
    """
    Parse YAML frontmatter from a CLAUDE.md file.

    Expected format:
    ---
    last_updated: 2025-12-03
    updated_by: Claude Code
    staleness_hours: 24
    ---

    Args:
        file_path: Path to the CLAUDE.md file

    Returns:
        Dictionary with frontmatter values, empty dict if no frontmatter
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for frontmatter delimiters
        if not content.startswith("---"):
            return {}

        # Find end delimiter
        end_match = re.search(r"\n---\s*\n", content[3:])
        if not end_match:
            return {}

        frontmatter_text = content[3 : end_match.start() + 3]

        # Simple YAML-like parsing (avoid dependency on pyyaml)
        result: dict[str, Any] = {}
        for line in frontmatter_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Type conversion
                if value.isdigit():
                    result[key] = int(value)
                elif value.lower() in ("true", "false"):
                    result[key] = value.lower() == "true"
                elif value.startswith("[") and value.endswith("]"):
                    # Simple list parsing
                    result[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
                else:
                    result[key] = value

        return result
    except Exception:
        return {}


def is_stale(file_path: str | Path, threshold_hours: int = DEFAULT_STALE_HOURS) -> bool:
    """
    Check if a CLAUDE.md file is stale based on its modification time.

    Args:
        file_path: Path to the CLAUDE.md file
        threshold_hours: Hours after which file is considered stale (default 24)

    Returns:
        True if file is stale, False otherwise
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False  # Non-existent files handled separately

        mtime = path.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600

        return age_hours > threshold_hours
    except Exception:
        return False  # On error, assume not stale


def is_naked_template(file_path: str | Path) -> bool:
    """
    Check if a CLAUDE.md file is an unfilled template.

    Detects:
    - Presence of TEMPLATE_MARKER comment
    - All placeholder brackets remaining [PURPOSE], [ROLE], etc.

    Args:
        file_path: Path to the CLAUDE.md file

    Returns:
        True if file appears to be an unfilled template
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for explicit template marker
        if TEMPLATE_MARKER in content:
            return True

        # Check for unfilled placeholder pattern
        # Matches [PLACEHOLDER] on its own line or as entire cell content
        placeholder_pattern = r"^\[.+\]$"
        lines = content.split("\n")
        placeholder_count = sum(1 for line in lines if re.match(placeholder_pattern, line.strip()))

        # If more than 3 placeholder lines, likely unfilled
        return placeholder_count > 3
    except Exception:
        return False


def create_from_template(directory: str | Path) -> str | None:
    """
    Create a CLAUDE.md file in the given directory from template.

    Args:
        directory: Path to the directory where CLAUDE.md should be created

    Returns:
        Path to created file, or None if creation failed
    """
    try:
        dir_path = Path(directory)
        claude_md_path = dir_path / "CLAUDE.md"

        # Don't overwrite existing files
        if claude_md_path.exists():
            return str(claude_md_path)

        # Find template
        project_root = _get_project_root()
        template_path = project_root / TEMPLATE_PATH

        if template_path.exists():
            # Copy template
            shutil.copy(template_path, claude_md_path)
        else:
            # Create minimal template if no template file exists
            dir_name = dir_path.name
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            minimal_template = f"""{TEMPLATE_MARKER}
---
last_updated: {timestamp}
updated_by: auto-generated
staleness_hours: 24
---
# {dir_name}

## Purpose
[1-2 sentences: what + why]

## Contents
| Path | Purpose |
|------|---------|
| `file` | [desc] |

## Tasks
- [ ] Fill in this CLAUDE.md template

## Learnings
- [pattern/discovery]

## Refs
- [desc]: `path:lines`
"""
            with open(claude_md_path, "w", encoding="utf-8") as f:
                f.write(minimal_template)

        return str(claude_md_path)
    except Exception:
        return None


def get_staleness_hours(file_path: str | Path) -> int:
    """
    Get staleness threshold from file's frontmatter, or default.

    Args:
        file_path: Path to the CLAUDE.md file

    Returns:
        Staleness threshold in hours
    """
    frontmatter = parse_frontmatter(file_path)
    return frontmatter.get("staleness_hours", DEFAULT_STALE_HOURS)


def get_last_updated(file_path: str | Path) -> str | None:
    """
    Get last_updated timestamp from file's frontmatter.

    Args:
        file_path: Path to the CLAUDE.md file

    Returns:
        last_updated string or None
    """
    frontmatter = parse_frontmatter(file_path)
    return frontmatter.get("last_updated")

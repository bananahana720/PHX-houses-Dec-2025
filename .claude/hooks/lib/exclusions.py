#!/usr/bin/env python3
"""
Shared directory exclusion patterns for context management hooks.

Centralizes exclusion logic to ensure consistent filtering across:
- stop_hygiene_hook.py (CLAUDE.md validation)
- delta_logger.py (session delta tracking)
- Other hooks needing path filtering

Categories:
- Caches: Binary/generated files with no context value
- Build artifacts: Generated output directories
- Virtual environments: Python venvs
- System: Git internals, node_modules
- Claude Code: Session data, audio, logs
- Project-specific: Data caches, archives, processed output
"""

from pathlib import Path, PurePosixPath

# Directories to exclude from CLAUDE.md tracking and delta logging
# These don't need context documentation or change tracking
EXCLUDED_DIRS: frozenset[str] = frozenset({
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
    # Project-specific processed output (P2 fix)
    "data/property_images/processed",
    # Project trash/archive (explicitly unwanted)
    "TRASH",
    "archive",
    # Generated reports (output, not source)
    "reports",
})

# Patterns for path-based filtering (substring match)
# Used for delta logging skip patterns
SKIP_PATTERNS: tuple[str, ...] = (
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
    # Project-specific processed output (P2 fix)
    "data/property_images/processed",
    # Project trash/archive (explicitly unwanted)
    "TRASH/",
    "archive/",
    # Generated reports (output, not source)
    "reports/",
)


def normalize_path(path: str | Path) -> str:
    """
    Normalize path to POSIX format for consistent comparison.

    Handles Windows/Unix path separator differences.

    Args:
        path: Path string or Path object

    Returns:
        POSIX-normalized path string
    """
    return PurePosixPath(Path(path)).as_posix()


def should_exclude_directory(directory: str | Path) -> bool:
    """
    Check if directory should be excluded from CLAUDE.md hygiene checks.

    Used by stop_hygiene_hook to filter relevant directories.

    Args:
        directory: Directory path to check

    Returns:
        True if directory should be excluded, False otherwise
    """
    normalized = normalize_path(directory)

    # Check if any excluded directory name appears in path
    if any(ex in normalized for ex in EXCLUDED_DIRS):
        return True

    # Check for Claude session directories (agent-* patterns)
    if "/.claude/projects/" in normalized:
        # Check if it's an agent session directory
        parts = Path(directory).parts
        for part in parts:
            if part.startswith("agent-"):
                return True

    return False


def should_skip_logging(file_path: str | Path) -> bool:
    """
    Check if file should be skipped from delta logging.

    Used by delta_logger to filter noise from session tracking.

    Args:
        file_path: File path to check

    Returns:
        True if file should be skipped, False otherwise
    """
    normalized = normalize_path(file_path)

    # Skip agent session directories (subagent transcripts)
    if "/.claude/projects/" in normalized:
        return True
    if "/agent-" in normalized:
        return True

    # Skip patterns (substring match)
    return any(pat in normalized for pat in SKIP_PATTERNS)

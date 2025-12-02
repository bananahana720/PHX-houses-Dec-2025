"""File operation utilities with atomic save and backup support."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def atomic_json_save(
    path: Path | str,
    data: Any,
    create_backup: bool = True,
    backup_dir: Path | None = None,
    indent: int = 2,
) -> Path | None:
    """Atomically save JSON data with optional backup.

    Uses write-to-temp + atomic-rename pattern to prevent corruption
    if the process crashes mid-write.

    The atomic pattern:
    1. Create backup of existing file (if requested)
    2. Write data to a temporary file (.tmp suffix)
    3. Atomically rename temp file to target path

    On POSIX systems, the rename is atomic. On Windows, Path.replace()
    will atomically replace the target file.

    Args:
        path: Target file path for JSON output.
        data: Data to serialize as JSON (must be JSON-serializable).
        create_backup: Whether to backup existing file before writing.
            Defaults to True.
        backup_dir: Directory for backups. Defaults to same directory as path.
        indent: JSON indentation level. Defaults to 2.

    Returns:
        Path to backup file if one was created, None otherwise.

    Raises:
        OSError: If file operations fail (permissions, disk full, etc.)
        TypeError: If data is not JSON-serializable.

    Example:
        >>> from pathlib import Path
        >>> data = {"properties": [...]}
        >>> backup = atomic_json_save(Path("data/enrichment.json"), data)
        >>> if backup:
        ...     print(f"Backup created: {backup}")
    """
    path = Path(path)
    backup_path: Path | None = None

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create backup of existing file
    if create_backup and path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_resolved = backup_dir or path.parent
        backup_dir_resolved = Path(backup_dir_resolved)
        backup_dir_resolved.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir_resolved / f"{path.stem}.{timestamp}.bak{path.suffix}"
        shutil.copy2(path, backup_path)
        logger.debug(f"Created backup: {backup_path}")

    # Write to temp file first (atomic pattern)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        # Atomic rename - on POSIX this is atomic, on Windows it replaces
        temp_path.replace(path)
        logger.debug(f"Atomically saved: {path}")

    except Exception:
        # Clean up temp file on failure
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass  # Best effort cleanup
        raise

    return backup_path


def cleanup_old_backups(
    directory: Path | str,
    pattern: str = "*.bak.json",
    keep_count: int = 5,
) -> list[Path]:
    """Remove old backup files, keeping only the most recent ones.

    Args:
        directory: Directory containing backup files.
        pattern: Glob pattern to match backup files.
        keep_count: Number of most recent backups to keep.

    Returns:
        List of paths that were deleted.

    Example:
        >>> deleted = cleanup_old_backups(Path("data/"), "enrichment_data.*.bak.json", keep_count=3)
        >>> print(f"Removed {len(deleted)} old backups")
    """
    directory = Path(directory)
    deleted: list[Path] = []

    if not directory.exists():
        return deleted

    # Find all matching backup files
    backups = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    # Remove old backups beyond keep_count
    for old_backup in backups[keep_count:]:
        try:
            old_backup.unlink()
            deleted.append(old_backup)
            logger.debug(f"Removed old backup: {old_backup}")
        except OSError as e:
            logger.warning(f"Failed to remove backup {old_backup}: {e}")

    return deleted

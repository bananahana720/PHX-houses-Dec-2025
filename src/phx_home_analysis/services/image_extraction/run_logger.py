"""Per-run change logging for audit trail.

Provides detailed logging of each extraction run for debugging,
auditing, and analysis. Each run creates a separate log file
with comprehensive change tracking.

Architecture:
    - Each run gets a unique ID and log file
    - Tracks all changes: new images, updates, removals, errors
    - Property-level summaries for quick review
    - Aggregate statistics for run comparison
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class PropertyChanges:
    """Changes for a single property during a run.

    Tracks all image-related changes for one property.

    Attributes:
        address: Full property address
        property_hash: 8-char hash of address
        urls_discovered: Total URLs found in listing
        new_images: Count of newly downloaded images
        unchanged: Count of already-known images
        duplicates: Count of duplicate images detected
        content_changed: Count of images with content changes
        removed: Count of URLs no longer in listing
        errors: Count of failed downloads
        new_image_ids: List of newly created image IDs
        error_messages: List of error messages
    """

    address: str
    property_hash: str
    urls_discovered: int = 0
    new_images: int = 0
    unchanged: int = 0
    duplicates: int = 0
    content_changed: int = 0
    removed: int = 0
    errors: int = 0
    new_image_ids: list[str] = field(default_factory=list)
    removed_urls: list[str] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "address": self.address,
            "property_hash": self.property_hash,
            "urls_discovered": self.urls_discovered,
            "new_images": self.new_images,
            "unchanged": self.unchanged,
            "duplicates": self.duplicates,
            "content_changed": self.content_changed,
            "removed": self.removed,
            "errors": self.errors,
            "new_image_ids": self.new_image_ids,
            "removed_urls": self.removed_urls,
            "error_messages": self.error_messages,
        }

    @property
    def has_changes(self) -> bool:
        """Check if this property had any changes."""
        return (
            self.new_images > 0
            or self.content_changed > 0
            or self.removed > 0
        )

    @property
    def needs_review(self) -> bool:
        """Check if this property needs manual review.

        Triggers on:
        - Large batch of new images (>10)
        - Multiple errors
        - Content changes
        """
        return (
            self.new_images > 10
            or self.errors > 3
            or self.content_changed > 0
        )


@dataclass
class RunLog:
    """Complete log of a single extraction run.

    Tracks all changes across all properties for auditing and debugging.

    Attributes:
        run_id: Unique identifier for this run
        started_at: ISO timestamp when run started
        ended_at: ISO timestamp when run ended (None if in progress)
        mode: Run mode (fresh, resume, incremental)
        properties_requested: Number of properties requested
        properties_processed: Number of properties actually processed
        property_changes: Dict mapping address -> PropertyChanges
        aggregate: Aggregate statistics
        errors: Global errors not associated with specific properties
    """

    run_id: str = field(default_factory=lambda: str(uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    ended_at: str | None = None
    mode: str = "incremental"
    properties_requested: int = 0
    properties_processed: int = 0
    property_changes: dict[str, PropertyChanges] = field(default_factory=dict)
    aggregate: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize aggregate counters."""
        if not self.aggregate:
            self.aggregate = {
                "total_urls_discovered": 0,
                "total_new_images": 0,
                "total_unchanged": 0,
                "total_duplicates": 0,
                "total_content_changed": 0,
                "total_removed": 0,
                "total_errors": 0,
                "properties_with_changes": 0,
                "properties_needing_review": 0,
            }

    def record_property(self, changes: PropertyChanges) -> None:
        """Record changes for a property.

        Args:
            changes: PropertyChanges for the property
        """
        self.property_changes[changes.address] = changes
        self.properties_processed += 1

        # Update aggregates
        self.aggregate["total_urls_discovered"] += changes.urls_discovered
        self.aggregate["total_new_images"] += changes.new_images
        self.aggregate["total_unchanged"] += changes.unchanged
        self.aggregate["total_duplicates"] += changes.duplicates
        self.aggregate["total_content_changed"] += changes.content_changed
        self.aggregate["total_removed"] += changes.removed
        self.aggregate["total_errors"] += changes.errors

        if changes.has_changes:
            self.aggregate["properties_with_changes"] += 1

        if changes.needs_review:
            self.aggregate["properties_needing_review"] += 1

    def record_error(self, message: str) -> None:
        """Record a global error.

        Args:
            message: Error message
        """
        self.errors.append(message)

    def finalize(self) -> None:
        """Finalize the run log with end timestamp."""
        self.ended_at = datetime.now().astimezone().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "mode": self.mode,
            "properties_requested": self.properties_requested,
            "properties_processed": self.properties_processed,
            "aggregate": self.aggregate,
            "property_changes": {
                addr: changes.to_dict()
                for addr, changes in self.property_changes.items()
            },
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
        }

    @property
    def duration_seconds(self) -> float | None:
        """Calculate run duration in seconds."""
        if not self.ended_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.ended_at)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None

    def save(self, metadata_dir: Path) -> Path:
        """Save run log to run_history directory.

        Creates run_history subdirectory if needed.

        Args:
            metadata_dir: Base metadata directory

        Returns:
            Path to saved log file
        """
        history_dir = metadata_dir / "run_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # Use timestamp + run_id for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"run_{timestamp}_{self.run_id}.json"
        log_path = history_dir / filename

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Saved run log to {log_path}")
            return log_path
        except OSError as e:
            logger.error(f"Failed to save run log: {e}")
            raise

    def get_summary(self) -> str:
        """Generate human-readable summary of the run.

        Returns:
            Multi-line summary string
        """
        lines = [
            f"Run {self.run_id} Summary",
            "=" * 40,
            f"Mode: {self.mode}",
            f"Duration: {self.duration_seconds:.1f}s" if self.duration_seconds else "Duration: In progress",
            f"Properties: {self.properties_processed}/{self.properties_requested}",
            "",
            "Aggregate Stats:",
            f"  URLs discovered: {self.aggregate['total_urls_discovered']}",
            f"  New images: {self.aggregate['total_new_images']}",
            f"  Unchanged: {self.aggregate['total_unchanged']}",
            f"  Duplicates: {self.aggregate['total_duplicates']}",
            f"  Content changed: {self.aggregate['total_content_changed']}",
            f"  Removed: {self.aggregate['total_removed']}",
            f"  Errors: {self.aggregate['total_errors']}",
            "",
            f"Properties with changes: {self.aggregate['properties_with_changes']}",
            f"Properties needing review: {self.aggregate['properties_needing_review']}",
        ]

        # Add properties needing review
        review_needed = [
            (addr, changes)
            for addr, changes in self.property_changes.items()
            if changes.needs_review
        ]
        if review_needed:
            lines.append("")
            lines.append("REVIEW NEEDED:")
            for addr, changes in review_needed:
                reasons = []
                if changes.new_images > 10:
                    reasons.append(f"{changes.new_images} new images")
                if changes.errors > 3:
                    reasons.append(f"{changes.errors} errors")
                if changes.content_changed > 0:
                    reasons.append(f"{changes.content_changed} content changes")
                lines.append(f"  {addr}: {', '.join(reasons)}")

        return "\n".join(lines)


class RunLogger:
    """Manager for run logs with history tracking.

    Provides convenience methods for creating and managing run logs
    with automatic history cleanup.

    Attributes:
        metadata_dir: Base directory for run logs
        max_history: Maximum number of run logs to keep
    """

    def __init__(self, metadata_dir: Path, max_history: int = 50):
        """Initialize run logger.

        Args:
            metadata_dir: Base metadata directory
            max_history: Maximum run logs to retain (default 50)
        """
        self.metadata_dir = Path(metadata_dir)
        self.max_history = max_history
        self.history_dir = self.metadata_dir / "run_history"
        self.current_run: RunLog | None = None

    def start_run(
        self,
        properties_requested: int,
        mode: str = "incremental",
    ) -> RunLog:
        """Start a new run and create log.

        Args:
            properties_requested: Number of properties to process
            mode: Run mode (fresh, resume, incremental)

        Returns:
            New RunLog instance
        """
        self.current_run = RunLog(
            mode=mode,
            properties_requested=properties_requested,
        )
        logger.info(f"Started run {self.current_run.run_id} (mode: {mode})")
        return self.current_run

    def finish_run(self) -> Path | None:
        """Finalize current run and save log.

        Returns:
            Path to saved log file, or None if no current run
        """
        if not self.current_run:
            return None

        self.current_run.finalize()
        log_path = self.current_run.save(self.metadata_dir)

        # Log summary
        logger.info("\n" + self.current_run.get_summary())

        # Cleanup old logs
        self._cleanup_history()

        self.current_run = None
        return log_path

    def _cleanup_history(self) -> None:
        """Remove old run logs beyond max_history limit."""
        if not self.history_dir.exists():
            return

        logs = sorted(self.history_dir.glob("run_*.json"))

        if len(logs) > self.max_history:
            to_delete = logs[: len(logs) - self.max_history]
            for log_path in to_delete:
                try:
                    log_path.unlink()
                    logger.debug(f"Deleted old run log: {log_path.name}")
                except OSError as e:
                    logger.warning(f"Failed to delete old run log {log_path}: {e}")

    def get_recent_runs(self, limit: int = 10) -> list[dict]:
        """Get summaries of recent runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summary dicts (most recent first)
        """
        if not self.history_dir.exists():
            return []

        logs = sorted(self.history_dir.glob("run_*.json"), reverse=True)[:limit]
        summaries = []

        for log_path in logs:
            try:
                with open(log_path, encoding="utf-8") as f:
                    data = json.load(f)
                    summaries.append({
                        "run_id": data.get("run_id"),
                        "started_at": data.get("started_at"),
                        "mode": data.get("mode"),
                        "properties_processed": data.get("properties_processed"),
                        "new_images": data.get("aggregate", {}).get("total_new_images", 0),
                        "errors": data.get("aggregate", {}).get("total_errors", 0),
                    })
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to read run log {log_path}: {e}")

        return summaries

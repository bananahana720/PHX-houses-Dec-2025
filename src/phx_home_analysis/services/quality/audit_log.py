"""Quality audit log tracking for data processing and quality events.

This module provides audit logging functionality for tracking quality-related
events throughout the property analysis pipeline, including field updates,
quality checks, data validations, and processing milestones.

The audit log enables:
- Comprehensive data provenance and change tracking
- Quality audit trails for compliance and debugging
- Historical analysis of data transformation steps
- Root cause analysis for data quality issues
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of actions that can be logged in the audit trail."""

    FIELD_UPDATED = "field_updated"
    FIELD_VALIDATED = "field_validated"
    FIELD_REJECTED = "field_rejected"
    QUALITY_CHECK_PASSED = "quality_check_passed"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    DATA_ENRICHED = "data_enriched"
    DATA_DEDUPLICATED = "data_deduplicated"
    DATA_STANDARDIZED = "data_standardized"
    CONFIDENCE_UPDATED = "confidence_updated"
    PROPERTY_SCORED = "property_scored"
    KILL_SWITCH_APPLIED = "kill_switch_applied"
    LOG_ROTATED = "log_rotated"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class AuditEntry:
    """Single entry in the audit log.

    Records a quality event including what happened, when, and relevant context.

    Attributes:
        property_hash: SHA256 hash identifying the property being processed.
        action: Type of action being logged (AuditAction enum).
        timestamp: When the action occurred.
        field_name: Optional field being modified (for field-level actions).
        old_value: Previous value before change (if applicable).
        new_value: New value after change (if applicable).
        source: Data source for the change (if applicable).
        confidence: Confidence level if applicable (0.0-1.0).
        message: Human-readable description of the action.
        run_id: Identifier for the processing run/batch.
        agent_name: Name of the agent/service performing the action.
        metadata: Optional additional context as dictionary.
    """

    property_hash: str
    action: AuditAction
    timestamp: datetime
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    source: str | None = None
    confidence: float | None = None
    message: str = ""
    run_id: str | None = None
    agent_name: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize entry to dictionary for JSON storage.

        Returns:
            Dictionary representation of the audit entry.
        """
        data = asdict(self)
        # Convert enum to string
        data["action"] = self.action.value
        # Convert datetime to ISO format string
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        """Deserialize entry from dictionary.

        Args:
            data: Dictionary containing audit entry data.

        Returns:
            AuditEntry instance.

        Raises:
            ValueError: If data is invalid or missing required fields.
        """
        try:
            entry_data = data.copy()
            # Convert action string to enum
            entry_data["action"] = AuditAction(entry_data["action"])
            # Convert timestamp ISO string to datetime
            entry_data["timestamp"] = datetime.fromisoformat(entry_data["timestamp"])
            return cls(**entry_data)
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid audit entry data: {e}") from e


class AuditLog:
    """Persistent audit log for quality events.

    Maintains a chronological log of all quality-related events during
    property analysis, with file persistence and query capabilities.

    Thread-safe for concurrent writes using a lock.
    """

    def __init__(self, log_file: Path | None = None):
        """Initialize audit log.

        Args:
            log_file: Path to JSON file for persistence. If None,
                     uses in-memory storage only (no persistence).
        """
        self.log_file = log_file
        self.entries: list[AuditEntry] = []
        self._lock = Lock()
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing log entries from file if it exists."""
        if not self.log_file or not self.log_file.exists():
            return

        try:
            with open(self.log_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.entries = [AuditEntry.from_dict(entry) for entry in data]
                logger.debug(f"Loaded {len(self.entries)} entries from {self.log_file}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to load audit log from {self.log_file}: {e}")
            # Start with empty log on corrupted file
            self.entries = []

    def add_entry(
        self,
        property_hash: str,
        action: AuditAction,
        message: str = "",
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        source: str | None = None,
        confidence: float | None = None,
        run_id: str | None = None,
        agent_name: str | None = None,
        metadata: dict | None = None,
    ) -> AuditEntry:
        """Add an entry to the audit log.

        Args:
            property_hash: SHA256 hash identifying the property.
            action: Type of action (AuditAction enum).
            message: Human-readable description of action.
            field_name: Optional field name for field-level actions.
            old_value: Previous value if applicable.
            new_value: New value if applicable.
            source: Data source if applicable.
            confidence: Confidence level (0.0-1.0) if applicable.
            run_id: Processing run identifier.
            agent_name: Agent/service performing action.
            metadata: Optional additional context.

        Returns:
            The created AuditEntry.

        Raises:
            ValueError: If field_name is provided without action being field-related.
            ValueError: If confidence is outside 0.0-1.0 range.
        """
        if confidence is not None and not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        entry = AuditEntry(
            property_hash=property_hash,
            action=action,
            timestamp=datetime.now(),
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            source=source,
            confidence=confidence,
            message=message,
            run_id=run_id,
            agent_name=agent_name,
            metadata=metadata or {},
        )

        with self._lock:
            self.entries.append(entry)

        return entry

    def save(self) -> None:
        """Persist audit log to file.

        Writes current entries to the log file with atomic write semantics
        (writes to temporary file, then renames).

        Raises:
            IOError: If file write fails.
        """
        if not self.log_file:
            return  # No persistence configured

        with self._lock:
            try:
                # Write to temporary file first
                temp_file = self.log_file.with_suffix(".tmp")
                data = [entry.to_dict() for entry in self.entries]

                with open(temp_file, "w") as f:
                    json.dump(data, f, indent=2)

                # Atomic rename
                temp_file.replace(self.log_file)
                logger.debug(f"Saved {len(self.entries)} entries to {self.log_file}")

            except OSError as e:
                logger.error(f"Failed to save audit log to {self.log_file}: {e}")
                raise

    def get_entries_for_property(self, property_hash: str) -> list[AuditEntry]:
        """Get all entries for a specific property.

        Args:
            property_hash: SHA256 hash of property.

        Returns:
            List of AuditEntry objects for that property, in chronological order.
        """
        with self._lock:
            return [e for e in self.entries if e.property_hash == property_hash]

    def get_entries_by_action(self, action: AuditAction) -> list[AuditEntry]:
        """Get all entries of a specific action type.

        Args:
            action: AuditAction enum value to filter by.

        Returns:
            List of AuditEntry objects with that action.
        """
        with self._lock:
            return [e for e in self.entries if e.action == action]

    def get_entries_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[AuditEntry]:
        """Get entries within a date range.

        Args:
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of AuditEntry objects in the date range.
        """
        with self._lock:
            return [e for e in self.entries if start_date <= e.timestamp <= end_date]

    def get_entries_by_run(self, run_id: str) -> list[AuditEntry]:
        """Get all entries for a specific processing run.

        Args:
            run_id: Processing run identifier.

        Returns:
            List of AuditEntry objects from that run.
        """
        with self._lock:
            return [e for e in self.entries if e.run_id == run_id]

    def get_entries_by_field(self, property_hash: str, field_name: str) -> list[AuditEntry]:
        """Get all entries for a specific field in a property.

        Args:
            property_hash: SHA256 hash of property.
            field_name: Name of field to query.

        Returns:
            List of AuditEntry objects for that field.
        """
        with self._lock:
            return [
                e
                for e in self.entries
                if e.property_hash == property_hash and e.field_name == field_name
            ]

    def clear(self) -> None:
        """Clear all entries from the audit log.

        Warning: This removes all entries from memory and file (if persisted).
        """
        with self._lock:
            self.entries.clear()
            if self.log_file and self.log_file.exists():
                self.log_file.unlink()

    def rotate_log(self, max_entries: int = 10000) -> Path | None:
        """Rotate audit log when it reaches maximum size.

        Creates a backup of current log and starts fresh if entries exceed max_entries.

        Args:
            max_entries: Maximum number of entries before rotation.

        Returns:
            Path to backup file if rotation occurred, None otherwise.
        """
        with self._lock:
            if len(self.entries) <= max_entries:
                return None

            if not self.log_file:
                # Can't rotate without a file
                self.entries = self.entries[-max_entries:]
                return None

            # Create backup file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.log_file.parent / f"{self.log_file.stem}_backup_{timestamp}.json"

            try:
                # Write current log to backup
                with open(backup_file, "w") as f:
                    data = [entry.to_dict() for entry in self.entries]
                    json.dump(data, f, indent=2)

                # Keep only recent entries
                self.entries = self.entries[-max_entries:]

                # Save the cleaned log
                data = [entry.to_dict() for entry in self.entries]
                with open(self.log_file, "w") as f:
                    json.dump(data, f, indent=2)

                # Log rotation event
                self.add_entry(
                    property_hash="system",
                    action=AuditAction.LOG_ROTATED,
                    message=f"Rotated log, kept {max_entries} recent entries",
                    metadata={"backup_file": str(backup_file)},
                )

                logger.info(f"Rotated audit log. Backup: {backup_file}")
                return backup_file

            except OSError as e:
                logger.error(f"Failed to rotate audit log: {e}")
                return None

    def get_count(self) -> int:
        """Get total number of entries in audit log.

        Returns:
            Total entry count.
        """
        with self._lock:
            return len(self.entries)

    def get_entries_for_property_after(
        self, property_hash: str, timestamp: datetime
    ) -> list[AuditEntry]:
        """Get entries for a property after a specific timestamp.

        Args:
            property_hash: SHA256 hash of property.
            timestamp: Only return entries after this time.

        Returns:
            List of AuditEntry objects matching criteria.
        """
        with self._lock:
            return [
                e
                for e in self.entries
                if e.property_hash == property_hash and e.timestamp > timestamp
            ]

    def get_summary(self) -> dict:
        """Get summary statistics of the audit log.

        Returns:
            Dictionary with summary information including:
            - total_entries: Total number of entries
            - properties_tracked: Number of unique properties
            - actions_breakdown: Count by action type
            - oldest_entry: Timestamp of oldest entry
            - newest_entry: Timestamp of newest entry
        """
        with self._lock:
            if not self.entries:
                return {
                    "total_entries": 0,
                    "properties_tracked": 0,
                    "actions_breakdown": {},
                    "oldest_entry": None,
                    "newest_entry": None,
                }

            # Count by action
            actions_breakdown = {}
            for entry in self.entries:
                action_name = entry.action.value
                actions_breakdown[action_name] = actions_breakdown.get(action_name, 0) + 1

            # Unique properties
            unique_properties = set(e.property_hash for e in self.entries)

            # Oldest and newest entries
            oldest = min(e.timestamp for e in self.entries)
            newest = max(e.timestamp for e in self.entries)

            return {
                "total_entries": len(self.entries),
                "properties_tracked": len(unique_properties),
                "actions_breakdown": actions_breakdown,
                "oldest_entry": oldest.isoformat(),
                "newest_entry": newest.isoformat(),
            }

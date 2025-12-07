"""Data models for enrichment merge operations.

This module provides dataclasses for representing merge results, field conflicts,
and conflict reports when merging county data into property enrichment records.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldConflict:
    """Represents a conflict between existing and new field values.

    Tracks when a field update would conflict with existing data,
    including the action taken and the reason for that action.

    Attributes:
        field_name: Name of the conflicting field.
        existing_value: Current value in enrichment data.
        new_value: New value from county data.
        action: Action taken - "preserved", "updated", "skipped", or "added".
        reason: Explanation of why the action was taken.
    """

    field_name: str
    existing_value: Any
    new_value: Any
    action: str  # "preserved", "updated", "skipped", "added"
    reason: str

    def __post_init__(self) -> None:
        """Validate action is one of the allowed values."""
        valid_actions = {"preserved", "updated", "skipped", "added"}
        if self.action not in valid_actions:
            raise ValueError(f"Invalid action '{self.action}'. Must be one of: {valid_actions}")


@dataclass
class ConflictReport:
    """Summary of all conflicts from a merge operation.

    Categorizes conflicts by type for reporting and auditing purposes.

    Attributes:
        preserved_manual: Fields preserved due to manual research.
        updated: Fields that were updated with new values.
        skipped_no_change: Field names where values matched (no update needed).
        new_fields: Field names that were added (no existing value).
    """

    preserved_manual: list[FieldConflict] = field(default_factory=list)
    updated: list[FieldConflict] = field(default_factory=list)
    skipped_no_change: list[str] = field(default_factory=list)
    new_fields: list[str] = field(default_factory=list)

    @property
    def total_preserved(self) -> int:
        """Count of fields preserved from manual research."""
        return len(self.preserved_manual)

    @property
    def total_updated(self) -> int:
        """Count of fields that were updated."""
        return len(self.updated)

    @property
    def total_new(self) -> int:
        """Count of new fields added."""
        return len(self.new_fields)

    @property
    def total_skipped(self) -> int:
        """Count of fields skipped (no change needed)."""
        return len(self.skipped_no_change)

    def to_dict(self) -> dict:
        """Convert to dictionary format for backward compatibility.

        Returns:
            Dictionary matching the legacy conflict format used by CLI.
        """
        return {
            "preserved_manual": [
                {
                    "field": c.field_name,
                    "value": c.existing_value,
                    "county_value": c.new_value,
                    "reason": c.reason,
                }
                for c in self.preserved_manual
            ],
            "updated": [
                {
                    "field": c.field_name,
                    "old": c.existing_value,
                    "new": c.new_value,
                    "reason": c.reason,
                }
                for c in self.updated
            ],
            "skipped_no_change": self.skipped_no_change,
            "new_fields": self.new_fields,
        }


@dataclass
class MergeResult:
    """Result of merging parcel data into enrichment.

    Contains the updated entry, conflict information, and status of the merge.

    Attributes:
        full_address: Full property address (merge key).
        success: Whether the merge completed successfully.
        updated_entry: The merged enrichment entry dictionary.
        conflict_report: Detailed conflict categorization.
        error: Error message if merge failed, None otherwise.
    """

    full_address: str
    success: bool
    updated_entry: dict
    conflict_report: ConflictReport = field(default_factory=ConflictReport)
    error: str | None = None

    @property
    def conflicts(self) -> list[FieldConflict]:
        """Get all conflicts (preserved + updated).

        Returns:
            Combined list of preserved and updated conflicts.
        """
        return [*self.conflict_report.preserved_manual, *self.conflict_report.updated]

    @property
    def has_conflicts(self) -> bool:
        """Check if there were any conflicts during merge."""
        return bool(self.conflict_report.preserved_manual or self.conflict_report.updated)

    def to_legacy_dict(self) -> dict:
        """Convert conflict report to legacy dictionary format.

        For backward compatibility with existing CLI code.

        Returns:
            Dictionary in the format expected by extract_county_data.py.
        """
        return self.conflict_report.to_dict()

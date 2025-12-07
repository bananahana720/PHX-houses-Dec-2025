"""Data models for property lifecycle management.

This module defines the core data structures for tracking property status,
staleness, and lifecycle transitions in the Phoenix home analysis pipeline.

Status Lifecycle:
    ACTIVE -> SOLD (property sold)
    ACTIVE -> DELISTED (listing removed)
    ACTIVE -> ARCHIVED (manually archived)
    SOLD/DELISTED -> ARCHIVED (post-sale/delisting cleanup)
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class PropertyStatus(str, Enum):
    """Status of a property in the analysis pipeline.

    Tracks the current state of a property listing to determine
    what actions are appropriate.

    Attributes:
        ACTIVE: Property is actively listed and being analyzed.
        SOLD: Property has been sold and is no longer on market.
        DELISTED: Listing was removed without a sale.
        ARCHIVED: Property has been archived (no longer tracked).
    """

    ACTIVE = "active"
    SOLD = "sold"
    DELISTED = "delisted"
    ARCHIVED = "archived"

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state (SOLD, DELISTED, ARCHIVED).

        Returns:
            True if property cannot transition further automatically.
        """
        return self in (PropertyStatus.SOLD, PropertyStatus.DELISTED, PropertyStatus.ARCHIVED)

    @property
    def can_archive(self) -> bool:
        """Check if property can be archived from this state.

        Returns:
            True if property can transition to ARCHIVED.
        """
        return self != PropertyStatus.ARCHIVED


class PropertyLifecycle(BaseModel):
    """Lifecycle tracking for a single property.

    Records status, timestamps, and staleness metrics for managing
    property data freshness and archival workflows.

    Attributes:
        full_address: Complete property address (used as identifier).
        status: Current property status in the pipeline.
        last_updated: When the property data was last refreshed.
        created_at: When the property was first added to tracking.
        archived_at: When the property was archived (None if not archived).
        staleness_days: Days since last_updated.

    Example:
        lifecycle = PropertyLifecycle(
            full_address="4732 W Davis Rd, Glendale, AZ 85306",
            status=PropertyStatus.ACTIVE,
            last_updated=datetime.now(),
        )
        if lifecycle.is_stale(threshold_days=30):
            print(f"Property {lifecycle.property_hash} is stale")
    """

    full_address: str = Field(
        ...,
        description="Complete property address",
        min_length=1,
    )
    status: PropertyStatus = Field(
        default=PropertyStatus.ACTIVE,
        description="Current lifecycle status",
    )
    last_updated: datetime = Field(
        ...,
        description="When property data was last refreshed",
    )
    created_at: datetime | None = Field(
        default=None,
        description="When property was first added to tracking",
    )
    archived_at: datetime | None = Field(
        default=None,
        description="When property was archived (None if not archived)",
    )
    staleness_days: int = Field(
        default=0,
        ge=0,
        description="Days since last_updated (calculated field)",
    )

    model_config = {"frozen": False, "extra": "ignore"}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def property_hash(self) -> str:
        """Generate property hash from address.

        Uses MD5 hash of lowercase address, truncated to 8 characters.
        This matches the project's standard property identification scheme.

        Returns:
            8-character hex hash of the address.
        """
        return hashlib.md5(self.full_address.lower().encode()).hexdigest()[:8]

    def is_stale(self, threshold_days: int = 30) -> bool:
        """Check if property data is stale.

        Args:
            threshold_days: Number of days after which data is considered stale.
                Defaults to 30 days.

        Returns:
            True if staleness_days exceeds threshold.
        """
        return self.staleness_days > threshold_days

    def calculate_staleness(self, reference_date: datetime | None = None) -> int:
        """Calculate staleness in days from reference date.

        Args:
            reference_date: Date to calculate staleness from.
                Defaults to current datetime.

        Returns:
            Number of days since last_updated.
        """
        reference = reference_date or datetime.now()
        delta = reference - self.last_updated
        return max(0, delta.days)

    def update_staleness(self, reference_date: datetime | None = None) -> None:
        """Update staleness_days field based on current date.

        Modifies the instance in-place.

        Args:
            reference_date: Date to calculate staleness from.
                Defaults to current datetime.
        """
        self.staleness_days = self.calculate_staleness(reference_date)

    def mark_archived(self, archived_at: datetime | None = None) -> None:
        """Mark property as archived.

        Updates status to ARCHIVED and sets archived_at timestamp.

        Args:
            archived_at: When the archival occurred.
                Defaults to current datetime.

        Raises:
            ValueError: If property is already archived.
        """
        if self.status == PropertyStatus.ARCHIVED:
            raise ValueError(f"Property {self.property_hash} is already archived")

        self.status = PropertyStatus.ARCHIVED
        self.archived_at = archived_at or datetime.now()

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage.

        Returns:
            Dictionary representation with ISO-formatted dates.
        """
        return {
            "full_address": self.full_address,
            "property_hash": self.property_hash,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "staleness_days": self.staleness_days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PropertyLifecycle:
        """Create PropertyLifecycle from dictionary.

        Args:
            data: Dictionary with lifecycle data.

        Returns:
            PropertyLifecycle instance.
        """
        return cls(
            full_address=data["full_address"],
            status=PropertyStatus(data.get("status", "active")),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            archived_at=(
                datetime.fromisoformat(data["archived_at"]) if data.get("archived_at") else None
            ),
            staleness_days=data.get("staleness_days", 0),
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"PropertyLifecycle({self.property_hash}, "
            f"status={self.status.value}, "
            f"stale={self.staleness_days}d)"
        )

    def __repr__(self) -> str:
        """Developer representation for debugging."""
        return (
            f"PropertyLifecycle("
            f"full_address={self.full_address!r}, "
            f"status={self.status}, "
            f"last_updated={self.last_updated.isoformat()}, "
            f"staleness_days={self.staleness_days})"
        )


class StalenessReport(BaseModel):
    """Report summarizing staleness analysis results.

    Structured result for CLI consumption with counts, lists, and
    human-readable summary.

    Attributes:
        generated_at: When the report was generated.
        threshold_days: Staleness threshold used for analysis.
        total_properties: Total number of properties analyzed.
        stale_count: Number of properties flagged as stale.
        fresh_count: Number of properties with recent data.
        stale_properties: List of stale PropertyLifecycle records.
        oldest_update: Date of oldest last_updated in dataset.
        newest_update: Date of newest last_updated in dataset.
    """

    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the report was generated",
    )
    threshold_days: int = Field(
        default=30,
        ge=1,
        description="Staleness threshold in days",
    )
    total_properties: int = Field(
        default=0,
        ge=0,
        description="Total properties analyzed",
    )
    stale_count: int = Field(
        default=0,
        ge=0,
        description="Number of stale properties",
    )
    fresh_count: int = Field(
        default=0,
        ge=0,
        description="Number of fresh properties",
    )
    stale_properties: list[PropertyLifecycle] = Field(
        default_factory=list,
        description="List of stale property lifecycle records",
    )
    oldest_update: datetime | None = Field(
        default=None,
        description="Oldest last_updated timestamp",
    )
    newest_update: datetime | None = Field(
        default=None,
        description="Newest last_updated timestamp",
    )

    model_config = {"frozen": False}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def stale_percentage(self) -> float:
        """Calculate percentage of stale properties.

        Returns:
            Percentage (0-100) of properties that are stale.
        """
        if self.total_properties == 0:
            return 0.0
        return (self.stale_count / self.total_properties) * 100

    @property
    def has_stale_properties(self) -> bool:
        """Check if any properties are stale.

        Returns:
            True if stale_count > 0.
        """
        return self.stale_count > 0

    def summary(self) -> str:
        """Generate human-readable summary string.

        Returns:
            Multi-line summary suitable for CLI output.
        """
        lines = [
            "=" * 60,
            "STALENESS REPORT",
            "=" * 60,
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Threshold: {self.threshold_days} days",
            "",
            f"Total Properties: {self.total_properties}",
            f"  Fresh: {self.fresh_count} ({100 - self.stale_percentage:.1f}%)",
            f"  Stale: {self.stale_count} ({self.stale_percentage:.1f}%)",
            "",
        ]

        if self.oldest_update and self.newest_update:
            lines.extend(
                [
                    "Update Range:",
                    f"  Oldest: {self.oldest_update.strftime('%Y-%m-%d')}",
                    f"  Newest: {self.newest_update.strftime('%Y-%m-%d')}",
                    "",
                ]
            )

        if self.stale_properties:
            lines.append("Stale Properties:")
            for prop in sorted(self.stale_properties, key=lambda p: -p.staleness_days):
                lines.append(
                    f"  [{prop.property_hash}] {prop.staleness_days}d stale - {prop.full_address}"
                )

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON output.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "generated_at": self.generated_at.isoformat(),
            "threshold_days": self.threshold_days,
            "total_properties": self.total_properties,
            "stale_count": self.stale_count,
            "fresh_count": self.fresh_count,
            "stale_percentage": self.stale_percentage,
            "stale_properties": [p.to_dict() for p in self.stale_properties],
            "oldest_update": (self.oldest_update.isoformat() if self.oldest_update else None),
            "newest_update": (self.newest_update.isoformat() if self.newest_update else None),
        }


class ArchiveResult(BaseModel):
    """Result of an archive operation.

    Structured result for CLI consumption with success/failure tracking.

    Attributes:
        success: Whether the archive operation succeeded.
        full_address: Address of the archived property.
        property_hash: Hash identifier of the property.
        archive_path: Path where the archive file was created.
        archived_at: Timestamp of archival.
        error_message: Error message if operation failed.
    """

    success: bool = Field(
        ...,
        description="Whether the operation succeeded",
    )
    full_address: str = Field(
        ...,
        description="Address of the property",
    )
    property_hash: str = Field(
        ...,
        description="Hash identifier of the property",
    )
    archive_path: str | None = Field(
        default=None,
        description="Path to created archive file",
    )
    archived_at: datetime | None = Field(
        default=None,
        description="When the archival occurred",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if operation failed",
    )

    model_config = {"frozen": False}

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "success": self.success,
            "full_address": self.full_address,
            "property_hash": self.property_hash,
            "archive_path": self.archive_path,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "error_message": self.error_message,
        }


class BatchArchiveResult(BaseModel):
    """Result of a batch archive operation.

    Aggregates results from archiving multiple properties.

    Attributes:
        total_requested: Number of properties requested for archival.
        success_count: Number of successful archival operations.
        failure_count: Number of failed archival operations.
        results: Individual ArchiveResult for each property.
        started_at: When the batch operation started.
        completed_at: When the batch operation completed.
    """

    total_requested: int = Field(
        default=0,
        ge=0,
        description="Number of properties requested for archival",
    )
    success_count: int = Field(
        default=0,
        ge=0,
        description="Number of successful archivals",
    )
    failure_count: int = Field(
        default=0,
        ge=0,
        description="Number of failed archivals",
    )
    results: list[ArchiveResult] = Field(
        default_factory=list,
        description="Individual archive results",
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="When batch operation started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When batch operation completed",
    )

    model_config = {"frozen": False}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage.

        Returns:
            Percentage (0-100) of successful operations.
        """
        if self.total_requested == 0:
            return 0.0
        return (self.success_count / self.total_requested) * 100

    @property
    def all_succeeded(self) -> bool:
        """Check if all operations succeeded.

        Returns:
            True if failure_count == 0 and total_requested > 0.
        """
        return self.failure_count == 0 and self.total_requested > 0

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Multi-line summary suitable for CLI output.
        """
        duration = ""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            duration = f" (duration: {delta.total_seconds():.1f}s)"

        lines = [
            "=" * 60,
            "BATCH ARCHIVE RESULT",
            "=" * 60,
            f"Started: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}{duration}",
            "",
            f"Total Requested: {self.total_requested}",
            f"  Succeeded: {self.success_count}",
            f"  Failed: {self.failure_count}",
            f"  Success Rate: {self.success_rate:.1f}%",
            "",
        ]

        if self.failure_count > 0:
            lines.append("Failed Properties:")
            for result in self.results:
                if not result.success:
                    lines.append(
                        f"  [{result.property_hash}] {result.full_address}: {result.error_message}"
                    )

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "total_requested": self.total_requested,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at.isoformat(),
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
        }

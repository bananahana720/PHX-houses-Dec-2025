"""Enrichment merge service - business logic for merging county data.

This module contains the core business logic for merging county assessor
parcel data into property enrichment records. It handles:
- Conflict detection and resolution
- Manual research preservation
- Lineage tracking
- Update-only mode (fill missing fields only)
- Freshness timestamps for data staleness detection

The service is designed to be stateless and easily testable through
dependency injection of the LineageTracker.
"""

import logging
from typing import Any

from ...validation.deduplication import compute_property_hash
from ..county_data.models import ParcelData
from ..quality import DataSource, LineageTracker
from .models import ConflictReport, FieldConflict, MergeResult

logger = logging.getLogger(__name__)


class EnrichmentMergeService:
    """Service for merging parcel data into enrichment records.

    Handles the business logic of merging county assessor data into existing
    property enrichment data while preserving manually researched values and
    tracking data lineage.

    Attributes:
        PROTECTED_SOURCES: Set of source values that indicate manual research.
        MERGE_FIELDS: Tuple of field names to merge from parcel data.

    Example:
        service = EnrichmentMergeService(lineage_tracker=tracker)
        result = service.merge_parcel(enrichment, address, parcel)
        if result.success:
            enrichment[address] = result.updated_entry
    """

    # Fields that should never be overwritten if manually researched
    PROTECTED_SOURCES: frozenset[str] = frozenset(
        {
            "manual",
            "manual_research",
            "user",
            "web_research",
        }
    )

    # Fields to merge from parcel data
    MERGE_FIELDS: tuple[str, ...] = (
        "lot_sqft",
        "year_built",
        "garage_spaces",
        "sewer_type",
        "has_pool",
        "tax_annual",
    )

    def __init__(self, lineage_tracker: LineageTracker | None = None) -> None:
        """Initialize merge service.

        Args:
            lineage_tracker: Optional lineage tracker for recording field updates.
                            If None, a default LineageTracker is created to ensure
                            lineage is always tracked.
        """
        # Always ensure lineage tracking is enabled - create default if not provided
        self._lineage_tracker = lineage_tracker or LineageTracker()

    @property
    def lineage_tracker(self) -> LineageTracker:
        """Access the lineage tracker (read-only).

        Returns:
            The LineageTracker instance used by this service.
        """
        return self._lineage_tracker

    def save_lineage(self) -> None:
        """Persist lineage data to disk.

        Call this after batch operations to ensure lineage is saved.
        """
        self._lineage_tracker.save()

    def should_update_field(
        self,
        entry: dict,
        field_name: str,
        new_value: Any,
    ) -> tuple[bool, str]:
        """Determine if a field should be updated.

        Implements conflict detection logic that:
        1. Preserves manually researched values (never overwrites)
        2. Updates missing values (None -> value)
        3. Skips when values match (no change needed)
        4. Updates when county data differs from non-manual existing data

        Args:
            entry: Existing enrichment entry dictionary.
            field_name: Name of field to potentially update.
            new_value: New value from county data.

        Returns:
            Tuple of (should_update: bool, reason: str) explaining the decision.
        """
        existing_value = entry.get(field_name)
        source_field = f"{field_name}_source"
        existing_source = entry.get(source_field, "")

        # Never overwrite manually researched data
        if existing_source in self.PROTECTED_SOURCES:
            logger.warning(
                f"  {field_name}: PRESERVING manual research value {existing_value} "
                f"(source={existing_source}) - county has {new_value}"
            )
            return False, f"Preserving manual research (source={existing_source})"

        # If no existing value, always update
        if existing_value is None:
            return True, "No existing value"

        # If values match, no need to update
        if existing_value == new_value:
            return False, "Values match"

        # Conflict: county differs from existing non-manual value
        # County data is authoritative for non-manual data
        logger.info(
            f"  {field_name}: Updating {existing_value} -> {new_value} "
            f"(existing source: {existing_source or 'unknown'})"
        )
        return True, f"Updating: {existing_value} -> {new_value}"

    def merge_parcel(
        self,
        existing_enrichment: dict,
        full_address: str,
        parcel: ParcelData,
        update_only: bool = False,
    ) -> MergeResult:
        """Merge parcel data into existing enrichment.

        Performs the merge operation, handling conflicts according to the
        update_only mode and preserving manually researched data.

        Args:
            existing_enrichment: Dict of all enrichment entries keyed by address.
            full_address: Property full address (key for lookup/storage).
            parcel: Extracted parcel data from county assessor.
            update_only: If True, only fill missing fields (None values).
                        If False, update all fields using conflict resolution.

        Returns:
            MergeResult containing the updated entry and conflict report.
        """
        entry = existing_enrichment.get(full_address, {}).copy()
        report = ConflictReport()

        # Compute property hash for lineage tracking (always tracked now)
        prop_hash = compute_property_hash(full_address)

        # Get parcel values to merge
        parcel_values = {
            "lot_sqft": parcel.lot_sqft,
            "year_built": parcel.year_built,
            "garage_spaces": parcel.garage_spaces,
            "sewer_type": parcel.sewer_type,
            "has_pool": parcel.has_pool,
            "tax_annual": parcel.tax_annual,
        }

        # Process each field
        for field_name, value in parcel_values.items():
            if value is None:
                continue

            existing_value = entry.get(field_name)

            if update_only:
                # Only set if missing or None
                if existing_value is None:
                    entry[field_name] = value
                    report.new_fields.append(field_name)
                    self._record_lineage(prop_hash, field_name, value, parcel.source)
            else:
                # Apply full conflict resolution
                should_update, reason = self.should_update_field(entry, field_name, value)

                if should_update:
                    entry[field_name] = value
                    if existing_value is None:
                        report.new_fields.append(field_name)
                    else:
                        report.updated.append(
                            FieldConflict(
                                field_name=field_name,
                                existing_value=existing_value,
                                new_value=value,
                                action="updated",
                                reason=reason,
                            )
                        )
                    self._record_lineage(
                        prop_hash, field_name, value, parcel.source, existing_value
                    )
                else:
                    if "manual" in reason.lower():
                        report.preserved_manual.append(
                            FieldConflict(
                                field_name=field_name,
                                existing_value=existing_value,
                                new_value=value,
                                action="preserved",
                                reason=reason,
                            )
                        )
                    else:
                        report.skipped_no_change.append(field_name)

        # Handle coordinates from ArcGIS fallback
        if parcel.latitude and parcel.longitude:
            self._merge_coordinates(entry, parcel, report, update_only, prop_hash)

        # Add freshness timestamps for data staleness detection
        self._add_freshness_timestamps(entry, report)

        return MergeResult(
            full_address=full_address,
            success=True,
            updated_entry=entry,
            conflict_report=report,
        )

    def _merge_coordinates(
        self,
        entry: dict,
        parcel: ParcelData,
        report: ConflictReport,
        update_only: bool,
        prop_hash: str,
    ) -> None:
        """Merge latitude/longitude coordinates from parcel data.

        Coordinates from ArcGIS fallback have slightly lower confidence
        than other county data fields.

        Args:
            entry: Enrichment entry to update (modified in place).
            parcel: Parcel data containing coordinates.
            report: Conflict report to update (modified in place).
            update_only: Whether in update-only mode.
            prop_hash: Property hash for lineage tracking (always required).
        """
        coord_fields = [
            ("latitude", parcel.latitude),
            ("longitude", parcel.longitude),
        ]

        for coord_field, coord_value in coord_fields:
            if coord_value is None:
                continue

            existing_coord = entry.get(coord_field)

            if update_only and existing_coord is not None:
                # In update-only mode, skip if already has value
                continue

            should_update, reason = self.should_update_field(entry, coord_field, coord_value)

            if should_update:
                entry[coord_field] = coord_value
                if existing_coord is None:
                    report.new_fields.append(coord_field)

                # Track lineage with lower confidence for ArcGIS coordinates
                self._record_lineage(
                    prop_hash,
                    coord_field,
                    coord_value,
                    "arcgis",
                    confidence=0.90,
                )

    def _record_lineage(
        self,
        prop_hash: str,
        field_name: str,
        value: Any,
        source: str,
        previous_value: Any = None,
        confidence: float | None = None,
    ) -> None:
        """Record field lineage.

        Lineage tracking is now mandatory - a LineageTracker is always available.

        Args:
            prop_hash: Property hash identifier.
            field_name: Name of the field being recorded.
            value: New value being set.
            source: Source of the data (e.g., "maricopa_assessor").
            previous_value: Previous value if this is an update.
            confidence: Override confidence score. If None, uses DataSource default.
        """
        notes = f"County API source: {source}"
        if previous_value is not None:
            notes += f", updated from {previous_value}"

        # Use provided confidence or DataSource default
        conf = confidence if confidence is not None else DataSource.ASSESSOR_API.default_confidence

        self._lineage_tracker.record_field(
            property_hash=prop_hash,
            field_name=field_name,
            source=DataSource.ASSESSOR_API,
            confidence=conf,
            original_value=value,
            notes=notes,
        )

    def _add_freshness_timestamps(
        self,
        entry: dict,
        report: ConflictReport,
    ) -> None:
        """Add freshness timestamps to track data staleness.

        Records timestamps for:
        - _last_updated: When the entry was last modified
        - _last_county_sync: When county data was last synced

        These metadata fields help identify stale data that may need refreshing.

        Args:
            entry: Enrichment entry to update (modified in place).
            report: Conflict report (used to check if changes were made).
        """
        # Import here to ensure it's available (linter may remove top-level import)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        # Always update _last_county_sync since we ran the county sync
        entry["_last_county_sync"] = now

        # Update _last_updated only if actual changes were made
        has_changes = report.new_fields or report.updated
        if has_changes:
            entry["_last_updated"] = now

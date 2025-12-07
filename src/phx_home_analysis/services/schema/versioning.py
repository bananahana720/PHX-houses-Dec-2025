"""Schema versioning for data files.

This module provides schema version detection, migration, and metadata management
for property data files. It enables reliable schema evolution without breaking
existing data.

Schema Version History:
    1.0.0 - Original schema (implicit, no _schema_metadata field)
            - Basic property fields (full_address, lot_sqft, year_built, etc.)
            - No crime data, flood data, census data, or walkability scores

    2.0.0 - Current schema with all fields
            - Added crime data fields (violent_crime_index, property_crime_index, crime_risk_level)
            - Added flood zone fields (flood_zone, flood_zone_panel, flood_insurance_required)
            - Added walkability scores (walk_score, transit_score, bike_score)
            - Added noise data (noise_score, noise_sources)
            - Added zoning data (zoning_code, zoning_description, zoning_category)
            - Added demographics (census_tract, median_household_income, median_home_value)
            - Added enhanced schools (elementary_rating, middle_rating, high_rating, school_count_1mi)
            - Added _schema_metadata field for version tracking

Usage:
    from phx_home_analysis.services.schema import (
        SchemaVersion,
        SchemaMetadata,
        SchemaMigrator,
    )

    migrator = SchemaMigrator()

    # Detect schema version from data
    version = migrator.get_version(data)

    # Migrate data to target version
    migrated_data = migrator.migrate(data, SchemaVersion.V2_0)

    # Add version metadata to data
    data_with_metadata = migrator.add_version_metadata(data)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SchemaVersion(Enum):
    """Enumeration of data schema versions.

    Each version represents a specific data schema structure. New versions
    should be added when breaking changes are made to the data model.
    """

    V1_0 = "1.0.0"  # Original schema (implicit, no metadata field)
    V2_0 = "2.0.0"  # Current schema with all fields including _schema_metadata

    @classmethod
    def current(cls) -> "SchemaVersion":
        """Get the current (latest) schema version.

        Returns:
            The most recent SchemaVersion enum value.
        """
        return cls.V2_0

    @classmethod
    def from_string(cls, version_str: str) -> "SchemaVersion":
        """Parse a version string into a SchemaVersion enum.

        Args:
            version_str: Version string like "1.0.0" or "2.0.0"

        Returns:
            Corresponding SchemaVersion enum value

        Raises:
            ValueError: If version string doesn't match any known version
        """
        for version in cls:
            if version.value == version_str:
                return version
        raise ValueError(f"Unknown schema version: {version_str}")

    def __lt__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering (allows version < comparison)."""
        versions = list(SchemaVersion)
        return versions.index(self) < versions.index(other)

    def __le__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering (allows version <= comparison)."""
        return self == other or self < other


@dataclass
class SchemaMetadata:
    """Metadata about the schema version of a data file.

    This class tracks the schema version and migration history of data files.

    Attributes:
        version: Current schema version string (e.g., "2.0.0")
        migrated_at: ISO timestamp of last migration (None if never migrated)
        migrated_from: Previous version before last migration (None if never migrated)
        created_at: ISO timestamp when version tracking was added
    """

    version: str
    migrated_at: str | None = None
    migrated_from: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the metadata
        """
        return {
            "version": self.version,
            "migrated_at": self.migrated_at,
            "migrated_from": self.migrated_from,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaMetadata":
        """Create SchemaMetadata from a dictionary.

        Args:
            data: Dictionary with metadata fields

        Returns:
            SchemaMetadata instance
        """
        return cls(
            version=data.get("version", SchemaVersion.V1_0.value),
            migrated_at=data.get("migrated_at"),
            migrated_from=data.get("migrated_from"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


# Fields added in V2.0 schema (used for version detection)
V2_FIELDS: set[str] = {
    # Crime data
    "violent_crime_index",
    "property_crime_index",
    "crime_risk_level",
    # Flood zone
    "flood_zone",
    "flood_zone_panel",
    "flood_insurance_required",
    # Walkability
    "walk_score",
    "transit_score",
    "bike_score",
    # Noise
    "noise_score",
    "noise_sources",
    # Zoning
    "zoning_code",
    "zoning_description",
    "zoning_category",
    # Demographics
    "census_tract",
    "median_household_income",
    "median_home_value",
    # Enhanced schools
    "elementary_rating",
    "middle_rating",
    "high_rating",
    "school_count_1mi",
}


class SchemaMigrator:
    """Handles schema version detection and data migration.

    This class provides methods to:
    - Detect the schema version of existing data
    - Migrate data from older schemas to newer versions
    - Add version metadata to data files

    The migrator supports both list-based (array of property records) and
    dict-based (top-level metadata with properties) data structures.

    Example:
        migrator = SchemaMigrator()

        # Detect version from data
        version = migrator.get_version(data)
        print(f"Data is at version {version.value}")

        # Migrate if needed
        if version < SchemaVersion.current():
            data = migrator.migrate(data, SchemaVersion.current())
    """

    def get_version(self, data: dict | list) -> SchemaVersion:
        """Detect schema version from data structure and content.

        Detection strategy:
        1. Check for explicit _schema_metadata field (V2.0+)
        2. Check for V2.0-specific fields (crime, flood, walkability, etc.)
        3. Default to V1.0 for legacy data

        Args:
            data: The data to analyze (dict or list of property records)

        Returns:
            Detected SchemaVersion
        """
        # Case 1: Data is a dict with _schema_metadata at top level
        if isinstance(data, dict):
            if "_schema_metadata" in data:
                version_str = data["_schema_metadata"].get("version", SchemaVersion.V1_0.value)
                try:
                    return SchemaVersion.from_string(version_str)
                except ValueError:
                    logger.warning(
                        f"Unknown version in _schema_metadata: {version_str}, assuming V1.0"
                    )
                    return SchemaVersion.V1_0

        # Case 2: Data is a list of property records
        if isinstance(data, list) and data:
            # Check first record for _schema_metadata
            first_record = data[0]
            if isinstance(first_record, dict):
                if "_schema_metadata" in first_record:
                    version_str = first_record["_schema_metadata"].get(
                        "version", SchemaVersion.V1_0.value
                    )
                    try:
                        return SchemaVersion.from_string(version_str)
                    except ValueError:
                        logger.warning(
                            f"Unknown version in _schema_metadata: {version_str}, assuming V1.0"
                        )
                        return SchemaVersion.V1_0

                # Check for V2.0 fields in records
                all_fields: set[str] = set()
                for record in data[:10]:  # Check first 10 records for efficiency
                    if isinstance(record, dict):
                        all_fields.update(record.keys())

                # If any V2.0 fields are present, it's likely V2.0 data without metadata
                if all_fields & V2_FIELDS:
                    return SchemaVersion.V2_0

        # Default: assume V1.0 (legacy data without version metadata)
        return SchemaVersion.V1_0

    def migrate(
        self,
        data: dict | list,
        target: SchemaVersion,
    ) -> dict | list:
        """Migrate data to target schema version.

        Applies sequential migrations from the current version to the target.
        Each migration step is idempotent - running it multiple times produces
        the same result.

        Args:
            data: The data to migrate
            target: Target schema version

        Returns:
            Migrated data with updated _schema_metadata

        Raises:
            ValueError: If downgrade is attempted (target < current)
        """
        current = self.get_version(data)

        if current == target:
            logger.info(f"Data already at version {target.value}, no migration needed")
            return data

        if target < current:
            raise ValueError(f"Schema downgrade not supported: {current.value} -> {target.value}")

        logger.info(f"Migrating schema from {current.value} to {target.value}")

        # Apply migrations sequentially
        migrated_data = data
        versions = list(SchemaVersion)
        current_idx = versions.index(current)
        target_idx = versions.index(target)

        for i in range(current_idx, target_idx):
            from_version = versions[i]
            to_version = versions[i + 1]
            migrated_data = self._apply_migration(migrated_data, from_version, to_version)

        # Update metadata after all migrations
        migrated_data = self._update_metadata_after_migration(migrated_data, current, target)

        return migrated_data

    def _apply_migration(
        self,
        data: dict | list,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> dict | list:
        """Apply a single migration step.

        Args:
            data: Data to migrate
            from_version: Source version
            to_version: Target version

        Returns:
            Migrated data
        """
        migration_key = f"{from_version.value}_to_{to_version.value}"

        migrations = {
            "1.0.0_to_2.0.0": self._migrate_v1_to_v2,
        }

        if migration_key in migrations:
            logger.info(f"Applying migration: {migration_key}")
            return migrations[migration_key](data)
        else:
            logger.warning(f"No migration handler for {migration_key}, returning data unchanged")
            return data

    def _migrate_v1_to_v2(self, data: dict | list) -> dict | list:
        """Migrate from V1.0 to V2.0 schema.

        V1.0 -> V2.0 changes:
        - Add _schema_metadata field
        - Initialize new optional fields with None (they're already optional in V2.0)

        This migration is mostly additive - V2.0 adds new optional fields
        that V1.0 data simply doesn't have yet.

        Args:
            data: V1.0 data

        Returns:
            V2.0 data
        """
        if isinstance(data, list):
            # For list format, we don't add fields to individual records
            # since all V2.0 fields are optional
            return data
        elif isinstance(data, dict):
            # For dict format with top-level structure, return as-is
            # The _schema_metadata will be added in _update_metadata_after_migration
            return data

        return data

    def _update_metadata_after_migration(
        self,
        data: dict | list,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> dict | list:
        """Update _schema_metadata after migration.

        Args:
            data: Migrated data
            from_version: Original version
            to_version: New version

        Returns:
            Data with updated _schema_metadata
        """
        now = datetime.now(timezone.utc).isoformat()
        new_metadata = SchemaMetadata(
            version=to_version.value,
            migrated_at=now,
            migrated_from=from_version.value,
            created_at=now,
        )

        if isinstance(data, list) and data:
            # For list format, add metadata to first record
            # (alternative: could add to all records)
            if isinstance(data[0], dict):
                data[0]["_schema_metadata"] = new_metadata.to_dict()
        elif isinstance(data, dict):
            # For dict format, add at top level
            data["_schema_metadata"] = new_metadata.to_dict()

        return data

    def add_version_metadata(
        self,
        data: dict | list,
        version: SchemaVersion | None = None,
    ) -> dict | list:
        """Add _schema_metadata field to data without performing migration.

        Use this to add version tracking to data that is already at the
        correct version but lacks the metadata field.

        Args:
            data: Data to add metadata to
            version: Version to set (defaults to detected version)

        Returns:
            Data with _schema_metadata field added
        """
        if version is None:
            version = self.get_version(data)

        now = datetime.now(timezone.utc).isoformat()
        metadata = SchemaMetadata(
            version=version.value,
            migrated_at=None,
            migrated_from=None,
            created_at=now,
        )

        if isinstance(data, list) and data:
            # For list format, add metadata to first record
            if isinstance(data[0], dict):
                # Don't overwrite existing metadata
                if "_schema_metadata" not in data[0]:
                    data[0]["_schema_metadata"] = metadata.to_dict()
                    logger.info(f"Added _schema_metadata (version {version.value}) to first record")
        elif isinstance(data, dict):
            # For dict format, add at top level
            if "_schema_metadata" not in data:
                data["_schema_metadata"] = metadata.to_dict()
                logger.info(f"Added _schema_metadata (version {version.value}) to top-level dict")

        return data

    def validate_version_compatibility(
        self,
        data: dict | list,
        required_version: SchemaVersion | None = None,
    ) -> tuple[bool, str]:
        """Validate that data meets minimum version requirements.

        Args:
            data: Data to validate
            required_version: Minimum required version (defaults to current)

        Returns:
            Tuple of (is_compatible, message)
        """
        if required_version is None:
            required_version = SchemaVersion.current()

        detected = self.get_version(data)

        if detected < required_version:
            return (
                False,
                f"Data version {detected.value} is below required {required_version.value}. "
                f"Run migration to upgrade.",
            )

        return (True, f"Data version {detected.value} meets requirements")

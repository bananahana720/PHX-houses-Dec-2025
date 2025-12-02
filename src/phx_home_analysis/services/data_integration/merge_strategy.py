"""Merge strategy for combining multi-source property data.

This module provides strategies for merging property data from multiple sources
with well-defined precedence rules and conflict resolution.

Data Source Precedence (highest to lowest):
1. MANUAL (3) - Human-verified enrichment data
2. COUNTY (2) - Maricopa County Assessor API (authoritative for physical attributes)
3. LISTING (1) - Zillow/Redfin listing data
4. DEFAULT (0) - System defaults and inferred values

The merge strategy ensures that more authoritative data sources always win
in case of conflicts, and tracks the source of each field for data lineage.
"""

from enum import IntEnum
from typing import Any

from .field_mapper import FieldMapper


class DataSourcePriority(IntEnum):
    """Data source priority levels (higher = more authoritative).

    Priority determines which source wins when multiple sources provide
    the same field. Manual data always wins, followed by county data,
    then listings, then defaults.
    """

    DEFAULT = 0  # System defaults, inferred values
    LISTING = 1  # Zillow/Redfin listing data
    COUNTY = 2  # Maricopa County Assessor (authoritative for lot, year, garage, etc.)
    MANUAL = 3  # Human-verified enrichment data (highest authority)


class MergeStrategy:
    """Strategy for merging property data from multiple sources.

    Implements field-level merge with source priority tracking and
    conflict resolution based on data source authority.
    """

    def __init__(self, field_mapper: FieldMapper | None = None):
        """Initialize merge strategy.

        Args:
            field_mapper: Optional FieldMapper for field name translation.
                If None, creates a default FieldMapper.
        """
        self.mapper = field_mapper or FieldMapper()

    def merge(
        self,
        sources: dict[str, tuple[dict[str, Any], DataSourcePriority]],
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Merge data from multiple sources with priority-based conflict resolution.

        Args:
            sources: Dictionary mapping source identifiers to (data, priority) tuples.
                Example: {
                    "manual": (manual_data, DataSourcePriority.MANUAL),
                    "county": (county_data, DataSourcePriority.COUNTY),
                    "listing": (listing_data, DataSourcePriority.LISTING),
                }

        Returns:
            Tuple of (merged_data, source_mapping):
                - merged_data: Merged property data with canonical field names
                - source_mapping: Dict mapping each field to its source identifier

        Examples:
            >>> strategy = MergeStrategy()
            >>> manual = {"lot_sqft": 8069, "beds": 4}
            >>> county = {"lot_sqft": 8100, "year_built": 1978}
            >>> listing = {"beds": 3, "price": 475000}
            >>> sources = {
            ...     "manual": (manual, DataSourcePriority.MANUAL),
            ...     "county": (county, DataSourcePriority.COUNTY),
            ...     "listing": (listing, DataSourcePriority.LISTING),
            ... }
            >>> merged, lineage = strategy.merge(sources)
            >>> merged["lot_sqft"]  # Manual wins over county
            8069
            >>> merged["year_built"]  # Only in county
            1978
            >>> merged["beds"]  # Manual wins over listing
            4
            >>> lineage["lot_sqft"]
            'manual'
            >>> lineage["year_built"]
            'county'
        """
        merged: dict[str, Any] = {}
        source_mapping: dict[str, str] = {}

        # Track best value seen for each field (field -> (value, priority, source))
        best_values: dict[str, tuple[Any, DataSourcePriority, str]] = {}

        # Process all sources
        for source_id, (data, priority) in sources.items():
            for field_name, value in data.items():
                # Skip None values (missing data)
                if value is None:
                    continue

                # Get canonical field name
                canonical = self.mapper.to_canonical(field_name, source_id)

                # Check if we should use this value
                if canonical not in best_values:
                    # First time seeing this field
                    best_values[canonical] = (value, priority, source_id)
                else:
                    current_value, current_priority, current_source = best_values[canonical]

                    # Higher priority wins
                    if priority > current_priority:
                        best_values[canonical] = (value, priority, source_id)
                    elif priority == current_priority:
                        # Same priority: prefer non-None, non-empty values
                        if value and not current_value:
                            best_values[canonical] = (value, priority, source_id)

        # Build final merged data and source mapping
        for canonical, (value, _, source_id) in best_values.items():
            merged[canonical] = value
            source_mapping[canonical] = source_id

        return merged, source_mapping

    def merge_with_defaults(
        self,
        sources: dict[str, tuple[dict[str, Any], DataSourcePriority]],
        defaults: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Merge data with default values for missing fields.

        Args:
            sources: Source data as in merge()
            defaults: Default values to use for missing fields

        Returns:
            Tuple of (merged_data, source_mapping)
        """
        # Add defaults with lowest priority
        sources_with_defaults = sources.copy()
        sources_with_defaults["defaults"] = (defaults, DataSourcePriority.DEFAULT)

        return self.merge(sources_with_defaults)


def merge_property_data(
    manual_data: dict[str, Any] | None = None,
    county_data: dict[str, Any] | None = None,
    listing_data: dict[str, Any] | None = None,
    defaults: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Merge property data from multiple sources with priority.

    Convenience function for common merge pattern. Data precedence:
    manual > county > listing > defaults

    Args:
        manual_data: Manual enrichment data (highest priority)
        county_data: Maricopa County Assessor data
        listing_data: Zillow/Redfin listing data
        defaults: Default values for missing fields (lowest priority)

    Returns:
        Tuple of (merged_data, source_mapping):
            - merged_data: Final merged property data with canonical field names
            - source_mapping: Dict showing which source each field came from

    Examples:
        >>> manual = {"lot_sqft": 8069, "sewer_type": "city"}
        >>> county = {"lot_sqft": 8100, "year_built": 1978, "garage_spaces": 2}
        >>> listing = {"beds": 4, "baths": 2.0, "price": 475000}
        >>> defaults = {"hoa_fee": 0, "has_pool": False}
        >>> merged, sources = merge_property_data(manual, county, listing, defaults)
        >>> merged["lot_sqft"]  # Manual wins
        8069
        >>> merged["year_built"]  # From county (only source)
        1978
        >>> merged["beds"]  # From listing (only source)
        4
        >>> merged["hoa_fee"]  # From defaults (not in other sources)
        0
        >>> sources["lot_sqft"]
        'manual'
        >>> sources["year_built"]
        'county'
    """
    strategy = MergeStrategy()
    sources: dict[str, tuple[dict[str, Any], DataSourcePriority]] = {}

    if manual_data:
        sources["manual"] = (manual_data, DataSourcePriority.MANUAL)
    if county_data:
        sources["county"] = (county_data, DataSourcePriority.COUNTY)
    if listing_data:
        sources["listing"] = (listing_data, DataSourcePriority.LISTING)
    if defaults:
        sources["defaults"] = (defaults, DataSourcePriority.DEFAULT)

    return strategy.merge(sources)


def merge_with_lineage_tracking(
    manual_data: dict[str, Any] | None = None,
    county_data: dict[str, Any] | None = None,
    listing_data: dict[str, Any] | None = None,
    existing_lineage: dict[str, dict[str, str]] | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """Merge property data and track detailed data lineage.

    Enhanced merge that tracks not just the source identifier but also
    timestamps and confidence levels for quality assurance.

    Args:
        manual_data: Manual enrichment data
        county_data: County assessor data
        listing_data: Listing data
        existing_lineage: Existing lineage metadata to preserve

    Returns:
        Tuple of (merged_data, lineage_metadata):
            - merged_data: Merged property data
            - lineage_metadata: Detailed lineage for each field including:
                * source: Source identifier
                * priority: Data source priority level
                * timestamp: When data was collected (if available)
    """
    merged, source_mapping = merge_property_data(manual_data, county_data, listing_data)

    # Build detailed lineage metadata
    lineage_metadata: dict[str, dict[str, str]] = {}

    for field, source_id in source_mapping.items():
        lineage_metadata[field] = {
            "source": source_id,
            "priority": str(_get_priority_for_source(source_id).value),
        }

        # Preserve existing lineage timestamps if available
        if existing_lineage and field in existing_lineage:
            if "timestamp" in existing_lineage[field]:
                lineage_metadata[field]["timestamp"] = existing_lineage[field]["timestamp"]

    return merged, lineage_metadata


def _get_priority_for_source(source_id: str) -> DataSourcePriority:
    """Get priority level for a source identifier.

    Args:
        source_id: Source identifier (manual, county, listing, defaults)

    Returns:
        DataSourcePriority enum value
    """
    priority_map = {
        "manual": DataSourcePriority.MANUAL,
        "county": DataSourcePriority.COUNTY,
        "listing": DataSourcePriority.LISTING,
        "defaults": DataSourcePriority.DEFAULT,
    }
    return priority_map.get(source_id, DataSourcePriority.DEFAULT)

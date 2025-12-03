"""Staleness detection service for property data freshness monitoring.

This module provides the StalenessDetector class for analyzing property data
freshness, identifying stale records, and generating staleness reports.

Staleness Definition:
    A property is considered stale if its last_updated timestamp is older
    than the configured threshold (default: 30 days).

Usage:
    from phx_home_analysis.services.lifecycle import StalenessDetector

    detector = StalenessDetector()
    report = detector.analyze()

    if report.has_stale_properties:
        print(report.summary())
        for prop in report.stale_properties:
            print(f"  {prop.full_address}: {prop.staleness_days} days stale")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import PropertyLifecycle, PropertyStatus, StalenessReport

logger = logging.getLogger(__name__)

# Default staleness threshold in days
DEFAULT_STALENESS_THRESHOLD = 30

# Default path to enrichment data
DEFAULT_ENRICHMENT_PATH = Path("data/enrichment_data.json")


class StalenessDetector:
    """Service for detecting stale property data.

    Analyzes property enrichment data to identify records that haven't been
    updated within the configured threshold period.

    Attributes:
        enrichment_path: Path to enrichment_data.json file.
        threshold_days: Number of days after which data is considered stale.

    Example:
        # Basic usage
        detector = StalenessDetector()
        report = detector.analyze()
        print(report.summary())

        # Custom threshold
        detector = StalenessDetector(threshold_days=14)
        report = detector.analyze()

        # Custom data path (for testing)
        detector = StalenessDetector(
            enrichment_path=Path("test_data/enrichment.json"),
            threshold_days=7
        )
    """

    def __init__(
        self,
        enrichment_path: Path | str | None = None,
        threshold_days: int = DEFAULT_STALENESS_THRESHOLD,
    ) -> None:
        """Initialize the staleness detector.

        Args:
            enrichment_path: Path to enrichment_data.json file.
                Defaults to data/enrichment_data.json.
            threshold_days: Number of days after which data is considered stale.
                Defaults to 30 days.

        Raises:
            ValueError: If threshold_days is less than 1.
        """
        if threshold_days < 1:
            raise ValueError(f"threshold_days must be >= 1, got {threshold_days}")

        self.enrichment_path = Path(enrichment_path) if enrichment_path else DEFAULT_ENRICHMENT_PATH
        self.threshold_days = threshold_days

        logger.debug(
            f"StalenessDetector initialized: path={self.enrichment_path}, "
            f"threshold={self.threshold_days}d"
        )

    def _load_enrichment_data(self) -> list[dict[str, Any]]:
        """Load property data from enrichment_data.json.

        Returns:
            List of property dictionaries.

        Raises:
            FileNotFoundError: If enrichment file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
        """
        if not self.enrichment_path.exists():
            raise FileNotFoundError(f"Enrichment file not found: {self.enrichment_path}")

        with open(self.enrichment_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(
                f"Expected list of properties, got {type(data).__name__}"
            )

        logger.debug(f"Loaded {len(data)} properties from {self.enrichment_path}")
        return data

    def _extract_last_updated(self, property_data: dict[str, Any]) -> datetime | None:
        """Extract last_updated timestamp from property data.

        Checks multiple possible field names for the update timestamp.

        Args:
            property_data: Dictionary containing property data.

        Returns:
            Parsed datetime or None if not found/invalid.
        """
        # Check common timestamp field names
        timestamp_fields = [
            "last_updated",
            "updated_at",
            "interior_assessment_date",
            "county_data_updated",
            "listing_updated",
        ]

        for field in timestamp_fields:
            value = property_data.get(field)
            if value:
                try:
                    if isinstance(value, datetime):
                        return value
                    return datetime.fromisoformat(str(value))
                except (ValueError, TypeError):
                    continue

        return None

    def _property_to_lifecycle(
        self,
        property_data: dict[str, Any],
        reference_date: datetime,
    ) -> PropertyLifecycle | None:
        """Convert property data dict to PropertyLifecycle model.

        Args:
            property_data: Raw property dictionary.
            reference_date: Date to calculate staleness against.

        Returns:
            PropertyLifecycle instance or None if conversion fails.
        """
        full_address = property_data.get("full_address")
        if not full_address:
            logger.warning("Property missing full_address, skipping")
            return None

        last_updated = self._extract_last_updated(property_data)
        if not last_updated:
            # If no timestamp, consider it stale from project start
            from datetime import timezone
            last_updated = datetime(2025, 1, 1, tzinfo=timezone.utc)
            logger.debug(f"No timestamp for {full_address}, using default")

        # Determine status from data if available
        status = PropertyStatus.ACTIVE
        if property_data.get("status"):
            try:
                status = PropertyStatus(property_data["status"])
            except ValueError:
                pass

        lifecycle = PropertyLifecycle(
            full_address=full_address,
            status=status,
            last_updated=last_updated,
            created_at=property_data.get("created_at"),
        )

        # Calculate staleness
        lifecycle.update_staleness(reference_date)

        return lifecycle

    def analyze(
        self,
        reference_date: datetime | None = None,
    ) -> StalenessReport:
        """Analyze enrichment data for stale properties.

        Loads all properties from enrichment_data.json, calculates staleness
        for each, and generates a comprehensive report.

        Args:
            reference_date: Date to calculate staleness against.
                Defaults to current datetime (UTC).

        Returns:
            StalenessReport with analysis results.

        Raises:
            FileNotFoundError: If enrichment file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
        """
        from datetime import timezone
        reference_date = reference_date or datetime.now(timezone.utc)

        logger.info(
            f"Analyzing staleness (threshold={self.threshold_days}d, "
            f"reference={reference_date.date()})"
        )

        # Load and convert data
        raw_data = self._load_enrichment_data()
        lifecycles: list[PropertyLifecycle] = []

        for prop_data in raw_data:
            lifecycle = self._property_to_lifecycle(prop_data, reference_date)
            if lifecycle:
                lifecycles.append(lifecycle)

        if not lifecycles:
            logger.warning("No valid properties found in enrichment data")
            return StalenessReport(
                threshold_days=self.threshold_days,
                generated_at=datetime.now(),
            )

        # Separate stale and fresh
        stale_properties = [
            lc for lc in lifecycles
            if lc.is_stale(self.threshold_days)
        ]
        fresh_count = len(lifecycles) - len(stale_properties)

        # Find date range
        all_dates = [lc.last_updated for lc in lifecycles]
        oldest_update = min(all_dates) if all_dates else None
        newest_update = max(all_dates) if all_dates else None

        # Build report
        report = StalenessReport(
            generated_at=datetime.now(),
            threshold_days=self.threshold_days,
            total_properties=len(lifecycles),
            stale_count=len(stale_properties),
            fresh_count=fresh_count,
            stale_properties=stale_properties,
            oldest_update=oldest_update,
            newest_update=newest_update,
        )

        logger.info(
            f"Staleness analysis complete: {report.stale_count}/{report.total_properties} "
            f"stale ({report.stale_percentage:.1f}%)"
        )

        return report

    def get_stale_addresses(
        self,
        reference_date: datetime | None = None,
    ) -> list[str]:
        """Get list of stale property addresses.

        Convenience method for getting just the addresses without full report.

        Args:
            reference_date: Date to calculate staleness against.
                Defaults to current datetime.

        Returns:
            List of full_address strings for stale properties.
        """
        report = self.analyze(reference_date)
        return [prop.full_address for prop in report.stale_properties]

    def get_stale_hashes(
        self,
        reference_date: datetime | None = None,
    ) -> list[str]:
        """Get list of stale property hashes.

        Convenience method for getting property hashes for archival.

        Args:
            reference_date: Date to calculate staleness against.
                Defaults to current datetime.

        Returns:
            List of property_hash strings for stale properties.
        """
        report = self.analyze(reference_date)
        return [prop.property_hash for prop in report.stale_properties]

    def check_property_staleness(
        self,
        full_address: str,
        reference_date: datetime | None = None,
    ) -> PropertyLifecycle | None:
        """Check staleness for a specific property.

        Args:
            full_address: Address of property to check.
            reference_date: Date to calculate staleness against.

        Returns:
            PropertyLifecycle if found, None otherwise.
        """
        from datetime import timezone as tz
        reference_date = reference_date or datetime.now(tz.utc)

        try:
            raw_data = self._load_enrichment_data()
        except FileNotFoundError:
            logger.error("Enrichment file not found")
            return None

        # Find matching property
        for prop_data in raw_data:
            if prop_data.get("full_address") == full_address:
                return self._property_to_lifecycle(prop_data, reference_date)

        logger.debug(f"Property not found: {full_address}")
        return None

    def summary(self, reference_date: datetime | None = None) -> str:
        """Generate human-readable staleness summary.

        Convenience method for CLI output.

        Args:
            reference_date: Date to calculate staleness against.

        Returns:
            Formatted summary string.
        """
        try:
            report = self.analyze(reference_date)
            return report.summary()
        except FileNotFoundError as e:
            return f"Error: {e}"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in enrichment file: {e}"

    def __str__(self) -> str:
        """String representation."""
        return (
            f"StalenessDetector(path={self.enrichment_path}, "
            f"threshold={self.threshold_days}d)"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"StalenessDetector("
            f"enrichment_path={self.enrichment_path!r}, "
            f"threshold_days={self.threshold_days})"
        )

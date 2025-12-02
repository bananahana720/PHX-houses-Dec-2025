"""Data lineage tracking for property fields.

This module provides the LineageTracker class for recording and retrieving
the provenance of property field values across the analysis pipeline.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import DataSource, FieldLineage

logger = logging.getLogger(__name__)


class LineageTracker:
    """Track data lineage for property fields.

    Maintains a record of where each property field value originated,
    when it was updated, and the confidence level associated with it.

    Supports persistence to JSON for crash recovery and auditing.

    Attributes:
        lineage_file: Path to JSON file for persistence.

    Example:
        tracker = LineageTracker()
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
            original_value=9500
        )
        lineage = tracker.get_field_lineage("ef7cd95f", "lot_sqft")
    """

    def __init__(self, lineage_file: Optional[Path] = None) -> None:
        """Initialize the lineage tracker.

        Args:
            lineage_file: Path to JSON file for persistence.
                         Defaults to data/field_lineage.json.
        """
        self.lineage_file = lineage_file or Path("data/field_lineage.json")
        self._lineage: dict[str, dict[str, FieldLineage]] = {}
        self._load()

    def _load(self) -> None:
        """Load existing lineage data from file."""
        if not self.lineage_file.exists():
            logger.debug(f"Lineage file not found: {self.lineage_file}")
            return

        try:
            with open(self.lineage_file, encoding="utf-8") as f:
                data = json.load(f)

            for property_hash, fields in data.items():
                self._lineage[property_hash] = {}
                for field_name, lineage_data in fields.items():
                    try:
                        self._lineage[property_hash][field_name] = FieldLineage.from_dict(
                            lineage_data
                        )
                    except (KeyError, ValueError) as e:
                        logger.warning(
                            f"Invalid lineage data for {property_hash}.{field_name}: {e}"
                        )

            logger.info(f"Loaded lineage for {len(self._lineage)} properties")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lineage file: {e}")
        except OSError as e:
            logger.error(f"Failed to read lineage file: {e}")

    def save(self) -> None:
        """Persist lineage data to file.

        Creates parent directories if they don't exist.
        """
        # Ensure parent directory exists
        self.lineage_file.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to JSON-compatible format
        data = {}
        for property_hash, fields in self._lineage.items():
            data[property_hash] = {}
            for field_name, lineage in fields.items():
                data[property_hash][field_name] = lineage.to_dict()

        try:
            with open(self.lineage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved lineage for {len(self._lineage)} properties")
        except OSError as e:
            logger.error(f"Failed to write lineage file: {e}")
            raise

    def record_field(
        self,
        property_hash: str,
        field_name: str,
        source: DataSource,
        confidence: float,
        original_value: Any = None,
        notes: Optional[str] = None,
    ) -> FieldLineage:
        """Record lineage for a field update.

        Args:
            property_hash: MD5 hash of property address (first 8 chars).
            field_name: Name of the field being recorded.
            source: Data source that provided the value.
            confidence: Confidence score (0.0-1.0).
            original_value: The raw value before transformation.
            notes: Optional notes about the data origin.

        Returns:
            The created FieldLineage object.
        """
        lineage = FieldLineage(
            field_name=field_name,
            source=source,
            confidence=confidence,
            updated_at=datetime.now(),
            original_value=original_value,
            notes=notes,
        )

        if property_hash not in self._lineage:
            self._lineage[property_hash] = {}

        self._lineage[property_hash][field_name] = lineage

        logger.debug(
            f"Recorded lineage: {property_hash}.{field_name} "
            f"from {source.value} (confidence: {confidence:.2f})"
        )

        return lineage

    def record_batch(
        self,
        property_hash: str,
        source: DataSource,
        fields: dict[str, Any],
        confidence: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> list[FieldLineage]:
        """Record lineage for multiple fields from the same source.

        Convenience method for recording many fields at once.

        Args:
            property_hash: MD5 hash of property address.
            source: Data source for all fields.
            fields: Dictionary mapping field names to values.
            confidence: Confidence score (uses source default if not provided).
            notes: Optional notes about the data origin.

        Returns:
            List of created FieldLineage objects.
        """
        if confidence is None:
            confidence = source.default_confidence

        lineages = []
        for field_name, value in fields.items():
            lineage = self.record_field(
                property_hash=property_hash,
                field_name=field_name,
                source=source,
                confidence=confidence,
                original_value=value,
                notes=notes,
            )
            lineages.append(lineage)

        return lineages

    def get_field_lineage(
        self, property_hash: str, field_name: str
    ) -> Optional[FieldLineage]:
        """Get lineage for a specific field.

        Args:
            property_hash: MD5 hash of property address.
            field_name: Name of the field.

        Returns:
            FieldLineage if found, None otherwise.
        """
        return self._lineage.get(property_hash, {}).get(field_name)

    def get_property_lineage(self, property_hash: str) -> dict[str, FieldLineage]:
        """Get all lineage records for a property.

        Args:
            property_hash: MD5 hash of property address.

        Returns:
            Dictionary mapping field names to FieldLineage objects.
        """
        return self._lineage.get(property_hash, {}).copy()

    def get_field_confidence(
        self, property_hash: str, field_name: str
    ) -> Optional[float]:
        """Get confidence score for a specific field.

        Args:
            property_hash: MD5 hash of property address.
            field_name: Name of the field.

        Returns:
            Confidence score (0.0-1.0) if found, None otherwise.
        """
        lineage = self.get_field_lineage(property_hash, field_name)
        return lineage.confidence if lineage else None

    def get_all_confidences(self, property_hash: str) -> dict[str, float]:
        """Get all confidence scores for a property.

        Args:
            property_hash: MD5 hash of property address.

        Returns:
            Dictionary mapping field names to confidence scores.
        """
        return {
            field_name: lineage.confidence
            for field_name, lineage in self._lineage.get(property_hash, {}).items()
        }

    def get_low_confidence_fields(
        self, property_hash: str, threshold: float = 0.8
    ) -> list[str]:
        """Get fields below confidence threshold.

        Args:
            property_hash: MD5 hash of property address.
            threshold: Confidence threshold (default 0.8).

        Returns:
            List of field names with confidence below threshold.
        """
        return [
            field_name
            for field_name, lineage in self._lineage.get(property_hash, {}).items()
            if lineage.confidence < threshold
        ]

    def clear_property(self, property_hash: str) -> None:
        """Clear all lineage records for a property.

        Args:
            property_hash: MD5 hash of property address.
        """
        if property_hash in self._lineage:
            del self._lineage[property_hash]
            logger.debug(f"Cleared lineage for property {property_hash}")

    def property_count(self) -> int:
        """Get number of properties with lineage records.

        Returns:
            Count of tracked properties.
        """
        return len(self._lineage)

    def field_count(self, property_hash: str) -> int:
        """Get number of tracked fields for a property.

        Args:
            property_hash: MD5 hash of property address.

        Returns:
            Count of tracked fields.
        """
        return len(self._lineage.get(property_hash, {}))

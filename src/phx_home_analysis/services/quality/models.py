"""Data models for quality metrics and data lineage tracking.

This module defines the core data structures for tracking data quality,
field-level lineage, and confidence scores across the property analysis pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DataSource(Enum):
    """Source of property data.

    Tracks where each piece of data originated for lineage tracking
    and confidence assessment.
    """

    CSV = "csv"
    ASSESSOR_API = "assessor_api"
    WEB_SCRAPE = "web_scrape"
    AI_INFERENCE = "ai_inference"
    MANUAL = "manual"
    DEFAULT = "default"
    BESTPLACES = "bestplaces"
    AREAVIBES = "areavibes"
    WALKSCORE = "walkscore"
    FEMA = "fema"
    GREATSCHOOLS = "greatschools"
    HOWLOUD = "howloud"
    CENSUS = "census"
    MARICOPA_GIS = "maricopa_gis"
    ZILLOW = "zillow"
    REDFIN = "redfin"
    GOOGLE_MAPS = "google_maps"
    IMAGE_ASSESSMENT = "image_assessment"

    @property
    def default_confidence(self) -> float:
        """Get default confidence score for this data source.

        Returns:
            Float from 0.0 to 1.0 indicating typical confidence level.
        """
        confidence_map = {
            DataSource.CSV: 0.90,  # User-provided listings, high trust
            DataSource.ASSESSOR_API: 0.95,  # Official county records
            DataSource.WEB_SCRAPE: 0.75,  # Web data may be stale/incorrect
            DataSource.AI_INFERENCE: 0.70,  # AI estimates have uncertainty
            DataSource.MANUAL: 0.85,  # Human inspection, subject to error
            DataSource.DEFAULT: 0.50,  # Default/assumed values
            DataSource.BESTPLACES: 0.80,  # Crime data aggregator
            DataSource.AREAVIBES: 0.80,  # Crime/neighborhood data
            DataSource.WALKSCORE: 0.90,  # Walk/transit scores (proprietary algorithm)
            DataSource.FEMA: 0.95,  # Official flood zone data
            DataSource.GREATSCHOOLS: 0.90,  # School ratings (updated from 0.85)
            DataSource.HOWLOUD: 0.75,  # Noise score estimates
            DataSource.CENSUS: 0.95,  # Official census data
            DataSource.MARICOPA_GIS: 0.95,  # Official county GIS data
            DataSource.ZILLOW: 0.85,  # Zillow/Redfin scraping
            DataSource.REDFIN: 0.85,  # Zillow/Redfin scraping
            DataSource.GOOGLE_MAPS: 0.90,  # Google Maps API
            DataSource.IMAGE_ASSESSMENT: 0.80,  # AI image analysis
        }
        return confidence_map.get(self, 0.5)


@dataclass
class FieldLineage:
    """Track lineage for a single property field.

    Records where a field value came from, when it was updated,
    and how confident we are in its accuracy.

    Attributes:
        field_name: Name of the property field.
        source: Data source that provided the value.
        confidence: Confidence score from 0.0 to 1.0.
        updated_at: When the field was last updated.
        original_value: The value before any transformations.
        notes: Optional notes about the data origin.
    """

    field_name: str
    source: DataSource
    confidence: float
    updated_at: datetime
    original_value: Any | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize field lineage data."""
        # Ensure confidence is in valid range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        # Convert string source to enum if needed
        if isinstance(self.source, str):
            self.source = DataSource(self.source.lower())

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage.

        Returns:
            Dictionary representation of field lineage.
        """
        return {
            "field_name": self.field_name,
            "source": self.source.value,
            "confidence": self.confidence,
            "updated_at": self.updated_at.isoformat(),
            "original_value": self.original_value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FieldLineage":
        """Create FieldLineage from dictionary.

        Args:
            data: Dictionary with field lineage data.

        Returns:
            FieldLineage instance.
        """
        return cls(
            field_name=data["field_name"],
            source=DataSource(data["source"]),
            confidence=data["confidence"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            original_value=data.get("original_value"),
            notes=data.get("notes"),
        )


@dataclass
class QualityScore:
    """Quality assessment for a property's data completeness and confidence.

    Calculates overall quality based on field completeness and confidence levels.

    Attributes:
        completeness: Percentage of required fields present (0.0-1.0).
        high_confidence_pct: Percentage of fields with high confidence (0.0-1.0).
        overall_score: Weighted combination of completeness and confidence.
        missing_fields: List of required fields that are missing.
        low_confidence_fields: List of fields below confidence threshold.
    """

    completeness: float
    high_confidence_pct: float
    overall_score: float
    missing_fields: list[str] = field(default_factory=list)
    low_confidence_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate quality score values."""
        for attr in ["completeness", "high_confidence_pct", "overall_score"]:
            value = getattr(self, attr)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{attr} must be between 0.0 and 1.0, got {value}")

    @property
    def is_high_quality(self) -> bool:
        """Check if quality score meets high quality threshold (>= 0.95).

        Returns:
            True if overall score is at least 95%.
        """
        return self.overall_score >= 0.95

    @property
    def quality_tier(self) -> str:
        """Get quality tier classification.

        Returns:
            'excellent' (>=0.95), 'good' (>=0.80), 'fair' (>=0.60), or 'poor'.
        """
        if self.overall_score >= 0.95:
            return "excellent"
        elif self.overall_score >= 0.80:
            return "good"
        elif self.overall_score >= 0.60:
            return "fair"
        else:
            return "poor"

    def to_dict(self) -> dict:
        """Serialize to dictionary.

        Returns:
            Dictionary representation of quality score.
        """
        return {
            "completeness": self.completeness,
            "high_confidence_pct": self.high_confidence_pct,
            "overall_score": self.overall_score,
            "missing_fields": self.missing_fields,
            "low_confidence_fields": self.low_confidence_fields,
            "quality_tier": self.quality_tier,
        }

"""Pydantic models for school ratings API responses.

Models support both SchoolDigger API and Google Places fallback patterns.
All models include to_enrichment_dict() for enrichment_data.json integration.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SchoolLevel(str, Enum):
    """School level classification."""

    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH = "high"
    UNKNOWN = "unknown"


class SchoolResult(BaseModel):
    """Individual school result with ratings and location.

    Represents a single school from SchoolDigger API or Google Places search.
    Distance is calculated via haversine formula from property coordinates.
    """

    name: str = Field(..., description="School name")
    address: str | None = Field(None, description="School address")
    latitude: float = Field(..., description="School latitude")
    longitude: float = Field(..., description="School longitude")
    rating: float | None = Field(
        None, ge=0.0, le=10.0, description="School rating (0-10 scale), None if unavailable"
    )
    level: SchoolLevel = Field(..., description="School level (elementary/middle/high)")
    distance_meters: float = Field(..., ge=0.0, description="Distance from property in meters")
    is_assigned: bool = Field(
        default=False, description="True if this is the assigned school (boundary-based)"
    )
    confidence: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Data confidence (0.95 API, 0.5 fallback)"
    )
    source: str = Field(
        default="schooldigger_api", description="Data source (schooldigger_api, google_places_fallback)"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with school data for JSON serialization
        """
        return {
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "rating": self.rating,
            "level": self.level.value,
            "distance_meters": self.distance_meters,
            "is_assigned": self.is_assigned,
            "confidence": self.confidence,
            "source": self.source,
        }


class AssignedSchoolsResult(BaseModel):
    """Assigned schools (elementary, middle, high) with composite rating.

    Contains one school per level with Arizona-weighted composite score.
    Used for enrichment_data.json school_data section.
    """

    elementary: SchoolResult | None = Field(None, description="Assigned elementary school")
    middle: SchoolResult | None = Field(None, description="Assigned middle school")
    high: SchoolResult | None = Field(None, description="Assigned high school")
    composite_rating: float | None = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Arizona-weighted composite: (elem×0.3) + (mid×0.3) + (high×0.4)",
    )
    confidence: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Data confidence (0.95 API, 0.5 fallback)"
    )
    source: str = Field(
        default="schooldigger_api", description="Data source (schooldigger_api, google_places_fallback)"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with elementary, middle, high sections plus composite metadata
        """
        result = {
            "elementary": self.elementary.to_enrichment_dict() if self.elementary else None,
            "middle": self.middle.to_enrichment_dict() if self.middle else None,
            "high": self.high.to_enrichment_dict() if self.high else None,
            "composite_rating": self.composite_rating,
            "schools_confidence": self.confidence,
            "schools_source": self.source,
        }
        return result


class SchoolFallbackResult(BaseModel):
    """Google Places fallback result (names only, no ratings).

    Used when SchoolDigger API fails. Provides school names and count
    but no quality ratings. Lower confidence reflects missing rating data.
    """

    school_names: list[str] = Field(default_factory=list, description="List of school names found")
    school_count: int = Field(default=0, ge=0, description="Number of schools found")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Low confidence (0.5) - names only, no ratings"
    )
    source: str = Field(
        default="google_places_fallback", description="Data source (always google_places_fallback)"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with fallback metadata and school names list
        """
        return {
            "elementary": None,
            "middle": None,
            "high": None,
            "composite_rating": None,
            "schools_confidence": self.confidence,
            "schools_source": self.source,
            "school_names": self.school_names,
            "school_count": self.school_count,
        }


__all__ = [
    "SchoolLevel",
    "SchoolResult",
    "AssignedSchoolsResult",
    "SchoolFallbackResult",
]

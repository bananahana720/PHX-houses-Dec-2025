"""Data models for air quality assessment.

AQI (Air Quality Index) Scale:
    0-50:    Good (Green) - Air quality is satisfactory
    51-100:  Moderate (Yellow) - Acceptable for most
    101-150: Unhealthy for Sensitive Groups (Orange)
    151-200: Unhealthy (Red) - Everyone may experience effects
    201-300: Very Unhealthy (Purple) - Health alert
    301-500: Hazardous (Maroon) - Emergency conditions

Data Source: EPA AirNow API (https://www.airnowapi.org)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AQICategory(Enum):
    """EPA Air Quality Index categories."""

    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"
    UNKNOWN = "Unknown"

    @classmethod
    def from_aqi(cls, aqi: int | None) -> "AQICategory":
        """Determine category from AQI value."""
        if aqi is None:
            return cls.UNKNOWN
        if aqi <= 50:
            return cls.GOOD
        if aqi <= 100:
            return cls.MODERATE
        if aqi <= 150:
            return cls.UNHEALTHY_SENSITIVE
        if aqi <= 200:
            return cls.UNHEALTHY
        if aqi <= 300:
            return cls.VERY_UNHEALTHY
        return cls.HAZARDOUS


@dataclass
class AirQualityData:
    """Air quality assessment for a location.

    Attributes:
        aqi_value: Air Quality Index (0-500 scale)
        aqi_category: Human-readable category
        primary_pollutant: Main pollutant (PM2.5, O3, PM10, CO, NO2, SO2)
        reporting_area: EPA reporting area name
        source: Data source identifier
        extracted_at: Timestamp of extraction
        latitude: Extraction latitude
        longitude: Extraction longitude
    """

    aqi_value: int | None = None
    aqi_category: str | None = None
    primary_pollutant: str | None = None
    reporting_area: str | None = None
    source: str = "epa_airnow"
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    latitude: float | None = None
    longitude: float | None = None

    @classmethod
    def from_api_response(
        cls,
        aqi: int | None,
        pollutant: str | None = None,
        area: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> "AirQualityData":
        """Create AirQualityData from API response.

        Args:
            aqi: AQI value (0-500)
            pollutant: Primary pollutant code
            area: Reporting area name
            lat: Latitude
            lng: Longitude

        Returns:
            AirQualityData instance with derived category
        """
        category = AQICategory.from_aqi(aqi)
        return cls(
            aqi_value=aqi,
            aqi_category=category.value,
            primary_pollutant=pollutant,
            reporting_area=area,
            latitude=lat,
            longitude=lng,
            extracted_at=datetime.now(),
        )

    @property
    def is_healthy(self) -> bool:
        """Check if air quality is healthy (AQI <= 100).

        Returns:
            True if Good or Moderate, False otherwise
        """
        return self.aqi_value is not None and self.aqi_value <= 100

    @property
    def health_concern_level(self) -> str:
        """Get health concern level for Arizona context.

        Arizona-specific considerations:
        - Summer ozone spikes (100-150 common)
        - Dust storms can spike PM10 (200+)
        - Wildfire smoke affects PM2.5

        Returns:
            Health concern description
        """
        if self.aqi_value is None:
            return "Unknown"
        if self.aqi_value <= 50:
            return "None"
        if self.aqi_value <= 100:
            return "Low"
        if self.aqi_value <= 150:
            return "Moderate - sensitive groups affected"
        if self.aqi_value <= 200:
            return "High - limit outdoor activity"
        return "Severe - avoid outdoor exposure"

    @property
    def score_modifier(self) -> float:
        """Calculate score modifier for property scoring (0-1 scale).

        Maps AQI to a 0-1 scale where:
        - 0-50 AQI = 1.0 (full points)
        - 51-100 = 0.8
        - 101-150 = 0.5
        - 151+ = 0.2

        Returns:
            Score modifier (0-1)
        """
        if self.aqi_value is None:
            return 0.5  # Neutral if unknown
        if self.aqi_value <= 50:
            return 1.0
        if self.aqi_value <= 100:
            return 0.8
        if self.aqi_value <= 150:
            return 0.5
        return 0.2

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for merging into enrichment_data.json.

        Returns:
            Dictionary with air quality fields for enrichment
        """
        return {
            "air_quality_aqi": self.aqi_value,
            "air_quality_category": self.aqi_category,
            "air_quality_pollutant": self.primary_pollutant,
            "air_quality_area": self.reporting_area,
            "air_quality_source": self.source,
        }

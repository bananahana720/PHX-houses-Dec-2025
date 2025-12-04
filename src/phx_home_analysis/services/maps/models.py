"""Google Maps API data models.

Pydantic models for geocoding, distance calculation, place search, and orientation.
All models include to_enrichment_dict() for enrichment_data.json integration.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Orientation(str, Enum):
    """Backyard orientation enum for Arizona-optimized scoring."""

    NORTH = "N"
    EAST = "E"
    SOUTH = "S"
    WEST = "W"


class GeocodeResult(BaseModel):
    """Geocoding API result with lat/lng and formatted address.

    Fields:
        latitude: Decimal latitude
        longitude: Decimal longitude
        formatted_address: Full formatted address from Google
        confidence: Data quality score (0.95 for Google Maps geocoding)
        source: Data source identifier

    Example:
        result = GeocodeResult(
            latitude=33.4484,
            longitude=-112.0740,
            formatted_address="123 Main St, Phoenix, AZ 85001, USA",
        )
    """

    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    formatted_address: str = Field(..., description="Full formatted address from Google")
    confidence: float = Field(default=0.95, description="Data quality confidence score")
    source: str = Field(
        default="google_maps_geocoding", description="Data source identifier"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with keys: latitude, longitude, formatted_address,
            geocode_confidence, geocode_source
        """
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "formatted_address": self.formatted_address,
            "geocode_confidence": self.confidence,
            "geocode_source": self.source,
        }


class DistanceResult(BaseModel):
    """Distance Matrix API result for work, supermarket, and park distances.

    Fields:
        work_distance_meters: Distance to downtown Phoenix work location
        supermarket_distance_meters: Distance to nearest supermarket
        park_distance_meters: Distance to nearest park
        confidence: Data quality score (0.95 for Google Maps distance matrix)
        source: Data source identifier

    Example:
        result = DistanceResult(
            work_distance_meters=8500,
            supermarket_distance_meters=1200,
            park_distance_meters=800,
        )
    """

    work_distance_meters: int | None = Field(
        default=None, description="Distance to work location in meters"
    )
    supermarket_distance_meters: int | None = Field(
        default=None, description="Distance to nearest supermarket in meters"
    )
    park_distance_meters: int | None = Field(
        default=None, description="Distance to nearest park in meters"
    )
    confidence: float = Field(default=0.95, description="Data quality confidence score")
    source: str = Field(
        default="google_maps_distance", description="Data source identifier"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with keys: work_distance_meters, supermarket_distance_meters,
            park_distance_meters, distance_confidence, distance_source
        """
        return {
            "work_distance_meters": self.work_distance_meters,
            "supermarket_distance_meters": self.supermarket_distance_meters,
            "park_distance_meters": self.park_distance_meters,
            "distance_confidence": self.confidence,
            "distance_source": self.source,
        }


class PlaceResult(BaseModel):
    """Places API nearby search result for POI (supermarket, park).

    Fields:
        name: Place name (e.g., "Safeway", "Phoenix Mountain Preserve")
        latitude: Place latitude
        longitude: Place longitude
        distance_meters: Distance from origin
        place_type: Type of place (supermarket, park, etc.)
        confidence: Data quality score (0.95 for Google Maps places)
        source: Data source identifier

    Example:
        result = PlaceResult(
            name="Safeway",
            latitude=33.4490,
            longitude=-112.0750,
            distance_meters=1200,
            place_type="supermarket",
        )
    """

    name: str = Field(..., description="Place name")
    latitude: float = Field(..., description="Place latitude")
    longitude: float = Field(..., description="Place longitude")
    distance_meters: int = Field(..., description="Distance from origin in meters")
    place_type: str = Field(..., description="Type of place (supermarket, park)")
    confidence: float = Field(default=0.95, description="Data quality confidence score")
    source: str = Field(default="google_maps_places", description="Data source identifier")

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with keys: {place_type}_name, {place_type}_distance_meters,
            {place_type}_lat, {place_type}_lng
        """
        return {
            f"{self.place_type}_name": self.name,
            f"{self.place_type}_distance_meters": self.distance_meters,
            f"{self.place_type}_lat": self.latitude,
            f"{self.place_type}_lng": self.longitude,
        }


class OrientationResult(BaseModel):
    """Backyard orientation determination from satellite imagery.

    Arizona-optimized scoring:
    - N (North) = 25pts (best - minimizes afternoon sun exposure)
    - E (East) = 18.75pts (good - morning sun only)
    - S (South) = 12.5pts (moderate - all-day sun)
    - W (West) = 0pts (worst - intense afternoon heat in Arizona)

    Fields:
        orientation: Backyard orientation enum (N/E/S/W)
        score_points: Points awarded based on orientation (0-25)
        confidence: Data quality score (0.70 for heuristic, 0.90+ for AI vision)
        source: Data source identifier

    Example:
        result = OrientationResult(
            orientation=Orientation.NORTH,
            score_points=25.0,
            confidence=0.70,
        )
    """

    orientation: Orientation = Field(..., description="Backyard orientation (N/E/S/W)")
    score_points: float = Field(..., description="Points awarded (0-25)")
    confidence: float = Field(
        default=0.70, description="Data quality confidence score (lower for heuristic)"
    )
    source: str = Field(
        default="google_maps_satellite_heuristic", description="Data source identifier"
    )

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment_data.json format.

        Returns:
            Dict with keys: backyard_orientation, orientation_score,
            orientation_confidence, orientation_source
        """
        return {
            "backyard_orientation": self.orientation.value,
            "orientation_score": self.score_points,
            "orientation_confidence": self.confidence,
            "orientation_source": self.source,
        }


__all__ = [
    "Orientation",
    "GeocodeResult",
    "DistanceResult",
    "PlaceResult",
    "OrientationResult",
]

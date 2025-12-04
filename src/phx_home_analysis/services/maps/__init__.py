"""Google Maps API integration for geographic data.

Provides geocoding, distance calculation, place search, and orientation determination
for property geographic analysis.

Exports:
    GoogleMapsClient: Main API client with all geographic methods
    GeocodeResult: Geocoding result model
    DistanceResult: Distance calculation result model
    PlaceResult: Place search result model
    OrientationResult: Orientation determination result model
    Orientation: Orientation enum (N/E/S/W)
"""

from .client import GoogleMapsClient
from .models import (
    DistanceResult,
    GeocodeResult,
    Orientation,
    OrientationResult,
    PlaceResult,
)

__all__ = [
    "GoogleMapsClient",
    "GeocodeResult",
    "DistanceResult",
    "PlaceResult",
    "OrientationResult",
    "Orientation",
]

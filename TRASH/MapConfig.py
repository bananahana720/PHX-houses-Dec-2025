"""DELETED: MapConfig class - no actual usage found in codebase.

Original location: src/phx_home_analysis/config/settings.py (lines 56-71)
Reason: Zero references to MapConfig fields (center_lat, center_lon, default_zoom, tile_provider)
Deleted: 2025-12-01
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MapConfig:
    """Configuration for map visualization and geocoding.

    Attributes:
        center_lat: Phoenix metropolitan area center latitude
        center_lon: Phoenix metropolitan area center longitude
        default_zoom: Default zoom level for maps
        tile_provider: Map tile provider (e.g., 'OpenStreetMap', 'CartoDB')
    """

    center_lat: float = 33.4484  # Phoenix, AZ
    center_lon: float = -112.0740
    default_zoom: int = 10
    tile_provider: str = "OpenStreetMap"

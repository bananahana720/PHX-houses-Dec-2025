"""FEMA National Flood Hazard Layer API client for flood zone data extraction."""

import asyncio
import logging
import time

import httpx

from phx_home_analysis.domain.enums import FloodZone

from .models import FloodZoneData

logger = logging.getLogger(__name__)

# FEMA NFHL ArcGIS REST API
NFHL_ENDPOINT = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"


class FEMAFloodClient:
    """HTTP client for FEMA National Flood Hazard Layer API.

    Queries flood zone data by latitude/longitude coordinates.
    Public federal API - no authentication required.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        rate_limit_seconds: float = 1.0,
    ):
        """Initialize client.

        Args:
            timeout: Request timeout in seconds
            rate_limit_seconds: Delay between API calls (recommended 1.0s)
        """
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "FEMAFloodClient":
        """Async context manager entry with HTTP/2 support."""
        # Try HTTP/2, fall back to HTTP/1.1 if h2 not installed
        try:
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                http2=True,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
        except ImportError:
            logger.debug("h2 package not installed, using HTTP/1.1")
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        if self._http:
            await self._http.aclose()

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls."""
        elapsed = time.time() - self._last_call
        if elapsed < self._rate_limit_seconds:
            await asyncio.sleep(self._rate_limit_seconds - elapsed)
        self._last_call = time.time()

    async def get_flood_zone(self, lat: float, lng: float) -> FloodZoneData | None:
        """Query flood zone for coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            FloodZoneData if found, None if no data or error
        """
        await self._apply_rate_limit()

        params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,FIRM_PAN,EFF_DATE",
            "returnGeometry": "false",
            "f": "json",
        }

        try:
            response = await self._http.get(NFHL_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for features
            features = data.get("features", [])
            if not features:
                logger.debug(f"No flood zone data found for ({lat}, {lng})")
                return None

            # Parse first feature
            attrs = features[0].get("attributes", {})
            return self._parse_flood_zone(attrs, lat, lng)

        except httpx.HTTPStatusError as e:
            logger.error(f"FEMA API HTTP error {e.response.status_code}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"FEMA API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"FEMA API unexpected error: {e}")
            return None

    def _parse_flood_zone(
        self, attrs: dict, lat: float, lng: float
    ) -> FloodZoneData | None:
        """Parse flood zone attributes from FEMA response.

        Args:
            attrs: Feature attributes from API response
            lat: Query latitude
            lng: Query longitude

        Returns:
            FloodZoneData if valid, None if parsing fails
        """
        try:
            # Parse flood zone code
            zone_code = attrs.get("FLD_ZONE", "").strip().upper()
            if not zone_code:
                logger.warning("Empty flood zone code in FEMA response")
                return None

            # Map FEMA zone code to FloodZone enum
            flood_zone = self._map_zone_code(zone_code)

            # Extract other fields
            zone_subtype = attrs.get("ZONE_SUBTY")
            panel = attrs.get("FIRM_PAN")
            effective_date = attrs.get("EFF_DATE")

            # Determine insurance requirement
            insurance_required = flood_zone.requires_insurance

            return FloodZoneData(
                flood_zone=flood_zone,
                flood_zone_panel=panel,
                flood_insurance_required=insurance_required,
                effective_date=effective_date,
                zone_subtype=zone_subtype,
                latitude=lat,
                longitude=lng,
            )

        except Exception as e:
            logger.error(f"Error parsing flood zone data: {e}")
            return None

    def _map_zone_code(self, code: str) -> FloodZone:
        """Map FEMA zone code to FloodZone enum.

        Args:
            code: FEMA flood zone code (e.g., "X", "AE", "0.2 PCT ANNUAL CHANCE")

        Returns:
            FloodZone enum value
        """
        code = code.upper().strip()

        # Direct mappings
        zone_map = {
            "X": FloodZone.X,
            "X500": FloodZone.X_SHADED,  # 500-year floodplain
            "0.2 PCT ANNUAL CHANCE": FloodZone.X_SHADED,  # 500-year (alternative name)
            "A": FloodZone.A,
            "AE": FloodZone.AE,
            "AH": FloodZone.AH,
            "AO": FloodZone.AO,
            "VE": FloodZone.VE,
        }

        # Check for exact match
        if code in zone_map:
            return zone_map[code]

        # Check for partial matches (e.g., "X PROTECTED BY LEVEE")
        for key, value in zone_map.items():
            if code.startswith(key):
                return value

        # Default to unknown
        logger.warning(f"Unknown FEMA flood zone code: {code}")
        return FloodZone.UNKNOWN

    async def get_flood_zones_batch(
        self, coordinates: list[tuple[float, float]]
    ) -> list[FloodZoneData | None]:
        """Query flood zones for multiple coordinates.

        Args:
            coordinates: List of (lat, lng) tuples

        Returns:
            List of FloodZoneData (None for failed queries)
        """
        results = []
        for lat, lng in coordinates:
            result = await self.get_flood_zone(lat, lng)
            results.append(result)
        return results

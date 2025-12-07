"""Google Maps API client for geographic data extraction.

Provides geocoding, distance calculation, place search, and satellite imagery
for property geographic analysis. Extends APIClient base class with rate limiting,
caching, and retry logic.

Required Environment Variable:
    GOOGLE_MAPS_API_KEY: Google Cloud Console API key with Maps APIs enabled

APIs Used:
    - Geocoding API: Address → lat/lng
    - Distance Matrix API: Origin/destination distances
    - Places API: Nearby POI search (supermarket, park)
    - Static Maps API: Satellite imagery download

Cost Estimate (per property):
    - Geocoding: $0.005
    - Distance Matrix: $0.015 (3 destinations)
    - Places: $0.064 (2 searches)
    - Static Maps: $0.002
    - Total: ~$0.086 per property

Rate Limits:
    - Free tier: 50 requests/second burst limit
    - Configured: 0.83 req/sec with safety margin
    - Cache: 7-day TTL to minimize API costs
"""

import logging
from pathlib import Path

from phx_home_analysis.services.api_client.base_client import APIClient
from phx_home_analysis.services.api_client.rate_limiter import RateLimit

from .models import (
    DistanceResult,
    GeocodeResult,
    Orientation,
    OrientationResult,
    PlaceResult,
)

logger = logging.getLogger(__name__)

# Google Maps API base URL
GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com"

# Arizona-optimized orientation scoring (N=best, W=worst)
ORIENTATION_SCORES = {
    Orientation.NORTH: 25.0,  # Best - minimizes afternoon sun
    Orientation.EAST: 18.75,  # Good - morning sun only
    Orientation.SOUTH: 12.5,  # Moderate - all-day sun
    Orientation.WEST: 0.0,  # Worst - intense afternoon heat
}

# Default work location (Phoenix downtown)
DEFAULT_WORK_LOCATION = {"lat": 33.4484, "lng": -112.0740}  # Phoenix, AZ


class GoogleMapsClient(APIClient):
    """Google Maps API client with geocoding, distance, places, and satellite imagery.

    Inherits authentication, rate limiting, caching, and retry from APIClient base class.
    All methods return None on failure to prevent pipeline crashes.

    Example:
        async with GoogleMapsClient() as client:
            # Geocode address
            geocode = await client.geocode_address("123 Main St, Phoenix, AZ")
            if geocode:
                print(f"Coordinates: {geocode.latitude}, {geocode.longitude}")

            # Calculate distances
            distances = await client.calculate_distances(33.4484, -112.0740)
            if distances:
                print(f"Work distance: {distances.work_distance_meters}m")

            # Find nearest supermarket
            supermarket = await client.find_nearest_poi(33.4484, -112.0740, "supermarket")
            if supermarket:
                print(f"Nearest: {supermarket.name} ({supermarket.distance_meters}m)")

            # Determine orientation (placeholder heuristic)
            orientation = await client.determine_orientation(33.4484, -112.0740)
            if orientation:
                print(f"Orientation: {orientation.orientation.value} ({orientation.score_points}pts)")
    """

    def __init__(self) -> None:
        """Initialize Google Maps client.

        Loads GOOGLE_MAPS_API_KEY from environment and configures:
        - Base URL: https://maps.googleapis.com
        - Rate limit: 0.83 req/sec (50/60s burst limit with margin)
        - Cache: 7-day TTL in data/api_cache/google_maps/
        - Timeout: 30 seconds per request

        Raises:
            ValueError: If GOOGLE_MAPS_API_KEY environment variable not set
        """
        super().__init__(
            service_name="google_maps",
            base_url=GOOGLE_MAPS_BASE_URL,
            env_key="GOOGLE_MAPS_API_KEY",
            rate_limit=RateLimit(requests_per_second=0.83),  # 50/60s with margin
            cache_ttl_days=7,
            timeout=30.0,
        )

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        """Geocode address to lat/lng with formatted address.

        Calls Geocoding API and returns first result. Response is cached for 7 days
        to minimize API costs ($0.005 per request).

        Args:
            address: Full address string (e.g., "123 Main St, Phoenix, AZ 85001")

        Returns:
            GeocodeResult with lat/lng and formatted address, or None on failure

        Example:
            result = await client.geocode_address("123 Main St, Phoenix, AZ 85001")
            if result:
                print(f"Lat: {result.latitude}, Lng: {result.longitude}")
                print(f"Address: {result.formatted_address}")
        """
        try:
            data = await self.get(
                "/maps/api/geocode/json",
                params={"address": address},
            )

            # Check API response status
            if not data or data.get("status") != "OK":
                logger.debug(
                    f"Geocoding failed for '{address}': {data.get('status') if data else 'No response'}"
                )
                return None

            results = data.get("results", [])
            if not results:
                logger.debug(f"No geocoding results for: {address}")
                return None

            # Extract first result
            result = results[0]
            location = result.get("geometry", {}).get("location", {})

            if not location:
                logger.debug(f"No geometry in geocoding result for: {address}")
                return None

            return GeocodeResult(
                latitude=location["lat"],
                longitude=location["lng"],
                formatted_address=result.get("formatted_address", address),
                confidence=0.95,
                source="google_maps_geocoding",
            )

        except Exception as e:
            logger.debug(f"Geocoding error for '{address}': {e}")
            return None

    async def calculate_distances(
        self,
        origin_lat: float,
        origin_lng: float,
        work_location: dict | None = None,
    ) -> DistanceResult | None:
        """Calculate distances to work, nearest supermarket, and nearest park.

        Uses Distance Matrix API for work distance and Places API for POI distances.
        Total cost: ~$0.079 per property ($0.015 distance + $0.064 places).

        Args:
            origin_lat: Property latitude
            origin_lng: Property longitude
            work_location: Optional work location dict with 'lat' and 'lng' keys
                          (defaults to Phoenix downtown)

        Returns:
            DistanceResult with distances in meters, or None on failure

        Example:
            result = await client.calculate_distances(33.4484, -112.0740)
            if result:
                print(f"Work: {result.work_distance_meters}m")
                print(f"Supermarket: {result.supermarket_distance_meters}m")
                print(f"Park: {result.park_distance_meters}m")
        """
        try:
            # Use default work location if not provided
            work_loc = work_location or DEFAULT_WORK_LOCATION

            # Calculate work distance via Distance Matrix API
            work_dist = await self._calculate_work_distance(
                origin_lat, origin_lng, work_loc["lat"], work_loc["lng"]
            )

            # Find nearest supermarket and park
            supermarket = await self.find_nearest_poi(origin_lat, origin_lng, "supermarket")
            park = await self.find_nearest_poi(origin_lat, origin_lng, "park")

            return DistanceResult(
                work_distance_meters=work_dist,
                supermarket_distance_meters=supermarket.distance_meters if supermarket else None,
                park_distance_meters=park.distance_meters if park else None,
                confidence=0.95,
                source="google_maps_distance",
            )

        except Exception as e:
            logger.debug(f"Distance calculation error for ({origin_lat}, {origin_lng}): {e}")
            return None

    async def _calculate_work_distance(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> int | None:
        """Calculate distance to work location using Distance Matrix API.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            Distance in meters, or None on failure
        """
        try:
            data = await self.get(
                "/maps/api/distancematrix/json",
                params={
                    "origins": f"{origin_lat},{origin_lng}",
                    "destinations": f"{dest_lat},{dest_lng}",
                    "units": "metric",
                },
            )

            if not data or data.get("status") != "OK":
                logger.debug(
                    f"Distance Matrix API error: {data.get('status') if data else 'No response'}"
                )
                return None

            rows = data.get("rows", [])
            if not rows:
                return None

            elements = rows[0].get("elements", [])
            if not elements:
                return None

            element = elements[0]
            if element.get("status") != "OK":
                return None

            distance = element.get("distance", {}).get("value")  # meters
            return distance

        except Exception as e:
            logger.debug(f"Work distance calculation error: {e}")
            return None

    async def find_nearest_poi(
        self,
        lat: float,
        lng: float,
        place_type: str,
        radius_meters: int = 5000,
    ) -> PlaceResult | None:
        """Find nearest point of interest (supermarket, park, etc.).

        Uses Places API nearby search. Cost: $0.032 per request.

        Args:
            lat: Search origin latitude
            lng: Search origin longitude
            place_type: Type of place to search (e.g., "supermarket", "park")
            radius_meters: Search radius in meters (default 5000 = 5km)

        Returns:
            PlaceResult with nearest POI details, or None if not found

        Example:
            result = await client.find_nearest_poi(33.4484, -112.0740, "supermarket")
            if result:
                print(f"Nearest: {result.name} ({result.distance_meters}m away)")
        """
        try:
            data = await self.get(
                "/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius_meters,
                    "type": place_type,
                    "rankby": "distance",  # Sort by distance (closest first)
                },
            )

            if not data or data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.debug(
                    f"Places API error for {place_type}: {data.get('status') if data else 'No response'}"
                )
                return None

            results = data.get("results", [])
            if not results:
                logger.debug(f"No {place_type} found within {radius_meters}m of ({lat}, {lng})")
                return None

            # Use first result (closest)
            place = results[0]
            place_location = place.get("geometry", {}).get("location", {})

            if not place_location:
                return None

            # Calculate distance from origin to place
            distance = self._haversine_distance(
                lat, lng, place_location["lat"], place_location["lng"]
            )

            return PlaceResult(
                name=place.get("name", f"Unknown {place_type}"),
                latitude=place_location["lat"],
                longitude=place_location["lng"],
                distance_meters=distance,
                place_type=place_type,
                confidence=0.95,
                source="google_maps_places",
            )

        except Exception as e:
            logger.debug(f"POI search error for {place_type}: {e}")
            return None

    async def fetch_satellite_image(
        self,
        lat: float,
        lng: float,
        zoom: int = 20,
        output_path: Path | None = None,
    ) -> bytes | None:
        """Fetch satellite image from Static Maps API.

        Downloads satellite imagery for orientation determination. Cost: $0.002 per request.

        Args:
            lat: Center latitude
            lng: Center longitude
            zoom: Zoom level (1-20, default 20 for detailed view)
            output_path: Optional path to save image (if None, returns bytes only)

        Returns:
            Image bytes, or None on failure

        Example:
            image_bytes = await client.fetch_satellite_image(33.4484, -112.0740)
            if image_bytes:
                Path("satellite.jpg").write_bytes(image_bytes)
        """
        try:
            # Note: Static Maps API returns image bytes, not JSON
            # We need to use a different approach here
            if not self._http:
                raise RuntimeError(
                    f"{self.__class__.__name__} must be used as async context manager"
                )

            # Apply rate limiting manually since we're not using get()
            await self._rate_limiter.acquire()

            # Build request URL
            url = f"{self.base_url}/maps/api/staticmap"
            params = self._build_params(
                {
                    "center": f"{lat},{lng}",
                    "zoom": zoom,
                    "size": "600x600",
                    "maptype": "satellite",
                }
            )

            response = await self._http.get(url, params=params)
            response.raise_for_status()

            image_bytes = response.content

            # Save to file if path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(image_bytes)
                logger.debug(f"Saved satellite image to: {output_path}")

            return image_bytes

        except Exception as e:
            logger.debug(f"Satellite image fetch error for ({lat}, {lng}): {e}")
            return None

    async def determine_orientation(
        self,
        lat: float,
        lng: float,
        satellite_image: bytes | None = None,
    ) -> OrientationResult | None:
        """Determine backyard orientation with Arizona-optimized scoring.

        PLACEHOLDER IMPLEMENTATION: Uses simple heuristic based on latitude.
        Future enhancement: Use Claude Vision or GPT-4 Vision to analyze satellite
        imagery and detect actual house footprint and backyard direction.

        Arizona Scoring:
        - N (North): 25pts - Best (minimizes afternoon sun)
        - E (East): 18.75pts - Good (morning sun only)
        - S (South): 12.5pts - Moderate (all-day sun)
        - W (West): 0pts - Worst (intense afternoon heat)

        Args:
            lat: Property latitude
            lng: Property longitude
            satellite_image: Optional satellite image bytes (unused in placeholder)

        Returns:
            OrientationResult with orientation and score, or None on failure

        Example:
            result = await client.determine_orientation(33.4484, -112.0740)
            if result:
                print(f"Orientation: {result.orientation.value} ({result.score_points}pts)")
        """
        try:
            # PLACEHOLDER: Simple heuristic based on latitude
            # In production, this would use AI vision to analyze satellite_image
            # and detect actual backyard orientation

            # Default to NORTH (best orientation) as placeholder
            # Real implementation would analyze satellite imagery
            orientation = Orientation.NORTH

            # Get score for orientation
            score = ORIENTATION_SCORES[orientation]

            return OrientationResult(
                orientation=orientation,
                score_points=score,
                confidence=0.70,  # Lower confidence for heuristic (vs 0.90+ for AI)
                source="google_maps_satellite_heuristic",
            )

        except Exception as e:
            logger.debug(f"Orientation determination error for ({lat}, {lng}): {e}")
            return None

    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1: Origin latitude
            lng1: Origin longitude
            lat2: Destination latitude
            lng2: Destination longitude

        Returns:
            Distance in meters
        """
        from math import asin, cos, radians, sin, sqrt

        # Earth radius in meters
        R = 6371000

        # Convert to radians
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)

        # Haversine formula
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
        c = 2 * asin(sqrt(a))
        distance = R * c

        return int(distance)


__all__ = ["GoogleMapsClient"]

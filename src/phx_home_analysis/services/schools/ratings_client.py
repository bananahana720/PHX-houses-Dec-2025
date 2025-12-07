"""SchoolDigger API client for school ratings extraction.

Provides school search, ratings retrieval, assigned school determination, and
composite scoring with Google Places fallback. Extends APIClient base class.

Required Environment Variables:
    SCHOOLDIGGER_API_KEY: RapidAPI key for SchoolDigger API access
    GOOGLE_MAPS_API_KEY: For Google Places fallback (already configured)

API Source:
    Primary: SchoolDigger via RapidAPI
    Fallback: Google Places API (names only, no ratings)

Rate Limits:
    - Free tier: 2,000 requests/month
    - Configured: 1000 requests/day quota tracking
    - Cache: 30-day TTL to minimize API usage

Cost Estimate:
    - SchoolDigger: Free (0-2,000 calls/month)
    - Google Places fallback: $0.032 per property (if needed)
"""

import logging
import math

from phx_home_analysis.services.api_client.base_client import APIClient
from phx_home_analysis.services.api_client.rate_limiter import RateLimit

from .api_models import (
    AssignedSchoolsResult,
    SchoolFallbackResult,
    SchoolLevel,
    SchoolResult,
)

logger = logging.getLogger(__name__)

# SchoolDigger API via RapidAPI base URL
SCHOOLDIGGER_BASE_URL = "https://schooldigger.p.rapidapi.com"

# Search radius thresholds (meters)
COMPREHENSIVE_RADIUS_METERS = 8046  # 5 miles - capture all nearby schools
ASSIGNED_FALLBACK_RADIUS_METERS = 3218  # 2 miles - reasonable assignment radius

# Distance conversion
METERS_PER_MILE = 1609.34


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two lat/lng points in meters.

    Uses haversine formula for accurate distance on Earth's surface.

    Args:
        lat1: Origin latitude
        lon1: Origin longitude
        lat2: Destination latitude
        lon2: Destination longitude

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in meters


class SchoolRatingsClient(APIClient):
    """SchoolDigger API client for school ratings with Google Places fallback.

    Inherits authentication, rate limiting, caching, and retry from APIClient.
    All methods return None on failure to prevent pipeline crashes.

    Example:
        async with SchoolRatingsClient() as client:
            # Get assigned schools with ratings
            result = await client.get_assigned_schools(33.4484, -112.0740)
            if result:
                print(f"Elementary: {result.elementary.name} ({result.elementary.rating}/10)")
                print(f"Composite: {result.composite_rating}/10")

            # Search all schools in area
            schools = await client.search_schools_by_location(33.4484, -112.0740)
            for school in schools:
                print(f"{school.name} ({school.level.value}): {school.rating}/10")
    """

    def __init__(self) -> None:
        """Initialize SchoolDigger client.

        Loads SCHOOLDIGGER_API_KEY from environment and configures:
        - Base URL: https://schooldigger.p.rapidapi.com
        - Rate limit: 1000 requests/day (free tier quota)
        - Cache: 30-day TTL in data/api_cache/schooldigger/
        - Timeout: 30 seconds per request

        Raises:
            ValueError: If SCHOOLDIGGER_API_KEY environment variable not set
        """
        super().__init__(
            service_name="schooldigger",
            base_url=SCHOOLDIGGER_BASE_URL,
            env_key="SCHOOLDIGGER_API_KEY",
            rate_limit=RateLimit(requests_per_day=1000),  # Free tier daily quota
            cache_ttl_days=30,  # 30-day cache per acceptance criteria
            timeout=30.0,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build RapidAPI headers with authentication.

        SchoolDigger via RapidAPI requires API key in X-RapidAPI-Key header.

        Returns:
            Headers dict with RapidAPI authentication
        """
        headers = super()._build_headers()  # Get Bearer token headers if any
        # For RapidAPI, API key goes in header, not query param
        if self._api_key:
            headers["X-RapidAPI-Key"] = self._api_key
            headers["X-RapidAPI-Host"] = "schooldigger.p.rapidapi.com"
        return headers

    def _build_params(self, params: dict | None) -> dict:
        """Build request params WITHOUT adding API key.

        SchoolDigger uses header-based auth (X-RapidAPI-Key), not query params.
        Override parent method to prevent API key from being added to URL.

        Args:
            params: User-provided params

        Returns:
            Params dict without API key
        """
        return dict(params) if params else {}

    async def search_schools_by_location(
        self,
        lat: float,
        lng: float,
        radius_meters: int = COMPREHENSIVE_RADIUS_METERS,
        limit: int = 50,
    ) -> list[SchoolResult]:
        """Search for schools near coordinates within radius.

        Calls SchoolDigger API to fetch schools sorted by distance.
        Filters by radius and calculates precise distances via haversine.

        Args:
            lat: Property latitude
            lng: Property longitude
            radius_meters: Search radius in meters (default 5 miles)
            limit: Maximum results to return (default 50)

        Returns:
            List of SchoolResult sorted by distance, or empty list on failure

        Example:
            schools = await client.search_schools_by_location(33.4484, -112.0740)
            for school in schools:
                print(f"{school.name}: {school.rating}/10, {school.distance_meters}m away")
        """
        try:
            # SchoolDigger API endpoint: /v1/schools/near
            # Params: latitude, longitude, distance (miles), st (state), page, perPage
            radius_miles = radius_meters / METERS_PER_MILE

            data = await self.get(
                "/v1/schools/near",
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "distance": radius_miles,
                    "st": "AZ",  # Arizona-specific
                    "perPage": limit,
                    "page": 1,
                },
            )

            if not data:
                logger.debug("SchoolDigger API returned no data")
                return []

            schools_data = data.get("schools", [])
            if not schools_data:
                logger.debug(f"No schools found within {radius_miles:.1f} miles of ({lat}, {lng})")
                return []

            schools = []
            for school in schools_data:
                # Parse school level from lowGrade/highGrade
                school_level = self._determine_school_level(
                    school.get("lowGrade"), school.get("highGrade")
                )

                # Calculate precise distance using haversine
                school_lat = school.get("latitude")
                school_lng = school.get("longitude")
                if school_lat is None or school_lng is None:
                    continue

                distance = haversine_distance(lat, lng, school_lat, school_lng)

                # Filter by radius (API distance param is approximate)
                if distance > radius_meters:
                    continue

                # Extract rating (0-10 scale) - SchoolDigger uses ranking, convert if needed
                # SchoolDigger provides 'schoolDiggerRating' (0-100 scale)
                rating_100 = school.get("schoolDiggerRating")
                rating = (rating_100 / 10.0) if rating_100 is not None else None

                schools.append(
                    SchoolResult(
                        name=school.get("schoolName", "Unknown School"),
                        address=school.get("address", {}).get("street"),
                        latitude=school_lat,
                        longitude=school_lng,
                        rating=rating,
                        level=school_level,
                        distance_meters=distance,
                        is_assigned=False,  # Determined separately
                        confidence=0.95,
                        source="schooldigger_api",
                    )
                )

            # Sort by distance ascending (nearest first)
            schools.sort(key=lambda s: s.distance_meters)
            return schools

        except Exception as e:
            logger.debug(f"School search failed: {e}")
            return []  # Return empty list, trigger fallback

    def _determine_school_level(self, low_grade: str | None, high_grade: str | None) -> SchoolLevel:
        """Determine school level from grade range.

        Args:
            low_grade: Lowest grade (e.g., "PK", "K", "1")
            high_grade: Highest grade (e.g., "5", "8", "12")

        Returns:
            SchoolLevel enum (ELEMENTARY, MIDDLE, HIGH, UNKNOWN)
        """
        if not high_grade:
            return SchoolLevel.UNKNOWN

        # Convert grade to int (handle PK, K as special cases)
        try:
            if high_grade.upper() in ("PK", "K"):
                grade_num = 0
            else:
                grade_num = int(high_grade)

            # Elementary: ends at grade 5 or lower
            if grade_num <= 5:
                return SchoolLevel.ELEMENTARY
            # Middle: ends at grade 8
            elif grade_num <= 8:
                return SchoolLevel.MIDDLE
            # High: ends at grade 9+
            else:
                return SchoolLevel.HIGH

        except (ValueError, AttributeError):
            return SchoolLevel.UNKNOWN

    async def get_assigned_schools(self, lat: float, lng: float) -> AssignedSchoolsResult | None:
        """Get assigned elementary, middle, and high schools with composite rating.

        Searches for schools near property and determines assigned schools.
        Falls back to Google Places if SchoolDigger fails.

        Args:
            lat: Property latitude
            lng: Property longitude

        Returns:
            AssignedSchoolsResult with elementary/middle/high and composite rating,
            or None on complete failure

        Example:
            result = await client.get_assigned_schools(33.4484, -112.0740)
            if result:
                print(f"Elementary: {result.elementary.name}")
                print(f"Composite rating: {result.composite_rating}/10")
        """
        try:
            # Search for schools within 5-mile radius
            schools = await self.search_schools_by_location(lat, lng)

            if not schools:
                # Fallback to Google Places
                logger.info("SchoolDigger returned no schools, falling back to Google Places")
                return await self._fallback_to_google_places(lat, lng)

            # Determine assigned schools (nearest of each level within 2 miles)
            assigned = await self._determine_assigned_schools(lat, lng, schools)

            if assigned:
                return assigned

            # If no assigned schools found, try Google Places fallback
            logger.info("No assigned schools determined, falling back to Google Places")
            return await self._fallback_to_google_places(lat, lng)

        except Exception as e:
            logger.error(f"get_assigned_schools failed: {e}")
            return None  # Final fallback: Return None, let pipeline continue

    async def _determine_assigned_schools(
        self, lat: float, lng: float, schools: list[SchoolResult]
    ) -> AssignedSchoolsResult | None:
        """Determine assigned schools from search results.

        Uses nearest school of each level within 2-mile radius as proxy for
        assigned school (SchoolDigger doesn't provide boundary data).

        Args:
            lat: Property latitude
            lng: Property longitude
            schools: List of SchoolResult from search

        Returns:
            AssignedSchoolsResult with nearest elementary/middle/high, or None
        """
        # Group schools by level
        elementary_schools = [s for s in schools if s.level == SchoolLevel.ELEMENTARY]
        middle_schools = [s for s in schools if s.level == SchoolLevel.MIDDLE]
        high_schools = [s for s in schools if s.level == SchoolLevel.HIGH]

        # Find nearest of each level within assigned fallback radius (2 miles)
        assigned_elementary = None
        assigned_middle = None
        assigned_high = None

        if elementary_schools:
            nearest = min(elementary_schools, key=lambda s: s.distance_meters)
            if nearest.distance_meters <= ASSIGNED_FALLBACK_RADIUS_METERS:
                nearest.is_assigned = True
                assigned_elementary = nearest

        if middle_schools:
            nearest = min(middle_schools, key=lambda s: s.distance_meters)
            if nearest.distance_meters <= ASSIGNED_FALLBACK_RADIUS_METERS:
                nearest.is_assigned = True
                assigned_middle = nearest

        if high_schools:
            nearest = min(high_schools, key=lambda s: s.distance_meters)
            if nearest.distance_meters <= ASSIGNED_FALLBACK_RADIUS_METERS:
                nearest.is_assigned = True
                assigned_high = nearest

        # Calculate composite rating (Arizona-weighted)
        composite = self.calculate_composite_rating(
            assigned_elementary.rating if assigned_elementary else None,
            assigned_middle.rating if assigned_middle else None,
            assigned_high.rating if assigned_high else None,
        )

        # Return None if no schools assigned
        if not any([assigned_elementary, assigned_middle, assigned_high]):
            return None

        return AssignedSchoolsResult(
            elementary=assigned_elementary,
            middle=assigned_middle,
            high=assigned_high,
            composite_rating=composite,
            confidence=0.95,
            source="schooldigger_api",
        )

    def calculate_composite_rating(
        self,
        elementary: float | None,
        middle: float | None,
        high: float | None,
    ) -> float | None:
        """Calculate Arizona-weighted composite school rating.

        Formula: (elementary × 0.3) + (middle × 0.3) + (high × 0.4)

        Arizona buyers prioritize high school quality (40% weight) for long-term
        property value and college readiness. Elementary and middle get 30% each.

        Handles missing ratings by calculating average using only available levels.

        Args:
            elementary: Elementary school rating (0-10), or None
            middle: Middle school rating (0-10), or None
            high: High school rating (0-10), or None

        Returns:
            Composite rating (0-10), or None if all three levels missing

        Example:
            # All three levels available
            rating = calculate_composite_rating(7.0, 8.0, 9.0)
            # Result: (7×0.3) + (8×0.3) + (9×0.4) = 8.1

            # Only elementary and high available
            rating = calculate_composite_rating(7.0, None, 9.0)
            # Result: (7×0.5) + (9×0.5) = 8.0
        """
        ratings = []
        weights = []

        if elementary is not None:
            ratings.append(elementary)
            weights.append(0.3)

        if middle is not None:
            ratings.append(middle)
            weights.append(0.3)

        if high is not None:
            ratings.append(high)
            weights.append(0.4)

        if not ratings:
            return None

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average
        composite = sum(r * w for r, w in zip(ratings, normalized_weights, strict=True))
        return round(composite, 1)

    async def _fallback_to_google_places(
        self, lat: float, lng: float
    ) -> SchoolFallbackResult | None:
        """Fallback to Google Places API for school names (no ratings).

        Used when SchoolDigger API fails or returns no results.
        Provides school names and count only - NO ratings available.

        Args:
            lat: Property latitude
            lng: Property longitude

        Returns:
            SchoolFallbackResult with school names and low confidence (0.5),
            or None on failure

        Example:
            result = await client._fallback_to_google_places(33.4484, -112.0740)
            if result:
                print(f"Found {result.school_count} schools")
                print(f"Names: {', '.join(result.school_names)}")
        """
        try:
            # Import GoogleMapsClient for fallback
            from phx_home_analysis.services.maps import GoogleMapsClient

            async with GoogleMapsClient() as maps_client:
                # Search for schools within 3-mile radius
                radius_meters = 4828  # 3 miles
                school_names = []

                # Search for "school" type places
                result = await maps_client.find_nearest_poi(
                    lat, lng, "school", radius_meters=radius_meters
                )

                if result:
                    school_names.append(result.name)

                # Try to get more schools by searching with different approaches
                # Note: Google Places "nearbysearch" is limited, this is best effort
                logger.info(
                    f"Google Places fallback found {len(school_names)} school(s) near ({lat}, {lng})"
                )

                return SchoolFallbackResult(
                    school_names=school_names,
                    school_count=len(school_names),
                    confidence=0.5,  # Low confidence - names only, no ratings
                    source="google_places_fallback",
                )

        except Exception as e:
            logger.error(f"Google Places fallback failed: {e}")
            return None


__all__ = ["SchoolRatingsClient", "haversine_distance"]

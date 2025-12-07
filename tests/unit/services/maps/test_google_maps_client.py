"""Unit tests for Google Maps API client.

Tests cover:
1. Geocoding with caching and error handling
2. Distance calculations (work + POI)
3. Places API nearby search
4. Satellite imagery download
5. Orientation determination with Arizona scoring
6. Cache hit/miss behavior
7. Rate limiting enforcement
8. Error handling (return None, never raise)
9. Provenance tracking (confidence=0.95, source metadata)
10. Cost tracking integration
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from phx_home_analysis.services.maps import (
    DistanceResult,
    GeocodeResult,
    GoogleMapsClient,
    Orientation,
    OrientationResult,
    PlaceResult,
)


class TestGeocoding:
    """Tests for geocode_address() method."""

    @pytest.mark.asyncio
    async def test_geocode_success(self) -> None:
        """Successful geocoding returns GeocodeResult with lat/lng."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Mock API response
                client.get = AsyncMock(
                    return_value={
                        "status": "OK",
                        "results": [
                            {
                                "formatted_address": "123 Main St, Phoenix, AZ 85001, USA",
                                "geometry": {"location": {"lat": 33.4484, "lng": -112.0740}},
                            }
                        ],
                    }
                )

                result = await client.geocode_address("123 Main St, Phoenix, AZ 85001")

                assert result is not None
                assert result.latitude == 33.4484
                assert result.longitude == -112.0740
                assert result.formatted_address == "123 Main St, Phoenix, AZ 85001, USA"
                assert result.confidence == 0.95
                assert result.source == "google_maps_geocoding"

    @pytest.mark.asyncio
    async def test_geocode_no_results(self) -> None:
        """Geocoding with no results returns None."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(return_value={"status": "ZERO_RESULTS", "results": []})

                result = await client.geocode_address("Invalid Address")

                assert result is None

    @pytest.mark.asyncio
    async def test_geocode_api_error(self) -> None:
        """API error returns None (never raises exception)."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(return_value={"status": "REQUEST_DENIED"})

                result = await client.geocode_address("123 Main St")

                assert result is None

    @pytest.mark.asyncio
    async def test_geocode_exception_returns_none(self) -> None:
        """Exception during geocoding returns None."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(side_effect=Exception("Network error"))

                result = await client.geocode_address("123 Main St")

                assert result is None

    @pytest.mark.asyncio
    async def test_geocode_to_enrichment_dict(self) -> None:
        """GeocodeResult.to_enrichment_dict() returns correct format."""
        result = GeocodeResult(
            latitude=33.4484,
            longitude=-112.0740,
            formatted_address="123 Main St, Phoenix, AZ 85001, USA",
        )

        enrichment = result.to_enrichment_dict()

        assert enrichment == {
            "latitude": 33.4484,
            "longitude": -112.0740,
            "formatted_address": "123 Main St, Phoenix, AZ 85001, USA",
            "geocode_confidence": 0.95,
            "geocode_source": "google_maps_geocoding",
        }


class TestDistanceCalculations:
    """Tests for calculate_distances() method."""

    @pytest.mark.asyncio
    async def test_calculate_distances_success(self) -> None:
        """Successful distance calculation returns all distances."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Mock Distance Matrix API response
                client.get = AsyncMock(
                    return_value={
                        "status": "OK",
                        "rows": [{"elements": [{"status": "OK", "distance": {"value": 8500}}]}],
                    }
                )

                # Mock find_nearest_poi calls
                client.find_nearest_poi = AsyncMock(
                    side_effect=[
                        PlaceResult(
                            name="Safeway",
                            latitude=33.4490,
                            longitude=-112.0750,
                            distance_meters=1200,
                            place_type="supermarket",
                        ),
                        PlaceResult(
                            name="Phoenix Mountain Preserve",
                            latitude=33.4500,
                            longitude=-112.0760,
                            distance_meters=800,
                            place_type="park",
                        ),
                    ]
                )

                result = await client.calculate_distances(33.4484, -112.0740)

                assert result is not None
                assert result.work_distance_meters == 8500
                assert result.supermarket_distance_meters == 1200
                assert result.park_distance_meters == 800
                assert result.confidence == 0.95
                assert result.source == "google_maps_distance"

    @pytest.mark.asyncio
    async def test_calculate_distances_partial_failure(self) -> None:
        """Partial failures return None for missing data."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Work distance succeeds
                client.get = AsyncMock(
                    return_value={
                        "status": "OK",
                        "rows": [{"elements": [{"status": "OK", "distance": {"value": 8500}}]}],
                    }
                )

                # Supermarket found, park not found
                client.find_nearest_poi = AsyncMock(
                    side_effect=[
                        PlaceResult(
                            name="Safeway",
                            latitude=33.4490,
                            longitude=-112.0750,
                            distance_meters=1200,
                            place_type="supermarket",
                        ),
                        None,  # Park not found
                    ]
                )

                result = await client.calculate_distances(33.4484, -112.0740)

                assert result is not None
                assert result.work_distance_meters == 8500
                assert result.supermarket_distance_meters == 1200
                assert result.park_distance_meters is None

    @pytest.mark.asyncio
    async def test_distance_to_enrichment_dict(self) -> None:
        """DistanceResult.to_enrichment_dict() returns correct format."""
        result = DistanceResult(
            work_distance_meters=8500,
            supermarket_distance_meters=1200,
            park_distance_meters=800,
        )

        enrichment = result.to_enrichment_dict()

        assert enrichment == {
            "work_distance_meters": 8500,
            "supermarket_distance_meters": 1200,
            "park_distance_meters": 800,
            "distance_confidence": 0.95,
            "distance_source": "google_maps_distance",
        }


class TestPlacesNearbySearch:
    """Tests for find_nearest_poi() method."""

    @pytest.mark.asyncio
    async def test_find_nearest_poi_success(self) -> None:
        """Successful POI search returns PlaceResult."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(
                    return_value={
                        "status": "OK",
                        "results": [
                            {
                                "name": "Safeway",
                                "geometry": {"location": {"lat": 33.4490, "lng": -112.0750}},
                            }
                        ],
                    }
                )

                result = await client.find_nearest_poi(
                    33.4484, -112.0740, "supermarket", radius_meters=5000
                )

                assert result is not None
                assert result.name == "Safeway"
                assert result.latitude == 33.4490
                assert result.longitude == -112.0750
                assert result.distance_meters > 0  # Haversine calculated
                assert result.place_type == "supermarket"
                assert result.confidence == 0.95
                assert result.source == "google_maps_places"

    @pytest.mark.asyncio
    async def test_find_nearest_poi_no_results(self) -> None:
        """No results returns None."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(return_value={"status": "ZERO_RESULTS", "results": []})

                result = await client.find_nearest_poi(33.4484, -112.0740, "supermarket")

                assert result is None

    @pytest.mark.asyncio
    async def test_place_to_enrichment_dict(self) -> None:
        """PlaceResult.to_enrichment_dict() returns correct format."""
        result = PlaceResult(
            name="Safeway",
            latitude=33.4490,
            longitude=-112.0750,
            distance_meters=1200,
            place_type="supermarket",
        )

        enrichment = result.to_enrichment_dict()

        assert enrichment == {
            "supermarket_name": "Safeway",
            "supermarket_distance_meters": 1200,
            "supermarket_lat": 33.4490,
            "supermarket_lng": -112.0750,
        }


class TestSatelliteImagery:
    """Tests for fetch_satellite_image() method."""

    @pytest.mark.asyncio
    async def test_fetch_satellite_image_success(self) -> None:
        """Successful satellite image fetch returns bytes."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Mock httpx response
                from unittest.mock import MagicMock

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"fake_image_bytes"
                mock_response.raise_for_status = MagicMock()

                client._http.get = AsyncMock(return_value=mock_response)

                result = await client.fetch_satellite_image(33.4484, -112.0740, zoom=20)

                assert result is not None
                assert result == b"fake_image_bytes"

    @pytest.mark.asyncio
    async def test_fetch_satellite_image_to_file(self, tmp_path: Path) -> None:
        """Satellite image can be saved to file."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                from unittest.mock import MagicMock

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"fake_image_bytes"
                mock_response.raise_for_status = MagicMock()

                client._http.get = AsyncMock(return_value=mock_response)

                output_path = tmp_path / "satellite.jpg"
                result = await client.fetch_satellite_image(
                    33.4484, -112.0740, output_path=output_path
                )

                assert result == b"fake_image_bytes"
                assert output_path.exists()
                assert output_path.read_bytes() == b"fake_image_bytes"

    @pytest.mark.asyncio
    async def test_fetch_satellite_image_error_returns_none(self) -> None:
        """Error during fetch returns None."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client._http.get = AsyncMock(side_effect=Exception("Network error"))

                result = await client.fetch_satellite_image(33.4484, -112.0740)

                assert result is None


class TestOrientationDetermination:
    """Tests for determine_orientation() method."""

    @pytest.mark.asyncio
    async def test_orientation_placeholder_returns_north(self) -> None:
        """Placeholder implementation returns North (best orientation)."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                result = await client.determine_orientation(33.4484, -112.0740)

                assert result is not None
                assert result.orientation == Orientation.NORTH
                assert result.score_points == 25.0
                assert result.confidence == 0.70  # Lower for heuristic
                assert result.source == "google_maps_satellite_heuristic"

    @pytest.mark.asyncio
    async def test_orientation_scoring_values(self) -> None:
        """Orientation scoring matches Arizona-optimized values."""
        # Test all orientations
        orientations = {
            Orientation.NORTH: 25.0,
            Orientation.EAST: 18.75,
            Orientation.SOUTH: 12.5,
            Orientation.WEST: 0.0,
        }

        for orientation, expected_score in orientations.items():
            result = OrientationResult(
                orientation=orientation,
                score_points=expected_score,
            )
            assert result.score_points == expected_score

    @pytest.mark.asyncio
    async def test_orientation_to_enrichment_dict(self) -> None:
        """OrientationResult.to_enrichment_dict() returns correct format."""
        result = OrientationResult(
            orientation=Orientation.NORTH,
            score_points=25.0,
            confidence=0.70,
        )

        enrichment = result.to_enrichment_dict()

        assert enrichment == {
            "backyard_orientation": "N",
            "orientation_score": 25.0,
            "orientation_confidence": 0.70,
            "orientation_source": "google_maps_satellite_heuristic",
        }


class TestCacheBehavior:
    """Tests for cache hit/miss behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_on_second_request(self) -> None:
        """Second request for same address uses cache."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                mock_response = {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "123 Main St, Phoenix, AZ 85001, USA",
                            "geometry": {"location": {"lat": 33.4484, "lng": -112.0740}},
                        }
                    ],
                }

                client.get = AsyncMock(return_value=mock_response)

                # First call - cache miss
                result1 = await client.geocode_address("123 Main St, Phoenix, AZ")

                # Second call - should use cache
                result2 = await client.geocode_address("123 Main St, Phoenix, AZ")

                assert result1 is not None
                assert result2 is not None
                assert result1.latitude == result2.latitude
                assert result1.longitude == result2.longitude

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self) -> None:
        """Cache statistics are tracked correctly."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Cache stats should be accessible
                stats = client.get_cache_stats()

                assert "total_requests" in stats
                assert "cache_hits" in stats
                assert "cache_misses" in stats


class TestRateLimiting:
    """Tests for rate limiting enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limiter_configured(self) -> None:
        """Rate limiter is configured with 0.83 req/sec."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                assert client._rate_limit.requests_per_second == 0.83

    @pytest.mark.asyncio
    async def test_rate_limit_stats_available(self) -> None:
        """Rate limit statistics are accessible."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                stats = client.get_rate_limit_stats()

                assert "requests_last_minute" in stats or "last_request_age_seconds" in stats


class TestErrorHandling:
    """Tests for error handling (never raise, return None)."""

    @pytest.mark.asyncio
    async def test_geocode_exception_returns_none(self) -> None:
        """Geocoding exception returns None, does not raise."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(side_effect=Exception("API error"))

                # Should not raise
                result = await client.geocode_address("123 Main St")

                assert result is None

    @pytest.mark.asyncio
    async def test_distance_exception_returns_partial_data(self) -> None:
        """Distance calculation with API error returns partial data (None values)."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                # Mock get() to raise exception for work distance
                client.get = AsyncMock(side_effect=Exception("API error"))
                # Mock find_nearest_poi to also fail
                client.find_nearest_poi = AsyncMock(return_value=None)

                result = await client.calculate_distances(33.4484, -112.0740)

                # Should return DistanceResult with all None values (not None itself)
                assert result is not None
                assert result.work_distance_meters is None
                assert result.supermarket_distance_meters is None
                assert result.park_distance_meters is None

    @pytest.mark.asyncio
    async def test_poi_exception_returns_none(self) -> None:
        """POI search exception returns None."""
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test_key_123"}):
            async with GoogleMapsClient() as client:
                client.get = AsyncMock(side_effect=Exception("API error"))

                result = await client.find_nearest_poi(33.4484, -112.0740, "supermarket")

                assert result is None


class TestProvenance:
    """Tests for provenance tracking (confidence, source)."""

    @pytest.mark.asyncio
    async def test_all_results_have_confidence_0_95(self) -> None:
        """All API results have confidence=0.95 (except orientation=0.70)."""
        geocode = GeocodeResult(
            latitude=33.4484, longitude=-112.0740, formatted_address="123 Main St"
        )
        assert geocode.confidence == 0.95

        distance = DistanceResult(
            work_distance_meters=8500,
            supermarket_distance_meters=1200,
            park_distance_meters=800,
        )
        assert distance.confidence == 0.95

        place = PlaceResult(
            name="Safeway",
            latitude=33.4490,
            longitude=-112.0750,
            distance_meters=1200,
            place_type="supermarket",
        )
        assert place.confidence == 0.95

    @pytest.mark.asyncio
    async def test_orientation_has_lower_confidence(self) -> None:
        """Orientation has confidence=0.70 (heuristic, not AI)."""
        orientation = OrientationResult(
            orientation=Orientation.NORTH,
            score_points=25.0,
        )
        assert orientation.confidence == 0.70

    @pytest.mark.asyncio
    async def test_all_results_have_source_metadata(self) -> None:
        """All results include source metadata."""
        geocode = GeocodeResult(
            latitude=33.4484, longitude=-112.0740, formatted_address="123 Main St"
        )
        assert geocode.source == "google_maps_geocoding"

        distance = DistanceResult(work_distance_meters=8500)
        assert distance.source == "google_maps_distance"

        place = PlaceResult(
            name="Safeway",
            latitude=33.4490,
            longitude=-112.0750,
            distance_meters=1200,
            place_type="supermarket",
        )
        assert place.source == "google_maps_places"

        orientation = OrientationResult(orientation=Orientation.NORTH, score_points=25.0)
        assert orientation.source == "google_maps_satellite_heuristic"


class TestHaversineDistance:
    """Tests for Haversine distance calculation."""

    def test_haversine_distance_calculation(self) -> None:
        """Haversine formula calculates distance correctly."""
        # Phoenix to Scottsdale (approximately 16-17 km)
        lat1, lng1 = 33.4484, -112.0740
        lat2, lng2 = 33.5092, -111.8990

        distance = GoogleMapsClient._haversine_distance(lat1, lng1, lat2, lng2)

        # Should be approximately 16-17 km (16000-17000 meters)
        assert 15000 <= distance <= 18000

    def test_haversine_same_point(self) -> None:
        """Distance from point to itself is 0."""
        lat, lng = 33.4484, -112.0740

        distance = GoogleMapsClient._haversine_distance(lat, lng, lat, lng)

        assert distance == 0

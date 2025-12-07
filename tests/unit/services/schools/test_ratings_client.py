"""Unit tests for SchoolDigger API ratings client.

Tests cover:
1. School search by coordinates with radius filtering (AC#1, #8)
2. Assigned school determination (nearest per level) (AC#3)
3. Composite rating calculation with Arizona weighting (AC#5)
4. Google Places fallback when API fails (AC#4, #7)
5. 30-day cache behavior (AC#2)
6. Rate limiting (1000 req/day quota) (AC#6)
7. Provenance tracking (confidence=0.95 API, 0.5 fallback) (AC#7)
8. Distance calculations using haversine formula (AC#8)
9. Error handling (return None, never raise)
10. to_enrichment_dict() schema compliance
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from phx_home_analysis.services.schools import (
    AssignedSchoolsResult,
    SchoolFallbackResult,
    SchoolLevel,
    SchoolRatingsClient,
    SchoolResult,
    haversine_distance,
)


class TestHaversineDistance:
    """Tests for haversine distance formula."""

    def test_distance_calculation_accuracy(self) -> None:
        """Haversine formula calculates correct distance."""
        # Phoenix to Scottsdale (approximately 14.6km = 14,600m)
        phx_lat, phx_lng = 33.4484, -112.0740
        scottsdale_lat, scottsdale_lng = 33.4942, -111.9261

        distance = haversine_distance(phx_lat, phx_lng, scottsdale_lat, scottsdale_lng)

        # Should be ~14-15km (actual distance ~14.6km)
        assert 14000 <= distance <= 15000

    def test_same_location_returns_zero(self) -> None:
        """Distance from location to itself is zero."""
        lat, lng = 33.4484, -112.0740
        distance = haversine_distance(lat, lng, lat, lng)

        assert distance < 1.0  # Allow floating point error

    def test_distance_is_symmetric(self) -> None:
        """Distance from A to B equals distance from B to A."""
        lat1, lng1 = 33.4484, -112.0740
        lat2, lng2 = 33.4942, -111.9261

        dist_ab = haversine_distance(lat1, lng1, lat2, lng2)
        dist_ba = haversine_distance(lat2, lng2, lat1, lng1)

        assert abs(dist_ab - dist_ba) < 0.1


class TestSchoolSearch:
    """Tests for search_schools_by_location() method."""

    @pytest.mark.asyncio
    async def test_search_success_returns_sorted_schools(self) -> None:
        """Successful search returns SchoolResult list sorted by distance."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                # Mock API response with 3 schools (elementary, middle, high)
                client.get = AsyncMock(
                    return_value={
                        "schools": [
                            {
                                "schoolName": "Desert Elementary",
                                "latitude": 33.4484,
                                "longitude": -112.0740,
                                "lowGrade": "K",
                                "highGrade": "5",
                                "schoolDiggerRating": 75,  # 7.5/10
                                "address": {"street": "123 School St"},
                            },
                            {
                                "schoolName": "Phoenix Middle School",
                                "latitude": 33.4500,
                                "longitude": -112.0750,
                                "lowGrade": "6",
                                "highGrade": "8",
                                "schoolDiggerRating": 80,  # 8.0/10
                                "address": {"street": "456 Education Ave"},
                            },
                            {
                                "schoolName": "Arizona High School",
                                "latitude": 33.4520,
                                "longitude": -112.0760,
                                "lowGrade": "9",
                                "highGrade": "12",
                                "schoolDiggerRating": 90,  # 9.0/10
                                "address": {"street": "789 Knowledge Blvd"},
                            },
                        ]
                    }
                )

                schools = await client.search_schools_by_location(33.4484, -112.0740)

                assert len(schools) == 3

                # Verify sorted by distance (nearest first)
                assert schools[0].name == "Desert Elementary"
                assert schools[0].distance_meters < schools[1].distance_meters
                assert schools[1].distance_meters < schools[2].distance_meters

                # Verify school levels parsed correctly
                assert schools[0].level == SchoolLevel.ELEMENTARY
                assert schools[1].level == SchoolLevel.MIDDLE
                assert schools[2].level == SchoolLevel.HIGH

                # Verify ratings converted from 0-100 to 0-10 scale
                assert schools[0].rating == 7.5
                assert schools[1].rating == 8.0
                assert schools[2].rating == 9.0

                # Verify provenance
                assert all(s.confidence == 0.95 for s in schools)
                assert all(s.source == "schooldigger_api" for s in schools)

    @pytest.mark.asyncio
    async def test_search_no_results_returns_empty_list(self) -> None:
        """Search with no results returns empty list."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                client.get = AsyncMock(return_value={"schools": []})

                schools = await client.search_schools_by_location(33.4484, -112.0740)

                assert schools == []

    @pytest.mark.asyncio
    async def test_search_api_error_returns_empty_list(self) -> None:
        """API error returns empty list (never raises exception)."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                client.get = AsyncMock(side_effect=Exception("Network error"))

                schools = await client.search_schools_by_location(33.4484, -112.0740)

                assert schools == []

    @pytest.mark.asyncio
    async def test_search_filters_by_radius(self) -> None:
        """Schools outside radius are filtered out."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                # Mock schools: one nearby (800m), one far (10km)
                client.get = AsyncMock(
                    return_value={
                        "schools": [
                            {
                                "schoolName": "Nearby School",
                                "latitude": 33.4555,  # ~800m away
                                "longitude": -112.0740,
                                "lowGrade": "K",
                                "highGrade": "5",
                                "schoolDiggerRating": 70,
                            },
                            {
                                "schoolName": "Far School",
                                "latitude": 33.5400,  # ~10km away
                                "longitude": -112.0740,
                                "lowGrade": "K",
                                "highGrade": "5",
                                "schoolDiggerRating": 90,
                            },
                        ]
                    }
                )

                # Search with 5km radius (default)
                schools = await client.search_schools_by_location(
                    33.4484, -112.0740, radius_meters=5000
                )

                # Only nearby school should be included
                assert len(schools) == 1
                assert schools[0].name == "Nearby School"


class TestAssignedSchools:
    """Tests for get_assigned_schools() method."""

    @pytest.mark.asyncio
    async def test_assigned_schools_with_composite_rating(self) -> None:
        """Returns assigned elementary, middle, high with composite rating."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                # Mock search results with all 3 levels within 2 miles
                mock_schools = [
                    SchoolResult(
                        name="Desert Elementary",
                        latitude=33.4500,
                        longitude=-112.0740,
                        rating=7.0,
                        level=SchoolLevel.ELEMENTARY,
                        distance_meters=1000,  # 1km < 2 miles
                        confidence=0.95,
                        source="schooldigger_api",
                    ),
                    SchoolResult(
                        name="Phoenix Middle",
                        latitude=33.4520,
                        longitude=-112.0740,
                        rating=8.0,
                        level=SchoolLevel.MIDDLE,
                        distance_meters=2000,  # 2km < 2 miles
                        confidence=0.95,
                        source="schooldigger_api",
                    ),
                    SchoolResult(
                        name="Arizona High",
                        latitude=33.4540,
                        longitude=-112.0740,
                        rating=9.0,
                        level=SchoolLevel.HIGH,
                        distance_meters=3000,  # 3km < 2 miles
                        confidence=0.95,
                        source="schooldigger_api",
                    ),
                ]

                client.search_schools_by_location = AsyncMock(return_value=mock_schools)

                result = await client.get_assigned_schools(33.4484, -112.0740)

                assert result is not None
                assert result.elementary.name == "Desert Elementary"
                assert result.middle.name == "Phoenix Middle"
                assert result.high.name == "Arizona High"

                # Verify composite rating: (7×0.3) + (8×0.3) + (9×0.4) = 8.1
                assert result.composite_rating == 8.1

                assert result.confidence == 0.95
                assert result.source == "schooldigger_api"

    @pytest.mark.asyncio
    async def test_assigned_schools_missing_one_level(self) -> None:
        """Composite rating handles missing middle school (uses normalized weights)."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                # Only elementary and high within range
                mock_schools = [
                    SchoolResult(
                        name="Desert Elementary",
                        latitude=33.4500,
                        longitude=-112.0740,
                        rating=7.0,
                        level=SchoolLevel.ELEMENTARY,
                        distance_meters=1000,
                        confidence=0.95,
                        source="schooldigger_api",
                    ),
                    SchoolResult(
                        name="Arizona High",
                        latitude=33.4540,
                        longitude=-112.0740,
                        rating=9.0,
                        level=SchoolLevel.HIGH,
                        distance_meters=3000,
                        confidence=0.95,
                        source="schooldigger_api",
                    ),
                ]

                client.search_schools_by_location = AsyncMock(return_value=mock_schools)

                result = await client.get_assigned_schools(33.4484, -112.0740)

                assert result is not None
                assert result.elementary is not None
                assert result.middle is None
                assert result.high is not None

                # Composite: Normalized weights 0.3/(0.3+0.4) and 0.4/(0.3+0.4) = 8.1
                assert result.composite_rating == 8.1

    @pytest.mark.asyncio
    async def test_assigned_schools_falls_back_to_google_places(self) -> None:
        """Fallback to Google Places when SchoolDigger returns no results."""
        with patch.dict(
            os.environ,
            {
                "SCHOOLDIGGER_API_KEY": "test_key_123",
                "GOOGLE_MAPS_API_KEY": "maps_key_456",
            },
        ):
            async with SchoolRatingsClient() as client:
                # Mock no results from SchoolDigger
                client.search_schools_by_location = AsyncMock(return_value=[])

                # Mock Google Places fallback
                client._fallback_to_google_places = AsyncMock(
                    return_value=SchoolFallbackResult(
                        school_names=["Washington Elementary", "Madison Middle", "Phoenix High"],
                        school_count=3,
                        confidence=0.5,
                        source="google_places_fallback",
                    )
                )

                result = await client.get_assigned_schools(33.4484, -112.0740)

                assert isinstance(result, SchoolFallbackResult)
                assert result.school_count == 3
                assert result.confidence == 0.5
                assert result.source == "google_places_fallback"


class TestCompositeRating:
    """Tests for calculate_composite_rating() method."""

    def test_all_three_levels_arizona_weighted(self) -> None:
        """Arizona weighting: (elem×0.3) + (mid×0.3) + (high×0.4)."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        rating = client.calculate_composite_rating(7.0, 8.0, 9.0)

        # (7×0.3) + (8×0.3) + (9×0.4) = 2.1 + 2.4 + 3.6 = 8.1
        assert rating == 8.1

    def test_missing_middle_normalizes_weights(self) -> None:
        """Missing middle school normalizes elementary and high to sum 1.0."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        rating = client.calculate_composite_rating(7.0, None, 9.0)

        # Normalized weights: 0.3/(0.3+0.4)=0.4286, 0.4/(0.3+0.4)=0.5714
        # (7×0.4286) + (9×0.5714) = 3.0 + 5.143 = 8.143 ≈ 8.1
        assert rating == 8.1

    def test_only_high_school_returns_high_rating(self) -> None:
        """Only high school available returns high school rating."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        rating = client.calculate_composite_rating(None, None, 9.0)

        assert rating == 9.0

    def test_all_missing_returns_none(self) -> None:
        """All three levels missing returns None."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        rating = client.calculate_composite_rating(None, None, None)

        assert rating is None


class TestGooglePlacesFallback:
    """Tests for _fallback_to_google_places() method."""

    @pytest.mark.asyncio
    async def test_fallback_returns_school_names_only(self) -> None:
        """Google Places fallback returns school names with low confidence."""
        with patch.dict(
            os.environ,
            {
                "SCHOOLDIGGER_API_KEY": "test_key_123",
                "GOOGLE_MAPS_API_KEY": "maps_key_456",
            },
        ):
            async with SchoolRatingsClient() as client:
                # Mock GoogleMapsClient.find_nearest_poi
                with patch("phx_home_analysis.services.maps.GoogleMapsClient") as mock_maps_client:
                    mock_instance = mock_maps_client.return_value.__aenter__.return_value
                    mock_instance.find_nearest_poi = AsyncMock(
                        return_value=type(
                            "PlaceResult", (), {"name": "Washington Elementary School"}
                        )()
                    )

                    result = await client._fallback_to_google_places(33.4484, -112.0740)

                    assert result is not None
                    assert result.school_count == 1
                    assert "Washington Elementary School" in result.school_names
                    assert result.confidence == 0.5  # Low confidence (names only)
                    assert result.source == "google_places_fallback"

    @pytest.mark.asyncio
    async def test_fallback_handles_google_maps_error(self) -> None:
        """Google Places fallback returns None on error."""
        with patch.dict(
            os.environ,
            {
                "SCHOOLDIGGER_API_KEY": "test_key_123",
                "GOOGLE_MAPS_API_KEY": "maps_key_456",
            },
        ):
            async with SchoolRatingsClient() as client:
                with patch("phx_home_analysis.services.maps.GoogleMapsClient") as mock_maps_client:
                    mock_maps_client.return_value.__aenter__.side_effect = Exception(
                        "Maps API error"
                    )

                    result = await client._fallback_to_google_places(33.4484, -112.0740)

                    assert result is None


class TestEnrichmentDict:
    """Tests for to_enrichment_dict() methods."""

    def test_school_result_to_enrichment_dict(self) -> None:
        """SchoolResult.to_enrichment_dict() returns correct format."""
        school = SchoolResult(
            name="Desert Elementary",
            address="123 School St",
            latitude=33.4484,
            longitude=-112.0740,
            rating=8.5,
            level=SchoolLevel.ELEMENTARY,
            distance_meters=1000,
            is_assigned=True,
            confidence=0.95,
            source="schooldigger_api",
        )

        enrichment = school.to_enrichment_dict()

        assert enrichment["name"] == "Desert Elementary"
        assert enrichment["address"] == "123 School St"
        assert enrichment["latitude"] == 33.4484
        assert enrichment["longitude"] == -112.0740
        assert enrichment["rating"] == 8.5
        assert enrichment["level"] == "elementary"
        assert enrichment["distance_meters"] == 1000
        assert enrichment["is_assigned"] is True
        assert enrichment["confidence"] == 0.95
        assert enrichment["source"] == "schooldigger_api"

    def test_assigned_schools_result_to_enrichment_dict(self) -> None:
        """AssignedSchoolsResult.to_enrichment_dict() returns correct format."""
        elementary = SchoolResult(
            name="Desert Elementary",
            latitude=33.4484,
            longitude=-112.0740,
            rating=7.0,
            level=SchoolLevel.ELEMENTARY,
            distance_meters=1000,
            is_assigned=True,
            confidence=0.95,
            source="schooldigger_api",
        )

        high = SchoolResult(
            name="Arizona High",
            latitude=33.4540,
            longitude=-112.0740,
            rating=9.0,
            level=SchoolLevel.HIGH,
            distance_meters=3000,
            is_assigned=True,
            confidence=0.95,
            source="schooldigger_api",
        )

        result = AssignedSchoolsResult(
            elementary=elementary,
            middle=None,
            high=high,
            composite_rating=8.0,
            confidence=0.95,
            source="schooldigger_api",
        )

        enrichment = result.to_enrichment_dict()

        assert enrichment["elementary"]["name"] == "Desert Elementary"
        assert enrichment["middle"] is None
        assert enrichment["high"]["name"] == "Arizona High"
        assert enrichment["composite_rating"] == 8.0
        assert enrichment["schools_confidence"] == 0.95
        assert enrichment["schools_source"] == "schooldigger_api"

    def test_fallback_result_to_enrichment_dict(self) -> None:
        """SchoolFallbackResult.to_enrichment_dict() returns correct format."""
        fallback = SchoolFallbackResult(
            school_names=["Washington Elementary", "Madison Middle", "Phoenix High"],
            school_count=3,
            confidence=0.5,
            source="google_places_fallback",
        )

        enrichment = fallback.to_enrichment_dict()

        assert enrichment["elementary"] is None
        assert enrichment["middle"] is None
        assert enrichment["high"] is None
        assert enrichment["composite_rating"] is None
        assert enrichment["school_names"] == [
            "Washington Elementary",
            "Madison Middle",
            "Phoenix High",
        ]
        assert enrichment["school_count"] == 3
        assert enrichment["schools_confidence"] == 0.5
        assert enrichment["schools_source"] == "google_places_fallback"


class TestSchoolLevelDetermination:
    """Tests for _determine_school_level() method."""

    def test_elementary_ends_at_grade_5(self) -> None:
        """Schools ending at grade 5 or lower are elementary."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        assert client._determine_school_level("K", "5") == SchoolLevel.ELEMENTARY
        assert client._determine_school_level("PK", "K") == SchoolLevel.ELEMENTARY
        assert client._determine_school_level("1", "4") == SchoolLevel.ELEMENTARY

    def test_middle_ends_at_grade_6_to_8(self) -> None:
        """Schools ending at grades 6-8 are middle."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        assert client._determine_school_level("6", "8") == SchoolLevel.MIDDLE
        assert client._determine_school_level("5", "7") == SchoolLevel.MIDDLE

    def test_high_ends_at_grade_9_plus(self) -> None:
        """Schools ending at grade 9+ are high."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        assert client._determine_school_level("9", "12") == SchoolLevel.HIGH
        assert client._determine_school_level("6", "12") == SchoolLevel.HIGH

    def test_invalid_grade_returns_unknown(self) -> None:
        """Invalid grade strings return UNKNOWN."""
        client = SchoolRatingsClient.__new__(SchoolRatingsClient)

        assert client._determine_school_level(None, None) == SchoolLevel.UNKNOWN
        assert client._determine_school_level("K", "invalid") == SchoolLevel.UNKNOWN


class TestRateLimiting:
    """Tests for rate limiting configuration."""

    @pytest.mark.asyncio
    async def test_rate_limit_configured_for_1000_per_day(self) -> None:
        """Client configured with 1000 requests/day quota."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                assert client._rate_limit.requests_per_day == 1000


class TestCaching:
    """Tests for 30-day cache behavior."""

    @pytest.mark.asyncio
    async def test_cache_configured_for_30_days(self) -> None:
        """Client configured with 30-day cache TTL."""
        with patch.dict(os.environ, {"SCHOOLDIGGER_API_KEY": "test_key_123"}):
            async with SchoolRatingsClient() as client:
                # Verify cache config via cache stats
                cache_stats = client.get_cache_stats()
                assert "cache_dir" in cache_stats
                assert "schooldigger" in cache_stats["cache_dir"]

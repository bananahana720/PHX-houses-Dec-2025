"""Scoring-specific test fixtures that EXTEND root conftest.py fixtures.

This module provides specialized fixtures for scoring module tests,
including PropertyDataBuilder for fluent test data construction and
tier-specific property fixtures for regression testing.

CRITICAL: Imports from root tests/conftest.py - DO NOT DUPLICATE fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import (
    FloodZone,
    Orientation,
    SewerType,
    SolarStatus,
)
from src.phx_home_analysis.domain.value_objects import Score, ScoreBreakdown

if TYPE_CHECKING:
    from collections.abc import Callable

# Re-export root fixtures for convenience (pytest autodiscover handles this)
# These are automatically available from tests/conftest.py
# - sample_property
# - sample_unicorn_property
# - sample_failed_property
# - sample_septic_property
# - sample_property_minimal
# - sample_properties
# - sample_score_breakdown
# - mock_scoring_weights
# - mock_tier_thresholds


# ============================================================================
# PROPERTY DATA BUILDER
# ============================================================================


@dataclass
class PropertyDataBuilder:
    """Fluent builder for PropertyData test objects.

    Provides a chainable API for constructing Property entities with
    specific characteristics for scoring tests. All methods return self
    to enable method chaining.

    Example:
        property = (
            PropertyDataBuilder()
            .with_location(school_rating=9.5, orientation=Orientation.N)
            .with_systems(roof_age=3, hvac_age=2)
            .with_interior(kitchen_layout_score=8.0)
            .build()
        )
    """

    # Base property fields
    _street: str = "100 Test St"
    _city: str = "Phoenix"
    _state: str = "AZ"
    _zip_code: str = "85001"
    _price_num: int = 450000
    _beds: int = 4
    _baths: float = 2.0
    _sqft: int = 2000

    # Location fields (Section A: 250 pts)
    _lot_sqft: int | None = 9000
    _year_built: int | None = 2015
    _garage_spaces: int | None = 2
    _sewer_type: SewerType | None = SewerType.CITY
    _hoa_fee: int | None = 0
    _school_rating: float | None = 7.0
    _orientation: Orientation | None = Orientation.N
    _distance_to_grocery_miles: float | None = 1.5
    _distance_to_highway_miles: float | None = 3.0
    _safety_neighborhood_score: float | None = 7.0
    _parks_walkability_score: float | None = 7.0
    _flood_zone: FloodZone | None = FloodZone.X
    _walk_score: int | None = 50
    _transit_score: int | None = 40
    _air_quality_aqi: int | None = 45

    # Systems fields (Section B: 175 pts)
    _roof_age: int | None = 8
    _hvac_age: int | None = 6
    _has_pool: bool | None = False
    _pool_equipment_age: int | None = None
    _solar_status: SolarStatus | None = SolarStatus.NONE
    _solar_lease_monthly: int | None = None
    _backyard_utility_score: float | None = 7.0
    _tax_annual: int | None = 4000

    # Interior fields (Section C: 180 pts)
    _kitchen_layout_score: float | None = 7.0
    _master_suite_score: float | None = 7.0
    _natural_light_score: float | None = 7.0
    _high_ceilings_score: float | None = 6.5
    _fireplace_present: bool | None = True
    _laundry_area_score: float | None = 7.0
    _aesthetics_score: float | None = 7.0

    # Kill-switch status
    _kill_switch_passed: bool = True

    def with_location(
        self,
        *,
        school_rating: float | None = None,
        orientation: Orientation | None = None,
        distance_to_grocery_miles: float | None = None,
        distance_to_highway_miles: float | None = None,
        safety_neighborhood_score: float | None = None,
        parks_walkability_score: float | None = None,
        flood_zone: FloodZone | None = None,
        walk_score: int | None = None,
        transit_score: int | None = None,
        air_quality_aqi: int | None = None,
    ) -> PropertyDataBuilder:
        """Set location-related fields (Section A: 250 pts).

        Args:
            school_rating: 0-10 school quality rating
            orientation: Property facing direction (N best, W worst)
            distance_to_grocery_miles: Distance to nearest grocery
            distance_to_highway_miles: Distance to nearest highway (closer = worse)
            safety_neighborhood_score: 0-10 neighborhood safety rating
            parks_walkability_score: 0-10 parks and walkability rating
            flood_zone: FEMA flood zone designation
            walk_score: Walk Score (0-100)
            transit_score: Transit Score (0-100)
            air_quality_aqi: AQI value (lower is better)

        Returns:
            Self for method chaining
        """
        if school_rating is not None:
            self._school_rating = school_rating
        if orientation is not None:
            self._orientation = orientation
        if distance_to_grocery_miles is not None:
            self._distance_to_grocery_miles = distance_to_grocery_miles
        if distance_to_highway_miles is not None:
            self._distance_to_highway_miles = distance_to_highway_miles
        if safety_neighborhood_score is not None:
            self._safety_neighborhood_score = safety_neighborhood_score
        if parks_walkability_score is not None:
            self._parks_walkability_score = parks_walkability_score
        if flood_zone is not None:
            self._flood_zone = flood_zone
        if walk_score is not None:
            self._walk_score = walk_score
        if transit_score is not None:
            self._transit_score = transit_score
        if air_quality_aqi is not None:
            self._air_quality_aqi = air_quality_aqi
        return self

    def with_systems(
        self,
        *,
        roof_age: int | None = None,
        hvac_age: int | None = None,
        has_pool: bool | None = None,
        pool_equipment_age: int | None = None,
        solar_status: SolarStatus | None = None,
        solar_lease_monthly: int | None = None,
        backyard_utility_score: float | None = None,
        tax_annual: int | None = None,
    ) -> PropertyDataBuilder:
        """Set systems-related fields (Section B: 175 pts).

        Args:
            roof_age: Age of roof in years (newer = better)
            hvac_age: Age of HVAC in years (newer = better)
            has_pool: Whether property has a pool
            pool_equipment_age: Age of pool equipment in years
            solar_status: Solar panel status (OWNED/LEASED/NONE)
            solar_lease_monthly: Monthly solar lease payment if leased
            backyard_utility_score: 0-10 backyard usability rating
            tax_annual: Annual property tax

        Returns:
            Self for method chaining
        """
        if roof_age is not None:
            self._roof_age = roof_age
        if hvac_age is not None:
            self._hvac_age = hvac_age
        if has_pool is not None:
            self._has_pool = has_pool
        if pool_equipment_age is not None:
            self._pool_equipment_age = pool_equipment_age
        if solar_status is not None:
            self._solar_status = solar_status
        if solar_lease_monthly is not None:
            self._solar_lease_monthly = solar_lease_monthly
        if backyard_utility_score is not None:
            self._backyard_utility_score = backyard_utility_score
        if tax_annual is not None:
            self._tax_annual = tax_annual
        return self

    def with_interior(
        self,
        *,
        kitchen_layout_score: float | None = None,
        master_suite_score: float | None = None,
        natural_light_score: float | None = None,
        high_ceilings_score: float | None = None,
        fireplace_present: bool | None = None,
        laundry_area_score: float | None = None,
        aesthetics_score: float | None = None,
    ) -> PropertyDataBuilder:
        """Set interior-related fields (Section C: 180 pts).

        Args:
            kitchen_layout_score: 0-10 kitchen layout quality
            master_suite_score: 0-10 master suite quality
            natural_light_score: 0-10 natural light quality
            high_ceilings_score: 0-10 ceiling height rating
            fireplace_present: Whether property has fireplace
            laundry_area_score: 0-10 laundry area quality
            aesthetics_score: 0-10 overall aesthetics rating

        Returns:
            Self for method chaining
        """
        if kitchen_layout_score is not None:
            self._kitchen_layout_score = kitchen_layout_score
        if master_suite_score is not None:
            self._master_suite_score = master_suite_score
        if natural_light_score is not None:
            self._natural_light_score = natural_light_score
        if high_ceilings_score is not None:
            self._high_ceilings_score = high_ceilings_score
        if fireplace_present is not None:
            self._fireplace_present = fireplace_present
        if laundry_area_score is not None:
            self._laundry_area_score = laundry_area_score
        if aesthetics_score is not None:
            self._aesthetics_score = aesthetics_score
        return self

    def with_base_info(
        self,
        *,
        street: str | None = None,
        city: str | None = None,
        price_num: int | None = None,
        beds: int | None = None,
        baths: float | None = None,
        sqft: int | None = None,
        lot_sqft: int | None = None,
        year_built: int | None = None,
        garage_spaces: int | None = None,
        sewer_type: SewerType | None = None,
        hoa_fee: int | None = None,
    ) -> PropertyDataBuilder:
        """Set base property info and kill-switch related fields.

        Args:
            street: Street address
            city: City name
            price_num: Numeric price value
            beds: Number of bedrooms (kill-switch: >= 4)
            baths: Number of bathrooms (kill-switch: >= 2.0)
            sqft: Square footage (kill-switch: > 1800)
            lot_sqft: Lot size in sqft (kill-switch: 7000-15000)
            year_built: Year built (kill-switch: <= 2023)
            garage_spaces: Number of garage spaces (kill-switch: >= 2)
            sewer_type: Sewer type (kill-switch: CITY)
            hoa_fee: HOA fee (kill-switch: = 0)

        Returns:
            Self for method chaining
        """
        if street is not None:
            self._street = street
        if city is not None:
            self._city = city
        if price_num is not None:
            self._price_num = price_num
        if beds is not None:
            self._beds = beds
        if baths is not None:
            self._baths = baths
        if sqft is not None:
            self._sqft = sqft
        if lot_sqft is not None:
            self._lot_sqft = lot_sqft
        if year_built is not None:
            self._year_built = year_built
        if garage_spaces is not None:
            self._garage_spaces = garage_spaces
        if sewer_type is not None:
            self._sewer_type = sewer_type
        if hoa_fee is not None:
            self._hoa_fee = hoa_fee
        return self

    def with_kill_switch_status(self, passed: bool) -> PropertyDataBuilder:
        """Set kill-switch passed status.

        Args:
            passed: Whether property passed kill-switch evaluation

        Returns:
            Self for method chaining
        """
        self._kill_switch_passed = passed
        return self

    def build(self) -> Property:
        """Build the Property entity with configured values.

        Returns:
            Property entity with all configured fields
        """
        full_address = f"{self._street}, {self._city}, {self._state} {self._zip_code}"
        price_per_sqft = self._price_num / self._sqft if self._sqft > 0 else 0.0

        prop = Property(
            street=self._street,
            city=self._city,
            state=self._state,
            zip_code=self._zip_code,
            full_address=full_address,
            price=f"${self._price_num:,}",
            price_num=self._price_num,
            beds=self._beds,
            baths=self._baths,
            sqft=self._sqft,
            price_per_sqft_raw=price_per_sqft,
            lot_sqft=self._lot_sqft,
            year_built=self._year_built,
            garage_spaces=self._garage_spaces,
            sewer_type=self._sewer_type,
            tax_annual=self._tax_annual,
            hoa_fee=self._hoa_fee,
            school_rating=self._school_rating,
            orientation=self._orientation,
            distance_to_grocery_miles=self._distance_to_grocery_miles,
            distance_to_highway_miles=self._distance_to_highway_miles,
            solar_status=self._solar_status,
            solar_lease_monthly=self._solar_lease_monthly,
            has_pool=self._has_pool,
            pool_equipment_age=self._pool_equipment_age,
            roof_age=self._roof_age,
            hvac_age=self._hvac_age,
            kitchen_layout_score=self._kitchen_layout_score,
            master_suite_score=self._master_suite_score,
            natural_light_score=self._natural_light_score,
            high_ceilings_score=self._high_ceilings_score,
            fireplace_present=self._fireplace_present,
            laundry_area_score=self._laundry_area_score,
            aesthetics_score=self._aesthetics_score,
            backyard_utility_score=self._backyard_utility_score,
            safety_neighborhood_score=self._safety_neighborhood_score,
            parks_walkability_score=self._parks_walkability_score,
            flood_zone=self._flood_zone,
            walk_score=self._walk_score,
            transit_score=self._transit_score,
            air_quality_aqi=self._air_quality_aqi,
        )

        prop.kill_switch_passed = self._kill_switch_passed
        return prop


# ============================================================================
# GOLDEN PROPERTY FIXTURES (TIER-SPECIFIC)
# ============================================================================


@pytest.fixture
def contender_property() -> Property:
    """Create a property that scores in Contender tier (363-483 points).

    This fixture creates a property with moderate scores across all
    dimensions, targeting the middle tier classification.

    Target scores:
    - Location: ~150/250 (60%)
    - Systems: ~105/175 (60%)
    - Interior: ~108/180 (60%)
    - Total: ~363/605 (60%) - Contender threshold

    Returns:
        Property scoring in Contender tier range
    """
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="200 Contender Way",
            city="Phoenix",
            price_num=475000,
            beds=4,
            baths=2.0,
            sqft=2100,
            lot_sqft=8500,
            year_built=2012,
            garage_spaces=2,
            hoa_fee=0,
        )
        .with_location(
            school_rating=6.5,
            orientation=Orientation.E,  # East (15pts vs 25pts North)
            distance_to_grocery_miles=2.0,
            safety_neighborhood_score=6.5,
            parks_walkability_score=6.0,
            flood_zone=FloodZone.X,
            walk_score=45,
            transit_score=35,
            air_quality_aqi=55,
        )
        .with_systems(
            roof_age=10,
            hvac_age=8,
            has_pool=False,
            backyard_utility_score=6.0,
            tax_annual=4000,
        )
        .with_interior(
            kitchen_layout_score=6.0,
            master_suite_score=6.5,
            natural_light_score=6.0,
            high_ceilings_score=5.5,
            fireplace_present=True,
            laundry_area_score=6.0,
            aesthetics_score=6.0,
        )
        .build()
    )


@pytest.fixture
def pass_tier_property() -> Property:
    """Create a property that scores in Pass tier (<363 points).

    This fixture creates a property with below-average scores,
    targeting the lowest passing tier classification.

    Target scores:
    - Location: ~100/250 (40%)
    - Systems: ~70/175 (40%)
    - Interior: ~72/180 (40%)
    - Total: ~242/605 (40%) - Pass tier

    Returns:
        Property scoring in Pass tier range
    """
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="300 Pass Tier Rd",
            city="Phoenix",
            price_num=400000,
            beds=4,
            baths=2.0,
            sqft=1900,
            lot_sqft=7500,
            year_built=2005,
            garage_spaces=2,
            hoa_fee=0,
        )
        .with_location(
            school_rating=4.5,
            orientation=Orientation.W,  # West (0pts - worst)
            distance_to_grocery_miles=4.0,
            safety_neighborhood_score=4.5,
            parks_walkability_score=4.0,
            flood_zone=FloodZone.X,
            walk_score=25,
            transit_score=20,
            air_quality_aqi=75,
        )
        .with_systems(
            roof_age=18,
            hvac_age=15,
            has_pool=False,
            backyard_utility_score=4.0,
            tax_annual=3500,
        )
        .with_interior(
            kitchen_layout_score=4.0,
            master_suite_score=4.5,
            natural_light_score=4.0,
            high_ceilings_score=4.0,
            fireplace_present=False,
            laundry_area_score=4.0,
            aesthetics_score=4.0,
        )
        .build()
    )


# ============================================================================
# BOUNDARY CONDITION FIXTURES
# ============================================================================


@pytest.fixture
def zero_score_property() -> Property:
    """Create a property with minimum possible scores (all 0).

    This fixture tests the lower boundary condition where all
    manual assessment scores are set to minimum values.

    Returns:
        Property with minimum scores
    """
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="0 Zero Score St",
            city="Phoenix",
            price_num=350000,
            beds=4,
            baths=2.0,
            sqft=1850,
            lot_sqft=7000,
            year_built=2020,
            garage_spaces=2,
            hoa_fee=0,
        )
        .with_location(
            school_rating=0.0,
            orientation=Orientation.W,
            distance_to_grocery_miles=10.0,
            safety_neighborhood_score=0.0,
            parks_walkability_score=0.0,
            flood_zone=FloodZone.AE,  # High flood risk
            walk_score=0,
            transit_score=0,
            air_quality_aqi=200,  # Very poor AQI
        )
        .with_systems(
            roof_age=30,
            hvac_age=25,
            has_pool=False,
            backyard_utility_score=0.0,
            tax_annual=6000,
        )
        .with_interior(
            kitchen_layout_score=0.0,
            master_suite_score=0.0,
            natural_light_score=0.0,
            high_ceilings_score=0.0,
            fireplace_present=False,
            laundry_area_score=0.0,
            aesthetics_score=0.0,
        )
        .build()
    )


@pytest.fixture
def max_score_property() -> Property:
    """Create a property with maximum possible scores (all 10).

    This fixture tests the upper boundary condition where all
    manual assessment scores are set to maximum values.

    Returns:
        Property with maximum scores
    """
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="10 Max Score Blvd",
            city="Paradise Valley",
            price_num=600000,
            beds=5,
            baths=3.5,
            sqft=3200,
            lot_sqft=12000,
            year_built=2022,
            garage_spaces=3,
            hoa_fee=0,
        )
        .with_location(
            school_rating=10.0,
            orientation=Orientation.N,  # North (best)
            distance_to_grocery_miles=0.3,
            safety_neighborhood_score=10.0,
            parks_walkability_score=10.0,
            flood_zone=FloodZone.X,  # Minimal flood risk
            walk_score=100,
            transit_score=100,
            air_quality_aqi=0,  # Perfect AQI
        )
        .with_systems(
            roof_age=0,  # Brand new
            hvac_age=0,  # Brand new
            has_pool=True,
            pool_equipment_age=0,
            solar_status=SolarStatus.OWNED,
            backyard_utility_score=10.0,
            tax_annual=5000,
        )
        .with_interior(
            kitchen_layout_score=10.0,
            master_suite_score=10.0,
            natural_light_score=10.0,
            high_ceilings_score=10.0,
            fireplace_present=True,
            laundry_area_score=10.0,
            aesthetics_score=10.0,
        )
        .build()
    )


@pytest.fixture
def tier_boundary_unicorn() -> Property:
    """Create a property at exact Unicorn threshold boundary (484 points).

    This fixture tests the exact boundary between Contender and Unicorn
    tiers. Score of exactly 484 should classify as Unicorn (>= threshold).

    Returns:
        Property at Unicorn boundary threshold
    """
    # Target 484/605 = ~80% across all sections
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="484 Unicorn Threshold Ln",
            city="Scottsdale",
            price_num=550000,
            beds=5,
            baths=3.0,
            sqft=2800,
            lot_sqft=10000,
            year_built=2018,
            garage_spaces=3,
            hoa_fee=0,
        )
        .with_location(
            school_rating=8.0,
            orientation=Orientation.N,
            distance_to_grocery_miles=0.8,
            safety_neighborhood_score=8.0,
            parks_walkability_score=8.0,
            flood_zone=FloodZone.X,
            walk_score=70,
            transit_score=60,
            air_quality_aqi=35,
        )
        .with_systems(
            roof_age=4,
            hvac_age=3,
            has_pool=True,
            pool_equipment_age=2,
            solar_status=SolarStatus.OWNED,
            backyard_utility_score=8.0,
            tax_annual=4500,
        )
        .with_interior(
            kitchen_layout_score=8.0,
            master_suite_score=8.0,
            natural_light_score=8.0,
            high_ceilings_score=8.0,
            fireplace_present=True,
            laundry_area_score=8.0,
            aesthetics_score=8.0,
        )
        .build()
    )


@pytest.fixture
def tier_boundary_contender() -> Property:
    """Create a property at exact Contender threshold boundary (363 points).

    This fixture tests the exact boundary between Pass and Contender
    tiers. Score of exactly 363 should classify as Contender (>= threshold).

    Returns:
        Property at Contender boundary threshold
    """
    # Target 363/605 = ~60% across all sections
    return (
        PropertyDataBuilder()
        .with_base_info(
            street="363 Contender Threshold Ave",
            city="Phoenix",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2000,
            lot_sqft=8000,
            year_built=2010,
            garage_spaces=2,
            hoa_fee=0,
        )
        .with_location(
            school_rating=6.0,
            orientation=Orientation.E,
            distance_to_grocery_miles=2.0,
            safety_neighborhood_score=6.0,
            parks_walkability_score=6.0,
            flood_zone=FloodZone.X,
            walk_score=40,
            transit_score=35,
            air_quality_aqi=50,
        )
        .with_systems(
            roof_age=12,
            hvac_age=10,
            has_pool=False,
            backyard_utility_score=6.0,
            tax_annual=4000,
        )
        .with_interior(
            kitchen_layout_score=6.0,
            master_suite_score=6.0,
            natural_light_score=6.0,
            high_ceilings_score=6.0,
            fireplace_present=True,
            laundry_area_score=6.0,
            aesthetics_score=6.0,
        )
        .build()
    )


# ============================================================================
# SCORE BREAKDOWN FIXTURES
# ============================================================================


@pytest.fixture
def empty_score_breakdown() -> ScoreBreakdown:
    """Create a ScoreBreakdown with empty score lists.

    Returns:
        ScoreBreakdown with all empty lists (0 total score)
    """
    return ScoreBreakdown(
        location_scores=[],
        systems_scores=[],
        interior_scores=[],
    )


@pytest.fixture
def max_score_breakdown() -> ScoreBreakdown:
    """Create a ScoreBreakdown with maximum scores (605 total).

    Returns:
        ScoreBreakdown with maximum possible scores
    """
    return ScoreBreakdown(
        location_scores=[Score(criterion="Max Location", base_score=10.0, weight=250)],
        systems_scores=[Score(criterion="Max Systems", base_score=10.0, weight=175)],
        interior_scores=[Score(criterion="Max Interior", base_score=10.0, weight=180)],
    )


@pytest.fixture
def half_score_breakdown() -> ScoreBreakdown:
    """Create a ScoreBreakdown at exactly 50% (302.5 total).

    Returns:
        ScoreBreakdown at 50% of maximum
    """
    return ScoreBreakdown(
        location_scores=[Score(criterion="Half Location", base_score=5.0, weight=250)],
        systems_scores=[Score(criterion="Half Systems", base_score=5.0, weight=175)],
        interior_scores=[Score(criterion="Half Interior", base_score=5.0, weight=180)],
    )


@pytest.fixture
def realistic_score_breakdown() -> ScoreBreakdown:
    """Create a realistic ScoreBreakdown with multiple scores per section.

    This fixture mimics actual PropertyScorer output with multiple criteria
    per section, matching the real 605-point scoring structure.

    Section A (Location): 9 criteria totaling 250 pts max
    Section B (Systems): 6 criteria totaling 175 pts max
    Section C (Interior): 7 criteria totaling 180 pts max

    Returns:
        ScoreBreakdown with realistic multi-score structure (~420 pts, Contender tier)
    """
    return ScoreBreakdown(
        location_scores=[
            Score(criterion="School District Rating", base_score=7.5, weight=42),
            Score(criterion="Noise Level / Quietness", base_score=8.0, weight=30),
            Score(criterion="Crime Index / Safety", base_score=6.5, weight=47),
            Score(criterion="Supermarket Proximity", base_score=7.0, weight=23),
            Score(criterion="Parks & Walkability", base_score=6.0, weight=23),
            Score(criterion="Sun Orientation", base_score=10.0, weight=25, note="North-facing"),
            Score(criterion="Flood Risk", base_score=9.0, weight=23, note="Zone X"),
            Score(criterion="Walk/Transit Score", base_score=5.5, weight=22),
            Score(criterion="Air Quality", base_score=8.0, weight=15),
        ],
        systems_scores=[
            Score(criterion="Roof Condition/Age", base_score=7.0, weight=45, note="8 years old"),
            Score(criterion="Backyard Utility", base_score=7.5, weight=35),
            Score(criterion="Plumbing/Electrical", base_score=6.5, weight=35, note="Built 2015"),
            Score(criterion="Pool Condition", base_score=5.0, weight=20, note="No pool"),
            Score(criterion="Cost Efficiency", base_score=6.0, weight=35, note="~$3,800/mo"),
            Score(criterion="Solar Status", base_score=5.0, weight=5, note="No solar"),
        ],
        interior_scores=[
            Score(criterion="Kitchen Layout", base_score=7.5, weight=40),
            Score(criterion="Master Suite", base_score=7.0, weight=35),
            Score(criterion="Natural Light", base_score=8.0, weight=30),
            Score(criterion="High Ceilings", base_score=6.0, weight=25, note="9 ft"),
            Score(criterion="Fireplace", base_score=10.0, weight=20, note="Gas fireplace"),
            Score(criterion="Laundry Area", base_score=7.5, weight=20, note="Dedicated room"),
            Score(criterion="Aesthetics", base_score=7.0, weight=10),
        ],
    )


# ============================================================================
# BUILDER FIXTURE FACTORY
# ============================================================================


@pytest.fixture
def property_builder() -> Callable[[], PropertyDataBuilder]:
    """Factory fixture for creating PropertyDataBuilder instances.

    This fixture returns a factory function that creates fresh
    PropertyDataBuilder instances, enabling multiple builders
    in a single test.

    Returns:
        Factory function that creates new PropertyDataBuilder

    Example:
        def test_something(property_builder):
            builder1 = property_builder()
            builder2 = property_builder()
            prop1 = builder1.with_location(school_rating=8.0).build()
            prop2 = builder2.with_interior(kitchen_layout_score=9.0).build()
    """

    def _create_builder() -> PropertyDataBuilder:
        return PropertyDataBuilder()

    return _create_builder


# ============================================================================
# FIXTURE VALIDATION TESTS
# ============================================================================


def test_contender_property_scores_as_contender(contender_property: Property) -> None:
    """Validate that contender_property fixture actually scores as Contender tier.

    This test ensures the contender_property fixture produces a property that
    scores within the Contender tier range (363-483 points) when run through
    the PropertyScorer.

    Regression test for Issue #7: Fixture tier validation.
    """
    from src.phx_home_analysis.domain.enums import Tier
    from src.phx_home_analysis.services.scoring.scorer import PropertyScorer

    scorer = PropertyScorer()
    contender_property.kill_switch_passed = True
    scorer.score_all([contender_property])

    # Verify it scores as Contender tier
    assert contender_property.tier == Tier.CONTENDER, (
        f"contender_property fixture scored as {contender_property.tier.value} "
        f"(score: {contender_property.total_score:.1f}), expected Contender tier. "
        "Adjust fixture scores to target 363-483 point range."
    )

    # Verify score is within expected range
    assert 363 <= contender_property.total_score < 484, (
        f"contender_property score {contender_property.total_score:.1f} is outside "
        f"Contender range (363-483). Adjust fixture to target ~420 pts."
    )

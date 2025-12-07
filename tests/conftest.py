"""Pytest configuration and shared fixtures for PHX Home Analysis tests.

This module provides reusable test fixtures for property creation, enrichment data,
and configuration, ensuring consistency across all test modules.
"""

import pytest

from src.phx_home_analysis.config.scoring_weights import ScoringWeights, TierThresholds
from src.phx_home_analysis.config.settings import AppConfig
from src.phx_home_analysis.domain.entities import EnrichmentData, Property
from src.phx_home_analysis.domain.enums import Orientation, SewerType, SolarStatus
from src.phx_home_analysis.domain.value_objects import Score, ScoreBreakdown

# ============================================================================
# PROPERTY FIXTURES
# ============================================================================


@pytest.fixture
def sample_property():
    """Create a basic property with all required fields.

    Returns a Property entity fully populated with realistic data for testing.
    This property passes all kill switches and has moderate scores.

    Returns:
        Property: Sample property in Phoenix, 4bd/2ba, $475k
    """
    return Property(
        street="123 Desert Rose Ln",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Desert Rose Ln, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=215.9,
        # County assessor data
        lot_sqft=9500,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        tax_annual=4200,
        # HOA and location data
        hoa_fee=0,
        commute_minutes=25,
        school_district="Phoenix Union High School District",
        school_rating=7.5,
        orientation=Orientation.N,
        distance_to_grocery_miles=1.2,
        distance_to_highway_miles=3.5,
        # Arizona-specific features
        solar_status=SolarStatus.NONE,
        solar_lease_monthly=None,
        has_pool=False,
        pool_equipment_age=None,
        roof_age=8,
        hvac_age=6,
        # Manual assessment scores (0-10 scale)
        kitchen_layout_score=7.0,
        master_suite_score=7.5,
        natural_light_score=8.0,
        high_ceilings_score=6.5,
        fireplace_present=True,
        laundry_area_score=7.0,
        aesthetics_score=7.0,
        backyard_utility_score=6.5,
        safety_neighborhood_score=7.5,
        parks_walkability_score=6.5,
    )


@pytest.fixture
def sample_unicorn_property():
    """Create a property that scores as a Unicorn (>400 points).

    A premium property with excellent scores across all categories.

    Returns:
        Property: High-scoring property with ideal characteristics
    """
    return Property(
        street="500 Camelback Rd",
        city="Paradise Valley",
        state="AZ",
        zip_code="85253",
        full_address="500 Camelback Rd, Paradise Valley, AZ 85253",
        price="$650,000",
        price_num=650000,
        beds=5,
        baths=3.5,
        sqft=3500,
        price_per_sqft_raw=185.7,
        lot_sqft=12000,
        year_built=2015,
        garage_spaces=3,
        sewer_type=SewerType.CITY,
        tax_annual=5800,
        hoa_fee=0,
        commute_minutes=20,
        school_district="Paradise Valley Unified School District",
        school_rating=9.5,
        orientation=Orientation.NE,
        distance_to_grocery_miles=0.8,
        distance_to_highway_miles=2.0,
        solar_status=SolarStatus.OWNED,
        solar_lease_monthly=None,
        has_pool=True,
        pool_equipment_age=2,
        roof_age=5,
        hvac_age=4,
        kitchen_layout_score=9.5,
        master_suite_score=9.5,
        natural_light_score=9.0,
        high_ceilings_score=9.0,
        fireplace_present=True,
        laundry_area_score=9.0,
        aesthetics_score=9.5,
        backyard_utility_score=9.0,
        safety_neighborhood_score=9.5,
        parks_walkability_score=8.5,
    )


@pytest.fixture
def sample_failed_property():
    """Create a property that fails kill switches (HOA fee).

    Returns a property that should fail the NO_HOA kill switch.

    Returns:
        Property: Property with $200/month HOA fee
    """
    return Property(
        street="789 Sunset Dr",
        city="Scottsdale",
        state="AZ",
        zip_code="85251",
        full_address="789 Sunset Dr, Scottsdale, AZ 85251",
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.0,
        sqft=2100,
        price_per_sqft_raw=214.3,
        lot_sqft=8500,
        year_built=2012,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        tax_annual=4000,
        hoa_fee=200,  # FAILS kill switch
        commute_minutes=30,
        school_district="Scottsdale Unified School District",
        school_rating=8.0,
        orientation=Orientation.S,
        distance_to_grocery_miles=1.5,
        distance_to_highway_miles=4.0,
        solar_status=SolarStatus.NONE,
        solar_lease_monthly=None,
        has_pool=False,
        pool_equipment_age=None,
        roof_age=10,
        hvac_age=8,
        kitchen_layout_score=6.0,
        master_suite_score=6.5,
        natural_light_score=7.0,
        high_ceilings_score=6.0,
        fireplace_present=False,
        laundry_area_score=5.5,
        aesthetics_score=6.0,
        backyard_utility_score=5.5,
        safety_neighborhood_score=7.0,
        parks_walkability_score=6.0,
    )


@pytest.fixture
def sample_septic_property():
    """Create a property with septic system (fails kill switch).

    Returns:
        Property: Property with septic system
    """
    return Property(
        street="456 Desert Road",
        city="Apache Junction",
        state="AZ",
        zip_code="85220",
        full_address="456 Desert Road, Apache Junction, AZ 85220",
        price="$380,000",
        price_num=380000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=190.0,
        lot_sqft=10000,
        year_built=2008,
        garage_spaces=2,
        sewer_type=SewerType.SEPTIC,  # FAILS kill switch
        tax_annual=3400,
        hoa_fee=0,
        commute_minutes=45,
        school_district="Apache Junction Unified School District",
        school_rating=6.5,
        orientation=Orientation.W,
        distance_to_grocery_miles=3.0,
        distance_to_highway_miles=5.0,
        solar_status=SolarStatus.NONE,
        solar_lease_monthly=None,
        has_pool=False,
        pool_equipment_age=None,
        roof_age=12,
        hvac_age=10,
        kitchen_layout_score=5.0,
        master_suite_score=5.5,
        natural_light_score=6.0,
        high_ceilings_score=5.0,
        fireplace_present=False,
        laundry_area_score=5.0,
        aesthetics_score=5.5,
        backyard_utility_score=5.5,
        safety_neighborhood_score=6.5,
        parks_walkability_score=5.5,
    )


@pytest.fixture
def sample_property_minimal():
    """Create a property with only required fields and None optional fields.

    Useful for testing handling of missing/incomplete data.

    Returns:
        Property: Property with minimal data
    """
    return Property(
        street="100 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="100 Main St, Phoenix, AZ 85001",
        price="$400,000",
        price_num=400000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=200.0,
        # Optional fields left None
        lot_sqft=None,
        year_built=None,
        garage_spaces=None,
        sewer_type=None,
        tax_annual=None,
        hoa_fee=None,
        commute_minutes=None,
        school_district=None,
        school_rating=None,
        orientation=None,
        distance_to_grocery_miles=None,
        distance_to_highway_miles=None,
        solar_status=None,
        solar_lease_monthly=None,
        has_pool=None,
        pool_equipment_age=None,
        roof_age=None,
        hvac_age=None,
        latitude=None,
        longitude=None,
        kitchen_layout_score=None,
        master_suite_score=None,
        natural_light_score=None,
        high_ceilings_score=None,
        fireplace_present=None,
        laundry_area_score=None,
        aesthetics_score=None,
        backyard_utility_score=None,
        safety_neighborhood_score=None,
        parks_walkability_score=None,
    )


@pytest.fixture
def sample_properties():
    """Create a collection of 5+ properties with various characteristics.

    Includes properties that pass, fail, and edge case scenarios.

    Returns:
        list: List of 6 Property entities with varied characteristics
    """
    return [
        # Property 1: Passes all kill switches, moderate score
        Property(
            street="123 Desert Rose Ln",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Desert Rose Ln, Phoenix, AZ 85001",
            price="$475,000",
            price_num=475000,
            beds=4,
            baths=2.0,
            sqft=2200,
            price_per_sqft_raw=215.9,
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type=SewerType.CITY,
            tax_annual=4200,
            hoa_fee=0,
            commute_minutes=25,
            school_rating=7.5,
            orientation=Orientation.N,
            distance_to_grocery_miles=1.2,
            distance_to_highway_miles=3.5,
            kitchen_layout_score=7.0,
            master_suite_score=7.5,
            natural_light_score=8.0,
            high_ceilings_score=6.5,
            fireplace_present=True,
            laundry_area_score=7.0,
            aesthetics_score=7.0,
            backyard_utility_score=6.5,
            safety_neighborhood_score=7.5,
            parks_walkability_score=6.5,
        ),
        # Property 2: Fails kill switch (HOA fee)
        Property(
            street="789 Sunset Dr",
            city="Scottsdale",
            state="AZ",
            zip_code="85251",
            full_address="789 Sunset Dr, Scottsdale, AZ 85251",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=214.3,
            lot_sqft=8500,
            year_built=2012,
            garage_spaces=2,
            sewer_type=SewerType.CITY,
            tax_annual=4000,
            hoa_fee=200,
            commute_minutes=30,
            school_rating=8.0,
            orientation=Orientation.S,
            distance_to_grocery_miles=1.5,
            distance_to_highway_miles=4.0,
            kitchen_layout_score=6.0,
            master_suite_score=6.5,
        ),
        # Property 3: Fails kill switch (septic system)
        Property(
            street="456 Desert Road",
            city="Apache Junction",
            state="AZ",
            zip_code="85220",
            full_address="456 Desert Road, Apache Junction, AZ 85220",
            price="$380,000",
            price_num=380000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=190.0,
            lot_sqft=10000,
            year_built=2008,
            garage_spaces=2,
            sewer_type=SewerType.SEPTIC,
            tax_annual=3400,
            hoa_fee=0,
            commute_minutes=45,
            school_rating=6.5,
            orientation=Orientation.W,
            distance_to_grocery_miles=3.0,
            distance_to_highway_miles=5.0,
            kitchen_layout_score=5.0,
        ),
        # Property 4: Fails kill switch (lot too small)
        Property(
            street="222 Cactus Ave",
            city="Tempe",
            state="AZ",
            zip_code="85281",
            full_address="222 Cactus Ave, Tempe, AZ 85281",
            price="$420,000",
            price_num=420000,
            beds=4,
            baths=2.0,
            sqft=1900,
            price_per_sqft_raw=221.1,
            lot_sqft=6500,  # Below 7000 minimum
            year_built=2014,
            garage_spaces=2,
            sewer_type=SewerType.CITY,
            tax_annual=3750,
            hoa_fee=0,
            commute_minutes=20,
            school_rating=8.5,
            orientation=Orientation.E,
            distance_to_grocery_miles=1.0,
            distance_to_highway_miles=2.5,
            kitchen_layout_score=7.5,
        ),
        # Property 5: Fails kill switch (insufficient bedrooms)
        Property(
            street="333 Saguaro Blvd",
            city="Chandler",
            state="AZ",
            zip_code="85224",
            full_address="333 Saguaro Blvd, Chandler, AZ 85224",
            price="$350,000",
            price_num=350000,
            beds=3,  # Below 4 minimum
            baths=2.0,
            sqft=1800,
            price_per_sqft_raw=194.4,
            lot_sqft=8000,
            year_built=2018,
            garage_spaces=2,
            sewer_type=SewerType.CITY,
            tax_annual=3100,
            hoa_fee=0,
            commute_minutes=35,
            school_rating=8.0,
            orientation=Orientation.NW,
            distance_to_grocery_miles=1.8,
            distance_to_highway_miles=3.0,
            kitchen_layout_score=7.0,
        ),
        # Property 6: High-quality property (Unicorn potential)
        Property(
            street="500 Camelback Rd",
            city="Paradise Valley",
            state="AZ",
            zip_code="85253",
            full_address="500 Camelback Rd, Paradise Valley, AZ 85253",
            price="$650,000",
            price_num=650000,
            beds=5,
            baths=3.5,
            sqft=3500,
            price_per_sqft_raw=185.7,
            lot_sqft=12000,
            year_built=2015,
            garage_spaces=3,
            sewer_type=SewerType.CITY,
            tax_annual=5800,
            hoa_fee=0,
            commute_minutes=20,
            school_rating=9.5,
            orientation=Orientation.NE,
            distance_to_grocery_miles=0.8,
            distance_to_highway_miles=2.0,
            solar_status=SolarStatus.OWNED,
            has_pool=True,
            pool_equipment_age=2,
            roof_age=5,
            hvac_age=4,
            kitchen_layout_score=9.5,
            master_suite_score=9.5,
            natural_light_score=9.0,
            high_ceilings_score=9.0,
            fireplace_present=True,
            laundry_area_score=9.0,
            aesthetics_score=9.5,
            backyard_utility_score=9.0,
            safety_neighborhood_score=9.5,
            parks_walkability_score=8.5,
        ),
    ]


# ============================================================================
# ENRICHMENT DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_enrichment():
    """Create enrichment data for a property.

    Returns:
        dict: Enrichment data matching enrichment_data.json structure
    """
    return {
        "123 Desert Rose Ln, Phoenix, AZ 85001": {
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "tax_annual": 4200,
            "hoa_fee": 0,
            "commute_minutes": 25,
            "school_district": "Phoenix Union High School District",
            "school_rating": 7.5,
            "orientation": "north",
            "distance_to_grocery_miles": 1.2,
            "distance_to_highway_miles": 3.5,
            "solar_status": "none",
            "solar_lease_monthly": None,
            "has_pool": False,
            "pool_equipment_age": None,
            "roof_age": 8,
            "hvac_age": 6,
        }
    }


@pytest.fixture
def sample_enrichment_data():
    """Create EnrichmentData value object.

    Returns:
        EnrichmentData: Enrichment data for a specific property
    """
    return EnrichmentData(
        full_address="123 Desert Rose Ln, Phoenix, AZ 85001",
        lot_sqft=9500,
        year_built=2010,
        garage_spaces=2,
        sewer_type="city",
        tax_annual=4200,
        hoa_fee=0,
        commute_minutes=25,
        school_district="Phoenix Union High School District",
        school_rating=7.5,
        orientation="north",
        distance_to_grocery_miles=1.2,
        distance_to_highway_miles=3.5,
        solar_status="none",
        solar_lease_monthly=None,
        has_pool=False,
        pool_equipment_age=None,
        roof_age=8,
        hvac_age=6,
    )


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def mock_config():
    """Create AppConfig for testing.

    Returns:
        AppConfig: Configuration with default values
    """
    return AppConfig.default()


@pytest.fixture
def mock_scoring_weights():
    """Create ScoringWeights for testing.

    Returns:
        ScoringWeights: Default scoring configuration
    """
    return ScoringWeights()


@pytest.fixture
def mock_tier_thresholds():
    """Create TierThresholds for testing.

    Returns:
        TierThresholds: Default tier classification thresholds
    """
    return TierThresholds()


# ============================================================================
# VALUE OBJECT FIXTURES
# ============================================================================


@pytest.fixture
def sample_scores():
    """Create a list of Score value objects.

    Returns:
        list: List of Score objects for location category
    """
    return [
        Score(criterion="School District Rating", base_score=7.5, weight=50),
        Score(criterion="Quietness/Noise", base_score=8.0, weight=50),
        Score(criterion="Safety/Neighborhood", base_score=7.5, weight=50),
    ]


@pytest.fixture
def sample_score_breakdown():
    """Create a ScoreBreakdown value object.

    Returns:
        ScoreBreakdown: Complete scoring breakdown for a property
    """
    location_scores = [
        Score(criterion="School District Rating", base_score=7.5, weight=50),
        Score(criterion="Quietness/Noise", base_score=8.0, weight=50),
        Score(criterion="Safety/Neighborhood", base_score=7.5, weight=50),
        Score(criterion="Supermarket Proximity", base_score=7.0, weight=40),
        Score(criterion="Parks & Walkability", base_score=6.5, weight=30),
        Score(criterion="Sun Orientation", base_score=7.0, weight=30),
    ]

    systems_scores = [
        Score(criterion="Roof Condition/Age", base_score=8.0, weight=50),
        Score(criterion="Backyard Utility", base_score=6.5, weight=40),
        Score(criterion="Plumbing/Electrical", base_score=7.5, weight=40),
        Score(criterion="Pool Condition", base_score=5.0, weight=30),
    ]

    interior_scores = [
        Score(criterion="Kitchen Layout", base_score=7.0, weight=40),
        Score(criterion="Master Suite", base_score=7.5, weight=40),
        Score(criterion="Natural Light", base_score=8.0, weight=30),
        Score(criterion="High Ceilings", base_score=6.5, weight=30),
        Score(criterion="Fireplace", base_score=8.0, weight=20),
        Score(criterion="Laundry Area", base_score=7.0, weight=20),
        Score(criterion="Aesthetics", base_score=7.0, weight=10),
    ]

    return ScoreBreakdown(
        location_scores=location_scores,
        systems_scores=systems_scores,
        interior_scores=interior_scores,
    )

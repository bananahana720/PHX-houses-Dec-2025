"""Quick test script for PropertyScorer service."""

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import Orientation, SewerType, SolarStatus
from src.phx_home_analysis.services.scoring import PropertyScorer


def create_test_property() -> Property:
    """Create a test property with various data points."""
    return Property(
        # Address
        street="123 Test St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Test St, Phoenix, AZ 85001",
        # Basic listing data
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.5,
        sqft=2200,
        price_per_sqft_raw=204.55,
        # County assessor data
        lot_sqft=10000,
        year_built=2005,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        tax_annual=3000,
        # HOA and location
        hoa_fee=0,
        commute_minutes=25,
        school_district="Paradise Valley USD",
        school_rating=8.5,
        orientation=Orientation.N,
        distance_to_grocery_miles=1.2,
        distance_to_highway_miles=1.5,
        # Arizona-specific
        solar_status=SolarStatus.NONE,
        solar_lease_monthly=None,
        has_pool=True,
        pool_equipment_age=5,
        roof_age=8,
        hvac_age=6,
        # Manual assessments (all neutral at 5.0)
        kitchen_layout_score=7.0,
        master_suite_score=6.5,
        natural_light_score=8.0,
        high_ceilings_score=7.0,
        fireplace_present=True,
        laundry_area_score=6.0,
        aesthetics_score=7.0,
        backyard_utility_score=7.5,
        safety_neighborhood_score=8.0,
        parks_walkability_score=6.0,
        # Analysis results (to be populated)
        kill_switch_passed=True,
        kill_switch_failures=[],
    )


def main():
    """Test the PropertyScorer."""
    print("Creating PropertyScorer...")
    scorer = PropertyScorer()
    print(f"Scorer initialized: {scorer}")
    print(f"Total strategies: {len(scorer._strategies)}")
    print()

    print("Creating test property...")
    property = create_test_property()
    print(f"Property: {property.short_address}")
    print()

    print("Scoring property...")
    score_breakdown = scorer.score(property)
    print()

    print("Score Breakdown:")
    print(f"  Location & Environment: {score_breakdown.location_total:.1f}/250 pts ({score_breakdown.location_percentage:.1f}%)")
    print(f"  Lot & Systems: {score_breakdown.systems_total:.1f}/160 pts ({score_breakdown.systems_percentage:.1f}%)")
    print(f"  Interior & Features: {score_breakdown.interior_total:.1f}/190 pts ({score_breakdown.interior_percentage:.1f}%)")
    print()
    print(f"  TOTAL SCORE: {score_breakdown.total_score:.1f}/600 pts ({score_breakdown.total_percentage:.1f}%)")
    print()

    print("Location Scores:")
    for score in score_breakdown.location_scores:
        print(f"  - {score.criterion}: {score.base_score:.1f}/10 -> {score.weighted_score:.1f}/{score.weight:.0f} pts")
    print()

    print("Systems Scores:")
    for score in score_breakdown.systems_scores:
        print(f"  - {score.criterion}: {score.base_score:.1f}/10 -> {score.weighted_score:.1f}/{score.weight:.0f} pts")
    print()

    print("Interior Scores:")
    for score in score_breakdown.interior_scores:
        print(f"  - {score.criterion}: {score.base_score:.1f}/10 -> {score.weighted_score:.1f}/{score.weight:.0f} pts")
    print()

    # Test score_all
    print("Testing score_all with multiple properties...")
    properties = [property, create_test_property()]
    scored = scorer.score_all(properties)
    print(f"Scored {len(scored)} properties")
    for p in scored:
        print(f"  - {p.short_address}: {p.total_score:.1f} pts, Tier: {p.tier.label if p.tier else 'None'}")


if __name__ == "__main__":
    main()

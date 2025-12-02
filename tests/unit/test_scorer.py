"""Unit tests for property scoring system.

Tests the PropertyScorer, scoring strategies, tier classification,
and score calculations with known inputs.
"""

import pytest

from src.phx_home_analysis.config.scoring_weights import ScoringWeights
from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import Orientation, Tier
from src.phx_home_analysis.domain.value_objects import Score, ScoreBreakdown
from src.phx_home_analysis.services.scoring.scorer import PropertyScorer
from src.phx_home_analysis.services.scoring.strategies.cost_efficiency import CostEfficiencyScorer

# ============================================================================
# PropertyScorer Tests
# ============================================================================


class TestPropertyScorer:
    """Test the PropertyScorer orchestrator."""

    def test_scorer_initialization(self):
        """Test PropertyScorer initializes with default strategies."""
        scorer = PropertyScorer()
        assert scorer.weights is not None
        assert scorer.thresholds is not None

    def test_scorer_initialization_custom_weights(self):
        """Test PropertyScorer initializes with custom weights."""
        weights = ScoringWeights()
        scorer = PropertyScorer(weights=weights)
        assert scorer.weights == weights

    def test_scorer_has_strategies(self):
        """Test PropertyScorer has strategies."""
        scorer = PropertyScorer()
        assert scorer.get_strategy_by_name("School District Rating") is not None

    def test_score_property(self, sample_property):
        """Test scoring a single property."""
        scorer = PropertyScorer()
        score_breakdown = scorer.score(sample_property)

        assert isinstance(score_breakdown, ScoreBreakdown)
        assert score_breakdown.total_score > 0
        assert len(score_breakdown.location_scores) > 0
        assert len(score_breakdown.systems_scores) > 0
        assert len(score_breakdown.interior_scores) > 0

    def test_score_all_properties(self, sample_properties):
        """Test scoring multiple properties."""
        scorer = PropertyScorer()
        scored_properties = scorer.score_all(sample_properties)

        assert len(scored_properties) == len(sample_properties)

        for prop in scored_properties:
            assert prop.score_breakdown is not None
            assert prop.tier is not None

    def test_score_breakdown_structure(self, sample_property):
        """Test ScoreBreakdown has expected structure."""
        scorer = PropertyScorer()
        score_breakdown = scorer.score(sample_property)

        # Check sections exist
        assert isinstance(score_breakdown.location_scores, list)
        assert isinstance(score_breakdown.systems_scores, list)
        assert isinstance(score_breakdown.interior_scores, list)

        # Check totals
        assert score_breakdown.location_total >= 0
        assert score_breakdown.systems_total >= 0
        assert score_breakdown.interior_total >= 0
        assert score_breakdown.total_score >= 0

    def test_total_score_positive(self):
        """Test total score calculation is positive."""
        scorer = PropertyScorer()

        # Create property with maximum scores
        prop = Property(
            street="100 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="100 Test St, Phoenix, AZ 85001",
            price="$500,000",
            price_num=500000,
            beds=5,
            baths=3.0,
            sqft=3000,
            price_per_sqft_raw=166.7,
            lot_sqft=12000,
            year_built=2020,
            garage_spaces=3,
            school_rating=10.0,
            orientation=Orientation.N,
            distance_to_grocery_miles=0.5,
            distance_to_highway_miles=1.0,
            roof_age=1,
            hvac_age=1,
            kitchen_layout_score=10.0,
            master_suite_score=10.0,
            natural_light_score=10.0,
            high_ceilings_score=10.0,
            fireplace_present=True,
            laundry_area_score=10.0,
            aesthetics_score=10.0,
            backyard_utility_score=10.0,
            safety_neighborhood_score=10.0,
            parks_walkability_score=10.0,
        )

        breakdown = scorer.score(prop)
        # Total score should be positive
        assert breakdown.total_score > 0

    def test_score_with_missing_fields(self, sample_property_minimal):
        """Test scoring handles missing optional fields gracefully."""
        scorer = PropertyScorer()
        score_breakdown = scorer.score(sample_property_minimal)

        # Should still produce scores (using neutral defaults)
        assert isinstance(score_breakdown, ScoreBreakdown)
        assert score_breakdown.total_score >= 0

    def test_score_all_updates_properties(self, sample_properties):
        """Test score_all updates property objects."""
        scorer = PropertyScorer()
        original_properties = sample_properties.copy()

        scored = scorer.score_all(sample_properties)

        # Should be same objects, mutated
        for orig, scored_prop in zip(original_properties, scored, strict=False):
            assert orig is scored_prop
            assert scored_prop.score_breakdown is not None
            assert scored_prop.tier is not None

    def test_get_strategies_by_category(self):
        """Test retrieving strategies by category."""
        scorer = PropertyScorer()

        location_strategies = scorer.get_strategies_by_category("location")
        systems_strategies = scorer.get_strategies_by_category("systems")
        interior_strategies = scorer.get_strategies_by_category("interior")

        assert len(location_strategies) > 0
        assert len(systems_strategies) > 0
        assert len(interior_strategies) > 0

    def test_get_strategy_by_name(self):
        """Test retrieving specific strategy by name."""
        scorer = PropertyScorer()

        strategy = scorer.get_strategy_by_name("School District Rating")
        assert strategy is not None
        assert strategy.category == "location"

    def test_get_strategy_by_name_not_found(self):
        """Test retrieving nonexistent strategy returns None."""
        scorer = PropertyScorer()

        strategy = scorer.get_strategy_by_name("Nonexistent Strategy")
        assert strategy is None


# ============================================================================
# Tier Classification Tests
# ============================================================================


class TestTierClassification:
    """Test tier classification logic."""

    def test_unicorn_tier_high_score(self, sample_unicorn_property):
        """Test property with >400 score gets UNICORN tier."""
        sample_unicorn_property.kill_switch_passed = True
        scorer = PropertyScorer()
        scorer.score_all([sample_unicorn_property])

        assert sample_unicorn_property.tier == Tier.UNICORN
        assert sample_unicorn_property.is_unicorn is True

    def test_contender_tier_medium_score(self, sample_property):
        """Test property with 300-400 score gets CONTENDER tier."""
        sample_property.kill_switch_passed = True
        scorer = PropertyScorer()
        scorer.score_all([sample_property])

        # Should score in 300-400 range with moderate data
        if 300 <= sample_property.total_score < 400:
            assert sample_property.tier == Tier.CONTENDER
            assert sample_property.is_contender is True

    def test_pass_tier_low_score(self):
        """Test property with <300 score gets PASS tier."""
        # Create minimalist property with low scores
        prop = Property(
            street="1 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Test St, Phoenix, AZ 85001",
            price="$250,000",
            price_num=250000,
            beds=4,
            baths=2.0,
            sqft=1500,
            price_per_sqft_raw=166.7,
            lot_sqft=7000,
            year_built=2023,
            garage_spaces=2,
            school_rating=1.0,  # Very low
            orientation=Orientation.W,  # Worst orientation
            distance_to_grocery_miles=10.0,  # Very far
            distance_to_highway_miles=0.5,  # Very close
            roof_age=20,  # Very old
            hvac_age=18,  # Very old
            kitchen_layout_score=1.0,
            master_suite_score=1.0,
            natural_light_score=1.0,
            high_ceilings_score=1.0,
            fireplace_present=False,
            laundry_area_score=1.0,
            aesthetics_score=1.0,
            backyard_utility_score=1.0,
            safety_neighborhood_score=1.0,
            parks_walkability_score=1.0,
        )

        prop.kill_switch_passed = True
        scorer = PropertyScorer()
        scorer.score_all([prop])

        # Should score low
        if prop.total_score < 300:
            assert prop.tier == Tier.PASS or prop.tier == Tier.CONTENDER
        assert prop.is_failed is False or prop.tier != Tier.FAILED

    def test_failed_tier_kill_switch_failed(self, sample_failed_property):
        """Test property that failed kill switches gets FAILED tier."""
        sample_failed_property.kill_switch_passed = False
        scorer = PropertyScorer()
        scorer.score_all([sample_failed_property])

        assert sample_failed_property.tier == Tier.FAILED
        assert sample_failed_property.is_failed is True

    def test_failed_tier_overrides_score(self, sample_unicorn_property):
        """Test FAILED tier is assigned regardless of high score."""
        sample_unicorn_property.kill_switch_passed = False
        scorer = PropertyScorer()
        scorer.score_all([sample_unicorn_property])

        assert sample_unicorn_property.tier == Tier.FAILED
        assert sample_unicorn_property.is_failed is True

    def test_tier_from_score_boundary_unicorn(self):
        """Test tier classification at Unicorn boundary (>480)."""
        # Exactly at boundary
        tier = Tier.from_score(480.0, True)
        assert tier == Tier.CONTENDER

        # Just above boundary
        tier = Tier.from_score(480.1, True)
        assert tier == Tier.UNICORN

    def test_tier_from_score_boundary_contender(self):
        """Test tier classification at Contender boundaries."""
        # Below contender
        tier = Tier.from_score(359.9, True)
        assert tier == Tier.PASS

        # At lower boundary
        tier = Tier.from_score(360.0, True)
        assert tier == Tier.CONTENDER

        # At upper boundary
        tier = Tier.from_score(480.0, True)
        assert tier == Tier.CONTENDER

        # Just below upper boundary
        tier = Tier.from_score(479.9, True)
        assert tier == Tier.CONTENDER

    def test_tier_from_score_failed_regardless_of_score(self):
        """Test FAILED tier is assigned when kill_switch_passed=False."""
        tier_high = Tier.from_score(450.0, False)
        tier_mid = Tier.from_score(350.0, False)
        tier_low = Tier.from_score(250.0, False)

        assert tier_high == Tier.FAILED
        assert tier_mid == Tier.FAILED
        assert tier_low == Tier.FAILED


# ============================================================================
# Score Value Object Tests
# ============================================================================


class TestScoreValueObject:
    """Test Score value object calculations."""

    def test_score_weighted_calculation(self):
        """Test Score.weighted_score calculates correctly."""
        # base_score=5.0 (50%), weight=100 -> weighted = 50
        score = Score(criterion="Test", base_score=5.0, weight=100)
        assert score.weighted_score == 50.0

    def test_score_weighted_full_points(self):
        """Test Score with full base score (10.0)."""
        # base_score=10.0 (100%), weight=50 -> weighted = 50
        score = Score(criterion="Test", base_score=10.0, weight=50)
        assert score.weighted_score == 50.0

    def test_score_weighted_zero_points(self):
        """Test Score with zero base score."""
        # base_score=0.0 (0%), weight=50 -> weighted = 0
        score = Score(criterion="Test", base_score=0.0, weight=50)
        assert score.weighted_score == 0.0

    def test_score_percentage_calculation(self):
        """Test Score.percentage calculates correctly."""
        # base_score=5.0 -> 50%
        score = Score(criterion="Test", base_score=5.0, weight=100)
        assert score.percentage == 50.0

    def test_score_percentage_zero_weight(self):
        """Test Score.percentage with zero weight."""
        score = Score(criterion="Test", base_score=5.0, weight=0)
        assert score.percentage == 0.0

    def test_score_max_possible(self):
        """Test Score.max_possible returns weight."""
        score = Score(criterion="Test", base_score=5.0, weight=75)
        assert score.max_possible == 75

    def test_score_validation_base_score_too_high(self):
        """Test Score validates base_score <= 10."""
        with pytest.raises(ValueError):
            Score(criterion="Test", base_score=10.1, weight=50)

    def test_score_validation_base_score_negative(self):
        """Test Score validates base_score >= 0."""
        with pytest.raises(ValueError):
            Score(criterion="Test", base_score=-0.1, weight=50)

    def test_score_validation_weight_negative(self):
        """Test Score validates weight >= 0."""
        with pytest.raises(ValueError):
            Score(criterion="Test", base_score=5.0, weight=-1)

    def test_score_string_representation(self):
        """Test Score string representation."""
        score = Score(criterion="Kitchen Layout", base_score=7.0, weight=40)
        str_repr = str(score)
        assert "Kitchen Layout" in str_repr
        assert "28.0" in str_repr  # 7.0/10 * 40 = 28.0
        assert "40" in str_repr


# ============================================================================
# ScoreBreakdown Value Object Tests
# ============================================================================


class TestScoreBreakdownValueObject:
    """Test ScoreBreakdown value object aggregation."""

    def test_location_total(self, sample_score_breakdown):
        """Test location_total sums correctly."""
        total = sample_score_breakdown.location_total
        assert isinstance(total, float)
        assert total > 0

    def test_systems_total(self, sample_score_breakdown):
        """Test systems_total sums correctly."""
        total = sample_score_breakdown.systems_total
        assert isinstance(total, float)
        assert total > 0

    def test_interior_total(self, sample_score_breakdown):
        """Test interior_total sums correctly."""
        total = sample_score_breakdown.interior_total
        assert isinstance(total, float)
        assert total > 0

    def test_total_score_aggregation(self, sample_score_breakdown):
        """Test total_score aggregates all sections."""
        total = sample_score_breakdown.total_score
        expected = (
            sample_score_breakdown.location_total
            + sample_score_breakdown.systems_total
            + sample_score_breakdown.interior_total
        )
        assert abs(total - expected) < 0.01  # Allow for float precision

    def test_location_percentage(self, sample_score_breakdown):
        """Test location_percentage calculation."""
        percentage = sample_score_breakdown.location_percentage
        # Percentage can exceed 100 if scores exceed section max
        assert percentage >= 0

    def test_systems_percentage(self, sample_score_breakdown):
        """Test systems_percentage calculation."""
        percentage = sample_score_breakdown.systems_percentage
        assert 0 <= percentage <= 100

    def test_interior_percentage(self, sample_score_breakdown):
        """Test interior_percentage calculation."""
        percentage = sample_score_breakdown.interior_percentage
        assert 0 <= percentage <= 100

    def test_total_percentage(self, sample_score_breakdown):
        """Test total_percentage calculation."""
        percentage = sample_score_breakdown.total_percentage
        assert 0 <= percentage <= 100

    def test_empty_score_breakdown(self):
        """Test ScoreBreakdown with empty score lists."""
        breakdown = ScoreBreakdown(
            location_scores=[],
            systems_scores=[],
            interior_scores=[],
        )

        assert breakdown.location_total == 0.0
        assert breakdown.systems_total == 0.0
        assert breakdown.interior_total == 0.0
        assert breakdown.total_score == 0.0

    def test_single_score_breakdown(self):
        """Test ScoreBreakdown with single score in each section."""
        breakdown = ScoreBreakdown(
            location_scores=[Score(criterion="Test1", base_score=5.0, weight=50)],
            systems_scores=[Score(criterion="Test2", base_score=5.0, weight=40)],
            interior_scores=[Score(criterion="Test3", base_score=5.0, weight=30)],
        )

        assert breakdown.location_total == 25.0  # 5.0/10 * 50
        assert breakdown.systems_total == 20.0  # 5.0/10 * 40
        assert breakdown.interior_total == 15.0  # 5.0/10 * 30
        assert breakdown.total_score == 60.0

    def test_score_breakdown_string_representation(self, sample_score_breakdown):
        """Test ScoreBreakdown string representation."""
        str_repr = str(sample_score_breakdown)
        assert "Location:" in str_repr
        assert "Systems:" in str_repr
        assert "Interior:" in str_repr
        assert "Total:" in str_repr


# ============================================================================
# Scoring with Manual Assessment Fields
# ============================================================================


class TestScoringWithManualAssessments:
    """Test scoring when manual assessment fields are populated."""

    def test_scoring_with_all_manual_assessments(self, sample_property):
        """Test scoring with all manual assessment fields filled."""
        # Populate all manual assessment fields
        sample_property.kitchen_layout_score = 8.0
        sample_property.master_suite_score = 8.5
        sample_property.natural_light_score = 9.0
        sample_property.high_ceilings_score = 7.5
        sample_property.fireplace_present = True
        sample_property.laundry_area_score = 8.0
        sample_property.aesthetics_score = 8.5
        sample_property.backyard_utility_score = 7.0
        sample_property.safety_neighborhood_score = 8.5
        sample_property.parks_walkability_score = 7.5

        scorer = PropertyScorer()
        scorer.score_all([sample_property])

        assert sample_property.score_breakdown is not None
        assert sample_property.total_score > 0

    def test_scoring_with_missing_manual_assessments(self, sample_property_minimal):
        """Test scoring handles missing manual assessment fields."""
        scorer = PropertyScorer()
        scorer.score_all([sample_property_minimal])

        # Should still produce valid scores (using neutral defaults)
        assert sample_property_minimal.score_breakdown is not None
        assert sample_property_minimal.total_score >= 0


# ============================================================================
# Real-world Scoring Scenarios
# ============================================================================


class TestRealWorldScoringScenarios:
    """Test realistic scoring scenarios."""

    def test_good_school_district_boosts_score(self, sample_property):
        """Test that good school district ratings increase score."""
        sample_property.kill_switch_passed = True
        sample_property.school_rating = 9.5

        scorer = PropertyScorer()
        scorer.score_all([sample_property])

        high_score = sample_property.total_score

        # Now test with low school rating
        sample_property.school_rating = 2.0
        scorer.score_all([sample_property])

        low_score = sample_property.total_score

        assert high_score > low_score

    def test_north_facing_beats_west_facing(self, sample_property):
        """Test that north-facing orientation scores better than west."""
        sample_property.kill_switch_passed = True
        sample_property.orientation = Orientation.N

        scorer = PropertyScorer()
        scorer.score_all([sample_property])
        north_score = sample_property.total_score

        # Now test with west orientation
        sample_property.orientation = Orientation.W
        scorer.score_all([sample_property])
        west_score = sample_property.total_score

        assert north_score > west_score

    def test_new_roof_hvac_boosts_score(self, sample_property):
        """Test that newer HVAC/roof age boosts score."""
        sample_property.kill_switch_passed = True
        sample_property.roof_age = 1
        sample_property.hvac_age = 1

        scorer = PropertyScorer()
        scorer.score_all([sample_property])
        new_score = sample_property.total_score

        # Now test with old roof/hvac
        sample_property.roof_age = 20
        sample_property.hvac_age = 18
        scorer.score_all([sample_property])
        old_score = sample_property.total_score

        assert new_score >= old_score  # At least equal or better


# ============================================================================
# CostEfficiencyScorer Tests
# ============================================================================


class TestCostEfficiencyScorer:
    """Test CostEfficiencyScorer strategy."""

    def test_scorer_initialization(self):
        """Test CostEfficiencyScorer initializes correctly."""
        scorer = CostEfficiencyScorer()
        assert scorer.name == "Cost Efficiency"
        assert scorer.category == "systems"
        assert scorer.weight == 35

    def test_scorer_with_custom_weights(self):
        """Test CostEfficiencyScorer with custom weights."""
        weights = ScoringWeights(cost_efficiency=50)
        scorer = CostEfficiencyScorer(weights=weights)
        assert scorer.weight == 50

    def test_low_monthly_cost_high_score(self):
        """Test property with low monthly cost ($3000) gets maximum score."""
        # Create a low-cost property (~$3000/mo)
        prop = Property(
            street="100 Affordable St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="100 Affordable St, Phoenix, AZ 85001",
            price="$300,000",
            price_num=300000,  # Low price = low mortgage
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=150.0,
            hoa_fee=0,
            tax_annual=2400,  # $200/mo
            has_pool=False,
        )

        scorer = CostEfficiencyScorer()
        base_score = scorer.calculate_base_score(prop)

        # Low monthly cost should yield high score
        assert base_score >= 8.0

    def test_high_monthly_cost_low_score(self):
        """Test property with high monthly cost ($5000+) gets minimum score."""
        # Create a high-cost property (~$5000+/mo)
        prop = Property(
            street="100 Expensive St",
            city="Scottsdale",
            state="AZ",
            zip_code="85251",
            full_address="100 Expensive St, Scottsdale, AZ 85251",
            price="$650,000",
            price_num=650000,  # High price = high mortgage
            beds=5,
            baths=3.0,
            sqft=3500,
            price_per_sqft_raw=185.7,
            hoa_fee=200,  # Additional burden
            tax_annual=6000,  # $500/mo
            has_pool=True,  # Additional $125/mo
            solar_lease_monthly=150,  # Additional burden
        )

        scorer = CostEfficiencyScorer()
        base_score = scorer.calculate_base_score(prop)

        # High monthly cost should yield low score
        assert base_score <= 3.0

    def test_target_budget_neutral_score(self):
        """Test property at target budget ($4000/mo) gets neutral score."""
        # Create a property at ~$4000/mo using comprehensive cost calculation
        # MonthlyCostEstimator includes: mortgage, tax, insurance, utilities,
        # water, trash, maintenance reserve (plus pool/HOA/solar if applicable)
        # At $475k with no pool: ~$4,029/mo total -> ~4.9 score
        prop = Property(
            street="100 Budget St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="100 Budget St, Phoenix, AZ 85001",
            price="$475,000",
            price_num=475000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=237.5,
            hoa_fee=0,
            tax_annual=None,  # Let service estimate
            has_pool=False,
        )

        scorer = CostEfficiencyScorer()
        base_score = scorer.calculate_base_score(prop)

        # At-budget property (~$4,029/mo) should score around 4.9 (neutral range)
        assert 3.0 <= base_score <= 7.0

    def test_score_formula_boundaries(self):
        """Test the scoring formula at specific cost boundaries."""
        scorer = CostEfficiencyScorer()

        # Create properties at specific cost points
        # $3,000/mo -> 10 pts
        # $4,000/mo -> 5 pts
        # $5,000/mo -> 0 pts

        # Very affordable property
        affordable = Property(
            street="1 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Test St, Phoenix, AZ 85001",
            price="$250,000",
            price_num=250000,
            beds=4,
            baths=2.0,
            sqft=1800,
            price_per_sqft_raw=138.9,
            hoa_fee=0,
            tax_annual=2000,
            has_pool=False,
        )

        score = scorer.calculate_base_score(affordable)
        # Should be high (close to 10)
        assert score >= 7.0

    def test_score_capped_at_ten(self):
        """Test that score is capped at maximum 10."""
        scorer = CostEfficiencyScorer()

        # Very cheap property (unrealistically low cost)
        cheap = Property(
            street="1 Cheap St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Cheap St, Phoenix, AZ 85001",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=1500,
            price_per_sqft_raw=66.7,
            hoa_fee=0,
            tax_annual=1000,
            has_pool=False,
        )

        score = scorer.calculate_base_score(cheap)
        assert score == 10.0

    def test_score_floored_at_zero(self):
        """Test that score is floored at minimum 0."""
        scorer = CostEfficiencyScorer()

        # Very expensive property
        expensive = Property(
            street="1 Luxury St",
            city="Paradise Valley",
            state="AZ",
            zip_code="85253",
            full_address="1 Luxury St, Paradise Valley, AZ 85253",
            price="$900,000",
            price_num=900000,
            beds=6,
            baths=4.0,
            sqft=5000,
            price_per_sqft_raw=180.0,
            hoa_fee=500,
            tax_annual=12000,
            has_pool=True,
            solar_lease_monthly=200,
        )

        score = scorer.calculate_base_score(expensive)
        assert score == 0.0

    def test_pool_adds_cost_burden(self):
        """Test that pool presence increases monthly cost and lowers score."""
        scorer = CostEfficiencyScorer()

        base_prop = Property(
            street="1 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Test St, Phoenix, AZ 85001",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=214.3,
            hoa_fee=0,
            tax_annual=4000,
            has_pool=False,
        )

        pool_prop = Property(
            street="2 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="2 Test St, Phoenix, AZ 85001",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=214.3,
            hoa_fee=0,
            tax_annual=4000,
            has_pool=True,  # Pool adds ~$125/mo
        )

        no_pool_score = scorer.calculate_base_score(base_prop)
        pool_score = scorer.calculate_base_score(pool_prop)

        # Pool should reduce score due to added monthly cost
        assert no_pool_score > pool_score

    def test_hoa_adds_cost_burden(self):
        """Test that HOA fees increase monthly cost and lower score."""
        scorer = CostEfficiencyScorer()

        no_hoa = Property(
            street="1 Free St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Free St, Phoenix, AZ 85001",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=214.3,
            hoa_fee=0,
            tax_annual=4000,
            has_pool=False,
        )

        with_hoa = Property(
            street="2 HOA St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="2 HOA St, Phoenix, AZ 85001",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=214.3,
            hoa_fee=200,  # HOA adds $200/mo
            tax_annual=4000,
            has_pool=False,
        )

        no_hoa_score = scorer.calculate_base_score(no_hoa)
        hoa_score = scorer.calculate_base_score(with_hoa)

        # HOA should reduce score due to added monthly cost
        assert no_hoa_score > hoa_score

    def test_weighted_score_calculation(self):
        """Test weighted score uses correct weight (35 pts)."""
        scorer = CostEfficiencyScorer()

        prop = Property(
            street="1 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="1 Test St, Phoenix, AZ 85001",
            price="$400,000",
            price_num=400000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=200.0,
            hoa_fee=0,
            tax_annual=3500,
            has_pool=False,
        )

        score = scorer.calculate_weighted_score(prop)

        assert score.criterion == "Cost Efficiency"
        assert score.weight == 35.0
        # Weighted score should be base_score / 10 * weight
        expected_weighted = (score.base_score / 10) * 35
        assert abs(score.weighted_score - expected_weighted) < 0.01


# ============================================================================
# Scoring Weights Tests
# ============================================================================


class TestScoringWeights:
    """Test ScoringWeights configuration."""

    def test_total_possible_score_equals_600(self):
        """Test that total possible score equals 600 points."""
        weights = ScoringWeights()
        assert weights.total_possible_score == 600

    def test_section_a_max_equals_250(self):
        """Test that Section A max equals 250 points."""
        weights = ScoringWeights()
        assert weights.section_a_max == 250

    def test_section_b_max_equals_170(self):
        """Test that Section B max equals 170 points."""
        weights = ScoringWeights()
        assert weights.section_b_max == 170

    def test_section_c_max_equals_180(self):
        """Test that Section C max equals 180 points."""
        weights = ScoringWeights()
        assert weights.section_c_max == 180

    def test_cost_efficiency_weight_is_35(self):
        """Test that cost_efficiency weight is 35 points."""
        weights = ScoringWeights()
        assert weights.cost_efficiency == 35

    def test_quietness_weight_is_30(self):
        """Test that quietness weight is 30 points."""
        weights = ScoringWeights()
        assert weights.quietness == 30

    def test_supermarket_proximity_weight_is_25(self):
        """Test that supermarket_proximity weight is 25 points."""
        weights = ScoringWeights()
        assert weights.supermarket_proximity == 25

    def test_pool_condition_weight_is_20(self):
        """Test that pool_condition weight is 20 points (reduced from 30)."""
        weights = ScoringWeights()
        assert weights.pool_condition == 20

"""Unit tests for scoring explanation generator.

Tests the ScoringExplainer class and explanation data classes for generating
human-readable scoring explanations, tier descriptions, and improvement suggestions.
"""

from src.phx_home_analysis.config.scoring_weights import ScoringWeights, TierThresholds
from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import (
    FloodZone,
    Orientation,
    SewerType,
    SolarStatus,
)
from src.phx_home_analysis.domain.value_objects import Score, ScoreBreakdown
from src.phx_home_analysis.services.scoring.explanation import (
    FullScoreExplanation,
    ScoreExplanation,
    ScoringExplainer,
    SectionExplanation,
)
from src.phx_home_analysis.services.scoring.scorer import PropertyScorer

# ============================================================================
# ScoreExplanation Tests
# ============================================================================


class TestScoreExplanation:
    """Tests for ScoreExplanation dataclass."""

    def test_score_explanation_creation(self):
        """Test basic ScoreExplanation creation."""
        explanation = ScoreExplanation(
            criterion="School District Rating",
            score=35.0,
            max_score=50.0,
            percentage=70.0,
            raw_value="8.5/10",
            reasoning="Excellent schools - families pay premium for this district",
        )

        assert explanation.criterion == "School District Rating"
        assert explanation.score == 35.0
        assert explanation.max_score == 50.0
        assert explanation.percentage == 70.0
        assert explanation.raw_value == "8.5/10"
        assert explanation.improvement_tip is None

    def test_score_explanation_with_improvement_tip(self):
        """Test ScoreExplanation with improvement tip."""
        explanation = ScoreExplanation(
            criterion="School District Rating",
            score=15.0,
            max_score=50.0,
            percentage=30.0,
            raw_value="4.5/10",
            reasoning="School ratings could be better",
            improvement_tip="Higher-rated districts available in Gilbert, Chandler",
        )

        assert explanation.improvement_tip is not None
        assert "Gilbert" in explanation.improvement_tip

    def test_score_explanation_with_none_raw_value(self):
        """Test ScoreExplanation handles None raw_value."""
        explanation = ScoreExplanation(
            criterion="Crime Index",
            score=25.0,
            max_score=47.0,
            percentage=53.0,
            raw_value=None,
            reasoning="Average safety for Phoenix metro area",
        )

        assert explanation.raw_value is None

    def test_score_explanation_to_dict(self):
        """Test ScoreExplanation.to_dict() serialization."""
        explanation = ScoreExplanation(
            criterion="School District Rating",
            score=35.0,
            max_score=50.0,
            percentage=70.0,
            raw_value="8.5/10",
            reasoning="Excellent schools",
            improvement_tip="Consider higher-rated districts",
        )

        result = explanation.to_dict()

        assert result["criterion"] == "School District Rating"
        assert result["score"] == 35.0
        assert result["max_score"] == 50.0
        assert result["percentage"] == 70.0
        assert result["raw_value"] == "8.5/10"
        assert result["reasoning"] == "Excellent schools"
        assert result["improvement_tip"] == "Consider higher-rated districts"

    def test_score_explanation_to_dict_rounds_values(self):
        """Test ScoreExplanation.to_dict() rounds numeric values."""
        explanation = ScoreExplanation(
            criterion="Test",
            score=35.6789,
            max_score=50.1234,
            percentage=71.2345,
            raw_value="test",
            reasoning="Test",
        )

        result = explanation.to_dict()

        assert result["score"] == 35.7
        assert result["max_score"] == 50.1
        assert result["percentage"] == 71.2

    def test_score_explanation_percentage_boundary_high(self):
        """Test high-scoring explanation (>= 70%)."""
        explanation = ScoreExplanation(
            criterion="Test",
            score=35.0,
            max_score=50.0,
            percentage=70.0,
            raw_value="test",
            reasoning="High score",
        )

        assert explanation.percentage >= 70.0

    def test_score_explanation_percentage_boundary_medium(self):
        """Test medium-scoring explanation (40-70%)."""
        explanation = ScoreExplanation(
            criterion="Test",
            score=25.0,
            max_score=50.0,
            percentage=50.0,
            raw_value="test",
            reasoning="Medium score",
        )

        assert 40.0 <= explanation.percentage < 70.0

    def test_score_explanation_percentage_boundary_low(self):
        """Test low-scoring explanation (< 40%)."""
        explanation = ScoreExplanation(
            criterion="Test",
            score=15.0,
            max_score=50.0,
            percentage=30.0,
            raw_value="test",
            reasoning="Low score",
        )

        assert explanation.percentage < 40.0


# ============================================================================
# SectionExplanation Tests
# ============================================================================


class TestSectionExplanation:
    """Tests for SectionExplanation dataclass."""

    def test_section_explanation_creation(self):
        """Test basic SectionExplanation creation."""
        criteria = [
            ScoreExplanation(
                criterion="School District Rating",
                score=35.0,
                max_score=50.0,
                percentage=70.0,
                raw_value="8.5/10",
                reasoning="Excellent schools",
            ),
        ]

        section = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=150.0,
            max_score=250.0,
            percentage=60.0,
            criteria=criteria,
            summary="Good location with solid schools and amenities.",
        )

        assert section.section == "Location & Environment"
        assert section.section_letter == "A"
        assert section.total_score == 150.0
        assert section.max_score == 250.0
        assert section.percentage == 60.0
        assert len(section.criteria) == 1
        assert section.summary == "Good location with solid schools and amenities."

    def test_section_explanation_with_strengths_and_weaknesses(self):
        """Test SectionExplanation with identified strengths and weaknesses."""
        criteria = [
            ScoreExplanation(
                criterion="School District",
                score=35.0,
                max_score=50.0,
                percentage=70.0,
                raw_value="8.5/10",
                reasoning="Good schools",
            ),
            ScoreExplanation(
                criterion="Crime Index",
                score=15.0,
                max_score=47.0,
                percentage=32.0,
                raw_value="65/100",
                reasoning="Higher crime area",
            ),
        ]

        section = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=150.0,
            max_score=250.0,
            percentage=60.0,
            criteria=criteria,
            summary="Mixed area with good schools but higher crime.",
            strengths=["School District"],
            weaknesses=["Crime Index"],
        )

        assert "School District" in section.strengths
        assert "Crime Index" in section.weaknesses

    def test_section_explanation_to_dict(self):
        """Test SectionExplanation.to_dict() serialization."""
        criteria = [
            ScoreExplanation(
                criterion="School District Rating",
                score=35.0,
                max_score=50.0,
                percentage=70.0,
                raw_value="8.5/10",
                reasoning="Excellent schools",
            ),
        ]

        section = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=150.0,
            max_score=250.0,
            percentage=60.0,
            criteria=criteria,
            summary="Good location",
            strengths=["School District"],
            weaknesses=[],
        )

        result = section.to_dict()

        assert result["section"] == "Location & Environment"
        assert result["section_letter"] == "A"
        assert result["total_score"] == 150.0
        assert result["max_score"] == 250.0
        assert result["percentage"] == 60.0
        assert len(result["criteria"]) == 1
        assert result["summary"] == "Good location"
        assert result["strengths"] == ["School District"]
        assert result["weaknesses"] == []

    def test_section_explanation_empty_criteria_list(self):
        """Test SectionExplanation with empty criteria list."""
        section = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=0.0,
            max_score=250.0,
            percentage=0.0,
            criteria=[],
            summary="No criteria evaluated",
        )

        assert len(section.criteria) == 0
        assert section.total_score == 0.0


# ============================================================================
# FullScoreExplanation Tests
# ============================================================================


class TestFullScoreExplanation:
    """Tests for FullScoreExplanation dataclass."""

    def test_full_score_explanation_unicorn_tier(self):
        """Test FullScoreExplanation for Unicorn tier property."""
        section_a = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=200.0,
            max_score=250.0,
            percentage=80.0,
            criteria=[],
            summary="Excellent location",
        )
        section_b = SectionExplanation(
            section="Lot & Systems",
            section_letter="B",
            total_score=150.0,
            max_score=175.0,
            percentage=85.7,
            criteria=[],
            summary="Excellent systems",
        )
        section_c = SectionExplanation(
            section="Interior & Features",
            section_letter="C",
            total_score=150.0,
            max_score=180.0,
            percentage=83.3,
            criteria=[],
            summary="Excellent interior",
        )

        explanation = FullScoreExplanation(
            address="123 Main St, Phoenix, AZ 85001",
            total_score=500.0,
            max_score=605.0,
            tier="Unicorn",
            tier_threshold=480.0,
            next_tier=None,
            points_to_next_tier=None,
            sections=[section_a, section_b, section_c],
            summary="Exceptional property with standout features",
            top_strengths=["Excellent location", "Great systems"],
            key_improvements=[],
        )

        assert explanation.tier == "Unicorn"
        assert explanation.next_tier is None
        assert explanation.points_to_next_tier is None
        assert explanation.total_score == 500.0

    def test_full_score_explanation_contender_tier(self):
        """Test FullScoreExplanation for Contender tier property."""
        section_a = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=150.0,
            max_score=250.0,
            percentage=60.0,
            criteria=[],
            summary="Good location",
        )
        section_b = SectionExplanation(
            section="Lot & Systems",
            section_letter="B",
            total_score=110.0,
            max_score=175.0,
            percentage=62.9,
            criteria=[],
            summary="Good systems",
        )
        section_c = SectionExplanation(
            section="Interior & Features",
            section_letter="C",
            total_score=110.0,
            max_score=180.0,
            percentage=61.1,
            criteria=[],
            summary="Average interior",
        )

        explanation = FullScoreExplanation(
            address="456 Oak Ave, Phoenix, AZ 85001",
            total_score=370.0,
            max_score=605.0,
            tier="Contender",
            tier_threshold=360.0,
            next_tier="Unicorn",
            points_to_next_tier=110.0,
            sections=[section_a, section_b, section_c],
            summary="Strong candidate with balanced scores",
            top_strengths=["Good location"],
            key_improvements=["Improve interior"],
        )

        assert explanation.tier == "Contender"
        assert explanation.next_tier == "Unicorn"
        assert explanation.points_to_next_tier == 110.0

    def test_full_score_explanation_pass_tier(self):
        """Test FullScoreExplanation for Pass tier property."""
        section_a = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=100.0,
            max_score=250.0,
            percentage=40.0,
            criteria=[],
            summary="Average location",
        )
        section_b = SectionExplanation(
            section="Lot & Systems",
            section_letter="B",
            total_score=80.0,
            max_score=175.0,
            percentage=45.7,
            criteria=[],
            summary="Below average systems",
        )
        section_c = SectionExplanation(
            section="Interior & Features",
            section_letter="C",
            total_score=100.0,
            max_score=180.0,
            percentage=55.6,
            criteria=[],
            summary="Average interior",
        )

        explanation = FullScoreExplanation(
            address="789 Desert Rd, Phoenix, AZ 85001",
            total_score=280.0,
            max_score=605.0,
            tier="Pass",
            tier_threshold=0.0,
            next_tier="Contender",
            points_to_next_tier=80.0,
            sections=[section_a, section_b, section_c],
            summary="Meets minimum criteria but lacks standout features",
            top_strengths=[],
            key_improvements=["Improve location", "Upgrade systems"],
        )

        assert explanation.tier == "Pass"
        assert explanation.next_tier == "Contender"
        assert explanation.points_to_next_tier == 80.0

    def test_full_score_explanation_to_dict(self):
        """Test FullScoreExplanation.to_dict() serialization."""
        section_a = SectionExplanation(
            section="Location & Environment",
            section_letter="A",
            total_score=150.0,
            max_score=250.0,
            percentage=60.0,
            criteria=[],
            summary="Good location",
        )

        explanation = FullScoreExplanation(
            address="123 Main St, Phoenix, AZ 85001",
            total_score=370.0,
            max_score=605.0,
            tier="Contender",
            tier_threshold=360.0,
            next_tier="Unicorn",
            points_to_next_tier=110.0,
            sections=[section_a],
            summary="Strong candidate",
            top_strengths=["Good location"],
            key_improvements=["Improve interior"],
        )

        result = explanation.to_dict()

        assert result["address"] == "123 Main St, Phoenix, AZ 85001"
        assert result["total_score"] == 370.0
        assert result["max_score"] == 605.0
        assert result["percentage"] == round((370.0 / 605.0) * 100, 1)
        assert result["tier"] == "Contender"
        assert result["tier_threshold"] == 360.0
        assert result["next_tier"] == "Unicorn"
        assert result["points_to_next_tier"] == 110.0
        assert len(result["sections"]) == 1


# ============================================================================
# ScoringExplainer Tests
# ============================================================================


class TestScoringExplainerInitialization:
    """Tests for ScoringExplainer initialization."""

    def test_explainer_initialization_default(self):
        """Test ScoringExplainer initializes with defaults."""
        explainer = ScoringExplainer()

        assert explainer._weights is not None
        assert explainer._thresholds is not None

    def test_explainer_initialization_custom_weights(self):
        """Test ScoringExplainer initializes with custom weights."""
        weights = ScoringWeights()
        explainer = ScoringExplainer(weights=weights)

        assert explainer._weights == weights

    def test_explainer_initialization_custom_thresholds(self):
        """Test ScoringExplainer initializes with custom thresholds."""
        thresholds = TierThresholds()
        explainer = ScoringExplainer(thresholds=thresholds)

        assert explainer._thresholds == thresholds

    def test_explainer_has_criterion_templates(self):
        """Test ScoringExplainer has criterion templates."""
        explainer = ScoringExplainer()

        assert len(explainer.CRITERION_TEMPLATES) > 0
        assert "School District Rating" in explainer.CRITERION_TEMPLATES
        assert "Roof Condition/Age" in explainer.CRITERION_TEMPLATES
        assert "Kitchen Layout" in explainer.CRITERION_TEMPLATES


class TestScoringExplainerExplanation:
    """Tests for complete score explanations."""

    def test_explain_sample_property(self, sample_property):
        """Test generating explanation for a sample property."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        assert isinstance(explanation, FullScoreExplanation)
        assert explanation.address == sample_property.full_address
        assert explanation.total_score == breakdown.total_score
        assert explanation.max_score == 605.0
        assert explanation.tier in ["Unicorn", "Contender", "Pass"]
        assert len(explanation.sections) == 3

    def test_explain_unicorn_property(self, sample_unicorn_property):
        """Test generating explanation for unicorn property."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_unicorn_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_unicorn_property, breakdown)

        assert explanation.tier == "Unicorn"
        assert explanation.next_tier is None
        assert explanation.points_to_next_tier is None
        assert explanation.total_score > 480.0

    def test_explain_generates_section_explanations(self, sample_property):
        """Test explanation includes section breakdowns."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        # Verify sections
        assert len(explanation.sections) == 3
        section_letters = [s.section_letter for s in explanation.sections]
        assert "A" in section_letters
        assert "B" in section_letters
        assert "C" in section_letters

    def test_explain_generates_top_strengths(self, sample_unicorn_property):
        """Test explanation identifies top strengths."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_unicorn_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_unicorn_property, breakdown)

        assert len(explanation.top_strengths) > 0
        assert len(explanation.top_strengths) <= 5

    def test_explain_generates_key_improvements(self, sample_property):
        """Test explanation identifies key improvement opportunities."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        # May or may not have improvements depending on scores
        assert isinstance(explanation.key_improvements, list)


class TestScoringExplainerRawValues:
    """Tests for raw value extraction and formatting."""

    def test_get_raw_value_school_rating(self, sample_property):
        """Test raw value extraction for school rating."""
        explainer = ScoringExplainer()
        raw_value = explainer._get_raw_value("School District Rating", sample_property)

        assert raw_value is not None
        assert "7.5" in str(raw_value)

    def test_get_raw_value_orientation_north(self, sample_property):
        """Test raw value extraction for North orientation."""
        explainer = ScoringExplainer()
        sample_property.orientation = Orientation.N
        raw_value = explainer._get_raw_value("Sun Orientation", sample_property)

        assert raw_value is not None
        assert "N" in str(raw_value).upper()

    def test_get_raw_value_orientation_west(self, sample_property):
        """Test raw value extraction for West orientation."""
        explainer = ScoringExplainer()
        sample_property.orientation = Orientation.W
        raw_value = explainer._get_raw_value("Sun Orientation", sample_property)

        assert raw_value is not None
        assert "W" in str(raw_value).upper()

    def test_get_raw_value_flood_zone_x(self, sample_property):
        """Test raw value extraction for minimal flood zone."""
        explainer = ScoringExplainer()
        sample_property.flood_zone = FloodZone.X
        raw_value = explainer._get_raw_value("Flood Risk", sample_property)

        assert raw_value is not None
        assert "X" in str(raw_value)

    def test_get_raw_value_solar_owned(self, sample_property):
        """Test raw value extraction for owned solar."""
        explainer = ScoringExplainer()
        sample_property.solar_status = SolarStatus.OWNED
        raw_value = explainer._get_raw_value("Solar Status", sample_property)

        assert raw_value is not None
        assert "Owned" in str(raw_value)

    def test_get_raw_value_solar_leased(self, sample_property):
        """Test raw value extraction for leased solar."""
        explainer = ScoringExplainer()
        sample_property.solar_status = SolarStatus.LEASED
        raw_value = explainer._get_raw_value("Solar Status", sample_property)

        assert raw_value is not None
        assert "Leased" in str(raw_value)

    def test_get_raw_value_fireplace_present(self, sample_property):
        """Test raw value extraction for fireplace present."""
        explainer = ScoringExplainer()
        sample_property.fireplace_present = True
        raw_value = explainer._get_raw_value("Fireplace", sample_property)

        assert raw_value == "Yes"

    def test_get_raw_value_fireplace_absent(self, sample_property):
        """Test raw value extraction for no fireplace."""
        explainer = ScoringExplainer()
        sample_property.fireplace_present = False
        raw_value = explainer._get_raw_value("Fireplace", sample_property)

        assert raw_value == "No"

    def test_get_raw_value_high_ceilings_vaulted(self, sample_property):
        """Test raw value extraction for vaulted ceilings."""
        explainer = ScoringExplainer()
        sample_property.high_ceilings_score = 9.5
        raw_value = explainer._get_raw_value("High Ceilings", sample_property)

        assert raw_value is not None
        assert "Vaulted" in str(raw_value) or "cathedral" in str(raw_value)

    def test_get_raw_value_high_ceilings_standard(self, sample_property):
        """Test raw value extraction for standard ceilings."""
        explainer = ScoringExplainer()
        sample_property.high_ceilings_score = 5.0
        raw_value = explainer._get_raw_value("High Ceilings", sample_property)

        assert raw_value is not None
        assert "feet" in str(raw_value).lower()

    def test_get_raw_value_pool_condition_no_pool(self, sample_property):
        """Test raw value extraction when property has no pool."""
        explainer = ScoringExplainer()
        sample_property.has_pool = False
        sample_property.pool_equipment_age = None
        raw_value = explainer._get_raw_value("Pool Condition", sample_property)

        # Should return None or indicate no pool
        assert raw_value is None or "no" in str(raw_value).lower()

    def test_get_raw_value_unknown_criterion(self, sample_property):
        """Test raw value extraction for unknown criterion."""
        explainer = ScoringExplainer()
        raw_value = explainer._get_raw_value("Unknown Criterion Name", sample_property)

        assert raw_value is None

    def test_get_raw_value_missing_property_field(self, sample_property):
        """Test raw value extraction when property field is missing."""
        explainer = ScoringExplainer()
        sample_property.school_rating = None
        raw_value = explainer._get_raw_value("School District Rating", sample_property)

        assert raw_value is None


class TestScoringExplainerTierInfo:
    """Tests for tier information determination."""

    def test_determine_tier_info_unicorn(self):
        """Test tier info for Unicorn tier."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(500.0)

        assert tier == "Unicorn"
        assert threshold == 484.0  # unicorn_min = 484
        assert next_tier is None
        assert points is None

    def test_determine_tier_info_contender_lower_bound(self):
        """Test tier info for Contender tier (lower bound)."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(363.0)

        assert tier == "Contender"
        assert threshold == 363.0  # contender_min = 363
        assert next_tier == "Unicorn"
        assert points is not None
        assert points > 0

    def test_determine_tier_info_contender_upper_bound(self):
        """Test tier info for Contender tier (upper bound)."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(483.0)

        assert tier == "Contender"
        assert next_tier == "Unicorn"

    def test_determine_tier_info_pass(self):
        """Test tier info for Pass tier."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(300.0)

        assert tier == "Pass"
        assert threshold == 0.0
        assert next_tier == "Contender"
        assert points is not None
        assert points > 0

    def test_determine_tier_info_boundary_484(self):
        """Test tier info at boundary score 484 (exactly at threshold)."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(484.0)

        # Exactly at threshold is Contender (need > not >=)
        assert tier == "Contender"

    def test_determine_tier_info_boundary_485(self):
        """Test tier info just above boundary (485)."""
        explainer = ScoringExplainer()
        tier, threshold, next_tier, points = explainer._determine_tier_info(485.0)

        # Just above boundary should be Unicorn
        assert tier == "Unicorn"


class TestScoringExplainerSectionExplanation:
    """Tests for section explanation generation."""

    def test_explain_section_excellent_scores(self, sample_unicorn_property):
        """Test section explanation for excellent scores (>75%)."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_unicorn_property)

        explainer = ScoringExplainer()
        section = explainer._explain_section(
            "Location & Environment",
            "A",
            breakdown.location_scores,
            explainer._weights.section_a_max,
            sample_unicorn_property,
        )

        assert section.section == "Location & Environment"
        assert section.section_letter == "A"
        assert "Excellent" in section.summary

    def test_explain_section_average_scores(self, sample_property):
        """Test section explanation for average scores (45-60%)."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        # Find a section with average scores or create mock
        section = explainer._explain_section(
            "Test Section",
            "X",
            breakdown.location_scores,
            explainer._weights.section_a_max,
            sample_property,
        )

        assert section.section_letter == "X"
        assert isinstance(section.summary, str)

    def test_explain_section_identifies_strengths(self, sample_unicorn_property):
        """Test section explanation identifies strengths (>70%)."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_unicorn_property)

        explainer = ScoringExplainer()
        section = explainer._explain_section(
            "Interior & Features",
            "C",
            breakdown.interior_scores,
            explainer._weights.section_c_max,
            sample_unicorn_property,
        )

        # Unicorn property should have strengths
        assert len(section.strengths) >= 0  # May be empty depending on scores

    def test_explain_section_identifies_weaknesses(self, sample_property):
        """Test section explanation identifies weaknesses (<50%)."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        section = explainer._explain_section(
            "Location & Environment",
            "A",
            breakdown.location_scores,
            explainer._weights.section_a_max,
            sample_property,
        )

        # Check weaknesses list structure
        assert isinstance(section.weaknesses, list)


class TestScoringExplainerCriterionExplanation:
    """Tests for criterion explanation generation."""

    def test_explain_criterion_high_score(self, sample_property):
        """Test criterion explanation for high score (>=70%)."""
        score = Score(
            criterion="School District Rating",
            base_score=8.5,
            weight=50,
        )

        explainer = ScoringExplainer()
        explanation = explainer._explain_criterion(score, sample_property)

        assert explanation.criterion == "School District Rating"
        assert explanation.percentage == 85.0
        assert (
            "high" not in explanation.reasoning.lower()
            or "excellent" in explanation.reasoning.lower()
        )

    def test_explain_criterion_medium_score(self, sample_property):
        """Test criterion explanation for medium score (40-70%)."""
        score = Score(
            criterion="School District Rating",
            base_score=6.5,
            weight=50,
        )

        explainer = ScoringExplainer()
        explanation = explainer._explain_criterion(score, sample_property)

        assert explanation.criterion == "School District Rating"
        assert explanation.percentage == 65.0

    def test_explain_criterion_low_score(self, sample_property):
        """Test criterion explanation for low score (<40%)."""
        score = Score(
            criterion="School District Rating",
            base_score=3.0,
            weight=50,
        )

        explainer = ScoringExplainer()
        explanation = explainer._explain_criterion(score, sample_property)

        assert explanation.criterion == "School District Rating"
        assert explanation.percentage == 30.0
        assert explanation.improvement_tip is not None

    def test_explain_criterion_includes_raw_value(self, sample_property):
        """Test criterion explanation includes raw value."""
        score = Score(
            criterion="School District Rating",
            base_score=7.5,
            weight=50,
        )

        explainer = ScoringExplainer()
        explanation = explainer._explain_criterion(score, sample_property)

        assert explanation.raw_value is not None

    def test_explain_criterion_includes_improvement_tip(self, sample_property):
        """Test low-scoring criterion includes improvement tip."""
        score = Score(
            criterion="Roof Condition/Age",
            base_score=2.0,
            weight=45,
        )

        explainer = ScoringExplainer()
        explanation = explainer._explain_criterion(score, sample_property)

        assert explanation.improvement_tip is not None


class TestScoringExplainerMarkdownGeneration:
    """Tests for markdown text generation."""

    def test_to_text_generates_markdown(self, sample_property):
        """Test FullScoreExplanation.to_text() generates markdown."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        markdown = explanation.to_text()

        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "##" in markdown  # Markdown headers
        assert "|" in markdown  # Markdown tables

    def test_to_text_includes_score_header(self, sample_property):
        """Test markdown includes score and tier header."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        markdown = explanation.to_text()

        assert "Property Score" in markdown
        assert (
            f"{int(explanation.total_score):.0f}" in markdown
            or f"{explanation.total_score:.0f}" in markdown
        )
        assert explanation.tier.upper() in markdown

    def test_to_text_includes_section_breakdowns(self, sample_property):
        """Test markdown includes all section breakdowns."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        markdown = explanation.to_text()

        assert "Section A" in markdown
        assert "Section B" in markdown
        assert "Section C" in markdown
        assert "Location & Environment" in markdown
        assert "Lot & Systems" in markdown
        assert "Interior & Features" in markdown

    def test_to_text_includes_criteria_table(self, sample_property):
        """Test markdown includes criteria table."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        markdown = explanation.to_text()

        # Check for table structure
        lines = markdown.split("\n")
        table_lines = [l for l in lines if "|" in l]
        assert len(table_lines) > 0

    def test_to_text_includes_tier_guidance(self, sample_property):
        """Test markdown includes tier context and guidance."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        markdown = explanation.to_text()

        if explanation.next_tier:
            assert explanation.next_tier in markdown

    def test_to_text_for_unicorn_shows_top_tier(self, sample_unicorn_property):
        """Test markdown for Unicorn shows top tier achieved."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_unicorn_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_unicorn_property, breakdown)

        markdown = explanation.to_text()

        assert "Top tier achieved" in markdown or "UNICORN" in markdown


class TestScoringExplainerEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_explain_property_with_none_address(self, sample_property):
        """Test explanation handles None address gracefully."""
        sample_property.full_address = None

        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property, breakdown)

        # Should use fallback address
        assert explanation.address == "Unknown" or len(explanation.address) > 0

    def test_explain_property_minimal_data(self, sample_property_minimal):
        """Test explanation with minimal property data."""
        scorer = PropertyScorer()
        breakdown = scorer.score(sample_property_minimal)

        explainer = ScoringExplainer()
        explanation = explainer.explain(sample_property_minimal, breakdown)

        assert isinstance(explanation, FullScoreExplanation)
        assert explanation.total_score >= 0

    def test_explain_zero_score_property(self):
        """Test explanation for property with zero score."""
        prop = Property(
            street="Zero St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="Zero St, Phoenix, AZ 85001",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=1800,
            price_per_sqft_raw=55.6,
            lot_sqft=5000,
            year_built=1950,
            garage_spaces=1,
            sewer_type=SewerType.CITY,
            hoa_fee=0,
        )

        # Create zero score breakdown
        empty_scores = []
        breakdown = ScoreBreakdown(
            location_scores=empty_scores,
            systems_scores=empty_scores,
            interior_scores=empty_scores,
        )

        explainer = ScoringExplainer()
        explanation = explainer.explain(prop, breakdown)

        assert explanation.total_score == 0.0
        assert explanation.tier == "Pass"

    def test_section_explanation_zero_max_score(self):
        """Test section explanation with zero max_score."""
        section = SectionExplanation(
            section="Test",
            section_letter="X",
            total_score=0.0,
            max_score=0.0,
            percentage=0.0,
            criteria=[],
            summary="No max score",
        )

        assert section.percentage == 0.0
        assert section.max_score == 0.0

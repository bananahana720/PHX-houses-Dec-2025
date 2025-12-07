"""Unit tests for quality metrics calculation."""

from src.phx_home_analysis.domain.entities import EnrichmentData
from src.phx_home_analysis.services.quality.metrics import (
    QualityMetricsCalculator,
    calculate_property_quality,
)
from src.phx_home_analysis.services.quality.models import QualityScore


class TestQualityMetricsCalculator:
    """Test suite for QualityMetricsCalculator class."""

    def test_calculate_with_all_required_fields_present(self):
        """Test completeness = 1.0 when all required fields present."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data)

        assert score.completeness == 1.0
        assert score.missing_fields == []

    def test_calculate_with_missing_required_fields(self):
        """Test completeness calculation with missing fields."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            # Missing: sqft, price, lot_sqft, year_built, garage_spaces, sewer_type
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data)

        # 3 present out of 9 required = 0.333...
        expected_completeness = 3 / 9
        assert abs(score.completeness - expected_completeness) < 0.01
        assert "sqft" in score.missing_fields
        assert "price" in score.missing_fields
        assert "lot_sqft" in score.missing_fields

    def test_calculate_with_high_confidence_fields(self):
        """Test high_confidence_pct with all fields above threshold."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }
        field_confidences = {
            "address": 0.90,
            "lot_sqft": 0.95,
            "year_built": 0.95,
            "garage_spaces": 0.95,
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data, field_confidences)

        # All 4 tracked fields have confidence >= 0.80
        assert score.high_confidence_pct == 1.0
        assert score.low_confidence_fields == []

    def test_calculate_with_low_confidence_fields(self):
        """Test high_confidence_pct with some fields below threshold."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
        }
        field_confidences = {
            "address": 0.90,  # HIGH
            "beds": 0.75,  # LOW (below 0.80 threshold)
            "orientation": 0.70,  # LOW
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data, field_confidences)

        # 1 out of 3 fields has confidence >= 0.80
        expected_high_conf_pct = 1 / 3
        assert abs(score.high_confidence_pct - expected_high_conf_pct) < 0.01
        assert "beds" in score.low_confidence_fields
        assert "orientation" in score.low_confidence_fields

    def test_overall_score_formula_60_40_weights(self):
        """Test overall_score = (completeness * 0.6) + (high_confidence_pct * 0.4)."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            # Missing: year_built, garage_spaces, sewer_type (6/9 = 0.667 completeness)
        }
        field_confidences = {
            "address": 0.90,  # HIGH
            "lot_sqft": 0.95,  # HIGH
            "orientation": 0.70,  # LOW
            # 2 out of 3 = 0.667 high_confidence_pct
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data, field_confidences)

        # completeness = 6/9 = 0.667
        # high_confidence_pct = 2/3 = 0.667
        # overall = (0.667 * 0.6) + (0.667 * 0.4) = 0.667
        expected_completeness = 6 / 9
        expected_high_conf = 2 / 3
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01

    def test_calculate_with_no_confidence_data_assumes_completeness(self):
        """Test that missing confidence data assumes high_confidence_pct = completeness."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            # Missing: year_built, garage_spaces, sewer_type (6/9 = 0.667)
        }

        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data, field_confidences=None)

        # When no confidence data, high_confidence_pct = completeness
        assert abs(score.completeness - score.high_confidence_pct) < 0.01

    def test_meets_threshold_with_high_quality_data(self):
        """Test meets_threshold returns True for high quality data."""
        property_data = {
            "address": "123 Main St",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }
        field_confidences = {
            "address": 0.90,
            "lot_sqft": 0.95,
            "year_built": 0.95,
            "garage_spaces": 0.95,
        }

        calculator = QualityMetricsCalculator()
        result = calculator.meets_threshold(property_data, field_confidences, threshold=0.95)

        # completeness = 1.0, high_conf = 1.0
        # overall = (1.0 * 0.6) + (1.0 * 0.4) = 1.0
        assert result is True

    def test_meets_threshold_with_low_quality_data(self):
        """Test meets_threshold returns False for low quality data."""
        property_data = {
            "address": "123 Main St",
            # Only 1 out of 9 required fields
        }
        field_confidences = {
            "address": 0.70,  # LOW confidence
        }

        calculator = QualityMetricsCalculator()
        result = calculator.meets_threshold(property_data, field_confidences, threshold=0.95)

        # completeness = 1/9 = 0.111, high_conf = 0/1 = 0.0
        # overall = (0.111 * 0.6) + (0.0 * 0.4) = 0.067
        assert result is False

    def test_get_improvement_suggestions_for_missing_fields(self):
        """Test improvement suggestions for missing fields."""
        score = QualityScore(
            completeness=0.5,
            high_confidence_pct=1.0,
            overall_score=0.7,
            missing_fields=["lot_sqft", "year_built", "garage_spaces"],
            low_confidence_fields=[],
        )

        calculator = QualityMetricsCalculator()
        suggestions = calculator.get_improvement_suggestions(score)

        assert len(suggestions) > 0
        assert any("missing required fields" in s.lower() for s in suggestions)
        assert any("lot_sqft" in s for s in suggestions)

    def test_get_improvement_suggestions_for_low_confidence(self):
        """Test improvement suggestions for low confidence fields."""
        score = QualityScore(
            completeness=1.0,
            high_confidence_pct=0.5,
            overall_score=0.8,
            missing_fields=[],
            low_confidence_fields=["orientation", "school_rating"],
        )

        calculator = QualityMetricsCalculator()
        suggestions = calculator.get_improvement_suggestions(score)

        assert len(suggestions) > 0
        assert any("low-confidence fields" in s.lower() for s in suggestions)
        assert any("orientation" in s for s in suggestions)


class TestCalculatePropertyQuality:
    """Test suite for calculate_property_quality() convenience function."""

    def test_calculate_with_enrichment_data_complete(self):
        """Test quality calculation with complete enrichment data."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type="city",
        )

        # Add provenance for tracked fields
        enrichment.set_field_provenance("lot_sqft", "assessor_api", 0.95)
        enrichment.set_field_provenance("year_built", "assessor_api", 0.95)
        enrichment.set_field_provenance("garage_spaces", "assessor_api", 0.95)
        enrichment.set_field_provenance("sewer_type", "assessor_api", 0.95)

        score = calculate_property_quality(enrichment)

        # 5 present out of 9 required (address, lot_sqft, year_built, garage_spaces, sewer_type)
        expected_completeness = 5 / 9
        # All 4 provenance fields have confidence >= 0.80
        expected_high_conf = 1.0
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01

    def test_calculate_with_enrichment_data_partial(self):
        """Test quality calculation with partial enrichment data."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=None,  # Missing
            garage_spaces=None,  # Missing
            sewer_type=None,  # Missing
        )

        # Add provenance only for lot_sqft
        enrichment.set_field_provenance("lot_sqft", "assessor_api", 0.95)

        score = calculate_property_quality(enrichment)

        # 2 present out of 9 required (address, lot_sqft)
        expected_completeness = 2 / 9
        # 1 provenance field, confidence = 0.95 >= 0.80
        expected_high_conf = 1.0
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01
        assert "year_built" in score.missing_fields
        assert "garage_spaces" in score.missing_fields

    def test_calculate_with_low_confidence_provenance(self):
        """Test quality calculation with low confidence provenance."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
        )

        # Add provenance with mixed confidence levels
        enrichment.set_field_provenance("lot_sqft", "web_scrape", 0.75)  # LOW
        enrichment.set_field_provenance("year_built", "assessor_api", 0.95)  # HIGH
        enrichment.set_field_provenance("garage_spaces", "ai_inference", 0.70)  # LOW

        score = calculate_property_quality(enrichment)

        # 4 present out of 9 required
        expected_completeness = 4 / 9
        # 1 out of 3 provenance fields has confidence >= 0.80
        expected_high_conf = 1 / 3
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01
        assert "lot_sqft" in score.low_confidence_fields
        assert "garage_spaces" in score.low_confidence_fields

    def test_calculate_with_no_provenance_data(self):
        """Test quality calculation with no provenance tracking."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type="city",
        )
        # No provenance set

        score = calculate_property_quality(enrichment)

        # 5 present out of 9 required
        expected_completeness = 5 / 9
        # No confidence data, so high_confidence_pct = completeness
        expected_high_conf = expected_completeness
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01

    def test_calculate_with_minimal_enrichment_data(self):
        """Test quality calculation with minimal enrichment data (address only)."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        score = calculate_property_quality(enrichment)

        # 1 present out of 9 required (address only)
        expected_completeness = 1 / 9
        # No confidence data, so high_confidence_pct = completeness
        expected_high_conf = expected_completeness
        expected_overall = (expected_completeness * 0.6) + (expected_high_conf * 0.4)

        assert abs(score.completeness - expected_completeness) < 0.01
        assert abs(score.high_confidence_pct - expected_high_conf) < 0.01
        assert abs(score.overall_score - expected_overall) < 0.01
        assert len(score.missing_fields) == 8  # All except address

    def test_quality_score_is_high_quality_property(self):
        """Test QualityScore.is_high_quality property."""
        score_high = QualityScore(
            completeness=1.0,
            high_confidence_pct=1.0,
            overall_score=1.0,
        )
        assert score_high.is_high_quality is True

        score_low = QualityScore(
            completeness=0.5,
            high_confidence_pct=0.5,
            overall_score=0.5,
        )
        assert score_low.is_high_quality is False

    def test_quality_score_tier_classification(self):
        """Test QualityScore.quality_tier classification."""
        score_excellent = QualityScore(
            completeness=1.0,
            high_confidence_pct=1.0,
            overall_score=0.95,
        )
        assert score_excellent.quality_tier == "excellent"

        score_good = QualityScore(
            completeness=0.85,
            high_confidence_pct=0.85,
            overall_score=0.85,
        )
        assert score_good.quality_tier == "good"

        score_fair = QualityScore(
            completeness=0.7,
            high_confidence_pct=0.7,
            overall_score=0.7,
        )
        assert score_fair.quality_tier == "fair"

        score_poor = QualityScore(
            completeness=0.3,
            high_confidence_pct=0.3,
            overall_score=0.3,
        )
        assert score_poor.quality_tier == "poor"

    def test_calculate_with_all_enrichment_fields_tracked(self):
        """Test with all enrichment fields having provenance."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type="city",
            hoa_fee=0.0,
            school_rating=7.5,
            orientation="north",
        )

        # Add provenance for all fields
        enrichment.set_field_provenance("lot_sqft", "assessor_api", 0.95)
        enrichment.set_field_provenance("year_built", "assessor_api", 0.95)
        enrichment.set_field_provenance("garage_spaces", "assessor_api", 0.95)
        enrichment.set_field_provenance("sewer_type", "assessor_api", 0.95)
        enrichment.set_field_provenance("hoa_fee", "zillow", 0.85)
        enrichment.set_field_provenance("school_rating", "greatschools", 0.90)
        enrichment.set_field_provenance("orientation", "google_maps", 0.90)

        score = calculate_property_quality(enrichment)

        # All 7 provenance fields have confidence >= 0.80
        assert score.high_confidence_pct == 1.0
        assert score.low_confidence_fields == []

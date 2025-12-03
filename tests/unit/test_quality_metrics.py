"""Unit tests for quality metrics and data lineage tracking.

Tests cover:
- QualityScore calculation and validation
- Completeness calculation
- High confidence percentage calculation
- LineageTracker record and retrieve operations
- Quality check script functionality
"""

from datetime import datetime

import pytest

from src.phx_home_analysis.services.quality import (
    DataSource,
    FieldLineage,
    LineageTracker,
    QualityMetricsCalculator,
    QualityScore,
)

# ============================================================================
# DataSource Tests
# ============================================================================


class TestDataSource:
    """Test DataSource enum and default confidences."""

    def test_data_source_values(self):
        """Test all DataSource enum values exist."""
        assert DataSource.CSV.value == "csv"
        assert DataSource.ASSESSOR_API.value == "assessor_api"
        assert DataSource.WEB_SCRAPE.value == "web_scrape"
        assert DataSource.AI_INFERENCE.value == "ai_inference"
        assert DataSource.MANUAL.value == "manual"
        assert DataSource.DEFAULT.value == "default"

    def test_default_confidence_csv(self):
        """CSV data should have high confidence (0.9)."""
        assert DataSource.CSV.default_confidence == 0.9

    def test_default_confidence_assessor_api(self):
        """Assessor API data should have highest confidence (0.95)."""
        assert DataSource.ASSESSOR_API.default_confidence == 0.95

    def test_default_confidence_web_scrape(self):
        """Web scrape data has moderate confidence (0.75)."""
        assert DataSource.WEB_SCRAPE.default_confidence == 0.75

    def test_default_confidence_ai_inference(self):
        """AI inference has moderate-low confidence (0.7)."""
        assert DataSource.AI_INFERENCE.default_confidence == 0.7

    def test_default_confidence_manual(self):
        """Manual data has good confidence (0.85)."""
        assert DataSource.MANUAL.default_confidence == 0.85

    def test_default_confidence_default(self):
        """Default values have low confidence (0.5)."""
        assert DataSource.DEFAULT.default_confidence == 0.5


# ============================================================================
# FieldLineage Tests
# ============================================================================


class TestFieldLineage:
    """Test FieldLineage dataclass."""

    def test_create_field_lineage(self):
        """Test creating a FieldLineage with all fields."""
        now = datetime.now()
        lineage = FieldLineage(
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
            updated_at=now,
            original_value=9500,
            notes="From county API",
        )

        assert lineage.field_name == "lot_sqft"
        assert lineage.source == DataSource.ASSESSOR_API
        assert lineage.confidence == 0.95
        assert lineage.updated_at == now
        assert lineage.original_value == 9500
        assert lineage.notes == "From county API"

    def test_field_lineage_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            FieldLineage(
                field_name="test",
                source=DataSource.CSV,
                confidence=1.5,  # Invalid
                updated_at=datetime.now(),
            )

        with pytest.raises(ValueError, match="Confidence must be between"):
            FieldLineage(
                field_name="test",
                source=DataSource.CSV,
                confidence=-0.1,  # Invalid
                updated_at=datetime.now(),
            )

    def test_field_lineage_string_source_conversion(self):
        """Test that string sources are converted to enum."""
        lineage = FieldLineage(
            field_name="test",
            source="csv",  # String instead of enum
            confidence=0.9,
            updated_at=datetime.now(),
        )
        assert lineage.source == DataSource.CSV

    def test_field_lineage_to_dict(self):
        """Test serialization to dictionary."""
        now = datetime.now()
        lineage = FieldLineage(
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
            updated_at=now,
            original_value=9500,
        )

        data = lineage.to_dict()
        assert data["field_name"] == "lot_sqft"
        assert data["source"] == "assessor_api"
        assert data["confidence"] == 0.95
        assert data["updated_at"] == now.isoformat()
        assert data["original_value"] == 9500

    def test_field_lineage_from_dict(self):
        """Test deserialization from dictionary."""
        now = datetime.now()
        data = {
            "field_name": "lot_sqft",
            "source": "assessor_api",
            "confidence": 0.95,
            "updated_at": now.isoformat(),
            "original_value": 9500,
            "notes": "Test note",
        }

        lineage = FieldLineage.from_dict(data)
        assert lineage.field_name == "lot_sqft"
        assert lineage.source == DataSource.ASSESSOR_API
        assert lineage.confidence == 0.95
        assert lineage.original_value == 9500
        assert lineage.notes == "Test note"


# ============================================================================
# QualityScore Tests
# ============================================================================


class TestQualityScore:
    """Test QualityScore dataclass."""

    def test_create_quality_score(self):
        """Test creating a QualityScore with all fields."""
        score = QualityScore(
            completeness=0.9,
            high_confidence_pct=0.85,
            overall_score=0.88,
            missing_fields=["sewer_type"],
            low_confidence_fields=["year_built"],
        )

        assert score.completeness == 0.9
        assert score.high_confidence_pct == 0.85
        assert score.overall_score == 0.88
        assert score.missing_fields == ["sewer_type"]
        assert score.low_confidence_fields == ["year_built"]

    def test_quality_score_validation(self):
        """Test validation of score values."""
        with pytest.raises(ValueError):
            QualityScore(
                completeness=1.5,  # Invalid
                high_confidence_pct=0.8,
                overall_score=0.9,
            )

    def test_is_high_quality_true(self):
        """Test high quality detection when >= 95%."""
        score = QualityScore(
            completeness=1.0,
            high_confidence_pct=0.9,
            overall_score=0.96,
        )
        assert score.is_high_quality is True

    def test_is_high_quality_false(self):
        """Test high quality detection when < 95%."""
        score = QualityScore(
            completeness=0.8,
            high_confidence_pct=0.7,
            overall_score=0.76,
        )
        assert score.is_high_quality is False

    def test_quality_tier_excellent(self):
        """Test excellent tier (>= 95%)."""
        score = QualityScore(
            completeness=1.0,
            high_confidence_pct=0.95,
            overall_score=0.98,
        )
        assert score.quality_tier == "excellent"

    def test_quality_tier_good(self):
        """Test good tier (80-95%)."""
        score = QualityScore(
            completeness=0.9,
            high_confidence_pct=0.85,
            overall_score=0.88,
        )
        assert score.quality_tier == "good"

    def test_quality_tier_fair(self):
        """Test fair tier (60-80%)."""
        score = QualityScore(
            completeness=0.7,
            high_confidence_pct=0.6,
            overall_score=0.66,
        )
        assert score.quality_tier == "fair"

    def test_quality_tier_poor(self):
        """Test poor tier (< 60%)."""
        score = QualityScore(
            completeness=0.5,
            high_confidence_pct=0.4,
            overall_score=0.46,
        )
        assert score.quality_tier == "poor"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        score = QualityScore(
            completeness=0.9,
            high_confidence_pct=0.85,
            overall_score=0.88,
            missing_fields=["sewer_type"],
            low_confidence_fields=["year_built"],
        )

        data = score.to_dict()
        assert data["completeness"] == 0.9
        assert data["high_confidence_pct"] == 0.85
        assert data["overall_score"] == 0.88
        assert data["quality_tier"] == "good"
        assert data["missing_fields"] == ["sewer_type"]
        assert data["low_confidence_fields"] == ["year_built"]


# ============================================================================
# QualityMetricsCalculator Tests
# ============================================================================


class TestQualityMetricsCalculator:
    """Test QualityMetricsCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a calculator instance."""
        return QualityMetricsCalculator()

    @pytest.fixture
    def complete_property(self):
        """Property with all required fields present."""
        return {
            "address": "123 Main St, Phoenix, AZ 85001",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }

    @pytest.fixture
    def partial_property(self):
        """Property with some required fields missing."""
        return {
            "address": "123 Main St, Phoenix, AZ 85001",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            # Missing: lot_sqft, year_built, garage_spaces, sewer_type
        }

    def test_completeness_all_fields_present(self, calculator, complete_property):
        """Test 100% completeness when all required fields present."""
        score = calculator.calculate(complete_property)
        assert score.completeness == 1.0
        assert score.missing_fields == []

    def test_completeness_partial_fields(self, calculator, partial_property):
        """Test partial completeness with missing fields."""
        score = calculator.calculate(partial_property)
        # 5 of 9 fields present = 5/9 = ~0.556
        assert score.completeness == pytest.approx(5 / 9, rel=0.01)
        assert set(score.missing_fields) == {
            "lot_sqft",
            "year_built",
            "garage_spaces",
            "sewer_type",
        }

    def test_completeness_empty_property(self, calculator):
        """Test 0% completeness with empty property."""
        score = calculator.calculate({})
        assert score.completeness == 0.0
        assert len(score.missing_fields) == 9  # All required fields missing

    def test_high_confidence_calculation(self, calculator, complete_property):
        """Test high confidence percentage calculation."""
        confidences = {
            "address": 0.95,  # High
            "beds": 0.90,  # High
            "baths": 0.85,  # High
            "sqft": 0.70,  # Low (below 0.8)
            "price": 0.95,  # High
        }

        score = calculator.calculate(complete_property, confidences)
        # 4 of 5 fields are high confidence = 0.80
        assert score.high_confidence_pct == pytest.approx(0.80, rel=0.01)
        assert score.low_confidence_fields == ["sqft"]

    def test_high_confidence_no_data(self, calculator, complete_property):
        """Test confidence defaults to completeness when no confidence data."""
        score = calculator.calculate(complete_property, field_confidences=None)
        # Without confidence data, high_confidence_pct = completeness
        assert score.high_confidence_pct == score.completeness

    def test_overall_score_formula(self, calculator, complete_property):
        """Test overall score weighted formula: (completeness * 0.6) + (high_conf * 0.4)."""
        confidences = {
            "address": 0.95,
            "beds": 0.90,
            "baths": 0.85,
            "sqft": 0.70,
            "price": 0.95,
        }

        score = calculator.calculate(complete_property, confidences)

        # completeness = 1.0 (all fields present)
        # high_confidence_pct = 0.80 (4/5 above threshold)
        # overall = (1.0 * 0.6) + (0.80 * 0.4) = 0.6 + 0.32 = 0.92
        expected_overall = (1.0 * 0.6) + (0.80 * 0.4)
        assert score.overall_score == pytest.approx(expected_overall, rel=0.01)

    def test_custom_required_fields(self):
        """Test calculator with custom required fields."""
        calculator = QualityMetricsCalculator(
            required_fields=["address", "price"]
        )

        property_data = {"address": "123 Main St"}
        score = calculator.calculate(property_data)

        # 1 of 2 fields = 0.5
        assert score.completeness == 0.5
        assert score.missing_fields == ["price"]

    def test_custom_confidence_threshold(self):
        """Test calculator with custom confidence threshold."""
        calculator = QualityMetricsCalculator(
            high_confidence_threshold=0.9
        )

        property_data = {"address": "123 Main St"}
        confidences = {"address": 0.85}  # Below 0.9 threshold

        score = calculator.calculate(property_data, confidences)
        assert score.high_confidence_pct == 0.0  # All below threshold
        assert "address" in score.low_confidence_fields

    def test_meets_threshold_pass(self, calculator, complete_property):
        """Test meets_threshold returns True when above threshold."""
        assert calculator.meets_threshold(complete_property, threshold=0.5) is True

    def test_meets_threshold_fail(self, calculator, partial_property):
        """Test meets_threshold returns False when below threshold."""
        assert calculator.meets_threshold(partial_property, threshold=0.95) is False

    def test_calculate_batch(self, calculator, complete_property, partial_property):
        """Test batch calculation returns individual and aggregate scores."""
        properties = [complete_property, partial_property]
        scores, aggregate = calculator.calculate_batch(properties)

        assert len(scores) == 2
        assert scores[0].completeness == 1.0
        assert scores[1].completeness == pytest.approx(5 / 9, rel=0.01)

        # Aggregate should be average
        expected_avg_completeness = (1.0 + 5 / 9) / 2
        assert aggregate.completeness == pytest.approx(
            expected_avg_completeness, rel=0.01
        )

    def test_calculate_batch_empty(self, calculator):
        """Test batch calculation with empty list."""
        scores, aggregate = calculator.calculate_batch([])
        assert scores == []
        assert aggregate.completeness == 0.0
        assert aggregate.overall_score == 0.0

    def test_get_improvement_suggestions_missing_fields(self, calculator):
        """Test suggestions for missing fields."""
        score = QualityScore(
            completeness=0.7,
            high_confidence_pct=0.9,
            overall_score=0.78,
            missing_fields=["lot_sqft", "year_built", "garage_spaces"],
            low_confidence_fields=[],
        )

        suggestions = calculator.get_improvement_suggestions(score)
        assert any("missing required fields" in s.lower() for s in suggestions)
        assert any("lot_sqft" in s for s in suggestions)

    def test_get_improvement_suggestions_low_confidence(self, calculator):
        """Test suggestions for low confidence fields."""
        score = QualityScore(
            completeness=1.0,
            high_confidence_pct=0.5,
            overall_score=0.80,
            missing_fields=[],
            low_confidence_fields=["year_built", "sewer_type"],
        )

        suggestions = calculator.get_improvement_suggestions(score)
        assert any("low-confidence" in s.lower() for s in suggestions)

    def test_get_improvement_suggestions_excellent(self, calculator):
        """Test suggestions when quality is excellent."""
        score = QualityScore(
            completeness=1.0,
            high_confidence_pct=1.0,
            overall_score=1.0,
            missing_fields=[],
            low_confidence_fields=[],
        )

        suggestions = calculator.get_improvement_suggestions(score)
        assert any("excellent" in s.lower() or "no improvements" in s.lower() for s in suggestions)


# ============================================================================
# LineageTracker Tests
# ============================================================================


class TestLineageTracker:
    """Test LineageTracker class."""

    @pytest.fixture
    def temp_lineage_file(self, tmp_path):
        """Create a temporary lineage file path."""
        return tmp_path / "test_lineage.json"

    @pytest.fixture
    def tracker(self, temp_lineage_file):
        """Create a tracker with temporary file."""
        return LineageTracker(temp_lineage_file)

    def test_record_field(self, tracker):
        """Test recording field lineage."""
        lineage = tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
            original_value=9500,
        )

        assert lineage.field_name == "lot_sqft"
        assert lineage.source == DataSource.ASSESSOR_API
        assert lineage.confidence == 0.95
        assert lineage.original_value == 9500

    def test_get_field_lineage(self, tracker):
        """Test retrieving field lineage."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )

        lineage = tracker.get_field_lineage("ef7cd95f", "lot_sqft")
        assert lineage is not None
        assert lineage.field_name == "lot_sqft"

    def test_get_field_lineage_not_found(self, tracker):
        """Test retrieving non-existent lineage returns None."""
        lineage = tracker.get_field_lineage("nonexistent", "field")
        assert lineage is None

    def test_get_property_lineage(self, tracker):
        """Test retrieving all lineage for a property."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="year_built",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )

        lineage = tracker.get_property_lineage("ef7cd95f")
        assert len(lineage) == 2
        assert "lot_sqft" in lineage
        assert "year_built" in lineage

    def test_record_batch(self, tracker):
        """Test recording multiple fields at once."""
        fields = {
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
        }

        lineages = tracker.record_batch(
            property_hash="ef7cd95f",
            source=DataSource.ASSESSOR_API,
            fields=fields,
        )

        assert len(lineages) == 3
        assert tracker.field_count("ef7cd95f") == 3

    def test_get_all_confidences(self, tracker):
        """Test getting all confidence scores for a property."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="beds",
            source=DataSource.CSV,
            confidence=0.90,
        )

        confidences = tracker.get_all_confidences("ef7cd95f")
        assert confidences["lot_sqft"] == 0.95
        assert confidences["beds"] == 0.90

    def test_get_low_confidence_fields(self, tracker):
        """Test finding low confidence fields."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="year_built",
            source=DataSource.AI_INFERENCE,
            confidence=0.70,
        )

        low_conf = tracker.get_low_confidence_fields("ef7cd95f", threshold=0.8)
        assert "year_built" in low_conf
        assert "lot_sqft" not in low_conf

    def test_save_and_load(self, temp_lineage_file):
        """Test persistence - save and reload."""
        # Create and populate tracker
        tracker1 = LineageTracker(temp_lineage_file)
        tracker1.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
            original_value=9500,
        )
        tracker1.save()

        # Create new tracker that loads from file
        tracker2 = LineageTracker(temp_lineage_file)
        lineage = tracker2.get_field_lineage("ef7cd95f", "lot_sqft")

        assert lineage is not None
        assert lineage.field_name == "lot_sqft"
        assert lineage.confidence == 0.95
        assert lineage.original_value == 9500

    def test_clear_property(self, tracker):
        """Test clearing all lineage for a property."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )

        tracker.clear_property("ef7cd95f")
        assert tracker.get_property_lineage("ef7cd95f") == {}

    def test_property_count(self, tracker):
        """Test counting tracked properties."""
        tracker.record_field(
            property_hash="ef7cd95f",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )
        tracker.record_field(
            property_hash="abc12345",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            confidence=0.95,
        )

        assert tracker.property_count() == 2

    def test_load_nonexistent_file(self, tmp_path):
        """Test graceful handling of missing file."""
        tracker = LineageTracker(tmp_path / "nonexistent.json")
        # Should not raise, just have empty data
        assert tracker.property_count() == 0

    def test_load_invalid_json(self, temp_lineage_file):
        """Test graceful handling of invalid JSON."""
        # Write invalid JSON
        temp_lineage_file.write_text("not valid json {{{")

        # Should not raise, just log error and have empty data
        tracker = LineageTracker(temp_lineage_file)
        assert tracker.property_count() == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestQualityIntegration:
    """Integration tests combining lineage and metrics."""

    def test_lineage_to_metrics_workflow(self, tmp_path):
        """Test complete workflow: record lineage, calculate metrics."""
        # 1. Create lineage tracker
        tracker = LineageTracker(tmp_path / "lineage.json")

        # 2. Record field lineage from various sources
        property_hash = "ef7cd95f"
        tracker.record_batch(
            property_hash=property_hash,
            source=DataSource.ASSESSOR_API,
            fields={"lot_sqft": 9500, "year_built": 2010, "garage_spaces": 2},
            confidence=0.95,
        )
        tracker.record_batch(
            property_hash=property_hash,
            source=DataSource.CSV,
            fields={"address": "123 Main St", "beds": 4, "baths": 2.0},
            confidence=0.90,
        )
        tracker.record_field(
            property_hash=property_hash,
            field_name="sewer_type",
            source=DataSource.MANUAL,
            confidence=0.85,
            original_value="city",
        )

        # 3. Property data
        property_data = {
            "address": "123 Main St, Phoenix, AZ 85001",
            "beds": 4,
            "baths": 2.0,
            "sqft": 2200,
            "price": 475000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }

        # 4. Get confidences and calculate metrics
        confidences = tracker.get_all_confidences(property_hash)
        calculator = QualityMetricsCalculator()
        score = calculator.calculate(property_data, confidences)

        # 5. Verify results
        assert score.completeness == 1.0  # All required fields present
        assert score.high_confidence_pct > 0.8  # Most fields high confidence
        assert score.overall_score > 0.9  # High overall quality

    def test_quality_gate_threshold(self, tmp_path):
        """Test quality gate with realistic data."""
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

        confidences = {
            "address": 0.95,
            "beds": 0.90,
            "baths": 0.90,
            "sqft": 0.90,
            "price": 0.95,
            "lot_sqft": 0.95,
            "year_built": 0.95,
            "garage_spaces": 0.95,
            "sewer_type": 0.85,
        }

        calculator = QualityMetricsCalculator()

        # Should pass 95% threshold
        assert calculator.meets_threshold(property_data, confidences, threshold=0.95) is True

        # Remove some confidence to fail threshold
        low_confidences = dict.fromkeys(confidences, 0.5)
        assert calculator.meets_threshold(property_data, low_confidences, threshold=0.95) is False

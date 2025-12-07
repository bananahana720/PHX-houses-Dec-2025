"""Unit tests for AI enrichment field inference module.

Tests all components of the AI enrichment system:
- FieldTagger: Missing field identification
- FieldInferencer: Triage workflow orchestration
- ConfidenceScorer: Confidence calculation
- Models: ConfidenceLevel, FieldInference, TriageResult
"""

import pytest

from src.phx_home_analysis.services.ai_enrichment import (
    ConfidenceLevel,
    ConfidenceScorer,
    FieldInference,
    FieldInferencer,
    FieldTagger,
    TriageResult,
)

# ============================================================================
# ConfidenceLevel Tests
# ============================================================================


class TestConfidenceLevel:
    """Test the ConfidenceLevel enum and from_score() method."""

    def test_from_score_high(self):
        """Test that scores >= 0.8 return HIGH."""
        assert ConfidenceLevel.from_score(0.8) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(0.9) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(1.0) == ConfidenceLevel.HIGH

    def test_from_score_medium(self):
        """Test that scores 0.5-0.8 return MEDIUM."""
        assert ConfidenceLevel.from_score(0.5) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.6) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.79) == ConfidenceLevel.MEDIUM

    def test_from_score_low(self):
        """Test that scores < 0.5 return LOW."""
        assert ConfidenceLevel.from_score(0.0) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.3) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.49) == ConfidenceLevel.LOW

    def test_from_score_boundary_high_medium(self):
        """Test boundary between HIGH and MEDIUM at 0.8."""
        assert ConfidenceLevel.from_score(0.8) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(0.7999) == ConfidenceLevel.MEDIUM

    def test_from_score_boundary_medium_low(self):
        """Test boundary between MEDIUM and LOW at 0.5."""
        assert ConfidenceLevel.from_score(0.5) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.4999) == ConfidenceLevel.LOW

    def test_enum_values(self):
        """Test that enum values are correct strings."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


# ============================================================================
# FieldInference Tests
# ============================================================================


class TestFieldInference:
    """Test the FieldInference dataclass."""

    def test_create_valid_inference(self):
        """Test creating a valid FieldInference."""
        inference = FieldInference(
            field_name="beds",
            inferred_value=4,
            confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            source="web_scrape",
        )
        assert inference.field_name == "beds"
        assert inference.inferred_value == 4
        assert inference.confidence == 0.9
        assert inference.confidence_level == ConfidenceLevel.HIGH
        assert inference.source == "web_scrape"
        assert inference.reasoning is None

    def test_create_inference_with_reasoning(self):
        """Test creating FieldInference with reasoning."""
        inference = FieldInference(
            field_name="lot_sqft",
            inferred_value=9500,
            confidence=0.95,
            confidence_level=ConfidenceLevel.HIGH,
            source="assessor_api",
            reasoning="Retrieved from Maricopa County records",
        )
        assert inference.reasoning == "Retrieved from Maricopa County records"

    def test_is_resolved_true(self):
        """Test is_resolved returns True for resolved inferences."""
        inference = FieldInference(
            field_name="beds",
            inferred_value=4,
            confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            source="web_scrape",
        )
        assert inference.is_resolved is True

    def test_is_resolved_false_for_pending(self):
        """Test is_resolved returns False for ai_pending source."""
        inference = FieldInference(
            field_name="sewer_type",
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="ai_pending",
        )
        assert inference.is_resolved is False

    def test_is_resolved_false_for_none_value(self):
        """Test is_resolved returns False when inferred_value is None."""
        inference = FieldInference(
            field_name="garage_spaces",
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="web_scrape",
        )
        assert inference.is_resolved is False

    def test_needs_ai_inference(self):
        """Test needs_ai_inference property."""
        pending = FieldInference(
            field_name="sewer_type",
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="ai_pending",
        )
        assert pending.needs_ai_inference is True

        resolved = FieldInference(
            field_name="beds",
            inferred_value=4,
            confidence=0.9,
            confidence_level=ConfidenceLevel.HIGH,
            source="web_scrape",
        )
        assert resolved.needs_ai_inference is False

    def test_invalid_confidence_too_high(self):
        """Test that confidence > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=1.5,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            )

    def test_invalid_confidence_negative(self):
        """Test that negative confidence raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=-0.1,
                confidence_level=ConfidenceLevel.LOW,
                source="web_scrape",
            )

    def test_invalid_source(self):
        """Test that invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Source must be one of"):
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="invalid_source",
            )


# ============================================================================
# TriageResult Tests
# ============================================================================


class TestTriageResult:
    """Test the TriageResult dataclass."""

    def test_create_empty_result(self):
        """Test creating an empty TriageResult."""
        result = TriageResult(property_hash="abc12345")
        assert result.property_hash == "abc12345"
        assert result.inferences == []
        assert result.fields_resolved == 0
        assert result.fields_pending == 0

    def test_create_result_with_inferences(self):
        """Test creating TriageResult with inferences."""
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]
        result = TriageResult(property_hash="abc12345", inferences=inferences)

        assert result.fields_resolved == 1
        assert result.fields_pending == 1

    def test_total_fields(self):
        """Test total_fields property."""
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="baths",
                inferred_value=2.0,
                confidence=0.85,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]
        result = TriageResult(property_hash="abc12345", inferences=inferences)
        assert result.total_fields == 3

    def test_resolution_rate(self):
        """Test resolution_rate calculation."""
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="baths",
                inferred_value=2.0,
                confidence=0.85,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
            FieldInference(
                field_name="lot_sqft",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]
        result = TriageResult(property_hash="abc12345", inferences=inferences)
        assert result.resolution_rate == 0.5  # 2/4 resolved

    def test_resolution_rate_empty(self):
        """Test resolution_rate returns 0.0 for empty result."""
        result = TriageResult(property_hash="abc12345")
        assert result.resolution_rate == 0.0

    def test_get_pending_inferences(self):
        """Test get_pending_inferences filter."""
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]
        result = TriageResult(property_hash="abc12345", inferences=inferences)
        pending = result.get_pending_inferences()

        assert len(pending) == 1
        assert pending[0].field_name == "sewer_type"

    def test_get_resolved_inferences(self):
        """Test get_resolved_inferences filter."""
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]
        result = TriageResult(property_hash="abc12345", inferences=inferences)
        resolved = result.get_resolved_inferences()

        assert len(resolved) == 1
        assert resolved[0].field_name == "beds"


# ============================================================================
# FieldTagger Tests
# ============================================================================


class TestFieldTagger:
    """Test the FieldTagger class."""

    def test_tag_all_missing_fields(self):
        """Test tagging when all fields are missing."""
        tagger = FieldTagger()
        missing = tagger.tag_missing_fields({})

        expected = [
            "beds",
            "baths",
            "sqft",
            "lot_sqft",
            "year_built",
            "garage_spaces",
            "sewer_type",
            "has_pool",
        ]
        assert missing == expected

    def test_tag_some_missing_fields(self):
        """Test tagging when some fields are present."""
        tagger = FieldTagger()
        property_data = {
            "beds": 4,
            "baths": 2.0,
            "sqft": 2000,
        }
        missing = tagger.tag_missing_fields(property_data)

        assert "beds" not in missing
        assert "baths" not in missing
        assert "sqft" not in missing
        assert "lot_sqft" in missing
        assert "year_built" in missing

    def test_tag_none_values_as_missing(self):
        """Test that None values are considered missing."""
        tagger = FieldTagger()
        property_data = {
            "beds": 4,
            "baths": None,  # Should be tagged as missing
            "sqft": 2000,
        }
        missing = tagger.tag_missing_fields(property_data)

        assert "beds" not in missing
        assert "baths" in missing  # None is missing
        assert "sqft" not in missing

    def test_tag_no_missing_fields(self):
        """Test tagging when all fields are present."""
        tagger = FieldTagger()
        property_data = {
            "beds": 4,
            "baths": 2.0,
            "sqft": 2000,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "has_pool": True,
        }
        missing = tagger.tag_missing_fields(property_data)
        assert missing == []

    def test_get_required_fields(self):
        """Test get_required_fields returns correct list."""
        tagger = FieldTagger()
        required = tagger.get_required_fields()

        assert len(required) == 8
        assert "beds" in required
        assert "baths" in required
        assert "sewer_type" in required

    def test_required_fields_is_copy(self):
        """Test that get_required_fields returns a copy."""
        tagger = FieldTagger()
        required = tagger.get_required_fields()
        required.append("extra_field")

        # Original should not be modified
        assert "extra_field" not in tagger.REQUIRED_FIELDS


# ============================================================================
# FieldInferencer Tests
# ============================================================================


class TestFieldInferencer:
    """Test the FieldInferencer class."""

    def test_init_creates_tagger(self):
        """Test that FieldInferencer initializes with a FieldTagger."""
        inferencer = FieldInferencer()
        assert isinstance(inferencer.tagger, FieldTagger)

    @pytest.mark.asyncio
    async def test_infer_fields_returns_inferences(self):
        """Test that infer_fields returns list of FieldInference."""
        inferencer = FieldInferencer()
        property_data = {"beds": 4, "baths": None}

        results = await inferencer.infer_fields(property_data, "123 Main St, Phoenix, AZ 85001")

        assert isinstance(results, list)
        assert all(isinstance(r, FieldInference) for r in results)

    @pytest.mark.asyncio
    async def test_infer_fields_marks_missing_for_ai(self):
        """Test that missing fields are marked for AI inference."""
        inferencer = FieldInferencer()
        property_data = {
            "beds": 4,
            "baths": None,
            "sqft": 2000,
        }

        results = await inferencer.infer_fields(property_data, "123 Main St, Phoenix, AZ 85001")

        # baths should be marked as ai_pending (since programmatic fails)
        baths_result = next((r for r in results if r.field_name == "baths"), None)
        assert baths_result is not None
        assert baths_result.source == "ai_pending"
        assert baths_result.needs_ai_inference is True

    @pytest.mark.asyncio
    async def test_infer_fields_all_required(self):
        """Test that all required missing fields get inferences."""
        inferencer = FieldInferencer()
        property_data = {}  # All fields missing

        results = await inferencer.infer_fields(property_data, "123 Main St, Phoenix, AZ 85001")

        # Should have inference for each required field
        result_fields = {r.field_name for r in results}
        expected_fields = set(FieldTagger.REQUIRED_FIELDS)
        assert result_fields == expected_fields

    def test_create_ai_pending_inference(self):
        """Test _create_ai_pending_inference method."""
        inferencer = FieldInferencer()
        inference = inferencer._create_ai_pending_inference("sewer_type")

        assert inference.field_name == "sewer_type"
        assert inference.inferred_value is None
        assert inference.confidence == 0.0
        assert inference.confidence_level == ConfidenceLevel.LOW
        assert inference.source == "ai_pending"
        assert inference.reasoning is not None

    def test_create_triage_result(self):
        """Test create_triage_result method."""
        inferencer = FieldInferencer()
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=0.9,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
        ]

        result = inferencer.create_triage_result("abc12345", inferences)

        assert isinstance(result, TriageResult)
        assert result.property_hash == "abc12345"
        assert result.inferences == inferences

    def test_get_field_source_priority_listing_fields(self):
        """Test source priority for listing-sourced fields."""
        inferencer = FieldInferencer()

        for field in ["beds", "baths", "sqft"]:
            priority = inferencer.get_field_source_priority(field)
            assert priority[0] == "web_scrape"
            assert "assessor_api" in priority

    def test_get_field_source_priority_assessor_fields(self):
        """Test source priority for assessor-sourced fields."""
        inferencer = FieldInferencer()

        for field in ["lot_sqft", "year_built"]:
            priority = inferencer.get_field_source_priority(field)
            assert priority[0] == "assessor_api"

    def test_get_field_source_priority_sewer(self):
        """Test source priority for sewer_type (often manual)."""
        inferencer = FieldInferencer()
        priority = inferencer.get_field_source_priority("sewer_type")

        assert "ai_inference" in priority
        assert "assessor_api" not in priority  # Not reliable for sewer


# ============================================================================
# ConfidenceScorer Tests
# ============================================================================


class TestConfidenceScorer:
    """Test the ConfidenceScorer class."""

    def test_score_inference_basic(self):
        """Test basic confidence scoring."""
        scorer = ConfidenceScorer()
        inference = FieldInference(
            field_name="lot_sqft",
            inferred_value=9500,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="assessor_api",
        )

        score = scorer.score_inference(inference)
        # lot_sqft (0.95) * assessor_api (0.95) * confidence (1.0) = 0.9025
        assert score == 0.9025

    def test_score_inference_web_scrape(self):
        """Test scoring for web scrape source."""
        scorer = ConfidenceScorer()
        inference = FieldInference(
            field_name="beds",
            inferred_value=4,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="web_scrape",
        )

        score = scorer.score_inference(inference)
        # beds (0.9) * web_scrape (0.85) * confidence (1.0) = 0.765
        assert score == pytest.approx(0.765, rel=0.01)

    def test_score_inference_ai_pending_zero(self):
        """Test that ai_pending source results in zero score."""
        scorer = ConfidenceScorer()
        inference = FieldInference(
            field_name="beds",
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="ai_pending",
        )

        score = scorer.score_inference(inference)
        assert score == 0.0

    def test_score_inference_custom_reliability(self):
        """Test scoring with custom source reliability."""
        scorer = ConfidenceScorer()
        inference = FieldInference(
            field_name="lot_sqft",
            inferred_value=9500,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="assessor_api",
        )

        score = scorer.score_inference(inference, source_reliability=0.5)
        # lot_sqft (0.95) * custom (0.5) * confidence (1.0) = 0.475
        assert score == pytest.approx(0.475, rel=0.01)

    def test_score_inference_capped_at_one(self):
        """Test that score is capped at 1.0."""
        scorer = ConfidenceScorer()
        inference = FieldInference(
            field_name="lot_sqft",
            inferred_value=9500,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="assessor_api",
        )

        # Even with very high reliability, capped at 1.0
        score = scorer.score_inference(inference, source_reliability=2.0)
        assert score <= 1.0

    def test_score_and_update_inference(self):
        """Test score_and_update_inference returns updated inference."""
        scorer = ConfidenceScorer()
        original = FieldInference(
            field_name="beds",
            inferred_value=4,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="web_scrape",
        )

        updated = scorer.score_and_update_inference(original)

        assert updated.field_name == original.field_name
        assert updated.inferred_value == original.inferred_value
        # Confidence should be adjusted
        assert updated.confidence == pytest.approx(0.765, rel=0.01)
        assert updated.confidence_level == ConfidenceLevel.MEDIUM

    def test_get_field_weight(self):
        """Test get_field_weight returns correct weights."""
        scorer = ConfidenceScorer()

        assert scorer.get_field_weight("beds") == 0.9
        assert scorer.get_field_weight("lot_sqft") == 0.95
        assert scorer.get_field_weight("sewer_type") == 0.6
        assert scorer.get_field_weight("unknown_field") == 0.5

    def test_get_source_reliability(self):
        """Test get_source_reliability returns correct values."""
        scorer = ConfidenceScorer()

        assert scorer.get_source_reliability("assessor_api") == 0.95
        assert scorer.get_source_reliability("web_scrape") == 0.85
        assert scorer.get_source_reliability("ai_pending") == 0.0
        assert scorer.get_source_reliability("unknown") == 0.5

    def test_score_multiple_inferences(self):
        """Test scoring multiple inferences at once."""
        scorer = ConfidenceScorer()
        inferences = [
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
            FieldInference(
                field_name="lot_sqft",
                inferred_value=9500,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                source="assessor_api",
            ),
        ]

        scored = scorer.score_multiple_inferences(inferences)

        assert len(scored) == 2
        assert all(isinstance(s, FieldInference) for s in scored)
        assert scored[0].confidence != inferences[0].confidence

    def test_calculate_aggregate_confidence(self):
        """Test aggregate confidence calculation."""
        scorer = ConfidenceScorer()
        inferences = [
            FieldInference(
                field_name="lot_sqft",
                inferred_value=9500,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                source="assessor_api",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
        ]

        aggregate = scorer.calculate_aggregate_confidence(inferences)
        # Should be weighted average
        assert 0 < aggregate < 1

    def test_calculate_aggregate_confidence_empty(self):
        """Test aggregate confidence returns 0 for empty list."""
        scorer = ConfidenceScorer()
        assert scorer.calculate_aggregate_confidence([]) == 0.0

    def test_meets_threshold(self):
        """Test meets_threshold check."""
        scorer = ConfidenceScorer()
        high_conf = FieldInference(
            field_name="lot_sqft",
            inferred_value=9500,
            confidence=1.0,
            confidence_level=ConfidenceLevel.HIGH,
            source="assessor_api",
        )
        low_conf = FieldInference(
            field_name="sewer_type",
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="ai_pending",
        )

        assert scorer.meets_threshold(high_conf, min_confidence=0.5) is True
        assert scorer.meets_threshold(low_conf, min_confidence=0.5) is False

    def test_get_high_confidence_inferences(self):
        """Test filtering for high confidence inferences."""
        scorer = ConfidenceScorer()
        inferences = [
            FieldInference(
                field_name="lot_sqft",
                inferred_value=9500,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                source="assessor_api",
            ),
            FieldInference(
                field_name="sewer_type",
                inferred_value=None,
                confidence=0.0,
                confidence_level=ConfidenceLevel.LOW,
                source="ai_pending",
            ),
            FieldInference(
                field_name="beds",
                inferred_value=4,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                source="web_scrape",
            ),
        ]

        high_conf = scorer.get_high_confidence_inferences(inferences, threshold=0.8)

        assert len(high_conf) == 1  # Only lot_sqft passes 0.8 threshold
        assert high_conf[0].field_name == "lot_sqft"

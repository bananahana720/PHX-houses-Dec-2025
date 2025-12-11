"""Unit tests for kill-switch consequence mapping and failure explanation module.

Tests the ConsequenceMapper, FailureExplanation, MultiFailureSummary classes
and HTML warning card generation functions (E3.S4).
"""

import json
from datetime import datetime, timezone

import pytest

from src.phx_home_analysis.services.kill_switch.consequences import (
    CONSEQUENCE_TEMPLATES,
    DISPLAY_NAMES,
    REQUIREMENT_DESCRIPTIONS,
    ConsequenceMapper,
    FailureExplanation,
    MultiFailureSummary,
    explain_with_consequences,
    generate_multi_failure_summary,
    generate_warning_card_html,
    generate_warning_cards_html,
)
from src.phx_home_analysis.services.kill_switch.explanation import CriterionResult

# =============================================================================
# ConsequenceMapper Tests (AC1)
# =============================================================================


class TestConsequenceTemplates:
    """Test that all 9 consequence templates are defined."""

    def test_all_nine_templates_defined(self):
        """Verify all 9 criteria have consequence templates."""
        expected_criteria = {
            "no_hoa",
            "city_sewer",
            "min_bedrooms",
            "min_bathrooms",
            "min_sqft",
            "min_garage",
            "lot_size",
            "no_new_build",
            "no_solar_lease",
        }
        assert set(CONSEQUENCE_TEMPLATES.keys()) == expected_criteria

    def test_all_nine_display_names_defined(self):
        """Verify all 9 criteria have display names."""
        assert len(DISPLAY_NAMES) == 9
        assert "no_hoa" in DISPLAY_NAMES
        assert DISPLAY_NAMES["no_hoa"] == "HOA Restriction"

    def test_all_nine_requirements_defined(self):
        """Verify all 9 criteria have requirement descriptions."""
        assert len(REQUIREMENT_DESCRIPTIONS) == 9
        assert "min_bedrooms" in REQUIREMENT_DESCRIPTIONS
        assert REQUIREMENT_DESCRIPTIONS["min_bedrooms"] == "Minimum 4 bedrooms"


class TestConsequenceMapper:
    """Test the ConsequenceMapper class."""

    def test_default_initialization(self):
        """Test ConsequenceMapper with default templates."""
        mapper = ConsequenceMapper()
        assert mapper._templates == CONSEQUENCE_TEMPLATES
        assert mapper._display_names == DISPLAY_NAMES
        assert mapper._requirements == REQUIREMENT_DESCRIPTIONS

    def test_custom_templates(self):
        """Test ConsequenceMapper with custom templates."""
        custom_templates = {"custom": "Custom consequence: {actual}"}
        mapper = ConsequenceMapper(templates=custom_templates)
        assert mapper._templates == custom_templates

    def test_get_consequence_no_hoa(self):
        """Test HOA consequence with annual calculation."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("no_hoa", actual=150, required=0)
        assert "$150" in result
        assert "$1800" in result  # 150 * 12 = 1800
        assert "annually" in result

    def test_get_consequence_city_sewer(self):
        """Test city sewer consequence."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("city_sewer", actual="septic", required="city")
        assert "Septic" in result
        assert "$300-500" in result
        assert "maintenance" in result

    def test_get_consequence_min_bedrooms(self):
        """Test minimum bedrooms consequence."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("min_bedrooms", actual=3, required=4)
        assert "3 bedrooms" in result
        assert "4 minimum" in result
        assert "resale value" in result

    def test_get_consequence_min_bathrooms(self):
        """Test minimum bathrooms consequence."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("min_bathrooms", actual=1.5, required=2)
        assert "1.5 bathrooms" in result
        assert "2 minimum" in result

    def test_get_consequence_min_sqft(self):
        """Test minimum sqft consequence with diff calculation."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("min_sqft", actual=1600, required=1800)
        assert "1,600 sqft" in result
        assert "200 sqft below" in result
        assert "1,800" in result

    def test_get_consequence_min_garage(self):
        """Test minimum garage consequence."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("min_garage", actual=1, required=2)
        assert "1 garage" in result
        assert "2 minimum" in result

    def test_get_consequence_lot_size(self):
        """Test lot size consequence with min/max."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("lot_size", actual=5000, required="7000-15000")
        assert "5,000 sqft" in result
        assert "7,000" in result
        assert "15,000" in result

    def test_get_consequence_no_new_build(self):
        """Test no new build consequence."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("no_new_build", actual=2024, required=2023)
        assert "2024" in result
        assert "construction quality" in result

    def test_get_consequence_no_solar_lease(self):
        """Test solar lease consequence with annual calculation."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("no_solar_lease", actual="lease", required="owned")
        assert "$150" in result
        assert "$1800" in result
        assert "obligation" in result

    def test_get_consequence_unknown_criterion(self):
        """Test fallback for unknown criterion."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("unknown_criterion", actual="foo", required="bar")
        assert "unknown_criterion failed" in result
        assert "foo" in result
        assert "bar" in result

    def test_get_display_name(self):
        """Test display name retrieval."""
        mapper = ConsequenceMapper()
        assert mapper.get_display_name("no_hoa") == "HOA Restriction"
        assert mapper.get_display_name("city_sewer") == "City Sewer Required"

    def test_get_display_name_unknown(self):
        """Test display name fallback for unknown criterion."""
        mapper = ConsequenceMapper()
        result = mapper.get_display_name("unknown_criterion")
        assert result == "Unknown Criterion"  # Title-cased with underscores replaced

    def test_get_requirement_description(self):
        """Test requirement description retrieval."""
        mapper = ConsequenceMapper()
        assert mapper.get_requirement_description("min_sqft") == "Minimum 1,800 sqft"
        assert mapper.get_requirement_description("lot_size") == "Between 7,000 and 15,000 sqft"

    def test_format_actual_value_hoa(self):
        """Test HOA value formatting."""
        mapper = ConsequenceMapper()
        assert mapper.format_actual_value("no_hoa", 150) == "$150/month"

    def test_format_actual_value_sqft(self):
        """Test sqft value formatting with comma."""
        mapper = ConsequenceMapper()
        assert mapper.format_actual_value("min_sqft", 1600) == "1,600 sqft"

    def test_format_actual_value_year(self):
        """Test year built value formatting."""
        mapper = ConsequenceMapper()
        assert mapper.format_actual_value("no_new_build", 2024) == "Year 2024"

    def test_format_actual_value_none(self):
        """Test None value handling."""
        mapper = ConsequenceMapper()
        assert mapper.format_actual_value("min_sqft", None) == "Unknown"

    def test_create_failure_explanation(self):
        """Test creating a complete FailureExplanation."""
        mapper = ConsequenceMapper()
        failure = mapper.create_failure_explanation(
            criterion_name="no_hoa",
            actual=150,
            required=0,
            is_hard=True,
            severity=0.0,
        )
        assert failure.criterion_name == "no_hoa"
        assert failure.display_name == "HOA Restriction"
        assert failure.requirement == "Must be $0/month"
        assert failure.actual_value == "$150/month"
        assert "$1800" in failure.consequence
        assert failure.is_hard is True
        assert failure.weight == 0.0


# =============================================================================
# FailureExplanation Tests (AC2)
# =============================================================================


class TestFailureExplanation:
    """Test the FailureExplanation dataclass."""

    def test_create_hard_failure(self):
        """Test creating a hard failure explanation."""
        failure = FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA Restriction",
            requirement="Must be $0/month",
            actual_value="$150/month",
            consequence="HOA fee adds $1800 annually",
            is_hard=True,
            severity=0.0,
        )
        assert failure.criterion_name == "no_hoa"
        assert failure.is_hard is True
        assert failure.severity == 0.0
        assert failure.weight == 0.0  # Alias

    def test_create_soft_failure(self):
        """Test creating a soft failure explanation."""
        failure = FailureExplanation(
            criterion_name="city_sewer",
            display_name="City Sewer Required",
            requirement="Must have city sewer",
            actual_value="septic",
            consequence="Septic requires maintenance",
            is_hard=False,
            severity=2.5,
        )
        assert failure.criterion_name == "city_sewer"
        assert failure.is_hard is False
        assert failure.severity == 2.5
        assert failure.weight == 2.5  # Alias

    def test_to_dict_hard_failure(self):
        """Test to_dict for hard failure."""
        failure = FailureExplanation(
            criterion_name="min_bedrooms",
            display_name="Minimum Bedrooms",
            requirement="Minimum 4 bedrooms",
            actual_value="3",
            consequence="Limits family use",
            is_hard=True,
            severity=0.0,
        )
        result = failure.to_dict()
        assert result["criterion_name"] == "min_bedrooms"
        assert result["display_name"] == "Minimum Bedrooms"
        assert result["requirement"] == "Minimum 4 bedrooms"
        assert result["actual_value"] == "3"
        assert result["consequence"] == "Limits family use"
        assert result["is_hard"] is True
        assert result["severity"] == 0.0
        assert result["type"] == "INSTANT_FAIL"

    def test_to_dict_soft_failure(self):
        """Test to_dict for soft failure."""
        failure = FailureExplanation(
            criterion_name="min_garage",
            display_name="Garage Spaces",
            requirement="Minimum 2 garage spaces",
            actual_value="1",
            consequence="Limits parking",
            is_hard=False,
            severity=1.5,
        )
        result = failure.to_dict()
        assert result["type"] == "WEIGHTED"
        assert result["severity"] == 1.5

    def test_to_dict_json_serializable(self):
        """Test that to_dict output is JSON serializable."""
        failure = FailureExplanation(
            criterion_name="lot_size",
            display_name="Lot Size Range",
            requirement="Between 7,000 and 15,000 sqft",
            actual_value="5,000 sqft",
            consequence="Outside preferred range",
            is_hard=False,
            severity=1.0,
        )
        # Should not raise
        json_str = json.dumps(failure.to_dict())
        assert isinstance(json_str, str)

    def test_str_hard_failure(self):
        """Test string representation for hard failure."""
        failure = FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA Restriction",
            requirement="Must be $0/month",
            actual_value="$150/month",
            consequence="Adds $1800 annually",
            is_hard=True,
            severity=0.0,
        )
        result = str(failure)
        assert "[INSTANT_FAIL]" in result
        assert "HOA Restriction" in result
        assert "$150/month" in result
        assert "Impact:" in result

    def test_str_soft_failure(self):
        """Test string representation for soft failure."""
        failure = FailureExplanation(
            criterion_name="city_sewer",
            display_name="City Sewer Required",
            requirement="Must have city sewer",
            actual_value="septic",
            consequence="Requires maintenance",
            is_hard=False,
            severity=2.5,
        )
        result = str(failure)
        assert "[WEIGHTED (severity 2.5)]" in result
        assert "City Sewer Required" in result

    def test_from_criterion_result_factory(self):
        """Test factory method for creating from criterion result."""
        failure = FailureExplanation.from_criterion_result(
            criterion_name="min_sqft",
            actual=1600,
            required=1800,
            is_hard=True,
            severity=0.0,
        )
        assert failure.criterion_name == "min_sqft"
        assert failure.display_name == "Minimum Square Footage"
        assert failure.actual_value == "1,600 sqft"
        assert "200 sqft below" in failure.consequence


# =============================================================================
# MultiFailureSummary Tests (AC3)
# =============================================================================


class TestMultiFailureSummary:
    """Test the MultiFailureSummary dataclass."""

    @pytest.fixture
    def hard_failure(self):
        """Create a hard failure for testing."""
        return FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA Restriction",
            requirement="Must be $0/month",
            actual_value="$150/month",
            consequence="Adds $1800 annually",
            is_hard=True,
            severity=0.0,
        )

    @pytest.fixture
    def soft_failure_high(self):
        """Create a high-weight soft failure."""
        return FailureExplanation(
            criterion_name="city_sewer",
            display_name="City Sewer Required",
            requirement="Must have city sewer",
            actual_value="septic",
            consequence="Requires maintenance",
            is_hard=False,
            severity=2.5,
        )

    @pytest.fixture
    def soft_failure_low(self):
        """Create a low-weight soft failure."""
        return FailureExplanation(
            criterion_name="lot_size",
            display_name="Lot Size Range",
            requirement="Between 7,000 and 15,000 sqft",
            actual_value="5,000 sqft",
            consequence="Outside range",
            is_hard=False,
            severity=1.0,
        )

    def test_create_summary_with_hard_failures(self, hard_failure):
        """Test summary with only hard failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=1,
            hard_failures=[hard_failure],
            soft_failures=[],
            summary_text="Failed 1 of 9 criteria (1 instant-fail)",
        )
        assert summary.has_hard_failures is True
        assert summary.has_soft_failures is False
        assert summary.total_soft_weight == 0.0

    def test_create_summary_with_soft_failures(self, soft_failure_high, soft_failure_low):
        """Test summary with only soft failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[],
            soft_failures=[soft_failure_high, soft_failure_low],
            summary_text="Failed 2 of 9 criteria (2 weighted)",
        )
        assert summary.has_hard_failures is False
        assert summary.has_soft_failures is True
        assert summary.total_soft_weight == 3.5
        assert summary.total_soft_severity == 3.5  # Alias

    def test_create_summary_mixed_failures(self, hard_failure, soft_failure_high):
        """Test summary with both hard and soft failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[hard_failure],
            soft_failures=[soft_failure_high],
            summary_text="Failed 2 of 9 criteria (1 instant-fail, 1 weighted)",
        )
        assert summary.has_hard_failures is True
        assert summary.has_soft_failures is True
        assert summary.total_soft_weight == 2.5

    def test_timestamp_default(self):
        """Test that timestamp defaults to now."""
        before = datetime.now(timezone.utc)
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=0,
            hard_failures=[],
            soft_failures=[],
            summary_text="Passed all 9 criteria",
        )
        after = datetime.now(timezone.utc)
        assert before <= summary.timestamp <= after

    def test_to_dict(self, hard_failure, soft_failure_high):
        """Test to_dict serialization."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[hard_failure],
            soft_failures=[soft_failure_high],
            summary_text="Failed 2 of 9 criteria",
        )
        result = summary.to_dict()
        assert result["total_criteria"] == 9
        assert result["failed_count"] == 2
        assert len(result["hard_failures"]) == 1
        assert len(result["soft_failures"]) == 1
        assert result["has_hard_failures"] is True
        assert result["has_soft_failures"] is True
        assert result["total_soft_weight"] == 2.5
        assert "timestamp" in result

    def test_to_dict_json_serializable(self, hard_failure):
        """Test that to_dict is JSON serializable."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=1,
            hard_failures=[hard_failure],
            soft_failures=[],
            summary_text="Failed 1 of 9",
        )
        json_str = json.dumps(summary.to_dict())
        assert isinstance(json_str, str)

    def test_to_text_hard_failures(self, hard_failure):
        """Test markdown text output with hard failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=1,
            hard_failures=[hard_failure],
            soft_failures=[],
            summary_text="Failed 1 of 9 criteria (1 instant-fail)",
        )
        text = summary.to_text()
        assert "## Kill-Switch Failure Summary" in text
        assert "**Failed 1 of 9 criteria (1 instant-fail)**" in text
        assert "### Instant-Fail Failures (Disqualification)" in text
        assert "**HOA Restriction**" in text
        assert "Impact:" in text

    def test_to_text_soft_failures(self, soft_failure_high, soft_failure_low):
        """Test markdown text output with soft failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[],
            soft_failures=[soft_failure_high, soft_failure_low],
            summary_text="Failed 2 of 9 criteria (2 weighted)",
        )
        text = summary.to_text()
        assert "### Weighted Failures (Total Severity: 3.5)" in text
        assert "[severity 2.5]" in text
        assert "[severity 1.0]" in text

    def test_to_text_empty(self):
        """Test text output with no failures."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=0,
            hard_failures=[],
            soft_failures=[],
            summary_text="Passed all 9 criteria",
        )
        text = summary.to_text()
        assert "**Passed all 9 criteria**" in text
        assert "### Instant-Fail" not in text
        assert "### Weighted" not in text

    def test_to_html(self, hard_failure):
        """Test HTML output generation."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=1,
            hard_failures=[hard_failure],
            soft_failures=[],
            summary_text="Failed 1 of 9 criteria",
        )
        html = summary.to_html()
        assert "kill-switch-warning-card" in html
        assert "kill-switch-hard" in html
        assert "HOA Restriction" in html


class TestGenerateMultiFailureSummary:
    """Test the generate_multi_failure_summary factory function."""

    def test_empty_failures(self):
        """Test with no failures."""
        summary = generate_multi_failure_summary([])
        assert summary.failed_count == 0
        assert summary.summary_text == "Passed all 9 criteria"
        assert summary.has_hard_failures is False
        assert summary.has_soft_failures is False

    def test_sorts_hard_by_name(self):
        """Test that hard failures are sorted alphabetically."""
        failures = [
            FailureExplanation(
                criterion_name="no_hoa",
                display_name="HOA",
                requirement="$0",
                actual_value="$100",
                consequence="Test",
                is_hard=True,
                severity=0.0,
            ),
            FailureExplanation(
                criterion_name="min_bedrooms",
                display_name="Bedrooms",
                requirement="4",
                actual_value="3",
                consequence="Test",
                is_hard=True,
                severity=0.0,
            ),
        ]
        summary = generate_multi_failure_summary(failures)
        assert summary.hard_failures[0].criterion_name == "min_bedrooms"
        assert summary.hard_failures[1].criterion_name == "no_hoa"

    def test_sorts_soft_by_weight_descending(self):
        """Test that soft failures are sorted by weight (highest first)."""
        failures = [
            FailureExplanation(
                criterion_name="lot_size",
                display_name="Lot",
                requirement="7k-15k",
                actual_value="5k",
                consequence="Test",
                is_hard=False,
                severity=1.0,
            ),
            FailureExplanation(
                criterion_name="city_sewer",
                display_name="Sewer",
                requirement="city",
                actual_value="septic",
                consequence="Test",
                is_hard=False,
                severity=2.5,
            ),
        ]
        summary = generate_multi_failure_summary(failures)
        assert summary.soft_failures[0].weight == 2.5
        assert summary.soft_failures[1].weight == 1.0

    def test_summary_text_hard_only(self):
        """Test summary text with only hard failures."""
        failure = FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA",
            requirement="$0",
            actual_value="$100",
            consequence="Test",
            is_hard=True,
            severity=0.0,
        )
        summary = generate_multi_failure_summary([failure])
        assert "1 instant-fail" in summary.summary_text
        assert "weighted" not in summary.summary_text

    def test_summary_text_soft_only(self):
        """Test summary text with only soft failures."""
        failure = FailureExplanation(
            criterion_name="city_sewer",
            display_name="Sewer",
            requirement="city",
            actual_value="septic",
            consequence="Test",
            is_hard=False,
            severity=2.5,
        )
        summary = generate_multi_failure_summary([failure])
        assert "1 weighted" in summary.summary_text
        assert "instant-fail" not in summary.summary_text

    def test_summary_text_mixed(self):
        """Test summary text with both hard and soft failures."""
        failures = [
            FailureExplanation(
                criterion_name="no_hoa",
                display_name="HOA",
                requirement="$0",
                actual_value="$100",
                consequence="Test",
                is_hard=True,
                severity=0.0,
            ),
            FailureExplanation(
                criterion_name="city_sewer",
                display_name="Sewer",
                requirement="city",
                actual_value="septic",
                consequence="Test",
                is_hard=False,
                severity=2.5,
            ),
        ]
        summary = generate_multi_failure_summary(failures)
        assert "1 instant-fail, 1 weighted" in summary.summary_text

    def test_custom_total_criteria(self):
        """Test with custom total criteria count."""
        summary = generate_multi_failure_summary([], total_criteria=5)
        assert summary.total_criteria == 5
        assert summary.summary_text == "Passed all 5 criteria"


# =============================================================================
# HTML Warning Card Tests (AC4)
# =============================================================================


class TestGenerateWarningCardHtml:
    """Test the generate_warning_card_html function."""

    @pytest.fixture
    def hard_failure(self):
        """Create a hard failure for testing."""
        return FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA Restriction",
            requirement="Must be $0/month",
            actual_value="$150/month",
            consequence="Adds $1800 annually to housing costs",
            is_hard=True,
            severity=0.0,
        )

    @pytest.fixture
    def soft_failure(self):
        """Create a soft failure for testing."""
        return FailureExplanation(
            criterion_name="city_sewer",
            display_name="City Sewer Required",
            requirement="Must have city sewer",
            actual_value="septic",
            consequence="Requires $300-500/year maintenance",
            is_hard=False,
            severity=2.5,
        )

    def test_hard_failure_red_border(self, hard_failure):
        """Test that hard failures have red border color."""
        html = generate_warning_card_html(hard_failure)
        assert "#dc3545" in html  # Red color
        assert "kill-switch-hard" in html

    def test_soft_failure_orange_border(self, soft_failure):
        """Test that soft failures have orange border color."""
        html = generate_warning_card_html(soft_failure)
        assert "#fd7e14" in html  # Orange color
        assert "kill-switch-soft" in html

    def test_hard_failure_badge_text(self, hard_failure):
        """Test that hard failures show INSTANT FAIL badge."""
        html = generate_warning_card_html(hard_failure)
        assert "INSTANT FAIL" in html

    def test_soft_failure_badge_text(self, soft_failure):
        """Test that soft failures show WEIGHTED badge with weight."""
        html = generate_warning_card_html(soft_failure)
        assert "WEIGHTED (2.5)" in html

    def test_displays_all_fields(self, hard_failure):
        """Test that all failure fields are displayed."""
        html = generate_warning_card_html(hard_failure)
        assert "HOA Restriction" in html  # display_name
        assert "Must be $0/month" in html  # requirement
        assert "$150/month" in html  # actual_value
        assert "Adds $1800 annually" in html  # consequence

    def test_aria_attributes_included(self, hard_failure):
        """Test ARIA attributes for accessibility."""
        html = generate_warning_card_html(hard_failure, include_aria=True)
        assert 'role="alert"' in html
        assert "aria-labelledby" in html
        assert 'aria-hidden="true"' in html  # Icon hidden from screen readers

    def test_aria_attributes_excluded(self, hard_failure):
        """Test ARIA attributes can be excluded."""
        html = generate_warning_card_html(hard_failure, include_aria=False)
        assert 'role="alert"' not in html

    def test_css_classes_present(self, hard_failure):
        """Test that CSS classes are present for external styling."""
        html = generate_warning_card_html(hard_failure)
        assert "kill-switch-warning-card" in html
        assert "ks-header" in html
        assert "ks-icon" in html
        assert "ks-title" in html
        assert "ks-badge" in html
        assert "ks-body" in html
        assert "ks-requirement" in html
        assert "ks-actual" in html
        assert "ks-consequence" in html

    def test_hard_failure_icon(self, hard_failure):
        """Test that hard failures show X icon."""
        html = generate_warning_card_html(hard_failure)
        assert ">X<" in html

    def test_soft_failure_icon(self, soft_failure):
        """Test that soft failures show ! icon."""
        html = generate_warning_card_html(soft_failure)
        assert ">!<" in html


class TestGenerateWarningCardsHtml:
    """Test the generate_warning_cards_html batch function."""

    @pytest.fixture
    def failures(self):
        """Create a list of failures for testing."""
        return [
            FailureExplanation(
                criterion_name="no_hoa",
                display_name="HOA Restriction",
                requirement="$0",
                actual_value="$150",
                consequence="Cost impact",
                is_hard=True,
                severity=0.0,
            ),
            FailureExplanation(
                criterion_name="city_sewer",
                display_name="City Sewer",
                requirement="city",
                actual_value="septic",
                consequence="Maintenance",
                is_hard=False,
                severity=2.5,
            ),
        ]

    def test_generates_multiple_cards(self, failures):
        """Test that multiple cards are generated."""
        html = generate_warning_cards_html(failures)
        assert html.count("kill-switch-warning-card") == 2

    def test_includes_summary_header(self, failures):
        """Test that summary header is included by default."""
        html = generate_warning_cards_html(failures)
        assert "kill-switch-summary" in html
        assert "Kill-Switch Evaluation" in html

    def test_excludes_summary_header(self, failures):
        """Test that summary header can be excluded."""
        html = generate_warning_cards_html(failures, include_summary_header=False)
        assert "kill-switch-summary" not in html

    def test_header_counts_failures(self, failures):
        """Test that header shows failure counts."""
        html = generate_warning_cards_html(failures)
        assert "1 instant-fail" in html
        assert "1 weighted" in html

    def test_uses_summary_text(self, failures):
        """Test that custom summary text is used when provided."""
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[failures[0]],
            soft_failures=[failures[1]],
            summary_text="Custom summary text",
        )
        html = generate_warning_cards_html(failures, summary=summary)
        assert "Custom summary text" in html

    def test_empty_failures(self):
        """Test with empty failure list."""
        html = generate_warning_cards_html([])
        assert "No Kill-Switch Failures" in html


# =============================================================================
# Integration Tests (AC5)
# =============================================================================


class TestExplainWithConsequences:
    """Test the explain_with_consequences integration function."""

    def test_with_criterion_results(self):
        """Test converting CriterionResult objects to summary."""
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has $150/month HOA",
            ),
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Property has septic system",
            ),
            CriterionResult(
                name="min_bedrooms",
                passed=True,  # Should be skipped
                is_hard=True,
                severity=0.0,
                message="",
            ),
        ]

        summary = explain_with_consequences(criterion_results)

        assert summary.failed_count == 2
        assert len(summary.hard_failures) == 1
        assert len(summary.soft_failures) == 1
        assert summary.hard_failures[0].criterion_name == "no_hoa"
        assert summary.soft_failures[0].criterion_name == "city_sewer"

    def test_with_property_data(self):
        """Test that property data is used for actual values."""
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Has HOA",
            ),
        ]
        property_data = {"hoa_fee": 200}

        summary = explain_with_consequences(criterion_results, property_data)

        assert summary.hard_failures[0].actual_value == "$200/month"

    def test_skips_passed_criteria(self):
        """Test that passed criteria are not included."""
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=True,
                is_hard=True,
                severity=0.0,
                message="",
            ),
            CriterionResult(
                name="min_bedrooms",
                passed=True,
                is_hard=True,
                severity=0.0,
                message="",
            ),
        ]

        summary = explain_with_consequences(criterion_results)

        assert summary.failed_count == 0
        assert summary.summary_text == "Passed all 9 criteria"

    def test_output_methods(self):
        """Test that summary output methods work correctly."""
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic system",
            ),
        ]

        summary = explain_with_consequences(criterion_results)

        # Test to_text()
        text = summary.to_text()
        assert "Weighted Failures" in text

        # Test to_html()
        html = summary.to_html()
        assert "kill-switch-warning-card" in html

        # Test to_dict()
        data = summary.to_dict()
        assert data["failed_count"] == 1

    def test_custom_mapper(self):
        """Test with custom ConsequenceMapper."""
        custom_templates = {"no_hoa": "Custom HOA message: ${actual}"}
        mapper = ConsequenceMapper(templates=custom_templates)

        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Has HOA",
            ),
        ]
        property_data = {"hoa_fee": 100}

        summary = explain_with_consequences(criterion_results, property_data, mapper=mapper)

        assert "Custom HOA message" in summary.hard_failures[0].consequence


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================


class TestConsequenceEdgeCases:
    """Test edge cases for consequence generation."""

    def test_none_actual_value(self):
        """Test handling of None actual value."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("no_hoa", actual=None, required=0)
        # Should handle gracefully
        assert "HOA" in result or "unknown" in result.lower()

    def test_invalid_type_actual_value(self):
        """Test handling of invalid type for actual value."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("min_sqft", actual="not a number", required=1800)
        # Should fallback gracefully
        assert "failed" in result.lower() or "unknown" in result.lower()

    def test_very_large_hoa_value(self):
        """Test with very large HOA value."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence("no_hoa", actual=10000, required=0)
        assert "$10000" in result
        assert "$120000" in result  # Annual

    def test_lot_size_custom_range(self):
        """Test lot size with custom min/max."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence(
            "lot_size", actual=5000, required="custom", min=6000, max=12000
        )
        assert "6,000" in result
        assert "12,000" in result

    def test_solar_lease_custom_monthly(self):
        """Test solar lease with custom monthly amount."""
        mapper = ConsequenceMapper()
        result = mapper.get_consequence(
            "no_solar_lease", actual="lease", required="owned", monthly=200
        )
        assert "$200" in result
        assert "$2400" in result  # 200 * 12


class TestHtmlAccessibility:
    """Test accessibility features of HTML output."""

    def test_role_alert_on_cards(self):
        """Test that cards have role=alert."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        assert 'role="alert"' in html

    def test_aria_labelledby(self):
        """Test aria-labelledby references title."""
        failure = FailureExplanation(
            criterion_name="test_criterion",
            display_name="Test",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        assert 'aria-labelledby="ks-title-test_criterion"' in html
        assert 'id="ks-title-test_criterion"' in html

    def test_icon_hidden_from_screen_readers(self):
        """Test that decorative icon is hidden from screen readers."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        assert 'aria-hidden="true"' in html

    def test_color_not_sole_indicator(self):
        """Test that text indicators accompany color coding."""
        hard_failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        soft_failure = FailureExplanation(
            criterion_name="test2",
            display_name="Test 2",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=False,
            severity=2.5,
        )

        hard_html = generate_warning_card_html(hard_failure)
        soft_html = generate_warning_card_html(soft_failure)

        # Hard failures have text "INSTANT FAIL" and icon "X"
        assert "INSTANT FAIL" in hard_html
        assert ">X<" in hard_html

        # Soft failures have text "WEIGHTED" and icon "!"
        assert "WEIGHTED" in soft_html
        assert ">!<" in soft_html


# =============================================================================
# XSS Security Tests
# =============================================================================


class TestXssPrevention:
    """Test XSS prevention in HTML output."""

    def test_html_escapes_malicious_display_name(self):
        """Test that malicious script in display_name is escaped."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="<script>alert('xss')</script>",
            requirement="Required",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        # Script tags should be escaped
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_escapes_malicious_requirement(self):
        """Test that malicious script in requirement is escaped."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="<img src=x onerror=alert('xss')>",
            actual_value="Actual",
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        # XSS attack in img tag should be escaped - < and > escaped
        assert "<img" not in html
        assert "&lt;img" in html
        # The entire tag is rendered inert
        assert "&gt;" in html

    def test_html_escapes_malicious_actual_value(self):
        """Test that malicious script in actual_value is escaped."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="Required",
            actual_value='"><script>alert(document.cookie)</script>',
            consequence="Impact",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        # Script injection should be escaped
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_escapes_malicious_consequence(self):
        """Test that malicious script in consequence is escaped."""
        failure = FailureExplanation(
            criterion_name="test",
            display_name="Test",
            requirement="Required",
            actual_value="Actual",
            consequence="<iframe src='javascript:alert(1)'></iframe>",
            is_hard=True,
            severity=0.0,
        )
        html = generate_warning_card_html(failure)
        # iframe injection should be escaped
        assert "<iframe" not in html
        assert "&lt;iframe" in html

    def test_html_escapes_all_user_fields(self):
        """Test comprehensive XSS protection across all user data fields."""
        xss_payload = "<script>alert('xss')</script>"
        failure = FailureExplanation(
            criterion_name="test",
            display_name=xss_payload,
            requirement=xss_payload,
            actual_value=xss_payload,
            consequence=xss_payload,
            is_hard=False,
            severity=2.5,
        )
        html = generate_warning_card_html(failure)
        # Count occurrences of escaped script tags (should be 4 - one per field)
        assert html.count("&lt;script&gt;") == 4
        # No unescaped script tags
        assert "<script>" not in html

"""Unit tests for kill-switch verdict explanation module.

Tests the VerdictExplainer and related classes that generate human-readable
explanations for kill-switch verdicts, including severity calculations,
categorization of HARD vs SOFT criteria, and text formatting.
"""

from src.phx_home_analysis.services.kill_switch.base import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.explanation import (
    CriterionResult,
    VerdictExplainer,
    VerdictExplanation,
)

# ============================================================================
# CriterionResult Tests
# ============================================================================


class TestCriterionResult:
    """Test the CriterionResult dataclass."""

    def test_create_hard_pass(self):
        """Test creating a passing HARD criterion."""
        cr = CriterionResult(
            name="no_hoa",
            passed=True,
            is_hard=True,
            severity=0.0,
            message="",
        )
        assert cr.name == "no_hoa"
        assert cr.passed is True
        assert cr.is_hard is True
        assert cr.severity == 0.0
        assert cr.message == ""

    def test_create_hard_fail(self):
        """Test creating a failing HARD criterion."""
        cr = CriterionResult(
            name="min_bedrooms",
            passed=False,
            is_hard=True,
            severity=0.0,  # HARD failures don't contribute severity
            message="Property has 3 bedrooms, minimum is 4",
        )
        assert cr.passed is False
        assert cr.is_hard is True
        assert cr.severity == 0.0
        assert "3 bedrooms" in cr.message

    def test_create_soft_fail(self):
        """Test creating a failing SOFT criterion."""
        cr = CriterionResult(
            name="city_sewer",
            passed=False,
            is_hard=False,
            severity=2.5,
            message="Property has septic system, city sewer required",
        )
        assert cr.passed is False
        assert cr.is_hard is False
        assert cr.severity == 2.5
        assert "septic" in cr.message.lower()

    def test_create_soft_pass(self):
        """Test creating a passing SOFT criterion."""
        cr = CriterionResult(
            name="lot_size",
            passed=True,
            is_hard=False,
            severity=0.0,  # No severity if passed
            message="",
        )
        assert cr.passed is True
        assert cr.is_hard is False
        assert cr.severity == 0.0


# ============================================================================
# VerdictExplanation Tests
# ============================================================================


class TestVerdictExplanation:
    """Test the VerdictExplanation dataclass and methods."""

    def test_create_pass_explanation_no_failures(self):
        """Test explanation for property passing all criteria."""
        explanation = VerdictExplanation(
            verdict="PASS",
            summary="Property PASSED all kill-switch criteria",
            hard_failures=[],
            soft_failures=[],
            soft_warnings=[],
            total_severity=0.0,
            severity_threshold=3.0,
        )
        assert explanation.verdict == "PASS"
        assert len(explanation.hard_failures) == 0
        assert len(explanation.soft_failures) == 0
        assert len(explanation.soft_warnings) == 0
        assert explanation.total_severity == 0.0

    def test_create_fail_explanation_with_hard_failure(self):
        """Test explanation for property failing HARD criterion."""
        hard_failure = CriterionResult(
            name="no_hoa",
            passed=False,
            is_hard=True,
            severity=0.0,
            message="Property has $200/month HOA fee",
        )
        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED due to 1 hard criterion violation(s): no_hoa",
            hard_failures=[hard_failure],
            soft_failures=[],
            soft_warnings=[],
            total_severity=0.0,
            severity_threshold=3.0,
        )
        assert explanation.verdict == "FAIL"
        assert len(explanation.hard_failures) == 1
        assert explanation.hard_failures[0].name == "no_hoa"

    def test_create_fail_explanation_with_soft_failures(self):
        """Test explanation for property failing SOFT criteria."""
        soft_failure1 = CriterionResult(
            name="city_sewer",
            passed=False,
            is_hard=False,
            severity=2.5,
            message="Property has septic system",
        )
        soft_failure2 = CriterionResult(
            name="no_new_build",
            passed=False,
            is_hard=False,
            severity=2.0,
            message="Property built in 2024",
        )
        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED - soft severity 4.5 exceeds threshold 3.0",
            hard_failures=[],
            soft_failures=[soft_failure1, soft_failure2],
            soft_warnings=[],
            total_severity=4.5,
            severity_threshold=3.0,
        )
        assert explanation.verdict == "FAIL"
        assert len(explanation.soft_failures) == 2
        assert explanation.total_severity == 4.5

    def test_create_warning_explanation(self):
        """Test explanation for property with WARNING verdict."""
        soft_warning = CriterionResult(
            name="lot_size",
            passed=False,
            is_hard=False,
            severity=1.0,
            message="Lot size is 6999 sqft, ideal range is 7000-15000",
        )
        explanation = VerdictExplanation(
            verdict="WARNING",
            summary="Property WARNING - soft severity 1.0 approaching threshold 3.0",
            hard_failures=[],
            soft_failures=[],
            soft_warnings=[soft_warning],
            total_severity=1.0,
            severity_threshold=3.0,
        )
        assert explanation.verdict == "WARNING"
        assert len(explanation.soft_warnings) == 1
        assert explanation.total_severity == 1.0

    def test_to_text_with_all_failure_types(self):
        """Test text output with HARD failures, SOFT failures, and warnings."""
        hard_failure = CriterionResult(
            name="min_bedrooms",
            passed=False,
            is_hard=True,
            severity=0.0,
            message="Property has 3 bedrooms, minimum is 4",
        )
        soft_failure = CriterionResult(
            name="city_sewer",
            passed=False,
            is_hard=False,
            severity=2.5,
            message="Property has septic system",
        )
        soft_warning = CriterionResult(
            name="lot_size",
            passed=False,
            is_hard=False,
            severity=0.5,
            message="Lot size is 6999 sqft",
        )

        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED due to hard and soft criteria violations",
            hard_failures=[hard_failure],
            soft_failures=[soft_failure],
            soft_warnings=[soft_warning],
            total_severity=2.5,
            severity_threshold=3.0,
        )

        text = explanation.to_text()
        assert "## Kill-Switch Verdict: FAIL" in text
        assert "### Hard Failures (Instant Fail)" in text
        assert "**min_bedrooms**" in text
        assert "### Soft Failures" in text
        assert "**city_sewer**" in text
        assert "### Warnings (Below Threshold)" in text
        assert "**lot_size**" in text

    def test_to_text_no_failures(self):
        """Test text output for property with no failures."""
        explanation = VerdictExplanation(
            verdict="PASS",
            summary="Property PASSED all kill-switch criteria",
            hard_failures=[],
            soft_failures=[],
            soft_warnings=[],
            total_severity=0.0,
            severity_threshold=3.0,
        )

        text = explanation.to_text()
        assert "## Kill-Switch Verdict: PASS" in text
        assert "Property PASSED all kill-switch criteria" in text
        assert "### Hard Failures" not in text
        assert "### Soft Failures" not in text
        assert "### Warnings" not in text

    def test_to_text_only_hard_failures(self):
        """Test text output with only HARD failures."""
        cr1 = CriterionResult(
            name="no_hoa",
            passed=False,
            is_hard=True,
            severity=0.0,
            message="Property has $200/month HOA",
        )
        cr2 = CriterionResult(
            name="min_bedrooms",
            passed=False,
            is_hard=True,
            severity=0.0,
            message="Property has 3 bedrooms",
        )

        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED due to 2 hard criterion violations",
            hard_failures=[cr1, cr2],
            soft_failures=[],
            soft_warnings=[],
            total_severity=0.0,
            severity_threshold=3.0,
        )

        text = explanation.to_text()
        assert "### Hard Failures (Instant Fail)" in text
        assert "**no_hoa**" in text
        assert "**min_bedrooms**" in text
        assert "### Soft Failures" not in text

    def test_to_dict_preserves_all_fields(self):
        """Test that to_dict preserves all explanation fields."""
        cr = CriterionResult(
            name="no_hoa",
            passed=False,
            is_hard=True,
            severity=0.0,
            message="Property has $200/month HOA",
        )

        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED due to hard criterion",
            hard_failures=[cr],
            soft_failures=[],
            soft_warnings=[],
            total_severity=0.0,
            severity_threshold=3.0,
        )

        result = explanation.to_dict()
        assert result["verdict"] == "FAIL"
        assert result["summary"] == "Property FAILED due to hard criterion"
        assert len(result["hard_failures"]) == 1
        assert result["hard_failures"][0]["name"] == "no_hoa"
        assert result["hard_failures"][0]["message"] == "Property has $200/month HOA"
        assert result["total_severity"] == 0.0
        assert result["severity_threshold"] == 3.0

    def test_to_dict_soft_failures_include_severity(self):
        """Test that to_dict includes severity for soft failures."""
        cr = CriterionResult(
            name="city_sewer",
            passed=False,
            is_hard=False,
            severity=2.5,
            message="Property has septic system",
        )

        explanation = VerdictExplanation(
            verdict="FAIL",
            summary="Property FAILED due to soft criteria",
            hard_failures=[],
            soft_failures=[cr],
            soft_warnings=[],
            total_severity=2.5,
            severity_threshold=3.0,
        )

        result = explanation.to_dict()
        assert len(result["soft_failures"]) == 1
        assert result["soft_failures"][0]["severity"] == 2.5

    def test_to_dict_warnings_section(self):
        """Test that to_dict includes soft_warnings section."""
        cr = CriterionResult(
            name="lot_size",
            passed=False,
            is_hard=False,
            severity=1.0,
            message="Lot size is 6999 sqft",
        )

        explanation = VerdictExplanation(
            verdict="WARNING",
            summary="Property WARNING - soft severity 1.0 approaching threshold",
            hard_failures=[],
            soft_failures=[],
            soft_warnings=[cr],
            total_severity=1.0,
            severity_threshold=3.0,
        )

        result = explanation.to_dict()
        assert len(result["soft_warnings"]) == 1
        assert result["soft_warnings"][0]["name"] == "lot_size"


# ============================================================================
# VerdictExplainer Tests
# ============================================================================


class TestVerdictExplainer:
    """Test the VerdictExplainer class."""

    def test_explainer_initialization_default_threshold(self):
        """Test VerdictExplainer with default severity threshold."""
        explainer = VerdictExplainer()
        assert explainer.severity_threshold == 3.0

    def test_explainer_initialization_custom_threshold(self):
        """Test VerdictExplainer with custom severity threshold."""
        explainer = VerdictExplainer(severity_threshold=2.5)
        assert explainer.severity_threshold == 2.5

    def test_explain_pass_verdict_no_failures(self):
        """Test explaining PASS verdict with no failures."""
        explainer = VerdictExplainer()
        criterion_results = []

        explanation = explainer.explain(KillSwitchVerdict.PASS, criterion_results)

        assert explanation.verdict == "PASS"
        assert len(explanation.hard_failures) == 0
        assert len(explanation.soft_failures) == 0
        assert len(explanation.soft_warnings) == 0
        assert explanation.total_severity == 0.0
        assert "PASSED" in explanation.summary

    def test_explain_fail_verdict_hard_failure(self):
        """Test explaining FAIL verdict with HARD criterion failure."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has $200/month HOA",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)

        assert explanation.verdict == "FAIL"
        assert len(explanation.hard_failures) == 1
        assert explanation.hard_failures[0].name == "no_hoa"
        assert "no_hoa" in explanation.summary

    def test_explain_fail_verdict_multiple_hard_failures(self):
        """Test explaining FAIL verdict with multiple HARD failures."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has $200/month HOA",
            ),
            CriterionResult(
                name="min_bedrooms",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has 3 bedrooms",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)

        assert len(explanation.hard_failures) == 2
        assert "2 hard criterion" in explanation.summary

    def test_explain_fail_verdict_soft_failures_exceed_threshold(self):
        """Test explaining FAIL verdict when soft severity exceeds threshold."""
        explainer = VerdictExplainer(severity_threshold=3.0)
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Property has septic system",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="Property built in 2024",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)

        assert explanation.verdict == "FAIL"
        assert len(explanation.soft_failures) == 2
        assert explanation.total_severity == 4.5
        assert "4.5" in explanation.summary or "4.5" in explanation.to_text()

    def test_explain_warning_verdict_soft_severity_below_fail_threshold(self):
        """Test explaining WARNING verdict when soft severity is below FAIL threshold."""
        explainer = VerdictExplainer(severity_threshold=3.0)
        criterion_results = [
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Lot size is 6999 sqft",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.WARNING, criterion_results)

        assert explanation.verdict == "WARNING"
        assert len(explanation.soft_warnings) == 1
        assert len(explanation.soft_failures) == 0
        assert explanation.total_severity == 1.0

    def test_explain_pass_with_soft_warnings(self):
        """Test explaining PASS verdict with soft warnings."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=0.5,
                message="Lot size is 6999 sqft",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.PASS, criterion_results)

        assert explanation.verdict == "PASS"
        assert len(explanation.soft_warnings) == 1
        assert "1 minor warning" in explanation.summary or "warning" in explanation.summary.lower()

    def test_generate_summary_hard_failure(self):
        """Test _generate_summary with HARD failures."""
        explainer = VerdictExplainer()
        hard_failures = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has HOA",
            ),
        ]

        summary = explainer._generate_summary(
            KillSwitchVerdict.FAIL,
            hard_failures=hard_failures,
            total_severity=0.0,
            failure_count=0,
            warning_count=0,
        )

        assert "FAILED" in summary
        assert "hard criterion" in summary
        assert "no_hoa" in summary

    def test_generate_summary_soft_failure_exceed_threshold(self):
        """Test _generate_summary when SOFT severity exceeds threshold."""
        explainer = VerdictExplainer(severity_threshold=3.0)
        summary = explainer._generate_summary(
            KillSwitchVerdict.FAIL,
            hard_failures=[],
            total_severity=4.5,
            failure_count=2,
            warning_count=0,
        )

        assert "FAILED" in summary
        assert "4.5" in summary
        assert "3.0" in summary

    def test_generate_summary_warning_verdict(self):
        """Test _generate_summary with WARNING verdict."""
        explainer = VerdictExplainer(severity_threshold=3.0)
        summary = explainer._generate_summary(
            KillSwitchVerdict.WARNING,
            hard_failures=[],
            total_severity=1.5,
            failure_count=0,
            warning_count=1,
        )

        assert "WARNING" in summary
        assert "1.5" in summary

    def test_generate_summary_pass_no_warnings(self):
        """Test _generate_summary with PASS and no warnings."""
        explainer = VerdictExplainer()
        summary = explainer._generate_summary(
            KillSwitchVerdict.PASS,
            hard_failures=[],
            total_severity=0.0,
            failure_count=0,
            warning_count=0,
        )

        assert "PASSED" in summary
        assert "all kill-switch criteria" in summary

    def test_generate_summary_pass_with_warnings(self):
        """Test _generate_summary with PASS but some warnings."""
        explainer = VerdictExplainer()
        summary = explainer._generate_summary(
            KillSwitchVerdict.PASS,
            hard_failures=[],
            total_severity=0.8,
            failure_count=0,
            warning_count=2,
        )

        assert "PASSED" in summary
        assert "2 minor warning" in summary
        assert "0.8" in summary

    def test_explain_mixed_hard_and_soft_failures(self):
        """Test explaining verdict with both HARD and SOFT failures."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has $200/month HOA",
            ),
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Property has septic system",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)

        assert len(explanation.hard_failures) == 1
        # HARD failures take precedence in summary
        assert "hard criterion" in explanation.summary

    def test_explain_preserves_message_formatting(self):
        """Test that explanation preserves original message formatting."""
        explainer = VerdictExplainer()
        message = "Property has $200/month HOA fee with community amenities"
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message=message,
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        text = explanation.to_text()

        assert message in text

    def test_explain_empty_criterion_results(self):
        """Test explaining with empty criterion results list."""
        explainer = VerdictExplainer()
        criterion_results = []

        explanation = explainer.explain(KillSwitchVerdict.PASS, criterion_results)

        assert explanation.verdict == "PASS"
        assert len(explanation.hard_failures) == 0
        assert len(explanation.soft_failures) == 0
        assert len(explanation.soft_warnings) == 0


# ============================================================================
# Integration Tests: Explain → Text/Dict Output
# ============================================================================


class TestExplanationOutputFormats:
    """Test explanation output in various formats."""

    def test_text_output_markdown_formatting(self):
        """Test that text output uses proper markdown formatting."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Property has $200/month HOA",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        text = explanation.to_text()

        assert "##" in text  # Markdown headers
        assert "**" in text  # Bold formatting
        assert "-" in text  # List items

    def test_dict_output_json_serializable(self):
        """Test that dict output is JSON-serializable."""
        import json

        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Property has septic system",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        result_dict = explanation.to_dict()

        # Should not raise exception
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)

    def test_multiple_soft_failures_formatting(self):
        """Test formatting when multiple soft failures are present."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Property has septic system",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="Property built in 2024",
            ),
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="Property has 1 garage space",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        text = explanation.to_text()
        result_dict = explanation.to_dict()

        # Text output
        assert "### Soft Failures" in text
        assert "city_sewer" in text
        assert "no_new_build" in text
        assert "min_garage" in text

        # Dict output
        assert len(result_dict["soft_failures"]) == 3
        assert result_dict["total_severity"] == 6.0

    def test_severity_formatting_precision(self):
        """Test that severity values are formatted with proper precision."""
        explainer = VerdictExplainer(severity_threshold=3.0)
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic system",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.WARNING, criterion_results)
        text = explanation.to_text()

        # Should show severity with 1 decimal place
        assert "2.5" in text or "2.50" in text


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestExplanationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_message_text_output(self):
        """Test handling of very long failure messages."""
        long_message = "Property fails because " + "reason " * 50
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="test_criterion",
                passed=False,
                is_hard=True,
                severity=0.0,
                message=long_message,
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        text = explanation.to_text()

        assert long_message in text

    def test_special_characters_in_messages(self):
        """Test handling of special characters in criterion messages."""
        special_message = "Property has $200/mo HOA (includes: parking, gym & pool)"
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message=special_message,
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)
        text = explanation.to_text()
        result_dict = explanation.to_dict()

        assert special_message in text
        assert result_dict["hard_failures"][0]["message"] == special_message

    def test_none_values_in_criterion_handling(self):
        """Test handling when criterion fields might be None-like."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=0.0,
                message="",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.PASS, criterion_results)
        text = explanation.to_text()

        assert "test" in text
        assert explanation.total_severity == 0.0

    def test_zero_severity_multiple_failures(self):
        """Test handling multiple failures with zero severity (passed)."""
        explainer = VerdictExplainer()
        criterion_results = [
            CriterionResult(
                name="criterion1",
                passed=True,
                is_hard=False,
                severity=0.0,
                message="",
            ),
            CriterionResult(
                name="criterion2",
                passed=True,
                is_hard=False,
                severity=0.0,
                message="",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.PASS, criterion_results)

        assert len(explanation.hard_failures) == 0
        assert len(explanation.soft_failures) == 0
        assert len(explanation.soft_warnings) == 0

    def test_high_severity_threshold_configuration(self):
        """Test explainer with high severity threshold."""
        explainer = VerdictExplainer(severity_threshold=5.0)
        criterion_results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic system",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="New build",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.WARNING, criterion_results)

        # With high threshold (5.0), severity 4.5 should be warning, not fail
        assert explanation.verdict == "WARNING"
        assert explanation.total_severity == 4.5

    def test_low_severity_threshold_configuration(self):
        """Test explainer with low severity threshold."""
        explainer = VerdictExplainer(severity_threshold=1.0)
        criterion_results = [
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage space",
            ),
        ]

        explanation = explainer.explain(KillSwitchVerdict.FAIL, criterion_results)

        # With low threshold (1.0), severity 1.5 >= 1.0 should fail
        assert explanation.verdict == "FAIL"
        assert len(explanation.soft_failures) == 1

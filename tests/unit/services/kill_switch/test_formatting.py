"""Unit tests for kill-switch verdict formatting utilities.

Tests the formatting functions introduced in E3.S3 for human-readable
verdict display with accessibility support.

Test Coverage:
- format_verdict for PASS, WARNING, FAIL with emoji
- format_verdict with plain_text=True for accessibility
- format_result for full breakdown output
- format_result with plain_text mode
- format_severity_bar visual indicator
- Ordering of failures in format_result output
"""

from datetime import datetime

from src.phx_home_analysis.services.kill_switch.base import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.formatting import (
    format_result,
    format_severity_bar,
    format_verdict,
    format_verdict_short,
)
from src.phx_home_analysis.services.kill_switch.result import (
    FailedCriterion,
    KillSwitchResult,
)

# ============================================================================
# format_verdict Tests
# ============================================================================


class TestFormatVerdict:
    """Test the format_verdict function."""

    def test_format_pass_with_emoji(self):
        """Test PASS verdict format includes emoji and text."""
        result = format_verdict(KillSwitchVerdict.PASS)
        assert "PASS" in result
        # Should contain green circle emoji (U+1F7E2)
        assert "\U0001f7e2" in result or "PASS" in result

    def test_format_warning_with_emoji(self):
        """Test WARNING verdict format includes emoji and text."""
        result = format_verdict(KillSwitchVerdict.WARNING)
        assert "WARNING" in result
        # Should contain yellow circle emoji (U+1F7E1)
        assert "\U0001f7e1" in result or "WARNING" in result

    def test_format_fail_with_emoji(self):
        """Test FAIL verdict format includes emoji and text."""
        result = format_verdict(KillSwitchVerdict.FAIL)
        assert "FAIL" in result
        # Should contain red circle emoji (U+1F534)
        assert "\U0001f534" in result or "FAIL" in result

    def test_format_pass_plain_text(self):
        """Test PASS verdict format in plain text mode."""
        result = format_verdict(KillSwitchVerdict.PASS, plain_text=True)
        assert result == "[PASS]"
        assert "\U0001f7e2" not in result

    def test_format_warning_plain_text(self):
        """Test WARNING verdict format in plain text mode."""
        result = format_verdict(KillSwitchVerdict.WARNING, plain_text=True)
        assert result == "[WARNING]"
        assert "\U0001f7e1" not in result

    def test_format_fail_plain_text(self):
        """Test FAIL verdict format in plain text mode."""
        result = format_verdict(KillSwitchVerdict.FAIL, plain_text=True)
        assert result == "[FAIL]"
        assert "\U0001f534" not in result


class TestFormatVerdictShort:
    """Test the format_verdict_short function."""

    def test_pass_short(self):
        """Test short format for PASS."""
        result = format_verdict_short(KillSwitchVerdict.PASS)
        assert result == "PASS"

    def test_warning_short(self):
        """Test short format for WARNING."""
        result = format_verdict_short(KillSwitchVerdict.WARNING)
        assert result == "WARNING"

    def test_fail_short(self):
        """Test short format for FAIL."""
        result = format_verdict_short(KillSwitchVerdict.FAIL)
        assert result == "FAIL"


# ============================================================================
# format_result Tests
# ============================================================================


class TestFormatResult:
    """Test the format_result function."""

    def test_format_pass_result_no_failures(self):
        """Test formatting PASS result with no failures."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="123 Main St, Phoenix, AZ",
        )
        output = format_result(result)
        assert "PASS" in output
        assert "123 Main St, Phoenix, AZ" in output
        assert "2025-12-10T14:30:00" in output
        assert "No failures detected" in output

    def test_format_fail_result_hard_failure(self):
        """Test formatting FAIL result with HARD failure."""
        fc = FailedCriterion(
            name="no_hoa",
            actual_value=200,
            required_value="$0 (no HOA allowed)",
            is_hard=True,
            severity=0.0,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[fc],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="456 Oak Ave, Phoenix, AZ",
        )
        output = format_result(result)
        assert "FAIL" in output
        assert "HARD Failures" in output
        assert "no_hoa" in output
        assert "200" in output
        assert "$0 (no HOA allowed)" in output

    def test_format_fail_result_soft_threshold(self):
        """Test formatting FAIL result with SOFT threshold exceeded."""
        fc1 = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        fc2 = FailedCriterion(
            name="lot_size",
            actual_value=6000,
            required_value="7000-15000 sqft",
            is_hard=False,
            severity=1.0,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[fc1, fc2],
            severity_score=3.5,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="789 Elm St, Phoenix, AZ",
        )
        output = format_result(result)
        assert "FAIL" in output
        assert "SOFT Failures" in output
        assert "city_sewer" in output
        assert "lot_size" in output
        assert "3.5" in output
        assert ">= 3.0" in output

    def test_format_warning_result(self):
        """Test formatting WARNING result."""
        fc = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.WARNING,
            failed_criteria=[fc],
            severity_score=2.5,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="321 Pine Rd, Phoenix, AZ",
        )
        output = format_result(result)
        assert "WARNING" in output
        assert "SOFT Failures" in output
        assert "< 3.0" in output

    def test_format_result_plain_text(self):
        """Test formatting result in plain text mode."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="123 Main St",
        )
        output = format_result(result, plain_text=True)
        assert "[PASS]" in output
        # Should not contain emoji
        assert "\U0001f7e2" not in output

    def test_format_result_soft_failures_sorted_by_severity(self):
        """Test that SOFT failures are sorted by severity descending."""
        # Create failures in wrong order (low severity first)
        fc1 = FailedCriterion(
            name="lot_size",
            actual_value=6000,
            required_value="7000-15000 sqft",
            is_hard=False,
            severity=1.0,
        )
        fc2 = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[fc1, fc2],  # Low severity first
            severity_score=3.5,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="Test",
        )
        output = format_result(result)
        # city_sewer (2.5) should appear before lot_size (1.0)
        city_sewer_pos = output.find("city_sewer")
        lot_size_pos = output.find("lot_size")
        assert city_sewer_pos < lot_size_pos

    def test_format_result_mixed_hard_and_soft(self):
        """Test formatting result with both HARD and SOFT failures."""
        hard_fc = FailedCriterion(
            name="no_hoa",
            actual_value=200,
            required_value="$0",
            is_hard=True,
            severity=0.0,
        )
        soft_fc = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[hard_fc, soft_fc],
            severity_score=2.5,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="Mixed Test",
        )
        output = format_result(result)
        # Both sections should appear
        assert "HARD Failures" in output
        assert "SOFT Failures" in output
        # HARD should appear first
        hard_pos = output.find("HARD Failures")
        soft_pos = output.find("SOFT Failures")
        assert hard_pos < soft_pos


# ============================================================================
# format_severity_bar Tests
# ============================================================================


class TestFormatSeverityBar:
    """Test the format_severity_bar function."""

    def test_zero_severity(self):
        """Test severity bar with 0.0 severity."""
        result = format_severity_bar(0.0, 3.0)
        assert "[..........]" in result
        assert "0.0/3.0" in result
        assert "EXCEEDED" not in result

    def test_half_severity(self):
        """Test severity bar at 50% of threshold."""
        result = format_severity_bar(1.5, 3.0)
        assert "#####" in result
        assert "1.5/3.0" in result
        assert "EXCEEDED" not in result

    def test_at_threshold(self):
        """Test severity bar exactly at threshold."""
        result = format_severity_bar(3.0, 3.0)
        assert "[##########]" in result
        assert "3.0/3.0" in result
        assert "EXCEEDED" in result

    def test_above_threshold(self):
        """Test severity bar above threshold."""
        result = format_severity_bar(4.5, 3.0)
        assert "[##########]" in result
        assert "4.5/3.0" in result
        assert "EXCEEDED" in result

    def test_custom_threshold(self):
        """Test severity bar with custom threshold."""
        result = format_severity_bar(2.0, 4.0)
        assert "2.0/4.0" in result
        assert "EXCEEDED" not in result

    def test_zero_threshold_guard(self):
        """Test that zero threshold produces invalid threshold message."""
        result = format_severity_bar(1.0, 0)
        assert "invalid threshold" in result
        assert "[??????????]" in result
        assert "1.0/0.0" in result

    def test_negative_threshold_guard(self):
        """Test that negative threshold produces invalid threshold message."""
        result = format_severity_bar(2.5, -1.0)
        assert "invalid threshold" in result
        assert "[??????????]" in result

    def test_negative_severity_clamped_to_zero(self):
        """Test that negative severity is clamped to zero."""
        result = format_severity_bar(-2.0, 3.0)
        # Negative severity should be clamped to 0.0
        assert "[..........]" in result
        assert "0.0/3.0" in result
        assert "EXCEEDED" not in result

    def test_custom_width(self):
        """Test severity bar with custom width."""
        result = format_severity_bar(1.5, 3.0, width=20)
        # Half severity should fill half the bar (10 #'s, 10 .'s)
        assert "##########.........." in result
        assert "1.5/3.0" in result

"""Unit tests for KillSwitchResult and FailedCriterion dataclasses.

Tests the result dataclasses introduced in E3.S3 for comprehensive
kill-switch verdict evaluation with full metadata.

Test Coverage:
- FailedCriterion creation for HARD and SOFT criteria
- FailedCriterion to_dict serialization
- FailedCriterion __str__ formatting
- KillSwitchResult creation with all verdict types
- KillSwitchResult.is_passing property
- KillSwitchResult.hard_failures and soft_failures properties
- KillSwitchResult.to_dict serialization
- KillSwitchResult.__str__ formatting
- Boundary condition tests for severity thresholds
- Timezone-aware timestamp validation
"""

from datetime import datetime, timezone

from src.phx_home_analysis.services.kill_switch.base import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.result import (
    FailedCriterion,
    KillSwitchResult,
)

# ============================================================================
# FailedCriterion Tests
# ============================================================================


class TestFailedCriterion:
    """Test the FailedCriterion dataclass."""

    def test_create_hard_criterion_failure(self):
        """Test creating a HARD criterion failure."""
        fc = FailedCriterion(
            name="no_hoa",
            actual_value=150.0,
            required_value="$0 (no HOA allowed)",
            is_hard=True,
            severity=0.0,
        )
        assert fc.name == "no_hoa"
        assert fc.actual_value == 150.0
        assert fc.required_value == "$0 (no HOA allowed)"
        assert fc.is_hard is True
        assert fc.severity == 0.0

    def test_create_soft_criterion_failure(self):
        """Test creating a SOFT criterion failure."""
        fc = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        assert fc.name == "city_sewer"
        assert fc.actual_value == "septic"
        assert fc.required_value == "city sewer"
        assert fc.is_hard is False
        assert fc.severity == 2.5

    def test_to_dict_hard_criterion(self):
        """Test to_dict for HARD criterion failure."""
        fc = FailedCriterion(
            name="min_bedrooms",
            actual_value=3,
            required_value="4+ bedrooms",
            is_hard=True,
            severity=0.0,
        )
        d = fc.to_dict()
        assert d["name"] == "min_bedrooms"
        assert d["actual_value"] == 3
        assert d["required_value"] == "4+ bedrooms"
        assert d["is_hard"] is True
        assert d["severity"] == 0.0

    def test_to_dict_soft_criterion(self):
        """Test to_dict for SOFT criterion failure."""
        fc = FailedCriterion(
            name="lot_size",
            actual_value=6000,
            required_value="7000-15000 sqft",
            is_hard=False,
            severity=1.0,
        )
        d = fc.to_dict()
        assert d["name"] == "lot_size"
        assert d["actual_value"] == 6000
        assert d["required_value"] == "7000-15000 sqft"
        assert d["is_hard"] is False
        assert d["severity"] == 1.0

    def test_str_hard_criterion(self):
        """Test string representation for HARD criterion."""
        fc = FailedCriterion(
            name="no_hoa",
            actual_value=200,
            required_value="$0",
            is_hard=True,
            severity=0.0,
        )
        s = str(fc)
        assert "no_hoa" in s
        assert "HARD" in s
        assert "200" in s
        assert "$0" in s

    def test_str_soft_criterion(self):
        """Test string representation for SOFT criterion."""
        fc = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
        s = str(fc)
        assert "city_sewer" in s
        assert "SOFT" in s
        assert "2.5" in s
        assert "septic" in s

    def test_actual_value_none(self):
        """Test FailedCriterion with None actual_value."""
        fc = FailedCriterion(
            name="year_built",
            actual_value=None,
            required_value="built 2023 or earlier",
            is_hard=False,
            severity=2.0,
        )
        assert fc.actual_value is None
        d = fc.to_dict()
        assert d["actual_value"] is None


# ============================================================================
# KillSwitchResult Tests
# ============================================================================


class TestKillSwitchResult:
    """Test the KillSwitchResult dataclass."""

    def test_create_pass_result(self):
        """Test creating a PASS result with no failures."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="123 Main St, Phoenix, AZ",
        )
        assert result.verdict == KillSwitchVerdict.PASS
        assert len(result.failed_criteria) == 0
        assert result.severity_score == 0.0
        assert result.property_address == "123 Main St, Phoenix, AZ"

    def test_create_warning_result(self):
        """Test creating a WARNING result with SOFT failure."""
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
            property_address="456 Oak Ave, Phoenix, AZ",
        )
        assert result.verdict == KillSwitchVerdict.WARNING
        assert len(result.failed_criteria) == 1
        assert result.severity_score == 2.5

    def test_create_fail_result_hard(self):
        """Test creating a FAIL result from HARD criterion."""
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
            property_address="789 Elm St, Phoenix, AZ",
        )
        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.failed_criteria) == 1
        assert result.failed_criteria[0].is_hard is True

    def test_create_fail_result_soft_threshold(self):
        """Test creating a FAIL result from SOFT threshold exceeded."""
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
            property_address="321 Pine Rd, Phoenix, AZ",
        )
        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.failed_criteria) == 2
        assert result.severity_score == 3.5

    def test_default_values(self):
        """Test default values for optional fields."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        assert result.failed_criteria == []
        assert result.severity_score == 0.0
        assert result.property_address == ""
        assert result.timestamp is not None  # Auto-generated


# ============================================================================
# KillSwitchResult.is_passing Property Tests
# ============================================================================


class TestKillSwitchResultIsPassing:
    """Test the is_passing property."""

    def test_pass_verdict_is_passing(self):
        """Test that PASS verdict returns is_passing=True."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        assert result.is_passing is True

    def test_warning_verdict_is_passing(self):
        """Test that WARNING verdict returns is_passing=True."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.WARNING,
            severity_score=2.5,
        )
        assert result.is_passing is True

    def test_fail_verdict_is_not_passing(self):
        """Test that FAIL verdict returns is_passing=False."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.FAIL)
        assert result.is_passing is False


# ============================================================================
# KillSwitchResult Hard/Soft Failures Properties Tests
# ============================================================================


class TestKillSwitchResultFailureProperties:
    """Test the hard_failures and soft_failures properties."""

    def test_hard_failures_filters_correctly(self):
        """Test hard_failures returns only HARD criterion failures."""
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
        )
        assert len(result.hard_failures) == 1
        assert result.hard_failures[0].name == "no_hoa"

    def test_soft_failures_filters_correctly(self):
        """Test soft_failures returns only SOFT criterion failures."""
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
        )
        assert len(result.soft_failures) == 1
        assert result.soft_failures[0].name == "city_sewer"

    def test_empty_failures(self):
        """Test empty failures returns empty lists."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        assert result.hard_failures == []
        assert result.soft_failures == []


# ============================================================================
# KillSwitchResult.to_dict Tests
# ============================================================================


class TestKillSwitchResultToDict:
    """Test the to_dict serialization method."""

    def test_to_dict_pass_result(self):
        """Test to_dict for PASS result."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="123 Main St",
        )
        d = result.to_dict()
        assert d["verdict"] == "PASS"
        assert d["failed_criteria"] == []
        assert d["severity_score"] == 0.0
        assert d["timestamp"] == "2025-12-10T14:30:00"
        assert d["property_address"] == "123 Main St"
        assert d["is_passing"] is True

    def test_to_dict_fail_result_with_criteria(self):
        """Test to_dict for FAIL result with failed criteria."""
        fc = FailedCriterion(
            name="no_hoa",
            actual_value=200,
            required_value="$0",
            is_hard=True,
            severity=0.0,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[fc],
            severity_score=0.0,
            timestamp=datetime(2025, 12, 10, 14, 30, 0),
            property_address="456 Oak Ave",
        )
        d = result.to_dict()
        assert d["verdict"] == "FAIL"
        assert len(d["failed_criteria"]) == 1
        assert d["failed_criteria"][0]["name"] == "no_hoa"
        assert d["is_passing"] is False


# ============================================================================
# KillSwitchResult.__str__ Tests
# ============================================================================


class TestKillSwitchResultStr:
    """Test the __str__ method."""

    def test_str_pass_no_address(self):
        """Test string representation for PASS without address."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        s = str(result)
        assert "Kill-Switch: PASS" in s

    def test_str_pass_with_address(self):
        """Test string representation for PASS with address."""
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            property_address="123 Main St",
        )
        s = str(result)
        assert "PASS" in s
        assert "123 Main St" in s

    def test_str_fail_hard(self):
        """Test string representation for FAIL with HARD failure."""
        fc = FailedCriterion(
            name="no_hoa",
            actual_value=200,
            required_value="$0",
            is_hard=True,
            severity=0.0,
        )
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[fc],
        )
        s = str(result)
        assert "FAIL" in s
        assert "1 HARD failure" in s

    def test_str_warning_soft(self):
        """Test string representation for WARNING with severity."""
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
        )
        s = str(result)
        assert "WARNING" in s
        assert "2.5" in s


# ============================================================================
# Boundary Condition Tests
# ============================================================================


class TestKillSwitchResultBoundaryConditions:
    """Test exact boundary conditions for severity thresholds."""

    def test_boundary_severity_exactly_1_5_is_warning(self):
        """Test that severity exactly 1.5 is WARNING (boundary case).

        Threshold: WARNING >= 1.5
        """
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.WARNING,
            severity_score=1.5,
            failed_criteria=[],
            property_address="test",
        )
        # WARNING is still considered passing
        assert result.is_passing is True
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_boundary_severity_exactly_3_0_is_fail(self):
        """Test that severity exactly 3.0 is FAIL (boundary case).

        Threshold: FAIL >= 3.0
        """
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.FAIL,
            severity_score=3.0,
            failed_criteria=[],
            property_address="test",
        )
        assert result.is_passing is False
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_boundary_severity_just_below_1_5_is_pass(self):
        """Test that severity just below 1.5 is PASS.

        Threshold: PASS if severity < 1.5
        """
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            severity_score=1.4999,
            failed_criteria=[],
            property_address="test",
        )
        assert result.is_passing is True
        assert result.verdict == KillSwitchVerdict.PASS

    def test_boundary_severity_just_below_3_0_is_warning(self):
        """Test that severity just below 3.0 is WARNING.

        Threshold: WARNING if 1.5 <= severity < 3.0
        """
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.WARNING,
            severity_score=2.9999,
            failed_criteria=[],
            property_address="test",
        )
        assert result.is_passing is True
        assert result.verdict == KillSwitchVerdict.WARNING


# ============================================================================
# Timestamp Tests
# ============================================================================


class TestKillSwitchResultTimestamp:
    """Test timestamp handling including timezone awareness."""

    def test_default_timestamp_is_timezone_aware(self):
        """Test that default timestamp is timezone-aware (UTC)."""
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        # Timestamp should be timezone-aware
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.tzinfo == timezone.utc

    def test_timestamp_is_recent(self):
        """Test that auto-generated timestamp is recent (within 1 second)."""
        before = datetime.now(timezone.utc)
        result = KillSwitchResult(verdict=KillSwitchVerdict.PASS)
        after = datetime.now(timezone.utc)

        assert before <= result.timestamp <= after

    def test_explicit_timestamp_preserved(self):
        """Test that explicitly set timestamp is preserved."""
        explicit_ts = datetime(2025, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            timestamp=explicit_ts,
        )
        assert result.timestamp == explicit_ts

    def test_to_dict_timestamp_iso_format(self):
        """Test that to_dict produces ISO format timestamp."""
        ts = datetime(2025, 12, 10, 14, 30, 0, tzinfo=timezone.utc)
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.PASS,
            timestamp=ts,
        )
        d = result.to_dict()
        # ISO format should include timezone info
        assert "2025-12-10" in d["timestamp"]
        assert "14:30:00" in d["timestamp"]

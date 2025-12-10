"""Unit tests for SOFT kill-switch severity evaluation module.

Tests the SoftSeverityEvaluator, SoftSeverityResult, SoftCriterionConfig,
and CSV configuration loading. Validates severity accumulation, threshold
boundaries, and verdict determination.

Test Coverage:
- SoftSeverityResult dataclass creation and serialization
- SoftSeverityEvaluator severity calculation and verdict determination
- Threshold boundary tests (exactly 1.5, 2.9, 3.0, 3.1)
- PASS verdict tests (0.0, 0.5, 1.0, 1.4 severity)
- WARNING verdict tests (1.5, 2.0, 2.5, 2.9 severity)
- FAIL verdict tests (3.0, 3.5, 4.0, 7.0 severity)
- SoftCriterionConfig Pydantic model validation
- CSV configuration loading and validation
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.phx_home_analysis.services.kill_switch.base import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.explanation import CriterionResult
from src.phx_home_analysis.services.kill_switch.severity import (
    SoftCriterionConfig,
    SoftSeverityEvaluator,
    SoftSeverityResult,
    load_soft_criteria_config,
)

# ============================================================================
# SoftSeverityResult Tests
# ============================================================================


class TestSoftSeverityResult:
    """Test the SoftSeverityResult dataclass."""

    def test_create_pass_result(self):
        """Test creating a PASS severity result."""
        result = SoftSeverityResult(
            total_severity=0.0,
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            breakdown={},
        )
        assert result.total_severity == 0.0
        assert result.verdict == KillSwitchVerdict.PASS
        assert len(result.failed_criteria) == 0
        assert len(result.breakdown) == 0

    def test_create_warning_result(self):
        """Test creating a WARNING severity result."""
        cr = CriterionResult(
            name="min_garage",
            passed=False,
            is_hard=False,
            severity=1.5,
            message="Only 1 garage space",
        )
        result = SoftSeverityResult(
            total_severity=1.5,
            verdict=KillSwitchVerdict.WARNING,
            failed_criteria=[cr],
            breakdown={"min_garage": 1.5},
        )
        assert result.total_severity == 1.5
        assert result.verdict == KillSwitchVerdict.WARNING
        assert len(result.failed_criteria) == 1
        assert result.breakdown["min_garage"] == 1.5

    def test_create_fail_result(self):
        """Test creating a FAIL severity result."""
        cr1 = CriterionResult(
            name="city_sewer",
            passed=False,
            is_hard=False,
            severity=2.5,
            message="Septic system",
        )
        cr2 = CriterionResult(
            name="lot_size",
            passed=False,
            is_hard=False,
            severity=1.0,
            message="Lot too small",
        )
        result = SoftSeverityResult(
            total_severity=3.5,
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[cr1, cr2],
            breakdown={"city_sewer": 2.5, "lot_size": 1.0},
        )
        assert result.total_severity == 3.5
        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.failed_criteria) == 2

    def test_to_dict_serialization(self):
        """Test SoftSeverityResult to_dict method."""
        result = SoftSeverityResult(
            total_severity=2.5,
            verdict=KillSwitchVerdict.WARNING,
            failed_criteria=[
                CriterionResult(
                    name="city_sewer",
                    passed=False,
                    is_hard=False,
                    severity=2.5,
                    message="Septic",
                )
            ],
            breakdown={"city_sewer": 2.5},
        )
        d = result.to_dict()
        assert d["total_severity"] == 2.5
        assert d["verdict"] == "WARNING"
        assert d["failed_criteria_count"] == 1
        assert d["failed_criteria"] == ["city_sewer"]
        assert d["breakdown"] == {"city_sewer": 2.5}
        assert d["threshold_fail"] == 3.0
        assert d["threshold_warning"] == 1.5

    def test_str_representation_no_failures(self):
        """Test string representation with no failures."""
        result = SoftSeverityResult(
            total_severity=0.0,
            verdict=KillSwitchVerdict.PASS,
            failed_criteria=[],
            breakdown={},
        )
        s = str(result)
        assert "PASS" in s
        assert "0.0" in s

    def test_str_representation_with_failures(self):
        """Test string representation with failures."""
        result = SoftSeverityResult(
            total_severity=3.5,
            verdict=KillSwitchVerdict.FAIL,
            failed_criteria=[
                CriterionResult(
                    name="city_sewer",
                    passed=False,
                    is_hard=False,
                    severity=2.5,
                    message="",
                ),
                CriterionResult(
                    name="lot_size",
                    passed=False,
                    is_hard=False,
                    severity=1.0,
                    message="",
                ),
            ],
            breakdown={"city_sewer": 2.5, "lot_size": 1.0},
        )
        s = str(result)
        assert "FAIL" in s
        assert "3.5" in s
        assert "city_sewer" in s


# ============================================================================
# SoftSeverityEvaluator Tests
# ============================================================================


class TestSoftSeverityEvaluator:
    """Test the SoftSeverityEvaluator class."""

    def test_default_initialization(self):
        """Test evaluator with default thresholds."""
        evaluator = SoftSeverityEvaluator()
        assert evaluator.fail_threshold == 3.0
        assert evaluator.warning_threshold == 1.5

    def test_custom_threshold_initialization(self):
        """Test evaluator with custom thresholds."""
        evaluator = SoftSeverityEvaluator(fail_threshold=5.0, warning_threshold=2.0)
        assert evaluator.fail_threshold == 5.0
        assert evaluator.warning_threshold == 2.0

    def test_invalid_threshold_order_raises_error(self):
        """Test that fail_threshold <= warning_threshold raises ValueError."""
        with pytest.raises(ValueError):
            SoftSeverityEvaluator(fail_threshold=1.5, warning_threshold=3.0)

    def test_equal_thresholds_raises_error(self):
        """Test that equal thresholds raises ValueError."""
        with pytest.raises(ValueError):
            SoftSeverityEvaluator(fail_threshold=2.0, warning_threshold=2.0)

    def test_get_threshold_info(self):
        """Test get_threshold_info method."""
        evaluator = SoftSeverityEvaluator()
        info = evaluator.get_threshold_info()
        assert info["fail_threshold"] == 3.0
        assert info["warning_threshold"] == 1.5

    def test_str_representation(self):
        """Test string representation."""
        evaluator = SoftSeverityEvaluator()
        s = str(evaluator)
        assert "3.0" in s
        assert "1.5" in s

    def test_repr_representation(self):
        """Test repr representation."""
        evaluator = SoftSeverityEvaluator()
        r = repr(evaluator)
        assert "SoftSeverityEvaluator" in r
        assert "fail_threshold=3.0" in r


# ============================================================================
# Severity Accumulation Tests (AC1)
# ============================================================================


class TestSeverityAccumulation:
    """Test severity accumulation behavior."""

    def test_single_soft_failure_accumulation(self):
        """Test severity from single SOFT failure."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Lot too small",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.0
        assert len(result.failed_criteria) == 1
        assert result.breakdown == {"lot_size": 1.0}

    def test_multiple_soft_failures_accumulation(self):
        """Test severity accumulation from multiple SOFT failures."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.5
        assert len(result.failed_criteria) == 2
        assert result.breakdown == {"city_sewer": 2.5, "lot_size": 1.0}

    def test_all_four_soft_criteria_fail(self):
        """Test all 4 SOFT criteria failing (7.0 total severity)."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="2024 build",
            ),
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 7.0
        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.failed_criteria) == 4

    def test_passed_criteria_not_accumulated(self):
        """Test that passed criteria don't contribute to severity."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=True,
                is_hard=False,
                severity=0.0,
                message="",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.0
        assert len(result.failed_criteria) == 1

    def test_hard_criteria_filtered_out(self):
        """Test that HARD criteria are filtered out of SOFT evaluation."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="no_hoa",
                passed=False,
                is_hard=True,
                severity=0.0,
                message="Has HOA",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            ),
        ]
        result = evaluator.evaluate(results)
        # HARD criterion should be filtered out
        assert result.total_severity == 1.0
        assert len(result.failed_criteria) == 1
        assert result.failed_criteria[0].name == "lot_size"


# ============================================================================
# Threshold Boundary Tests (AC2)
# ============================================================================


class TestThresholdBoundaries:
    """Test exact threshold boundary behavior."""

    def test_severity_exactly_1_5_is_warning(self):
        """Test that severity exactly 1.5 is WARNING (boundary)."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.5
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_severity_2_9_is_warning(self):
        """Test that severity 2.9 is still WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=2.9,
                message="test",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 2.9
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_severity_exactly_3_0_is_fail(self):
        """Test that severity exactly 3.0 is FAIL (boundary)."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=0.5,
                message="test",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.0
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_severity_3_1_is_fail(self):
        """Test that severity 3.1 is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=3.1,
                message="test",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.1
        assert result.verdict == KillSwitchVerdict.FAIL


# ============================================================================
# PASS Verdict Tests (AC2 - severity < 1.5)
# ============================================================================


class TestPassVerdict:
    """Test PASS verdict scenarios (severity < 1.5)."""

    def test_severity_0_0_is_pass(self):
        """Test that severity 0.0 (no failures) is PASS."""
        evaluator = SoftSeverityEvaluator()
        results = []
        result = evaluator.evaluate(results)
        assert result.total_severity == 0.0
        assert result.verdict == KillSwitchVerdict.PASS

    def test_severity_0_5_is_pass(self):
        """Test that severity 0.5 is PASS."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=0.5,
                message="test",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 0.5
        assert result.verdict == KillSwitchVerdict.PASS

    def test_severity_1_0_is_pass(self):
        """Test that severity 1.0 (lot_size only) is PASS."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.0
        assert result.verdict == KillSwitchVerdict.PASS

    def test_severity_1_4_is_pass(self):
        """Test that severity 1.4 (just below WARNING) is PASS."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=1.4,
                message="test",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.4
        assert result.verdict == KillSwitchVerdict.PASS


# ============================================================================
# WARNING Verdict Tests (AC2 - severity 1.5-2.99)
# ============================================================================


class TestWarningVerdict:
    """Test WARNING verdict scenarios (severity 1.5-2.99)."""

    def test_severity_1_5_is_warning(self):
        """Test that severity 1.5 (min_garage only) is WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 1.5
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_severity_2_0_is_warning(self):
        """Test that severity 2.0 (no_new_build only) is WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="2024 build",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 2.0
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_severity_2_5_is_warning(self):
        """Test that severity 2.5 (city_sewer only) is WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 2.5
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_severity_2_9_is_warning(self):
        """Test that severity 2.9 (just below FAIL) is WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="test",
                passed=False,
                is_hard=False,
                severity=2.9,
                message="test",
            )
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 2.9
        assert result.verdict == KillSwitchVerdict.WARNING

    def test_lot_size_plus_min_garage_is_warning(self):
        """Test lot_size (1.0) + min_garage (1.5) = 2.5 is WARNING."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small lot",
            ),
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 2.5
        assert result.verdict == KillSwitchVerdict.WARNING


# ============================================================================
# FAIL Verdict Tests (AC2 - severity >= 3.0)
# ============================================================================


class TestFailVerdict:
    """Test FAIL verdict scenarios (severity >= 3.0)."""

    def test_severity_3_0_is_fail(self):
        """Test that severity exactly 3.0 is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="2024",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.0
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_severity_3_5_is_fail(self):
        """Test that severity 3.5 (city_sewer + lot_size) is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.5
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_severity_4_0_is_fail(self):
        """Test that severity 4.0 is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 4.0
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_severity_7_0_is_fail(self):
        """Test that severity 7.0 (all SOFT fail) is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="city_sewer",
                passed=False,
                is_hard=False,
                severity=2.5,
                message="Septic",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="2024",
            ),
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            ),
            CriterionResult(
                name="lot_size",
                passed=False,
                is_hard=False,
                severity=1.0,
                message="Small",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 7.0
        assert result.verdict == KillSwitchVerdict.FAIL

    def test_min_garage_plus_no_new_build_is_fail(self):
        """Test min_garage (1.5) + no_new_build (2.0) = 3.5 is FAIL."""
        evaluator = SoftSeverityEvaluator()
        results = [
            CriterionResult(
                name="min_garage",
                passed=False,
                is_hard=False,
                severity=1.5,
                message="1 garage",
            ),
            CriterionResult(
                name="no_new_build",
                passed=False,
                is_hard=False,
                severity=2.0,
                message="2024",
            ),
        ]
        result = evaluator.evaluate(results)
        assert result.total_severity == 3.5
        assert result.verdict == KillSwitchVerdict.FAIL


# ============================================================================
# SoftCriterionConfig Tests
# ============================================================================


class TestSoftCriterionConfig:
    """Test the SoftCriterionConfig Pydantic model."""

    def test_valid_soft_criterion_config(self):
        """Test creating valid SOFT criterion config."""
        config = SoftCriterionConfig(
            name="city_sewer",
            type="SOFT",
            operator="==",
            threshold="CITY",
            severity=2.5,
            description="City sewer required",
        )
        assert config.name == "city_sewer"
        assert config.type == "SOFT"
        assert config.operator == "=="
        assert config.threshold == "CITY"
        assert config.severity == 2.5
        assert config.description == "City sewer required"

    def test_valid_hard_criterion_config(self):
        """Test creating valid HARD criterion config."""
        config = SoftCriterionConfig(
            name="no_hoa",
            type="HARD",
            operator="==",
            threshold="0",
            severity=0.0,
            description="No HOA",
        )
        assert config.type == "HARD"
        assert config.severity == 0.0

    def test_range_operator_config(self):
        """Test criterion config with range operator."""
        config = SoftCriterionConfig(
            name="lot_size",
            type="SOFT",
            operator="range",
            threshold="7000-15000",
            severity=1.0,
            description="Lot size range",
        )
        assert config.operator == "range"
        assert config.threshold == "7000-15000"

    def test_severity_precision_rounding(self):
        """Test that severity is rounded to 2 decimal places."""
        config = SoftCriterionConfig(
            name="test",
            type="SOFT",
            operator="==",
            threshold="test",
            severity=2.567,
            description="test",
        )
        assert config.severity == 2.57

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises validation error."""
        with pytest.raises(ValidationError):
            SoftCriterionConfig(
                name="test",
                type="INVALID",
                operator="==",
                threshold="test",
                severity=1.0,
                description="test",
            )

    def test_invalid_operator_raises_error(self):
        """Test that invalid operator raises validation error."""
        with pytest.raises(ValidationError):
            SoftCriterionConfig(
                name="test",
                type="SOFT",
                operator="INVALID",
                threshold="test",
                severity=1.0,
                description="test",
            )

    def test_severity_too_high_raises_error(self):
        """Test that severity > 10.0 raises validation error."""
        with pytest.raises(ValidationError):
            SoftCriterionConfig(
                name="test",
                type="SOFT",
                operator="==",
                threshold="test",
                severity=10.5,
                description="test",
            )

    def test_severity_negative_raises_error(self):
        """Test that negative severity raises validation error."""
        with pytest.raises(ValidationError):
            SoftCriterionConfig(
                name="test",
                type="SOFT",
                operator="==",
                threshold="test",
                severity=-1.0,
                description="test",
            )

    def test_empty_name_raises_error(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError):
            SoftCriterionConfig(
                name="",
                type="SOFT",
                operator="==",
                threshold="test",
                severity=1.0,
                description="test",
            )


# ============================================================================
# CSV Configuration Loading Tests
# ============================================================================


class TestLoadSoftCriteriaConfig:
    """Test CSV configuration loading."""

    def test_load_valid_csv(self, tmp_path: Path):
        """Test loading valid CSV configuration."""
        csv_content = """name,type,operator,threshold,severity,description
city_sewer,SOFT,==,CITY,2.5,City sewer required
no_new_build,SOFT,<=,2023,2.0,No new builds
min_garage,SOFT,>=,2,1.5,Min 2 garage
lot_size,SOFT,range,7000-15000,1.0,Lot size range
"""
        csv_path = tmp_path / "kill_switch.csv"
        csv_path.write_text(csv_content)

        configs = load_soft_criteria_config(csv_path)

        assert len(configs) == 4
        assert configs[0].name == "city_sewer"
        assert configs[0].severity == 2.5
        assert configs[1].name == "no_new_build"
        assert configs[2].name == "min_garage"
        assert configs[3].name == "lot_size"

    def test_load_csv_filters_hard_criteria(self, tmp_path: Path):
        """Test that HARD criteria are filtered out when loading."""
        csv_content = """name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,No HOA
city_sewer,SOFT,==,CITY,2.5,City sewer
min_bedrooms,HARD,>=,4,0.0,4 beds
lot_size,SOFT,range,7000-15000,1.0,Lot size
"""
        csv_path = tmp_path / "kill_switch.csv"
        csv_path.write_text(csv_content)

        configs = load_soft_criteria_config(csv_path)

        # Should only have SOFT criteria
        assert len(configs) == 2
        assert configs[0].name == "city_sewer"
        assert configs[1].name == "lot_size"

    def test_load_csv_file_not_found(self):
        """Test FileNotFoundError for missing CSV."""
        with pytest.raises(FileNotFoundError):
            load_soft_criteria_config(Path("/nonexistent/path.csv"))

    def test_load_csv_missing_header(self, tmp_path: Path):
        """Test ValueError for CSV without header."""
        csv_content = ""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError, match="no header row"):
            load_soft_criteria_config(csv_path)

    def test_load_csv_missing_required_field(self, tmp_path: Path):
        """Test ValueError for CSV missing required fields."""
        csv_content = """name,type,operator
city_sewer,SOFT,==
"""
        csv_path = tmp_path / "incomplete.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError, match="missing required fields"):
            load_soft_criteria_config(csv_path)

    def test_load_csv_invalid_severity(self, tmp_path: Path):
        """Test ValueError for invalid severity value."""
        csv_content = """name,type,operator,threshold,severity,description
city_sewer,SOFT,==,CITY,invalid,City sewer
"""
        csv_path = tmp_path / "bad_severity.csv"
        csv_path.write_text(csv_content)

        with pytest.raises(ValueError, match="Invalid data"):
            load_soft_criteria_config(csv_path)

    def test_load_csv_with_comments(self, tmp_path: Path):
        """Test loading CSV that has comment lines (rows starting with #)."""
        csv_content = """name,type,operator,threshold,severity,description
# This is a comment line that should be skipped
city_sewer,SOFT,==,CITY,2.5,City sewer
# Another comment
lot_size,SOFT,range,7000-15000,1.0,Lot size range
"""
        csv_path = tmp_path / "with_comments.csv"
        csv_path.write_text(csv_content)

        configs = load_soft_criteria_config(csv_path)
        # Should only load 2 SOFT criteria, skipping comment lines
        assert len(configs) == 2
        assert configs[0].name == "city_sewer"
        assert configs[1].name == "lot_size"


# ============================================================================
# Integration with KillSwitchFilter Tests
# ============================================================================


class TestKillSwitchFilterIntegration:
    """Test SoftSeverityEvaluator integration with KillSwitchFilter."""

    def test_filter_has_soft_evaluator(self):
        """Test that KillSwitchFilter has soft evaluator attribute."""
        from src.phx_home_analysis.services.kill_switch import KillSwitchFilter

        ks_filter = KillSwitchFilter()
        evaluator = ks_filter.get_soft_evaluator()
        assert evaluator is not None
        assert isinstance(evaluator, SoftSeverityEvaluator)

    def test_filter_evaluate_soft_severity_method_exists(self):
        """Test that evaluate_soft_severity method exists on filter."""
        from src.phx_home_analysis.services.kill_switch import KillSwitchFilter

        ks_filter = KillSwitchFilter()
        assert hasattr(ks_filter, "evaluate_soft_severity")
        assert callable(ks_filter.evaluate_soft_severity)


# ============================================================================
# Integration Test for Actual CSV File
# ============================================================================


class TestActualCsvFileLoading:
    """Integration tests that load the actual config/kill_switch.csv file."""

    def test_load_actual_kill_switch_csv(self):
        """Test loading the actual config/kill_switch.csv file.

        This integration test validates that:
        1. The config/kill_switch.csv file exists
        2. It can be parsed without errors
        3. It contains the expected 4 SOFT criteria
        4. All SOFT criteria have valid severity weights
        """
        # Get the project root (tests/unit/services/kill_switch -> project root)
        project_root = Path(__file__).parent.parent.parent.parent.parent
        csv_path = project_root / "config" / "kill_switch.csv"

        # Verify file exists
        assert csv_path.exists(), f"Config file not found: {csv_path}"

        # Load and validate
        configs = load_soft_criteria_config(csv_path)

        # Should have exactly 4 SOFT criteria
        assert len(configs) == 4, f"Expected 4 SOFT criteria, got {len(configs)}"

        # Validate expected SOFT criteria names and severities
        expected_criteria = {
            "city_sewer": 2.5,
            "no_new_build": 2.0,
            "min_garage": 1.5,
            "lot_size": 1.0,
        }

        loaded_criteria = {cfg.name: cfg.severity for cfg in configs}
        assert loaded_criteria == expected_criteria, (
            f"Criteria mismatch. Expected: {expected_criteria}, Got: {loaded_criteria}"
        )

        # Validate all configs have required fields
        for cfg in configs:
            assert cfg.name, "Config name should not be empty"
            assert cfg.type == "SOFT", f"Expected SOFT type, got {cfg.type}"
            assert cfg.operator in ("==", "!=", ">", "<", ">=", "<=", "range")
            assert cfg.threshold, "Config threshold should not be empty"
            assert 0.0 <= cfg.severity <= 10.0, f"Invalid severity: {cfg.severity}"
            assert cfg.description, "Config description should not be empty"

    def test_actual_csv_hard_criteria_skipped_with_warning(self, caplog):
        """Test that HARD criteria in actual CSV are skipped with warning logged."""
        import logging

        project_root = Path(__file__).parent.parent.parent.parent.parent
        csv_path = project_root / "config" / "kill_switch.csv"

        # Enable warning capture
        with caplog.at_level(logging.WARNING):
            configs = load_soft_criteria_config(csv_path)

        # Should have logged a warning about skipped HARD rows
        assert any(
            "Skipped" in record.message and "HARD" in record.message for record in caplog.records
        ), "Expected warning about skipped HARD criteria"

        # Verify only SOFT configs returned
        assert all(cfg.type == "SOFT" for cfg in configs)

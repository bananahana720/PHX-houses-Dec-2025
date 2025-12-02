"""Tests for the consolidated kill-switch module in scripts/lib.

Verifies that the consolidated implementation matches behavior of:
- scripts/phx_home_analyzer.py (original)
- scripts/deal_sheets.py (original)
- src/phx_home_analysis/services/kill_switch (canonical)
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from lib.kill_switch import (
    HARD_CRITERIA,
    KILL_SWITCH_CRITERIA,
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    SOFT_SEVERITY_WEIGHTS,
    KillSwitchVerdict,
    apply_kill_switch,
    evaluate_kill_switches,
    evaluate_kill_switches_for_display,
    get_kill_switch_summary,
)


# Simple Property dataclass matching scripts/phx_home_analyzer.py
@dataclass
class Property:
    """Test property dataclass."""

    beds: int = 0
    baths: float = 0.0
    hoa_fee: float | None = None
    sewer_type: str | None = None
    garage_spaces: int | None = None
    lot_sqft: int | None = None
    year_built: int | None = None
    kill_switch_passed: bool | None = None
    kill_switch_failures: list[str] = field(default_factory=list)


class TestKillSwitchCriteria:
    """Test individual kill switch criteria."""

    def test_criteria_count(self):
        """Should have 7 kill switch criteria."""
        assert len(KILL_SWITCH_CRITERIA) == 7

    def test_criteria_have_required_fields(self):
        """Each criterion should have field, check, description, requirement."""
        for name, criteria in KILL_SWITCH_CRITERIA.items():
            assert "field" in criteria, f"{name} missing 'field'"
            assert "check" in criteria, f"{name} missing 'check'"
            assert "description" in criteria, f"{name} missing 'description'"
            assert "requirement" in criteria, f"{name} missing 'requirement'"
            assert callable(criteria["check"]), f"{name} 'check' not callable"


class TestHoaKillSwitch:
    """Test HOA kill switch logic."""

    def test_no_hoa_passes(self):
        """Property with $0 HOA should pass."""
        prop = Property(beds=4, baths=2, hoa_fee=0)
        result = apply_kill_switch(prop)
        assert "hoa" not in str(result.kill_switch_failures).lower()

    def test_none_hoa_passes(self):
        """Property with None HOA (unknown) should pass."""
        prop = Property(beds=4, baths=2, hoa_fee=None)
        result = apply_kill_switch(prop)
        assert "hoa" not in str(result.kill_switch_failures).lower()

    def test_positive_hoa_fails(self):
        """Property with HOA fee should fail."""
        prop = Property(beds=4, baths=2, hoa_fee=150)
        result = apply_kill_switch(prop)
        assert not result.kill_switch_passed or "hoa" in str(
            result.kill_switch_failures
        ).lower()


class TestSewerKillSwitch:
    """Test sewer kill switch logic."""

    def test_city_sewer_passes(self):
        """Property with city sewer should pass."""
        prop = Property(beds=4, baths=2, sewer_type="city")
        result = apply_kill_switch(prop)
        assert "sewer" not in str(result.kill_switch_failures).lower()

    def test_unknown_sewer_passes(self):
        """Property with unknown sewer should pass (permissive)."""
        prop = Property(beds=4, baths=2, sewer_type=None)
        result = apply_kill_switch(prop)
        assert "sewer" not in str(result.kill_switch_failures).lower()

    def test_septic_sewer_fails(self):
        """Property with septic should fail."""
        prop = Property(beds=4, baths=2, sewer_type="septic")
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "sewer" in failures_str


class TestGarageKillSwitch:
    """Test garage kill switch logic."""

    def test_two_car_garage_passes(self):
        """Property with 2-car garage should pass."""
        prop = Property(beds=4, baths=2, garage_spaces=2)
        result = apply_kill_switch(prop)
        assert "garage" not in str(result.kill_switch_failures).lower()

    def test_three_car_garage_passes(self):
        """Property with 3-car garage should pass."""
        prop = Property(beds=4, baths=2, garage_spaces=3)
        result = apply_kill_switch(prop)
        assert "garage" not in str(result.kill_switch_failures).lower()

    def test_one_car_garage_fails(self):
        """Property with 1-car garage should fail."""
        prop = Property(beds=4, baths=2, garage_spaces=1)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "garage" in failures_str

    def test_unknown_garage_passes(self):
        """Property with unknown garage should pass (permissive)."""
        prop = Property(beds=4, baths=2, garage_spaces=None)
        result = apply_kill_switch(prop)
        assert "garage" not in str(result.kill_switch_failures).lower()


class TestBedsKillSwitch:
    """Test bedrooms kill switch logic."""

    def test_four_beds_passes(self):
        """Property with 4 beds should pass."""
        prop = Property(beds=4, baths=2)
        result = apply_kill_switch(prop)
        assert "beds" not in str(result.kill_switch_failures).lower()

    def test_five_beds_passes(self):
        """Property with 5 beds should pass."""
        prop = Property(beds=5, baths=2)
        result = apply_kill_switch(prop)
        assert "beds" not in str(result.kill_switch_failures).lower()

    def test_three_beds_fails(self):
        """Property with 3 beds should fail."""
        prop = Property(beds=3, baths=2)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "beds" in failures_str


class TestBathsKillSwitch:
    """Test bathrooms kill switch logic."""

    def test_two_baths_passes(self):
        """Property with 2 baths should pass."""
        prop = Property(beds=4, baths=2.0)
        result = apply_kill_switch(prop)
        assert "baths" not in str(result.kill_switch_failures).lower()

    def test_three_baths_passes(self):
        """Property with 3 baths should pass."""
        prop = Property(beds=4, baths=3.0)
        result = apply_kill_switch(prop)
        assert "baths" not in str(result.kill_switch_failures).lower()

    def test_one_bath_fails(self):
        """Property with 1 bath should fail."""
        prop = Property(beds=4, baths=1.0)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "baths" in failures_str


class TestLotSizeKillSwitch:
    """Test lot size kill switch logic."""

    def test_mid_range_lot_passes(self):
        """Property with lot in range (10000 sqft) should pass."""
        prop = Property(beds=4, baths=2, lot_sqft=10000)
        result = apply_kill_switch(prop)
        assert "lot" not in str(result.kill_switch_failures).lower()

    def test_minimum_lot_passes(self):
        """Property at minimum (7000 sqft) should pass."""
        prop = Property(beds=4, baths=2, lot_sqft=7000)
        result = apply_kill_switch(prop)
        assert "lot" not in str(result.kill_switch_failures).lower()

    def test_maximum_lot_passes(self):
        """Property at maximum (15000 sqft) should pass."""
        prop = Property(beds=4, baths=2, lot_sqft=15000)
        result = apply_kill_switch(prop)
        assert "lot" not in str(result.kill_switch_failures).lower()

    def test_small_lot_fails(self):
        """Property with small lot (5000 sqft) should fail."""
        prop = Property(beds=4, baths=2, lot_sqft=5000)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "lot" in failures_str

    def test_large_lot_fails(self):
        """Property with large lot (20000 sqft) should fail."""
        prop = Property(beds=4, baths=2, lot_sqft=20000)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "lot" in failures_str

    def test_unknown_lot_passes(self):
        """Property with unknown lot should pass (permissive)."""
        prop = Property(beds=4, baths=2, lot_sqft=None)
        result = apply_kill_switch(prop)
        assert "lot" not in str(result.kill_switch_failures).lower()


class TestYearBuiltKillSwitch:
    """Test year built kill switch logic."""

    def test_older_home_passes(self):
        """Property built in 2000 should pass."""
        prop = Property(beds=4, baths=2, year_built=2000)
        result = apply_kill_switch(prop)
        assert "year" not in str(result.kill_switch_failures).lower()

    def test_2023_home_passes(self):
        """Property built in 2023 should pass (at boundary)."""
        prop = Property(beds=4, baths=2, year_built=2023)
        result = apply_kill_switch(prop)
        assert "year" not in str(result.kill_switch_failures).lower()

    def test_new_build_fails(self):
        """Property built in current year should fail."""
        prop = Property(beds=4, baths=2, year_built=datetime.now().year)
        result = apply_kill_switch(prop)
        failures_str = str(result.kill_switch_failures).lower()
        assert "year" in failures_str or "new" in failures_str

    def test_unknown_year_passes(self):
        """Property with unknown year should pass (permissive)."""
        prop = Property(beds=4, baths=2, year_built=None)
        result = apply_kill_switch(prop)
        assert "year" not in str(result.kill_switch_failures).lower()


class TestFullPropertyEvaluation:
    """Test complete property evaluation scenarios."""

    def test_perfect_property_passes(self):
        """Property meeting all criteria should pass."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        result = apply_kill_switch(prop)
        assert result.kill_switch_passed is True
        assert len(result.kill_switch_failures) == 0

    def test_multiple_failures(self):
        """Property failing multiple criteria should list all failures."""
        prop = Property(
            beds=3,  # Fails
            baths=1,  # Fails
            hoa_fee=100,  # Fails
            sewer_type="septic",  # Fails
            garage_spaces=1,  # Fails
            lot_sqft=5000,  # Fails
            year_built=datetime.now().year,  # Fails
        )
        result = apply_kill_switch(prop)
        assert result.kill_switch_passed is False
        assert len(result.kill_switch_failures) == 7


class TestEvaluateKillSwitches:
    """Test the evaluate_kill_switches function."""

    def test_returns_tuple(self):
        """Should return (verdict, severity, failures, results) tuple."""
        prop = Property(beds=4, baths=2)
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert isinstance(verdict, KillSwitchVerdict)
        assert isinstance(severity, float)
        assert isinstance(failures, list)
        assert isinstance(results, list)

    def test_with_dict_input(self):
        """Should work with dict input (for pandas compatibility)."""
        data = {"beds": 4, "baths": 2.0, "hoa_fee": 0, "sewer_type": "city"}
        verdict, severity, failures, results = evaluate_kill_switches(data)
        assert isinstance(verdict, KillSwitchVerdict)
        assert isinstance(results, list)


class TestEvaluateKillSwitchesForDisplay:
    """Test the display-friendly evaluation function."""

    def test_returns_dict(self):
        """Should return dict with criterion names as keys."""
        prop = Property(beds=4, baths=2)
        results = evaluate_kill_switches_for_display(prop)
        assert isinstance(results, dict)

    def test_result_structure(self):
        """Each result should have passed, color, label, description."""
        prop = Property(beds=4, baths=2, hoa_fee=0)
        results = evaluate_kill_switches_for_display(prop)

        for name, result in results.items():
            if name == "_summary":
                # Summary has different structure
                assert "verdict" in result
                assert "severity_score" in result
                continue
            assert "passed" in result
            assert "color" in result
            assert "label" in result
            assert "description" in result
            assert result["color"] in ("green", "yellow", "red")
            assert result["label"] in ("PASS", "FAIL", "UNKNOWN", "HARD FAIL")

    def test_pass_color_green(self):
        """Passing criteria should be green."""
        prop = Property(beds=4, baths=2)
        results = evaluate_kill_switches_for_display(prop)
        # Beds with 4 should pass and be green
        # Find the beds key (may be "BEDS" or "Beds")
        beds_result = None
        for key in results:
            if "bed" in key.lower():
                beds_result = results[key]
                break
        assert beds_result is not None, f"Beds not found in {list(results.keys())}"
        assert beds_result["passed"] is True
        assert beds_result["color"] == "green"

    def test_fail_color_red(self):
        """Failing criteria should be red."""
        prop = Property(beds=3, baths=2)
        results = evaluate_kill_switches_for_display(prop)
        # Beds with 3 should fail and be red
        # Find the beds key (may be "BEDS" or "Beds")
        beds_result = None
        for key in results:
            if "bed" in key.lower():
                beds_result = results[key]
                break
        assert beds_result is not None, f"Beds not found in {list(results.keys())}"
        assert beds_result["passed"] is False
        assert beds_result["color"] == "red"


class TestGetKillSwitchSummary:
    """Test the summary function."""

    def test_returns_string(self):
        """Should return a string summary."""
        summary = get_kill_switch_summary()
        assert isinstance(summary, str)

    def test_contains_all_criteria(self):
        """Summary should mention all criteria."""
        summary = get_kill_switch_summary().lower()
        assert "hoa" in summary
        assert "sewer" in summary
        assert "garage" in summary
        assert "beds" in summary or "bedroom" in summary
        assert "baths" in summary or "bathroom" in summary
        assert "lot" in summary
        assert "year" in summary or "build" in summary


# =============================================================================
# SEVERITY THRESHOLD TESTS (Wave 1.1 Implementation)
# =============================================================================


class TestSeverityThresholdConstants:
    """Test that severity constants are properly defined."""

    def test_hard_criteria_defined(self):
        """HARD_CRITERIA should contain hoa, beds, baths."""
        assert "hoa" in HARD_CRITERIA
        assert "beds" in HARD_CRITERIA
        assert "baths" in HARD_CRITERIA

    def test_soft_criteria_weights_defined(self):
        """SOFT_SEVERITY_WEIGHTS should have correct weights."""
        assert SOFT_SEVERITY_WEIGHTS["sewer"] == 2.5
        assert SOFT_SEVERITY_WEIGHTS["garage"] == 1.5
        assert SOFT_SEVERITY_WEIGHTS["lot_size"] == 1.0
        assert SOFT_SEVERITY_WEIGHTS["year_built"] == 2.0

    def test_thresholds_defined(self):
        """Threshold constants should be correctly defined."""
        assert SEVERITY_FAIL_THRESHOLD == 3.0
        assert SEVERITY_WARNING_THRESHOLD == 1.5


class TestKillSwitchVerdictEnum:
    """Test the KillSwitchVerdict enum."""

    def test_enum_values(self):
        """Enum should have PASS, WARNING, FAIL values."""
        assert KillSwitchVerdict.PASS.value == "PASS"
        assert KillSwitchVerdict.WARNING.value == "WARNING"
        assert KillSwitchVerdict.FAIL.value == "FAIL"


class TestSeverityThreshold:
    """Test severity threshold calculations with different property configurations."""

    def test_septic_alone_is_warning(self):
        """Septic (2.5) < 3.0 threshold = WARNING."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # SOFT: 2.5
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert len(failures) == 1

    def test_septic_plus_new_build_is_fail(self):
        """Septic (2.5) + Year (2.0) = 4.5 >= 3.0 = FAIL."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # SOFT: 2.5
            garage_spaces=2,
            lot_sqft=10000,
            year_built=datetime.now().year,  # SOFT: 2.0
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 4.5
        assert len(failures) == 2

    def test_small_lot_alone_is_pass(self):
        """Lot (1.0) < 1.5 warning threshold = PASS."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=5000,  # SOFT: 1.0 (too small)
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.PASS
        assert severity == 1.0
        assert len(failures) == 1

    def test_garage_plus_lot_is_warning(self):
        """Garage (1.5) + Lot (1.0) = 2.5 = WARNING."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=1,  # SOFT: 1.5
            lot_sqft=5000,  # SOFT: 1.0 (too small)
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert len(failures) == 2

    def test_hoa_is_hard_fail(self):
        """HOA > $0 = instant FAIL, no severity calc for HARD criteria."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=150,  # HARD FAIL
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        # Severity should still be 0 since no SOFT criteria failed
        assert severity == 0.0
        # But we should have 1 failure from HOA
        assert len(failures) == 1
        assert "hoa" in failures[0].lower()

    def test_beds_is_hard_fail(self):
        """Beds < 4 = instant FAIL, no severity calc for HARD criteria."""
        prop = Property(
            beds=3,  # HARD FAIL
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 0.0
        assert len(failures) == 1

    def test_baths_is_hard_fail(self):
        """Baths < 2 = instant FAIL, no severity calc for HARD criteria."""
        prop = Property(
            beds=4,
            baths=1.5,  # HARD FAIL
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 0.0
        assert len(failures) == 1

    def test_hard_fail_plus_soft_failures_still_hard_fail(self):
        """HARD fail takes precedence, but SOFT severity still calculated."""
        prop = Property(
            beds=3,  # HARD FAIL
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # SOFT: 2.5
            garage_spaces=1,  # SOFT: 1.5
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        # SOFT severity is still calculated
        assert severity == 4.0  # 2.5 + 1.5
        # 3 failures total
        assert len(failures) == 3

    def test_all_soft_failures_is_fail(self):
        """All SOFT criteria failing = 7.0 severity = FAIL."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # SOFT: 2.5
            garage_spaces=1,  # SOFT: 1.5
            lot_sqft=5000,  # SOFT: 1.0 (too small)
            year_built=datetime.now().year,  # SOFT: 2.0
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 7.0
        assert len(failures) == 4

    def test_perfect_property_is_pass(self):
        """Property passing all criteria has PASS verdict and 0 severity."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.PASS
        assert severity == 0.0
        assert len(failures) == 0


class TestKillSwitchResultFields:
    """Test that KillSwitchResult has the new severity fields."""

    def test_result_has_is_hard_field(self):
        """KillSwitchResult should have is_hard field."""
        prop = Property(beds=4, baths=2, hoa_fee=150)  # HOA fails
        verdict, severity, failures, results = evaluate_kill_switches(prop)

        hoa_result = next(r for r in results if r.name == "hoa")
        assert hasattr(hoa_result, "is_hard")
        assert hoa_result.is_hard is True

    def test_result_has_severity_weight_field(self):
        """KillSwitchResult should have severity_weight field."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # SOFT failure
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)

        sewer_result = next(r for r in results if r.name == "sewer")
        assert hasattr(sewer_result, "severity_weight")
        assert sewer_result.severity_weight == 2.5

    def test_passed_criteria_have_zero_severity_weight(self):
        """Passed criteria should have severity_weight of 0."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="city",
        )
        verdict, severity, failures, results = evaluate_kill_switches(prop)

        sewer_result = next(r for r in results if r.name == "sewer")
        assert sewer_result.passed is True
        assert sewer_result.severity_weight == 0.0


class TestApplyKillSwitchSeverity:
    """Test that apply_kill_switch works with severity system."""

    def test_apply_sets_passed_for_warning(self):
        """WARNING verdict should set kill_switch_passed = True."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # WARNING (2.5)
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        result = apply_kill_switch(prop)
        # WARNING is still "passed" for backward compatibility
        assert result.kill_switch_passed is True
        assert len(result.kill_switch_failures) == 1

    def test_apply_sets_failed_for_hard_fail(self):
        """HARD FAIL should set kill_switch_passed = False."""
        prop = Property(
            beds=3,  # HARD FAIL
            baths=2,
            hoa_fee=0,
            sewer_type="city",
            garage_spaces=2,
            lot_sqft=10000,
            year_built=2010,
        )
        result = apply_kill_switch(prop)
        assert result.kill_switch_passed is False
        assert len(result.kill_switch_failures) == 1

    def test_apply_sets_failed_for_severity_threshold(self):
        """Severity >= 3.0 should set kill_switch_passed = False."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # 2.5
            garage_spaces=2,
            lot_sqft=10000,
            year_built=datetime.now().year,  # 2.0 -> total 4.5
        )
        result = apply_kill_switch(prop)
        assert result.kill_switch_passed is False
        assert len(result.kill_switch_failures) == 2


class TestEvaluateKillSwitchesForDisplaySeverity:
    """Test display function includes severity info."""

    def test_display_includes_summary(self):
        """Display results should include _summary key."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",
        )
        results = evaluate_kill_switches_for_display(prop)
        assert "_summary" in results
        assert "verdict" in results["_summary"]
        assert "severity_score" in results["_summary"]

    def test_display_summary_has_correct_verdict(self):
        """Display summary should have correct verdict."""
        prop = Property(
            beds=4,
            baths=2,
            hoa_fee=0,
            sewer_type="septic",  # 2.5 -> WARNING
        )
        results = evaluate_kill_switches_for_display(prop)
        assert results["_summary"]["verdict"] == "WARNING"
        assert results["_summary"]["severity_score"] == 2.5

    def test_display_criteria_have_is_hard_field(self):
        """Display criteria should have is_hard field."""
        prop = Property(beds=4, baths=2, hoa_fee=0)
        results = evaluate_kill_switches_for_display(prop)

        # Check HOA criterion (HARD)
        hoa_key = None
        for key in results:
            if key != "_summary" and "hoa" in key.lower():
                hoa_key = key
                break
        assert hoa_key is not None
        assert results[hoa_key]["is_hard"] is True

    def test_display_hard_fail_label(self):
        """Display should show 'HARD FAIL' label for HARD failures."""
        prop = Property(beds=3, baths=2, hoa_fee=0)  # beds HARD FAIL
        results = evaluate_kill_switches_for_display(prop)

        # Find beds criterion
        beds_key = None
        for key in results:
            if key != "_summary" and "bed" in key.lower():
                beds_key = key
                break
        assert beds_key is not None
        assert results[beds_key]["label"] == "HARD FAIL"

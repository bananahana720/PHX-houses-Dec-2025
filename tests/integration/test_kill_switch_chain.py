"""Integration tests for kill-switch filter chain and severity system.

Tests the complete kill-switch validation chain including:
- HARD criteria (immediate fail)
- SOFT criteria with severity accumulation
- WARNING vs FAIL verdict thresholds
- Boundary conditions
"""


from src.phx_home_analysis.domain.enums import SewerType
from src.phx_home_analysis.services.kill_switch import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.filter import KillSwitchFilter

# ============================================================================
# Test Complete Kill-Switch Chain
# ============================================================================


class TestKillSwitchFilterChain:
    """Test the full kill-switch filtering chain."""

    def test_all_properties_processed_consistently(self, sample_properties):
        """Test that all properties in batch are processed consistently.

        Every property should either pass or fail filtering, with no data loss.
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)

        # All properties accounted for
        assert len(passed) + len(failed) == len(sample_properties)

        # No duplicates
        all_addresses = [p.full_address for p in passed + failed]
        assert len(all_addresses) == len(set(all_addresses))

    def test_kill_switch_chain_verdict_type(self, sample_property):
        """Test that evaluate_with_severity returns proper verdict type.

        Verdict should be KillSwitchVerdict enum (PASS, WARNING, or FAIL).
        """
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert isinstance(verdict, KillSwitchVerdict)
        assert isinstance(severity, (int, float))
        assert isinstance(failures, list)

    def test_kill_switch_chain_reports_all_failures(self, sample_property):
        """Test that all failure reasons are reported in failures list.

        If a property fails multiple criteria, all failures should be listed.
        """
        # Create property that fails multiple SOFT criteria
        sample_property.sewer_type = SewerType.UNKNOWN  # SOFT: severity 2.5
        sample_property.year_built = 2024  # SOFT: severity 2.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Should have at least 2 failures
        assert len(failures) >= 2
        assert any("sewer" in f.lower() for f in failures)
        assert any("year" in f.lower() or "2024" in f for f in failures)

    def test_kill_switch_chain_maintains_property_reference(self, sample_property):
        """Test that filtering maintains property references for scoring.

        Properties should be returned unchanged so downstream scoring can access
        all original data.
        """
        original_address = sample_property.full_address
        original_price = sample_property.price_num

        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_property])

        assert len(passed) == 1
        assert passed[0].full_address == original_address
        assert passed[0].price_num == original_price


# ============================================================================
# Test HARD Criteria (Instant Fail)
# ============================================================================


class TestHardCriteriaChain:
    """Test HARD kill-switch criteria that cause immediate failure."""

    def test_hoa_hard_fail_immediately(self, sample_property):
        """Test that any HOA fee causes immediate FAIL (HARD criterion).

        HARD criteria should not be affected by SOFT criterion severity.
        """
        sample_property.hoa_fee = 100

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert any("HOA" in f for f in failures)

    def test_min_bedrooms_hard_fail_immediately(self, sample_property):
        """Test that insufficient bedrooms causes immediate FAIL (HARD criterion)."""
        sample_property.beds = 3

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert any("bed" in f.lower() for f in failures)

    def test_min_bathrooms_hard_fail_immediately(self, sample_property):
        """Test that insufficient bathrooms causes immediate FAIL (HARD criterion)."""
        sample_property.baths = 1.5

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert any("bath" in f.lower() for f in failures)

    def test_multiple_hard_fails(self, sample_property):
        """Test that property with multiple HARD failures shows all failures."""
        sample_property.beds = 3
        sample_property.baths = 1.5
        sample_property.hoa_fee = 200

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        # Should report all failures
        assert len(failures) >= 3


# ============================================================================
# Test SOFT Criteria and Severity Accumulation
# ============================================================================


class TestSoftCriteriaSeverityChain:
    """Test SOFT criteria severity accumulation and thresholds."""

    def test_single_soft_failure_below_warning_threshold(self, sample_property):
        """Test single SOFT failure with severity < 1.5 is PASS.

        Example: Lot size (severity 1.0) alone = PASS.
        """
        sample_property.lot_sqft = 6500  # SOFT: severity 1.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Lot size alone (1.0) is below WARNING threshold (1.5) = PASS
        assert verdict == KillSwitchVerdict.PASS
        assert severity == 1.0
        assert any("lot" in f.lower() for f in failures)

    def test_sewer_failure_at_warning_threshold(self, sample_septic_property):
        """Test septic sewer (severity 2.5) results in WARNING verdict.

        Septic severity (2.5) >= WARNING threshold (1.5) but < FAIL (3.0).
        """
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(
            sample_septic_property
        )

        # Septic (2.5) is >= 1.5 = WARNING, < 3.0 = not FAIL
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert any("sewer" in f.lower() or "septic" in f.lower() for f in failures)

    def test_year_built_soft_failure(self, sample_property):
        """Test new build year (2024, severity 2.0) results in WARNING.

        2024+ severity (2.0) >= WARNING threshold (1.5) but < FAIL (3.0).
        """
        sample_property.year_built = 2024

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Year built (2.0) is >= 1.5 = WARNING, < 3.0 = not FAIL
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.0
        assert any("year" in f.lower() or "2024" in f for f in failures)

    def test_garage_failure_at_warning_threshold(self, sample_property):
        """Test single garage space (severity 1.5) results in WARNING.

        1-car garage severity (1.5) equals WARNING threshold exactly.
        """
        sample_property.garage_spaces = 1

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Garage (1.5) = WARNING threshold (1.5), < FAIL threshold (3.0)
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 1.5
        assert any("garage" in f.lower() for f in failures)

    def test_sewer_unknown_failure(self, sample_property):
        """Test unknown sewer type (severity 2.5) results in WARNING.

        Cannot verify sewer is city = severity 2.5 = WARNING.
        """
        sample_property.sewer_type = SewerType.UNKNOWN

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Unknown sewer (2.5) is >= 1.5 = WARNING, < 3.0 = not FAIL
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert any("sewer" in f.lower() or "unknown" in f.lower() for f in failures)


# ============================================================================
# Test Severity Accumulation (Multiple SOFT Failures)
# ============================================================================


class TestSeverityAccumulation:
    """Test accumulation of multiple SOFT criterion failures."""

    def test_two_soft_failures_below_fail_threshold(self, sample_property):
        """Test two SOFT failures that sum below FAIL threshold = WARNING.

        Example: Lot (1.0) + year (2.0) = 3.0 at boundary.
        Note: Documentation says >= 3.0 = FAIL
        """
        sample_property.lot_sqft = 6500  # SOFT: severity 1.0
        sample_property.year_built = 2024  # SOFT: severity 2.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Sum: 1.0 + 2.0 = 3.0 >= FAIL threshold (3.0)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 3.0
        assert len(failures) >= 2

    def test_accumulation_reaches_fail_threshold(self, sample_property):
        """Test severity accumulation reaching exact FAIL threshold (3.0).

        Multiple failures: sewer (2.5) + garage (1.5) = 4.0 > 3.0 = FAIL.
        """
        sample_property.sewer_type = SewerType.SEPTIC  # SOFT: severity 2.5
        sample_property.garage_spaces = 1  # SOFT: severity 1.5

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Sum: 2.5 + 1.5 = 4.0 >= FAIL threshold (3.0) = FAIL
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 4.0
        assert len(failures) >= 2

    def test_accumulation_exceeds_fail_threshold(self, sample_property):
        """Test severity accumulation well above FAIL threshold.

        Multiple failures: sewer (2.5) + year (2.0) + garage (1.5) = 6.0.
        """
        sample_property.sewer_type = SewerType.SEPTIC  # SOFT: severity 2.5
        sample_property.year_built = 2024  # SOFT: severity 2.0
        sample_property.garage_spaces = 1  # SOFT: severity 1.5

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Sum: 2.5 + 2.0 + 1.5 = 6.0 > FAIL threshold (3.0) = FAIL
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 6.0
        assert len(failures) >= 3


# ============================================================================
# Test Boundary Conditions (Critical Thresholds)
# ============================================================================


class TestSeverityBoundaryConditions:
    """Test critical boundary conditions for severity thresholds."""

    def test_severity_exactly_at_1_5_warning_boundary(self, sample_property):
        """Test severity exactly at 1.5 WARNING threshold boundary.

        Severity = 1.5 should trigger WARNING (>= 1.5).
        """
        sample_property.garage_spaces = 1  # Exactly 1.5 severity

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 1.5

    def test_severity_just_below_warning_boundary(self, sample_property):
        """Test severity just below 1.5 WARNING boundary.

        Lot size = 1.0 severity < 1.5 = PASS.
        """
        sample_property.lot_sqft = 6500  # Exactly 1.0 severity

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.PASS
        assert severity == 1.0

    def test_severity_exactly_at_3_0_fail_boundary(self, sample_property):
        """Test severity exactly at 3.0 FAIL threshold boundary.

        Severity = 3.0 should trigger FAIL (>= 3.0).
        """
        sample_property.lot_sqft = 6500  # Lot: severity 1.0
        sample_property.year_built = 2024  # Year: severity 2.0
        # Total: 1.0 + 2.0 = 3.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 3.0

    def test_severity_just_below_fail_boundary(self, sample_property):
        """Test severity just below 3.0 FAIL boundary.

        Severity = 2.9 < 3.0 = WARNING, not FAIL.
        """
        # Create combination that sums to just below 3.0
        # Example: sewer (2.5) + lot (small amount) ~ 2.9
        sample_property.sewer_type = SewerType.SEPTIC  # severity 2.5

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        # Single sewer failure is 2.5 < 3.0 = WARNING
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5

    def test_severity_just_above_fail_boundary(self, sample_property):
        """Test severity just above 3.0 FAIL boundary.

        Severity > 3.0 = FAIL.
        """
        sample_property.sewer_type = SewerType.SEPTIC  # severity 2.5
        sample_property.garage_spaces = 1  # severity 1.5
        # Total: 2.5 + 1.5 = 4.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert severity >= 3.0


# ============================================================================
# Test Verdict Consistency
# ============================================================================


class TestVerdictConsistency:
    """Test consistency between batch and individual evaluation."""

    def test_batch_filter_verdict_matches_individual(self, sample_property):
        """Test that batch filtering produces same verdict as individual evaluation.

        filter_properties() and evaluate_with_severity() should agree.
        """
        filter_service = KillSwitchFilter()

        # Individual evaluation
        individual_verdict, individual_severity, individual_failures = (
            filter_service.evaluate_with_severity(sample_property)
        )

        # Batch evaluation
        passed, failed = filter_service.filter_properties([sample_property])

        # Results should be consistent
        if individual_verdict == KillSwitchVerdict.FAIL:
            assert len(failed) == 1
            assert len(passed) == 0
        elif individual_verdict == KillSwitchVerdict.WARNING:
            # WARNING passes filter (backward compatibility)
            assert len(passed) == 1
            assert len(failed) == 0
        else:  # PASS
            assert len(passed) == 1
            assert len(failed) == 0

    def test_verdict_consistency_across_properties(self, sample_properties):
        """Test that verdict is consistent for all properties in batch.

        Each property should get same verdict via batch and individual evaluation.
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)

        for prop in passed:
            verdict, _, _ = filter_service.evaluate_with_severity(prop)
            # Passed properties should be PASS or WARNING
            assert verdict in [KillSwitchVerdict.PASS, KillSwitchVerdict.WARNING]

        for prop in failed:
            verdict, _, _ = filter_service.evaluate_with_severity(prop)
            # Failed properties should be FAIL (hard criterion failure)
            assert verdict == KillSwitchVerdict.FAIL


# ============================================================================
# Test Real-World Scenarios
# ============================================================================


class TestRealWorldScenarios:
    """Test realistic property scenarios."""

    def test_property_with_all_soft_criteria_failures(self, sample_property):
        """Test property failing all 4 SOFT criteria.

        This is a worst-case scenario for severity accumulation.
        """
        sample_property.sewer_type = SewerType.SEPTIC  # 2.5
        sample_property.year_built = 2024  # 2.0
        sample_property.garage_spaces = 1  # 1.5
        sample_property.lot_sqft = 6500  # 1.0
        # Total: 2.5 + 2.0 + 1.5 + 1.0 = 7.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 7.0
        assert len(failures) == 4

    def test_property_with_hard_fail_plus_soft_failures(self, sample_property):
        """Test that HARD failure dominates (ignores SOFT accumulation).

        If any HARD criterion fails, verdict is FAIL regardless of SOFT severity.
        """
        sample_property.hoa_fee = 100  # HARD fail
        sample_property.sewer_type = SewerType.SEPTIC  # SOFT: 2.5
        sample_property.year_built = 2024  # SOFT: 2.0

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert any("HOA" in f for f in failures)
        # HARD failures take precedence

    def test_near_threshold_property_passes(self, sample_property):
        """Test property just below fail threshold still PASSES.

        Property with 1.0 severity (lot size) = PASS.
        """
        sample_property.lot_sqft = 6500  # Just below minimum

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.PASS
        assert severity < 1.5  # Below warning
        assert len(failures) >= 1  # But has failure recorded

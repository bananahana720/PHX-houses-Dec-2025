"""Unit tests for kill switch filtering logic.

Tests all kill switch criteria individually and in combination, covering
both happy path and edge cases as defined in CLAUDE.md buyer requirements.
"""

from src.phx_home_analysis.domain.enums import SewerType, SolarStatus
from src.phx_home_analysis.services.kill_switch import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.criteria import (
    CitySewerKillSwitch,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
    MinSqftKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)
from src.phx_home_analysis.services.kill_switch.filter import KillSwitchFilter

# ============================================================================
# NoHoaKillSwitch Tests
# ============================================================================


class TestNoHoaKillSwitch:
    """Test the NO HOA kill switch criterion."""

    def test_pass_with_zero_hoa_fee(self, sample_property):
        """Test property with hoa_fee=0 passes."""
        sample_property.hoa_fee = 0
        kill_switch = NoHoaKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_pass_with_none_hoa_fee(self, sample_property):
        """Test property with hoa_fee=None passes (treated as no HOA)."""
        sample_property.hoa_fee = None
        kill_switch = NoHoaKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_fail_with_positive_hoa_fee(self, sample_property):
        """Test property with any positive HOA fee fails."""
        sample_property.hoa_fee = 100
        kill_switch = NoHoaKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_fail_with_large_hoa_fee(self, sample_property):
        """Test property with large HOA fee fails."""
        sample_property.hoa_fee = 500
        kill_switch = NoHoaKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_failure_message_with_hoa(self, sample_property):
        """Test failure message includes HOA fee amount."""
        sample_property.hoa_fee = 200
        kill_switch = NoHoaKillSwitch()
        message = kill_switch.failure_message(sample_property)
        assert "$200/month" in message
        assert "NO HOA" in message

    def test_kill_switch_name(self):
        """Test kill switch has correct name."""
        kill_switch = NoHoaKillSwitch()
        assert kill_switch.name == "no_hoa"

    def test_kill_switch_description(self):
        """Test kill switch has correct description."""
        kill_switch = NoHoaKillSwitch()
        assert "NO HOA" in kill_switch.description


# ============================================================================
# CitySewerKillSwitch Tests
# ============================================================================


class TestCitySewerKillSwitch:
    """Test the city sewer kill switch criterion."""

    def test_pass_with_city_sewer(self, sample_property):
        """Test property with city sewer passes."""
        sample_property.sewer_type = SewerType.CITY
        kill_switch = CitySewerKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_fail_with_septic(self, sample_property):
        """Test property with septic system fails."""
        sample_property.sewer_type = SewerType.SEPTIC
        kill_switch = CitySewerKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_fail_with_unknown_sewer(self, sample_property):
        """Test property with unknown sewer type fails."""
        sample_property.sewer_type = SewerType.UNKNOWN
        kill_switch = CitySewerKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_sewer(self, sample_property):
        """Test property with None sewer_type fails (cannot verify)."""
        sample_property.sewer_type = None
        kill_switch = CitySewerKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_failure_message_septic(self, sample_property):
        """Test failure message for septic system."""
        sample_property.sewer_type = SewerType.SEPTIC
        kill_switch = CitySewerKillSwitch()
        message = kill_switch.failure_message(sample_property)
        assert "Septic" in message
        assert "city sewer" in message

    def test_failure_message_unknown(self, sample_property):
        """Test failure message for unknown sewer type."""
        sample_property.sewer_type = SewerType.UNKNOWN
        kill_switch = CitySewerKillSwitch()
        message = kill_switch.failure_message(sample_property)
        assert "unknown" in message.lower()

    def test_kill_switch_name(self):
        """Test kill switch has correct name."""
        kill_switch = CitySewerKillSwitch()
        assert kill_switch.name == "city_sewer"


# ============================================================================
# MinGarageKillSwitch Tests
# ============================================================================


class TestMinGarageKillSwitch:
    """Test the minimum garage kill switch criterion."""

    def test_pass_with_two_spaces(self, sample_property):
        """Test property with exactly 2 garage spaces passes."""
        sample_property.garage_spaces = 2
        kill_switch = MinGarageKillSwitch(min_spaces=2)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_more_spaces(self, sample_property):
        """Test property with more than minimum garage spaces passes."""
        sample_property.garage_spaces = 3
        kill_switch = MinGarageKillSwitch(min_spaces=2)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_one_space(self, sample_property):
        """Test property with only 1 garage space fails."""
        sample_property.garage_spaces = 1
        kill_switch = MinGarageKillSwitch(min_spaces=2)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_zero_spaces(self, sample_property):
        """Test property with no garage spaces fails."""
        sample_property.garage_spaces = 0
        kill_switch = MinGarageKillSwitch(min_spaces=2)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_spaces(self, sample_property):
        """Test property with None garage_spaces fails (cannot verify)."""
        sample_property.garage_spaces = None
        kill_switch = MinGarageKillSwitch(min_spaces=2)
        assert kill_switch.check(sample_property) is False

    def test_custom_minimum(self, sample_property):
        """Test custom minimum garage requirement."""
        sample_property.garage_spaces = 3
        kill_switch = MinGarageKillSwitch(min_spaces=3)
        assert kill_switch.check(sample_property) is True

        sample_property.garage_spaces = 2
        assert kill_switch.check(sample_property) is False

    def test_failure_message(self, sample_property):
        """Test failure message includes actual garage count."""
        sample_property.garage_spaces = 0
        kill_switch = MinGarageKillSwitch(min_spaces=1, indoor_required=True)
        message = kill_switch.failure_message(sample_property)
        assert "0 garage space(s)" in message
        assert "1+ indoor garage" in message


# ============================================================================
# MinBedroomsKillSwitch Tests
# ============================================================================


class TestMinBedroomsKillSwitch:
    """Test the minimum bedrooms kill switch criterion."""

    def test_pass_with_four_beds(self, sample_property):
        """Test property with exactly 4 bedrooms passes."""
        sample_property.beds = 4
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_more_beds(self, sample_property):
        """Test property with more than 4 bedrooms passes."""
        sample_property.beds = 5
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_three_beds(self, sample_property):
        """Test property with 3 bedrooms fails."""
        sample_property.beds = 3
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_one_bed(self, sample_property):
        """Test property with 1 bedroom fails."""
        sample_property.beds = 1
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_beds(self, sample_property):
        """Test property with None beds fails (cannot verify)."""
        sample_property.beds = None
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        assert kill_switch.check(sample_property) is False

    def test_custom_minimum(self, sample_property):
        """Test custom minimum bedroom requirement."""
        sample_property.beds = 3
        kill_switch = MinBedroomsKillSwitch(min_beds=3)
        assert kill_switch.check(sample_property) is True

    def test_failure_message(self, sample_property):
        """Test failure message includes actual bedroom count."""
        sample_property.beds = 3
        kill_switch = MinBedroomsKillSwitch(min_beds=4)
        message = kill_switch.failure_message(sample_property)
        assert "3 bedrooms" in message
        assert "4+" in message


# ============================================================================
# MinBathroomsKillSwitch Tests
# ============================================================================


class TestMinBathroomsKillSwitch:
    """Test the minimum bathrooms kill switch criterion."""

    def test_pass_with_two_baths(self, sample_property):
        """Test property with exactly 2 bathrooms passes."""
        sample_property.baths = 2.0
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_fractional_baths(self, sample_property):
        """Test property with 2.5 bathrooms passes."""
        sample_property.baths = 2.5
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_more_baths(self, sample_property):
        """Test property with 3 bathrooms passes."""
        sample_property.baths = 3.0
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_one_bath(self, sample_property):
        """Test property with 1 bathroom fails."""
        sample_property.baths = 1.0
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_one_half_bath(self, sample_property):
        """Test property with 1.5 bathrooms fails."""
        sample_property.baths = 1.5
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_baths(self, sample_property):
        """Test property with None baths fails (cannot verify)."""
        sample_property.baths = None
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        assert kill_switch.check(sample_property) is False

    def test_custom_minimum(self, sample_property):
        """Test custom minimum bathroom requirement."""
        sample_property.baths = 2.5
        kill_switch = MinBathroomsKillSwitch(min_baths=2.5)
        assert kill_switch.check(sample_property) is True

    def test_failure_message(self, sample_property):
        """Test failure message includes actual bathroom count."""
        sample_property.baths = 1.5
        kill_switch = MinBathroomsKillSwitch(min_baths=2.0)
        message = kill_switch.failure_message(sample_property)
        assert "1.5 bathrooms" in message


# ============================================================================
# LotSizeKillSwitch Tests
# ============================================================================


class TestLotSizeKillSwitch:
    """Test the lot size kill switch criterion."""

    def test_pass_with_minimum_lot(self, sample_property):
        """Test property with exactly 8001 sqft (above minimum) passes."""
        sample_property.lot_sqft = 8001
        kill_switch = LotSizeKillSwitch(min_sqft=8000)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_maximum_lot(self, sample_property):
        """Test property with exactly 15000 sqft (maximum) passes."""
        sample_property.lot_sqft = 15000
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_middle_lot(self, sample_property):
        """Test property with lot size between min and max passes."""
        sample_property.lot_sqft = 9500
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_exact_minimum_lot(self, sample_property):
        """Test property with exactly 7000 sqft (minimum boundary) passes."""
        sample_property.lot_sqft = 7000
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_lot_too_small(self, sample_property):
        """Test property with lot size below 7000 fails."""
        sample_property.lot_sqft = 6999
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_lot_too_large(self, sample_property):
        """Test property with lot size above 15000 fails."""
        sample_property.lot_sqft = 15001
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_very_small_lot(self, sample_property):
        """Test property with very small lot fails."""
        sample_property.lot_sqft = 3000
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_very_large_lot(self, sample_property):
        """Test property with very large lot fails."""
        sample_property.lot_sqft = 25000
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_lot(self, sample_property):
        """Test property with None lot_sqft fails (cannot verify)."""
        sample_property.lot_sqft = None
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        assert kill_switch.check(sample_property) is False

    def test_failure_message_too_small(self, sample_property):
        """Test failure message for lot too small."""
        sample_property.lot_sqft = 6500
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        message = kill_switch.failure_message(sample_property)
        assert "too small" in message.lower()
        assert "6,500" in message

    def test_failure_message_too_large(self, sample_property):
        """Test failure message for lot too large."""
        sample_property.lot_sqft = 20000
        kill_switch = LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)
        message = kill_switch.failure_message(sample_property)
        assert "too large" in message.lower()
        assert "20,000" in message

    def test_custom_lot_size_range(self, sample_property):
        """Test custom lot size with max range."""
        # With custom range specified
        kill_switch = LotSizeKillSwitch(min_sqft=5000, max_sqft=10000)

        sample_property.lot_sqft = 5001
        assert kill_switch.check(sample_property) is True

        sample_property.lot_sqft = 10000
        assert kill_switch.check(sample_property) is True

        sample_property.lot_sqft = 4999
        assert kill_switch.check(sample_property) is False

        sample_property.lot_sqft = 10001
        assert kill_switch.check(sample_property) is False

        # With default range (7000-15000)
        kill_switch_default = LotSizeKillSwitch()
        sample_property.lot_sqft = 8001
        assert kill_switch_default.check(sample_property) is True

        sample_property.lot_sqft = 6999  # Below min
        assert kill_switch_default.check(sample_property) is False

        sample_property.lot_sqft = 15001  # Above max
        assert kill_switch_default.check(sample_property) is False


# ============================================================================
# NoNewBuildKillSwitch Tests
# ============================================================================


class TestNoNewBuildKillSwitch:
    """Test the no new build kill switch criterion."""

    def test_pass_with_2023_build(self, sample_property):
        """Test property built in 2023 passes."""
        sample_property.year_built = 2023
        kill_switch = NoNewBuildKillSwitch(max_year=2023)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_older_build(self, sample_property):
        """Test property built before 2023 passes."""
        sample_property.year_built = 2010
        kill_switch = NoNewBuildKillSwitch(max_year=2023)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_very_old_build(self, sample_property):
        """Test old property built in 1980 passes."""
        sample_property.year_built = 1980
        kill_switch = NoNewBuildKillSwitch(max_year=2023)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_current_year_build(self, sample_property):
        """Test property built in current year fails."""
        from datetime import datetime

        sample_property.year_built = datetime.now().year
        kill_switch = NoNewBuildKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_fail_with_future_build(self, sample_property):
        """Test property built in future year fails."""
        from datetime import datetime

        sample_property.year_built = datetime.now().year + 1
        kill_switch = NoNewBuildKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_year(self, sample_property):
        """Test property with None year_built fails (cannot verify)."""
        sample_property.year_built = None
        kill_switch = NoNewBuildKillSwitch(max_year=2023)
        assert kill_switch.check(sample_property) is False

    def test_failure_message_new_build(self, sample_property):
        """Test failure message for new build."""
        from datetime import datetime

        current_year = datetime.now().year
        sample_property.year_built = current_year
        kill_switch = NoNewBuildKillSwitch()
        message = kill_switch.failure_message(sample_property)
        assert str(current_year) in message
        assert str(current_year - 1) in message or "earlier" in message

    def test_custom_year_threshold(self, sample_property):
        """Test custom year threshold."""
        kill_switch = NoNewBuildKillSwitch(max_year=2020)

        sample_property.year_built = 2020
        assert kill_switch.check(sample_property) is True

        sample_property.year_built = 2021
        assert kill_switch.check(sample_property) is False


# ============================================================================
# KillSwitchFilter Integration Tests
# ============================================================================


class TestKillSwitchFilter:
    """Test the integrated KillSwitchFilter that applies all criteria."""

    def test_all_pass_with_good_property(self, sample_property):
        """Test property that passes all kill switches."""
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])

        assert len(passed) == 1
        assert len(failed) == 0
        assert passed[0].kill_switch_passed is True
        assert passed[0].kill_switch_failures == []

    def test_fail_with_hoa(self, sample_failed_property):
        """Test property that fails on HOA."""
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_failed_property])

        assert len(passed) == 0
        assert len(failed) == 1
        assert failed[0].kill_switch_passed is False
        assert any("HOA" in msg for msg in failed[0].kill_switch_failures)

    def test_fail_with_septic(self, sample_septic_property):
        """Test property with septic contributes severity (SOFT criterion as of BLUE Phase).

        City sewer is now a SOFT criterion with severity 2.5.
        Septic alone (2.5) >= WARNING threshold (1.5) results in WARNING (not FAIL).
        WARNING still passes the filter for backward compatibility.
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_septic_property])

        # Septic is now a SOFT criterion = WARNING (severity 2.5)
        # WARNING passes the filter (backward compatibility)
        assert len(passed) == 1
        assert len(failed) == 0
        assert any("Septic" in msg or "sewer" in msg for msg in passed[0].kill_switch_failures)

    def test_multiple_properties_mixed(self, sample_properties):
        """Test filtering multiple properties with mixed results."""
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)

        # Expect mixed results
        assert len(passed) > 0
        assert len(failed) > 0
        assert len(passed) + len(failed) == len(sample_properties)

    def test_filter_maintains_property_order(self, sample_properties):
        """Test that filter maintains property references."""
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)

        # All original properties should appear in either passed or failed
        original_addresses = {p.full_address for p in sample_properties}
        filtered_addresses = {p.full_address for p in passed + failed}
        assert original_addresses == filtered_addresses

    def test_custom_kill_switches(self, sample_property):
        """Test filter with custom kill switches."""
        custom_switches = [
            NoHoaKillSwitch(),
            MinBedroomsKillSwitch(min_beds=3),  # Relaxed requirement
        ]
        filter_service = KillSwitchFilter(kill_switches=custom_switches)
        passed, failed = filter_service.filter_properties([sample_property])

        assert len(passed) == 1
        assert len(failed) == 0

    def test_default_kill_switches_count(self):
        """Test that default filter has all 9 kill switches (5 HARD + 4 SOFT as of BLUE Phase)."""
        filter_service = KillSwitchFilter()
        assert len(filter_service.get_kill_switch_names()) == 9

    def test_default_kill_switch_names(self):
        """Test that all expected kill switch names are present."""
        filter_service = KillSwitchFilter()
        names = filter_service.get_kill_switch_names()

        expected_names = {
            "no_hoa",
            "no_solar_lease",
            "min_bedrooms",
            "min_bathrooms",
            "min_sqft",
            # SOFT criteria (added in BLUE Phase)
            "city_sewer",
            "no_new_build",
            "min_garage",
            "lot_size",
        }
        assert set(names) == expected_names

    def test_evaluate_single_property(self, sample_property):
        """Test evaluating a single property."""
        filter_service = KillSwitchFilter()
        passed, failures = filter_service.evaluate(sample_property)

        assert passed is True
        assert failures == []

    def test_evaluate_failing_property(self, sample_failed_property):
        """Test evaluating property that fails."""
        filter_service = KillSwitchFilter()
        passed, failures = filter_service.evaluate(sample_failed_property)

        assert passed is False
        assert len(failures) > 0

    def test_multiple_kill_switch_failures(self, sample_property):
        """Test property that fails multiple kill switches."""
        # Create property that fails both HOA and lot size
        sample_property.hoa_fee = 150
        sample_property.lot_sqft = 5000  # Too small

        filter_service = KillSwitchFilter()
        passed, failures = filter_service.evaluate(sample_property)

        assert passed is False
        assert len(failures) >= 2  # At least HOA and lot size

    def test_failure_messages_are_descriptive(self, sample_failed_property):
        """Test that failure messages are descriptive."""
        filter_service = KillSwitchFilter()
        passed, failures = filter_service.evaluate(sample_failed_property)

        assert all(len(msg) > 10 for msg in failures)  # Messages are descriptive


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestKillSwitchEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_lot_size_boundary_below(self, sample_property):
        """Test lot size exactly 1 sqft below minimum.

        Lot size is now a SOFT criterion (min 7000 sqft) - contributes severity 1.0.
        Below minimum (1.0 severity) < WARNING threshold (1.5) = PASS.
        """
        sample_property.lot_sqft = 6999
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        # Lot size is SOFT (1.0 severity) < WARNING threshold (1.5) = PASS
        assert len(passed) == 1
        assert len(failed) == 0
        assert any("lot" in msg.lower() for msg in passed[0].kill_switch_failures)

    def test_lot_size_boundary_above(self, sample_property):
        """Test lot size exactly 1 sqft above maximum.

        Lot size is a SOFT criterion (severity 1.0), so a single failure
        results in PASS (1.0 < 1.5 WARNING threshold).
        """
        sample_property.lot_sqft = 15001
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        # Lot size alone (1.0) is below WARNING threshold (1.5) = PASS
        assert len(passed) == 1
        assert len(failed) == 0

    def test_year_built_boundary_below(self, sample_property):
        """Test year built exactly at threshold (2023)."""
        sample_property.year_built = 2023
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(passed) == 1

    def test_year_built_boundary_above(self, sample_property):
        """Test year built exactly above threshold (2024).

        Year built is a SOFT criterion (severity 2.0), so a single failure
        results in WARNING (2.0 >= 1.5 but < 3.0 FAIL threshold).
        """
        sample_property.year_built = 2024
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        # Year built alone (2.0) is WARNING, not FAIL
        assert len(passed) == 1
        assert len(failed) == 0

    def test_garage_spaces_boundary(self, sample_property):
        """Test garage spaces at exact threshold."""
        sample_property.garage_spaces = 2
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(passed) == 1

        # Garage is a SOFT criterion (severity 1.5), so a single failure
        # results in WARNING (1.5 = WARNING threshold, < 3.0 FAIL threshold)
        sample_property.garage_spaces = 1
        passed, failed = filter_service.filter_properties([sample_property])
        # WARNING passes, not FAIL
        assert len(passed) == 1
        assert len(failed) == 0

    def test_bedrooms_boundary(self, sample_property):
        """Test bedrooms at exact threshold."""
        sample_property.beds = 4
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(passed) == 1

        sample_property.beds = 3
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(failed) == 1

    def test_bathrooms_boundary(self, sample_property):
        """Test bathrooms at exact threshold."""
        sample_property.baths = 2.0
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(passed) == 1

        sample_property.baths = 1.9
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(failed) == 1

    def test_hoa_fee_boundary(self, sample_property):
        """Test HOA fee exactly at boundary (0)."""
        sample_property.hoa_fee = 0
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(passed) == 1

        sample_property.hoa_fee = 1
        passed, failed = filter_service.filter_properties([sample_property])
        assert len(failed) == 1


# ============================================================================
# Severity Threshold Tests (Wave 1.1)
# ============================================================================


class TestSeverityThresholdOOP:
    """Test the OOP implementation of severity threshold system."""

    def test_evaluate_with_severity_returns_verdict(self, sample_property):
        """evaluate_with_severity should return verdict, severity, and failures."""
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)
        assert isinstance(verdict, KillSwitchVerdict)
        assert isinstance(severity, float)
        assert isinstance(failures, list)

    def test_perfect_property_passes(self, sample_property):
        """Property passing all criteria should have PASS verdict."""
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)
        assert verdict == KillSwitchVerdict.PASS
        assert severity == 0.0
        assert len(failures) == 0

    def test_septic_is_soft_fail(self, sample_septic_property):
        """Septic now results in SOFT FAIL (BLUE Phase change).

        City sewer is a SOFT criterion with severity 2.5.
        Single SOFT failure (2.5) >= WARNING threshold (1.5) = WARNING verdict.
        """
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_septic_property)
        # Septic severity (2.5) >= WARNING threshold (1.5) = WARNING
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert len(failures) == 1
        assert any("Septic" in msg or "sewer" in msg for msg in failures)

    def test_hoa_is_hard_fail(self, sample_failed_property):
        """HOA failure (HARD criterion) should result in FAIL."""
        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_failed_property)
        assert verdict == KillSwitchVerdict.FAIL
        # Severity for HARD fails doesn't contribute
        assert any("HOA" in msg for msg in failures)

    def test_soft_failures_accumulate(self, sample_property):
        """SOFT criteria accumulate severity as of BLUE Phase.

        Sewer (2.5) + Year (2.0) = 4.5 > FAIL threshold (3.0) = FAIL.
        """
        sample_property.sewer_type = SewerType.SEPTIC  # 2.5 severity
        sample_property.year_built = 2024  # 2.0 severity

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)
        # Severity accumulation: 2.5 + 2.0 = 4.5 >= FAIL threshold (3.0)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 4.5
        assert len(failures) == 2

    def test_get_hard_criteria(self):
        """get_hard_criteria should return HARD kill switches."""
        filter_service = KillSwitchFilter()
        hard = filter_service.get_hard_criteria()
        hard_names = [ks.name for ks in hard]
        assert "no_hoa" in hard_names
        assert "min_bedrooms" in hard_names
        assert "min_bathrooms" in hard_names

    def test_get_soft_criteria(self):
        """get_soft_criteria should return 4 SOFT criteria (BLUE Phase change)."""
        filter_service = KillSwitchFilter()
        soft = filter_service.get_soft_criteria()
        soft_names = [ks.name for ks in soft]

        # 4 SOFT criteria as of BLUE Phase
        assert len(soft_names) == 4
        assert "city_sewer" in soft_names
        assert "no_new_build" in soft_names
        assert "min_garage" in soft_names
        assert "lot_size" in soft_names

    def test_summary_includes_hard_and_soft_sections(self):
        """summary() should include HARD and SOFT sections."""
        filter_service = KillSwitchFilter()
        summary = filter_service.summary()
        assert "HARD" in summary
        assert "SOFT" in summary
        assert "severity" in summary.lower() or "weight" in summary.lower()


# ============================================================================
# Severity Boundary Condition Tests (Wave 3)
# ============================================================================

# Document threshold constants for clarity
WARNING_THRESHOLD = 1.5  # Severity >= 1.5 triggers WARNING
FAIL_THRESHOLD = 3.0  # Severity >= 3.0 triggers FAIL


class TestSeverityBoundaryConditions:
    """Test exact boundary conditions for severity thresholds.

    Validates that the severity thresholds (WARNING at 1.5, FAIL at 3.0)
    are applied with exact precision at boundaries.

    SOFT criteria severity weights:
    - city_sewer: 2.5 (septic or unknown)
    - no_new_build: 2.0 (year_built >= 2024)
    - min_garage: 1.5 (garage_spaces < 2)
    - lot_size: 1.0 (lot_sqft outside 7k-15k range)
    """

    def test_severity_1_49_is_pass(self, sample_property):
        """Severity 1.49 should PASS (below WARNING threshold).

        Use combination: min_garage (1.5) - 0.01 buffer
        Since we can't create exactly 1.49 with discrete weights,
        we test 1.0 (lot_size) which is < 1.5 threshold.
        """
        # Fail only lot_size (1.0 severity) - below WARNING threshold
        sample_property.lot_sqft = 6999  # Too small (severity 1.0)

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.PASS
        assert severity == 1.0
        assert len(failures) == 1

    def test_severity_1_50_is_warning(self, sample_property):
        """Severity 1.50 should be WARNING (at threshold).

        Use min_garage criterion: garage_spaces < 2 = severity 1.5
        """
        # Fail only min_garage (1.5 severity) - exactly at WARNING threshold
        sample_property.garage_spaces = 1  # Insufficient (severity 1.5)

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 1.5
        assert len(failures) == 1

    def test_severity_1_51_is_warning(self, sample_property):
        """Severity 1.51 should be WARNING (above threshold).

        Use combination: min_garage (1.5) + small fraction
        Since we can't create exactly 1.51 with discrete weights,
        we test 2.5 (lot_size 1.0 + garage 1.5) which is > 1.5 but < 3.0.
        """
        # Fail lot_size (1.0) + min_garage (1.5) = 2.5 severity
        sample_property.lot_sqft = 6999  # Too small (severity 1.0)
        sample_property.garage_spaces = 1  # Insufficient (severity 1.5)

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert len(failures) == 2

    def test_severity_2_99_is_warning(self, sample_property):
        """Severity 2.99 should be WARNING (below FAIL threshold).

        Use combination: no_new_build (2.0) + lot_size (1.0) = 3.0
        Since we can't create exactly 2.99 with discrete weights,
        we test 2.5 (city_sewer alone) which is < 3.0 threshold.
        """
        # Fail only city_sewer (2.5 severity) - below FAIL threshold
        sample_property.sewer_type = SewerType.SEPTIC  # Severity 2.5

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
        assert len(failures) == 1

    def test_severity_3_00_is_fail(self, sample_property):
        """Severity 3.00 should FAIL (at threshold).

        Use combination: no_new_build (2.0) + lot_size (1.0) = 3.0
        """
        # Fail no_new_build (2.0) + lot_size (1.0) = 3.0 severity
        sample_property.year_built = 2024  # New build (severity 2.0)
        sample_property.lot_sqft = 6999  # Too small (severity 1.0)

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 3.0
        assert len(failures) == 2

    def test_severity_3_01_is_fail(self, sample_property):
        """Severity 3.01 should FAIL (above threshold).

        Use combination: no_new_build (2.0) + min_garage (1.5) = 3.5
        """
        # Fail no_new_build (2.0) + min_garage (1.5) = 3.5 severity
        sample_property.year_built = 2024  # New build (severity 2.0)
        sample_property.garage_spaces = 1  # Insufficient (severity 1.5)

        filter_service = KillSwitchFilter()
        verdict, severity, failures = filter_service.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 3.5
        assert len(failures) == 2


# ============================================================================
# MinSqftKillSwitch Tests
# ============================================================================


class TestMinSqftKillSwitch:
    """Test the minimum square footage kill switch criterion (HARD).

    MinSqftKillSwitch is a HARD criterion requiring sqft > 1800.
    Per CLAUDE.md: sqft > 1800 is buyer requirement (instant fail).
    """

    def test_pass_with_2200_sqft(self, sample_property):
        """Test property with 2200 sqft passes (typical passing case)."""
        sample_property.sqft = 2200
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        assert kill_switch.check(sample_property) is True

    def test_pass_with_1801_sqft(self, sample_property):
        """Test property with 1801 sqft passes (just above boundary)."""
        sample_property.sqft = 1801
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        assert kill_switch.check(sample_property) is True

    def test_fail_with_1800_sqft(self, sample_property):
        """Test property with exactly 1800 sqft fails (boundary condition).

        The requirement is sqft > 1800, not sqft >= 1800.
        Exactly 1800 does NOT satisfy > 1800, so it should FAIL.
        """
        sample_property.sqft = 1800
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_zero_sqft(self, sample_property):
        """Test property with 0 sqft fails."""
        sample_property.sqft = 0
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        assert kill_switch.check(sample_property) is False

    def test_fail_with_none_sqft(self, sample_property):
        """Test property with None sqft fails (cannot verify requirement)."""
        sample_property.sqft = None
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        assert kill_switch.check(sample_property) is False

    def test_failure_message(self, sample_property):
        """Test failure message includes actual sqft."""
        sample_property.sqft = 1500
        kill_switch = MinSqftKillSwitch(min_sqft=1800)
        message = kill_switch.failure_message(sample_property)
        assert "1,500" in message
        assert "1,800" in message or "sqft" in message.lower()

    def test_kill_switch_name(self):
        """Test kill switch has correct name."""
        kill_switch = MinSqftKillSwitch()
        assert kill_switch.name == "min_sqft"

    def test_kill_switch_description(self):
        """Test kill switch has correct description."""
        kill_switch = MinSqftKillSwitch()
        assert "1,800" in kill_switch.description
        assert "sqft" in kill_switch.description.lower()

    def test_is_hard_criterion(self):
        """Test that MinSqftKillSwitch is a HARD criterion."""
        kill_switch = MinSqftKillSwitch()
        assert kill_switch.is_hard is True

    def test_custom_minimum(self, sample_property):
        """Test custom minimum sqft requirement."""
        sample_property.sqft = 2000
        kill_switch = MinSqftKillSwitch(min_sqft=2500)
        assert kill_switch.check(sample_property) is False

        sample_property.sqft = 2501
        assert kill_switch.check(sample_property) is True


# ============================================================================
# NoSolarLeaseKillSwitch Tests
# ============================================================================


class TestNoSolarLeaseKillSwitch:
    """Test the no solar lease kill switch criterion (HARD).

    NoSolarLeaseKillSwitch is a HARD criterion requiring solar != lease.
    Per CLAUDE.md: solar lease is buyer disqualifier (liability, not asset).
    """

    def test_pass_with_owned_solar(self, sample_property):
        """Test property with owned solar passes."""
        sample_property.solar_status = SolarStatus.OWNED
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_pass_with_no_solar(self, sample_property):
        """Test property with no solar panels passes."""
        sample_property.solar_status = SolarStatus.NONE
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_pass_with_none_solar_status(self, sample_property):
        """Test property with None solar_status passes (unknown = pass)."""
        sample_property.solar_status = None
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_pass_with_unknown_solar(self, sample_property):
        """Test property with unknown solar status passes.

        Unknown status does not fail - only explicit LEASED fails.
        """
        sample_property.solar_status = SolarStatus.UNKNOWN
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is True

    def test_fail_with_leased_solar(self, sample_property):
        """Test property with leased solar fails (HARD criterion)."""
        sample_property.solar_status = SolarStatus.LEASED
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_failure_message_leased(self, sample_property):
        """Test failure message for leased solar."""
        sample_property.solar_status = SolarStatus.LEASED
        kill_switch = NoSolarLeaseKillSwitch()
        message = kill_switch.failure_message(sample_property)
        assert "solar" in message.lower() or "lease" in message.lower()
        assert "$100" in message or "liability" in message.lower()

    def test_kill_switch_name(self):
        """Test kill switch has correct name."""
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.name == "no_solar_lease"

    def test_kill_switch_description(self):
        """Test kill switch has correct description."""
        kill_switch = NoSolarLeaseKillSwitch()
        assert (
            "solar" in kill_switch.description.lower() or "lease" in kill_switch.description.lower()
        )

    def test_is_hard_criterion(self):
        """Test that NoSolarLeaseKillSwitch is a HARD criterion (default)."""
        kill_switch = NoSolarLeaseKillSwitch()
        # Default is_hard returns True from base class
        assert kill_switch.is_hard is True

    def test_fail_with_leased_string(self, sample_property):
        """Test property with 'leased' string value fails."""
        # Some data sources may provide string instead of enum
        sample_property.solar_status = "leased"
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is False

    def test_pass_with_owned_string(self, sample_property):
        """Test property with 'owned' string value passes."""
        sample_property.solar_status = "owned"
        kill_switch = NoSolarLeaseKillSwitch()
        assert kill_switch.check(sample_property) is True

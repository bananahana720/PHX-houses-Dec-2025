"""Comprehensive integration tests for KillSwitchFilter.evaluate_to_result() method.

Tests the evaluate_to_result() method introduced in E3.S3 for generating
comprehensive KillSwitchResult objects from property evaluation.

Test Coverage:
- Passing property -> PASS verdict, empty failed_criteria
- HARD failure -> FAIL verdict with HARD criterion in failed_criteria
- SOFT threshold exceeded (>=3.0) -> FAIL verdict
- WARNING threshold (1.5-3.0) -> WARNING verdict
- property_address populated correctly
- timestamp is recent (within 1 second)
- Multiple failures tracked correctly
- Mixed HARD + SOFT failures
"""

from datetime import datetime

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import Orientation, SewerType, SolarStatus
from src.phx_home_analysis.services.kill_switch.base import KillSwitchVerdict
from src.phx_home_analysis.services.kill_switch.filter import KillSwitchFilter

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def filter_service():
    """Create KillSwitchFilter with default criteria."""
    return KillSwitchFilter()


@pytest.fixture
def passing_property():
    """Create a property that passes all kill-switch criteria.

    - 4 bedrooms (HARD: >= 4) PASS
    - 2 bathrooms (HARD: >= 2) PASS
    - 2200 sqft (HARD: > 1800) PASS
    - HOA $0 (HARD: = 0) PASS
    - No solar lease (HARD: != lease) PASS
    - City sewer (SOFT: 2.5 if not city) PASS
    - Year 2010 (SOFT: 2.0 if > 2023) PASS
    - 2 garage spaces (SOFT: 1.5 if < 2) PASS
    - 9500 sqft lot (SOFT: 1.0 if < 7000 or > 15000) PASS
    """
    return Property(
        street="123 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Main St, Phoenix, AZ 85001",
        price="$500,000",
        price_num=500000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=227.3,
        lot_sqft=9500,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        solar_status=SolarStatus.NONE,
        orientation=Orientation.N,
    )


@pytest.fixture
def hard_failure_property():
    """Create a property that fails a HARD criterion (HOA).

    - HOA $200 (HARD: = 0) FAIL
    """
    return Property(
        street="456 Oak Ave",
        city="Phoenix",
        state="AZ",
        zip_code="85002",
        full_address="456 Oak Ave, Phoenix, AZ 85002",
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=204.5,
        lot_sqft=9500,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=200,  # HARD FAIL
        solar_status=SolarStatus.NONE,
        orientation=Orientation.N,
    )


@pytest.fixture
def soft_threshold_exceeded_property():
    """Create a property that exceeds SOFT severity threshold (>=3.0).

    - Septic sewer (SOFT: 2.5) FAIL
    - Small lot 5000 sqft (SOFT: 1.0) FAIL
    - Total severity: 3.5 >= 3.0 -> FAIL
    """
    return Property(
        street="789 Elm St",
        city="Phoenix",
        state="AZ",
        zip_code="85003",
        full_address="789 Elm St, Phoenix, AZ 85003",
        price="$400,000",
        price_num=400000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=181.8,
        lot_sqft=5000,  # SOFT 1.0
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.SEPTIC,  # SOFT 2.5
        hoa_fee=0,
        solar_status=SolarStatus.NONE,
        orientation=Orientation.N,
    )


@pytest.fixture
def warning_property():
    """Create a property with WARNING severity (1.5 <= severity < 3.0).

    - Septic sewer (SOFT: 2.5) FAIL
    - Total severity: 2.5 -> WARNING
    """
    return Property(
        street="321 Pine Rd",
        city="Phoenix",
        state="AZ",
        zip_code="85004",
        full_address="321 Pine Rd, Phoenix, AZ 85004",
        price="$480,000",
        price_num=480000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=218.2,
        lot_sqft=10000,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.SEPTIC,  # SOFT 2.5
        hoa_fee=0,
        solar_status=SolarStatus.NONE,
        orientation=Orientation.N,
    )


# ============================================================================
# PASS Verdict Tests
# ============================================================================


class TestEvaluateToResultPass:
    """Test evaluate_to_result() for properties that PASS."""

    def test_passing_property_returns_pass_verdict(self, filter_service, passing_property):
        """Test that a passing property gets PASS verdict."""
        result = filter_service.evaluate_to_result(passing_property)

        assert result.verdict == KillSwitchVerdict.PASS
        assert result.is_passing is True

    def test_passing_property_has_empty_failed_criteria(self, filter_service, passing_property):
        """Test that a passing property has no failed criteria."""
        result = filter_service.evaluate_to_result(passing_property)

        assert result.failed_criteria == []
        assert len(result.hard_failures) == 0
        assert len(result.soft_failures) == 0

    def test_passing_property_has_zero_severity(self, filter_service, passing_property):
        """Test that a passing property has zero severity score."""
        result = filter_service.evaluate_to_result(passing_property)

        assert result.severity_score == 0.0


# ============================================================================
# FAIL Verdict Tests - HARD Criteria
# ============================================================================


class TestEvaluateToResultHardFail:
    """Test evaluate_to_result() for HARD criterion failures."""

    def test_hard_failure_returns_fail_verdict(self, filter_service, hard_failure_property):
        """Test that a HARD failure gets FAIL verdict."""
        result = filter_service.evaluate_to_result(hard_failure_property)

        assert result.verdict == KillSwitchVerdict.FAIL
        assert result.is_passing is False

    def test_hard_failure_has_hard_criterion_in_failed_criteria(
        self, filter_service, hard_failure_property
    ):
        """Test that HARD failure is in failed_criteria."""
        result = filter_service.evaluate_to_result(hard_failure_property)

        assert len(result.hard_failures) >= 1
        # Should have no_hoa failure
        hard_names = [fc.name for fc in result.hard_failures]
        assert "no_hoa" in hard_names

    def test_hard_failure_criterion_has_correct_metadata(
        self, filter_service, hard_failure_property
    ):
        """Test that HARD failure criterion has correct metadata."""
        result = filter_service.evaluate_to_result(hard_failure_property)

        hoa_failures = [fc for fc in result.hard_failures if fc.name == "no_hoa"]
        assert len(hoa_failures) == 1
        hoa_fail = hoa_failures[0]

        assert hoa_fail.is_hard is True
        assert hoa_fail.severity == 0.0  # HARD criteria have 0 severity
        assert hoa_fail.actual_value == 200
        assert "$0" in hoa_fail.required_value


# ============================================================================
# FAIL Verdict Tests - SOFT Threshold Exceeded
# ============================================================================


class TestEvaluateToResultSoftThresholdExceeded:
    """Test evaluate_to_result() for SOFT threshold exceeded failures."""

    def test_soft_threshold_exceeded_returns_fail_verdict(
        self, filter_service, soft_threshold_exceeded_property
    ):
        """Test that SOFT threshold exceeded (>=3.0) gets FAIL verdict."""
        result = filter_service.evaluate_to_result(soft_threshold_exceeded_property)

        assert result.verdict == KillSwitchVerdict.FAIL
        assert result.is_passing is False

    def test_soft_threshold_exceeded_has_multiple_soft_failures(
        self, filter_service, soft_threshold_exceeded_property
    ):
        """Test that multiple SOFT failures are tracked."""
        result = filter_service.evaluate_to_result(soft_threshold_exceeded_property)

        assert len(result.soft_failures) >= 2
        soft_names = [fc.name for fc in result.soft_failures]
        assert "city_sewer" in soft_names
        assert "lot_size" in soft_names

    def test_soft_threshold_exceeded_severity_calculated_correctly(
        self, filter_service, soft_threshold_exceeded_property
    ):
        """Test that severity is sum of SOFT criterion weights."""
        result = filter_service.evaluate_to_result(soft_threshold_exceeded_property)

        # city_sewer = 2.5, lot_size = 1.0, total = 3.5
        assert result.severity_score >= 3.0


# ============================================================================
# WARNING Verdict Tests
# ============================================================================


class TestEvaluateToResultWarning:
    """Test evaluate_to_result() for WARNING verdicts (1.5 <= severity < 3.0)."""

    def test_warning_property_returns_warning_verdict(self, filter_service, warning_property):
        """Test that WARNING severity gets WARNING verdict."""
        result = filter_service.evaluate_to_result(warning_property)

        assert result.verdict == KillSwitchVerdict.WARNING
        assert result.is_passing is True  # WARNING is still passing

    def test_warning_property_has_soft_failures(self, filter_service, warning_property):
        """Test that WARNING property has SOFT failures."""
        result = filter_service.evaluate_to_result(warning_property)

        assert len(result.soft_failures) >= 1
        assert len(result.hard_failures) == 0

    def test_warning_property_severity_in_warning_range(self, filter_service, warning_property):
        """Test that WARNING severity is in range [1.5, 3.0)."""
        result = filter_service.evaluate_to_result(warning_property)

        assert 1.5 <= result.severity_score < 3.0


# ============================================================================
# Property Address Tests
# ============================================================================


class TestEvaluateToResultPropertyAddress:
    """Test that property_address is populated correctly."""

    def test_property_address_populated_from_address_attribute(
        self, filter_service, passing_property
    ):
        """Test property_address comes from property.address."""
        result = filter_service.evaluate_to_result(passing_property)

        # Property.address should map to result.property_address
        assert result.property_address is not None
        # property_address should be a string
        assert isinstance(result.property_address, str)

    def test_property_address_populated_correctly(self, filter_service, passing_property):
        """Test property_address matches property address."""
        result = filter_service.evaluate_to_result(passing_property)

        # Should contain the address (as string)
        expected = str(passing_property.address) if passing_property.address else ""
        assert result.property_address == expected


# ============================================================================
# Timestamp Tests
# ============================================================================


class TestEvaluateToResultTimestamp:
    """Test that timestamp is recent and correct."""

    def test_timestamp_is_recent(self, filter_service, passing_property):
        """Test that timestamp is within 2 seconds of now."""
        # evaluate_to_result now uses datetime.now(timezone.utc) for consistency
        from datetime import timezone

        before = datetime.now(timezone.utc)
        result = filter_service.evaluate_to_result(passing_property)
        after = datetime.now(timezone.utc)

        result_ts = result.timestamp

        # Check that timestamp is within the expected range
        # Allow some tolerance for execution time
        assert before <= result_ts <= after, (
            f"Timestamp {result_ts} not in range [{before}, {after}]"
        )

    def test_timestamp_is_datetime_type(self, filter_service, passing_property):
        """Test that timestamp is a datetime object."""
        result = filter_service.evaluate_to_result(passing_property)

        assert isinstance(result.timestamp, datetime)


# ============================================================================
# Multiple Failures Tests
# ============================================================================


class TestEvaluateToResultMultipleFailures:
    """Test tracking of multiple failures."""

    def test_multiple_hard_failures_tracked(self, filter_service):
        """Test that multiple HARD failures are all tracked."""
        # Property with multiple HARD failures: low beds AND low baths
        property_multi_hard = Property(
            street="999 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="999 Test St, Phoenix, AZ 85001",
            price="$300,000",
            price_num=300000,
            beds=2,  # HARD FAIL: needs >= 4
            baths=1.0,  # HARD FAIL: needs >= 2
            sqft=2200,
            price_per_sqft_raw=136.4,
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type=SewerType.CITY,
            hoa_fee=0,
            solar_status=SolarStatus.NONE,
            orientation=Orientation.N,
        )

        result = filter_service.evaluate_to_result(property_multi_hard)

        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.hard_failures) >= 2
        hard_names = [fc.name for fc in result.hard_failures]
        assert "min_bedrooms" in hard_names
        assert "min_bathrooms" in hard_names

    def test_multiple_soft_failures_accumulated(self, filter_service):
        """Test that multiple SOFT failures accumulate severity."""
        # Property with multiple SOFT failures: septic + small lot + no garage
        property_multi_soft = Property(
            street="888 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="888 Test St, Phoenix, AZ 85001",
            price="$350,000",
            price_num=350000,
            beds=4,
            baths=2.0,
            sqft=2200,
            price_per_sqft_raw=159.1,
            lot_sqft=5000,  # SOFT 1.0: < 7000
            year_built=2010,
            garage_spaces=0,  # SOFT 1.5: < 2
            sewer_type=SewerType.SEPTIC,  # SOFT 2.5
            hoa_fee=0,
            solar_status=SolarStatus.NONE,
            orientation=Orientation.N,
        )

        result = filter_service.evaluate_to_result(property_multi_soft)

        # Total severity: 1.0 + 1.5 + 2.5 = 5.0 >= 3.0 -> FAIL
        assert result.verdict == KillSwitchVerdict.FAIL
        assert result.severity_score >= 3.0
        assert len(result.soft_failures) >= 3

    def test_mixed_hard_and_soft_failures(self, filter_service):
        """Test that mixed HARD and SOFT failures are both tracked."""
        property_mixed = Property(
            street="777 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="777 Test St, Phoenix, AZ 85001",
            price="$400,000",
            price_num=400000,
            beds=3,  # HARD FAIL: needs >= 4
            baths=2.0,
            sqft=2200,
            price_per_sqft_raw=181.8,
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type=SewerType.SEPTIC,  # SOFT 2.5
            hoa_fee=0,
            solar_status=SolarStatus.NONE,
            orientation=Orientation.N,
        )

        result = filter_service.evaluate_to_result(property_mixed)

        assert result.verdict == KillSwitchVerdict.FAIL
        assert len(result.hard_failures) >= 1
        assert len(result.soft_failures) >= 1


# ============================================================================
# Result Serialization Tests
# ============================================================================


class TestEvaluateToResultSerialization:
    """Test that results can be serialized."""

    def test_to_dict_returns_valid_dict(self, filter_service, passing_property):
        """Test that to_dict() returns a valid dictionary."""
        result = filter_service.evaluate_to_result(passing_property)
        d = result.to_dict()

        assert isinstance(d, dict)
        assert "verdict" in d
        assert "failed_criteria" in d
        assert "severity_score" in d
        assert "timestamp" in d
        assert "property_address" in d
        assert "is_passing" in d

    def test_to_dict_verdict_is_string(self, filter_service, passing_property):
        """Test that verdict in to_dict is a string."""
        result = filter_service.evaluate_to_result(passing_property)
        d = result.to_dict()

        assert isinstance(d["verdict"], str)
        assert d["verdict"] in ["PASS", "WARNING", "FAIL"]

    def test_to_dict_failed_criteria_are_dicts(self, filter_service, hard_failure_property):
        """Test that failed_criteria in to_dict are dictionaries."""
        result = filter_service.evaluate_to_result(hard_failure_property)
        d = result.to_dict()

        assert isinstance(d["failed_criteria"], list)
        for fc in d["failed_criteria"]:
            assert isinstance(fc, dict)
            assert "name" in fc
            assert "actual_value" in fc
            assert "required_value" in fc
            assert "is_hard" in fc
            assert "severity" in fc

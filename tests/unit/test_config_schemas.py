"""Unit tests for configuration schema validation.

Tests cover:
- Schema validation for scoring_weights.yaml structure
- Schema validation for buyer_criteria.yaml structure
- Field constraints (min/max values, required fields)
- Cross-field validation (totals, ordering, thresholds)
- Error message quality
"""

import pytest
from pydantic import ValidationError

from phx_home_analysis.validation.config_schemas import (
    AppConfigSchema,
    BuyerCriteriaConfigSchema,
    ConfigurationError,
    HardCriteriaSchema,
    LocationCriteriaSchema,
    LotSizeCriterionSchema,
    ScoringWeightsConfigSchema,
    SectionWeightsSchema,
    SewerCriterionSchema,
    ThresholdsSchema,
    TierThresholdsSchema,
    ValueZoneSchema,
    ValueZonesSchema,
    YearBuiltCriterionSchema,
)

# =============================================================================
# FIXTURES - Valid Configuration Data
# =============================================================================


@pytest.fixture
def valid_value_zone():
    """Valid value zone data."""
    return {
        "min_score": 365,
        "max_price": 550000,
        "label": "Value Sweet Spot",
        "description": "High-quality properties at affordable prices",
    }


@pytest.fixture
def valid_value_zones():
    """Valid value zones configuration."""
    return {
        "sweet_spot": {
            "min_score": 365,
            "max_price": 550000,
            "label": "Value Sweet Spot",
            "description": "High-quality properties at affordable prices",
        },
        "premium": {
            "min_score": 480,
            "max_price": None,
            "label": "Unicorn Territory",
            "description": "Top-tier properties",
        },
    }


@pytest.fixture
def valid_location_criteria():
    """Valid location criteria weights (Sprint 0: 9 fields, 250pts total)."""
    return {
        "school": 42,
        "quietness": 30,
        "crime_index": 47,  # Replaces "safety"
        "supermarket": 23,
        "parks": 23,
        "sun_orientation": 25,
        "flood_risk": 23,  # NEW
        "walk_transit": 22,  # NEW
        "air_quality": 15,  # NEW
    }


@pytest.fixture
def valid_systems_criteria():
    """Valid systems criteria weights (Sprint 0: 6 fields, 175pts total)."""
    return {
        "roof": 45,
        "backyard": 35,
        "plumbing": 35,
        "pool": 20,
        "cost_efficiency": 35,
        "solar_status": 5,  # NEW
    }


@pytest.fixture
def valid_interior_criteria():
    """Valid interior criteria weights (Sprint 0: 7 fields, 180pts total)."""
    return {
        "kitchen": 40,
        "master_bedroom": 35,  # Reduced from 40
        "light": 30,
        "ceilings": 25,  # Reduced from 30
        "fireplace": 20,
        "laundry": 20,
        "aesthetics": 10,
    }


@pytest.fixture
def valid_section_weights(
    valid_location_criteria, valid_systems_criteria, valid_interior_criteria
):
    """Valid section weights with correct totals (605 pts, 1.0 weight) - Sprint 0."""
    return {
        "location": {
            "points": 250,
            "weight": 0.4132,
            "criteria": valid_location_criteria,
        },
        "systems": {
            "points": 175,
            "weight": 0.2893,
            "criteria": valid_systems_criteria,
        },
        "interior": {
            "points": 180,
            "weight": 0.2975,
            "criteria": valid_interior_criteria,
        },
    }


@pytest.fixture
def valid_tier_thresholds():
    """Valid tier thresholds configuration (Sprint 0: 605pt system)."""
    return {
        "unicorn": {
            "min_score": 484,  # 80% of 605
            "label": "Unicorn",
            "description": "Exceptional properties",
        },
        "contender": {
            "min_score": 363,  # 60% of 605
            "label": "Contender",
            "description": "Strong properties",
        },
        "pass": {
            "min_score": 0,
            "label": "Pass",
            "description": "Acceptable properties",
        },
    }


@pytest.fixture
def valid_scoring_weights(valid_value_zones, valid_section_weights, valid_tier_thresholds):
    """Valid complete scoring weights configuration."""
    return {
        "value_zones": valid_value_zones,
        "section_weights": valid_section_weights,
        "tier_thresholds": valid_tier_thresholds,
    }


@pytest.fixture
def valid_hard_criteria():
    """Valid hard criteria configuration (Sprint 0: 8 HARD fields)."""
    return {
        "hoa_fee": 0,
        "min_beds": 4,
        "min_baths": 2,
        "min_sqft": 1800,  # NEW
        "min_lot_sqft": 8000,  # NEW
        "sewer_type": "city",  # NEW
        "min_garage": 1,  # NEW
        "solar_lease": False,  # NEW
    }


@pytest.fixture
def valid_soft_criteria():
    """Valid soft criteria configuration."""
    return {
        "sewer_type": {"required": "city", "severity": 2.5},
        "year_built": {"max": "current_year", "severity": 2.0},
        "garage_spaces": {"min": 2, "severity": 1.5},
        "lot_sqft": {"min": 7000, "max": 15000, "severity": 1.0},
    }


@pytest.fixture
def valid_thresholds():
    """Valid severity thresholds."""
    return {
        "severity_fail": 3.0,
        "severity_warning": 1.5,
    }


@pytest.fixture
def valid_buyer_criteria(valid_hard_criteria, valid_soft_criteria, valid_thresholds):
    """Valid complete buyer criteria configuration."""
    return {
        "hard_criteria": valid_hard_criteria,
        "soft_criteria": valid_soft_criteria,
        "thresholds": valid_thresholds,
    }


# =============================================================================
# VALUE ZONE SCHEMA TESTS
# =============================================================================


class TestValueZoneSchema:
    """Tests for ValueZoneSchema validation."""

    def test_valid_value_zone(self, valid_value_zone):
        """Test that valid value zone passes validation."""
        schema = ValueZoneSchema(**valid_value_zone)
        assert schema.min_score == 365
        assert schema.max_price == 550000
        assert schema.label == "Value Sweet Spot"

    def test_value_zone_null_max_price(self, valid_value_zone):
        """Test that None is allowed for max_price."""
        valid_value_zone["max_price"] = None
        schema = ValueZoneSchema(**valid_value_zone)
        assert schema.max_price is None

    def test_value_zone_min_score_negative(self, valid_value_zone):
        """Test that negative min_score is rejected."""
        valid_value_zone["min_score"] = -1
        with pytest.raises(ValidationError) as exc_info:
            ValueZoneSchema(**valid_value_zone)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_value_zone_min_score_over_605(self, valid_value_zone):
        """Test that min_score > 605 is rejected."""
        valid_value_zone["min_score"] = 606
        with pytest.raises(ValidationError) as exc_info:
            ValueZoneSchema(**valid_value_zone)
        assert "less than or equal to 605" in str(exc_info.value)

    def test_value_zone_empty_label(self, valid_value_zone):
        """Test that empty label is rejected."""
        valid_value_zone["label"] = ""
        with pytest.raises(ValidationError):
            ValueZoneSchema(**valid_value_zone)

    def test_value_zone_missing_required_field(self, valid_value_zone):
        """Test that missing required field raises error."""
        del valid_value_zone["label"]
        with pytest.raises(ValidationError) as exc_info:
            ValueZoneSchema(**valid_value_zone)
        assert "label" in str(exc_info.value)


class TestValueZonesSchema:
    """Tests for ValueZonesSchema validation."""

    def test_valid_value_zones(self, valid_value_zones):
        """Test that valid value zones pass validation."""
        schema = ValueZonesSchema(**valid_value_zones)
        assert schema.sweet_spot.min_score == 365
        assert schema.premium.min_score == 480

    def test_value_zones_missing_sweet_spot(self, valid_value_zones):
        """Test that missing sweet_spot raises error."""
        del valid_value_zones["sweet_spot"]
        with pytest.raises(ValidationError) as exc_info:
            ValueZonesSchema(**valid_value_zones)
        assert "sweet_spot" in str(exc_info.value)

    def test_value_zones_extra_field_rejected(self, valid_value_zones):
        """Test that extra fields are rejected (extra='forbid')."""
        valid_value_zones["extra_zone"] = {"min_score": 100, "label": "Extra"}
        with pytest.raises(ValidationError) as exc_info:
            ValueZonesSchema(**valid_value_zones)
        assert "extra_zone" in str(exc_info.value) or "Extra inputs" in str(exc_info.value)


# =============================================================================
# SECTION WEIGHTS SCHEMA TESTS
# =============================================================================


class TestSectionWeightsSchema:
    """Tests for SectionWeightsSchema validation."""

    def test_valid_section_weights(self, valid_section_weights):
        """Test that valid section weights pass validation."""
        schema = SectionWeightsSchema(**valid_section_weights)
        assert schema.location.points == 250
        assert schema.systems.points == 175
        assert schema.interior.points == 180

    def test_section_weights_total_points_not_605(self, valid_section_weights):
        """Test that total points != 605 is rejected."""
        valid_section_weights["location"]["points"] = 200  # 200+175+180 = 555 != 605
        with pytest.raises(ValidationError) as exc_info:
            SectionWeightsSchema(**valid_section_weights)
        assert "605" in str(exc_info.value)

    def test_section_weights_total_weight_not_1(self, valid_section_weights):
        """Test that total weight != 1.0 is rejected."""
        valid_section_weights["location"]["weight"] = 0.5  # 0.5+0.2893+0.2975 = 1.0868 != 1.0
        with pytest.raises(ValidationError) as exc_info:
            SectionWeightsSchema(**valid_section_weights)
        assert "1.0" in str(exc_info.value)

    def test_section_negative_points(self, valid_section_weights):
        """Test that negative points is rejected."""
        valid_section_weights["location"]["points"] = -50
        valid_section_weights["systems"]["points"] = 475  # Make total still 605 (-50+475+180=605)
        with pytest.raises(ValidationError) as exc_info:
            SectionWeightsSchema(**valid_section_weights)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_section_weight_over_1(self, valid_section_weights):
        """Test that weight > 1.0 is rejected."""
        valid_section_weights["location"]["weight"] = 1.5
        with pytest.raises(ValidationError) as exc_info:
            SectionWeightsSchema(**valid_section_weights)
        assert "less than or equal to 1" in str(exc_info.value)


class TestLocationCriteriaSchema:
    """Tests for LocationCriteriaSchema validation."""

    def test_valid_location_criteria(self, valid_location_criteria):
        """Test that valid location criteria passes validation."""
        schema = LocationCriteriaSchema(**valid_location_criteria)
        assert schema.school == 42
        assert schema.crime_index == 47

    def test_location_criteria_negative_weight(self, valid_location_criteria):
        """Test that negative weight is rejected."""
        valid_location_criteria["school"] = -10
        with pytest.raises(ValidationError):
            LocationCriteriaSchema(**valid_location_criteria)

    def test_location_criteria_weight_over_100(self, valid_location_criteria):
        """Test that weight > 100 is rejected."""
        valid_location_criteria["school"] = 101
        with pytest.raises(ValidationError):
            LocationCriteriaSchema(**valid_location_criteria)


# =============================================================================
# TIER THRESHOLDS SCHEMA TESTS
# =============================================================================


class TestTierThresholdsSchema:
    """Tests for TierThresholdsSchema validation."""

    def test_valid_tier_thresholds(self, valid_tier_thresholds):
        """Test that valid tier thresholds pass validation."""
        schema = TierThresholdsSchema(**valid_tier_thresholds)
        assert schema.unicorn.min_score == 484
        assert schema.contender.min_score == 363
        assert schema.pass_.min_score == 0

    def test_tier_thresholds_unicorn_not_greater_than_contender(
        self, valid_tier_thresholds
    ):
        """Test that unicorn <= contender is rejected."""
        valid_tier_thresholds["unicorn"]["min_score"] = 363  # Same as contender
        with pytest.raises(ValidationError) as exc_info:
            TierThresholdsSchema(**valid_tier_thresholds)
        assert "unicorn" in str(exc_info.value).lower()
        assert "contender" in str(exc_info.value).lower()

    def test_tier_thresholds_contender_not_greater_than_pass(
        self, valid_tier_thresholds
    ):
        """Test that contender <= pass is rejected."""
        valid_tier_thresholds["contender"]["min_score"] = 0  # Same as pass
        with pytest.raises(ValidationError) as exc_info:
            TierThresholdsSchema(**valid_tier_thresholds)
        assert "contender" in str(exc_info.value).lower()

    def test_tier_threshold_negative_score(self, valid_tier_thresholds):
        """Test that negative min_score is rejected."""
        valid_tier_thresholds["pass"]["min_score"] = -10
        with pytest.raises(ValidationError):
            TierThresholdsSchema(**valid_tier_thresholds)

    def test_tier_threshold_over_605(self, valid_tier_thresholds):
        """Test that min_score > 605 is rejected."""
        valid_tier_thresholds["unicorn"]["min_score"] = 650
        with pytest.raises(ValidationError):
            TierThresholdsSchema(**valid_tier_thresholds)


# =============================================================================
# SCORING WEIGHTS CONFIG SCHEMA TESTS
# =============================================================================


class TestScoringWeightsConfigSchema:
    """Tests for complete ScoringWeightsConfigSchema validation."""

    def test_valid_scoring_weights(self, valid_scoring_weights):
        """Test that valid scoring weights pass validation."""
        schema = ScoringWeightsConfigSchema(**valid_scoring_weights)
        assert schema.section_weights.location.points == 250
        assert schema.tier_thresholds.unicorn.min_score == 484
        assert schema.value_zones.sweet_spot.min_score == 365

    def test_scoring_weights_optional_defaults(self, valid_scoring_weights):
        """Test that defaults section is optional."""
        schema = ScoringWeightsConfigSchema(**valid_scoring_weights)
        assert schema.defaults is None

    def test_scoring_weights_with_defaults(self, valid_scoring_weights):
        """Test that defaults section can be provided."""
        valid_scoring_weights["defaults"] = {
            "value_zone_min_score": 365,
            "value_zone_max_price": 550000,
        }
        schema = ScoringWeightsConfigSchema(**valid_scoring_weights)
        assert schema.defaults.value_zone_min_score == 365


# =============================================================================
# BUYER CRITERIA SCHEMA TESTS
# =============================================================================


class TestHardCriteriaSchema:
    """Tests for HardCriteriaSchema validation."""

    def test_valid_hard_criteria(self, valid_hard_criteria):
        """Test that valid hard criteria passes validation (Sprint 0: 8 fields)."""
        schema = HardCriteriaSchema(**valid_hard_criteria)
        assert schema.hoa_fee == 0
        assert schema.min_beds == 4
        assert schema.min_baths == 2
        assert schema.min_sqft == 1800
        assert schema.min_lot_sqft == 8000
        assert schema.sewer_type == "city"
        assert schema.min_garage == 1
        assert schema.solar_lease is False

    def test_hard_criteria_negative_hoa(self, valid_hard_criteria):
        """Test that negative HOA fee is rejected."""
        valid_hard_criteria["hoa_fee"] = -100
        with pytest.raises(ValidationError):
            HardCriteriaSchema(**valid_hard_criteria)

    def test_hard_criteria_zero_beds(self, valid_hard_criteria):
        """Test that 0 beds is rejected (min is 1)."""
        valid_hard_criteria["min_beds"] = 0
        with pytest.raises(ValidationError):
            HardCriteriaSchema(**valid_hard_criteria)

    def test_hard_criteria_fractional_baths(self, valid_hard_criteria):
        """Test that fractional baths are allowed (Sprint 0: 8 fields)."""
        valid_hard_criteria["min_baths"] = 2.5
        schema = HardCriteriaSchema(**valid_hard_criteria)
        assert schema.min_baths == 2.5
        # Verify other fields still present
        assert schema.min_sqft == 1800
        assert schema.sewer_type == "city"


class TestSewerCriterionSchema:
    """Tests for SewerCriterionSchema validation."""

    def test_valid_sewer_criterion(self):
        """Test valid sewer criterion."""
        schema = SewerCriterionSchema(required="city", severity=2.5)
        assert schema.required == "city"
        assert schema.severity == 2.5

    def test_sewer_criterion_invalid_type(self):
        """Test that invalid sewer type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SewerCriterionSchema(required="septic", severity=2.5)
        assert "literal" in str(exc_info.value).lower() or "Input should be" in str(
            exc_info.value
        )

    def test_sewer_criterion_severity_over_10(self):
        """Test that severity > 10 is rejected."""
        with pytest.raises(ValidationError):
            SewerCriterionSchema(required="city", severity=11.0)


class TestYearBuiltCriterionSchema:
    """Tests for YearBuiltCriterionSchema validation."""

    def test_valid_year_built_current_year_token(self):
        """Test current_year token is accepted."""
        schema = YearBuiltCriterionSchema(max="current_year", severity=2.0)
        assert schema.max == "current_year"

    def test_valid_year_built_integer(self):
        """Test integer year is accepted."""
        schema = YearBuiltCriterionSchema(max=2024, severity=2.0)
        assert schema.max == 2024

    def test_year_built_invalid_token(self):
        """Test that invalid string token is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            YearBuiltCriterionSchema(max="last_year", severity=2.0)
        assert "current_year" in str(exc_info.value)

    def test_year_built_get_max_year_token(self):
        """Test get_max_year() resolves current_year token."""
        import datetime

        schema = YearBuiltCriterionSchema(max="current_year", severity=2.0)
        assert schema.get_max_year() == datetime.datetime.now().year

    def test_year_built_get_max_year_integer(self):
        """Test get_max_year() returns integer as-is."""
        schema = YearBuiltCriterionSchema(max=2020, severity=2.0)
        assert schema.get_max_year() == 2020


class TestLotSizeCriterionSchema:
    """Tests for LotSizeCriterionSchema validation."""

    def test_valid_lot_size_criterion(self):
        """Test valid lot size criterion."""
        schema = LotSizeCriterionSchema(min=7000, max=15000, severity=1.0)
        assert schema.min == 7000
        assert schema.max == 15000

    def test_lot_size_max_less_than_min(self):
        """Test that max < min is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LotSizeCriterionSchema(min=15000, max=7000, severity=1.0)
        assert "max" in str(exc_info.value).lower()
        assert "min" in str(exc_info.value).lower()

    def test_lot_size_max_equals_min(self):
        """Test that max == min is rejected."""
        with pytest.raises(ValidationError):
            LotSizeCriterionSchema(min=10000, max=10000, severity=1.0)


class TestThresholdsSchema:
    """Tests for ThresholdsSchema validation."""

    def test_valid_thresholds(self, valid_thresholds):
        """Test valid thresholds pass validation."""
        schema = ThresholdsSchema(**valid_thresholds)
        assert schema.severity_fail == 3.0
        assert schema.severity_warning == 1.5

    def test_thresholds_warning_not_less_than_fail(self, valid_thresholds):
        """Test that warning >= fail is rejected."""
        valid_thresholds["severity_warning"] = 3.0  # Same as fail
        with pytest.raises(ValidationError) as exc_info:
            ThresholdsSchema(**valid_thresholds)
        assert "warning" in str(exc_info.value).lower()
        assert "fail" in str(exc_info.value).lower()

    def test_thresholds_warning_greater_than_fail(self, valid_thresholds):
        """Test that warning > fail is rejected."""
        valid_thresholds["severity_warning"] = 4.0  # Greater than fail
        with pytest.raises(ValidationError):
            ThresholdsSchema(**valid_thresholds)

    def test_thresholds_negative_values(self, valid_thresholds):
        """Test that negative thresholds are rejected."""
        valid_thresholds["severity_fail"] = -1.0
        with pytest.raises(ValidationError):
            ThresholdsSchema(**valid_thresholds)


class TestBuyerCriteriaConfigSchema:
    """Tests for complete BuyerCriteriaConfigSchema validation."""

    def test_valid_buyer_criteria(self, valid_buyer_criteria):
        """Test that valid buyer criteria passes validation."""
        schema = BuyerCriteriaConfigSchema(**valid_buyer_criteria)
        assert schema.hard_criteria.min_beds == 4
        assert schema.soft_criteria.sewer_type.severity == 2.5
        assert schema.thresholds.severity_fail == 3.0


# =============================================================================
# APP CONFIG SCHEMA TESTS
# =============================================================================


class TestAppConfigSchema:
    """Tests for complete AppConfigSchema validation."""

    def test_valid_app_config(self, valid_scoring_weights, valid_buyer_criteria):
        """Test that valid app config passes validation (Sprint 0)."""
        schema = AppConfigSchema(
            scoring=valid_scoring_weights,
            buyer_criteria=valid_buyer_criteria,
        )
        assert schema.scoring.section_weights.location.points == 250
        assert schema.buyer_criteria.hard_criteria.min_beds == 4
        assert schema.buyer_criteria.hard_criteria.min_sqft == 1800


# =============================================================================
# CONFIGURATION ERROR TESTS
# =============================================================================


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test that ConfigurationError is an Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)

    def test_configuration_error_message(self):
        """Test that ConfigurationError preserves message."""
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"

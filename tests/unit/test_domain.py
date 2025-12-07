"""Unit tests for domain models and enums.

Tests domain entities, value objects, and their computed properties.
"""

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import (
    Orientation,
    RiskLevel,
    SewerType,
    SolarStatus,
    Tier,
)
from src.phx_home_analysis.domain.value_objects import (
    Address,
    RiskAssessment,
)

# ============================================================================
# Tier Enum Tests
# ============================================================================


class TestTierEnum:
    """Test Tier enum properties and classification."""

    def test_tier_values(self):
        """Test all tier enum values exist."""
        assert Tier.UNICORN.value == "unicorn"
        assert Tier.CONTENDER.value == "contender"
        assert Tier.PASS.value == "pass"
        assert Tier.FAILED.value == "failed"

    def test_tier_colors(self):
        """Test each tier has a color code."""
        assert len(Tier.UNICORN.color) > 0
        assert len(Tier.CONTENDER.color) > 0
        assert len(Tier.PASS.color) > 0
        assert len(Tier.FAILED.color) > 0

    def test_tier_colors_are_hex(self):
        """Test tier colors are valid hex codes."""
        for tier in Tier:
            color = tier.color
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB

    def test_tier_labels(self):
        """Test tier labels are human-readable."""
        assert Tier.UNICORN.label == "Unicorn"
        assert Tier.CONTENDER.label == "Contender"
        assert Tier.PASS.label == "Pass"
        assert Tier.FAILED.label == "Failed"

    def test_tier_icons(self):
        """Test tier icons exist."""
        assert Tier.UNICORN.icon == "🦄"
        assert Tier.CONTENDER.icon == "⭐"
        assert Tier.PASS.icon == "✓"
        assert Tier.FAILED.icon == "✗"

    def test_tier_from_score_unicorn(self):
        """Test Tier.from_score classifies >480 as UNICORN."""
        tier = Tier.from_score(500.0, True)
        assert tier == Tier.UNICORN

    def test_tier_from_score_contender(self):
        """Test Tier.from_score classifies 360-480 as CONTENDER."""
        tier = Tier.from_score(420.0, True)
        assert tier == Tier.CONTENDER

    def test_tier_from_score_pass(self):
        """Test Tier.from_score classifies <360 as PASS."""
        tier = Tier.from_score(300.0, True)
        assert tier == Tier.PASS

    def test_tier_from_score_failed_regardless_of_score(self):
        """Test Tier.from_score returns FAILED when kill_switch=False."""
        for score in [50, 300, 420, 500]:
            tier = Tier.from_score(score, False)
            assert tier == Tier.FAILED

    def test_tier_from_score_boundary_unicorn_exactly_480(self):
        """Test boundary: score=480.0 is CONTENDER, not UNICORN."""
        tier = Tier.from_score(480.0, True)
        assert tier == Tier.CONTENDER

    def test_tier_from_score_boundary_contender_exactly_360(self):
        """Test boundary: score=360.0 is CONTENDER, not PASS."""
        tier = Tier.from_score(360.0, True)
        assert tier == Tier.CONTENDER


# ============================================================================
# RiskLevel Enum Tests
# ============================================================================


class TestRiskLevelEnum:
    """Test RiskLevel enum properties."""

    def test_risk_level_values(self):
        """Test all risk level values exist."""
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.POSITIVE.value == "positive"
        assert RiskLevel.UNKNOWN.value == "unknown"

    def test_risk_level_scores(self):
        """Test risk level scores are numeric."""
        assert isinstance(RiskLevel.HIGH.score, float)
        assert isinstance(RiskLevel.MEDIUM.score, float)
        assert isinstance(RiskLevel.LOW.score, float)
        assert isinstance(RiskLevel.POSITIVE.score, float)
        assert isinstance(RiskLevel.UNKNOWN.score, float)

    def test_risk_level_score_values(self):
        """Test risk level scores are on 0-10 scale."""
        assert RiskLevel.HIGH.score == 0.0
        assert RiskLevel.MEDIUM.score == 5.0
        assert RiskLevel.LOW.score == 7.5
        assert RiskLevel.POSITIVE.score == 10.0
        assert RiskLevel.UNKNOWN.score == 5.0

    def test_risk_level_css_classes(self):
        """Test risk level CSS classes."""
        assert "risk-" in RiskLevel.HIGH.css_class
        assert "risk-" in RiskLevel.MEDIUM.css_class
        assert "risk-" in RiskLevel.LOW.css_class

    def test_risk_level_colors(self):
        """Test risk level colors are hex."""
        for level in RiskLevel:
            color = level.color
            assert color.startswith("#")
            assert len(color) == 7


# ============================================================================
# SewerType Enum Tests
# ============================================================================


class TestSewerTypeEnum:
    """Test SewerType enum properties."""

    def test_sewer_type_values(self):
        """Test sewer type values."""
        assert SewerType.CITY.value == "city"
        assert SewerType.SEPTIC.value == "septic"
        assert SewerType.UNKNOWN.value == "unknown"

    def test_sewer_type_acceptability(self):
        """Test sewer type acceptability for buyer requirements."""
        assert SewerType.CITY.is_acceptable is True
        assert SewerType.SEPTIC.is_acceptable is False
        assert SewerType.UNKNOWN.is_acceptable is False

    def test_sewer_type_descriptions(self):
        """Test sewer type descriptions."""
        assert "City sewer" in SewerType.CITY.description
        assert "Septic" in SewerType.SEPTIC.description
        assert "unknown" in SewerType.UNKNOWN.description.lower()


# ============================================================================
# SolarStatus Enum Tests
# ============================================================================


class TestSolarStatusEnum:
    """Test SolarStatus enum properties."""

    def test_solar_status_values(self):
        """Test solar status values."""
        assert SolarStatus.OWNED.value == "owned"
        assert SolarStatus.LEASED.value == "leased"
        assert SolarStatus.NONE.value == "none"
        assert SolarStatus.UNKNOWN.value == "unknown"

    def test_solar_status_problematic(self):
        """Test which solar statuses are problematic."""
        assert SolarStatus.LEASED.is_problematic is True
        assert SolarStatus.OWNED.is_problematic is False
        assert SolarStatus.NONE.is_problematic is False
        assert SolarStatus.UNKNOWN.is_problematic is False

    def test_solar_status_descriptions(self):
        """Test solar status descriptions."""
        assert "Owned" in SolarStatus.OWNED.description
        assert "Leased" in SolarStatus.LEASED.description
        assert "cost burden" in SolarStatus.LEASED.description


# ============================================================================
# Orientation Enum Tests
# ============================================================================


class TestOrientationEnum:
    """Test Orientation enum properties."""

    def test_orientation_values(self):
        """Test orientation enum values."""
        assert Orientation.N.value == "north"
        assert Orientation.S.value == "south"
        assert Orientation.E.value == "east"
        assert Orientation.W.value == "west"

    def test_orientation_cooling_cost_multipliers(self):
        """Test cooling cost multipliers."""
        assert Orientation.N.cooling_cost_multiplier < 1.0  # Best
        assert Orientation.W.cooling_cost_multiplier > 1.0  # Worst
        assert Orientation.S.cooling_cost_multiplier == 1.0  # Baseline

    def test_orientation_cooling_cost_order(self):
        """Test cooling costs from best to worst."""
        # North should be cheapest
        assert Orientation.N.cooling_cost_multiplier < Orientation.W.cooling_cost_multiplier

    def test_orientation_base_scores(self):
        """Test orientation base scores (0-10 scale)."""
        assert Orientation.N.base_score == 10.0  # Best
        assert Orientation.W.base_score == 0.0  # Worst
        assert Orientation.UNKNOWN.base_score == 5.0  # Neutral

    def test_orientation_from_string(self):
        """Test parsing orientation from strings."""
        assert Orientation.from_string("N") == Orientation.N
        assert Orientation.from_string("north") == Orientation.N
        assert Orientation.from_string("NORTH") == Orientation.N

        assert Orientation.from_string("W") == Orientation.W
        assert Orientation.from_string("west") == Orientation.W
        assert Orientation.from_string("WEST") == Orientation.W

    def test_orientation_from_string_invalid(self):
        """Test parsing invalid orientation defaults to UNKNOWN."""
        assert Orientation.from_string("invalid") == Orientation.UNKNOWN
        assert Orientation.from_string(None) == Orientation.UNKNOWN
        assert Orientation.from_string("") == Orientation.UNKNOWN

    def test_orientation_from_string_diagonals(self):
        """Test parsing diagonal orientations."""
        assert Orientation.from_string("NE") == Orientation.NE
        assert Orientation.from_string("northeast") == Orientation.NE
        assert Orientation.from_string("SW") == Orientation.SW

    def test_orientation_descriptions(self):
        """Test orientation descriptions."""
        assert "North" in Orientation.N.description
        assert "West" in Orientation.W.description
        assert "cooling" in Orientation.W.description.lower()


# ============================================================================
# Address Value Object Tests
# ============================================================================


class TestAddressValueObject:
    """Test Address value object."""

    def test_address_creation(self):
        """Test creating an Address value object."""
        address = Address(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
        )

        assert address.street == "123 Main St"
        assert address.city == "Phoenix"
        assert address.state == "AZ"
        assert address.zip_code == "85001"

    def test_address_full_address(self):
        """Test Address.full_address property."""
        address = Address(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
        )

        assert address.full_address == "123 Main St, Phoenix, AZ 85001"

    def test_address_short_address(self):
        """Test Address.short_address property."""
        address = Address(
            street="456 Oak Ave",
            city="Scottsdale",
            state="AZ",
            zip_code="85251",
        )

        assert address.short_address == "456 Oak Ave, Scottsdale"

    def test_address_is_frozen(self):
        """Test Address is immutable."""
        address = Address(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
        )

        with pytest.raises(AttributeError):  # FrozenInstanceError
            address.street = "456 Oak Ave"

    def test_address_string_representation(self):
        """Test Address string representation."""
        address = Address(
            street="789 Elm St",
            city="Tempe",
            state="AZ",
            zip_code="85281",
        )

        assert str(address) == "789 Elm St, Tempe, AZ 85281"


# ============================================================================
# RiskAssessment Value Object Tests
# ============================================================================


class TestRiskAssessmentValueObject:
    """Test RiskAssessment value object."""

    def test_risk_assessment_creation(self):
        """Test creating a RiskAssessment."""
        risk = RiskAssessment(
            category="Structural",
            level=RiskLevel.HIGH,
            description="Roof needs replacement within 2 years",
            mitigation="Budget $15,000 for roof replacement",
        )

        assert risk.category == "Structural"
        assert risk.level == RiskLevel.HIGH
        assert risk.description == "Roof needs replacement within 2 years"
        assert risk.mitigation == "Budget $15,000 for roof replacement"

    def test_risk_assessment_score(self):
        """Test RiskAssessment.score property."""
        risk_high = RiskAssessment(
            category="Test",
            level=RiskLevel.HIGH,
            description="Test",
        )
        risk_positive = RiskAssessment(
            category="Test",
            level=RiskLevel.POSITIVE,
            description="Test",
        )

        assert risk_high.score == 0.0
        assert risk_positive.score == 10.0

    def test_risk_assessment_is_high_risk(self):
        """Test RiskAssessment.is_high_risk property."""
        high_risk = RiskAssessment(
            category="Test",
            level=RiskLevel.HIGH,
            description="Test",
        )
        low_risk = RiskAssessment(
            category="Test",
            level=RiskLevel.LOW,
            description="Test",
        )

        assert high_risk.is_high_risk is True
        assert low_risk.is_high_risk is False

    def test_risk_assessment_is_frozen(self):
        """Test RiskAssessment is immutable."""
        risk = RiskAssessment(
            category="Test",
            level=RiskLevel.HIGH,
            description="Test",
        )

        with pytest.raises(AttributeError):
            risk.category = "New Category"

    def test_risk_assessment_optional_mitigation(self):
        """Test RiskAssessment with no mitigation."""
        risk = RiskAssessment(
            category="Test",
            level=RiskLevel.LOW,
            description="Minor concern",
        )

        assert risk.mitigation is None

    def test_risk_assessment_string_representation(self):
        """Test RiskAssessment string representation."""
        risk = RiskAssessment(
            category="Financial",
            level=RiskLevel.MEDIUM,
            description="HOA fees may increase",
        )

        str_repr = str(risk)
        assert "Financial" in str_repr
        assert "MEDIUM" in str_repr
        assert "HOA fees" in str_repr


# ============================================================================
# Property Entity Tests
# ============================================================================


class TestPropertyEntity:
    """Test Property entity and its computed properties."""

    def test_property_creation(self, sample_property):
        """Test creating a Property."""
        assert sample_property.street == "123 Desert Rose Ln"
        assert sample_property.city == "Phoenix"
        assert sample_property.beds == 4
        assert sample_property.baths == 2.0

    def test_property_address_property(self, sample_property):
        """Test Property.address returns Address value object."""
        address = sample_property.address
        assert isinstance(address, Address)
        assert address.street == sample_property.street

    def test_property_short_address(self, sample_property):
        """Test Property.short_address property."""
        short = sample_property.short_address
        assert short == f"{sample_property.street}, {sample_property.city}"

    def test_property_price_per_sqft(self, sample_property):
        """Test Property.price_per_sqft calculation."""
        # 475000 / 2200 = 215.90...
        assert abs(sample_property.price_per_sqft - 215.9) < 1.0

    def test_property_price_per_sqft_zero_sqft(self):
        """Test Property.price_per_sqft with zero sqft."""
        prop = Property(
            street="123 Main",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Main, Phoenix, AZ 85001",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=0,  # Zero sqft
            price_per_sqft_raw=0.0,
        )

        assert prop.price_per_sqft == 0.0

    def test_property_has_hoa_with_fee(self, sample_property):
        """Test Property.has_hoa when fee is set."""
        sample_property.hoa_fee = 150
        assert sample_property.has_hoa is True

    def test_property_has_hoa_no_fee(self, sample_property):
        """Test Property.has_hoa when fee is zero."""
        sample_property.hoa_fee = 0
        assert sample_property.has_hoa is False

    def test_property_has_hoa_none(self, sample_property):
        """Test Property.has_hoa when fee is None."""
        sample_property.hoa_fee = None
        assert sample_property.has_hoa is False

    def test_property_age_years(self, sample_property):
        """Test Property.age_years calculation."""
        sample_property.year_built = 2010
        age = sample_property.age_years
        assert age == 15  # 2025 - 2010

    def test_property_age_years_none(self, sample_property):
        """Test Property.age_years with None year_built."""
        sample_property.year_built = None
        assert sample_property.age_years is None

    def test_property_total_score(self, sample_property):
        """Test Property.total_score property."""
        # Without score breakdown, should be 0
        assert sample_property.total_score == 0.0

    def test_property_is_unicorn(self, sample_property):
        """Test Property.is_unicorn property."""
        sample_property.tier = Tier.UNICORN
        assert sample_property.is_unicorn is True

        sample_property.tier = Tier.CONTENDER
        assert sample_property.is_unicorn is False

    def test_property_is_contender(self, sample_property):
        """Test Property.is_contender property."""
        sample_property.tier = Tier.CONTENDER
        assert sample_property.is_contender is True

        sample_property.tier = Tier.PASS
        assert sample_property.is_contender is False

    def test_property_is_failed(self, sample_property):
        """Test Property.is_failed property."""
        sample_property.tier = Tier.FAILED
        assert sample_property.is_failed is True

        sample_property.kill_switch_passed = False
        assert sample_property.is_failed is True

        sample_property.tier = Tier.PASS
        sample_property.kill_switch_passed = True
        assert sample_property.is_failed is False

    def test_property_monthly_costs_empty_without_cache(self, sample_property):
        """Test Property.monthly_costs returns empty dict when not cached."""
        # Without calling set_monthly_costs, should return empty dict
        costs = sample_property.monthly_costs
        assert costs == {}

    def test_property_monthly_costs_with_cache(self, sample_property):
        """Test Property.monthly_costs returns cached data after set_monthly_costs."""
        # Simulate service layer setting the cache
        sample_property.set_monthly_costs(
            {
                "mortgage": 2500.0,
                "property_tax": 300.0,
                "hoa": 0.0,
                "solar_lease": 0.0,
                "pool_maintenance": 0.0,
            }
        )

        costs = sample_property.monthly_costs

        assert "mortgage" in costs
        assert "property_tax" in costs
        assert "hoa" in costs
        assert "solar_lease" in costs
        assert "pool_maintenance" in costs

        # All should be non-negative
        for cost in costs.values():
            assert cost >= 0

    def test_property_total_monthly_cost_without_cache(self, sample_property):
        """Test Property.total_monthly_cost returns 0 when not cached."""
        total = sample_property.total_monthly_cost
        assert total == 0.0

    def test_property_total_monthly_cost_with_cache(self, sample_property):
        """Test Property.total_monthly_cost aggregation with cached data."""
        sample_property.set_monthly_costs(
            {
                "mortgage": 2500.0,
                "property_tax": 300.0,
                "hoa": 150.0,
                "solar_lease": 0.0,
                "pool_maintenance": 0.0,
            }
        )

        total = sample_property.total_monthly_cost
        expected = sum(sample_property.monthly_costs.values())

        assert abs(total - expected) < 0.01
        assert abs(total - 2950.0) < 0.01

    def test_property_set_monthly_costs_with_hoa(self, sample_property):
        """Test monthly costs can include HOA fee via set_monthly_costs."""
        sample_property.set_monthly_costs(
            {
                "mortgage": 2500.0,
                "property_tax": 300.0,
                "hoa": 150.0,
                "solar_lease": 0.0,
                "pool_maintenance": 0.0,
            }
        )
        costs = sample_property.monthly_costs

        assert costs["hoa"] == 150.0

    def test_property_set_monthly_costs_with_solar_lease(self, sample_property):
        """Test monthly costs can include solar lease via set_monthly_costs."""
        sample_property.set_monthly_costs(
            {
                "mortgage": 2500.0,
                "property_tax": 300.0,
                "hoa": 0.0,
                "solar_lease": 120.0,
                "pool_maintenance": 0.0,
            }
        )
        costs = sample_property.monthly_costs

        assert costs["solar_lease"] == 120.0

    def test_property_set_monthly_costs_with_pool(self, sample_property):
        """Test monthly costs can include pool maintenance via set_monthly_costs."""
        sample_property.set_monthly_costs(
            {
                "mortgage": 2500.0,
                "property_tax": 300.0,
                "hoa": 0.0,
                "solar_lease": 0.0,
                "pool_maintenance": 200.0,
            }
        )
        costs = sample_property.monthly_costs

        # Service uses comprehensive pool cost: $125 service + $75 energy = $200
        assert costs["pool_maintenance"] == 200.0

    def test_property_effective_price_no_renovation(self, sample_property):
        """Test effective_price without renovation estimate."""
        assert sample_property.effective_price == sample_property.price_num

    def test_property_high_risks(self, sample_property):
        """Test Property.high_risks filters correctly."""
        sample_property.risk_assessments = [
            RiskAssessment("Cat1", RiskLevel.HIGH, "High risk"),
            RiskAssessment("Cat2", RiskLevel.MEDIUM, "Medium risk"),
            RiskAssessment("Cat3", RiskLevel.HIGH, "High risk"),
        ]

        high_risks = sample_property.high_risks
        assert len(high_risks) == 2
        assert all(r.is_high_risk for r in high_risks)

    def test_property_string_representation(self, sample_property):
        """Test Property string representation."""
        sample_property.tier = Tier.CONTENDER
        str_repr = str(sample_property)

        assert sample_property.full_address in str_repr
        assert "4bd" in str_repr
        assert "2.0ba" in str_repr  # baths is float
        assert "Contender" in str_repr

    def test_property_full_address_auto_generated(self):
        """Test full_address is auto-generated if not provided."""
        prop = Property(
            street="100 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="",  # Empty
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=50.0,
        )

        # Should be auto-generated in __post_init__
        assert prop.full_address == "100 Test St, Phoenix, AZ 85001"


# ============================================================================
# Enum String Normalization Tests
# ============================================================================


class TestEnumStringNormalization:
    """Test Property.__post_init__ normalizes enum strings."""

    def test_sewer_type_string_normalization(self):
        """Test sewer_type is converted from string to enum."""
        prop = Property(
            street="Test",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="Test",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=50.0,
            sewer_type="city",  # String instead of enum
        )

        assert isinstance(prop.sewer_type, SewerType)
        assert prop.sewer_type == SewerType.CITY

    def test_solar_status_string_normalization(self):
        """Test solar_status is converted from string to enum."""
        prop = Property(
            street="Test",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="Test",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=50.0,
            solar_status="leased",  # String instead of enum
        )

        assert isinstance(prop.solar_status, SolarStatus)
        assert prop.solar_status == SolarStatus.LEASED

    def test_orientation_string_normalization(self):
        """Test orientation is converted from string to enum."""
        prop = Property(
            street="Test",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="Test",
            price="$100,000",
            price_num=100000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=50.0,
            orientation="north",  # String instead of enum
        )

        assert isinstance(prop.orientation, Orientation)
        assert prop.orientation == Orientation.N

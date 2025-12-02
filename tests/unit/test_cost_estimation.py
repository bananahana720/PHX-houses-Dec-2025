"""Unit tests for cost estimation service.

Tests cover:
- Mortgage calculation (P&I amortization)
- Property tax estimation
- Insurance calculation
- Utility estimation
- Pool maintenance costs
- With/without pool scenarios
- With/without solar lease scenarios
- Total calculation
- Edge cases (0 sqft, high LTV, etc.)
"""

from dataclasses import dataclass

import pytest

from src.phx_home_analysis.services.cost_estimation import (
    DOWN_PAYMENT_DEFAULT,
    INSURANCE_ANNUAL_PER_1K,
    MAINTENANCE_RESERVE_RATE,
    MORTGAGE_RATE_30YR,
    POOL_TOTAL_MONTHLY,
    PROPERTY_TAX_RATE,
    TRASH_MONTHLY,
    UTILITY_RATE_PER_SQFT,
    WATER_MONTHLY_ESTIMATE,
    CostEstimate,
    MonthlyCostEstimator,
    MonthlyCosts,
    RateConfig,
)

# =============================================================================
# TEST FIXTURES
# =============================================================================


@dataclass
class MockProperty:
    """Mock property object for testing cost estimation."""

    price_num: int = 475000
    sqft: int = 2200
    has_pool: bool | None = False
    hoa_fee: int | None = 0
    solar_lease_monthly: int | None = None
    tax_annual: int | None = None


@pytest.fixture
def estimator():
    """Default cost estimator with standard settings."""
    return MonthlyCostEstimator()


@pytest.fixture
def estimator_custom_rate():
    """Cost estimator with custom rate."""
    return MonthlyCostEstimator(down_payment=50000, rate=0.065)


@pytest.fixture
def basic_property():
    """Basic property without pool or solar."""
    return MockProperty(
        price_num=475000,
        sqft=2200,
        has_pool=False,
        hoa_fee=0,
        solar_lease_monthly=None,
        tax_annual=None,
    )


@pytest.fixture
def property_with_pool():
    """Property with pool."""
    return MockProperty(
        price_num=500000,
        sqft=2500,
        has_pool=True,
        hoa_fee=0,
        solar_lease_monthly=None,
        tax_annual=None,
    )


@pytest.fixture
def property_with_solar():
    """Property with solar lease."""
    return MockProperty(
        price_num=450000,
        sqft=2000,
        has_pool=False,
        hoa_fee=0,
        solar_lease_monthly=150,
        tax_annual=None,
    )


@pytest.fixture
def property_with_hoa():
    """Property with HOA fee."""
    return MockProperty(
        price_num=400000,
        sqft=1800,
        has_pool=False,
        hoa_fee=200,
        solar_lease_monthly=None,
        tax_annual=None,
    )


@pytest.fixture
def property_with_known_tax():
    """Property with known annual tax."""
    return MockProperty(
        price_num=475000,
        sqft=2200,
        has_pool=False,
        hoa_fee=0,
        solar_lease_monthly=None,
        tax_annual=4200,
    )


@pytest.fixture
def luxury_property():
    """Higher-end property with all features."""
    return MockProperty(
        price_num=650000,
        sqft=3500,
        has_pool=True,
        hoa_fee=0,
        solar_lease_monthly=175,
        tax_annual=5800,
    )


# =============================================================================
# MORTGAGE CALCULATION TESTS
# =============================================================================


class TestMortgageCalculation:
    """Test mortgage P&I calculation."""

    def test_basic_mortgage_calculation(self, estimator, basic_property):
        """Test standard mortgage calculation."""
        costs = estimator.estimate(basic_property)

        # Loan amount: $475k - $50k = $425k
        # At 6.99% for 30 years, monthly P&I should be ~$2,824
        assert 2800 < costs.mortgage < 2850

    def test_zero_loan_amount(self, estimator):
        """Test when down payment covers full price."""
        property = MockProperty(price_num=40000)  # Less than $50k down
        costs = estimator.estimate(property)

        assert costs.mortgage == 0.0

    def test_custom_rate_affects_mortgage(self, basic_property):
        """Test that custom rate changes mortgage payment."""
        estimator_high = MonthlyCostEstimator(rate=0.08)
        estimator_low = MonthlyCostEstimator(rate=0.05)

        costs_high = estimator_high.estimate(basic_property)
        costs_low = estimator_low.estimate(basic_property)

        assert costs_high.mortgage > costs_low.mortgage

    def test_custom_down_payment_affects_mortgage(self, basic_property):
        """Test that different down payments change mortgage."""
        estimator_large = MonthlyCostEstimator(down_payment=100000)
        estimator_small = MonthlyCostEstimator(down_payment=25000)

        costs_large = estimator_large.estimate(basic_property)
        costs_small = estimator_small.estimate(basic_property)

        assert costs_large.mortgage < costs_small.mortgage

    def test_mortgage_precision(self, estimator, basic_property):
        """Test mortgage is rounded to 2 decimal places."""
        costs = estimator.estimate(basic_property)
        assert costs.mortgage == round(costs.mortgage, 2)

    def test_zero_interest_rate(self, basic_property):
        """Test mortgage calculation with zero interest rate."""
        estimator = MonthlyCostEstimator(rate=0.0)
        costs = estimator.estimate(basic_property)

        # Simple division: ($475k - $50k) / 360 months
        expected = (475000 - 50000) / 360
        assert abs(costs.mortgage - expected) < 0.01


# =============================================================================
# PROPERTY TAX TESTS
# =============================================================================


class TestPropertyTaxCalculation:
    """Test property tax calculation."""

    def test_estimated_property_tax(self, estimator, basic_property):
        """Test property tax estimation when no actual tax provided."""
        costs = estimator.estimate(basic_property)

        # Expected: $475k * 0.66% / 12 = ~$261/month
        expected = (475000 * PROPERTY_TAX_RATE) / 12
        assert abs(costs.property_tax - expected) < 1.0

    def test_actual_tax_used_when_provided(self, estimator, property_with_known_tax):
        """Test that actual tax_annual is used when available."""
        costs = estimator.estimate(property_with_known_tax)

        # $4,200 / 12 = $350/month
        assert costs.property_tax == 350.0

    def test_zero_tax_falls_back_to_estimate(self, estimator):
        """Test that zero tax_annual triggers estimation."""
        property = MockProperty(price_num=400000, tax_annual=0)
        costs = estimator.estimate(property)

        # Should estimate, not use 0
        expected = (400000 * PROPERTY_TAX_RATE) / 12
        assert abs(costs.property_tax - expected) < 1.0


# =============================================================================
# INSURANCE TESTS
# =============================================================================


class TestInsuranceCalculation:
    """Test homeowner's insurance calculation."""

    def test_insurance_calculation(self, estimator, basic_property):
        """Test basic insurance calculation."""
        costs = estimator.estimate(basic_property)

        # Expected: ($475k / $1k) * $6.50 / 12 = ~$257/month
        expected = (475000 / 1000) * INSURANCE_ANNUAL_PER_1K / 12
        assert abs(costs.insurance - expected) < 1.0

    def test_insurance_scales_with_value(self, estimator):
        """Test insurance scales with home value."""
        property_low = MockProperty(price_num=300000)
        property_high = MockProperty(price_num=600000)

        costs_low = estimator.estimate(property_low)
        costs_high = estimator.estimate(property_high)

        # Should be roughly 2x
        assert costs_high.insurance > costs_low.insurance * 1.9


# =============================================================================
# UTILITY TESTS
# =============================================================================


class TestUtilityCalculation:
    """Test utility cost estimation."""

    def test_basic_utility_calculation(self, estimator, basic_property):
        """Test utility calculation based on sqft."""
        costs = estimator.estimate(basic_property)

        # Expected: 2200 sqft * $0.10/sqft = $220/month
        expected = 2200 * UTILITY_RATE_PER_SQFT
        assert abs(costs.utilities - expected) < 1.0

    def test_utility_minimum(self, estimator):
        """Test utility minimum is applied for small/zero sqft."""
        property = MockProperty(sqft=0)
        costs = estimator.estimate(property)

        # Should use minimum ($120 for electric/gas only)
        assert costs.utilities == 120.0

    def test_utility_maximum(self, estimator):
        """Test utility maximum is applied for very large homes."""
        property = MockProperty(sqft=10000)  # Would be $800 without cap
        costs = estimator.estimate(property)

        # Should cap at $500 (electric/gas only)
        assert costs.utilities == 500.0

    def test_utility_scales_with_sqft(self, estimator):
        """Test utilities scale with square footage."""
        property_small = MockProperty(sqft=1500)
        property_large = MockProperty(sqft=3000)

        costs_small = estimator.estimate(property_small)
        costs_large = estimator.estimate(property_large)

        assert costs_large.utilities > costs_small.utilities


# =============================================================================
# WATER COST TESTS
# =============================================================================


class TestWaterCosts:
    """Test water cost calculation."""

    def test_water_default_estimate(self, estimator, basic_property):
        """Test default water cost estimate is applied."""
        costs = estimator.estimate(basic_property)

        # Should be ~$90/mo (base $30 + 12k gal * $5/kgal)
        assert costs.water == WATER_MONTHLY_ESTIMATE
        assert 80 <= costs.water <= 120  # Spec range

    def test_water_included_in_total(self, estimator, basic_property):
        """Test water is included in total monthly costs."""
        costs = estimator.estimate(basic_property)

        # Total should include water
        components_sum = (
            costs.mortgage
            + costs.property_tax
            + costs.insurance
            + costs.utilities
            + costs.water
            + costs.trash
            + costs.pool_maintenance
            + costs.maintenance_reserve
            + costs.hoa_fee
            + costs.solar_lease
        )
        assert abs(costs.total - components_sum) < 0.01

    def test_water_in_variable_costs(self, estimator, basic_property):
        """Test water is categorized as variable cost."""
        costs = estimator.estimate(basic_property)

        # Variable costs should include water
        expected_variable = (
            costs.utilities
            + costs.water
            + costs.trash
            + costs.pool_maintenance
            + costs.maintenance_reserve
        )
        assert abs(costs.variable_costs - expected_variable) < 0.01


# =============================================================================
# TRASH COST TESTS
# =============================================================================


class TestTrashCosts:
    """Test trash/recycling cost calculation."""

    def test_trash_default_estimate(self, estimator, basic_property):
        """Test default trash cost estimate is applied."""
        costs = estimator.estimate(basic_property)

        # Should be ~$40/mo (Maricopa County average)
        assert costs.trash == TRASH_MONTHLY
        assert 30 <= costs.trash <= 50  # Spec range

    def test_trash_included_in_total(self, estimator, basic_property):
        """Test trash is included in total monthly costs."""
        costs = estimator.estimate(basic_property)

        # Verify trash contributes to total
        assert costs.trash > 0
        assert costs.total >= costs.trash

    def test_trash_in_variable_costs(self, estimator, basic_property):
        """Test trash is categorized as variable cost."""
        costs = estimator.estimate(basic_property)

        # Variable costs should include trash
        assert costs.variable_costs >= costs.trash

    def test_water_and_trash_separate_from_utilities(self, estimator, basic_property):
        """Test water and trash are separate line items from utilities."""
        costs = estimator.estimate(basic_property)

        # All three should be positive and distinct
        assert costs.utilities > 0
        assert costs.water > 0
        assert costs.trash > 0

        # Combined should be more than utilities alone
        total_utility_related = costs.utilities + costs.water + costs.trash
        assert total_utility_related > costs.utilities


# =============================================================================
# POOL COST TESTS
# =============================================================================


class TestPoolCosts:
    """Test pool maintenance cost calculation."""

    def test_no_pool_costs_without_pool(self, estimator, basic_property):
        """Test no pool costs when has_pool is False."""
        basic_property.has_pool = False
        costs = estimator.estimate(basic_property)

        assert costs.pool_maintenance == 0.0

    def test_pool_costs_with_pool(self, estimator, property_with_pool):
        """Test pool costs are added when has_pool is True."""
        costs = estimator.estimate(property_with_pool)

        # Should be $200/month ($125 service + $75 energy)
        assert costs.pool_maintenance == POOL_TOTAL_MONTHLY

    def test_none_pool_treated_as_no_pool(self, estimator):
        """Test None has_pool is treated as no pool."""
        property = MockProperty(has_pool=None)
        costs = estimator.estimate(property)

        assert costs.pool_maintenance == 0.0


# =============================================================================
# SOLAR LEASE TESTS
# =============================================================================


class TestSolarLease:
    """Test solar lease cost handling."""

    def test_no_solar_lease_without_solar(self, estimator, basic_property):
        """Test no solar costs when solar_lease_monthly is None."""
        costs = estimator.estimate(basic_property)

        assert costs.solar_lease == 0.0

    def test_solar_lease_included_when_present(self, estimator, property_with_solar):
        """Test solar lease is included when specified."""
        costs = estimator.estimate(property_with_solar)

        assert costs.solar_lease == 150.0

    def test_zero_solar_lease_treated_as_none(self, estimator):
        """Test zero solar_lease_monthly is treated as no solar."""
        property = MockProperty(solar_lease_monthly=0)
        costs = estimator.estimate(property)

        assert costs.solar_lease == 0.0


# =============================================================================
# HOA FEE TESTS
# =============================================================================


class TestHoaFee:
    """Test HOA fee handling."""

    def test_no_hoa_fee_when_zero(self, estimator, basic_property):
        """Test no HOA costs when hoa_fee is 0."""
        costs = estimator.estimate(basic_property)

        assert costs.hoa_fee == 0.0

    def test_hoa_fee_included_when_present(self, estimator, property_with_hoa):
        """Test HOA fee is included when specified."""
        costs = estimator.estimate(property_with_hoa)

        assert costs.hoa_fee == 200.0

    def test_none_hoa_treated_as_zero(self, estimator):
        """Test None hoa_fee is treated as no HOA."""
        property = MockProperty(hoa_fee=None)
        costs = estimator.estimate(property)

        assert costs.hoa_fee == 0.0


# =============================================================================
# MAINTENANCE RESERVE TESTS
# =============================================================================


class TestMaintenanceReserve:
    """Test maintenance reserve calculation."""

    def test_maintenance_reserve_calculation(self, estimator, basic_property):
        """Test maintenance reserve is 1% annually / 12."""
        costs = estimator.estimate(basic_property)

        # Expected: $475k * 0.01 / 12 = ~$396/month
        expected = 475000 * MAINTENANCE_RESERVE_RATE
        assert abs(costs.maintenance_reserve - expected) < 1.0

    def test_maintenance_minimum_applied(self, estimator):
        """Test maintenance minimum is applied for low-value homes."""
        property = MockProperty(price_num=100000)  # Would be ~$83/month
        costs = estimator.estimate(property)

        # Should use minimum ($200)
        assert costs.maintenance_reserve == 200.0


# =============================================================================
# TOTAL CALCULATION TESTS
# =============================================================================


class TestTotalCalculation:
    """Test total monthly cost calculation."""

    def test_total_equals_sum_of_components(self, estimator, basic_property):
        """Test that total equals sum of all components."""
        costs = estimator.estimate(basic_property)

        expected_total = sum([
            costs.mortgage,
            costs.property_tax,
            costs.insurance,
            costs.utilities,
            costs.water,
            costs.trash,
            costs.pool_maintenance,
            costs.maintenance_reserve,
            costs.hoa_fee,
            costs.solar_lease,
        ])

        assert abs(costs.total - expected_total) < 0.01

    def test_total_with_all_features(self, estimator, luxury_property):
        """Test total calculation with all cost components."""
        costs = estimator.estimate(luxury_property)

        # All components should be > 0 except HOA
        assert costs.mortgage > 0
        assert costs.property_tax > 0
        assert costs.insurance > 0
        assert costs.utilities > 0
        assert costs.water > 0
        assert costs.trash > 0
        assert costs.pool_maintenance > 0
        assert costs.maintenance_reserve > 0
        assert costs.hoa_fee == 0
        assert costs.solar_lease > 0

    def test_piti_calculation(self, estimator, basic_property):
        """Test PITI (Principal, Interest, Tax, Insurance)."""
        costs = estimator.estimate(basic_property)

        expected_piti = costs.mortgage + costs.property_tax + costs.insurance
        assert abs(costs.piti - expected_piti) < 0.01


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_sqft(self, estimator):
        """Test handling of zero square footage."""
        property = MockProperty(sqft=0)
        costs = estimator.estimate(property)

        # Should use minimum utility, not crash
        assert costs.utilities == 120.0  # Electric/gas minimum
        assert costs.water == WATER_MONTHLY_ESTIMATE
        assert costs.trash == TRASH_MONTHLY

    def test_none_sqft(self, estimator):
        """Test handling of None square footage."""
        property = MockProperty()
        property.sqft = None
        costs = estimator.estimate(property)

        # Should use minimum utility
        assert costs.utilities == 120.0  # Electric/gas minimum
        assert costs.water == WATER_MONTHLY_ESTIMATE
        assert costs.trash == TRASH_MONTHLY

    def test_very_low_price(self, estimator):
        """Test with price below down payment."""
        property = MockProperty(price_num=30000)
        costs = estimator.estimate(property)

        # No mortgage needed
        assert costs.mortgage == 0.0
        assert costs.total > 0  # Other costs still apply

    def test_very_high_price(self, estimator):
        """Test with high-value property."""
        property = MockProperty(price_num=1500000)
        costs = estimator.estimate(property)

        # Should handle without overflow
        assert costs.total > 0
        assert costs.mortgage > 5000

    def test_negative_values_handled(self, estimator):
        """Test that negative values don't cause issues."""
        property = MockProperty(
            price_num=475000,
            hoa_fee=-100,  # Invalid but shouldn't crash
            solar_lease_monthly=-50,
        )
        costs = estimator.estimate(property)

        # Negative values treated as 0
        assert costs.hoa_fee == 0.0
        assert costs.solar_lease == 0.0


# =============================================================================
# ESTIMATOR CONFIGURATION TESTS
# =============================================================================


class TestEstimatorConfiguration:
    """Test estimator configuration options."""

    def test_default_down_payment(self, estimator):
        """Test default down payment is $50,000."""
        assert estimator.down_payment == 50000

    def test_default_mortgage_rate(self, estimator):
        """Test default mortgage rate is 6.99%."""
        assert estimator.mortgage_rate == MORTGAGE_RATE_30YR

    def test_custom_rate_config(self):
        """Test using custom RateConfig."""
        config = RateConfig(
            mortgage_rate=0.055,
            down_payment=100000,
        )
        estimator = MonthlyCostEstimator(config=config)

        assert estimator.mortgage_rate == 0.055
        assert estimator.down_payment == 100000

    def test_rate_config_overrides_individual_args(self):
        """Test that config parameter overrides rate and down_payment."""
        config = RateConfig(mortgage_rate=0.06, down_payment=75000)
        estimator = MonthlyCostEstimator(
            down_payment=50000,  # Should be ignored
            rate=0.07,  # Should be ignored
            config=config,
        )

        assert estimator.down_payment == 75000
        assert estimator.mortgage_rate == 0.06


# =============================================================================
# ESTIMATE FROM VALUES TESTS
# =============================================================================


class TestEstimateFromValues:
    """Test estimate_from_values convenience method."""

    def test_basic_estimate_from_values(self, estimator):
        """Test basic estimate from individual values."""
        costs = estimator.estimate_from_values(
            price=450000,
            sqft=2000,
            has_pool=False,
            hoa_fee=0,
        )

        assert isinstance(costs, MonthlyCosts)
        assert costs.mortgage > 0
        assert costs.pool_maintenance == 0

    def test_estimate_from_values_with_pool(self, estimator):
        """Test estimate with pool included."""
        costs = estimator.estimate_from_values(
            price=500000,
            sqft=2500,
            has_pool=True,
        )

        assert costs.pool_maintenance == POOL_TOTAL_MONTHLY

    def test_estimate_from_values_with_all_options(self, estimator):
        """Test estimate with all options specified."""
        costs = estimator.estimate_from_values(
            price=550000,
            sqft=2800,
            has_pool=True,
            hoa_fee=150,
            solar_lease=175,
            tax_annual=5000,
        )

        assert costs.hoa_fee == 150.0
        assert costs.solar_lease == 175.0
        assert costs.property_tax == 5000 / 12


# =============================================================================
# DETAILED ESTIMATE TESTS
# =============================================================================


class TestDetailedEstimate:
    """Test estimate_detailed method."""

    def test_detailed_estimate_returns_cost_estimate(
        self, estimator, basic_property
    ):
        """Test that estimate_detailed returns CostEstimate."""
        result = estimator.estimate_detailed(basic_property)

        assert isinstance(result, CostEstimate)
        assert isinstance(result.monthly_costs, MonthlyCosts)

    def test_detailed_estimate_metadata(self, estimator, basic_property):
        """Test detailed estimate includes correct metadata."""
        result = estimator.estimate_detailed(basic_property)

        assert result.home_value == 475000
        assert result.loan_amount == 475000 - 50000
        assert result.down_payment == 50000
        assert result.interest_rate == MORTGAGE_RATE_30YR
        assert result.sqft == 2200

    def test_detailed_estimate_notes_for_tax(self, estimator, basic_property):
        """Test notes are generated when tax is estimated."""
        result = estimator.estimate_detailed(basic_property)

        # Should have note about estimated tax
        assert any("tax estimated" in note.lower() for note in result.notes)

    def test_detailed_estimate_notes_for_pool(self, estimator, property_with_pool):
        """Test notes mention pool costs."""
        result = estimator.estimate_detailed(property_with_pool)

        assert any("pool" in note.lower() for note in result.notes)

    def test_detailed_estimate_notes_for_solar(self, estimator, property_with_solar):
        """Test notes warn about solar lease transfer."""
        result = estimator.estimate_detailed(property_with_solar)

        assert any("solar" in note.lower() for note in result.notes)


# =============================================================================
# MAX AFFORDABLE PRICE TESTS
# =============================================================================


class TestMaxAffordablePrice:
    """Test max affordable price calculation."""

    def test_max_price_within_budget(self, estimator):
        """Test calculated max price results in costs under budget."""
        max_payment = 4000.0
        max_price = estimator.calculate_max_affordable_price(max_payment)

        # Verify the price works
        costs = estimator.estimate_from_values(price=int(max_price))
        assert costs.total <= max_payment + 50  # Allow small tolerance

    def test_max_price_with_pool(self, estimator):
        """Test max price is lower when pool is included."""
        max_payment = 4000.0

        price_no_pool = estimator.calculate_max_affordable_price(
            max_payment, has_pool=False
        )
        price_with_pool = estimator.calculate_max_affordable_price(
            max_payment, has_pool=True
        )

        assert price_with_pool < price_no_pool

    def test_max_price_with_hoa(self, estimator):
        """Test max price is lower when HOA is included."""
        max_payment = 4000.0

        price_no_hoa = estimator.calculate_max_affordable_price(
            max_payment, hoa_fee=0
        )
        price_with_hoa = estimator.calculate_max_affordable_price(
            max_payment, hoa_fee=200
        )

        assert price_with_hoa < price_no_hoa


# =============================================================================
# MONTHLY COSTS MODEL TESTS
# =============================================================================


class TestMonthlyCostsModel:
    """Test MonthlyCosts dataclass behavior."""

    def test_monthly_costs_is_frozen(self):
        """Test MonthlyCosts is immutable."""
        costs = MonthlyCosts(
            mortgage=2500,
            property_tax=300,
            insurance=250,
            utilities=200,
            water=90,
            trash=40,
            pool_maintenance=0,
            maintenance_reserve=400,
            hoa_fee=0,
            solar_lease=0,
        )

        with pytest.raises(AttributeError):
            costs.mortgage = 3000

    def test_monthly_costs_to_dict(self):
        """Test to_dict includes all fields."""
        costs = MonthlyCosts(
            mortgage=2500,
            property_tax=300,
            insurance=250,
            utilities=200,
            water=90,
            trash=40,
            pool_maintenance=200,
            maintenance_reserve=400,
            hoa_fee=150,
            solar_lease=100,
        )

        d = costs.to_dict()

        assert d["mortgage"] == 2500
        assert d["water"] == 90
        assert d["trash"] == 40
        assert d["total"] == costs.total
        assert d["piti"] == costs.piti
        assert "fixed_costs" in d
        assert "variable_costs" in d

    def test_monthly_costs_fixed_vs_variable(self):
        """Test fixed and variable cost categorization."""
        costs = MonthlyCosts(
            mortgage=2500,
            property_tax=300,
            insurance=250,
            utilities=200,
            water=90,
            trash=40,
            pool_maintenance=200,
            maintenance_reserve=400,
            hoa_fee=150,
            solar_lease=100,
        )

        # Fixed: mortgage + tax + insurance + HOA
        assert costs.fixed_costs == 2500 + 300 + 250 + 150

        # Variable: utilities + water + trash + pool + maintenance
        assert costs.variable_costs == 200 + 90 + 40 + 200 + 400

    def test_monthly_costs_str(self):
        """Test string representation."""
        costs = MonthlyCosts(
            mortgage=2500,
            property_tax=300,
            insurance=250,
            utilities=200,
            water=90,
            trash=40,
            pool_maintenance=0,
            maintenance_reserve=400,
            hoa_fee=0,
            solar_lease=0,
        )

        s = str(costs)
        assert "MonthlyCosts" in s
        assert "total" in s


# =============================================================================
# RATE CONFIG TESTS
# =============================================================================


class TestRateConfig:
    """Test RateConfig behavior."""

    def test_rate_config_with_rate(self):
        """Test with_rate creates new config."""
        config = RateConfig()
        new_config = config.with_rate(0.055)

        assert new_config.mortgage_rate == 0.055
        assert config.mortgage_rate == MORTGAGE_RATE_30YR  # Original unchanged

    def test_rate_config_with_down_payment(self):
        """Test with_down_payment creates new config."""
        config = RateConfig()
        new_config = config.with_down_payment(100000)

        assert new_config.down_payment == 100000
        assert config.down_payment == DOWN_PAYMENT_DEFAULT  # Original unchanged

    def test_rate_config_pool_total(self):
        """Test pool_total property."""
        config = RateConfig(pool_maintenance=125, pool_energy=75)
        assert config.pool_total == 200


# =============================================================================
# INTEGRATION WITH DOMAIN PROPERTY
# =============================================================================


class TestDomainPropertyIntegration:
    """Test integration with domain Property entity."""

    def test_works_with_domain_property(self, estimator, sample_property):
        """Test estimator works with actual domain Property."""
        costs = estimator.estimate(sample_property)

        assert isinstance(costs, MonthlyCosts)
        assert costs.total > 0

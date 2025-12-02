"""Monthly cost estimation service for Phoenix home analysis.

This module provides the MonthlyCostEstimator class for calculating
comprehensive monthly housing costs including mortgage, taxes, insurance,
utilities, maintenance, and Arizona-specific costs like pool maintenance.
"""

from typing import Protocol

from .models import CostEstimate, MonthlyCosts
from .rates import (
    DOWN_PAYMENT_DEFAULT,
    MORTGAGE_RATE_30YR,
    RateConfig,
)


class PropertyLike(Protocol):
    """Protocol for objects that can provide property data for cost estimation.

    This protocol allows the estimator to work with any object that has
    the required attributes, including the domain Property entity.
    """

    price_num: int
    sqft: int
    has_pool: bool | None
    hoa_fee: int | None
    solar_lease_monthly: int | None
    tax_annual: int | None


class MonthlyCostEstimator:
    """Service for calculating monthly housing costs.

    Calculates comprehensive monthly costs including:
    - Mortgage principal and interest (P&I)
    - Property tax (monthly portion)
    - Homeowner's insurance
    - Utilities (estimated from sqft)
    - Pool maintenance (if applicable)
    - Maintenance reserve (1% annually)
    - HOA fee
    - Solar lease (if applicable)

    Uses Arizona-specific rates and assumptions for accurate Phoenix-area
    home cost estimation.

    Example:
        estimator = MonthlyCostEstimator(down_payment=50000)
        costs = estimator.estimate(property)
        print(f"Total monthly: ${costs.total:,.2f}")
    """

    def __init__(
        self,
        down_payment: float = DOWN_PAYMENT_DEFAULT,
        rate: float | None = None,
        config: RateConfig | None = None,
    ) -> None:
        """Initialize the cost estimator.

        Args:
            down_payment: Down payment amount (default: $50,000)
            rate: Annual mortgage interest rate (default: 6.99%)
            config: Full rate configuration object (overrides other args)
        """
        if config is not None:
            self._config = config
        else:
            self._config = RateConfig(
                mortgage_rate=rate if rate is not None else MORTGAGE_RATE_30YR,
                down_payment=down_payment,
            )

    @property
    def down_payment(self) -> float:
        """Current down payment amount."""
        return self._config.down_payment

    @property
    def mortgage_rate(self) -> float:
        """Current annual mortgage interest rate."""
        return self._config.mortgage_rate

    @property
    def config(self) -> RateConfig:
        """Current rate configuration."""
        return self._config

    def estimate(self, property: PropertyLike) -> MonthlyCosts:
        """Calculate monthly costs for a property.

        Args:
            property: Property object with required attributes

        Returns:
            MonthlyCosts breakdown for the property
        """
        home_value = float(property.price_num)
        sqft = property.sqft if property.sqft else 0

        # Calculate each component
        mortgage = self._calculate_mortgage(home_value)
        property_tax = self._calculate_property_tax(home_value, property.tax_annual)
        insurance = self._calculate_insurance(home_value)
        utilities = self._calculate_utilities(sqft)
        water = self._calculate_water()
        trash = self._calculate_trash()
        pool_maintenance = self._calculate_pool_costs(property.has_pool)
        maintenance_reserve = self._calculate_maintenance_reserve(home_value)
        hoa_fee = self._get_hoa_fee(property.hoa_fee)
        solar_lease = self._get_solar_lease(property.solar_lease_monthly)

        return MonthlyCosts(
            mortgage=mortgage,
            property_tax=property_tax,
            insurance=insurance,
            utilities=utilities,
            water=water,
            trash=trash,
            pool_maintenance=pool_maintenance,
            maintenance_reserve=maintenance_reserve,
            hoa_fee=hoa_fee,
            solar_lease=solar_lease,
        )

    def estimate_detailed(self, property: PropertyLike) -> CostEstimate:
        """Calculate detailed cost estimate with metadata.

        Args:
            property: Property object with required attributes

        Returns:
            CostEstimate with breakdown and estimation context
        """
        home_value = float(property.price_num)
        loan_amount = max(0.0, home_value - self._config.down_payment)
        sqft = property.sqft if property.sqft else 0

        monthly_costs = self.estimate(property)
        notes = self._generate_notes(property, loan_amount)

        return CostEstimate(
            monthly_costs=monthly_costs,
            home_value=home_value,
            loan_amount=loan_amount,
            down_payment=self._config.down_payment,
            interest_rate=self._config.mortgage_rate,
            sqft=sqft,
            has_pool=bool(property.has_pool),
            has_solar_lease=bool(property.solar_lease_monthly),
            notes=tuple(notes),
        )

    def estimate_from_values(
        self,
        price: int,
        sqft: int = 2000,
        has_pool: bool = False,
        hoa_fee: int = 0,
        solar_lease: int = 0,
        tax_annual: int | None = None,
    ) -> MonthlyCosts:
        """Calculate monthly costs from individual values.

        Convenience method for quick estimates without a property object.

        Args:
            price: Home purchase price
            sqft: Square footage (default: 2000)
            has_pool: Whether property has a pool
            hoa_fee: Monthly HOA fee (0 if none)
            solar_lease: Monthly solar lease payment (0 if none)
            tax_annual: Annual property tax (None to estimate)

        Returns:
            MonthlyCosts breakdown
        """
        home_value = float(price)

        mortgage = self._calculate_mortgage(home_value)
        property_tax = self._calculate_property_tax(home_value, tax_annual)
        insurance = self._calculate_insurance(home_value)
        utilities = self._calculate_utilities(sqft)
        water = self._calculate_water()
        trash = self._calculate_trash()
        pool_maintenance = self._calculate_pool_costs(has_pool)
        maintenance_reserve = self._calculate_maintenance_reserve(home_value)

        return MonthlyCosts(
            mortgage=mortgage,
            property_tax=property_tax,
            insurance=insurance,
            utilities=utilities,
            water=water,
            trash=trash,
            pool_maintenance=pool_maintenance,
            maintenance_reserve=maintenance_reserve,
            hoa_fee=float(hoa_fee),
            solar_lease=float(solar_lease),
        )

    def _calculate_mortgage(self, home_value: float) -> float:
        """Calculate monthly mortgage payment (P&I).

        Uses standard amortization formula:
        M = P * [r(1+r)^n] / [(1+r)^n - 1]

        Where:
        - M = monthly payment
        - P = principal (loan amount)
        - r = monthly interest rate
        - n = number of payments

        Args:
            home_value: Property purchase price

        Returns:
            Monthly principal and interest payment
        """
        loan_amount = max(0.0, home_value - self._config.down_payment)

        if loan_amount <= 0:
            return 0.0

        monthly_rate = self._config.mortgage_rate / 12
        num_payments = self._config.loan_term_months

        if monthly_rate <= 0:
            # Zero interest rate: simple division
            return loan_amount / num_payments

        # Standard amortization formula
        factor = (1 + monthly_rate) ** num_payments
        mortgage = loan_amount * (monthly_rate * factor) / (factor - 1)

        return round(mortgage, 2)

    def _calculate_property_tax(
        self,
        home_value: float,
        tax_annual: int | None,
    ) -> float:
        """Calculate monthly property tax.

        Uses actual annual tax if available from county assessor,
        otherwise estimates based on effective tax rate.

        Args:
            home_value: Property value
            tax_annual: Known annual tax amount (if available)

        Returns:
            Monthly property tax amount
        """
        if tax_annual is not None and tax_annual > 0:
            # Use actual tax data from county assessor
            return float(tax_annual) / 12

        # Estimate based on effective rate
        annual_tax = home_value * self._config.property_tax_rate
        return round(annual_tax / 12, 2)

    def _calculate_insurance(self, home_value: float) -> float:
        """Calculate monthly homeowner's insurance.

        Based on Arizona average of ~$6.50 per $1,000 of home value.

        Args:
            home_value: Property value

        Returns:
            Monthly insurance premium
        """
        annual_insurance = (home_value / 1000) * self._config.insurance_per_1k
        return round(annual_insurance / 12, 2)

    def _calculate_utilities(self, sqft: int) -> float:
        """Calculate estimated monthly utilities (electric and gas only).

        Arizona-specific estimate including higher summer electricity
        due to A/C usage. Based on ~$0.08 per sqft monthly average.
        Water and trash are calculated separately.

        Args:
            sqft: Property square footage

        Returns:
            Estimated monthly electric/gas utility costs
        """
        if sqft <= 0:
            return self._config.utility_min

        estimated = sqft * self._config.utility_rate_per_sqft

        # Apply min/max bounds
        return round(
            max(self._config.utility_min, min(estimated, self._config.utility_max)),
            2,
        )

    def _calculate_water(self) -> float:
        """Calculate monthly water bill.

        Based on Arizona city water averages:
        - Base charge: ~$30/month
        - Usage: ~$5 per 1,000 gallons
        - Average household: ~12,000 gallons/month
        - Total estimate: ~$90/month (spec range: $80-120/mo)

        Returns:
            Estimated monthly water cost
        """
        return self._config.water_monthly

    def _calculate_trash(self) -> float:
        """Calculate monthly trash/recycling pickup cost.

        Based on Maricopa County city averages:
        - Average: ~$40/month (spec range: $30-50/mo)

        Returns:
            Monthly trash pickup cost
        """
        return self._config.trash_monthly

    def _calculate_pool_costs(self, has_pool: bool | None) -> float:
        """Calculate monthly pool maintenance and energy costs.

        Arizona pools require year-round maintenance:
        - Service (cleaning, chemicals): ~$125/month
        - Energy (pump, heater): ~$75/month

        Args:
            has_pool: Whether property has a pool

        Returns:
            Monthly pool costs (0 if no pool)
        """
        if not has_pool:
            return 0.0
        return self._config.pool_total

    def _calculate_maintenance_reserve(self, home_value: float) -> float:
        """Calculate monthly maintenance reserve.

        Standard rule: 1% of home value annually for maintenance/repairs.
        Monthly = (home_value * 0.01) / 12

        Args:
            home_value: Property value

        Returns:
            Monthly maintenance reserve
        """
        monthly_reserve = home_value * self._config.maintenance_rate

        # Apply minimum
        return round(max(monthly_reserve, self._config.maintenance_min), 2)

    def _get_hoa_fee(self, hoa_fee: int | None) -> float:
        """Get monthly HOA fee.

        Args:
            hoa_fee: Monthly HOA fee from property data

        Returns:
            HOA fee or 0 if none
        """
        if hoa_fee is None or hoa_fee <= 0:
            return 0.0
        return float(hoa_fee)

    def _get_solar_lease(self, solar_lease_monthly: int | None) -> float:
        """Get monthly solar lease payment.

        Args:
            solar_lease_monthly: Monthly solar lease from property data

        Returns:
            Solar lease payment or 0 if none
        """
        if solar_lease_monthly is None or solar_lease_monthly <= 0:
            return 0.0
        return float(solar_lease_monthly)

    def _generate_notes(
        self,
        property: PropertyLike,
        loan_amount: float,
    ) -> list[str]:
        """Generate estimation notes and warnings.

        Args:
            property: Property being estimated
            loan_amount: Calculated loan amount

        Returns:
            List of note strings
        """
        notes = []

        # Down payment coverage
        if property.price_num <= self._config.down_payment:
            notes.append("Down payment covers full purchase price (no mortgage)")

        # Tax estimation
        if property.tax_annual is None or property.tax_annual <= 0:
            notes.append(
                f"Property tax estimated at {self._config.property_tax_rate:.2%} rate"
            )

        # Pool costs
        if property.has_pool:
            notes.append("Pool maintenance costs included ($200/month)")

        # Solar lease warning
        if property.solar_lease_monthly:
            notes.append(
                f"Solar lease: ${property.solar_lease_monthly}/month "
                "(verify transfer terms)"
            )

        # High LTV warning
        if property.price_num > 0:
            ltv = loan_amount / property.price_num
            if ltv > 0.80:
                notes.append(
                    f"LTV ratio {ltv:.1%} may require PMI (not included in estimate)"
                )

        return notes

    def calculate_max_affordable_price(
        self,
        max_monthly_payment: float,
        sqft_estimate: int = 2000,
        has_pool: bool = False,
        hoa_fee: int = 0,
        solar_lease: int = 0,
    ) -> float:
        """Calculate maximum affordable home price given monthly budget.

        Iteratively finds the highest price where total monthly costs
        stay within the specified budget.

        Args:
            max_monthly_payment: Maximum total monthly housing cost
            sqft_estimate: Estimated square footage for utilities
            has_pool: Whether to include pool costs
            hoa_fee: Expected monthly HOA fee
            solar_lease: Expected monthly solar lease

        Returns:
            Maximum affordable home price
        """
        # Binary search for max price
        low, high = 0.0, 2_000_000.0
        tolerance = 1000.0  # $1k precision

        while high - low > tolerance:
            mid = (low + high) / 2
            costs = self.estimate_from_values(
                price=int(mid),
                sqft=sqft_estimate,
                has_pool=has_pool,
                hoa_fee=hoa_fee,
                solar_lease=solar_lease,
            )

            if costs.total <= max_monthly_payment:
                low = mid
            else:
                high = mid

        return round(low, -3)  # Round to nearest $1k

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"MonthlyCostEstimator("
            f"down_payment=${self._config.down_payment:,.0f}, "
            f"rate={self._config.mortgage_rate:.2%})"
        )

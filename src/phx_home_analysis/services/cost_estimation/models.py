"""Data models for monthly housing cost estimation.

This module defines immutable value objects representing monthly cost breakdowns
for Phoenix-area home ownership analysis.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MonthlyCosts:
    """Immutable monthly cost breakdown for a property.

    All values are in USD per month. Uses frozen=True for immutability,
    making instances hashable and safe for use in caches or sets.

    Attributes:
        mortgage: Principal and interest payment
        property_tax: Monthly portion of annual property tax
        insurance: Homeowner's insurance premium
        utilities: Estimated monthly utilities (electric, gas only)
        water: Monthly water bill
        trash: Monthly trash/recycling pickup
        pool_maintenance: Pool service and energy costs (0 if no pool)
        maintenance_reserve: 1% annual maintenance reserve (monthly)
        hoa_fee: Monthly HOA fee (0 if no HOA)
        solar_lease: Monthly solar panel lease payment (0 if none)
    """

    mortgage: float  # P&I
    property_tax: float
    insurance: float
    utilities: float  # Electric/gas only
    water: float = 0.0  # Water bill
    trash: float = 0.0  # Trash/recycling pickup
    pool_maintenance: float = 0.0
    maintenance_reserve: float = 0.0
    hoa_fee: float = 0.0
    solar_lease: float = 0.0

    @property
    def total(self) -> float:
        """Calculate total monthly housing cost.

        Returns:
            Sum of all monthly cost components
        """
        return sum([
            self.mortgage,
            self.property_tax,
            self.insurance,
            self.utilities,
            self.water,
            self.trash,
            self.pool_maintenance,
            self.maintenance_reserve,
            self.hoa_fee,
            self.solar_lease,
        ])

    @property
    def piti(self) -> float:
        """Calculate PITI (Principal, Interest, Tax, Insurance).

        This is the standard lender-required payment calculation.

        Returns:
            Sum of mortgage, property tax, and insurance
        """
        return self.mortgage + self.property_tax + self.insurance

    @property
    def fixed_costs(self) -> float:
        """Calculate fixed monthly costs (mortgage, tax, insurance, HOA).

        These costs are relatively stable month-to-month.

        Returns:
            Sum of fixed cost components
        """
        return self.mortgage + self.property_tax + self.insurance + self.hoa_fee

    @property
    def variable_costs(self) -> float:
        """Calculate variable monthly costs (utilities, water, trash, maintenance, pool).

        These costs can fluctuate based on usage and conditions.

        Returns:
            Sum of variable cost components
        """
        return (
            self.utilities
            + self.water
            + self.trash
            + self.pool_maintenance
            + self.maintenance_reserve
        )

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with all cost components and totals
        """
        return {
            "mortgage": self.mortgage,
            "property_tax": self.property_tax,
            "insurance": self.insurance,
            "utilities": self.utilities,
            "water": self.water,
            "trash": self.trash,
            "pool_maintenance": self.pool_maintenance,
            "maintenance_reserve": self.maintenance_reserve,
            "hoa_fee": self.hoa_fee,
            "solar_lease": self.solar_lease,
            "total": self.total,
            "piti": self.piti,
            "fixed_costs": self.fixed_costs,
            "variable_costs": self.variable_costs,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"MonthlyCosts(total=${self.total:,.2f}, "
            f"mortgage=${self.mortgage:,.2f}, "
            f"tax=${self.property_tax:,.2f}, "
            f"insurance=${self.insurance:,.2f})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"MonthlyCosts("
            f"mortgage={self.mortgage:.2f}, "
            f"property_tax={self.property_tax:.2f}, "
            f"insurance={self.insurance:.2f}, "
            f"utilities={self.utilities:.2f}, "
            f"water={self.water:.2f}, "
            f"trash={self.trash:.2f}, "
            f"pool_maintenance={self.pool_maintenance:.2f}, "
            f"maintenance_reserve={self.maintenance_reserve:.2f}, "
            f"hoa_fee={self.hoa_fee:.2f}, "
            f"solar_lease={self.solar_lease:.2f})"
        )


@dataclass(frozen=True)
class CostEstimate:
    """Extended cost estimate with additional context.

    Includes the monthly breakdown plus metadata about the estimate
    such as assumptions and whether any values were estimated.

    Attributes:
        monthly_costs: The detailed monthly cost breakdown
        home_value: Property value used for calculations
        loan_amount: Amount financed after down payment
        down_payment: Down payment amount
        interest_rate: Annual interest rate used
        sqft: Square footage used for utility estimates
        has_pool: Whether pool costs are included
        has_solar_lease: Whether solar lease is included
        notes: List of estimation notes or warnings
    """

    monthly_costs: MonthlyCosts
    home_value: float
    loan_amount: float
    down_payment: float
    interest_rate: float
    sqft: int
    has_pool: bool
    has_solar_lease: bool
    notes: tuple[str, ...] = ()

    @property
    def total_monthly(self) -> float:
        """Total monthly cost from the breakdown.

        Returns:
            Total monthly housing cost
        """
        return self.monthly_costs.total

    @property
    def annual_cost(self) -> float:
        """Estimated annual housing cost.

        Returns:
            Monthly cost multiplied by 12
        """
        return self.monthly_costs.total * 12

    @property
    def ltv_ratio(self) -> float:
        """Loan-to-value ratio.

        Returns:
            Loan amount divided by home value (0-1 scale)
        """
        if self.home_value == 0:
            return 0.0
        return self.loan_amount / self.home_value

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with all estimate details
        """
        return {
            "monthly_costs": self.monthly_costs.to_dict(),
            "home_value": self.home_value,
            "loan_amount": self.loan_amount,
            "down_payment": self.down_payment,
            "interest_rate": self.interest_rate,
            "sqft": self.sqft,
            "has_pool": self.has_pool,
            "has_solar_lease": self.has_solar_lease,
            "total_monthly": self.total_monthly,
            "annual_cost": self.annual_cost,
            "ltv_ratio": self.ltv_ratio,
            "notes": list(self.notes),
        }

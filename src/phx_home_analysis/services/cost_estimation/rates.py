"""2025 Arizona rate data for housing cost estimation.

This module contains current market rates and constants for calculating
monthly housing costs in the Phoenix metropolitan area.

Data sources:
- Mortgage rates: Freddie Mac PMMS (Dec 2024)
- Insurance rates: Arizona Department of Insurance averages
- Property tax: Maricopa County Assessor effective rates
- Utilities: APS/SRP average residential rates
- Pool costs: Local pool service industry averages

Last updated: December 2024
"""

from dataclasses import dataclass
from typing import Final


# =============================================================================
# MORTGAGE RATES AND TERMS
# =============================================================================

# 30-year fixed mortgage rate (6.99% as of Dec 2024)
MORTGAGE_RATE_30YR: Final[float] = 0.0699

# 15-year fixed mortgage rate (for reference)
MORTGAGE_RATE_15YR: Final[float] = 0.0625

# Standard loan terms in months
LOAN_TERM_30YR_MONTHS: Final[int] = 360
LOAN_TERM_15YR_MONTHS: Final[int] = 180

# Default down payment for first-time homebuyer analysis
DOWN_PAYMENT_DEFAULT: Final[float] = 50000.0

# PMI threshold (loan-to-value ratio above which PMI is required)
PMI_THRESHOLD_LTV: Final[float] = 0.80

# Annual PMI rate (percentage of loan amount)
PMI_ANNUAL_RATE: Final[float] = 0.005  # 0.5% of loan


# =============================================================================
# INSURANCE RATES
# =============================================================================

# Annual homeowner's insurance per $1,000 of home value
# Arizona average: ~$6.50 per $1k (varies by coverage and location)
INSURANCE_ANNUAL_PER_1K: Final[float] = 6.50

# Minimum annual insurance (base coverage)
INSURANCE_MINIMUM_ANNUAL: Final[float] = 800.0


# =============================================================================
# PROPERTY TAX RATES
# =============================================================================

# Effective property tax rate in Maricopa County
# Based on Limited Property Value (LPV), not Full Cash Value (FCV)
# Actual rate varies by municipality and special districts
PROPERTY_TAX_RATE: Final[float] = 0.0066  # ~0.66% effective rate

# Alternative: Use actual tax_annual from county assessor when available


# =============================================================================
# UTILITY RATES (Arizona-specific)
# =============================================================================

# Monthly utility cost per square foot (AZ average)
# Electric and gas only (water and trash are separate line items)
# AZ has higher electric costs due to A/C usage (June-Sept)
UTILITY_RATE_PER_SQFT: Final[float] = 0.08  # ~$0.08/sqft/month (electric/gas only)

# Minimum monthly utilities (small home baseline)
UTILITY_MINIMUM_MONTHLY: Final[float] = 120.0  # Electric/gas only

# Maximum monthly utilities cap (very large homes)
UTILITY_MAXIMUM_MONTHLY: Final[float] = 500.0  # Electric/gas only


# =============================================================================
# WATER COSTS (Arizona-specific)
# =============================================================================

# City water rates (Maricopa County average)
# Base service charge + usage-based
WATER_MONTHLY_BASE: Final[float] = 30.0  # Base service charge
WATER_RATE_PER_KGAL: Final[float] = 5.0  # Per 1,000 gallons
WATER_AVG_USAGE_KGAL: Final[float] = 12.0  # Average AZ household (12k gal/mo)

# Calculated monthly water estimate: ~$90/mo
WATER_MONTHLY_ESTIMATE: Final[float] = (
    WATER_MONTHLY_BASE + (WATER_RATE_PER_KGAL * WATER_AVG_USAGE_KGAL)
)


# =============================================================================
# TRASH COSTS (Arizona-specific)
# =============================================================================

# City trash/recycling pickup (Maricopa County cities average)
TRASH_MONTHLY: Final[float] = 40.0  # Average for Phoenix metro cities


# =============================================================================
# POOL COSTS (Arizona-specific)
# =============================================================================

# Monthly pool service (cleaning, chemical balance)
POOL_BASE_MAINTENANCE: Final[float] = 125.0  # $125/mo average

# Monthly pool energy cost (pump, heater, cleaning system)
POOL_ENERGY_MONTHLY: Final[float] = 75.0  # $75/mo average

# Combined monthly pool cost
POOL_TOTAL_MONTHLY: Final[float] = POOL_BASE_MAINTENANCE + POOL_ENERGY_MONTHLY

# Seasonal variation note: Summer pool costs can be 20-30% higher


# =============================================================================
# MAINTENANCE RESERVES
# =============================================================================

# Annual maintenance as percentage of home value
# Rule of thumb: 1% annually for maintenance/repairs
MAINTENANCE_RESERVE_ANNUAL_RATE: Final[float] = 0.01  # 1% annually

# Monthly maintenance reserve rate (1% / 12 months)
MAINTENANCE_RESERVE_RATE: Final[float] = MAINTENANCE_RESERVE_ANNUAL_RATE / 12

# Minimum monthly maintenance reserve
MAINTENANCE_MINIMUM_MONTHLY: Final[float] = 200.0


# =============================================================================
# SOLAR LEASE DEFAULTS
# =============================================================================

# Typical solar lease monthly payment range in AZ
SOLAR_LEASE_TYPICAL_MIN: Final[float] = 100.0
SOLAR_LEASE_TYPICAL_MAX: Final[float] = 200.0

# Default solar lease payment when not specified
SOLAR_LEASE_DEFAULT: Final[float] = 150.0


# =============================================================================
# RATE CONFIGURATION DATACLASS
# =============================================================================

@dataclass(frozen=True)
class RateConfig:
    """Configuration object for rate parameters.

    Allows customization of rates while providing sensible defaults.
    Immutable to prevent accidental modification during calculations.
    """

    # Mortgage
    mortgage_rate: float = MORTGAGE_RATE_30YR
    loan_term_months: int = LOAN_TERM_30YR_MONTHS
    down_payment: float = DOWN_PAYMENT_DEFAULT

    # Insurance and tax
    insurance_per_1k: float = INSURANCE_ANNUAL_PER_1K
    property_tax_rate: float = PROPERTY_TAX_RATE

    # Utilities (electric/gas only)
    utility_rate_per_sqft: float = UTILITY_RATE_PER_SQFT
    utility_min: float = UTILITY_MINIMUM_MONTHLY
    utility_max: float = UTILITY_MAXIMUM_MONTHLY

    # Water
    water_monthly: float = WATER_MONTHLY_ESTIMATE

    # Trash
    trash_monthly: float = TRASH_MONTHLY

    # Pool
    pool_maintenance: float = POOL_BASE_MAINTENANCE
    pool_energy: float = POOL_ENERGY_MONTHLY

    # Maintenance
    maintenance_rate: float = MAINTENANCE_RESERVE_RATE
    maintenance_min: float = MAINTENANCE_MINIMUM_MONTHLY

    # Solar
    solar_lease_default: float = SOLAR_LEASE_DEFAULT

    @property
    def pool_total(self) -> float:
        """Total monthly pool cost.

        Returns:
            Sum of maintenance and energy costs
        """
        return self.pool_maintenance + self.pool_energy

    def with_rate(self, mortgage_rate: float) -> "RateConfig":
        """Create new config with different mortgage rate.

        Args:
            mortgage_rate: New annual mortgage rate

        Returns:
            New RateConfig with updated rate
        """
        return RateConfig(
            mortgage_rate=mortgage_rate,
            loan_term_months=self.loan_term_months,
            down_payment=self.down_payment,
            insurance_per_1k=self.insurance_per_1k,
            property_tax_rate=self.property_tax_rate,
            utility_rate_per_sqft=self.utility_rate_per_sqft,
            utility_min=self.utility_min,
            utility_max=self.utility_max,
            water_monthly=self.water_monthly,
            trash_monthly=self.trash_monthly,
            pool_maintenance=self.pool_maintenance,
            pool_energy=self.pool_energy,
            maintenance_rate=self.maintenance_rate,
            maintenance_min=self.maintenance_min,
            solar_lease_default=self.solar_lease_default,
        )

    def with_down_payment(self, down_payment: float) -> "RateConfig":
        """Create new config with different down payment.

        Args:
            down_payment: New down payment amount

        Returns:
            New RateConfig with updated down payment
        """
        return RateConfig(
            mortgage_rate=self.mortgage_rate,
            loan_term_months=self.loan_term_months,
            down_payment=down_payment,
            insurance_per_1k=self.insurance_per_1k,
            property_tax_rate=self.property_tax_rate,
            utility_rate_per_sqft=self.utility_rate_per_sqft,
            utility_min=self.utility_min,
            utility_max=self.utility_max,
            water_monthly=self.water_monthly,
            trash_monthly=self.trash_monthly,
            pool_maintenance=self.pool_maintenance,
            pool_energy=self.pool_energy,
            maintenance_rate=self.maintenance_rate,
            maintenance_min=self.maintenance_min,
            solar_lease_default=self.solar_lease_default,
        )


# Default rate configuration
DEFAULT_RATES: Final[RateConfig] = RateConfig()

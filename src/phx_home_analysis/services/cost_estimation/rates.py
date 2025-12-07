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

Note: Core rate constants are defined in config/constants.py
This module primarily provides the RateConfig dataclass for rate management.
"""

from dataclasses import dataclass
from typing import Final

from ...config.constants import (
    INSURANCE_RATE_PER_1K,
    MAINTENANCE_MINIMUM_MONTHLY,
    MAINTENANCE_RESERVE_MONTHLY_RATE,
    MORTGAGE_RATE_30YR,
    MORTGAGE_TERM_MONTHS,
    POOL_ENERGY_MONTHLY,
    POOL_SERVICE_MONTHLY,
    PROPERTY_TAX_RATE,
    SOLAR_LEASE_DEFAULT,
    TRASH_MONTHLY,
    UTILITY_MAXIMUM_MONTHLY,
    UTILITY_MINIMUM_MONTHLY,
    UTILITY_RATE_PER_SQFT,
    WATER_MONTHLY_ESTIMATE,
)

# =============================================================================
# MORTGAGE RATES AND TERMS
# =============================================================================
# All mortgage constants are imported from config.constants
# See constants.py for documentation and data sources

# 15-year fixed mortgage rate (for reference)
MORTGAGE_RATE_15YR: Final[float] = 0.0625

# 15-year mortgage term in months
LOAN_TERM_15YR_MONTHS: Final[int] = 180

# Default down payment for first-time homebuyer analysis
DOWN_PAYMENT_DEFAULT: Final[float] = 50000.0

# PMI threshold (loan-to-value ratio above which PMI is required)
PMI_THRESHOLD_LTV: Final[float] = 0.80

# Annual PMI rate (percentage of loan amount)
PMI_ANNUAL_RATE: Final[float] = 0.005  # 0.5% of loan

# Re-export aliases for backward compatibility (already imported from constants)
# MORTGAGE_RATE_30YR already imported above
LOAN_TERM_30YR_MONTHS: Final[int] = MORTGAGE_TERM_MONTHS


# =============================================================================
# INSURANCE RATES
# =============================================================================
# Insurance constants are imported from config.constants
# See constants.py for documentation

# Minimum annual insurance (base coverage)
INSURANCE_MINIMUM_ANNUAL: Final[float] = 800.0

# Re-export from constants for backward compatibility
INSURANCE_ANNUAL_PER_1K = INSURANCE_RATE_PER_1K  # noqa: F811


# =============================================================================
# PROPERTY TAX RATES
# =============================================================================
# Property tax rate is imported from config.constants
# See constants.py for documentation
# Alternative: Use actual tax_annual from county assessor when available


# =============================================================================
# UTILITY RATES (Arizona-specific)
# =============================================================================
# Utility rates are imported from config.constants
# See constants.py for documentation

# Maximum monthly utilities cap (very large homes)
# Note: UTILITY_MAXIMUM_MONTHLY already imported from constants above
UTILITY_RATE_PER_SQFT_LOCAL: Final[float] = UTILITY_RATE_PER_SQFT  # Alias for compatibility


# =============================================================================
# WATER COSTS (Arizona-specific)
# =============================================================================
# Water constants defined inline (not in config.constants)

# City water rates (Maricopa County average)
# Base service charge + usage-based
WATER_MONTHLY_BASE: Final[float] = 30.0  # Base service charge
WATER_RATE_PER_KGAL: Final[float] = 5.0  # Per 1,000 gallons
WATER_AVG_USAGE_KGAL: Final[float] = 12.0  # Average AZ household (12k gal/mo)

# WATER_MONTHLY_ESTIMATE already imported from constants above


# =============================================================================
# TRASH COSTS (Arizona-specific)
# =============================================================================
# Trash cost is imported from config.constants
# See constants.py for documentation


# =============================================================================
# POOL COSTS (Arizona-specific)
# =============================================================================
# Pool costs are imported from config.constants
# See constants.py for documentation

# Combined monthly pool cost
POOL_TOTAL_MONTHLY: Final[float] = POOL_SERVICE_MONTHLY + POOL_ENERGY_MONTHLY

# Re-export from constants for backward compatibility
POOL_BASE_MAINTENANCE = POOL_SERVICE_MONTHLY  # noqa: F811


# =============================================================================
# MAINTENANCE RESERVES
# =============================================================================
# Maintenance constants are imported from config.constants
# See constants.py for documentation

# Monthly maintenance reserve rate (derived from annual rate)
MAINTENANCE_RESERVE_RATE: Final[float] = MAINTENANCE_RESERVE_MONTHLY_RATE  # noqa: F811

# Re-import and re-export MAINTENANCE_RESERVE_ANNUAL_RATE for backward compatibility
from ...config.constants import MAINTENANCE_RESERVE_ANNUAL_RATE  # noqa: F401

# =============================================================================
# SOLAR LEASE DEFAULTS
# =============================================================================
# Default solar lease payment is imported from config.constants
# See constants.py for documentation

# Typical solar lease monthly payment range in AZ
SOLAR_LEASE_TYPICAL_MIN: Final[float] = 100.0
SOLAR_LEASE_TYPICAL_MAX: Final[float] = 200.0

# SOLAR_LEASE_DEFAULT already imported from constants above


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

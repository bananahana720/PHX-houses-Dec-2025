"""Cost estimation service for PHX Home Analysis.

This module provides monthly housing cost calculation for Phoenix-area
properties, including mortgage, taxes, insurance, utilities, pool costs,
and maintenance reserves.

Key Features:
- Arizona-specific rate data (2025 market conditions)
- Property tax estimation with county assessor data fallback
- Pool maintenance costs (service + energy)
- Solar lease handling
- Maintenance reserve calculation (1% annually)

Usage:
    from phx_home_analysis.services.cost_estimation import (
        MonthlyCostEstimator,
        MonthlyCosts,
        RateConfig,
    )

    # Basic usage with property object
    estimator = MonthlyCostEstimator(down_payment=50000)
    costs = estimator.estimate(property)
    print(f"Total monthly: ${costs.total:,.2f}")

    # Quick estimate from values
    costs = estimator.estimate_from_values(
        price=450000,
        sqft=2200,
        has_pool=True,
        hoa_fee=0,
    )

    # Max affordable price calculation
    max_price = estimator.calculate_max_affordable_price(
        max_monthly_payment=4000
    )
"""

from .models import MonthlyCosts, CostEstimate
from .rates import (
    # Core rate constants
    MORTGAGE_RATE_30YR,
    MORTGAGE_RATE_15YR,
    LOAN_TERM_30YR_MONTHS,
    DOWN_PAYMENT_DEFAULT,
    # Insurance and tax
    INSURANCE_ANNUAL_PER_1K,
    PROPERTY_TAX_RATE,
    # Utilities (electric/gas only)
    UTILITY_RATE_PER_SQFT,
    UTILITY_MINIMUM_MONTHLY,
    UTILITY_MAXIMUM_MONTHLY,
    # Water
    WATER_MONTHLY_BASE,
    WATER_RATE_PER_KGAL,
    WATER_AVG_USAGE_KGAL,
    WATER_MONTHLY_ESTIMATE,
    # Trash
    TRASH_MONTHLY,
    # Pool costs
    POOL_BASE_MAINTENANCE,
    POOL_ENERGY_MONTHLY,
    POOL_TOTAL_MONTHLY,
    # Maintenance
    MAINTENANCE_RESERVE_RATE,
    MAINTENANCE_RESERVE_ANNUAL_RATE,
    MAINTENANCE_MINIMUM_MONTHLY,
    # Configuration
    RateConfig,
    DEFAULT_RATES,
)
from .estimator import MonthlyCostEstimator, PropertyLike

__all__ = [
    # Main classes
    "MonthlyCostEstimator",
    "MonthlyCosts",
    "CostEstimate",
    "RateConfig",
    "PropertyLike",
    # Rate constants
    "MORTGAGE_RATE_30YR",
    "MORTGAGE_RATE_15YR",
    "LOAN_TERM_30YR_MONTHS",
    "DOWN_PAYMENT_DEFAULT",
    "INSURANCE_ANNUAL_PER_1K",
    "PROPERTY_TAX_RATE",
    "UTILITY_RATE_PER_SQFT",
    "UTILITY_MINIMUM_MONTHLY",
    "UTILITY_MAXIMUM_MONTHLY",
    # Water
    "WATER_MONTHLY_BASE",
    "WATER_RATE_PER_KGAL",
    "WATER_AVG_USAGE_KGAL",
    "WATER_MONTHLY_ESTIMATE",
    # Trash
    "TRASH_MONTHLY",
    # Pool
    "POOL_BASE_MAINTENANCE",
    "POOL_ENERGY_MONTHLY",
    "POOL_TOTAL_MONTHLY",
    "MAINTENANCE_RESERVE_RATE",
    "MAINTENANCE_RESERVE_ANNUAL_RATE",
    "MAINTENANCE_MINIMUM_MONTHLY",
    "DEFAULT_RATES",
]

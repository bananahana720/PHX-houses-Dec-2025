---
name: cost-efficiency
description: Estimate monthly housing costs for AZ properties including mortgage, taxes, insurance, utilities, pool, and maintenance. Use when calculating affordability, comparing properties, or generating cost projections.
allowed-tools: Read, Bash(python:*)
---

# Cost Efficiency Skill

Expert at estimating comprehensive monthly housing costs for Phoenix-area properties using Arizona-specific rate data and the project's cost estimation module.

## Overview

The cost estimation service calculates total monthly housing costs including:

| Component | Description | Source |
|-----------|-------------|--------|
| **Mortgage** | Principal & interest (P&I) | Amortization formula |
| **Property Tax** | Monthly tax portion | County assessor or rate estimate |
| **Insurance** | Homeowner's insurance | AZ average per $1k value |
| **Utilities** | Electric, gas, water | Sqft-based AZ estimate |
| **Pool Maintenance** | Service + energy | AZ pool industry averages |
| **Maintenance Reserve** | 1% annually | Standard homeowner reserve |
| **HOA Fee** | Monthly association dues | Listing data |
| **Solar Lease** | Panel lease payment | Listing data |

**Target Buyer Constraint:** Max $4,000/month total housing cost

## Centralized Constants

**Location:** `src/phx_home_analysis/config/constants.py`

All cost estimation rates and thresholds are centralized:

```python
from src.phx_home_analysis.config.constants import (
    # Mortgage & Financing
    MORTGAGE_RATE_30YR,            # 0.0699 (6.99%)
    MORTGAGE_TERM_MONTHS,          # 360 (30 years)
    DOWN_PAYMENT_DEFAULT,          # 50,000.0
    PMI_THRESHOLD_LTV,             # 0.80

    # Insurance
    INSURANCE_RATE_PER_1K,         # 6.50 (per $1k value)
    INSURANCE_MINIMUM_ANNUAL,      # 800.0

    # Property Tax
    PROPERTY_TAX_RATE,             # 0.0066 (0.66%)

    # Utilities
    UTILITY_RATE_PER_SQFT,         # 0.08 ($/sqft/month)
    UTILITY_MINIMUM_MONTHLY,       # 120.0
    UTILITY_MAXIMUM_MONTHLY,       # 500.0

    # Pool Costs
    POOL_SERVICE_MONTHLY,          # 125.0
    POOL_ENERGY_MONTHLY,           # 75.0
    POOL_TOTAL_MONTHLY,            # 200.0

    # Maintenance Reserve
    MAINTENANCE_RESERVE_ANNUAL_RATE,  # 0.01 (1%)
    MAINTENANCE_MINIMUM_MONTHLY,      # 200.0

    # Solar Leases
    SOLAR_LEASE_TYPICAL_MIN,       # 100.0
    SOLAR_LEASE_TYPICAL_MAX,       # 200.0
    SOLAR_LEASE_DEFAULT,           # 150.0
)
```

**Note:** These constants are the **single source of truth** - both CLI and service layers import from here. Update all rates in `src/phx_home_analysis/config/constants.py` only.

## Using the Cost Estimator

### Basic Usage

```python
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator

# Initialize with default $50k down payment
estimator = MonthlyCostEstimator(down_payment=50000)

# Estimate from property object
costs = estimator.estimate(property)
print(f"Total monthly: ${costs.total:,.2f}")
print(f"PITI: ${costs.piti:,.2f}")
```

### Quick Estimate from Values

```python
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator

estimator = MonthlyCostEstimator(down_payment=50000, rate=0.0699)

# Estimate without property object
costs = estimator.estimate_from_values(
    price=450000,
    sqft=2200,
    has_pool=True,
    hoa_fee=0,
    solar_lease=0,
    tax_annual=None,  # Will estimate at 0.66% rate
)

print(f"Total: ${costs.total:,.2f}")
print(f"Mortgage: ${costs.mortgage:,.2f}")
print(f"Tax: ${costs.property_tax:,.2f}")
print(f"Insurance: ${costs.insurance:,.2f}")
print(f"Utilities: ${costs.utilities:,.2f}")
print(f"Pool: ${costs.pool_maintenance:,.2f}")
print(f"Maintenance: ${costs.maintenance_reserve:,.2f}")
```

### Detailed Estimate with Metadata

```python
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator

estimator = MonthlyCostEstimator(down_payment=50000)
estimate = estimator.estimate_detailed(property)

print(f"Monthly: ${estimate.total_monthly:,.2f}")
print(f"Annual: ${estimate.annual_cost:,.2f}")
print(f"LTV: {estimate.ltv_ratio:.1%}")
print(f"Notes: {estimate.notes}")
```

### Maximum Affordable Price Calculation

```python
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator

estimator = MonthlyCostEstimator(down_payment=50000)

# Find max price for $4k/month budget
max_price = estimator.calculate_max_affordable_price(
    max_monthly_payment=4000,
    sqft_estimate=2000,
    has_pool=True,
    hoa_fee=0,
    solar_lease=0,
)

print(f"Max affordable price: ${max_price:,.0f}")
# Approximately $480-520k depending on rates
```

### Custom Rate Configuration

```python
from src.phx_home_analysis.services.cost_estimation import (
    MonthlyCostEstimator,
    RateConfig,
)

# Customize rates for scenario analysis
config = RateConfig(
    mortgage_rate=0.0650,      # Lower rate scenario
    down_payment=75000,        # Higher down payment
    property_tax_rate=0.0070,  # Slightly higher tax area
    pool_maintenance=150,      # Premium pool service
)

estimator = MonthlyCostEstimator(config=config)
costs = estimator.estimate_from_values(price=500000, sqft=2400, has_pool=True)
```

## MonthlyCosts Model

The `MonthlyCosts` dataclass provides the cost breakdown:

```python
@dataclass(frozen=True)
class MonthlyCosts:
    mortgage: float           # P&I payment
    property_tax: float       # Monthly tax portion
    insurance: float          # Homeowner's insurance
    utilities: float          # Electric/gas/water
    pool_maintenance: float   # Service + energy (0 if no pool)
    maintenance_reserve: float # 1% annual / 12
    hoa_fee: float            # Monthly HOA (0 if none)
    solar_lease: float        # Solar lease (0 if none/owned)

    @property
    def total(self) -> float:
        """Sum of all monthly costs."""

    @property
    def piti(self) -> float:
        """Principal + Interest + Tax + Insurance (lender calculation)."""

    @property
    def fixed_costs(self) -> float:
        """Mortgage + tax + insurance + HOA (stable costs)."""

    @property
    def variable_costs(self) -> float:
        """Utilities + pool + maintenance (fluctuating costs)."""

    def to_dict(self) -> dict[str, float]:
        """Serialize for JSON/reporting."""
```

## CostEstimate Model

Extended estimate with context metadata:

```python
@dataclass(frozen=True)
class CostEstimate:
    monthly_costs: MonthlyCosts
    home_value: float
    loan_amount: float
    down_payment: float
    interest_rate: float
    sqft: int
    has_pool: bool
    has_solar_lease: bool
    notes: tuple[str, ...]    # Estimation warnings/notes

    @property
    def total_monthly(self) -> float

    @property
    def annual_cost(self) -> float

    @property
    def ltv_ratio(self) -> float
```

## Cost Breakdown Example

For a typical property: **$450,000, 2,200 sqft, pool, no HOA**

```
Monthly Cost Breakdown
======================
Mortgage (P&I):       $2,660.85  (6.99% on $400k loan)
Property Tax:           $247.50  (0.66% rate / 12)
Insurance:              $243.75  ($6.50/1k / 12)
Utilities:              $220.00  ($0.10 x 2,200 sqft)
Pool Maintenance:       $200.00  ($125 service + $75 energy)
Maintenance Reserve:    $375.00  (1% of $450k / 12)
HOA Fee:                  $0.00
Solar Lease:              $0.00
-----------------------
TOTAL:                $3,947.10
```

**Key Metrics:**
- PITI: $3,152.10 (lender qualification)
- Fixed Costs: $3,152.10 (stable month-to-month)
- Variable Costs: $795.00 (fluctuates seasonally)

## Integration with Scoring

The cost estimator integrates with the scoring system for affordability evaluation:

### Affordability Check (40 pts in Location Section)

```python
def score_affordability(costs: MonthlyCosts, max_budget: float = 4000) -> int:
    """Score affordability relative to buyer's max budget.

    Returns:
        Score 0-40 based on cost efficiency
    """
    if costs.total <= max_budget * 0.75:
        return 40  # Well under budget (excellent value)
    elif costs.total <= max_budget * 0.85:
        return 30  # Comfortable margin
    elif costs.total <= max_budget * 0.95:
        return 20  # Tight but manageable
    elif costs.total <= max_budget:
        return 10  # At budget limit
    else:
        return 0   # Over budget
```

### Value Ratio Calculation

```python
def value_ratio(score: float, total_monthly: float) -> float:
    """Calculate points per $100 of monthly cost.

    Higher = better value (more score per dollar).
    """
    if total_monthly <= 0:
        return 0.0
    return score / (total_monthly / 100)

# Example: 420 pts / $39.47 (per $100) = 10.64 pts per $100
```

## CLI Usage

```bash
# Estimate costs for all properties
python -c "
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator
estimator = MonthlyCostEstimator(down_payment=50000)
costs = estimator.estimate_from_values(price=450000, sqft=2200, has_pool=True)
print(f'Total: \${costs.total:,.2f}')
"

# Calculate max affordable price
python -c "
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator
estimator = MonthlyCostEstimator(down_payment=50000)
max_price = estimator.calculate_max_affordable_price(4000, has_pool=True)
print(f'Max affordable: \${max_price:,.0f}')
"
```

## Rate Sources

| Rate | Value | Source | Last Updated |
|------|-------|--------|--------------|
| 30-yr Mortgage | 6.99% | Freddie Mac PMMS | Dec 2024 |
| Property Tax | 0.66% | Maricopa County Assessor | 2024 |
| Insurance | $6.50/1k | AZ Dept of Insurance | 2024 |
| Utilities | $0.10/sqft | APS/SRP residential avg | 2024 |
| Pool Service | $125/mo | Phoenix pool industry | 2024 |
| Pool Energy | $75/mo | SRP residential rates | 2024 |

## Estimation Notes

The estimator generates notes for transparency:

| Note | Condition |
|------|-----------|
| "Down payment covers full purchase price" | Down payment >= price |
| "Property tax estimated at 0.66% rate" | No tax_annual data |
| "Pool maintenance costs included ($200/month)" | has_pool = True |
| "Solar lease: $X/month (verify transfer terms)" | solar_lease > 0 |
| "LTV ratio X% may require PMI (not included)" | LTV > 80% |

## Best Practices

1. **Use actual tax data** when available from county assessor
2. **Verify solar status** - owned vs leased has major cost impact
3. **Adjust for orientation** - west-facing adds $50-100/mo in summer
4. **Budget for HVAC** - AZ units last 10-15 years (shorter than national)
5. **Pool costs are conservative** - summer energy can spike 30%
6. **Run scenarios** - test different down payments and rates

## Module Location

```
src/phx_home_analysis/services/cost_estimation/
    __init__.py      # Public API exports
    models.py        # MonthlyCosts, CostEstimate dataclasses
    rates.py         # 2025 AZ rate constants, RateConfig
    estimator.py     # MonthlyCostEstimator service class
```

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `arizona-context` | AZ-specific costs (pool, HVAC, solar) |
| `scoring` | Integrates affordability into 600-pt system |
| `deal-sheets` | Displays cost breakdown in reports |
| `property-data` | Provides input data for estimates |

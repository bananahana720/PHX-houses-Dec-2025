---
name: cost-efficiency
description: Estimate monthly housing costs for AZ properties including mortgage, taxes, insurance, utilities, pool, and maintenance. Target buyer constraint is $4,000/month max. Use when calculating affordability, comparing properties, generating cost projections, or scoring cost efficiency (Section B, 40 pts).
allowed-tools: Read, Bash(python:*)
---

# Cost Efficiency Skill

Estimate comprehensive monthly housing costs for Phoenix-area properties.

## Quick Reference: Cost Components

| Component | Typical Range | Source |
|-----------|--------------|--------|
| Mortgage (P&I) | $2,000-3,500 | 6.99% rate, 30yr |
| Property Tax | $200-400 | 0.66% of value |
| Insurance | $100-200 | $6.50 per $1k value |
| Utilities | $150-300 | $0.08/sqft |
| Pool (if applicable) | $200 | Service + energy |
| Maintenance Reserve | $200-400 | 1% annually |
| HOA | $0 (kill-switch) | Listing data |
| Solar Lease | $100-200 (if leased) | Listing data |
| **Total Target** | **≤$4,000** | Buyer constraint |

## Service Layer

```python
from src.phx_home_analysis.services.cost_estimation import MonthlyCostEstimator

estimator = MonthlyCostEstimator(down_payment=50000)
costs = estimator.estimate(property)
print(f"Total: ${costs.total:,.2f}")

# Or from values
costs = estimator.estimate_from_values(
    price=450000, sqft=2200, has_pool=True,
    hoa_fee=0, solar_lease=0
)
```

## Scoring Formula (Section B: 40 pts)

```python
# Cost Efficiency Score
base_score = max(0, 10 - ((monthly_cost - 3000) / 200))
points = base_score * 4  # Max 40 pts

# Monthly Cost → Points
# $3,000 → 40 pts (optimal)
# $3,500 → 30 pts
# $4,000 → 20 pts (neutral)
# $4,500 → 10 pts
# $5,000 → 0 pts (expensive)
```

## Constants (Single Source of Truth)

```python
from src.phx_home_analysis.config.constants import (
    MORTGAGE_RATE_30YR,            # 0.0699 (6.99%)
    DOWN_PAYMENT_DEFAULT,          # 50,000
    PROPERTY_TAX_RATE,             # 0.0066 (0.66%)
    INSURANCE_RATE_PER_1K,         # 6.50
    UTILITY_RATE_PER_SQFT,         # 0.08
    POOL_TOTAL_MONTHLY,            # 200.0
    MAINTENANCE_RESERVE_ANNUAL_RATE,  # 0.01
)
```

## Max Affordable Price Calculator

```python
max_price = estimator.calculate_max_affordable_price(
    max_monthly_payment=4000,
    sqft_estimate=2000,
    has_pool=True,
    hoa_fee=0,
    solar_lease=0,
)
# Approximately $480-520k at current rates
```

## Quick Estimation Table

| Price | No Pool | With Pool |
|-------|---------|-----------|
| $400k | ~$3,200 | ~$3,400 |
| $450k | ~$3,500 | ~$3,700 |
| $500k | ~$3,800 | ~$4,000 |
| $550k | ~$4,100 | ~$4,300 |

*Assumes $50k down, 6.99% rate, 2200 sqft, no HOA/solar lease*

## Best Practices

1. **Use service layer** - `MonthlyCostEstimator` from cost_estimation
2. **Include all costs** - Pool, solar lease often forgotten
3. **$4k ceiling** - Buyer hard constraint, factor in scoring
4. **Verify taxes** - County assessor more accurate than estimate
5. **Solar leases add $100-200/mo** - Major affordability impact

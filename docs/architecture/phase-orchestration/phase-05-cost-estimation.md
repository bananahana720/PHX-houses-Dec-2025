# Phase 0.5: Cost Estimation

**Purpose:** Calculate monthly ownership costs for CostEfficiencyScorer

**Prerequisites:**
- Phase 0 must be complete (need property data for cost calculation)

**Implementation:** Inline service call (no CLI script required)

```python
from pathlib import Path
from phx_home_analysis.services.cost_estimation import MonthlyCostEstimator
from phx_home_analysis.services.data_cache import PropertyDataCache

# Load property data
cache = PropertyDataCache()
enrichment = cache.get_enrichment_data(Path("data/enrichment_data.json"))
property_data = enrichment.get(address, {})

# Calculate costs
estimator = MonthlyCostEstimator()
estimate = estimator.estimate(
    price=property_data.get("price", 0),
    sqft=property_data.get("sqft", 0),
    hoa_fee=property_data.get("hoa_fee", 0),
    has_pool=property_data.get("has_pool", False),
    solar_status=property_data.get("solar_status", "none")
)

# Update enrichment data
property_data["monthly_cost"] = estimate.total_monthly
property_data["cost_breakdown"] = estimate.to_dict()

# Save updated enrichment
cache.update_enrichment_data(enrichment, Path("data/enrichment_data.json"))
```

**Fields Updated:**
- `monthly_cost`: Total monthly ownership cost
- `cost_breakdown`: Detailed cost components (mortgage, tax, insurance, HOA, utilities, maintenance, pool, solar)

**Post-execution validation:**
```python
if enrichment.get("monthly_cost") is None:
    log_warning("Cost estimation failed - CostEfficiencyScorer will use defaults")
    enrichment["monthly_cost"] = 0  # Will be flagged by scorer
```

**Fatal if Missing:** No - CostEfficiencyScorer uses defaults if cost unavailable

**Checkpoint**: `phase05_cost = "complete"`

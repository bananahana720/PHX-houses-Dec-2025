# 5. Scoring Function Updates

### 5.1 New Scoring Functions Needed

#### 5.1.1 HVAC Condition Scorer

```python
# File: src/phx_home_analysis/services/scoring/strategies/hvac.py

from typing import Final
from src.phx_home_analysis.config.constants import (
    DEFAULT_NEUTRAL_SCORE,
)

# HVAC Age Thresholds (Arizona-specific)
# Research basis: Domain-Alpha Building Systems Report
# Arizona HVAC lifespan: 8-15 years (not 20+ nationally)
HVAC_AGE_NEW_MAX: Final[int] = 5        # 0-5 years = new
HVAC_AGE_GOOD_MAX: Final[int] = 10      # 6-10 years = good
HVAC_AGE_AGING_MAX: Final[int] = 15     # 11-15 years = aging
# > 15 years = replacement likely needed

# Score mappings for HVAC age (10-point scale, then multiplied by 2.5)
SCORE_HVAC_NEW: Final[float] = 10.0       # <= 5 years
SCORE_HVAC_GOOD: Final[float] = 8.0       # <= 10 years
SCORE_HVAC_AGING: Final[float] = 4.8      # <= 15 years
SCORE_HVAC_REPLACEMENT: Final[float] = 2.0  # > 15 years


class HvacConditionScorer:
    """Score HVAC system condition based on age and inspection.

    Research basis: Domain-Alpha Building Systems Report
    - Arizona HVAC lifespan: 8-15 years (vs 15-25 years nationally)
    - Extreme heat (115F+ summers) accelerates compressor wear
    - Efficiency degrades significantly after 10 years
    - Replacement cost: $11,000-$26,000 for full system

    Scoring (25 pts max):
        - 0-5 years: 25 pts (full efficiency, no concerns)
        - 6-10 years: 20 pts (normal wear, 5+ years remaining)
        - 11-15 years: 12 pts (approaching replacement window)
        - 16+ years: 5 pts (replacement likely needed soon)
        - Unknown: 12.5 pts (neutral default)

    Args:
        property_data: Property record from enrichment_data.json

    Returns:
        Score from 0 to 25
    """

    weight: int = 25  # Maximum points

    def score(self, property_data: dict) -> float:
        """Calculate HVAC condition score.

        Priority order for age determination:
        1. hvac_age (if explicitly provided)
        2. hvac_install_year (calculate age from current year)
        3. year_built (assume original HVAC)
        4. Default to neutral score
        """
        hvac_age = self._determine_hvac_age(property_data)

        if hvac_age is None:
            # Unknown - return neutral
            base_score = DEFAULT_NEUTRAL_SCORE
        elif hvac_age <= HVAC_AGE_NEW_MAX:
            base_score = SCORE_HVAC_NEW
        elif hvac_age <= HVAC_AGE_GOOD_MAX:
            base_score = SCORE_HVAC_GOOD
        elif hvac_age <= HVAC_AGE_AGING_MAX:
            base_score = SCORE_HVAC_AGING
        else:
            base_score = SCORE_HVAC_REPLACEMENT

        # Convert 10-point scale to weighted points (max 25)
        return (base_score / 10.0) * self.weight

    def _determine_hvac_age(self, property_data: dict) -> int | None:
        """Determine HVAC age from available data."""
        from datetime import datetime
        current_year = datetime.now().year

        # Priority 1: Explicit hvac_age
        if property_data.get("hvac_age") is not None:
            return property_data["hvac_age"]

        # Priority 2: Calculate from hvac_install_year
        if property_data.get("hvac_install_year") is not None:
            return current_year - property_data["hvac_install_year"]

        # Priority 3: Derive from year_built (assume original)
        if property_data.get("year_built") is not None:
            return current_year - property_data["year_built"]

        # Unknown
        return None
```

#### 5.1.2 Solar Lease Cost Integration

```python
# Update to src/phx_home_analysis/services/cost_estimation/calculator.py

def calculate_monthly_cost(self, property_data: dict) -> float:
    """Calculate total monthly cost including solar lease.

    Research basis: Market-Beta Pool/Solar Economics
    - Solar lease payments typically $100-200/month
    - Must be included in total cost of ownership
    """
    base_cost = (
        self._calculate_mortgage(property_data)
        + self._calculate_property_tax(property_data)
        + self._calculate_insurance(property_data)
        + self._calculate_hoa(property_data)
        + self._calculate_utilities(property_data)
        + self._calculate_pool_costs(property_data)
    )

    # ADD: Solar lease payment
    solar_lease_cost = self._calculate_solar_lease(property_data)

    return base_cost + solar_lease_cost


def _calculate_solar_lease(self, property_data: dict) -> float:
    """Calculate solar lease monthly cost.

    Research basis: Market-Beta Pool/Solar Economics
    - Typical range: $100-200/month
    - Default estimate: $150/month if leased but amount unknown
    """
    solar_status = property_data.get("solar_status", "").lower()

    if solar_status != "leased":
        return 0.0

    # Use actual lease payment if known
    if property_data.get("solar_lease_monthly"):
        return float(property_data["solar_lease_monthly"])

    # Default estimate for leased solar
    from src.phx_home_analysis.config.constants import SOLAR_LEASE_DEFAULT
    return SOLAR_LEASE_DEFAULT  # $150/month
```

### 5.2 Modified Scoring Functions

#### 5.2.1 Roof Condition Scorer Updates

```python
# CHANGE: Update roof age thresholds for Arizona reality
# RATIONALE: Domain-Alpha research shows:
#   - Arizona tile roof underlayment: 12-20 years (tiles last 50+ years)
#   - Arizona shingle roof: 12-25 years (vs 20-30 nationally)
#   - Extreme UV and heat degrade materials faster

# BEFORE (in constants.py):
ROOF_AGE_NEW_MAX: Final[int] = 5        # 0-5 years = new/replaced = 10 pts
ROOF_AGE_GOOD_MAX: Final[int] = 10      # 6-10 years = good = 7 pts
ROOF_AGE_FAIR_MAX: Final[int] = 15      # 11-15 years = fair = 5 pts
ROOF_AGE_AGING_MAX: Final[int] = 20     # 16-20 years = aging = 3 pts
# > 20 years = replacement needed = 1 pt

# AFTER (adjusted for Arizona):
ROOF_AGE_NEW_MAX: Final[int] = 5        # 0-5 years = new/replaced = 10 pts (unchanged)
ROOF_AGE_GOOD_MAX: Final[int] = 8       # 6-8 years = good = 7 pts (reduced from 10)
ROOF_AGE_FAIR_MAX: Final[int] = 12      # 9-12 years = fair = 5 pts (reduced from 15)
ROOF_AGE_AGING_MAX: Final[int] = 18     # 13-18 years = aging = 3 pts (reduced from 20)
# > 18 years = replacement needed = 1 pt

# RATIONALE TABLE:
# | Roof Type | National Lifespan | Arizona Lifespan | Reduction |
# |-----------|-------------------|------------------|-----------|
# | Tile (underlayment) | 20-30 years | 12-20 years | 33-40% |
# | Shingle | 20-30 years | 12-25 years | 17-40% |
# | Foam | 20-30 years | 15-25 years | 17-25% |
```

#### 5.2.2 Pool Equipment Age Thresholds

```python
# CHANGE: Update pool equipment age thresholds
# RATIONALE: Market-Beta and Domain-Alpha research shows:
#   - Pool pump lifespan: 8-12 years (AZ heat accelerates wear)
#   - Pool heater lifespan: 11-15 years
#   - Equipment operates more hours in AZ (year-round use)

# BEFORE (in constants.py):
POOL_EQUIP_NEW_MAX: Final[int] = 3    # 0-3 years = new equipment = 10 pts
POOL_EQUIP_GOOD_MAX: Final[int] = 6   # 4-6 years = good condition = 7 pts
POOL_EQUIP_FAIR_MAX: Final[int] = 10  # 7-10 years = fair condition = 5 pts
# > 10 years = needs replacement = 3 pts

# AFTER (adjusted for Arizona pool economics):
POOL_EQUIP_NEW_MAX: Final[int] = 3    # 0-3 years = new equipment = 10 pts (unchanged)
POOL_EQUIP_GOOD_MAX: Final[int] = 5   # 4-5 years = good condition = 7 pts (reduced from 6)
POOL_EQUIP_FAIR_MAX: Final[int] = 8   # 6-8 years = fair condition = 5 pts (reduced from 10)
# > 8 years = needs replacement = 3 pts (was > 10 years)
```

---

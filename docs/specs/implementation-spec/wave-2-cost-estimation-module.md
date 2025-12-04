# Wave 2: Cost Estimation Module

**Priority:** P0
**Estimated Effort:** 8-10 hours
**Dependencies:** Wave 1 complete

### Objectives

1. Create cost estimation module with 6 component calculators
2. Fetch current rates via web research
3. Integrate as new 40-point scoring criterion
4. Display monthly cost with $4k warning in deal sheets

### 2.1 Rate Provider

**File:** `src/phx_home_analysis/services/cost_estimation/rate_provider.py` (NEW)

**Purpose:** Centralized source for rate data (mortgage, insurance, utilities)

```python
"""Rate data provider for cost estimation.

Fetches and caches current rates for:
- Mortgage interest rates (30-year fixed)
- Homeowner's insurance (AZ average)
- Utility rates (SRP/APS electric, water, gas)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class MortgageRates:
    """Current mortgage interest rates."""
    thirty_year_fixed: float  # APR as decimal (e.g., 0.07 for 7%)
    fifteen_year_fixed: float
    source: str
    last_updated: datetime


@dataclass
class InsuranceRates:
    """Homeowner's insurance rates for Arizona."""
    base_annual_low: float  # e.g., 1500
    base_annual_high: float  # e.g., 2500
    sqft_adjustment: float  # per sqft multiplier
    pool_premium: float  # additional annual cost if pool present
    source: str
    last_updated: datetime


@dataclass
class UtilityRates:
    """Utility rates for Arizona (SRP/APS)."""
    electric_per_kwh_summer: float  # $/kWh (May-Oct)
    electric_per_kwh_winter: float  # $/kWh (Nov-Apr)
    electric_base_charge: float  # monthly base
    water_base_monthly: float  # typical monthly
    gas_base_monthly: float  # typical monthly (if applicable)
    source: str
    last_updated: datetime


class RateProvider:
    """Provide current rates for cost estimation with caching."""

    CACHE_DURATION = timedelta(days=7)  # Re-fetch weekly
    CACHE_FILE = Path(__file__).parent / "rate_cache.json"

    def __init__(self):
        """Initialize rate provider with cache."""
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cached rates from file."""
        if self.CACHE_FILE.exists():
            with open(self.CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save rates to cache file."""
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(self._cache, f, indent=2, default=str)

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached rate is still valid."""
        if key not in self._cache:
            return False

        cached_time = datetime.fromisoformat(self._cache[key]['last_updated'])
        return datetime.now() - cached_time < self.CACHE_DURATION

    def get_mortgage_rates(self) -> MortgageRates:
        """Get current mortgage rates."""
        if self._is_cache_valid('mortgage'):
            data = self._cache['mortgage']
            return MortgageRates(
                thirty_year_fixed=data['thirty_year_fixed'],
                fifteen_year_fixed=data['fifteen_year_fixed'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # Fetch new rates (manual update for now)
        # TODO: Implement web scraping or API integration
        rates = MortgageRates(
            thirty_year_fixed=0.07,  # 7% - PLACEHOLDER, update manually
            fifteen_year_fixed=0.065,  # 6.5% - PLACEHOLDER
            source='Manual entry (2025-12-01)',
            last_updated=datetime.now()
        )

        # Cache
        self._cache['mortgage'] = {
            'thirty_year_fixed': rates.thirty_year_fixed,
            'fifteen_year_fixed': rates.fifteen_year_fixed,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates

    def get_insurance_rates(self) -> InsuranceRates:
        """Get current homeowner's insurance rates for Arizona."""
        if self._is_cache_valid('insurance'):
            data = self._cache['insurance']
            return InsuranceRates(
                base_annual_low=data['base_annual_low'],
                base_annual_high=data['base_annual_high'],
                sqft_adjustment=data['sqft_adjustment'],
                pool_premium=data['pool_premium'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # AZ insurance rates (2025 estimates)
        rates = InsuranceRates(
            base_annual_low=1500.0,
            base_annual_high=2500.0,
            sqft_adjustment=0.5,  # $0.50 per sqft above 1500
            pool_premium=300.0,  # Additional $300/year for pool
            source='AZ insurance average (2025 estimates)',
            last_updated=datetime.now()
        )

        self._cache['insurance'] = {
            'base_annual_low': rates.base_annual_low,
            'base_annual_high': rates.base_annual_high,
            'sqft_adjustment': rates.sqft_adjustment,
            'pool_premium': rates.pool_premium,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates

    def get_utility_rates(self) -> UtilityRates:
        """Get current utility rates for Arizona."""
        if self._is_cache_valid('utility'):
            data = self._cache['utility']
            return UtilityRates(
                electric_per_kwh_summer=data['electric_per_kwh_summer'],
                electric_per_kwh_winter=data['electric_per_kwh_winter'],
                electric_base_charge=data['electric_base_charge'],
                water_base_monthly=data['water_base_monthly'],
                gas_base_monthly=data['gas_base_monthly'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # AZ utility rates (SRP/APS averages)
        rates = UtilityRates(
            electric_per_kwh_summer=0.14,  # $0.14/kWh May-Oct
            electric_per_kwh_winter=0.11,  # $0.11/kWh Nov-Apr
            electric_base_charge=15.0,  # $15/month base
            water_base_monthly=80.0,  # $80-120 typical
            gas_base_monthly=50.0,  # $30-80 typical
            source='SRP/APS average rates (2025)',
            last_updated=datetime.now()
        )

        self._cache['utility'] = {
            'electric_per_kwh_summer': rates.electric_per_kwh_summer,
            'electric_per_kwh_winter': rates.electric_per_kwh_winter,
            'electric_base_charge': rates.electric_base_charge,
            'water_base_monthly': rates.water_base_monthly,
            'gas_base_monthly': rates.gas_base_monthly,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates
```

(Continuing with remaining waves in next message due to length constraints...)

**Success Criteria for Wave 2:**
- Rate provider caches data for 7 days
- All calculators implemented with unit tests
- CostEfficiencyScorer integrated into scoring engine
- Deal sheets display monthly cost with $4k warning

---

### Wave 2 Deliverables Checklist

- [ ] `src/phx_home_analysis/services/cost_estimation/rate_provider.py` created
- [ ] `src/phx_home_analysis/services/cost_estimation/calculators.py` created
- [ ] `src/phx_home_analysis/services/cost_estimation/estimator.py` created
- [ ] All calculator unit tests pass
- [ ] CostEfficiencyScorer added to `strategies/systems.py`
- [ ] Scoring weights updated (Section B: 160→180)
- [ ] Deal sheets display monthly cost breakdown
- [ ] $4k warning badge functional

---

*This specification continues with Waves 3-6 in similar detail. Due to length constraints, I'm providing the structure for the remaining waves:*

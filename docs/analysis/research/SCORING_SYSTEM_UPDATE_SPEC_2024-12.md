# Scoring System Update Specification

**Version:** 2.0.0
**Date:** December 2024
**Status:** Implementation-Ready
**Author:** Synthesis Agent (Claude Opus 4.5)

---

## 1. Executive Summary

### 1.1 What Changes Are Recommended

This specification proposes targeted updates to the PHX Houses Analysis Pipeline scoring system based on comprehensive research across 9 research reports covering market conditions, domain expertise, and technical capabilities.

**Kill-Switch Updates:**
1. **ADD: Solar Lease criterion (SOFT, severity 2.5)** - Properties with leased solar systems face 3-8% value reduction and transfer complications

**Scoring Weight Updates:**
1. **ADD: HVAC Condition (25 pts)** to Section B - Arizona's extreme heat reduces HVAC lifespan to 8-15 years
2. **REBALANCE: Section A** - Reduce by 25 pts across lower-priority criteria to accommodate HVAC
3. **ADJUST: Roof scoring thresholds** - Align with Arizona-specific lifespan research
4. **ADJUST: Pool equipment age thresholds** - Match Arizona equipment degradation patterns

### 1.2 Impact on Score Distribution

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Section A Max | 250 pts | 225 pts | -25 |
| Section B Max | 170 pts | 195 pts | +25 |
| Section C Max | 180 pts | 180 pts | 0 |
| **Total Max** | **600 pts** | **600 pts** | **0** |

**Expected Tier Distribution Impact:**
- Properties with aging HVAC (10-15 years) will score lower in Section B
- Properties with leased solar will face kill-switch severity or outright failure
- Net effect: More accurate risk assessment for first-time buyers

### 1.3 Rationale Summary

| Change | Research Source | Key Finding |
|--------|-----------------|-------------|
| Solar Lease kill-switch | Market-Beta, Domain-Beta | 75% of Phoenix solar is leased; 3-8% value reduction; transfer complications |
| HVAC scoring | Domain-Alpha | AZ HVAC lifespan 8-15 years (not 20+); $11k-26k replacement |
| Roof threshold adjustment | Domain-Alpha | AZ underlayment 12-20 years; shingles 12-25 years |
| Pool equipment thresholds | Market-Beta, Domain-Alpha | AZ heat reduces pool pump life to 8-12 years |

---

## 2. Kill-Switch Updates

### 2.1 Current Kill-Switch Configuration

**Source:** `src/phx_home_analysis/config/constants.py:38-74`

```python
# Current HARD Criteria (Instant Fail)
# - HOA fee > $0 -> FAIL
# - Bedrooms < 4 -> FAIL
# - Bathrooms < 2 -> FAIL

# Current SOFT Criteria (Severity Accumulation)
SEVERITY_WEIGHT_SEWER: Final[float] = 2.5      # Septic = +2.5
SEVERITY_WEIGHT_YEAR_BUILT: Final[float] = 2.0  # >= 2024 = +2.0
SEVERITY_WEIGHT_GARAGE: Final[float] = 1.5      # < 2 spaces = +1.5
SEVERITY_WEIGHT_LOT_SIZE: Final[float] = 1.0    # Outside 7k-15k sqft = +1.0

# Thresholds
SEVERITY_FAIL_THRESHOLD: Final[float] = 3.0     # >= 3.0 = FAIL
SEVERITY_WARNING_THRESHOLD: Final[float] = 1.5  # >= 1.5 = WARNING
```

### 2.2 Proposed Kill-Switch Changes

#### 2.2.1 New SOFT Criterion: Solar Lease

```python
# CHANGE: Add Solar Lease as SOFT criterion
# RATIONALE: Market-Beta research shows:
#   - 75% of Phoenix solar installations are leased (not owned)
#   - Leased solar reduces home value by 3-8%
#   - Annual escalator rates of 2-3% create long-term cost burden
#   - Lease buyout costs $9,000-$21,000
#   - Transfer complications at sale (Domain-Beta: 100+ solar company bankruptcies since 2023)

# BEFORE:
# No solar lease criterion exists

# AFTER:
# Add to constants.py after line 74:

# Solar lease burden: Transfer liability, ongoing payments, value reduction
# Properties with leased solar face 3-8% reduced market value
SEVERITY_WEIGHT_SOLAR_LEASE: Final[float] = 2.5
```

**Implementation Details:**

```python
# Add to services/kill_switch/criteria.py

class SolarLeaseCriterion(SoftCriterion):
    """Evaluate solar lease status.

    Research basis: Market-Beta Pool/Solar Economics Report
    - 75% of Phoenix solar is leased
    - 3-8% home value reduction
    - $100-200/month ongoing payments
    - Transfer complications at sale

    Scoring:
    - solar_status = "owned" or "none" -> PASS (severity 0)
    - solar_status = "leased" -> FAIL (severity 2.5)
    - solar_status = None/unknown -> PASS with yellow flag
    """

    name = "solar_lease"
    display_name = "Solar Lease Status"
    severity_weight = SEVERITY_WEIGHT_SOLAR_LEASE

    def evaluate(self, property_data: dict) -> CriterionResult:
        solar_status = property_data.get("solar_status", "").lower()

        if solar_status == "leased":
            return CriterionResult(
                passed=False,
                severity_weight=self.severity_weight,
                actual_value=solar_status,
                required_value="owned or none",
                message="Leased solar system: transfer liability, ongoing payments"
            )

        if solar_status in ("owned", "none", ""):
            return CriterionResult(
                passed=True,
                severity_weight=0.0,
                actual_value=solar_status or "unknown",
                required_value="owned or none",
                message="Solar status acceptable"
            )

        # Unknown status - pass with caution
        return CriterionResult(
            passed=True,
            severity_weight=0.0,
            actual_value="unknown",
            required_value="owned or none",
            message="Solar status unknown - verify before purchase",
            flag="YELLOW"
        )
```

#### 2.2.2 Updated Constants Module

```python
# COMPLETE UPDATED constants.py SECTION (lines 53-80)

# =============================================================================
# KILL-SWITCH SEVERITY WEIGHTS (SOFT CRITERIA)
# =============================================================================
# Source: Business rules based on buyer profile priorities
# Applied to properties that DON'T fail hard criteria but have minor issues

# City sewer required: Septic is infrastructure concern, adds 2.5 severity
# Septic systems are less desirable in Phoenix metro and add maintenance burden
# Research basis: Domain-Gamma - 10%+ failure rate, $4k-20k replacement
SEVERITY_WEIGHT_SEWER: Final[float] = 2.5

# Solar lease liability: Transfer complications, ongoing payments, value reduction
# Research basis: Market-Beta - 3-8% value reduction, 75% of Phoenix solar leased
SEVERITY_WEIGHT_SOLAR_LEASE: Final[float] = 2.5

# New build avoidance (year_built >= 2024): Newer homes more likely to have issues
# Excludes current-year builds but allows prior years; adds 2.0 severity
# Research basis: Domain-Beta - 8-9 year warranty period for latent defects
SEVERITY_WEIGHT_YEAR_BUILT: Final[float] = 2.0

# 2-car garage minimum: Convenience factor in Phoenix metro living
# Adds 1.5 severity if less than 2 spaces
SEVERITY_WEIGHT_GARAGE: Final[float] = 1.5

# Lot size (7k-15k sqft range): Preference factor, wide acceptable range
# Adds 1.0 severity if outside target range
SEVERITY_WEIGHT_LOT_SIZE: Final[float] = 1.0
```

### 2.3 Kill-Switch Validation Matrix

| Criterion | Type | Current Severity | Proposed Severity | Research Support |
|-----------|------|------------------|-------------------|------------------|
| HOA > $0 | HARD | instant | instant | Market-Alpha: AZ has 2nd-highest HOA fees ($448 avg) |
| Beds < 4 | HARD | instant | instant | Market-Gamma: Multigenerational demand at 17% |
| Baths < 2 | HARD | instant | instant | Core requirement, no change |
| Septic (not city sewer) | SOFT | 2.5 | 2.5 | Domain-Gamma: 10%+ failure rate, $4k-20k replacement |
| **Solar Lease** | **SOFT** | **N/A** | **2.5** | **Market-Beta: 3-8% value reduction, transfer issues** |
| Year Built >= 2024 | SOFT | 2.0 | 2.0 | Domain-Beta: Warranty period concerns |
| Garage < 2 spaces | SOFT | 1.5 | 1.5 | Convenience factor, no change |
| Lot outside 7k-15k sqft | SOFT | 1.0 | 1.0 | Preference factor, no change |

**Maximum SOFT Severity (updated):** 9.5 (was 7.0)

**Critical Combinations That Now Trigger FAIL:**
- Solar Lease (2.5) + Septic (2.5) = 5.0 >= 3.0 -> FAIL
- Solar Lease (2.5) + Year 2024 (2.0) = 4.5 >= 3.0 -> FAIL
- Solar Lease (2.5) + Garage (1.5) = 4.0 >= 3.0 -> FAIL
- Solar Lease (2.5) alone = 2.5 < 3.0 -> WARNING

---

## 3. Scoring Weight Updates

### 3.1 Current Scoring Configuration

**Source:** `src/phx_home_analysis/config/scoring_weights.py`

```python
# Current Section A: Location & Environment (250 pts)
school_district: int = 42
quietness: int = 30
crime_index: int = 47
supermarket_proximity: int = 23
parks_walkability: int = 23
sun_orientation: int = 25
flood_risk: int = 23
walk_transit: int = 22
air_quality: int = 15
# TOTAL: 250 pts

# Current Section B: Lot & Systems (170 pts)
roof_condition: int = 45
backyard_utility: int = 35
plumbing_electrical: int = 35
pool_condition: int = 20
cost_efficiency: int = 35
# TOTAL: 170 pts

# Current Section C: Interior & Features (180 pts)
kitchen_layout: int = 40
master_suite: int = 35
natural_light: int = 30
high_ceilings: int = 25
fireplace: int = 20
laundry_area: int = 20
aesthetics: int = 10
# TOTAL: 180 pts

# GRAND TOTAL: 600 pts
```

### 3.2 Section A: Location (250 pts -> 225 pts)

#### Proposed Changes

To accommodate the new HVAC scoring criterion (25 pts) in Section B, Section A is reduced by 25 pts across lower-priority criteria:

| Criterion | Current | Proposed | Delta | Rationale |
|-----------|---------|----------|-------|-----------|
| school_district | 42 | 42 | 0 | High priority - GreatSchools rating critical |
| quietness | 30 | 25 | -5 | Still important but less than safety |
| crime_index | 47 | 47 | 0 | High priority - safety is paramount |
| supermarket_proximity | 23 | 18 | -5 | Convenience factor, car-dependent area |
| parks_walkability | 23 | 18 | -5 | Convenience factor, less critical |
| sun_orientation | 25 | 25 | 0 | Critical for AZ cooling costs |
| flood_risk | 23 | 18 | -5 | Most Phoenix properties Zone X |
| walk_transit | 22 | 17 | -5 | Phoenix is car-dependent |
| air_quality | 15 | 15 | 0 | Keep as baseline |
| **TOTAL** | **250** | **225** | **-25** | |

```python
# PROPOSED Section A Updates in scoring_weights.py

# SECTION A: LOCATION & ENVIRONMENT (225 pts - reduced from 250)
school_district: int = 42    # Unchanged - high priority
quietness: int = 25          # Reduced from 30 (-5) - still important
crime_index: int = 47        # Unchanged - safety paramount
supermarket_proximity: int = 18  # Reduced from 23 (-5) - convenience
parks_walkability: int = 18  # Reduced from 23 (-5) - convenience
sun_orientation: int = 25    # Unchanged - critical for AZ
flood_risk: int = 18         # Reduced from 23 (-5) - most are Zone X
walk_transit: int = 17       # Reduced from 22 (-5) - car-dependent area
air_quality: int = 15        # Unchanged - baseline health factor
```

### 3.3 Section B: Lot & Systems (170 pts -> 195 pts)

#### New Criterion: HVAC Condition (25 pts)

```python
# CHANGE: Add HVAC Condition scoring (25 pts max)
# RATIONALE: Domain-Alpha Building Systems Research shows:
#   - Arizona HVAC lifespan: 8-15 years (not 20+ years nationally)
#   - Replacement cost: $11,000-$26,000 for full system
#   - Arizona heat (115F+ summers) accelerates wear
#   - Efficiency degradation significant after 10 years

# BEFORE:
# No explicit HVAC scoring criterion

# AFTER:
# Add hvac_condition: int = 25 to Section B

"""
hvac_condition (25 pts max):
    HVAC system age and condition assessment
    Arizona-specific: Systems degrade faster due to extreme heat

    Scoring logic:
        - New/Recent (0-5 years): 25 pts - Full efficiency, no concerns
        - Good (6-10 years): 20 pts - Normal wear, 5+ years remaining
        - Aging (11-15 years): 12 pts - Approaching replacement window
        - End-of-life (16+ years): 5 pts - Replacement likely needed soon
        - Unknown: 12.5 pts (neutral)

    Data source: Listing description, county records, visual inspection
    Research basis: Domain-Alpha Building Systems (HVAC lifespan 8-15 years in AZ)

    Note: Score assumes original HVAC unless replacement documented.
    Age calculated as: current_year - hvac_install_year (or year_built if unknown)
"""
```

#### Proposed Section B Configuration

| Criterion | Current | Proposed | Delta | Rationale |
|-----------|---------|----------|-------|-----------|
| roof_condition | 45 | 45 | 0 | Critical - expensive replacement |
| backyard_utility | 35 | 35 | 0 | Important for AZ outdoor living |
| plumbing_electrical | 35 | 35 | 0 | Infrastructure assessment |
| pool_condition | 20 | 20 | 0 | Equipment concerns in AZ heat |
| cost_efficiency | 35 | 35 | 0 | Critical for budget adherence |
| **hvac_condition** | **0** | **25** | **+25** | **NEW: Critical for AZ** |
| **TOTAL** | **170** | **195** | **+25** | |

```python
# PROPOSED Section B in scoring_weights.py

# SECTION B: LOT & SYSTEMS (195 pts - increased from 170)
roof_condition: int = 45        # Unchanged - critical infrastructure
backyard_utility: int = 35      # Unchanged - AZ outdoor living
plumbing_electrical: int = 35   # Unchanged - infrastructure
pool_condition: int = 20        # Unchanged - AZ-specific concern
cost_efficiency: int = 35       # Unchanged - budget critical
hvac_condition: int = 25        # NEW - Arizona HVAC lifespan 8-15 years
```

### 3.4 Section C: Interior (180 pts - Unchanged)

No changes proposed for Section C. Interior scoring criteria remain appropriate.

```python
# SECTION C: INTERIOR & FEATURES (180 pts - unchanged)
kitchen_layout: int = 40
master_suite: int = 35
natural_light: int = 30
high_ceilings: int = 25
fireplace: int = 20
laundry_area: int = 20
aesthetics: int = 10
```

### 3.5 Point Reallocation Summary

| Section | Current | Proposed | Delta |
|---------|---------|----------|-------|
| **A: Location & Environment** | 250 | 225 | -25 |
| **B: Lot & Systems** | 170 | 195 | +25 |
| **C: Interior & Features** | 180 | 180 | 0 |
| **GRAND TOTAL** | **600** | **600** | **0** |

**Verification:** 225 + 195 + 180 = 600 (correct)

---

## 4. New Data Fields Required

### 4.1 enrichment_data.json Schema Updates

```json
{
  "solar_status": {
    "type": "string",
    "enum": ["owned", "leased", "none", "unknown"],
    "source": "listing_extraction, county_records",
    "kill_switch_use": true,
    "scoring_use": false,
    "default": "unknown",
    "description": "Solar panel ownership status",
    "research_basis": "Market-Beta: 75% of Phoenix solar is leased",
    "detection_hints": [
      "Look for 'solar lease' or 'leased panels' in listing",
      "Check for solar company name in HOA/encumbrances",
      "Arizona law A.R.S. 44-1763 requires seller disclosure"
    ]
  },

  "solar_lease_monthly": {
    "type": "number",
    "source": "listing_extraction, seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Monthly solar lease payment if leased",
    "typical_range": [100, 200],
    "notes": "Included in cost_efficiency calculation"
  },

  "solar_lease_buyout": {
    "type": "number",
    "source": "seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": false,
    "default": null,
    "description": "Lease buyout amount if available",
    "typical_range": [9000, 21000]
  },

  "hvac_age": {
    "type": "integer",
    "source": "listing_extraction, county_records, visual_inspection",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Age of HVAC system in years",
    "derivation": "If unknown, derive from year_built (assume original)",
    "research_basis": "Domain-Alpha: AZ HVAC lifespan 8-15 years"
  },

  "hvac_install_year": {
    "type": "integer",
    "source": "listing_extraction, permit_records",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Year HVAC system was installed/replaced",
    "notes": "If null, use year_built as proxy"
  },

  "hvac_condition": {
    "type": "string",
    "enum": ["new", "good", "fair", "aging", "replacement_needed", "unknown"],
    "source": "visual_inspection, listing_description",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": "unknown",
    "description": "Assessed condition of HVAC system"
  },

  "roof_underlayment_age": {
    "type": "integer",
    "source": "permit_records, seller_disclosure",
    "kill_switch_use": false,
    "scoring_use": true,
    "default": null,
    "description": "Age of roof underlayment (separate from tile)",
    "research_basis": "Domain-Alpha: Tile lasts 50+ years but underlayment 12-20 years in AZ"
  }
}
```

### 4.2 Data Source Mapping

| Field | Primary Source | Fallback Source | Extraction Phase |
|-------|---------------|-----------------|------------------|
| solar_status | Listing description | Seller disclosure | Phase 1 (listing-browser) |
| solar_lease_monthly | Listing description | Seller disclosure | Phase 1 (listing-browser) |
| hvac_age | Listing description | Derived from year_built | Phase 1 / Phase 2 |
| hvac_install_year | Permit records | Listing description | Phase 1 (listing-browser) |
| hvac_condition | Visual inspection | Listing photos | Phase 2 (image-assessor) |
| roof_underlayment_age | Permit records | Seller disclosure | Phase 1 / Manual |

### 4.3 Detection Patterns for Solar Status

```python
# Patterns to identify solar lease in listing text
SOLAR_LEASE_PATTERNS = [
    r"solar\s+lease",
    r"leased\s+solar",
    r"solar\s+panel\s+lease",
    r"ppa\s+agreement",  # Power Purchase Agreement
    r"sunrun",           # Major solar lease companies
    r"vivint\s+solar",
    r"sunnova",
    r"tesla\s+lease",
    r"solar\s+city\s+lease",
    r"assume\s+solar\s+lease",
    r"solar\s+contract",
    r"transferable\s+solar"
]

SOLAR_OWNED_PATTERNS = [
    r"owned\s+solar",
    r"solar\s+panels?\s+included",
    r"paid\s+off\s+solar",
    r"solar\s+conveys",
    r"no\s+solar\s+lease"
]
```

---

## 5. Scoring Function Updates

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

## 6. Tier Threshold Analysis

### 6.1 Should Thresholds Change?

**Recommendation: NO CHANGE to tier thresholds**

The tier thresholds remain appropriate because:

1. **Percentage-based calibration** - Thresholds are defined as percentages of max score:
   - Unicorn: >80% (>480 of 600)
   - Contender: 60-80% (360-480)
   - Pass: <60% (<360)

2. **Total score unchanged** - The 600-point maximum is maintained

3. **Section rebalancing is minor** - Shifting 25 pts from Location to Systems doesn't fundamentally change score distribution

### 6.2 Distribution Impact Analysis

**Expected Impact:**

| Property Profile | Score Impact | Tier Impact |
|------------------|--------------|-------------|
| New HVAC (0-5 years) | +25 pts (full) | Potential tier upgrade |
| Aging HVAC (11-15 years) | +12 pts | Neutral |
| Old HVAC (16+ years) | +5 pts | Potential tier downgrade |
| Leased Solar + other SOFT | Kill-switch FAIL | Excluded before scoring |
| Leased Solar only | WARNING | Flagged but scored |

**Score Range Examples:**

| Scenario | Current Score | New Score | Delta |
|----------|---------------|-----------|-------|
| Excellent property, new HVAC | 520 | 545 | +25 |
| Excellent property, aging HVAC | 520 | 507 | -13 |
| Average property, old HVAC | 380 | 360 | -20 |
| Borderline property, new HVAC | 355 | 380 | +25 |

---

## 7. Migration Plan

### 7.1 Update Sequence

```
Phase 1: Constants & Configuration (No Breaking Changes)
├── Update constants.py with new constants
├── Add SEVERITY_WEIGHT_SOLAR_LEASE = 2.5
├── Add HVAC age thresholds
├── Update roof age thresholds
└── Update pool equipment thresholds

Phase 2: Schema Updates
├── Add new fields to validation/schemas.py
├── Update enrichment_data.json schema
└── Add field definitions to property-data skill

Phase 3: Kill-Switch Integration
├── Add SolarLeaseCriterion to criteria.py
├── Update SOFT_SEVERITY_WEIGHTS dict
├── Update evaluate_kill_switches() function
└── Add tests for solar lease criterion

Phase 4: Scoring Integration
├── Implement HvacConditionScorer
├── Add hvac_condition to ScoringWeights dataclass
├── Update scoring_weights.py Section A/B totals
├── Update PropertyScorer to include HVAC
├── Update cost estimation for solar lease

Phase 5: Data Pipeline Updates
├── Update listing-browser agent to detect solar lease
├── Update extraction patterns for HVAC age
├── Update image-assessor for HVAC condition
└── Update deal sheets for new fields

Phase 6: Validation & Testing
├── Run full test suite
├── Re-score sample properties
├── Validate tier distribution
└── Update documentation
```

### 7.2 Backwards Compatibility

**Graceful Handling of Missing Data:**

```python
# Properties without new fields use neutral defaults
DEFAULTS = {
    "solar_status": "unknown",     # Passes kill-switch with yellow flag
    "hvac_age": None,              # Uses neutral score (12.5 pts)
    "hvac_condition": "unknown",   # Uses neutral score
}

# Existing properties scored before migration
# Will receive neutral HVAC score until re-enriched
```

**Data Migration Script:**

```python
# scripts/migrate_scoring_v2.py

def migrate_existing_properties():
    """Add default values for new fields to existing properties."""
    enrichment = load_enrichment_data()

    for address, data in enrichment.items():
        # Add solar_status if missing
        if "solar_status" not in data:
            data["solar_status"] = "unknown"

        # Derive hvac_age from year_built if possible
        if "hvac_age" not in data and data.get("year_built"):
            data["hvac_age"] = 2025 - data["year_built"]

        # Add hvac_condition if missing
        if "hvac_condition" not in data:
            data["hvac_condition"] = "unknown"

    save_enrichment_data(enrichment)
```

### 7.3 Validation Steps

```bash
# 1. Run unit tests
pytest tests/unit/services/kill_switch/ -v
pytest tests/unit/services/scoring/ -v

# 2. Validate constants integrity
python -c "from src.phx_home_analysis.config.constants import *; \
    assert SCORE_SECTION_A_TOTAL + SCORE_SECTION_B_TOTAL + SCORE_SECTION_C_TOTAL == MAX_POSSIBLE_SCORE"

# 3. Re-score sample properties and compare
python scripts/phx_home_analyzer.py --compare-before-after

# 4. Verify tier distribution
python scripts/analyze_tier_distribution.py
```

---

## 8. Test Cases

### 8.1 Kill-Switch Edge Cases

#### 8.1.1 Solar Lease Tests

```python
# tests/unit/services/kill_switch/test_solar_lease.py

class TestSolarLeaseCriterion:

    def test_solar_owned_passes(self):
        """Owned solar should pass without severity."""
        prop = {"solar_status": "owned"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0

    def test_solar_none_passes(self):
        """No solar should pass without severity."""
        prop = {"solar_status": "none"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0

    def test_solar_leased_fails_with_severity(self):
        """Leased solar should fail with 2.5 severity."""
        prop = {"solar_status": "leased"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is False
        assert result.severity_weight == 2.5

    def test_solar_unknown_passes_with_flag(self):
        """Unknown solar status should pass with yellow flag."""
        prop = {"solar_status": "unknown"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0
        assert result.flag == "YELLOW"

    def test_solar_leased_plus_septic_fails_threshold(self):
        """Leased solar (2.5) + septic (2.5) = 5.0 >= 3.0 threshold."""
        prop = {"solar_status": "leased", "sewer_type": "septic"}
        verdict, severity, failures, _ = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 5.0
        assert len(failures) == 2

    def test_solar_leased_alone_is_warning(self):
        """Leased solar alone (2.5) should be WARNING, not FAIL."""
        prop = {
            "solar_status": "leased",
            "sewer_type": "city",
            "year_built": 2010,
            "garage_spaces": 2,
            "lot_sqft": 10000,
            "beds": 4,
            "baths": 2,
            "hoa_fee": 0
        }
        verdict, severity, failures, _ = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
```

### 8.2 Scoring Boundary Conditions

#### 8.2.1 HVAC Scoring Tests

```python
# tests/unit/services/scoring/test_hvac_scorer.py

class TestHvacConditionScorer:

    @pytest.mark.parametrize("hvac_age,expected_score", [
        (0, 25),    # Brand new - full points
        (5, 25),    # 5 years - still new category
        (6, 20),    # 6 years - good category
        (10, 20),   # 10 years - upper bound of good
        (11, 12),   # 11 years - aging category
        (15, 12),   # 15 years - upper bound of aging
        (16, 5),    # 16 years - replacement needed
        (25, 5),    # 25 years - definitely needs replacement
    ])
    def test_hvac_age_scoring(self, hvac_age, expected_score):
        """Test HVAC age scoring at boundary points."""
        prop = {"hvac_age": hvac_age}
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == expected_score

    def test_hvac_age_derived_from_year_built(self):
        """When hvac_age missing, derive from year_built."""
        prop = {"year_built": 2015}  # 10 years old in 2025
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 20  # Good category (6-10 years)

    def test_hvac_age_unknown_returns_neutral(self):
        """Unknown HVAC age should return neutral score."""
        prop = {}  # No hvac_age, no year_built
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 12.5  # Neutral (50% of 25)

    def test_hvac_install_year_takes_precedence(self):
        """hvac_install_year should override year_built derivation."""
        prop = {
            "year_built": 1990,      # House is 35 years old
            "hvac_install_year": 2020  # But HVAC replaced 5 years ago
        }
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 25  # New category based on HVAC install
```

### 8.3 New Criteria Validation

#### 8.3.1 Total Score Validation

```python
# tests/unit/services/scoring/test_total_score.py

class TestTotalScoreCalculation:

    def test_section_totals_sum_to_600(self):
        """Verify all section weights sum to 600."""
        weights = ScoringWeights()
        assert weights.section_a_max == 225
        assert weights.section_b_max == 195
        assert weights.section_c_max == 180
        assert weights.total_possible_score == 600

    def test_perfect_score_is_600(self):
        """Property with perfect scores should total 600."""
        perfect_property = {
            # Section A: 225 pts
            "school_rating": 10,
            "distance_to_highway_miles": 5.0,
            "safety_score": 100,
            "distance_to_grocery_miles": 0.3,
            "parks_walkability_score": 10,
            "orientation": "north",
            "flood_zone": "X",
            "walk_score": 100,
            "transit_score": 100,
            "bike_score": 100,
            "air_quality_index": 30,

            # Section B: 195 pts
            "roof_age": 2,
            "lot_sqft": 12000,
            "sqft": 2000,
            "year_built": 2020,
            "has_pool": True,
            "pool_equipment_age": 2,
            "monthly_cost": 2800,
            "hvac_age": 2,  # NEW

            # Section C: 180 pts
            "kitchen_layout_score": 10,
            "master_suite_score": 10,
            "natural_light_score": 10,
            "high_ceilings_score": 10,
            "fireplace_score": 10,
            "laundry_area_score": 10,
            "aesthetics_score": 10,
        }

        scorer = PropertyScorer()
        result = scorer.score(perfect_property)
        assert result.total_score == 600
```

---

## 9. Appendix: Research Report References

### 9.1 Primary Sources by Topic

| Topic | Report | Key Findings |
|-------|--------|--------------|
| Solar Lease Economics | Market-Beta | 75% leased, 3-8% value reduction, $100-200/mo payments |
| Solar Regulations | Domain-Beta | A.R.S. 44-1763 disclosure requirement, 100+ bankruptcies |
| HVAC Lifespan | Domain-Alpha | 8-15 years in AZ (not 20+), $11k-26k replacement |
| Roof Lifespan | Domain-Alpha | Underlayment 12-20 years, shingles 12-25 years |
| Pool Equipment | Market-Beta, Domain-Alpha | Pump 8-12 years, heater 11-15 years |
| Septic Systems | Domain-Gamma | 10%+ failure rate, $4k-20k replacement |
| HOA Validation | Market-Alpha | AZ 2nd-highest fees ($448 avg), 70% prefer non-HOA |
| Crime Data | Tech-Beta | Phoenix Open Data free, FBI CDE supplemental |
| WalkScore | Tech-Beta | Free tier 5K/day, integrate for scoring |

### 9.2 Research Report Locations

```
docs/analysis/research/
├── market-alpha-financial-baseline-2024-12.md
├── market-beta-pool-solar-economics-2024-12.md
├── market-gamma-demographics-appreciation-2024-12.md
├── domain-alpha-building-systems-2024-12.md
├── domain-beta-regulations-2024-12.md
├── domain-gamma-land-infrastructure-2024-12.md
├── tech-alpha-government-apis-2024-12.md
├── tech-beta-data-apis-2024-12.md
└── tech-gamma-scraping-infrastructure-2024-12.md
```

---

## 10. Implementation Checklist

```markdown
## Kill-Switch Updates
- [ ] Add SEVERITY_WEIGHT_SOLAR_LEASE = 2.5 to constants.py
- [ ] Implement SolarLeaseCriterion class
- [ ] Add solar_status to SOFT_SEVERITY_WEIGHTS
- [ ] Update evaluate_kill_switches() to include solar lease
- [ ] Add solar lease detection patterns to listing extraction
- [ ] Write unit tests for solar lease criterion
- [ ] Update kill-switch skill documentation

## Scoring Updates
- [ ] Add HVAC age constants to constants.py
- [ ] Implement HvacConditionScorer class
- [ ] Update ScoringWeights dataclass with hvac_condition
- [ ] Update Section A weights (reduce by 25 pts)
- [ ] Update Section B weights (add hvac_condition)
- [ ] Adjust roof age thresholds for Arizona
- [ ] Adjust pool equipment thresholds for Arizona
- [ ] Add HVAC to PropertyScorer orchestration
- [ ] Write unit tests for HVAC scorer
- [ ] Update scoring skill documentation

## Schema Updates
- [ ] Add solar_status field to enrichment schema
- [ ] Add hvac_age field to enrichment schema
- [ ] Add hvac_install_year field to enrichment schema
- [ ] Add hvac_condition field to enrichment schema
- [ ] Update property-data skill with new fields
- [ ] Update validation schemas

## Cost Estimation Updates
- [ ] Add solar lease to monthly cost calculation
- [ ] Update cost-efficiency skill documentation

## Testing
- [ ] Run full test suite
- [ ] Test kill-switch combinations with solar lease
- [ ] Test HVAC scoring at boundary conditions
- [ ] Validate 600-point total maintained
- [ ] Re-score sample properties for comparison
- [ ] Document tier distribution changes

## Documentation
- [ ] Update CLAUDE.md scoring section
- [ ] Update scoring skill SKILL.md
- [ ] Update kill-switch skill SKILL.md
- [ ] Update AGENT_BRIEFING.md if needed
- [ ] Add migration notes to CHANGELOG
```

---

**Document Version:** 2.0.0
**Last Updated:** December 2024
**Status:** Ready for Implementation Review
**Estimated Implementation Effort:** 16-24 hours
**Risk Level:** Low (additive changes with backwards compatibility)

# Sprint 0: Architecture Prerequisites

**Status:** Ready for Development
**Priority:** P0 (Blocks all other work)
**Estimated Points:** 8
**Created:** 2025-12-03
**Sprint:** Sprint 0

---

## Objective

Align the scoring system and kill-switch criteria with PRD requirements before implementing story-driven features. This sprint addresses critical architectural inconsistencies discovered during PRD validation:

1. **Scoring system mismatch**: Code uses 605 points, constants/YAML define 600 points
2. **Missing HARD criterion**: Square footage requirement (>1800 sqft) not implemented
3. **Outdated kill-switch**: Lot size uses range instead of minimum threshold
4. **Soft criterion misconfiguration**: Sewer requirement should be HARD, not SOFT
5. **Ambiguous garage requirement**: Need to clarify indoor vs total garage spaces

All 7 kill-switch criteria must be HARD (instant fail) to match PRD. The 605-point scoring system is correct; configuration files need updating.

---

## Acceptance Criteria

### Global Success Criteria
- [ ] `constants.py` defines: `MAX_POSSIBLE_SCORE=605`, `TIER_UNICORN_MIN=484`, `TIER_CONTENDER_MIN=363`
- [ ] `scoring_weights.yaml` section weights: `location: 250`, `systems: 175`, `interior: 180`
- [ ] All 7 kill-switch criteria are HARD (instant fail), no SOFT criteria remain
- [ ] `buyer_criteria.yaml` hard_criteria section lists all 7 criteria, soft_criteria section removed
- [ ] `filter.py` default kill switches: 7 HARD criteria, no SOFT criteria
- [ ] `constants.py` HARD_CRITERIA_NAMES set contains all 7 kill-switch names
- [ ] All unit tests pass with updated thresholds and kill-switch behavior
- [ ] `NoNewBuildKillSwitch` removed from default kill switches (not in PRD)

### Kill-Switch Criteria (PRD Requirement)
All 7 criteria must be HARD:
1. HOA fee = $0
2. Bedrooms >= 4
3. Bathrooms >= 2
4. Square footage > 1800 sqft (NEW)
5. Lot size > 8000 sqft (UPDATED from range)
6. Garage >= 1 indoor space (CLARIFIED)
7. Sewer = city (CHANGED from SOFT to HARD)

---

## ARCH-05: Update to 605-Point Scoring

### Current State

**Inconsistency discovered:**
- `scoring_weights.py` dataclass (lines 253-279): Already defines 605 pts
  - Section A: 250 pts (school_district=42, quietness=30, crime_index=47, supermarket=23, parks=23, orientation=25, flood=23, walk_transit=22, air_quality=15)
  - Section B: 175 pts (roof=45, backyard=35, plumbing=35, pool=20, cost_eff=35, solar=5)
  - Section C: 180 pts (kitchen=40, master=35, light=30, ceilings=25, fireplace=20, laundry=20, aesthetics=10)
  - `total_possible_score` property calculates 605 correctly

**But:**
- `constants.py` (line 23): `MAX_POSSIBLE_SCORE = 600`
- `constants.py` (line 27): `TIER_UNICORN_MIN = 480` (80% of 600)
- `constants.py` (line 31): `TIER_CONTENDER_MIN = 360` (60% of 600)
- `constants.py` (line 459): Assertion checks sum equals 600, not 605
- `constants.py` (lines 350-456): Section constants sum to 600 (230+180+190)
- `config/scoring_weights.yaml` (lines 30-61): Defines 600 pts (230+180+190)

**Impact:** Tier classification and documentation are wrong. Properties scored as "Unicorn" at 480+ should require 484+ (80% of 605).

### Target State

All files define 605-point system with correct tier thresholds:
- `MAX_POSSIBLE_SCORE = 605`
- `TIER_UNICORN_MIN = 484` (80% of 605)
- `TIER_CONTENDER_MIN = 363` (60% of 605)
- Section A: 250 pts
- Section B: 175 pts
- Section C: 180 pts

### Technical Tasks

#### Task 1: Update `constants.py` scoring constants
**File:** `src/phx_home_analysis/config/constants.py`

**Changes:**
```python
# Line 19-23: Update MAX_POSSIBLE_SCORE
- MAX_POSSIBLE_SCORE: Final[int] = 600
+ MAX_POSSIBLE_SCORE: Final[int] = 605

# Line 25-27: Update TIER_UNICORN_MIN (80% of 605)
- TIER_UNICORN_MIN: Final[int] = 480
+ TIER_UNICORN_MIN: Final[int] = 484

# Line 29-31: Update TIER_CONTENDER_MIN (60% of 605)
- TIER_CONTENDER_MIN: Final[int] = 360
+ TIER_CONTENDER_MIN: Final[int] = 363

# Line 33-35: Update TIER_PASS_MAX
- TIER_PASS_MAX: Final[int] = 359
+ TIER_PASS_MAX: Final[int] = 362
```

#### Task 2: Update section weight constants in `constants.py`
**File:** `src/phx_home_analysis/config/constants.py`

**Changes:**
```python
# Lines 350-384: Section A constants (update comment and totals)
# Change "230 pts max" to "250 pts max" in header comment
# Update individual criteria to match scoring_weights.py:

SCORE_SECTION_A_SCHOOL_DISTRICT: Final[int] = 42  # Was 50
SCORE_SECTION_A_QUIETNESS: Final[int] = 30        # Was 40
SCORE_SECTION_A_CRIME_INDEX: Final[int] = 47      # NEW (replaces SAFETY)
SCORE_SECTION_A_SUPERMARKET_PROXIMITY: Final[int] = 23  # Was 30
SCORE_SECTION_A_PARKS_WALKABILITY: Final[int] = 23     # Was 30
SCORE_SECTION_A_SUN_ORIENTATION: Final[int] = 25       # Was 30
SCORE_SECTION_A_FLOOD_RISK: Final[int] = 23            # NEW
SCORE_SECTION_A_WALK_TRANSIT: Final[int] = 22          # NEW
SCORE_SECTION_A_AIR_QUALITY: Final[int] = 15           # NEW

# Lines 386-415: Section B constants (update comment and totals)
# Change "180 pts max" to "175 pts max" in header comment

SCORE_SECTION_B_ROOF_CONDITION: Final[int] = 45        # Was 50
SCORE_SECTION_B_BACKYARD_UTILITY: Final[int] = 35      # Was 40
SCORE_SECTION_B_PLUMBING_ELECTRICAL: Final[int] = 35   # Was 40
SCORE_SECTION_B_POOL_CONDITION: Final[int] = 20        # Same
SCORE_SECTION_B_COST_EFFICIENCY: Final[int] = 35       # Was 30
SCORE_SECTION_B_SOLAR_STATUS: Final[int] = 5           # NEW

# Lines 417-456: Section C constants (update comment and totals)
# Change "190 pts max" to "180 pts max" in header comment

SCORE_SECTION_C_KITCHEN_LAYOUT: Final[int] = 40        # Same
SCORE_SECTION_C_MASTER_SUITE: Final[int] = 35          # Was 40
SCORE_SECTION_C_NATURAL_LIGHT: Final[int] = 30         # Same
SCORE_SECTION_C_HIGH_CEILINGS: Final[int] = 25         # Was 30
SCORE_SECTION_C_FIREPLACE: Final[int] = 20             # Same
SCORE_SECTION_C_LAUNDRY_AREA: Final[int] = 20          # Same
SCORE_SECTION_C_AESTHETICS: Final[int] = 10            # Same

# Line 459: Update assertion to check 605
assert SCORE_SECTION_A_TOTAL + SCORE_SECTION_B_TOTAL + SCORE_SECTION_C_TOTAL == 605
```

#### Task 3: Update `scoring_weights.yaml`
**File:** `config/scoring_weights.yaml`

**Changes:**
```yaml
# Lines 29-61: Update section_weights
section_weights:
  location:           # Section A
-   points: 230
-   weight: 0.3833    # 230/600
+   points: 250
+   weight: 0.4132    # 250/605
    criteria:
-     school: 50
-     quietness: 40
-     safety: 50
-     supermarket: 30
-     parks: 30
-     sun_orientation: 30
+     school: 42
+     quietness: 30
+     crime_index: 47
+     supermarket: 23
+     parks: 23
+     sun_orientation: 25
+     flood_risk: 23
+     walk_transit: 22
+     air_quality: 15

  systems:            # Section B
-   points: 180
-   weight: 0.3000    # 180/600
+   points: 175
+   weight: 0.2893    # 175/605
    criteria:
-     roof: 50
-     backyard: 40
-     plumbing: 40
+     roof: 45
+     backyard: 35
+     plumbing: 35
      pool: 20
-     cost_efficiency: 30
+     cost_efficiency: 35
+     solar_status: 5

  interior:           # Section C
-   points: 190
-   weight: 0.3167    # 190/600
+   points: 180
+   weight: 0.2975    # 180/605
    criteria:
      kitchen: 40
-     master_bedroom: 40
+     master_bedroom: 35
      light: 30
-     ceilings: 30
+     ceilings: 25
      fireplace: 20
      laundry: 20
      aesthetics: 10

# Lines 68-82: Update tier_thresholds
tier_thresholds:
  unicorn:
-   min_score: 480
+   min_score: 484
    label: "Unicorn"
-   description: "Exceptional properties (480+ pts)"
+   description: "Exceptional properties (484+ pts)"

  contender:
-   min_score: 360
+   min_score: 363
    label: "Contender"
-   description: "Strong properties (360-480 pts)"
+   description: "Strong properties (363-484 pts)"

  pass:
    min_score: 0
    label: "Pass"
-   description: "Acceptable properties (0-360 pts)"
+   description: "Acceptable properties (0-363 pts)"

# Lines 89-91: Update defaults
defaults:
- value_zone_min_score: 365
+ value_zone_min_score: 363
  value_zone_max_price: 550000
```

#### Task 4: Update `scoring_weights.py` docstring and constants
**File:** `src/phx_home_analysis/config/scoring_weights.py`

**Changes:**
```python
# Line 7: Update total score comment
- Total possible score: 600 points
+ Total possible score: 605 points

# Line 8: Update section breakdown
- Note: Section A totals 250 points (not 150) based on specified individual weights.
+ Section breakdown: A=250pts, B=175pts, C=180pts

# Lines 365-377: Update TierThresholds docstring
- Thresholds are calibrated to the 600-point scoring scale
- (Section A: 230 pts, Section B: 180 pts, Section C: 190 pts).
+ Thresholds are calibrated to the 605-point scoring scale
+ (Section A: 250 pts, Section B: 175 pts, Section C: 180 pts).

# Lines 370-377: Update threshold values
- unicorn_min: int = 480  # Exceptional - immediate action (80%+ of 600)
- contender_min: int = 360  # Strong - serious consideration (60-80% of 600)
- pass_max: int = 359  # Meets minimums but unremarkable (<60% of 600)
+ unicorn_min: int = 484  # Exceptional - immediate action (80%+ of 605)
+ contender_min: int = 363  # Strong - serious consideration (60-80% of 605)
+ pass_max: int = 362  # Meets minimums but unremarkable (<60% of 605)
```

### Tests Required

#### Test 1: `test_constants_605_scoring_system`
**File:** `tests/unit/test_constants.py` (create if not exists)

**Test coverage:**
- Verify `MAX_POSSIBLE_SCORE == 605`
- Verify tier thresholds: `TIER_UNICORN_MIN == 484`, `TIER_CONTENDER_MIN == 363`
- Verify section totals: `SCORE_SECTION_A_TOTAL == 250`, `SCORE_SECTION_B_TOTAL == 175`, `SCORE_SECTION_C_TOTAL == 180`
- Verify assertion passes: `assert A + B + C == 605`

#### Test 2: `test_scoring_weights_605_total`
**File:** `tests/unit/test_scoring_weights.py` (update existing)

**Test coverage:**
- Verify `ScoringWeights().total_possible_score == 605`
- Verify `section_a_max == 250`, `section_b_max == 175`, `section_c_max == 180`
- Verify `TierThresholds.unicorn_min == 484`, `TierThresholds.contender_min == 363`
- Verify `classify()` method uses correct thresholds

#### Test 3: Integration test for tier classification
**File:** `tests/integration/test_tier_classification.py` (update existing)

**Test coverage:**
- Property with score 483 → Contender (below new Unicorn threshold)
- Property with score 484 → Unicorn (at new threshold)
- Property with score 362 → Pass (below new Contender threshold)
- Property with score 363 → Contender (at new threshold)

---

## ARCH-04: Implement SqftKillSwitch

### Current State

**Missing implementation:**
- No `SqftKillSwitch` or `MinSqftKillSwitch` class exists in `criteria.py`
- `filter.py` default kill switches (lines 95-104): Only 8 criteria, missing sqft
- `constants.py` HARD_CRITERIA_NAMES (line 88): Missing "min_sqft" entry
- `buyer_criteria.yaml`: No sqft criterion defined

**PRD requirement:** Properties must have >1800 sqft (HARD criterion, instant fail if <= 1800 sqft)

### Target State

New HARD kill-switch criterion implemented:
- `MinSqftKillSwitch(min_sqft=1800)` class in `criteria.py`
- Added to default kill switches in `filter.py`
- Added to HARD_CRITERIA_NAMES set in `constants.py`
- Documented in `buyer_criteria.yaml`

### Technical Tasks

#### Task 1: Create `MinSqftKillSwitch` class
**File:** `src/phx_home_analysis/services/kill_switch/criteria.py`

**Implementation:**
```python
class MinSqftKillSwitch(KillSwitch):
    """Kill switch: Property must have minimum square footage.

    Buyer requirement is at least 1800 sqft of living space. Properties
    with less square footage are automatically rejected.
    """

    def __init__(self, min_sqft: int = 1800):
        """Initialize sqft kill switch with minimum requirement.

        Args:
            min_sqft: Minimum square feet required (default: 1800)
        """
        self._min_sqft = min_sqft

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_sqft"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Minimum {self._min_sqft:,} sqft required"

    @property
    def is_hard(self) -> bool:
        """This is a HARD criterion (instant fail)."""
        return True

    def check(self, property: "Property") -> bool:
        """Test if property has minimum square footage.

        Args:
            property: Property to evaluate

        Returns:
            True if sqft > min_sqft, False otherwise
        """
        # sqft is required field in Property, should never be None
        # But handle defensively
        if property.sqft is None:
            return False
        return property.sqft > self._min_sqft

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with sqft.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual sqft
        """
        if property.sqft is None:
            return f"Square footage unknown (buyer requires {self._min_sqft:,}+ sqft)"
        return f"Only {property.sqft:,} sqft (buyer requires >{self._min_sqft:,} sqft)"
```

**Location:** Add after `MinBathroomsKillSwitch` (after line 281)

#### Task 2: Add to default kill switches
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Line 33: Add import
from .criteria import (
    CitySewerKillSwitch,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
+   MinSqftKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)

# Lines 95-104: Add to default kill switches
return [
    NoHoaKillSwitch(),
    NoSolarLeaseKillSwitch(),
    MinBedroomsKillSwitch(min_beds=4),
    MinBathroomsKillSwitch(min_baths=2.0),
+   MinSqftKillSwitch(min_sqft=1800),
    # ... rest of switches
]
```

#### Task 3: Update `constants.py` HARD_CRITERIA_NAMES
**File:** `src/phx_home_analysis/services/kill_switch/constants.py`

**Changes:**
```python
# Line 88: Add "min_sqft" to HARD_CRITERIA_NAMES set
- HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "no_solar_lease"}
+ HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "no_solar_lease"}
```

#### Task 4: Update `buyer_criteria.yaml`
**File:** `config/buyer_criteria.yaml`

**Changes:**
```yaml
# Lines 15-18: Add min_sqft to hard_criteria
hard_criteria:
  hoa_fee: 0        # Must be zero (no HOA allowed)
  min_beds: 4       # Minimum 4 bedrooms required
  min_baths: 2      # Minimum 2 bathrooms required
+ min_sqft: 1800    # Minimum 1800 square feet required
```

### Tests Required

#### Test 1: `test_min_sqft_kill_switch_pass`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Property with sqft=2000 → PASS (above threshold)
- Property with sqft=1801 → PASS (just above threshold)
- Verify `is_hard == True`

#### Test 2: `test_min_sqft_kill_switch_fail`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Property with sqft=1800 → FAIL (at threshold, not above)
- Property with sqft=1500 → FAIL (below threshold)
- Property with sqft=None → FAIL (missing data)
- Verify failure message includes actual sqft

#### Test 3: `test_default_kill_switches_include_sqft`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Verify `KillSwitchFilter()` includes `MinSqftKillSwitch` in default switches
- Verify `get_hard_criteria()` includes sqft criterion
- Verify count of hard criteria is correct after addition

---

## ARCH-03: Fix LotSizeKillSwitch

### Current State

**Current implementation:**
- `LotSizeKillSwitch` (lines 283-348 in `criteria.py`): Range-based (7000-15000 sqft)
- Default instance (line 102 in `filter.py`): `LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)`
- Classification: SOFT criterion (severity 1.0)
- `buyer_criteria.yaml` (lines 44-47): Defines min=7000, max=15000, severity=1.0

**PRD requirement:** Lot size must be >8000 sqft (HARD criterion, no maximum)

**Rationale:** Phoenix market reality shows 7k-8k lots are often small/cramped. 8k+ provides comfortable space. Large lots (>15k) are acceptable in Phoenix (common in North Phoenix/Anthem).

### Target State

Updated HARD criterion:
- Minimum lot size: 8000 sqft (increased from 7000)
- No maximum (removed 15000 cap)
- HARD criterion (changed from SOFT)
- Instant fail if lot_sqft <= 8000 or lot_sqft is None

### Technical Tasks

#### Task 1: Update `LotSizeKillSwitch` class
**File:** `src/phx_home_analysis/services/kill_switch/criteria.py`

**Changes:**
```python
# Lines 283-348: Update LotSizeKillSwitch

class LotSizeKillSwitch(KillSwitch):
-   """Kill switch: Property lot must be within 7,000-15,000 sqft range.
+   """Kill switch: Property lot must be at least 8,000 sqft.

-   Buyer requirement is lot size between 7,000 and 15,000 square feet.
-   Properties outside this range (too small or too large) are automatically
-   rejected.
+   Buyer requirement is lot size greater than 8,000 square feet.
+   Properties with smaller lots are automatically rejected.
+   No maximum lot size (larger lots are acceptable in Phoenix market).
    """

-   def __init__(self, min_sqft: int = 7000, max_sqft: int = 15000):
+   def __init__(self, min_sqft: int = 8000, max_sqft: int | None = None):
        """Initialize lot size kill switch with minimum threshold.

        Args:
-           min_sqft: Minimum lot size in square feet (default: 7000)
-           max_sqft: Maximum lot size in square feet (default: 15000)
+           min_sqft: Minimum lot size in square feet (default: 8000)
+           max_sqft: Maximum lot size (optional, default: None = no max)
        """
        self._min_sqft = min_sqft
        self._max_sqft = max_sqft

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "lot_size"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
-       return f"Lot size must be {self._min_sqft:,}-{self._max_sqft:,} sqft"
+       if self._max_sqft is not None:
+           return f"Lot size must be {self._min_sqft:,}-{self._max_sqft:,} sqft"
+       return f"Lot size must be >{self._min_sqft:,} sqft"

+   @property
+   def is_hard(self) -> bool:
+       """This is a HARD criterion (instant fail)."""
+       return True

    def check(self, property: "Property") -> bool:
-       """Test if property lot size is within acceptable range.
+       """Test if property lot size meets minimum requirement.

        Args:
            property: Property to evaluate

        Returns:
-           True if min_sqft <= lot_sqft <= max_sqft, False otherwise
+           True if lot_sqft > min_sqft (and < max_sqft if max set), False otherwise
        """
        # None or missing lot size fails (cannot verify requirement)
        if property.lot_sqft is None:
            return False
-       return self._min_sqft <= property.lot_sqft <= self._max_sqft
+       if self._max_sqft is not None:
+           return property.lot_sqft > self._min_sqft and property.lot_sqft <= self._max_sqft
+       return property.lot_sqft > self._min_sqft

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with lot size.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual lot size
        """
        if property.lot_sqft is None:
-           return (
-               f"Lot size unknown (buyer requires "
-               f"{self._min_sqft:,}-{self._max_sqft:,} sqft)"
-           )
-       elif property.lot_sqft < self._min_sqft:
+           if self._max_sqft is not None:
+               return f"Lot size unknown (buyer requires {self._min_sqft:,}-{self._max_sqft:,} sqft)"
+           return f"Lot size unknown (buyer requires >{self._min_sqft:,} sqft)"
+       elif property.lot_sqft <= self._min_sqft:
            return (
-               f"Lot too small: {property.lot_sqft:,} sqft "
-               f"(buyer requires {self._min_sqft:,}+ sqft)"
+               f"Lot too small: {property.lot_sqft:,} sqft "
+               f"(buyer requires >{self._min_sqft:,} sqft)"
            )
-       else:  # lot_sqft > max_sqft
+       elif self._max_sqft is not None and property.lot_sqft > self._max_sqft:
            return (
                f"Lot too large: {property.lot_sqft:,} sqft "
                f"(buyer requires max {self._max_sqft:,} sqft)"
            )
+       # Should not reach here if check() returned False
+       return f"Failed kill switch: {self.description}"
```

#### Task 2: Update default kill switch instantiation
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Line 102: Update LotSizeKillSwitch instantiation
- LotSizeKillSwitch(min_sqft=7000, max_sqft=15000),
+ LotSizeKillSwitch(min_sqft=8000),  # No max_sqft (None = no upper limit)
```

#### Task 3: Update `buyer_criteria.yaml` - Move to hard_criteria
**File:** `config/buyer_criteria.yaml`

**Changes:**
```yaml
# Lines 15-18: Add lot_sqft to hard_criteria
hard_criteria:
  hoa_fee: 0        # Must be zero (no HOA allowed)
  min_beds: 4       # Minimum 4 bedrooms required
  min_baths: 2      # Minimum 2 bathrooms required
  min_sqft: 1800    # Minimum 1800 square feet required
+ min_lot_sqft: 8000  # Minimum 8000 sqft lot required (no maximum)

# Lines 27-48: Remove lot_sqft from soft_criteria
soft_criteria:
  # ... other criteria ...

- # Lot size range
- lot_sqft:
-   min: 7000                     # Minimum 7,000 square feet
-   max: 15000                    # Maximum 15,000 square feet
-   severity: 1.0                 # Minor preference - low weight
```

#### Task 4: Update `constants.py` - Remove LOT_SIZE from SOFT weights
**File:** `src/phx_home_analysis/services/kill_switch/constants.py`

**Changes:**
```python
# Lines 61-66: Remove lot_size from SOFT_SEVERITY_WEIGHTS
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
    "sewer": SEVERITY_WEIGHT_SEWER,        # Septic risk - infrastructure concern
    "garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
-   "lot_size": SEVERITY_WEIGHT_LOT_SIZE,  # Minor preference
    "year_built": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Lines 71-76: Remove lot_size from SOFT_SEVERITY_WEIGHTS_SERVICE
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
    "city_sewer": SEVERITY_WEIGHT_SEWER,       # Septic risk - infrastructure concern
    "min_garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
-   "lot_size": SEVERITY_WEIGHT_LOT_SIZE,      # Minor preference
    "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Line 88: Add lot_size to HARD_CRITERIA_NAMES
- HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "no_solar_lease"}
+ HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "lot_size", "no_solar_lease"}
```

#### Task 5: Remove `SEVERITY_WEIGHT_LOT_SIZE` from `constants.py` (optional cleanup)
**File:** `src/phx_home_analysis/config/constants.py`

**Changes:**
```python
# Lines 71-73: Mark as deprecated or remove
- # Lot size (7k-15k sqft range): Preference factor, wide acceptable range
- # Adds 1.0 severity if outside target range
- SEVERITY_WEIGHT_LOT_SIZE: Final[float] = 1.0
+ # LOT SIZE MOVED TO HARD CRITERIA (no severity weight)
+ # See kill_switch/criteria.py LotSizeKillSwitch
```

### Tests Required

#### Test 1: `test_lot_size_kill_switch_hard_criterion`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Verify `LotSizeKillSwitch().is_hard == True`
- Property with lot_sqft=8001 → PASS (just above min)
- Property with lot_sqft=8000 → FAIL (at threshold, not above)
- Property with lot_sqft=7500 → FAIL (below min)
- Property with lot_sqft=20000 → PASS (no max limit)
- Property with lot_sqft=None → FAIL (missing data)

#### Test 2: `test_lot_size_default_8000_no_max`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Verify default `LotSizeKillSwitch` uses min_sqft=8000, max_sqft=None
- Verify large lots (15k+) pass default filter
- Verify 8k or smaller lots fail default filter

#### Test 3: `test_lot_size_backward_compat_with_max`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Instantiate `LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)` (old behavior)
- Verify range-based checking still works if max_sqft provided
- Property with lot_sqft=16000 → FAIL (exceeds max)
- Property with lot_sqft=10000 → PASS (within range)

---

## ARCH-02: SewerKillSwitch → HARD

### Current State

**Current implementation:**
- `CitySewerKillSwitch` (lines 75-120 in `criteria.py`): SOFT criterion (severity 2.5)
- `base.py` KillSwitch base class: `is_hard` property defaults to `False`
- Default instance (line 98 in `filter.py`): `CitySewerKillSwitch()` (SOFT)
- `constants.py` (line 62): `SEVERITY_WEIGHT_SEWER = 2.5`
- `buyer_criteria.yaml` (lines 29-31): Defined as soft_criteria with severity 2.5

**PRD requirement:** City sewer is HARD criterion (instant fail if not city sewer)

**Rationale:** Septic systems in Phoenix metro are infrastructure risk (maintenance burden, failure risk, resale challenges). Not negotiable for buyer profile.

### Target State

HARD criterion:
- `CitySewerKillSwitch.is_hard` returns `True`
- Removed from SOFT_SEVERITY_WEIGHTS dicts
- Moved to hard_criteria in `buyer_criteria.yaml`
- Instant fail if sewer_type != CITY

### Technical Tasks

#### Task 1: Update `CitySewerKillSwitch` to HARD
**File:** `src/phx_home_analysis/services/kill_switch/criteria.py`

**Changes:**
```python
# Lines 75-120: Add is_hard property to CitySewerKillSwitch

class CitySewerKillSwitch(KillSwitch):
    """Kill switch: Property must have city sewer (no septic).

    Buyer requirement is municipal sewer connection. Properties with septic
    systems are automatically rejected.
    """

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "city_sewer"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return "City sewer required (no septic systems)"

+   @property
+   def is_hard(self) -> bool:
+       """This is a HARD criterion (instant fail)."""
+       return True

    def check(self, property: "Property") -> bool:
        # ... existing implementation ...
```

#### Task 2: Update `constants.py` - Remove sewer from SOFT weights
**File:** `src/phx_home_analysis/services/kill_switch/constants.py`

**Changes:**
```python
# Lines 61-66: Remove sewer from SOFT_SEVERITY_WEIGHTS
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
-   "sewer": SEVERITY_WEIGHT_SEWER,        # Septic risk - infrastructure concern
    "garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "year_built": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Lines 71-76: Remove city_sewer from SOFT_SEVERITY_WEIGHTS_SERVICE
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
-   "city_sewer": SEVERITY_WEIGHT_SEWER,       # Septic risk - infrastructure concern
    "min_garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Line 88: Add city_sewer to HARD_CRITERIA_NAMES
- HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "lot_size", "no_solar_lease"}
+ HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "lot_size", "city_sewer", "no_solar_lease"}
```

#### Task 3: Update `buyer_criteria.yaml` - Move to hard_criteria
**File:** `config/buyer_criteria.yaml`

**Changes:**
```yaml
# Lines 15-20: Add sewer_type to hard_criteria
hard_criteria:
  hoa_fee: 0        # Must be zero (no HOA allowed)
  min_beds: 4       # Minimum 4 bedrooms required
  min_baths: 2      # Minimum 2 bathrooms required
  min_sqft: 1800    # Minimum 1800 square feet required
  min_lot_sqft: 8000  # Minimum 8000 sqft lot required (no maximum)
+ sewer_type: "city"  # City sewer required (no septic)

# Lines 27-32: Remove sewer_type from soft_criteria
soft_criteria:
- # City sewer requirement (no septic systems)
- sewer_type:
-   required: "city"              # Accepted values: "city", "city_sewer", "municipal", "public"
-   severity: 2.5                 # Infrastructure concern - high weight

  # ... other criteria ...
```

#### Task 4: Mark `SEVERITY_WEIGHT_SEWER` as deprecated
**File:** `src/phx_home_analysis/config/constants.py`

**Changes:**
```python
# Lines 59-61: Mark as deprecated
- # City sewer required: Septic is infrastructure concern, adds 2.5 severity
- # Septic systems are less desirable in Phoenix metro and add maintenance burden
- SEVERITY_WEIGHT_SEWER: Final[float] = 2.5
+ # CITY SEWER MOVED TO HARD CRITERIA (no severity weight)
+ # See kill_switch/criteria.py CitySewerKillSwitch
```

### Tests Required

#### Test 1: `test_city_sewer_is_hard_criterion`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Verify `CitySewerKillSwitch().is_hard == True`
- Property with sewer_type=CITY → PASS
- Property with sewer_type=SEPTIC → FAIL (instant)
- Property with sewer_type=UNKNOWN → FAIL (instant)
- Property with sewer_type=None → FAIL (instant)

#### Test 2: `test_sewer_instant_fail_no_severity`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Property fails sewer but no other criteria
- Verify verdict=FAIL (instant, not WARNING)
- Verify severity_score=0.0 (HARD failures don't contribute to severity)
- Verify failure message indicates instant fail

---

## ARCH-01: GarageKillSwitch Indoor Required

### Current State

**Current implementation:**
- `MinGarageKillSwitch` (lines 122-173 in `criteria.py`): SOFT criterion (severity 1.5), min_spaces=2
- Default instance (line 99 in `filter.py`): `MinGarageKillSwitch(min_spaces=2)` (SOFT)
- `constants.py` (line 68): `SEVERITY_WEIGHT_GARAGE = 1.5`
- `buyer_criteria.yaml` (lines 39-41): Defined as soft_criteria, min=2, severity=1.5
- Property entity: Has `garage_spaces` field (int) but no `indoor_garage` field

**PRD requirement:** Minimum 1 indoor garage space (HARD criterion)

**Clarification needed:**
- "Indoor" means attached/direct access garage (not detached/carport)
- Some properties may have `garage_spaces=2` but only carport (no indoor)
- Need to distinguish between total parking spaces and indoor garage spaces

**Data limitation:** Current `garage_spaces` field doesn't distinguish indoor vs outdoor. May need enrichment.

### Target State

HARD criterion with indoor requirement:
- Minimum 1 indoor garage space (changed from 2 total spaces)
- HARD criterion (changed from SOFT)
- Instant fail if `garage_spaces < 1` OR `indoor_garage == False`
- **Note:** Indoor garage detection may require Phase 2 image analysis or listing text parsing

### Technical Tasks

#### Task 1: Update `MinGarageKillSwitch` to HARD with indoor check
**File:** `src/phx_home_analysis/services/kill_switch/criteria.py`

**Changes:**
```python
# Lines 122-173: Update MinGarageKillSwitch

class MinGarageKillSwitch(KillSwitch):
-   """Kill switch: Property must have minimum 2-car garage.
+   """Kill switch: Property must have minimum 1 indoor garage space.

-   Buyer requirement is at least 2 garage spaces. Properties with less than
-   2 garage spaces are automatically rejected.
+   Buyer requirement is at least 1 indoor garage space (attached/direct access).
+   Properties without indoor garage are automatically rejected. Detached garages
+   and carports do not count toward indoor garage requirement.
    """

-   def __init__(self, min_spaces: int = 2):
+   def __init__(self, min_spaces: int = 1, indoor_required: bool = True):
        """Initialize garage kill switch with minimum space requirement.

        Args:
-           min_spaces: Minimum number of garage spaces required (default: 2)
+           min_spaces: Minimum number of garage spaces required (default: 1)
+           indoor_required: Whether garage must be indoor/attached (default: True)
        """
        self._min_spaces = min_spaces
+       self._indoor_required = indoor_required

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_garage"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
-       return f"Minimum {self._min_spaces}-car garage required"
+       if self._indoor_required:
+           return f"Minimum {self._min_spaces} indoor garage space(s) required"
+       return f"Minimum {self._min_spaces} garage space(s) required"

+   @property
+   def is_hard(self) -> bool:
+       """This is a HARD criterion (instant fail)."""
+       return True

    def check(self, property: "Property") -> bool:
        """Test if property has minimum garage spaces.

        Args:
            property: Property to evaluate

        Returns:
-           True if garage_spaces >= min_spaces, False otherwise
+           True if garage_spaces >= min_spaces (and indoor if required), False otherwise
        """
        # None or missing garage data fails (cannot verify requirement)
        if property.garage_spaces is None:
            return False
-       return property.garage_spaces >= self._min_spaces
+
+       # Check minimum spaces
+       if property.garage_spaces < self._min_spaces:
+           return False
+
+       # If indoor required, check indoor_garage field (if available)
+       if self._indoor_required:
+           # Check if property has indoor_garage field
+           indoor_garage = getattr(property, 'indoor_garage', None)
+           if indoor_garage is None:
+               # Field not available - assume garage is indoor if garage_spaces >= 1
+               # This is a reasonable default for listings (most 1+ car garages are attached)
+               return property.garage_spaces >= self._min_spaces
+           # Field available - check it
+           return indoor_garage is True
+
+       return True

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with garage count.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual garage spaces
        """
        if property.garage_spaces is None:
-           return f"Garage spaces unknown (buyer requires {self._min_spaces}+ car garage)"
-       return f"Only {property.garage_spaces}-car garage (buyer requires {self._min_spaces}+)"
+           if self._indoor_required:
+               return f"Garage spaces unknown (buyer requires {self._min_spaces}+ indoor garage)"
+           return f"Garage spaces unknown (buyer requires {self._min_spaces}+ garage spaces)"
+
+       # Check if failure is due to indoor requirement
+       indoor_garage = getattr(property, 'indoor_garage', None)
+       if self._indoor_required and indoor_garage is False:
+           return (
+               f"No indoor garage (has {property.garage_spaces} spaces but detached/carport only, "
+               f"buyer requires {self._min_spaces}+ indoor garage)"
+           )
+
+       # Failure due to insufficient spaces
+       if self._indoor_required:
+           return (
+               f"Only {property.garage_spaces} garage space(s) "
+               f"(buyer requires {self._min_spaces}+ indoor garage)"
+           )
+       return f"Only {property.garage_spaces} garage space(s) (buyer requires {self._min_spaces}+)"
```

#### Task 2: Update default kill switch instantiation
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Line 99: Update MinGarageKillSwitch instantiation
- MinGarageKillSwitch(min_spaces=2),
+ MinGarageKillSwitch(min_spaces=1, indoor_required=True),
```

#### Task 3: Update `constants.py` - Remove garage from SOFT weights
**File:** `src/phx_home_analysis/services/kill_switch/constants.py`

**Changes:**
```python
# Lines 61-66: Remove garage from SOFT_SEVERITY_WEIGHTS
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
-   "garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "year_built": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Lines 71-76: Remove min_garage from SOFT_SEVERITY_WEIGHTS_SERVICE
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
-   "min_garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Line 88: Add min_garage to HARD_CRITERIA_NAMES
- HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "lot_size", "city_sewer", "no_solar_lease"}
+ HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms", "min_sqft", "lot_size", "city_sewer", "min_garage", "no_solar_lease"}
```

#### Task 4: Update `buyer_criteria.yaml` - Move to hard_criteria
**File:** `config/buyer_criteria.yaml`

**Changes:**
```yaml
# Lines 15-21: Add garage to hard_criteria
hard_criteria:
  hoa_fee: 0        # Must be zero (no HOA allowed)
  min_beds: 4       # Minimum 4 bedrooms required
  min_baths: 2      # Minimum 2 bathrooms required
  min_sqft: 1800    # Minimum 1800 square feet required
  min_lot_sqft: 8000  # Minimum 8000 sqft lot required (no maximum)
  sewer_type: "city"  # City sewer required (no septic)
+ min_garage: 1      # Minimum 1 indoor garage space required (attached/direct access)

# Lines 33-41: Remove garage_spaces from soft_criteria
soft_criteria:
- # Minimum garage spaces
- garage_spaces:
-   min: 2                        # At least 2-car garage
-   severity: 1.5                 # Convenience factor - moderate weight

  # ... other criteria ...
```

#### Task 5: Mark `SEVERITY_WEIGHT_GARAGE` as deprecated
**File:** `src/phx_home_analysis/config/constants.py`

**Changes:**
```python
# Lines 67-69: Mark as deprecated
- # 2-car garage minimum: Convenience factor in Phoenix metro living
- # Adds 1.5 severity if less than 2 spaces
- SEVERITY_WEIGHT_GARAGE: Final[float] = 1.5
+ # GARAGE MOVED TO HARD CRITERIA (no severity weight)
+ # See kill_switch/criteria.py MinGarageKillSwitch
```

#### Task 6: Add `indoor_garage` field to Property entity (optional, Phase 2)
**File:** `src/phx_home_analysis/domain/entities.py`

**Changes (optional - for future enrichment):**
```python
@dataclass
class Property:
    # ... existing fields ...
    garage_spaces: int | None = None
+   indoor_garage: bool | None = None  # True=attached/direct access, False=detached/carport
```

**Note:** This field will initially be `None` for all properties. Phase 2 image assessment or listing text parsing can populate it.

### Tests Required

#### Test 1: `test_min_garage_hard_criterion_1_space`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Verify `MinGarageKillSwitch(min_spaces=1).is_hard == True`
- Property with garage_spaces=1, indoor_garage=True → PASS
- Property with garage_spaces=2, indoor_garage=True → PASS
- Property with garage_spaces=0 → FAIL
- Property with garage_spaces=None → FAIL

#### Test 2: `test_min_garage_indoor_required`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Property with garage_spaces=2, indoor_garage=False → FAIL (has spaces but not indoor)
- Property with garage_spaces=1, indoor_garage=True → PASS (indoor requirement met)
- Property with garage_spaces=1, indoor_garage=None → PASS (assume indoor if spaces >= 1)
- Verify failure message includes "detached/carport only" when indoor_garage=False

#### Test 3: `test_default_garage_1_indoor`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Verify default `MinGarageKillSwitch` uses min_spaces=1, indoor_required=True
- Verify changed from old default (min_spaces=2, SOFT)

#### Test 4: `test_garage_backward_compat_no_indoor_check`
**File:** `tests/unit/test_kill_switch.py`

**Test coverage:**
- Instantiate `MinGarageKillSwitch(min_spaces=2, indoor_required=False)` (old behavior)
- Verify indoor_garage field not checked if indoor_required=False
- Property with garage_spaces=2 → PASS (regardless of indoor_garage value)

---

## Cleanup: Remove NoNewBuildKillSwitch from Defaults

### Current State

**Identified discrepancy:**
- `NoNewBuildKillSwitch` exists in default kill switches (line 103 in `filter.py`)
- Not listed in PRD kill-switch criteria (only 7 criteria defined)
- Currently SOFT (severity 2.0)

**Decision:** Remove from defaults. Not in PRD requirements. If buyer wants it later, can add via custom kill switches.

### Technical Tasks

#### Task 1: Remove from default kill switches
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Lines 95-104: Remove NoNewBuildKillSwitch from default list
return [
    NoHoaKillSwitch(),
    NoSolarLeaseKillSwitch(),
    MinBedroomsKillSwitch(min_beds=4),
    MinBathroomsKillSwitch(min_baths=2.0),
    MinSqftKillSwitch(min_sqft=1800),
    LotSizeKillSwitch(min_sqft=8000),
    CitySewerKillSwitch(),
    MinGarageKillSwitch(min_spaces=1, indoor_required=True),
-   NoNewBuildKillSwitch(max_year=2023),
]
```

#### Task 2: Update docstring in `filter.py`
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Lines 50-58: Update docstring
"""
Default kill switches match buyer requirements from CLAUDE.md:
- NO HOA (HARD)
- NO solar lease (HARD)
- Minimum 4 bedrooms (HARD)
- Minimum 2 bathrooms (HARD)
- Minimum 1800 sqft (HARD)
- Lot size > 8000 sqft (HARD)
- City sewer only (HARD)
- Minimum 1 indoor garage space (HARD)
"""
```

#### Task 3: Remove from imports (optional cleanup)
**File:** `src/phx_home_analysis/services/kill_switch/filter.py`

**Changes:**
```python
# Lines 26-35: Remove NoNewBuildKillSwitch import if no longer used
from .criteria import (
    CitySewerKillSwitch,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
    MinSqftKillSwitch,
    NoHoaKillSwitch,
-   NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)
```

**Note:** Keep `NoNewBuildKillSwitch` class in `criteria.py` for backward compatibility and custom use.

#### Task 4: Remove year_built from SOFT weights (no longer in defaults)
**File:** `src/phx_home_analysis/services/kill_switch/constants.py`

**Changes:**
```python
# Lines 61-66: Remove year_built from SOFT_SEVERITY_WEIGHTS (empty dict now)
- SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
-     "year_built": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
- }
+ SOFT_SEVERITY_WEIGHTS: dict[str, float] = {}

# Lines 71-76: Remove no_new_build from SOFT_SEVERITY_WEIGHTS_SERVICE (empty dict now)
- SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
-     "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
- }
+ SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {}
```

#### Task 5: Remove soft_criteria section from `buyer_criteria.yaml`
**File:** `config/buyer_criteria.yaml`

**Changes:**
```yaml
# Lines 22-74: Remove entire soft_criteria section and thresholds
- # =============================================================================
- # SOFT CRITERIA (Severity Weighted)
- # =============================================================================
- # Each failed criterion contributes its severity weight to total severity score
- # Property FAILS if total severity >= severity_fail threshold
- # Property gets WARNING if total severity >= severity_warning threshold
-
- soft_criteria:
-   # No new builds (must be built before current year)
-   year_built:
-     max: "current_year"           # Special token - evaluated as datetime.now().year
-     severity: 2.0                 # New build avoidance - moderate-high weight
-
- # =============================================================================
- # SEVERITY THRESHOLDS
- # =============================================================================
- # Thresholds determine final verdict based on accumulated severity score
-
- thresholds:
-   severity_fail: 3.0              # Total severity >= 3.0 -> FAIL
-   severity_warning: 1.5           # Total severity >= 1.5 -> WARNING
-                                   # Total severity < 1.5 -> PASS

# Add note about all criteria being HARD
+ # =============================================================================
+ # NOTES
+ # =============================================================================
+ # All criteria are HARD (instant fail). No SOFT criteria with severity accumulation.
+ # Properties must pass ALL hard criteria to proceed to scoring phase.
```

### Tests Required

#### Test 1: `test_default_kill_switches_count_8_not_9`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Verify `KillSwitchFilter()` has exactly 8 kill switches (not 9)
- Verify `NoNewBuildKillSwitch` not in default switches
- Verify all 8 switches are HARD (get_soft_criteria() returns empty list)

#### Test 2: `test_new_build_property_passes_default_filter`
**File:** `tests/unit/test_kill_switch_filter.py`

**Test coverage:**
- Property with year_built=2024 (new build)
- Passes all other HARD criteria
- Verify verdict=PASS (new build not rejected by defaults)

---

## Implementation Order

Execute in this dependency-aware sequence:

### Phase 1: Scoring System Updates (ARCH-05)
**Rationale:** Foundation for all other work. No dependencies.

1. Update `constants.py` scoring constants (MAX_POSSIBLE_SCORE, tier thresholds)
2. Update `constants.py` section weight constants (A=250, B=175, C=180)
3. Update `scoring_weights.yaml` (section weights, tier thresholds, defaults)
4. Update `scoring_weights.py` docstrings
5. Run tests: `pytest tests/unit/test_constants.py tests/unit/test_scoring_weights.py`

**Validation:** All scoring tests pass, assertion check passes, tier classification correct.

### Phase 2A: Add New Kill-Switch (ARCH-04)
**Rationale:** New criterion, no conflicts with existing code.

1. Create `MinSqftKillSwitch` class in `criteria.py`
2. Add to imports in `filter.py`
3. Add to default kill switches in `filter.py`
4. Update `constants.py` HARD_CRITERIA_NAMES
5. Update `buyer_criteria.yaml` hard_criteria
6. Run tests: `pytest tests/unit/test_kill_switch.py::test_min_sqft*`

**Validation:** Sqft kill-switch tests pass, default filter includes 9 switches (temporarily).

### Phase 2B: Update Existing Kill-Switches (ARCH-03, ARCH-02, ARCH-01)
**Rationale:** Modify existing criteria, potential conflicts if done concurrently.

**Execute in parallel (no dependencies):**

1. **ARCH-03 (LotSizeKillSwitch):**
   - Update `LotSizeKillSwitch` class (min=8000, no max, HARD)
   - Update default instantiation in `filter.py`
   - Update `constants.py` (remove from SOFT weights, add to HARD names)
   - Update `buyer_criteria.yaml`
   - Run tests: `pytest tests/unit/test_kill_switch.py::test_lot_size*`

2. **ARCH-02 (CitySewerKillSwitch):**
   - Add `is_hard` property to `CitySewerKillSwitch`
   - Update `constants.py` (remove from SOFT weights, add to HARD names)
   - Update `buyer_criteria.yaml`
   - Run tests: `pytest tests/unit/test_kill_switch.py::test_city_sewer*`

3. **ARCH-01 (MinGarageKillSwitch):**
   - Update `MinGarageKillSwitch` class (min=1, indoor_required=True, HARD)
   - Update default instantiation in `filter.py`
   - Update `constants.py` (remove from SOFT weights, add to HARD names)
   - Update `buyer_criteria.yaml`
   - Run tests: `pytest tests/unit/test_kill_switch.py::test_min_garage*`

**Validation:** All individual kill-switch tests pass.

### Phase 3: Cleanup (Remove NoNewBuildKillSwitch)
**Rationale:** Final cleanup, depends on all other kill-switches being correct.

1. Remove `NoNewBuildKillSwitch` from default kill switches in `filter.py`
2. Update docstring in `filter.py`
3. Update `constants.py` (empty SOFT_SEVERITY_WEIGHTS dicts)
4. Update `buyer_criteria.yaml` (remove soft_criteria section)
5. Run tests: `pytest tests/unit/test_kill_switch_filter.py`

**Validation:** Exactly 8 HARD kill-switches in defaults, all SOFT dicts empty.

### Phase 4: Integration Testing
**Rationale:** Verify complete system with all changes.

1. Run full test suite: `pytest tests/`
2. Integration test: `pytest tests/integration/test_tier_classification.py`
3. Manual validation: `python scripts/phx_home_analyzer.py --test`
4. Check console output for correct tier thresholds (484/363)
5. Check kill-switch verdicts all show HARD failures

**Validation:** All tests pass, no regressions, correct tier classification.

---

## Definition of Done Checklist

### Code Changes
- [ ] `constants.py`: MAX_POSSIBLE_SCORE=605, TIER_UNICORN_MIN=484, TIER_CONTENDER_MIN=363
- [ ] `constants.py`: Section totals A=250, B=175, C=180
- [ ] `constants.py`: Section constants match scoring_weights.py exactly
- [ ] `scoring_weights.yaml`: section_weights 250+175+180=605, tier_thresholds 484/363
- [ ] `scoring_weights.py`: Docstrings updated, TierThresholds values updated
- [ ] `criteria.py`: MinSqftKillSwitch class implemented (HARD, min=1800)
- [ ] `criteria.py`: LotSizeKillSwitch updated (HARD, min=8000, no max)
- [ ] `criteria.py`: CitySewerKillSwitch updated (HARD, is_hard=True)
- [ ] `criteria.py`: MinGarageKillSwitch updated (HARD, min=1, indoor_required=True)
- [ ] `filter.py`: Default kill switches list has 8 HARD criteria
- [ ] `filter.py`: NoNewBuildKillSwitch removed from defaults
- [ ] `filter.py`: Docstring lists all 8 HARD criteria
- [ ] `constants.py`: HARD_CRITERIA_NAMES has 8 entries (all kill-switch names)
- [ ] `constants.py`: SOFT_SEVERITY_WEIGHTS dicts are empty
- [ ] `buyer_criteria.yaml`: hard_criteria has 8 entries
- [ ] `buyer_criteria.yaml`: soft_criteria section removed

### Testing
- [ ] All unit tests pass: `pytest tests/unit/`
- [ ] All integration tests pass: `pytest tests/integration/`
- [ ] New tests added for 605-point scoring system
- [ ] New tests added for MinSqftKillSwitch
- [ ] Updated tests for LotSizeKillSwitch (HARD, min=8000)
- [ ] Updated tests for CitySewerKillSwitch (HARD)
- [ ] Updated tests for MinGarageKillSwitch (HARD, min=1, indoor)
- [ ] Test coverage >= 80% for modified files
- [ ] No test regressions (all existing tests still pass)

### Documentation
- [ ] All docstrings updated to reflect 605-point system
- [ ] All comments referencing 600 points changed to 605
- [ ] Kill-switch docstrings reflect HARD vs SOFT correctly
- [ ] `buyer_criteria.yaml` comments explain HARD-only system
- [ ] Section weight constants have correct comments (250/175/180)

### Validation
- [ ] Manual smoke test: Run analyzer on test properties
- [ ] Verify tier classification: Properties at 483 → Contender, 484 → Unicorn
- [ ] Verify kill-switch verdicts: All failures show "FAIL (instant)" not "WARNING"
- [ ] Verify severity scores: All properties show severity=0.0 (no SOFT criteria)
- [ ] Check console output formatting for 605-point system

### Quality Gates
- [ ] Linter passes: `ruff check .`
- [ ] Formatter passes: `ruff format --check .`
- [ ] Type checker passes: `mypy src/`
- [ ] No new security vulnerabilities: `pip-audit`

---

## Risk Assessment

### Potential Regressions

#### Risk 1: Tier Classification Changes
**Impact:** HIGH - Properties previously "Unicorn" (480-483) now "Contender"

**Mitigation:**
- Update all documentation referencing old thresholds
- Add migration note in CHANGELOG
- Test edge cases (scores 480, 483, 484, 360, 362, 363)
- Communicate threshold change to stakeholders

**Rollback:** Revert `constants.py` and `scoring_weights.yaml` tier thresholds

#### Risk 2: Kill-Switch False Positives
**Impact:** HIGH - Properties previously PASS now FAIL (SOFT → HARD)

**Affected properties:**
- Septic systems (was WARNING at severity 2.5, now FAIL)
- Lots 7000-8000 sqft (was PASS, now FAIL)
- 1-car garages (was WARNING at severity 1.5, now potentially FAIL if not indoor)

**Mitigation:**
- Before deployment: Export current property verdicts
- After deployment: Compare verdict changes
- Document expected verdict changes for transparency
- Test edge cases thoroughly

**Rollback:** Revert kill-switch changes, restore SOFT criteria

#### Risk 3: Missing indoor_garage Data
**Impact:** MEDIUM - Cannot verify indoor garage requirement for existing properties

**Current state:** `indoor_garage` field doesn't exist, will be `None` for all properties

**Mitigation:**
- Implementation assumes garage is indoor if `indoor_garage=None` and `garage_spaces >= 1`
- Document assumption in code comments
- Phase 2 image assessment can populate `indoor_garage` field
- For now, effectively checks `garage_spaces >= 1` (same as before but HARD)

**Rollback:** Set `indoor_required=False` in default instantiation

#### Risk 4: Scoring Section Weight Mismatches
**Impact:** MEDIUM - Individual criteria scores may not sum to section totals

**Example:** If `SchoolDistrictScorer` still uses old 50pt max but constant says 42pt

**Mitigation:**
- Verify all scoring strategies use constants from `config/constants.py`
- Add integration test that checks: sum of individual scores <= section total
- Manual review of all `strategies/*.py` files

**Rollback:** Revert `constants.py` section weights

#### Risk 5: YAML Config Parsing Errors
**Impact:** LOW - Malformed YAML after manual edits

**Mitigation:**
- Validate YAML syntax before committing: `python -c "import yaml; yaml.safe_load(open('config/scoring_weights.yaml'))"`
- Add YAML validation test
- Use YAML linter in CI

**Rollback:** Revert `scoring_weights.yaml` and `buyer_criteria.yaml`

### Breaking Changes

1. **Tier threshold change:** Code relying on exact threshold values (480/360) will break
2. **Kill-switch API change:** `LotSizeKillSwitch` signature changed (max_sqft now optional)
3. **Kill-switch API change:** `MinGarageKillSwitch` signature changed (added indoor_required)
4. **Verdict behavior change:** SOFT criteria removed, no more WARNING verdicts (only PASS/FAIL)

### Backward Compatibility

**Preserved:**
- `NoNewBuildKillSwitch` class still exists (can be used in custom filters)
- `LotSizeKillSwitch` still accepts `max_sqft` parameter (backward compat)
- `MinGarageKillSwitch` still accepts `min_spaces` parameter (backward compat)
- Property entity schema unchanged (no required fields added)

**Not preserved:**
- Default kill-switches changed (8 HARD criteria instead of 4 HARD + 4 SOFT)
- Tier thresholds changed (484/363 instead of 480/360)
- Severity accumulation removed from defaults (no SOFT criteria)

---

## Notes

### Decision Log

1. **605 vs 600 points:** Chose 605 as source of truth because `scoring_weights.py` dataclass already defines 605, and it's the active code implementation.

2. **Tier thresholds:** Calculated as 80% and 60% of 605 (484, 363) to maintain consistent percentile approach.

3. **All criteria HARD:** PRD specifies 7 must-have criteria with no severity accumulation, so HARD is correct classification.

4. **Lot size minimum 8000:** Research shows 7k-8k lots in Phoenix often cramped, 8k+ provides comfortable space. Removed 15k max because large lots common and acceptable in North Phoenix/Anthem.

5. **Garage indoor requirement:** Buyer profile needs attached garage (direct access), not carport. Min reduced from 2 to 1 but must be indoor.

6. **Assume indoor if unknown:** Reasonable default since most 1+ car listings are attached garages. Phase 2 can refine with image analysis.

7. **Remove NoNewBuildKillSwitch:** Not in PRD criteria list, likely added during early development. Keep class for backward compat but remove from defaults.

### Future Work

1. **Phase 2 enrichment:** Populate `indoor_garage` field via image analysis or listing text parsing ("attached garage", "direct access")

2. **Scoring strategy review:** Verify all strategies in `services/scoring/strategies/*.py` use updated constants

3. **Migration script:** Generate report showing properties with verdict changes (PASS→FAIL, Unicorn→Contender)

4. **Documentation update:** Update README, PRD, and skill files to reflect 605-point system and 8 HARD criteria

5. **Monitoring:** Track kill-switch failure rates after deployment to validate thresholds

### References

- **PRD:** `docs/PRD-2025-12.md` - Sections 2.2 (Kill-Switch Criteria), 4.2 (Scoring System)
- **Validation Report:** `docs/PRD-validation-report-2025-12-02.md` - ARCH action items
- **Scoring weights:** `src/phx_home_analysis/config/scoring_weights.py:1-394`
- **Kill-switch constants:** `src/phx_home_analysis/services/kill_switch/constants.py:1-89`
- **Filter orchestrator:** `src/phx_home_analysis/services/kill_switch/filter.py:1-350`
- **Buyer criteria config:** `config/buyer_criteria.yaml:1-74`

---

**End of Sprint 0 Story**

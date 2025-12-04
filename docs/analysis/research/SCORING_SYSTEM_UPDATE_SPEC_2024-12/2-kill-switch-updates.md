# 2. Kill-Switch Updates

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

# Configuration Module

The `config` module centralizes all configuration and constants for the PHX Home Analysis pipeline.

## Files

### `constants.py`
**Master constants file** containing all magic numbers and configuration values used throughout the system.

#### Structure
- Scoring thresholds (600-point system)
- Kill-switch severity weights and thresholds
- Confidence and quality metrics
- Arizona-specific rates and constants
- Image processing parameters
- Stealth browser extraction settings

#### Usage
```python
from phx_home_analysis.config.constants import (
    TIER_UNICORN_MIN,
    CONFIDENCE_HIGH_THRESHOLD,
    SEVERITY_FAIL_THRESHOLD,
    POOL_SERVICE_MONTHLY,
)

# Use constants directly
if score > TIER_UNICORN_MIN:
    tier = "Unicorn"

# Update one value in constants.py affects entire system
```

#### Key Constants by Category

**Scoring System (600 points)**
- `MAX_POSSIBLE_SCORE`: 600
- `TIER_UNICORN_MIN`: 480 (>80%)
- `TIER_CONTENDER_MIN`: 360 (60-80%)
- `TIER_PASS_MAX`: 359 (<60%)

**Kill-Switch Severity**
- `SEVERITY_FAIL_THRESHOLD`: 3.0
- `SEVERITY_WARNING_THRESHOLD`: 1.5
- `SEVERITY_WEIGHT_SEWER`: 2.5
- `SEVERITY_WEIGHT_YEAR_BUILT`: 2.0
- `SEVERITY_WEIGHT_GARAGE`: 1.5
- `SEVERITY_WEIGHT_LOT_SIZE`: 1.0

**Confidence Thresholds**
- `CONFIDENCE_HIGH_THRESHOLD`: 0.80
- `QUALITY_GATE_THRESHOLD`: 0.95
- `DATA_CONFIDENCE_ASSESSOR_API`: 0.95
- `DATA_CONFIDENCE_WEB_SCRAPE`: 0.85
- `DATA_CONFIDENCE_MANUAL`: 0.85

**Arizona Rates** (all monthly, 2025)
- `MORTGAGE_RATE_30YR`: 0.0699 (6.99%)
- `INSURANCE_RATE_PER_1K`: 6.50 (annual per $1k value)
- `PROPERTY_TAX_RATE`: 0.0066 (~0.66%)
- `UTILITY_RATE_PER_SQFT`: 0.08 ($/sqft/month)
- `POOL_SERVICE_MONTHLY`: 125.00
- `POOL_ENERGY_MONTHLY`: 75.00
- `MAINTENANCE_RESERVE_ANNUAL_RATE`: 0.01 (1%)

### `settings.py`
**Application-level configuration** for paths, buyer profile, and extraction settings.

#### Key Classes

**ProjectPaths**
- Base directory configuration
- Input/output file paths
- Environment variable support

**BuyerProfile**
- Financial criteria (max payment, down payment)
- Hard kill-switch criteria (beds, baths, garage, lot size)
- Deal breakers (HOA, sewer, year built)

**ArizonaContext**
- Arizona-specific factors
- Sun orientation impact
- Pool and HVAC considerations

**StealthExtractionConfig**
- Proxy settings
- Browser viewport dimensions
- Human behavior simulation delays
- CAPTCHA handling parameters

**ImageExtractionConfig**
- Image storage paths
- Processing dimensions
- Deduplication parameters
- Rate limiting and retry logic

**AppConfig**
- Aggregates all configuration components
- Single entry point for full system config

#### Usage
```python
from phx_home_analysis.config.settings import AppConfig

# Load default configuration
config = AppConfig.default()

# Access buyer profile
print(config.buyer.max_monthly_payment)  # 4000
print(config.buyer.min_bedrooms)         # 4

# Access file paths
input_file = config.paths.input_csv
output_file = config.paths.output_csv
```

### `scoring_weights.py`
**Scoring system configuration** (600-point breakdown).

#### Key Classes

**ScoringWeights**
Defines individual point allocations for each scoring category:
- Section A: Location & Environment (230 pts)
- Section B: Lot & Systems (180 pts)
- Section C: Interior & Features (190 pts)

**TierThresholds**
Defines tier classification boundaries:
- `unicorn_min`: 480 (exceptional)
- `contender_min`: 360 (strong)
- `pass_max`: 359 (baseline)

#### Usage
```python
from phx_home_analysis.config.scoring_weights import ScoringWeights, TierThresholds

weights = ScoringWeights()
print(weights.total_possible_score)  # 600
print(weights.section_a_max)          # 230
print(weights.section_b_max)          # 180
print(weights.section_c_max)          # 190

thresholds = TierThresholds()
tier = thresholds.classify(545)  # "Unicorn"
```

### `__init__.py`
**Package initialization** - exposes key classes for convenient imports.

## How Constants Flow Through System

```
config/constants.py (single source of truth)
        ↓
[kill_switch/constants.py]  → KillSwitchFilter
[ai_enrichment/models.py]   → FieldInference
[confidence_scorer.py]      → ConfidenceScorer
[cost_estimation/rates.py]  → CostEstimator
        ↓
[domain/entities.py]        → Property objects
[services/*]                → Analysis pipeline
        ↓
Pipeline output with consistent scoring/filtering
```

## Common Changes & Where to Make Them

### Update Scoring Thresholds
**File:** `config/constants.py`
**Constants:** `TIER_UNICORN_MIN`, `TIER_CONTENDER_MIN`
**Affected:** TierClassifier, deal sheets, reports

### Update Kill-Switch Severity
**File:** `config/constants.py`
**Constants:** `SEVERITY_FAIL_THRESHOLD`, `SEVERITY_WARNING_THRESHOLD`, `SEVERITY_WEIGHT_*`
**Affected:** KillSwitchFilter, all kill-switch evaluations

### Update Arizona Rates
**File:** `config/constants.py`
**Constants:** `*_RATE_*`, `*_MONTHLY`, `*_ANNUAL`
**Affected:** CostEstimator, monthly payment calculations

### Update Buyer Profile
**File:** `config/settings.py`
**Class:** `BuyerProfile`
**Affected:** Kill-switch hard criteria, property filtering

### Update Confidence Thresholds
**File:** `config/constants.py`
**Constants:** `CONFIDENCE_HIGH_THRESHOLD`, `DATA_CONFIDENCE_*`, `FIELD_CONFIDENCE_*`
**Affected:** FieldInference, quality metrics, CI/CD gates

## Best Practices

### 1. Use Constants, Never Magic Numbers
❌ **Bad:**
```python
if score > 480:  # What's this magic number?
    return "Unicorn"
```

✅ **Good:**
```python
from phx_home_analysis.config.constants import TIER_UNICORN_MIN

if score > TIER_UNICORN_MIN:
    return "Unicorn"
```

### 2. Document Data Sources
Every constant should include:
```python
# Source: [Where does this value come from?]
# Rationale: [Why is this the right value?]
# Last updated: [When was this validated?]
```

### 3. Group Related Constants
Don't scatter related values across files:
```python
# Good: All pool costs together
POOL_SERVICE_MONTHLY = 125.0
POOL_ENERGY_MONTHLY = 75.0
POOL_TOTAL_MONTHLY = POOL_SERVICE_MONTHLY + POOL_ENERGY_MONTHLY
```

### 4. Use Final for Immutability
```python
TIER_UNICORN_MIN: Final[int] = 480  # Can't be reassigned
```

### 5. Test Configuration Changes
Before updating constants:
1. Verify new value with market data / business rules
2. Run full test suite
3. Update documentation
4. Document change rationale

## Adding New Constants

When adding new configuration values:

1. **Determine location:** Constants file or Settings class?
   - Magic numbers → `constants.py`
   - Application settings → `settings.py`
   - Scoring weights → `scoring_weights.py`

2. **Document thoroughly:**
   ```python
   # Data source and rationale
   # Validation/testing performed
   # Related constants
   CONSTANT_NAME: Final[type] = value  # Comment explaining use
   ```

3. **Add to type hints:** If adding to dataclass, update hints

4. **Update related files:** If new constant affects existing logic

5. **Add to this README:** In the appropriate section

## Validation & Testing

The constants module includes built-in validation:

```python
# Ensures 600-point system remains consistent
assert SCORE_SECTION_A_TOTAL + SCORE_SECTION_B_TOTAL + SCORE_SECTION_C_TOTAL == MAX_POSSIBLE_SCORE
```

This assertion runs when the module is imported, catching any accidental inconsistencies.

## References

- **CLAUDE.md**: Project overview
- **CONSTANTS_MIGRATION.md**: Implementation details
- **../domain/entities.py**: How constants are used in entities
- **../services/**: How constants are consumed throughout system

## Questions?

When in doubt:
1. Search for the constant in `constants.py`
2. Read the documentation comment
3. Follow the import chain to see how it's used
4. Check git history for when/why it was set to that value

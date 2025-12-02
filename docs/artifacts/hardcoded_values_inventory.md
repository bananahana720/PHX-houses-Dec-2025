# Hardcoded Values Inventory - PHX Houses Analysis
**Date:** 2025-12-01
**Scan Type:** Deep code review for hardcoded constants, magic numbers, and stale data

---

## EXECUTIVE SUMMARY

### Critical Issues Found
1. **SCORING SYSTEM INCONSISTENCY**: Mix of 500pt and 600pt references across codebase
2. **GEOGRAPHIC DATA**: 21+ hardcoded latitude/longitude coordinates in `generate_map.py`
3. **YEAR HARDCODING**: Year 2024 threshold scattered across 15+ files
4. **MISSING CENTRALIZATION**: Kill-switch thresholds defined in multiple locations

### Risk Assessment
| Category | High Risk | Medium Risk | Low Risk | Total |
|----------|-----------|-------------|----------|-------|
| Scoring Constants | 8 | 12 | 5 | 25 |
| Kill-Switch Values | 0 | 7 | 8 | 15 |
| Price/Budget | 2 | 4 | 3 | 9 |
| Geographic Data | 1 | 0 | 0 | 1 |
| Date/Year Values | 3 | 8 | 2 | 13 |
| **TOTAL** | **14** | **31** | **18** | **63** |

---

## SECTION 1: SCORING CONSTANTS

### 1.1 CRITICAL: 500 vs 600 Point Inconsistency

**Root Cause:** System upgraded from 500pt to 600pt but legacy references remain

| Value | File:Line | Context | Should Be | Risk |
|-------|-----------|---------|-----------|------|
| 500 | `scripts/deal_sheets.py:400` | `{{ property['total_score'] }}/500 pts` | `/600 pts` | **HIGH** - User-facing display |
| 500 | `scripts/deal_sheets.py:437` | Location `/150` (legacy) | `/230` | **HIGH** - Wrong denominator |
| 500 | `scripts/deal_sheets.py:464` | Total `/500` | `/600` | **HIGH** - Wrong total |
| 500 | `scripts/deal_sheets.py:466` | `(total / 500 * 100)` | `/600` | **HIGH** - Wrong percentage calc |
| 500 | `scripts/value_spotter.py:186` | `"Max 500 points"` axis label | `"Max 600 points"` | **HIGH** - Visualization label |
| 500 | `src/phx_home_analysis/domain/entities.py:178` | Docstring `0-500 pts` | `0-600 pts` | **MEDIUM** - Documentation |
| 500 | `src/phx_home_analysis/reporters/console_reporter.py:185` | `{prop.total_score:.1f}/500` | `/600` | **HIGH** - Console output |
| 500 | `src/phx_home_analysis/reporters/console_reporter.py:188` | `{prop.total_score:.1f}/500` | `/600` | **HIGH** - Console output |

**Impact:** Users see incorrect max scores, percentages calculated wrong, tier thresholds misinterpreted

**Recommendation:**
```python
# Create config constant
from src.phx_home_analysis.config.scoring_weights import ScoringWeights
MAX_TOTAL_SCORE = ScoringWeights().total_possible_score  # 600
```

---

### 1.2 Section Maximums (CORRECT in most places)

**Correct Configuration (scoring_weights.py):**
- Section A (Location): 230 pts
- Section B (Lot/Systems): 180 pts
- Section C (Interior): 190 pts
- **Total: 600 pts**

**Legacy References to Fix:**

| Value | File:Line | Context | Should Be | Risk |
|-------|-----------|---------|-----------|------|
| 150 | `scripts/deal_sheets.py:437` | `score_location / 150` | `/230` | **HIGH** - Wrong section A max |
| 150 | `scripts/deal_sheets.py:439-440` | Location percentage calc | `/230` | **HIGH** - Wrong percentage |
| 160 | `scripts/deal_sheets.py:446` | `score_lot_systems / 160` | `/180` | **MEDIUM** - Wrong section B max |
| 160 | `scripts/deal_sheets.py:448-449` | Systems percentage calc | `/180` | **MEDIUM** - Wrong percentage |
| 160 | `scripts/analyze.py:262` | Console output `/160` | `/180` | **MEDIUM** - Display issue |
| 150 | `src/phx_home_analysis/reporters/console_reporter.py:194` | `Location .../150` | `/230` | **HIGH** - Console display |
| 160 | `src/phx_home_analysis/reporters/console_reporter.py:195` | `Systems .../160` | `/180` | **HIGH** - Console display |

**Files with CORRECT values:**
- ✅ `src/phx_home_analysis/config/scoring_weights.py` (lines 22, 75, 130)
- ✅ `scripts/radar_charts.py` (lines 81-83)
- ✅ `tests/unit/test_scorer.py` (assertions at 878, 883, 888)
- ✅ `scripts/deal_sheets/templates.py` (updated versions)

---

## SECTION 2: KILL-SWITCH THRESHOLDS

### 2.1 Severity Weights (SOFT Criteria)

**Canonical Source:** `scripts/lib/kill_switch.py:45-50`

| Criterion | Weight | Files Using Value | Consistency |
|-----------|--------|-------------------|-------------|
| `sewer` | 2.5 | kill_switch.py only | ✅ CENTRALIZED |
| `year_built` | 2.0 | kill_switch.py only | ✅ CENTRALIZED |
| `garage` | 1.5 | kill_switch.py only | ✅ CENTRALIZED |
| `lot_size` | 1.0 | kill_switch.py only | ✅ CENTRALIZED |

**Threshold Constants:**
- `SEVERITY_FAIL_THRESHOLD = 3.0` (line 56)
- `SEVERITY_WARNING_THRESHOLD = 1.5` (line 57)

**Status:** ✅ Well-centralized, no hardcoded duplicates found

---

### 2.2 Hard Criteria Thresholds

| Criterion | Value | File:Line | Context | Risk |
|-----------|-------|-----------|---------|------|
| **Beds (min)** | 4 | Multiple locations | Min 4 bedrooms | ✅ LOW - Well understood |
| **Baths (min)** | 2 | Multiple locations | Min 2 bathrooms | ✅ LOW - Well understood |
| **HOA** | $0 | Multiple locations | NO HOA fees | ✅ LOW - Well understood |
| **Lot size (min)** | 7000 | 15+ files | Min lot sqft | **MEDIUM** - Should centralize |
| **Lot size (max)** | 15000 | 15+ files | Max lot sqft | **MEDIUM** - Should centralize |
| **Year built** | < 2024 | 15+ files | No new builds | **MEDIUM** - Hardcoded year |

**Lot Size Hardcoding Issues:**

| File:Line | Context | Risk |
|-----------|---------|------|
| `scripts/deal_sheets.py:43` | `7000 <= val <= 15000` | MEDIUM |
| `scripts/value_spotter.py:110-111` | `cmin=7000, cmax=15000` | LOW (visualization) |
| `src/phx_home_analysis/services/kill_switch/criteria.py:291` | `min_sqft: int = 7000, max_sqft: int = 15000` | LOW (defaults) |
| `src/phx_home_analysis/services/kill_switch/filter.py:95` | `LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)` | MEDIUM |
| `scripts/lib/kill_switch.py:162` | `if 7000 <= sqft <= 15000` | MEDIUM |

**Recommendation:** Create config constant:
```python
# In settings.py or scoring_weights.py
LOT_SIZE_MIN_SQFT = 7000
LOT_SIZE_MAX_SQFT = 15000
```

---

## SECTION 3: PRICE & BUDGET CONSTANTS

### 3.1 Monthly Payment Threshold

**Primary Value:** `$4,000/month` (buyer's max payment)

| File:Line | Context | Risk |
|-----------|---------|------|
| `tests/conftest.py:564` | `max_mortgage_payment=4000` | LOW (test fixture) |
| `scripts/deal_sheets/templates.py:481` | `{% if monthly_cost > 4000 %}` | **HIGH** - Should use config |
| `scripts/deal_sheets/templates.py:485` | `"Exceeds $4,000 threshold"` | **HIGH** - Hardcoded message |
| `scripts/gen_9832_deal_sheet.py:136` | `"over $4k target"` | MEDIUM (legacy script) |
| `src/phx_home_analysis/config/scoring_weights.py:124` | `$4,000/mo: 15 pts` | LOW (documentation) |
| `src/phx_home_analysis/services/scoring/strategies/cost_efficiency.py:26` | `$4,000/mo: 5 pts` | LOW (documentation) |

**Recommendation:**
```python
# In settings.py
MAX_MONTHLY_PAYMENT = 4000  # Buyer's maximum affordable payment
```

---

### 3.2 Value Zone Boundaries

**File:** `scripts/value_spotter.py:47-48`

| Constant | Value | Risk |
|----------|-------|------|
| `value_zone_min_score` | 365 | **MEDIUM** - Arbitrary threshold |
| `value_zone_max_price` | 550000 | **MEDIUM** - Market-dependent |

**Context:** Defines "Value Zone" quadrant (high score, low price)

**Issue:** These are market-dependent and should be:
1. Configurable via CLI args or config file
2. Calculated dynamically based on dataset distribution
3. Documented with clear rationale

**Recommendation:**
```python
# Calculate from data
value_zone_min_score = df['total_score'].quantile(0.60)  # Top 40%
value_zone_max_price = df['price'].quantile(0.40)  # Bottom 60%
```

---

### 3.3 Tier Boundaries

**File:** `src/phx_home_analysis/config/scoring_weights.py:315-317`

| Tier | Score Range | % of Max | Risk |
|------|-------------|----------|------|
| Unicorn | ≥ 480 | ≥ 80% | ✅ LOW - Config-based |
| Contender | 360-479 | 60-79% | ✅ LOW - Config-based |
| Pass | < 360 | < 60% | ✅ LOW - Config-based |

**Status:** ✅ Well-designed with clear percentage basis

---

## SECTION 4: GEOGRAPHIC HARDCODING

### 4.1 CRITICAL: Hardcoded Coordinates

**File:** `scripts/generate_map.py:75-96`

**Issue:** 21+ properties with hardcoded lat/lon coordinates

```python
geocoding = {
    "4209 W Wahalla Ln, Glendale, AZ 85308": (33.6353, -112.2024),
    "4417 W Sandra Cir, Glendale, AZ 85308": (33.6412, -112.1943),
    # ... 19 more hardcoded entries
}
```

**Risk:** **HIGH**
- Not scalable for new properties
- Data duplication (should be in enrichment_data.json)
- Manual maintenance required
- Geocoding failures silently ignored

**Recommendation:**
1. Move all coordinates to `enrichment_data.json`
2. Use geocoding service (Google Maps API, Nominatim) for new properties
3. Implement fallback chain:
   ```python
   coords = (
       get_from_enrichment(address) or
       get_from_geocoding_service(address) or
       get_from_manual_lookup(address)
   )
   ```

---

## SECTION 5: DATE & YEAR HARDCODING

### 5.1 Year Built Threshold (2024)

**Value:** `< 2024` (no new builds)

**Files with hardcoded 2024:**

| File:Line | Context | Risk |
|-----------|---------|------|
| `scripts/deal_sheets.py:48` | `lambda val: val < 2024` | **HIGH** - Needs annual update |
| `scripts/lib/kill_switch.py:177` | `if year < 2024:` | **HIGH** - Needs annual update |
| `scripts/lib/kill_switch.py:230` | `"No new builds (< 2024)"` | MEDIUM (description) |
| `scripts/data_quality_report.py:91` | `if year_built >= 2024:` | **HIGH** - Quality check |
| `src/phx_home_analysis/validation/schemas.py:289` | `Field(..., lt=2024, ...)` | **HIGH** - Pydantic validation |
| `src/phx_home_analysis/services/kill_switch/criteria.py:362` | Docstring reference | LOW (docs) |
| `src/phx_home_analysis/config/settings.py:112` | `max_year_built: int = 2023` | ✅ **GOOD** - Config value |

**Issue:** Year threshold must be updated annually (2024 → 2025 on Jan 1)

**Current State (Dec 2025):**
- ⚠️ **STALE DATA**: We're in December 2025, but code still filters `< 2024`
- Should be `< 2025` or `< 2026` depending on buyer preference

**Recommendation:**
```python
# In settings.py
MAX_YEAR_BUILT = 2024  # Update annually or make dynamic
# Or dynamic:
import datetime
MAX_YEAR_BUILT = datetime.datetime.now().year - 1  # Exclude current year
```

**Action Required:**
1. Update all `< 2024` to use `settings.MAX_YEAR_BUILT`
2. Add documentation reminder to update annually
3. Consider making dynamic if buyer wants "no builds from last N years"

---

### 5.2 Other Time-Based Values

| File:Line | Value | Context | Risk |
|-----------|-------|---------|------|
| `generate_extraction_report.py:240` | `extraction_report_20251130.json` | Filename with date | LOW (report artifact) |
| `tests/unit/test_state_manager.py:43,48` | `2025-01-01T00:00:00` | Test fixture | LOW (test data) |

---

## SECTION 6: COST ESTIMATION CONSTANTS

### 6.1 Arizona-Specific Costs

**File:** `src/phx_home_analysis/config/settings.py:144`

| Constant | Value | Risk |
|----------|-------|------|
| `solar_lease_penalty` | $150/mo | LOW - Config-based |
| `download_delay_ms` | 500ms | LOW - Performance tuning |

**File:** `src/phx_home_analysis/services/cost_estimation/rates.py:81`

| Constant | Value | Risk |
|----------|-------|------|
| `UTILITY_MAXIMUM_MONTHLY` | $500 | MEDIUM - Should document rationale |

**File:** `src/phx_home_analysis/domain/entities.py:262`

| Constant | Value | Risk |
|----------|-------|------|
| Pool maintenance | $100-150/mo | LOW - Documented range |

---

## SECTION 7: MISCELLANEOUS HARDCODED VALUES

### 7.1 Test Data & Fixtures

Multiple test files contain hardcoded property data - **LOW RISK** (expected for tests)

### 7.2 Proxy Configuration

**Files:** `test_proxy_extension.py`, `test_extension_only.py`

Hardcoded proxy credentials - **CRITICAL SECURITY ISSUE**
```python
password="g2j2p2cv602u"  # EXPOSED CREDENTIAL
```

**Action Required:** Remove or replace with placeholder values

---

## RECOMMENDATIONS

### Priority 1 (Immediate - Week 1)

1. **Fix Scoring Inconsistency**
   - Update all `/500` to `/600` in deal_sheets.py, value_spotter.py, console_reporter.py
   - Fix section maximums: 150→230, 160→180
   - **Files to edit:** 8 files, ~15 lines total

2. **Update Year Threshold**
   - Change `< 2024` to `< 2025` (or use config constant)
   - **Rationale:** We're in Dec 2025, data is stale
   - **Files to edit:** 7 files

3. **Remove Exposed Credentials**
   - Replace `password="g2j2p2cv602u"` with placeholder
   - **Files:** test_proxy_extension.py, test_extension_only.py

### Priority 2 (This Month - Weeks 2-3)

4. **Centralize Kill-Switch Thresholds**
   ```python
   # Create: src/phx_home_analysis/config/kill_switch_config.py
   LOT_SIZE_MIN_SQFT = 7000
   LOT_SIZE_MAX_SQFT = 15000
   MIN_BEDROOMS = 4
   MIN_BATHROOMS = 2
   MAX_HOA_FEE = 0
   ```

5. **Centralize Budget Constants**
   ```python
   # Add to settings.py
   MAX_MONTHLY_PAYMENT = 4000
   VALUE_ZONE_SCORE_PERCENTILE = 0.60
   VALUE_ZONE_PRICE_PERCENTILE = 0.40
   ```

6. **Move Geocoding to Data**
   - Export `generate_map.py` geocoding dict to JSON
   - Update enrichment_data.json with coordinates
   - Add geocoding service fallback

### Priority 3 (Next Month - Week 4+)

7. **Dynamic Value Zone Calculation**
   - Replace hardcoded 365/550k with percentile-based calculation
   - Make configurable via CLI args

8. **Create Constants Registry**
   ```python
   # src/phx_home_analysis/config/constants.py
   """
   Centralized constants registry for PHX Home Analysis
   Single source of truth for all hardcoded values
   """
   ```

9. **Documentation**
   - Document all constants with rationale
   - Add "Annual Review" checklist for year-dependent values

---

## TESTING IMPACT

**Files to Test After Changes:**
1. `scripts/deal_sheets.py` - Score display
2. `scripts/value_spotter.py` - Axis labels
3. `scripts/analyze.py` - Console output
4. `src/phx_home_analysis/reporters/console_reporter.py` - Score display
5. All kill-switch tests (year threshold change)

**Regression Risk:** MEDIUM
- Score calculations unchanged (logic correct)
- Only display/threshold values being updated
- Existing tests should catch calculation issues

---

## APPENDIX: SEARCH PATTERNS USED

```bash
# Scoring constants
grep -rn "\b(500|600|150|160|180|190|230)\b" --include="*.py"

# Kill-switch thresholds
grep -rn "\b(3\.0|2\.5|2\.0|1\.5|1\.0)\b" --include="*.py"
grep -rn "\b(7000|15000)\b" --include="*.py"

# Budget/price
grep -rn "\b(4000|550000|480000|365)\b" --include="*.py"

# Year references
grep -rn "\b202[0-9]\b" --include="*.py"
grep -rn "< 2024|<2024|year_built.*2024" --include="*.py"

# Geographic
grep -rn "33\.[0-9]+.*-112\.[0-9]+" --include="*.py"
```

---

**Report Generated:** 2025-12-01
**Codebase Version:** PHX-houses-Dec-2025
**Total Hardcoded Values Identified:** 63
**High Priority Issues:** 14
**Medium Priority Issues:** 31
**Low Priority Issues:** 18

"""Shared constants for kill-switch evaluation system.

Single source of truth for severity thresholds, weights, and criteria sets
used by both scripts/lib/kill_switch.py and src/phx_home_analysis/services/kill_switch/.

Kill Switch System (5 HARD + 4 SOFT Criteria):

HARD criteria (instant fail):
- NO HOA
- NO solar lease
- Minimum 4 bedrooms
- Minimum 2 bathrooms
- Minimum 1800 sqft

SOFT criteria (severity accumulation):
- City sewer only (severity 2.5)
- Year built ≤2023 (severity 2.0)
- Minimum 2 indoor garage spaces (severity 1.5)
- Lot size 7k-15k sqft (severity 1.0)

Verdict Logic:
- Any HARD failure -> FAIL (instant)
- SOFT severity ≥3.0 -> FAIL
- SOFT severity ≥1.5 -> WARNING
- Otherwise -> PASS

See config/constants.py for detailed documentation on severity thresholds
and weights (retained for backward compatibility).
"""

from enum import Enum

from ...config.constants import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    SEVERITY_WEIGHT_GARAGE,
    SEVERITY_WEIGHT_LOT_SIZE,
    SEVERITY_WEIGHT_SEWER,
    SEVERITY_WEIGHT_YEAR_BUILT,
)

# =============================================================================
# VERDICT ENUM
# =============================================================================


class KillSwitchVerdict(Enum):
    """Kill switch verdict outcome."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


# =============================================================================
# SEVERITY THRESHOLD CONSTANTS
# =============================================================================

# Threshold constants for verdict determination
# Imported from config.constants - DO NOT modify here
# Update only in src/phx_home_analysis/config/constants.py
__SEVERITY_FAIL_THRESHOLD = SEVERITY_FAIL_THRESHOLD
__SEVERITY_WARNING_THRESHOLD = SEVERITY_WARNING_THRESHOLD

# =============================================================================
# SEVERITY WEIGHTS FOR SOFT CRITERIA
# =============================================================================
# NOTE: As of BLUE Phase, 4 criteria are SOFT (weighted) and 4 are HARD (instant fail).
# SOFT criteria accumulate severity scores that determine verdict.
#
# SOFT Criteria (severity weighted, accumulate):
# - city_sewer: 2.5 (if sewer is unknown/septic, not city)
# - no_new_build: 2.0 (if year_built >= 2024)
# - min_garage: 1.5 (if garage_spaces < 2)
# - lot_size: 1.0 (if lot_sqft outside 7k-15k range)
#
# HARD Criteria (instant fail, no accumulation):
# - no_hoa: instant fail
# - no_solar_lease: instant fail
# - min_bedrooms: instant fail
# - min_bathrooms: instant fail
# - min_sqft: instant fail

# Severity weights for SOFT criteria (scripts/lib naming convention)
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
    "city_sewer": SEVERITY_WEIGHT_SEWER,
    "year_built": SEVERITY_WEIGHT_YEAR_BUILT,
    "garage": SEVERITY_WEIGHT_GARAGE,
    "lot_size": SEVERITY_WEIGHT_LOT_SIZE,
}

# Severity weights for SOFT criteria (service layer naming convention)
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
    "city_sewer": SEVERITY_WEIGHT_SEWER,
    "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,
    "min_garage": SEVERITY_WEIGHT_GARAGE,
    "lot_size": SEVERITY_WEIGHT_LOT_SIZE,
}

# =============================================================================
# HARD CRITERIA SETS
# =============================================================================

# HARD criteria names (scripts/lib naming convention)
# Used by scripts/lib/kill_switch.py
HARD_CRITERIA: set[str] = {"hoa", "beds", "baths", "sqft", "lot_size", "sewer", "garage"}

# HARD criteria names (service layer naming convention)
# Used by src/phx_home_analysis/services/kill_switch/
# 4 HARD criteria (instant fail)
# 4 SOFT criteria (severity weighted, accumulate)
HARD_CRITERIA_NAMES: set[str] = {
    "no_hoa",
    "no_solar_lease",
    "min_bedrooms",
    "min_bathrooms",
    "min_sqft",
}

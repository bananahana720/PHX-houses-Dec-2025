"""Shared constants for kill-switch evaluation system.

Single source of truth for severity thresholds, weights, and criteria sets
used by both scripts/lib/kill_switch.py and src/phx_home_analysis/services/kill_switch/.

Kill Switch System (Weighted Severity Threshold):
- HARD criteria (instant fail): beds < 4, baths < 2, HOA > $0
- SOFT criteria (severity weighted): sewer, garage, lot_size, year_built

Verdict Logic:
- Any HARD failure -> FAIL (instant, severity N/A)
- severity >= SEVERITY_FAIL_THRESHOLD -> FAIL (threshold exceeded)
- SEVERITY_WARNING_THRESHOLD <= severity < SEVERITY_FAIL_THRESHOLD -> WARNING
- severity < SEVERITY_WARNING_THRESHOLD -> PASS

See config/constants.py for detailed documentation on severity thresholds
and weights.
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

# Severity weights for SOFT criteria (scripts/lib naming convention)
# Used by scripts/lib/kill_switch.py
# All weights defined in config.constants.py
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
    "sewer": SEVERITY_WEIGHT_SEWER,        # Septic risk - infrastructure concern
    "garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "lot_size": SEVERITY_WEIGHT_LOT_SIZE,  # Minor preference
    "year_built": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# Severity weights for SOFT criteria (service layer naming convention)
# Used by src/phx_home_analysis/services/kill_switch/
# All weights defined in config.constants.py
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {
    "city_sewer": SEVERITY_WEIGHT_SEWER,       # Septic risk - infrastructure concern
    "min_garage": SEVERITY_WEIGHT_GARAGE,      # Convenience factor
    "lot_size": SEVERITY_WEIGHT_LOT_SIZE,      # Minor preference
    "no_new_build": SEVERITY_WEIGHT_YEAR_BUILT,  # New build avoidance
}

# =============================================================================
# HARD CRITERIA SETS
# =============================================================================

# HARD criteria names (scripts/lib naming convention)
# Used by scripts/lib/kill_switch.py
HARD_CRITERIA: set[str] = {"hoa", "beds", "baths"}

# HARD criteria names (service layer naming convention)
# Used by src/phx_home_analysis/services/kill_switch/
HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms"}

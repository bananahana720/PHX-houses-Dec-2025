"""Shared constants for kill-switch evaluation system.

Single source of truth for severity thresholds, weights, and criteria sets
used by both scripts/lib/kill_switch.py and src/phx_home_analysis/services/kill_switch/.

Kill Switch System (All HARD Criteria):
All 8 default criteria are HARD (instant fail). No SOFT criteria in defaults.

HARD criteria:
- NO HOA
- NO solar lease
- Minimum 4 bedrooms
- Minimum 2 bathrooms
- Minimum 1800 sqft
- Lot size > 8000 sqft
- City sewer only
- Minimum 1 indoor garage

Verdict Logic:
- Any HARD failure -> FAIL (instant)
- All pass -> PASS

See config/constants.py for detailed documentation on severity thresholds
and weights (retained for backward compatibility).
"""

from enum import Enum

from ...config.constants import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
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
# SEVERITY WEIGHTS FOR SOFT CRITERIA (DEPRECATED)
# =============================================================================
# NOTE: As of Sprint 0, all default criteria are HARD (instant fail).
# These dictionaries are retained for backward compatibility but are empty
# since no SOFT criteria exist in the default configuration.

# Severity weights for SOFT criteria (scripts/lib naming convention)
# EMPTY - all criteria are now HARD
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {}

# Severity weights for SOFT criteria (service layer naming convention)
# EMPTY - all criteria are now HARD
SOFT_SEVERITY_WEIGHTS_SERVICE: dict[str, float] = {}

# =============================================================================
# HARD CRITERIA SETS
# =============================================================================

# HARD criteria names (scripts/lib naming convention)
# Used by scripts/lib/kill_switch.py
HARD_CRITERIA: set[str] = {"hoa", "beds", "baths", "sqft", "lot_size", "sewer", "garage"}

# HARD criteria names (service layer naming convention)
# Used by src/phx_home_analysis/services/kill_switch/
# All 8 default kill switches are HARD
HARD_CRITERIA_NAMES: set[str] = {
    "no_hoa",
    "no_solar_lease",
    "min_bedrooms",
    "min_bathrooms",
    "min_sqft",
    "lot_size",
    "city_sewer",
    "min_garage",
}

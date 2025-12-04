"""Kill Switch Filter service for PHX Home Analysis.

This module provides automated filtering for property listings.

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

Usage:
    from phx_home_analysis.services.kill_switch import KillSwitchFilter, KillSwitchVerdict

    filter_service = KillSwitchFilter()
    passed, failed = filter_service.filter_properties(properties)

    # Or with severity-aware evaluation
    verdict, severity, failures = filter_service.evaluate_with_severity(property)
"""

from .base import (
    HARD_CRITERIA_NAMES,
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    SOFT_SEVERITY_WEIGHTS,
    KillSwitch,
    KillSwitchVerdict,
)
from .criteria import (
    CitySewerKillSwitch,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
    MinSqftKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)
from .explanation import CriterionResult, VerdictExplainer, VerdictExplanation
from .filter import KillSwitchFilter

__all__ = [
    # Base types and constants
    "KillSwitch",
    "KillSwitchVerdict",
    "SOFT_SEVERITY_WEIGHTS",
    "HARD_CRITERIA_NAMES",
    "SEVERITY_FAIL_THRESHOLD",
    "SEVERITY_WARNING_THRESHOLD",
    # Filter orchestrator
    "KillSwitchFilter",
    # Concrete kill switch implementations
    "NoHoaKillSwitch",
    "CitySewerKillSwitch",
    "MinGarageKillSwitch",
    "MinBedroomsKillSwitch",
    "MinBathroomsKillSwitch",
    "MinSqftKillSwitch",
    "LotSizeKillSwitch",
    "NoNewBuildKillSwitch",
    "NoSolarLeaseKillSwitch",
    # Explanation system
    "VerdictExplainer",
    "VerdictExplanation",
    "CriterionResult",
]

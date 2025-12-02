"""Kill Switch Filter service for PHX Home Analysis.

This module provides automated filtering for property listings using a weighted
severity threshold system.

Kill Switch System (Weighted Severity Threshold):
- HARD criteria (instant fail): beds < 4, baths < 2, HOA > $0
- SOFT criteria (severity weighted): sewer, garage, lot_size, year_built

Verdict Logic:
- Any HARD failure -> FAIL (instant, severity N/A)
- severity >= 3.0 -> FAIL (threshold exceeded)
- 1.5 <= severity < 3.0 -> WARNING (approaching limit)
- severity < 1.5 -> PASS

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
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
)
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
    "LotSizeKillSwitch",
    "NoNewBuildKillSwitch",
]

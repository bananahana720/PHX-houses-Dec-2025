"""Shared utilities for PHX Home Analysis scripts.

This package provides consolidated implementations of common functionality
used across analysis scripts, eliminating code duplication.
"""

from .kill_switch import (
    # Constants
    KILL_SWITCH_CRITERIA,
    KILL_SWITCH_DISPLAY_NAMES,
    HARD_CRITERIA,
    SOFT_SEVERITY_WEIGHTS,
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    # Types
    KillSwitchResult,
    KillSwitchVerdict,
    # Functions
    apply_kill_switch,
    evaluate_kill_switches,
    evaluate_kill_switches_legacy,
    evaluate_kill_switches_for_display,
    get_kill_switch_summary,
)

__all__ = [
    # Constants
    "KILL_SWITCH_CRITERIA",
    "KILL_SWITCH_DISPLAY_NAMES",
    "HARD_CRITERIA",
    "SOFT_SEVERITY_WEIGHTS",
    "SEVERITY_FAIL_THRESHOLD",
    "SEVERITY_WARNING_THRESHOLD",
    # Types
    "KillSwitchResult",
    "KillSwitchVerdict",
    # Functions
    "apply_kill_switch",
    "evaluate_kill_switches",
    "evaluate_kill_switches_legacy",
    "evaluate_kill_switches_for_display",
    "get_kill_switch_summary",
]

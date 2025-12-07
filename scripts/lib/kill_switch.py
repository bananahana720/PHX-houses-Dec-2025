"""Compatibility layer for kill switch logic - delegates to service layer.

DEPRECATION NOTICE:
This module is a compatibility shim that wraps the service layer implementation
at src/phx_home_analysis/services/kill_switch/. New code should import directly
from the service layer. This module will be removed in a future release.

For details, see: src/phx_home_analysis/services/kill_switch/

Single source of truth for kill-switch criteria used by:
- scripts/phx_home_analyzer.py
- scripts/deal_sheets.py
- Other analysis scripts

Kill Switch System (5 HARD + 4 SOFT Criteria):
5 HARD criteria (instant fail) + 4 SOFT criteria (severity-based, fail if ≥3.0).

HARD criteria:
- NO HOA (hoa_fee must be $0)
- Minimum 4 bedrooms
- Minimum 2 bathrooms
- Minimum 1800 sqft
- Lot size >= 8000 sqft
- City sewer only (no septic)
- Minimum 1 indoor garage

Verdict Logic:
- Any HARD failure -> FAIL (instant)
- All pass -> PASS

Note: SOFT severity weights are deprecated and empty. The WARNING verdict
is retained for backward compatibility but not used in default configuration.

Usage with Property dataclass:
    from scripts.lib import apply_kill_switch
    prop = apply_kill_switch(prop)  # Updates prop.kill_switch_passed and failures

Usage with pandas DataFrame rows:
    from scripts.lib import evaluate_kill_switches
    verdict, severity, failures, results = evaluate_kill_switches(row_dict)

Usage with custom config:
    from scripts.lib.kill_switch import KillSwitchFilter
    filter = KillSwitchFilter(config_path='config/buyer_criteria.yaml')
    verdict, severity, failures, results = filter.evaluate(property_data)

MIGRATION GUIDE:
    OLD: from scripts.lib import evaluate_kill_switches
    NEW: from scripts.lib import evaluate_kill_switches  # Still works via compat shim

    OLD: from scripts.lib.kill_switch import KillSwitchFilter
    NEW: from phx_home_analysis.services.kill_switch import KillSwitchFilter
"""

import math
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, Union

import yaml

# Requires: uv pip install -e .
from phx_home_analysis.services.kill_switch.constants import (
    HARD_CRITERIA,
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    SOFT_SEVERITY_WEIGHTS,
    KillSwitchVerdict,
)

# =============================================================================
# SEVERITY THRESHOLD SYSTEM (imported from constants)
# =============================================================================


class PropertyLike(Protocol):
    """Protocol for objects that can be evaluated by kill switches.

    Compatible with:
    - scripts/phx_home_analyzer.py Property dataclass
    - src/phx_home_analysis/domain/entities.py Property entity
    - Any object with matching attributes
    """

    hoa_fee: int | float | None
    sewer_type: str | None
    garage_spaces: int | None
    garage_type: str | None  # "attached", "detached", None for indoor check
    beds: int
    baths: float
    sqft: int | None  # Interior square footage
    lot_sqft: int | None
    year_built: int | None


@dataclass
class KillSwitchResult:
    """Result of evaluating a single kill switch."""

    name: str
    passed: bool
    description: str
    actual_value: Any = None
    is_hard: bool = False  # True for HARD criteria (instant fail)
    severity_weight: float = 0.0  # Weight for SOFT criteria (0 if passed or HARD)


# =============================================================================
# KILL SWITCH CRITERIA DEFINITIONS
# =============================================================================

def _is_none_or_nan(value: Any) -> bool:
    """Check if value is None, NaN, or empty string (for pandas/CSV compatibility)."""
    if value is None:
        return True
    # Handle empty strings from CSV data
    if isinstance(value, str) and value.strip() == '':
        return True
    try:
        return math.isnan(value)
    except (TypeError, ValueError):
        return False


def _check_hoa(value: Any) -> tuple[bool, str]:
    """Check HOA requirement: Must be NO HOA (0 or None/NaN)."""
    if _is_none_or_nan(value) or value == 0:
        return True, "$0/mo" if value == 0 else "None"
    return False, f"${int(value)}/mo"


def _check_sewer(value: Any) -> tuple[bool, str]:
    """Check sewer requirement: Must be city sewer.

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    # Handle both string and enum values
    sewer_str = str(value).lower() if value else ""
    if sewer_str in ("city", "sewertype.city", "public"):
        return True, "City"
    return False, str(value).capitalize()


def _check_garage(value: Any, garage_type: Any = None) -> tuple[bool, str]:
    """Check garage requirement: Minimum 1 indoor garage space.

    Per Sprint 0 ARCH-01: min_spaces=1, indoor_required=True.
    Indoor = attached or detached (not carport, not None).

    Note: None/unknown spaces passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    spaces = int(value) if value else 0
    if spaces < 1:
        return False, f"{spaces}-car"
    # Check indoor requirement
    if garage_type is not None and not _is_none_or_nan(garage_type):
        garage_type_str = str(garage_type).lower()
        is_indoor = garage_type_str in ("attached", "detached")
        if not is_indoor:
            return False, f"{spaces}-car ({garage_type_str}, not indoor)"
    # Passed: at least 1 space, indoor or unknown type
    return True, f"{spaces}-car"


def _check_beds(value: Any) -> tuple[bool, str]:
    """Check bedroom requirement: Minimum 4 bedrooms."""
    beds = int(value) if value else 0
    if beds >= 4:
        return True, f"{beds} beds"
    return False, f"{beds} beds"


def _check_baths(value: Any) -> tuple[bool, str]:
    """Check bathroom requirement: Minimum 2 bathrooms."""
    baths = float(value) if value else 0.0
    if baths >= 2:
        return True, f"{baths} baths"
    return False, f"{baths} baths"


def _check_sqft(value: Any) -> tuple[bool, str]:
    """Check interior sqft requirement: Minimum 1800 sqft.

    Per Sprint 0 ARCH-04: min_sqft=1800 (HARD).

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    sqft = int(value) if value else 0
    if sqft >= 1800:
        return True, f"{sqft:,} sqft"
    return False, f"{sqft:,} sqft (need 1800+)"


def _check_lot_size(value: Any) -> tuple[bool, str]:
    """Check lot size requirement: Minimum 8,000 sqft.

    Per Sprint 0 ARCH-03: min_sqft=8000, max_sqft=None (no upper limit).

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    sqft = int(value) if value else 0
    if sqft >= 8000:
        return True, f"{sqft:,} sqft"
    return False, f"{sqft:,} sqft (need 8000+)"


def _check_year_built(value: Any) -> tuple[bool, str]:
    """Check year built requirement: No new builds (< current year).

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    year = int(value) if value else 0
    current_year = datetime.now().year
    if year < current_year:
        return True, str(year)
    return False, f"{year} (new build)"


# Central criteria definition - single source of truth
# 5 HARD criteria (instant fail) + 4 SOFT criteria (severity-based, fail if ≥3.0)
KILL_SWITCH_CRITERIA = {
    "hoa": {
        "field": "hoa_fee",
        "check": _check_hoa,
        "description": "NO HOA fees allowed",
        "requirement": "Must be $0/month or None",
        "is_hard": True,  # HARD: Buyer is firm on NO HOA
    },
    "beds": {
        "field": "beds",
        "check": _check_beds,
        "description": "Minimum 4 bedrooms",
        "requirement": "At least 4 bedrooms",
        "is_hard": True,  # HARD: Core space requirement
    },
    "baths": {
        "field": "baths",
        "check": _check_baths,
        "description": "Minimum 2 bathrooms",
        "requirement": "At least 2 bathrooms",
        "is_hard": True,  # HARD: Core space requirement
    },
    "sqft": {
        "field": "sqft",
        "check": _check_sqft,
        "description": "Minimum 1800 sqft",
        "requirement": "At least 1800 interior square feet",
        "is_hard": True,  # HARD: Core space requirement (ARCH-04)
    },
    "lot_size": {
        "field": "lot_sqft",
        "check": _check_lot_size,
        "description": "Lot size >= 8,000 sqft",
        "requirement": "At least 8,000 square feet lot",
        "is_hard": True,  # HARD: Lot requirement (ARCH-03)
    },
    "sewer": {
        "field": "sewer_type",
        "check": _check_sewer,
        "description": "City sewer required",
        "requirement": "No septic systems",
        "is_hard": True,  # HARD: Infrastructure requirement (ARCH-02)
    },
    "garage": {
        "field": "garage_spaces",
        "check": _check_garage,
        "description": "Minimum 1 indoor garage",
        "requirement": "At least 1 indoor (attached/detached) garage space",
        "is_hard": True,  # HARD: Garage requirement (ARCH-01)
    },
}

# year_built is a SOFT criterion with severity 2.0.
# The _check_year_built function is retained for custom configurations.
# To use it, add to KILL_SWITCH_CRITERIA:
#   "year_built": {
#       "field": "year_built",
#       "check": _check_year_built,
#       "description": f"No new builds (< {datetime.now().year})",
#       "requirement": f"Built before {datetime.now().year}",
#       "is_hard": True,
#   }


# =============================================================================
# EVALUATION FUNCTIONS
# =============================================================================

def _calculate_verdict(
    has_hard_failure: bool, severity_score: float
) -> KillSwitchVerdict:
    """Calculate final verdict based on HARD failures and severity score.

    Args:
        has_hard_failure: True if any HARD criterion failed
        severity_score: Sum of SOFT criterion weights for failed criteria

    Returns:
        KillSwitchVerdict: PASS, WARNING, or FAIL
    """
    if has_hard_failure:
        return KillSwitchVerdict.FAIL
    if severity_score >= SEVERITY_FAIL_THRESHOLD:
        return KillSwitchVerdict.FAIL
    if severity_score >= SEVERITY_WARNING_THRESHOLD:
        return KillSwitchVerdict.WARNING
    return KillSwitchVerdict.PASS


def evaluate_kill_switches(
    data: Union[dict[str, Any], "PropertyLike"],
) -> tuple[KillSwitchVerdict, float, list[str], list[KillSwitchResult]]:
    """Evaluate all kill switches against property data using severity threshold system.

    DEPRECATED: Use phx_home_analysis.services.kill_switch.KillSwitchFilter.evaluate()
    instead. This function will be removed in v2.0.

    Severity Threshold System:
    - HARD criteria (beds, baths, hoa): Instant FAIL on any failure
    - SOFT criteria (sewer, garage, lot_size, year_built): Weighted severity sum
    - Verdict based on severity thresholds

    Compatible with:
    - Dict from pandas DataFrame row (row.to_dict())
    - Property dataclass instance
    - Any object with matching attributes

    Args:
        data: Property data as dict or object with attributes

    Returns:
        Tuple of:
        - verdict: KillSwitchVerdict (PASS/WARNING/FAIL)
        - severity_score: float (sum of SOFT weights for failed criteria)
        - failure_messages: List of human-readable failure messages
        - results: List of KillSwitchResult for detailed inspection
    """
    warnings.warn(
        "evaluate_kill_switches() is deprecated. "
        "Use phx_home_analysis.services.kill_switch.KillSwitchFilter.evaluate() instead. "
        "This function will be removed in v2.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    failures: list[str] = []
    results: list[KillSwitchResult] = []
    has_hard_failure: bool = False
    severity_score: float = 0.0

    for name, criteria in KILL_SWITCH_CRITERIA.items():
        field_name = criteria["field"]
        is_hard = criteria.get("is_hard", name in HARD_CRITERIA)

        # Get value from dict or object
        if isinstance(data, dict):
            value = data.get(field_name)
        else:
            value = getattr(data, field_name, None)

        # Special handling for garage - needs garage_type for indoor check
        if name == "garage":
            if isinstance(data, dict):
                garage_type = data.get("garage_type")
            else:
                garage_type = getattr(data, "garage_type", None)
            passed, actual_str = criteria["check"](value, garage_type)
        else:
            # Evaluate criterion
            passed, actual_str = criteria["check"](value)

        # Calculate severity weight for this criterion
        criterion_weight = 0.0
        if not passed:
            if is_hard:
                has_hard_failure = True
            else:
                criterion_weight = SOFT_SEVERITY_WEIGHTS.get(name, 0.0)
                severity_score += criterion_weight

        result = KillSwitchResult(
            name=name,
            passed=passed,
            description=criteria["description"],
            actual_value=actual_str,
            is_hard=is_hard,
            severity_weight=criterion_weight,
        )
        results.append(result)

        if not passed:
            severity_info = ""
            if not is_hard and criterion_weight > 0:
                severity_info = f" [severity +{criterion_weight}]"
            elif is_hard:
                severity_info = " [HARD FAIL]"
            failures.append(
                f"{name}: {criteria['description']} ({actual_str}){severity_info}"
            )

    verdict = _calculate_verdict(has_hard_failure, severity_score)
    return verdict, severity_score, failures, results


def evaluate_kill_switches_legacy(
    data: Union[dict[str, Any], "PropertyLike"],
) -> tuple[bool, list[str], list[KillSwitchResult]]:
    """Legacy evaluation function for backward compatibility.

    Returns the old-style (passed, failures, results) tuple.
    PASS/WARNING map to True, FAIL maps to False.

    Args:
        data: Property data as dict or object with attributes

    Returns:
        Tuple of:
        - passed: True if verdict is PASS or WARNING, False if FAIL
        - failure_messages: List of human-readable failure messages
        - results: List of KillSwitchResult for detailed inspection
    """
    verdict, severity, failures, results = evaluate_kill_switches(data)
    # WARNING is still considered "passed" for legacy compatibility
    # Only FAIL is a hard rejection
    passed = verdict != KillSwitchVerdict.FAIL
    return passed, failures, results


def apply_kill_switch(prop: "PropertyLike") -> "PropertyLike":
    """Apply all kill switch criteria to a Property and update its attributes.

    DEPRECATED: Use phx_home_analysis.services.kill_switch.KillSwitchFilter.filter_properties()
    instead. This function will be removed in v2.0.

    Updates prop.kill_switch_passed, prop.kill_switch_failures, and optionally
    prop.kill_switch_verdict and prop.kill_switch_severity in-place.

    Args:
        prop: Property dataclass instance to evaluate

    Returns:
        The same property instance (modified in-place)
    """
    warnings.warn(
        "apply_kill_switch() is deprecated. "
        "Use phx_home_analysis.services.kill_switch.KillSwitchFilter.filter_properties() instead. "
        "This function will be removed in v2.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    verdict, severity, failures, _ = evaluate_kill_switches(prop)

    # PASS and WARNING both count as "passed" for backward compatibility
    # Only FAIL results in kill_switch_passed = False
    prop.kill_switch_passed = verdict != KillSwitchVerdict.FAIL
    prop.kill_switch_failures = failures

    # Optionally set new severity fields if they exist on the property
    if hasattr(prop, "kill_switch_verdict"):
        prop.kill_switch_verdict = verdict.value
    if hasattr(prop, "kill_switch_severity"):
        prop.kill_switch_severity = severity

    return prop


def get_kill_switch_summary() -> str:
    """Get human-readable summary of all kill switch criteria.

    Returns:
        Multi-line string describing 5 HARD + 4 SOFT criteria
    """
    lines = [
        "Kill Switch Criteria (5 HARD + 4 SOFT):",
        "",
        "HARD Criteria (instant fail):"
    ]

    # List all criteria (5 HARD + 4 SOFT)
    for _name, criteria in KILL_SWITCH_CRITERIA.items():
        lines.append(f"  - {criteria['description']}")
        lines.append(f"    Requirement: {criteria['requirement']}")

    lines.append("")
    lines.append("Verdict: Any HARD failure -> FAIL, All pass -> PASS")
    lines.append("")
    lines.append("Note: SOFT severity weights are deprecated (empty dict).")
    return "\n".join(lines)


def get_criteria_for_field(field_name: str) -> dict[str, Any] | None:
    """Get kill switch criteria for a specific field.

    Args:
        field_name: Name of the field (e.g., "hoa_fee", "lot_sqft")

    Returns:
        Criteria dict or None if no criterion for that field
    """
    for name, criteria in KILL_SWITCH_CRITERIA.items():
        if criteria["field"] == field_name:
            return {"name": name, **criteria}
    return None


# =============================================================================
# PANDAS/RENDERING COMPATIBLE FUNCTIONS
# =============================================================================

def evaluate_kill_switches_for_display(
    data: Union[dict[str, Any], "PropertyLike"],
) -> dict[str, dict[str, Any]]:
    """Evaluate kill switches with display-friendly output for deal sheets.

    DEPRECATED: Use phx_home_analysis.services.kill_switch module instead.
    This function will be removed in v2.0.

    Compatible with pandas DataFrame rows and rendering use cases.
    Returns results with color coding for UI display.

    Note: 5 HARD criteria (instant fail) + 4 SOFT criteria (severity-based).

    Args:
        data: Property data as dict or object with attributes

    Returns:
        Dict mapping criterion name to result dict with:
        - passed: bool
        - color: 'green' | 'yellow' | 'red'
        - label: 'PASS' | 'FAIL' | 'UNKNOWN' | 'HARD FAIL'
        - description: human-readable value description
        - is_hard: bool (True for HARD criteria)
        - severity_weight: float (weight for SOFT criteria, 0 if passed)

        Also includes '_summary' key with:
        - verdict: 'PASS' | 'WARNING' | 'FAIL'
        - severity_score: float
    """
    warnings.warn(
        "evaluate_kill_switches_for_display() is deprecated. "
        "Use phx_home_analysis.services.kill_switch module instead. "
        "This function will be removed in v2.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    results: dict[str, dict[str, Any]] = {}
    severity_score = 0.0
    has_hard_failure = False

    for name, criteria in KILL_SWITCH_CRITERIA.items():
        field_name = criteria["field"]
        is_hard = criteria.get("is_hard", name in HARD_CRITERIA)

        # Get value from dict or object
        if isinstance(data, dict):
            value = data.get(field_name)
        else:
            value = getattr(data, field_name, None)

        # Get garage_type for garage check
        garage_type = None
        if name == "garage":
            if isinstance(data, dict):
                garage_type = data.get("garage_type")
            else:
                garage_type = getattr(data, "garage_type", None)

        # Check if value is missing/unknown
        if _is_none_or_nan(value):
            # Unknown/missing data - mark as yellow warning
            # Note: Some criteria pass with unknown values (permissive)
            if name == "garage":
                passed, actual_str = criteria["check"](value, garage_type)
            else:
                passed, actual_str = criteria["check"](value)
            if passed:
                color = "yellow"  # Passed but uncertain
                label = "UNKNOWN"
            else:
                color = "red"
                label = "HARD FAIL" if is_hard else "FAIL"
        else:
            if name == "garage":
                passed, actual_str = criteria["check"](value, garage_type)
            else:
                passed, actual_str = criteria["check"](value)
            if passed:
                color = "green"
                label = "PASS"
            else:
                color = "red"
                label = "HARD FAIL" if is_hard else "FAIL"

        # Calculate severity for failed SOFT criteria
        criterion_weight = 0.0
        if not passed:
            if is_hard:
                has_hard_failure = True
            else:
                criterion_weight = SOFT_SEVERITY_WEIGHTS.get(name, 0.0)
                severity_score += criterion_weight

        results[name.upper() if len(name) <= 4 else name.title()] = {
            "passed": passed,
            "color": color,
            "label": label,
            "description": actual_str,
            "is_hard": is_hard,
            "severity_weight": criterion_weight,
        }

    # Add summary information
    verdict = _calculate_verdict(has_hard_failure, severity_score)
    results["_summary"] = {
        "verdict": verdict.value,
        "severity_score": severity_score,
        "has_hard_failure": has_hard_failure,
    }

    return results


# Display name mapping for deal sheets (Title Case)
KILL_SWITCH_DISPLAY_NAMES = {
    "hoa": "HOA",
    "beds": "Beds",
    "baths": "Baths",
    "sqft": "Sqft",
    "lot_size": "Lot Size",
    "sewer": "Sewer",
    "garage": "Garage",
}


# =============================================================================
# CONFIGURABLE KILL SWITCH FILTER
# =============================================================================

class KillSwitchFilter:
    """Kill switch filter with configurable criteria from YAML.

    DEPRECATED: Use phx_home_analysis.services.kill_switch.KillSwitchFilter instead.
    This class will be removed in v2.0.

    Supports loading buyer criteria from YAML config file while maintaining
    backward compatibility with hardcoded defaults.

    Usage:
        # Use default criteria (hardcoded values)
        filter = KillSwitchFilter()

        # Use custom YAML config
        filter = KillSwitchFilter(config_path='config/buyer_criteria.yaml')

        # Evaluate property
        verdict, severity, failures, results = filter.evaluate(property_data)
    """

    # Instance variable type annotations
    config_path: str | None
    hoa_fee_max: int
    min_beds: int
    min_baths: int
    min_sqft: int
    min_lot_sqft: int
    max_lot_sqft: int | None
    required_sewer: str
    min_garage: int
    garage_indoor_required: bool
    sewer_severity: float
    garage_severity: float
    lot_severity: float
    max_year_built: int | None
    year_severity: float
    severity_fail_threshold: float
    severity_warning_threshold: float

    def __init__(self, config_path: str | None = None):
        """Initialize filter with optional YAML config.

        Args:
            config_path: Path to YAML config file. If None, uses hardcoded defaults.
        """
        warnings.warn(
            "KillSwitchFilter from scripts.lib is deprecated. "
            "Use phx_home_analysis.services.kill_switch.KillSwitchFilter instead. "
            "This class will be removed in v2.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.config_path = config_path
        self._load_config()

    def _load_config(self) -> None:
        """Load criteria from YAML config or use defaults."""
        if self.config_path is None:
            # Use hardcoded defaults
            self._use_defaults()
            return

        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"Kill switch config file not found: {self.config_path}"
            )

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML config: {e}") from e

        # Load hard criteria
        hard = config.get('hard_criteria', {})
        self.hoa_fee_max = hard.get('hoa_fee', 0)
        self.min_beds = hard.get('min_beds', 4)
        self.min_baths = hard.get('min_baths', 2)

        # Load soft criteria
        soft = config.get('soft_criteria', {})

        # Sewer type
        sewer = soft.get('sewer_type', {})
        self.required_sewer = sewer.get('required', 'city')
        self.sewer_severity = sewer.get('severity', 2.5)

        # Year built
        year = soft.get('year_built', {})
        max_year_str = year.get('max', 'current_year')
        if max_year_str == 'current_year':
            self.max_year_built = datetime.now().year
        else:
            self.max_year_built = int(max_year_str)
        self.year_severity = year.get('severity', 2.0)

        # Garage
        garage = soft.get('garage_spaces', {})
        self.min_garage = garage.get('min', 2)
        self.garage_severity = garage.get('severity', 1.5)

        # Lot size
        lot = soft.get('lot_sqft', {})
        self.min_lot_sqft = lot.get('min', 7000)
        self.max_lot_sqft = lot.get('max', 15000)
        self.lot_severity = lot.get('severity', 1.0)

        # Load thresholds
        thresholds = config.get('thresholds', {})
        self.severity_fail_threshold = thresholds.get('severity_fail', 3.0)
        self.severity_warning_threshold = thresholds.get('severity_warning', 1.5)

    def _use_defaults(self) -> None:
        """Use hardcoded default criteria values (5 HARD + 4 SOFT)."""
        # All criteria are HARD (instant fail)
        self.hoa_fee_max = 0
        self.min_beds = 4
        self.min_baths = 2
        self.min_sqft = 1800  # ARCH-04
        self.min_lot_sqft = 8000  # ARCH-03 (no max)
        self.max_lot_sqft = None  # No upper limit
        self.required_sewer = 'city'  # ARCH-02
        self.min_garage = 1  # ARCH-01
        self.garage_indoor_required = True  # ARCH-01

        # Deprecated: SOFT severity weights (all criteria now HARD)
        self.sewer_severity = 0.0  # Deprecated
        self.garage_severity = 0.0  # Deprecated
        self.lot_severity = 0.0  # Deprecated

        # year_built removed from defaults (class retained for custom use)
        self.max_year_built = None
        self.year_severity = 0.0  # Deprecated

        # Thresholds (retained for backward compatibility)
        self.severity_fail_threshold = 3.0
        self.severity_warning_threshold = 1.5

    def evaluate(
        self, data: dict[str, Any] | PropertyLike
    ) -> tuple[KillSwitchVerdict, float, list[str], list[KillSwitchResult]]:
        """Evaluate property against configured criteria.

        This method uses the standard kill switch logic but with configurable
        thresholds and criteria from YAML config (or defaults).

        Args:
            data: Property data as dict or PropertyLike object

        Returns:
            Tuple of (verdict, severity_score, failure_messages, results)
        """
        # For now, delegate to standard evaluation function
        # In future, could customize evaluation logic based on config
        return evaluate_kill_switches(data)

    def get_summary(self) -> str:
        """Get human-readable summary of configured criteria.

        Returns:
            Multi-line string describing 5 HARD + 4 SOFT criteria
        """
        lot_desc = f"{self.min_lot_sqft:,}+ sqft"
        if self.max_lot_sqft:
            lot_desc = f"{self.min_lot_sqft:,}-{self.max_lot_sqft:,} sqft"

        indoor_note = " (indoor required)" if getattr(self, 'garage_indoor_required', False) else ""

        lines = [
            "Kill Switch Criteria (5 HARD + 4 SOFT):",
            "",
            "HARD Criteria (instant fail):",
            f"  - HOA fee: Must be ${self.hoa_fee_max}/month or None",
            f"  - Bedrooms: Minimum {self.min_beds} bedrooms",
            f"  - Bathrooms: Minimum {self.min_baths} bathrooms",
            f"  - Sqft: Minimum {getattr(self, 'min_sqft', 1800):,} sqft",
            f"  - Lot size: {lot_desc}",
            f"  - Sewer: Must be {self.required_sewer}",
            f"  - Garage: Minimum {self.min_garage} space(s){indoor_note}",
            "",
            "Verdict: Any HARD failure -> FAIL, All pass -> PASS",
        ]

        if self.config_path:
            lines.insert(1, f"Config source: {self.config_path}")
        else:
            lines.insert(1, "Config source: hardcoded defaults")

        return "\n".join(lines)

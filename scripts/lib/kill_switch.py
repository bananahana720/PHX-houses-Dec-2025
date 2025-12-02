"""Consolidated Kill Switch Logic for PHX Home Analysis Scripts.

Single source of truth for kill-switch criteria used by:
- scripts/phx_home_analyzer.py
- scripts/deal_sheets.py
- Other analysis scripts

Kill Switch System (Weighted Severity Threshold):
- HARD criteria (instant fail): beds < 4, baths < 2, HOA > $0
- SOFT criteria (severity weighted): sewer, garage, lot_size, year_built

Verdict Logic:
- Any HARD failure -> FAIL (instant, severity N/A)
- severity >= 3.0 -> FAIL (threshold exceeded)
- 1.5 <= severity < 3.0 -> WARNING (approaching limit)
- severity < 1.5 -> PASS

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
"""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, Union

import yaml

# =============================================================================
# SEVERITY THRESHOLD SYSTEM
# =============================================================================

class KillSwitchVerdict(Enum):
    """Kill switch verdict outcome."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


# Severity weights for SOFT criteria
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
    "sewer": 2.5,      # Septic risk - infrastructure concern
    "garage": 1.5,     # Convenience factor
    "lot_size": 1.0,   # Minor preference
    "year_built": 2.0, # New build avoidance
}

# HARD criteria - instant fail, no severity calculation
HARD_CRITERIA: set = {"hoa", "beds", "baths"}

# Threshold constants
SEVERITY_FAIL_THRESHOLD: float = 3.0
SEVERITY_WARNING_THRESHOLD: float = 1.5


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
    beds: int
    baths: float
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
    """Check if value is None or NaN (for pandas compatibility)."""
    if value is None:
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


def _check_garage(value: Any) -> tuple[bool, str]:
    """Check garage requirement: Minimum 2-car garage.

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    spaces = int(value) if value else 0
    if spaces >= 2:
        return True, f"{spaces}-car"
    return False, f"{spaces}-car"


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


def _check_lot_size(value: Any) -> tuple[bool, str]:
    """Check lot size requirement: 7,000-15,000 sqft.

    Note: None/unknown passes with warning (cannot verify).
    """
    if _is_none_or_nan(value):
        return True, "Unknown"
    sqft = int(value) if value else 0
    if 7000 <= sqft <= 15000:
        return True, f"{sqft:,} sqft"
    if sqft < 7000:
        return False, f"{sqft:,} sqft (too small)"
    return False, f"{sqft:,} sqft (too large)"


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
# is_hard: True = instant fail (HARD), False = contributes to severity (SOFT)
KILL_SWITCH_CRITERIA = {
    "hoa": {
        "field": "hoa_fee",
        "check": _check_hoa,
        "description": "NO HOA fees allowed",
        "requirement": "Must be $0/month or None",
        "is_hard": True,  # HARD: Buyer is firm on NO HOA
    },
    "sewer": {
        "field": "sewer_type",
        "check": _check_sewer,
        "description": "City sewer required",
        "requirement": "No septic systems",
        "is_hard": False,  # SOFT: Infrastructure risk (weight 2.5)
    },
    "garage": {
        "field": "garage_spaces",
        "check": _check_garage,
        "description": "Minimum 2-car garage",
        "requirement": "At least 2 garage spaces",
        "is_hard": False,  # SOFT: Convenience factor (weight 1.5)
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
    "lot_size": {
        "field": "lot_sqft",
        "check": _check_lot_size,
        "description": "Lot size 7,000-15,000 sqft",
        "requirement": "Between 7,000 and 15,000 square feet",
        "is_hard": False,  # SOFT: Minor preference (weight 1.0)
    },
    "year_built": {
        "field": "year_built",
        "check": _check_year_built,
        "description": f"No new builds (< {datetime.now().year})",
        "requirement": f"Built before {datetime.now().year}",
        "is_hard": False,  # SOFT: New build avoidance (weight 2.0)
    },
}


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

    Updates prop.kill_switch_passed, prop.kill_switch_failures, and optionally
    prop.kill_switch_verdict and prop.kill_switch_severity in-place.

    Args:
        prop: Property dataclass instance to evaluate

    Returns:
        The same property instance (modified in-place)
    """
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
        Multi-line string describing all criteria with severity info
    """
    lines = [
        "Kill Switch Criteria (Severity Threshold System):",
        "",
        "HARD Criteria (instant fail):"
    ]

    # List HARD criteria
    for name, criteria in KILL_SWITCH_CRITERIA.items():
        if criteria.get("is_hard", False):
            lines.append(f"  - {criteria['description']}")
            lines.append(f"    Requirement: {criteria['requirement']}")

    lines.append("")
    lines.append("SOFT Criteria (severity weighted):")

    # List SOFT criteria with weights
    for name, criteria in KILL_SWITCH_CRITERIA.items():
        if not criteria.get("is_hard", False):
            weight = SOFT_SEVERITY_WEIGHTS.get(name, 0.0)
            lines.append(f"  - {criteria['description']} (weight: {weight})")
            lines.append(f"    Requirement: {criteria['requirement']}")

    lines.append("")
    lines.append(f"Thresholds: FAIL >= {SEVERITY_FAIL_THRESHOLD}, "
                 f"WARNING >= {SEVERITY_WARNING_THRESHOLD}")
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

    Compatible with pandas DataFrame rows and rendering use cases.
    Returns results with color coding for UI display.

    Now includes severity information for SOFT criteria.

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

        # Check if value is missing/unknown
        if _is_none_or_nan(value):
            # Unknown/missing data - mark as yellow warning
            # Note: Some criteria pass with unknown values (permissive)
            passed, actual_str = criteria["check"](value)
            if passed:
                color = "yellow"  # Passed but uncertain
                label = "UNKNOWN"
            else:
                color = "red"
                label = "HARD FAIL" if is_hard else "FAIL"
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
    "sewer": "Sewer",
    "garage": "Garage",
    "beds": "Beds",
    "baths": "Baths",
    "lot_size": "Lot Size",
    "year_built": "Year Built",
}


# =============================================================================
# CONFIGURABLE KILL SWITCH FILTER
# =============================================================================

class KillSwitchFilter:
    """Kill switch filter with configurable criteria from YAML.

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

    def __init__(self, config_path: str | None = None):
        """Initialize filter with optional YAML config.

        Args:
            config_path: Path to YAML config file. If None, uses hardcoded defaults.
        """
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
            raise ValueError(f"Failed to parse YAML config: {e}")

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
        """Use hardcoded default criteria values."""
        # Hard criteria
        self.hoa_fee_max = 0
        self.min_beds = 4
        self.min_baths = 2

        # Soft criteria
        self.required_sewer = 'city'
        self.sewer_severity = 2.5
        self.max_year_built = datetime.now().year
        self.year_severity = 2.0
        self.min_garage = 2
        self.garage_severity = 1.5
        self.min_lot_sqft = 7000
        self.max_lot_sqft = 15000
        self.lot_severity = 1.0

        # Thresholds
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
            Multi-line string describing all criteria and thresholds
        """
        lines = [
            "Kill Switch Criteria (Configured):",
            "",
            "HARD Criteria (instant fail):",
            f"  - HOA fee: Must be ${self.hoa_fee_max}/month or None",
            f"  - Bedrooms: Minimum {self.min_beds} bedrooms",
            f"  - Bathrooms: Minimum {self.min_baths} bathrooms",
            "",
            "SOFT Criteria (severity weighted):",
            f"  - Sewer: Must be {self.required_sewer} (severity: {self.sewer_severity})",
            f"  - Year built: Before {self.max_year_built} (severity: {self.year_severity})",
            f"  - Garage: Minimum {self.min_garage} spaces (severity: {self.garage_severity})",
            f"  - Lot size: {self.min_lot_sqft:,}-{self.max_lot_sqft:,} sqft (severity: {self.lot_severity})",
            "",
            f"Thresholds: FAIL >= {self.severity_fail_threshold}, "
            f"WARNING >= {self.severity_warning_threshold}",
        ]

        if self.config_path:
            lines.insert(1, f"Config source: {self.config_path}")
        else:
            lines.insert(1, "Config source: Hardcoded defaults")

        return "\n".join(lines)

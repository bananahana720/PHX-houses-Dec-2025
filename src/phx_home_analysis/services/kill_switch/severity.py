"""SOFT Kill-Switch Severity Evaluator.

This module provides dedicated evaluation of SOFT criteria with severity accumulation.
It extracts the severity calculation logic into a dedicated class following the
Single Responsibility Principle.

Severity Thresholds (from config.constants):
- FAIL: Total severity >= 3.0 (severity threshold exceeded)
- WARNING: Total severity >= 1.5 and < 3.0 (approaching threshold)
- PASS: Total severity < 1.5 (acceptable severity level)

Current SOFT Criteria (from constants.py):
| Criterion    | Severity | Condition for Failure       |
|--------------|----------|----------------------------|
| city_sewer   | 2.5      | Sewer type is not CITY     |
| no_new_build | 2.0      | Year built > 2023          |
| min_garage   | 1.5      | Garage spaces < 2          |
| lot_size     | 1.0      | Lot outside 7k-15k sqft    |

Severity Accumulation Examples:
| Failed Criteria      | Total Severity | Verdict |
|----------------------|----------------|---------|
| None                 | 0.0            | PASS    |
| lot_size only        | 1.0            | PASS    |
| min_garage only      | 1.5            | WARNING |
| lot_size + min_garage| 2.5            | WARNING |
| city_sewer only      | 2.5            | WARNING |
| city_sewer + lot_size| 3.5            | FAIL    |
| All 4 SOFT fail      | 7.0            | FAIL    |

Usage:
    from phx_home_analysis.services.kill_switch.severity import (
        SoftSeverityEvaluator,
        SoftSeverityResult,
    )

    evaluator = SoftSeverityEvaluator()
    result = evaluator.evaluate(soft_criterion_results)
    print(result.verdict)        # PASS, WARNING, or FAIL
    print(result.total_severity) # e.g., 2.5
    print(result.breakdown)      # {"city_sewer": 2.5}
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from .base import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    KillSwitchVerdict,
)

if TYPE_CHECKING:
    from .explanation import CriterionResult

import logging

logger = logging.getLogger(__name__)


@dataclass
class SoftSeverityResult:
    """Result of SOFT criteria severity evaluation.

    Contains the total accumulated severity, verdict determination,
    failed criteria list, and detailed breakdown by criterion.

    Attributes:
        total_severity: Sum of severity weights for all failed SOFT criteria
        verdict: KillSwitchVerdict (PASS/WARNING/FAIL) based on thresholds
        failed_criteria: List of CriterionResult objects that failed
        breakdown: Dict mapping criterion name to its severity contribution

    Example:
        >>> result = SoftSeverityResult(
        ...     total_severity=2.5,
        ...     verdict=KillSwitchVerdict.WARNING,
        ...     failed_criteria=[cr1],
        ...     breakdown={"city_sewer": 2.5}
        ... )
        >>> result.verdict.value
        'WARNING'
    """

    total_severity: float
    verdict: KillSwitchVerdict
    failed_criteria: list["CriterionResult"] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary with verdict, severity, and breakdown fields
        """
        return {
            "total_severity": self.total_severity,
            "verdict": self.verdict.value,
            "failed_criteria_count": len(self.failed_criteria),
            "failed_criteria": [cr.name for cr in self.failed_criteria],
            "breakdown": self.breakdown,
            "threshold_fail": SEVERITY_FAIL_THRESHOLD,
            "threshold_warning": SEVERITY_WARNING_THRESHOLD,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if not self.failed_criteria:
            return f"SOFT Severity: {self.verdict.value} (0.0 - no SOFT failures)"
        criteria_list = ", ".join(self.breakdown.keys())
        return (
            f"SOFT Severity: {self.verdict.value} "
            f"(total={self.total_severity:.1f}, failed=[{criteria_list}])"
        )


class SoftCriterionConfig(BaseModel):
    """Configuration for a single SOFT criterion loaded from CSV.

    This model validates CSV rows for SOFT criteria configuration,
    enabling config-driven loading without code changes.

    CSV Schema:
        name,type,operator,threshold,severity,description

    Example CSV row:
        city_sewer,SOFT,==,CITY,2.5,City sewer required (no septic)

    Attributes:
        name: Unique identifier for the criterion (e.g., "city_sewer")
        type: Must be "SOFT" for SOFT criteria
        operator: Comparison operator (==, !=, >, <, >=, <=, range)
        threshold: Value to compare against (string for flexibility)
        severity: Severity weight when criterion fails (0.1-10.0)
        description: Human-readable description of the criterion
    """

    name: str = Field(..., min_length=1, description="Unique criterion identifier")
    type: str = Field(..., pattern=r"^(SOFT|HARD)$", description="Criterion type")
    operator: str = Field(
        ...,
        pattern=r"^(==|!=|>|<|>=|<=|range)$",
        description="Comparison operator",
    )
    threshold: str = Field(..., description="Comparison value(s)")
    severity: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Severity weight when failed",
    )
    description: str = Field(..., description="Human-readable description")

    @field_validator("severity")
    @classmethod
    def validate_severity_precision(cls, v: float) -> float:
        """Ensure severity has reasonable precision (max 2 decimal places)."""
        return round(v, 2)

    model_config = {"strict": True, "extra": "forbid"}


class SoftSeverityEvaluator:
    """Evaluator for SOFT kill-switch criteria with severity accumulation.

    This class implements the dedicated SOFT criteria evaluation logic,
    calculating total severity and determining verdict based on thresholds.

    Threshold-Based Verdicts:
        - FAIL: total_severity >= 3.0 (severity threshold exceeded)
        - WARNING: total_severity >= 1.5 and < 3.0 (approaching threshold)
        - PASS: total_severity < 1.5 (acceptable severity level)

    Attributes:
        fail_threshold: Severity threshold for FAIL verdict (default: 3.0)
        warning_threshold: Severity threshold for WARNING verdict (default: 1.5)

    Usage:
        evaluator = SoftSeverityEvaluator()

        # Evaluate a list of SOFT criterion results
        soft_results = [cr for cr in all_results if not cr.is_hard]
        result = evaluator.evaluate(soft_results)

        if result.verdict == KillSwitchVerdict.FAIL:
            print(f"SOFT severity too high: {result.total_severity}")

    Example - Adding Future SOFT Criteria:
        To add a new SOFT criterion (e.g., "pool" with severity 0.5):

        1. Add to config/kill_switch.csv:
           pool,SOFT,==,true,0.5,Pool presence preferred

        2. Create criterion class in criteria.py implementing KillSwitch

        3. The evaluator will automatically include it in severity calculation

        Note: Severity weights should be calibrated so combinations make sense:
        - Single criterion should not exceed WARNING threshold (1.5) alone
          unless it's a significant issue (e.g., city_sewer at 2.5)
        - Multiple minor issues should accumulate to WARNING/FAIL
        - Current weights sum to 7.0 (all fail = FAIL verdict)
    """

    def __init__(
        self,
        fail_threshold: float = SEVERITY_FAIL_THRESHOLD,
        warning_threshold: float = SEVERITY_WARNING_THRESHOLD,
    ):
        """Initialize evaluator with severity thresholds.

        Args:
            fail_threshold: Severity at or above which verdict is FAIL (default: 3.0)
            warning_threshold: Severity at or above which verdict is WARNING (default: 1.5)

        Raises:
            ValueError: If fail_threshold <= warning_threshold
        """
        if fail_threshold <= warning_threshold:
            raise ValueError(
                f"fail_threshold ({fail_threshold}) must be > warning_threshold ({warning_threshold})"
            )
        self.fail_threshold = fail_threshold
        self.warning_threshold = warning_threshold

    def evaluate(self, soft_results: list["CriterionResult"]) -> SoftSeverityResult:
        """Evaluate SOFT criteria and return severity result.

        Accumulates severity weights from failed SOFT criteria and determines
        verdict based on configured thresholds.

        Args:
            soft_results: List of CriterionResult objects for SOFT criteria only.
                          Each result should have is_hard=False.

        Returns:
            SoftSeverityResult with total severity, verdict, and breakdown.

        Note:
            This method filters out any HARD criteria that may have been
            accidentally included. Only non-passing SOFT criteria contribute
            to the severity score.

        Example:
            >>> from phx_home_analysis.services.kill_switch.explanation import CriterionResult
            >>> results = [
            ...     CriterionResult(name="city_sewer", passed=False, is_hard=False, severity=2.5, message="Septic"),
            ...     CriterionResult(name="lot_size", passed=False, is_hard=False, severity=1.0, message="Too small"),
            ... ]
            >>> evaluator = SoftSeverityEvaluator()
            >>> result = evaluator.evaluate(results)
            >>> result.total_severity
            3.5
            >>> result.verdict
            <KillSwitchVerdict.FAIL: 'FAIL'>
        """
        # Filter to only SOFT criteria that failed
        failed_soft = [cr for cr in soft_results if not cr.is_hard and not cr.passed]

        # Build breakdown and calculate total
        breakdown: dict[str, float] = {}
        total_severity = 0.0

        for cr in failed_soft:
            breakdown[cr.name] = cr.severity
            total_severity += cr.severity

        # Round to 2 decimal places to avoid float precision errors (e.g., 2.9999999 vs 3.0)
        total_severity = round(total_severity, 2)

        # Determine verdict based on thresholds
        verdict = self._calculate_verdict(total_severity)

        return SoftSeverityResult(
            total_severity=total_severity,
            verdict=verdict,
            failed_criteria=failed_soft,
            breakdown=breakdown,
        )

    def _calculate_verdict(self, severity: float) -> KillSwitchVerdict:
        """Calculate verdict based on severity score.

        Args:
            severity: Total accumulated severity score

        Returns:
            KillSwitchVerdict based on threshold comparison:
            - FAIL if severity >= fail_threshold (3.0)
            - WARNING if severity >= warning_threshold (1.5)
            - PASS otherwise
        """
        if severity >= self.fail_threshold:
            return KillSwitchVerdict.FAIL
        if severity >= self.warning_threshold:
            return KillSwitchVerdict.WARNING
        return KillSwitchVerdict.PASS

    def get_threshold_info(self) -> dict[str, float]:
        """Get configured threshold values.

        Returns:
            Dictionary with fail and warning thresholds
        """
        return {
            "fail_threshold": self.fail_threshold,
            "warning_threshold": self.warning_threshold,
        }

    def __str__(self) -> str:
        """String representation showing thresholds."""
        return f"SoftSeverityEvaluator(fail>={self.fail_threshold}, warn>={self.warning_threshold})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"SoftSeverityEvaluator(fail_threshold={self.fail_threshold}, "
            f"warning_threshold={self.warning_threshold})"
        )


def load_soft_criteria_config(path: Path) -> list[SoftCriterionConfig]:
    """Load SOFT criteria configuration from CSV file.

    Note:
        **Future Implementation**: This function is not yet wired into
        KillSwitchFilter's production initialization. The filter uses hardcoded
        criteria from _get_default_kill_switches(). This CSV loader is provided
        for validation, testing, and future config-driven criteria support.

    Reads a CSV file with kill-switch criteria definitions and returns
    validated SoftCriterionConfig objects for SOFT criteria only.

    CSV Schema (header row required):
        name,type,operator,threshold,severity,description

    Example CSV:
        name,type,operator,threshold,severity,description
        city_sewer,SOFT,==,CITY,2.5,City sewer required (no septic)
        no_new_build,SOFT,<=,2023,2.0,No new builds (year <= 2023)
        min_garage,SOFT,>=,2,1.5,Minimum 2 garage spaces
        lot_size,SOFT,range,7000-15000,1.0,Lot size 7k-15k sqft preferred

    Args:
        path: Path to CSV file containing criteria configuration

    Returns:
        List of validated SoftCriterionConfig objects (SOFT type only)

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV format is invalid or validation fails

    Example:
        >>> from pathlib import Path
        >>> configs = load_soft_criteria_config(Path("config/kill_switch.csv"))
        >>> for cfg in configs:
        ...     print(f"{cfg.name}: severity={cfg.severity}")
        city_sewer: severity=2.5
        no_new_build: severity=2.0
        min_garage: severity=1.5
        lot_size: severity=1.0
    """
    import csv

    if not path.exists():
        logger.error("Kill-switch config file not found: %s", path)
        raise FileNotFoundError(f"Kill-switch config file not found: {path}")

    configs: list[SoftCriterionConfig] = []

    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate header
        expected_fields = {"name", "type", "operator", "threshold", "severity", "description"}
        if reader.fieldnames is None:
            logger.error("CSV file has no header row: %s", path)
            raise ValueError(f"CSV file has no header row: {path}")

        missing_fields = expected_fields - set(reader.fieldnames)
        if missing_fields:
            logger.error(
                "CSV missing required fields: %s. Expected: %s", missing_fields, expected_fields
            )
            raise ValueError(
                f"CSV missing required fields: {missing_fields}. Expected: {expected_fields}"
            )

        hard_rows_skipped = 0
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Skip comment lines (rows where name starts with #)
            name_value = row.get("name", "").strip()
            if name_value.startswith("#"):
                continue

            # Skip HARD criteria - only process SOFT
            row_type = row.get("type", "").upper()
            if row_type == "HARD":
                hard_rows_skipped += 1
                continue
            if row_type != "SOFT":
                # Skip any other unrecognized type silently (could be blank/malformed)
                continue

            try:
                # Convert severity to float
                severity = float(row["severity"])

                config = SoftCriterionConfig(
                    name=name_value,
                    type=row_type,
                    operator=row["operator"].strip(),
                    threshold=row["threshold"].strip(),
                    severity=severity,
                    description=row["description"].strip(),
                )
                configs.append(config)
            except (ValueError, KeyError) as e:
                logger.error("Invalid data in CSV row %d: %s. Row: %s", row_num, e, row)
                raise ValueError(f"Invalid data in CSV row {row_num}: {e}. Row: {row}") from e

    # Log warning for skipped HARD rows (HARD criteria are code-defined, not CSV-driven)
    if hard_rows_skipped > 0:
        logger.warning(
            "Skipped %d HARD criteria rows from %s (HARD criteria are code-defined)",
            hard_rows_skipped,
            path,
        )

    return configs

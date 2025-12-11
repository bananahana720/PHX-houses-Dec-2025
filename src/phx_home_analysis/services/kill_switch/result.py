"""Kill-switch result dataclasses for verdict evaluation.

This module provides structured result types for kill-switch evaluations,
enabling comprehensive tracking of verdict outcomes with full metadata.

Usage:
    from phx_home_analysis.services.kill_switch import (
        KillSwitchResult,
        FailedCriterion,
    )

    # Create a failed criterion
    failed = FailedCriterion(
        name="no_hoa",
        actual_value=150.0,
        required_value="$0",
        is_hard=True,
        severity=0.0,
    )

    # Create a result
    result = KillSwitchResult(
        verdict=KillSwitchVerdict.FAIL,
        failed_criteria=[failed],
        severity_score=0.0,
        timestamp=datetime.now(),
        property_address="123 Main St, Phoenix, AZ",
    )

    print(result)  # Quick summary
    print(result.to_dict())  # JSON serialization
    print(result.is_passing)  # False
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base import KillSwitchVerdict


@dataclass
class FailedCriterion:
    """Represents a single failed kill-switch criterion.

    Captures both HARD (instant fail) and SOFT (severity weighted) criterion
    failures with all metadata needed for reporting and analysis.

    Attributes:
        name: Criterion identifier (e.g., "no_hoa", "city_sewer")
        actual_value: What the property actually has
        required_value: Human-readable requirement description
        is_hard: True for HARD criteria (instant fail), False for SOFT
        severity: Severity weight for SOFT criteria, 0.0 for HARD

    Example:
        # HARD criterion failure
        hard_fail = FailedCriterion(
            name="no_hoa",
            actual_value=150.0,
            required_value="$0 (no HOA allowed)",
            is_hard=True,
            severity=0.0,
        )

        # SOFT criterion failure
        soft_fail = FailedCriterion(
            name="city_sewer",
            actual_value="septic",
            required_value="city sewer",
            is_hard=False,
            severity=2.5,
        )
    """

    name: str
    actual_value: Any
    required_value: str
    is_hard: bool
    severity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields suitable for JSON export
        """
        return {
            "name": self.name,
            "actual_value": self.actual_value,
            "required_value": self.required_value,
            "is_hard": self.is_hard,
            "severity": self.severity,
        }

    def __str__(self) -> str:
        """Human-readable format for display.

        Returns:
            Formatted string showing criterion failure details
        """
        type_label = "HARD" if self.is_hard else f"SOFT (severity {self.severity})"
        return f"{self.name} [{type_label}]: {self.actual_value} (required: {self.required_value})"


@dataclass
class KillSwitchResult:
    """Comprehensive result of kill-switch evaluation for a property.

    Encapsulates the complete verdict with all metadata needed for
    reporting, persistence, and analysis.

    Attributes:
        verdict: PASS, WARNING, or FAIL
        failed_criteria: All failed criteria (not just first)
        severity_score: Accumulated SOFT severity score
        timestamp: When the evaluation was performed
        property_address: Property identifier for reports

    Properties:
        is_passing: True if verdict is not FAIL

    Example:
        result = KillSwitchResult(
            verdict=KillSwitchVerdict.WARNING,
            failed_criteria=[
                FailedCriterion(
                    name="city_sewer",
                    actual_value="septic",
                    required_value="city sewer",
                    is_hard=False,
                    severity=2.5,
                ),
            ],
            severity_score=2.5,
            timestamp=datetime.now(),
            property_address="123 Main St, Phoenix, AZ",
        )

        print(result.is_passing)  # True (WARNING is still passing)
        print(result.to_dict())   # JSON-serializable dict
    """

    verdict: KillSwitchVerdict
    failed_criteria: list[FailedCriterion] = field(default_factory=list)
    severity_score: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    property_address: str = ""

    @property
    def is_passing(self) -> bool:
        """Check if the verdict allows the property to pass.

        PASS and WARNING verdicts are considered passing.
        Only FAIL is considered non-passing.

        Returns:
            True if verdict is PASS or WARNING, False if FAIL
        """
        return self.verdict != KillSwitchVerdict.FAIL

    @property
    def hard_failures(self) -> list[FailedCriterion]:
        """Get only HARD criterion failures.

        Returns:
            List of FailedCriterion where is_hard is True
        """
        return [fc for fc in self.failed_criteria if fc.is_hard]

    @property
    def soft_failures(self) -> list[FailedCriterion]:
        """Get only SOFT criterion failures.

        Returns:
            List of FailedCriterion where is_hard is False
        """
        return [fc for fc in self.failed_criteria if not fc.is_hard]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields suitable for JSON export
        """
        return {
            "verdict": self.verdict.value,
            "failed_criteria": [fc.to_dict() for fc in self.failed_criteria],
            "severity_score": self.severity_score,
            "timestamp": self.timestamp.isoformat(),
            "property_address": self.property_address,
            "is_passing": self.is_passing,
        }

    def __str__(self) -> str:
        """Quick summary for display.

        Returns:
            One-line summary of the verdict and key metrics
        """
        hard_count = len(self.hard_failures)
        soft_count = len(self.soft_failures)

        parts = [f"Kill-Switch: {self.verdict.value}"]

        if self.property_address:
            parts.append(f"for {self.property_address}")

        if hard_count > 0:
            parts.append(f"({hard_count} HARD failure(s))")
        elif soft_count > 0:
            parts.append(f"(severity: {self.severity_score:.1f})")

        return " ".join(parts)

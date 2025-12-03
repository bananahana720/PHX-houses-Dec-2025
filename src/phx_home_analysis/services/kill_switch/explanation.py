"""Kill-switch verdict explanation generator.

This module provides human-readable explanations for kill-switch verdicts,
translating the technical evaluation results into clear, actionable feedback.

Usage:
    explainer = VerdictExplainer()
    explanation = explainer.explain(verdict, criterion_results)
    print(explanation.to_text())
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import KillSwitchVerdict


@dataclass
class CriterionResult:
    """Result of a single kill-switch criterion check.

    Attributes:
        name: Kill switch criterion name (e.g., "no_hoa", "min_bedrooms")
        passed: Whether the property passed this criterion
        is_hard: Whether this is a HARD criterion (instant fail)
        severity: Severity weight (0 if passed or HARD)
        message: Human-readable failure message
    """

    name: str
    passed: bool
    is_hard: bool
    severity: float  # 0 if passed or hard
    message: str


@dataclass
class VerdictExplanation:
    """Human-readable explanation of kill-switch verdict.

    Provides structured breakdown of verdict with categorized failures
    and a narrative explanation suitable for user display.

    Attributes:
        verdict: Verdict string (PASS, WARNING, FAIL)
        summary: One-line summary of verdict outcome
        hard_failures: List of HARD criterion failures (instant fail)
        soft_failures: List of SOFT criterion failures (exceeded threshold)
        soft_warnings: List of SOFT criterion warnings (below threshold)
        total_severity: Sum of all SOFT failure severity weights
        severity_threshold: Threshold used to determine FAIL verdict
    """

    verdict: str  # PASS, WARNING, FAIL
    summary: str  # One-line summary
    hard_failures: list[CriterionResult]
    soft_failures: list[CriterionResult]
    soft_warnings: list[CriterionResult]
    total_severity: float
    severity_threshold: float

    def to_text(self) -> str:
        """Generate full text explanation.

        Returns:
            Multi-line markdown formatted explanation suitable for
            console display, logging, or report generation
        """
        lines = [f"## Kill-Switch Verdict: {self.verdict}", "", self.summary, ""]

        if self.hard_failures:
            lines.append("### Hard Failures (Instant Fail)")
            for cr in self.hard_failures:
                lines.append(f"- **{cr.name}**: {cr.message}")
            lines.append("")

        if self.soft_failures:
            lines.append(
                f"### Soft Failures (Severity: {self.total_severity:.1f} >= {self.severity_threshold})"
            )
            for cr in self.soft_failures:
                lines.append(f"- **{cr.name}** (severity {cr.severity}): {cr.message}")
            lines.append("")

        if self.soft_warnings:
            lines.append("### Warnings (Below Threshold)")
            for cr in self.soft_warnings:
                lines.append(f"- **{cr.name}** (severity {cr.severity}): {cr.message}")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert explanation to dictionary for JSON serialization.

        Returns:
            Dictionary with all explanation fields suitable for JSON export
        """
        return {
            "verdict": self.verdict,
            "summary": self.summary,
            "hard_failures": [
                {
                    "name": cr.name,
                    "message": cr.message,
                }
                for cr in self.hard_failures
            ],
            "soft_failures": [
                {
                    "name": cr.name,
                    "severity": cr.severity,
                    "message": cr.message,
                }
                for cr in self.soft_failures
            ],
            "soft_warnings": [
                {
                    "name": cr.name,
                    "severity": cr.severity,
                    "message": cr.message,
                }
                for cr in self.soft_warnings
            ],
            "total_severity": self.total_severity,
            "severity_threshold": self.severity_threshold,
        }


class VerdictExplainer:
    """Generates human-readable explanations for kill-switch verdicts.

    Transforms technical verdict results into user-friendly explanations
    with categorized failures and actionable feedback.

    Usage:
        explainer = VerdictExplainer()
        verdict, severity, failures = filter_service.evaluate_with_severity(property)

        # Build criterion results
        criterion_results = []
        for kill_switch in filter_service._kill_switches:
            passed = kill_switch.check(property)
            cr = CriterionResult(
                name=kill_switch.name,
                passed=passed,
                is_hard=kill_switch.is_hard,
                severity=0.0 if passed or kill_switch.is_hard else kill_switch.severity_weight,
                message=kill_switch.failure_message(property) if not passed else ""
            )
            criterion_results.append(cr)

        explanation = explainer.explain(verdict, criterion_results)
        print(explanation.to_text())
    """

    def __init__(self, severity_threshold: float = 3.0):
        """Initialize explainer with severity threshold.

        Args:
            severity_threshold: SOFT severity threshold for FAIL verdict (default: 3.0)
        """
        self.severity_threshold = severity_threshold

    def explain(
        self, verdict: "KillSwitchVerdict", criterion_results: list[CriterionResult]
    ) -> VerdictExplanation:
        """Generate explanation from verdict and criterion results.

        Args:
            verdict: The final kill-switch verdict (PASS/WARNING/FAIL)
            criterion_results: List of individual criterion evaluation results

        Returns:
            VerdictExplanation with structured breakdown and narrative summary
        """
        # Separate hard failures and soft failures
        hard_failures = [cr for cr in criterion_results if not cr.passed and cr.is_hard]
        soft_failures = [cr for cr in criterion_results if not cr.passed and not cr.is_hard]

        # Calculate total severity from soft failures
        total_severity = sum(cr.severity for cr in soft_failures)

        # Separate soft failures into actual failures vs warnings
        # based on whether total severity exceeds threshold
        actual_failures = []
        warnings = []

        if total_severity >= self.severity_threshold:
            # All soft failures are actual failures (contributed to exceeding threshold)
            actual_failures = soft_failures
        else:
            # Total severity below threshold, these are just warnings
            warnings = soft_failures

        # Generate summary based on verdict type
        summary = self._generate_summary(
            verdict, hard_failures, total_severity, len(actual_failures), len(warnings)
        )

        return VerdictExplanation(
            verdict=verdict.value,
            summary=summary,
            hard_failures=hard_failures,
            soft_failures=actual_failures,
            soft_warnings=warnings,
            total_severity=total_severity,
            severity_threshold=self.severity_threshold,
        )

    def _generate_summary(
        self,
        verdict: "KillSwitchVerdict",
        hard_failures: list[CriterionResult],
        total_severity: float,
        failure_count: int,
        warning_count: int,
    ) -> str:
        """Generate one-line summary based on verdict and failures.

        Args:
            verdict: The final verdict
            hard_failures: List of HARD criterion failures
            total_severity: Total SOFT severity score
            failure_count: Number of SOFT failures
            warning_count: Number of SOFT warnings

        Returns:
            One-line summary string
        """
        # Import verdict enum locally to avoid circular dependency
        from .base import KillSwitchVerdict

        if hard_failures:
            # FAIL due to HARD criteria
            criterion_names = ", ".join(cr.name for cr in hard_failures)
            return (
                f"Property FAILED due to {len(hard_failures)} hard criterion "
                f"violation(s): {criterion_names}"
            )
        elif verdict == KillSwitchVerdict.FAIL:
            # FAIL due to soft severity threshold
            return (
                f"Property FAILED - soft severity {total_severity:.1f} exceeds "
                f"threshold {self.severity_threshold}"
            )
        elif verdict == KillSwitchVerdict.WARNING:
            # WARNING - severity approaching threshold
            return (
                f"Property WARNING - soft severity {total_severity:.1f} approaching "
                f"threshold {self.severity_threshold}"
            )
        else:
            # PASS - all criteria met or severity acceptable
            if warning_count > 0:
                return (
                    f"Property PASSED with {warning_count} minor warning(s) "
                    f"(severity {total_severity:.1f})"
                )
            return "Property PASSED all kill-switch criteria"

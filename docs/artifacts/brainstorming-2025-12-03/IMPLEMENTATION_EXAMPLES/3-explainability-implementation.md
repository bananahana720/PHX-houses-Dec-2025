# 3. EXPLAINABILITY IMPLEMENTATION

### 3.1 Kill-Switch Verdict Explanation

```python
# src/phx_home_analysis/services/kill_switch/verdict.py

from dataclasses import dataclass


@dataclass
class CriterionEvaluation:
    """Result of evaluating a single criterion."""
    criterion_id: str
    criterion_name: str
    requirement: str
    actual_value: Any
    passed: bool
    severity_weight: float | None = None


@dataclass
class KillSwitchVerdictExplanation:
    """Detailed explanation of kill-switch verdict."""
    verdict: str  # "PASS", "WARNING", "FAIL"
    verdict_explanation: str
    evaluated_at: datetime
    evaluator: str

    # Hard failures (if any)
    hard_failures: list[CriterionEvaluation]

    # Soft criteria results
    soft_criteria_results: list[CriterionEvaluation]
    total_severity: float
    severity_fail_threshold: float
    severity_warning_threshold: float

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    def to_readable_text(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"KILL-SWITCH VERDICT: {self.verdict.upper()}",
            f"Evaluated: {self.evaluated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        if self.hard_failures:
            lines.append("HARD CRITERIA FAILURES (Instant Fail):")
            for failure in self.hard_failures:
                lines.append(f"  ✗ {failure.criterion_name}")
                lines.append(f"    Requirement: {failure.requirement}")
                lines.append(f"    Actual: {failure.actual_value}")
                lines.append("")

        if self.soft_criteria_results:
            lines.append("SOFT CRITERIA EVALUATION:")
            lines.append(f"(Threshold: {self.severity_fail_threshold} to FAIL, " +
                        f"{self.severity_warning_threshold} to WARN)")
            lines.append("")

            total_severity = 0.0
            for result in self.soft_criteria_results:
                status = "✓ PASS" if result.passed else "✗ FAIL"
                lines.append(f"{status}: {result.criterion_name}")
                lines.append(f"  Requirement: {result.requirement}")
                lines.append(f"  Actual: {result.actual_value}")

                if not result.passed:
                    lines.append(f"  Severity: +{result.severity_weight}")
                    total_severity += result.severity_weight

                lines.append("")

            lines.append(f"TOTAL SEVERITY: {total_severity}")
            lines.append(f"FAIL THRESHOLD: {self.severity_fail_threshold}")
            lines.append(f"VERDICT: {'FAIL (severity exceeded)' if total_severity >= self.severity_fail_threshold else 'PASS'}")
            lines.append("")

        if self.recommendations:
            lines.append("RECOMMENDATIONS:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")

        return "\n".join(lines)


# Usage in KillSwitchFilter
class ExplainableKillSwitchFilter:
    """Kill-switch filter with detailed explanations."""

    def evaluate_with_explanation(
        self,
        property: Property
    ) -> KillSwitchVerdictExplanation:
        """Evaluate property with full explanation."""
        hard_failures = []
        soft_results = []
        total_severity = 0.0

        # Evaluate hard criteria
        for criterion in self.hard_criteria:
            value = getattr(property, criterion.field, None)
            evaluation = CriterionEvaluation(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                requirement=criterion.requirement_description(),
                actual_value=value,
                passed=criterion.evaluate(value)
            )

            if not evaluation.passed:
                hard_failures.append(evaluation)

        # If any hard failures, return immediately
        if hard_failures:
            return KillSwitchVerdictExplanation(
                verdict="FAIL",
                verdict_explanation="Property failed hard criteria (instant fail)",
                evaluated_at=datetime.now(),
                evaluator="KillSwitchFilter",
                hard_failures=hard_failures,
                soft_criteria_results=[],
                total_severity=0.0,
                severity_fail_threshold=self.fail_threshold,
                severity_warning_threshold=self.warning_threshold,
                recommendations=[
                    f"Address {failure.criterion_name.lower()} to pass filter"
                    for failure in hard_failures
                ]
            )

        # Evaluate soft criteria
        for criterion in self.soft_criteria:
            value = getattr(property, criterion.field, None)
            passed = criterion.evaluate(value)
            severity = 0.0 if passed else criterion.severity_weight

            evaluation = CriterionEvaluation(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                requirement=criterion.requirement_description(),
                actual_value=value,
                passed=passed,
                severity_weight=criterion.severity_weight
            )
            soft_results.append(evaluation)

            if not passed:
                total_severity += severity

        # Determine verdict
        if total_severity >= self.fail_threshold:
            verdict = "FAIL"
            verdict_text = f"Severity {total_severity} >= threshold {self.fail_threshold}"
        elif total_severity >= self.warning_threshold:
            verdict = "WARNING"
            verdict_text = f"Severity {total_severity} >= warning {self.warning_threshold}"
        else:
            verdict = "PASS"
            verdict_text = f"Severity {total_severity} < threshold {self.warning_threshold}"

        # Generate recommendations
        recommendations = []
        if total_severity >= self.warning_threshold:
            failed_criteria = [r for r in soft_results if not r.passed]
            for criterion in failed_criteria:
                recommendations.append(
                    f"Address {criterion.criterion_name} (severity {criterion.severity_weight})"
                )

        return KillSwitchVerdictExplanation(
            verdict=verdict,
            verdict_explanation=verdict_text,
            evaluated_at=datetime.now(),
            evaluator="KillSwitchFilter",
            hard_failures=[],
            soft_criteria_results=soft_results,
            total_severity=total_severity,
            severity_fail_threshold=self.fail_threshold,
            severity_warning_threshold=self.warning_threshold,
            recommendations=recommendations
        )
```

---

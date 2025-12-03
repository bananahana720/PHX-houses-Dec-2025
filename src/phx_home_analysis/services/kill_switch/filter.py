"""Kill Switch Filter orchestrator for property evaluation.

This module provides the KillSwitchFilter class that coordinates multiple
kill switch criteria to evaluate properties using a weighted severity threshold
system.

Severity Threshold System:
- HARD criteria (instant fail): beds < 4, baths < 2, HOA > $0, solar lease
- SOFT criteria (severity weighted): sewer, garage, lot_size, year_built

Verdict Logic:
- Any HARD failure -> FAIL (instant, severity N/A)
- severity >= 3.0 -> FAIL (threshold exceeded)
- 1.5 <= severity < 3.0 -> WARNING (approaching limit)
- severity < 1.5 -> PASS
"""

from typing import TYPE_CHECKING

from .base import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
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
    NoSolarLeaseKillSwitch,
)
from .explanation import CriterionResult, VerdictExplainer, VerdictExplanation

if TYPE_CHECKING:
    from ...domain.entities import Property


class KillSwitchFilter:
    """Orchestrator for evaluating properties against kill switch criteria.

    Uses weighted severity threshold system:
    - HARD criteria cause instant FAIL
    - SOFT criteria accumulate severity scores
    - Verdict determined by severity thresholds

    Default kill switches match buyer requirements from CLAUDE.md:
    - NO HOA (HARD)
    - NO solar lease (HARD)
    - Minimum 4 bedrooms (HARD)
    - Minimum 2 bathrooms (HARD)
    - City sewer only (SOFT, weight=2.5)
    - Minimum 2-car garage (SOFT, weight=1.5)
    - Lot size 7,000-15,000 sqft (SOFT, weight=1.0)
    - No new builds (pre-2024) (SOFT, weight=2.0)

    Usage:
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(properties)

        # Or with severity-aware evaluation
        verdict, severity, failures = filter_service.evaluate_with_severity(property)

        # Or with custom kill switches
        custom_switches = [NoHoaKillSwitch(), MinBedroomsKillSwitch(min_beds=3)]
        filter_service = KillSwitchFilter(kill_switches=custom_switches)
    """

    def __init__(self, kill_switches: list[KillSwitch] | None = None):
        """Initialize filter with kill switch criteria.

        Args:
            kill_switches: List of KillSwitch instances to apply. If None,
                uses all default kill switches from CLAUDE.md buyer criteria.
        """
        if kill_switches is None:
            # Use all default kill switches from buyer requirements
            self._kill_switches = self._get_default_kill_switches()
        else:
            self._kill_switches = kill_switches

        # Initialize verdict explainer with threshold from constants
        self._explainer = VerdictExplainer(severity_threshold=SEVERITY_FAIL_THRESHOLD)

    @staticmethod
    def _get_default_kill_switches() -> list[KillSwitch]:
        """Get default kill switches matching CLAUDE.md buyer requirements.

        Returns:
            List of all default KillSwitch instances
        """
        return [
            NoHoaKillSwitch(),
            NoSolarLeaseKillSwitch(),
            CitySewerKillSwitch(),
            MinGarageKillSwitch(min_spaces=2),
            MinBedroomsKillSwitch(min_beds=4),
            MinBathroomsKillSwitch(min_baths=2.0),
            LotSizeKillSwitch(min_sqft=7000, max_sqft=15000),
            NoNewBuildKillSwitch(max_year=2023),
        ]

    def _calculate_verdict(
        self, has_hard_failure: bool, severity_score: float
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

    def evaluate_with_severity(
        self, property: "Property"
    ) -> tuple[KillSwitchVerdict, float, list[str]]:
        """Evaluate property with full severity information.

        Args:
            property: Property entity to evaluate

        Returns:
            Tuple of (verdict, severity_score, failure_messages) where:
            - verdict: KillSwitchVerdict (PASS/WARNING/FAIL)
            - severity_score: Sum of SOFT weights for failed criteria
            - failure_messages: List of failure messages with severity info
        """
        failures: list[str] = []
        has_hard_failure: bool = False
        severity_score: float = 0.0

        for kill_switch in self._kill_switches:
            if not kill_switch.check(property):
                # Property failed this kill switch
                failure_msg = kill_switch.failure_message(property)
                failures.append(failure_msg)

                if kill_switch.is_hard:
                    has_hard_failure = True
                else:
                    severity_score += kill_switch.severity_weight

        verdict = self._calculate_verdict(has_hard_failure, severity_score)
        return verdict, severity_score, failures

    def evaluate_with_explanation(
        self, property: "Property"
    ) -> tuple[KillSwitchVerdict, float, list[str], VerdictExplanation]:
        """Evaluate property with full severity information and human-readable explanation.

        This method extends evaluate_with_severity by also generating a complete
        explanation of the verdict that can be displayed to users or included in reports.

        Args:
            property: Property entity to evaluate

        Returns:
            Tuple of (verdict, severity_score, failure_messages, explanation) where:
            - verdict: KillSwitchVerdict (PASS/WARNING/FAIL)
            - severity_score: Sum of SOFT weights for failed criteria
            - failure_messages: List of failure messages with severity info
            - explanation: VerdictExplanation with structured breakdown

        Example:
            verdict, severity, failures, explanation = filter.evaluate_with_explanation(prop)
            print(explanation.to_text())  # Display explanation
            print(explanation.summary)    # Get one-line summary
        """
        # Build criterion results for all kill switches
        criterion_results: list[CriterionResult] = []
        has_hard_failure: bool = False
        severity_score: float = 0.0
        failures: list[str] = []

        for kill_switch in self._kill_switches:
            passed = kill_switch.check(property)

            # Create criterion result
            cr = CriterionResult(
                name=kill_switch.name,
                passed=passed,
                is_hard=kill_switch.is_hard,
                severity=0.0 if passed or kill_switch.is_hard else kill_switch.severity_weight,
                message=kill_switch.failure_message(property) if not passed else "",
            )
            criterion_results.append(cr)

            # Track failures for backward compatibility
            if not passed:
                failures.append(cr.message)
                if kill_switch.is_hard:
                    has_hard_failure = True
                else:
                    severity_score += kill_switch.severity_weight

        # Calculate verdict
        verdict = self._calculate_verdict(has_hard_failure, severity_score)

        # Generate explanation
        explanation = self._explainer.explain(verdict, criterion_results)

        return verdict, severity_score, failures, explanation


    def evaluate(self, property: "Property") -> tuple[bool, list[str]]:
        """Evaluate single property against all kill switches.

        Applies all kill switches using severity threshold system.
        PASS and WARNING both return True (passed), only FAIL returns False.

        Args:
            property: Property entity to evaluate

        Returns:
            Tuple of (passed_all, failure_messages) where:
            - passed_all: True if verdict is PASS or WARNING, False if FAIL
            - failure_messages: List of failure messages (empty if no failures)
        """
        verdict, severity, failures = self.evaluate_with_severity(property)
        # WARNING is still considered "passed" for backward compatibility
        passed = verdict != KillSwitchVerdict.FAIL
        return passed, failures

    def filter_properties(
        self, properties: list["Property"]
    ) -> tuple[list["Property"], list["Property"]]:
        """Filter list of properties into passed and failed categories.

        Evaluates each property using severity threshold system and updates its
        kill_switch_passed and kill_switch_failures attributes. Properties with
        WARNING verdict are considered passed but may have warnings recorded.

        Args:
            properties: List of Property entities to filter

        Returns:
            Tuple of (passed_properties, failed_properties) where:
            - passed_properties: Properties with PASS or WARNING verdict
            - failed_properties: Properties with FAIL verdict
        """
        passed: list[Property] = []
        failed: list[Property] = []

        for property in properties:
            verdict, severity, failure_messages = self.evaluate_with_severity(property)

            # Update property with kill switch results
            # PASS and WARNING both map to kill_switch_passed = True
            property.kill_switch_passed = verdict != KillSwitchVerdict.FAIL
            property.kill_switch_failures = failure_messages

            # Optionally set new severity fields if they exist
            if hasattr(property, "kill_switch_verdict"):
                property.kill_switch_verdict = verdict.value
            if hasattr(property, "kill_switch_severity"):
                property.kill_switch_severity = severity

            # Categorize for return
            if verdict != KillSwitchVerdict.FAIL:
                passed.append(property)
            else:
                failed.append(property)

        return passed, failed

    def get_kill_switch_names(self) -> list[str]:
        """Get list of all active kill switch names.

        Returns:
            List of kill switch name identifiers
        """
        return [ks.name for ks in self._kill_switches]

    def get_kill_switch_descriptions(self) -> list[str]:
        """Get list of all active kill switch descriptions.

        Returns:
            List of human-readable kill switch descriptions
        """
        return [ks.description for ks in self._kill_switches]

    def get_hard_criteria(self) -> list[KillSwitch]:
        """Get list of HARD kill switches (instant fail).

        Returns:
            List of HARD KillSwitch instances
        """
        return [ks for ks in self._kill_switches if ks.is_hard]

    def get_soft_criteria(self) -> list[KillSwitch]:
        """Get list of SOFT kill switches (severity weighted).

        Returns:
            List of SOFT KillSwitch instances
        """
        return [ks for ks in self._kill_switches if not ks.is_hard]

    def summary(self) -> str:
        """Generate summary of active kill switches with severity info.

        Returns:
            Multi-line string describing all active kill switches
        """
        lines = [
            "Kill Switch Filter (Severity Threshold System)",
            f"Total: {len(self._kill_switches)} criteria",
            "",
            "HARD Criteria (instant fail):",
        ]

        for ks in self.get_hard_criteria():
            lines.append(f"  - {ks.name}: {ks.description}")

        lines.append("")
        lines.append("SOFT Criteria (severity weighted):")

        for ks in self.get_soft_criteria():
            lines.append(f"  - {ks.name} (weight={ks.severity_weight}): {ks.description}")

        lines.append("")
        lines.append(
            f"Thresholds: FAIL >= {SEVERITY_FAIL_THRESHOLD}, "
            f"WARNING >= {SEVERITY_WARNING_THRESHOLD}"
        )

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation shows count of active kill switches."""
        hard_count = len(self.get_hard_criteria())
        soft_count = len(self.get_soft_criteria())
        return f"KillSwitchFilter({hard_count} HARD, {soft_count} SOFT criteria)"

    def __repr__(self) -> str:
        """Developer representation shows kill switch names."""
        names = ", ".join(self.get_kill_switch_names())
        return f"KillSwitchFilter(kill_switches=[{names}])"

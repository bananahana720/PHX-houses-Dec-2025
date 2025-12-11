"""Kill Switch Filter orchestrator for property evaluation.

This module provides the KillSwitchFilter class that coordinates multiple
kill switch criteria to evaluate properties.

5 HARD + 4 SOFT Kill-Switch Criteria:

HARD (instant fail):
- NO HOA (hoa_fee must be 0 or None)
- NO solar lease
- Minimum 4 bedrooms
- Minimum 2 bathrooms
- Minimum 1800 sqft living space

SOFT (severity accumulation):
- City sewer only (severity 2.5)
- Year built <=2023 (severity 2.0)
- Minimum 2 indoor garage spaces (severity 1.5)
- Lot size 7k-15k sqft (severity 1.0)

Verdict Logic:
- Any HARD failure -> FAIL (instant)
- SOFT severity >=3.0 -> FAIL
- SOFT severity >=1.5 -> WARNING
- Otherwise -> PASS

Configuration:
- Default: Uses hardcoded criteria (backward compatible)
- Config-driven: Provide config_path to load from CSV file

Usage:
    # Default (hardcoded criteria)
    filter_service = KillSwitchFilter()

    # Config-driven
    filter_service = KillSwitchFilter(config_path=Path("config/kill_switch.csv"))

    # With hot-reload in dev mode
    filter_service = KillSwitchFilter(
        config_path=Path("config/kill_switch.csv"),
        enable_hot_reload=True,
    )
"""

import logging
from pathlib import Path
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
    MinSqftKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)
from .explanation import CriterionResult, VerdictExplainer, VerdictExplanation

if TYPE_CHECKING:
    from ...domain.entities import Property
    from .config_loader import KillSwitchConfig
    from .config_watcher import ConfigWatcher
    from .result import KillSwitchResult
    from .severity import SoftSeverityEvaluator, SoftSeverityResult

logger = logging.getLogger(__name__)


class KillSwitchFilter:
    """Orchestrator for evaluating properties against kill switch criteria.

    5 HARD + 4 SOFT criteria with severity accumulation system.

    HARD criteria (instant fail):
    1. NO HOA (HARD)
    2. NO solar lease (HARD)
    3. Minimum 4 bedrooms (HARD)
    4. Minimum 2 bathrooms (HARD)
    5. Minimum 1800 sqft living space (HARD)

    SOFT criteria (severity weighted):
    6. City sewer only (severity 2.5)
    7. Year built <=2023 (severity 2.0)
    8. Minimum 2 indoor garage spaces (severity 1.5)
    9. Lot size 7k-15k sqft (severity 1.0)

    Verdict thresholds:
    - FAIL: Any HARD failure OR severity >=3.0
    - WARNING: Severity >=1.5
    - PASS: All HARD pass AND severity <1.5

    Usage:
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(properties)

        # Or with severity-aware evaluation
        verdict, severity, failures = filter_service.evaluate_with_severity(property)

        # Or with custom kill switches
        custom_switches = [NoHoaKillSwitch(), MinBedroomsKillSwitch(min_beds=3)]
        filter_service = KillSwitchFilter(kill_switches=custom_switches)
    """

    def __init__(
        self,
        kill_switches: list[KillSwitch] | None = None,
        config_path: str | Path | None = None,
        enable_hot_reload: bool = False,
    ):
        """Initialize filter with kill switch criteria.

        Args:
            kill_switches: List of KillSwitch instances to apply. Takes precedence
                over config_path if both provided.
            config_path: Path to CSV configuration file. If provided (and kill_switches
                is None), loads criteria from CSV.
            enable_hot_reload: If True and config_path is provided, watch for config
                file changes and reload automatically (dev mode only).

        Priority:
            1. kill_switches (explicit list) - highest priority
            2. config_path (load from CSV) - if kill_switches is None
            3. Default hardcoded criteria - if both are None
        """
        # Store config path for potential hot-reload
        self._config_path: Path | None = Path(config_path) if config_path else None
        self._enable_hot_reload = enable_hot_reload
        self._config_watcher: ConfigWatcher | None = None

        # Determine kill switches to use (priority order)
        if kill_switches is not None:
            self._kill_switches = kill_switches
        elif self._config_path is not None:
            self._kill_switches = self._load_from_config(self._config_path)
        else:
            # Use all default kill switches from buyer requirements
            self._kill_switches = self._get_default_kill_switches()

        # Initialize verdict explainer with threshold from constants
        self._explainer = VerdictExplainer(severity_threshold=SEVERITY_FAIL_THRESHOLD)

        # Initialize SOFT severity evaluator for dedicated SOFT evaluation
        # Import here to avoid circular imports - module uses this class
        from .severity import SoftSeverityEvaluator

        self._soft_evaluator = SoftSeverityEvaluator(
            fail_threshold=SEVERITY_FAIL_THRESHOLD,
            warning_threshold=SEVERITY_WARNING_THRESHOLD,
        )

        # Setup hot-reload watcher if enabled
        if enable_hot_reload and self._config_path is not None:
            self._setup_hot_reload()

    @staticmethod
    def _get_default_kill_switches() -> list[KillSwitch]:
        """Get default kill switches matching buyer requirements.

        5 HARD criteria (instant fail):
        - NO HOA
        - NO solar lease
        - Minimum 4 bedrooms
        - Minimum 2 bathrooms
        - Minimum 1800 sqft

        4 SOFT criteria (severity weighted, accumulate):
        - City sewer only (severity 2.5)
        - No new builds <=2023 (severity 2.0)
        - Minimum 2 garage spaces (severity 1.5)
        - Lot size 7k-15k sqft (severity 1.0)

        Returns:
            List of all default KillSwitch instances (5 HARD + 4 SOFT criteria)
        """
        return [
            NoHoaKillSwitch(),
            NoSolarLeaseKillSwitch(),
            MinBedroomsKillSwitch(min_beds=4),
            MinBathroomsKillSwitch(min_baths=2.0),
            MinSqftKillSwitch(min_sqft=1800),
            # SOFT criteria (severity weighted)
            CitySewerKillSwitch(),
            NoNewBuildKillSwitch(max_year=2023),
            MinGarageKillSwitch(min_spaces=2, indoor_required=True),
            LotSizeKillSwitch(min_sqft=7000, max_sqft=15000),
        ]

    def _load_from_config(self, config_path: Path) -> list[KillSwitch]:
        """Load kill switches from CSV configuration file.

        Args:
            config_path: Path to CSV configuration file

        Returns:
            List of KillSwitch instances created from config

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        from .config_factory import load_kill_switches_from_config

        return load_kill_switches_from_config(config_path)

    def _setup_hot_reload(self) -> None:
        """Set up hot-reload watcher for configuration changes.

        Only active when enable_hot_reload=True was passed to __init__.
        Creates a ConfigWatcher that monitors the config file for changes.
        """
        if self._config_path is None:
            return

        from .config_watcher import ConfigWatcher

        self._config_watcher = ConfigWatcher(
            config_path=self._config_path,
            on_change=self._on_config_change,
        )
        logger.info("Hot-reload watcher enabled for %s", self._config_path)

    def _on_config_change(self, new_configs: list["KillSwitchConfig"]) -> None:
        """Callback when configuration file changes.

        Args:
            new_configs: List of KillSwitchConfig objects from updated file
        """
        from .config_factory import create_kill_switches_from_config

        old_names = {ks.name for ks in self._kill_switches}
        self._kill_switches = create_kill_switches_from_config(new_configs)
        new_names = {ks.name for ks in self._kill_switches}

        added = new_names - old_names
        removed = old_names - new_names

        if added:
            logger.info("Config hot-reload: Added criteria: %s", added)
        if removed:
            logger.info("Config hot-reload: Removed criteria: %s", removed)

    def reload_config(self) -> list[str]:
        """Reload configuration from file.

        Reloads the kill-switch configuration from the CSV file specified
        at initialization. This allows updating criteria without restarting.

        Returns:
            List of changed criteria names (added, removed, or modified)

        Raises:
            ValueError: If no config_path was specified at initialization
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid

        Example:
            filter_svc = KillSwitchFilter(config_path=Path("config/kill_switch.csv"))
            # ... later, after config file is modified ...
            changed = filter_svc.reload_config()
            print(f"Changed criteria: {changed}")
        """
        if self._config_path is None:
            raise ValueError("Cannot reload - no config_path specified at initialization")

        old_config = self._get_config_snapshot()
        self._kill_switches = self._load_from_config(self._config_path)
        new_config = self._get_config_snapshot()

        # Detect changes
        changed = self._detect_config_changes(old_config, new_config)
        if changed:
            logger.info("Config reloaded. Changed criteria: %s", changed)
        else:
            logger.debug("Config reloaded. No changes detected.")

        return changed

    def _get_config_snapshot(self) -> dict[str, dict]:
        """Get current configuration as a snapshot dict.

        Returns:
            Dict mapping criterion name to its attributes
        """
        return {
            ks.name: {
                "is_hard": ks.is_hard,
                "severity_weight": ks.severity_weight,
                "description": ks.description,
            }
            for ks in self._kill_switches
        }

    def _detect_config_changes(
        self, old_config: dict[str, dict], new_config: dict[str, dict]
    ) -> list[str]:
        """Detect which criteria changed between two configuration snapshots.

        Args:
            old_config: Previous configuration snapshot
            new_config: New configuration snapshot

        Returns:
            List of criteria names that were added, removed, or modified
        """
        changed: list[str] = []
        old_names = set(old_config.keys())
        new_names = set(new_config.keys())

        # Added criteria
        added = new_names - old_names
        changed.extend(sorted(added))

        # Removed criteria
        removed = old_names - new_names
        changed.extend(sorted(removed))

        # Modified criteria (present in both, but different)
        common = old_names & new_names
        for name in sorted(common):
            if old_config[name] != new_config[name]:
                changed.append(name)

        return changed

    def check_for_config_changes(self) -> bool:
        """Check if configuration file has changed since last load.

        Only works when a ConfigWatcher is active (enable_hot_reload=True).

        Returns:
            True if config file changed, False otherwise
        """
        if self._config_watcher is None:
            return False
        return self._config_watcher.check_for_changes()

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

    def evaluate_soft_severity(self, property: "Property") -> "SoftSeverityResult":
        """Evaluate SOFT criteria only and return detailed severity result.

        Uses the dedicated SoftSeverityEvaluator to provide detailed breakdown
        of SOFT criteria evaluation. Note: This evaluates SOFT criteria ONLY.
        For complete evaluation including HARD criteria, use evaluate_with_severity().

        Args:
            property: Property entity to evaluate

        Returns:
            SoftSeverityResult with total_severity, verdict, breakdown dict
        """

        soft_results: list[CriterionResult] = []
        for kill_switch in self._kill_switches:
            if kill_switch.is_hard:
                continue
            passed = kill_switch.check(property)
            cr = CriterionResult(
                name=kill_switch.name,
                passed=passed,
                is_hard=False,
                severity=0.0 if passed else kill_switch.severity_weight,
                message=kill_switch.failure_message(property) if not passed else "",
            )
            soft_results.append(cr)
        return self._soft_evaluator.evaluate(soft_results)

    def get_soft_evaluator(self) -> "SoftSeverityEvaluator":
        """Get the SOFT severity evaluator instance."""

        return self._soft_evaluator

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

    def evaluate_to_result(self, property: "Property") -> "KillSwitchResult":
        """Evaluate property and return comprehensive KillSwitchResult.

        Args:
            property: Property entity to evaluate

        Returns:
            KillSwitchResult with verdict, failed_criteria, severity_score,
            timestamp, and property_address
        """
        from datetime import datetime, timezone

        from .result import FailedCriterion, KillSwitchResult

        failed_criteria: list[FailedCriterion] = []
        has_hard_failure: bool = False
        severity_score: float = 0.0

        for kill_switch in self._kill_switches:
            passed = kill_switch.check(property)
            if not passed:
                actual_value = self._get_actual_value(kill_switch.name, property)
                required_value = self._get_required_value(kill_switch.name)
                fc = FailedCriterion(
                    name=kill_switch.name,
                    actual_value=actual_value,
                    required_value=required_value,
                    is_hard=kill_switch.is_hard,
                    severity=0.0 if kill_switch.is_hard else kill_switch.severity_weight,
                )
                failed_criteria.append(fc)
                if kill_switch.is_hard:
                    has_hard_failure = True
                else:
                    severity_score += kill_switch.severity_weight

        verdict = self._calculate_verdict(has_hard_failure, severity_score)
        address_obj = getattr(property, "address", None)
        address = str(address_obj) if address_obj else ""

        return KillSwitchResult(
            verdict=verdict,
            failed_criteria=failed_criteria,
            severity_score=severity_score,
            timestamp=datetime.now(timezone.utc),
            property_address=address,
        )

    def _get_actual_value(self, name: str, property: "Property") -> str | int | float | None:
        """Extract actual value from property for a criterion."""
        mapping = {
            "no_hoa": getattr(property, "hoa_fee", None),
            "min_bedrooms": getattr(property, "beds", None),
            "min_bathrooms": getattr(property, "baths", None),
            "min_sqft": getattr(property, "sqft", None),
            "no_solar_lease": getattr(property, "solar_status", None),
            "city_sewer": getattr(property, "sewer_type", None),
            "min_garage": getattr(property, "garage_spaces", None),
            "lot_size": getattr(property, "lot_sqft", None),
            "no_new_build": getattr(property, "year_built", None),
        }
        value = mapping.get(name)
        # Safely extract .value from enum-like objects
        if value is not None and hasattr(value, "value"):
            enum_value: str | int | float | None = getattr(value, "value", None)
            return enum_value
        return value

    def _get_required_value(self, name: str) -> str:
        """Get human-readable required value for a criterion."""
        mapping = {
            "no_hoa": "$0 (no HOA allowed)",
            "min_bedrooms": "4+ bedrooms",
            "min_bathrooms": "2+ bathrooms",
            "min_sqft": ">1800 sqft",
            "no_solar_lease": "no solar lease",
            "city_sewer": "city sewer",
            "min_garage": "2+ indoor garage spaces",
            "lot_size": "7000-15000 sqft",
            "no_new_build": "built 2023 or earlier",
        }
        return mapping.get(name, name)

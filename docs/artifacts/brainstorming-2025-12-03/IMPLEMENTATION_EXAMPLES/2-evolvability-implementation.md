# 2. EVOLVABILITY IMPLEMENTATION

### 2.1 Extract Kill-Switch Criteria to JSON

#### File: data/buyer_profile.json

```json
{
  "$schema": "buyer_profile_v1",
  "version": "1.0.0",
  "created_at": "2025-12-03",
  "created_by": "andrew@example.com",
  "description": "First-time home buyer profile for Phoenix metro (Dec 2025)",

  "hard_criteria": [
    {
      "id": "no_hoa",
      "name": "No HOA Fees",
      "field": "hoa_fee",
      "operator": "==",
      "threshold": 0,
      "fail_severity": "INSTANT",
      "reason": "HOA fees add to monthly costs and restrict customization"
    },
    {
      "id": "min_bedrooms",
      "name": "Minimum 4 Bedrooms",
      "field": "beds",
      "operator": ">=",
      "threshold": 4,
      "fail_severity": "INSTANT",
      "reason": "Need space for growing family"
    },
    {
      "id": "min_bathrooms",
      "name": "Minimum 2 Bathrooms",
      "field": "baths",
      "operator": ">=",
      "threshold": 2,
      "fail_severity": "INSTANT",
      "reason": "Essential convenience for family living"
    }
  ],

  "soft_criteria": [
    {
      "id": "city_sewer",
      "name": "City Sewer Required",
      "field": "sewer_type",
      "operator": "==",
      "threshold": "city",
      "severity_weight": 2.5,
      "reason": "Septic systems require maintenance and inspection; city sewer more reliable"
    },
    {
      "id": "year_built",
      "name": "Pre-2024 Construction",
      "field": "year_built",
      "operator": "<",
      "threshold": 2024,
      "severity_weight": 2.0,
      "reason": "Avoid new build complications; established neighborhoods preferred"
    },
    {
      "id": "garage_spaces",
      "name": "Minimum 2-Car Garage",
      "field": "garage_spaces",
      "operator": ">=",
      "threshold": 2,
      "severity_weight": 1.5,
      "reason": "Convenience for family; protection from Arizona heat"
    },
    {
      "id": "lot_size",
      "name": "Lot Size 7,000-15,000 sqft",
      "field": "lot_sqft",
      "operator": "between",
      "threshold": {"min": 7000, "max": 15000},
      "severity_weight": 1.0,
      "reason": "Sweet spot: not too small (no yard), not too large (maintenance burden)"
    }
  ],

  "severity_thresholds": {
    "fail": 3.0,
    "warning": 1.5,
    "pass": 0.0
  },

  "change_history": [
    {
      "version": "1.0.0",
      "date": "2025-12-03",
      "author": "andrew@example.com",
      "changes": "Initial buyer profile"
    }
  ]
}
```

#### Python Implementation:

```python
# src/phx_home_analysis/services/kill_switch/buyer_profile.py

from dataclasses import dataclass
from enum import Enum
from typing import Any
import json
from pathlib import Path


class Operator(str, Enum):
    """Comparison operators for criteria."""
    EQ = "=="
    NE = "!="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    BETWEEN = "between"


@dataclass
class HardCriterion:
    """A hard kill-switch criterion."""
    id: str
    name: str
    field: str
    operator: Operator
    threshold: Any
    reason: str

    def evaluate(self, value: Any) -> bool:
        """Check if value meets criterion."""
        if self.operator == Operator.EQ:
            return value == self.threshold
        elif self.operator == Operator.NE:
            return value != self.threshold
        elif self.operator == Operator.LT:
            return value < self.threshold
        elif self.operator == Operator.LTE:
            return value <= self.threshold
        elif self.operator == Operator.GT:
            return value > self.threshold
        elif self.operator == Operator.GTE:
            return value >= self.threshold
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


@dataclass
class SoftCriterion:
    """A soft kill-switch criterion with severity weighting."""
    id: str
    name: str
    field: str
    operator: Operator
    threshold: Any
    severity_weight: float
    reason: str

    def evaluate(self, value: Any) -> bool:
        """Check if value meets criterion."""
        # Same logic as HardCriterion.evaluate()
        ...

    def get_severity_if_failed(self, value: Any) -> float:
        """Return severity weight if criterion fails, 0 if passes."""
        if self.evaluate(value):
            return 0.0
        return self.severity_weight


@dataclass
class BuyerProfile:
    """Complete buyer profile with criteria."""
    version: str
    hard_criteria: list[HardCriterion]
    soft_criteria: list[SoftCriterion]
    severity_thresholds: dict[str, float]

    @property
    def fail_threshold(self) -> float:
        return self.severity_thresholds.get("fail", 3.0)

    @property
    def warning_threshold(self) -> float:
        return self.severity_thresholds.get("warning", 1.5)

    @staticmethod
    def load_from_file(filepath: Path) -> "BuyerProfile":
        """Load buyer profile from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        hard_criteria = [
            HardCriterion(
                id=h["id"],
                name=h["name"],
                field=h["field"],
                operator=Operator(h["operator"]),
                threshold=h["threshold"],
                reason=h["reason"]
            )
            for h in data.get("hard_criteria", [])
        ]

        soft_criteria = [
            SoftCriterion(
                id=s["id"],
                name=s["name"],
                field=s["field"],
                operator=Operator(s["operator"]),
                threshold=s["threshold"],
                severity_weight=s["severity_weight"],
                reason=s["reason"]
            )
            for s in data.get("soft_criteria", [])
        ]

        return BuyerProfile(
            version=data["version"],
            hard_criteria=hard_criteria,
            soft_criteria=soft_criteria,
            severity_thresholds=data.get("severity_thresholds", {})
        )


# Modified KillSwitchFilter to use BuyerProfile
class ConfigurableKillSwitchFilter:
    """Kill-switch filter using external buyer profile."""

    def __init__(self, buyer_profile_path: Path = None):
        if buyer_profile_path is None:
            buyer_profile_path = Path("data/buyer_profile.json")

        self.buyer_profile = BuyerProfile.load_from_file(buyer_profile_path)

    def evaluate(self, property: Property) -> tuple[str, float, list[str]]:
        """
        Evaluate property against buyer profile.

        Returns:
            (verdict, severity_total, failures)
            verdict: "PASS", "WARNING", or "FAIL"
            severity_total: accumulated severity from soft criteria
            failures: list of failed criteria IDs
        """
        failures = []

        # Check hard criteria
        for criterion in self.buyer_profile.hard_criteria:
            value = getattr(property, criterion.field, None)
            if value is None:
                continue

            if not criterion.evaluate(value):
                failures.append(f"{criterion.id}: {criterion.name}")
                return "FAIL", 0.0, failures  # Instant fail

        # Accumulate severity from soft criteria
        severity_total = 0.0
        soft_failures = []

        for criterion in self.buyer_profile.soft_criteria:
            value = getattr(property, criterion.field, None)
            if value is None:
                continue

            severity = criterion.get_severity_if_failed(value)
            if severity > 0:
                severity_total += severity
                soft_failures.append(f"{criterion.id}: {criterion.name} (severity {severity})")

        failures.extend(soft_failures)

        # Determine verdict based on severity thresholds
        if severity_total >= self.buyer_profile.fail_threshold:
            return "FAIL", severity_total, failures
        elif severity_total >= self.buyer_profile.warning_threshold:
            return "WARNING", severity_total, failures
        else:
            return "PASS", severity_total, []
```

### 2.2 Create Phase Configuration

#### File: data/phase_configuration.json

```json
{
  "$schema": "phase_configuration_v1",
  "version": "1.0.0",
  "phases": {
    "phase0_county": {
      "id": "phase0_county",
      "display_name": "County Data Extraction",
      "description": "Extract property data from Maricopa County Assessor API",
      "executor": "script",
      "executor_path": "scripts/extract_county_data.py",
      "dependencies": [],
      "timeout_seconds": 120,
      "retryable": true,
      "max_retries": 3,
      "backoff_factor": 2.0
    },
    "phase1_listing": {
      "id": "phase1_listing",
      "display_name": "Image Extraction",
      "description": "Extract property photos from Zillow/Redfin/Realtor.com",
      "executor": "agent",
      "executor_path": ".claude/agents/listing-browser.md",
      "executor_model": "haiku",
      "dependencies": [],
      "timeout_seconds": 600,
      "retryable": true,
      "max_retries": 2
    },
    "phase1_map": {
      "id": "phase1_map",
      "display_name": "Geographic Analysis",
      "description": "Analyze school ratings, safety scores, orientation, distances",
      "executor": "agent",
      "executor_path": ".claude/agents/map-analyzer.md",
      "executor_model": "haiku",
      "dependencies": [],
      "timeout_seconds": 300,
      "retryable": true,
      "max_retries": 2
    },
    "phase2_images": {
      "id": "phase2_images",
      "display_name": "Interior Assessment",
      "description": "Assess interior and exterior condition, score Section C",
      "executor": "agent",
      "executor_path": ".claude/agents/image-assessor.md",
      "executor_model": "sonnet",
      "dependencies": ["phase1_listing"],
      "timeout_seconds": 900,
      "retryable": false,
      "prerequisite_validation": "validate_phase_prerequisites.py"
    },
    "phase3_synthesis": {
      "id": "phase3_synthesis",
      "display_name": "Scoring & Classification",
      "description": "Score properties and classify tiers",
      "executor": "script",
      "executor_path": "scripts/phx_home_analyzer.py",
      "dependencies": ["phase0_county", "phase1_listing", "phase1_map", "phase2_images"],
      "timeout_seconds": 120,
      "retryable": true,
      "max_retries": 3
    },
    "phase4_report": {
      "id": "phase4_report",
      "display_name": "Report Generation",
      "description": "Generate deal sheets and visualizations",
      "executor": "script",
      "executor_path": "scripts/generate_all_reports.py",
      "dependencies": ["phase3_synthesis"],
      "timeout_seconds": 300,
      "retryable": true,
      "max_retries": 2
    }
  },
  "execution_order": [
    ["phase0_county"],
    ["phase1_listing", "phase1_map"],
    ["phase2_images"],
    ["phase3_synthesis"],
    ["phase4_report"]
  ]
}
```

#### Python Implementation:

```python
# src/phx_home_analysis/pipeline/phase_dag.py

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json


class ExecutorType(str, Enum):
    SCRIPT = "script"
    AGENT = "agent"
    MANUAL = "manual"


@dataclass
class Phase:
    """Definition of a pipeline phase."""
    id: str
    display_name: str
    description: str
    executor_type: ExecutorType
    executor_path: str
    dependencies: list[str]
    timeout_seconds: int
    retryable: bool
    max_retries: int = 1
    backoff_factor: float = 1.0
    executor_model: str | None = None
    prerequisite_validation: str | None = None

    def is_blocked_by(self, completed_phases: set[str]) -> bool:
        """Check if this phase can run given completed phases."""
        for dep in self.dependencies:
            if dep not in completed_phases:
                return True
        return False


@dataclass
class PhaseDAG:
    """Directed acyclic graph of phases."""
    version: str
    phases: dict[str, Phase]
    execution_order: list[list[str]]  # Groups for parallel execution

    @staticmethod
    def load_from_file(filepath: Path) -> "PhaseDAG":
        """Load phase configuration from JSON."""
        with open(filepath) as f:
            data = json.load(f)

        phases = {}
        for phase_id, phase_data in data["phases"].items():
            phases[phase_id] = Phase(
                id=phase_data["id"],
                display_name=phase_data["display_name"],
                description=phase_data["description"],
                executor_type=ExecutorType(phase_data["executor"]),
                executor_path=phase_data["executor_path"],
                dependencies=phase_data.get("dependencies", []),
                timeout_seconds=phase_data["timeout_seconds"],
                retryable=phase_data["retryable"],
                max_retries=phase_data.get("max_retries", 1),
                backoff_factor=phase_data.get("backoff_factor", 1.0),
                executor_model=phase_data.get("executor_model"),
                prerequisite_validation=phase_data.get("prerequisite_validation")
            )

        return PhaseDAG(
            version=data["version"],
            phases=phases,
            execution_order=data["execution_order"]
        )

    def get_phase(self, phase_id: str) -> Phase:
        """Get phase by ID."""
        return self.phases[phase_id]

    def is_valid_dag(self) -> tuple[bool, list[str]]:
        """Check if DAG is valid (no cycles, all deps exist)."""
        errors = []

        # Check all dependencies exist
        for phase_id, phase in self.phases.items():
            for dep in phase.dependencies:
                if dep not in self.phases:
                    errors.append(f"Phase {phase_id} depends on non-existent phase {dep}")

        # Check no cycles (simple DFS)
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in self.phases[node].dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for phase_id in self.phases:
            if phase_id not in visited:
                if has_cycle(phase_id):
                    errors.append(f"Cycle detected involving {phase_id}")

        return len(errors) == 0, errors
```

---

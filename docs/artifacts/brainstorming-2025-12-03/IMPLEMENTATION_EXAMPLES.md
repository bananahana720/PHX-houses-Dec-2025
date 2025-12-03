# Implementation Examples for Cross-Cutting Concerns
## PHX Houses Analysis Pipeline

**Purpose**: Concrete code examples for implementing the recommended architectural improvements.

---

## 1. TRACEABILITY IMPLEMENTATION

### 1.1 Add Field-Level Metadata to enrichment_data.json

#### Before (Current):
```json
{
  "full_address": "123 Main St",
  "lot_sqft": 9387,
  "year_built": 1983,
  "_last_updated": "2025-12-03T03:24:41"
}
```

#### After (With Provenance):
```json
{
  "_schema_version": "2.0.0",
  "full_address": "123 Main St",
  "lot_sqft": {
    "value": 9387,
    "source": "maricopa_assessor_api",
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py",
    "lineage_id": "phase0_county_run_20251203_abc123"
  },
  "year_built": {
    "value": 1983,
    "source": "maricopa_assessor_api",
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py"
  },
  "orientation": {
    "value": "south",
    "source": "satellite_visual_estimate",
    "phase": "phase1_map",
    "confidence": 0.65,
    "extracted_at": "2025-12-03T05:30:00",
    "validated_by": "map-analyzer",
    "notes": "Medium confidence - satellite imagery only"
  },
  "_metadata": {
    "last_modified": "2025-12-03T05:30:00",
    "last_modified_by": "map-analyzer",
    "modification_count": 3,
    "lineage_chain": [
      "phase0_county_run_20251203_abc123",
      "phase1_map_run_20251203_def456"
    ]
  }
}
```

#### Python Implementation:

```python
# src/phx_home_analysis/domain/value_objects.py

@dataclass
class FieldMetadata:
    """Metadata for a single enriched field."""
    value: Any
    source: str  # "maricopa_assessor_api", "zillow_scrape", "satellite_visual", "manual"
    phase: str   # "phase0_county", "phase1_map", "phase2_images", etc.
    confidence: float  # 0.0 - 1.0
    extracted_at: datetime
    validated_by: str  # Script name or agent name
    notes: str | None = None
    lineage_id: str | None = None  # Link to extraction run

    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.80

    def is_medium_confidence(self) -> bool:
        return 0.60 <= self.confidence < 0.80

    def is_low_confidence(self) -> bool:
        return self.confidence < 0.60

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "source": self.source,
            "phase": self.phase,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "validated_by": self.validated_by,
            "notes": self.notes,
            "lineage_id": self.lineage_id
        }


# Enhanced EnrichmentData class
@dataclass
class EnrichmentDataWithMetadata:
    """Property enrichment with field-level provenance tracking."""
    full_address: str

    # Instead of: lot_sqft: int | None
    # Do: lot_sqft: FieldMetadata | int | None (backward compatible)

    _fields_metadata: dict[str, FieldMetadata] = field(default_factory=dict)
    _last_modified: datetime | None = None
    _last_modified_by: str | None = None

    def set_field_with_metadata(
        self,
        field_name: str,
        value: Any,
        source: str,
        phase: str,
        confidence: float,
        validated_by: str,
        notes: str | None = None
    ) -> None:
        """Set a field with full provenance metadata."""
        metadata = FieldMetadata(
            value=value,
            source=source,
            phase=phase,
            confidence=confidence,
            extracted_at=datetime.now(timezone.utc),
            validated_by=validated_by,
            notes=notes
        )
        self._fields_metadata[field_name] = metadata
        setattr(self, field_name, value)
        self._last_modified = datetime.now(timezone.utc)
        self._last_modified_by = validated_by

    def get_field_metadata(self, field_name: str) -> FieldMetadata | None:
        """Retrieve metadata for a field."""
        return self._fields_metadata.get(field_name)

    def get_high_confidence_fields(self) -> list[str]:
        """List all fields with high confidence."""
        return [
            field for field, metadata in self._fields_metadata.items()
            if metadata.is_high_confidence()
        ]

    def to_dict_with_metadata(self) -> dict:
        """Serialize including metadata."""
        result = {"_schema_version": "2.0.0", "full_address": self.full_address}

        # Add each field with metadata
        for field_name, metadata in self._fields_metadata.items():
            result[field_name] = metadata.to_dict()

        # Add fields without explicit metadata (backward compatibility)
        for field_name in self.__dataclass_fields__:
            if field_name not in result and field_name != "_fields_metadata":
                value = getattr(self, field_name, None)
                if value is not None:
                    result[field_name] = value

        result["_metadata"] = {
            "last_modified": self._last_modified.isoformat() if self._last_modified else None,
            "last_modified_by": self._last_modified_by
        }
        return result
```

### 1.2 Create Scoring Lineage Capture

```python
# src/phx_home_analysis/services/scoring/lineage.py

@dataclass
class ScoringStrategyResult:
    """Result from a single scoring strategy."""
    strategy_name: str
    phase: str
    points_awarded: float
    max_possible: float
    input_fields: dict[str, Any]
    reasoning: str
    notes: str | None = None

    @property
    def percent_of_max(self) -> float:
        return (self.points_awarded / self.max_possible * 100) if self.max_possible > 0 else 0


@dataclass
class SectionScoringLineage:
    """Scoring lineage for one section (Location, Systems, Interior)."""
    section_name: str
    total_points: float
    max_possible: float
    strategies: list[ScoringStrategyResult]

    def to_dict(self) -> dict:
        return {
            "section": self.section_name,
            "total": self.total_points,
            "max_possible": self.max_possible,
            "percentage": self.total_points / self.max_possible * 100,
            "strategies": [
                {
                    "name": s.strategy_name,
                    "phase": s.phase,
                    "points": s.points_awarded,
                    "max": s.max_possible,
                    "percent": s.percent_of_max,
                    "reasoning": s.reasoning,
                    "inputs": s.input_fields,
                    "notes": s.notes
                }
                for s in self.strategies
            ]
        }


@dataclass
class CompleteScoringLineage:
    """Complete scoring lineage for a property."""
    property_address: str
    scoring_run_id: str
    scored_at: datetime
    sections: list[SectionScoringLineage]
    total_score: float
    max_possible: float
    tier: str

    def to_dict(self) -> dict:
        return {
            "address": self.property_address,
            "run_id": self.scoring_run_id,
            "scored_at": self.scored_at.isoformat(),
            "sections": [s.to_dict() for s in self.sections],
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "tier": self.tier
        }


# Modified PropertyScorer to capture lineage
class ExplainablePropertyScorer(PropertyScorer):
    """PropertyScorer that tracks scoring lineage."""

    def score(self, property: Property) -> tuple[float, CompleteScoringLineage]:
        """Score property and return lineage explaining the score."""
        import uuid
        from datetime import datetime, timezone

        run_id = str(uuid.uuid4())
        sections_lineage = []

        # Score each section
        location_lineage = self._score_section_location(property, run_id)
        systems_lineage = self._score_section_systems(property, run_id)
        interior_lineage = self._score_section_interior(property, run_id)

        sections_lineage = [location_lineage, systems_lineage, interior_lineage]

        total_score = sum(s.total_points for s in sections_lineage)
        tier = TierClassifier().classify(total_score)

        lineage = CompleteScoringLineage(
            property_address=property.full_address,
            scoring_run_id=run_id,
            scored_at=datetime.now(timezone.utc),
            sections=sections_lineage,
            total_score=total_score,
            max_possible=600,
            tier=tier.value
        )

        # Store lineage on property for persistence
        property.scoring_lineage = lineage

        return total_score, lineage

    def _score_section_location(self, property: Property, run_id: str) -> SectionScoringLineage:
        """Score location section with detailed lineage."""
        strategies_lineage = []
        total = 0.0

        # School district strategy
        school_score = SchoolDistrictScorer().score(property)
        school_result = ScoringStrategyResult(
            strategy_name="SchoolDistrictScorer",
            phase="phase1_map",
            points_awarded=school_score,
            max_possible=45,
            input_fields={"school_rating": property.school_rating},
            reasoning=f"GreatSchools {property.school_rating}/10 → {school_score}/45 points",
        )
        strategies_lineage.append(school_result)
        total += school_score

        # Safety strategy
        safety_score = CrimeIndexScorer().score(property)
        safety_result = ScoringStrategyResult(
            strategy_name="CrimeIndexScorer",
            phase="phase1_map",
            points_awarded=safety_score,
            max_possible=50,
            input_fields={
                "violent_crime_index": property.violent_crime_index,
                "property_crime_index": property.property_crime_index
            },
            reasoning=f"Crime index (60% violent + 40% property) → {safety_score}/50 points"
        )
        strategies_lineage.append(safety_result)
        total += safety_score

        # ... repeat for all location strategies ...

        return SectionScoringLineage(
            section_name="Location & Environment",
            total_points=total,
            max_possible=230,
            strategies=strategies_lineage
        )
```

---

## 2. EVOLVABILITY IMPLEMENTATION

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

## 3. EXPLAINABILITY IMPLEMENTATION

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

## 4. AUTONOMY IMPLEMENTATION

### 4.1 Parallel Property Processing

```python
# src/phx_home_analysis/pipeline/parallel_orchestrator.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging


@dataclass
class PropertyProcessingResult:
    """Result of processing a single property."""
    address: str
    status: str  # "completed", "failed", "blocked"
    phases_completed: list[str]
    phases_failed: list[str]
    error_message: str | None = None
    duration_seconds: float = 0.0


class ParallelPropertyOrchestrator:
    """Process multiple properties in parallel with dependency awareness."""

    def __init__(
        self,
        phase_dag: PhaseDAG,
        max_parallel_properties: int = 3,
        max_parallel_phases: int = 2
    ):
        self.phase_dag = phase_dag
        self.max_parallel_properties = max_parallel_properties
        self.max_parallel_phases = max_parallel_phases
        self.logger = logging.getLogger(__name__)

    def process_all_properties(
        self,
        properties: list[Property]
    ) -> list[PropertyProcessingResult]:
        """Process all properties in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_parallel_properties) as executor:
            futures = {
                executor.submit(self.process_single_property, prop): prop
                for prop in properties
            }

            for future in as_completed(futures):
                prop = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(
                        f"Property {prop.full_address}: {result.status} "
                        f"({result.duration_seconds:.2f}s)"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Processing {prop.full_address} failed: {e}",
                        exc_info=True
                    )
                    results.append(PropertyProcessingResult(
                        address=prop.full_address,
                        status="failed",
                        phases_completed=[],
                        phases_failed=[],
                        error_message=str(e)
                    ))

        return results

    def process_single_property(self, property: Property) -> PropertyProcessingResult:
        """Process a single property through all phases."""
        import time
        start_time = time.time()

        phases_completed = []
        phases_failed = []
        work_item = WorkItem(address=property.full_address)

        # Process phases in order
        for phase_group in self.phase_dag.execution_order:
            # Check if all dependencies are met
            completed_set = set(phases_completed)

            # Execute phases in group in parallel (if applicable)
            with ThreadPoolExecutor(max_workers=self.max_parallel_phases) as executor:
                futures = {}

                for phase_id in phase_group:
                    phase = self.phase_dag.get_phase(phase_id)

                    # Check if phase is blocked
                    if phase.is_blocked_by(completed_set):
                        self.logger.debug(f"{phase_id}: blocked by dependencies")
                        continue

                    # Check if phase was already completed
                    if work_item.is_phase_completed(phase_id):
                        self.logger.debug(f"{phase_id}: already completed (resuming)")
                        phases_completed.append(phase_id)
                        continue

                    # Submit phase execution
                    future = executor.submit(
                        self._execute_phase,
                        property,
                        phase,
                        work_item
                    )
                    futures[future] = phase_id

                # Wait for parallel phases to complete
                for future in as_completed(futures):
                    phase_id = futures[future]
                    try:
                        success = future.result()
                        if success:
                            phases_completed.append(phase_id)
                            work_item.mark_phase_completed(phase_id)
                        else:
                            phases_failed.append(phase_id)
                    except Exception as e:
                        self.logger.error(f"{phase_id} failed: {e}")
                        phases_failed.append(phase_id)

        duration = time.time() - start_time
        status = "completed" if not phases_failed else "failed"

        return PropertyProcessingResult(
            address=property.full_address,
            status=status,
            phases_completed=phases_completed,
            phases_failed=phases_failed,
            duration_seconds=duration
        )

    def _execute_phase(
        self,
        property: Property,
        phase: Phase,
        work_item: WorkItem
    ) -> bool:
        """Execute a single phase for a property."""
        import time

        max_attempts = phase.max_retries
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                # Validate prerequisites if needed
                if phase.prerequisite_validation:
                    can_spawn = self._validate_prerequisites(
                        property,
                        phase.prerequisite_validation
                    )
                    if not can_spawn:
                        self.logger.warning(
                            f"{phase.id}: prerequisites not met for {property.full_address}"
                        )
                        work_item.mark_phase_skipped(phase.id)
                        return False

                # Execute phase
                self.logger.info(f"Starting {phase.id} for {property.full_address}")

                if phase.executor_type == ExecutorType.SCRIPT:
                    self._execute_script_phase(property, phase)
                elif phase.executor_type == ExecutorType.AGENT:
                    self._execute_agent_phase(property, phase)

                self.logger.info(f"Completed {phase.id} for {property.full_address}")
                return True

            except Exception as e:
                attempt += 1
                last_error = e

                if attempt < max_attempts and phase.retryable:
                    wait_time = phase.backoff_factor ** (attempt - 1)
                    self.logger.warning(
                        f"{phase.id} attempt {attempt} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"{phase.id} failed after {attempt} attempts: {e}"
                    )

        return False

    def _validate_prerequisites(
        self,
        property: Property,
        validation_script: str
    ) -> bool:
        """Validate phase prerequisites."""
        # Implement by calling validate_phase_prerequisites.py
        pass

    def _execute_script_phase(self, property: Property, phase: Phase) -> None:
        """Execute a script-based phase."""
        # Implement by running Python script
        pass

    def _execute_agent_phase(self, property: Property, phase: Phase) -> None:
        """Execute an agent-based phase."""
        # Implement by spawning Task with agent
        pass
```

---

## Summary

These implementation examples show:

1. **Traceability**: Field metadata and scoring lineage capture
2. **Evolvability**: Configuration files instead of hard-coded constants
3. **Explainability**: Detailed verdict explanations with reasoning
4. **Autonomy**: Parallel processing with retry logic

Each can be implemented incrementally without breaking existing functionality.


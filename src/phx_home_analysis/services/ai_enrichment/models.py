"""Data models for AI-assisted field inference and triage.

This module defines the core data structures used for tracking field inference
results, confidence levels, and overall triage outcomes. These models support
the AI enrichment pipeline that attempts to fill in missing property data.

Confidence Levels:
- HIGH (>=0.8): Very reliable inference, can be used without manual verification
- MEDIUM (0.5-0.8): Moderately reliable, may need spot-checking
- LOW (<0.5): Unreliable, should be verified manually or flagged for AI inference

Sources:
- web_scrape: Data obtained from Zillow, Redfin, or other listing sites
- assessor_api: Data from Maricopa County Assessor API
- ai_inference: Data inferred by Claude AI based on available context
- ai_pending: Field tagged for AI inference but not yet processed
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...config.constants import CONFIDENCE_HIGH_THRESHOLD


class ConfidenceLevel(Enum):
    """Confidence level categorization for inferred values.

    Thresholds (defined in config.constants):
    - HIGH: score >= CONFIDENCE_HIGH_THRESHOLD (0.8)
    - MEDIUM: 0.5 <= score < CONFIDENCE_HIGH_THRESHOLD
    - LOW: score < 0.5
    """

    HIGH = "high"  # >= CONFIDENCE_HIGH_THRESHOLD confidence
    MEDIUM = "medium"  # 0.5 - CONFIDENCE_HIGH_THRESHOLD
    LOW = "low"  # < 0.5

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """Convert a numeric confidence score to a ConfidenceLevel.

        Args:
            score: Confidence score between 0.0 and 1.0

        Returns:
            ConfidenceLevel corresponding to the score

        Examples:
            >>> ConfidenceLevel.from_score(0.9)
            <ConfidenceLevel.HIGH: 'high'>
            >>> ConfidenceLevel.from_score(0.6)
            <ConfidenceLevel.MEDIUM: 'medium'>
            >>> ConfidenceLevel.from_score(0.3)
            <ConfidenceLevel.LOW: 'low'>
        """
        if score >= CONFIDENCE_HIGH_THRESHOLD:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        return cls.LOW


@dataclass
class FieldInference:
    """Result of inferring a single field value.

    Represents the outcome of attempting to infer a missing property field,
    including the inferred value (if any), confidence metrics, and the source
    of the inference.

    Attributes:
        field_name: Name of the field being inferred (e.g., "beds", "lot_sqft")
        inferred_value: The inferred value, or None if inference failed
        confidence: Numeric confidence score between 0.0 and 1.0
        confidence_level: Categorical confidence level (HIGH, MEDIUM, LOW)
        source: Origin of the inference (web_scrape, assessor_api, ai_inference, ai_pending)
        reasoning: Optional explanation of how the value was inferred
    """

    field_name: str
    inferred_value: Any
    confidence: float
    confidence_level: ConfidenceLevel
    source: str  # "web_scrape", "assessor_api", "ai_inference", "ai_pending"
    reasoning: str | None = None

    def __post_init__(self) -> None:
        """Validate field inference data after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

        valid_sources = {"web_scrape", "assessor_api", "ai_inference", "ai_pending", "phoenix_mls"}
        if self.source not in valid_sources:
            raise ValueError(f"Source must be one of {valid_sources}, got {self.source}")

    @property
    def is_resolved(self) -> bool:
        """Check if the field has been successfully resolved.

        Returns:
            True if inferred_value is not None and source is not ai_pending
        """
        return self.inferred_value is not None and self.source != "ai_pending"

    @property
    def needs_ai_inference(self) -> bool:
        """Check if the field needs AI inference.

        Returns:
            True if source is ai_pending
        """
        return self.source == "ai_pending"


@dataclass
class TriageResult:
    """Summary result of triaging all missing fields for a property.

    Aggregates the inference results for all missing fields on a single property,
    providing counts of resolved vs pending fields and the full list of inferences.

    Attributes:
        property_hash: MD5 hash identifier for the property (first 8 chars)
        inferences: List of FieldInference objects for each missing field
        fields_resolved: Count of fields successfully inferred
        fields_pending: Count of fields still awaiting inference
    """

    property_hash: str
    inferences: list[FieldInference] = field(default_factory=list)
    fields_resolved: int = 0
    fields_pending: int = 0

    def __post_init__(self) -> None:
        """Recalculate resolved/pending counts from inferences."""
        if self.inferences:
            self.fields_resolved = sum(1 for inf in self.inferences if inf.is_resolved)
            self.fields_pending = sum(1 for inf in self.inferences if not inf.is_resolved)

    @property
    def total_fields(self) -> int:
        """Total number of fields that were triaged.

        Returns:
            Sum of resolved and pending fields
        """
        return self.fields_resolved + self.fields_pending

    @property
    def resolution_rate(self) -> float:
        """Percentage of fields that were successfully resolved.

        Returns:
            Float between 0.0 and 1.0, or 0.0 if no fields triaged
        """
        if self.total_fields == 0:
            return 0.0
        return self.fields_resolved / self.total_fields

    def get_pending_inferences(self) -> list[FieldInference]:
        """Get all inferences that need AI processing.

        Returns:
            List of FieldInference objects with source="ai_pending"
        """
        return [inf for inf in self.inferences if inf.needs_ai_inference]

    def get_resolved_inferences(self) -> list[FieldInference]:
        """Get all successfully resolved inferences.

        Returns:
            List of FieldInference objects that have been resolved
        """
        return [inf for inf in self.inferences if inf.is_resolved]

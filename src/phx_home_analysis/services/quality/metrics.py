"""Quality metrics calculation for property data.

This module provides the QualityMetricsCalculator class for assessing
data completeness and confidence levels across property records.
"""

import logging
from typing import TYPE_CHECKING, Any

from .models import QualityScore

if TYPE_CHECKING:
    from ...domain import EnrichmentData

logger = logging.getLogger(__name__)


class QualityMetricsCalculator:
    """Calculate quality metrics for property data.

    Assesses data completeness (presence of required fields) and
    confidence levels to produce an overall quality score.

    Quality Formula:
        overall_score = (completeness * 0.6) + (high_confidence_pct * 0.4)

    Where:
        - completeness = present_fields / required_fields
        - high_confidence_pct = fields_above_threshold / total_tracked_fields

    Attributes:
        REQUIRED_FIELDS: List of fields that must be present for full completeness.
        HIGH_CONFIDENCE_THRESHOLD: Minimum confidence to count as "high confidence".
        COMPLETENESS_WEIGHT: Weight for completeness in overall score (0.6).
        CONFIDENCE_WEIGHT: Weight for confidence in overall score (0.4).

    Example:
        calculator = QualityMetricsCalculator()
        score = calculator.calculate(
            property_data={"address": "123 Main St", "beds": 4, ...},
            field_confidences={"address": 0.95, "beds": 0.90, ...}
        )
        print(f"Quality: {score.overall_score:.1%}")  # Quality: 92.0%
    """

    # Required fields for completeness calculation
    # These are kill-switch and essential listing fields
    REQUIRED_FIELDS: list[str] = [
        "address",
        "beds",
        "baths",
        "sqft",
        "price",
        "lot_sqft",
        "year_built",
        "garage_spaces",
        "sewer_type",
    ]

    # Confidence threshold for "high confidence" classification
    HIGH_CONFIDENCE_THRESHOLD: float = 0.8

    # Weights for overall score calculation
    COMPLETENESS_WEIGHT: float = 0.6
    CONFIDENCE_WEIGHT: float = 0.4

    def __init__(
        self,
        required_fields: list[str] | None = None,
        high_confidence_threshold: float | None = None,
    ) -> None:
        """Initialize the calculator with optional custom configuration.

        Args:
            required_fields: Override default required fields list.
            high_confidence_threshold: Override default confidence threshold.
        """
        if required_fields is not None:
            self.required_fields = required_fields
        else:
            self.required_fields = self.REQUIRED_FIELDS.copy()

        if high_confidence_threshold is not None:
            if not 0.0 <= high_confidence_threshold <= 1.0:
                raise ValueError("high_confidence_threshold must be between 0.0 and 1.0")
            self.high_confidence_threshold = high_confidence_threshold
        else:
            self.high_confidence_threshold = self.HIGH_CONFIDENCE_THRESHOLD

    def calculate(
        self,
        property_data: dict[str, Any],
        field_confidences: dict[str, float] | None = None,
    ) -> QualityScore:
        """Calculate quality score for a property.

        Args:
            property_data: Dictionary of property field values.
            field_confidences: Optional dictionary mapping field names
                             to confidence scores (0.0-1.0).

        Returns:
            QualityScore with completeness, confidence, and overall metrics.
        """
        field_confidences = field_confidences or {}

        # Calculate completeness: % of required fields present
        present_fields = []
        missing_fields = []

        for field in self.required_fields:
            value = property_data.get(field)
            if value is not None and value != "":
                present_fields.append(field)
            else:
                missing_fields.append(field)

        completeness = (
            len(present_fields) / len(self.required_fields) if self.required_fields else 1.0
        )

        # Calculate high confidence percentage
        if field_confidences:
            high_conf_fields = [
                f for f, c in field_confidences.items() if c >= self.high_confidence_threshold
            ]
            low_conf_fields = [
                f for f, c in field_confidences.items() if c < self.high_confidence_threshold
            ]
            high_confidence_pct = len(high_conf_fields) / len(field_confidences)
        else:
            # If no confidence data, assume completeness equals confidence
            high_confidence_pct = completeness
            low_conf_fields = []

        # Calculate overall score using weighted formula
        overall_score = (
            completeness * self.COMPLETENESS_WEIGHT + high_confidence_pct * self.CONFIDENCE_WEIGHT
        )

        return QualityScore(
            completeness=completeness,
            high_confidence_pct=high_confidence_pct,
            overall_score=overall_score,
            missing_fields=missing_fields,
            low_confidence_fields=low_conf_fields,
        )

    def calculate_batch(
        self,
        properties: list[dict[str, Any]],
        property_confidences: dict[str, dict[str, float]] | None = None,
    ) -> tuple[list[QualityScore], QualityScore]:
        """Calculate quality scores for multiple properties.

        Args:
            properties: List of property data dictionaries.
            property_confidences: Optional dict mapping property identifiers
                                 to field confidence dictionaries.

        Returns:
            Tuple of (individual scores list, aggregate score).
        """
        property_confidences = property_confidences or {}
        scores = []

        for i, prop_data in enumerate(properties):
            # Use index or address as key for confidence lookup
            prop_key = prop_data.get("address", str(i))
            confidences = property_confidences.get(prop_key, {})
            score = self.calculate(prop_data, confidences)
            scores.append(score)

        # Calculate aggregate score
        if scores:
            avg_completeness = sum(s.completeness for s in scores) / len(scores)
            avg_high_conf = sum(s.high_confidence_pct for s in scores) / len(scores)
            avg_overall = sum(s.overall_score for s in scores) / len(scores)

            # Collect all unique missing and low-confidence fields
            all_missing = set()
            all_low_conf = set()
            for score in scores:
                all_missing.update(score.missing_fields)
                all_low_conf.update(score.low_confidence_fields)

            aggregate = QualityScore(
                completeness=avg_completeness,
                high_confidence_pct=avg_high_conf,
                overall_score=avg_overall,
                missing_fields=sorted(all_missing),
                low_confidence_fields=sorted(all_low_conf),
            )
        else:
            aggregate = QualityScore(
                completeness=0.0,
                high_confidence_pct=0.0,
                overall_score=0.0,
                missing_fields=self.required_fields.copy(),
                low_confidence_fields=[],
            )

        return scores, aggregate

    def meets_threshold(
        self,
        property_data: dict[str, Any],
        field_confidences: dict[str, float] | None = None,
        threshold: float = 0.95,
    ) -> bool:
        """Check if property data meets quality threshold.

        Convenience method for CI/CD quality gates.

        Args:
            property_data: Dictionary of property field values.
            field_confidences: Optional field confidence scores.
            threshold: Quality threshold (default 0.95 for 95%).

        Returns:
            True if overall_score >= threshold.
        """
        score = self.calculate(property_data, field_confidences)
        return score.overall_score >= threshold

    def get_improvement_suggestions(
        self,
        quality_score: QualityScore,
    ) -> list[str]:
        """Generate suggestions for improving data quality.

        Args:
            quality_score: Quality score to analyze.

        Returns:
            List of actionable suggestions.
        """
        suggestions = []

        # Check missing fields
        if quality_score.missing_fields:
            fields_str = ", ".join(quality_score.missing_fields[:3])
            if len(quality_score.missing_fields) > 3:
                fields_str += f" (+{len(quality_score.missing_fields) - 3} more)"
            suggestions.append(f"Add missing required fields: {fields_str}")

        # Check low confidence fields
        if quality_score.low_confidence_fields:
            fields_str = ", ".join(quality_score.low_confidence_fields[:3])
            if len(quality_score.low_confidence_fields) > 3:
                fields_str += f" (+{len(quality_score.low_confidence_fields) - 3} more)"
            suggestions.append(
                f"Verify low-confidence fields with authoritative sources: {fields_str}"
            )

        # Check overall score
        if quality_score.completeness < 0.9:
            suggestions.append(
                f"Improve completeness from {quality_score.completeness:.0%} to 90%+"
            )

        if quality_score.high_confidence_pct < 0.8:
            suggestions.append(
                f"Improve confidence from {quality_score.high_confidence_pct:.0%} to 80%+"
            )

        if not suggestions:
            suggestions.append("Data quality is excellent - no improvements needed")

        return suggestions


def calculate_property_quality(enrichment: "EnrichmentData") -> QualityScore:
    """Calculate quality score for a property from EnrichmentData.

    This is a convenience function that extracts property data and field
    confidences from an EnrichmentData entity and calculates quality metrics.

    Formula:
        overall_score = (completeness * 0.60) + (high_confidence_pct * 0.40)

    Where:
        - completeness = percentage of non-null required fields
        - high_confidence_pct = percentage of fields with confidence >= 0.80

    Args:
        enrichment: EnrichmentData entity with field values and provenance.

    Returns:
        QualityScore with completeness, high_confidence_pct, and overall_score.

    Example:
        >>> enrichment = EnrichmentData(
        ...     full_address="123 Main St",
        ...     lot_sqft=9500,
        ...     year_built=2010,
        ...     garage_spaces=2,
        ... )
        >>> enrichment.set_field_provenance("lot_sqft", "assessor_api", 0.95)
        >>> score = calculate_property_quality(enrichment)
        >>> print(f"Quality: {score.overall_score:.1%}")
    """
    # Extract property data from enrichment fields
    property_data = {
        "address": enrichment.full_address,
        "beds": None,  # Not in EnrichmentData
        "baths": None,  # Not in EnrichmentData
        "sqft": None,  # Not in EnrichmentData
        "price": None,  # Not in EnrichmentData
        "lot_sqft": enrichment.lot_sqft,
        "year_built": enrichment.year_built,
        "garage_spaces": enrichment.garage_spaces,
        "sewer_type": enrichment.sewer_type,
    }

    # Extract field confidences from provenance data
    field_confidences = {}
    for field_name, provenance in enrichment._provenance.items():
        field_confidences[field_name] = provenance.confidence

    # Use the calculator to compute quality score
    calculator = QualityMetricsCalculator()
    return calculator.calculate(
        property_data=property_data,
        field_confidences=field_confidences,
    )

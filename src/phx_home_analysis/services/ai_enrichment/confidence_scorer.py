"""Confidence scoring for field inferences.

This module calculates confidence scores for inferred property field values,
taking into account both the inherent reliability of different field types
and the reliability of the data source.

Field Confidence Weights:
- Higher weights for fields with more reliable data sources
- Lower weights for fields that are harder to verify accurately

Source Reliability:
- Assessor API: Very high (government data)
- Web Scraping: High for basic listing data
- AI Inference: Variable based on context available
"""

import logging

from ...config.constants import (
    CONFIDENCE_HIGH_THRESHOLD,
    DATA_CONFIDENCE_ASSESSOR_API,
    DATA_CONFIDENCE_MANUAL,
    DATA_CONFIDENCE_WEB_SCRAPE,
    FIELD_CONFIDENCE_HAS_POOL,
    FIELD_CONFIDENCE_LOT_SQFT,
    FIELD_CONFIDENCE_ORIENTATION,
    FIELD_CONFIDENCE_SQFT,
    FIELD_CONFIDENCE_YEAR_BUILT,
)
from .models import ConfidenceLevel, FieldInference

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Calculate and adjust confidence scores for field inferences.

    Uses field-specific weights and source reliability factors to
    produce accurate confidence scores that reflect the trustworthiness
    of inferred values.

    Attributes:
        FIELD_CONFIDENCE_WEIGHTS: Base confidence weights per field
        SOURCE_RELIABILITY: Reliability multipliers per source type

    Example:
        >>> scorer = ConfidenceScorer()
        >>> inference = FieldInference(
        ...     field_name="lot_sqft",
        ...     inferred_value=9500,
        ...     confidence=0.95,
        ...     confidence_level=ConfidenceLevel.HIGH,
        ...     source="assessor_api"
        ... )
        >>> final_score = scorer.score_inference(inference)
        >>> final_score > 0.9
        True
    """

    # Base confidence weights for each field type
    # Reflects how accurately each field can typically be inferred
    # See config.constants for documentation on field weights
    FIELD_CONFIDENCE_WEIGHTS: dict[str, float] = {
        "beds": 0.9,  # Usually accurate from listings
        "baths": 0.9,  # Usually accurate from listings
        "sqft": FIELD_CONFIDENCE_SQFT,  # Sometimes varies between sources
        "lot_sqft": FIELD_CONFIDENCE_LOT_SQFT,  # Very accurate from assessor
        "year_built": FIELD_CONFIDENCE_YEAR_BUILT,  # Very accurate from assessor
        "garage_spaces": 0.7,  # Can be ambiguous (carport vs garage)
        "sewer_type": 0.6,  # Often needs manual verification
        "has_pool": FIELD_CONFIDENCE_HAS_POOL,  # Usually visible in photos/listings
        "orientation": FIELD_CONFIDENCE_ORIENTATION,  # Satellite imagery + manual
    }

    # Reliability multipliers for different data sources
    # See config.constants for documentation on data source confidence
    SOURCE_RELIABILITY: dict[str, float] = {
        "assessor_api": DATA_CONFIDENCE_ASSESSOR_API,  # Government records, highest trust
        "web_scrape": DATA_CONFIDENCE_WEB_SCRAPE,  # Listing data, generally reliable
        "ai_inference": 0.6,  # AI guesses, lower trust
        "ai_pending": 0.0,  # Not yet processed
        "manual": DATA_CONFIDENCE_MANUAL,  # Human inspection
    }

    def score_inference(
        self,
        inference: FieldInference,
        source_reliability: float | None = None,
    ) -> float:
        """Calculate final confidence score for an inference.

        Combines the inference's raw confidence, the field-specific weight,
        and the source reliability to produce a final confidence score.

        Formula: min(1.0, base_weight * source_reliability * raw_confidence)

        Args:
            inference: The FieldInference to score
            source_reliability: Optional override for source reliability.
                If not provided, uses SOURCE_RELIABILITY lookup.

        Returns:
            Final confidence score between 0.0 and 1.0
        """
        base_weight = self.FIELD_CONFIDENCE_WEIGHTS.get(inference.field_name, None)
        if base_weight is None:
            logger.warning(
                f"Unknown field '{inference.field_name}' in confidence scoring, defaulting to 0.5"
            )
            base_weight = 0.5

        if source_reliability is None:
            source_reliability = self.SOURCE_RELIABILITY.get(inference.source, None)
            if source_reliability is None:
                logger.warning(
                    f"Unknown source '{inference.source}' in confidence scoring, defaulting to 0.5"
                )
                source_reliability = 0.5

        return min(1.0, base_weight * source_reliability * inference.confidence)

    def score_and_update_inference(
        self,
        inference: FieldInference,
    ) -> FieldInference:
        """Score an inference and return a new one with updated confidence.

        Creates a new FieldInference with the calculated confidence score
        and appropriate confidence level.

        Args:
            inference: Original FieldInference

        Returns:
            New FieldInference with updated confidence and confidence_level
        """
        final_score = self.score_inference(inference)
        return FieldInference(
            field_name=inference.field_name,
            inferred_value=inference.inferred_value,
            confidence=final_score,
            confidence_level=ConfidenceLevel.from_score(final_score),
            source=inference.source,
            reasoning=inference.reasoning,
        )

    def get_field_weight(self, field_name: str) -> float:
        """Get the base confidence weight for a field.

        Args:
            field_name: Name of the field

        Returns:
            Base confidence weight, or 0.5 if field not recognized
        """
        weight = self.FIELD_CONFIDENCE_WEIGHTS.get(field_name, None)
        if weight is None:
            logger.warning(f"Unknown field '{field_name}' in get_field_weight, defaulting to 0.5")
            weight = 0.5
        return weight

    def get_source_reliability(self, source: str) -> float:
        """Get the reliability factor for a data source.

        Args:
            source: Source identifier (assessor_api, web_scrape, etc.)

        Returns:
            Source reliability factor, or 0.5 if source not recognized
        """
        reliability = self.SOURCE_RELIABILITY.get(source, None)
        if reliability is None:
            logger.warning(
                f"Unknown source '{source}' in get_source_reliability, defaulting to 0.5"
            )
            reliability = 0.5
        return reliability

    def score_multiple_inferences(
        self,
        inferences: list[FieldInference],
    ) -> list[FieldInference]:
        """Score multiple inferences and return updated versions.

        Args:
            inferences: List of FieldInference objects to score

        Returns:
            List of new FieldInference objects with updated confidence
        """
        return [self.score_and_update_inference(inf) for inf in inferences]

    def calculate_aggregate_confidence(
        self,
        inferences: list[FieldInference],
    ) -> float:
        """Calculate aggregate confidence across multiple inferences.

        Uses weighted average based on field importance.

        Args:
            inferences: List of FieldInference objects

        Returns:
            Weighted average confidence score, or 0.0 if no inferences
        """
        if not inferences:
            return 0.0

        total_weight = 0.0
        weighted_confidence = 0.0

        for inference in inferences:
            weight = self.get_field_weight(inference.field_name)
            score = self.score_inference(inference)
            weighted_confidence += weight * score
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_confidence / total_weight

    def meets_threshold(
        self,
        inference: FieldInference,
        min_confidence: float = 0.5,
    ) -> bool:
        """Check if an inference meets a minimum confidence threshold.

        Args:
            inference: FieldInference to check
            min_confidence: Minimum required confidence (default 0.5)

        Returns:
            True if scored confidence meets or exceeds threshold
        """
        return self.score_inference(inference) >= min_confidence

    def get_high_confidence_inferences(
        self,
        inferences: list[FieldInference],
        threshold: float = CONFIDENCE_HIGH_THRESHOLD,
    ) -> list[FieldInference]:
        """Filter inferences to only those with high confidence.

        Args:
            inferences: List of FieldInference objects
            threshold: Minimum confidence threshold (default CONFIDENCE_HIGH_THRESHOLD)

        Returns:
            List of FieldInference objects meeting the threshold
        """
        return [inf for inf in inferences if self.score_inference(inf) >= threshold]

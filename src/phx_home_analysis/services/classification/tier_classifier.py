"""Property tier classification service.

Classifies properties into tiers (UNICORN, CONTENDER, PASS) based on total scores
using configurable thresholds.

Usage:
    from phx_home_analysis.services.scoring import PropertyScorer

    scorer = PropertyScorer()
    classifier = TierClassifier(scorer.thresholds)
    tier = classifier.classify(property_obj)
    properties_with_tiers = classifier.classify_batch(properties)
"""

import logging

from ...config.scoring_weights import TierThresholds
from ...domain import Property, Tier

logger = logging.getLogger(__name__)


class TierClassifier:
    """Classifies properties into tiers based on score thresholds.

    Tier boundaries:
    - UNICORN: score > unicorn_min (typically 480 pts)
    - CONTENDER: contender_min <= score <= unicorn_min (typically 360-480 pts)
    - PASS: score < contender_min (typically <360 pts)

    Responsibilities:
    - Apply threshold logic to determine tier from score
    - Classify single properties or batches
    - Update Property.tier attribute with classification result
    """

    def __init__(self, thresholds: TierThresholds) -> None:
        """Initialize classifier with score thresholds.

        Args:
            thresholds: Scoring threshold configuration
        """
        self._thresholds = thresholds
        logger.debug(
            f"TierClassifier initialized: UNICORN>{thresholds.unicorn_min}, "
            f"CONTENDER>={thresholds.contender_min}"
        )

    def classify(self, property_obj: Property) -> Tier:
        """Classify a single property into a tier.

        Reads score_breakdown.total_score and applies threshold logic.

        Args:
            property_obj: Property with score_breakdown populated

        Returns:
            Tier classification (UNICORN, CONTENDER, or PASS)

        Raises:
            ValueError: If property lacks score_breakdown
        """
        if not property_obj.score_breakdown:
            raise ValueError(f"Property {property_obj.full_address} missing score_breakdown")

        score = property_obj.score_breakdown.total_score

        if score > self._thresholds.unicorn_min:
            return Tier.UNICORN
        elif score >= self._thresholds.contender_min:
            return Tier.CONTENDER
        else:
            return Tier.PASS

    def classify_batch(self, properties: list[Property]) -> list[Property]:
        """Classify a batch of properties and update their tier attributes.

        Args:
            properties: List of scored properties with score_breakdown populated

        Returns:
            Same list of properties with Property.tier updated (modified in place)
        """
        classified_count = 0

        for property_obj in properties:
            try:
                property_obj.tier = self.classify(property_obj)
                classified_count += 1
            except ValueError as e:
                logger.warning(f"Skipping classification: {e}")
                continue

        logger.info(f"Classified {classified_count}/{len(properties)} properties into tiers")
        return properties

    def group_by_tier(
        self, properties: list[Property]
    ) -> tuple[list[Property], list[Property], list[Property]]:
        """Group properties by tier classification.

        Args:
            properties: List of properties with tier attribute set

        Returns:
            Tuple of (unicorns, contenders, passed) lists
        """
        unicorns = [p for p in properties if p.tier == Tier.UNICORN]
        contenders = [p for p in properties if p.tier == Tier.CONTENDER]
        passed = [p for p in properties if p.tier == Tier.PASS]

        logger.debug(
            f"Grouped: {len(unicorns)} unicorns, {len(contenders)} contenders, {len(passed)} passed"
        )

        return unicorns, contenders, passed

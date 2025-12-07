"""Single property analysis workflow service.

Orchestrates the complete analysis workflow for a single property:
1. Load enrichment data
2. Merge enrichment into property
3. Evaluate kill switches
4. Score if passing
5. Classify tier

Usage:
    analyzer = PropertyAnalyzer(
        enrichment_merger=merger,
        kill_switch_filter=filter,
        scorer=scorer,
        tier_classifier=classifier
    )
    analyzed_property = analyzer.analyze(property_obj, enrichment_lookup)
"""

import logging

from ...domain import EnrichmentData, Property
from ...services.classification import TierClassifier
from ...services.enrichment import EnrichmentMerger
from ...services.kill_switch import KillSwitchFilter
from ...services.scoring import PropertyScorer

logger = logging.getLogger(__name__)


class PropertyAnalyzer:
    """Analyzes individual properties through the complete workflow.

    Responsibilities:
    - Coordinate enrichment, filtering, scoring, and classification
    - Handle single-property analysis use cases
    - Provide detailed logging for each analysis step
    - Update Property object with all analysis results
    """

    def __init__(
        self,
        enrichment_merger: EnrichmentMerger,
        kill_switch_filter: KillSwitchFilter,
        scorer: PropertyScorer,
        tier_classifier: TierClassifier,
    ) -> None:
        """Initialize analyzer with required services.

        Args:
            enrichment_merger: Service to merge enrichment data
            kill_switch_filter: Service to evaluate kill switches
            scorer: Service to score properties
            tier_classifier: Service to classify tiers
        """
        self._merger = enrichment_merger
        self._filter = kill_switch_filter
        self._scorer = scorer
        self._classifier = tier_classifier

        logger.debug("PropertyAnalyzer initialized with all services")

    def analyze(
        self,
        property_obj: Property,
        enrichment_lookup: dict[str, EnrichmentData],
    ) -> Property:
        """Analyze a single property through the complete workflow.

        Args:
            property_obj: Property to analyze
            enrichment_lookup: Dictionary mapping addresses to enrichment data

        Returns:
            Property object with complete analysis (modified in place)
        """
        logger.info(f"Analyzing property: {property_obj.full_address}")

        # Step 1: Enrich property with external data
        enrichment = enrichment_lookup.get(property_obj.full_address)
        if enrichment:
            self._merger.merge(property_obj, enrichment)
            logger.debug(f"Enrichment merged for {property_obj.full_address}")
        else:
            logger.warning(f"No enrichment data found for {property_obj.full_address}")

        # Step 2: Evaluate kill switches
        passed, failures = self._filter.evaluate(property_obj)
        property_obj.kill_switch_passed = passed
        property_obj.kill_switch_failures = failures

        if not passed:
            logger.info(
                f"Property failed kill switches: {', '.join(failures)} - "
                f"{property_obj.full_address}"
            )
            return property_obj

        logger.debug(f"Property passed kill switches: {property_obj.full_address}")

        # Step 3: Score passing property
        score_breakdown = self._scorer.score(property_obj)
        property_obj.score_breakdown = score_breakdown
        logger.debug(
            f"Property scored {score_breakdown.total_score:.1f} pts: {property_obj.full_address}"
        )

        # Step 4: Classify tier
        tier = self._classifier.classify(property_obj)
        property_obj.tier = tier
        logger.info(
            f"Analysis complete: {property_obj.full_address} - "
            f"{score_breakdown.total_score:.1f} pts ({tier.value})"
        )

        return property_obj

    def find_and_analyze(
        self,
        full_address: str,
        all_properties: list[Property],
        enrichment_lookup: dict[str, EnrichmentData],
    ) -> Property | None:
        """Find a property by address and analyze it.

        Convenience method that combines property lookup with analysis.

        Args:
            full_address: Complete address to search for
            all_properties: List of all available properties
            enrichment_lookup: Dictionary mapping addresses to enrichment data

        Returns:
            Analyzed Property object, or None if address not found
        """
        logger.info(f"Searching for property: {full_address}")

        # Find matching property (case-insensitive)
        matching_property = None
        for prop in all_properties:
            if prop.full_address.lower() == full_address.lower():
                matching_property = prop
                break

        if not matching_property:
            logger.warning(f"Property not found: {full_address}")
            return None

        # Analyze the found property
        return self.analyze(matching_property, enrichment_lookup)

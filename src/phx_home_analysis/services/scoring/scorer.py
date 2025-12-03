"""Property scoring orchestrator.

This module provides the PropertyScorer class that orchestrates scoring across
all strategies, calculates category totals, and assigns tier classifications.
"""


from ...config.scoring_weights import ScoringWeights, TierThresholds
from ...domain.entities import Property
from ...domain.enums import Tier
from ...domain.value_objects import ScoreBreakdown
from .base import ScoringStrategy
from .strategies import ALL_STRATEGIES


class PropertyScorer:
    """Orchestrates property scoring across all criteria.

    The PropertyScorer applies all scoring strategies to a property, groups
    scores by category (location, systems, interior), and produces a complete
    ScoreBreakdown with tier classification.

    Example:
        >>> scorer = PropertyScorer()
        >>> properties = load_properties()
        >>> scored = scorer.score_all(properties)
        >>> unicorns = [p for p in scored if p.is_unicorn]
    """

    def __init__(
        self,
        strategies: list[ScoringStrategy] | None = None,
        weights: ScoringWeights | None = None,
        thresholds: TierThresholds | None = None,
    ) -> None:
        """Initialize PropertyScorer with strategies and config.

        Args:
            strategies: List of scoring strategies to apply. If None, uses all
                default strategies from strategies module.
            weights: Scoring weights configuration. If None, uses default weights.
            thresholds: Tier classification thresholds. If None, uses defaults.
        """
        self._weights = weights or ScoringWeights()
        self._thresholds = thresholds or TierThresholds()

        # Initialize strategies (create instances from classes)
        if strategies is None:
            self._strategies = [strategy_class(self._weights) for strategy_class in ALL_STRATEGIES]  # type: ignore[abstract]
        else:
            self._strategies = strategies

    @property
    def weights(self) -> ScoringWeights:
        """Scoring weights configuration.

        Returns:
            ScoringWeights instance
        """
        return self._weights

    @property
    def thresholds(self) -> TierThresholds:
        """Tier classification thresholds.

        Returns:
            TierThresholds instance
        """
        return self._thresholds

    def score(self, property: Property) -> ScoreBreakdown:
        """Calculate complete score breakdown for a single property.

        Applies all scoring strategies, groups by category, and returns a
        ScoreBreakdown value object with all scores and totals.

        Args:
            property: Property entity to score

        Returns:
            ScoreBreakdown with location, systems, and interior scores
        """
        # Calculate scores for all strategies
        location_scores = []
        systems_scores = []
        interior_scores = []

        for strategy in self._strategies:
            score = strategy.calculate_weighted_score(property)

            # Group by category
            if strategy.category == "location":
                location_scores.append(score)
            elif strategy.category == "systems":
                systems_scores.append(score)
            elif strategy.category == "interior":
                interior_scores.append(score)

        # Create and return ScoreBreakdown
        return ScoreBreakdown(
            location_scores=location_scores,
            systems_scores=systems_scores,
            interior_scores=interior_scores,
        )

    def score_all(self, properties: list[Property]) -> list[Property]:
        """Score all properties and assign tier classifications.

        Mutates the input Property entities by setting:
        - score_breakdown: Complete ScoreBreakdown value object
        - tier: Tier classification based on total score and kill switches

        Only properties that passed kill switches (kill_switch_passed=True)
        receive non-FAILED tier classifications.

        Args:
            properties: List of Property entities to score

        Returns:
            Same list of properties with score_breakdown and tier populated
        """
        for property in properties:
            # Calculate score breakdown
            score_breakdown = self.score(property)
            property.score_breakdown = score_breakdown

            # Assign tier based on total score and kill switch status
            property.tier = Tier.from_score(
                score=score_breakdown.total_score,
                kill_switch_passed=property.kill_switch_passed,
            )

        return properties

    def get_strategies_by_category(self, category: str) -> list[ScoringStrategy]:
        """Get all strategies for a specific category.

        Args:
            category: Category name ("location", "systems", or "interior")

        Returns:
            List of strategies matching the category
        """
        return [s for s in self._strategies if s.category == category]

    def get_strategy_by_name(self, name: str) -> ScoringStrategy | None:
        """Get strategy by criterion name.

        Args:
            name: Criterion name (e.g., "School District Rating")

        Returns:
            Matching strategy or None if not found
        """
        for strategy in self._strategies:
            if strategy.name == name:
                return strategy
        return None

    def __str__(self) -> str:
        """String representation shows strategy count and max score."""
        return (
            f"PropertyScorer(strategies={len(self._strategies)}, "
            f"max_score={self._weights.total_possible_score})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"PropertyScorer(strategies={len(self._strategies)}, "
            f"weights={self._weights}, "
            f"thresholds={self._thresholds})"
        )

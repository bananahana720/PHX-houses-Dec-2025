"""Property scoring orchestrator.

This module provides the PropertyScorer class that orchestrates scoring across
all strategies, calculates category totals, and assigns tier classifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...config.scoring_weights import ScoringWeights, TierThresholds
from ...domain.entities import Property
from ...domain.enums import Tier
from ...domain.value_objects import ScoreBreakdown
from .base import ScoringStrategy
from .strategies import ALL_STRATEGIES

if TYPE_CHECKING:
    from .explanation import FullScoreExplanation


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

    def score_location(self, property: Property) -> float:
        """Calculate Section A (Location & Environment) score independently.

        Applies only location-related scoring strategies and returns the
        total weighted score for this section.

        Args:
            property: Property entity to score

        Returns:
            Total location score (0-250 pts)
        """
        location_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "location"
        ]
        return sum(score.weighted_score for score in location_scores)

    def score_systems(self, property: Property) -> float:
        """Calculate Section B (Lot & Systems) score independently.

        Applies only systems-related scoring strategies and returns the
        total weighted score for this section.

        Args:
            property: Property entity to score

        Returns:
            Total systems score (0-175 pts)
        """
        systems_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "systems"
        ]
        return sum(score.weighted_score for score in systems_scores)

    def score_interior(self, property: Property) -> float:
        """Calculate Section C (Interior & Features) score independently.

        Applies only interior-related scoring strategies and returns the
        total weighted score for this section.

        Args:
            property: Property entity to score

        Returns:
            Total interior score (0-180 pts)
        """
        interior_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "interior"
        ]
        return sum(score.weighted_score for score in interior_scores)

    def score(self, property: Property) -> ScoreBreakdown:
        """Calculate complete score breakdown for a single property.

        Applies all scoring strategies, groups by category, and returns a
        ScoreBreakdown value object with all scores and totals.

        Args:
            property: Property entity to score

        Returns:
            ScoreBreakdown with location, systems, and interior scores
        """
        # Calculate scores for all strategies, grouped by category
        location_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "location"
        ]
        systems_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "systems"
        ]
        interior_scores = [
            strategy.calculate_weighted_score(property)
            for strategy in self._strategies
            if strategy.category == "interior"
        ]

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

    def explain_score(
        self,
        property: Property,
        breakdown: ScoreBreakdown | None = None,
    ) -> FullScoreExplanation:
        """Generate human-readable explanation for a property's scores.

        Creates a detailed explanation of why the property received each score,
        what would improve scores, and how it compares to tier thresholds.

        Args:
            property: Property entity to explain
            breakdown: Optional pre-calculated score breakdown. If None,
                will calculate scores first.

        Returns:
            FullScoreExplanation with detailed reasoning for all scores

        Example:
            >>> scorer = PropertyScorer()
            >>> property = load_property("123 Main St")
            >>> explanation = scorer.explain_score(property)
            >>> print(explanation.to_text())  # Markdown output
            >>> print(explanation.to_dict())  # JSON-serializable dict
        """
        # Import here to avoid circular dependency
        from .explanation import ScoringExplainer

        # Calculate breakdown if not provided
        if breakdown is None:
            breakdown = self.score(property)

        # Create explainer with same weights and thresholds
        explainer = ScoringExplainer(
            weights=self._weights,
            thresholds=self._thresholds,
        )

        return explainer.explain(property, breakdown)

    def score_with_explanation(
        self,
        property: Property,
    ) -> tuple[ScoreBreakdown, FullScoreExplanation]:
        """Calculate scores and generate explanation in one call.

        Convenience method that returns both the score breakdown and
        explanation without recalculating scores.

        Args:
            property: Property entity to score and explain

        Returns:
            Tuple of (ScoreBreakdown, FullScoreExplanation)

        Example:
            >>> scorer = PropertyScorer()
            >>> breakdown, explanation = scorer.score_with_explanation(property)
            >>> print(f"Total: {breakdown.total_score}")
            >>> print(explanation.to_text())
        """
        breakdown = self.score(property)
        explanation = self.explain_score(property, breakdown)
        return breakdown, explanation

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

"""Cost Efficiency scoring strategy (Section B).

This module implements the CostEfficiencyScorer that scores properties based on
their estimated monthly cost efficiency, capturing the financial burden of
ownership including mortgage, taxes, HOA, solar lease, and pool maintenance.
"""

from typing import Optional

from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ..base import ScoringStrategy


class CostEfficiencyScorer(ScoringStrategy):
    """Score based on estimated monthly cost efficiency.

    Formula: base_score = max(0, 10 - ((monthly_cost - 3000) / 200))

    Scoring breakdown:
    - $3,000/mo or less: 10 pts (maximum - very affordable)
    - $3,200/mo: 9 pts
    - $3,400/mo: 8 pts
    - $3,600/mo: 7 pts
    - $3,800/mo: 6 pts
    - $4,000/mo: 5 pts (neutral - at buyer max)
    - $4,200/mo: 4 pts
    - $4,400/mo: 3 pts
    - $4,600/mo: 2 pts
    - $4,800/mo: 1 pt
    - $5,000+/mo: 0 pts (exceeds target budget)

    The formula deducts 0.5 points per $100 above $3,000/mo baseline.
    This scoring captures the total cost of ownership beyond just purchase price,
    accounting for:
    - Mortgage payment (30-year, estimated down payment, market rate)
    - Property taxes
    - HOA fees (if applicable)
    - Solar lease payments (if applicable)
    - Pool maintenance costs (if applicable)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Cost Efficiency"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.cost_efficiency

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from estimated monthly cost.

        Uses the Property.total_monthly_cost computed property which includes:
        - Mortgage payment (30-year, $50k down, 7% rate)
        - Property tax (annual / 12)
        - HOA fee (if applicable)
        - Solar lease (if applicable)
        - Pool maintenance estimate ($125/mo if pool present)

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on monthly cost efficiency)
        """
        # Get the total monthly cost from the property
        monthly_cost = property.total_monthly_cost

        # Handle edge case where cost calculation fails
        if monthly_cost <= 0:
            return 5.0  # Neutral default

        # Formula: base_score = max(0, 10 - ((monthly_cost - 3000) / 200))
        # This gives:
        # - $3,000/mo -> 10 pts
        # - $4,000/mo -> 5 pts
        # - $5,000/mo -> 0 pts
        base_score = max(0.0, 10.0 - ((monthly_cost - 3000) / 200))

        # Cap at 10 for properties under $3,000/mo
        return min(10.0, base_score)

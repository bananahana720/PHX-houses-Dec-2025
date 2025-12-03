"""Cost Efficiency scoring strategy (Section B).

This module implements the CostEfficiencyScorer that scores properties based on
their estimated monthly cost efficiency, capturing the financial burden of
ownership including mortgage, taxes, HOA, solar lease, and pool maintenance.
"""


from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ...cost_estimation import MonthlyCostEstimator
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

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        cost_estimator: MonthlyCostEstimator | None = None,
    ) -> None:
        """Initialize with scoring weights and cost estimator.

        Args:
            weights: Scoring weights config, defaults to standard weights
            cost_estimator: Cost estimator service, defaults to new instance
        """
        self._weights = weights or ScoringWeights()
        self._cost_estimator = cost_estimator or MonthlyCostEstimator()

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

        Uses MonthlyCostEstimator service to calculate costs including:
        - Mortgage payment (30-year, $50k down, 7% rate)
        - Property tax (annual / 12)
        - HOA fee (if applicable)
        - Solar lease (if applicable)
        - Pool maintenance estimate ($125/mo if pool present)

        Also caches the cost breakdown on the property for later use.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on monthly cost efficiency)
        """
        # Use injected service to calculate monthly costs
        cost_estimate = self._cost_estimator.estimate(property)
        monthly_cost = cost_estimate.total

        # Cache the costs on the property for other consumers
        property.set_monthly_costs({
            "mortgage": cost_estimate.mortgage,
            "property_tax": cost_estimate.property_tax,
            "hoa": cost_estimate.hoa_fee,
            "solar_lease": cost_estimate.solar_lease,
            "pool_maintenance": cost_estimate.pool_maintenance,
        })

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

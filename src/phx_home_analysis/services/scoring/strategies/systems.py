"""Lot & Systems scoring strategies (Section B).

This module implements scoring strategies for property systems and lot:
- Roof Condition/Age (50 pts)
- Backyard Utility (40 pts)
- Plumbing/Electrical (40 pts)
- Pool Condition (20 pts)
- Cost Efficiency (30 pts) - in cost_efficiency.py

Total Section B maximum: 180 points
"""


from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ..base import ScoringStrategy


class RoofConditionScorer(ScoringStrategy):
    """Score based on roof age and condition.

    Arizona heat reduces roof lifespan vs national average.

    Scoring logic based on roof_age:
    - 0-5 years: 10 pts (new/replaced)
    - 6-10 years: 7 pts (good condition)
    - 11-15 years: 5 pts (fair condition)
    - 16-20 years: 3 pts (aging)
    - >20 years: 1 pt (replacement needed)
    - Unknown: 5 pts (neutral)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Roof Condition/Age"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.roof_condition

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from roof age.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on age)
        """
        if property.roof_age is None:
            return 5.0  # Neutral default

        age = property.roof_age

        if age <= 5:
            return 10.0  # New/replaced
        elif age <= 10:
            return 7.0  # Good condition
        elif age <= 15:
            return 5.0  # Fair condition
        elif age <= 20:
            return 3.0  # Aging
        else:
            return 1.0  # Replacement needed


class BackyardUtilityScorer(ScoringStrategy):
    """Score based on usable backyard space assessment.

    Uses backyard_utility_score field (manual visual inspection).
    Factors: Lot size, pool, covered patio, landscaping, usable space.

    Estimated calculation:
    - lot_sqft - house_sqft - front_yard_estimate
    - Account for pool and hardscaping

    Scoring:
    - 10: Large usable space (>4000 sqft)
    - 5: Medium space (2000-4000 sqft) / unknown
    - 0: Minimal space (<1000 sqft)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Backyard Utility"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.backyard_utility

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual backyard assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.backyard_utility_score is None:
            return 5.0  # Neutral default
        return float(property.backyard_utility_score)


class PlumbingElectricalScorer(ScoringStrategy):
    """Score based on year built (proxy for system age).

    Modern builds have copper plumbing, 200A service, updated panels.
    Older properties may need upgrades.

    Scoring logic based on year_built:
    - 2010+: 10 pts (recent build)
    - 2000-2009: 8 pts (modern)
    - 1990-1999: 6 pts (updated)
    - 1980-1989: 4 pts (aging)
    - <1980: 2 pts (old systems)
    - Unknown: 5 pts (neutral)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Plumbing/Electrical Systems"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.plumbing_electrical

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from year built.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on year built)
        """
        if property.year_built is None:
            return 5.0  # Neutral default

        year = property.year_built

        if year >= 2010:
            return 10.0  # Recent build
        elif year >= 2000:
            return 8.0  # Modern
        elif year >= 1990:
            return 6.0  # Updated
        elif year >= 1980:
            return 4.0  # Aging
        else:
            return 2.0  # Old systems


class PoolConditionScorer(ScoringStrategy):
    """Score based on pool equipment age (if pool present).

    Pool equipment fails faster in Arizona heat/sun.
    No pool receives neutral score (no maintenance burden).

    Scoring logic:
    - No pool: 5 pts (neutral, no burden)
    - Has pool with equipment age:
      - 0-3 years: 10 pts (new equipment)
      - 4-6 years: 7 pts (good condition)
      - 7-10 years: 5 pts (fair condition)
      - >10 years: 3 pts (needs replacement)
    - Has pool, age unknown: 5 pts (neutral)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Pool Condition"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.pool_condition

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from pool status and equipment age.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on pool equipment age)
        """
        # No pool = neutral (no burden, no benefit)
        if not property.has_pool:
            return 5.0

        # Has pool but age unknown = neutral
        if property.pool_equipment_age is None:
            return 5.0

        age = property.pool_equipment_age

        if age <= 3:
            return 10.0  # New equipment
        elif age <= 6:
            return 7.0  # Good condition
        elif age <= 10:
            return 5.0  # Fair condition
        else:
            return 3.0  # Needs replacement

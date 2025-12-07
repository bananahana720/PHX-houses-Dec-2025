"""Lot & Systems scoring strategies (Section B).

This module implements scoring strategies for property systems and lot:
- Roof Condition/Age (45 pts)
- Backyard Utility (35 pts)
- Plumbing/Electrical (35 pts)
- Pool Condition (20 pts)
- Cost Efficiency (35 pts) - in cost_efficiency.py
- Solar Status (5 pts)

Total Section B maximum: 175 points
"""

from ....config.constants import (
    DEFAULT_NEUTRAL_SCORE,
    PLUMBING_YEAR_AGING_MIN,
    PLUMBING_YEAR_MODERN_MIN,
    PLUMBING_YEAR_RECENT_MIN,
    PLUMBING_YEAR_UPDATED_MIN,
    POOL_EQUIP_FAIR_MAX,
    POOL_EQUIP_GOOD_MAX,
    POOL_EQUIP_NEW_MAX,
    ROOF_AGE_AGING_MAX,
    ROOF_AGE_FAIR_MAX,
    ROOF_AGE_GOOD_MAX,
    ROOF_AGE_NEW_MAX,
    SCORE_PLUMBING_AGING,
    SCORE_PLUMBING_MODERN,
    SCORE_PLUMBING_OLD,
    SCORE_PLUMBING_RECENT,
    SCORE_PLUMBING_UPDATED,
    SCORE_POOL_FAIR,
    SCORE_POOL_GOOD,
    SCORE_POOL_NEW,
    SCORE_POOL_REPLACEMENT,
    SCORE_ROOF_AGING,
    SCORE_ROOF_FAIR,
    SCORE_ROOF_GOOD,
    SCORE_ROOF_NEW,
    SCORE_ROOF_REPLACEMENT,
)
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
            return DEFAULT_NEUTRAL_SCORE

        age = property.roof_age

        if age <= ROOF_AGE_NEW_MAX:
            return SCORE_ROOF_NEW
        elif age <= ROOF_AGE_GOOD_MAX:
            return SCORE_ROOF_GOOD
        elif age <= ROOF_AGE_FAIR_MAX:
            return SCORE_ROOF_FAIR
        elif age <= ROOF_AGE_AGING_MAX:
            return SCORE_ROOF_AGING
        else:
            return SCORE_ROOF_REPLACEMENT


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
            return DEFAULT_NEUTRAL_SCORE
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
            return DEFAULT_NEUTRAL_SCORE

        year = property.year_built

        if year >= PLUMBING_YEAR_RECENT_MIN:
            return SCORE_PLUMBING_RECENT
        elif year >= PLUMBING_YEAR_MODERN_MIN:
            return SCORE_PLUMBING_MODERN
        elif year >= PLUMBING_YEAR_UPDATED_MIN:
            return SCORE_PLUMBING_UPDATED
        elif year >= PLUMBING_YEAR_AGING_MIN:
            return SCORE_PLUMBING_AGING
        else:
            return SCORE_PLUMBING_OLD


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
            return DEFAULT_NEUTRAL_SCORE

        # Has pool but age unknown = neutral
        if property.pool_equipment_age is None:
            return DEFAULT_NEUTRAL_SCORE

        age = property.pool_equipment_age

        if age <= POOL_EQUIP_NEW_MAX:
            return SCORE_POOL_NEW
        elif age <= POOL_EQUIP_GOOD_MAX:
            return SCORE_POOL_GOOD
        elif age <= POOL_EQUIP_FAIR_MAX:
            return SCORE_POOL_FAIR
        else:
            return SCORE_POOL_REPLACEMENT


class SolarStatusScorer(ScoringStrategy):
    """Awards bonus points for owned solar panels.

    Scoring:
    - Owned solar (paid off): 10 pts - valuable asset, adds 4-7% home value
    - Solar loan (building equity): 6 pts - becoming asset
    - No solar: 5 pts - neutral, no burden
    - Unknown: 4 pts - conservative default
    - Leased solar: 0 pts - liability (also fails kill-switch)

    Note: Leased solar typically fails the kill-switch before
    reaching scoring, but we score it at 0 for completeness.
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Solar Status"

    @property
    def category(self) -> str:
        return "systems"

    @property
    def weight(self) -> int:
        return self._weights.solar_status

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score (0-10) for solar status.

        Args:
            property: Property to score

        Returns:
            Base score (0-10) based on solar ownership status
        """
        from ....domain.enums import SolarStatus

        solar_status = getattr(property, "solar_status", None)

        if solar_status is None:
            return 4.0  # Unknown - conservative middle

        # Handle both SolarStatus enum and string values
        if isinstance(solar_status, SolarStatus):
            if solar_status == SolarStatus.OWNED:
                return 10.0  # Full points - asset
            elif solar_status == SolarStatus.NONE:
                return 5.0  # Neutral
            elif solar_status == SolarStatus.LEASED:
                return 0.0  # Liability
            elif solar_status == SolarStatus.UNKNOWN:
                return 4.0  # Conservative default
        else:
            # Handle string comparison for backward compatibility
            status = solar_status.lower() if isinstance(solar_status, str) else str(solar_status)
            if status in ("owned", "solarstatus.owned"):
                return 10.0  # Full points - asset
            elif status in ("none", "solarstatus.none"):
                return 5.0  # Neutral
            elif status in ("leased", "solarstatus.leased"):
                return 0.0  # Liability

        return 4.0  # Unknown default

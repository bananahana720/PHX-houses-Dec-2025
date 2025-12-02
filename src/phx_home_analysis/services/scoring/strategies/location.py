"""Location & Environment scoring strategies (Section A).

This module implements scoring strategies for location-related criteria:
- School District Rating (50 pts)
- Quietness/Noise (50 pts)
- Safety/Neighborhood (50 pts)
- Supermarket Proximity (40 pts)
- Parks & Walkability (30 pts)
- Sun Orientation (30 pts)

Total Section A maximum: 250 points
"""

from typing import Optional

from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ....domain.enums import Orientation
from ..base import ScoringStrategy


class SchoolDistrictScorer(ScoringStrategy):
    """Score based on GreatSchools district rating.

    Uses school_rating directly (1-10 scale) as base score.
    Data source: GreatSchools.org

    Scoring:
    - Rating 10: 10 pts (excellent schools)
    - Rating 5: 5 pts (average schools)
    - Rating 1: 1 pt (poor schools)
    - Unknown: 5 pts (neutral)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "School District Rating"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.school_district

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from school rating.

        Args:
            property: Property to score

        Returns:
            Base score (1-10 from GreatSchools, 5 if unknown)
        """
        if property.school_rating is None:
            return 5.0  # Neutral default
        return float(property.school_rating)


class QuietnessScorer(ScoringStrategy):
    """Score based on distance to highways/freeways.

    Scoring logic based on distance_to_highway_miles:
    - >2 miles: 10 pts (very quiet)
    - 1-2 miles: 7 pts (quiet)
    - 0.5-1 mile: 5 pts (acceptable)
    - <0.5 miles: 3 pts (noisy)

    Data source: Google Maps
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Quietness/Noise Level"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.quietness

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from highway distance.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on distance)
        """
        if property.distance_to_highway_miles is None:
            return 5.0  # Neutral default

        distance = property.distance_to_highway_miles

        if distance >= 2.0:
            return 10.0  # Very quiet
        elif distance >= 1.0:
            return 7.0  # Quiet
        elif distance >= 0.5:
            return 5.0  # Acceptable
        else:
            return 3.0  # Noisy


class SafetyScorer(ScoringStrategy):
    """Score based on manual neighborhood safety assessment.

    Uses safety_neighborhood_score field (manual visual inspection).
    Factors: Crime statistics, street lighting, neighborhood upkeep.

    Scoring:
    - 10: Excellent (gated, well-lit, pristine)
    - 5: Average/unknown
    - 0: Poor (visible issues)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Safety/Neighborhood"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.safety

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual safety assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.safety_neighborhood_score is None:
            return 5.0  # Neutral default
        return float(property.safety_neighborhood_score)


class SupermarketScorer(ScoringStrategy):
    """Score based on distance to grocery stores.

    Scoring logic based on distance_to_grocery_miles:
    - <0.5 miles: 10 pts (walking distance)
    - 0.5-1 mile: 8 pts (very close)
    - 1-1.5 miles: 6 pts (close)
    - 1.5-2 miles: 4 pts (moderate)
    - >2 miles: 2 pts (far)

    Data source: Google Maps
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Supermarket Proximity"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.supermarket_proximity

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from grocery store distance.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on distance)
        """
        if property.distance_to_grocery_miles is None:
            return 5.0  # Neutral default

        distance = property.distance_to_grocery_miles

        if distance < 0.5:
            return 10.0  # Walking distance
        elif distance < 1.0:
            return 8.0  # Very close
        elif distance < 1.5:
            return 6.0  # Close
        elif distance < 2.0:
            return 4.0  # Moderate
        else:
            return 2.0  # Far


class ParksWalkabilityScorer(ScoringStrategy):
    """Score based on manual parks and walkability assessment.

    Uses parks_walkability_score field (manual visual inspection).
    Factors: Parks within 1 mile, sidewalks, bike lanes, trail access.

    Scoring:
    - 10: Excellent (parks, sidewalks, trails)
    - 5: Average/unknown
    - 0: Poor (no amenities)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Parks & Walkability"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.parks_walkability

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual walkability assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.parks_walkability_score is None:
            return 5.0  # Neutral default
        return float(property.parks_walkability_score)


class OrientationScorer(ScoringStrategy):
    """Score based on sun orientation (cooling cost impact).

    Uses Orientation enum's base_score property which accounts for
    Arizona climate and cooling costs.

    Scoring:
    - North: 10 pts (best, minimal sun)
    - Northeast/Northwest: 8.5 pts (excellent)
    - East: 7.5 pts (good, morning sun only)
    - South: 6 pts (moderate)
    - Southeast: 5 pts (moderate)
    - Southwest: 3 pts (high cooling costs)
    - West: 0 pts (worst, afternoon sun)
    - Unknown: 5 pts (neutral)

    Data source: Google Maps satellite view
    """

    def __init__(self, weights: Optional[ScoringWeights] = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Sun Orientation"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.sun_orientation

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from orientation enum.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from Orientation.base_score)
        """
        if property.orientation is None:
            return 5.0  # Neutral default
        return property.orientation.base_score

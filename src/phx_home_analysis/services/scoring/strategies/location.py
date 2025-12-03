"""Location & Environment scoring strategies (Section A).

This module implements scoring strategies for location-related criteria:
- School District Rating (45 pts)
- Quietness/Noise (30 pts)
- Crime Index (50 pts) - REPLACES SafetyScorer
- Supermarket Proximity (25 pts)
- Parks & Walkability (25 pts)
- Sun Orientation (25 pts)
- Flood Risk (25 pts) - NEW
- Walk/Transit (25 pts) - NEW

Total Section A maximum: 250 points
"""

import warnings

from ....config.constants import (
    CRIME_INDEX_PROPERTY_WEIGHT,
    CRIME_INDEX_TO_SCORE_DIVISOR,
    CRIME_INDEX_VIOLENT_WEIGHT,
    DEFAULT_NEUTRAL_SCORE,
    DISTANCE_GROCERY_CLOSE_MILES,
    DISTANCE_GROCERY_MODERATE_MILES,
    DISTANCE_GROCERY_VERY_CLOSE_MILES,
    DISTANCE_GROCERY_WALKING_MILES,
    DISTANCE_HIGHWAY_ACCEPTABLE_MILES,
    DISTANCE_HIGHWAY_QUIET_MILES,
    DISTANCE_HIGHWAY_VERY_QUIET_MILES,
    SCORE_FLOOD_ZONE_A,
    SCORE_FLOOD_ZONE_AE,
    SCORE_FLOOD_ZONE_AH,
    SCORE_FLOOD_ZONE_AO,
    SCORE_FLOOD_ZONE_UNKNOWN,
    SCORE_FLOOD_ZONE_VE,
    SCORE_FLOOD_ZONE_X,
    SCORE_FLOOD_ZONE_X_SHADED,
    SCORE_GROCERY_CLOSE,
    SCORE_GROCERY_FAR,
    SCORE_GROCERY_MODERATE,
    SCORE_GROCERY_VERY_CLOSE,
    SCORE_GROCERY_WALKING,
    SCORE_QUIETNESS_ACCEPTABLE,
    SCORE_QUIETNESS_NOISY,
    SCORE_QUIETNESS_QUIET,
    SCORE_QUIETNESS_VERY_QUIET,
    WALKSCORE_TO_BASE_DIVISOR,
    WALKSCORE_WEIGHT_BIKE,
    WALKSCORE_WEIGHT_TRANSIT,
    WALKSCORE_WEIGHT_WALK,
)
from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ....domain.enums import FloodZone
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

    def __init__(self, weights: ScoringWeights | None = None) -> None:
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
            return DEFAULT_NEUTRAL_SCORE
        return float(property.school_rating)


class QuietnessScorer(ScoringStrategy):
    """Score based on distance to highways/freeways.

    DEPRECATED: Use NoiseLevelScorer for HowLoud API data with highway fallback.

    Scoring logic based on distance_to_highway_miles:
    - >2 miles: 10 pts (very quiet)
    - 1-2 miles: 7 pts (quiet)
    - 0.5-1 mile: 5 pts (acceptable)
    - <0.5 miles: 3 pts (noisy)

    Data source: Google Maps
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
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
            return DEFAULT_NEUTRAL_SCORE

        distance = property.distance_to_highway_miles

        if distance >= DISTANCE_HIGHWAY_VERY_QUIET_MILES:
            return SCORE_QUIETNESS_VERY_QUIET
        elif distance >= DISTANCE_HIGHWAY_QUIET_MILES:
            return SCORE_QUIETNESS_QUIET
        elif distance >= DISTANCE_HIGHWAY_ACCEPTABLE_MILES:
            return SCORE_QUIETNESS_ACCEPTABLE
        else:
            return SCORE_QUIETNESS_NOISY


class NoiseLevelScorer(ScoringStrategy):
    """Score based on HowLoud noise data with highway distance fallback.

    Primary: Uses noise_score from HowLoud.com (0-100 scale, 100=quietest).
    Fallback: Falls back to highway distance if noise_score unavailable.

    HowLoud noise score conversion (0-100 to 0-10):
    - 80-100: 8-10 pts (Very Quiet)
    - 60-79: 6-7.9 pts (Quiet)
    - 40-59: 4-5.9 pts (Moderate)
    - 20-39: 2-3.9 pts (Loud)
    - 0-19: 0-1.9 pts (Very Loud)

    Data source: HowLoud.com API, Google Maps (fallback)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Noise Level"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.quietness  # Uses same weight as quietness (30 pts)

    def calculate_base_score(self, property: Property) -> float:
        """Calculate score from HowLoud noise data or highway distance fallback.

        Priority:
        1. noise_score from HowLoud (0-100 scale)
        2. distance_to_highway_miles (fallback)
        3. DEFAULT_NEUTRAL_SCORE if neither available

        Args:
            property: Property to score

        Returns:
            Base score (0-10)
        """
        # Priority 1: Use noise_score if available (from HowLoud)
        if hasattr(property, "noise_score") and property.noise_score is not None:
            # Convert 0-100 scale to 0-10
            return property.noise_score / 10.0

        # Priority 2: Fallback to highway distance
        if property.distance_to_highway_miles is not None:
            distance = property.distance_to_highway_miles
            if distance >= DISTANCE_HIGHWAY_VERY_QUIET_MILES:
                return SCORE_QUIETNESS_VERY_QUIET
            elif distance >= DISTANCE_HIGHWAY_QUIET_MILES:
                return SCORE_QUIETNESS_QUIET
            elif distance >= DISTANCE_HIGHWAY_ACCEPTABLE_MILES:
                return SCORE_QUIETNESS_ACCEPTABLE
            else:
                return SCORE_QUIETNESS_NOISY

        # Priority 3: No data available
        return DEFAULT_NEUTRAL_SCORE


class SafetyScorer(ScoringStrategy):
    """DEPRECATED: Use CrimeIndexScorer instead.

    Manual neighborhood safety assessment based on visual inspection.
    Replaced by automated CrimeIndexScorer using objective crime data.

    Uses safety_neighborhood_score field (manual visual inspection).
    Factors: Crime statistics, street lighting, neighborhood upkeep.

    Scoring:
    - 10: Excellent (gated, well-lit, pristine)
    - 5: Average/unknown
    - 0: Poor (visible issues)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        warnings.warn(
            "SafetyScorer is deprecated, use CrimeIndexScorer instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Safety/Neighborhood (Deprecated)"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.crime_index  # Use crime_index weight

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual safety assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.safety_neighborhood_score is None:
            return DEFAULT_NEUTRAL_SCORE
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

    def __init__(self, weights: ScoringWeights | None = None) -> None:
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
            return DEFAULT_NEUTRAL_SCORE

        distance = property.distance_to_grocery_miles

        if distance < DISTANCE_GROCERY_WALKING_MILES:
            return SCORE_GROCERY_WALKING
        elif distance < DISTANCE_GROCERY_VERY_CLOSE_MILES:
            return SCORE_GROCERY_VERY_CLOSE
        elif distance < DISTANCE_GROCERY_CLOSE_MILES:
            return SCORE_GROCERY_CLOSE
        elif distance < DISTANCE_GROCERY_MODERATE_MILES:
            return SCORE_GROCERY_MODERATE
        else:
            return SCORE_GROCERY_FAR


class ParksWalkabilityScorer(ScoringStrategy):
    """Score based on manual parks and walkability assessment.

    Uses parks_walkability_score field (manual visual inspection).
    Factors: Parks within 1 mile, sidewalks, bike lanes, trail access.

    Scoring:
    - 10: Excellent (parks, sidewalks, trails)
    - 5: Average/unknown
    - 0: Poor (no amenities)
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
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
            return DEFAULT_NEUTRAL_SCORE
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

    def __init__(self, weights: ScoringWeights | None = None) -> None:
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
            return DEFAULT_NEUTRAL_SCORE
        return property.orientation.base_score


class CrimeIndexScorer(ScoringStrategy):
    """Score based on automated crime index data from BestPlaces/AreaVibes.

    Uses violent and property crime indices (0-100, 100=safest).
    Composite score: 60% violent crime + 40% property crime.

    Replaces manual SafetyScorer with automated objective data.

    Data sources: BestPlaces.net, AreaVibes.com, NeighborhoodScout
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Crime Index"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.crime_index

    def calculate_base_score(self, property: Property) -> float:
        """Calculate score from crime indices.

        Score mapping (index 0-100, 100=safest):
        - Index 90-100 (safest): 9-10 pts
        - Index 70-89: 7-8.9 pts
        - Index 50-69: 5-6.9 pts
        - Index 30-49: 3-4.9 pts
        - Index 0-29: 0-2.9 pts
        - Unknown: 5 pts (neutral)

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on crime indices)
        """
        violent = property.violent_crime_index
        property_crime = property.property_crime_index

        if violent is None and property_crime is None:
            # Fall back to manual safety score if available
            if property.safety_neighborhood_score is not None:
                return property.safety_neighborhood_score
            return DEFAULT_NEUTRAL_SCORE

        # Use available data
        if violent is not None and property_crime is not None:
            # Composite: 60% violent, 40% property
            composite = (violent * CRIME_INDEX_VIOLENT_WEIGHT) + (
                property_crime * CRIME_INDEX_PROPERTY_WEIGHT
            )
        elif violent is not None:
            composite = violent
        else:
            composite = property_crime

        # Convert 0-100 index to 0-10 score
        return composite / CRIME_INDEX_TO_SCORE_DIVISOR


class FloodRiskScorer(ScoringStrategy):
    """Score based on FEMA flood zone data.

    Flood zone risk impacts:
    - Insurance costs (federally required in high-risk zones)
    - Property damage risk (flooding, water damage)
    - Resale value (buyers avoid flood zones)

    Data source: FEMA National Flood Hazard Layer
    """

    ZONE_SCORES = {
        FloodZone.X: SCORE_FLOOD_ZONE_X,
        FloodZone.X_SHADED: SCORE_FLOOD_ZONE_X_SHADED,
        FloodZone.A: SCORE_FLOOD_ZONE_A,
        FloodZone.AE: SCORE_FLOOD_ZONE_AE,
        FloodZone.AH: SCORE_FLOOD_ZONE_AH,
        FloodZone.AO: SCORE_FLOOD_ZONE_AO,
        FloodZone.VE: SCORE_FLOOD_ZONE_VE,
        FloodZone.UNKNOWN: SCORE_FLOOD_ZONE_UNKNOWN,
    }

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Flood Risk"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.flood_risk

    def calculate_base_score(self, property: Property) -> float:
        """Calculate score from flood zone.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on flood zone, 5 if unknown)
        """
        zone = property.flood_zone

        if isinstance(zone, str):
            try:
                zone = FloodZone(zone.lower())
            except ValueError:
                return DEFAULT_NEUTRAL_SCORE

        return self.ZONE_SCORES.get(zone, DEFAULT_NEUTRAL_SCORE)


class WalkTransitScorer(ScoringStrategy):
    """Score based on Walk Score, Transit Score, and Bike Score.

    Combines walkability and transit access metrics.
    Important for lifestyle convenience and car-optional living.

    Note: In Phoenix suburbs, transit scores are typically low,
    but walkability and bike-ability still matter for neighborhood quality.

    Data source: WalkScore.com API
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Walk/Transit"

    @property
    def category(self) -> str:
        return "location"

    @property
    def weight(self) -> int:
        return self._weights.walk_transit

    def calculate_base_score(self, property: Property) -> float:
        """Calculate composite walk/transit/bike score.

        Weighting:
        - Walk Score: 40%
        - Transit Score: 40%
        - Bike Score: 20%

        Each score is 0-100, converted to 0-10.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 weighted composite, 5 if all unknown)
        """
        walk = property.walk_score
        transit = property.transit_score
        bike = property.bike_score

        # If all unknown, return neutral
        if all(s is None for s in [walk, transit, bike]):
            return DEFAULT_NEUTRAL_SCORE

        # Use available scores with adjusted weights
        scores = []
        weights = []

        if walk is not None:
            scores.append(walk / WALKSCORE_TO_BASE_DIVISOR)
            weights.append(WALKSCORE_WEIGHT_WALK)

        if transit is not None:
            scores.append(transit / WALKSCORE_TO_BASE_DIVISOR)
            weights.append(WALKSCORE_WEIGHT_TRANSIT)

        if bike is not None:
            scores.append(bike / WALKSCORE_TO_BASE_DIVISOR)
            weights.append(WALKSCORE_WEIGHT_BIKE)

        # Normalize weights if some scores missing
        total_weight = sum(weights)
        if total_weight == 0:
            return DEFAULT_NEUTRAL_SCORE

        normalized_weights = [w / total_weight for w in weights]
        weighted_score = sum(s * w for s, w in zip(scores, normalized_weights))

        return weighted_score


class AirQualityScorer(ScoringStrategy):
    """Score based on EPA AirNow air quality index.

    Uses AQI (Air Quality Index) to score environmental health:
    - 0-50 AQI = 10/10 (Good - optimal air quality)
    - 51-100 AQI = 8/10 (Moderate - acceptable)
    - 101-150 AQI = 5/10 (Unhealthy for Sensitive Groups)
    - 151-200 AQI = 3/10 (Unhealthy)
    - 201+ AQI = 1/10 (Very Unhealthy/Hazardous)

    Arizona-specific considerations:
    - Summer ozone spikes are common (AQI 80-120)
    - Dust storms can spike PM10 readings temporarily
    - Proximity to freeways affects local AQI

    Note: This scorer uses a portion of the location environmental budget.
    Currently weighted at 15 pts (taken from school_district, crime_index, supermarket).

    Data source: EPA AirNow API
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights."""
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        """Strategy name for reporting."""
        return "Air Quality"

    @property
    def category(self) -> str:
        """Scoring category."""
        return "location"

    @property
    def weight(self) -> int:
        """Point weight for this strategy.

        Returns the official air_quality weight from ScoringWeights (15 pts).
        """
        return self._weights.air_quality

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from AQI value.

        Args:
            property: Property entity with potential air_quality_aqi field

        Returns:
            Score from 1-10 based on AQI, or neutral if unavailable
        """
        aqi = getattr(property, "air_quality_aqi", None)

        if aqi is None:
            return DEFAULT_NEUTRAL_SCORE

        # Map AQI to 1-10 scale (lower AQI = better)
        if aqi <= 50:
            return 10.0  # Good
        elif aqi <= 100:
            return 8.0  # Moderate
        elif aqi <= 150:
            return 5.0  # Unhealthy for Sensitive
        elif aqi <= 200:
            return 3.0  # Unhealthy
        else:
            return 1.0  # Very Unhealthy / Hazardous

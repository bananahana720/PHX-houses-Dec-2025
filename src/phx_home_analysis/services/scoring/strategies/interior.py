"""Interior & Features scoring strategies (Section C).

This module implements scoring strategies for interior features:
- Kitchen Layout (40 pts)
- Master Suite (40 pts)
- Natural Light (30 pts)
- High Ceilings (30 pts)
- Fireplace (20 pts)
- Laundry Area (20 pts)
- Aesthetics (10 pts)

Total Section C maximum: 190 points
"""


from ....config.constants import (
    DEFAULT_FIREPLACE_ABSENT_SCORE,
    DEFAULT_FIREPLACE_PRESENT_SCORE,
    DEFAULT_NEUTRAL_SCORE,
)
from ....config.scoring_weights import ScoringWeights
from ....domain.entities import Property
from ..base import ScoringStrategy


class KitchenLayoutScorer(ScoringStrategy):
    """Score based on kitchen design and layout quality.

    Uses kitchen_layout_score field (manual visual inspection from photos).
    Factors: Open concept, island/counter space, modern appliances,
    pantry size, natural light.

    Scoring:
    - 10: Excellent (modern, open, spacious)
    - 5: Average/unknown
    - 0: Poor (dated, cramped, closed-off)

    Data source: Listing photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Kitchen Layout"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.kitchen_layout

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual kitchen assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.kitchen_layout_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.kitchen_layout_score)


class MasterSuiteScorer(ScoringStrategy):
    """Score based on primary bedroom and bath quality.

    Uses master_suite_score field (manual visual inspection from photos).
    Factors: Bedroom size, walk-in closet, bathroom quality (dual sinks,
    separate tub/shower), privacy from other bedrooms.

    Scoring:
    - 10: Excellent (large, walk-in closet, luxe bath)
    - 5: Average/unknown
    - 0: Poor (small, inadequate closet/bath)

    Data source: Listing photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Master Suite"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.master_suite

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual master suite assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.master_suite_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.master_suite_score)


class NaturalLightScorer(ScoringStrategy):
    """Score based on window coverage and natural lighting.

    Uses natural_light_score field (manual visual inspection from photos).
    Factors: Number/size of windows, skylights, room brightness in photos,
    open floor plan.

    Scoring:
    - 10: Excellent (abundant windows, skylights, bright)
    - 5: Average/unknown
    - 0: Poor (few windows, dark)

    Data source: Listing photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Natural Light"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.natural_light

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual natural light assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.natural_light_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.natural_light_score)


class HighCeilingsScorer(ScoringStrategy):
    """Score based on ceiling height.

    Uses high_ceilings_score field (manual assessment from photos/listing).

    Scoring:
    - Vaulted/cathedral: 10 pts
    - 10+ feet: 8 pts
    - 9 feet: 6 pts
    - 8 feet (standard): 5 pts
    - <8 feet: 3 pts
    - Unknown: 5 pts

    Data source: Listing description/photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "High Ceilings"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.high_ceilings

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual ceiling height assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.high_ceilings_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.high_ceilings_score)


class FireplaceScorer(ScoringStrategy):
    """Score based on fireplace presence and type.

    Uses fireplace_present and manual assessment from photos.
    Less critical in Arizona but adds ambiance.

    Scoring:
    - Has fireplace (fireplace_present=True): Scale from manual score
    - No fireplace: 0 pts
    - Unknown: 5 pts (neutral)

    Data source: Listing photos/description
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Fireplace"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.fireplace

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from fireplace presence.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 based on presence/type)
        """
        # If fireplace presence is unknown, default to neutral
        if property.fireplace_present is None:
            return DEFAULT_NEUTRAL_SCORE

        # No fireplace = 0 points
        if not property.fireplace_present:
            return DEFAULT_FIREPLACE_ABSENT_SCORE

        # Has fireplace - use manual assessment if available
        # (could distinguish gas vs wood-burning in manual score)
        return DEFAULT_FIREPLACE_PRESENT_SCORE


class LaundryAreaScorer(ScoringStrategy):
    """Score based on laundry room quality and location.

    Uses laundry_area_score field (manual visual inspection from photos).

    Scoring logic:
    - Dedicated room upstairs: 10 pts
    - Dedicated room (any floor): 7.5 pts
    - Laundry closet: 5 pts
    - Garage only: 2.5 pts
    - No dedicated space: 0 pts
    - Unknown: 5 pts

    Data source: Listing photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Laundry Area"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.laundry_area

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual laundry area assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.laundry_area_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.laundry_area_score)


class AestheticsScorer(ScoringStrategy):
    """Score based on overall subjective appeal.

    Uses aesthetics_score field (manual visual inspection from photos).
    Factors: Curb appeal, interior finishes, color scheme, modern vs dated.

    Scoring:
    - 10: Beautiful, modern, well-maintained
    - 5: Average/unknown
    - 0: Dated, unappealing, needs cosmetic work

    Data source: Listing photos
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize with scoring weights.

        Args:
            weights: Scoring weights config, defaults to standard weights
        """
        self._weights = weights or ScoringWeights()

    @property
    def name(self) -> str:
        return "Overall Aesthetics"

    @property
    def category(self) -> str:
        return "interior"

    @property
    def weight(self) -> int:
        return self._weights.aesthetics

    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score from manual aesthetics assessment.

        Args:
            property: Property to score

        Returns:
            Base score (0-10 from manual assessment, 5 if not assessed)
        """
        if property.aesthetics_score is None:
            return DEFAULT_NEUTRAL_SCORE
        return float(property.aesthetics_score)

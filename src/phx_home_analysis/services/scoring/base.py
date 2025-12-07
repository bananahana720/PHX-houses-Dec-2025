"""Abstract base classes for scoring strategies.

This module defines the abstract base class that all scoring strategies must
implement, providing a consistent interface for calculating property scores.
"""

from abc import ABC, abstractmethod

from ...domain.entities import Property
from ...domain.value_objects import Score


class ScoringStrategy(ABC):
    """Abstract base class for property scoring strategies.

    Each scoring strategy evaluates a specific criterion (e.g., school rating,
    roof condition) and returns a Score value object with base score (0-10 scale)
    and weighted score based on the criterion's importance.

    Subclasses must implement:
    - name: Human-readable criterion name
    - category: Scoring section ("location", "systems", or "interior")
    - weight: Maximum possible points for this criterion
    - calculate_base_score: Logic to compute 0-10 score from property data
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable criterion name.

        Returns:
            Criterion name for display (e.g., "School District Rating")
        """
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Scoring section category.

        Returns:
            One of: "location", "systems", or "interior"
        """
        pass

    @property
    @abstractmethod
    def weight(self) -> int:
        """Maximum possible points for this criterion.

        Returns:
            Weight in points (e.g., 50 for school district)
        """
        pass

    @abstractmethod
    def calculate_base_score(self, property: Property) -> float:
        """Calculate base score for this criterion on 0-10 scale.

        Args:
            property: Property entity to score

        Returns:
            Base score on 0-10 scale where:
            - 10 = Perfect/Ideal
            - 5 = Neutral/Unknown
            - 0 = Poor/Unacceptable
        """
        pass

    def calculate_weighted_score(self, property: Property, note: str | None = None) -> Score:
        """Calculate weighted score for this criterion.

        Computes base score (0-10) and converts to weighted score using the
        criterion's weight. Returns a Score value object with all details.

        Args:
            property: Property entity to score
            note: Optional explanatory note for score rationale

        Returns:
            Score value object with criterion, base score, weight, and note
        """
        base_score = self.calculate_base_score(property)
        return Score(
            criterion=self.name,
            base_score=base_score,
            weight=float(self.weight),
            note=note,
        )

    def __str__(self) -> str:
        """String representation shows criterion name and weight."""
        return f"{self.name} ({self.weight} pts max)"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}(name='{self.name}', "
            f"category='{self.category}', weight={self.weight})"
        )

"""Data models for school ratings and information."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SchoolData:
    """School ratings and counts for a location.

    GreatSchools ratings are on a 1-10 scale where:
        8-10: Above Average to Excellent
        5-7:  Average
        1-4:  Below Average to Struggling

    Attributes:
        elementary_rating: Best elementary school rating within 1 mile (1-10)
        middle_rating: Best middle school rating within 1 mile (1-10)
        high_rating: Best high school rating within 1 mile (1-10)
        school_count_1mi: Total number of schools within 1 mile
        source: Data source name
        extracted_at: Timestamp of extraction
    """

    elementary_rating: float | None = None
    middle_rating: float | None = None
    high_rating: float | None = None
    school_count_1mi: int | None = None
    source: str = "greatschools.org"
    extracted_at: datetime | None = None

    @classmethod
    def from_ratings(
        cls,
        elementary_rating: float | None = None,
        middle_rating: float | None = None,
        high_rating: float | None = None,
        school_count_1mi: int | None = None,
    ) -> "SchoolData":
        """Create SchoolData with timestamp.

        Args:
            elementary_rating: Best elementary rating (1-10)
            middle_rating: Best middle school rating (1-10)
            high_rating: Best high school rating (1-10)
            school_count_1mi: Total schools within 1 mile

        Returns:
            SchoolData instance with extraction timestamp
        """
        return cls(
            elementary_rating=elementary_rating,
            middle_rating=middle_rating,
            high_rating=high_rating,
            school_count_1mi=school_count_1mi,
            extracted_at=datetime.now(),
        )

    @property
    def overall_rating(self) -> float | None:
        """Calculate average of available school ratings.

        Returns:
            Average rating or None if no ratings available
        """
        ratings = [
            r
            for r in [self.elementary_rating, self.middle_rating, self.high_rating]
            if r is not None
        ]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)

    @property
    def rating_label(self) -> str:
        """Get label for overall school quality.

        Returns:
            Human-readable school quality label
        """
        rating = self.overall_rating
        if rating is None:
            return "Unknown"
        if rating >= 8:
            return "Excellent Schools"
        if rating >= 6:
            return "Above Average Schools"
        if rating >= 4:
            return "Average Schools"
        return "Below Average Schools"

"""Data models for Walk Score, Transit Score, and Bike Score."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class WalkScoreData:
    """Walk Score, Transit Score, and Bike Score for a location.

    Scores range from 0-100:
        90-100: Walker's/Biker's/Rider's Paradise
        70-89:  Very Walkable/Bikeable/Good Transit
        50-69:  Somewhat Walkable/Bikeable/Some Transit
        25-49:  Car-Dependent
        0-24:   Very Car-Dependent

    Attributes:
        walk_score: Walkability score (0-100)
        transit_score: Public transit score (0-100)
        bike_score: Bikeability score (0-100)
        source: Data source name
        extracted_at: Timestamp of extraction
    """

    walk_score: int | None = None
    transit_score: int | None = None
    bike_score: int | None = None
    source: str = "walkscore.com"
    extracted_at: datetime | None = None

    @classmethod
    def from_scores(
        cls,
        walk_score: int | None = None,
        transit_score: int | None = None,
        bike_score: int | None = None,
    ) -> "WalkScoreData":
        """Create WalkScoreData with timestamp.

        Args:
            walk_score: Walk score (0-100)
            transit_score: Transit score (0-100)
            bike_score: Bike score (0-100)

        Returns:
            WalkScoreData instance with extraction timestamp
        """
        return cls(
            walk_score=walk_score,
            transit_score=transit_score,
            bike_score=bike_score,
            extracted_at=datetime.now(),
        )

    @property
    def walkability_label(self) -> str:
        """Get walkability label from walk_score.

        Returns:
            Human-readable walkability label
        """
        if self.walk_score is None:
            return "Unknown"
        if self.walk_score >= 90:
            return "Walker's Paradise"
        if self.walk_score >= 70:
            return "Very Walkable"
        if self.walk_score >= 50:
            return "Somewhat Walkable"
        if self.walk_score >= 25:
            return "Car-Dependent"
        return "Very Car-Dependent"

    @property
    def transit_label(self) -> str:
        """Get transit label from transit_score.

        Returns:
            Human-readable transit label
        """
        if self.transit_score is None:
            return "Unknown"
        if self.transit_score >= 90:
            return "Rider's Paradise"
        if self.transit_score >= 70:
            return "Excellent Transit"
        if self.transit_score >= 50:
            return "Good Transit"
        if self.transit_score >= 25:
            return "Some Transit"
        return "Minimal Transit"

    @property
    def bike_label(self) -> str:
        """Get bike label from bike_score.

        Returns:
            Human-readable bike label
        """
        if self.bike_score is None:
            return "Unknown"
        if self.bike_score >= 90:
            return "Biker's Paradise"
        if self.bike_score >= 70:
            return "Very Bikeable"
        if self.bike_score >= 50:
            return "Bikeable"
        if self.bike_score >= 25:
            return "Somewhat Bikeable"
        return "Not Bikeable"

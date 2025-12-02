"""Data models for noise level assessments."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NoiseData:
    """Noise level assessment for a location.

    HowLoud noise scores range from 0-100 where 100 is quietest:
        80-100: Very Quiet
        60-79:  Quiet
        40-59:  Moderate
        20-39:  Loud
        0-19:   Very Loud

    Attributes:
        noise_score: Quietness score (0-100, 100=quietest)
        noise_sources: List of noise sources (e.g., ["traffic", "airport"])
        source: Data source name
        extracted_at: Timestamp of extraction
    """

    noise_score: int | None = None
    noise_sources: list[str] = field(default_factory=list)
    source: str = "howloud.com"
    extracted_at: datetime | None = None

    @classmethod
    def from_score(
        cls,
        noise_score: int | None,
        noise_sources: list[str] | None = None,
    ) -> "NoiseData":
        """Create NoiseData with timestamp.

        Args:
            noise_score: Noise score (0-100, 100=quietest)
            noise_sources: List of identified noise sources

        Returns:
            NoiseData instance with extraction timestamp
        """
        return cls(
            noise_score=noise_score,
            noise_sources=noise_sources or [],
            extracted_at=datetime.now(),
        )

    @property
    def noise_label(self) -> str:
        """Get noise level label from score.

        Returns:
            Human-readable noise level label
        """
        if self.noise_score is None:
            return "Unknown"
        if self.noise_score >= 80:
            return "Very Quiet"
        if self.noise_score >= 60:
            return "Quiet"
        if self.noise_score >= 40:
            return "Moderate"
        if self.noise_score >= 20:
            return "Loud"
        return "Very Loud"

    @property
    def is_quiet(self) -> bool:
        """Check if location is considered quiet (score >= 60).

        Returns:
            True if quiet or very quiet, False otherwise
        """
        return self.noise_score is not None and self.noise_score >= 60

    @property
    def primary_noise_source(self) -> str | None:
        """Get primary (first) noise source if available.

        Returns:
            Primary noise source or None
        """
        return self.noise_sources[0] if self.noise_sources else None

"""Data models for crime statistics."""

from dataclasses import dataclass
from datetime import datetime

from ...domain.enums import CrimeRiskLevel


@dataclass
class CrimeData:
    """Crime statistics for a location.

    Attributes:
        violent_crime_index: Violent crime safety index (0-100, 100=safest)
        property_crime_index: Property crime safety index (0-100, 100=safest)
        crime_risk_level: Overall crime risk classification
        source: Data source name
        extracted_at: Timestamp of extraction
    """

    violent_crime_index: float | None = None
    property_crime_index: float | None = None
    crime_risk_level: CrimeRiskLevel = CrimeRiskLevel.UNKNOWN
    source: str = "bestplaces.net"
    extracted_at: datetime | None = None

    @classmethod
    def from_indices(
        cls,
        violent_crime_index: float | None,
        property_crime_index: float | None,
    ) -> "CrimeData":
        """Create CrimeData with computed risk level.

        Computes overall crime_risk_level from average of violent and property indices.

        Args:
            violent_crime_index: Violent crime index (0-100, 100=safest)
            property_crime_index: Property crime index (0-100, 100=safest)

        Returns:
            CrimeData instance with computed risk level
        """
        # Compute average index for risk level classification
        if violent_crime_index is not None and property_crime_index is not None:
            avg_index = (violent_crime_index + property_crime_index) / 2
            risk_level = CrimeRiskLevel.from_index(avg_index)
        else:
            risk_level = CrimeRiskLevel.UNKNOWN

        return cls(
            violent_crime_index=violent_crime_index,
            property_crime_index=property_crime_index,
            crime_risk_level=risk_level,
            extracted_at=datetime.now(),
        )

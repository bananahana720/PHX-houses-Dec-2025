"""Data models for FEMA flood zone data extraction."""

from dataclasses import dataclass, field
from datetime import datetime

from phx_home_analysis.domain.enums import FloodZone


@dataclass
class FloodZoneData:
    """FEMA flood zone data for a property location.

    Extracted from FEMA National Flood Hazard Layer (NFHL) ArcGIS service.
    """

    flood_zone: FloodZone
    flood_zone_panel: str | None = None
    flood_insurance_required: bool = False
    effective_date: str | None = None  # When FIRM became effective
    zone_subtype: str | None = None  # Additional zone classification

    # Metadata
    source: str = "fema_nfhl"
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    # Geocoding
    latitude: float | None = None
    longitude: float | None = None

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for JSON serialization.

        Returns:
            Dictionary compatible with enrichment_data.json structure
        """
        return {
            "flood_zone": self.flood_zone.value,
            "flood_zone_panel": self.flood_zone_panel,
            "flood_insurance_required": self.flood_insurance_required,
            "flood_zone_effective_date": self.effective_date,
        }

    @property
    def risk_level(self) -> str:
        """Get human-readable risk level.

        Returns:
            Risk level string: 'high', 'moderate', 'minimal', or 'unknown'
        """
        return self.flood_zone.risk_level

    @property
    def description(self) -> str:
        """Get human-readable flood zone description.

        Returns:
            Description of flood zone and insurance requirements
        """
        risk = self.risk_level
        insurance = "Required" if self.flood_insurance_required else "Not Required"
        return f"Flood Zone {self.flood_zone.value.upper()}: {risk.capitalize()} risk - Insurance {insurance}"

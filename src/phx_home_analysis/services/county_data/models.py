"""Data models for county assessor data extraction."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParcelData:
    """Property data extracted from Maricopa County Assessor API.

    Contains all fields relevant for kill-switch evaluation and enrichment.
    """

    apn: str
    full_address: str

    # Kill-switch fields
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    sewer_type: str | None = None  # "city" or "septic"
    has_pool: bool | None = None
    beds: int | None = None
    baths: float | None = None

    # Tax and valuation
    tax_annual: float | None = None
    full_cash_value: int | None = None
    limited_value: int | None = None

    # Additional property info
    livable_sqft: int | None = None
    roof_type: str | None = None
    exterior_wall_type: str | None = None

    # Geocoding (from ArcGIS fallback)
    latitude: float | None = None
    longitude: float | None = None

    # Metadata
    source: str = "maricopa_assessor"

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for JSON serialization.

        Returns:
            Dictionary compatible with enrichment_data.json structure
        """
        return {
            "lot_sqft": self.lot_sqft,
            "year_built": self.year_built,
            "garage_spaces": self.garage_spaces,
            "sewer_type": self.sewer_type,
            "has_pool": self.has_pool,
            "tax_annual": self.tax_annual,
            # Preserve None for fields not from county API
            # These must come from other sources
        }


@dataclass
class ZoningData:
    """Zoning data extracted from Maricopa County GIS.

    Provides zoning classification for property location.
    """

    zoning_code: str
    zoning_description: str | None = None
    zoning_category: str | None = None  # residential, commercial, industrial, mixed

    # Geocoding
    latitude: float | None = None
    longitude: float | None = None

    # Metadata
    source: str = "maricopa_gis"
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for JSON serialization.

        Returns:
            Dictionary compatible with enrichment_data.json structure
        """
        return {
            "zoning_code": self.zoning_code,
            "zoning_description": self.zoning_description,
            "zoning_category": self.zoning_category,
        }

    @property
    def is_residential(self) -> bool:
        """Check if zoning is residential.

        Returns:
            True if residential zoning
        """
        if self.zoning_category:
            return self.zoning_category.lower() == "residential"

        # Fallback: check code prefix
        if self.zoning_code:
            code_upper = self.zoning_code.upper()
            return code_upper.startswith(("R", "RS", "R1", "R2", "R3"))

        return False

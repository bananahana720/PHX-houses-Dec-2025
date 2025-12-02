"""Data models for county assessor data extraction."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParcelData:
    """Property data extracted from Maricopa County Assessor API.

    Contains all fields relevant for kill-switch evaluation and enrichment.
    """

    apn: str
    full_address: str

    # Kill-switch fields
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    garage_spaces: Optional[int] = None
    sewer_type: Optional[str] = None  # "city" or "septic"
    has_pool: Optional[bool] = None
    beds: Optional[int] = None
    baths: Optional[float] = None

    # Tax and valuation
    tax_annual: Optional[int] = None
    full_cash_value: Optional[int] = None
    limited_value: Optional[int] = None

    # Additional property info
    livable_sqft: Optional[int] = None
    roof_type: Optional[str] = None
    exterior_wall_type: Optional[str] = None

    # Geocoding (from ArcGIS fallback)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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

"""Data models for county assessor data extraction."""

from dataclasses import dataclass


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

"""Data models for building permit history.

Permit data helps estimate:
- Roof age (last roofing permit vs year_built)
- HVAC age (last mechanical permit)
- Major renovations (remodel permits)
- Addition/expansion history

Data Source: Maricopa County GIS Building Permits Layer
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PermitType(Enum):
    """Common building permit types."""

    ROOFING = "roofing"
    MECHANICAL = "mechanical"  # HVAC
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    REMODEL = "remodel"
    ADDITION = "addition"
    POOL = "pool"
    SOLAR = "solar"
    OTHER = "other"

    @classmethod
    def from_description(cls, desc: str | None) -> "PermitType":
        """Infer permit type from description text."""
        if not desc:
            return cls.OTHER

        desc_lower = desc.lower()

        if any(kw in desc_lower for kw in ["roof", "shingle", "tile roof"]):
            return cls.ROOFING
        if any(kw in desc_lower for kw in ["hvac", "a/c", "ac ", "heat", "furnace", "mechanical"]):
            return cls.MECHANICAL
        if any(kw in desc_lower for kw in ["electric", "panel", "outlet", "wiring"]):
            return cls.ELECTRICAL
        if any(kw in desc_lower for kw in ["plumb", "water heater", "sewer", "drain"]):
            return cls.PLUMBING
        if any(kw in desc_lower for kw in ["remodel", "renovation", "alteration"]):
            return cls.REMODEL
        if any(kw in desc_lower for kw in ["addition", "expand", "extend"]):
            return cls.ADDITION
        if any(kw in desc_lower for kw in ["pool", "spa"]):
            return cls.POOL
        if any(kw in desc_lower for kw in ["solar", "pv ", "photovoltaic"]):
            return cls.SOLAR

        return cls.OTHER


@dataclass
class Permit:
    """Individual building permit record."""

    permit_number: str | None = None
    permit_type: PermitType = PermitType.OTHER
    description: str | None = None
    issue_date: str | None = None  # ISO 8601 format
    final_date: str | None = None  # ISO 8601 format
    status: str | None = None  # ISSUED, FINAL, EXPIRED
    valuation: float | None = None  # Dollar value of work

    @property
    def year_issued(self) -> int | None:
        """Extract year from issue_date."""
        if not self.issue_date:
            return None
        try:
            return int(self.issue_date[:4])
        except (ValueError, IndexError):
            return None


@dataclass
class PermitHistory:
    """Permit history for a property.

    Aggregates all permits and provides derived fields for scoring.

    Attributes:
        permits: List of individual permit records
        parcel_number: APN/parcel identifier
        source: Data source identifier
        extracted_at: Timestamp of extraction
    """

    permits: list[Permit] = field(default_factory=list)
    parcel_number: str | None = None
    source: str = "maricopa_gis"
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    latitude: float | None = None
    longitude: float | None = None

    @property
    def permit_count(self) -> int:
        """Total number of permits."""
        return len(self.permits)

    @property
    def permit_types(self) -> list[str]:
        """Unique permit types found."""
        return list({p.permit_type.value for p in self.permits})

    @property
    def last_roof_permit_year(self) -> int | None:
        """Year of most recent roofing permit."""
        roof_permits = [p for p in self.permits if p.permit_type == PermitType.ROOFING]
        if not roof_permits:
            return None
        years = [p.year_issued for p in roof_permits if p.year_issued]
        return max(years) if years else None

    @property
    def last_hvac_permit_year(self) -> int | None:
        """Year of most recent HVAC/mechanical permit."""
        hvac_permits = [p for p in self.permits if p.permit_type == PermitType.MECHANICAL]
        if not hvac_permits:
            return None
        years = [p.year_issued for p in hvac_permits if p.year_issued]
        return max(years) if years else None

    @property
    def last_permit_date(self) -> str | None:
        """Most recent permit issue date (any type)."""
        if not self.permits:
            return None
        dates = [p.issue_date for p in self.permits if p.issue_date]
        return max(dates) if dates else None

    @property
    def has_solar_permit(self) -> bool:
        """Check if property has solar installation permit."""
        return any(p.permit_type == PermitType.SOLAR for p in self.permits)

    @property
    def has_pool_permit(self) -> bool:
        """Check if property has pool permit."""
        return any(p.permit_type == PermitType.POOL for p in self.permits)

    @property
    def total_valuation(self) -> float:
        """Sum of all permit valuations."""
        return sum(p.valuation or 0 for p in self.permits)

    def get_estimated_roof_age(self, current_year: int, year_built: int | None) -> int | None:
        """Estimate roof age using permit data or year_built fallback.

        Args:
            current_year: Current year for age calculation
            year_built: Property year built (fallback)

        Returns:
            Estimated roof age in years, or None if unknown
        """
        if self.last_roof_permit_year:
            return current_year - self.last_roof_permit_year
        if year_built:
            return current_year - year_built
        return None

    def get_estimated_hvac_age(self, current_year: int, year_built: int | None) -> int | None:
        """Estimate HVAC age using permit data or year_built fallback.

        In Arizona, HVAC typically lasts 10-15 years (shorter than national avg).

        Args:
            current_year: Current year for age calculation
            year_built: Property year built (fallback)

        Returns:
            Estimated HVAC age in years, or None if unknown
        """
        if self.last_hvac_permit_year:
            return current_year - self.last_hvac_permit_year
        if year_built:
            # Assume HVAC replaced every 12 years in AZ
            age_from_built = current_year - year_built
            # If house is old enough, assume at least one replacement
            if age_from_built > 15:
                return age_from_built % 12  # Estimate based on replacement cycle
            return age_from_built
        return None

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for merging into enrichment_data.json.

        Returns:
            Dictionary with permit fields for enrichment
        """
        return {
            "permit_count": self.permit_count,
            "permit_types": self.permit_types,
            "last_roof_permit_year": self.last_roof_permit_year,
            "last_hvac_permit_year": self.last_hvac_permit_year,
            "last_permit_date": self.last_permit_date,
            "has_solar_permit": self.has_solar_permit,
            "has_pool_permit": self.has_pool_permit,
            "permit_total_valuation": self.total_valuation,
            "permit_data_source": self.source,
        }

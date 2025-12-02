"""Pydantic schemas for property data validation.

This module defines Pydantic models for validating property and enrichment data
with comprehensive field constraints, cross-field validation, and business rules.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class SewerTypeSchema(str, Enum):
    """Sewer system type enumeration for validation."""

    CITY = "city"
    SEPTIC = "septic"
    UNKNOWN = "unknown"


class SolarStatusSchema(str, Enum):
    """Solar panel ownership status enumeration."""

    OWNED = "owned"
    LEASED = "leased"
    NONE = "none"
    UNKNOWN = "unknown"


class OrientationSchema(str, Enum):
    """Property orientation (direction front facade faces)."""

    N = "north"
    S = "south"
    E = "east"
    W = "west"
    NE = "northeast"
    NW = "northwest"
    SE = "southeast"
    SW = "southwest"
    UNKNOWN = "unknown"


class PropertySchema(BaseModel):
    """Pydantic schema for property data validation.

    Validates core property listing data with field constraints and cross-field
    validation rules. All fields correspond to data from listings and county records.

    Attributes:
        address: Full property address (minimum 5 characters)
        beds: Number of bedrooms (1-20)
        baths: Number of bathrooms (0.5-20, supports half baths)
        sqft: Living area square footage (100-100,000)
        lot_sqft: Lot size in square feet (0-500,000)
        year_built: Year property was constructed (1800-2030)
        price: Property listing price in dollars (>= 0)
        hoa_fee: Monthly HOA fee (>= 0, None for no HOA)
        garage_spaces: Number of garage spaces (0-10)
        has_pool: Whether property has a pool
        pool_equipment_age: Age of pool equipment in years (requires has_pool=True)
        sewer_type: City sewer or septic system
    """

    address: str = Field(..., min_length=5, description="Full property address")
    beds: int = Field(..., ge=1, le=20, description="Number of bedrooms")
    baths: float = Field(..., ge=0.5, le=20, description="Number of bathrooms")
    sqft: int = Field(..., ge=100, le=100000, description="Living area square feet")
    lot_sqft: int | None = Field(None, ge=0, le=500000, description="Lot size sqft")
    year_built: int | None = Field(None, ge=1800, le=2030, description="Year built")
    price: int = Field(..., ge=0, description="Listing price in dollars")
    hoa_fee: float | None = Field(None, ge=0, description="Monthly HOA fee")
    garage_spaces: int | None = Field(None, ge=0, le=10, description="Garage spaces")
    has_pool: bool | None = Field(None, description="Has swimming pool")
    pool_equipment_age: int | None = Field(
        None, ge=0, le=50, description="Pool equipment age in years"
    )
    sewer_type: SewerTypeSchema | None = Field(None, description="Sewer system type")
    roof_age: int | None = Field(None, ge=0, le=100, description="Roof age in years")
    hvac_age: int | None = Field(None, ge=0, le=50, description="HVAC age in years")
    solar_status: SolarStatusSchema | None = Field(None, description="Solar status")
    orientation: OrientationSchema | None = Field(None, description="Property orientation")

    model_config = {"str_strip_whitespace": True, "validate_assignment": True}

    @field_validator("address")
    @classmethod
    def validate_address_format(cls, v: str) -> str:
        """Validate address contains minimal structure."""
        if not v or len(v.strip()) < 5:
            raise ValueError("Address must be at least 5 characters")
        # Basic check for address-like structure (contains a number)
        if not any(c.isdigit() for c in v):
            raise ValueError("Address should contain a street number")
        return v.strip()

    @field_validator("baths")
    @classmethod
    def validate_baths_increment(cls, v: float) -> float:
        """Validate baths are in 0.5 increments."""
        if v % 0.5 != 0:
            raise ValueError("Baths must be in 0.5 increments (e.g., 1.0, 1.5, 2.0)")
        return v

    @model_validator(mode="after")
    def validate_pool_age_requires_pool(self) -> "PropertySchema":
        """Ensure pool_equipment_age is only set when has_pool=True."""
        if self.pool_equipment_age is not None and not self.has_pool:
            raise ValueError("pool_equipment_age requires has_pool=True")
        return self

    @model_validator(mode="after")
    def validate_year_built_reasonable(self) -> "PropertySchema":
        """Validate year_built is reasonable for property age calculations."""
        if self.year_built is not None:
            import datetime

            current_year = datetime.datetime.now().year
            if self.year_built > current_year:
                raise ValueError(f"year_built ({self.year_built}) cannot be in the future")
        return self


class EnrichmentDataSchema(BaseModel):
    """Schema for enrichment data validation.

    Validates data collected from external sources including county assessor,
    school ratings, geographic analysis, and property inspections.

    Attributes:
        full_address: Property address for matching (required)
        school_rating: GreatSchools rating (1-10 scale)
        safety_neighborhood_score: Neighborhood safety score (0-10)
        noise_level: Ambient noise level score (0-10, lower is quieter)
        commute_minutes: Commute time to work location
        distance_to_grocery_miles: Distance to nearest supermarket
        distance_to_highway_miles: Distance to nearest highway
        kitchen_layout_score: Kitchen quality assessment (0-10)
        master_suite_score: Master bedroom/bath quality (0-10)
        natural_light_score: Natural lighting quality (0-10)
        high_ceilings_score: Ceiling height/volume score (0-10)
        laundry_area_score: Laundry room quality (0-10)
        aesthetics_score: Overall aesthetic appeal (0-10)
        backyard_utility_score: Backyard functionality (0-10)
        parks_walkability_score: Access to parks/trails (0-10)
    """

    full_address: str = Field(..., min_length=5, description="Property address for matching")

    # Core property data (for kill switch evaluation)
    beds: int | None = Field(None, ge=1, le=20, description="Number of bedrooms")
    baths: float | None = Field(None, ge=0.5, le=20, description="Number of bathrooms")
    lot_sqft: int | None = Field(None, ge=0, le=500000, description="Lot size in sqft")
    year_built: int | None = Field(None, ge=1800, le=2030, description="Year built")
    garage_spaces: int | None = Field(None, ge=0, le=10, description="Garage spaces")
    sewer_type: str | None = Field(None, description="Sewer type: city, septic, unknown")
    hoa_fee: float | None = Field(None, ge=0, description="Monthly HOA fee (0 = no HOA)")
    tax_annual: float | None = Field(None, ge=0, description="Annual property tax")
    has_pool: bool | None = Field(None, description="Has swimming pool")
    list_price: int | None = Field(None, ge=0, description="Listing price")

    # Location scores (Section A)
    school_rating: float | None = Field(
        None, ge=1, le=10, description="GreatSchools rating 1-10"
    )
    safety_neighborhood_score: float | None = Field(
        None, ge=0, le=10, description="Neighborhood safety 0-10"
    )
    noise_level: float | None = Field(
        None, ge=0, le=10, description="Noise level 0-10 (lower is quieter)"
    )
    commute_minutes: int | None = Field(
        None, ge=0, le=180, description="Commute time in minutes"
    )
    distance_to_grocery_miles: float | None = Field(
        None, ge=0, le=50, description="Distance to grocery store"
    )
    distance_to_highway_miles: float | None = Field(
        None, ge=0, le=50, description="Distance to highway"
    )

    # Interior scores (Section C)
    kitchen_layout_score: float | None = Field(
        None, ge=0, le=10, description="Kitchen quality 0-10"
    )
    master_suite_score: float | None = Field(
        None, ge=0, le=10, description="Master suite quality 0-10"
    )
    natural_light_score: float | None = Field(
        None, ge=0, le=10, description="Natural lighting 0-10"
    )
    high_ceilings_score: float | None = Field(
        None, ge=0, le=10, description="Ceiling height 0-10"
    )
    laundry_area_score: float | None = Field(
        None, ge=0, le=10, description="Laundry area quality 0-10"
    )
    aesthetics_score: float | None = Field(
        None, ge=0, le=10, description="Overall aesthetics 0-10"
    )
    backyard_utility_score: float | None = Field(
        None, ge=0, le=10, description="Backyard functionality 0-10"
    )
    parks_walkability_score: float | None = Field(
        None, ge=0, le=10, description="Parks access 0-10"
    )
    fireplace_present: bool | None = Field(None, description="Has fireplace")

    # Systems (Section B) - ages and conditions
    roof_age: int | None = Field(None, ge=0, le=100, description="Roof age in years")
    hvac_age: int | None = Field(None, ge=0, le=50, description="HVAC system age")
    pool_equipment_age: int | None = Field(None, ge=0, le=50, description="Pool equip age")

    # Arizona-specific
    orientation: str | None = Field(None, description="Property orientation N/S/E/W")
    solar_status: str | None = Field(None, description="Solar ownership status")
    solar_lease_monthly: int | None = Field(
        None, ge=0, le=500, description="Monthly solar lease payment"
    )

    # Metadata fields (prefixed with _) for tracking data freshness
    # These are optional timestamps in ISO 8601 format
    # Note: Pydantic doesn't support fields starting with _ directly,
    # so we use model_config extra="allow" to accept them

    model_config = {
        "str_strip_whitespace": True,
        "extra": "allow",  # Allow metadata fields like _last_updated, _last_county_sync
    }

    @field_validator("orientation")
    @classmethod
    def validate_orientation(cls, v: str | None) -> str | None:
        """Validate orientation is a recognized value."""
        if v is None:
            return None
        v_lower = v.strip().lower()
        valid = {
            "n",
            "north",
            "s",
            "south",
            "e",
            "east",
            "w",
            "west",
            "ne",
            "northeast",
            "nw",
            "northwest",
            "se",
            "southeast",
            "sw",
            "southwest",
            "unknown",
        }
        if v_lower not in valid:
            raise ValueError(f"Invalid orientation: {v}. Must be one of: {sorted(valid)}")
        return v_lower

    @field_validator("solar_status")
    @classmethod
    def validate_solar_status(cls, v: str | None) -> str | None:
        """Validate solar status is a recognized value."""
        if v is None:
            return None
        v_lower = v.strip().lower()
        valid = {"owned", "leased", "none", "unknown"}
        if v_lower not in valid:
            raise ValueError(f"Invalid solar_status: {v}. Must be one of: {sorted(valid)}")
        return v_lower


class KillSwitchCriteriaSchema(BaseModel):
    """Schema for validating kill-switch evaluation inputs.

    Used to validate that a property has sufficient data to evaluate
    kill-switch criteria before running the filter.

    Attributes:
        beds: Minimum 4 required
        baths: Minimum 2 required
        lot_sqft: Must be 7,000-15,000
        garage_spaces: Minimum 2 required
        hoa_fee: Must be 0 or None (no HOA)
        sewer_type: Must be 'city'
        year_built: Must be < 2024
    """

    beds: int = Field(..., ge=4, description="Minimum 4 bedrooms required")
    baths: float = Field(..., ge=2, description="Minimum 2 bathrooms required")
    lot_sqft: int = Field(..., ge=7000, le=15000, description="Lot must be 7k-15k sqft")
    garage_spaces: int = Field(..., ge=2, description="Minimum 2-car garage required")
    hoa_fee: float | None = Field(None, le=0, description="No HOA allowed (fee must be 0)")
    sewer_type: SewerTypeSchema = Field(
        SewerTypeSchema.CITY, description="City sewer required"
    )
    year_built: int = Field(..., description="No new builds (pre-current year)")

    @field_validator("year_built")
    @classmethod
    def validate_year_built_not_new(cls, v: int) -> int:
        """Validate year_built is before current year (no new builds)."""
        from datetime import datetime
        current_year = datetime.now().year
        if v >= current_year:
            raise ValueError(f"year_built must be before {current_year} (no new builds)")
        return v

    @field_validator("hoa_fee")
    @classmethod
    def validate_no_hoa(cls, v: float | None) -> float | None:
        """Validate HOA fee is 0 or None."""
        if v is not None and v > 0:
            raise ValueError("Property has HOA fee - kill switch failed")
        return v

    @field_validator("sewer_type")
    @classmethod
    def validate_city_sewer(cls, v: SewerTypeSchema) -> SewerTypeSchema:
        """Validate sewer type is city."""
        if v != SewerTypeSchema.CITY:
            raise ValueError(f"Sewer type must be 'city', got '{v.value}'")
        return v

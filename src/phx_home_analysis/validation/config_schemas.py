"""Pydantic schemas for configuration validation.

This module provides Pydantic models for validating scoring weights and buyer criteria
configuration loaded from YAML files. All schemas include strict validation with
helpful error messages.

Configuration Hierarchy:
    AppConfigSchema
    ├── ScoringWeightsConfigSchema (scoring_weights.yaml)
    │   ├── ValueZonesSchema
    │   ├── SectionWeightsSchema
    │   ├── TierThresholdsSchema
    │   └── defaults (optional)
    └── BuyerCriteriaConfigSchema (buyer_criteria.yaml)
        ├── HardCriteriaSchema
        ├── SoftCriteriaSchema
        └── ThresholdsSchema

Example:
    >>> from phx_home_analysis.validation.config_schemas import ScoringWeightsConfigSchema
    >>> config = ScoringWeightsConfigSchema(**yaml_data)
    >>> config.section_weights.location.points
    250
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================


class ConfigurationError(Exception):
    """Raised when configuration validation fails.

    This exception provides detailed error messages with:
    - Source file path
    - Field path (nested field location)
    - Invalid value
    - Valid range or example
    - Human-readable explanation

    Example:
        ConfigurationError: Invalid configuration in config/scoring_weights.yaml
          Field: section_weights.location.points
          Value: -50 (int)
          Error: Must be positive integer (0-605)
          Example: points: 250
    """

    pass


# =============================================================================
# VALUE ZONE SCHEMAS (scoring_weights.yaml:10-22)
# =============================================================================


class ValueZoneSchema(BaseModel):
    """Schema for a single value zone definition.

    Attributes:
        min_score: Minimum score to qualify for this zone (0-605)
        max_price: Maximum price for this zone (None = no limit)
        label: Display label for visualization
        description: Human-readable description
    """

    model_config = ConfigDict(extra="forbid")

    min_score: Annotated[int, Field(ge=0, le=605, description="Minimum score (0-605)")]
    max_price: Annotated[
        int | None,
        Field(default=None, ge=0, description="Maximum price (None = no limit)"),
    ]
    label: Annotated[str, Field(min_length=1, description="Display label")]
    description: Annotated[str, Field(min_length=1, description="Zone description")]


class ValueZonesSchema(BaseModel):
    """Schema for value zones configuration.

    Defines regions in the score/price scatter plot for property classification.

    Attributes:
        sweet_spot: High-quality affordable properties zone
        premium: Top-tier properties zone (Unicorn territory)
    """

    model_config = ConfigDict(extra="forbid")

    sweet_spot: ValueZoneSchema
    premium: ValueZoneSchema


# =============================================================================
# SECTION WEIGHTS SCHEMAS (scoring_weights.yaml:29-61)
# =============================================================================


class LocationCriteriaSchema(BaseModel):
    """Schema for location section criteria weights.

    Attributes:
        school: School rating weight (0-100)
        quietness: Noise/highway distance weight (0-100)
        crime_index: Crime index weight (0-100)
        supermarket: Grocery proximity weight (0-100)
        parks: Parks/walkability weight (0-100)
        sun_orientation: Sun exposure weight (0-100)
        flood_risk: Flood zone risk weight (0-100)
        walk_transit: Walk/Transit/Bike score weight (0-100)
        air_quality: Air quality index weight (0-100)
    """

    model_config = ConfigDict(extra="forbid")

    school: Annotated[int, Field(ge=0, le=100, description="School rating weight")]
    quietness: Annotated[int, Field(ge=0, le=100, description="Noise/highway distance weight")]
    crime_index: Annotated[int, Field(ge=0, le=100, description="Crime index weight")]
    supermarket: Annotated[int, Field(ge=0, le=100, description="Grocery proximity weight")]
    parks: Annotated[int, Field(ge=0, le=100, description="Parks/walkability weight")]
    sun_orientation: Annotated[int, Field(ge=0, le=100, description="Sun exposure weight")]
    flood_risk: Annotated[int, Field(ge=0, le=100, description="Flood zone risk weight")]
    walk_transit: Annotated[int, Field(ge=0, le=100, description="Walk/Transit/Bike score weight")]
    air_quality: Annotated[int, Field(ge=0, le=100, description="Air quality index weight")]


class SystemsCriteriaSchema(BaseModel):
    """Schema for systems section criteria weights.

    Attributes:
        roof: Roof condition weight (0-100)
        backyard: Backyard utility weight (0-100)
        plumbing: Plumbing/electrical weight (0-100)
        pool: Pool condition weight (0-100)
        cost_efficiency: Monthly cost weight (0-100)
        solar_status: Solar panel ownership status weight (0-100)
    """

    model_config = ConfigDict(extra="forbid")

    roof: Annotated[int, Field(ge=0, le=100, description="Roof condition weight")]
    backyard: Annotated[int, Field(ge=0, le=100, description="Backyard utility weight")]
    plumbing: Annotated[int, Field(ge=0, le=100, description="Plumbing/electrical weight")]
    pool: Annotated[int, Field(ge=0, le=100, description="Pool condition weight")]
    cost_efficiency: Annotated[int, Field(ge=0, le=100, description="Monthly cost weight")]
    solar_status: Annotated[int, Field(ge=0, le=100, description="Solar status weight")]


class InteriorCriteriaSchema(BaseModel):
    """Schema for interior section criteria weights.

    Attributes:
        kitchen: Kitchen layout weight (0-100)
        master_bedroom: Master suite weight (0-100)
        light: Natural light weight (0-100)
        ceilings: Ceiling height weight (0-100)
        fireplace: Fireplace weight (0-100)
        laundry: Laundry area weight (0-100)
        aesthetics: Overall aesthetics weight (0-100)
    """

    model_config = ConfigDict(extra="forbid")

    kitchen: Annotated[int, Field(ge=0, le=100, description="Kitchen layout weight")]
    master_bedroom: Annotated[int, Field(ge=0, le=100, description="Master suite weight")]
    light: Annotated[int, Field(ge=0, le=100, description="Natural light weight")]
    ceilings: Annotated[int, Field(ge=0, le=100, description="Ceiling height weight")]
    fireplace: Annotated[int, Field(ge=0, le=100, description="Fireplace weight")]
    laundry: Annotated[int, Field(ge=0, le=100, description="Laundry area weight")]
    aesthetics: Annotated[int, Field(ge=0, le=100, description="Overall aesthetics weight")]


class SectionWeightSchema(BaseModel):
    """Schema for a single scoring section.

    Attributes:
        points: Total points for this section (0-605)
        weight: Section weight as fraction (0.0-1.0)
        criteria: Criteria weights within this section
    """

    model_config = ConfigDict(extra="forbid")

    points: Annotated[int, Field(ge=0, le=605, description="Section points (0-605)")]
    weight: Annotated[float, Field(ge=0.0, le=1.0, description="Section weight (0.0-1.0)")]
    criteria: LocationCriteriaSchema | SystemsCriteriaSchema | InteriorCriteriaSchema


class LocationSectionSchema(BaseModel):
    """Schema for location section weight."""

    model_config = ConfigDict(extra="forbid")

    points: Annotated[int, Field(ge=0, le=605, description="Section points (0-605)")]
    weight: Annotated[float, Field(ge=0.0, le=1.0, description="Section weight (0.0-1.0)")]
    criteria: LocationCriteriaSchema


class SystemsSectionSchema(BaseModel):
    """Schema for systems section weight."""

    model_config = ConfigDict(extra="forbid")

    points: Annotated[int, Field(ge=0, le=605, description="Section points (0-605)")]
    weight: Annotated[float, Field(ge=0.0, le=1.0, description="Section weight (0.0-1.0)")]
    criteria: SystemsCriteriaSchema


class InteriorSectionSchema(BaseModel):
    """Schema for interior section weight."""

    model_config = ConfigDict(extra="forbid")

    points: Annotated[int, Field(ge=0, le=605, description="Section points (0-605)")]
    weight: Annotated[float, Field(ge=0.0, le=1.0, description="Section weight (0.0-1.0)")]
    criteria: InteriorCriteriaSchema


class SectionWeightsSchema(BaseModel):
    """Schema for all scoring section weights.

    Validates that:
    - Total points across sections = 605
    - Total weight across sections = 1.0 (within tolerance)

    Attributes:
        location: Location section (Section A)
        systems: Systems section (Section B)
        interior: Interior section (Section C)
    """

    model_config = ConfigDict(extra="forbid")

    location: LocationSectionSchema
    systems: SystemsSectionSchema
    interior: InteriorSectionSchema

    @model_validator(mode="after")
    def validate_totals(self) -> SectionWeightsSchema:
        """Validate that section totals are correct."""
        total_points = self.location.points + self.systems.points + self.interior.points
        total_weight = self.location.weight + self.systems.weight + self.interior.weight

        if total_points != 605:
            raise ValueError(
                f"Total section points must equal 605, got {total_points} "
                f"(location={self.location.points}, systems={self.systems.points}, "
                f"interior={self.interior.points})"
            )

        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                f"Total section weights must equal 1.0, got {total_weight:.4f} "
                f"(location={self.location.weight}, systems={self.systems.weight}, "
                f"interior={self.interior.weight})"
            )

        return self


# =============================================================================
# TIER THRESHOLD SCHEMAS (scoring_weights.yaml:68-82)
# =============================================================================


class TierThresholdSchema(BaseModel):
    """Schema for a single tier threshold.

    Attributes:
        min_score: Minimum score to qualify for this tier (0-605)
        label: Tier display label
        description: Tier description
    """

    model_config = ConfigDict(extra="forbid")

    min_score: Annotated[int, Field(ge=0, le=605, description="Minimum score (0-605)")]
    label: Annotated[str, Field(min_length=1, description="Tier label")]
    description: Annotated[str, Field(min_length=1, description="Tier description")]


class TierThresholdsSchema(BaseModel):
    """Schema for tier thresholds configuration.

    Validates that tier thresholds are correctly ordered:
    unicorn.min_score > contender.min_score > pass_.min_score

    Attributes:
        unicorn: Exceptional properties threshold
        contender: Good properties threshold
        pass_: Acceptable properties threshold (aliased from 'pass')
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    unicorn: TierThresholdSchema
    contender: TierThresholdSchema
    pass_: TierThresholdSchema = Field(alias="pass")

    @model_validator(mode="after")
    def validate_tier_ordering(self) -> TierThresholdsSchema:
        """Validate tier thresholds are correctly ordered."""
        if self.unicorn.min_score <= self.contender.min_score:
            raise ValueError(
                f"unicorn.min_score ({self.unicorn.min_score}) must be greater than "
                f"contender.min_score ({self.contender.min_score})"
            )

        if self.contender.min_score <= self.pass_.min_score:
            raise ValueError(
                f"contender.min_score ({self.contender.min_score}) must be greater than "
                f"pass.min_score ({self.pass_.min_score})"
            )

        return self


# =============================================================================
# SCORING WEIGHTS CONFIG SCHEMA (complete scoring_weights.yaml)
# =============================================================================


class DefaultsSchema(BaseModel):
    """Schema for default values configuration.

    Attributes:
        value_zone_min_score: Default minimum score for value zone
        value_zone_max_price: Default maximum price for value zone
    """

    model_config = ConfigDict(extra="allow")

    value_zone_min_score: Annotated[
        int, Field(default=363, ge=0, le=605, description="Default min score")
    ]
    value_zone_max_price: Annotated[
        int, Field(default=550000, ge=0, description="Default max price")
    ]


class ScoringWeightsConfigSchema(BaseModel):
    """Complete schema for scoring_weights.yaml.

    Attributes:
        value_zones: Score/price analysis zones
        section_weights: Scoring section weights (605 points total)
        tier_thresholds: Tier classification thresholds
        defaults: Default values for backward compatibility
    """

    model_config = ConfigDict(extra="forbid")

    value_zones: ValueZonesSchema
    section_weights: SectionWeightsSchema
    tier_thresholds: TierThresholdsSchema
    defaults: DefaultsSchema | None = None


# =============================================================================
# BUYER CRITERIA SCHEMAS (buyer_criteria.yaml)
# =============================================================================


class HardCriteriaSchema(BaseModel):
    """Schema for hard kill-switch criteria (instant fail).

    All hard criteria must pass or the property is immediately rejected.
    All 8 default criteria are HARD (no SOFT criteria).

    Attributes:
        hoa_fee: Maximum HOA fee allowed (0 = no HOA)
        min_beds: Minimum bedrooms required
        min_baths: Minimum bathrooms required
        min_sqft: Minimum living space sqft required
        min_lot_sqft: Minimum lot size sqft required
        sewer_type: Required sewer type (city)
        min_garage: Minimum indoor garage spaces required
        solar_lease: Whether solar lease allowed (False = not allowed)
    """

    model_config = ConfigDict(extra="forbid")

    hoa_fee: Annotated[int, Field(ge=0, description="Maximum HOA fee (0 = no HOA allowed)")]
    min_beds: Annotated[int, Field(ge=1, le=10, description="Minimum bedrooms (1-10)")]
    min_baths: Annotated[
        int | float, Field(ge=1.0, le=10.0, description="Minimum bathrooms (1.0-10.0)")
    ]
    min_sqft: Annotated[int, Field(ge=0, description="Minimum living space sqft")]
    min_lot_sqft: Annotated[int, Field(ge=0, description="Minimum lot size sqft")]
    sewer_type: Annotated[
        Literal["city", "city_sewer", "municipal", "public"],
        Field(description="Required sewer type"),
    ]
    min_garage: Annotated[int, Field(ge=0, le=10, description="Minimum indoor garage spaces")]
    solar_lease: Annotated[
        bool, Field(description="Whether solar lease allowed (False = not allowed)")
    ]


class SewerCriterionSchema(BaseModel):
    """Schema for sewer type criterion.

    Attributes:
        required: Required sewer type value
        severity: Severity weight if criterion fails (0.0-10.0)
    """

    model_config = ConfigDict(extra="forbid")

    required: Literal["city", "city_sewer", "municipal", "public"]
    severity: Annotated[float, Field(ge=0.0, le=10.0, description="Severity weight (0.0-10.0)")]


class YearBuiltCriterionSchema(BaseModel):
    """Schema for year built criterion.

    Attributes:
        max: Maximum year (int or 'current_year' token)
        severity: Severity weight if criterion fails (0.0-10.0)
    """

    model_config = ConfigDict(extra="forbid")

    max: str | int = Field(description="Max year or 'current_year' token")
    severity: Annotated[float, Field(ge=0.0, le=10.0, description="Severity weight (0.0-10.0)")]

    @field_validator("max")
    @classmethod
    def validate_max_year(cls, v: str | int) -> str | int:
        """Validate max year is reasonable or 'current_year' token."""
        if isinstance(v, str):
            if v != "current_year":
                raise ValueError(f"max must be an integer or 'current_year', got '{v}'")
        elif isinstance(v, int):
            current_year = datetime.now().year
            if v < 1900 or v > current_year + 5:
                raise ValueError(f"max year must be between 1900 and {current_year + 5}, got {v}")
        return v

    def get_max_year(self) -> int:
        """Get the actual max year value, resolving 'current_year' token."""
        if self.max == "current_year":
            return datetime.now().year
        return int(self.max)


class GarageCriterionSchema(BaseModel):
    """Schema for garage spaces criterion.

    Attributes:
        min: Minimum garage spaces required
        severity: Severity weight if criterion fails (0.0-10.0)
    """

    model_config = ConfigDict(extra="forbid")

    min: Annotated[int, Field(ge=0, le=10, description="Minimum garage spaces (0-10)")]
    severity: Annotated[float, Field(ge=0.0, le=10.0, description="Severity weight (0.0-10.0)")]


class LotSizeCriterionSchema(BaseModel):
    """Schema for lot size criterion.

    Validates that max > min.

    Attributes:
        min: Minimum lot size in sqft
        max: Maximum lot size in sqft
        severity: Severity weight if criterion fails (0.0-10.0)
    """

    model_config = ConfigDict(extra="forbid")

    min: Annotated[int, Field(ge=0, description="Minimum lot size in sqft")]
    max: Annotated[int, Field(ge=0, description="Maximum lot size in sqft")]
    severity: Annotated[float, Field(ge=0.0, le=10.0, description="Severity weight (0.0-10.0)")]

    @model_validator(mode="after")
    def validate_max_gt_min(self) -> LotSizeCriterionSchema:
        """Validate that max is greater than min."""
        if self.max <= self.min:
            raise ValueError(f"max ({self.max}) must be greater than min ({self.min})")
        return self


class SoftCriteriaSchema(BaseModel):
    """Schema for soft kill-switch criteria (severity weighted).

    Each failed soft criterion adds its severity weight to the total.
    Property fails if total severity >= severity_fail threshold.

    Attributes:
        sewer_type: City sewer requirement
        year_built: No new builds requirement
        garage_spaces: Minimum garage requirement
        lot_sqft: Lot size range requirement
    """

    model_config = ConfigDict(extra="forbid")

    sewer_type: SewerCriterionSchema
    year_built: YearBuiltCriterionSchema
    garage_spaces: GarageCriterionSchema
    lot_sqft: LotSizeCriterionSchema


class ThresholdsSchema(BaseModel):
    """Schema for severity thresholds.

    Validates that severity_warning < severity_fail.

    Attributes:
        severity_fail: Total severity >= this triggers FAIL
        severity_warning: Total severity >= this triggers WARNING
    """

    model_config = ConfigDict(extra="forbid")

    severity_fail: Annotated[float, Field(ge=0.0, le=10.0, description="Fail threshold (0.0-10.0)")]
    severity_warning: Annotated[
        float, Field(ge=0.0, le=10.0, description="Warning threshold (0.0-10.0)")
    ]

    @model_validator(mode="after")
    def validate_warning_lt_fail(self) -> ThresholdsSchema:
        """Validate that warning threshold is less than fail threshold."""
        if self.severity_warning >= self.severity_fail:
            raise ValueError(
                f"severity_warning ({self.severity_warning}) must be less than "
                f"severity_fail ({self.severity_fail})"
            )
        return self


class BuyerCriteriaConfigSchema(BaseModel):
    """Complete schema for buyer_criteria.yaml.

    All criteria are now HARD (instant fail). soft_criteria and thresholds
    are optional for backward compatibility but are not used in defaults.

    Attributes:
        hard_criteria: Instant fail criteria (all 8 criteria)
        soft_criteria: Optional severity-weighted criteria (deprecated)
        thresholds: Optional verdict thresholds (deprecated)
    """

    model_config = ConfigDict(extra="allow")

    hard_criteria: HardCriteriaSchema
    soft_criteria: SoftCriteriaSchema | None = None
    thresholds: ThresholdsSchema | None = None


# =============================================================================
# COMPLETE APPLICATION CONFIG SCHEMA
# =============================================================================


class AppConfigSchema(BaseModel):
    """Complete application configuration schema.

    Combines scoring weights and buyer criteria into a single validated config.

    Attributes:
        scoring: Scoring weights configuration
        buyer_criteria: Buyer criteria configuration
    """

    model_config = ConfigDict(extra="forbid")

    scoring: ScoringWeightsConfigSchema
    buyer_criteria: BuyerCriteriaConfigSchema


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Custom exceptions
    "ConfigurationError",
    # Value zones
    "ValueZoneSchema",
    "ValueZonesSchema",
    # Section weights
    "LocationCriteriaSchema",
    "SystemsCriteriaSchema",
    "InteriorCriteriaSchema",
    "SectionWeightSchema",
    "LocationSectionSchema",
    "SystemsSectionSchema",
    "InteriorSectionSchema",
    "SectionWeightsSchema",
    # Tier thresholds
    "TierThresholdSchema",
    "TierThresholdsSchema",
    # Scoring config
    "DefaultsSchema",
    "ScoringWeightsConfigSchema",
    # Buyer criteria
    "HardCriteriaSchema",
    "SewerCriterionSchema",
    "YearBuiltCriterionSchema",
    "GarageCriterionSchema",
    "LotSizeCriterionSchema",
    "SoftCriteriaSchema",
    "ThresholdsSchema",
    "BuyerCriteriaConfigSchema",
    # Complete config
    "AppConfigSchema",
]

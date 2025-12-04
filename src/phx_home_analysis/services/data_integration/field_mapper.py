from typing import Any

"""Field name mapping between data sources.

This module provides field name translation between different data sources
to ensure consistent canonical field names throughout the application.

Data Sources:
- county_api: Maricopa County Assessor API
- listing: Zillow/Redfin listing data
- enrichment: Manual research and enrichment JSON
- csv: CSV listing file (phx_homes.csv)

All mappings resolve to canonical field names used in PropertySchema and
EnrichmentDataSchema validation models.
"""


# Canonical field names (target for all mappings)
CANONICAL_FIELDS = {
    # Core property identifiers
    "address",
    "full_address",
    # Basic property info
    "beds",
    "baths",
    "sqft",  # Living area
    "livable_sqft",  # Alias for sqft
    "lot_sqft",
    "year_built",
    "price",
    "list_price",  # Alias for price
    # HOA and fees
    "hoa_fee",
    "tax_annual",
    # Property features
    "garage_spaces",
    "has_pool",
    "pool_equipment_age",
    "sewer_type",
    "roof_age",
    "hvac_age",
    "solar_status",
    "solar_lease_monthly",
    "orientation",
    "fireplace_present",
    # Location scores (Section A - 250 pts)
    "school_rating",
    "school_district",
    "safety_neighborhood_score",
    "noise_level",
    "commute_minutes",
    "distance_to_grocery_miles",
    "distance_to_highway_miles",
    "distance_to_park_miles",
    "parks_walkability_score",
    # Interior scores (Section C - 180 pts)
    "kitchen_layout_score",
    "kitchen_quality_score",
    "master_suite_score",
    "master_quality_score",
    "natural_light_score",
    "high_ceilings_score",
    "ceiling_height_score",
    "fireplace_score",
    "laundry_area_score",
    "laundry_score",
    "aesthetics_score",
    # Systems scores (Section B - 175 pts)
    "backyard_utility_score",
    # Valuation
    "full_cash_value",
    "limited_value",
    # Additional metadata
    "roof_type",
    "exterior_wall_type",
    "latitude",
    "longitude",
    # Kill switch
    "kill_switch_passed",
    "kill_switch_failures",
    # Cost estimation
    "monthly_cost",
    "cost_breakdown",
    # Data quality
    "roof_age_confidence",
    "hvac_age_confidence",
    "pool_equipment_age_confidence",
    "interior_assessment_date",
}


# Field mappings from each source to canonical names
FIELD_MAPPING: dict[str, dict[str, str]] = {
    # County API mappings (from ParcelData model)
    "county_api": {
        "apn": "apn",
        "full_address": "full_address",
        "lot_sqft": "lot_sqft",
        "year_built": "year_built",
        "garage_spaces": "garage_spaces",
        "sewer_type": "sewer_type",
        "has_pool": "has_pool",
        "beds": "beds",
        "baths": "baths",
        "tax_annual": "tax_annual",
        "full_cash_value": "full_cash_value",
        "limited_value": "limited_value",
        "livable_sqft": "livable_sqft",
        "roof_type": "roof_type",
        "exterior_wall_type": "exterior_wall_type",
        "latitude": "latitude",
        "longitude": "longitude",
    },
    # Listing sources (Zillow, Redfin from CSV)
    "listing": {
        "street": "street",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "price": "price",
        "price_num": "price",  # Alias: price_num -> price
        "beds": "beds",
        "baths": "baths",
        "sqft": "sqft",
        "livable_sqft": "sqft",  # Alias: livable_sqft -> sqft
        "price_per_sqft": "price_per_sqft",
        "full_address": "full_address",
    },
    # Enrichment JSON (manual research + automated enrichment)
    "enrichment": {
        "full_address": "full_address",
        # Core property data
        "lot_sqft": "lot_sqft",
        "lot_size_sqft": "lot_sqft",  # Alias
        "year_built": "year_built",
        "garage_spaces": "garage_spaces",
        "sewer_type": "sewer_type",
        "has_pool": "has_pool",
        "beds": "beds",
        "baths": "baths",
        "tax_annual": "tax_annual",
        "hoa_fee": "hoa_fee",
        "list_price": "price",  # Alias: list_price -> price
        "price": "price",
        "sqft": "sqft",
        # Location data
        "school_district": "school_district",
        "school_rating": "school_rating",
        "safety_neighborhood_score": "safety_neighborhood_score",
        "safety_data_source": "safety_data_source",
        "parks_walkability_score": "parks_walkability_score",
        "parks_data_source": "parks_data_source",
        "distance_to_park_miles": "distance_to_park_miles",
        "commute_minutes": "commute_minutes",
        "distance_to_grocery_miles": "distance_to_grocery_miles",
        "distance_to_highway_miles": "distance_to_highway_miles",
        "orientation": "orientation",
        # Systems/ages
        "roof_age": "roof_age",
        "hvac_age": "hvac_age",
        "pool_equipment_age": "pool_equipment_age",
        "roof_age_confidence": "roof_age_confidence",
        "hvac_age_confidence": "hvac_age_confidence",
        "pool_equipment_age_confidence": "pool_equipment_age_confidence",
        # Solar
        "solar_status": "solar_status",
        "solar_lease_monthly": "solar_lease_monthly",
        # Interior scores
        "kitchen_layout_score": "kitchen_layout_score",
        "kitchen_quality_score": "kitchen_quality_score",
        "kitchen_quality_score_source": "kitchen_quality_score_source",
        "master_suite_score": "master_suite_score",
        "master_quality_score": "master_quality_score",
        "master_quality_score_source": "master_quality_score_source",
        "natural_light_score": "natural_light_score",
        "natural_light_score_source": "natural_light_score_source",
        "high_ceilings_score": "high_ceilings_score",
        "ceiling_height_score": "ceiling_height_score",
        "ceiling_height_score_source": "ceiling_height_score_source",
        "fireplace_present": "fireplace_present",
        "fireplace_score": "fireplace_score",
        "fireplace_score_source": "fireplace_score_source",
        "laundry_area_score": "laundry_area_score",
        "laundry_score": "laundry_score",
        "laundry_score_source": "laundry_score_source",
        "aesthetics_score": "aesthetics_score",
        "aesthetics_score_source": "aesthetics_score_source",
        # Metadata
        "interior_assessment_date": "interior_assessment_date",
        # Kill switch
        "kill_switch_passed": "kill_switch_passed",
        "kill_switch_failures": "kill_switch_failures",
        # Cost estimation
        "monthly_cost": "monthly_cost",
        "cost_breakdown": "cost_breakdown",
    },
    # CSV file (phx_homes.csv)
    "csv": {
        "street": "street",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "price": "price",
        "price_num": "price",
        "beds": "beds",
        "baths": "baths",
        "sqft": "sqft",
        "price_per_sqft": "price_per_sqft",
        "full_address": "full_address",
    },
}


# Reverse mapping: canonical -> source-specific names
REVERSE_MAPPING: dict[str, dict[str, str]] = {}
for source, mappings in FIELD_MAPPING.items():
    REVERSE_MAPPING[source] = {canonical: source_field for source_field, canonical in mappings.items()}


class FieldMapper:
    """Maps field names between data sources to canonical names.

    Provides bidirectional mapping between source-specific field names
    and canonical field names used throughout the application.

    Examples:
        >>> mapper = FieldMapper()
        >>> mapper.to_canonical("price_num", "listing")
        'price'
        >>> mapper.to_canonical("lot_size_sqft", "enrichment")
        'lot_sqft'
        >>> mapper.from_canonical("price", "listing")
        'price'
        >>> mapper.from_canonical("sqft", "county_api")
        'livable_sqft'
    """

    def __init__(self, custom_mappings: dict[str, dict[str, str]] | None = None):
        """Initialize field mapper with optional custom mappings.

        Args:
            custom_mappings: Optional additional source mappings to merge
                with default FIELD_MAPPING
        """
        self.mappings = FIELD_MAPPING.copy()
        if custom_mappings:
            for source, fields in custom_mappings.items():
                if source in self.mappings:
                    self.mappings[source].update(fields)
                else:
                    self.mappings[source] = fields

        # Build reverse mappings
        self._build_reverse_mappings()

    def _build_reverse_mappings(self) -> None:
        """Build reverse lookup tables for canonical -> source mappings."""
        self.reverse_mappings: dict[str, dict[str, str]] = {}
        for source, fields in self.mappings.items():
            self.reverse_mappings[source] = {canonical: source_field for source_field, canonical in fields.items()}

    def to_canonical(self, field_name: str, source: str) -> str:
        """Convert source-specific field name to canonical name.

        Args:
            field_name: Field name from the source system
            source: Source identifier (county_api, listing, enrichment, csv)

        Returns:
            Canonical field name, or original field_name if no mapping exists

        Examples:
            >>> mapper.to_canonical("price_num", "listing")
            'price'
            >>> mapper.to_canonical("lot_size_sqft", "enrichment")
            'lot_sqft'
            >>> mapper.to_canonical("unknown_field", "listing")
            'unknown_field'
        """
        if source not in self.mappings:
            return field_name

        return self.mappings[source].get(field_name, field_name)

    def from_canonical(self, canonical_name: str, target_source: str) -> str:
        """Convert canonical name to target source's field name.

        Args:
            canonical_name: Canonical field name
            target_source: Target source identifier

        Returns:
            Source-specific field name, or canonical_name if no mapping exists

        Examples:
            >>> mapper.from_canonical("price", "listing")
            'price'
            >>> mapper.from_canonical("sqft", "county_api")
            'livable_sqft'
        """
        if target_source not in self.reverse_mappings:
            return canonical_name

        return self.reverse_mappings[target_source].get(canonical_name, canonical_name)

    def translate_dict(self, data: dict[str, Any], source: str, to_canonical: bool = True) -> dict[str, Any]:
        """Translate all field names in a dictionary.

        Args:
            data: Dictionary with source-specific or canonical field names
            source: Source identifier
            to_canonical: If True, translate to canonical names.
                If False, translate from canonical to source names.

        Returns:
            New dictionary with translated field names

        Examples:
            >>> data = {"price_num": 475000, "lot_size_sqft": 8069}
            >>> mapper.translate_dict(data, "enrichment", to_canonical=True)
            {'price': 475000, 'lot_sqft': 8069}
        """
        if to_canonical:
            return {self.to_canonical(k, source): v for k, v in data.items()}
        else:
            return {self.from_canonical(k, source): v for k, v in data.items()}

    def get_source_fields(self, source: str) -> set[str]:
        """Get all field names recognized by a source.

        Args:
            source: Source identifier

        Returns:
            Set of field names for the source
        """
        return set(self.mappings.get(source, {}).keys())

    def get_canonical_fields(self) -> set[str]:
        """Get all canonical field names.

        Returns:
            Set of all canonical field names
        """
        return CANONICAL_FIELDS.copy()

    def is_valid_source(self, source: str) -> bool:
        """Check if a source identifier is recognized.

        Args:
            source: Source identifier to check

        Returns:
            True if source is valid
        """
        return source in self.mappings

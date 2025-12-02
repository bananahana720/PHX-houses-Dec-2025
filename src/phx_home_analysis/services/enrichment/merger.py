"""Enrichment data merger service.

This service handles merging enrichment data from external sources into Property objects.
Enrichment data includes county assessor records, HOA information, location details,
and Arizona-specific features (solar, pool, HVAC).

Usage:
    merger = EnrichmentMerger()
    enriched_property = merger.merge(property_obj, enrichment_data)
    enriched_properties = merger.merge_batch(properties, enrichment_lookup)
"""

import logging

from ...domain import EnrichmentData, Orientation, Property, SewerType, SolarStatus

logger = logging.getLogger(__name__)


class EnrichmentMerger:
    """Merges enrichment data into Property objects.

    Handles type conversions, enum mappings, and null-safe attribute updates.
    Enrichment data takes precedence over CSV data when present.

    Responsibilities:
    - Match enrichment data to properties by address
    - Convert string values to appropriate enums (SewerType, Orientation, SolarStatus)
    - Merge county assessor data (lot_sqft, year_built, garage_spaces)
    - Merge HOA and tax information
    - Merge location data (school ratings, distances, commute)
    - Merge Arizona-specific features (solar, pool, HVAC, roof age)
    """

    def merge(self, property_obj: Property, enrichment: EnrichmentData) -> Property:
        """Merge enrichment data into a single property.

        Args:
            property_obj: Property object to enrich
            enrichment: Enrichment data to merge

        Returns:
            Property object with enrichment data merged (same instance, modified)
        """
        # County assessor data
        if enrichment.lot_sqft is not None:
            property_obj.lot_sqft = enrichment.lot_sqft
        if enrichment.year_built is not None:
            property_obj.year_built = enrichment.year_built
        if enrichment.garage_spaces is not None:
            property_obj.garage_spaces = enrichment.garage_spaces
        if enrichment.sewer_type is not None:
            property_obj.sewer_type = self._convert_to_sewer_type(enrichment.sewer_type)
        if enrichment.tax_annual is not None:
            property_obj.tax_annual = enrichment.tax_annual

        # HOA and location data
        if enrichment.hoa_fee is not None:
            property_obj.hoa_fee = enrichment.hoa_fee
        if enrichment.commute_minutes is not None:
            property_obj.commute_minutes = enrichment.commute_minutes
        if enrichment.school_district is not None:
            property_obj.school_district = enrichment.school_district
        if enrichment.school_rating is not None:
            property_obj.school_rating = enrichment.school_rating
        if enrichment.orientation is not None:
            property_obj.orientation = self._convert_to_orientation(enrichment.orientation)
        if enrichment.distance_to_grocery_miles is not None:
            property_obj.distance_to_grocery_miles = enrichment.distance_to_grocery_miles
        if enrichment.distance_to_highway_miles is not None:
            property_obj.distance_to_highway_miles = enrichment.distance_to_highway_miles

        # Arizona-specific features
        if enrichment.solar_status is not None:
            property_obj.solar_status = self._convert_to_solar_status(enrichment.solar_status)
        if enrichment.solar_lease_monthly is not None:
            property_obj.solar_lease_monthly = enrichment.solar_lease_monthly
        if enrichment.has_pool is not None:
            property_obj.has_pool = enrichment.has_pool
        if enrichment.pool_equipment_age is not None:
            property_obj.pool_equipment_age = enrichment.pool_equipment_age
        if enrichment.roof_age is not None:
            property_obj.roof_age = enrichment.roof_age
        if enrichment.hvac_age is not None:
            property_obj.hvac_age = enrichment.hvac_age

        return property_obj

    def merge_batch(
        self,
        properties: list[Property],
        enrichment_lookup: dict[str, EnrichmentData],
    ) -> list[Property]:
        """Merge enrichment data into a batch of properties.

        Matches properties to enrichment data by full_address and applies merge.

        Args:
            properties: List of Property objects from CSV
            enrichment_lookup: Dictionary mapping full_address to EnrichmentData objects

        Returns:
            List of properties with enrichment data merged (same instances, modified)
        """
        enriched_count = 0

        for property_obj in properties:
            enrichment = enrichment_lookup.get(property_obj.full_address)

            if not enrichment:
                logger.debug(f"No enrichment data for: {property_obj.full_address}")
                continue

            self.merge(property_obj, enrichment)
            enriched_count += 1

        logger.info(f"Enriched {enriched_count}/{len(properties)} properties")
        return properties

    def _convert_to_sewer_type(self, value: str | SewerType) -> SewerType:
        """Convert string or enum to SewerType enum.

        Args:
            value: String value or SewerType enum

        Returns:
            SewerType enum value, defaults to UNKNOWN if invalid
        """
        if isinstance(value, SewerType):
            return value

        try:
            return SewerType(value.lower())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid sewer_type value: {value}, using UNKNOWN")
            return SewerType.UNKNOWN

    def _convert_to_orientation(self, value: str | Orientation) -> Orientation | None:
        """Convert string or enum to Orientation enum.

        Args:
            value: String value or Orientation enum

        Returns:
            Orientation enum value, or None if invalid
        """
        if isinstance(value, Orientation):
            return value

        try:
            return Orientation(value.lower())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid orientation value: {value}, using None")
            return None

    def _convert_to_solar_status(self, value: str | SolarStatus) -> SolarStatus | None:
        """Convert string or enum to SolarStatus enum.

        Args:
            value: String value or SolarStatus enum

        Returns:
            SolarStatus enum value, or None if invalid
        """
        if isinstance(value, SolarStatus):
            return value

        try:
            return SolarStatus(value.lower())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid solar_status value: {value}, using None")
            return None

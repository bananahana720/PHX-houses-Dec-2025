"""JSON-based repository for enrichment data."""

import json
from pathlib import Path
from typing import Optional

from ..domain.entities import Property, EnrichmentData
from .base import EnrichmentRepository, DataLoadError, DataSaveError


class JsonEnrichmentRepository(EnrichmentRepository):
    """JSON file-based repository for enrichment data."""

    def __init__(self, json_file_path: str | Path):
        """Initialize JSON repository.

        Args:
            json_file_path: Path to the enrichment data JSON file.
        """
        self.json_file_path = Path(json_file_path)
        self._enrichment_cache: Optional[dict[str, EnrichmentData]] = None

    def load_all(self) -> dict[str, EnrichmentData]:
        """Load all enrichment data from the JSON file.

        If the file doesn't exist, creates a template file and returns empty dict.

        Returns:
            Dictionary mapping full_address to EnrichmentData objects.

        Raises:
            DataLoadError: If JSON file cannot be read or parsed.
        """
        try:
            if not self.json_file_path.exists():
                # Create default enrichment template
                self._create_default_template()
                self._enrichment_cache = {}
                return {}

            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list and dict formats
            if isinstance(data, list):
                enrichment_dict = {item['full_address']: self._dict_to_enrichment(item) for item in data}
            elif isinstance(data, dict):
                enrichment_dict = {address: self._dict_to_enrichment(item) for address, item in data.items()}
            else:
                raise DataLoadError("Invalid JSON format: expected list or dict")

            self._enrichment_cache = enrichment_dict
            return enrichment_dict

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON format: {e}") from e
        except (IOError, OSError) as e:
            raise DataLoadError(f"Failed to read JSON file: {e}") from e
        except KeyError as e:
            raise DataLoadError(f"Missing required field in JSON: {e}") from e

    def load_for_property(self, full_address: str) -> Optional[EnrichmentData]:
        """Load enrichment data for a specific property.

        Args:
            full_address: The complete formatted address.

        Returns:
            EnrichmentData object if found, None otherwise.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        if self._enrichment_cache is None:
            self.load_all()

        return self._enrichment_cache.get(full_address) if self._enrichment_cache else None

    def save_all(self, enrichment_data: dict[str, EnrichmentData]) -> None:
        """Save all enrichment data to the JSON file.

        Args:
            enrichment_data: Dictionary mapping full_address to EnrichmentData.

        Raises:
            DataSaveError: If JSON file cannot be written.
        """
        try:
            # Ensure parent directory exists
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to list format for JSON
            data_list = [self._enrichment_to_dict(enrichment) for enrichment in enrichment_data.values()]

            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, indent=2, ensure_ascii=False)

            self._enrichment_cache = enrichment_data

        except (IOError, OSError) as e:
            raise DataSaveError(f"Failed to write JSON file: {e}") from e

    def apply_enrichment_to_property(self, property: Property, enrichment_dict: Optional[dict] = None) -> Property:
        """Apply enrichment data to a property object.

        Args:
            property: Property object to enrich.
            enrichment_dict: Optional enrichment dict. If None, loads from cache.

        Returns:
            Property object with enrichment data applied.

        Raises:
            DataLoadError: If enrichment data cannot be loaded.
        """
        if enrichment_dict is None:
            # Load from cache or file
            if self._enrichment_cache is None:
                self.load_all()

            if self._enrichment_cache:
                enrichment_data = self._enrichment_cache.get(property.full_address)
            else:
                enrichment_data = None
        else:
            enrichment_data = self._dict_to_enrichment(enrichment_dict) if enrichment_dict else None

        if not enrichment_data:
            return property

        # Apply enrichment data to property
        property.lot_sqft = enrichment_data.lot_sqft
        property.year_built = enrichment_data.year_built
        property.garage_spaces = enrichment_data.garage_spaces
        property.sewer_type = enrichment_data.sewer_type
        property.tax_annual = enrichment_data.tax_annual
        property.hoa_fee = enrichment_data.hoa_fee
        property.commute_minutes = enrichment_data.commute_minutes
        property.school_district = enrichment_data.school_district
        property.school_rating = enrichment_data.school_rating
        property.orientation = enrichment_data.orientation
        property.distance_to_grocery_miles = enrichment_data.distance_to_grocery_miles
        property.distance_to_highway_miles = enrichment_data.distance_to_highway_miles
        property.solar_status = enrichment_data.solar_status
        property.solar_lease_monthly = enrichment_data.solar_lease_monthly
        property.has_pool = enrichment_data.has_pool
        property.pool_equipment_age = enrichment_data.pool_equipment_age
        property.roof_age = enrichment_data.roof_age
        property.hvac_age = enrichment_data.hvac_age

        return property

    def _dict_to_enrichment(self, data: dict) -> EnrichmentData:
        """Convert dictionary to EnrichmentData object.

        Args:
            data: Dictionary from JSON.

        Returns:
            EnrichmentData object.
        """
        return EnrichmentData(
            full_address=data['full_address'],
            lot_sqft=data.get('lot_sqft'),
            year_built=data.get('year_built'),
            garage_spaces=data.get('garage_spaces'),
            sewer_type=data.get('sewer_type'),
            tax_annual=data.get('tax_annual'),
            hoa_fee=data.get('hoa_fee'),
            commute_minutes=data.get('commute_minutes'),
            school_district=data.get('school_district'),
            school_rating=data.get('school_rating'),
            orientation=data.get('orientation'),
            distance_to_grocery_miles=data.get('distance_to_grocery_miles'),
            distance_to_highway_miles=data.get('distance_to_highway_miles'),
            solar_status=data.get('solar_status'),
            solar_lease_monthly=data.get('solar_lease_monthly'),
            has_pool=data.get('has_pool'),
            pool_equipment_age=data.get('pool_equipment_age'),
            roof_age=data.get('roof_age'),
            hvac_age=data.get('hvac_age'),
        )

    def _enrichment_to_dict(self, enrichment: EnrichmentData) -> dict:
        """Convert EnrichmentData object to dictionary for JSON serialization.

        Args:
            enrichment: EnrichmentData object.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        return {
            'full_address': enrichment.full_address,
            'lot_sqft': enrichment.lot_sqft,
            'year_built': enrichment.year_built,
            'garage_spaces': enrichment.garage_spaces,
            'sewer_type': enrichment.sewer_type,
            'tax_annual': enrichment.tax_annual,
            'hoa_fee': enrichment.hoa_fee,
            'commute_minutes': enrichment.commute_minutes,
            'school_district': enrichment.school_district,
            'school_rating': enrichment.school_rating,
            'orientation': enrichment.orientation,
            'distance_to_grocery_miles': enrichment.distance_to_grocery_miles,
            'distance_to_highway_miles': enrichment.distance_to_highway_miles,
            'solar_status': enrichment.solar_status,
            'solar_lease_monthly': enrichment.solar_lease_monthly,
            'has_pool': enrichment.has_pool,
            'pool_equipment_age': enrichment.pool_equipment_age,
            'roof_age': enrichment.roof_age,
            'hvac_age': enrichment.hvac_age,
        }

    def _create_default_template(self) -> None:
        """Create a default enrichment template JSON file.

        Creates a template file with example structure when enrichment_data.json
        doesn't exist, to guide manual data entry.
        """
        template = [
            {
                "full_address": "EXAMPLE: 123 Main St, Phoenix, AZ 85001",
                "lot_sqft": 8500,
                "year_built": 2005,
                "garage_spaces": 2,
                "sewer_type": "city",
                "tax_annual": 2400,
                "hoa_fee": 0,
                "commute_minutes": 25,
                "school_district": "Example School District",
                "school_rating": 7.5,
                "orientation": None,
                "distance_to_grocery_miles": 0.8,
                "distance_to_highway_miles": 1.5,
                "solar_status": None,
                "solar_lease_monthly": None,
                "has_pool": True,
                "pool_equipment_age": 5,
                "roof_age": 10,
                "hvac_age": 8
            }
        ]

        try:
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            # If template creation fails, silently continue
            # The empty cache will be returned
            pass

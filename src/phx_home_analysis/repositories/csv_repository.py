"""CSV-based repository for property data."""

import csv
from pathlib import Path
from typing import Any

from ..domain.entities import Property
from ..domain.enums import Orientation, SewerType, SolarStatus, Tier
from .base import DataLoadError, DataSaveError, PropertyRepository


class CsvPropertyRepository(PropertyRepository):
    """CSV file-based repository for property data."""

    def __init__(self, csv_file_path: str | Path, ranked_csv_path: str | Path | None = None):
        """Initialize CSV repository.

        Args:
            csv_file_path: Path to the input CSV file (phx_homes.csv).
            ranked_csv_path: Optional path to the output ranked CSV file.
        """
        self.csv_file_path = Path(csv_file_path)
        self.ranked_csv_path = Path(ranked_csv_path) if ranked_csv_path else None
        self._properties_cache: dict[str, Property] | None = None

    def load_all(self) -> list[Property]:
        """Load all properties from the CSV file.

        Returns:
            List of Property objects.

        Raises:
            DataLoadError: If CSV file cannot be read or parsed.
        """
        try:
            if not self.csv_file_path.exists():
                raise DataLoadError(f"CSV file not found: {self.csv_file_path}")

            properties = []
            with open(self.csv_file_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    property_obj = self._row_to_property(row)
                    properties.append(property_obj)

            # Cache for quick lookups
            self._properties_cache = {p.full_address: p for p in properties}
            return properties

        except OSError as e:
            raise DataLoadError(f"Failed to read CSV file: {e}") from e
        except (ValueError, KeyError) as e:
            raise DataLoadError(f"Failed to parse CSV data: {e}") from e

    def load_by_address(self, full_address: str) -> Property | None:
        """Load a single property by its full address.

        Args:
            full_address: The complete formatted address.

        Returns:
            Property object if found, None otherwise.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        if self._properties_cache is None:
            self.load_all()

        return self._properties_cache.get(full_address) if self._properties_cache else None

    def save_all(self, properties: list[Property]) -> None:
        """Save all properties to the ranked CSV file.

        Args:
            properties: List of Property objects to save.

        Raises:
            DataSaveError: If CSV file cannot be written.
        """
        if not self.ranked_csv_path:
            raise DataSaveError("No ranked CSV path configured")

        try:
            # Ensure parent directory exists
            self.ranked_csv_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.ranked_csv_path, 'w', encoding='utf-8', newline='') as f:
                if not properties:
                    return

                # Define output columns
                fieldnames = self._get_output_fieldnames()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for property_obj in properties:
                    row = self._property_to_row(property_obj)
                    writer.writerow(row)

        except OSError as e:
            raise DataSaveError(f"Failed to write CSV file: {e}") from e

    def save_one(self, property: Property) -> None:
        """Save a single property (not supported for CSV - use save_all).

        Args:
            property: Property object to save.

        Raises:
            NotImplementedError: CSV repository requires saving all at once.
        """
        raise NotImplementedError(
            "CSV repository does not support saving individual properties. Use save_all() instead."
        )

    def _row_to_property(self, row: dict[str, str]) -> Property:
        """Convert CSV row dictionary to Property object.

        Args:
            row: Dictionary from CSV DictReader.

        Returns:
            Property object.
        """
        return Property(
            # Address fields
            street=row['street'].strip(),
            city=row['city'].strip(),
            state=row['state'].strip(),
            zip_code=row.get('zip', row.get('zip_code', '')).strip(),
            full_address=row['full_address'].strip(),

            # Basic listing data (required fields with fallback to 0)
            price=row['price'].strip(),
            price_num=self._parse_int(row.get('price_num')),  # Can be None if unparseable
            beds=self._parse_int(row.get('beds')) or 0,
            baths=self._parse_float(row.get('baths')) or 0.0,
            sqft=self._parse_int(row.get('sqft')) or 0,
            price_per_sqft_raw=self._parse_float(row.get('price_per_sqft')) or 0.0,

            # County assessor data (may be in ranked CSV)
            lot_sqft=self._parse_int(row.get('lot_sqft')),
            year_built=self._parse_int(row.get('year_built')),
            garage_spaces=self._parse_int(row.get('garage_spaces')),
            sewer_type=self._parse_enum(row.get('sewer_type'), SewerType),
            tax_annual=self._parse_int(row.get('tax_annual')),

            # HOA and location data
            hoa_fee=self._parse_int(row.get('hoa_fee')),
            commute_minutes=self._parse_int(row.get('commute_minutes')),
            school_district=row.get('school_district', '').strip() or None,
            school_rating=self._parse_float(row.get('school_rating')),
            orientation=self._parse_enum(row.get('orientation'), Orientation),
            distance_to_grocery_miles=self._parse_float(row.get('distance_to_grocery_miles')),
            distance_to_highway_miles=self._parse_float(row.get('distance_to_highway_miles')),

            # Arizona-specific features
            solar_status=self._parse_enum(row.get('solar_status'), SolarStatus),
            solar_lease_monthly=self._parse_int(row.get('solar_lease_monthly')),
            has_pool=self._parse_bool(row.get('has_pool')),
            pool_equipment_age=self._parse_int(row.get('pool_equipment_age')),
            roof_age=self._parse_int(row.get('roof_age')),
            hvac_age=self._parse_int(row.get('hvac_age')),

            # Analysis results (populated by pipeline, may not be in input CSV)
            kill_switch_passed=self._parse_bool(row.get('kill_switch_passed')) or False,
            kill_switch_failures=self._parse_list(row.get('kill_switch_failures')),
            tier=self._parse_enum(row.get('tier'), Tier),

            # Geocoding
            latitude=self._parse_float(row.get('latitude')),
            longitude=self._parse_float(row.get('longitude')),

            # Manual assessment scores (may be in ranked CSV)
            kitchen_layout_score=self._parse_float(row.get('kitchen_layout_score')),
            master_suite_score=self._parse_float(row.get('master_suite_score')),
            natural_light_score=self._parse_float(row.get('natural_light_score')),
            high_ceilings_score=self._parse_float(row.get('high_ceilings_score')),
            fireplace_present=self._parse_bool(row.get('fireplace_present')),
            laundry_area_score=self._parse_float(row.get('laundry_area_score')),
            aesthetics_score=self._parse_float(row.get('aesthetics_score')),
            backyard_utility_score=self._parse_float(row.get('backyard_utility_score')),
            safety_neighborhood_score=self._parse_float(row.get('safety_neighborhood_score')),
            parks_walkability_score=self._parse_float(row.get('parks_walkability_score')),
        )

    def _property_to_row(self, property_obj: Property) -> dict[str, Any]:
        """Convert Property object to CSV row dictionary.

        Args:
            property_obj: Property object to convert.

        Returns:
            Dictionary suitable for CSV DictWriter.
        """
        # Get score breakdown if available
        score_location = 0.0
        score_lot_systems = 0.0
        score_interior = 0.0
        if property_obj.score_breakdown:
            score_location = property_obj.score_breakdown.location_total
            score_lot_systems = property_obj.score_breakdown.systems_total
            score_interior = property_obj.score_breakdown.interior_total

        return {
            # Address fields
            'street': property_obj.street,
            'city': property_obj.city,
            'state': property_obj.state,
            'zip': property_obj.zip_code,
            'full_address': property_obj.full_address,

            # Basic listing data
            'price': property_obj.price,
            'price_num': property_obj.price_num,
            'beds': property_obj.beds,
            'baths': property_obj.baths,
            'sqft': property_obj.sqft,
            'price_per_sqft': f"{property_obj.price_per_sqft:.2f}" if property_obj.price_per_sqft else '',

            # County assessor data
            'lot_sqft': property_obj.lot_sqft or '',
            'year_built': property_obj.year_built or '',
            'garage_spaces': property_obj.garage_spaces or '',
            'sewer_type': property_obj.sewer_type.value if property_obj.sewer_type else '',
            'tax_annual': property_obj.tax_annual or '',

            # HOA and location data
            'hoa_fee': property_obj.hoa_fee if property_obj.hoa_fee is not None else '',
            'commute_minutes': property_obj.commute_minutes or '',
            'school_district': property_obj.school_district or '',
            'school_rating': f"{property_obj.school_rating:.1f}" if property_obj.school_rating else '',
            'orientation': property_obj.orientation.value if property_obj.orientation else '',
            'distance_to_grocery_miles': f"{property_obj.distance_to_grocery_miles:.1f}" if property_obj.distance_to_grocery_miles else '',
            'distance_to_highway_miles': f"{property_obj.distance_to_highway_miles:.1f}" if property_obj.distance_to_highway_miles else '',

            # Arizona-specific features
            'solar_status': property_obj.solar_status.value if property_obj.solar_status else '',
            'solar_lease_monthly': property_obj.solar_lease_monthly or '',
            'has_pool': str(property_obj.has_pool).lower() if property_obj.has_pool is not None else '',
            'pool_equipment_age': property_obj.pool_equipment_age or '',
            'roof_age': property_obj.roof_age or '',
            'hvac_age': property_obj.hvac_age or '',

            # Analysis results
            'score_location': f"{score_location:.1f}" if score_location else '',
            'score_lot_systems': f"{score_lot_systems:.1f}" if score_lot_systems else '',
            'score_interior': f"{score_interior:.1f}" if score_interior else '',
            'total_score': int(property_obj.total_score) if property_obj.total_score else '',
            'tier': property_obj.tier.value if property_obj.tier else '',
            'kill_switch_passed': str(property_obj.kill_switch_passed).lower() if property_obj.kill_switch_passed is not None else '',
            'kill_switch_failures': ';'.join(property_obj.kill_switch_failures) if property_obj.kill_switch_failures else '',

            # Geocoding
            'latitude': f"{property_obj.latitude:.6f}" if property_obj.latitude else '',
            'longitude': f"{property_obj.longitude:.6f}" if property_obj.longitude else '',

            # Manual assessment scores
            'kitchen_layout_score': f"{property_obj.kitchen_layout_score:.1f}" if property_obj.kitchen_layout_score else '',
            'master_suite_score': f"{property_obj.master_suite_score:.1f}" if property_obj.master_suite_score else '',
            'natural_light_score': f"{property_obj.natural_light_score:.1f}" if property_obj.natural_light_score else '',
            'high_ceilings_score': f"{property_obj.high_ceilings_score:.1f}" if property_obj.high_ceilings_score else '',
            'fireplace_present': str(property_obj.fireplace_present).lower() if property_obj.fireplace_present is not None else '',
            'laundry_area_score': f"{property_obj.laundry_area_score:.1f}" if property_obj.laundry_area_score else '',
            'aesthetics_score': f"{property_obj.aesthetics_score:.1f}" if property_obj.aesthetics_score else '',
            'backyard_utility_score': f"{property_obj.backyard_utility_score:.1f}" if property_obj.backyard_utility_score else '',
            'safety_neighborhood_score': f"{property_obj.safety_neighborhood_score:.1f}" if property_obj.safety_neighborhood_score else '',
            'parks_walkability_score': f"{property_obj.parks_walkability_score:.1f}" if property_obj.parks_walkability_score else '',
        }

    def _get_output_fieldnames(self) -> list[str]:
        """Get the ordered list of fieldnames for output CSV.

        Returns:
            List of column names.
        """
        return [
            # Address
            'street', 'city', 'state', 'zip', 'full_address',
            # Listing data
            'price', 'price_num', 'beds', 'baths', 'sqft', 'price_per_sqft',
            # County data
            'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type', 'tax_annual',
            # Location
            'hoa_fee', 'commute_minutes', 'school_district', 'school_rating',
            'orientation', 'distance_to_grocery_miles', 'distance_to_highway_miles',
            # Features
            'solar_status', 'solar_lease_monthly', 'has_pool',
            'pool_equipment_age', 'roof_age', 'hvac_age',
            # Manual assessment scores
            'kitchen_layout_score', 'master_suite_score', 'natural_light_score',
            'high_ceilings_score', 'fireplace_present', 'laundry_area_score',
            'aesthetics_score', 'backyard_utility_score', 'safety_neighborhood_score',
            'parks_walkability_score',
            # Analysis results
            'score_location', 'score_lot_systems', 'score_interior',
            'total_score', 'tier', 'kill_switch_passed', 'kill_switch_failures',
            # Geocoding
            'latitude', 'longitude',
        ]

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """Parse integer from CSV string, handling empty/None values.

        Args:
            value: String value from CSV.

        Returns:
            Parsed integer or None.
        """
        if not value or not value.strip():
            return None
        try:
            return int(value.strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        """Parse float from CSV string, handling empty/None values.

        Args:
            value: String value from CSV.

        Returns:
            Parsed float or None.
        """
        if not value or not value.strip():
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_bool(value: str | None) -> bool | None:
        """Parse boolean from CSV string.

        Args:
            value: String value from CSV (true/false/1/0/yes/no).

        Returns:
            Parsed boolean or None.
        """
        if not value or not value.strip():
            return None
        value_lower = value.strip().lower()
        if value_lower in ('true', '1', 'yes'):
            return True
        elif value_lower in ('false', '0', 'no'):
            return False
        return None

    @staticmethod
    def _parse_list(value: str | None, delimiter: str = ';') -> list[str]:
        """Parse list from delimited CSV string.

        Args:
            value: String value from CSV.
            delimiter: Delimiter character (default: semicolon).

        Returns:
            List of strings.
        """
        if not value or not value.strip():
            return []
        return [item.strip() for item in value.split(delimiter) if item.strip()]

    @staticmethod
    def _parse_enum(value: str | None, enum_class: type[Any]) -> Any | None:
        """Parse enum from CSV string.

        Args:
            value: String value from CSV.
            enum_class: Enum class to parse into.

        Returns:
            Enum instance or None.
        """
        if not value or not value.strip():
            return None
        try:
            # Try both uppercase and lowercase
            normalized = value.strip()
            for member in enum_class:
                if member.value.lower() == normalized.lower():
                    return member
            return None
        except (ValueError, AttributeError):
            return None

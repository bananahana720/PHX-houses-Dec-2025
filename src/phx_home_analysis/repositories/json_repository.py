"""JSON-based repository for enrichment data."""

import json
import logging
from pathlib import Path

from ..domain.entities import EnrichmentData, Property
from .base import DataLoadError, DataSaveError, EnrichmentRepository

logger = logging.getLogger(__name__)


class JsonEnrichmentRepository(EnrichmentRepository):
    """JSON file-based repository for enrichment data."""

    def __init__(self, json_file_path: str | Path):
        """Initialize JSON repository.

        Args:
            json_file_path: Path to the enrichment data JSON file.
        """
        self.json_file_path = Path(json_file_path)
        self._enrichment_cache: dict[str, EnrichmentData] | None = None
        self._address_index: dict[str, str] | None = None  # normalized → full_address (O(1) lookup)

    def load_all(self, validate: bool = True) -> dict[str, EnrichmentData]:
        """Load all enrichment data from the JSON file with optional validation.

        If the file doesn't exist, creates a template file and returns empty dict.

        Args:
            validate: Whether to validate data against Pydantic schema (default True).
                     Set to False for backward compatibility or when loading known-good data.

        Returns:
            Dictionary mapping full_address to EnrichmentData objects.

        Raises:
            DataLoadError: If JSON file cannot be read, parsed, or validated.
        """
        # Import here to avoid circular imports
        from ..validation.validators import validate_enrichment_entry

        try:
            if not self.json_file_path.exists():
                # Create default enrichment template
                self._create_default_template()
                self._enrichment_cache = {}
                self._address_index = {}  # Empty index for empty cache
                return {}

            with open(self.json_file_path, encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list and dict formats
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict):
                # Convert dict format to list format, ensuring full_address is in each item
                raw_items = []
                for address, item in data.items():
                    if isinstance(item, dict):
                        item_copy = item.copy()
                        item_copy.setdefault("full_address", address)
                        raw_items.append(item_copy)
                    else:
                        raise DataLoadError(f"Invalid item for address '{address}': expected dict")
            else:
                raise DataLoadError("Invalid JSON format: expected list or dict")

            # Validate each entry if validation is enabled
            enrichment_dict = {}
            validation_errors = []

            for i, item in enumerate(raw_items):
                try:
                    if validate:
                        # Validate and normalize the entry
                        validated_item = validate_enrichment_entry(item, normalize=True)
                    else:
                        validated_item = item

                    address = validated_item.get("full_address") or item.get("full_address")
                    if not address:
                        raise ValueError("Missing required field: full_address")

                    enrichment_dict[address] = self._dict_to_enrichment(validated_item)

                except ValueError as e:
                    address = item.get("full_address", f"entry {i}")
                    validation_errors.append(f"{address}: {e}")
                    logger.warning("Validation error for %s: %s", address, e)

            if validation_errors:
                error_summary = "; ".join(validation_errors[:5])
                if len(validation_errors) > 5:
                    error_summary += f" ... and {len(validation_errors) - 5} more errors"
                raise DataLoadError(f"Validation failed for {len(validation_errors)} entries: {error_summary}")

            self._enrichment_cache = enrichment_dict

            # Build normalized address index for O(1) lookups
            self._address_index = {
                enrichment.normalized_address: address
                for address, enrichment in enrichment_dict.items()
            }

            return enrichment_dict

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON format: {e}") from e
        except OSError as e:
            raise DataLoadError(f"Failed to read JSON file: {e}") from e
        except KeyError as e:
            raise DataLoadError(f"Missing required field in JSON: {e}") from e

    def load_for_property(self, full_address: str) -> EnrichmentData | None:
        """Load enrichment data for a specific property using normalized address matching.

        Lookup priority (all O(1)):
        1. Exact match on full_address (fastest, most common)
        2. Normalized address index lookup (case-insensitive, punctuation-removed)

        Args:
            full_address: The address to look up (will be normalized for matching).

        Returns:
            EnrichmentData object if found, None otherwise.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        from ..utils.address_utils import normalize_address

        if self._enrichment_cache is None:
            self.load_all()

        if not self._enrichment_cache:
            return None

        # Try exact match first (fastest path, O(1))
        if full_address in self._enrichment_cache:
            return self._enrichment_cache[full_address]

        # Use normalized index for O(1) lookup instead of O(n) scan
        normalized_lookup = normalize_address(full_address)
        cached_address = self._address_index.get(normalized_lookup) if self._address_index else None

        if cached_address:
            return self._enrichment_cache.get(cached_address)

        return None

    def save_all(self, enrichment_data: dict[str, EnrichmentData], validate: bool = True) -> None:
        """Save all enrichment data to the JSON file atomically with optional validation.

        Uses atomic write pattern (write-to-temp + rename) to prevent
        data corruption if the process crashes mid-write.

        Args:
            enrichment_data: Dictionary mapping full_address to EnrichmentData.
            validate: Whether to validate data before saving (default True).
                     Set to False for backward compatibility or trusted data.

        Raises:
            DataSaveError: If validation fails or JSON file cannot be written.
        """
        # Import here to avoid circular imports
        from ..utils.file_ops import atomic_json_save
        from ..validation.validators import validate_enrichment_entry

        try:
            # Convert to list format for JSON
            data_list = [self._enrichment_to_dict(enrichment) for enrichment in enrichment_data.values()]

            # Validate before saving if enabled
            if validate:
                validation_errors = []
                validated_list = []

                for i, item in enumerate(data_list):
                    try:
                        validated_item = validate_enrichment_entry(item, normalize=True)
                        validated_list.append(validated_item)
                    except ValueError as e:
                        address = item.get("full_address", f"entry {i}")
                        validation_errors.append(f"{address}: {e}")
                        logger.warning("Validation error for %s: %s", address, e)

                if validation_errors:
                    error_summary = "; ".join(validation_errors[:5])
                    if len(validation_errors) > 5:
                        error_summary += f" ... and {len(validation_errors) - 5} more errors"
                    raise DataSaveError(
                        f"Validation failed, not saving. {len(validation_errors)} entries invalid: {error_summary}"
                    )

                # Use validated data for saving
                data_list = validated_list

            # Atomic save with backup
            backup = atomic_json_save(self.json_file_path, data_list, create_backup=True)
            if backup:
                logger.debug(f"Created backup: {backup}")

            self._enrichment_cache = enrichment_data

            # Rebuild normalized address index for O(1) lookups
            self._address_index = {
                enrichment.normalized_address: address
                for address, enrichment in enrichment_data.items()
            }

        except OSError as e:
            raise DataSaveError(f"Failed to write JSON file: {e}") from e

    def restore_from_backup(self, backup_path: Path | str | None = None) -> bool:
        """Restore enrichment data from backup file.

        If backup_path is not specified, finds the most recent valid backup
        in the same directory as the main JSON file.

        Args:
            backup_path: Specific backup file to restore from.
                If None, uses most recent backup matching pattern.

        Returns:
            True if restore was successful, False if no valid backup found.

        Raises:
            DataLoadError: If backup file cannot be read or is invalid.

        Example:
            >>> repo = JsonEnrichmentRepository("data/enrichment_data.json")
            >>> if repo.restore_from_backup():
            ...     print("Restored from backup successfully")
        """
        import shutil

        if backup_path is None:
            # Find most recent backup
            backup_pattern = f"{self.json_file_path.stem}.*.bak{self.json_file_path.suffix}"
            backups = sorted(
                self.json_file_path.parent.glob(backup_pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            if not backups:
                logger.warning(f"No backup files found matching {backup_pattern}")
                return False

            backup_path = backups[0]
        else:
            backup_path = Path(backup_path)

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Validate backup is valid JSON with expected structure
        try:
            with open(backup_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise DataLoadError(f"Invalid backup format: expected list, got {type(data)}")

            # Verify at least one entry has required fields
            if data and not all("full_address" in item for item in data[:5]):
                raise DataLoadError("Backup file missing required 'full_address' field")

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in backup file: {e}") from e

        # Create backup of current (possibly corrupted) file before restore
        if self.json_file_path.exists():
            corrupted_backup = self.json_file_path.with_suffix(".corrupted.json")
            try:
                shutil.copy2(self.json_file_path, corrupted_backup)
                logger.info(f"Saved corrupted file to: {corrupted_backup}")
            except OSError:
                pass  # Best effort

        # Restore from backup
        shutil.copy2(backup_path, self.json_file_path)
        logger.info(f"Restored from backup: {backup_path}")

        # Invalidate cache and index to force reload
        self._enrichment_cache = None
        self._address_index = None

        return True

    def apply_enrichment_to_property(self, property: Property, enrichment_dict: dict | None = None) -> Property:
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

        # Import enums for conversion
        from ..domain.enums import Orientation, SewerType, SolarStatus

        # Apply enrichment data to property
        property.lot_sqft = enrichment_data.lot_sqft
        property.year_built = enrichment_data.year_built
        property.garage_spaces = enrichment_data.garage_spaces
        # Convert string to enum for sewer_type
        property.sewer_type = SewerType(enrichment_data.sewer_type) if enrichment_data.sewer_type else None  # type: ignore[arg-type]
        property.tax_annual = enrichment_data.tax_annual
        property.hoa_fee = enrichment_data.hoa_fee
        property.commute_minutes = enrichment_data.commute_minutes
        property.school_district = enrichment_data.school_district
        property.school_rating = enrichment_data.school_rating
        # Convert string to enum for orientation
        property.orientation = Orientation(enrichment_data.orientation) if enrichment_data.orientation else None  # type: ignore[arg-type]
        property.distance_to_grocery_miles = enrichment_data.distance_to_grocery_miles
        property.distance_to_highway_miles = enrichment_data.distance_to_highway_miles
        # Convert string to enum for solar_status
        property.solar_status = SolarStatus(enrichment_data.solar_status) if enrichment_data.solar_status else None  # type: ignore[arg-type]
        property.solar_lease_monthly = enrichment_data.solar_lease_monthly
        property.has_pool = enrichment_data.has_pool
        property.pool_equipment_age = enrichment_data.pool_equipment_age
        property.roof_age = enrichment_data.roof_age
        property.hvac_age = enrichment_data.hvac_age

        return property

    def _dict_to_enrichment(self, data: dict) -> EnrichmentData:
        """Convert dictionary to EnrichmentData object.

        Computes normalized_address if not present in data for backward compatibility.
        Loads provenance metadata if present.

        Args:
            data: Dictionary from JSON.

        Returns:
            EnrichmentData object.
        """
        from ..utils.address_utils import normalize_address

        full_address = data["full_address"]
        # Compute normalized_address if not in data (backward compatibility)
        normalized = data.get("normalized_address") or normalize_address(full_address)

        enrichment = EnrichmentData(
            full_address=full_address,
            normalized_address=normalized,
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

        # Load provenance metadata if present
        if '_provenance' in data:
            for field_name, prov_data in data['_provenance'].items():
                enrichment.set_field_provenance(
                    field_name=field_name,
                    source=prov_data['data_source'],
                    confidence=prov_data['confidence'],
                    fetched_at=prov_data['fetched_at'],
                    agent_id=prov_data.get('agent_id'),
                    phase=prov_data.get('phase'),
                    derived_from=prov_data.get('derived_from', []),
                )

        return enrichment

    def _enrichment_to_dict(self, enrichment: EnrichmentData) -> dict:
        """Convert EnrichmentData object to dictionary for JSON serialization.

        Ensures normalized_address is always included in output.
        Includes provenance metadata if present.

        Args:
            enrichment: EnrichmentData object.

        Returns:
            Dictionary suitable for JSON serialization.
        """
        from ..utils.address_utils import normalize_address

        # Ensure normalized_address is present
        normalized = enrichment.normalized_address or normalize_address(enrichment.full_address)

        base_dict = {
            'full_address': enrichment.full_address,
            'normalized_address': normalized,
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

        # Add provenance metadata if present
        if enrichment._provenance:
            base_dict['_provenance'] = {
                field_name: {
                    'data_source': prov.data_source,
                    'confidence': prov.confidence,
                    'fetched_at': prov.fetched_at,
                    'agent_id': prov.agent_id,
                    'phase': prov.phase,
                    'derived_from': prov.derived_from,
                }
                for field_name, prov in enrichment._provenance.items()
            }

        return base_dict

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
        except OSError:
            # If template creation fails, silently continue
            # The empty cache will be returned
            pass

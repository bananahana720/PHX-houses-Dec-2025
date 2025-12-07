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

    def _detect_format(self, raw_data: dict | list) -> list[dict]:
        """Detect JSON format: 'dict' (new) or 'list' (legacy) and convert to list.

        Args:
            raw_data: Raw JSON data loaded from file.

        Returns:
            List of item dictionaries.

        Raises:
            DataLoadError: If format is invalid.
        """
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            # Convert dict format to list format, ensuring full_address is in each item
            raw_items = []
            for address, item in raw_data.items():
                if isinstance(item, dict):
                    item_copy = item.copy()
                    item_copy.setdefault("full_address", address)
                    raw_items.append(item_copy)
                else:
                    raise DataLoadError(f"Invalid item for address '{address}': expected dict")
            return raw_items
        else:
            raise DataLoadError("Invalid JSON format: expected list or dict")

    def _parse_entries(self, raw_items: list[dict], validate: bool) -> dict[str, EnrichmentData]:
        """Parse raw JSON entries into EnrichmentData objects.

        Args:
            raw_items: List of raw item dictionaries.
            validate: Whether to validate each entry.

        Returns:
            Dictionary mapping full_address to EnrichmentData objects.

        Raises:
            DataLoadError: If validation fails for any entries.
        """
        from ..validation.validators import validate_enrichment_entry

        enrichment_dict = {}
        validation_errors = []

        for i, item in enumerate(raw_items):
            try:
                if validate:
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
            raise DataLoadError(
                f"Validation failed for {len(validation_errors)} entries: {error_summary}"
            )

        return enrichment_dict

    def _build_address_index(self, data: dict[str, EnrichmentData]) -> dict[str, str]:
        """Build normalized address lookup index.

        Args:
            data: Dictionary mapping full_address to EnrichmentData.

        Returns:
            Dictionary mapping normalized_address to full_address for O(1) lookups.
        """
        return {enrichment.normalized_address: address for address, enrichment in data.items()}

    def _serialize_to_dict(self, data: dict[str, EnrichmentData]) -> list[dict]:
        """Convert EnrichmentData objects to serializable dicts.

        Args:
            data: Dictionary mapping full_address to EnrichmentData objects.

        Returns:
            List of serializable dictionaries.
        """
        return [self._enrichment_to_dict(enrichment) for enrichment in data.values()]

    def _validate_before_save(self, data_list: list[dict]) -> list[dict]:
        """Validate data before saving.

        Args:
            data_list: List of item dictionaries to validate.

        Returns:
            List of validated dictionaries.

        Raises:
            DataSaveError: If validation fails for any entries.
        """
        from ..validation.validators import validate_enrichment_entry

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

        return validated_list

    def _create_backup(self) -> Path | None:
        """Create timestamped backup of current data file.

        Returns:
            Path to backup file if successful, None otherwise.
        """
        import shutil
        from datetime import datetime

        if not self.json_file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.json_file_path.with_name(
            f"{self.json_file_path.stem}.{timestamp}.bak{self.json_file_path.suffix}"
        )

        try:
            shutil.copy2(self.json_file_path, backup_path)
            return backup_path
        except OSError:
            return None

    def _find_backups(self) -> list[Path]:
        """Find all backup files sorted by timestamp (newest first).

        Returns:
            List of backup file paths, sorted newest first.
        """
        backup_pattern = f"{self.json_file_path.stem}.*.bak{self.json_file_path.suffix}"
        backups = sorted(
            self.json_file_path.parent.glob(backup_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not backups:
            logger.warning(f"No backup files found matching {backup_pattern}")

        return backups

    def _validate_backup(self, backup_path: Path) -> bool:
        """Validate backup file integrity.

        Args:
            backup_path: Path to backup file to validate.

        Returns:
            True if backup is valid, False otherwise.

        Raises:
            DataLoadError: If backup file contains invalid JSON.
        """
        try:
            with open(backup_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise DataLoadError(f"Invalid backup format: expected list, got {type(data)}")

            # Verify at least one entry has required fields
            if data and not all("full_address" in item for item in data[:5]):
                raise DataLoadError("Backup file missing required 'full_address' field")

            return True

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in backup file: {e}") from e

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
        try:
            if not self.json_file_path.exists():
                self._create_default_template()
                self._enrichment_cache = {}
                self._address_index = {}
                return {}

            with open(self.json_file_path, encoding="utf-8") as f:
                raw_data = json.load(f)

            # Detect format and convert to list
            raw_items = self._detect_format(raw_data)

            # Parse and validate entries
            enrichment_dict = self._parse_entries(raw_items, validate)

            # Update cache and build index
            self._enrichment_cache = enrichment_dict
            self._address_index = self._build_address_index(enrichment_dict)

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
        from ..utils.file_ops import atomic_json_save

        try:
            # Serialize to dict format
            data_list = self._serialize_to_dict(enrichment_data)

            # Validate before saving if enabled
            if validate:
                data_list = self._validate_before_save(data_list)

            # Create backup and write atomically
            backup = self._create_backup()
            atomic_json_save(self.json_file_path, data_list, create_backup=False)
            if backup:
                logger.debug(f"Created backup: {backup}")

            # Update cache and index
            self._enrichment_cache = enrichment_data
            self._address_index = self._build_address_index(enrichment_data)

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

        # Find or validate backup path
        if backup_path is None:
            backups = self._find_backups()
            if not backups:
                return False
            backup_path = backups[0]
        else:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

        # Validate backup integrity
        if not self._validate_backup(backup_path):
            raise DataLoadError(f"Backup file validation failed: {backup_path}")

        # Save current file as corrupted backup (best effort)
        if self.json_file_path.exists():
            corrupted_backup = self.json_file_path.with_suffix(".corrupted.json")
            try:
                shutil.copy2(self.json_file_path, corrupted_backup)
                logger.info(f"Saved corrupted file to: {corrupted_backup}")
            except OSError:
                pass

        # Restore from backup
        shutil.copy2(backup_path, self.json_file_path)
        logger.info(f"Restored from backup: {backup_path}")

        # Invalidate cache and index
        self._enrichment_cache = None
        self._address_index = None

        return True

    def apply_enrichment_to_property(
        self, property: Property, enrichment_dict: dict | None = None
    ) -> Property:
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
        property.sewer_type = (
            SewerType(enrichment_data.sewer_type) if enrichment_data.sewer_type else None
        )  # type: ignore[arg-type]
        property.tax_annual = enrichment_data.tax_annual
        property.hoa_fee = enrichment_data.hoa_fee
        property.commute_minutes = enrichment_data.commute_minutes
        property.school_district = enrichment_data.school_district
        property.school_rating = enrichment_data.school_rating
        # Convert string to enum for orientation
        property.orientation = (
            Orientation(enrichment_data.orientation) if enrichment_data.orientation else None
        )  # type: ignore[arg-type]
        property.distance_to_grocery_miles = enrichment_data.distance_to_grocery_miles
        property.distance_to_highway_miles = enrichment_data.distance_to_highway_miles
        # Convert string to enum for solar_status
        property.solar_status = (
            SolarStatus(enrichment_data.solar_status) if enrichment_data.solar_status else None
        )  # type: ignore[arg-type]
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
            # Core identification
            full_address=full_address,
            normalized_address=normalized,
            # County assessor data
            lot_sqft=data.get("lot_sqft"),
            year_built=data.get("year_built"),
            garage_spaces=data.get("garage_spaces"),
            sewer_type=data.get("sewer_type"),
            tax_annual=data.get("tax_annual"),
            # HOA and location data
            hoa_fee=data.get("hoa_fee"),
            beds=data.get("beds"),
            baths=data.get("baths"),
            sqft=data.get("sqft"),
            commute_minutes=data.get("commute_minutes"),
            school_district=data.get("school_district"),
            school_rating=data.get("school_rating"),
            orientation=data.get("orientation"),
            distance_to_grocery_miles=data.get("distance_to_grocery_miles"),
            distance_to_highway_miles=data.get("distance_to_highway_miles"),
            # Arizona-specific features
            solar_status=data.get("solar_status"),
            solar_lease_monthly=data.get("solar_lease_monthly"),
            has_pool=data.get("has_pool"),
            pool_equipment_age=data.get("pool_equipment_age"),
            roof_age=data.get("roof_age"),
            hvac_age=data.get("hvac_age"),
            # Manual assessment fields
            kitchen_layout_score=data.get("kitchen_layout_score"),
            master_suite_score=data.get("master_suite_score"),
            natural_light_score=data.get("natural_light_score"),
            high_ceilings_score=data.get("high_ceilings_score"),
            fireplace_present=data.get("fireplace_present"),
            laundry_area_score=data.get("laundry_area_score"),
            aesthetics_score=data.get("aesthetics_score"),
            backyard_utility_score=data.get("backyard_utility_score"),
            safety_neighborhood_score=data.get("safety_neighborhood_score"),
            parks_walkability_score=data.get("parks_walkability_score"),
            # Location - Crime/Safety
            violent_crime_index=data.get("violent_crime_index"),
            property_crime_index=data.get("property_crime_index"),
            crime_risk_level=data.get("crime_risk_level"),
            # Location - Flood Zone
            flood_zone=data.get("flood_zone"),
            flood_zone_panel=data.get("flood_zone_panel"),
            flood_insurance_required=data.get("flood_insurance_required"),
            # Location - Walk/Transit/Bike Scores
            walk_score=data.get("walk_score"),
            transit_score=data.get("transit_score"),
            bike_score=data.get("bike_score"),
            # Location - Noise
            noise_score=data.get("noise_score"),
            noise_sources=data.get("noise_sources"),
            # Location - Zoning
            zoning_code=data.get("zoning_code"),
            zoning_description=data.get("zoning_description"),
            zoning_category=data.get("zoning_category"),
            # Demographics
            census_tract=data.get("census_tract"),
            median_household_income=data.get("median_household_income"),
            median_home_value=data.get("median_home_value"),
            # Schools - Enhanced
            elementary_rating=data.get("elementary_rating"),
            middle_rating=data.get("middle_rating"),
            high_rating=data.get("high_rating"),
            school_count_1mi=data.get("school_count_1mi"),
            # Market Data
            list_price=data.get("list_price"),
            days_on_market=data.get("days_on_market"),
            original_list_price=data.get("original_list_price"),
            price_reduced=data.get("price_reduced"),
            price_reduced_pct=data.get("price_reduced_pct"),
            # Air Quality
            air_quality_aqi=data.get("air_quality_aqi"),
            air_quality_category=data.get("air_quality_category"),
            air_quality_pollutant=data.get("air_quality_pollutant"),
            # Permit History
            permit_count=data.get("permit_count"),
            permit_types=data.get("permit_types"),
            last_roof_permit_year=data.get("last_roof_permit_year"),
            last_hvac_permit_year=data.get("last_hvac_permit_year"),
            has_solar_permit=data.get("has_solar_permit"),
            # Exterior Assessment
            roof_visual_condition=data.get("roof_visual_condition"),
            roof_age_visual_estimate=data.get("roof_age_visual_estimate"),
            roof_condition_notes=data.get("roof_condition_notes"),
            pool_equipment_age_visual=data.get("pool_equipment_age_visual"),
            pool_equipment_condition=data.get("pool_equipment_condition"),
            pool_system_type=data.get("pool_system_type"),
            hvac_age_visual_estimate=data.get("hvac_age_visual_estimate"),
            hvac_brand=data.get("hvac_brand"),
            hvac_refrigerant=data.get("hvac_refrigerant"),
            hvac_condition_notes=data.get("hvac_condition_notes"),
            foundation_concerns=data.get("foundation_concerns"),
            foundation_red_flags=data.get("foundation_red_flags"),
            backyard_covered_patio=data.get("backyard_covered_patio"),
            backyard_patio_score=data.get("backyard_patio_score"),
            backyard_pool_ratio=data.get("backyard_pool_ratio"),
            backyard_sun_orientation=data.get("backyard_sun_orientation"),
            # Zillow identifiers
            zpid=data.get("zpid"),
            # MLS Listing Identifiers
            mls_number=data.get("mls_number"),
            listing_url=data.get("listing_url"),
            listing_status=data.get("listing_status"),
            listing_office=data.get("listing_office"),
            mls_last_updated=data.get("mls_last_updated"),
            # Property Classification
            property_type=data.get("property_type"),
            architecture_style=data.get("architecture_style"),
            # Systems & Utilities
            cooling_type=data.get("cooling_type"),
            heating_type=data.get("heating_type"),
            water_source=data.get("water_source"),
            roof_material=data.get("roof_material"),
            # Interior Features (Structured lists)
            kitchen_features=data.get("kitchen_features"),
            master_bath_features=data.get("master_bath_features"),
            laundry_features=data.get("laundry_features"),
            interior_features_list=data.get("interior_features_list"),
            flooring_types=data.get("flooring_types"),
            # Exterior Features (Structured lists)
            exterior_features_list=data.get("exterior_features_list"),
            patio_features=data.get("patio_features"),
            lot_features=data.get("lot_features"),
            # Schools (Names)
            elementary_school_name=data.get("elementary_school_name"),
            middle_school_name=data.get("middle_school_name"),
            high_school_name=data.get("high_school_name"),
            # Location Reference
            cross_streets=data.get("cross_streets"),
            # === E2-R3: EXTENDED MLS FIELDS ===
            # Geo Coordinates
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            # Legal/Parcel Data
            township=data.get("township"),
            range_section=data.get("range_section"),
            section=data.get("section"),
            lot_number=data.get("lot_number"),
            subdivision=data.get("subdivision"),
            apn=data.get("apn"),
            # Property Structure
            exterior_stories=data.get("exterior_stories"),
            interior_levels=data.get("interior_levels"),
            builder_name=data.get("builder_name"),
            dwelling_styles=data.get("dwelling_styles"),
            # View & Environment Features
            view_features=data.get("view_features"),
            community_features=data.get("community_features"),
            property_description=data.get("property_description"),
            # Interior Feature Categories
            dining_area_features=data.get("dining_area_features"),
            technology_features=data.get("technology_features"),
            window_features=data.get("window_features"),
            other_rooms=data.get("other_rooms"),
            # Exterior Feature Categories
            construction_materials=data.get("construction_materials"),
            construction_finish=data.get("construction_finish"),
            parking_features=data.get("parking_features"),
            fencing_types=data.get("fencing_types"),
            # School Districts
            elementary_district=data.get("elementary_district"),
            middle_district=data.get("middle_district"),
            high_district=data.get("high_district"),
            # Contract/Listing Info
            list_date=data.get("list_date"),
            ownership_type=data.get("ownership_type"),
            possession_terms=data.get("possession_terms"),
            new_financing=data.get("new_financing"),
            # Pool Details
            private_pool_features=data.get("private_pool_features"),
            spa_features=data.get("spa_features"),
            community_pool=data.get("community_pool"),
            # Updates/Renovations
            kitchen_year_updated=data.get("kitchen_year_updated"),
            kitchen_update_scope=data.get("kitchen_update_scope"),
            # Basement
            has_basement=data.get("has_basement"),
            # Additional Details
            fireplaces_total=data.get("fireplaces_total"),
            total_covered_spaces=data.get("total_covered_spaces"),
            utilities_provider=data.get("utilities_provider"),
            services_available=data.get("services_available"),
            # Listing Remarks
            public_remarks=data.get("public_remarks"),
            directions=data.get("directions"),
        )

        # Load provenance metadata if present
        if "_provenance" in data:
            for field_name, prov_data in data["_provenance"].items():
                enrichment.set_field_provenance(
                    field_name=field_name,
                    source=prov_data["data_source"],
                    confidence=prov_data["confidence"],
                    fetched_at=prov_data["fetched_at"],
                    agent_id=prov_data.get("agent_id"),
                    phase=prov_data.get("phase"),
                    derived_from=prov_data.get("derived_from", []),
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
            # Core identification
            "full_address": enrichment.full_address,
            "normalized_address": normalized,
            # County assessor data
            "lot_sqft": enrichment.lot_sqft,
            "year_built": enrichment.year_built,
            "garage_spaces": enrichment.garage_spaces,
            "sewer_type": enrichment.sewer_type,
            "tax_annual": enrichment.tax_annual,
            # HOA and location data
            "hoa_fee": enrichment.hoa_fee,
            "beds": enrichment.beds,
            "baths": enrichment.baths,
            "sqft": enrichment.sqft,
            "commute_minutes": enrichment.commute_minutes,
            "school_district": enrichment.school_district,
            "school_rating": enrichment.school_rating,
            "orientation": enrichment.orientation,
            "distance_to_grocery_miles": enrichment.distance_to_grocery_miles,
            "distance_to_highway_miles": enrichment.distance_to_highway_miles,
            # Arizona-specific features
            "solar_status": enrichment.solar_status,
            "solar_lease_monthly": enrichment.solar_lease_monthly,
            "has_pool": enrichment.has_pool,
            "pool_equipment_age": enrichment.pool_equipment_age,
            "roof_age": enrichment.roof_age,
            "hvac_age": enrichment.hvac_age,
            # Manual assessment fields
            "kitchen_layout_score": enrichment.kitchen_layout_score,
            "master_suite_score": enrichment.master_suite_score,
            "natural_light_score": enrichment.natural_light_score,
            "high_ceilings_score": enrichment.high_ceilings_score,
            "fireplace_present": enrichment.fireplace_present,
            "laundry_area_score": enrichment.laundry_area_score,
            "aesthetics_score": enrichment.aesthetics_score,
            "backyard_utility_score": enrichment.backyard_utility_score,
            "safety_neighborhood_score": enrichment.safety_neighborhood_score,
            "parks_walkability_score": enrichment.parks_walkability_score,
            # Location - Crime/Safety
            "violent_crime_index": enrichment.violent_crime_index,
            "property_crime_index": enrichment.property_crime_index,
            "crime_risk_level": enrichment.crime_risk_level,
            # Location - Flood Zone
            "flood_zone": enrichment.flood_zone,
            "flood_zone_panel": enrichment.flood_zone_panel,
            "flood_insurance_required": enrichment.flood_insurance_required,
            # Location - Walk/Transit/Bike Scores
            "walk_score": enrichment.walk_score,
            "transit_score": enrichment.transit_score,
            "bike_score": enrichment.bike_score,
            # Location - Noise
            "noise_score": enrichment.noise_score,
            "noise_sources": enrichment.noise_sources,
            # Location - Zoning
            "zoning_code": enrichment.zoning_code,
            "zoning_description": enrichment.zoning_description,
            "zoning_category": enrichment.zoning_category,
            # Demographics
            "census_tract": enrichment.census_tract,
            "median_household_income": enrichment.median_household_income,
            "median_home_value": enrichment.median_home_value,
            # Schools - Enhanced
            "elementary_rating": enrichment.elementary_rating,
            "middle_rating": enrichment.middle_rating,
            "high_rating": enrichment.high_rating,
            "school_count_1mi": enrichment.school_count_1mi,
            # Market Data
            "list_price": enrichment.list_price,
            "days_on_market": enrichment.days_on_market,
            "original_list_price": enrichment.original_list_price,
            "price_reduced": enrichment.price_reduced,
            "price_reduced_pct": enrichment.price_reduced_pct,
            # Air Quality
            "air_quality_aqi": enrichment.air_quality_aqi,
            "air_quality_category": enrichment.air_quality_category,
            "air_quality_pollutant": enrichment.air_quality_pollutant,
            # Permit History
            "permit_count": enrichment.permit_count,
            "permit_types": enrichment.permit_types,
            "last_roof_permit_year": enrichment.last_roof_permit_year,
            "last_hvac_permit_year": enrichment.last_hvac_permit_year,
            "has_solar_permit": enrichment.has_solar_permit,
            # Exterior Assessment
            "roof_visual_condition": enrichment.roof_visual_condition,
            "roof_age_visual_estimate": enrichment.roof_age_visual_estimate,
            "roof_condition_notes": enrichment.roof_condition_notes,
            "pool_equipment_age_visual": enrichment.pool_equipment_age_visual,
            "pool_equipment_condition": enrichment.pool_equipment_condition,
            "pool_system_type": enrichment.pool_system_type,
            "hvac_age_visual_estimate": enrichment.hvac_age_visual_estimate,
            "hvac_brand": enrichment.hvac_brand,
            "hvac_refrigerant": enrichment.hvac_refrigerant,
            "hvac_condition_notes": enrichment.hvac_condition_notes,
            "foundation_concerns": enrichment.foundation_concerns,
            "foundation_red_flags": enrichment.foundation_red_flags,
            "backyard_covered_patio": enrichment.backyard_covered_patio,
            "backyard_patio_score": enrichment.backyard_patio_score,
            "backyard_pool_ratio": enrichment.backyard_pool_ratio,
            "backyard_sun_orientation": enrichment.backyard_sun_orientation,
            # Zillow identifiers
            "zpid": enrichment.zpid,
            # MLS Listing Identifiers
            "mls_number": enrichment.mls_number,
            "listing_url": enrichment.listing_url,
            "listing_status": enrichment.listing_status,
            "listing_office": enrichment.listing_office,
            "mls_last_updated": enrichment.mls_last_updated,
            # Property Classification
            "property_type": enrichment.property_type,
            "architecture_style": enrichment.architecture_style,
            # Systems & Utilities
            "cooling_type": enrichment.cooling_type,
            "heating_type": enrichment.heating_type,
            "water_source": enrichment.water_source,
            "roof_material": enrichment.roof_material,
            # Interior Features (Structured lists)
            "kitchen_features": enrichment.kitchen_features,
            "master_bath_features": enrichment.master_bath_features,
            "laundry_features": enrichment.laundry_features,
            "interior_features_list": enrichment.interior_features_list,
            "flooring_types": enrichment.flooring_types,
            # Exterior Features (Structured lists)
            "exterior_features_list": enrichment.exterior_features_list,
            "patio_features": enrichment.patio_features,
            "lot_features": enrichment.lot_features,
            # Schools (Names)
            "elementary_school_name": enrichment.elementary_school_name,
            "middle_school_name": enrichment.middle_school_name,
            "high_school_name": enrichment.high_school_name,
            # Location Reference
            "cross_streets": enrichment.cross_streets,
            # === E2-R3: EXTENDED MLS FIELDS ===
            # Geo Coordinates
            "latitude": enrichment.latitude,
            "longitude": enrichment.longitude,
            # Legal/Parcel Data
            "township": enrichment.township,
            "range_section": enrichment.range_section,
            "section": enrichment.section,
            "lot_number": enrichment.lot_number,
            "subdivision": enrichment.subdivision,
            "apn": enrichment.apn,
            # Property Structure
            "exterior_stories": enrichment.exterior_stories,
            "interior_levels": enrichment.interior_levels,
            "builder_name": enrichment.builder_name,
            "dwelling_styles": enrichment.dwelling_styles,
            # View & Environment Features
            "view_features": enrichment.view_features,
            "community_features": enrichment.community_features,
            "property_description": enrichment.property_description,
            # Interior Feature Categories
            "dining_area_features": enrichment.dining_area_features,
            "technology_features": enrichment.technology_features,
            "window_features": enrichment.window_features,
            "other_rooms": enrichment.other_rooms,
            # Exterior Feature Categories
            "construction_materials": enrichment.construction_materials,
            "construction_finish": enrichment.construction_finish,
            "parking_features": enrichment.parking_features,
            "fencing_types": enrichment.fencing_types,
            # School Districts
            "elementary_district": enrichment.elementary_district,
            "middle_district": enrichment.middle_district,
            "high_district": enrichment.high_district,
            # Contract/Listing Info
            "list_date": enrichment.list_date,
            "ownership_type": enrichment.ownership_type,
            "possession_terms": enrichment.possession_terms,
            "new_financing": enrichment.new_financing,
            # Pool Details
            "private_pool_features": enrichment.private_pool_features,
            "spa_features": enrichment.spa_features,
            "community_pool": enrichment.community_pool,
            # Updates/Renovations
            "kitchen_year_updated": enrichment.kitchen_year_updated,
            "kitchen_update_scope": enrichment.kitchen_update_scope,
            # Basement
            "has_basement": enrichment.has_basement,
            # Additional Details
            "fireplaces_total": enrichment.fireplaces_total,
            "total_covered_spaces": enrichment.total_covered_spaces,
            "utilities_provider": enrichment.utilities_provider,
            "services_available": enrichment.services_available,
            # Listing Remarks
            "public_remarks": enrichment.public_remarks,
            "directions": enrichment.directions,
        }

        # Add provenance metadata if present
        if enrichment._provenance:
            base_dict["_provenance"] = {
                field_name: {
                    "data_source": prov.data_source,
                    "confidence": prov.confidence,
                    "fetched_at": prov.fetched_at,
                    "agent_id": prov.agent_id,
                    "phase": prov.phase,
                    "derived_from": prov.derived_from,
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
                "hvac_age": 8,
            }
        ]

        try:
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_file_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
        except OSError:
            # If template creation fails, silently continue
            # The empty cache will be returned
            pass

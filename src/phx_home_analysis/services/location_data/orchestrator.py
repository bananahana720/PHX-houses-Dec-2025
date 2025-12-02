"""Orchestrator for coordinating all location data extractors.

Coordinates extraction from multiple location data sources with state management,
crash recovery, and intelligent skipping of already-processed data.

Supported sources:
- crime: Crime statistics (ZIP-level, SpotCrime API)
- walkscore: Walk Score, Transit Score, Bike Score (per property)
- schools: School ratings (per property, GreatSchools)
- noise: Noise levels (per property, HowLoud)
- flood: FEMA flood zones (per property, coordinate-based)
- census: Demographics (ZIP-level, Census API)
- zoning: Zoning codes (per property, Maricopa County)
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...domain.entities import Property
from ...validation.deduplication import compute_property_hash
from .state_manager import LocationStateManager

# Use TYPE_CHECKING to avoid circular imports at runtime
# Imports only used for type hints
if TYPE_CHECKING:
    from ..census_data import DemographicData
    from ..county_data import ZoningData
    from ..crime_data import CrimeData
    from ..flood_data import FloodZoneData
    from ..noise_data import NoiseData
    from ..schools import SchoolData
    from ..walkscore import WalkScoreData

logger = logging.getLogger(__name__)


@dataclass
class LocationData:
    """Aggregated location data from all sources.

    Combines data from multiple extractors into a single object
    with convenience method for converting to enrichment format.
    """

    crime: "CrimeData | None" = None
    walkscore: "WalkScoreData | None" = None
    schools: "SchoolData | None" = None
    noise: "NoiseData | None" = None
    flood: "FloodZoneData | None" = None
    census: "DemographicData | None" = None
    zoning: "ZoningData | None" = None

    def to_enrichment_dict(self) -> dict[str, Any]:
        """Convert to enrichment data format.

        Returns:
            Dictionary suitable for merging into enrichment_data.json
        """
        result = {}
        if self.crime:
            result.update(self.crime.to_enrichment_dict())
        if self.walkscore:
            result.update(self.walkscore.to_enrichment_dict())
        if self.schools:
            result.update(self.schools.to_enrichment_dict())
        if self.noise:
            result.update(self.noise.to_enrichment_dict())
        if self.flood:
            result.update(self.flood.to_enrichment_dict())
        if self.census:
            result.update(self.census.to_enrichment_dict())
        if self.zoning:
            result["zoning_code"] = self.zoning.zoning_code
            result["zoning_description"] = self.zoning.zoning_description
            result["zoning_category"] = self.zoning.zoning_category
        return result


class LocationDataOrchestrator:
    """Coordinates extraction from all location data sources.

    Manages state persistence, crash recovery, and intelligent skipping
    of already-processed data across multiple extraction sources.

    Example:
        orchestrator = LocationDataOrchestrator()
        results = await orchestrator.extract_batch(properties)
        await orchestrator.close()
    """

    SOURCES = ["crime", "walkscore", "schools", "noise", "flood", "census", "zoning"]
    ZIP_LEVEL_SOURCES = ["crime", "census"]  # These batch by ZIP

    def __init__(
        self,
        state_manager: LocationStateManager | None = None,
        enabled_sources: list[str] | None = None,
    ):
        """Initialize orchestrator.

        Args:
            state_manager: Optional state manager. Creates default if None.
            enabled_sources: List of sources to extract. Uses all if None.
        """
        self.state = state_manager or LocationStateManager()
        self.enabled_sources = set(enabled_sources or self.SOURCES)

        # Validate sources
        invalid = self.enabled_sources - set(self.SOURCES)
        if invalid:
            raise ValueError(f"Invalid sources: {invalid}. Valid sources: {self.SOURCES}")

        # Initialize extractors lazily (use Any to avoid circular import)
        self._crime_extractor: Any = None
        self._walk_extractor: Any = None
        self._school_extractor: Any = None
        self._noise_extractor: Any = None
        self._flood_client: Any = None
        self._census_client: Any = None
        self._assessor_client: Any = None

    async def extract_for_property(
        self,
        property: Property,
        skip_completed: bool = True,
    ) -> LocationData:
        """Extract all location data for a property.

        Args:
            property: Property to extract data for
            skip_completed: Whether to skip already-completed sources

        Returns:
            LocationData with extracted data from all sources
        """
        prop_hash = compute_property_hash(property.full_address)
        logger.info("Extracting location data for %s (%s)", property.full_address, prop_hash)

        result = LocationData()

        # Crime (ZIP-level)
        if "crime" in self.enabled_sources:
            if not skip_completed or not self.state.is_zip_completed(property.zip_code, "crime"):
                result.crime = await self._extract_crime(property)
                if result.crime:
                    self.state.mark_zip_completed(property.zip_code, "crime")
                    self.state.mark_source_completed(prop_hash, "crime")
            else:
                logger.debug("Skipping crime data (ZIP %s already completed)", property.zip_code)

        # Walk Score (per property)
        if "walkscore" in self.enabled_sources:
            if not skip_completed or not self.state.is_property_completed(prop_hash, "walkscore"):
                result.walkscore = await self._extract_walkscore(property)
                if result.walkscore:
                    self.state.mark_source_completed(prop_hash, "walkscore")
            else:
                logger.debug("Skipping walk score (already completed)")

        # Schools (per property)
        if "schools" in self.enabled_sources:
            if not skip_completed or not self.state.is_property_completed(prop_hash, "schools"):
                result.schools = await self._extract_schools(property)
                if result.schools:
                    self.state.mark_source_completed(prop_hash, "schools")
            else:
                logger.debug("Skipping schools (already completed)")

        # Noise (per property)
        if "noise" in self.enabled_sources:
            if not skip_completed or not self.state.is_property_completed(prop_hash, "noise"):
                result.noise = await self._extract_noise(property)
                if result.noise:
                    self.state.mark_source_completed(prop_hash, "noise")
            else:
                logger.debug("Skipping noise (already completed)")

        # Flood (per property, coordinate-based)
        if "flood" in self.enabled_sources:
            if not skip_completed or not self.state.is_property_completed(prop_hash, "flood"):
                result.flood = await self._extract_flood(property)
                if result.flood:
                    self.state.mark_source_completed(prop_hash, "flood")
            else:
                logger.debug("Skipping flood (already completed)")

        # Census (ZIP-level)
        if "census" in self.enabled_sources:
            if not skip_completed or not self.state.is_zip_completed(property.zip_code, "census"):
                result.census = await self._extract_census(property)
                if result.census:
                    self.state.mark_zip_completed(property.zip_code, "census")
                    self.state.mark_source_completed(prop_hash, "census")
            else:
                logger.debug("Skipping census (ZIP %s already completed)", property.zip_code)

        # Zoning (per property)
        if "zoning" in self.enabled_sources:
            if not skip_completed or not self.state.is_property_completed(prop_hash, "zoning"):
                result.zoning = await self._extract_zoning(property)
                if result.zoning:
                    self.state.mark_source_completed(prop_hash, "zoning")
            else:
                logger.debug("Skipping zoning (already completed)")

        # Save state after each property
        self.state.save()

        return result

    async def extract_batch(
        self,
        properties: list[Property],
        max_concurrent: int = 3,
        skip_completed: bool = True,
    ) -> dict[str, LocationData]:
        """Extract location data for multiple properties.

        Args:
            properties: List of properties to extract
            max_concurrent: Maximum concurrent extractions (default 3)
            skip_completed: Whether to skip already-completed properties

        Returns:
            Dictionary mapping property hash to LocationData
        """
        results = {}

        # Process sequentially for now (nodriver doesn't support concurrent browsers well)
        # TODO: Investigate concurrent extraction with separate browser instances
        for prop in properties:
            prop_hash = compute_property_hash(prop.full_address)

            if skip_completed and self.state.is_property_completed(prop_hash):
                logger.info("Skipping completed property: %s", prop.full_address)
                continue

            if self.state.is_permanent_failure(prop_hash, "all"):
                logger.info("Skipping permanent failure: %s", prop.full_address)
                continue

            try:
                results[prop_hash] = await self.extract_for_property(prop, skip_completed)
                self.state.mark_property_completed(prop_hash)
            except Exception as e:
                logger.error("Failed to extract for %s: %s", prop.full_address, e)
                self.state.mark_property_failed(prop_hash)

            self.state.save()

        return results

    async def _extract_crime(self, property: Property) -> Any:
        """Extract crime data.

        Args:
            property: Property to extract for

        Returns:
            CrimeData if successful, None otherwise
        """
        if not self._crime_extractor:
            # Lazy import to avoid circular dependency
            from ..crime_data import CrimeDataExtractor

            self._crime_extractor = CrimeDataExtractor()
        try:
            result = await self._crime_extractor.extract(property)
            return result.data if result.success else None
        except Exception as e:
            logger.error("Crime extraction failed: %s", e)
            return None

    async def _extract_walkscore(self, property: Property) -> Any:
        """Extract walk score data.

        Args:
            property: Property to extract for

        Returns:
            WalkScoreData if successful, None otherwise
        """
        if not self._walk_extractor:
            from ..walkscore import WalkScoreExtractor

            self._walk_extractor = WalkScoreExtractor()
        try:
            result = await self._walk_extractor.extract(property)
            return result.data if result.success else None
        except Exception as e:
            logger.error("Walk score extraction failed: %s", e)
            return None

    async def _extract_schools(self, property: Property) -> Any:
        """Extract school data.

        Args:
            property: Property to extract for

        Returns:
            SchoolData if successful, None otherwise
        """
        if not self._school_extractor:
            from ..schools import GreatSchoolsExtractor

            self._school_extractor = GreatSchoolsExtractor()
        try:
            result = await self._school_extractor.extract(property)
            return result.data if result.success else None
        except Exception as e:
            logger.error("School extraction failed: %s", e)
            return None

    async def _extract_noise(self, property: Property) -> Any:
        """Extract noise data.

        Args:
            property: Property to extract for

        Returns:
            NoiseData if successful, None otherwise
        """
        if not self._noise_extractor:
            from ..noise_data import HowLoudExtractor

            self._noise_extractor = HowLoudExtractor()
        try:
            result = await self._noise_extractor.extract(property)
            return result.data if result.success else None
        except Exception as e:
            logger.error("Noise extraction failed: %s", e)
            return None

    async def _extract_flood(self, property: Property) -> Any:
        """Extract flood zone data.

        Args:
            property: Property to extract for

        Returns:
            FloodZoneData if successful, None otherwise
        """
        if not property.latitude or not property.longitude:
            logger.warning("No coordinates for flood lookup: %s", property.full_address)
            return None
        if not self._flood_client:
            from ..flood_data import FEMAFloodClient

            self._flood_client = FEMAFloodClient()
        try:
            return await self._flood_client.get_flood_zone(property.latitude, property.longitude)
        except Exception as e:
            logger.error("Flood extraction failed: %s", e)
            return None

    async def _extract_census(self, property: Property) -> Any:
        """Extract census data.

        Args:
            property: Property to extract for

        Returns:
            DemographicData if successful, None otherwise
        """
        if not property.latitude or not property.longitude:
            logger.warning("No coordinates for census lookup: %s", property.full_address)
            return None
        if not self._census_client:
            from ..census_data import CensusAPIClient

            self._census_client = CensusAPIClient()
        try:
            return await self._census_client.get_demographics(property.latitude, property.longitude)
        except Exception as e:
            logger.error("Census extraction failed: %s", e)
            return None

    async def _extract_zoning(self, property: Property) -> Any:
        """Extract zoning data.

        Args:
            property: Property to extract for

        Returns:
            ZoningData if successful, None otherwise
        """
        if not property.latitude or not property.longitude:
            logger.warning("No coordinates for zoning lookup: %s", property.full_address)
            return None
        if not self._assessor_client:
            from ..county_data import MaricopaAssessorClient

            self._assessor_client = MaricopaAssessorClient()
        try:
            return await self._assessor_client.get_zoning_data(property.latitude, property.longitude)
        except Exception as e:
            logger.error("Zoning extraction failed: %s", e)
            return None

    async def close(self) -> None:
        """Close all extractors and save final state."""
        if self._crime_extractor:
            await self._crime_extractor.close()
        if self._walk_extractor:
            await self._walk_extractor.close()
        if self._school_extractor:
            await self._school_extractor.close()
        if self._noise_extractor:
            await self._noise_extractor.close()
        if self._flood_client:
            await self._flood_client.close()
        if self._census_client:
            await self._census_client.close()
        if self._assessor_client:
            await self._assessor_client.close()

        # Save final state
        self.state.save()
        logger.info("Orchestrator closed, state saved")

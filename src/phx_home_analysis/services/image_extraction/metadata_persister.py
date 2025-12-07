"""Metadata persistence service for listing extraction data.

Persists extracted listing metadata (kill-switch fields, MLS info) to
enrichment_data.json with proper provenance tracking.
"""

import logging
from pathlib import Path
from typing import Any

from ...domain.entities import EnrichmentData
from ...repositories.json_repository import JsonEnrichmentRepository
from ...services.quality.lineage import LineageTracker
from ...services.quality.models import DataSource
from ...services.quality.provenance_service import ProvenanceService

logger = logging.getLogger(__name__)


# Field mapping from PhoenixMLS metadata keys to EnrichmentData fields
MLS_FIELD_MAPPING: dict[str, str] = {
    "hoa_fee": "hoa_fee",
    "beds": "beds",
    "baths": "baths",
    "sqft": "sqft",
    "lot_sqft": "lot_sqft",
    "garage_spaces": "garage_spaces",
    "sewer_type": "sewer_type",
    "year_built": "year_built",
    "mls_number": "mls_number",
    "listing_url": "listing_url",
}


class MetadataPersister:
    """Persists extracted listing metadata to enrichment_data.json.

    Integrates with ProvenanceService for field-level lineage tracking
    and uses atomic writes for crash safety.

    Attributes:
        repository: JsonEnrichmentRepository for data persistence.
        provenance_service: ProvenanceService for tracking field provenance.
        data_source: DataSource enum value for this extractor.
    """

    def __init__(
        self,
        enrichment_path: Path | None = None,
        lineage_path: Path | None = None,
        data_source: DataSource = DataSource.PHOENIX_MLS,
    ):
        """Initialize MetadataPersister.

        Args:
            enrichment_path: Path to enrichment_data.json (default: data/enrichment_data.json)
            lineage_path: Path to field_lineage.json (default: data/field_lineage.json)
            data_source: DataSource for provenance tracking
        """
        if enrichment_path is None:
            enrichment_path = Path("data/enrichment_data.json")
        if lineage_path is None:
            lineage_path = Path("data/field_lineage.json")

        self.enrichment_path = enrichment_path
        self.repository = JsonEnrichmentRepository(enrichment_path)
        self.lineage_tracker = LineageTracker(lineage_path)
        self.provenance_service = ProvenanceService(self.lineage_tracker)
        self.data_source = data_source

    def persist_metadata(
        self,
        full_address: str,
        property_hash: str,
        metadata: dict[str, Any],
        agent_id: str = "listing-browser",
        phase: str = "phase1",
    ) -> dict[str, str]:
        """Persist listing metadata to enrichment_data.json.

        Args:
            full_address: Full property address (key for enrichment entry)
            property_hash: 8-char hash of address
            metadata: Dict of extracted metadata (from PhoenixMLS)
            agent_id: Agent that extracted the data
            phase: Pipeline phase (default: phase1)

        Returns:
            Dict mapping field names to update status ("updated", "skipped", "error")
        """
        results: dict[str, str] = {}

        # Load current enrichment data
        all_enrichment = self.repository.load_all()

        # Find or create entry for this property
        enrichment = None
        for entry in all_enrichment.values():
            if entry.full_address == full_address:
                enrichment = entry
                break

        if enrichment is None:
            # Create new entry
            enrichment = EnrichmentData(full_address=full_address)
            all_enrichment[full_address] = enrichment
            logger.info(f"Created new enrichment entry for: {full_address}")

        # Update fields from metadata
        updated_count = 0
        for mls_key, enrichment_field in MLS_FIELD_MAPPING.items():
            if mls_key not in metadata:
                continue

            value = metadata[mls_key]
            if value is None:
                continue

            # Get current value
            current_value = getattr(enrichment, enrichment_field, None)

            # Only update if value is different or missing
            if current_value == value:
                results[enrichment_field] = "unchanged"
                continue

            try:
                # Set the field value
                setattr(enrichment, enrichment_field, value)

                # Record provenance
                self.provenance_service.record_field(
                    enrichment=enrichment,
                    property_hash=property_hash,
                    field_name=enrichment_field,
                    source=self.data_source,
                    value=value,
                    agent_id=agent_id,
                    phase=phase,
                    notes="Extracted from PhoenixMLS listing",
                )

                results[enrichment_field] = "updated"
                updated_count += 1
                logger.debug(f"Updated {enrichment_field}: {current_value} -> {value}")

            except Exception as e:
                logger.error(f"Failed to update {enrichment_field}: {e}")
                results[enrichment_field] = f"error: {e}"

        # Save if any updates
        if updated_count > 0:
            self.repository.save_all(all_enrichment)
            self.lineage_tracker.save()
            logger.info(
                f"Persisted {updated_count} fields for {full_address} (hash: {property_hash})"
            )
        else:
            logger.debug(f"No updates needed for {full_address}")

        return results

    def persist_batch(
        self,
        properties: list[tuple[str, str, dict[str, Any]]],
        agent_id: str = "listing-browser",
        phase: str = "phase1",
    ) -> dict[str, dict[str, str]]:
        """Persist metadata for multiple properties.

        Args:
            properties: List of (full_address, property_hash, metadata) tuples
            agent_id: Agent that extracted the data
            phase: Pipeline phase

        Returns:
            Dict mapping addresses to field update results
        """
        all_results: dict[str, dict[str, str]] = {}

        for full_address, property_hash, metadata in properties:
            try:
                results = self.persist_metadata(
                    full_address=full_address,
                    property_hash=property_hash,
                    metadata=metadata,
                    agent_id=agent_id,
                    phase=phase,
                )
                all_results[full_address] = results
            except Exception as e:
                logger.error(f"Failed to persist metadata for {full_address}: {e}")
                all_results[full_address] = {"_error": str(e)}

        return all_results

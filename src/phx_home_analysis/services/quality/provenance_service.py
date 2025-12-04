"""Provenance tracking service for standardized field updates."""

import logging
from datetime import datetime
from typing import Any

from ...domain.entities import EnrichmentData
from .lineage import LineageTracker
from .models import DataSource

logger = logging.getLogger(__name__)


class ProvenanceService:
    """Service for recording provenance metadata consistently.

    Provides high-level API for scripts/agents to record data updates
    with proper confidence scoring and timestamp tracking.

    Attributes:
        lineage_tracker: LineageTracker instance for persistence.

    Example:
        >>> service = ProvenanceService()
        >>> service.record_batch(
        ...     enrichment=property_data,
        ...     property_hash="ef7cd95f",
        ...     source=DataSource.ASSESSOR_API,
        ...     fields={'lot_sqft': 9500, 'year_built': 2005}
        ... )
    """

    def __init__(self, lineage_tracker: LineageTracker | None = None):
        """Initialize provenance service.

        Args:
            lineage_tracker: LineageTracker instance (creates new if None).
        """
        self.lineage_tracker = lineage_tracker or LineageTracker()

    def record_field(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        field_name: str,
        source: DataSource,
        value: Any,
        confidence: float | None = None,
        agent_id: str | None = None,
        phase: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Record provenance for a single field update.

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address (first 8 chars).
            field_name: Name of the field being updated.
            source: Data source providing the value.
            value: The actual field value.
            confidence: Override confidence (uses source default if None).
            agent_id: Optional agent identifier.
            phase: Optional phase identifier (e.g., "phase0", "phase1").
            notes: Optional notes about the update.
        """
        if confidence is None:
            confidence = source.default_confidence

        timestamp = datetime.now().isoformat()

        # Update EnrichmentData provenance
        enrichment.set_field_provenance(
            field_name=field_name,
            source=source.value,
            confidence=confidence,
            fetched_at=timestamp,
            agent_id=agent_id,
            phase=phase,
        )

        # Track in LineageTracker for historical queries
        self.lineage_tracker.record_field(
            property_hash=property_hash,
            field_name=field_name,
            source=source,
            confidence=confidence,
            original_value=value,
            notes=notes,
        )

        logger.debug(
            f"Recorded provenance: {property_hash}.{field_name} "
            f"from {source.value} (confidence: {confidence:.2f})"
        )

    def record_batch(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        source: DataSource,
        fields: dict[str, Any],
        confidence: float | None = None,
        agent_id: str | None = None,
        phase: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Record provenance for multiple fields from the same source.

        Convenience method for batch updates (e.g., County Assessor API response).

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address.
            source: Data source for all fields.
            fields: Dictionary mapping field names to values.
            confidence: Override confidence (uses source default if None).
            agent_id: Optional agent identifier.
            phase: Optional phase identifier.
            notes: Optional notes about the batch.
        """
        if confidence is None:
            confidence = source.default_confidence

        for field_name, value in fields.items():
            self.record_field(
                enrichment=enrichment,
                property_hash=property_hash,
                field_name=field_name,
                source=source,
                value=value,
                confidence=confidence,
                agent_id=agent_id,
                phase=phase,
                notes=notes,
            )

        logger.info(
            f"Recorded batch provenance: {len(fields)} fields "
            f"from {source.value} for {property_hash}"
        )

    def record_derived(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        field_name: str,
        source: DataSource,
        value: Any,
        derived_from: list[str],
        confidence: float | None = None,
        agent_id: str | None = None,
        phase: str | None = None,
    ) -> None:
        """Record provenance for a derived field.

        For fields computed from other fields (e.g., cost_efficiency_score),
        tracks the source fields and uses minimum confidence (conservative).

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address.
            field_name: Name of the derived field.
            source: Primary data source (often AI_INFERENCE).
            value: The computed value.
            derived_from: List of source field names.
            confidence: Override confidence (uses minimum of sources if None).
            agent_id: Optional agent identifier.
            phase: Optional phase identifier.
        """
        if confidence is None:
            # Use minimum confidence among source fields (conservative)
            source_confidences = []
            for src_field in derived_from:
                prov = enrichment.get_field_provenance(src_field)
                if prov is not None:
                    source_confidences.append(prov.confidence)
            confidence = (
                min(source_confidences) if source_confidences else source.default_confidence
            )

        timestamp = datetime.now().isoformat()

        # Update EnrichmentData provenance
        enrichment.set_field_provenance(
            field_name=field_name,
            source=source.value,
            confidence=confidence,
            fetched_at=timestamp,
            agent_id=agent_id,
            phase=phase,
            derived_from=derived_from,
        )

        # Track in LineageTracker
        self.lineage_tracker.record_field(
            property_hash=property_hash,
            field_name=field_name,
            source=source,
            confidence=confidence,
            original_value=value,
            notes=f"Derived from: {', '.join(derived_from)}",
        )

        logger.debug(
            f"Recorded derived provenance: {property_hash}.{field_name} "
            f"from {source.value} (confidence: {confidence:.2f}, "
            f"sources: {len(derived_from)})"
        )

    def save(self) -> None:
        """Persist lineage data to disk."""
        self.lineage_tracker.save()

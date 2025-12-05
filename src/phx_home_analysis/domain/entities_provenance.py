"""Provenance methods for EnrichmentData - to be merged into entities.py"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .value_objects import FieldProvenance

# These methods should be added to the EnrichmentData class in entities.py

# First, add this field to EnrichmentData:
#     # Provenance metadata (field-level tracking)
#     _provenance: dict[str, FieldProvenance] = field(default_factory=dict)

# Then add these methods:

def set_field_provenance(
    self,
    field_name: str,
    source: str,
    confidence: float,
    fetched_at: str | None = None,
    agent_id: str | None = None,
    phase: str | None = None,
    derived_from: list[str] | None = None,
) -> None:
    """Set provenance metadata for a field.

    Args:
        field_name: Name of the field.
        source: Data source identifier (e.g., "assessor_api", "zillow").
        confidence: Confidence score (0.0-1.0).
        fetched_at: ISO 8601 timestamp (defaults to now).
        agent_id: Optional agent identifier.
        phase: Optional phase identifier (e.g., "phase0", "phase1").
        derived_from: Source fields for derived values.
    """
    from datetime import datetime

    if fetched_at is None:
        fetched_at = datetime.now().isoformat()

    self._provenance[field_name] = FieldProvenance(
        data_source=source,
        confidence=confidence,
        fetched_at=fetched_at,
        agent_id=agent_id,
        phase=phase,
        derived_from=derived_from or [],
    )

def get_field_provenance(self, field_name: str):  # -> FieldProvenance | None:
    """Get provenance metadata for a field.

    Args:
        field_name: Name of the field to query.

    Returns:
        FieldProvenance if set, None otherwise.
    """
    return self._provenance.get(field_name)

def get_low_confidence_fields(self, threshold: float = 0.80) -> list[str]:
    """Get fields with confidence below threshold.

    Args:
        threshold: Confidence threshold (default 0.80).

    Returns:
        List of field names with confidence < threshold.
    """
    return [
        field_name
        for field_name, prov in self._provenance.items()
        if prov.confidence < threshold
    ]

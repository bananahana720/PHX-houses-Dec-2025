"""Enrichment service for merging external data into property records.

This module provides services for:
1. Merging county assessor parcel data into enrichment_data.json with conflict
   detection and lineage tracking (EnrichmentMergeService)
2. Merging EnrichmentData objects into Property objects (EnrichmentMerger)

Example usage for county data merge:
    from phx_home_analysis.services.enrichment import EnrichmentMergeService

    service = EnrichmentMergeService(lineage_tracker=tracker)
    result = service.merge_parcel(enrichment, address, parcel)
    if result.success:
        enrichment[address] = result.updated_entry

Example usage for property enrichment:
    from phx_home_analysis.services.enrichment import EnrichmentMerger

    merger = EnrichmentMerger()
    enriched_property = merger.merge(property_obj, enrichment_data)
"""

from .merge_service import EnrichmentMergeService
from .merger import EnrichmentMerger
from .models import ConflictReport, FieldConflict, MergeResult
from .protocols import AssessorClientProtocol, LineageTrackerProtocol

__all__ = [
    # County data merge service
    "EnrichmentMergeService",
    "FieldConflict",
    "MergeResult",
    "ConflictReport",
    "AssessorClientProtocol",
    "LineageTrackerProtocol",
    # Property object enrichment
    "EnrichmentMerger",
]

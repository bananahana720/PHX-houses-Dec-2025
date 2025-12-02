"""Pydantic-based validation layer for property data.

This module provides schema validation, data normalization, type inference,
and duplicate detection for property data used in the PHX Home Analysis pipeline.

Exports:
    - PropertySchema: Pydantic model for property data validation
    - EnrichmentDataSchema: Pydantic model for enrichment data validation
    - SewerTypeSchema: Enum for sewer type values
    - PropertyValidator: Main validation class
    - ValidationResult: Result container for validation operations
    - normalize_address: Address normalization function
    - infer_type: Type inference from string values
    - DuplicateDetector: Hash-based duplicate detection class
    - compute_property_hash: Compute property hash from address
"""

from .deduplication import DuplicateDetector, compute_property_hash
from .normalizer import infer_type, normalize_address
from .schemas import (
    EnrichmentDataSchema,
    OrientationSchema,
    PropertySchema,
    SewerTypeSchema,
    SolarStatusSchema,
)
from .validators import (
    PropertyValidator,
    ValidationResult,
    validate_enrichment,
    validate_enrichment_entry,
    validate_enrichment_list,
    validate_property,
)

__all__ = [
    # Schemas
    "PropertySchema",
    "EnrichmentDataSchema",
    "SewerTypeSchema",
    "SolarStatusSchema",
    "OrientationSchema",
    # Validators
    "PropertyValidator",
    "ValidationResult",
    "validate_property",
    "validate_enrichment",
    "validate_enrichment_entry",
    "validate_enrichment_list",
    # Normalizers
    "normalize_address",
    "infer_type",
    # Deduplication
    "DuplicateDetector",
    "compute_property_hash",
]

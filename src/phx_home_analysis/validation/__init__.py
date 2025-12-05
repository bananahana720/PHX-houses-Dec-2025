"""Pydantic-based validation layer for property data and configuration.

This module provides schema validation, data normalization, type inference,
and duplicate detection for property data used in the PHX Home Analysis pipeline.

Property Schemas:
    - PropertySchema: Pydantic model for property data validation
    - EnrichmentDataSchema: Pydantic model for enrichment data validation
    - SewerTypeSchema: Enum for sewer type values

Image Schemas (E2.S4):
    - ImageEntryV2: Pydantic model for image manifest entries with lineage
    - URLEntryV2: Pydantic model for URL tracker entries with lineage
    - ManifestV2: Pydantic model for manifest structure validation

Configuration Schemas (E1.S1):
    - AppConfigSchema: Complete application configuration
    - ScoringWeightsConfigSchema: Scoring weights from scoring_weights.yaml
    - BuyerCriteriaConfigSchema: Buyer criteria from buyer_criteria.yaml
    - ConfigurationError: Exception for configuration validation failures

Validators:
    - PropertyValidator: Main validation class
    - ValidationResult: Result container for validation operations
    - normalize_address: Address normalization function
    - infer_type: Type inference from string values

Deduplication:
    - DuplicateDetector: Hash-based duplicate detection class
    - compute_property_hash: Compute property hash from address
"""

from .config_schemas import (
    AppConfigSchema,
    BuyerCriteriaConfigSchema,
    ConfigurationError,
    HardCriteriaSchema,
    ScoringWeightsConfigSchema,
    SectionWeightsSchema,
    SoftCriteriaSchema,
    ThresholdsSchema,
    TierThresholdsSchema,
    ValueZonesSchema,
)
from .deduplication import DuplicateDetector, compute_property_hash
from .image_schemas import ImageEntryV2, ManifestV2, URLEntryV2
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
    # Property Schemas
    "PropertySchema",
    "EnrichmentDataSchema",
    "SewerTypeSchema",
    "SolarStatusSchema",
    "OrientationSchema",
    # Image Schemas (E2.S4)
    "ImageEntryV2",
    "URLEntryV2",
    "ManifestV2",
    # Configuration Schemas (E1.S1)
    "ConfigurationError",
    "AppConfigSchema",
    "ScoringWeightsConfigSchema",
    "BuyerCriteriaConfigSchema",
    "ValueZonesSchema",
    "SectionWeightsSchema",
    "TierThresholdsSchema",
    "HardCriteriaSchema",
    "SoftCriteriaSchema",
    "ThresholdsSchema",
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

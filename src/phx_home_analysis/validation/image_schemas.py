"""Pydantic validation models for image extraction data integrity.

Provides runtime validation for image manifest entries, URL tracker entries,
and manifest structure to ensure data lineage tracking and prevent corruption.

Key Features:
    - ImageEntryV2: Validates image manifest entries with full lineage
    - URLEntryV2: Validates URL tracker entries with audit trail
    - ManifestV2: Validates overall manifest structure
    - Hash validation: Ensures property_hash matches computed value from address
    - Field validators: Enforce length constraints and format requirements

Usage:
    from phx_home_analysis.validation.image_schemas import ImageEntryV2, ManifestV2

    # Validate manifest entry
    entry = ImageEntryV2.model_validate(entry_dict)

    # Validate entire manifest
    manifest = ManifestV2.model_validate(manifest_dict)
"""

import hashlib

from pydantic import BaseModel, field_validator, model_validator


class ImageEntryV2(BaseModel):
    """Validated image manifest entry with full lineage.

    Ensures all required fields are present and property_hash matches
    the computed hash from the property_address.

    Attributes:
        image_id: UUID identifier for the image
        property_address: Full property address for lineage
        property_hash: 8-char SHA256 hash of normalized address
        source: Image source (zillow, redfin, etc.)
        source_url: Original download URL
        local_path: Relative path to processed image
        phash: Perceptual hash for deduplication
        dhash: Difference hash for deduplication
        width: Image width in pixels
        height: Image height in pixels
        file_size_bytes: File size in bytes
        status: Processing status (processed, failed, etc.)
        downloaded_at: ISO timestamp when downloaded
        processed_at: ISO timestamp when processed (optional)
        created_by_run_id: Run ID that created this image
        content_hash: MD5 hash of image bytes
    """
    image_id: str
    property_address: str
    property_hash: str
    source: str
    source_url: str
    local_path: str
    phash: str
    dhash: str
    width: int
    height: int
    file_size_bytes: int
    status: str
    downloaded_at: str
    processed_at: str | None = None
    created_by_run_id: str = ""
    content_hash: str = ""

    @field_validator('property_hash')
    @classmethod
    def validate_property_hash_length(cls, v: str) -> str:
        """Ensure property_hash is exactly 8 characters.

        Args:
            v: Property hash value

        Returns:
            Validated property hash

        Raises:
            ValueError: If hash is not 8 characters
        """
        if v and len(v) != 8:
            raise ValueError(f"property_hash must be 8 chars, got {len(v)}")
        return v

    @model_validator(mode='after')
    def validate_hash_matches_address(self) -> 'ImageEntryV2':
        """Verify property_hash matches computed hash from address.

        Ensures data integrity by validating that the stored hash
        matches the expected hash computed from the property address.

        Returns:
            Self after validation

        Raises:
            ValueError: If property_hash doesn't match computed hash
        """
        if self.property_hash and self.property_address:
            expected = hashlib.sha256(
                self.property_address.lower().strip().encode()
            ).hexdigest()[:8]
            if self.property_hash != expected:
                raise ValueError(
                    f"property_hash {self.property_hash} != computed {expected}"
                )
        return self


class URLEntryV2(BaseModel):
    """Validated URL tracker entry with full lineage.

    Tracks URL lifecycle with audit trail for data integrity.

    Attributes:
        image_id: UUID of associated image
        property_hash: 8-char property hash
        original_address: Full address at extraction time
        first_seen: ISO timestamp when first discovered
        last_seen: ISO timestamp when last checked
        content_hash: Hash of image content
        source: Image source identifier
        status: URL status (active, removed, stale)
        first_run_id: Run ID that first discovered this URL
        last_run_id: Run ID that last updated this entry
    """
    image_id: str
    property_hash: str
    original_address: str = ""
    first_seen: str
    last_seen: str
    content_hash: str = ""
    source: str = ""
    status: str = "active"
    first_run_id: str = ""
    last_run_id: str = ""


class ManifestV2(BaseModel):
    """Validated manifest structure.

    Ensures overall manifest structure is correct and contains
    valid image entries for each property.

    Attributes:
        version: Manifest schema version
        last_updated: ISO timestamp of last update
        properties: Dict mapping property address to list of images
    """
    version: str = "2.0.0"
    last_updated: str
    properties: dict[str, list[ImageEntryV2]]

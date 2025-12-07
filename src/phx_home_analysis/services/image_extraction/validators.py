"""Pre-extraction and during-extraction validators for data integrity."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phx_home_analysis.domain.entities import Property

logger = logging.getLogger(__name__)


class DataIntegrityError(Exception):
    """Base exception for data integrity violations."""

    def __init__(self, message: str, rule_id: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.rule_id = rule_id
        self.context: dict[str, Any] = context or {}


class AddressMismatchError(DataIntegrityError):
    """Address doesn't match expected value."""
    pass


class HashMismatchError(DataIntegrityError):
    """Computed hash doesn't match stored hash."""
    pass


class MissingFileError(DataIntegrityError):
    """Expected file doesn't exist on disk."""
    pass


@dataclass
class ValidationResult:
    """Result of property validation."""
    is_valid: bool
    property_address: str
    property_hash: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def compute_property_hash(address: str) -> str:
    """Compute canonical 8-char hash for property address."""
    normalized = address.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:8]


class PreExtractionValidator:
    """Validates properties before extraction begins."""

    def __init__(self, processed_dir: Path):
        self.processed_dir = processed_dir

    def validate_property(self, property: Property) -> ValidationResult:
        """
        Validate a single property before extraction.

        Checks:
        - Address is non-empty
        - Hash computes consistently
        - No conflicting data
        """
        errors: list[str] = []
        warnings: list[str] = []

        address = property.full_address

        # Check address is non-empty
        if not address or not address.strip():
            errors.append("PRE-001: Address is empty or whitespace only")
            return ValidationResult(
                is_valid=False,
                property_address=address,
                property_hash="",
                errors=errors,
            )

        # Compute hash
        property_hash = compute_property_hash(address)

        # Verify hash is deterministic (compute twice)
        hash_check = compute_property_hash(address)
        if property_hash != hash_check:
            errors.append(f"PRE-003: Hash not deterministic: {property_hash} != {hash_check}")

        # Verify hash format
        if len(property_hash) != 8:
            errors.append(f"PRE-002: Hash wrong length: {len(property_hash)} != 8")

        return ValidationResult(
            is_valid=len(errors) == 0,
            property_address=address,
            property_hash=property_hash,
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(self, properties: list[Property]) -> dict[str, ValidationResult]:
        """
        Validate a batch of properties.

        Also checks for duplicate addresses.
        """
        results: dict[str, ValidationResult] = {}
        seen_addresses: dict[str, int] = {}

        for prop in properties:
            result = self.validate_property(prop)

            # Check for duplicates
            normalized = prop.full_address.lower().strip()
            if normalized in seen_addresses:
                result.warnings.append(
                    f"PRE-004: Duplicate address (same as index {seen_addresses[normalized]})"
                )
            else:
                seen_addresses[normalized] = len(results)

            results[prop.full_address] = result

        return results


class DuringExtractionAssertions:
    """Runtime assertions during image extraction."""

    @staticmethod
    def assert_property_binding(
        image_content_hash: str,
        expected_address: str,
        actual_address: str,
        local_path: str,
    ) -> None:
        """
        Assert image is bound to correct property.

        Raises:
            AddressMismatchError: If addresses don't match
            HashMismatchError: If path doesn't contain content hash
        """
        # Check address matches
        if actual_address != expected_address:
            raise AddressMismatchError(
                f"Address mismatch: expected '{expected_address}', got '{actual_address}'",
                rule_id="DUR-001",
                context={
                    "expected": expected_address,
                    "actual": actual_address,
                    "content_hash": image_content_hash,
                }
            )

        # Check path contains content hash
        if image_content_hash[:8] not in local_path:
            raise HashMismatchError(
                f"Path '{local_path}' doesn't contain content hash prefix '{image_content_hash[:8]}'",
                rule_id="DUR-002",
                context={
                    "local_path": local_path,
                    "content_hash": image_content_hash,
                }
            )

    @staticmethod
    def assert_file_exists(local_path: Path, min_size: int = 100) -> None:
        """
        Assert saved file exists and has minimum size.

        Raises:
            MissingFileError: If file doesn't exist or is too small
        """
        if not local_path.exists():
            raise MissingFileError(
                f"File doesn't exist: {local_path}",
                rule_id="DUR-004",
                context={"path": str(local_path)}
            )

        size = local_path.stat().st_size
        if size < min_size:
            raise MissingFileError(
                f"File too small ({size} bytes < {min_size}): {local_path}",
                rule_id="DUR-004",
                context={"path": str(local_path), "size": size, "min_size": min_size}
            )

    @staticmethod
    def assert_content_hash_matches(
        image_data: bytes,
        expected_hash: str,
    ) -> None:
        """
        Assert computed content hash matches expected.

        Raises:
            HashMismatchError: If hashes don't match
        """
        import hashlib
        actual_hash = hashlib.md5(image_data).hexdigest()

        if actual_hash != expected_hash:
            raise HashMismatchError(
                f"Content hash mismatch: expected {expected_hash}, got {actual_hash}",
                rule_id="DUR-005",
                context={
                    "expected": expected_hash,
                    "actual": actual_hash,
                }
            )

    @staticmethod
    def assert_image_quality(
        image_data: bytes,
        min_dimension: int = 200,
        min_size: int = 5000,
    ) -> None:
        """
        Assert image meets minimum quality requirements.

        Checks both file size and image dimensions to ensure images
        are usable for visual assessment.

        Args:
            image_data: Raw image bytes
            min_dimension: Minimum width/height in pixels (default: 200px)
            min_size: Minimum file size in bytes (default: 5000 bytes)

        Raises:
            DataIntegrityError: If image doesn't meet quality requirements
                - DUR-010: File size too small
                - DUR-011: Image width too small
                - DUR-012: Image height too small
        """
        # Check file size
        file_size = len(image_data)
        if file_size < min_size:
            raise DataIntegrityError(
                f"Image file size too small ({file_size} bytes < {min_size} bytes)",
                rule_id="DUR-010",
                context={
                    "file_size": file_size,
                    "min_size": min_size,
                }
            )

        # Check image dimensions
        try:
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            if width < min_dimension:
                raise DataIntegrityError(
                    f"Image width too small ({width}px < {min_dimension}px)",
                    rule_id="DUR-011",
                    context={
                        "width": width,
                        "height": height,
                        "min_dimension": min_dimension,
                    }
                )

            if height < min_dimension:
                raise DataIntegrityError(
                    f"Image height too small ({height}px < {min_dimension}px)",
                    rule_id="DUR-012",
                    context={
                        "width": width,
                        "height": height,
                        "min_dimension": min_dimension,
                    }
                )

        except Exception as e:
            if isinstance(e, DataIntegrityError):
                raise
            # If we can't open the image, it's corrupt/invalid
            raise DataIntegrityError(
                f"Unable to validate image dimensions: {e}",
                rule_id="DUR-010",
                context={"error": str(e)}
            ) from e


# Required fields for kill-switch evaluation
REQUIRED_FIELDS = [
    "beds",
    "baths",
    "lot_sqft",
    "garage_spaces",
    "hoa_fee",
    "sewer_type",
    "year_built",
]


@dataclass
class MetadataCompletenessReport:
    """Report of metadata completeness for property data."""

    property_address: str
    total_fields: int
    present_fields: int
    missing_fields: list[str] = field(default_factory=list)

    @property
    def completeness_percentage(self) -> float:
        """Calculate completeness as percentage (0-100)."""
        if self.total_fields == 0:
            return 100.0
        return (self.present_fields / self.total_fields) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if all required fields are present."""
        return len(self.missing_fields) == 0


class MetadataCompletenessValidator:
    """Validates metadata completeness for kill-switch evaluation."""

    def __init__(self, required_fields: list[str] | None = None):
        """
        Initialize validator with required fields.

        Args:
            required_fields: List of required field names.
                If None, uses REQUIRED_FIELDS constant.
        """
        self.required_fields = required_fields or REQUIRED_FIELDS

    def validate(self, property_data: dict[str, Any]) -> MetadataCompletenessReport:
        """
        Validate metadata completeness for a property.

        Checks that all required fields are present and non-None.

        Args:
            property_data: Property data dictionary from enrichment_data.json

        Returns:
            MetadataCompletenessReport with completeness analysis
        """
        property_address = property_data.get("full_address", "Unknown")
        missing_fields: list[str] = []

        for field_name in self.required_fields:
            value = property_data.get(field_name)
            # Field is missing if not in dict or value is None
            if value is None:
                missing_fields.append(field_name)

        return MetadataCompletenessReport(
            property_address=property_address,
            total_fields=len(self.required_fields),
            present_fields=len(self.required_fields) - len(missing_fields),
            missing_fields=missing_fields,
        )

    def validate_batch(
        self, properties: list[dict[str, Any]]
    ) -> dict[str, MetadataCompletenessReport]:
        """
        Validate metadata completeness for multiple properties.

        Args:
            properties: List of property data dictionaries

        Returns:
            Dict mapping property address to completeness report
        """
        results: dict[str, MetadataCompletenessReport] = {}

        for property_data in properties:
            report = self.validate(property_data)
            results[report.property_address] = report

        return results

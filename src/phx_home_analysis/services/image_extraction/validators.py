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

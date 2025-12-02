"""Validation logic for property data.

This module provides validation classes and result containers for
validating property data against Pydantic schemas.
"""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from .normalizer import (
    clean_price,
    normalize_boolean,
    normalize_orientation,
    normalize_sewer_type,
    normalize_solar_status,
)
from .schemas import (
    EnrichmentDataSchema,
    KillSwitchCriteriaSchema,
    PropertySchema,
)


@dataclass
class ValidationResult:
    """Container for validation operation results.

    Attributes:
        is_valid: Whether validation passed
        errors: List of validation error details from Pydantic
        warnings: List of non-fatal validation warnings
        normalized_data: Data after normalization (if validation passed)
    """

    is_valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_data: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        """Allow using ValidationResult directly in boolean context."""
        return self.is_valid

    def error_messages(self) -> list[str]:
        """Get human-readable error messages.

        Returns:
            List of formatted error message strings
        """
        messages = []
        for error in self.errors:
            loc = ".".join(str(loc_part) for loc_part in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            messages.append(f"{loc}: {msg}" if loc else msg)
        return messages

    def first_error(self) -> str | None:
        """Get the first error message, if any.

        Returns:
            First error message string, or None if no errors
        """
        messages = self.error_messages()
        return messages[0] if messages else None


class PropertyValidator:
    """Validator for property data using Pydantic schemas.

    Provides methods for validating property data, enrichment data,
    and kill-switch criteria with optional data normalization.
    """

    def __init__(self, normalize: bool = True):
        """Initialize the validator.

        Args:
            normalize: Whether to apply data normalization before validation
        """
        self.normalize = normalize

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate property data against PropertySchema.

        Args:
            data: Property data dictionary

        Returns:
            ValidationResult with validation status and any errors
        """
        return self._validate_with_schema(data, PropertySchema)

    def validate_enrichment(self, data: dict[str, Any]) -> ValidationResult:
        """Validate enrichment data against EnrichmentDataSchema.

        Args:
            data: Enrichment data dictionary

        Returns:
            ValidationResult with validation status and any errors
        """
        return self._validate_with_schema(data, EnrichmentDataSchema)

    def validate_kill_switch(self, data: dict[str, Any]) -> ValidationResult:
        """Validate property against kill-switch criteria.

        This validates that a property passes all mandatory kill-switch
        criteria: NO HOA, city sewer, 2-car garage, 4+ beds, 2+ baths,
        7k-15k sqft lot, pre-2024 build.

        Args:
            data: Property data dictionary

        Returns:
            ValidationResult with kill-switch validation status
        """
        return self._validate_with_schema(data, KillSwitchCriteriaSchema)

    def _validate_with_schema(
        self, data: dict[str, Any], schema: type[BaseModel]
    ) -> ValidationResult:
        """Validate data against a Pydantic schema.

        Args:
            data: Data dictionary to validate
            schema: Pydantic model class to validate against

        Returns:
            ValidationResult with validation status and any errors
        """
        warnings: list[str] = []
        normalized_data = data.copy()

        # Apply normalization if enabled
        if self.normalize:
            normalized_data, norm_warnings = self._normalize_data(data, schema)
            warnings.extend(norm_warnings)

        try:
            validated = schema(**normalized_data)
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=warnings,
                normalized_data=validated.model_dump(),
            )
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=e.errors(),  # type: ignore[arg-type]
                warnings=warnings,
                normalized_data=None,
            )

    def _normalize_data(
        self, data: dict[str, Any], schema: type[BaseModel]
    ) -> tuple[dict[str, Any], list[str]]:
        """Normalize data before validation.

        Args:
            data: Raw data dictionary
            schema: Target schema for context-aware normalization

        Returns:
            Tuple of (normalized_data, warnings)
        """
        normalized = data.copy()
        warnings: list[str] = []

        # Normalize address if present
        if "address" in normalized and isinstance(normalized["address"], str):
            original = normalized["address"]
            # Don't fully normalize addresses for PropertySchema - just strip
            normalized["address"] = original.strip()

        if "full_address" in normalized and isinstance(normalized["full_address"], str):
            normalized["full_address"] = normalized["full_address"].strip()

        # Normalize sewer_type
        if "sewer_type" in normalized and isinstance(normalized["sewer_type"], str):
            normalized["sewer_type"] = normalize_sewer_type(normalized["sewer_type"])

        # Normalize orientation
        if "orientation" in normalized and isinstance(normalized["orientation"], str):
            normalized["orientation"] = normalize_orientation(normalized["orientation"])

        # Normalize solar_status
        if "solar_status" in normalized and isinstance(normalized["solar_status"], str):
            normalized["solar_status"] = normalize_solar_status(normalized["solar_status"])

        # Normalize price
        if "price" in normalized:
            original_price = normalized["price"]
            normalized["price"] = clean_price(original_price)
            if normalized["price"] is None and original_price is not None:
                warnings.append(f"Could not parse price: {original_price}")

        # Normalize boolean fields
        bool_fields = ["has_pool", "fireplace_present"]
        for bool_field in bool_fields:
            if bool_field in normalized:
                normalized[bool_field] = normalize_boolean(normalized[bool_field])

        # Normalize HOA fee
        if "hoa_fee" in normalized:
            hoa = normalized["hoa_fee"]
            if isinstance(hoa, str):
                hoa = clean_price(hoa)
            if hoa is not None and hoa == 0:
                # Convert 0 to None for "no HOA" representation
                normalized["hoa_fee"] = 0.0  # Keep as 0 for explicit "no HOA"
            normalized["hoa_fee"] = hoa

        return normalized, warnings


class BatchValidator:
    """Validator for batch property data validation.

    Validates multiple property records and provides aggregate statistics.
    """

    def __init__(self, validator: PropertyValidator | None = None):
        """Initialize the batch validator.

        Args:
            validator: PropertyValidator instance, or None to create default
        """
        self.validator = validator or PropertyValidator()

    def validate_batch(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[ValidationResult], dict[str, Any]]:
        """Validate a batch of property records.

        Args:
            records: List of property data dictionaries

        Returns:
            Tuple of (list of ValidationResults, summary statistics dict)
        """
        results = []
        valid_count = 0
        invalid_count = 0
        error_types: dict[str, int] = {}

        for record in records:
            result = self.validator.validate(record)
            results.append(result)

            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                # Track error types
                for error in result.errors:
                    error_type = error.get("type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1

        summary = {
            "total": len(records),
            "valid": valid_count,
            "invalid": invalid_count,
            "valid_percent": (valid_count / len(records) * 100) if records else 0,
            "error_types": error_types,
        }

        return results, summary

    def filter_valid(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter batch to return only valid records.

        Args:
            records: List of property data dictionaries

        Returns:
            List of validated and normalized data dictionaries
        """
        valid_records = []
        for record in records:
            result = self.validator.validate(record)
            if result.is_valid and result.normalized_data:
                valid_records.append(result.normalized_data)
        return valid_records


def validate_property(data: dict[str, Any], normalize: bool = True) -> ValidationResult:
    """Convenience function to validate a single property.

    Args:
        data: Property data dictionary
        normalize: Whether to apply normalization

    Returns:
        ValidationResult with validation status
    """
    validator = PropertyValidator(normalize=normalize)
    return validator.validate(data)


def validate_enrichment(data: dict[str, Any], normalize: bool = True) -> ValidationResult:
    """Convenience function to validate enrichment data.

    Args:
        data: Enrichment data dictionary
        normalize: Whether to apply normalization

    Returns:
        ValidationResult with validation status
    """
    validator = PropertyValidator(normalize=normalize)
    return validator.validate_enrichment(data)


def validate_enrichment_entry(data: dict[str, Any], normalize: bool = True) -> dict[str, Any]:
    """Validate a single enrichment entry and return normalized data.

    This function is designed for use by repositories that need to validate
    enrichment data on load/save operations. Unlike validate_enrichment(),
    this function raises on validation failure and returns the normalized dict.

    Args:
        data: Raw dictionary from JSON
        normalize: Whether to apply normalization before validation

    Returns:
        Validated and normalized dictionary

    Raises:
        ValueError: If data is invalid (wraps Pydantic ValidationError)
    """
    result = validate_enrichment(data, normalize=normalize)
    if not result.is_valid:
        error_msgs = result.error_messages()
        address = data.get("full_address", "unknown")
        raise ValueError(f"Validation failed for '{address}': {'; '.join(error_msgs)}")
    return result.normalized_data or data


def validate_enrichment_list(
    data_list: list[dict[str, Any]], normalize: bool = True
) -> list[dict[str, Any]]:
    """Validate a list of enrichment entries.

    Args:
        data_list: List of raw dictionaries from JSON
        normalize: Whether to apply normalization before validation

    Returns:
        List of validated and normalized dictionaries

    Raises:
        ValueError: If any entry is invalid (includes index and address in error)
    """
    validated = []
    errors = []

    for i, entry in enumerate(data_list):
        try:
            validated.append(validate_enrichment_entry(entry, normalize=normalize))
        except ValueError as e:
            address = entry.get("full_address", "unknown")
            errors.append(f"Entry {i} ({address}): {e}")

    if errors:
        raise ValueError(f"Validation failed for {len(errors)} entries:\n" + "\n".join(errors))

    return validated

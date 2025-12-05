"""Tests for data integrity validators."""
from pathlib import Path

import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.services.image_extraction.validators import (
    AddressMismatchError,
    DuringExtractionAssertions,
    HashMismatchError,
    MissingFileError,
    PreExtractionValidator,
    compute_property_hash,
)


def test_compute_property_hash():
    """Test hash computation is consistent and canonical."""
    address = "1234 Main St, Phoenix, AZ 85001"

    # Hash should be deterministic
    hash1 = compute_property_hash(address)
    hash2 = compute_property_hash(address)
    assert hash1 == hash2

    # Hash should be 8 characters
    assert len(hash1) == 8

    # Case insensitive
    hash_upper = compute_property_hash(address.upper())
    hash_lower = compute_property_hash(address.lower())
    assert hash_upper == hash_lower

    # Whitespace normalized
    hash_spaces = compute_property_hash("  " + address + "  ")
    assert hash_spaces == hash1


def test_pre_extraction_validator_valid_property():
    """Test validator accepts valid properties."""
    validator = PreExtractionValidator(Path("/tmp/processed"))

    property = Property(
        street="1234 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="1234 Main St, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2200,
        price_per_sqft_raw=215.91,
    )

    result = validator.validate_property(property)

    assert result.is_valid
    assert len(result.errors) == 0
    assert result.property_address == property.full_address
    assert len(result.property_hash) == 8


def test_pre_extraction_validator_empty_address():
    """Test validator rejects empty addresses."""
    validator = PreExtractionValidator(Path("/tmp/processed"))

    # Create property with all empty address fields
    # Note: Property.__post_init__ will auto-generate full_address if empty,
    # so we need to set it to empty string after initialization
    property = Property(
        street="",
        city="",
        state="",
        zip_code="",
        full_address="",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2200,
        price_per_sqft_raw=215.91,
    )
    # Override the auto-generated full_address
    property.full_address = ""

    result = validator.validate_property(property)

    assert not result.is_valid
    assert len(result.errors) == 1
    assert "PRE-001" in result.errors[0]


def test_pre_extraction_validator_batch_duplicates():
    """Test batch validator detects duplicate addresses."""
    validator = PreExtractionValidator(Path("/tmp/processed"))

    property1 = Property(
        street="1234 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="1234 Main St, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2200,
        price_per_sqft_raw=215.91,
    )

    property2 = Property(
        street="1234 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="1234 Main St, Phoenix, AZ 85001",  # Duplicate
        price="$480,000",
        price_num=480000,
        beds=4,
        baths=2.5,
        sqft=2200,
        price_per_sqft_raw=218.18,
    )

    results = validator.validate_batch([property1, property2])

    # Since both properties have the same address, dict will only have one entry
    # (the second one overwrites the first)
    assert len(results) == 1
    assert results[property1.full_address].is_valid

    # The single result should have warning about duplicate
    assert len(results[property1.full_address].warnings) > 0
    assert "PRE-004" in results[property1.full_address].warnings[0]


def test_during_extraction_assertions_address_mismatch():
    """Test assertion catches address mismatches."""
    with pytest.raises(AddressMismatchError) as exc_info:
        DuringExtractionAssertions.assert_property_binding(
            image_content_hash="abc123def456",
            expected_address="1234 Main St, Phoenix, AZ 85001",
            actual_address="5678 Oak Ave, Phoenix, AZ 85002",
            local_path="processed/abc123de/image.png",
        )

    assert exc_info.value.rule_id == "DUR-001"
    assert "expected" in exc_info.value.context
    assert "actual" in exc_info.value.context


def test_during_extraction_assertions_hash_not_in_path():
    """Test assertion catches hash not in path."""
    with pytest.raises(HashMismatchError) as exc_info:
        DuringExtractionAssertions.assert_property_binding(
            image_content_hash="abc123def456",
            expected_address="1234 Main St, Phoenix, AZ 85001",
            actual_address="1234 Main St, Phoenix, AZ 85001",
            local_path="processed/wrong_hash/image.png",
        )

    assert exc_info.value.rule_id == "DUR-002"


def test_during_extraction_assertions_file_missing(tmp_path):
    """Test assertion catches missing files."""
    missing_file = tmp_path / "nonexistent.png"

    with pytest.raises(MissingFileError) as exc_info:
        DuringExtractionAssertions.assert_file_exists(missing_file)

    assert exc_info.value.rule_id == "DUR-004"


def test_during_extraction_assertions_file_too_small(tmp_path):
    """Test assertion catches files that are too small."""
    tiny_file = tmp_path / "tiny.png"
    tiny_file.write_bytes(b"x" * 10)  # Only 10 bytes

    with pytest.raises(MissingFileError) as exc_info:
        DuringExtractionAssertions.assert_file_exists(tiny_file, min_size=100)

    assert exc_info.value.rule_id == "DUR-004"
    assert "too small" in str(exc_info.value).lower()


def test_during_extraction_assertions_content_hash_mismatch():
    """Test assertion catches content hash mismatches."""
    image_data = b"fake image content"

    with pytest.raises(HashMismatchError) as exc_info:
        DuringExtractionAssertions.assert_content_hash_matches(
            image_data=image_data,
            expected_hash="wrong_hash_value",
        )

    assert exc_info.value.rule_id == "DUR-005"

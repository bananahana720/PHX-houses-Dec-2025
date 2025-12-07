"""Tests for data integrity validators."""
from pathlib import Path

import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.services.image_extraction.validators import (
    REQUIRED_FIELDS,
    AddressMismatchError,
    DataIntegrityError,
    DuringExtractionAssertions,
    HashMismatchError,
    MetadataCompletenessReport,
    MetadataCompletenessValidator,
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


# GAP 4: Image Quality Validation Tests


def test_assert_image_quality_file_too_small():
    """Test image quality validation catches files that are too small."""
    tiny_data = b"x" * 100  # Only 100 bytes

    with pytest.raises(DataIntegrityError) as exc_info:
        DuringExtractionAssertions.assert_image_quality(
            image_data=tiny_data,
            min_size=5000,
        )

    assert exc_info.value.rule_id == "DUR-010"
    assert "file size too small" in str(exc_info.value).lower()
    assert exc_info.value.context["file_size"] == 100
    assert exc_info.value.context["min_size"] == 5000


def test_assert_image_quality_dimension_too_small(tmp_path):
    """Test image quality validation catches images with dimensions too small."""
    import io

    from PIL import Image

    # Create a tiny 50x50 pixel image
    img = Image.new("RGB", (50, 50), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    image_data = img_bytes.getvalue()

    # Should fail dimension check (min_dimension=200), use low min_size to pass file check
    with pytest.raises(DataIntegrityError) as exc_info:
        DuringExtractionAssertions.assert_image_quality(
            image_data=image_data,
            min_dimension=200,
            min_size=100,  # Low enough to pass file size check
        )

    assert exc_info.value.rule_id in ["DUR-011", "DUR-012"]  # Width or height
    assert "too small" in str(exc_info.value).lower()
    assert exc_info.value.context["width"] == 50
    assert exc_info.value.context["height"] == 50


def test_assert_image_quality_valid_image():
    """Test image quality validation passes for valid images."""
    import io

    from PIL import Image

    # Create a 500x500 pixel image (meets min 200px and file size requirements)
    img = Image.new("RGB", (500, 500), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    image_data = img_bytes.getvalue()

    # Should pass both file size and dimension checks (use lower min_size for testing)
    try:
        DuringExtractionAssertions.assert_image_quality(
            image_data=image_data,
            min_dimension=200,
            min_size=1000,  # Lower threshold for testing
        )
    except DataIntegrityError:
        pytest.fail("Valid image should not raise DataIntegrityError")


def test_assert_image_quality_corrupt_image():
    """Test image quality validation catches corrupt image data."""
    corrupt_data = b"This is not a valid image file content"

    with pytest.raises(DataIntegrityError) as exc_info:
        DuringExtractionAssertions.assert_image_quality(
            image_data=corrupt_data,
            min_size=10,  # Low enough to pass file size check
        )

    assert exc_info.value.rule_id == "DUR-010"
    assert "unable to validate" in str(exc_info.value).lower()


# GAP 5: Metadata Completeness Validation Tests


def test_metadata_completeness_all_fields_present():
    """Test completeness validation with all required fields present."""
    property_data = {
        "full_address": "123 Main St, Phoenix, AZ 85001",
        "beds": 4,
        "baths": 2.5,
        "lot_sqft": 9000,
        "garage_spaces": 2,
        "hoa_fee": 0,
        "sewer_type": "city",
        "year_built": 2010,
    }

    validator = MetadataCompletenessValidator()
    report = validator.validate(property_data)

    assert report.is_complete
    assert report.completeness_percentage == 100.0
    assert len(report.missing_fields) == 0
    assert report.present_fields == len(REQUIRED_FIELDS)
    assert report.property_address == "123 Main St, Phoenix, AZ 85001"


def test_metadata_completeness_missing_fields():
    """Test completeness validation with missing required fields."""
    property_data = {
        "full_address": "456 Oak Ave, Phoenix, AZ 85002",
        "beds": 3,
        "baths": 2.0,
        # Missing: lot_sqft, garage_spaces, hoa_fee, sewer_type, year_built
    }

    validator = MetadataCompletenessValidator()
    report = validator.validate(property_data)

    assert not report.is_complete
    assert report.completeness_percentage < 100.0
    assert len(report.missing_fields) == 5
    assert "lot_sqft" in report.missing_fields
    assert "garage_spaces" in report.missing_fields
    assert "hoa_fee" in report.missing_fields
    assert "sewer_type" in report.missing_fields
    assert "year_built" in report.missing_fields
    assert report.present_fields == 2  # Only beds and baths


def test_metadata_completeness_none_values():
    """Test completeness validation treats None as missing."""
    property_data = {
        "full_address": "789 Pine Dr, Phoenix, AZ 85003",
        "beds": 4,
        "baths": 2.5,
        "lot_sqft": None,  # Explicitly None
        "garage_spaces": 2,
        "hoa_fee": None,  # Explicitly None
        "sewer_type": "city",
        "year_built": 2015,
    }

    validator = MetadataCompletenessValidator()
    report = validator.validate(property_data)

    assert not report.is_complete
    assert len(report.missing_fields) == 2
    assert "lot_sqft" in report.missing_fields
    assert "hoa_fee" in report.missing_fields
    assert report.present_fields == 5


def test_metadata_completeness_batch_validation():
    """Test batch validation of multiple properties."""
    properties = [
        {
            "full_address": "Property 1",
            "beds": 4,
            "baths": 2,
            "lot_sqft": 8000,
            "garage_spaces": 2,
            "hoa_fee": 0,
            "sewer_type": "city",
            "year_built": 2010,
        },
        {
            "full_address": "Property 2",
            "beds": 3,
            "baths": 2,
            # Missing other fields
        },
    ]

    validator = MetadataCompletenessValidator()
    results = validator.validate_batch(properties)

    assert len(results) == 2
    assert results["Property 1"].is_complete
    assert not results["Property 2"].is_complete
    assert results["Property 1"].completeness_percentage == 100.0
    assert results["Property 2"].completeness_percentage < 50.0


def test_metadata_completeness_custom_required_fields():
    """Test validator with custom required fields list."""
    custom_fields = ["beds", "baths", "price"]
    property_data = {
        "full_address": "Custom Property",
        "beds": 4,
        "baths": 2,
        "price": 500000,
        # Other fields not required
    }

    validator = MetadataCompletenessValidator(required_fields=custom_fields)
    report = validator.validate(property_data)

    assert report.is_complete
    assert report.total_fields == 3
    assert report.present_fields == 3


def test_metadata_completeness_report_dataclass():
    """Test MetadataCompletenessReport dataclass properties."""
    report = MetadataCompletenessReport(
        property_address="Test Property",
        total_fields=7,
        present_fields=5,
        missing_fields=["lot_sqft", "hoa_fee"],
    )

    assert report.completeness_percentage == pytest.approx(71.43, rel=0.01)
    assert not report.is_complete
    assert len(report.missing_fields) == 2

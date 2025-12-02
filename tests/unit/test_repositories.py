"""Unit tests for repository classes.

Tests CSV and JSON repositories for property and enrichment data,
including edge cases, error handling, and caching behavior.
"""

import json
from pathlib import Path

import pytest

from src.phx_home_analysis.domain.entities import EnrichmentData, Property
from src.phx_home_analysis.domain.enums import SewerType
from src.phx_home_analysis.repositories.base import DataLoadError, DataSaveError
from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository

# ============================================================================
# FIXTURES: Temporary Files
# ============================================================================


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file with valid property data.

    Returns:
        Path: Path to temporary CSV file
    """
    csv_file = tmp_path / "test_properties.csv"
    csv_content = """street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address,lot_sqft,year_built,garage_spaces,sewer_type,tax_annual,hoa_fee,school_rating,latitude,longitude
123 Main St,Phoenix,AZ,85001,$475000,475000,4,2.0,2200,215.9,"123 Main St, Phoenix, AZ 85001",9500,2010,2,city,4200,0,7.5,33.4484,-112.0742
456 Oak Ave,Scottsdale,AZ,85251,$550000,550000,4,2.5,2500,220.0,"456 Oak Ave, Scottsdale, AZ 85251",10500,2012,2,city,5100,150,8.0,33.5131,-111.9254"""
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def temp_csv_empty(tmp_path):
    """Create an empty CSV file with headers only.

    Returns:
        Path: Path to empty CSV file
    """
    csv_file = tmp_path / "empty_properties.csv"
    csv_content = "street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address\n"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def temp_csv_missing_columns(tmp_path):
    """Create CSV with missing required columns.

    Returns:
        Path: Path to CSV with missing columns
    """
    csv_file = tmp_path / "missing_columns.csv"
    # Missing 'street' column
    csv_content = """city,state,zip,price,price_num,beds,baths,sqft,full_address
Phoenix,AZ,85001,$475000,475000,4,2.0,2200,123 Main St, Phoenix, AZ 85001"""
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def temp_csv_malformed(tmp_path):
    """Create CSV with malformed numeric data.

    Returns:
        Path: Path to CSV with malformed rows
    """
    csv_file = tmp_path / "malformed.csv"
    csv_content = """street,city,state,zip,price,price_num,beds,baths,sqft,full_address
123 Main St,Phoenix,AZ,85001,$475000,NOT_A_NUMBER,4,two,2200,123 Main St, Phoenix, AZ 85001"""
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON enrichment file.

    Returns:
        Path: Path to temporary JSON file
    """
    json_file = tmp_path / "enrichment_data.json"
    json_content = [
        {
            "full_address": "123 Main St, Phoenix, AZ 85001",
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "tax_annual": 4200,
            "hoa_fee": 0,
            "commute_minutes": 25,
            "school_district": "Phoenix Union",
            "school_rating": 7.5,
            "orientation": "north",
            "distance_to_grocery_miles": 1.2,
            "distance_to_highway_miles": 3.5,
            "solar_status": "none",
            "solar_lease_monthly": None,
            "has_pool": False,
            "pool_equipment_age": None,
            "roof_age": 8,
            "hvac_age": 6,
        },
        {
            "full_address": "456 Oak Ave, Scottsdale, AZ 85251",
            "lot_sqft": 10500,
            "year_built": 2012,
            "garage_spaces": 2,
            "sewer_type": "city",
            "tax_annual": 5100,
            "hoa_fee": 150,
            "commute_minutes": 30,
            "school_district": "Scottsdale Unified",
            "school_rating": 8.0,
            "orientation": "south",
            "distance_to_grocery_miles": 1.5,
            "distance_to_highway_miles": 4.0,
            "solar_status": "owned",
            "solar_lease_monthly": None,
            "has_pool": True,
            "pool_equipment_age": 3,
            "roof_age": 5,
            "hvac_age": 4,
        },
    ]
    json_file.write_text(json.dumps(json_content))
    return json_file


@pytest.fixture
def temp_json_empty(tmp_path):
    """Create an empty JSON object file.

    Returns:
        Path: Path to empty JSON object
    """
    json_file = tmp_path / "enrichment_empty.json"
    json_file.write_text("{}")
    return json_file


@pytest.fixture
def temp_json_invalid(tmp_path):
    """Create an invalid JSON file.

    Returns:
        Path: Path to invalid JSON file
    """
    json_file = tmp_path / "enrichment_invalid.json"
    json_file.write_text("{invalid json content")
    return json_file


# ============================================================================
# CsvPropertyRepository Tests
# ============================================================================


class TestCsvPropertyRepositoryLoad:
    """Tests for loading CSV property data."""

    def test_load_valid_csv(self, temp_csv_file):
        """Test loading a well-formed CSV file."""
        repo = CsvPropertyRepository(temp_csv_file)
        properties = repo.load_all()

        assert len(properties) == 2
        assert isinstance(properties[0], Property)
        assert properties[0].street == "123 Main St"
        assert properties[0].city == "Phoenix"
        assert properties[0].beds == 4
        assert properties[0].baths == 2.0
        assert properties[0].price_num == 475000

    def test_load_empty_csv(self, temp_csv_empty):
        """Test handling of empty CSV (headers only)."""
        repo = CsvPropertyRepository(temp_csv_empty)
        properties = repo.load_all()

        assert isinstance(properties, list)
        assert len(properties) == 0

    def test_load_missing_file(self, tmp_path):
        """Test error handling when CSV file doesn't exist."""
        non_existent = tmp_path / "does_not_exist.csv"
        repo = CsvPropertyRepository(non_existent)

        with pytest.raises(DataLoadError, match="CSV file not found"):
            repo.load_all()

    def test_load_missing_required_columns(self, temp_csv_missing_columns):
        """Test error handling when required columns are missing."""
        repo = CsvPropertyRepository(temp_csv_missing_columns)

        with pytest.raises(DataLoadError, match="Failed to parse CSV data"):
            repo.load_all()

    def test_load_malformed_row(self, temp_csv_malformed):
        """Test handling of malformed numeric data in CSV."""
        repo = CsvPropertyRepository(temp_csv_malformed)
        properties = repo.load_all()

        # Repository should handle gracefully by parsing what it can
        assert len(properties) == 1
        assert properties[0].street == "123 Main St"
        # price_num should be None due to malformed value
        assert properties[0].price_num is None

    def test_load_by_address_found(self, temp_csv_file):
        """Test loading a single property by address."""
        repo = CsvPropertyRepository(temp_csv_file)
        property_obj = repo.load_by_address("123 Main St, Phoenix, AZ 85001")

        assert property_obj is not None
        assert property_obj.street == "123 Main St"
        assert property_obj.city == "Phoenix"

    def test_load_by_address_not_found(self, temp_csv_file):
        """Test loading property by address that doesn't exist."""
        repo = CsvPropertyRepository(temp_csv_file)
        property_obj = repo.load_by_address("999 Nonexistent St, NoCity, AZ 00000")

        assert property_obj is None

    def test_load_by_address_uses_cache(self, temp_csv_file):
        """Test that load_by_address uses cached data."""
        repo = CsvPropertyRepository(temp_csv_file)
        # First load populates cache
        repo.load_all()
        # Rename original file to verify cache is used
        new_path = temp_csv_file.parent / "renamed.csv"
        temp_csv_file.rename(new_path)

        # Should still work from cache
        property_obj = repo.load_by_address("123 Main St, Phoenix, AZ 85001")
        assert property_obj is not None

    def test_cache_behavior(self, temp_csv_file):
        """Test that properties are cached after loading."""
        repo = CsvPropertyRepository(temp_csv_file)
        assert repo._properties_cache is None

        repo.load_all()
        assert repo._properties_cache is not None
        assert len(repo._properties_cache) == 2


class TestCsvPropertyRepositorySave:
    """Tests for saving CSV property data."""

    def test_save_properties(self, tmp_path, sample_property):
        """Test writing properties to a new CSV file."""
        csv_input = tmp_path / "input.csv"
        csv_output = tmp_path / "output.csv"

        # Create minimal input CSV
        csv_input.write_text(
            "street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address\n"
            "123 Main St,Phoenix,AZ,85001,$475000,475000,4,2.0,2200,215.9,123 Main St, Phoenix, AZ 85001\n"
        )

        repo = CsvPropertyRepository(csv_input, csv_output)
        repo.save_all([sample_property])

        # Verify file was created
        assert csv_output.exists()

        # Verify we can read it back
        repo2 = CsvPropertyRepository(csv_output)
        loaded = repo2.load_all()
        assert len(loaded) == 1
        assert loaded[0].street == sample_property.street

    def test_save_empty_list(self, tmp_path):
        """Test saving empty property list."""
        csv_input = tmp_path / "input.csv"
        csv_output = tmp_path / "output.csv"

        csv_input.write_text("street,city,state,zip,price,price_num,beds,baths,sqft,full_address\n")

        repo = CsvPropertyRepository(csv_input, csv_output)
        repo.save_all([])

        # File should be created with headers only
        assert csv_output.exists()
        content = csv_output.read_text()
        lines = content.strip().split("\n")
        assert len(lines) >= 1  # At least header

    def test_save_creates_parent_directory(self, tmp_path):
        """Test that save_all creates parent directories if needed."""
        csv_input = tmp_path / "input.csv"
        csv_output = tmp_path / "subdir" / "nested" / "output.csv"

        csv_input.write_text("street,city,state,zip,price,price_num,beds,baths,sqft,full_address\n")

        repo = CsvPropertyRepository(csv_input, csv_output)
        repo.save_all([])

        assert csv_output.parent.exists()
        assert csv_output.exists()

    def test_save_without_ranked_path(self, temp_csv_file, sample_property):
        """Test error when trying to save without ranked CSV path."""
        repo = CsvPropertyRepository(temp_csv_file, ranked_csv_path=None)

        with pytest.raises(DataSaveError, match="No ranked CSV path configured"):
            repo.save_all([sample_property])

    def test_save_one_not_implemented(self, temp_csv_file, sample_property):
        """Test that save_one raises NotImplementedError."""
        repo = CsvPropertyRepository(temp_csv_file)

        with pytest.raises(NotImplementedError):
            repo.save_one(sample_property)

    def test_save_and_reload(self, tmp_path, sample_property):
        """Test round-trip: save and reload properties."""
        csv_input = tmp_path / "input.csv"
        csv_output = tmp_path / "output.csv"

        csv_input.write_text(
            "street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address\n"
            "dummy,dummy,AZ,00000,$0,0,0,0.0,0,0.0,dummy, dummy, AZ 00000\n"
        )

        # Save properties with scores
        repo1 = CsvPropertyRepository(csv_input, csv_output)
        repo1.save_all([sample_property])

        # Reload and verify
        repo2 = CsvPropertyRepository(csv_output)
        reloaded = repo2.load_all()

        assert len(reloaded) == 1
        assert reloaded[0].street == sample_property.street
        assert reloaded[0].city == sample_property.city
        assert reloaded[0].beds == sample_property.beds


class TestCsvPropertyRepositoryParsing:
    """Tests for parsing helper methods."""

    def test_parse_int_valid(self):
        """Test parsing valid integer."""
        result = CsvPropertyRepository._parse_int("12345")
        assert result == 12345

    def test_parse_int_none(self):
        """Test parsing None/empty string."""
        assert CsvPropertyRepository._parse_int(None) is None
        assert CsvPropertyRepository._parse_int("") is None
        assert CsvPropertyRepository._parse_int("  ") is None

    def test_parse_int_invalid(self):
        """Test parsing invalid integer."""
        result = CsvPropertyRepository._parse_int("not_a_number")
        assert result is None

    def test_parse_float_valid(self):
        """Test parsing valid float."""
        result = CsvPropertyRepository._parse_float("123.45")
        assert result == 123.45

    def test_parse_float_none(self):
        """Test parsing None/empty string."""
        assert CsvPropertyRepository._parse_float(None) is None
        assert CsvPropertyRepository._parse_float("") is None

    def test_parse_float_invalid(self):
        """Test parsing invalid float."""
        result = CsvPropertyRepository._parse_float("not_a_float")
        assert result is None

    def test_parse_bool_true_values(self):
        """Test parsing true boolean values."""
        assert CsvPropertyRepository._parse_bool("true") is True
        assert CsvPropertyRepository._parse_bool("True") is True
        assert CsvPropertyRepository._parse_bool("TRUE") is True
        assert CsvPropertyRepository._parse_bool("1") is True
        assert CsvPropertyRepository._parse_bool("yes") is True

    def test_parse_bool_false_values(self):
        """Test parsing false boolean values."""
        assert CsvPropertyRepository._parse_bool("false") is False
        assert CsvPropertyRepository._parse_bool("False") is False
        assert CsvPropertyRepository._parse_bool("0") is False
        assert CsvPropertyRepository._parse_bool("no") is False

    def test_parse_bool_none(self):
        """Test parsing None/empty string."""
        assert CsvPropertyRepository._parse_bool(None) is None
        assert CsvPropertyRepository._parse_bool("") is None

    def test_parse_list_valid(self):
        """Test parsing delimited list."""
        result = CsvPropertyRepository._parse_list("item1;item2;item3")
        assert result == ["item1", "item2", "item3"]

    def test_parse_list_with_spaces(self):
        """Test parsing list with extra spaces."""
        result = CsvPropertyRepository._parse_list("item1 ; item2 ; item3")
        assert result == ["item1", "item2", "item3"]

    def test_parse_list_empty(self):
        """Test parsing empty list."""
        assert CsvPropertyRepository._parse_list(None) == []
        assert CsvPropertyRepository._parse_list("") == []
        assert CsvPropertyRepository._parse_list("  ") == []

    def test_parse_enum_valid(self):
        """Test parsing valid enum value."""
        result = CsvPropertyRepository._parse_enum("city", SewerType)
        assert result == SewerType.CITY

    def test_parse_enum_case_insensitive(self):
        """Test that enum parsing is case-insensitive."""
        result = CsvPropertyRepository._parse_enum("CITY", SewerType)
        assert result == SewerType.CITY

    def test_parse_enum_invalid(self):
        """Test parsing invalid enum value."""
        result = CsvPropertyRepository._parse_enum("invalid", SewerType)
        assert result is None

    def test_parse_enum_none(self):
        """Test parsing None/empty string."""
        assert CsvPropertyRepository._parse_enum(None, SewerType) is None
        assert CsvPropertyRepository._parse_enum("", SewerType) is None


# ============================================================================
# JsonEnrichmentRepository Tests
# ============================================================================


class TestJsonEnrichmentRepositoryLoad:
    """Tests for loading JSON enrichment data."""

    def test_load_valid_json(self, temp_json_file):
        """Test loading well-formed JSON enrichment data."""
        repo = JsonEnrichmentRepository(temp_json_file)
        enrichment = repo.load_all()

        assert isinstance(enrichment, dict)
        assert len(enrichment) == 2
        assert "123 Main St, Phoenix, AZ 85001" in enrichment
        assert enrichment["123 Main St, Phoenix, AZ 85001"].lot_sqft == 9500

    def test_load_empty_json(self, temp_json_empty):
        """Test handling of empty JSON object."""
        repo = JsonEnrichmentRepository(temp_json_empty)
        enrichment = repo.load_all()

        assert isinstance(enrichment, dict)
        assert len(enrichment) == 0

    def test_load_invalid_json(self, temp_json_invalid):
        """Test error handling for invalid JSON."""
        repo = JsonEnrichmentRepository(temp_json_invalid)

        with pytest.raises(DataLoadError, match="Invalid JSON format"):
            repo.load_all()

    def test_load_missing_file_creates_template(self, tmp_path):
        """Test that missing file creates template."""
        json_file = tmp_path / "enrichment_data.json"
        repo = JsonEnrichmentRepository(json_file)

        enrichment = repo.load_all()

        # Should return empty dict
        assert isinstance(enrichment, dict)
        assert len(enrichment) == 0

        # Template file should be created
        assert json_file.exists()

    def test_load_for_property_found(self, temp_json_file):
        """Test loading enrichment data for specific property."""
        repo = JsonEnrichmentRepository(temp_json_file)
        enrichment = repo.load_for_property("123 Main St, Phoenix, AZ 85001")

        assert enrichment is not None
        assert enrichment.full_address == "123 Main St, Phoenix, AZ 85001"
        assert enrichment.lot_sqft == 9500

    def test_load_for_property_not_found(self, temp_json_file):
        """Test loading enrichment for non-existent property."""
        repo = JsonEnrichmentRepository(temp_json_file)
        enrichment = repo.load_for_property("999 Nonexistent, NoCity, AZ 00000")

        assert enrichment is None

    def test_load_for_property_uses_cache(self, temp_json_file):
        """Test that load_for_property uses cached data."""
        repo = JsonEnrichmentRepository(temp_json_file)
        # First load populates cache
        repo.load_all()
        # Rename original file to verify cache is used
        new_path = temp_json_file.parent / "renamed.json"
        temp_json_file.rename(new_path)

        # Should still work from cache
        enrichment = repo.load_for_property("123 Main St, Phoenix, AZ 85001")
        assert enrichment is not None


class TestJsonEnrichmentRepositorySave:
    """Tests for saving JSON enrichment data."""

    def test_save_enrichment(self, tmp_path):
        """Test saving enrichment data to JSON."""
        json_file = tmp_path / "enrichment_data.json"
        repo = JsonEnrichmentRepository(json_file)

        enrichment_data = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(
                full_address="123 Main St, Phoenix, AZ 85001",
                lot_sqft=9500,
                year_built=2010,
                garage_spaces=2,
                sewer_type="city",
                tax_annual=4200,
                hoa_fee=0,
                commute_minutes=25,
                school_district="Phoenix Union",
                school_rating=7.5,
            )
        }

        repo.save_all(enrichment_data)
        assert json_file.exists()

        # Reload and verify
        repo2 = JsonEnrichmentRepository(json_file)
        loaded = repo2.load_all()
        assert "123 Main St, Phoenix, AZ 85001" in loaded
        assert loaded["123 Main St, Phoenix, AZ 85001"].lot_sqft == 9500

    def test_save_creates_parent_directory(self, tmp_path):
        """Test that save_all creates parent directories."""
        json_file = tmp_path / "subdir" / "nested" / "enrichment.json"
        repo = JsonEnrichmentRepository(json_file)

        repo.save_all({})

        assert json_file.parent.exists()
        assert json_file.exists()

    def test_save_empty_enrichment(self, tmp_path):
        """Test saving empty enrichment dictionary."""
        json_file = tmp_path / "enrichment_data.json"
        repo = JsonEnrichmentRepository(json_file)

        repo.save_all({})

        assert json_file.exists()
        content = json_file.read_text()
        data = json.loads(content)
        assert isinstance(data, list)
        assert len(data) == 0


class TestJsonEnrichmentRepositoryApplyEnrichment:
    """Tests for applying enrichment data to properties."""

    def test_apply_enrichment_to_property(self, sample_property_minimal, temp_json_file):
        """Test applying enrichment data to a property."""
        repo = JsonEnrichmentRepository(temp_json_file)
        enriched = repo.apply_enrichment_to_property(sample_property_minimal)

        # The minimal property should have None values
        # After applying enrichment, it should be populated
        # But only if the address matches
        assert enriched is not None

    def test_apply_enrichment_with_dict(self, sample_property_minimal):
        """Test applying enrichment from a dictionary."""
        repo = JsonEnrichmentRepository(Path("/tmp/nonexistent.json"))
        enrichment_dict = {
            "full_address": "100 Main St, Phoenix, AZ 85001",
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
        }

        enriched = repo.apply_enrichment_to_property(sample_property_minimal, enrichment_dict)

        # lot_sqft should be applied
        assert enriched.lot_sqft == 9500
        assert enriched.year_built == 2010

    def test_apply_enrichment_no_match(self, sample_property_minimal, temp_json_file):
        """Test applying enrichment when no matching property exists."""
        repo = JsonEnrichmentRepository(temp_json_file)
        # Reload to populate cache
        repo.load_all()

        # Create property with address not in enrichment file
        sample_property_minimal.full_address = "999 Nonexistent, NoCity, AZ 00000"
        enriched = repo.apply_enrichment_to_property(sample_property_minimal)

        # Should return property unchanged
        assert enriched == sample_property_minimal

    def test_apply_enrichment_updates_property(self, sample_property_minimal):
        """Test that enrichment properly updates property fields."""
        repo = JsonEnrichmentRepository(Path("/tmp/nonexistent.json"))
        enrichment_dict = {
            "full_address": sample_property_minimal.full_address,
            "lot_sqft": 12000,
            "year_built": 2015,
            "sewer_type": "city",
        }

        enriched = repo.apply_enrichment_to_property(sample_property_minimal, enrichment_dict)

        assert enriched.lot_sqft == 12000
        assert enriched.year_built == 2015
        assert enriched.sewer_type == SewerType.CITY


class TestJsonEnrichmentRepositorySerialization:
    """Tests for JSON serialization and deserialization."""

    def test_dict_to_enrichment(self, temp_json_file):
        """Test converting dictionary to EnrichmentData."""
        repo = JsonEnrichmentRepository(temp_json_file)
        data = {
            "full_address": "123 Main St, Phoenix, AZ 85001",
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
        }

        enrichment = repo._dict_to_enrichment(data)

        assert isinstance(enrichment, EnrichmentData)
        assert enrichment.full_address == "123 Main St, Phoenix, AZ 85001"
        assert enrichment.lot_sqft == 9500

    def test_enrichment_to_dict(self, temp_json_file, sample_enrichment_data):
        """Test converting EnrichmentData to dictionary."""
        repo = JsonEnrichmentRepository(temp_json_file)
        data = repo._enrichment_to_dict(sample_enrichment_data)

        assert isinstance(data, dict)
        assert data["full_address"] == sample_enrichment_data.full_address
        assert data["lot_sqft"] == sample_enrichment_data.lot_sqft

    def test_load_both_list_and_dict_formats(self, tmp_path):
        """Test loading JSON in both list and dict formats."""
        # Test list format
        json_list = tmp_path / "enrichment_list.json"
        json_list.write_text(
            json.dumps([{"full_address": "123 Main St", "lot_sqft": 9500}])
        )

        repo_list = JsonEnrichmentRepository(json_list)
        enrichment_list = repo_list.load_all()
        assert len(enrichment_list) == 1

        # Test dict format
        json_dict = tmp_path / "enrichment_dict.json"
        json_dict.write_text(
            json.dumps({"123 Main St": {"full_address": "123 Main St", "lot_sqft": 9500}})
        )

        repo_dict = JsonEnrichmentRepository(json_dict)
        enrichment_dict = repo_dict.load_all()
        assert len(enrichment_dict) == 1


# ============================================================================
# Integration Tests
# ============================================================================


class TestRepositoryIntegration:
    """Integration tests combining CSV and JSON repositories."""

    def test_csv_and_json_together(self, temp_csv_file, temp_json_file):
        """Test using CSV and JSON repositories together."""
        csv_repo = CsvPropertyRepository(temp_csv_file)
        json_repo = JsonEnrichmentRepository(temp_json_file)

        properties = csv_repo.load_all()
        enrichment_data = json_repo.load_all()

        # Apply enrichment to properties
        for prop in properties:
            json_repo.apply_enrichment_to_property(prop)

        assert len(properties) == 2
        assert len(enrichment_data) == 2

    def test_property_round_trip(self, tmp_path, sample_property):
        """Test full round-trip: CSV -> Property -> CSV."""
        csv_input = tmp_path / "input.csv"
        csv_output = tmp_path / "output.csv"

        # Create input CSV
        csv_input.write_text(
            "street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address\n"
            f"{sample_property.street},{sample_property.city},{sample_property.state},"
            f"{sample_property.zip_code},{sample_property.price},"
            f"{sample_property.price_num},{sample_property.beds},{sample_property.baths},"
            f"{sample_property.sqft},200.0,{sample_property.full_address}\n"
        )

        # Load, modify, and save
        repo1 = CsvPropertyRepository(csv_input, csv_output)
        properties = repo1.load_all()
        properties[0].beds = 5  # Modify
        repo1.save_all(properties)

        # Reload and verify
        repo2 = CsvPropertyRepository(csv_output)
        reloaded = repo2.load_all()
        assert reloaded[0].beds == 5

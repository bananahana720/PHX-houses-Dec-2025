"""Unit tests for Maricopa County API data pipeline.

This module provides comprehensive tests for:
1. SQL escaping functions (security)
2. Path validation (security)
3. Atomic file saves (reliability)
4. EnrichmentMergeService (business logic)
5. Concurrent extraction (performance)

Test Categories:
- TestSqlEscaping: SQL injection prevention
- TestPathValidation: Path traversal attack prevention
- TestAtomicSave: Atomic file save operations
- TestEnrichmentMergeService: Business logic for merging county data
- TestConcurrentExtraction: Async concurrent extraction tests
- TestMaricopaAssessorClientHelpers: Client helper method tests
"""

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Import modules to test
from phx_home_analysis.services.county_data.assessor_client import (
    MaricopaAssessorClient,
    escape_like_pattern,
    escape_sql_string,
)
from phx_home_analysis.services.county_data.models import ParcelData
from phx_home_analysis.services.enrichment import (
    ConflictReport,
    EnrichmentMergeService,
    FieldConflict,
)
from phx_home_analysis.utils.file_ops import atomic_json_save, cleanup_old_backups

# ============================================================================
# SQL ESCAPING TESTS - Security
# ============================================================================


class TestSqlEscaping:
    """Tests for SQL injection prevention in LIKE patterns and string literals."""

    # --- escape_like_pattern tests ---

    def test_escape_like_pattern_basic(self):
        """Test that basic strings pass through unchanged."""
        assert escape_like_pattern("test") == "test"
        assert escape_like_pattern("4732 W Davis Rd") == "4732 W Davis Rd"

    def test_escape_like_pattern_percent(self):
        """Test escaping of % wildcard character."""
        assert escape_like_pattern("100%") == "100\\%"
        assert escape_like_pattern("%test%") == "\\%test\\%"

    def test_escape_like_pattern_underscore(self):
        """Test escaping of _ wildcard character."""
        assert escape_like_pattern("test_value") == "test\\_value"
        assert escape_like_pattern("_prefix") == "\\_prefix"
        assert escape_like_pattern("suffix_") == "suffix\\_"

    def test_escape_like_pattern_single_quote(self):
        """Test escaping of single quotes (SQL string delimiter)."""
        assert escape_like_pattern("O'Brien") == "O''Brien"
        assert escape_like_pattern("it's") == "it''s"
        assert escape_like_pattern("'quoted'") == "''quoted''"

    def test_escape_like_pattern_backslash(self):
        """Test escaping of backslash characters."""
        assert escape_like_pattern("path\\file") == "path\\\\file"
        assert escape_like_pattern("C:\\Users") == "C:\\\\Users"

    def test_escape_like_pattern_combined(self):
        """Test escaping of multiple special characters together."""
        input_str = "100% of O'Brien's test_files\\"
        expected = "100\\% of O''Brien''s test\\_files\\\\"
        assert escape_like_pattern(input_str) == expected

    def test_escape_like_pattern_injection_attempt_quote_break(self):
        """Test that SQL injection via quote break is neutralized."""
        # Attempt to break out of string literal
        malicious = "'; DROP TABLE properties; --"
        escaped = escape_like_pattern(malicious)
        # Single quotes should be doubled, preventing break-out
        assert "''" in escaped
        assert "'" not in escaped.replace("''", "")

    def test_escape_like_pattern_injection_attempt_union(self):
        """Test that UNION-based injection is neutralized via escaping."""
        malicious = "' UNION SELECT * FROM users --"
        escaped = escape_like_pattern(malicious)
        # The single quote becomes two single quotes ('' instead of ')
        # so SQL parser sees literal quote string, not end of string
        assert escaped == "'' UNION SELECT * FROM users --"

    def test_escape_like_pattern_injection_attempt_wildcard(self):
        """Test that wildcard injection is neutralized."""
        # Attacker tries to match all records
        malicious = "%"
        escaped = escape_like_pattern(malicious)
        assert escaped == "\\%"

    def test_escape_like_pattern_empty_string(self):
        """Test that empty string is handled correctly."""
        assert escape_like_pattern("") == ""

    def test_escape_like_pattern_unicode(self):
        """Test that unicode characters pass through unchanged."""
        assert escape_like_pattern("Phoenix, AZ") == "Phoenix, AZ"
        assert escape_like_pattern("Calle Uno") == "Calle Uno"

    def test_escape_like_pattern_escape_order(self):
        """Test that escape order is correct (backslash first)."""
        # If backslash isn't escaped first, we'd get double-escaping issues
        # Input: %\ should become \%\\, not \\%\\\\
        input_str = "%\\"
        expected = "\\%\\\\"
        assert escape_like_pattern(input_str) == expected

    # --- escape_sql_string tests ---

    def test_escape_sql_string_basic(self):
        """Test that basic strings pass through unchanged."""
        assert escape_sql_string("test") == "test"
        assert escape_sql_string("123-45-678") == "123-45-678"

    def test_escape_sql_string_quote(self):
        """Test escaping of single quotes."""
        assert escape_sql_string("it's") == "it''s"
        assert escape_sql_string("O'Brien") == "O''Brien"

    def test_escape_sql_string_multiple_quotes(self):
        """Test escaping of multiple single quotes."""
        assert escape_sql_string("don't won't") == "don''t won''t"
        assert escape_sql_string("'''") == "''''''"

    def test_escape_sql_string_injection_attempt(self):
        """Test that SQL injection via quote is neutralized."""
        malicious = "'; DELETE FROM parcels; --"
        escaped = escape_sql_string(malicious)
        # The single quote becomes two single quotes ('' instead of ')
        # so SQL parser sees literal quote string, not end of string
        assert escaped == "''; DELETE FROM parcels; --"

    def test_escape_sql_string_empty(self):
        """Test that empty string is handled correctly."""
        assert escape_sql_string("") == ""


# ============================================================================
# PATH VALIDATION TESTS - Security
# ============================================================================


class TestPathValidation:
    """Tests for path traversal prevention in CLI file arguments."""

    @pytest.fixture
    def base_dir(self, tmp_path):
        """Create a temporary base directory for testing."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "data").mkdir()
        return project_dir

    def test_validate_path_within_base(self, base_dir):
        """Test that paths within base directory are allowed."""
        # Import the function from the script
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import validate_path
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        valid_path = base_dir / "data" / "file.json"
        valid_path.parent.mkdir(exist_ok=True)
        valid_path.touch()

        result = validate_path(valid_path, base_dir, "--test")
        assert result.is_absolute()
        # Should not raise an exception

    def test_validate_path_traversal_blocked(self, base_dir, monkeypatch):
        """Test that path traversal attempts are blocked."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import validate_path
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        # Attempt path traversal
        malicious_path = base_dir / ".." / ".." / "etc" / "passwd"

        # validate_path calls sys.exit on failure, so we need to catch it
        with pytest.raises(SystemExit) as exc_info:
            validate_path(malicious_path, base_dir, "--csv")

        assert exc_info.value.code == 1

    def test_validate_path_symlink_traversal(self, base_dir):
        """Test that symlink-based traversal is blocked."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import validate_path
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        # Create symlink pointing outside base
        symlink_path = base_dir / "data" / "sneaky_link"
        try:
            # On Windows, creating symlinks may require admin privileges
            import os

            if hasattr(os, "symlink"):
                symlink_path.symlink_to(base_dir.parent.parent / "etc")

                with pytest.raises(SystemExit):
                    validate_path(symlink_path / "passwd", base_dir, "--csv")
            else:
                pytest.skip("Symlinks not supported on this platform")
        except (OSError, NotImplementedError):
            pytest.skip("Symlink creation not permitted")


# ============================================================================
# ATOMIC SAVE TESTS - Reliability
# ============================================================================


class TestAtomicSave:
    """Tests for atomic file save operations with backup support."""

    def test_atomic_save_creates_file(self, tmp_path):
        """Test that atomic save creates a new file."""
        target = tmp_path / "test.json"
        data = {"key": "value", "nested": {"a": 1, "b": 2}}

        atomic_json_save(target, data, create_backup=False)

        assert target.exists()
        with open(target, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == data

    def test_atomic_save_creates_parent_directories(self, tmp_path):
        """Test that atomic save creates parent directories if missing."""
        target = tmp_path / "nested" / "dir" / "test.json"
        data = {"key": "value"}

        atomic_json_save(target, data, create_backup=False)

        assert target.exists()
        assert target.parent.exists()

    def test_atomic_save_creates_backup(self, tmp_path):
        """Test that atomic save creates backup of existing file."""
        target = tmp_path / "test.json"
        original = {"original": True}
        new_data = {"new": True}

        # Create original file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(original, f)

        # Save new data with backup
        backup_path = atomic_json_save(target, new_data, create_backup=True)

        # Check backup was created
        assert backup_path is not None
        assert backup_path.exists()
        assert ".bak" in backup_path.suffix or "bak" in backup_path.name

        with open(backup_path, encoding="utf-8") as f:
            backup_data = json.load(f)
        assert backup_data == original

        # Check new data was saved
        with open(target, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == new_data

    def test_atomic_save_no_backup_when_disabled(self, tmp_path):
        """Test that no backup is created when disabled."""
        target = tmp_path / "test.json"
        original = {"original": True}
        new_data = {"new": True}

        # Create original file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(original, f)

        # Save without backup
        backup_path = atomic_json_save(target, new_data, create_backup=False)

        assert backup_path is None
        # No backup files should exist
        backup_files = list(tmp_path.glob("*.bak*"))
        assert len(backup_files) == 0

    def test_atomic_save_no_partial_write_on_serialization_error(self, tmp_path):
        """Test that failed serialization doesn't corrupt existing file."""
        target = tmp_path / "test.json"
        original = {"original": True}

        # Create original file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(original, f)

        original_content = target.read_text()

        # Attempt to save non-serializable data
        with pytest.raises(TypeError):
            atomic_json_save(target, {"bad": lambda: None}, create_backup=False)

        # Original file should be unchanged
        assert target.read_text() == original_content
        with open(target, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == original

    def test_atomic_save_no_temp_file_left_on_success(self, tmp_path):
        """Test that temp files are cleaned up on success."""
        target = tmp_path / "test.json"
        atomic_json_save(target, {"key": "value"}, create_backup=False)

        # No .tmp files should remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_atomic_save_no_temp_file_left_on_failure(self, tmp_path):
        """Test that temp files are cleaned up on failure."""
        target = tmp_path / "test.json"

        with pytest.raises(TypeError):
            atomic_json_save(target, {"bad": lambda: None}, create_backup=False)

        # No .tmp files should remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_atomic_save_custom_indent(self, tmp_path):
        """Test that custom indent is respected."""
        target = tmp_path / "test.json"
        data = {"key": "value"}

        atomic_json_save(target, data, create_backup=False, indent=4)

        content = target.read_text()
        # With indent=4, the JSON should have 4-space indentation
        assert "    " in content

    def test_atomic_save_preserves_unicode(self, tmp_path):
        """Test that unicode characters are preserved."""
        target = tmp_path / "test.json"
        data = {"address": "Calle de la Paz", "city": "Phoenix"}

        atomic_json_save(target, data, create_backup=False)

        with open(target, encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["address"] == "Calle de la Paz"

    def test_cleanup_old_backups(self, tmp_path):
        """Test that old backups are cleaned up correctly."""
        import time

        # Create multiple backup files
        for i in range(7):
            backup = tmp_path / f"test.202312{10 + i:02d}_120000.bak.json"
            backup.write_text("{}")
            # Ensure different modification times
            time.sleep(0.01)

        # Keep only 3 most recent
        deleted = cleanup_old_backups(tmp_path, "test.*.bak.json", keep_count=3)

        assert len(deleted) == 4
        remaining = list(tmp_path.glob("test.*.bak.json"))
        assert len(remaining) == 3


# ============================================================================
# ENRICHMENT MERGE SERVICE TESTS - Business Logic
# ============================================================================


class TestEnrichmentMergeService:
    """Tests for EnrichmentMergeService business logic."""

    @pytest.fixture
    def service(self):
        """Create merge service with default lineage tracker.

        Note: Even when passing None, a default LineageTracker is created
        internally to ensure lineage is always tracked.
        """
        return EnrichmentMergeService(lineage_tracker=None)

    @pytest.fixture
    def sample_parcel(self):
        """Create sample parcel data from county assessor."""
        return ParcelData(
            apn="123-45-678",
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=8000,
            year_built=2000,
            garage_spaces=2,
            sewer_type="city",
            has_pool=True,
            source="maricopa_official",
        )

    @pytest.fixture
    def sample_parcel_arcgis(self):
        """Create sample parcel data from ArcGIS fallback (limited fields)."""
        return ParcelData(
            apn="123-45-678",
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=8000,
            year_built=2000,
            latitude=33.4484,
            longitude=-112.0740,
            source="maricopa_arcgis",
            # Fields NOT available from ArcGIS
            garage_spaces=None,
            sewer_type=None,
            has_pool=None,
        )

    # --- New property tests ---

    def test_merge_new_property(self, service, sample_parcel):
        """Test merging data for a new property (no existing entry)."""
        result = service.merge_parcel(
            existing_enrichment={},
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        assert result.success
        assert result.updated_entry["lot_sqft"] == 8000
        assert result.updated_entry["year_built"] == 2000
        assert result.updated_entry["garage_spaces"] == 2
        assert result.updated_entry["has_pool"] is True
        assert result.updated_entry["sewer_type"] == "city"

    def test_merge_new_property_reports_new_fields(self, service, sample_parcel):
        """Test that new fields are properly reported in conflict report."""
        result = service.merge_parcel(
            existing_enrichment={},
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        assert "lot_sqft" in result.conflict_report.new_fields
        assert "year_built" in result.conflict_report.new_fields
        assert result.conflict_report.total_new > 0

    # --- Manual research preservation tests ---

    def test_merge_preserves_manual_research(self, service, sample_parcel):
        """Test that manually researched data is preserved."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,  # Different from parcel (8000)
                "lot_sqft_source": "manual_research",
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        # Manual research should be preserved
        assert result.updated_entry["lot_sqft"] == 7500
        assert len(result.conflict_report.preserved_manual) >= 1

        # Check the preserved conflict details
        preserved = result.conflict_report.preserved_manual[0]
        assert preserved.field_name == "lot_sqft"
        assert preserved.existing_value == 7500
        assert preserved.new_value == 8000

    def test_merge_preserves_user_source(self, service, sample_parcel):
        """Test that user-sourced data is preserved."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7800,
                "lot_sqft_source": "user",
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        assert result.updated_entry["lot_sqft"] == 7800

    def test_merge_preserves_web_research(self, service, sample_parcel):
        """Test that web-researched data is preserved."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "sewer_type": "septic",
                "sewer_type_source": "web_research",
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        # Web research should be preserved over county data
        assert result.updated_entry["sewer_type"] == "septic"

    # --- Non-manual data update tests ---

    def test_merge_updates_non_manual_data(self, service, sample_parcel):
        """Test that non-manual data gets updated with county data."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,
                "lot_sqft_source": "csv",  # Not manual
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        # County data should override CSV data
        assert result.updated_entry["lot_sqft"] == 8000

    def test_merge_updates_unknown_source(self, service, sample_parcel):
        """Test that data with unknown source gets updated."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "year_built": 1995,
                # No source field - unknown source
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        # Unknown source should be updated
        assert result.updated_entry["year_built"] == 2000
        assert len(result.conflict_report.updated) >= 1

    # --- Update-only mode tests ---

    def test_merge_update_only_fills_missing(self, service, sample_parcel):
        """Test update_only mode fills missing fields."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,  # Existing value
                # year_built is missing
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
            update_only=True,
        )

        # Existing lot_sqft should be preserved
        assert result.updated_entry["lot_sqft"] == 7500
        # Missing year_built should be filled
        assert result.updated_entry["year_built"] == 2000

    def test_merge_update_only_preserves_all_existing(self, service, sample_parcel):
        """Test update_only mode preserves all existing values."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,
                "year_built": 1999,
                "garage_spaces": 3,
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
            update_only=True,
        )

        # All existing values should be preserved even if different
        assert result.updated_entry["lot_sqft"] == 7500
        assert result.updated_entry["year_built"] == 1999
        assert result.updated_entry["garage_spaces"] == 3

    def test_merge_update_only_skips_none_values(self, service, sample_parcel_arcgis):
        """Test update_only mode doesn't fill with None values."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,
                # garage_spaces is missing
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel_arcgis,  # garage_spaces is None
            update_only=True,
        )

        # garage_spaces should not be set since parcel has None
        assert result.updated_entry.get("garage_spaces") is None

    # --- should_update_field tests ---

    def test_should_update_field_manual_source(self, service):
        """Test that manual sources are never overwritten."""
        entry = {"field": "value", "field_source": "manual"}
        should_update, reason = service.should_update_field(entry, "field", "new_value")

        assert should_update is False
        assert "manual" in reason.lower()

    def test_should_update_field_manual_research_source(self, service):
        """Test that manual_research sources are never overwritten."""
        entry = {"field": "value", "field_source": "manual_research"}
        should_update, reason = service.should_update_field(entry, "field", "new_value")

        assert should_update is False
        assert "manual" in reason.lower()

    def test_should_update_field_none_existing(self, service):
        """Test that None values are always updated."""
        entry = {"field": None}
        should_update, reason = service.should_update_field(entry, "field", "new_value")

        assert should_update is True
        assert "no existing" in reason.lower()

    def test_should_update_field_missing(self, service):
        """Test that missing fields are updated."""
        entry = {}
        should_update, reason = service.should_update_field(entry, "field", "new_value")

        assert should_update is True

    def test_should_update_field_same_value(self, service):
        """Test that same values don't trigger update."""
        entry = {"field": "value"}
        should_update, reason = service.should_update_field(entry, "field", "value")

        assert should_update is False
        assert "match" in reason.lower()

    def test_should_update_field_different_value(self, service):
        """Test that different values trigger update."""
        entry = {"field": "old_value"}
        should_update, reason = service.should_update_field(entry, "field", "new_value")

        assert should_update is True
        assert "old_value" in reason and "new_value" in reason

    # --- Coordinates merge tests ---

    def test_merge_coordinates_from_arcgis(self, service, sample_parcel_arcgis):
        """Test that coordinates from ArcGIS fallback are merged."""
        result = service.merge_parcel(
            existing_enrichment={},
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel_arcgis,
        )

        assert result.updated_entry.get("latitude") == 33.4484
        assert result.updated_entry.get("longitude") == -112.0740

    def test_merge_coordinates_preserves_existing_in_update_only(
        self, service, sample_parcel_arcgis
    ):
        """Test that existing coordinates are preserved in update_only mode."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "latitude": 33.5000,
                "longitude": -112.1000,
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel_arcgis,
            update_only=True,
        )

        # Existing coordinates should be preserved
        assert result.updated_entry["latitude"] == 33.5000
        assert result.updated_entry["longitude"] == -112.1000

    # --- MergeResult and ConflictReport tests ---

    def test_merge_result_has_conflicts(self, service, sample_parcel):
        """Test MergeResult.has_conflicts property."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,
                "lot_sqft_source": "manual",
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        assert result.has_conflicts is True

    def test_merge_result_no_conflicts(self, service, sample_parcel):
        """Test MergeResult when there are no conflicts."""
        result = service.merge_parcel(
            existing_enrichment={},
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        # New fields aren't conflicts
        assert result.has_conflicts is False

    def test_merge_result_to_legacy_dict(self, service, sample_parcel):
        """Test MergeResult.to_legacy_dict() for backward compatibility."""
        existing = {
            "123 Main St, Phoenix, AZ 85001": {
                "lot_sqft": 7500,
                "lot_sqft_source": "manual",
            }
        }

        result = service.merge_parcel(
            existing_enrichment=existing,
            full_address="123 Main St, Phoenix, AZ 85001",
            parcel=sample_parcel,
        )

        legacy = result.to_legacy_dict()
        assert "preserved_manual" in legacy
        assert "updated" in legacy
        assert "new_fields" in legacy
        assert "skipped_no_change" in legacy


# ============================================================================
# CONCURRENT EXTRACTION TESTS - Performance
# ============================================================================


class TestConcurrentExtraction:
    """Tests for concurrent property extraction functionality."""

    @dataclass
    class MockProperty:
        """Mock property for testing."""

        full_address: str
        street: str

    @pytest.fixture
    def mock_properties(self):
        """Create a list of mock properties for testing."""
        return [
            self.MockProperty(full_address=f"{i} Main St, Phoenix, AZ 85001", street=f"{i} Main St")
            for i in range(1, 6)
        ]

    @pytest.fixture
    def mock_parcel(self):
        """Create a mock parcel data result."""
        return ParcelData(
            apn="123-45-678",
            full_address="Test",
            lot_sqft=8000,
            year_built=2000,
            source="test",
        )

    @pytest.mark.asyncio
    async def test_extract_batch_concurrent_success(self, mock_properties, mock_parcel):
        """Test concurrent extraction of multiple properties."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import extract_batch_concurrent
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        # Create mock client
        mock_client = AsyncMock()
        mock_client.extract_for_address = AsyncMock(return_value=mock_parcel)

        results = await extract_batch_concurrent(mock_client, mock_properties, max_concurrent=2)

        assert len(results) == 5
        # All should succeed
        for result in results:
            assert result.success
            assert result.parcel is not None

    @pytest.mark.asyncio
    async def test_extract_batch_concurrent_handles_errors(self, mock_properties):
        """Test that errors in individual extractions don't fail the batch."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import extract_batch_concurrent
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        # Mock client that raises on some calls
        call_count = 0

        async def mock_extract(street):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("API error")
            return ParcelData(apn="123", full_address=street, lot_sqft=8000, source="test")

        mock_client = AsyncMock()
        mock_client.extract_for_address = mock_extract

        results = await extract_batch_concurrent(mock_client, mock_properties, max_concurrent=2)

        # All results should be present
        assert len(results) == 5
        # Some should succeed, some should fail
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) > 0
        assert len(failures) > 0

    @pytest.mark.asyncio
    async def test_extract_batch_concurrent_progress_callback(self, mock_properties, mock_parcel):
        """Test that progress callback is called for each property."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import extract_batch_concurrent
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        mock_client = AsyncMock()
        mock_client.extract_for_address = AsyncMock(return_value=mock_parcel)

        progress_calls = []

        def on_progress(current, total, result):
            progress_calls.append((current, total, result))

        await extract_batch_concurrent(
            mock_client,
            mock_properties,
            max_concurrent=2,
            progress_callback=on_progress,
        )

        # Callback should be called for each property
        assert len(progress_calls) == 5
        # Total should always be 5
        for _, total, _ in progress_calls:
            assert total == 5

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, mock_properties, mock_parcel):
        """Test that semaphore properly limits concurrent requests."""
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        try:
            from extract_county_data import extract_batch_concurrent
        except ImportError:
            pytest.skip("extract_county_data.py not importable")
        finally:
            sys.path.pop(0)

        # Track concurrent calls
        current_concurrent = 0
        max_concurrent_observed = 0

        async def mock_extract(street):
            nonlocal current_concurrent, max_concurrent_observed
            current_concurrent += 1
            max_concurrent_observed = max(max_concurrent_observed, current_concurrent)
            await asyncio.sleep(0.1)  # Simulate API call
            current_concurrent -= 1
            return mock_parcel

        mock_client = AsyncMock()
        mock_client.extract_for_address = mock_extract

        await extract_batch_concurrent(
            mock_client,
            mock_properties,
            max_concurrent=2,  # Limit to 2
        )

        # Should never exceed the semaphore limit
        assert max_concurrent_observed <= 2


# ============================================================================
# MARICOPA ASSESSOR CLIENT HELPER TESTS
# ============================================================================


class TestMaricopaAssessorClientHelpers:
    """Tests for MaricopaAssessorClient helper methods."""

    def test_safe_int_from_int(self):
        """Test _safe_int with integer input."""
        assert MaricopaAssessorClient._safe_int(42) == 42

    def test_safe_int_from_float(self):
        """Test _safe_int with float input (truncates)."""
        assert MaricopaAssessorClient._safe_int(42.9) == 42

    def test_safe_int_from_string(self):
        """Test _safe_int with string input."""
        assert MaricopaAssessorClient._safe_int("42") == 42
        assert MaricopaAssessorClient._safe_int(" 42 ") == 42

    def test_safe_int_from_none(self):
        """Test _safe_int with None returns None."""
        assert MaricopaAssessorClient._safe_int(None) is None

    def test_safe_int_from_empty_string(self):
        """Test _safe_int with empty string returns None."""
        assert MaricopaAssessorClient._safe_int("") is None
        assert MaricopaAssessorClient._safe_int("   ") is None

    def test_safe_int_from_invalid(self):
        """Test _safe_int with invalid input returns None."""
        assert MaricopaAssessorClient._safe_int("not a number") is None

    def test_safe_float_from_float(self):
        """Test _safe_float with float input."""
        assert MaricopaAssessorClient._safe_float(42.5) == 42.5

    def test_safe_float_from_string(self):
        """Test _safe_float with string input."""
        assert MaricopaAssessorClient._safe_float("42.5") == 42.5

    def test_safe_float_from_none(self):
        """Test _safe_float with None returns None."""
        assert MaricopaAssessorClient._safe_float(None) is None

    def test_safe_bool_from_bool(self):
        """Test _safe_bool with bool input."""
        assert MaricopaAssessorClient._safe_bool(True) is True
        assert MaricopaAssessorClient._safe_bool(False) is False

    def test_safe_bool_from_string(self):
        """Test _safe_bool with string input."""
        assert MaricopaAssessorClient._safe_bool("true") is True
        assert MaricopaAssessorClient._safe_bool("yes") is True
        assert MaricopaAssessorClient._safe_bool("1") is True
        assert MaricopaAssessorClient._safe_bool("false") is False

    def test_safe_bool_from_int(self):
        """Test _safe_bool with int input."""
        assert MaricopaAssessorClient._safe_bool(1) is True
        assert MaricopaAssessorClient._safe_bool(0) is False

    def test_safe_bool_from_none(self):
        """Test _safe_bool with None returns None."""
        assert MaricopaAssessorClient._safe_bool(None) is None


# ============================================================================
# DATA MODEL TESTS
# ============================================================================


class TestParcelData:
    """Tests for ParcelData model."""

    def test_parcel_data_creation(self):
        """Test ParcelData can be created with required fields."""
        parcel = ParcelData(
            apn="123-45-678",
            full_address="123 Main St, Phoenix, AZ 85001",
        )
        assert parcel.apn == "123-45-678"
        assert parcel.full_address == "123 Main St, Phoenix, AZ 85001"
        assert parcel.source == "maricopa_assessor"  # Default

    def test_parcel_data_to_enrichment_dict(self):
        """Test ParcelData.to_enrichment_dict() method."""
        parcel = ParcelData(
            apn="123-45-678",
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=8000,
            year_built=2000,
            garage_spaces=2,
            sewer_type="city",
            has_pool=True,
            tax_annual=4500.00,
        )

        enrichment_dict = parcel.to_enrichment_dict()

        assert enrichment_dict["lot_sqft"] == 8000
        assert enrichment_dict["year_built"] == 2000
        assert enrichment_dict["garage_spaces"] == 2
        assert enrichment_dict["sewer_type"] == "city"
        assert enrichment_dict["has_pool"] is True
        assert enrichment_dict["tax_annual"] == 4500.00


class TestFieldConflict:
    """Tests for FieldConflict model validation."""

    def test_field_conflict_valid_actions(self):
        """Test that valid actions are accepted."""
        for action in ["preserved", "updated", "skipped", "added"]:
            conflict = FieldConflict(
                field_name="test",
                existing_value="old",
                new_value="new",
                action=action,
                reason="test reason",
            )
            assert conflict.action == action

    def test_field_conflict_invalid_action(self):
        """Test that invalid actions raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FieldConflict(
                field_name="test",
                existing_value="old",
                new_value="new",
                action="invalid_action",
                reason="test reason",
            )
        assert "invalid_action" in str(exc_info.value).lower()


class TestConflictReport:
    """Tests for ConflictReport model."""

    def test_conflict_report_totals(self):
        """Test ConflictReport total property calculations."""
        report = ConflictReport(
            preserved_manual=[
                FieldConflict(
                    field_name="f1",
                    existing_value=1,
                    new_value=2,
                    action="preserved",
                    reason="manual",
                ),
            ],
            updated=[
                FieldConflict(
                    field_name="f2",
                    existing_value=1,
                    new_value=2,
                    action="updated",
                    reason="override",
                ),
                FieldConflict(
                    field_name="f3",
                    existing_value=3,
                    new_value=4,
                    action="updated",
                    reason="override",
                ),
            ],
            new_fields=["f4", "f5", "f6"],
            skipped_no_change=["f7"],
        )

        assert report.total_preserved == 1
        assert report.total_updated == 2
        assert report.total_new == 3
        assert report.total_skipped == 1

    def test_conflict_report_to_dict(self):
        """Test ConflictReport.to_dict() for backward compatibility."""
        report = ConflictReport(
            preserved_manual=[
                FieldConflict(
                    field_name="lot_sqft",
                    existing_value=7500,
                    new_value=8000,
                    action="preserved",
                    reason="manual",
                ),
            ],
            updated=[
                FieldConflict(
                    field_name="year_built",
                    existing_value=1999,
                    new_value=2000,
                    action="updated",
                    reason="override",
                ),
            ],
            new_fields=["garage_spaces"],
            skipped_no_change=["has_pool"],
        )

        d = report.to_dict()

        assert len(d["preserved_manual"]) == 1
        assert d["preserved_manual"][0]["field"] == "lot_sqft"
        assert d["preserved_manual"][0]["value"] == 7500
        assert d["preserved_manual"][0]["county_value"] == 8000

        assert len(d["updated"]) == 1
        assert d["updated"][0]["field"] == "year_built"
        assert d["updated"][0]["old"] == 1999
        assert d["updated"][0]["new"] == 2000

        assert d["new_fields"] == ["garage_spaces"]
        assert d["skipped_no_change"] == ["has_pool"]

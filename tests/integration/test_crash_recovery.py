"""Integration tests for crash recovery scenarios.

Tests the data storage layer's ability to recover from corrupted or missing
data files using backup restore functionality.
"""

import json
from pathlib import Path

from src.phx_home_analysis.domain.entities import EnrichmentData
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository


class TestCrashRecoveryIntegration:
    """Integration tests for crash recovery scenarios."""

    def test_recovery_after_corrupt_json(self, tmp_path: Path):
        """System should recover from corrupted JSON file.

        Scenario:
        1. Create valid data and save twice (second save creates backup)
        2. Simulate corruption by writing invalid content
        3. Recover from backup
        4. Verify data is restored correctly
        """
        json_path = tmp_path / "enrichment_data.json"

        # Step 1: Create initial valid data
        repo = JsonEnrichmentRepository(json_path)
        valid_data = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(
                full_address="123 Main St, Phoenix, AZ 85001",
                lot_sqft=8500,
                year_built=2010,
            )
        }
        # First save creates the file (no backup since no existing file)
        repo.save_all(valid_data)

        # Second save creates a backup of the existing file
        repo.save_all(valid_data)

        # Verify backup was created after second save
        backups = list(tmp_path.glob("enrichment_data.*.bak.json"))
        assert len(backups) >= 1, "Backup should be created on second save"

        # Step 2: Simulate corruption
        json_path.write_text("{invalid json content with missing bracket")

        # Step 3: Create new repo instance and recover
        repo2 = JsonEnrichmentRepository(json_path)
        result = repo2.restore_from_backup()

        assert result is True, "Restore should succeed"

        # Step 4: Verify recovered data
        recovered = repo2.load_all()
        assert "123 Main St, Phoenix, AZ 85001" in recovered
        assert recovered["123 Main St, Phoenix, AZ 85001"].lot_sqft == 8500

    def test_recovery_after_missing_file(self, tmp_path: Path):
        """System should recover when main file is missing but backup exists.

        Scenario:
        1. Create backup file manually (simulating backup from previous run)
        2. Main file does not exist
        3. Restore from backup
        4. Verify main file is created with backup content
        """
        json_path = tmp_path / "enrichment_data.json"
        backup_path = tmp_path / "enrichment_data.20251203_120000.bak.json"

        # Create only backup (main file never existed or was deleted)
        backup_data = [
            {
                "full_address": "456 Oak Ave, Mesa, AZ 85201",
                "lot_sqft": 9000,
                "year_built": 2015,
            }
        ]
        backup_path.write_text(json.dumps(backup_data))

        # Verify main file doesn't exist
        assert not json_path.exists()

        # Recovery
        repo = JsonEnrichmentRepository(json_path)
        result = repo.restore_from_backup()

        assert result is True
        assert json_path.exists(), "Main file should be created from backup"

        # Verify content
        loaded = repo.load_all()
        assert "456 Oak Ave, Mesa, AZ 85201" in loaded
        assert loaded["456 Oak Ave, Mesa, AZ 85201"].lot_sqft == 9000

    def test_recovery_preserves_all_fields(self, tmp_path: Path):
        """Recovery should preserve all enrichment fields without data loss.

        Scenario:
        1. Create comprehensive data with many fields
        2. Save and create backup
        3. Corrupt main file
        4. Recover and verify ALL fields are intact
        """
        json_path = tmp_path / "enrichment_data.json"

        # Create data with many fields
        repo = JsonEnrichmentRepository(json_path)
        comprehensive_data = {
            "123 Complete St, Phoenix, AZ 85001": EnrichmentData(
                full_address="123 Complete St, Phoenix, AZ 85001",
                lot_sqft=10000,
                year_built=2008,
                garage_spaces=3,
                sewer_type="city",
                tax_annual=4500.50,
                hoa_fee=0,
                commute_minutes=25,
                school_district="Phoenix Union",
                school_rating=8.5,
                orientation="north",
                distance_to_grocery_miles=1.2,
                distance_to_highway_miles=3.0,
                solar_status="owned",
                solar_lease_monthly=None,
                has_pool=True,
                pool_equipment_age=3,
                roof_age=12,
                hvac_age=8,
            )
        }
        repo.save_all(comprehensive_data)

        # Create backup by saving again
        repo.save_all(comprehensive_data)

        # Corrupt main file
        json_path.write_text("corrupted")

        # Recover
        repo2 = JsonEnrichmentRepository(json_path)
        repo2.restore_from_backup()

        # Verify ALL fields
        recovered = repo2.load_all()
        assert "123 Complete St, Phoenix, AZ 85001" in recovered

        data = recovered["123 Complete St, Phoenix, AZ 85001"]
        assert data.lot_sqft == 10000
        assert data.year_built == 2008
        assert data.garage_spaces == 3
        assert data.sewer_type == "city"
        assert data.tax_annual == 4500.50
        assert data.hoa_fee == 0
        assert data.commute_minutes == 25
        assert data.school_district == "Phoenix Union"
        assert data.school_rating == 8.5
        assert data.orientation == "north"
        assert data.distance_to_grocery_miles == 1.2
        assert data.distance_to_highway_miles == 3.0
        assert data.solar_status == "owned"
        assert data.has_pool is True
        assert data.pool_equipment_age == 3
        assert data.roof_age == 12
        assert data.hvac_age == 8

    def test_multiple_properties_recovery(self, tmp_path: Path):
        """Recovery should handle multiple properties correctly.

        Scenario:
        1. Create data with multiple properties
        2. Save and backup
        3. Corrupt
        4. Recover and verify all properties present
        """
        json_path = tmp_path / "enrichment_data.json"

        # Create multiple properties
        repo = JsonEnrichmentRepository(json_path)
        multi_data = {
            "123 First St, Phoenix, AZ 85001": EnrichmentData(
                full_address="123 First St, Phoenix, AZ 85001",
                lot_sqft=7000,
            ),
            "456 Second Ave, Scottsdale, AZ 85251": EnrichmentData(
                full_address="456 Second Ave, Scottsdale, AZ 85251",
                lot_sqft=8000,
            ),
            "789 Third Blvd, Mesa, AZ 85201": EnrichmentData(
                full_address="789 Third Blvd, Mesa, AZ 85201",
                lot_sqft=9000,
            ),
        }
        repo.save_all(multi_data)
        repo.save_all(multi_data)  # Creates backup

        # Corrupt
        json_path.write_text("[]")  # Empty list

        # Recover
        repo2 = JsonEnrichmentRepository(json_path)
        repo2.restore_from_backup()

        # Verify all properties
        recovered = repo2.load_all()
        assert len(recovered) == 3
        assert "123 First St, Phoenix, AZ 85001" in recovered
        assert "456 Second Ave, Scottsdale, AZ 85251" in recovered
        assert "789 Third Blvd, Mesa, AZ 85201" in recovered


class TestAtomicWriteIntegrity:
    """Tests verifying atomic write behavior prevents partial writes."""

    def test_atomic_save_creates_backup(self, tmp_path: Path):
        """Atomic save should always create backup of existing file."""
        json_path = tmp_path / "enrichment_data.json"

        # Initial save (no backup since no existing file)
        repo = JsonEnrichmentRepository(json_path)
        data = {
            "123 Test St": EnrichmentData(
                full_address="123 Test St",
                lot_sqft=5000,
            )
        }
        repo.save_all(data)

        # Count backups before second save
        backups_before = list(tmp_path.glob("enrichment_data.*.bak.json"))

        # Second save should create backup
        data["123 Test St"].lot_sqft = 6000
        repo.save_all(data)

        backups_after = list(tmp_path.glob("enrichment_data.*.bak.json"))
        assert len(backups_after) > len(backups_before), "Backup should be created"

    def test_save_then_load_consistency(self, tmp_path: Path):
        """Data should be identical after save-load cycle."""
        json_path = tmp_path / "enrichment_data.json"

        repo = JsonEnrichmentRepository(json_path)
        original_data = {
            "123 Test St, Phoenix, AZ 85001": EnrichmentData(
                full_address="123 Test St, Phoenix, AZ 85001",
                lot_sqft=8500,
                year_built=2012,
                garage_spaces=2,
                hoa_fee=0,
            )
        }

        repo.save_all(original_data)

        # Load in new repo instance
        repo2 = JsonEnrichmentRepository(json_path)
        loaded_data = repo2.load_all()

        # Compare
        assert "123 Test St, Phoenix, AZ 85001" in loaded_data
        loaded = loaded_data["123 Test St, Phoenix, AZ 85001"]
        original = original_data["123 Test St, Phoenix, AZ 85001"]

        assert loaded.full_address == original.full_address
        assert loaded.lot_sqft == original.lot_sqft
        assert loaded.year_built == original.year_built
        assert loaded.garage_spaces == original.garage_spaces
        assert loaded.hoa_fee == original.hoa_fee


class TestNormalizedAddressRecovery:
    """Tests that normalized_address is correctly handled in recovery."""

    def test_normalized_address_preserved_after_recovery(self, tmp_path: Path):
        """Normalized address should be preserved/recomputed after recovery."""
        json_path = tmp_path / "enrichment_data.json"
        backup_path = tmp_path / "enrichment_data.20251203_120000.bak.json"

        # Create backup with normalized_address
        backup_data = [
            {
                "full_address": "123 Main St, Phoenix, AZ 85001",
                "normalized_address": "123 main st phoenix az 85001",
                "lot_sqft": 8000,
            }
        ]
        backup_path.write_text(json.dumps(backup_data))

        # Restore
        repo = JsonEnrichmentRepository(json_path)
        repo.restore_from_backup()

        # Verify normalized_address is present
        loaded = repo.load_all()
        assert "123 Main St, Phoenix, AZ 85001" in loaded
        assert (
            loaded["123 Main St, Phoenix, AZ 85001"].normalized_address
            == "123 main st phoenix az 85001"
        )

    def test_normalized_address_computed_if_missing_in_backup(self, tmp_path: Path):
        """Normalized address should be computed if missing from backup."""
        json_path = tmp_path / "enrichment_data.json"
        backup_path = tmp_path / "enrichment_data.20251203_120000.bak.json"

        # Create backup WITHOUT normalized_address (simulating old format)
        backup_data = [
            {
                "full_address": "456 Oak Ave, Mesa, AZ 85201",
                "lot_sqft": 9000,
            }
        ]
        backup_path.write_text(json.dumps(backup_data))

        # Restore
        repo = JsonEnrichmentRepository(json_path)
        repo.restore_from_backup()

        # Verify normalized_address is computed
        loaded = repo.load_all()
        assert "456 Oak Ave, Mesa, AZ 85201" in loaded
        assert (
            loaded["456 Oak Ave, Mesa, AZ 85201"].normalized_address == "456 oak ave mesa az 85201"
        )

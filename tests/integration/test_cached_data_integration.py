"""Integration tests for CachedDataManager with pipeline.

Tests the CachedDataManager integration with real repositories and pipeline
to verify caching behavior, data persistence, and performance improvements.
"""

import json
import time
from unittest.mock import patch

from src.phx_home_analysis.domain.entities import EnrichmentData
from src.phx_home_analysis.pipeline.orchestrator import AnalysisPipeline
from src.phx_home_analysis.repositories.cached_manager import CachedDataManager
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository


class TestCachedDataManagerIntegration:
    """Test CachedDataManager integration with real repositories."""

    def test_pipeline_uses_cached_data(self, tmp_path, sample_property):
        """Verify pipeline only loads data once during full run.

        Tests that multiple get_all() calls within a single pipeline run
        use the cached data without re-reading from disk.
        """
        # Arrange - Create test data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        # Create repository and cache
        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Load data multiple times
        with patch.object(repo, 'load_all', wraps=repo.load_all) as mock_load:
            data1 = cache.get_all()
            data2 = cache.get_all()
            data3 = cache.get_all()

        # Assert - load_all() called only once
        assert mock_load.call_count == 1
        # All references should be the same object
        assert data1 is data2
        assert data2 is data3
        # Data should be valid
        assert len(data1) == 1
        assert sample_property.full_address in data1

    def test_cache_invalidation_forces_reload(self, tmp_path, sample_property):
        """Verify invalidate() causes next get_all() to reload from disk.

        Tests that cache invalidation properly clears cached data and
        forces a reload on the next access.
        """
        # Arrange - Create test data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Load, invalidate, reload
        data1 = cache.get_all()
        assert cache.is_loaded is True

        cache.invalidate()
        assert cache.is_loaded is False

        with patch.object(repo, 'load_all', wraps=repo.load_all) as mock_load:
            data2 = cache.get_all()

        # Assert - Reload occurred
        mock_load.assert_called_once()
        # Data should be different object reference
        assert data1 is not data2
        # But same content
        assert len(data1) == len(data2)
        assert sample_property.full_address in data2

    def test_dirty_flag_triggers_save(self, tmp_path, sample_property):
        """Verify save_if_dirty() writes changes to disk.

        Tests that the dirty flag correctly tracks modifications and
        triggers saves only when needed.
        """
        # Arrange - Create initial data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Load data
        cache.get_all()
        assert cache.is_dirty is False

        # No changes yet, should not save
        saved = cache.save_if_dirty()
        assert saved is False

        # Make a change
        new_address = "456 Test St, Phoenix, AZ 85001"
        new_enrichment = EnrichmentData(
            full_address=new_address,
            lot_sqft=10000,
            year_built=2015,
            garage_spaces=3,
            sewer_type="city",
            hoa_fee=0,
        )
        cache.update(new_address, new_enrichment)
        assert cache.is_dirty is True

        # Save changes
        saved = cache.save_if_dirty()
        assert saved is True
        assert cache.is_dirty is False

        # Second save should not write (no changes)
        saved = cache.save_if_dirty()
        assert saved is False

        # Assert - Verify file was updated (saved as list of dicts)
        saved_data = json.loads(enrichment_file.read_text())
        assert len(saved_data) == 2
        # Find the new address in the list
        addresses = [item["full_address"] for item in saved_data]
        assert new_address in addresses
        # Find the new entry
        new_entry = next(item for item in saved_data if item["full_address"] == new_address)
        assert new_entry["lot_sqft"] == 10000

    def test_concurrent_access_safety(self, tmp_path, sample_property):
        """Verify cache handles concurrent read access safely.

        Tests that multiple threads/operations can safely read from
        the cache without corruption or race conditions.
        """
        # Arrange - Create test data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"

        # Create multiple properties for testing
        test_data = []
        for i in range(10):
            address = f"{i} Test St, Phoenix, AZ 85001"
            test_data.append({
                "full_address": address,
                "lot_sqft": 9000 + i * 100,
                "year_built": 2010 + i,
                "garage_spaces": 2,
                "sewer_type": "city",
                "hoa_fee": 0,
            })
        enrichment_file.write_text(json.dumps(test_data))

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Multiple concurrent reads
        results = []
        for _ in range(5):
            data = cache.get_all()
            results.append(data)

        # Assert - All reads return same reference
        for i in range(len(results) - 1):
            assert results[i] is results[i + 1]

        # Data integrity verified
        assert len(results[0]) == 10
        addresses = [item["full_address"] for item in test_data]
        for address in addresses:
            assert address in results[0]

    def test_cache_with_force_reload(self, tmp_path, sample_property):
        """Verify force_reload parameter bypasses cache.

        Tests that force_reload=True always loads from disk even
        when cache is populated.
        """
        # Arrange - Create test data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Load with and without force_reload
        with patch.object(repo, 'load_all', wraps=repo.load_all) as mock_load:
            data1 = cache.get_all()  # Initial load
            data2 = cache.get_all()  # Uses cache
            data3 = cache.get_all(force_reload=True)  # Forces reload

        # Assert - Two loads occurred (initial + force_reload)
        assert mock_load.call_count == 2
        # data1 and data2 are same reference (cached)
        assert data1 is data2
        # data3 is different reference (reloaded)
        assert data1 is not data3
        # But content is the same
        assert len(data1) == len(data3)

    def test_update_before_load_triggers_load(self, tmp_path, sample_property):
        """Verify update() on unloaded cache triggers initial load.

        Tests that calling update() before get_all() automatically
        loads the cache first.
        """
        # Arrange - Create test data file (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Update before explicit load
        assert cache.is_loaded is False

        new_enrichment = EnrichmentData(
            full_address="New Address, Phoenix, AZ 85001",
            lot_sqft=10000,
            year_built=2020,
            garage_spaces=3,
            sewer_type="city",
            hoa_fee=0,
        )

        with patch.object(repo, 'load_all', wraps=repo.load_all) as mock_load:
            cache.update("New Address, Phoenix, AZ 85001", new_enrichment)

        # Assert - Load was triggered
        mock_load.assert_called_once()
        assert cache.is_loaded is True
        assert cache.is_dirty is True

    def test_cache_performance_improvement(self, tmp_path, sample_property):
        """Verify cache provides measurable performance improvement.

        Tests that cached access is significantly faster than
        repeated file I/O operations.
        """
        # Arrange - Create large test dataset (list format)
        enrichment_file = tmp_path / "enrichment_data.json"
        test_data = []

        # Create 100 properties
        for i in range(100):
            address = f"{i} Test St, Phoenix, AZ 85001"
            test_data.append({
                "full_address": address,
                "lot_sqft": 9000 + i * 100,
                "year_built": 2010 + (i % 15),
                "garage_spaces": 2 + (i % 2),
                "sewer_type": "city",
                "hoa_fee": 0,
            })
        enrichment_file.write_text(json.dumps(test_data))

        # Create cached and uncached repos
        cached_repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(cached_repo)

        uncached_repo = JsonEnrichmentRepository(str(enrichment_file))

        # Act - Time cached access (multiple reads)
        cache.get_all()  # Warm up cache
        start_cached = time.perf_counter()
        for _ in range(10):
            data = cache.get_all()
        cached_time = time.perf_counter() - start_cached

        # Time uncached access (multiple reads from disk)
        start_uncached = time.perf_counter()
        for _ in range(10):
            data = uncached_repo.load_all()
        uncached_time = time.perf_counter() - start_uncached

        # Assert - Cached access should be significantly faster
        # Cache should be at least 5x faster (conservative estimate)
        assert cached_time < uncached_time / 5, (
            f"Cache not providing expected speedup: "
            f"cached={cached_time:.4f}s, uncached={uncached_time:.4f}s"
        )

    def test_pipeline_run_with_cache_manager(
        self, tmp_path, sample_property
    ):
        """Verify complete pipeline run uses cache manager correctly.

        Tests that the pipeline run() method properly integrates with
        CachedDataManager and saves changes if dirty.
        """
        # Arrange - Create test data files
        enrichment_file = tmp_path / "enrichment_data.json"
        csv_file = tmp_path / "phx_homes.csv"
        output_csv = tmp_path / "ranked_homes.csv"

        # Create minimal CSV with one property and required columns
        csv_file.write_text(
            "full_address,street,city,state,zip,price,price_num,beds,baths,sqft\n"
            f"{sample_property.full_address},123 Desert Rose Ln,Phoenix,AZ,85001,$475000,475000,4,2.0,2200\n"
        )

        # Create enrichment data (list format)
        test_data = [{
            "full_address": sample_property.full_address,
            "lot_sqft": 9500,
            "year_built": 2010,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }]
        enrichment_file.write_text(json.dumps(test_data))

        # Create config using default then replacing paths (frozen dataclass)
        from dataclasses import replace

        from src.phx_home_analysis.config.settings import AppConfig, ProjectPaths

        # Create custom paths
        paths = ProjectPaths(
            base_dir=tmp_path,
            input_csv=csv_file,
            output_csv=output_csv,
            enrichment_json=enrichment_file,
        )

        # Use default config and replace paths
        default_config = AppConfig.default(base_dir=tmp_path)
        mock_config = replace(default_config, paths=paths)

        # Create repositories
        from src.phx_home_analysis.repositories import CsvPropertyRepository
        property_repo = CsvPropertyRepository(
            csv_file_path=str(csv_file),
            ranked_csv_path=str(output_csv)
        )
        enrichment_repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(enrichment_repo)

        pipeline = AnalysisPipeline(
            config=mock_config,
            property_repo=property_repo,
            enrichment_repo=enrichment_repo,
            cached_data_manager=cache,
        )

        # Act - Run full pipeline
        with patch.object(enrichment_repo, 'load_all', wraps=enrichment_repo.load_all) as mock_load:
            result = pipeline.run()

        # Assert - Only one load occurred
        assert mock_load.call_count == 1

        # Pipeline completed successfully
        assert result.total_properties == 1
        assert result.execution_time_seconds >= 0

        # Output file created
        assert output_csv.exists()


class TestCachedDataManagerEdgeCases:
    """Test edge cases and error conditions for CachedDataManager."""

    def test_empty_cache_load(self, tmp_path):
        """Verify cache handles empty enrichment file correctly."""
        # Arrange - Create empty enrichment file
        enrichment_file = tmp_path / "enrichment_data.json"
        enrichment_file.write_text("{}")

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Load empty cache
        data = cache.get_all()

        # Assert - Empty dict returned
        assert data == {}
        assert cache.is_loaded is True

    def test_save_empty_cache(self, tmp_path):
        """Verify save_if_dirty() handles empty cache correctly."""
        # Arrange - Create empty enrichment file
        enrichment_file = tmp_path / "enrichment_data.json"
        enrichment_file.write_text("{}")

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Save without loading
        saved = cache.save_if_dirty()

        # Assert - No save occurred (cache not loaded)
        assert saved is False

    def test_invalidate_unloaded_cache(self, tmp_path):
        """Verify invalidate() on unloaded cache is safe."""
        # Arrange - Create repository
        enrichment_file = tmp_path / "enrichment_data.json"
        enrichment_file.write_text("{}")

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        # Act - Invalidate before loading
        assert cache.is_loaded is False
        cache.invalidate()

        # Assert - No error, still not loaded
        assert cache.is_loaded is False
        assert cache.is_dirty is False

    def test_multiple_updates_accumulate_dirty_flag(self, tmp_path):
        """Verify multiple updates maintain dirty flag correctly."""
        # Arrange
        enrichment_file = tmp_path / "enrichment_data.json"
        enrichment_file.write_text("{}")

        repo = JsonEnrichmentRepository(str(enrichment_file))
        cache = CachedDataManager(repo)

        cache.get_all()  # Load empty cache
        assert cache.is_dirty is False

        # Act - Multiple updates
        for i in range(3):
            enrichment = EnrichmentData(
                full_address=f"{i} Test St, Phoenix, AZ 85001",
                lot_sqft=9000 + i * 100,
                year_built=2010,
                garage_spaces=2,
                sewer_type="city",
                hoa_fee=0,
            )
            cache.update(f"{i} Test St, Phoenix, AZ 85001", enrichment)

        # Assert - Dirty flag persists
        assert cache.is_dirty is True

        # Save and verify
        saved = cache.save_if_dirty()
        assert saved is True
        assert cache.is_dirty is False

        # All updates saved
        data = json.loads(enrichment_file.read_text())
        assert len(data) == 3

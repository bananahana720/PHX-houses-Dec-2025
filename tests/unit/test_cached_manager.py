"""Unit tests for CachedDataManager.

Tests the centralized caching layer for enrichment data, including:
- Cache hit behavior (second call uses cached data)
- Force reload bypasses cache
- Update marks dirty
- Save only when dirty
- Cache invalidation
- Integration with EnrichmentRepository
"""

import pytest

from src.phx_home_analysis.domain.entities import EnrichmentData
from src.phx_home_analysis.repositories.cached_manager import CachedDataManager
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def enrichment_data_dict():
    """Create sample enrichment data dictionary."""
    return {
        "123 Main St, Phoenix, AZ 85001": EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2010,
            garage_spaces=2,
            sewer_type="city",
        ),
        "456 Oak Ave, Scottsdale, AZ 85251": EnrichmentData(
            full_address="456 Oak Ave, Scottsdale, AZ 85251",
            lot_sqft=10500,
            year_built=2012,
            garage_spaces=2,
            sewer_type="city",
        ),
    }


@pytest.fixture
def mock_repository(enrichment_data_dict):
    """Create a mock repository that returns test data."""

    class MockRepository:
        def __init__(self):
            self.load_count = 0
            self.save_count = 0
            self.last_saved_data = None
            self._data = enrichment_data_dict.copy()

        def load_all(self):
            self.load_count += 1
            # Return a copy to simulate fresh load
            return self._data.copy()

        def save_all(self, data):
            self.save_count += 1
            self.last_saved_data = data
            self._data = data.copy()

    return MockRepository()


@pytest.fixture
def cache_manager(mock_repository):
    """Create a CachedDataManager with mock repository."""
    return CachedDataManager(mock_repository)


# ============================================================================
# Basic Cache Behavior Tests
# ============================================================================


class TestCacheBasicBehavior:
    """Tests for basic cache loading and hit behavior."""

    def test_first_call_loads_from_repository(self, cache_manager, mock_repository):
        """First call to get_all should load from repository."""
        assert mock_repository.load_count == 0

        data = cache_manager.get_all()

        assert mock_repository.load_count == 1
        assert len(data) == 2
        assert "123 Main St, Phoenix, AZ 85001" in data

    def test_second_call_uses_cache(self, cache_manager, mock_repository):
        """Second call to get_all should use cached data (no repository call)."""
        # First call loads from repository
        data1 = cache_manager.get_all()
        assert mock_repository.load_count == 1

        # Second call uses cache
        data2 = cache_manager.get_all()
        assert mock_repository.load_count == 1  # Still 1, not 2

        # Should return same object reference
        assert data1 is data2

    def test_multiple_calls_use_cache(self, cache_manager, mock_repository):
        """Multiple calls should all use cache after first load."""
        cache_manager.get_all()
        cache_manager.get_all()
        cache_manager.get_all()
        cache_manager.get_all()

        # Only one load despite 4 calls
        assert mock_repository.load_count == 1

    def test_cache_not_loaded_initially(self, cache_manager):
        """Cache should not be loaded on initialization."""
        assert not cache_manager.is_loaded
        assert cache_manager._cache is None

    def test_cache_loaded_after_get_all(self, cache_manager):
        """Cache should be marked as loaded after get_all."""
        assert not cache_manager.is_loaded

        cache_manager.get_all()

        assert cache_manager.is_loaded
        assert cache_manager._cache is not None


# ============================================================================
# Force Reload Tests
# ============================================================================


class TestForceReload:
    """Tests for force_reload parameter."""

    def test_force_reload_bypasses_cache(self, cache_manager, mock_repository):
        """force_reload=True should reload from repository."""
        # First load
        cache_manager.get_all()
        assert mock_repository.load_count == 1

        # Force reload
        cache_manager.get_all(force_reload=True)
        assert mock_repository.load_count == 2

    def test_force_reload_returns_fresh_data(self, cache_manager, mock_repository):
        """force_reload should return fresh data from repository."""
        # First load
        data1 = cache_manager.get_all()

        # Modify repository data
        mock_repository._data["789 New St, Phoenix, AZ 85003"] = EnrichmentData(
            full_address="789 New St, Phoenix, AZ 85003",
            lot_sqft=8000,
        )

        # Normal call won't see new data
        data2 = cache_manager.get_all()
        assert "789 New St, Phoenix, AZ 85003" not in data2

        # Force reload sees new data
        data3 = cache_manager.get_all(force_reload=True)
        assert "789 New St, Phoenix, AZ 85003" in data3

    def test_force_reload_resets_dirty_flag(self, cache_manager):
        """force_reload should reset dirty flag."""
        # Load and modify
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)
        assert cache_manager.is_dirty

        # Force reload resets dirty
        cache_manager.get_all(force_reload=True)
        assert not cache_manager.is_dirty


# ============================================================================
# Update and Dirty Flag Tests
# ============================================================================


class TestUpdateAndDirtyFlag:
    """Tests for update() method and dirty flag tracking."""

    def test_update_marks_cache_as_dirty(self, cache_manager):
        """Updating cache should set dirty flag."""
        cache_manager.get_all()
        assert not cache_manager.is_dirty

        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        assert cache_manager.is_dirty

    def test_update_adds_new_entry(self, cache_manager):
        """Update should add new entries to cache."""
        data = cache_manager.get_all()
        assert "999 Test St" not in data

        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        data = cache_manager.get_all()
        assert "999 Test St" in data
        assert data["999 Test St"].lot_sqft == 7000

    def test_update_modifies_existing_entry(self, cache_manager):
        """Update should modify existing entries."""
        data = cache_manager.get_all()
        original_lot = data["123 Main St, Phoenix, AZ 85001"].lot_sqft

        # Modify existing entry
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=12000,
        )
        cache_manager.update("123 Main St, Phoenix, AZ 85001", enrichment)

        data = cache_manager.get_all()
        assert data["123 Main St, Phoenix, AZ 85001"].lot_sqft == 12000
        assert data["123 Main St, Phoenix, AZ 85001"].lot_sqft != original_lot

    def test_update_loads_cache_if_not_loaded(self, cache_manager, mock_repository):
        """Update should load cache if not already loaded."""
        assert not cache_manager.is_loaded
        assert mock_repository.load_count == 0

        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        assert cache_manager.is_loaded
        assert mock_repository.load_count == 1

    def test_multiple_updates_keep_dirty_flag(self, cache_manager):
        """Multiple updates should keep dirty flag set."""
        cache_manager.get_all()

        for i in range(5):
            enrichment = EnrichmentData(
                full_address=f"{i} Test St",
                lot_sqft=7000 + i,
            )
            cache_manager.update(f"{i} Test St", enrichment)

        assert cache_manager.is_dirty


# ============================================================================
# Save If Dirty Tests
# ============================================================================


class TestSaveIfDirty:
    """Tests for save_if_dirty() conditional save logic."""

    def test_save_if_dirty_returns_false_when_not_dirty(self, cache_manager, mock_repository):
        """save_if_dirty should return False when cache is clean."""
        cache_manager.get_all()
        assert mock_repository.save_count == 0

        result = cache_manager.save_if_dirty()

        assert result is False
        assert mock_repository.save_count == 0

    def test_save_if_dirty_returns_true_when_dirty(self, cache_manager, mock_repository):
        """save_if_dirty should return True when cache has changes."""
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        result = cache_manager.save_if_dirty()

        assert result is True
        assert mock_repository.save_count == 1

    def test_save_if_dirty_calls_repository_save(self, cache_manager, mock_repository):
        """save_if_dirty should call repository.save_all with cache data."""
        data = cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        cache_manager.save_if_dirty()

        assert mock_repository.last_saved_data is not None
        assert "999 Test St" in mock_repository.last_saved_data

    def test_save_if_dirty_resets_dirty_flag(self, cache_manager):
        """save_if_dirty should reset dirty flag after save."""
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)
        assert cache_manager.is_dirty

        cache_manager.save_if_dirty()

        assert not cache_manager.is_dirty

    def test_save_if_dirty_multiple_times_only_saves_once(self, cache_manager, mock_repository):
        """Calling save_if_dirty multiple times should only save once."""
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        result1 = cache_manager.save_if_dirty()
        result2 = cache_manager.save_if_dirty()
        result3 = cache_manager.save_if_dirty()

        assert result1 is True
        assert result2 is False
        assert result3 is False
        assert mock_repository.save_count == 1

    def test_save_if_dirty_returns_false_when_cache_not_loaded(
        self, cache_manager, mock_repository
    ):
        """save_if_dirty should return False if cache never loaded."""
        assert not cache_manager.is_loaded

        result = cache_manager.save_if_dirty()

        assert result is False
        assert mock_repository.save_count == 0


# ============================================================================
# Cache Invalidation Tests
# ============================================================================


class TestCacheInvalidation:
    """Tests for invalidate() method."""

    def test_invalidate_clears_cache(self, cache_manager):
        """invalidate should clear cached data."""
        cache_manager.get_all()
        assert cache_manager.is_loaded

        cache_manager.invalidate()

        assert not cache_manager.is_loaded
        assert cache_manager._cache is None

    def test_invalidate_resets_dirty_flag(self, cache_manager):
        """invalidate should reset dirty flag."""
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)
        assert cache_manager.is_dirty

        cache_manager.invalidate()

        assert not cache_manager.is_dirty

    def test_invalidate_forces_reload_on_next_get(self, cache_manager, mock_repository):
        """After invalidate, next get_all should reload from repository."""
        cache_manager.get_all()
        assert mock_repository.load_count == 1

        cache_manager.invalidate()
        cache_manager.get_all()

        assert mock_repository.load_count == 2

    def test_invalidate_discards_unsaved_changes(self, cache_manager):
        """invalidate should discard unsaved changes."""
        cache_manager.get_all()
        enrichment = EnrichmentData(
            full_address="999 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("999 Test St", enrichment)

        # Invalidate without saving
        cache_manager.invalidate()

        # Reload - change should be gone
        data = cache_manager.get_all()
        assert "999 Test St" not in data


# ============================================================================
# Integration Tests
# ============================================================================


class TestCachedManagerIntegration:
    """Integration tests with real JsonEnrichmentRepository."""

    def test_with_real_repository(self, tmp_path, enrichment_data_dict):
        """Test CachedDataManager with real JsonEnrichmentRepository."""
        import json

        # Create JSON file
        json_file = tmp_path / "enrichment_data.json"
        json_data = [
            {
                "full_address": addr,
                "lot_sqft": data.lot_sqft,
                "year_built": data.year_built,
                "garage_spaces": data.garage_spaces,
                "sewer_type": data.sewer_type,
            }
            for addr, data in enrichment_data_dict.items()
        ]
        json_file.write_text(json.dumps(json_data))

        # Create repository and cache manager
        repo = JsonEnrichmentRepository(json_file)
        cache = CachedDataManager(repo)

        # Load data (should read from file)
        data1 = cache.get_all()
        assert len(data1) == 2

        # Second load uses cache
        data2 = cache.get_all()
        assert data1 is data2

        # Modify and save
        enrichment = EnrichmentData(
            full_address="999 New St",
            lot_sqft=8000,
        )
        cache.update("999 New St", enrichment)
        assert cache.save_if_dirty()

        # Verify file was updated
        repo2 = JsonEnrichmentRepository(json_file)
        data3 = repo2.load_all()
        assert "999 New St" in data3

    def test_cache_reduces_io_operations(self, tmp_path, enrichment_data_dict):
        """Verify cache reduces disk I/O operations."""
        import json

        # Create JSON file
        json_file = tmp_path / "enrichment_data.json"
        json_data = [
            {
                "full_address": addr,
                "lot_sqft": data.lot_sqft,
                "year_built": data.year_built,
                "garage_spaces": data.garage_spaces,
                "sewer_type": data.sewer_type,
            }
            for addr, data in enrichment_data_dict.items()
        ]
        json_file.write_text(json.dumps(json_data))

        # Without cache: 3 loads = 3 file reads
        repo1 = JsonEnrichmentRepository(json_file)
        _ = repo1.load_all()
        _ = repo1.load_all()
        _ = repo1.load_all()
        # Each call reads from disk (inefficient)

        # With cache: 3 loads = 1 file read
        repo2 = JsonEnrichmentRepository(json_file)
        cache = CachedDataManager(repo2)
        data1 = cache.get_all()
        data2 = cache.get_all()
        data3 = cache.get_all()

        # All three calls use same cached data
        assert data1 is data2
        assert data2 is data3


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_cache(self, cache_manager, mock_repository):
        """Test behavior with empty enrichment data."""
        mock_repository._data = {}

        data = cache_manager.get_all()

        assert data == {}
        assert cache_manager.is_loaded

    def test_update_empty_cache(self, cache_manager, mock_repository):
        """Test updating an initially empty cache."""
        mock_repository._data = {}

        enrichment = EnrichmentData(
            full_address="123 Test St",
            lot_sqft=7000,
        )
        cache_manager.update("123 Test St", enrichment)

        data = cache_manager.get_all()
        assert "123 Test St" in data

    def test_save_empty_cache_does_nothing(self, cache_manager, mock_repository):
        """Saving an empty clean cache should do nothing."""
        mock_repository._data = {}
        cache_manager.get_all()

        result = cache_manager.save_if_dirty()

        assert result is False
        assert mock_repository.save_count == 0

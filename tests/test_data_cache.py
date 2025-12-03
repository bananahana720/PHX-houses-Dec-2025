"""Tests for PropertyDataCache singleton."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from phx_home_analysis.services.data_cache import PropertyDataCache


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before and after each test."""
    PropertyDataCache.reset()
    yield
    PropertyDataCache.reset()


@pytest.fixture
def temp_csv():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, newline=''
    ) as f:
        f.write("name,value\n")
        f.write("foo,1\n")
        f.write("bar,2\n")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


@pytest.fixture
def temp_json():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}], f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


def test_singleton_same_instance():
    """Test that PropertyDataCache returns the same instance."""
    cache1 = PropertyDataCache()
    cache2 = PropertyDataCache()

    assert cache1 is cache2


def test_csv_data_loaded(temp_csv):
    """Test that CSV data is loaded correctly."""
    cache = PropertyDataCache()
    data = cache.get_csv_data(temp_csv)

    assert len(data) == 2
    assert data[0]["name"] == "foo"
    assert data[0]["value"] == "1"
    assert data[1]["name"] == "bar"
    assert data[1]["value"] == "2"


def test_csv_data_cached(temp_csv):
    """Test that CSV data is cached and not reloaded."""
    cache = PropertyDataCache()

    # First load
    data1 = cache.get_csv_data(temp_csv)
    stats1 = cache.get_cache_stats()

    # Second load (should be cached)
    data2 = cache.get_csv_data(temp_csv)
    stats2 = cache.get_cache_stats()

    assert data1 is data2  # Same object reference
    assert stats1['csv_mtime'] == stats2['csv_mtime']


def test_csv_data_reloaded_on_mtime_change(temp_csv):
    """Test that CSV data is reloaded when file changes."""
    cache = PropertyDataCache()

    # First load
    cache.get_csv_data(temp_csv)

    # Modify file (wait to ensure mtime changes)
    time.sleep(0.01)
    with open(temp_csv, 'a', newline='') as f:
        f.write("baz,3\n")

    # Second load (should reload due to mtime change)
    data2 = cache.get_csv_data(temp_csv)

    assert len(data2) == 3  # Should have new row
    assert data2[2]["name"] == "baz"


def test_json_data_loaded(temp_json):
    """Test that JSON data is loaded correctly."""
    cache = PropertyDataCache()
    data = cache.get_enrichment_data(temp_json)

    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "test1"


def test_json_data_cached(temp_json):
    """Test that JSON data is cached and not reloaded."""
    cache = PropertyDataCache()

    # First load
    data1 = cache.get_enrichment_data(temp_json)
    stats1 = cache.get_cache_stats()

    # Second load (should be cached)
    data2 = cache.get_enrichment_data(temp_json)
    stats2 = cache.get_cache_stats()

    assert data1 is data2  # Same object reference
    assert stats1['json_mtime'] == stats2['json_mtime']


def test_invalidate_clears_cache(temp_csv, temp_json):
    """Test that invalidate() clears all cached data."""
    cache = PropertyDataCache()

    # Load both files
    cache.get_csv_data(temp_csv)
    cache.get_enrichment_data(temp_json)

    stats_before = cache.get_cache_stats()
    assert stats_before['csv_cached'] is True
    assert stats_before['json_cached'] is True

    # Invalidate
    cache.invalidate()

    stats_after = cache.get_cache_stats()
    assert stats_after['csv_cached'] is False
    assert stats_after['json_cached'] is False


def test_cache_stats(temp_csv):
    """Test that get_cache_stats() returns correct information."""
    cache = PropertyDataCache()

    # Before loading
    stats = cache.get_cache_stats()
    assert stats['csv_cached'] is False
    assert stats['csv_rows'] == 0

    # After loading
    cache.get_csv_data(temp_csv)
    stats = cache.get_cache_stats()
    assert stats['csv_cached'] is True
    assert stats['csv_rows'] == 2
    assert stats['csv_path'] == str(temp_csv)


def test_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    cache = PropertyDataCache()

    with pytest.raises(FileNotFoundError):
        cache.get_csv_data(Path("nonexistent.csv"))

    with pytest.raises(FileNotFoundError):
        cache.get_enrichment_data(Path("nonexistent.json"))


def test_different_paths_cached_separately(temp_csv):
    """Test that different file paths are cached separately."""
    # Create a second temp CSV
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, newline=''
    ) as f:
        f.write("name,value\n")
        f.write("different,99\n")
        temp_csv2 = Path(f.name)

    try:
        cache = PropertyDataCache()

        # Load first file
        data1 = cache.get_csv_data(temp_csv)
        assert len(data1) == 2

        # Load second file (should replace cache)
        data2 = cache.get_csv_data(temp_csv2)
        assert len(data2) == 1
        assert data2[0]["value"] == "99"

        # Load first file again (should reload from disk)
        data3 = cache.get_csv_data(temp_csv)
        assert len(data3) == 2
        assert data3[0]["name"] == "foo"

    finally:
        temp_csv2.unlink()


def test_reset_clears_singleton():
    """Test that reset() clears the singleton instance."""
    cache1 = PropertyDataCache()

    PropertyDataCache.reset()

    cache2 = PropertyDataCache()

    # Should be different instances after reset
    assert cache1 is not cache2

# PropertyDataCache Usage Guide

## Overview

`PropertyDataCache` is a thread-safe singleton service that caches CSV and JSON property data files to eliminate redundant file I/O operations during pipeline runs.

## Problem Statement

Before implementing the cache, property data files were loaded 3-5 times per pipeline run:

1. `scripts/phx_home_analyzer.py` - loads CSV + JSON
2. `scripts/deal_sheets/generator.py` - reloads both files
3. `scripts/quality_check.py` - loads JSON again

This redundant I/O caused unnecessary disk reads and slower pipeline execution.

## Solution

The `PropertyDataCache` singleton caches file contents with automatic mtime-based invalidation:

- Files are loaded once and cached in memory
- Subsequent reads return cached data instantly
- Files are automatically reloaded if modified (mtime changes)
- Thread-safe for concurrent access

## Usage

### Basic Usage

```python
from pathlib import Path
from phx_home_analysis.services.data_cache import PropertyDataCache

# Get singleton instance
cache = PropertyDataCache()

# Load CSV data (cached automatically)
csv_data = cache.get_csv_data(Path("data/phx_homes.csv"))
# Returns: list[dict[str, Any]]

# Load enrichment JSON (cached automatically)
enrichment = cache.get_enrichment_data(Path("data/enrichment_data.json"))
# Returns: dict[str, Any] | list[dict[str, Any]]
```

### Cache Invalidation

```python
# Force reload on next access
cache.invalidate()

# Or reset singleton (testing only)
PropertyDataCache.reset()
```

### Cache Statistics

```python
stats = cache.get_cache_stats()
print(stats)
# {
#     'csv_cached': True,
#     'json_cached': True,
#     'csv_path': 'data/phx_homes.csv',
#     'json_path': 'data/enrichment_data.json',
#     'csv_mtime': 1234567890.0,
#     'json_mtime': 1234567890.0,
#     'csv_rows': 50,
#     'json_entries': 50
# }
```

## Integration Examples

### Before (Direct File I/O)

```python
import csv

def load_listings(csv_path: str) -> list[dict]:
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
```

### After (Using Cache)

```python
from pathlib import Path
from phx_home_analysis.services.data_cache import PropertyDataCache

def load_listings(csv_path: str) -> list[dict]:
    cache = PropertyDataCache()
    return cache.get_csv_data(Path(csv_path))
```

## Performance Benefits

Run the benchmark to see performance improvements:

```bash
python scripts/benchmark_cache.py
```

Expected results for typical property datasets:
- **Speedup**: 10-50x faster for subsequent loads
- **Time saved**: ~0.1-0.5s per pipeline run
- **Memory overhead**: Minimal (data already loaded by first script)

## Thread Safety

The cache is fully thread-safe:

```python
import threading
from phx_home_analysis.services.data_cache import PropertyDataCache

def worker():
    cache = PropertyDataCache()
    data = cache.get_csv_data(Path("data/phx_homes.csv"))
    # Safe to call from multiple threads

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Testing

```bash
# Run cache tests
uv run pytest tests/test_data_cache.py -v

# Run with coverage
uv run pytest tests/test_data_cache.py --cov=phx_home_analysis.services.data_cache
```

## Implementation Details

### Singleton Pattern

```python
class PropertyDataCache:
    _instance = None
    _lock_class = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock_class:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance
```

### Automatic Invalidation

Files are reloaded when:
1. File path changes
2. File mtime changes (detected via `Path.stat().st_mtime`)
3. `invalidate()` is called

### Cache Keys

The cache uses file paths as keys:
- Different paths are treated as different files
- Loading a different file replaces the cache for that slot (CSV or JSON)

## Migration Guide

### Step 1: Import the cache

```python
from phx_home_analysis.services.data_cache import PropertyDataCache
```

### Step 2: Replace direct file I/O

**CSV files:**
```python
# Before
with open(csv_path) as f:
    reader = csv.DictReader(f)
    data = [dict(row) for row in reader]

# After
cache = PropertyDataCache()
data = cache.get_csv_data(Path(csv_path))
```

**JSON files:**
```python
# Before
with open(json_path) as f:
    data = json.load(f)

# After
cache = PropertyDataCache()
data = cache.get_enrichment_data(Path(json_path))
```

### Step 3: Update tests

Add `reset_singleton` fixture if needed:

```python
@pytest.fixture(autouse=True)
def reset_singleton():
    PropertyDataCache.reset()
    yield
    PropertyDataCache.reset()
```

## Files Modified

The following scripts now use `PropertyDataCache`:

- `scripts/phx_home_analyzer.py`
  - `load_listings()` - CSV loading
  - `enrich_from_manual_data()` - JSON loading

- `scripts/deal_sheets/data_loader.py`
  - `load_ranked_csv()` - CSV loading
  - `load_enrichment_json()` - JSON loading

- `scripts/quality_check.py`
  - `load_property_data()` - CSV and JSON loading

## API Reference

### `PropertyDataCache.get_csv_data(csv_path: Path) -> list[dict[str, Any]]`

Load CSV data with automatic caching.

**Parameters:**
- `csv_path`: Path to CSV file

**Returns:**
- List of dictionaries (one per row)

**Raises:**
- `FileNotFoundError`: If CSV file doesn't exist
- `ValueError`: If CSV is malformed

### `PropertyDataCache.get_enrichment_data(json_path: Path) -> dict | list`

Load JSON data with automatic caching.

**Parameters:**
- `json_path`: Path to JSON file

**Returns:**
- Dictionary or list (depends on JSON structure)

**Raises:**
- `FileNotFoundError`: If JSON file doesn't exist
- `json.JSONDecodeError`: If JSON is malformed

### `PropertyDataCache.invalidate() -> None`

Force cache invalidation for all cached data.

### `PropertyDataCache.get_cache_stats() -> dict[str, Any]`

Get cache statistics for debugging/monitoring.

**Returns:**
- Dictionary with cache statistics

### `PropertyDataCache.reset() -> None`

Reset singleton instance (for testing only).

**Warning:** Only use in tests. Production code should not reset the singleton.

## Best Practices

1. **Always use Path objects**: Convert strings to `Path` objects before calling cache methods
2. **Don't reset in production**: Only use `reset()` in test fixtures
3. **Check file existence**: Handle `FileNotFoundError` when loading data
4. **Monitor cache stats**: Use `get_cache_stats()` for debugging
5. **Invalidate when needed**: Call `invalidate()` after manual file modifications

## Troubleshooting

### Cache not invalidating after file changes

**Problem:** File modified but cache still returns old data.

**Solution:** Check file mtime. On some filesystems, mtime may not update immediately. Call `invalidate()` manually if needed.

### Different data returned from same file

**Problem:** Same file returns different data on different calls.

**Solution:** Ensure file path is consistent (absolute vs relative). Use `Path.resolve()` to normalize paths.

### Memory usage concerns

**Problem:** Worried about memory usage with large files.

**Solution:** Cache only stores data in memory once. Multiple calls don't duplicate data. If memory is a concern, call `invalidate()` to free memory.

## See Also

- `tests/test_data_cache.py` - Comprehensive test suite
- `scripts/benchmark_cache.py` - Performance benchmark
- `src/phx_home_analysis/services/data_cache.py` - Implementation

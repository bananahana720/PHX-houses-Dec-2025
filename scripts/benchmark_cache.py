#!/usr/bin/env python
"""Benchmark data cache performance improvement.

Demonstrates the performance benefit of using PropertyDataCache by
simulating multiple pipeline runs with and without caching.

Usage:
    python scripts/benchmark_cache.py
"""

import csv
import json
import time
from pathlib import Path

# Requires: uv pip install -e .
from phx_home_analysis.services.data_cache import PropertyDataCache


def load_csv_direct(csv_path: Path) -> list[dict]:
    """Load CSV without cache (traditional approach)."""
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_json_direct(json_path: Path) -> dict | list:
    """Load JSON without cache (traditional approach)."""
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)


def load_csv_cached(csv_path: Path) -> list[dict]:
    """Load CSV with cache."""
    cache = PropertyDataCache()
    return cache.get_csv_data(csv_path)


def load_json_cached(json_path: Path) -> dict | list:
    """Load JSON with cache."""
    cache = PropertyDataCache()
    return cache.get_enrichment_data(json_path)


def benchmark_direct(csv_path: Path, json_path: Path, iterations: int = 3) -> float:
    """Benchmark direct file I/O (no cache)."""
    start = time.perf_counter()

    for _ in range(iterations):
        load_csv_direct(csv_path)
        load_json_direct(json_path)

    end = time.perf_counter()
    return end - start


def benchmark_cached(csv_path: Path, json_path: Path, iterations: int = 3) -> float:
    """Benchmark cached file I/O."""
    # Reset cache to ensure clean state
    PropertyDataCache.reset()

    start = time.perf_counter()

    for _ in range(iterations):
        load_csv_cached(csv_path)
        load_json_cached(json_path)

    end = time.perf_counter()
    return end - start


def main():
    """Run benchmark and display results."""
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "phx_homes.csv"
    json_path = data_dir / "enrichment_data.json"

    # Check if files exist
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        return 1

    if not json_path.exists():
        print(f"ERROR: JSON file not found: {json_path}")
        return 1

    # Get file sizes
    csv_size = csv_path.stat().st_size / 1024  # KB
    json_size = json_path.stat().st_size / 1024  # KB

    print("=" * 70)
    print("PropertyDataCache Performance Benchmark")
    print("=" * 70)
    print(f"CSV file:  {csv_path.name} ({csv_size:.1f} KB)")
    print(f"JSON file: {json_path.name} ({json_size:.1f} KB)")
    print()

    # Run benchmarks
    iterations = 5
    print(f"Simulating {iterations} pipeline runs (CSV + JSON load each run)...\n")

    print("[1/2] Direct file I/O (no cache)...")
    direct_time = benchmark_direct(csv_path, json_path, iterations)
    print(f"      Total: {direct_time:.4f}s | Per run: {direct_time/iterations:.4f}s")

    print("\n[2/2] Cached file I/O (PropertyDataCache)...")
    cached_time = benchmark_cached(csv_path, json_path, iterations)
    print(f"      Total: {cached_time:.4f}s | Per run: {cached_time/iterations:.4f}s")

    # Calculate improvement
    speedup = direct_time / cached_time if cached_time > 0 else 0
    time_saved = direct_time - cached_time
    percent_faster = ((direct_time - cached_time) / direct_time * 100) if direct_time > 0 else 0

    print()
    print("=" * 70)
    print("Results Summary")
    print("=" * 70)
    print(f"Speedup:        {speedup:.2f}x faster")
    print(f"Time saved:     {time_saved:.4f}s ({percent_faster:.1f}% reduction)")
    print(f"Cache stats:    {PropertyDataCache().get_cache_stats()}")
    print()

    # Show cache statistics
    cache = PropertyDataCache()
    stats = cache.get_cache_stats()

    if stats['csv_cached']:
        print(f"CSV cached:     {stats['csv_rows']} rows")
    if stats['json_cached']:
        print(f"JSON cached:    {stats['json_entries']} entries")

    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())

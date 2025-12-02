"""Singleton data cache with mtime-based invalidation and schema versioning.

This module provides a thread-safe singleton cache for property data files
(CSV and JSON) to eliminate redundant file I/O operations during pipeline runs.

Features:
- Automatic mtime-based cache invalidation
- Schema version detection and validation on JSON load
- Warning logs for outdated schema versions
- Optional auto-migration support

Usage:
    from phx_home_analysis.services.data_cache import PropertyDataCache

    cache = PropertyDataCache()

    # Load CSV data (cached automatically)
    csv_data = cache.get_csv_data(Path("data/phx_homes.csv"))

    # Load enrichment JSON (cached automatically, schema version checked)
    enrichment = cache.get_enrichment_data(Path("data/enrichment_data.json"))

    # Force reload if needed
    cache.invalidate()
    csv_data = cache.get_csv_data(csv_path)

    # Clear singleton (for testing only)
    PropertyDataCache.reset()

Thread Safety:
    All public methods are thread-safe using threading.Lock.

Cache Invalidation:
    Files are automatically reloaded if their mtime changes.
    Call invalidate() to force reload on next access.

Schema Versioning:
    On JSON load, the schema version is detected and logged.
    If version is outdated, a warning is logged with migration instructions.
"""

import csv
import json
import logging
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PropertyDataCache:
    """Thread-safe singleton cache for property data files.

    Caches CSV and JSON property data with automatic mtime-based invalidation.
    Reduces redundant file I/O when multiple scripts access the same data files.

    Attributes:
        _instance: Singleton instance (class-level)
        _csv_data: Cached CSV data as list of dicts
        _enrichment_data: Cached enrichment JSON as dict/list
        _csv_mtime: Last modified time of cached CSV file
        _json_mtime: Last modified time of cached JSON file
        _csv_path: Path to currently cached CSV file
        _json_path: Path to currently cached JSON file
        _lock: Thread synchronization lock
    """

    _instance: Optional['PropertyDataCache'] = None
    _lock_class = threading.Lock()  # Class-level lock for __new__
    _initialized: bool  # Instance variable (set in __new__)

    def __new__(cls) -> 'PropertyDataCache':
        """Create or return singleton instance (thread-safe).

        Returns:
            Singleton PropertyDataCache instance
        """
        if cls._instance is None:
            with cls._lock_class:
                # Double-check pattern for thread safety
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        """Initialize cache state (only runs once due to singleton pattern)."""
        if self._initialized:
            return

        # Cache storage
        self._csv_data: list[dict[str, Any]] | None = None
        self._enrichment_data: dict[str, Any] | list[dict[str, Any]] | None = None

        # Modification time tracking
        self._csv_mtime: float = 0.0
        self._json_mtime: float = 0.0

        # Path tracking (to detect path changes)
        self._csv_path: Path | None = None
        self._json_path: Path | None = None

        # Instance-level lock for cache operations
        self._lock = threading.Lock()

        self._initialized = True

    def get_csv_data(self, csv_path: Path) -> list[dict[str, Any]]:
        """Get CSV data, reloading if file changed or path changed.

        Args:
            csv_path: Path to CSV file to load

        Returns:
            List of dictionaries representing CSV rows

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV file is malformed
        """
        with self._lock:
            # Convert to Path object if string
            csv_path = Path(csv_path)

            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

            # Get current mtime
            current_mtime = csv_path.stat().st_mtime

            # Check if reload needed (file changed, path changed, or not cached)
            needs_reload = (
                self._csv_data is None
                or self._csv_path != csv_path
                or current_mtime != self._csv_mtime
            )

            if needs_reload:
                # Load CSV data
                csv_data = []
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        csv_data.append(dict(row))

                # Update cache
                self._csv_data = csv_data
                self._csv_mtime = current_mtime
                self._csv_path = csv_path

            assert self._csv_data is not None  # Guaranteed after reload
            return self._csv_data

    def get_enrichment_data(
        self,
        json_path: Path,
        check_schema: bool = True,
        auto_migrate: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Get enrichment JSON, reloading if file changed or path changed.

        On load, checks the schema version and logs warnings if outdated.
        Optionally auto-migrates to the current schema version.

        Args:
            json_path: Path to enrichment JSON file to load
            check_schema: If True, check schema version and log warnings
            auto_migrate: If True, auto-migrate outdated schemas (writes to file)

        Returns:
            Enrichment data (dict or list depending on file format)

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON file is malformed
        """
        with self._lock:
            # Convert to Path object if string
            json_path = Path(json_path)

            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_path}")

            # Get current mtime
            current_mtime = json_path.stat().st_mtime

            # Check if reload needed (file changed, path changed, or not cached)
            needs_reload = (
                self._enrichment_data is None
                or self._json_path != json_path
                or current_mtime != self._json_mtime
            )

            if needs_reload:
                # Load JSON data
                with open(json_path, encoding='utf-8') as f:
                    enrichment_data = json.load(f)

                # Check schema version if enabled
                if check_schema:
                    enrichment_data = self._check_and_migrate_schema(
                        enrichment_data, json_path, auto_migrate
                    )

                # Update cache
                self._enrichment_data = enrichment_data
                self._json_mtime = current_mtime
                self._json_path = json_path

            assert self._enrichment_data is not None  # Guaranteed after reload
            return self._enrichment_data

    def _check_and_migrate_schema(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        json_path: Path,
        auto_migrate: bool,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Check schema version and optionally migrate.

        Args:
            data: Loaded JSON data
            json_path: Path to JSON file (for migration write-back)
            auto_migrate: If True, migrate and write back to file

        Returns:
            Data (potentially migrated)
        """
        try:
            from phx_home_analysis.services.schema import (
                SchemaMigrator,
                SchemaVersion,
            )

            migrator = SchemaMigrator()
            detected_version = migrator.get_version(data)
            current_version = SchemaVersion.current()

            if detected_version < current_version:
                logger.warning(
                    f"Schema version {detected_version.value} is outdated "
                    f"(current: {current_version.value}). "
                    f"Run: python scripts/migrate_schema.py --file {json_path}"
                )

                if auto_migrate:
                    logger.info(f"Auto-migrating schema to {current_version.value}")
                    data = migrator.migrate(data, current_version)

                    # Write back to file
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    logger.info(f"Migrated schema written to {json_path}")

            elif detected_version == current_version:
                logger.debug(f"Schema version {detected_version.value} is current")

        except ImportError:
            logger.debug("Schema versioning module not available, skipping check")
        except Exception as e:
            logger.warning(f"Schema version check failed: {e}")

        return data

    def invalidate(self) -> None:
        """Force cache invalidation for all cached data.

        Next call to get_csv_data() or get_enrichment_data() will reload from disk.
        """
        with self._lock:
            self._csv_data = None
            self._enrichment_data = None
            self._csv_mtime = 0.0
            self._json_mtime = 0.0
            self._csv_path = None
            self._json_path = None

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for debugging/monitoring.

        Returns:
            Dictionary with cache statistics including:
            - csv_cached: Whether CSV data is cached
            - json_cached: Whether JSON data is cached
            - csv_path: Path to cached CSV file (or None)
            - json_path: Path to cached JSON file (or None)
            - csv_mtime: Last modified time of cached CSV
            - json_mtime: Last modified time of cached JSON
        """
        with self._lock:
            return {
                'csv_cached': self._csv_data is not None,
                'json_cached': self._enrichment_data is not None,
                'csv_path': str(self._csv_path) if self._csv_path else None,
                'json_path': str(self._json_path) if self._json_path else None,
                'csv_mtime': self._csv_mtime,
                'json_mtime': self._json_mtime,
                'csv_rows': len(self._csv_data) if self._csv_data else 0,
                'json_entries': (
                    len(self._enrichment_data)
                    if self._enrichment_data is not None
                    else 0
                ),
            }

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing only).

        Warning:
            This method is intended for testing only. Using it in production
            code can lead to unexpected behavior if multiple code paths expect
            the same singleton instance.
        """
        with cls._lock_class:
            cls._instance = None

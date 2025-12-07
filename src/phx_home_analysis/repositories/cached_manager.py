"""Centralized cache manager for property enrichment data.

This module provides a caching layer that sits between the pipeline and the
EnrichmentRepository, eliminating redundant JSON file reads during pipeline
execution. The cache supports explicit invalidation for data changes and
provides dirty-flag tracking for conditional saves.

Typical Usage:
    >>> from phx_home_analysis.repositories import CachedDataManager, JsonEnrichmentRepository
    >>>
    >>> repo = JsonEnrichmentRepository("data/enrichment_data.json")
    >>> cache = CachedDataManager(repo)
    >>>
    >>> # First call loads from disk
    >>> data = cache.get_all()
    >>>
    >>> # Subsequent calls use cache (no disk I/O)
    >>> data = cache.get_all()
    >>>
    >>> # Update cache entry
    >>> cache.update("123 Main St", enrichment_data)
    >>>
    >>> # Save only if changed
    >>> if cache.save_if_dirty():
    ...     print("Changes saved to disk")
"""

from ..domain.entities import EnrichmentData
from .base import EnrichmentRepository


class CachedDataManager:
    """Centralized cache for property data with invalidation support.

    Provides single-load semantics for pipeline runs while supporting
    explicit invalidation when data changes. Implements a write-through
    cache pattern with dirty-flag tracking for conditional persistence.

    The cache eliminates redundant JSON loads in the pipeline orchestrator,
    which previously called load_all() multiple times per run (lines 228, 233,
    300-301 in orchestrator.py), causing unnecessary I/O overhead for 300+
    properties.

    Attributes:
        _repository: Underlying EnrichmentRepository for disk persistence
        _cache: In-memory cache of enrichment data, None if not loaded
        _dirty: Flag indicating cache has unsaved changes

    Example:
        >>> repo = JsonEnrichmentRepository("data/enrichment_data.json")
        >>> cache = CachedDataManager(repo)
        >>>
        >>> # Load all data (disk I/O)
        >>> data1 = cache.get_all()
        >>>
        >>> # Use cache (no disk I/O)
        >>> data2 = cache.get_all()
        >>> assert data1 is data2  # Same object reference
        >>>
        >>> # Update cache
        >>> cache.update("123 Main St", enrichment_data)
        >>>
        >>> # Conditionally save
        >>> saved = cache.save_if_dirty()  # Returns True if saved
    """

    def __init__(self, repository: EnrichmentRepository):
        """Initialize cached data manager.

        Args:
            repository: EnrichmentRepository instance for disk persistence
        """
        self._repository = repository
        self._cache: dict[str, EnrichmentData] | None = None
        self._dirty = False

    def get_all(self, force_reload: bool = False) -> dict[str, EnrichmentData]:
        """Get all enrichment data, using cache if available.

        Returns cached data if available, otherwise loads from repository.
        Provides force_reload option to bypass cache and reload from disk.

        Args:
            force_reload: If True, bypass cache and reload from disk.
                         Default is False (use cache if available).

        Returns:
            Dictionary mapping full_address to EnrichmentData objects.
            Returns the same object reference on subsequent calls unless
            force_reload=True.

        Example:
            >>> cache = CachedDataManager(repo)
            >>> data1 = cache.get_all()  # Loads from disk
            >>> data2 = cache.get_all()  # Uses cache
            >>> assert data1 is data2    # Same reference
            >>>
            >>> data3 = cache.get_all(force_reload=True)  # Reloads from disk
            >>> assert data1 is not data3  # Different reference
        """
        if self._cache is None or force_reload:
            self._cache = self._repository.load_all()
            self._dirty = False
        return self._cache

    def update(self, address: str, data: EnrichmentData) -> None:
        """Update cache entry (marks dirty for eventual save).

        Updates or adds an enrichment entry in the cache. Marks the cache
        as dirty to trigger save on next save_if_dirty() call. If cache
        is not loaded, automatically loads it first.

        Args:
            address: Full address key for the enrichment entry
            data: EnrichmentData object to store

        Example:
            >>> cache = CachedDataManager(repo)
            >>> enrichment = EnrichmentData(full_address="123 Main St", lot_sqft=9500)
            >>> cache.update("123 Main St", enrichment)
            >>> assert cache.save_if_dirty() is True  # Has changes to save
        """
        if self._cache is None:
            self.get_all()

        # Cache should never be None after get_all(), but type checker needs this
        if self._cache is not None:
            self._cache[address] = data
            self._dirty = True

    def save_if_dirty(self) -> bool:
        """Save to disk if cache has changes. Returns True if saved.

        Conditionally persists cache to disk only if changes have been made
        via update() calls. Resets dirty flag after successful save.

        Returns:
            True if data was saved to disk, False if no changes or cache empty.

        Example:
            >>> cache = CachedDataManager(repo)
            >>> data = cache.get_all()
            >>>
            >>> # No changes yet
            >>> assert cache.save_if_dirty() is False
            >>>
            >>> # Make a change
            >>> cache.update("123 Main St", enrichment_data)
            >>>
            >>> # Now it saves
            >>> assert cache.save_if_dirty() is True
            >>>
            >>> # Second call doesn't save (not dirty)
            >>> assert cache.save_if_dirty() is False
        """
        if self._dirty and self._cache is not None:
            self._repository.save_all(self._cache)
            self._dirty = False
            return True
        return False

    def invalidate(self) -> None:
        """Clear cache, forcing reload on next access.

        Invalidates the cache and resets dirty flag. Next call to get_all()
        will reload data from disk. Useful for testing or when external
        processes modify the data file.

        Example:
            >>> cache = CachedDataManager(repo)
            >>> data1 = cache.get_all()  # Loads from disk
            >>>
            >>> # External process modifies data file
            >>> external_modify_data_file()
            >>>
            >>> cache.invalidate()
            >>> data2 = cache.get_all()  # Reloads from disk with new data
            >>> assert data1 is not data2
        """
        self._cache = None
        self._dirty = False

    @property
    def is_loaded(self) -> bool:
        """Check if cache has been loaded.

        Returns:
            True if cache contains data, False if cache is empty/uninitialized.
        """
        return self._cache is not None

    @property
    def is_dirty(self) -> bool:
        """Check if cache has unsaved changes.

        Returns:
            True if cache has been modified since last save, False otherwise.
        """
        return self._dirty

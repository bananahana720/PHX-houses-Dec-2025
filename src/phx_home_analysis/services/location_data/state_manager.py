"""State manager for location data extraction with crash recovery.

Tracks extraction progress across multiple data sources (crime, schools, flood, etc.)
with support for ZIP-level batching, per-source completion, and permanent failure tracking.

State is persisted to JSON for crash recovery and incremental processing.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LocationExtractionState:
    """Tracks extraction progress for crash recovery.

    Supports three levels of granularity:
    1. Property-level completion (all sources complete)
    2. Per-source completion (specific extractors)
    3. ZIP-level completion (for batch sources like crime, census)
    """

    # Global completion
    completed_properties: set[str] = field(default_factory=set)  # By property hash
    failed_properties: set[str] = field(default_factory=set)

    # Per-source completion (for partial retries)
    source_completed: dict[str, set[str]] = field(default_factory=dict)
    # e.g., {"crime": {"ef7cd95f", "a1b2c3d4"}, "flood": {"ef7cd95f"}}

    # ZIP-level completion (for batch sources like crime, census)
    completed_zips: dict[str, set[str]] = field(default_factory=dict)
    # e.g., {"crime": {"85306", "85023"}, "census": {"85306"}}

    # Permanent failures (don't retry)
    permanent_failures: dict[str, set[str]] = field(default_factory=dict)

    # Metadata
    last_updated: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "completed_properties": list(self.completed_properties),
            "failed_properties": list(self.failed_properties),
            "source_completed": {k: list(v) for k, v in self.source_completed.items()},
            "completed_zips": {k: list(v) for k, v in self.completed_zips.items()},
            "permanent_failures": {k: list(v) for k, v in self.permanent_failures.items()},
            "last_updated": self.last_updated,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LocationExtractionState":
        """Load from dictionary."""
        return cls(
            completed_properties=set(data.get("completed_properties", [])),
            failed_properties=set(data.get("failed_properties", [])),
            source_completed={k: set(v) for k, v in data.get("source_completed", {}).items()},
            completed_zips={k: set(v) for k, v in data.get("completed_zips", {}).items()},
            permanent_failures={k: set(v) for k, v in data.get("permanent_failures", {}).items()},
            last_updated=data.get("last_updated", ""),
            version=data.get("version", "1.0.0"),
        )


class LocationStateManager:
    """Manages extraction state with atomic saves and recovery.

    Provides thread-safe state persistence with atomic writes to prevent
    corruption during crashes or interruptions.

    Example:
        manager = LocationStateManager()
        if not manager.is_property_completed(prop_hash, "crime"):
            # Extract crime data
            manager.mark_source_completed(prop_hash, "crime")
            manager.save()
    """

    STATE_FILE = "data/location_extraction_state.json"

    def __init__(self, state_file: Path | str | None = None):
        """Initialize state manager.

        Args:
            state_file: Path to state JSON file. Uses default if None.
        """
        self.state_file = Path(state_file or self.STATE_FILE)
        self._state = self._load()

    def _load(self) -> LocationExtractionState:
        """Load state from file or create new.

        Returns:
            LocationExtractionState instance (empty if file doesn't exist)
        """
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                state = LocationExtractionState.from_dict(data)
                logger.info(
                    "Loaded state: %d properties completed, %d failed",
                    len(state.completed_properties),
                    len(state.failed_properties),
                )
                return state
            except Exception as e:
                logger.warning("Failed to load state: %s, starting fresh", e)
        return LocationExtractionState()

    def save(self) -> None:
        """Atomic save state to file.

        Uses temporary file + rename for atomic write to prevent
        corruption if interrupted mid-write.
        """
        self._state.last_updated = datetime.now().astimezone().isoformat()

        # Atomic write
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(
            json.dumps(self._state.to_dict(), indent=2),
            encoding="utf-8",
        )
        temp_file.replace(self.state_file)
        logger.debug("Saved state to disk")

    def is_property_completed(self, prop_hash: str, source: str | None = None) -> bool:
        """Check if property extraction is complete.

        Args:
            prop_hash: Property hash identifier
            source: Optional specific source to check. If None, checks global completion.

        Returns:
            True if property (or source) was previously completed
        """
        if source:
            return prop_hash in self._state.source_completed.get(source, set())
        return prop_hash in self._state.completed_properties

    def is_zip_completed(self, zip_code: str, source: str) -> bool:
        """Check if ZIP-level data is already extracted.

        Args:
            zip_code: ZIP code to check
            source: Data source name (e.g., "crime", "census")

        Returns:
            True if ZIP data was previously extracted for this source
        """
        return zip_code in self._state.completed_zips.get(source, set())

    def mark_source_completed(self, prop_hash: str, source: str) -> None:
        """Mark a source as completed for a property.

        Args:
            prop_hash: Property hash identifier
            source: Data source name (e.g., "crime", "flood")
        """
        if source not in self._state.source_completed:
            self._state.source_completed[source] = set()
        self._state.source_completed[source].add(prop_hash)

    def mark_zip_completed(self, zip_code: str, source: str) -> None:
        """Mark ZIP-level data as completed.

        Args:
            zip_code: ZIP code
            source: Data source name (e.g., "crime", "census")
        """
        if source not in self._state.completed_zips:
            self._state.completed_zips[source] = set()
        self._state.completed_zips[source].add(zip_code)

    def mark_property_completed(self, prop_hash: str) -> None:
        """Mark property as fully completed (all sources).

        Args:
            prop_hash: Property hash identifier
        """
        self._state.completed_properties.add(prop_hash)
        self._state.failed_properties.discard(prop_hash)

    def mark_property_failed(self, prop_hash: str) -> None:
        """Mark property as failed.

        Args:
            prop_hash: Property hash identifier
        """
        self._state.failed_properties.add(prop_hash)

    def mark_permanent_failure(self, prop_hash: str, source: str, reason: str) -> None:
        """Mark as permanent failure (don't retry).

        Args:
            prop_hash: Property hash identifier
            source: Data source name
            reason: Reason for permanent failure
        """
        if source not in self._state.permanent_failures:
            self._state.permanent_failures[source] = set()
        self._state.permanent_failures[source].add(prop_hash)
        logger.warning("Permanent failure for %s from %s: %s", prop_hash, source, reason)

    def is_permanent_failure(self, prop_hash: str, source: str) -> bool:
        """Check if marked as permanent failure.

        Args:
            prop_hash: Property hash identifier
            source: Data source name

        Returns:
            True if marked as permanent failure
        """
        return prop_hash in self._state.permanent_failures.get(source, set())

    def reset(self) -> None:
        """Reset all state (for --fresh flag)."""
        self._state = LocationExtractionState()
        if self.state_file.exists():
            self.state_file.unlink()
        logger.info("State reset")

    @property
    def completed_count(self) -> int:
        """Get count of completed properties."""
        return len(self._state.completed_properties)

    @property
    def failed_count(self) -> int:
        """Get count of failed properties."""
        return len(self._state.failed_properties)

    def get_pending_count(self, total_properties: int) -> int:
        """Get count of properties not yet processed.

        Args:
            total_properties: Total number of properties to process

        Returns:
            Number of properties not in completed or failed sets
        """
        processed = len(self._state.completed_properties) + len(self._state.failed_properties)
        return max(0, total_properties - processed)

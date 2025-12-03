"""State persistence manager for image extraction operations.

Provides resumable extraction by tracking completed and failed properties.
State is persisted to JSON for crash recovery and incremental processing.

Security:
    Uses atomic file writes to prevent corruption from crashes/interrupts.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionState:
    """Persistent state for resumable extraction.

    Tracks which properties have been processed (successfully or failed)
    to enable resumption of interrupted extraction runs.

    Attributes:
        completed_properties: Set of addresses that completed successfully
        failed_properties: Set of addresses that failed
        property_last_checked: Dict mapping address -> ISO datetime when last processed
        last_updated: ISO timestamp of last state modification
    """

    completed_properties: set[str] = field(default_factory=set)
    failed_properties: set[str] = field(default_factory=set)
    property_last_checked: dict[str, str] = field(default_factory=dict)
    last_updated: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation
        """
        return {
            "completed_properties": list(self.completed_properties),
            "failed_properties": list(self.failed_properties),
            "property_last_checked": self.property_last_checked,
            "last_updated": self.last_updated or datetime.now().astimezone().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionState":
        """Load from dictionary.

        Args:
            data: Dictionary from JSON

        Returns:
            ExtractionState instance
        """
        return cls(
            completed_properties=set(data.get("completed_properties", [])),
            failed_properties=set(data.get("failed_properties", [])),
            property_last_checked=data.get("property_last_checked", {}),
            last_updated=data.get("last_updated"),
        )

    def record_property_checked(self, address: str) -> None:
        """Record when a property was last checked for images.

        Updates the timestamp regardless of whether new images were found.

        Args:
            address: Full property address
        """
        self.property_last_checked[address] = datetime.now().astimezone().isoformat()

    def get_property_last_checked(self, address: str) -> str | None:
        """Get the last time a property was checked.

        Args:
            address: Full property address

        Returns:
            ISO datetime string or None if never checked
        """
        return self.property_last_checked.get(address)

    def get_stale_properties(self, max_age_days: int = 7) -> list[str]:
        """Get properties not checked within the specified period.

        Args:
            max_age_days: Maximum age in days before considered stale

        Returns:
            List of addresses that are stale
        """
        stale = []
        now = datetime.now().astimezone()

        for address in self.completed_properties:
            last_checked = self.property_last_checked.get(address)
            if not last_checked:
                stale.append(address)
                continue

            try:
                checked_dt = datetime.fromisoformat(last_checked)
                age_days = (now - checked_dt).days
                if age_days > max_age_days:
                    stale.append(address)
            except (ValueError, TypeError):
                stale.append(address)

        return stale


class StateManager:
    """Manages extraction state persistence.

    Provides atomic read/write operations for extraction state with
    automatic timestamping and logging.
    """

    def __init__(self, state_path: Path):
        """Initialize state manager.

        Args:
            state_path: Path to state JSON file
        """
        self.state_path = Path(state_path)
        self._state: ExtractionState | None = None

    def load(self) -> ExtractionState:
        """Load state from disk.

        Returns:
            ExtractionState instance (empty if file doesn't exist)
        """
        if self._state is not None:
            return self._state

        if self.state_path.exists():
            try:
                with open(self.state_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._state = ExtractionState.from_dict(data)
                    logger.info(
                        f"Loaded state: {len(self._state.completed_properties)} completed, "
                        f"{len(self._state.failed_properties)} failed"
                    )
                    return self._state
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load state: {e}")

        self._state = ExtractionState()
        return self._state

    def save(self, state: ExtractionState | None = None) -> None:
        """Save state to disk atomically.

        Security: Uses temp file + rename to prevent corruption from crashes.

        Args:
            state: State to save (uses cached state if None)
        """
        import os
        import tempfile

        if state is not None:
            self._state = state

        if self._state is None:
            logger.warning("No state to save")
            return

        self._state.last_updated = datetime.now().astimezone().isoformat()

        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write using temp file + rename
            fd, temp_path = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self._state.to_dict(), f, indent=2)
                os.replace(temp_path, self.state_path)  # Atomic on POSIX and Windows
                logger.debug("Saved state to disk")
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except OSError as e:
            logger.error(f"Failed to save state: {e}")

    def mark_completed(self, property_address: str) -> None:
        """Mark property as completed.

        Args:
            property_address: Full address of completed property
        """
        state = self.load()
        state.completed_properties.add(property_address)
        state.failed_properties.discard(property_address)
        self._state = state

    def mark_failed(self, property_address: str) -> None:
        """Mark property as failed.

        Args:
            property_address: Full address of failed property
        """
        state = self.load()
        state.failed_properties.add(property_address)
        self._state = state

    def is_completed(self, property_address: str) -> bool:
        """Check if property was already completed.

        Args:
            property_address: Full address to check

        Returns:
            True if property was previously completed
        """
        state = self.load()
        return property_address in state.completed_properties

    def is_failed(self, property_address: str) -> bool:
        """Check if property previously failed.

        Args:
            property_address: Full address to check

        Returns:
            True if property previously failed
        """
        state = self.load()
        return property_address in state.failed_properties

    def get_pending_count(self, total_properties: int) -> int:
        """Get count of properties not yet processed.

        Args:
            total_properties: Total number of properties to process

        Returns:
            Number of properties not in completed or failed sets
        """
        state = self.load()
        processed = len(state.completed_properties) + len(state.failed_properties)
        return max(0, total_properties - processed)

    def reset(self) -> None:
        """Reset state to empty (for reprocessing)."""
        self._state = ExtractionState()
        if self.state_path.exists():
            self.state_path.unlink()
        logger.info("State reset")

    @property
    def completed_count(self) -> int:
        """Get count of completed properties."""
        state = self.load()
        return len(state.completed_properties)

    @property
    def failed_count(self) -> int:
        """Get count of failed properties."""
        state = self.load()
        return len(state.failed_properties)

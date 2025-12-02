"""State persistence manager for image extraction operations.

Provides resumable extraction by tracking completed and failed properties.
State is persisted to JSON for crash recovery and incremental processing.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ExtractionState:
    """Persistent state for resumable extraction.

    Tracks which properties have been processed (successfully or failed)
    to enable resumption of interrupted extraction runs.
    """

    completed_properties: Set[str] = field(default_factory=set)
    failed_properties: Set[str] = field(default_factory=set)
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation
        """
        return {
            "completed_properties": list(self.completed_properties),
            "failed_properties": list(self.failed_properties),
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
            last_updated=data.get("last_updated"),
        )


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
        self._state: Optional[ExtractionState] = None

    def load(self) -> ExtractionState:
        """Load state from disk.

        Returns:
            ExtractionState instance (empty if file doesn't exist)
        """
        if self._state is not None:
            return self._state

        if self.state_path.exists():
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._state = ExtractionState.from_dict(data)
                    logger.info(
                        f"Loaded state: {len(self._state.completed_properties)} completed, "
                        f"{len(self._state.failed_properties)} failed"
                    )
                    return self._state
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load state: {e}")

        self._state = ExtractionState()
        return self._state

    def save(self, state: Optional[ExtractionState] = None) -> None:
        """Save state to disk.

        Args:
            state: State to save (uses cached state if None)
        """
        if state is not None:
            self._state = state

        if self._state is None:
            logger.warning("No state to save")
            return

        self._state.last_updated = datetime.now().astimezone().isoformat()

        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, indent=2)
            logger.debug("Saved state to disk")
        except IOError as e:
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

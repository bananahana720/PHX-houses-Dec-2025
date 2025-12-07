"""Unit tests for state management service.

Tests checkpoint/recovery state persistence, property completion tracking,
and manifest operations for resumable extraction.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from phx_home_analysis.services.image_extraction.state_manager import (
    ExtractionState,
    StateManager,
)


class TestExtractionState:
    """Tests for ExtractionState dataclass."""

    def test_default_initialization(self):
        """Test ExtractionState with default values."""
        state = ExtractionState()

        assert state.completed_properties == set()
        assert state.failed_properties == set()
        assert state.property_last_checked == {}
        assert state.last_updated is None

    def test_to_dict_conversion(self):
        """Test converting state to dictionary."""
        state = ExtractionState()
        state.completed_properties.add("123 Main St")
        state.failed_properties.add("456 Oak Ave")
        state.property_last_checked["123 Main St"] = "2025-12-06T10:00:00"

        result = state.to_dict()

        assert "123 Main St" in result["completed_properties"]
        assert "456 Oak Ave" in result["failed_properties"]
        assert result["property_last_checked"]["123 Main St"] == "2025-12-06T10:00:00"
        assert "last_updated" in result

    def test_to_dict_sets_last_updated_if_none(self):
        """Test to_dict sets last_updated timestamp if None."""
        state = ExtractionState()

        result = state.to_dict()

        assert result["last_updated"] is not None
        # Should be valid ISO format
        datetime.fromisoformat(result["last_updated"])

    def test_from_dict_loading(self):
        """Test loading state from dictionary."""
        data = {
            "completed_properties": ["123 Main St", "456 Oak Ave"],
            "failed_properties": ["789 Pine Rd"],
            "property_last_checked": {"123 Main St": "2025-12-06T10:00:00"},
            "last_updated": "2025-12-06T12:00:00",
        }

        state = ExtractionState.from_dict(data)

        assert "123 Main St" in state.completed_properties
        assert "456 Oak Ave" in state.completed_properties
        assert "789 Pine Rd" in state.failed_properties
        assert state.property_last_checked["123 Main St"] == "2025-12-06T10:00:00"
        assert state.last_updated == "2025-12-06T12:00:00"

    def test_from_dict_handles_empty_data(self):
        """Test from_dict handles empty/missing fields gracefully."""
        data = {}

        state = ExtractionState.from_dict(data)

        assert state.completed_properties == set()
        assert state.failed_properties == set()
        assert state.property_last_checked == {}
        assert state.last_updated is None

    def test_record_property_checked(self):
        """Test recording property check timestamp."""
        state = ExtractionState()
        address = "123 Main St"

        state.record_property_checked(address)

        assert address in state.property_last_checked
        timestamp = state.property_last_checked[address]
        # Should be valid ISO format
        datetime.fromisoformat(timestamp)

    def test_record_property_checked_updates_existing(self):
        """Test recording updates existing timestamp."""
        state = ExtractionState()
        address = "123 Main St"

        old_timestamp = "2025-12-05T10:00:00+00:00"  # Use timezone-aware timestamp
        state.property_last_checked[address] = old_timestamp
        state.record_property_checked(address)

        new_timestamp = state.property_last_checked[address]
        assert new_timestamp != old_timestamp
        # Both timestamps should be parseable
        datetime.fromisoformat(new_timestamp)
        datetime.fromisoformat(old_timestamp)

    def test_get_property_last_checked(self):
        """Test retrieving property last checked timestamp."""
        state = ExtractionState()
        address = "123 Main St"
        timestamp = "2025-12-06T10:00:00"
        state.property_last_checked[address] = timestamp

        result = state.get_property_last_checked(address)

        assert result == timestamp

    def test_get_property_last_checked_missing(self):
        """Test retrieving timestamp for unchecked property."""
        state = ExtractionState()

        result = state.get_property_last_checked("nonexistent address")

        assert result is None

    def test_get_stale_properties_by_age(self):
        """Test identifying stale properties by age."""
        state = ExtractionState()

        # Add properties with different ages (use timezone-aware datetimes)
        now = datetime.now().astimezone()
        old_timestamp = (now - timedelta(days=10)).isoformat()
        recent_timestamp = (now - timedelta(days=3)).isoformat()

        state.completed_properties.add("123 Main St")
        state.completed_properties.add("456 Oak Ave")
        state.property_last_checked["123 Main St"] = old_timestamp
        state.property_last_checked["456 Oak Ave"] = recent_timestamp

        stale = state.get_stale_properties(max_age_days=7)

        assert "123 Main St" in stale
        assert "456 Oak Ave" not in stale

    def test_get_stale_properties_never_checked(self):
        """Test identifying properties never checked."""
        state = ExtractionState()

        state.completed_properties.add("123 Main St")
        # No timestamp in property_last_checked

        stale = state.get_stale_properties(max_age_days=7)

        assert "123 Main St" in stale

    def test_get_stale_properties_invalid_timestamp(self):
        """Test handling invalid timestamps in staleness check."""
        state = ExtractionState()

        state.completed_properties.add("123 Main St")
        state.property_last_checked["123 Main St"] = "invalid-timestamp"

        stale = state.get_stale_properties(max_age_days=7)

        # Should treat invalid timestamp as stale
        assert "123 Main St" in stale

    def test_get_stale_properties_excludes_failed(self):
        """Test staleness only checks completed properties."""
        state = ExtractionState()

        old_timestamp = (datetime.now() - timedelta(days=10)).isoformat()

        state.failed_properties.add("123 Main St")
        state.property_last_checked["123 Main St"] = old_timestamp

        stale = state.get_stale_properties(max_age_days=7)

        # Failed properties not checked for staleness
        assert "123 Main St" not in stale


class TestStateManager:
    """Tests for StateManager class."""

    def test_initialization(self, tmp_path: Path):
        """Test StateManager initialization."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        assert manager.state_path == state_path
        assert manager._state is None  # Not loaded yet

    def test_load_creates_empty_state_if_missing(self, tmp_path: Path):
        """Test load creates empty state when file doesn't exist."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        state = manager.load()

        assert isinstance(state, ExtractionState)
        assert state.completed_properties == set()
        assert state.failed_properties == set()

    def test_load_reads_existing_state(self, tmp_path: Path):
        """Test load reads existing state from disk."""
        state_path = tmp_path / "state.json"

        # Create state file
        data = {
            "completed_properties": ["123 Main St"],
            "failed_properties": ["456 Oak Ave"],
            "property_last_checked": {},
            "last_updated": "2025-12-06T10:00:00",
        }
        state_path.write_text(json.dumps(data))

        manager = StateManager(state_path)
        state = manager.load()

        assert "123 Main St" in state.completed_properties
        assert "456 Oak Ave" in state.failed_properties

    def test_load_caches_state(self, tmp_path: Path):
        """Test load caches state and doesn't reload."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        state1 = manager.load()
        state2 = manager.load()

        # Should return same instance
        assert state1 is state2

    def test_load_handles_corrupted_json(self, tmp_path: Path):
        """Test load handles corrupted JSON file gracefully."""
        state_path = tmp_path / "state.json"
        state_path.write_text("invalid json {")

        manager = StateManager(state_path)
        state = manager.load()

        # Should create empty state
        assert state.completed_properties == set()

    def test_save_creates_directory(self, tmp_path: Path):
        """Test save creates parent directory if needed."""
        state_path = tmp_path / "subdir" / "state.json"
        manager = StateManager(state_path)

        state = ExtractionState()
        manager.save(state)

        assert state_path.parent.exists()
        assert state_path.exists()

    def test_save_writes_state_to_disk(self, tmp_path: Path):
        """Test save writes state to JSON file."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        state = ExtractionState()
        state.completed_properties.add("123 Main St")
        manager.save(state)

        # Read and verify
        with open(state_path) as f:
            data = json.load(f)

        assert "123 Main St" in data["completed_properties"]

    def test_save_sets_last_updated(self, tmp_path: Path):
        """Test save sets last_updated timestamp."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        state = ExtractionState()
        manager.save(state)

        assert state.last_updated is not None
        datetime.fromisoformat(state.last_updated)

    def test_save_uses_cached_state_if_none(self, tmp_path: Path):
        """Test save uses cached state when state param is None."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        # Load/create state
        state = manager.load()
        state.completed_properties.add("123 Main St")

        # Save without passing state
        manager.save()

        # Verify saved
        with open(state_path) as f:
            data = json.load(f)
        assert "123 Main St" in data["completed_properties"]

    def test_save_handles_no_state_gracefully(self, tmp_path: Path):
        """Test save handles case where no state exists."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        # Don't load or provide state
        manager.save()

        # Should not crash, file should not be created
        assert not state_path.exists()

    def test_mark_completed(self, tmp_path: Path):
        """Test mark_completed adds property to completed set."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        address = "123 Main St"
        manager.mark_completed(address)

        state = manager.load()
        assert address in state.completed_properties
        assert address not in state.failed_properties

    def test_mark_completed_removes_from_failed(self, tmp_path: Path):
        """Test mark_completed removes property from failed set."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        address = "123 Main St"

        # First mark as failed
        state = manager.load()
        state.failed_properties.add(address)

        # Then mark as completed
        manager.mark_completed(address)

        state = manager.load()
        assert address in state.completed_properties
        assert address not in state.failed_properties

    def test_mark_failed(self, tmp_path: Path):
        """Test mark_failed adds property to failed set."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        address = "456 Oak Ave"
        manager.mark_failed(address)

        state = manager.load()
        assert address in state.failed_properties

    def test_is_completed_check(self, tmp_path: Path):
        """Test is_completed returns True for completed properties."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        address = "123 Main St"
        manager.mark_completed(address)

        assert manager.is_completed(address)
        assert not manager.is_completed("different address")

    def test_is_failed_check(self, tmp_path: Path):
        """Test is_failed returns True for failed properties."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        address = "456 Oak Ave"
        manager.mark_failed(address)

        assert manager.is_failed(address)
        assert not manager.is_failed("different address")

    def test_get_pending_count(self, tmp_path: Path):
        """Test get_pending_count calculates unprocessed properties."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        manager.mark_completed("123 Main St")
        manager.mark_completed("456 Oak Ave")
        manager.mark_failed("789 Pine Rd")

        # 3 processed out of 10 total
        pending = manager.get_pending_count(total_properties=10)

        assert pending == 7

    def test_get_pending_count_all_processed(self, tmp_path: Path):
        """Test get_pending_count returns 0 when all processed."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        manager.mark_completed("123 Main St")
        manager.mark_failed("456 Oak Ave")

        pending = manager.get_pending_count(total_properties=2)

        assert pending == 0

    def test_get_pending_count_handles_overflow(self, tmp_path: Path):
        """Test get_pending_count handles case where processed > total."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        manager.mark_completed("123 Main St")
        manager.mark_completed("456 Oak Ave")

        # More processed than total (shouldn't happen, but handle gracefully)
        pending = manager.get_pending_count(total_properties=1)

        assert pending == 0  # max(0, 1-2) = 0

    def test_reset_clears_state(self, tmp_path: Path):
        """Test reset clears all state."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        # Add some state
        manager.mark_completed("123 Main St")
        manager.mark_failed("456 Oak Ave")
        manager.save()

        # Reset
        manager.reset()

        state = manager.load()
        assert state.completed_properties == set()
        assert state.failed_properties == set()

    def test_reset_deletes_state_file(self, tmp_path: Path):
        """Test reset deletes state file from disk."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        # Create state file
        manager.mark_completed("123 Main St")
        manager.save()
        assert state_path.exists()

        # Reset
        manager.reset()

        assert not state_path.exists()

    def test_completed_count_property(self, tmp_path: Path):
        """Test completed_count property returns count."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        manager.mark_completed("123 Main St")
        manager.mark_completed("456 Oak Ave")

        assert manager.completed_count == 2

    def test_failed_count_property(self, tmp_path: Path):
        """Test failed_count property returns count."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        manager.mark_failed("123 Main St")
        manager.mark_failed("456 Oak Ave")
        manager.mark_failed("789 Pine Rd")

        assert manager.failed_count == 3

    def test_atomic_save_prevents_corruption(self, tmp_path: Path):
        """Test save uses atomic write to prevent corruption."""
        state_path = tmp_path / "state.json"
        manager = StateManager(state_path)

        state = ExtractionState()
        state.completed_properties.add("123 Main St")

        # Save should use temp file + rename
        manager.save(state)

        # No temp files should remain
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

        # Final file should exist and be valid JSON
        assert state_path.exists()
        with open(state_path) as f:
            data = json.load(f)
        assert "123 Main St" in data["completed_properties"]

    def test_persistence_across_instances(self, tmp_path: Path):
        """Test state persists across manager instances."""
        state_path = tmp_path / "state.json"

        # Create and save state
        manager1 = StateManager(state_path)
        manager1.mark_completed("123 Main St")
        manager1.save()

        # Create new instance and load
        manager2 = StateManager(state_path)
        state = manager2.load()

        assert "123 Main St" in state.completed_properties

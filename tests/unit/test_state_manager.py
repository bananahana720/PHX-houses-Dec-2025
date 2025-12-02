"""Tests for the StateManager module."""

import tempfile
from pathlib import Path

import pytest

from src.phx_home_analysis.services.image_extraction.state_manager import (
    ExtractionState,
    StateManager,
)


class TestExtractionState:
    """Test ExtractionState dataclass."""

    def test_default_empty(self):
        """Default state should be empty."""
        state = ExtractionState()
        assert len(state.completed_properties) == 0
        assert len(state.failed_properties) == 0
        assert state.last_updated is None

    def test_to_dict(self):
        """Should serialize to dict."""
        state = ExtractionState(
            completed_properties={"addr1", "addr2"},
            failed_properties={"addr3"},
        )
        data = state.to_dict()
        assert "completed_properties" in data
        assert "failed_properties" in data
        assert "last_updated" in data
        assert set(data["completed_properties"]) == {"addr1", "addr2"}
        assert data["failed_properties"] == ["addr3"]

    def test_from_dict(self):
        """Should deserialize from dict."""
        data = {
            "completed_properties": ["addr1", "addr2"],
            "failed_properties": ["addr3"],
            "last_updated": "2025-01-01T00:00:00+00:00",
        }
        state = ExtractionState.from_dict(data)
        assert state.completed_properties == {"addr1", "addr2"}
        assert state.failed_properties == {"addr3"}
        assert state.last_updated == "2025-01-01T00:00:00+00:00"

    def test_from_dict_missing_fields(self):
        """Should handle missing fields gracefully."""
        state = ExtractionState.from_dict({})
        assert len(state.completed_properties) == 0
        assert len(state.failed_properties) == 0

    def test_roundtrip(self):
        """to_dict and from_dict should roundtrip."""
        original = ExtractionState(
            completed_properties={"addr1", "addr2"},
            failed_properties={"addr3"},
        )
        data = original.to_dict()
        restored = ExtractionState.from_dict(data)
        assert restored.completed_properties == original.completed_properties
        assert restored.failed_properties == original.failed_properties


class TestStateManager:
    """Test StateManager class."""

    @pytest.fixture
    def temp_state_path(self):
        """Create temporary state file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "state.json"

    def test_load_nonexistent_file(self, temp_state_path):
        """Loading nonexistent file returns empty state."""
        manager = StateManager(temp_state_path)
        state = manager.load()
        assert len(state.completed_properties) == 0
        assert len(state.failed_properties) == 0

    def test_save_and_load(self, temp_state_path):
        """Saved state should be loadable."""
        manager = StateManager(temp_state_path)
        state = ExtractionState(
            completed_properties={"addr1", "addr2"},
            failed_properties={"addr3"},
        )
        manager.save(state)

        # Create new manager to force reload
        manager2 = StateManager(temp_state_path)
        loaded = manager2.load()

        assert loaded.completed_properties == {"addr1", "addr2"}
        assert loaded.failed_properties == {"addr3"}

    def test_mark_completed(self, temp_state_path):
        """mark_completed should add to completed set."""
        manager = StateManager(temp_state_path)
        manager.mark_completed("123 Main St")

        assert manager.is_completed("123 Main St")
        assert not manager.is_failed("123 Main St")

    def test_mark_completed_removes_from_failed(self, temp_state_path):
        """mark_completed should remove from failed set."""
        manager = StateManager(temp_state_path)
        manager.mark_failed("123 Main St")
        assert manager.is_failed("123 Main St")

        manager.mark_completed("123 Main St")
        assert manager.is_completed("123 Main St")
        assert not manager.is_failed("123 Main St")

    def test_mark_failed(self, temp_state_path):
        """mark_failed should add to failed set."""
        manager = StateManager(temp_state_path)
        manager.mark_failed("123 Main St")

        assert manager.is_failed("123 Main St")
        assert not manager.is_completed("123 Main St")

    def test_is_completed(self, temp_state_path):
        """is_completed should return correct status."""
        manager = StateManager(temp_state_path)
        assert not manager.is_completed("123 Main St")

        manager.mark_completed("123 Main St")
        assert manager.is_completed("123 Main St")

    def test_is_failed(self, temp_state_path):
        """is_failed should return correct status."""
        manager = StateManager(temp_state_path)
        assert not manager.is_failed("123 Main St")

        manager.mark_failed("123 Main St")
        assert manager.is_failed("123 Main St")

    def test_get_pending_count(self, temp_state_path):
        """get_pending_count should calculate correctly."""
        manager = StateManager(temp_state_path)
        manager.mark_completed("addr1")
        manager.mark_completed("addr2")
        manager.mark_failed("addr3")

        # 10 total, 3 processed = 7 pending
        assert manager.get_pending_count(10) == 7

    def test_reset(self, temp_state_path):
        """reset should clear all state."""
        manager = StateManager(temp_state_path)
        manager.mark_completed("addr1")
        manager.mark_failed("addr2")
        manager.save()

        manager.reset()

        assert manager.completed_count == 0
        assert manager.failed_count == 0
        assert not temp_state_path.exists()

    def test_completed_count(self, temp_state_path):
        """completed_count property should work."""
        manager = StateManager(temp_state_path)
        assert manager.completed_count == 0

        manager.mark_completed("addr1")
        manager.mark_completed("addr2")
        assert manager.completed_count == 2

    def test_failed_count(self, temp_state_path):
        """failed_count property should work."""
        manager = StateManager(temp_state_path)
        assert manager.failed_count == 0

        manager.mark_failed("addr1")
        assert manager.failed_count == 1

    def test_creates_parent_dirs(self):
        """save should create parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "a" / "b" / "c" / "state.json"
            manager = StateManager(nested_path)
            manager.mark_completed("addr1")
            manager.save()

            assert nested_path.exists()

    def test_handles_corrupt_json(self, temp_state_path):
        """Should handle corrupt JSON gracefully."""
        temp_state_path.write_text("not valid json {{{")

        manager = StateManager(temp_state_path)
        state = manager.load()

        # Should return empty state on error
        assert len(state.completed_properties) == 0

    def test_caches_state(self, temp_state_path):
        """Should cache loaded state."""
        manager = StateManager(temp_state_path)
        manager.mark_completed("addr1")

        # Should not lose data without save
        assert manager.is_completed("addr1")

        # Multiple loads should return same cached state
        state1 = manager.load()
        state2 = manager.load()
        assert state1 is state2

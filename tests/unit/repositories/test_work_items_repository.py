"""Unit tests for WorkItemsRepository."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from phx_home_analysis.repositories import WorkItemsRepository
from phx_home_analysis.repositories.base import DataLoadError


class TestWorkItemsRepositoryInitialization:
    """Tests for repository initialization."""

    def test_init_creates_repository(self, tmp_path):
        """Repository initializes with file path."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        assert repo.json_file_path == json_path

    def test_load_state_empty_file(self, tmp_path):
        """Loading nonexistent file returns empty state."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        state = repo.load_state()

        assert "session" in state
        assert "work_items" in state
        assert "summary" in state
        assert state["work_items"] == []


class TestSessionInitialization:
    """Tests for session initialization."""

    def test_initialize_session_batch_mode(self, tmp_path):
        """Batch mode session initializes with addresses."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        state = repo.load_state()
        assert state["session"]["mode"] == "batch"
        assert state["session"]["total_items"] == 3
        assert len(state["work_items"]) == 3

    def test_initialize_session_single_mode(self, tmp_path):
        """Single mode session initializes with one address."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        state = repo.load_state()
        assert state["session"]["mode"] == "single"
        assert state["session"]["total_items"] == 1

    def test_initialize_session_generates_session_id(self, tmp_path):
        """Session ID is auto-generated if not provided."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        state = repo.load_state()
        assert "session_id" in state["session"]
        assert state["session"]["session_id"].startswith("session_")

    def test_initialize_session_custom_session_id(self, tmp_path):
        """Custom session ID can be provided."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        custom_id = "custom_session_12345"
        repo.initialize_session(mode="batch", addresses=["123 Main St"], session_id=custom_id)

        state = repo.load_state()
        assert state["session"]["session_id"] == custom_id


class TestWorkItemCreation:
    """Tests for work item structure creation."""

    def test_work_item_has_required_fields(self, tmp_path):
        """Work items contain all required fields."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        item = state["work_items"][0]

        assert "id" in item
        assert "address" in item
        assert "status" in item
        assert "phases" in item
        assert "created_at" in item
        assert "updated_at" in item

    def test_work_item_has_all_phases(self, tmp_path):
        """Work items include all pipeline phases."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        phases = state["work_items"][0]["phases"]

        expected_phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]

        for phase in expected_phases:
            assert phase in phases
            assert phases[phase]["status"] == "pending"

    def test_work_item_id_is_8_char_hex(self, tmp_path):
        """Work item ID is 8-character hex string."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        item_id = state["work_items"][0]["id"]

        assert len(item_id) == 8
        assert all(c in "0123456789abcdef" for c in item_id)


class TestPhaseCheckpointing:
    """Tests for phase checkpoint operations."""

    def test_checkpoint_phase_start(self, tmp_path):
        """Phase start updates status to in_progress."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"
        assert "started_at" in phase

    def test_checkpoint_phase_complete_success(self, tmp_path):
        """Phase complete updates status to completed."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "completed"
        assert "completed_at" in phase

    def test_checkpoint_phase_complete_failure(self, tmp_path):
        """Phase complete with error updates status to failed."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St", "phase1_listing", error_message="HTTP 500 error"
        )

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "failed"
        assert phase["error_message"] == "HTTP 500 error"
        assert phase["retry_count"] == 1

    def test_checkpoint_multiple_phases(self, tmp_path):
        """Multiple phases can be checkpointed independently."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Complete phase1_listing
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Complete phase1_map
        repo.checkpoint_phase_start("123 Main St", "phase1_map")
        repo.checkpoint_phase_complete("123 Main St", "phase1_map")

        item = repo.get_work_item("123 Main St")

        assert item["phases"]["phase1_listing"]["status"] == "completed"
        assert item["phases"]["phase1_map"]["status"] == "completed"
        assert item["phases"]["phase2_images"]["status"] == "pending"


class TestStateTransitions:
    """Tests for state transition validation."""

    def test_invalid_phase_transition_raises_error(self, tmp_path):
        """Invalid phase transition raises ValueError."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Try to complete without starting
        with pytest.raises(ValueError, match="Invalid phase transition"):
            repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

    def test_cannot_restart_completed_phase(self, tmp_path):
        """Cannot restart a completed phase."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Try to restart completed phase
        with pytest.raises(ValueError, match="Invalid phase transition"):
            repo.checkpoint_phase_start("123 Main St", "phase1_listing")

    def test_can_retry_failed_phase(self, tmp_path):
        """Failed phase can be retried."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St", "phase1_listing", error_message="Network error"
        )

        # Retry should be allowed
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"
        assert phase["retry_count"] == 1


class TestWorkItemStatusUpdate:
    """Tests for automatic work item status updates."""

    def test_status_updates_to_in_progress(self, tmp_path):
        """Work item status updates to in_progress when phase starts."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "in_progress"

    def test_status_updates_to_completed(self, tmp_path):
        """Work item status updates to completed when all phases complete."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "completed"

    def test_status_updates_to_failed(self, tmp_path):
        """Work item status updates to failed when any phase fails."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing", error_message="Error")

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "failed"


class TestStaleItemDetection:
    """Tests for stale in_progress item detection."""

    def test_stale_items_reset_to_pending(self, tmp_path):
        """Items in_progress > 30 minutes reset to pending."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Manually set started_at to 40 minutes ago
        state = repo.load_state()
        past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
        state["work_items"][0]["phases"]["phase1_listing"]["started_at"] = past_time.isoformat()
        repo.save_state(state)

        # Load again to trigger stale detection
        state = repo.load_state()
        item = state["work_items"][0]
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "pending"
        assert "stale_reset_at" in phase

    def test_fresh_items_not_reset(self, tmp_path):
        """Items in_progress < 30 minutes are not reset."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Load again (should not reset)
        state = repo.load_state()
        item = state["work_items"][0]
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"


class TestSummaryCalculation:
    """Tests for summary statistics calculation."""

    def test_summary_calculates_totals(self, tmp_path):
        """Summary calculates total counts by status."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete one phase for first property, start one phase for second, leave third untouched
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")
        repo.checkpoint_phase_start("456 Oak Ave", "phase1_listing")

        state = repo.load_state()
        summary = state["summary"]

        assert summary["total"] == 3
        assert summary["pending"] == 2  # "123 Main St" (partial) + "789 Elm Blvd" (untouched)
        assert summary["in_progress"] == 1  # "456 Oak Ave" (actively in progress)
        assert summary["completed"] == 0  # No property has all phases complete

    def test_summary_calculates_completion_percentage(self, tmp_path):
        """Summary calculates completion percentage."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete all phases for first item
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        state = repo.load_state()
        summary = state["summary"]

        assert summary["completed"] == 1
        assert summary["completion_percentage"] == 50.0


class TestBackupManagement:
    """Tests for backup creation and cleanup."""

    def test_backup_created_before_save(self, tmp_path):
        """Backup file is created before save."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Check backup exists
        backups = list(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) >= 1

    def test_old_backups_cleaned_up(self, tmp_path):
        """Old backups are cleaned up, keeping MAX_BACKUPS most recent."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Create 15 checkpoints (exceeds MAX_BACKUPS = 10)
        for i in range(15):
            repo.checkpoint_phase_start("123 Main St", "phase1_listing")
            # Complete and restart to create more checkpoints
            if i < 14:
                repo.checkpoint_phase_complete(
                    "123 Main St", "phase1_listing", error_message="test"
                )

        backups = list(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) <= repo.MAX_BACKUPS


class TestErrorHandling:
    """Tests for error handling."""

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Loading invalid JSON raises DataLoadError."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text("{invalid json}")

        repo = WorkItemsRepository(json_path)

        with pytest.raises(DataLoadError, match="Invalid JSON"):
            repo.load_state()

    def test_checkpoint_unknown_address_raises_error(self, tmp_path):
        """Checkpointing unknown address raises ValueError."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        with pytest.raises(ValueError, match="Work item not found"):
            repo.checkpoint_phase_start("999 Unknown St", "phase1_listing")


class TestQueryMethods:
    """Tests for query methods."""

    def test_get_pending_items(self, tmp_path):
        """get_pending_items returns only pending items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        pending = repo.get_pending_items()
        assert len(pending) == 2
        assert all(item["status"] == "pending" for item in pending)

    def test_get_incomplete_items(self, tmp_path):
        """get_incomplete_items returns non-completed items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete all phases for first item
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        incomplete = repo.get_incomplete_items()
        assert len(incomplete) == 1
        assert incomplete[0]["address"] == "456 Oak Ave"


class TestAtomicWrites:
    """Tests for atomic write operations."""

    def test_state_file_exists_after_save(self, tmp_path):
        """State file exists after save operation."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        assert json_path.exists()

        # Verify content is valid JSON
        with open(json_path) as f:
            data = json.load(f)
            assert "work_items" in data

    def test_no_temp_files_left_behind(self, tmp_path):
        """No temporary files remain after save."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Check no temp files
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

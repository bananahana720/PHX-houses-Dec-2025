"""Unit tests for ResumePipeline."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from phx_home_analysis.pipeline.resume import ResumePipeline, StateValidationError
from phx_home_analysis.repositories import WorkItemsRepository


class TestStateValidationError:
    """Tests for StateValidationError exception."""

    def test_error_with_message(self) -> None:
        """StateValidationError stores message."""
        error = StateValidationError("Test error")
        assert str(error) == "Test error"

    def test_error_with_details(self) -> None:
        """StateValidationError stores details dict."""
        error = StateValidationError("Test", details={"field": "value"})
        assert error.details == {"field": "value"}

    def test_error_with_suggestion(self) -> None:
        """StateValidationError stores suggestion."""
        error = StateValidationError("Test", suggestion="Run with --fresh")
        assert error.suggestion == "Run with --fresh"

    def test_error_defaults(self) -> None:
        """StateValidationError has sensible defaults."""
        error = StateValidationError("Test")
        assert error.details == {}
        assert error.suggestion is None


class TestResumePipelineInitialization:
    """Tests for ResumePipeline initialization."""

    def test_init_creates_resumer(self, tmp_path: Path) -> None:
        """ResumePipeline initializes with repository."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        assert resumer.repo is repo
        assert resumer.fresh is False

    def test_init_with_fresh_flag(self, tmp_path: Path) -> None:
        """Fresh flag disables resume."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo, fresh=True)

        assert resumer.fresh is True


class TestCanResume:
    """Tests for can_resume() method."""

    def test_can_resume_with_valid_state(self, tmp_path: Path) -> None:
        """Returns True when valid state exists."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        resumer = ResumePipeline(repo)
        assert resumer.can_resume() is True

    def test_cannot_resume_empty_state(self, tmp_path: Path) -> None:
        """Returns False when no state exists."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        resumer = ResumePipeline(repo)
        assert resumer.can_resume() is False

    def test_cannot_resume_with_fresh_flag(self, tmp_path: Path) -> None:
        """Returns False when fresh flag is set."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        resumer = ResumePipeline(repo, fresh=True)
        assert resumer.can_resume() is False


class TestLoadAndValidate:
    """Tests for load_and_validate() method."""

    def test_loads_valid_state(self, tmp_path: Path) -> None:
        """Loads and returns valid state."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        resumer = ResumePipeline(repo)
        state = resumer.load_and_validate()

        assert "session" in state
        assert "work_items" in state

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """Raises StateValidationError on invalid JSON."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text("{invalid json}")

        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        with pytest.raises(StateValidationError, match="corrupted"):
            resumer.load_and_validate()

    def test_raises_on_missing_session(self, tmp_path: Path) -> None:
        """Raises StateValidationError when session missing."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text('{"work_items": []}')

        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        with pytest.raises(StateValidationError, match="missing required field"):
            resumer.load_and_validate()

    def test_raises_on_missing_work_items(self, tmp_path: Path) -> None:
        """Raises StateValidationError when work_items missing."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text('{"session": {"session_id": "test"}}')

        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        with pytest.raises(StateValidationError, match="missing required field"):
            resumer.load_and_validate()

    def test_error_includes_suggestion(self, tmp_path: Path) -> None:
        """StateValidationError includes suggestion."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text("{invalid}")

        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        try:
            resumer.load_and_validate()
        except StateValidationError as e:
            assert e.suggestion is not None
            assert "--fresh" in e.suggestion


class TestResetStaleItems:
    """Tests for reset_stale_items() method.

    Note: The WorkItemsRepository.load_state() already resets stale items,
    so ResumePipeline.reset_stale_items() handles additional cases where
    the repository may not have caught stale items or where we need
    additional processing (like error preservation).
    """

    def test_resets_stale_items_in_loaded_state(self, tmp_path: Path) -> None:
        """ResumePipeline.reset_stale_items() resets items stuck >30 minutes.

        This test validates the ResumePipeline's own reset_stale_items() method
        by creating a scenario where stale items exist in the loaded state
        and verifying they are properly reset to 'pending' status.
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Create resumer and load state first
        resumer = ResumePipeline(repo)
        state = resumer.load_and_validate()

        # Now manually modify the loaded state to simulate a stale item
        # This bypasses repository's reset logic to test ResumePipeline's reset_stale_items
        past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
        state["work_items"][0]["phases"]["phase1_listing"]["started_at"] = past_time.isoformat()
        state["work_items"][0]["phases"]["phase1_listing"]["status"] = "in_progress"
        state["work_items"][0]["status"] = "in_progress"

        # Call ResumePipeline's reset_stale_items which should reset this item
        reset_addresses = resumer.reset_stale_items()

        # Verify ResumePipeline detected and reset the stale item
        assert "123 Main St" in reset_addresses
        assert resumer._state["work_items"][0]["phases"]["phase1_listing"]["status"] == "pending"
        assert resumer._state["work_items"][0]["status"] == "pending"

    def test_preserves_fresh_items(self, tmp_path: Path) -> None:
        """Items recently started are not reset."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        reset = resumer.reset_stale_items()

        assert len(reset) == 0

    def test_stale_reset_records_timestamp(self, tmp_path: Path) -> None:
        """Stale reset records stale_reset_at timestamp.

        Note: This is recorded by the repository during load_state().
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Set stale timestamp directly in file
        import json
        with open(json_path) as f:
            state = json.load(f)
        past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
        state["work_items"][0]["phases"]["phase1_listing"]["started_at"] = past_time.isoformat()
        state["work_items"][0]["status"] = "in_progress"
        with open(json_path, "w") as f:
            json.dump(state, f)

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()

        # Repository should have recorded stale_reset_at
        phase = resumer._state["work_items"][0]["phases"]["phase1_listing"]
        assert "stale_reset_at" in phase

    def test_reset_returns_empty_without_state(self, tmp_path: Path) -> None:
        """reset_stale_items returns empty list when no state loaded."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        resumer = ResumePipeline(repo)
        reset = resumer.reset_stale_items()

        assert reset == []


class TestGetPendingAddresses:
    """Tests for get_pending_addresses() method."""

    def test_returns_pending_items(self, tmp_path: Path) -> None:
        """Returns addresses with pending status."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St", "456 Oak Ave"])

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        pending = resumer.get_pending_addresses()

        assert "123 Main St" in pending
        assert "456 Oak Ave" in pending

    def test_excludes_completed_items(self, tmp_path: Path) -> None:
        """Excludes addresses with completed status."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St", "456 Oak Ave"])

        # Complete all phases for first item
        phases = ["phase0_county", "phase1_listing", "phase1_map",
                  "phase2_images", "phase3_synthesis", "phase4_report"]
        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        pending = resumer.get_pending_addresses()

        assert "123 Main St" not in pending
        assert "456 Oak Ave" in pending

    def test_includes_retriable_failed_items(self, tmp_path: Path) -> None:
        """Includes failed items with retry_count < MAX_RETRIES."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing", error_message="Failed")

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        pending = resumer.get_pending_addresses()

        # Failed items should still be pending for retry
        assert "123 Main St" in pending


class TestGetCompletedAddresses:
    """Tests for get_completed_addresses() method."""

    def test_returns_completed_items(self, tmp_path: Path) -> None:
        """Returns addresses with completed status."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St", "456 Oak Ave"])

        # Complete all phases for first item
        phases = ["phase0_county", "phase1_listing", "phase1_map",
                  "phase2_images", "phase3_synthesis", "phase4_report"]
        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        completed = resumer.get_completed_addresses()

        assert "123 Main St" in completed
        assert "456 Oak Ave" not in completed

    def test_returns_empty_for_no_completions(self, tmp_path: Path) -> None:
        """Returns empty list when nothing completed."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        completed = resumer.get_completed_addresses()

        assert completed == []


class TestGetResumeSummary:
    """Tests for get_resume_summary() method."""

    def test_returns_summary_stats(self, tmp_path: Path) -> None:
        """Returns session and summary statistics."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St", "456 Oak Ave"])

        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        summary = resumer.get_resume_summary()

        assert "session_id" in summary
        assert summary["total_items"] == 2
        assert summary["pending"] == 2

    def test_returns_empty_without_load(self, tmp_path: Path) -> None:
        """Returns empty dict if load_and_validate not called."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        resumer = ResumePipeline(repo)
        summary = resumer.get_resume_summary()

        assert summary == {}


class TestPrepareFreshStart:
    """Tests for prepare_fresh_start() method."""

    def test_backs_up_existing_state(self, tmp_path: Path) -> None:
        """Creates backup before fresh start."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])

        resumer = ResumePipeline(repo, fresh=True)
        backup_path = resumer.prepare_fresh_start(["456 Oak Ave"])

        assert backup_path is not None
        assert Path(backup_path).exists()

    def test_initializes_new_session(self, tmp_path: Path) -> None:
        """Initializes new session with provided addresses."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])

        resumer = ResumePipeline(repo, fresh=True)
        resumer.prepare_fresh_start(["456 Oak Ave", "789 Elm Blvd"])

        state = repo.load_state()
        addresses = [item["address"] for item in state["work_items"]]
        assert "456 Oak Ave" in addresses
        assert "789 Elm Blvd" in addresses
        assert "123 Main St" not in addresses

    def test_returns_none_when_no_existing_state(self, tmp_path: Path) -> None:
        """Returns None when no existing state to back up."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        resumer = ResumePipeline(repo, fresh=True)
        backup_path = resumer.prepare_fresh_start(["456 Oak Ave"])

        assert backup_path is None


class TestEstimateDataLoss:
    """Tests for estimate_data_loss() method."""

    def test_counts_completed_items(self, tmp_path: Path) -> None:
        """Returns count of completed items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St", "456 Oak Ave"])

        # Complete first item
        phases = ["phase0_county", "phase1_listing", "phase1_map",
                  "phase2_images", "phase3_synthesis", "phase4_report"]
        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        resumer = ResumePipeline(repo)
        loss = resumer.estimate_data_loss()

        assert loss == 1

    def test_returns_zero_for_empty_state(self, tmp_path: Path) -> None:
        """Returns 0 when no completed items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        resumer = ResumePipeline(repo)
        loss = resumer.estimate_data_loss()

        assert loss == 0

    def test_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        """Returns 0 when file doesn't exist."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        resumer = ResumePipeline(repo)
        loss = resumer.estimate_data_loss()

        assert loss == 0


class TestVersionCompatibility:
    """Tests for schema version validation."""

    def test_compatible_version_passes(self, tmp_path: Path) -> None:
        """Compatible versions pass validation."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Add version to session
        state = repo.load_state()
        state["session"]["schema_version"] = "1.0.0"
        repo.save_state(state)

        resumer = ResumePipeline(repo)
        # Should not raise
        state = resumer.load_and_validate()
        assert state is not None

    def test_incompatible_version_fails(self, tmp_path: Path) -> None:
        """Incompatible versions raise StateValidationError."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Add incompatible version
        state = repo.load_state()
        state["session"]["schema_version"] = "2.0.0"
        repo.save_state(state)

        resumer = ResumePipeline(repo)
        with pytest.raises(StateValidationError, match="version mismatch"):
            resumer.load_and_validate()

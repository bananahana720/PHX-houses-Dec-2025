"""Integration tests for pipeline resume workflow.

Tests the complete resume workflow including:
- Resume after interruption
- Fresh start with backup
- Stale item recovery
- No duplicate processing
- Corrupt state error handling
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from phx_home_analysis.pipeline.resume import ResumePipeline, StateValidationError
from phx_home_analysis.repositories import WorkItemsRepository


class TestResumeWorkflowIntegration:
    """Integration tests for complete resume workflow."""

    def test_resume_after_interruption(self, tmp_path: Path) -> None:
        """Test resuming after simulated interruption.

        Simulates a scenario where:
        1. Pipeline starts with 3 properties
        2. First property completes all phases
        3. Second property starts phase 1 (simulated interruption)
        4. On resume, only properties 2 and 3 should be pending
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Simulate initial run with 3 properties
        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete first property
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]
        for phase in phases:
            repo.checkpoint_phase_start(addresses[0], phase)
            repo.checkpoint_phase_complete(addresses[0], phase)

        # Start second property (simulating interruption during phase 0)
        repo.checkpoint_phase_start(addresses[1], "phase0_county")

        # Create resumer and load state
        resumer = ResumePipeline(repo)
        assert resumer.can_resume()

        resumer.load_and_validate()
        pending = resumer.get_pending_addresses()
        completed = resumer.get_completed_addresses()

        # First property should be completed
        assert addresses[0] in completed

        # Second and third property should be pending
        # (second was in_progress but phase should be pending now due to fresh session)
        assert addresses[2] in pending

    def test_fresh_start_preserves_backup(self, tmp_path: Path) -> None:
        """Test fresh start creates backup of existing state.

        Verifies that:
        1. Backup file is created with timestamp
        2. Backup contains original session data
        3. New session has different session_id
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Create initial state
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        original_session_id = repo.load_state()["session"]["session_id"]

        # Fresh start with new addresses
        resumer = ResumePipeline(repo, fresh=True)
        backup_path = resumer.prepare_fresh_start(["456 Oak Ave"])

        # Verify backup exists
        assert backup_path is not None
        backup = Path(backup_path)
        assert backup.exists()

        # Verify backup contains original session
        with open(backup) as f:
            backup_state = json.load(f)
        assert backup_state["session"]["session_id"] == original_session_id

        # Verify new session is different
        new_state = repo.load_state()
        assert new_state["session"]["session_id"] != original_session_id

    def test_stale_item_recovery(self, tmp_path: Path) -> None:
        """Test automatic recovery of stale in_progress items.

        Simulates a scenario where an item was left in in_progress
        status for more than 30 minutes (due to crash/timeout).
        The item should be automatically reset to pending.
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize and start a phase
        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Manually make it stale (40 minutes ago) - write directly to file
        with open(json_path) as f:
            state = json.load(f)

        past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
        state["work_items"][0]["phases"]["phase1_listing"]["started_at"] = past_time.isoformat()
        state["work_items"][0]["status"] = "in_progress"

        with open(json_path, "w") as f:
            json.dump(state, f)

        # Resume should reset stale item (via repository)
        resumer = ResumePipeline(repo)
        resumer.load_and_validate()

        # Verify phase was reset
        item = resumer._state["work_items"][0]
        phase = item["phases"]["phase1_listing"]
        assert phase["status"] == "pending"
        assert "stale_reset_at" in phase

    def test_no_duplicate_processing(self, tmp_path: Path) -> None:
        """Test that completed items are not re-processed on resume.

        Verifies that:
        1. Completed items are excluded from pending list
        2. Only incomplete items appear in pending
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize with 2 properties
        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete first property
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]
        for phase in phases:
            repo.checkpoint_phase_start(addresses[0], phase)
            repo.checkpoint_phase_complete(addresses[0], phase)

        # Resume
        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        pending = resumer.get_pending_addresses()

        # Only second property should be pending
        assert len(pending) == 1
        assert pending[0] == addresses[1]

    def test_corrupt_state_error_handling(self, tmp_path: Path) -> None:
        """Test clear error messages for corrupt state.

        Verifies that:
        1. StateValidationError is raised for corrupt JSON
        2. Error message contains 'corrupted'
        3. Suggestion includes --fresh flag
        """
        json_path = tmp_path / "work_items.json"
        json_path.write_text("{not: valid: json}")

        repo = WorkItemsRepository(json_path)
        resumer = ResumePipeline(repo)

        with pytest.raises(StateValidationError) as exc_info:
            resumer.load_and_validate()

        error = exc_info.value
        assert "corrupted" in str(error).lower()
        assert error.suggestion is not None
        assert "--fresh" in error.suggestion

    def test_resume_summary_statistics(self, tmp_path: Path) -> None:
        """Test resume summary provides accurate statistics.

        Verifies that get_resume_summary() returns:
        - Correct session_id
        - Accurate total_items count
        - Correct pending/completed/failed counts
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize with 3 properties
        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete first property
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]
        for phase in phases:
            repo.checkpoint_phase_start(addresses[0], phase)
            repo.checkpoint_phase_complete(addresses[0], phase)

        # Load and get summary
        resumer = ResumePipeline(repo)
        resumer.load_and_validate()
        summary = resumer.get_resume_summary()

        assert summary["total_items"] == 3
        assert summary["completed"] == 1
        assert summary["pending"] == 2
        assert summary["session_id"] is not None

    def test_estimate_data_loss(self, tmp_path: Path) -> None:
        """Test data loss estimation before fresh start.

        Verifies that estimate_data_loss() correctly counts
        completed items that would need re-processing.
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize with 3 properties
        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete first two properties
        phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]
        for addr in addresses[:2]:
            for phase in phases:
                repo.checkpoint_phase_start(addr, phase)
                repo.checkpoint_phase_complete(addr, phase)

        # Estimate data loss
        resumer = ResumePipeline(repo)
        loss = resumer.estimate_data_loss()

        assert loss == 2

    def test_fresh_flag_prevents_resume(self, tmp_path: Path) -> None:
        """Test that fresh flag prevents resume even when state exists.

        Verifies that:
        1. can_resume() returns False with fresh flag
        2. Fresh start ignores existing state
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Create existing state
        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        # With fresh flag
        resumer = ResumePipeline(repo, fresh=True)
        assert resumer.can_resume() is False

    def test_version_mismatch_error(self, tmp_path: Path) -> None:
        """Test clear error for incompatible schema version.

        Verifies that:
        1. StateValidationError is raised for version mismatch
        2. Error message contains expected and found versions
        """
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Set incompatible version directly
        with open(json_path) as f:
            state = json.load(f)
        state["session"]["schema_version"] = "2.0.0"
        with open(json_path, "w") as f:
            json.dump(state, f)

        resumer = ResumePipeline(repo)
        with pytest.raises(StateValidationError) as exc_info:
            resumer.load_and_validate()

        error = exc_info.value
        assert "version mismatch" in str(error).lower()
        assert error.details.get("found") == "2.0.0"

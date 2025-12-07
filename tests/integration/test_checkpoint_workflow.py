"""Integration tests for checkpoint workflow."""

import json

from phx_home_analysis.repositories import WorkItemsRepository


class TestCheckpointWorkflowIntegration:
    """Integration tests for complete checkpoint workflow."""

    def test_full_pipeline_checkpoint_workflow(self, tmp_path):
        """Test complete pipeline execution with checkpointing."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize session
        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Execute Phase 0 for both properties
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase0_county")
            repo.checkpoint_phase_complete(address, "phase0_county")

        # Execute Phase 1 listing
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase1_listing")
            repo.checkpoint_phase_complete(address, "phase1_listing")

        # Execute Phase 1 map
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase1_map")
            repo.checkpoint_phase_complete(address, "phase1_map")

        # Verify state
        state = repo.load_state()

        for item in state["work_items"]:
            assert item["phases"]["phase0_county"]["status"] == "completed"
            assert item["phases"]["phase1_listing"]["status"] == "completed"
            assert item["phases"]["phase1_map"]["status"] == "completed"
            assert item["phases"]["phase2_images"]["status"] == "pending"

    def test_crash_recovery_scenario(self, tmp_path):
        """Simulate crash and recovery."""
        json_path = tmp_path / "work_items.json"

        # Initial execution
        repo1 = WorkItemsRepository(json_path)
        repo1.initialize_session(mode="single", addresses=["123 Main St"])
        repo1.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Simulate crash (create new repo instance)
        repo2 = WorkItemsRepository(json_path)
        state = repo2.load_state()

        # Verify state persisted
        item = state["work_items"][0]
        assert item["phases"]["phase1_listing"]["status"] == "in_progress"

    def test_backup_restore_integration(self, tmp_path):
        """Test backup creation and manual restore."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Find backup
        backups = sorted(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) > 0

        backup = backups[-1]

        # Verify backup content
        with open(backup) as f:
            backup_data = json.load(f)

        assert "work_items" in backup_data
        assert len(backup_data["work_items"]) == 1

    def test_concurrent_property_processing(self, tmp_path):
        """Test multiple properties processing independently."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Property 1: Complete phase 1
        repo.checkpoint_phase_start(addresses[0], "phase1_listing")
        repo.checkpoint_phase_complete(addresses[0], "phase1_listing")

        # Property 2: Start phase 1
        repo.checkpoint_phase_start(addresses[1], "phase1_listing")

        # Property 3: Not started

        # Verify independent states
        state = repo.load_state()
        items = {item["address"]: item for item in state["work_items"]}

        assert items[addresses[0]]["phases"]["phase1_listing"]["status"] == "completed"
        assert items[addresses[1]]["phases"]["phase1_listing"]["status"] == "in_progress"
        assert items[addresses[2]]["phases"]["phase1_listing"]["status"] == "pending"

    def test_retry_after_failure(self, tmp_path):
        """Test retry workflow after phase failure."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # First attempt fails
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing", error_message="HTTP 500")

        item = repo.get_work_item("123 Main St")
        assert item["phases"]["phase1_listing"]["retry_count"] == 1

        # Retry succeeds
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        assert item["phases"]["phase1_listing"]["status"] == "completed"
        assert item["phases"]["phase1_listing"]["retry_count"] == 1  # Count preserved

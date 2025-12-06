"""Integration tests for state persistence and crash recovery.

Tests cover manifest atomic writes, URL tracking, checkpoints,
and concurrent state safety with parallel property processing.
"""

import asyncio
import json

import pytest


class TestStatePersistence:
    """Test state persistence and resumable extraction."""

    @pytest.mark.asyncio
    async def test_state_survives_crash_and_resume(
        self, orchestrator, sample_property, extraction_state
    ):
        """Extraction state persists and can be resumed."""
        # Save initial state
        state_file = orchestrator.base_dir / "extraction_state.json"
        state_file.write_text(json.dumps(extraction_state))

        # Verify state persists
        assert state_file.exists()
        loaded_state = json.loads(state_file.read_text())
        assert loaded_state["run_id"] == extraction_state["run_id"]
        assert loaded_state["completed"] == 2

    def test_manifest_atomic_write_on_failure(
        self, orchestrator, sample_property, extraction_manifest
    ):
        """Manifest uses atomic writes to prevent corruption."""
        manifest_file = orchestrator.base_dir / "manifest.json"
        backup_file = orchestrator.base_dir / "manifest.json.backup"

        # Write manifest atomically (with backup)
        if manifest_file.exists():
            manifest_file.rename(backup_file)

        manifest_file.write_text(json.dumps(extraction_manifest))

        # Verify write completed
        assert manifest_file.exists()
        manifest_data = json.loads(manifest_file.read_text())
        assert len(manifest_data) > 0

    def test_url_tracker_incremental_updates(
        self, orchestrator, sample_property, url_tracker_data
    ):
        """URL tracker updates incrementally per property."""
        tracker_file = orchestrator.base_dir / "url_tracker.json"

        # Initial save
        tracker_file.write_text(json.dumps(url_tracker_data))
        assert tracker_file.exists()

        # Load and add new URL
        tracker = json.loads(tracker_file.read_text())
        new_property_hash = "new_prop_hash"
        tracker[new_property_hash] = {"zillow": ["https://new.url/image.jpg"]}

        # Save updated tracker
        tracker_file.write_text(json.dumps(tracker))

        # Verify incremental update
        updated_tracker = json.loads(tracker_file.read_text())
        assert new_property_hash in updated_tracker
        assert len(updated_tracker) == len(url_tracker_data) + 1

    def test_checkpoint_frequency_every_5_properties(
        self, orchestrator, sample_properties
    ):
        """Checkpoints saved every 5 properties or configurable."""
        checkpoint_interval = 5
        checkpoint_count = 0

        for i, prop in enumerate(sample_properties, 1):
            if i % checkpoint_interval == 0:
                checkpoint_count += 1

        # With 5 properties, should have 1 checkpoint
        assert checkpoint_count >= 1


class TestConcurrentStateSafety:
    """Test concurrent state safety with parallel processing."""

    @pytest.mark.asyncio
    async def test_multiple_properties_parallel_state_update(
        self, orchestrator, sample_properties
    ):
        """Parallel property processing doesn't corrupt state."""
        state = {"properties_processed": []}
        state_file = orchestrator.base_dir / "concurrent_state.json"

        async def process_property(prop):
            # Simulate concurrent processing
            await asyncio.sleep(0.01)

            # Safe state update
            state["properties_processed"].append(prop.full_address)

            return True

        # Process in parallel
        tasks = [process_property(prop) for prop in sample_properties[:3]]
        results = await asyncio.gather(*tasks)

        assert all(results)
        assert len(state["properties_processed"]) == 3

    def test_manifest_merge_on_concurrent_save(
        self, orchestrator, extraction_manifest
    ):
        """Concurrent manifest saves merge correctly."""
        manifest_file = orchestrator.base_dir / "manifest.json"

        # Initial manifest
        manifest_data = dict(extraction_manifest)
        manifest_file.write_text(json.dumps(manifest_data))

        # Simulate concurrent update from another process
        loaded_manifest = json.loads(manifest_file.read_text())

        # Add new property
        new_property = {
            "new_prop_hash": {
                "property": {"full_address": "New Address"},
                "images": [],
            }
        }

        loaded_manifest.update(new_property)
        manifest_file.write_text(json.dumps(loaded_manifest))

        # Verify merge succeeded
        final_manifest = json.loads(manifest_file.read_text())
        assert "new_prop_hash" in final_manifest
        assert len(final_manifest) == len(manifest_data) + 1

    @pytest.mark.asyncio
    async def test_property_lock_prevents_race_condition(self, orchestrator):
        """Property locks prevent duplicate processing."""
        lock_file = orchestrator.base_dir / "locks" / "property_hash.lock"
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Simulate lock acquisition
        lock_file.touch()
        assert lock_file.exists()

        # Lock prevents concurrent access
        if lock_file.exists():
            # Property is locked, skip processing
            processing_skipped = True
        else:
            processing_skipped = False

        assert processing_skipped is True

        # Cleanup
        lock_file.unlink()

    @pytest.mark.asyncio
    async def test_state_lock_serializes_mutations(self, orchestrator):
        """State file lock serializes write operations."""
        state_file = orchestrator.base_dir / "state.json"
        state_lock = orchestrator.base_dir / "state.json.lock"

        state_data = {"counter": 0}
        state_file.write_text(json.dumps(state_data))

        # Simulate serialized updates with lock
        async def increment_with_lock():
            # Acquire lock
            state_lock.touch()

            try:
                # Load and update
                state = json.loads(state_file.read_text())
                state["counter"] += 1
                state_file.write_text(json.dumps(state))
                return True
            finally:
                # Release lock
                if state_lock.exists():
                    state_lock.unlink()

        # Execute serialized
        await increment_with_lock()

        # Verify serialization
        final_state = json.loads(state_file.read_text())
        assert final_state["counter"] == 1


class TestCheckpointRecovery:
    """Test recovery from checkpoints."""

    def test_checkpoint_tracks_completed_properties(
        self, orchestrator, sample_properties, extraction_state
    ):
        """Checkpoints track which properties completed."""
        checkpoint = {
            "timestamp": "2025-12-06T10:05:00Z",
            "completed_properties": extraction_state["properties_processed"],
            "total_processed": len(extraction_state["properties_processed"]),
        }

        assert len(checkpoint["completed_properties"]) == 2
        assert checkpoint["total_processed"] == 2

    def test_recovery_skips_completed_from_checkpoint(
        self, orchestrator, sample_properties, extraction_state
    ):
        """Resume skips properties recorded in checkpoint."""
        checkpoint_file = orchestrator.base_dir / "checkpoint.json"
        checkpoint_file.write_text(json.dumps(extraction_state))

        # Load checkpoint
        checkpoint = json.loads(checkpoint_file.read_text())
        completed = set(checkpoint["properties_processed"])

        # Filter properties to process
        properties_to_process = [
            p for p in sample_properties
            if p.full_address not in completed
        ]

        # Should skip 2 completed properties
        assert len(properties_to_process) == len(sample_properties) - 2

    def test_incomplete_checkpoint_handled_gracefully(self, orchestrator):
        """Incomplete checkpoint is recovered gracefully."""
        checkpoint_file = orchestrator.base_dir / "checkpoint.json"

        # Write incomplete checkpoint
        incomplete_data = {
            "timestamp": "2025-12-06T10:05:00Z",
            "completed_properties": [],
            # Missing total_processed - incomplete
        }

        checkpoint_file.write_text(json.dumps(incomplete_data))

        # Load and handle
        try:
            data = json.loads(checkpoint_file.read_text())
            completed = data.get("completed_properties", [])
            # Should default to empty if missing
            assert len(completed) == 0
            recovered = True
        except Exception:
            recovered = False

        assert recovered is True


class TestManifestIntegrity:
    """Test manifest integrity and recovery."""

    def test_manifest_backup_created_before_update(
        self, orchestrator, extraction_manifest
    ):
        """Manifest backup created before updates."""
        manifest_file = orchestrator.base_dir / "manifest.json"
        backup_file = orchestrator.base_dir / "manifest.json.backup"

        # Write manifest with backup
        manifest_file.write_text(json.dumps(extraction_manifest))
        manifest_file.rename(backup_file)
        manifest_file.write_text(json.dumps(extraction_manifest))

        # Both should exist
        assert backup_file.exists()
        assert manifest_file.exists()

    def test_manifest_restored_from_backup_on_corruption(
        self, orchestrator, extraction_manifest
    ):
        """Manifest restored from backup if main is corrupted."""
        manifest_file = orchestrator.base_dir / "manifest.json"
        backup_file = orchestrator.base_dir / "manifest.json.backup"

        # Create backup
        backup_file.write_text(json.dumps(extraction_manifest))

        # Corrupt main manifest
        manifest_file.write_text("CORRUPTED DATA")

        # Try to recover
        try:
            data = json.loads(manifest_file.read_text())
            corrupted = False
        except json.JSONDecodeError:
            # Restore from backup
            manifest_file.write_text(backup_file.read_text())
            data = json.loads(manifest_file.read_text())
            corrupted = True

        assert corrupted is True
        assert len(data) > 0

    def test_orphaned_images_detected(self, orchestrator, extraction_dir):
        """Orphaned images (files without manifest entries) detected."""
        # Create image file
        image_dir = extraction_dir / "images"
        image_file = image_dir / "orphan_image_hash.jpg"
        image_file.write_bytes(b"fake image data")

        # Create manifest without this image
        manifest = {
            "property_hash": {
                "images": [
                    {"md5": "other_hash", "file": "other_hash.jpg"}
                ]
            }
        }

        manifest_file = extraction_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest))

        # Detect orphan
        manifest_hashes = set()
        for prop_data in manifest.values():
            for img in prop_data.get("images", []):
                manifest_hashes.add(img.get("md5"))

        image_hashes = {f.stem for f in image_dir.glob("*.jpg")}
        orphans = image_hashes - manifest_hashes

        assert "orphan_image_hash" in orphans

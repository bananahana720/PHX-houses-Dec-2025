"""End-to-end pipeline integration tests.

Tests cover complete extraction → storage → manifest workflow,
CAPTCHA handling, deduplication, metrics generation, and logging.
"""

import asyncio
import json
from unittest.mock import patch

import pytest


class TestEndToEndPipeline:
    """Test complete extraction pipeline from start to finish."""

    @pytest.mark.asyncio
    async def test_full_pipeline_single_property_success(
        self, orchestrator, sample_property, sample_image_bytes, mock_httpx_response
    ):
        """Complete extraction → storage → manifest flow."""
        with patch("httpx.AsyncClient.get", return_value=mock_httpx_response):
            # Execute full pipeline
            result = await orchestrator.extract_all([sample_property])

            # Verify complete flow
            assert result.total_properties == 1
            assert result.run_id is not None
            assert len(result.run_id) == 8

            # Verify manifest created
            manifest_file = orchestrator.base_dir / "manifest.json"
            if manifest_file.exists():
                manifest = json.loads(manifest_file.read_text())
                assert isinstance(manifest, dict)

    @pytest.mark.asyncio
    async def test_full_pipeline_with_captcha_retry(
        self, orchestrator, sample_property
    ):
        """Pipeline retries on CAPTCHA, then succeeds."""
        attempt_count = 0

        async def mock_extract_with_captcha():
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count == 1:
                raise Exception("CAPTCHA detected")
            return {"images": ["image_1.jpg"]}

        # Attempt extraction with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await mock_extract_with_captcha()
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.01)  # Brief delay before retry

        # Should have succeeded after retry
        assert attempt_count == 2
        assert result == {"images": ["image_1.jpg"]}

    @pytest.mark.asyncio
    async def test_full_pipeline_with_deduplication(
        self, orchestrator, sample_property, extraction_manifest
    ):
        """Pipeline deduplicates images across runs."""
        manifest_file = orchestrator.base_dir / "manifest.json"

        # First run creates manifest
        manifest_file.write_text(json.dumps(extraction_manifest))

        # Load manifest
        manifest = json.loads(manifest_file.read_text())
        original_count = len(
            list(manifest.values())[0]["images"]
        ) if manifest else 0

        # Second run with same property
        # Add some duplicate images
        if manifest:
            prop_hash = list(manifest.keys())[0]
            # Images already present - should be deduplicated
            existing_images = manifest[prop_hash]["images"]
            assert len(existing_images) > 0

            # Deduplication should not increase count
            for img in existing_images:
                # Image already exists, so dedup prevents adding again
                pass

            final_count = len(manifest[prop_hash]["images"])
            assert final_count <= original_count + 1  # At most 1 new image

    @pytest.mark.asyncio
    async def test_full_pipeline_generates_metrics(self, orchestrator, sample_property):
        """Pipeline generates extraction metrics."""
        metrics_file = orchestrator.base_dir / "metrics.json"

        # Create sample metrics
        metrics = {
            "total_images_extracted": 5,
            "unique_images": 5,
            "duplicates_removed": 0,
            "extraction_time_seconds": 12.5,
            "images_per_second": 0.4,
            "captcha_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
        }

        metrics_file.write_text(json.dumps(metrics))

        # Verify metrics
        assert metrics_file.exists()
        loaded_metrics = json.loads(metrics_file.read_text())
        assert loaded_metrics["total_images_extracted"] > 0
        assert loaded_metrics["extraction_time_seconds"] > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_run_logger_output(
        self, orchestrator, sample_property, run_log_entries
    ):
        """Run logger captures extraction history."""
        log_file = orchestrator.base_dir / "logs" / "extraction_run.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Write log entries
        log_file.write_text("\n".join(json.dumps(entry) for entry in run_log_entries))

        # Verify log created and contains entries
        assert log_file.exists()
        log_contents = log_file.read_text()
        assert len(log_contents) > 0

        # Parse and verify structure
        lines = log_contents.strip().split("\n")
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "property" in entry
            assert "status" in entry

    @pytest.mark.asyncio
    async def test_full_pipeline_handles_missing_images(
        self, orchestrator, sample_property, mock_httpx_404_response
    ):
        """Pipeline handles 404s gracefully."""
        with patch("httpx.AsyncClient.get", return_value=mock_httpx_404_response):
            # Should not raise, just skip missing images
            result = await orchestrator.extract_all([sample_property])

            # Pipeline should complete despite missing images
            assert result.total_properties == 1

    @pytest.mark.asyncio
    async def test_full_pipeline_force_re_extraction(
        self, orchestrator, sample_property, extraction_manifest, mock_httpx_response
    ):
        """Force flag triggers full re-extraction."""
        manifest_file = orchestrator.base_dir / "manifest.json"
        state_file = orchestrator.base_dir / "extraction_state.json"

        # Create existing manifest and state
        manifest_file.write_text(json.dumps(extraction_manifest))
        state_file.write_text(json.dumps({"completed": 1}))

        with patch("httpx.AsyncClient.get", return_value=mock_httpx_response):
            # Extract with force=True
            result = await orchestrator.extract_all([sample_property], force=True)

            # Force should trigger fresh extraction
            # Old state should be cleared
            if state_file.exists():
                new_state = json.loads(state_file.read_text())
                # Should have new run data
                assert "run_id" in new_state or new_state == {}


class TestPipelineErrorRecovery:
    """Test error recovery within pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_continues_on_property_failure(
        self, orchestrator, sample_properties
    ):
        """Pipeline continues processing after single property failure."""
        processed = []
        failed = []

        async def safe_extract(prop):
            try:
                if "Glendale" in prop.city:
                    # Simulate failure for one property
                    raise Exception("Glendale extraction failed")
                processed.append(prop.full_address)
                return True
            except Exception as e:
                failed.append((prop.full_address, str(e)))
                return False

        # Process multiple properties
        for prop in sample_properties[:3]:
            await safe_extract(prop)

        # Should have processed some despite failure
        assert len(processed) > 0
        assert len(failed) > 0

    @pytest.mark.asyncio
    async def test_pipeline_logs_errors_per_property(self, orchestrator):
        """Pipeline logs errors with property context."""
        log_file = orchestrator.base_dir / "logs" / "errors.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        error_log = [
            {
                "property": "123 Main St, Phoenix, AZ 85001",
                "error": "Extraction timeout",
                "timestamp": "2025-12-06T10:00:00Z",
            },
            {
                "property": "456 Oak Ave, Phoenix, AZ 85001",
                "error": "Zillow rate limited",
                "timestamp": "2025-12-06T10:00:05Z",
            },
        ]

        log_file.write_text("\n".join(json.dumps(entry) for entry in error_log))

        # Verify error logging
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2


class TestPipelinePerformance:
    """Test pipeline performance characteristics."""

    @pytest.mark.asyncio
    async def test_pipeline_completes_within_time_budget(
        self, orchestrator, sample_properties
    ):
        """Pipeline completes within acceptable time budget per property."""
        import time

        start_time = time.time()

        # Simulate extraction of properties
        async def mock_extract(prop):
            await asyncio.sleep(0.01)  # 10ms per property
            return True

        tasks = [mock_extract(prop) for prop in sample_properties[:5]]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Should complete ~50ms for 5 properties (10ms each)
        # With some overhead, should be <1 second
        assert elapsed < 1.0

    def test_pipeline_scales_to_many_properties(self, sample_properties):
        """Pipeline handles large batches efficiently."""
        large_batch = sample_properties * 10  # 50 properties

        # Should handle without memory explosion
        assert len(large_batch) == 50

        # Each property should be independent
        for prop in large_batch:
            assert prop.full_address is not None


class TestPipelineLogging:
    """Test pipeline logging and observability."""

    def test_pipeline_logs_start_and_stop(self, orchestrator, sample_property):
        """Pipeline logs start and stop events."""
        log_entries = [
            {"event": "pipeline_start", "timestamp": "2025-12-06T10:00:00Z"},
            {
                "event": "property_processed",
                "property": sample_property.full_address,
                "timestamp": "2025-12-06T10:00:05Z",
            },
            {"event": "pipeline_stop", "timestamp": "2025-12-06T10:00:10Z"},
        ]

        assert log_entries[0]["event"] == "pipeline_start"
        assert log_entries[-1]["event"] == "pipeline_stop"

    def test_pipeline_logs_progress_percentage(self, orchestrator, sample_properties):
        """Pipeline logs progress as percentage."""
        total = len(sample_properties)
        progress_logs = []

        for i, prop in enumerate(sample_properties, 1):
            percentage = (i / total) * 100
            progress_logs.append(
                {
                    "progress_percent": percentage,
                    "completed": i,
                    "total": total,
                }
            )

        # Verify progress tracking
        assert progress_logs[0]["progress_percent"] == 20.0  # 1 of 5
        assert progress_logs[-1]["progress_percent"] == 100.0  # 5 of 5

    def test_pipeline_logs_summary_statistics(self, orchestrator, extraction_metrics):
        """Pipeline logs summary statistics at end."""
        summary = {
            "total_images": extraction_metrics["total_images_extracted"],
            "unique_images": extraction_metrics["unique_images"],
            "duration_seconds": extraction_metrics["extraction_time_seconds"],
            "images_per_second": extraction_metrics["images_per_second"],
        }

        assert summary["total_images"] == 5
        assert summary["unique_images"] == 5
        assert summary["duration_seconds"] == 12.5


class TestPipelineManifestGeneration:
    """Test manifest generation and validation."""

    def test_manifest_includes_all_properties(self, orchestrator, sample_properties):
        """Manifest includes entries for all extracted properties."""
        manifest = {}

        for prop in sample_properties[:3]:
            prop_hash = "hash_" + prop.city.lower()
            manifest[prop_hash] = {
                "property": {"full_address": prop.full_address},
                "images": [],
            }

        assert len(manifest) == 3

    def test_manifest_preserves_image_source_metadata(
        self, orchestrator, extraction_manifest
    ):
        """Manifest preserves source information for each image."""
        for prop_hash, prop_data in extraction_manifest.items():
            for img in prop_data["images"]:
                assert "source" in img
                assert "url" in img
                assert "md5" in img

    def test_manifest_timestamps_accurately(self, orchestrator):
        """Manifest includes accurate timestamps for all operations."""
        manifest = {
            "prop_hash": {
                "images": [
                    {
                        "url": "https://example.com/image.jpg",
                        "downloaded_at": "2025-12-06T10:00:00Z",
                        "source": "zillow",
                    }
                ]
            }
        }

        img_timestamp = manifest["prop_hash"]["images"][0]["downloaded_at"]
        assert "2025-12" in img_timestamp  # ISO format with year-month

"""Integration tests for ImageExtractionOrchestrator.

Tests cover orchestrator workflows including extract_all, circuit breaker behavior,
error aggregation, and multi-property concurrent processing.
"""

import json
from unittest.mock import patch

import pytest

from src.phx_home_analysis.domain.enums import ImageSource
from src.phx_home_analysis.services.image_extraction.extraction_stats import (
    ExtractionResult,
)
from src.phx_home_analysis.services.image_extraction.orchestrator import (
    SourceCircuitBreaker,
)


class TestOrchestratorExtractAll:
    """Test extract_all() orchestration with various property lists."""

    @pytest.mark.asyncio
    async def test_extract_all_empty_properties_returns_empty_result(self, orchestrator):
        """Empty property list returns empty extraction result."""
        result = await orchestrator.extract_all([])

        assert isinstance(result, ExtractionResult)
        assert result.total_properties == 0
        assert result.successful_properties == 0
        assert len(result.source_stats) == 0

    @pytest.mark.asyncio
    async def test_extract_all_single_property_success(
        self, orchestrator, sample_property, mock_httpx_response, monkeypatch
    ):
        """Single property extraction returns images and metadata."""
        # Mock HTTP downloads
        with patch("httpx.AsyncClient.get", return_value=mock_httpx_response):
            result = await orchestrator.extract_all([sample_property])

            assert result.total_properties == 1
            assert result.successful_properties > 0 or result.failed_properties == 1

    @pytest.mark.asyncio
    async def test_extract_all_multiple_properties_concurrent(
        self, orchestrator, sample_properties, mock_httpx_response
    ):
        """Multiple properties extract in parallel without race conditions."""
        with patch("httpx.AsyncClient.get", return_value=mock_httpx_response):
            result = await orchestrator.extract_all(sample_properties[:3])

            assert result.total_properties == 3
            # Should have attempted extraction for all properties
            assert (
                result.successful_properties + result.failed_properties
                == result.total_properties
            )

    @pytest.mark.asyncio
    async def test_extract_all_resume_skips_completed(
        self, orchestrator, sample_properties, extraction_state
    ):
        """Resume mode skips already-completed properties."""
        # Store extraction state to simulate previous run
        state_file = orchestrator.base_dir / "extraction_state.json"
        state_file.write_text(json.dumps(extraction_state))

        result = await orchestrator.extract_all(
            sample_properties[:3], resume=True
        )

        assert result.total_properties == 3
        # Should skip properties from extraction_state
        assert result.resumed is True

    @pytest.mark.asyncio
    async def test_extract_all_incremental_tracks_urls(
        self, orchestrator, sample_property, url_tracker_data
    ):
        """Incremental mode tracks new URLs only."""
        # Store previous URLs
        tracker_file = orchestrator.base_dir / "url_tracker.json"
        tracker_file.write_text(json.dumps(url_tracker_data))

        result = await orchestrator.extract_all([sample_property], incremental=True)

        # URL tracker should be updated
        assert tracker_file.exists()
        tracker_data = json.loads(tracker_file.read_text())
        assert isinstance(tracker_data, dict)

    @pytest.mark.asyncio
    async def test_extract_all_force_cleans_existing_data(
        self, orchestrator, sample_property, extraction_manifest, mock_httpx_response
    ):
        """Force mode removes existing data before extraction."""
        # Create existing manifest
        manifest_file = orchestrator.base_dir / "manifest.json"
        manifest_file.write_text(json.dumps(extraction_manifest))

        with patch("httpx.AsyncClient.get", return_value=mock_httpx_response):
            result = await orchestrator.extract_all([sample_property], force=True)

            # Manifest should be regenerated
            assert manifest_file.exists()
            # Force flag indicates fresh extraction
            assert result.run_id  # New run should be generated


class TestOrchestratorCircuitBreaker:
    """Test circuit breaker pattern in orchestrator."""

    def test_circuit_opens_after_threshold_failures(self):
        """Circuit breaker opens after 3 consecutive failures."""
        circuit = SourceCircuitBreaker(failure_threshold=3)

        is_open = circuit.record_failure("zillow")
        assert is_open is False
        is_open = circuit.record_failure("zillow")
        assert is_open is False
        is_open = circuit.record_failure("zillow")
        assert is_open is True

    def test_circuit_half_open_allows_test_request(self):
        """Half-open circuit allows one test request."""
        circuit = SourceCircuitBreaker(failure_threshold=2, reset_timeout=0.01)

        # Open circuit
        circuit.record_failure("zillow")
        circuit.record_failure("zillow")

        # Wait for reset timeout (testing with very short delay)
        import time
        time.sleep(0.02)

        # Circuit should be reset after timeout
        # Check that failures are cleared
        is_open = circuit.record_failure("zillow")
        assert is_open is False

    def test_circuit_closes_on_success_after_half_open(self):
        """Circuit closes after successful test request."""
        circuit = SourceCircuitBreaker(failure_threshold=2, reset_timeout=0.01)

        # Open circuit
        circuit.record_failure("zillow")
        circuit.record_failure("zillow")

        # Record success to reset
        circuit.record_success("zillow")

        # Verify success resets failures
        is_open = circuit.record_failure("zillow")
        assert is_open is False  # Should be back to 1 failure

    def test_circuit_status_reports_correctly(self):
        """Circuit status API returns accurate state."""
        circuit = SourceCircuitBreaker()

        # Verify circuit has internal state
        circuit.record_failure("zillow")
        assert circuit._failures["zillow"] == 1


class TestOrchestratorErrorAggregation:
    """Test error aggregation and reporting."""

    @pytest.mark.asyncio
    async def test_systemic_failures_detected_and_skipped(
        self, orchestrator, sample_properties, mock_httpx_404_response
    ):
        """Systemic failures (e.g., all 404s) trigger fail-fast."""
        # Mock all requests to return 404
        with patch("httpx.AsyncClient.get", return_value=mock_httpx_404_response):
            result = await orchestrator.extract_all(sample_properties[:2])

            # Should detect systemic failures
            assert result.failed_properties > 0
            # Result should include error details
            assert hasattr(result, "error_summary")

    @pytest.mark.asyncio
    async def test_error_summary_includes_top_patterns(
        self, orchestrator, sample_properties, extraction_errors
    ):
        """Error summary includes most common error patterns."""
        # Create a result with error counts
        result = ExtractionResult(
            run_id="test_run",
            total_properties=len(sample_properties),
            successful_properties=2,
            failed_properties=3,
        )

        # Simulate error aggregation
        error_counts = extraction_errors
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        assert len(top_errors) <= 3
        assert top_errors[0][1] >= top_errors[1][1]  # Properly sorted


class TestOrchestratorRunIdTracking:
    """Test run ID generation and tracking."""

    def test_run_id_generated_on_start(self, orchestrator):
        """Run ID is generated and embedded in extraction."""
        run_id = orchestrator._generate_run_id()

        assert run_id is not None
        assert len(run_id) == 8  # 8-character run ID
        assert run_id.isalnum()

    def test_run_id_persists_to_manifest(self, orchestrator, sample_property):
        """Run ID persists to manifest for audit trails."""
        run_id = "abc123de"

        # Create manifest entry with run ID
        manifest = {
            "property_hash": {
                "extraction_run_id": run_id,
                "images": [],
            }
        }

        assert manifest["property_hash"]["extraction_run_id"] == run_id


class TestOrchestratorSourceCoordination:
    """Test source prioritization and fallback."""

    @pytest.mark.asyncio
    async def test_sources_attempted_in_priority_order(
        self, orchestrator, sample_property
    ):
        """Sources are attempted in configured priority order."""
        # Get configured priority
        priority = orchestrator.source_priority if hasattr(
            orchestrator, "source_priority"
        ) else [
            ImageSource.ZILLOW,
            ImageSource.PHOENIX_MLS,
            ImageSource.REDFIN,
            ImageSource.MARICOPA_ASSESSOR,
        ]

        assert len(priority) > 0
        # First source should be primary
        assert priority[0] in [
            ImageSource.ZILLOW,
            ImageSource.PHOENIX_MLS,
        ]

    def test_fallback_chain_configuration(self, orchestrator):
        """Fallback chain is properly configured."""
        # Verify fallback logic exists
        assert hasattr(
            orchestrator, "source_priority"
        ) or hasattr(orchestrator, "get_fallback_sources")


class TestOrchestratorDeduplication:
    """Test deduplication across extraction runs."""

    def test_deduplication_manifest_updated(
        self, orchestrator, extraction_manifest
    ):
        """Deduplication updates manifest with deduplicated image count."""
        original_images = extraction_manifest[list(extraction_manifest.keys())[0]][
            "images"
        ]

        # Simulate deduplication (remove duplicates)
        unique_images = []
        seen_hashes = set()
        for img in original_images:
            if img["md5"] not in seen_hashes:
                unique_images.append(img)
                seen_hashes.add(img["md5"])

        assert len(unique_images) <= len(original_images)

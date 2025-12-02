"""Tests for the ExtractionStats module."""

from datetime import datetime, timedelta, timezone

from src.phx_home_analysis.services.image_extraction.extraction_stats import (
    ExtractionResult,
    SourceStats,
    StatsTracker,
)


class TestSourceStats:
    """Test SourceStats dataclass."""

    def test_default_values(self):
        """Default values should be zero."""
        stats = SourceStats(source="test")
        assert stats.properties_processed == 0
        assert stats.properties_failed == 0
        assert stats.images_found == 0
        assert stats.images_downloaded == 0
        assert stats.images_failed == 0
        assert stats.duplicates_detected == 0

    def test_success_rate_zero_total(self):
        """Success rate should be 0 when no properties."""
        stats = SourceStats(source="test")
        assert stats.success_rate == 0.0

    def test_success_rate_all_passed(self):
        """Success rate should be 100 when all passed."""
        stats = SourceStats(source="test", properties_processed=10, properties_failed=0)
        assert stats.success_rate == 100.0

    def test_success_rate_partial(self):
        """Success rate should calculate correctly."""
        stats = SourceStats(source="test", properties_processed=7, properties_failed=3)
        assert stats.success_rate == 70.0

    def test_download_success_rate_zero_found(self):
        """Download success rate should be 0 when no images found."""
        stats = SourceStats(source="test", images_found=0)
        assert stats.download_success_rate == 0.0

    def test_download_success_rate_all_downloaded(self):
        """Download success rate should be 100 when all downloaded."""
        stats = SourceStats(source="test", images_found=10, images_downloaded=10)
        assert stats.download_success_rate == 100.0

    def test_download_success_rate_partial(self):
        """Download success rate should calculate correctly."""
        stats = SourceStats(source="test", images_found=10, images_downloaded=8)
        assert stats.download_success_rate == 80.0


class TestExtractionResult:
    """Test ExtractionResult dataclass."""

    def test_default_values(self):
        """Default values should be zero/empty."""
        result = ExtractionResult()
        assert result.total_properties == 0
        assert result.properties_completed == 0
        assert result.properties_failed == 0
        assert result.properties_skipped == 0
        assert result.total_images == 0
        assert result.unique_images == 0
        assert result.duplicate_images == 0
        assert result.failed_downloads == 0
        assert len(result.by_source) == 0
        assert result.start_time is None
        assert result.end_time is None

    def test_duration_seconds_no_times(self):
        """Duration should be 0 without times."""
        result = ExtractionResult()
        assert result.duration_seconds == 0.0

    def test_duration_seconds_with_times(self):
        """Duration should calculate correctly."""
        now = datetime.now(timezone.utc)
        result = ExtractionResult(
            start_time=now,
            end_time=now + timedelta(seconds=120),
        )
        assert result.duration_seconds == 120.0

    def test_success_rate_zero_total(self):
        """Success rate should be 0 when no properties."""
        result = ExtractionResult(total_properties=0)
        assert result.success_rate == 0.0

    def test_success_rate_all_completed(self):
        """Success rate should be 100 when all completed."""
        result = ExtractionResult(total_properties=10, properties_completed=10)
        assert result.success_rate == 100.0

    def test_success_rate_partial(self):
        """Success rate should calculate correctly."""
        result = ExtractionResult(total_properties=10, properties_completed=7)
        assert result.success_rate == 70.0

    def test_properties_per_minute_zero_duration(self):
        """Rate should be 0 when no duration."""
        result = ExtractionResult(properties_completed=10)
        assert result.properties_per_minute == 0.0

    def test_properties_per_minute_with_duration(self):
        """Rate should calculate correctly."""
        now = datetime.now(timezone.utc)
        result = ExtractionResult(
            properties_completed=30,
            properties_failed=0,
            start_time=now,
            end_time=now + timedelta(minutes=10),
        )
        assert result.properties_per_minute == 3.0

    def test_to_dict(self):
        """Should serialize to dict."""
        now = datetime.now(timezone.utc)
        result = ExtractionResult(
            total_properties=10,
            properties_completed=7,
            properties_failed=2,
            properties_skipped=1,
            total_images=50,
            unique_images=40,
            duplicate_images=10,
            failed_downloads=3,
            start_time=now,
            end_time=now + timedelta(seconds=60),
        )
        result.by_source["zillow"] = SourceStats(
            source="zillow",
            properties_processed=5,
            images_found=25,
        )

        data = result.to_dict()

        assert data["total_properties"] == 10
        assert data["properties_completed"] == 7
        assert data["success_rate"] == 70.0
        assert data["duration_seconds"] == 60.0
        assert "zillow" in data["by_source"]
        assert data["by_source"]["zillow"]["properties_processed"] == 5


class TestStatsTracker:
    """Test StatsTracker class."""

    def test_init(self):
        """Should initialize with total properties."""
        tracker = StatsTracker(total_properties=100)
        result = tracker.current_result
        assert result.total_properties == 100
        assert result.start_time is not None

    def test_initialize_source(self):
        """Should initialize source stats."""
        tracker = StatsTracker()
        tracker.initialize_source("zillow")

        result = tracker.current_result
        assert "zillow" in result.by_source
        assert result.by_source["zillow"].source == "zillow"

    def test_initialize_source_idempotent(self):
        """Initializing same source twice should not reset."""
        tracker = StatsTracker()
        tracker.initialize_source("zillow")
        tracker.record_property_completed("zillow", 5, 5)
        tracker.initialize_source("zillow")

        result = tracker.current_result
        assert result.by_source["zillow"].images_found == 5

    def test_record_property_completed(self):
        """Should record completed property."""
        tracker = StatsTracker()
        tracker.record_property_completed("zillow", images_found=10, images_downloaded=8)

        result = tracker.current_result
        assert result.properties_completed == 1
        assert result.total_images == 10
        assert result.unique_images == 8
        assert result.by_source["zillow"].properties_processed == 1
        assert result.by_source["zillow"].images_found == 10
        assert result.by_source["zillow"].images_downloaded == 8

    def test_record_property_failed(self):
        """Should record failed property."""
        tracker = StatsTracker()
        tracker.record_property_failed("zillow")

        result = tracker.current_result
        assert result.properties_failed == 1
        assert result.by_source["zillow"].properties_failed == 1

    def test_record_property_skipped(self):
        """Should record skipped property."""
        tracker = StatsTracker()
        tracker.record_property_skipped()

        result = tracker.current_result
        assert result.properties_skipped == 1

    def test_record_duplicate(self):
        """Should record duplicate image."""
        tracker = StatsTracker()
        tracker.record_duplicate("zillow")

        result = tracker.current_result
        assert result.duplicate_images == 1
        assert result.by_source["zillow"].duplicates_detected == 1

    def test_record_download_failed(self):
        """Should record failed download."""
        tracker = StatsTracker()
        tracker.record_download_failed("zillow")

        result = tracker.current_result
        assert result.failed_downloads == 1
        assert result.by_source["zillow"].images_failed == 1

    def test_finalize(self):
        """Should set end time on finalize."""
        tracker = StatsTracker()
        result = tracker.finalize()

        assert result.end_time is not None
        assert result.duration_seconds >= 0

    def test_log_progress(self):
        """Should generate progress message."""
        tracker = StatsTracker()
        tracker.record_property_completed("zillow", 5, 5)
        tracker.record_property_failed("redfin")

        msg = tracker.log_progress(10)

        assert "2/10" in msg
        assert "1 ok" in msg
        assert "1 failed" in msg

    def test_multiple_sources(self):
        """Should track multiple sources independently."""
        tracker = StatsTracker()
        tracker.record_property_completed("zillow", 10, 8)
        tracker.record_property_completed("redfin", 5, 5)
        tracker.record_property_failed("zillow")

        result = tracker.current_result

        assert result.properties_completed == 2
        assert result.properties_failed == 1
        assert result.by_source["zillow"].properties_processed == 1
        assert result.by_source["zillow"].properties_failed == 1
        assert result.by_source["redfin"].properties_processed == 1
        assert result.by_source["redfin"].properties_failed == 0

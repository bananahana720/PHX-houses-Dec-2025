"""Statistics tracking for image extraction operations.

Provides data classes and tracking utilities for monitoring extraction
progress and generating summary reports.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceStats:
    """Statistics for a single image source.

    Tracks extraction performance metrics per source (e.g., Zillow, Redfin).
    """

    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0

    @property
    def success_rate(self) -> float:
        """Percentage of properties successfully processed.

        Returns:
            Success rate 0-100
        """
        total = self.properties_processed + self.properties_failed
        if total == 0:
            return 0.0
        return (self.properties_processed / total) * 100

    @property
    def download_success_rate(self) -> float:
        """Percentage of images successfully downloaded.

        Returns:
            Download success rate 0-100
        """
        if self.images_found == 0:
            return 0.0
        return (self.images_downloaded / self.images_found) * 100


@dataclass
class ExtractionResult:
    """Aggregated results from image extraction process.

    Contains overall statistics across all sources and properties.
    """

    total_properties: int = 0
    properties_completed: int = 0
    properties_failed: int = 0
    properties_skipped: int = 0
    total_images: int = 0
    unique_images: int = 0
    duplicate_images: int = 0
    failed_downloads: int = 0
    by_source: dict[str, SourceStats] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """Total extraction duration in seconds.

        Returns:
            Duration or 0 if not complete
        """
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Percentage of properties successfully processed.

        Returns:
            Success rate 0-100
        """
        if self.total_properties == 0:
            return 0.0
        return (self.properties_completed / self.total_properties) * 100

    @property
    def properties_per_minute(self) -> float:
        """Processing rate in properties per minute.

        Returns:
            Rate or 0 if duration is 0
        """
        if self.duration_seconds == 0:
            return 0.0
        processed = self.properties_completed + self.properties_failed
        return (processed / self.duration_seconds) * 60

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation
        """
        return {
            "total_properties": self.total_properties,
            "properties_completed": self.properties_completed,
            "properties_failed": self.properties_failed,
            "properties_skipped": self.properties_skipped,
            "total_images": self.total_images,
            "unique_images": self.unique_images,
            "duplicate_images": self.duplicate_images,
            "failed_downloads": self.failed_downloads,
            "by_source": {
                name: {
                    "properties_processed": stats.properties_processed,
                    "properties_failed": stats.properties_failed,
                    "images_found": stats.images_found,
                    "images_downloaded": stats.images_downloaded,
                    "images_failed": stats.images_failed,
                    "duplicates_detected": stats.duplicates_detected,
                    "success_rate": stats.success_rate,
                    "download_success_rate": stats.download_success_rate,
                }
                for name, stats in self.by_source.items()
            },
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "properties_per_minute": self.properties_per_minute,
        }


class StatsTracker:
    """Tracks extraction statistics during processing.

    Provides convenient methods for recording events during extraction
    and generating the final ExtractionResult.
    """

    def __init__(self, total_properties: int = 0):
        """Initialize stats tracker.

        Args:
            total_properties: Total number of properties to process
        """
        self._result = ExtractionResult(
            total_properties=total_properties,
            start_time=datetime.now().astimezone(),
        )

    def initialize_source(self, source: str) -> None:
        """Initialize stats for a source.

        Args:
            source: Source identifier
        """
        if source not in self._result.by_source:
            self._result.by_source[source] = SourceStats(source=source)

    def record_property_completed(
        self,
        source: str,
        images_found: int = 0,
        images_downloaded: int = 0,
    ) -> None:
        """Record successful property processing.

        Args:
            source: Source that processed the property
            images_found: Number of image URLs found
            images_downloaded: Number of images successfully downloaded
        """
        self._result.properties_completed += 1
        self.initialize_source(source)
        stats = self._result.by_source[source]
        stats.properties_processed += 1
        stats.images_found += images_found
        stats.images_downloaded += images_downloaded
        self._result.total_images += images_found
        self._result.unique_images += images_downloaded

    def record_property_failed(self, source: str) -> None:
        """Record failed property processing.

        Args:
            source: Source that failed
        """
        self._result.properties_failed += 1
        self.initialize_source(source)
        self._result.by_source[source].properties_failed += 1

    def record_property_skipped(self) -> None:
        """Record skipped property (already processed)."""
        self._result.properties_skipped += 1

    def record_duplicate(self, source: str) -> None:
        """Record duplicate image detection.

        Args:
            source: Source where duplicate was found
        """
        self._result.duplicate_images += 1
        self.initialize_source(source)
        self._result.by_source[source].duplicates_detected += 1

    def record_download_failed(self, source: str) -> None:
        """Record failed image download.

        Args:
            source: Source where download failed
        """
        self._result.failed_downloads += 1
        self.initialize_source(source)
        self._result.by_source[source].images_failed += 1

    def finalize(self) -> ExtractionResult:
        """Finalize and return results.

        Sets end time and returns the complete result.

        Returns:
            Completed ExtractionResult
        """
        self._result.end_time = datetime.now().astimezone()
        return self._result

    @property
    def current_result(self) -> ExtractionResult:
        """Get current result (without finalizing).

        Returns:
            Current ExtractionResult state
        """
        return self._result

    def log_progress(self, total_to_process: int) -> str:
        """Generate progress log message.

        Args:
            total_to_process: Total properties being processed this run

        Returns:
            Formatted progress string
        """
        completed = self._result.properties_completed + self._result.properties_failed
        return (
            f"Progress: {completed}/{total_to_process} properties "
            f"({self._result.properties_completed} ok, "
            f"{self._result.properties_failed} failed, "
            f"{self._result.unique_images} images)"
        )

"""Image extraction orchestrator coordinating all sources.

Orchestrates image extraction across multiple sources with deduplication,
standardization, and state persistence for resumable operations.

Features:
    - URL-level tracking for incremental extraction
    - New image detection on re-runs
    - Run history logging for audit trails
    - Verbose batch summaries

Security: Uses asyncio.Lock to prevent race conditions on state/manifest writes.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import httpx

from ...domain.entities import Property
from ...domain.enums import ImageSource, ImageStatus
from ...domain.value_objects import ImageMetadata
from ...errors import is_transient_error
from .deduplicator import DeduplicationError, ImageDeduplicator
from .extraction_stats import ExtractionResult, SourceStats
from .extractors import (
    MaricopaAssessorExtractor,
    PhoenixMLSExtractor,
    PhoenixMLSSearchExtractor,
    RedfinExtractor,
    ZillowExtractor,
)
from .extractors.base import (
    ExtractionError,
    ImageDownloadError,
    ImageExtractor,
    RateLimitError,
    SourceUnavailableError,
)
from .image_processor import ImageProcessor
from .metadata_persister import MetadataPersister
from .metrics import CaptchaMetrics
from .run_logger import PropertyChanges, RunLogger
from .standardizer import ImageProcessingError, ImageStandardizer
from .state_manager import ExtractionState
from .url_tracker import URLTracker

logger = logging.getLogger(__name__)


class SourceCircuitBreaker:
    """Prevents cascade failures by temporarily disabling failing sources.

    Implements the circuit breaker pattern:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Source disabled after threshold failures
    - HALF-OPEN: After reset timeout, allows one test request

    Attributes:
        failure_threshold: Number of consecutive failures to open circuit
        reset_timeout: Seconds before attempting to close circuit
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 300):
        """Initialize circuit breaker with thresholds.

        Args:
            failure_threshold: Consecutive failures before opening circuit (default: 3)
            reset_timeout: Seconds to wait before half-open state (default: 300 = 5 min)
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures: dict[str, int] = defaultdict(int)
        self._disabled_until: dict[str, float] = {}
        self._successes_since_half_open: dict[str, int] = defaultdict(int)

    def record_failure(self, source: str) -> bool:
        """Record a failure for a source.

        Args:
            source: Source identifier (e.g., "zillow", "redfin")

        Returns:
            True if circuit is now open (source disabled)
        """
        self._failures[source] += 1
        self._successes_since_half_open[source] = 0

        if self._failures[source] >= self.failure_threshold:
            self._disabled_until[source] = time.time() + self.reset_timeout
            logger.warning(
                "Circuit OPEN for %s - disabled for %ds after %d failures",
                source,
                self.reset_timeout,
                self._failures[source],
            )
            return True
        return False

    def record_success(self, source: str) -> None:
        """Record a success for a source, potentially closing circuit."""
        if source in self._disabled_until:
            # Half-open state - success closes circuit
            self._successes_since_half_open[source] += 1
            if self._successes_since_half_open[source] >= 2:
                del self._disabled_until[source]
                self._failures[source] = 0
                logger.info("Circuit CLOSED for %s - source recovered", source)
        else:
            # Normal operation - reset failure count
            self._failures[source] = 0

    def is_available(self, source: str) -> bool:
        """Check if a source is available (circuit closed or half-open).

        Returns:
            True if requests should be attempted to this source
        """
        if source not in self._disabled_until:
            return True

        if time.time() >= self._disabled_until[source]:
            # Transition to half-open
            logger.info("Circuit HALF-OPEN for %s - testing recovery", source)
            return True

        return False

    def get_status(self) -> dict[str, str]:
        """Get status of all sources for logging/monitoring.

        Returns:
            Dict mapping source name to status string
        """
        status = {}
        now = time.time()
        for source in set(self._failures.keys()) | set(self._disabled_until.keys()):
            if source not in self._disabled_until:
                status[source] = "closed"
            elif now >= self._disabled_until[source]:
                status[source] = "half-open"
            else:
                remaining = int(self._disabled_until[source] - now)
                status[source] = f"open ({remaining}s remaining)"
        return status


class ErrorAggregator:
    """Detect and skip systemic failures to comply with Axiom 9 (Fail Fast).

    Prevents redundant error logging when the same error pattern occurs repeatedly
    (e.g., 404s from the same base URL across all properties).

    Attributes:
        threshold: Number of identical errors before skipping similar ones
        error_counts: Counter tracking frequency of normalized error patterns
        skip_patterns: Set of error patterns to skip after threshold reached
    """

    def __init__(self, threshold: int = 3):
        """Initialize error aggregator with threshold.

        Args:
            threshold: Number of occurrences before skipping similar errors (default: 3)
        """
        self.threshold = threshold
        self.error_counts: Counter[str] = Counter()
        self.skip_patterns: set[str] = set()

    def record_error(self, error_msg: str) -> bool:
        """Record error and return True if should skip similar errors.

        Args:
            error_msg: Full error message from exception

        Returns:
            True if this error pattern should be skipped (threshold reached)
        """
        # Normalize error message (extract URL pattern or error type)
        normalized = self._normalize_error(error_msg)
        self.error_counts[normalized] += 1

        if self.error_counts[normalized] >= self.threshold:
            if normalized not in self.skip_patterns:
                self.skip_patterns.add(normalized)
                logger.warning(
                    "Systemic failure detected (%dx): %s... Skipping similar errors.",
                    self.threshold,
                    normalized[:100],
                )
            return True
        return False

    def _normalize_error(self, msg: str) -> str:
        """Extract error pattern from message for deduplication.

        For 404 errors, extracts the domain/path pattern.
        For other errors, uses first 100 chars.

        Args:
            msg: Error message to normalize

        Returns:
            Normalized pattern string for comparison
        """
        # For 404 errors, extract the base URL pattern
        if "404" in msg and "http" in msg:
            # Extract domain/path pattern (e.g., https://ssl.cdn-redfin.com/photo/)
            match = re.search(r"(https?://[^/]+(?:/[^/]+){0,2})", msg)
            if match:
                return f"404:{match.group(1)}"
        return msg[:100]

    def should_skip(self, url: str) -> bool:
        """Check if URL matches a known failing pattern.

        Args:
            url: URL to check against skip patterns

        Returns:
            True if URL should be skipped based on known failures
        """
        for pattern in self.skip_patterns:
            if pattern.startswith("404:") and pattern[4:] in url:
                return True
        return False

    def get_summary(self) -> dict[str, int]:
        """Get error frequency summary for logging.

        Returns:
            Dict of top 5 most common error patterns with counts
        """
        return dict(self.error_counts.most_common(5))


class ImageExtractionOrchestrator:
    """Coordinates image extraction across all sources.

    Orchestrates the complete image extraction pipeline:
    1. Extract URLs from each enabled source
    2. Download images with retry logic
    3. Deduplicate using perceptual hashing
    4. Standardize format and size
    5. Save to organized directory structure
    6. Track progress and allow resumption
    """

    def __init__(
        self,
        base_dir: Path,
        enabled_sources: list[ImageSource] | None = None,
        max_concurrent_properties: int | None = None,
        deduplication_threshold: int = 8,
        max_dimension: int = 1024,
        work_items_path: Path | None = None,
    ):
        """Initialize orchestrator with configuration.

        Args:
            base_dir: Base directory for image storage (data/images)
            enabled_sources: List of sources to extract from (all if None)
            max_concurrent_properties: Max properties to process in parallel.
                Defaults to min(cpu_count * 2, 15) for optimal I/O-bound performance
                while respecting rate limiting constraints.
            deduplication_threshold: Hamming distance threshold for duplicates
            max_dimension: Maximum image dimension in pixels
            work_items_path: Path to work_items.json for phase status updates (optional)

        Performance Tuning Notes:
            - Default concurrency is CPU-based since image extraction is I/O-bound
            - Cap at 15 to avoid triggering rate limits on source APIs
            - Minimum of 2 ensures reasonable performance on low-core systems
            - For systems with 4+ cores, this typically yields 8-15 concurrent properties
        """
        self.base_dir = Path(base_dir)
        self.enabled_sources = enabled_sources or list(ImageSource)
        self.work_items_path = Path(work_items_path) if work_items_path else None

        # Compute optimal concurrency: 2x CPU count, bounded between 2 and 15
        # I/O-bound workloads benefit from higher concurrency than CPU-bound
        # Cap at 15 to avoid rate limiting issues with source APIs
        if max_concurrent_properties is None:
            cpu_count = os.cpu_count() or 2
            max_concurrent_properties = max(2, min(cpu_count * 2, 15))

        self.max_concurrent = max_concurrent_properties

        # Create directory structure
        self.processed_dir = self.base_dir / "processed"
        self.raw_dir = self.base_dir / "raw"
        self.metadata_dir = self.base_dir / "metadata"

        for directory in [self.processed_dir, self.raw_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.deduplicator = ImageDeduplicator(
            hash_index_path=self.metadata_dir / "hash_index.json",
            similarity_threshold=deduplication_threshold,
        )
        self.standardizer = ImageStandardizer(
            max_dimension=max_dimension,
            output_format="PNG",
        )
        self.image_processor = ImageProcessor(
            base_dir=self.processed_dir,
            deduplicator=self.deduplicator,
            standardizer=self.standardizer,
        )

        # Initialize metadata persister for listing data
        self.metadata_persister = MetadataPersister(
            enrichment_path=self.base_dir.parent / "enrichment_data.json",
            lineage_path=self.base_dir.parent / "field_lineage.json",
        )

        # State tracking
        self.manifest_path = self.metadata_dir / "image_manifest.json"
        self.state_path = self.metadata_dir / "extraction_state.json"
        self.manifest: dict[str, list[dict]] = self._load_manifest()
        self.state: ExtractionState = self._load_state()

        # URL tracking for incremental extraction
        self.url_tracker = URLTracker.load(self.metadata_dir / "url_tracker.json")

        # Run logging for audit trail
        self.run_logger = RunLogger(self.metadata_dir)

        # Circuit breaker for resilience
        self._circuit_breaker = SourceCircuitBreaker(
            failure_threshold=3,
            reset_timeout=300,  # 5 minutes
        )

        # Error aggregation for Axiom 9 (Fail Fast) compliance
        self._error_aggregator = ErrorAggregator(threshold=3)

        # CAPTCHA metrics tracking
        self.captcha_metrics = CaptchaMetrics()

        # Security: Lock for thread-safe state/manifest mutations
        self._state_lock = asyncio.Lock()

        # HTTP client (shared across extractors)
        self._http_client: httpx.AsyncClient | None = None

        # Run ID for audit trail (8-char identifier)
        self.run_id: str = str(uuid4())[:8]

        # Statistics accumulator for O(1) get_statistics()
        # Populated during extraction, reset on clear_state()
        self._stats_accumulator = {
            "total_images": 0,
            "by_source": defaultdict(int),
            "by_property": defaultdict(int),
            "extraction_errors": 0,
        }

        # Run startup reconciliation if manifest exists
        if self.manifest_path.exists():
            self._run_startup_reconciliation()

    def _load_manifest(self) -> dict[str, list[dict]]:
        """Load image manifest from disk.

        Returns:
            Dict mapping property_address to list of image metadata
        """
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    data = json.load(f)
                    properties = data.get("properties", {})
                    logger.info(f"Loaded manifest with {len(properties)} properties")
                    return dict(properties)  # Type cast for mypy
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load manifest: {e}")

        return {}

    def _atomic_json_write(self, path: Path, data: dict) -> None:
        """Write JSON atomically using temp file + rename.

        Security: Prevents corruption from crashes/interrupts during write.

        Args:
            path: Target file path
            data: Data to serialize as JSON
        """
        import tempfile as tf

        fd, temp_path = tf.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, path)  # Atomic on POSIX and Windows
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _save_manifest(self) -> None:
        """Save image manifest to disk atomically with locking."""
        from phx_home_analysis.services.image_extraction.file_lock import ManifestLock

        locks_dir = self.metadata_dir / "locks"
        locks_dir.mkdir(parents=True, exist_ok=True)

        with ManifestLock(locks_dir):
            # Re-load manifest to merge any concurrent changes
            current_manifest = self._load_manifest()

            # Merge our changes (our properties take precedence)
            for address, images in self.manifest.items():
                current_manifest[address] = images

            data = {
                "version": "2.0.0",
                "last_updated": datetime.now().astimezone().isoformat(),
                "properties": current_manifest,
            }
            self._atomic_json_write(self.manifest_path, data)

            # Update our in-memory copy
            self.manifest = current_manifest

        logger.debug("Saved manifest to disk")

    def _run_startup_reconciliation(self) -> None:
        """
        Run reconciliation check on startup.

        Validates data integrity across manifest, disk files, and URL tracker.
        Logs warnings if quality is below 90%.

        Called automatically from __init__ if manifest exists.
        """
        try:
            from .reconciliation import DataReconciler

            reconciler = DataReconciler(
                manifest_path=self.manifest_path,
                processed_dir=self.processed_dir,
                url_tracker_path=self.metadata_dir / "url_tracker.json",
            )

            report = reconciler.reconcile()

            # Log summary
            logger.info(
                f"Startup reconciliation: overall quality {report.overall_quality:.1f}% "
                f"({report.manifest_image_count} manifest, {report.disk_file_count} disk)"
            )

            # Warn if quality is below 90%
            if not report.is_healthy:
                logger.warning(
                    f"Data quality below 90% ({report.overall_quality:.1f}%): "
                    f"{len(report.orphan_files)} orphans, "
                    f"{len(report.ghost_entries)} ghosts, "
                    f"{len(report.hash_mismatches)} hash mismatches"
                )

                # Log specific issues for debugging
                if report.orphan_files:
                    logger.warning(f"Orphan files (first 5): {report.orphan_files[:5]}")
                if report.ghost_entries:
                    logger.warning(f"Ghost entries (first 5): {report.ghost_entries[:5]}")
                if report.hash_mismatches:
                    logger.warning(f"Hash mismatches (first 5): {report.hash_mismatches[:5]}")

        except Exception as e:
            # Don't fail initialization if reconciliation errors
            logger.warning(f"Startup reconciliation failed: {e}", exc_info=True)

    def _load_state(self) -> ExtractionState:
        """Load extraction state from disk.

        Returns:
            ExtractionState instance
        """
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    data = json.load(f)
                    state = ExtractionState.from_dict(data)
                    logger.info(
                        f"Loaded state: {len(state.completed_properties)} completed, "
                        f"{len(state.failed_properties)} failed"
                    )
                    return state
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load state: {e}")

        return ExtractionState()

    def _save_state(self) -> None:
        """Save extraction state to disk atomically.

        Synchronous version kept for use in cleanup/exit scenarios where
        guaranteed completion before exit is required.
        """
        self._atomic_json_write(self.state_path, self.state.to_dict())
        logger.debug("Saved state to disk")

    async def _save_state_async(self) -> None:
        """Non-blocking state save using thread pool executor.

        Offloads JSON serialization to memory, then file I/O to thread pool,
        preventing blocking of the async event loop during checkpoints.

        Performance: Reduces checkpoint time from 50-200ms to <5ms by avoiding
        synchronous I/O in the event loop. Uses atomic writes to prevent corruption.
        """
        start = time.perf_counter()
        loop = asyncio.get_event_loop()

        # Serialize data in memory first (fast, ~1-5ms)
        timestamp = datetime.now().astimezone().isoformat()

        state_data = self.state.to_dict()
        manifest_data = {
            "version": "1.0.0",
            "last_updated": timestamp,
            "properties": self.manifest,
        }

        # Extract URL tracker data inline
        self.url_tracker.last_updated = timestamp
        tracker_data = {
            "version": self.url_tracker.version,
            "last_updated": self.url_tracker.last_updated,
            "total_urls": len(self.url_tracker.urls),
            "urls": {url: entry.to_dict() for url, entry in self.url_tracker.urls.items()},
        }

        # Offload file I/O to thread pool (non-blocking)
        await asyncio.gather(
            loop.run_in_executor(None, self._write_json_sync, self.state_path, state_data),
            loop.run_in_executor(None, self._write_json_sync, self.manifest_path, manifest_data),
            loop.run_in_executor(
                None, self._write_json_sync, self.metadata_dir / "url_tracker.json", tracker_data
            ),
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug("Async state save completed in %.1fms", elapsed_ms)

    def _write_json_sync(self, path: Path, data: dict) -> None:
        """Synchronous JSON write with atomic rename (for thread pool execution).

        Uses temp file + rename pattern to prevent corruption from crashes/interrupts.
        This method is designed to be called from a thread pool executor.

        Args:
            path: Target file path
            data: Data to serialize as JSON
        """
        import tempfile

        # Write to temp file first
        fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            # Atomic rename (POSIX and Windows)
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _get_property_hash(self, property: Property) -> str:
        """Generate consistent hash for property directory naming.

        Args:
            property: Property instance

        Returns:
            Short hash string (8 chars)
        """
        # Use full address for stable hashing
        hash_input = property.full_address.lower().strip()
        return hashlib.sha256(hash_input.encode()).hexdigest()[:8]

    def _get_existing_image_metadata(
        self,
        content_hash: str,
        property: Property,
    ) -> ImageMetadata | None:
        """Get metadata for existing content-addressed image.

        Args:
            content_hash: MD5 hash of image content
            property: Property instance

        Returns:
            ImageMetadata if found, None otherwise
        """
        # Check if image already in manifest for this property
        if property.full_address in self.manifest:
            for img in self.manifest[property.full_address]:
                if img.get("content_hash") == content_hash:
                    return ImageMetadata(
                        image_id=img["image_id"],
                        property_address=property.full_address,
                        source=img["source"],
                        source_url=img.get("source_url", ""),
                        local_path=img["local_path"],
                        original_path=img.get("original_path"),
                        phash=img.get("phash", ""),
                        dhash=img.get("dhash", ""),
                        width=img.get("width", 0),
                        height=img.get("height", 0),
                        file_size_bytes=img.get("file_size_bytes", 0),
                        status=img.get("status", "processed"),
                        downloaded_at=img.get("downloaded_at", ""),
                        processed_at=img.get("processed_at"),
                        property_hash=img.get("property_hash", self._get_property_hash(property)),
                        created_by_run_id=img.get("created_by_run_id", ""),
                        content_hash=content_hash,
                    )
        return None

    def _get_property_dir(self, property: Property) -> Path:
        """Get processed images directory for a property.

        Args:
            property: Property instance

        Returns:
            Path to property's processed image directory
        """
        prop_hash = self._get_property_hash(property)
        return self.processed_dir / prop_hash

    def _create_extractors(self) -> list[ImageExtractor]:
        """Create extractor instances for enabled sources.

        Returns:
            List of configured extractors
        """
        extractors: list[ImageExtractor] = []

        extractor_map = {
            # PhoenixMLS Search FIRST: Most reliable search-based discovery (E2.R2)
            ImageSource.PHOENIX_MLS_SEARCH: PhoenixMLSSearchExtractor,
            # PhoenixMLS Direct: For future use when MLS# known
            ImageSource.PHOENIX_MLS: PhoenixMLSExtractor,
            ImageSource.MARICOPA_ASSESSOR: MaricopaAssessorExtractor,
            ImageSource.ZILLOW: ZillowExtractor,
            ImageSource.REDFIN: RedfinExtractor,
        }

        for source in self.enabled_sources:
            # Convert string source to ImageSource enum if needed
            source_enum = source if isinstance(source, ImageSource) else ImageSource(source)

            if source_enum in extractor_map:
                extractor_class = extractor_map[source_enum]
                extractor = extractor_class(http_client=self._http_client)
                extractors.append(extractor)
                logger.info(f"Enabled extractor: {extractor.name}")

        return extractors

    async def extract_all(
        self,
        properties: list[Property],
        resume: bool = True,
        incremental: bool = True,
        force: bool = False,
    ) -> ExtractionResult:
        """Extract images for all properties across all sources.

        Args:
            properties: List of properties to process
            resume: Skip already completed properties if True
            incremental: Use URL-level tracking to only download new images
            force: If True, force re-extraction by deleting existing data

        Returns:
            ExtractionResult with statistics
        """
        # Determine run mode for logging
        run_mode = "fresh" if not resume else ("incremental" if incremental else "resume")

        logger.info(
            f"Starting extraction for {len(properties)} properties "
            f"across {len(self.enabled_sources)} sources (mode: {run_mode})"
        )

        # Start run logging
        self.run_logger.start_run(
            properties_requested=len(properties),
            mode=run_mode,
        )

        # Initialize HTTP client with connection pool limits
        # Performance Tuning: Increased pool limits for higher concurrency
        # - max_connections=50: Support up to 15 concurrent properties * ~3 sources
        # - max_keepalive_connections=20: Maintain persistent connections for reuse
        # - keepalive_expiry=30: Balance connection reuse vs resource cleanup
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

        result = ExtractionResult(
            total_properties=len(properties),
            properties_completed=0,
            properties_failed=0,
            properties_skipped=0,
            total_images=0,
            unique_images=0,
            duplicate_images=0,
            failed_downloads=0,
            start_time=datetime.now().astimezone(),
        )

        # Initialize source stats
        for source in self.enabled_sources:
            result.by_source[source.value] = SourceStats(source=source.value)

        # Filter properties if resuming
        properties_to_process = properties
        if resume:
            properties_to_process = [
                p for p in properties if p.full_address not in self.state.completed_properties
            ]
            result.properties_skipped = len(properties) - len(properties_to_process)

            if result.properties_skipped > 0:
                logger.info(f"Resuming: skipping {result.properties_skipped} completed properties")

        # Process properties with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(
            prop: Property,
        ) -> tuple[Property, list[ImageMetadata], PropertyChanges]:
            async with semaphore:
                return await self.extract_for_property_with_tracking(
                    prop, result, incremental=incremental, force=force
                )

        # Process all properties
        tasks = [process_with_semaphore(prop) for prop in properties_to_process]

        for coro in asyncio.as_completed(tasks):
            try:
                prop, images, prop_changes = await coro

                # Record property changes in run log
                if self.run_logger.current_run:
                    self.run_logger.current_run.record_property(prop_changes)

                # Security: Wrap state/manifest mutations in lock to prevent race conditions
                async with self._state_lock:
                    # Update results
                    if images or prop_changes.unchanged > 0:
                        # Property completed (has images, even if all unchanged)
                        result.properties_completed += 1
                        self.state.completed_properties.add(prop.full_address)

                        # Record when property was last checked
                        self.state.record_property_checked(prop.full_address)

                        # Add/update manifest with new images
                        if images:
                            existing = self.manifest.get(prop.full_address, [])
                            new_images = [self._image_metadata_to_dict(img) for img in images]
                            self.manifest[prop.full_address] = existing + new_images
                    elif prop_changes.errors > 0:
                        result.properties_failed += 1
                        self.state.failed_properties.add(prop.full_address)
                    else:
                        # No images found but no errors - still mark as checked
                        self.state.record_property_checked(prop.full_address)

                    # Periodic save (within lock to ensure consistency)
                    # Use async save to avoid blocking event loop (50-200ms → <5ms)
                    if (result.properties_completed + result.properties_failed) % 5 == 0:
                        await self._save_state_async()

                # Log property summary
                self._log_property_summary(prop.full_address, prop_changes)

                # Log overall progress (outside lock - read-only)
                completed = result.properties_completed + result.properties_failed
                logger.info(
                    f"Progress: {completed}/{len(properties_to_process)} properties "
                    f"({result.properties_completed} ok, {result.properties_failed} failed)"
                )

            except Exception as e:
                # Classify error as transient or permanent
                is_transient = is_transient_error(e)
                error_category = "transient" if is_transient else "permanent"

                logger.error(
                    f"Unexpected error processing property ({error_category}): {e}",
                    exc_info=True,
                )
                async with self._state_lock:
                    result.properties_failed += 1
                    # Mark property as failed (permanent) or leave for retry (transient)
                    if not is_transient:
                        self.state.mark_failed(property.full_address)

                if self.run_logger.current_run:
                    self.run_logger.current_run.record_error(f"[{error_category}] {str(e)}")

        # Final save (with lock)
        async with self._state_lock:
            self.state.last_updated = datetime.now().astimezone().isoformat()
            self._save_state()
            self._save_manifest()
            self.url_tracker.save(self.metadata_dir / "url_tracker.json")

        # Close HTTP client
        await self._http_client.aclose()
        self._http_client = None

        result.end_time = datetime.now().astimezone()

        # Log circuit breaker status if any circuits are not closed
        circuit_status = self._circuit_breaker.get_status()
        if any(s != "closed" for s in circuit_status.values()):
            logger.info("Circuit breaker status: %s", circuit_status)

        # Log error aggregation summary (Axiom 9: Fail Fast)
        error_summary = self._error_aggregator.get_summary()
        if error_summary:
            logger.info("Error aggregation summary (top 5 patterns): %s", error_summary)

        # Log CAPTCHA metrics summary
        captcha_summary = self.captcha_metrics.get_summary()
        if captcha_summary["captcha_encounters"] > 0:
            logger.info("CAPTCHA metrics summary: %s", captcha_summary)

            # Check for alerting conditions
            should_alert, alert_reason = self.captcha_metrics.should_alert()
            if should_alert:
                # Log at appropriate level based on severity
                if "CRITICAL" in alert_reason:
                    logger.error(alert_reason)
                elif "WARNING" in alert_reason:
                    logger.warning(alert_reason)
                else:
                    logger.info(alert_reason)

        # Finalize run log
        run_log_path = self.run_logger.finish_run()
        if run_log_path:
            logger.info(f"Run log saved to: {run_log_path}")

        logger.info(
            f"Extraction complete: {result.properties_completed}/{result.total_properties} succeeded, "
            f"{result.unique_images} unique images, {result.duplicate_images} duplicates"
        )

        return result

    async def extract_for_property(
        self,
        property: Property,
        result: ExtractionResult,
    ) -> list[ImageMetadata]:
        """Extract images for a single property from all sources.

        Args:
            property: Property to extract images for
            result: ExtractionResult to update with stats

        Returns:
            List of successfully processed ImageMetadata
        """
        logger.info(f"Processing property: {property.full_address}")

        images: list[ImageMetadata] = []
        property_dir = self._get_property_dir(property)
        property_dir.mkdir(parents=True, exist_ok=True)

        # Create extractors
        extractors = self._create_extractors()

        # Extract from each source
        for extractor in extractors:
            source_name = extractor.source.value
            # Initialize source stats if not already present
            if source_name not in result.by_source:
                result.by_source[source_name] = SourceStats(source=source_name)
            source_stats = result.by_source[source_name]

            # Circuit breaker: Skip if source is disabled
            if not self._circuit_breaker.is_available(source_name):
                logger.debug(f"Skipping {extractor.name} - circuit open")
                continue

            try:
                # Check if extractor can handle this property
                if not extractor.can_handle(property):
                    logger.debug(f"{extractor.name} cannot handle this property")
                    continue

                # Extract URLs
                logger.debug(f"Extracting from {extractor.name}")

                # Track extraction attempt for CAPTCHA metrics (stealth sources only)
                if source_name in ("zillow", "redfin"):
                    self.captcha_metrics.record_extraction_attempt()

                urls = await extractor.extract_image_urls(property)
                source_stats.images_found += len(urls)

                logger.info(f"{extractor.name}: found {len(urls)} images")

                # Download and process each image
                for url in urls:
                    try:
                        # Check if this is a local file path (screenshots)
                        if url.startswith(("data/", "./", "/", "C:", "D:")) or (
                            not url.startswith("http") and os.path.exists(url)
                        ):
                            # Local file - read directly instead of downloading
                            with open(url, "rb") as f:
                                image_data = f.read()
                            content_type = "image/png"
                            logger.debug(f"Read local screenshot: {url}")
                        else:
                            # Download from URL
                            image_data, content_type = await extractor.download_image(url)

                        # Compute hash
                        try:
                            phash = self.deduplicator.compute_hash(image_data)
                        except DeduplicationError as e:
                            logger.warning(f"Failed to hash image {url}: {e}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            continue

                        # Check for duplicate
                        is_duplicate, duplicate_of = self.deduplicator.is_duplicate(phash)

                        if is_duplicate:
                            logger.debug(f"Duplicate detected: {url} (matches {duplicate_of})")
                            source_stats.duplicates_detected += 1
                            result.duplicate_images += 1
                            continue

                        # Standardize image
                        try:
                            standardized_data = self.standardizer.standardize(image_data)
                        except ImageProcessingError as e:
                            logger.warning(f"Failed to standardize image {url}: {e}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            continue

                        # Compute content hash for deterministic storage
                        content_hash = hashlib.md5(standardized_data).hexdigest()
                        image_id = content_hash  # Use content hash as image ID

                        # Content-addressed directory structure
                        content_dir = self.processed_dir / content_hash[:8]
                        content_dir.mkdir(parents=True, exist_ok=True)
                        local_path = content_dir / f"{content_hash}.png"

                        # Skip if already exists (natural deduplication)
                        if local_path.exists():
                            logger.debug(f"Image already exists (dedup): {content_hash}")
                            continue

                        with open(local_path, "wb") as f:
                            f.write(standardized_data)

                        # Get dimensions
                        width, height = self.standardizer.get_dimensions(standardized_data)

                        # Create metadata
                        now = datetime.now().astimezone().isoformat()
                        property_hash = self._get_property_hash(property)
                        metadata = ImageMetadata(
                            image_id=image_id,
                            property_address=property.full_address,
                            source=extractor.source.value,
                            source_url=url,
                            local_path=str(local_path.relative_to(self.base_dir)),
                            original_path=None,  # Not preserving raw images by default
                            phash=phash.phash,
                            dhash=phash.dhash,
                            width=width,
                            height=height,
                            file_size_bytes=len(standardized_data),
                            status=ImageStatus.PROCESSED.value,
                            downloaded_at=now,
                            processed_at=now,
                            property_hash=property_hash,
                            created_by_run_id=self.run_id,
                            content_hash=content_hash,
                        )

                        # Register hash
                        self.deduplicator.register_hash(
                            image_id=image_id,
                            phash=phash,
                            property_address=property.full_address,
                            source=extractor.source.value,
                        )

                        images.append(metadata)
                        source_stats.images_downloaded += 1
                        result.total_images += 1
                        result.unique_images += 1

                        logger.debug(f"Saved image: {content_hash}.png")

                        # Rate limiting
                        await extractor._rate_limit()

                    except ImageDownloadError as e:
                        logger.warning(f"Failed to download {url}: {e}")
                        source_stats.images_failed += 1
                        result.failed_downloads += 1

                    except Exception as e:
                        # Classify error as transient or permanent
                        is_transient = is_transient_error(e)
                        error_category = "transient" if is_transient else "permanent"

                        logger.error(
                            f"Unexpected error processing {url} ({error_category}): {e}",
                            exc_info=True,
                        )
                        source_stats.images_failed += 1
                        result.failed_downloads += 1

                source_stats.properties_processed += 1

                # Circuit breaker: Record success
                self._circuit_breaker.record_success(source_name)

            except (SourceUnavailableError, RateLimitError) as e:
                logger.error(f"{extractor.name} unavailable: {e}")
                source_stats.properties_failed += 1

                # Circuit breaker: Record failure for source-level errors
                circuit_opened = self._circuit_breaker.record_failure(source_name)
                if circuit_opened:
                    logger.warning(
                        f"Circuit opened for {extractor.name} - will skip remaining properties"
                    )

            except ExtractionError as e:
                logger.error(f"Extraction failed for {extractor.name}: {e}")
                source_stats.properties_failed += 1

                # Circuit breaker: Record failure
                self._circuit_breaker.record_failure(source_name)

            except Exception as e:
                # Classify error as transient or permanent
                is_transient = is_transient_error(e)
                error_category = "transient" if is_transient else "permanent"

                logger.error(
                    f"Unexpected error with {extractor.name} ({error_category}): {e}",
                    exc_info=True,
                )
                source_stats.properties_failed += 1

                # Circuit breaker: Record failure for unexpected errors
                # Only record permanent failures in circuit breaker to avoid over-tripping
                if not is_transient:
                    self._circuit_breaker.record_failure(source_name)

            finally:
                # Close extractor
                await extractor.close()

        logger.info(f"Property complete: {len(images)} unique images extracted")
        return images

    async def _force_cleanup_property(
        self,
        property: Property,
        property_hash: str,
    ) -> None:
        """
        Delete all existing data for a property before re-extraction.

        Called when --force flag is passed. Cleans:
        1. Property folder (images)
        2. Manifest entries
        3. URL tracker entries
        4. Completed state
        """

        logger.warning(f"--force: Cleaning up existing data for {property.full_address}")

        # 1. Find and delete images for this property from manifest
        if property.full_address in self.manifest:
            images = self.manifest[property.full_address]
            for img in images:
                # Delete the actual image file
                img_path = self.base_dir / img.get("local_path", "")
                if img_path.exists():
                    img_path.unlink()
                    logger.debug(f"--force: Deleted {img_path}")

                # Delete parent dir if empty
                if img_path.parent.exists() and not any(img_path.parent.iterdir()):
                    img_path.parent.rmdir()

            # Remove from manifest
            del self.manifest[property.full_address]
            self._save_manifest()
            logger.info(f"--force: Removed {len(images)} images from manifest")

        # 2. Clear URL tracker entries
        if self.url_tracker:
            deleted = self.url_tracker.clear_property(property_hash)
            if deleted:
                self.url_tracker.save(self.metadata_dir / "url_tracker.json")
                logger.info(f"--force: Cleared {deleted} URL tracker entries")

        # 3. Remove from completed properties
        if property.full_address in self.state.completed_properties:
            self.state.completed_properties.discard(property.full_address)
            self._save_state()
            logger.info("--force: Removed from completed properties")

        # 4. Remove from failed properties (allow retry)
        if property.full_address in self.state.failed_properties:
            self.state.failed_properties.discard(property.full_address)
            self._save_state()
            logger.info("--force: Removed from failed properties")

    async def extract_for_property_with_tracking(
        self,
        property: Property,
        result: ExtractionResult,
        incremental: bool = True,
        force: bool = False,
    ) -> tuple[Property, list[ImageMetadata], PropertyChanges]:
        """Extract images for a property with URL-level tracking.

        Enhanced version of extract_for_property that tracks individual URLs
        to enable incremental extraction on re-runs.

        Args:
            property: Property to extract images for
            result: ExtractionResult to update with stats
            incremental: If True, skip already-known URLs
            force: If True, delete existing property data before extraction

        Returns:
            Tuple of (property, new_images, property_changes)
        """
        logger.info(f"Processing property: {property.full_address}")

        property_hash = self._get_property_hash(property)
        locks_dir = self.metadata_dir / "locks"
        locks_dir.mkdir(parents=True, exist_ok=True)

        # Acquire property lock for exclusive access
        from phx_home_analysis.services.image_extraction.file_lock import PropertyLock

        with PropertyLock(locks_dir, property_hash, timeout=120.0):
            # --force cleanup if requested
            if force:
                await self._force_cleanup_property(property, property_hash)

            return await self._extract_for_property_locked(
                property, property_hash, result, incremental
            )

    async def _extract_for_property_locked(
        self,
        property: Property,
        property_hash: str,
        result: ExtractionResult,
        incremental: bool,
    ) -> tuple[Property, list[ImageMetadata], PropertyChanges]:
        """Inner extraction logic called within property lock."""
        property_dir = self._get_property_dir(property)
        property_dir.mkdir(parents=True, exist_ok=True)

        # Initialize change tracking
        prop_changes = PropertyChanges(
            address=property.full_address,
            property_hash=property_hash,
        )

        new_images: list[ImageMetadata] = []
        all_discovered_urls: set[str] = set()

        # Create extractors
        extractors = self._create_extractors()

        # Extract from each source
        for extractor in extractors:
            source_name = extractor.source.value
            # Initialize source stats if not already present
            if source_name not in result.by_source:
                result.by_source[source_name] = SourceStats(source=source_name)
            source_stats = result.by_source[source_name]

            # Circuit breaker: Skip if source is disabled
            if not self._circuit_breaker.is_available(source_name):
                logger.debug(f"Skipping {extractor.name} - circuit open")
                continue

            try:
                # Check if extractor can handle this property
                if not extractor.can_handle(property):
                    logger.debug(f"{extractor.name} cannot handle this property")
                    continue

                # Extract URLs
                logger.debug(f"Extracting from {extractor.name}")
                result_data = await extractor.extract_image_urls(property)

                # Handle both tuple (PhoenixMLS: urls, metadata) and list (other extractors) returns
                if isinstance(result_data, tuple):
                    urls, metadata = result_data
                    # Merge metadata from PhoenixMLS into listing_metadata
                    if metadata:
                        prop_changes.listing_metadata.update(metadata)
                        logger.info(
                            f"{extractor.name}: collected metadata: {list(metadata.keys())}"
                        )

                        # Persist metadata to enrichment_data.json with provenance
                        try:
                            self.metadata_persister.persist_metadata(
                                full_address=property.full_address,
                                property_hash=property_hash,
                                metadata=metadata,
                                agent_id="listing-browser",
                                phase="phase1",
                            )
                        except Exception as persist_err:
                            logger.warning(
                                f"Failed to persist metadata for {property.full_address}: {persist_err}"
                            )
                else:
                    urls = result_data

                source_stats.images_found += len(urls)
                prop_changes.urls_discovered += len(urls)
                all_discovered_urls.update(urls)

                logger.info(f"{extractor.name}: found {len(urls)} images")

                # Collect listing metadata if extractor provides it (legacy)
                # Zillow uses last_metadata attribute pattern
                if hasattr(extractor, "last_metadata") and extractor.last_metadata:
                    prop_changes.listing_metadata.update(extractor.last_metadata)
                    logger.info(
                        f"{extractor.name}: collected metadata (legacy): "
                        f"{list(extractor.last_metadata.keys())}"
                    )

                    # Persist legacy metadata to enrichment_data.json with provenance
                    try:
                        self.metadata_persister.persist_metadata(
                            full_address=property.full_address,
                            property_hash=property_hash,
                            metadata=extractor.last_metadata,
                            agent_id="listing-browser",
                            phase="phase1",
                        )
                    except Exception as persist_err:
                        logger.warning(
                            f"Failed to persist legacy metadata for {property.full_address}: {persist_err}"
                        )

                # Download and process each image
                for url in urls:
                    try:
                        # Skip URLs matching known systemic failures (Axiom 9: Fail Fast)
                        if self._error_aggregator.should_skip(url):
                            logger.debug(f"Skipping URL with known failure pattern: {url[:60]}...")
                            continue

                        # Check URL against tracker if incremental
                        if incremental:
                            url_status, existing_id = self.url_tracker.check_url(url)

                            if url_status == "known":
                                # URL already processed, skip download
                                self.url_tracker.mark_active(url)
                                prop_changes.unchanged += 1
                                logger.debug(f"Skipping known URL: {url[:60]}...")
                                continue
                            elif url_status == "stale":
                                # URL is stale, may want to refresh
                                logger.debug(f"Re-checking stale URL: {url[:60]}...")
                            # For "new" or "content_changed", proceed with download

                        # Check if this is a local file path (screenshots)
                        if url.startswith(("data/", "./", "/", "C:", "D:")) or (
                            not url.startswith("http") and os.path.exists(url)
                        ):
                            # Local file - read directly instead of downloading
                            with open(url, "rb") as f:
                                image_data = f.read()
                            logger.debug(f"Read local screenshot: {url}")
                        else:
                            # Download from URL
                            image_data, _ = await extractor.download_image(url)

                        # Compute content hash for URL tracking
                        content_hash = hashlib.md5(image_data).hexdigest()

                        # Check for content change if URL was known
                        if incremental:
                            url_status, _ = self.url_tracker.check_url(url, content_hash)
                            if url_status == "content_changed":
                                prop_changes.content_changed += 1
                                logger.info(f"Content changed at URL: {url[:60]}...")

                        # Process image using ImageProcessor
                        processed_image, error = await self.image_processor.process_image(
                            image_data=image_data,
                            source_url=url,
                            property_hash=property_hash,
                            run_id=self.run_id,
                        )

                        if error:
                            # Processing failed
                            logger.warning(f"Failed to process {url}: {error}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            prop_changes.errors += 1
                            prop_changes.error_messages.append(f"Processing failed: {url}")
                            self._stats_accumulator["extraction_errors"] += 1
                            continue

                        if not processed_image:
                            # Shouldn't happen, but handle gracefully
                            logger.error(f"ImageProcessor returned None for {url}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            prop_changes.errors += 1
                            self._stats_accumulator["extraction_errors"] += 1
                            continue

                        # Handle duplicates (processed_image is from ImageProcessor)
                        if processed_image.is_duplicate:
                            logger.debug(
                                f"Duplicate detected: {url} (matches {processed_image.duplicate_of})"
                            )
                            source_stats.duplicates_detected += 1
                            result.duplicate_images += 1
                            prop_changes.duplicates += 1

                            # Still register URL to track it
                            if incremental and processed_image.duplicate_of:
                                self.url_tracker.register_url(
                                    url=url,
                                    image_id=processed_image.duplicate_of,
                                    property_hash=property_hash,
                                    content_hash=content_hash,
                                    source=extractor.source.value,
                                )
                            continue

                        # New unique image - create metadata
                        now = datetime.now().astimezone().isoformat()
                        metadata = ImageMetadata(
                            image_id=processed_image.image_id,
                            property_address=property.full_address,
                            source=extractor.source.value,
                            source_url=url,
                            local_path=str(processed_image.local_path.relative_to(self.base_dir)),
                            original_path=None,
                            phash=processed_image.phash,
                            dhash=processed_image.dhash,
                            width=processed_image.width,
                            height=processed_image.height,
                            file_size_bytes=processed_image.file_size_bytes,
                            status=ImageStatus.PROCESSED.value,
                            downloaded_at=now,
                            processed_at=now,
                            property_hash=property_hash,
                            created_by_run_id=self.run_id,
                            content_hash=processed_image.content_hash,
                        )

                        # Register URL in tracker
                        if incremental:
                            self.url_tracker.register_url(
                                url=url,
                                image_id=processed_image.image_id,
                                property_hash=property_hash,
                                content_hash=content_hash,
                                source=extractor.source.value,
                            )

                        new_images.append(metadata)
                        prop_changes.new_images += 1
                        prop_changes.new_image_ids.append(processed_image.image_id)
                        source_stats.images_downloaded += 1
                        result.total_images += 1
                        result.unique_images += 1

                        # Update statistics accumulator (O(1))
                        self._stats_accumulator["total_images"] += 1
                        self._stats_accumulator["by_source"][extractor.source.value] += 1
                        self._stats_accumulator["by_property"][property.full_address] += 1

                        logger.debug(f"Saved new image: {processed_image.image_id[:8]}.png")

                        # Rate limiting
                        await extractor._rate_limit()

                    except ImageDownloadError as e:
                        error_msg = f"Failed to download {url}: {e}"
                        # Record error for systemic failure detection
                        should_skip = self._error_aggregator.record_error(error_msg)
                        if not should_skip:
                            # Only log details if not a known pattern
                            logger.warning(error_msg)
                        source_stats.images_failed += 1
                        result.failed_downloads += 1
                        prop_changes.errors += 1
                        prop_changes.error_messages.append(f"Download failed: {url}")
                        # Update statistics accumulator
                        self._stats_accumulator["extraction_errors"] += 1

                    except Exception as e:
                        # Classify error as transient or permanent
                        is_transient = is_transient_error(e)
                        error_category = "transient" if is_transient else "permanent"

                        error_msg = f"Unexpected error processing {url} ({error_category}): {e}"
                        # Record error for systemic failure detection
                        should_skip = self._error_aggregator.record_error(error_msg)
                        if not should_skip:
                            # Only log details if not a known pattern
                            logger.error(error_msg, exc_info=True)
                        source_stats.images_failed += 1
                        result.failed_downloads += 1
                        prop_changes.errors += 1
                        prop_changes.error_messages.append(f"Error ({error_category}): {url}: {e}")
                        # Update statistics accumulator
                        self._stats_accumulator["extraction_errors"] += 1

                source_stats.properties_processed += 1

                # Circuit breaker: Record success
                self._circuit_breaker.record_success(source_name)

            except (SourceUnavailableError, RateLimitError) as e:
                logger.error(f"{extractor.name} unavailable: {e}")
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(f"{extractor.name} unavailable")

                # Circuit breaker: Record failure for source-level errors
                circuit_opened = self._circuit_breaker.record_failure(source_name)
                if circuit_opened:
                    logger.warning(
                        f"Circuit opened for {extractor.name} - will skip remaining properties"
                    )

            except ExtractionError as e:
                logger.error(f"Extraction failed for {extractor.name}: {e}")
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(f"{extractor.name} extraction failed")

                # Circuit breaker: Record failure
                self._circuit_breaker.record_failure(source_name)

            except Exception as e:
                # Classify error as transient or permanent
                is_transient = is_transient_error(e)
                error_category = "transient" if is_transient else "permanent"

                logger.error(
                    f"Unexpected error with {extractor.name} ({error_category}): {e}",
                    exc_info=True,
                )
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(
                    f"{extractor.name} error ({error_category}): {e}"
                )

                # Circuit breaker: Record failure for unexpected errors
                # Only record permanent failures in circuit breaker to avoid over-tripping
                if not is_transient:
                    self._circuit_breaker.record_failure(source_name)

            finally:
                # Close extractor
                await extractor.close()

        # Detect removed URLs (were tracked before but not in current listing)
        if incremental:
            removed_urls = self.url_tracker.detect_removed_urls(property_hash, all_discovered_urls)
            prop_changes.removed = len(removed_urls)
            prop_changes.removed_urls = removed_urls

        logger.info(
            f"Property complete: {prop_changes.new_images} new, "
            f"{prop_changes.unchanged} unchanged, "
            f"{prop_changes.duplicates} duplicates"
        )

        return property, new_images, prop_changes

    def _log_property_summary(self, address: str, changes: PropertyChanges) -> None:
        """Log property extraction summary with verbose details.

        Args:
            address: Property address
            changes: PropertyChanges tracking extraction results
        """
        logger.info(
            "Property: %s | URLs: %d discovered, %d new, %d unchanged, %d duplicates, %d errors",
            address,
            changes.urls_discovered,
            changes.new_images,
            changes.unchanged,
            changes.duplicates,
            changes.errors,
        )

        # Warn if large batch of new images (potential listing overhaul)
        if changes.new_images > 10:
            logger.warning(
                "REVIEW NEEDED: %d new images for %s - verify listing changes",
                changes.new_images,
                address,
            )

        # Warn if content changes detected
        if changes.content_changed > 0:
            logger.warning(
                "CONTENT CHANGED: %d images have new content at same URL for %s",
                changes.content_changed,
                address,
            )

        # Warn if URLs were removed
        if changes.removed > 0:
            logger.info(
                "REMOVED: %d URLs no longer in listing for %s",
                changes.removed,
                address,
            )

    def _image_metadata_to_dict(self, metadata: ImageMetadata) -> dict:
        """Convert ImageMetadata to dict for JSON serialization.

        Args:
            metadata: ImageMetadata instance

        Returns:
            Dict representation
        """
        return {
            "image_id": metadata.image_id,
            "property_address": metadata.property_address,  # BUGFIX: was omitted
            "source": metadata.source,
            "source_url": metadata.source_url,
            "local_path": metadata.local_path,
            "phash": metadata.phash,
            "dhash": metadata.dhash,
            "width": metadata.width,
            "height": metadata.height,
            "file_size_bytes": metadata.file_size_bytes,
            "status": metadata.status,
            "downloaded_at": metadata.downloaded_at,
            "processed_at": metadata.processed_at,
            # NEW lineage fields for E2.S4 data integrity
            "property_hash": metadata.property_hash,
            "created_by_run_id": metadata.created_by_run_id,
            "content_hash": metadata.content_hash,
        }

    def get_property_images(self, property: Property) -> list[ImageMetadata]:
        """Get all images for a property from manifest.

        Args:
            property: Property to get images for

        Returns:
            List of ImageMetadata for this property
        """
        images_data = self.manifest.get(property.full_address, [])

        return [
            ImageMetadata(
                image_id=img["image_id"],
                property_address=property.full_address,
                source=img["source"],
                source_url=img["source_url"],
                local_path=img["local_path"],
                original_path=img.get("original_path"),
                phash=img["phash"],
                dhash=img["dhash"],
                width=img["width"],
                height=img["height"],
                file_size_bytes=img["file_size_bytes"],
                status=img["status"],
                downloaded_at=img["downloaded_at"],
                processed_at=img.get("processed_at"),
                property_hash=img.get("property_hash", self._get_property_hash(property)),
                created_by_run_id=img.get("created_by_run_id", ""),
                content_hash=img.get("content_hash", ""),
            )
            for img in images_data
        ]

    def get_statistics(self) -> dict:
        """Get comprehensive statistics about extracted images.

        Performance: O(1) when stats are pre-computed during extraction.
        Falls back to O(n*m) computation from manifest for backward compatibility.

        Returns:
            Dict with extraction statistics
        """
        # If stats accumulated during extraction, use pre-computed values (O(1))
        if self._stats_accumulator["total_images"] > 0:
            return {
                "total_properties": len(self._stats_accumulator["by_property"]),
                "total_images": self._stats_accumulator["total_images"],
                "images_by_source": dict(self._stats_accumulator["by_source"]),
                "extraction_errors": self._stats_accumulator["extraction_errors"],
                "completed_properties": len(self.state.completed_properties),
                "failed_properties": len(self.state.failed_properties),
                "stale_properties": len(self.state.get_stale_properties()),
                "url_tracker_stats": self.url_tracker.get_stats(),
                "deduplication_stats": self.deduplicator.get_stats(),
                "last_updated": self.state.last_updated,
                "stats_source": "pre-computed",  # Indicator for debugging
            }

        # Fallback: compute from manifest (for backward compatibility)
        return self._compute_statistics_from_manifest()

    def _compute_statistics_from_manifest(self) -> dict:
        """Compute statistics from manifest (O(n*m) - fallback method).

        Used when stats accumulator is empty (e.g., after restart without extraction).

        Returns:
            Dict with extraction statistics computed from manifest
        """
        total_images = sum(len(images) for images in self.manifest.values())

        by_source: dict[str, int] = {}
        for images in self.manifest.values():
            for img in images:
                source = img["source"]
                by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_properties": len(self.manifest),
            "total_images": total_images,
            "images_by_source": by_source,
            "extraction_errors": 0,  # Not tracked in manifest
            "completed_properties": len(self.state.completed_properties),
            "failed_properties": len(self.state.failed_properties),
            "stale_properties": len(self.state.get_stale_properties()),
            "url_tracker_stats": self.url_tracker.get_stats(),
            "deduplication_stats": self.deduplicator.get_stats(),
            "last_updated": self.state.last_updated,
            "stats_source": "manifest",  # Indicator for debugging
        }

    def clear_state(self) -> None:
        """Clear extraction state to start fresh.

        Warning: Does not delete downloaded images, only state tracking.
        """
        self.state = ExtractionState()
        self._save_state()

        # Reset statistics accumulator
        self._stats_accumulator = {
            "total_images": 0,
            "by_source": defaultdict(int),
            "by_property": defaultdict(int),
            "extraction_errors": 0,
        }

        logger.info("Cleared extraction state")

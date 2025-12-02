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
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import httpx

from ...domain.entities import Property
from ...domain.enums import ImageSource, ImageStatus
from ...domain.value_objects import ImageMetadata
from .deduplicator import DeduplicationError, ImageDeduplicator
from .extraction_stats import ExtractionResult, SourceStats
from .extractors import (
    MaricopaAssessorExtractor,
    PhoenixMLSExtractor,
    RedfinExtractor,
    ZillowExtractor,
)
from .extractors.base import (
    ExtractionError,
    ImageDownloadError,
    ImageExtractor,
    SourceUnavailableError,
)
from .run_logger import PropertyChanges, RunLogger
from .standardizer import ImageProcessingError, ImageStandardizer
from .state_manager import ExtractionState
from .url_tracker import URLTracker

logger = logging.getLogger(__name__)


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

        Performance Tuning Notes:
            - Default concurrency is CPU-based since image extraction is I/O-bound
            - Cap at 15 to avoid triggering rate limits on source APIs
            - Minimum of 2 ensures reasonable performance on low-core systems
            - For systems with 4+ cores, this typically yields 8-15 concurrent properties
        """
        self.base_dir = Path(base_dir)
        self.enabled_sources = enabled_sources or list(ImageSource)

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

        # State tracking
        self.manifest_path = self.metadata_dir / "image_manifest.json"
        self.state_path = self.metadata_dir / "extraction_state.json"
        self.manifest: dict[str, list[dict]] = self._load_manifest()
        self.state: ExtractionState = self._load_state()

        # URL tracking for incremental extraction
        self.url_tracker = URLTracker.load(self.metadata_dir / "url_tracker.json")

        # Run logging for audit trail
        self.run_logger = RunLogger(self.metadata_dir)

        # Security: Lock for thread-safe state/manifest mutations
        self._state_lock = asyncio.Lock()

        # HTTP client (shared across extractors)
        self._http_client: httpx.AsyncClient | None = None

    def _load_manifest(self) -> dict[str, list[dict]]:
        """Load image manifest from disk.

        Returns:
            Dict mapping property_address to list of image metadata
        """
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    data = json.load(f)
                    logger.info(
                        f"Loaded manifest with {len(data.get('properties', {}))} properties"
                    )
                    return data.get("properties", {})
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
        """Save image manifest to disk atomically."""
        data = {
            "version": "1.0.0",
            "last_updated": datetime.now().astimezone().isoformat(),
            "properties": self.manifest,
        }

        self._atomic_json_write(self.manifest_path, data)
        logger.debug("Saved manifest to disk")

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
        """Save extraction state to disk atomically."""
        self._atomic_json_write(self.state_path, self.state.to_dict())
        logger.debug("Saved state to disk")

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
            ImageSource.MARICOPA_ASSESSOR: MaricopaAssessorExtractor,
            ImageSource.PHOENIX_MLS: PhoenixMLSExtractor,
            ImageSource.ZILLOW: ZillowExtractor,
            ImageSource.REDFIN: RedfinExtractor,
        }

        for source in self.enabled_sources:
            if source in extractor_map:
                extractor_class = extractor_map[source]
                extractor = extractor_class(http_client=self._http_client)
                extractors.append(extractor)
                logger.info(f"Enabled extractor: {extractor.name}")

        return extractors

    async def extract_all(
        self,
        properties: list[Property],
        resume: bool = True,
        incremental: bool = True,
    ) -> ExtractionResult:
        """Extract images for all properties across all sources.

        Args:
            properties: List of properties to process
            resume: Skip already completed properties if True
            incremental: Use URL-level tracking to only download new images

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
                p
                for p in properties
                if p.full_address not in self.state.completed_properties
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
                    prop, result, incremental=incremental
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
                    if (result.properties_completed + result.properties_failed) % 5 == 0:
                        self._save_state()
                        self._save_manifest()
                        self.url_tracker.save(self.metadata_dir / "url_tracker.json")

                # Log property summary
                self._log_property_summary(prop.full_address, prop_changes)

                # Log overall progress (outside lock - read-only)
                completed = result.properties_completed + result.properties_failed
                logger.info(
                    f"Progress: {completed}/{len(properties_to_process)} properties "
                    f"({result.properties_completed} ok, {result.properties_failed} failed)"
                )

            except Exception as e:
                logger.error(f"Unexpected error processing property: {e}", exc_info=True)
                async with self._state_lock:
                    result.properties_failed += 1
                if self.run_logger.current_run:
                    self.run_logger.current_run.record_error(str(e))

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
            source_stats = result.by_source[extractor.source.value]

            try:
                # Check if extractor can handle this property
                if not extractor.can_handle(property):
                    logger.debug(f"{extractor.name} cannot handle this property")
                    continue

                # Extract URLs
                logger.debug(f"Extracting from {extractor.name}")
                urls = await extractor.extract_image_urls(property)
                source_stats.images_found += len(urls)

                logger.info(f"{extractor.name}: found {len(urls)} images")

                # Download and process each image
                for url in urls:
                    try:
                        # Download
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

                        # Generate image ID and save
                        image_id = str(uuid4())
                        filename = f"{image_id}.png"
                        local_path = property_dir / filename

                        with open(local_path, "wb") as f:
                            f.write(standardized_data)

                        # Get dimensions
                        width, height = self.standardizer.get_dimensions(standardized_data)

                        # Create metadata
                        now = datetime.now().astimezone().isoformat()
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

                        logger.debug(f"Saved image: {filename}")

                        # Rate limiting
                        await extractor._rate_limit()

                    except ImageDownloadError as e:
                        logger.warning(f"Failed to download {url}: {e}")
                        source_stats.images_failed += 1
                        result.failed_downloads += 1

                    except Exception as e:
                        logger.error(f"Unexpected error processing {url}: {e}", exc_info=True)
                        source_stats.images_failed += 1
                        result.failed_downloads += 1

                source_stats.properties_processed += 1

            except SourceUnavailableError as e:
                logger.error(f"{extractor.name} unavailable: {e}")
                source_stats.properties_failed += 1

            except ExtractionError as e:
                logger.error(f"Extraction failed for {extractor.name}: {e}")
                source_stats.properties_failed += 1

            except Exception as e:
                logger.error(
                    f"Unexpected error with {extractor.name}: {e}",
                    exc_info=True,
                )
                source_stats.properties_failed += 1

            finally:
                # Close extractor
                await extractor.close()

        logger.info(f"Property complete: {len(images)} unique images extracted")
        return images

    async def extract_for_property_with_tracking(
        self,
        property: Property,
        result: ExtractionResult,
        incremental: bool = True,
    ) -> tuple[Property, list[ImageMetadata], PropertyChanges]:
        """Extract images for a property with URL-level tracking.

        Enhanced version of extract_for_property that tracks individual URLs
        to enable incremental extraction on re-runs.

        Args:
            property: Property to extract images for
            result: ExtractionResult to update with stats
            incremental: If True, skip already-known URLs

        Returns:
            Tuple of (property, new_images, property_changes)
        """
        logger.info(f"Processing property: {property.full_address}")

        property_hash = self._get_property_hash(property)
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
            source_stats = result.by_source[extractor.source.value]

            try:
                # Check if extractor can handle this property
                if not extractor.can_handle(property):
                    logger.debug(f"{extractor.name} cannot handle this property")
                    continue

                # Extract URLs
                logger.debug(f"Extracting from {extractor.name}")
                urls = await extractor.extract_image_urls(property)
                source_stats.images_found += len(urls)
                prop_changes.urls_discovered += len(urls)
                all_discovered_urls.update(urls)

                logger.info(f"{extractor.name}: found {len(urls)} images")

                # Download and process each image
                for url in urls:
                    try:
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

                        # Download
                        image_data, content_type = await extractor.download_image(url)

                        # Compute content hash for URL tracking
                        content_hash = hashlib.md5(image_data).hexdigest()

                        # Check for content change if URL was known
                        if incremental:
                            url_status, _ = self.url_tracker.check_url(url, content_hash)
                            if url_status == "content_changed":
                                prop_changes.content_changed += 1
                                logger.info(f"Content changed at URL: {url[:60]}...")

                        # Compute perceptual hash
                        try:
                            phash = self.deduplicator.compute_hash(image_data)
                        except DeduplicationError as e:
                            logger.warning(f"Failed to hash image {url}: {e}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            prop_changes.errors += 1
                            prop_changes.error_messages.append(f"Hash failed: {url}")
                            continue

                        # Check for duplicate
                        is_duplicate, duplicate_of = self.deduplicator.is_duplicate(phash)

                        if is_duplicate:
                            logger.debug(f"Duplicate detected: {url} (matches {duplicate_of})")
                            source_stats.duplicates_detected += 1
                            result.duplicate_images += 1
                            prop_changes.duplicates += 1

                            # Still register URL to track it
                            if incremental and duplicate_of:
                                self.url_tracker.register_url(
                                    url=url,
                                    image_id=duplicate_of,
                                    property_hash=property_hash,
                                    content_hash=content_hash,
                                    source=extractor.source.value,
                                )
                            continue

                        # Standardize image
                        try:
                            standardized_data = self.standardizer.standardize(image_data)
                        except ImageProcessingError as e:
                            logger.warning(f"Failed to standardize image {url}: {e}")
                            source_stats.images_failed += 1
                            result.failed_downloads += 1
                            prop_changes.errors += 1
                            prop_changes.error_messages.append(f"Standardize failed: {url}")
                            continue

                        # Generate image ID and save
                        image_id = str(uuid4())
                        filename = f"{image_id}.png"
                        local_path = property_dir / filename

                        with open(local_path, "wb") as f:
                            f.write(standardized_data)

                        # Get dimensions
                        width, height = self.standardizer.get_dimensions(standardized_data)

                        # Create metadata
                        now = datetime.now().astimezone().isoformat()
                        metadata = ImageMetadata(
                            image_id=image_id,
                            property_address=property.full_address,
                            source=extractor.source.value,
                            source_url=url,
                            local_path=str(local_path.relative_to(self.base_dir)),
                            original_path=None,
                            phash=phash.phash,
                            dhash=phash.dhash,
                            width=width,
                            height=height,
                            file_size_bytes=len(standardized_data),
                            status=ImageStatus.PROCESSED.value,
                            downloaded_at=now,
                            processed_at=now,
                        )

                        # Register hash
                        self.deduplicator.register_hash(
                            image_id=image_id,
                            phash=phash,
                            property_address=property.full_address,
                            source=extractor.source.value,
                        )

                        # Register URL in tracker
                        if incremental:
                            self.url_tracker.register_url(
                                url=url,
                                image_id=image_id,
                                property_hash=property_hash,
                                content_hash=content_hash,
                                source=extractor.source.value,
                            )

                        new_images.append(metadata)
                        prop_changes.new_images += 1
                        prop_changes.new_image_ids.append(image_id)
                        source_stats.images_downloaded += 1
                        result.total_images += 1
                        result.unique_images += 1

                        logger.debug(f"Saved new image: {filename}")

                        # Rate limiting
                        await extractor._rate_limit()

                    except ImageDownloadError as e:
                        logger.warning(f"Failed to download {url}: {e}")
                        source_stats.images_failed += 1
                        result.failed_downloads += 1
                        prop_changes.errors += 1
                        prop_changes.error_messages.append(f"Download failed: {url}")

                    except Exception as e:
                        logger.error(f"Unexpected error processing {url}: {e}", exc_info=True)
                        source_stats.images_failed += 1
                        result.failed_downloads += 1
                        prop_changes.errors += 1
                        prop_changes.error_messages.append(f"Error: {url}: {e}")

                source_stats.properties_processed += 1

            except SourceUnavailableError as e:
                logger.error(f"{extractor.name} unavailable: {e}")
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(f"{extractor.name} unavailable")

            except ExtractionError as e:
                logger.error(f"Extraction failed for {extractor.name}: {e}")
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(f"{extractor.name} extraction failed")

            except Exception as e:
                logger.error(
                    f"Unexpected error with {extractor.name}: {e}",
                    exc_info=True,
                )
                source_stats.properties_failed += 1
                prop_changes.errors += 1
                prop_changes.error_messages.append(f"{extractor.name} error: {e}")

            finally:
                # Close extractor
                await extractor.close()

        # Detect removed URLs (were tracked before but not in current listing)
        if incremental:
            removed_urls = self.url_tracker.detect_removed_urls(
                property_hash, all_discovered_urls
            )
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
            "Property: %s | URLs: %d discovered, %d new, %d unchanged, "
            "%d duplicates, %d errors",
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
            )
            for img in images_data
        ]

    def get_statistics(self) -> dict:
        """Get comprehensive statistics about extracted images.

        Returns:
            Dict with extraction statistics
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
            "completed_properties": len(self.state.completed_properties),
            "failed_properties": len(self.state.failed_properties),
            "stale_properties": len(self.state.get_stale_properties()),
            "url_tracker_stats": self.url_tracker.get_stats(),
            "deduplication_stats": self.deduplicator.get_stats(),
            "last_updated": self.state.last_updated,
        }

    def clear_state(self) -> None:
        """Clear extraction state to start fresh.

        Warning: Does not delete downloaded images, only state tracking.
        """
        self.state = ExtractionState()
        self._save_state()
        logger.info("Cleared extraction state")

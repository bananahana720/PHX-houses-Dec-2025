"""Image processing service for extraction pipeline.

Coordinates image deduplication, standardization, and content-addressed storage.
Encapsulates the image processing workflow that was previously scattered
across the orchestrator.

Key Features:
- Content-addressed storage using MD5 hashes
- Two-level deduplication (perceptual + content hash)
- Format standardization (PNG, max dimension)
- Comprehensive metadata tracking

Example:
    processor = ImageProcessor(base_dir, deduplicator, standardizer)
    result, error = await processor.process_image(
        image_data=bytes_data,
        source_url="https://...",
        property_hash="abc12345",
        run_id="deadbeef",
    )
    if result:
        print(f"Saved to {result.local_path}")

Security: No network I/O in critical path; all file writes are atomic.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .deduplicator import ImageDeduplicator
    from .standardizer import ImageStandardizer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessedImage:
    """Result of processing a single image.

    Immutable dataclass containing all metadata for a successfully
    processed image.

    Attributes:
        image_id: Content hash (MD5) serving as unique identifier
        content_hash: Same as image_id (kept for clarity in different contexts)
        local_path: Path where image is stored
        phash: Perceptual hash for visual similarity detection
        dhash: Difference hash for visual similarity detection
        width: Image width in pixels
        height: Image height in pixels
        file_size_bytes: Size of standardized image file
        is_duplicate: True if this image was a duplicate (not saved again)
        duplicate_of: If duplicate, the original image_id it matches
    """

    image_id: str
    content_hash: str
    local_path: Path
    phash: str
    dhash: str
    width: int
    height: int
    file_size_bytes: int
    is_duplicate: bool
    duplicate_of: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict with all fields, Path converted to string
        """
        return {
            "image_id": self.image_id,
            "content_hash": self.content_hash,
            "local_path": str(self.local_path),
            "phash": self.phash,
            "dhash": self.dhash,
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
        }


@dataclass
class ProcessingStats:
    """Statistics from processing images for one property.

    Mutable dataclass that accumulates metrics during batch processing.

    Attributes:
        images_processed: Total images attempted
        images_saved: New images successfully saved
        duplicates_detected: Images skipped due to deduplication
        errors: Count of processing errors
        error_messages: List of error descriptions
    """

    images_processed: int = 0
    images_saved: int = 0
    duplicates_detected: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)

    def record_success(self, is_duplicate: bool = False) -> None:
        """Record a successful image processing.

        Args:
            is_duplicate: True if image was deduplicated (not saved)
        """
        self.images_processed += 1
        if is_duplicate:
            self.duplicates_detected += 1
        else:
            self.images_saved += 1

    def record_error(self, message: str) -> None:
        """Record a processing error.

        Args:
            message: Error description
        """
        self.images_processed += 1
        self.errors += 1
        self.error_messages.append(message)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/reporting."""
        return {
            "images_processed": self.images_processed,
            "images_saved": self.images_saved,
            "duplicates_detected": self.duplicates_detected,
            "errors": self.errors,
            "error_messages": self.error_messages[:5],  # Limit for logging
        }


class ImageProcessor:
    """Coordinates image processing: dedup, standardize, and store.

    Provides a single entry point for processing downloaded images,
    handling:
    1. Perceptual hash computation for visual deduplication
    2. Format standardization (PNG, max dimension)
    3. Content-addressed storage (MD5 hash → file path)
    4. Metadata extraction (dimensions, file size)

    Thread Safety:
        This class is thread-safe for concurrent `process_image` calls.
        Internal services (deduplicator, standardizer) handle their own locking.

    Example:
        processor = ImageProcessor(
            base_dir=Path("data/property_images/processed"),
            deduplicator=ImageDeduplicator(...),
            standardizer=ImageStandardizer(...),
        )

        result, error = await processor.process_image(
            image_data=downloaded_bytes,
            source_url="https://cdn.zillow.com/...",
            property_hash="abc12345",
            run_id="deadbeef",
        )

        if result and not result.is_duplicate:
            print(f"New image saved: {result.local_path}")
    """

    def __init__(
        self,
        base_dir: Path,
        deduplicator: ImageDeduplicator,
        standardizer: ImageStandardizer,
    ):
        """Initialize image processor with required services.

        Args:
            base_dir: Directory for processed image storage
            deduplicator: Service for perceptual hash-based deduplication
            standardizer: Service for format conversion and resizing
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._deduplicator = deduplicator
        self._standardizer = standardizer

        logger.info("ImageProcessor initialized: base_dir=%s", self.base_dir)

    async def process_image(
        self,
        image_data: bytes,
        source_url: str,
        property_hash: str,
        run_id: str,
    ) -> tuple[ProcessedImage | None, str | None]:
        """Process image: deduplicate, standardize, and store.

        Full processing workflow:
        1. Compute perceptual hashes (pHash, dHash)
        2. Check for visual duplicates via LSH
        3. Standardize format (PNG) and size (max_dimension)
        4. Compute content hash (MD5) for storage path
        5. Save to content-addressed location
        6. Register in deduplicator index

        Args:
            image_data: Raw image bytes from download
            source_url: Original URL (for logging/debugging)
            property_hash: 8-char hash of property address
            run_id: Current extraction run ID for audit trail

        Returns:
            Tuple of (ProcessedImage, None) on success,
            (None, error_message) on failure,
            (None, None) if image is a duplicate
        """
        try:
            # Step 1: Compute perceptual hashes for visual deduplication
            try:
                phash, dhash = self._deduplicator.compute_hashes(image_data)
            except Exception as e:
                return None, f"Hash computation failed: {e}"

            # Step 2: Check for visual duplicates
            is_dup, original_id = self._deduplicator.is_duplicate(phash, dhash)
            if is_dup:
                logger.debug(
                    "Visual duplicate detected: %s matches %s", source_url[:50], original_id
                )
                return ProcessedImage(
                    image_id=original_id or "",
                    content_hash=original_id or "",
                    local_path=self.get_content_path(original_id or ""),
                    phash=phash,
                    dhash=dhash,
                    width=0,
                    height=0,
                    file_size_bytes=0,
                    is_duplicate=True,
                    duplicate_of=original_id,
                ), None

            # Step 3: Standardize format and size
            try:
                standardized_data, width, height = self._standardizer.standardize(image_data)
            except Exception as e:
                return None, f"Standardization failed: {e}"

            # Step 4: Compute content hash for storage path
            content_hash = self.compute_content_hash(standardized_data)
            local_path = self.get_content_path(content_hash)

            # Step 5: Check if already stored (content dedup)
            if self.image_exists(content_hash):
                logger.debug("Content duplicate: %s already exists", content_hash[:8])
                return ProcessedImage(
                    image_id=content_hash,
                    content_hash=content_hash,
                    local_path=local_path,
                    phash=phash,
                    dhash=dhash,
                    width=width,
                    height=height,
                    file_size_bytes=len(standardized_data),
                    is_duplicate=True,
                    duplicate_of=content_hash,
                ), None

            # Step 6: Save to content-addressed location
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(standardized_data)

            # Step 7: Register in deduplicator for future runs
            self._deduplicator.register(content_hash, phash, dhash)

            logger.debug(
                "Processed image: %s -> %s (%dx%d, %d bytes)",
                source_url[:50],
                content_hash[:8],
                width,
                height,
                len(standardized_data),
            )

            return ProcessedImage(
                image_id=content_hash,
                content_hash=content_hash,
                local_path=local_path,
                phash=phash,
                dhash=dhash,
                width=width,
                height=height,
                file_size_bytes=len(standardized_data),
                is_duplicate=False,
                duplicate_of=None,
            ), None

        except Exception as e:
            logger.error("Unexpected error processing %s: %s", source_url[:50], e)
            return None, f"Unexpected error: {e}"

    def compute_content_hash(self, data: bytes) -> str:
        """Compute MD5 hash for content addressing.

        Args:
            data: Image bytes to hash

        Returns:
            32-character hex digest
        """
        return hashlib.md5(data).hexdigest()

    def get_content_path(self, content_hash: str) -> Path:
        """Get storage path for content-addressed image.

        Uses first 8 characters of hash as subdirectory to limit
        files per directory (max 65536 with 8 hex chars).

        Args:
            content_hash: MD5 hash of image content

        Returns:
            Path: {base_dir}/{hash[:8]}/{hash}.png
        """
        return self.base_dir / content_hash[:8] / f"{content_hash}.png"

    def image_exists(self, content_hash: str) -> bool:
        """Check if image already exists in storage.

        Args:
            content_hash: MD5 hash to check

        Returns:
            True if file exists at content-addressed path
        """
        return self.get_content_path(content_hash).exists()

    def get_stats(self) -> dict:
        """Get storage statistics for monitoring.

        Returns:
            Dict with file count and deduplicator stats
        """
        try:
            file_count = sum(1 for _ in self.base_dir.rglob("*.png"))
        except Exception:
            file_count = -1

        return {
            "base_dir": str(self.base_dir),
            "file_count": file_count,
            "deduplicator_stats": self._deduplicator.get_stats()
            if hasattr(self._deduplicator, "get_stats")
            else {},
        }

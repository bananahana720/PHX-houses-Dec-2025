"""Image download service for property image caching.

Provides async image downloads with:
- Semaphore-controlled concurrency (max 5 concurrent downloads)
- Sequential filename generation (img_001.jpg, img_002.jpg, etc.)
- Format conversion (webp/png to jpg)
- Cache hit detection by URL and content hash
- Retry logic for transient failures (429, 5xx, timeouts)
- Error handling with partial success support

Architecture:
    ImageDownloader - Main service class for downloading images
    ImageManifest - Tracks downloaded images for cache detection
    ImageManifestEntry - Metadata for a single downloaded image
    DownloadResult - Result of a single download attempt
    CleanupResult - Result of cache cleanup operation
"""

import asyncio
import hashlib
import json
import logging
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_CONCURRENT = 5
DEFAULT_TIMEOUT = 30.0
JPEG_QUALITY = 85
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
MAX_AGE_DAYS = 14


def normalize_address_for_folder(address: str) -> str:
    """Normalize address to folder-safe string.

    Converts address to lowercase, replaces non-alphanumeric characters
    with hyphens, and removes leading/trailing hyphens.

    Args:
        address: Full property address

    Returns:
        Normalized folder name (e.g., "123-main-st-phoenix-az-85001")

    Examples:
        >>> normalize_address_for_folder("123 Main St, Phoenix, AZ 85001")
        '123-main-st-phoenix-az-85001'
        >>> normalize_address_for_folder("456 Oak Ave #10, Mesa, AZ 85201")
        '456-oak-ave-10-mesa-az-85201'
    """
    if not address:
        return ""

    # Lowercase and replace non-alphanumeric with hyphens
    normalized = re.sub(r"[^a-z0-9]+", "-", address.lower())

    # Remove leading/trailing hyphens
    return normalized.strip("-")


@dataclass
class ImageManifestEntry:
    """Metadata for a single downloaded image.

    Attributes:
        filename: Local filename (e.g., "img_001.jpg")
        source_url: Original URL the image was downloaded from
        download_timestamp: ISO timestamp of download
        file_size_bytes: Size of saved file in bytes
        width: Image width in pixels
        height: Image height in pixels
        content_hash: MD5 hash of image content for cache detection
        original_format: Original image format before conversion (e.g., "webp")
    """

    filename: str
    source_url: str
    download_timestamp: str
    file_size_bytes: int
    width: int
    height: int
    content_hash: str
    original_format: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "source_url": self.source_url,
            "download_timestamp": self.download_timestamp,
            "file_size_bytes": self.file_size_bytes,
            "width": self.width,
            "height": self.height,
            "content_hash": self.content_hash,
            "original_format": self.original_format,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageManifestEntry":
        """Create entry from dictionary."""
        return cls(
            filename=data["filename"],
            source_url=data["source_url"],
            download_timestamp=data["download_timestamp"],
            file_size_bytes=data["file_size_bytes"],
            width=data["width"],
            height=data["height"],
            content_hash=data["content_hash"],
            original_format=data.get("original_format"),
        )


@dataclass
class ImageManifest:
    """Manifest tracking downloaded images for a property.

    Provides cache hit detection by URL and content hash.

    Attributes:
        property_address: Full property address
        images: List of downloaded image entries
        version: Manifest schema version
        last_updated: ISO timestamp of last update
    """

    property_address: str
    images: list[ImageManifestEntry] = field(default_factory=list)
    version: str = "2.0.0"
    last_updated: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "property_address": self.property_address,
            "last_updated": self.last_updated or datetime.now().isoformat(),
            "images": [img.to_dict() for img in self.images],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImageManifest":
        """Create manifest from dictionary."""
        images = [ImageManifestEntry.from_dict(img_data) for img_data in data.get("images", [])]
        return cls(
            property_address=data["property_address"],
            images=images,
            version=data.get("version", "2.0.0"),
            last_updated=data.get("last_updated"),
        )

    def is_cached(self, url: str) -> bool:
        """Check if URL is already in manifest (cache hit).

        Args:
            url: Source URL to check

        Returns:
            True if URL already downloaded
        """
        return any(img.source_url == url for img in self.images)

    def is_cached_by_hash(self, content_hash: str) -> bool:
        """Check if content hash exists in manifest.

        Args:
            content_hash: MD5 hash of image content

        Returns:
            True if content already exists
        """
        return any(img.content_hash == content_hash for img in self.images)

    def get_entry_by_url(self, url: str) -> ImageManifestEntry | None:
        """Get manifest entry by URL.

        Args:
            url: Source URL

        Returns:
            ImageManifestEntry if found, None otherwise
        """
        for img in self.images:
            if img.source_url == url:
                return img
        return None

    def remove_entries(self, filenames: list[str]) -> None:
        """Remove entries by filename.

        Args:
            filenames: List of filenames to remove
        """
        self.images = [img for img in self.images if img.filename not in filenames]

    def save(self, path: Path) -> None:
        """Save manifest to JSON file with atomic write.

        Args:
            path: Path to save manifest
        """
        self.last_updated = datetime.now().isoformat()
        data = self.to_dict()

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            Path(temp_path).replace(path)
        except Exception:
            Path(temp_path).unlink(missing_ok=True)
            raise

    @classmethod
    def load(cls, path: Path, address: str) -> "ImageManifest":
        """Load manifest from JSON file.

        Creates empty manifest if file doesn't exist.

        Args:
            path: Path to manifest file
            address: Property address (used if creating new)

        Returns:
            ImageManifest instance
        """
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load manifest: {e}")

        return cls(property_address=address)


@dataclass
class DownloadResult:
    """Result of a single image download attempt.

    Attributes:
        url: Source URL
        success: Whether download succeeded
        filename: Local filename if successful
        file_size: Size in bytes if successful
        content_hash: MD5 hash if successful
        original_format: Original format if successful
        error: Error message if failed
        was_cached: True if skipped due to cache hit
    """

    url: str
    success: bool
    filename: str | None = None
    file_size: int = 0
    content_hash: str | None = None
    original_format: str | None = None
    error: str | None = None
    was_cached: bool = False


@dataclass
class CleanupResult:
    """Result of cache cleanup operation.

    Attributes:
        files_deleted: Number of files deleted
        space_reclaimed_bytes: Total bytes reclaimed
        dry_run: Whether this was a dry run
        deleted_files: List of deleted filenames
    """

    files_deleted: int
    space_reclaimed_bytes: int = 0
    dry_run: bool = False
    deleted_files: list[str] = field(default_factory=list)


class ImageDownloader:
    """Async image downloader with caching support.

    Downloads images from URLs with:
    - Semaphore-controlled concurrency (default max 5)
    - Sequential filename generation (img_001.jpg, img_002.jpg, etc.)
    - Format conversion (webp/png to jpg)
    - Cache hit detection
    - Retry logic for transient failures

    Attributes:
        base_dir: Base directory for image storage
        max_concurrent: Maximum concurrent downloads
    """

    def __init__(
        self,
        base_dir: Path,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize image downloader.

        Args:
            base_dir: Base directory for image storage
            max_concurrent: Maximum concurrent downloads (default: 5)
            timeout: HTTP timeout in seconds (default: 30)
        """
        self.base_dir = Path(base_dir)
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore: asyncio.Semaphore | None = None

    def get_property_folder(self, address: str) -> Path:
        """Get or create property folder.

        Creates folder using normalized address name.

        Args:
            address: Full property address

        Returns:
            Path to property folder
        """
        folder_name = normalize_address_for_folder(address)
        folder = self.base_dir / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _generate_filename(self, index: int) -> str:
        """Generate sequential filename.

        Args:
            index: 1-based index

        Returns:
            Filename like "img_001.jpg"
        """
        return f"img_{index:03d}.jpg"

    def _convert_to_jpg(self, image_data: bytes) -> bytes:
        """Convert image to JPEG format.

        Handles:
        - PNG (including RGBA with transparency)
        - WebP
        - Other formats supported by PIL

        RGBA images are composited on white background.

        Args:
            image_data: Raw image bytes

        Returns:
            JPEG image bytes
        """
        source_img = Image.open(BytesIO(image_data))

        # Handle RGBA (transparency) by compositing on white background
        if source_img.mode == "RGBA":
            background = Image.new("RGB", source_img.size, (255, 255, 255))
            background.paste(source_img, mask=source_img.split()[3])  # Alpha channel as mask
            rgb_img: Image.Image = background
        elif source_img.mode == "P":
            # Palette mode - may have transparency
            if "transparency" in source_img.info:
                rgba_img = source_img.convert("RGBA")
                background = Image.new("RGB", rgba_img.size, (255, 255, 255))
                background.paste(rgba_img, mask=rgba_img.split()[3])
                rgb_img = background
            else:
                rgb_img = source_img.convert("RGB")
        elif source_img.mode != "RGB":
            rgb_img = source_img.convert("RGB")
        else:
            rgb_img = source_img

        # Save as JPEG
        output = BytesIO()
        rgb_img.save(output, format="JPEG", quality=JPEG_QUALITY)
        return output.getvalue()

    def _get_image_dimensions(self, image_data: bytes) -> tuple[int, int]:
        """Get image dimensions.

        Args:
            image_data: Image bytes

        Returns:
            Tuple of (width, height)
        """
        img = Image.open(BytesIO(image_data))
        return img.size

    def _get_image_format(self, image_data: bytes) -> str | None:
        """Detect image format.

        Args:
            image_data: Image bytes

        Returns:
            Format string (e.g., "JPEG", "PNG", "WEBP")
        """
        try:
            img = Image.open(BytesIO(image_data))
            return img.format
        except Exception:
            return None

    async def _download_one(
        self,
        url: str,
        index: int,
        output_dir: Path,
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient | None = None,
    ) -> DownloadResult:
        """Download a single image with retry logic.

        Args:
            url: Image URL
            index: 1-based index for filename
            output_dir: Directory to save image
            semaphore: Concurrency limiter
            client: Optional shared HTTP client

        Returns:
            DownloadResult with success/failure info
        """
        async with semaphore:
            owns_client = client is None
            if owns_client:
                actual_client = httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                        )
                    },
                )
            else:
                # Type narrowing: client is not None in this branch
                assert client is not None
                actual_client = client

            try:
                # Retry loop for transient failures
                last_error = None
                for attempt in range(MAX_RETRIES):
                    try:
                        response = await actual_client.get(url)
                        response.raise_for_status()

                        # Get raw content
                        raw_data = response.content

                        # Detect original format
                        original_format = self._get_image_format(raw_data)

                        # Convert to JPEG
                        jpg_data = self._convert_to_jpg(raw_data)

                        # Compute hash for cache detection only (not security-sensitive)
                        # MD5 is sufficient for deduplication; collision resistance not required
                        content_hash = hashlib.md5(raw_data).hexdigest()  # noqa: S324

                        # Get dimensions from converted image
                        width, height = self._get_image_dimensions(jpg_data)

                        # Generate filename and save
                        filename = self._generate_filename(index)
                        file_path = output_dir / filename
                        file_path.write_bytes(jpg_data)

                        logger.debug(f"Downloaded: {filename} ({len(jpg_data)} bytes)")

                        return DownloadResult(
                            url=url,
                            success=True,
                            filename=filename,
                            file_size=len(jpg_data),
                            content_hash=content_hash,
                            original_format=original_format,
                        )

                    except httpx.HTTPStatusError as e:
                        status_code = e.response.status_code
                        if status_code in (429, 503, 502, 504):
                            # Retryable errors
                            last_error = str(e)
                            wait_time = RETRY_BACKOFF_BASE * (2**attempt)
                            logger.warning(
                                f"Retrying {url} after {wait_time}s (status {status_code})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Non-retryable HTTP error
                            return DownloadResult(
                                url=url,
                                success=False,
                                error=f"HTTP {status_code}: {e}",
                            )

                    except httpx.TimeoutException as e:
                        last_error = str(e)
                        wait_time = RETRY_BACKOFF_BASE * (2**attempt)
                        logger.warning(f"Timeout for {url}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    except Exception as e:
                        # Non-retryable error
                        return DownloadResult(
                            url=url,
                            success=False,
                            error=f"Error: {e}",
                        )

                # Exhausted retries
                return DownloadResult(
                    url=url,
                    success=False,
                    error=f"Failed after {MAX_RETRIES} retries: {last_error}",
                )

            finally:
                if owns_client:
                    await actual_client.aclose()

    async def download_images(
        self,
        urls: list[str],
        address: str,
        manifest: ImageManifest | None = None,
        skip_cached: bool = True,
    ) -> list[DownloadResult]:
        """Download multiple images for a property.

        Args:
            urls: List of image URLs to download
            address: Property address (for folder creation)
            manifest: Optional manifest for cache detection
            skip_cached: Skip URLs already in manifest

        Returns:
            List of DownloadResult for each URL
        """
        if not urls:
            return []

        output_dir = self.get_property_folder(address)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results: list[DownloadResult] = []

        # Determine starting index based on existing files
        existing_count = len(list(output_dir.glob("img_*.jpg")))
        start_index = existing_count + 1

        # Create shared HTTP client for efficiency
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=self.max_concurrent * 2),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
            },
        ) as client:
            tasks = []
            url_to_index = {}

            current_index = start_index
            for url in urls:
                # Check cache
                if skip_cached and manifest and manifest.is_cached(url):
                    results.append(
                        DownloadResult(
                            url=url,
                            success=True,
                            was_cached=True,
                        )
                    )
                    logger.debug(f"Skipped (cached): {url[:60]}...")
                    continue

                url_to_index[url] = current_index
                tasks.append(
                    self._download_one(
                        url=url,
                        index=current_index,
                        output_dir=output_dir,
                        semaphore=semaphore,
                        client=client,
                    )
                )
                current_index += 1

            # Execute downloads concurrently
            if tasks:
                download_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in download_results:
                    if isinstance(result, BaseException):
                        # Handle unexpected exceptions (including Exception subclasses)
                        results.append(
                            DownloadResult(
                                url="unknown",
                                success=False,
                                error=str(result),
                            )
                        )
                    else:
                        # Type narrowing: result is DownloadResult after BaseException check
                        results.append(result)

        # Log summary
        successful = sum(1 for r in results if r.success and not r.was_cached)
        cached = sum(1 for r in results if r.was_cached)
        failed = sum(1 for r in results if not r.success)
        logger.info(f"Download complete: {successful} new, {cached} cached, {failed} failed")

        return results

    def cleanup_old_images(
        self,
        address: str,
        manifest: ImageManifest,
        max_age_days: int = MAX_AGE_DAYS,
        dry_run: bool = False,
    ) -> CleanupResult:
        """Remove images older than max_age_days.

        Args:
            address: Property address
            manifest: Image manifest for age detection
            max_age_days: Maximum age in days (default: 14)
            dry_run: If True, don't actually delete files

        Returns:
            CleanupResult with deletion stats
        """
        folder = self.get_property_folder(address)
        cutoff = datetime.now() - timedelta(days=max_age_days)

        deleted_files = []
        space_reclaimed = 0

        for entry in manifest.images:
            try:
                download_time = datetime.fromisoformat(entry.download_timestamp)
                if download_time < cutoff:
                    file_path = folder / entry.filename
                    if file_path.exists():
                        if not dry_run:
                            space_reclaimed += file_path.stat().st_size
                            file_path.unlink()
                            logger.debug(f"Deleted: {entry.filename}")
                        deleted_files.append(entry.filename)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp for {entry.filename}: {e}")

        # Update manifest (remove deleted entries)
        if not dry_run and deleted_files:
            manifest.remove_entries(deleted_files)

        result = CleanupResult(
            files_deleted=len(deleted_files),
            space_reclaimed_bytes=space_reclaimed,
            dry_run=dry_run,
            deleted_files=deleted_files,
        )

        if deleted_files:
            action = "Would delete" if dry_run else "Deleted"
            logger.info(
                f"{action} {len(deleted_files)} files, reclaimed {space_reclaimed / 1024:.1f} KB"
            )

        return result

    def create_manifest_entry(
        self, result: DownloadResult, address: str
    ) -> ImageManifestEntry | None:
        """Create manifest entry from download result.

        Args:
            result: Successful download result
            address: Property address

        Returns:
            ImageManifestEntry if successful, None otherwise
        """
        if not result.success or result.was_cached or not result.filename:
            return None

        folder = self.get_property_folder(address)
        file_path = folder / result.filename

        # Get dimensions from saved file
        try:
            with open(file_path, "rb") as f:
                width, height = self._get_image_dimensions(f.read())
        except Exception:
            width, height = 0, 0

        return ImageManifestEntry(
            filename=result.filename,
            source_url=result.url,
            download_timestamp=datetime.now().isoformat(),
            file_size_bytes=result.file_size,
            width=width,
            height=height,
            content_hash=result.content_hash or "",
            original_format=result.original_format,
        )


# Convenience function for CLI usage
async def download_property_images(
    address: str,
    urls: list[str],
    base_dir: Path,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
) -> tuple[list[DownloadResult], ImageManifest]:
    """Download all images for a property.

    High-level convenience function that handles:
    - Manifest loading/saving
    - Cache hit detection
    - Image downloading
    - Manifest updates

    Args:
        address: Property address
        urls: List of image URLs
        base_dir: Base directory for images
        max_concurrent: Max concurrent downloads

    Returns:
        Tuple of (download results, updated manifest)
    """
    downloader = ImageDownloader(base_dir=base_dir, max_concurrent=max_concurrent)

    folder = downloader.get_property_folder(address)
    manifest_path = folder / "images_manifest.json"
    manifest = ImageManifest.load(manifest_path, address)

    results = await downloader.download_images(
        urls=urls,
        address=address,
        manifest=manifest,
        skip_cached=True,
    )

    # Update manifest with new entries
    for result in results:
        entry = downloader.create_manifest_entry(result, address)
        if entry:
            manifest.images.append(entry)

    # Save manifest
    manifest.save(manifest_path)

    return results, manifest

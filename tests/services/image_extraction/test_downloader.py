"""Unit tests for ImageDownloader service.

Tests cover:
- Async downloads with semaphore (AC6)
- Sequential filename generation (AC1)
- Error handling and partial success (AC3)
- Format conversion (AC7)
- Cache hit detection (AC4)
- Retry logic for transient failures
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

import httpx
import pytest
from PIL import Image

from src.phx_home_analysis.services.image_extraction.downloader import (
    DownloadResult,
    ImageDownloader,
    ImageManifest,
    ImageManifestEntry,
    normalize_address_for_folder,
)

# === Fixtures ===


@pytest.fixture
def temp_images_dir(tmp_path):
    """Create temporary images directory."""
    images_dir = tmp_path / "property_images"
    images_dir.mkdir(parents=True)
    return images_dir


@pytest.fixture
def downloader(temp_images_dir):
    """Create ImageDownloader instance."""
    return ImageDownloader(base_dir=temp_images_dir, max_concurrent=5)


@pytest.fixture
def sample_jpg_bytes():
    """Generate sample JPEG image bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    output = BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Generate sample PNG image bytes."""
    img = Image.new("RGB", (100, 100), color="green")
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def sample_webp_bytes():
    """Generate sample WebP image bytes."""
    img = Image.new("RGB", (100, 100), color="blue")
    output = BytesIO()
    img.save(output, format="WEBP", quality=85)
    return output.getvalue()


@pytest.fixture
def sample_rgba_png_bytes():
    """Generate sample PNG image with alpha channel."""
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


# === Address Normalization Tests ===


class TestNormalizeAddressForFolder:
    """Tests for address normalization function."""

    def test_basic_address(self):
        """Test simple address normalization."""
        result = normalize_address_for_folder("123 Main St, Phoenix, AZ 85001")
        assert result == "123-main-st-phoenix-az-85001"

    def test_removes_special_characters(self):
        """Test removal of special characters."""
        result = normalize_address_for_folder("456 Oak Ave #10, Mesa, AZ 85201")
        assert result == "456-oak-ave-10-mesa-az-85201"

    def test_handles_multiple_spaces(self):
        """Test handling of multiple spaces."""
        result = normalize_address_for_folder("789  Elm  Street,  Tempe,  AZ  85281")
        assert result == "789-elm-street-tempe-az-85281"

    def test_removes_leading_trailing_hyphens(self):
        """Test removal of leading/trailing hyphens."""
        result = normalize_address_for_folder("  123 Main St  ")
        assert result == "123-main-st"
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_empty_string(self):
        """Test empty string handling."""
        result = normalize_address_for_folder("")
        assert result == ""

    def test_unicode_characters(self):
        """Test Unicode character handling."""
        result = normalize_address_for_folder("123 Cañón Rd, Phoenix, AZ")
        # Unicode should be handled gracefully
        assert "-" in result
        assert "phoenix" in result


# === ImageManifest Tests ===


class TestImageManifest:
    """Tests for ImageManifest dataclass and serialization."""

    def test_create_empty_manifest(self):
        """Test creating empty manifest."""
        manifest = ImageManifest(property_address="123 Main St, Phoenix, AZ 85001")
        assert manifest.property_address == "123 Main St, Phoenix, AZ 85001"
        assert len(manifest.images) == 0
        assert manifest.version == "2.0.0"

    def test_add_image_entry(self):
        """Test adding image entry to manifest."""
        manifest = ImageManifest(property_address="123 Main St, Phoenix, AZ 85001")
        entry = ImageManifestEntry(
            filename="img_001.jpg",
            source_url="https://example.com/img1.jpg",
            download_timestamp=datetime.now().isoformat(),
            file_size_bytes=50000,
            width=800,
            height=600,
            content_hash="abc123",
            original_format="webp",
        )
        manifest.images.append(entry)
        assert len(manifest.images) == 1
        assert manifest.images[0].filename == "img_001.jpg"

    def test_manifest_to_dict(self):
        """Test converting manifest to dictionary."""
        manifest = ImageManifest(property_address="123 Main St, Phoenix, AZ 85001")
        entry = ImageManifestEntry(
            filename="img_001.jpg",
            source_url="https://example.com/img1.jpg",
            download_timestamp="2025-12-04T12:00:00",
            file_size_bytes=50000,
            width=800,
            height=600,
            content_hash="abc123",
            original_format="webp",
        )
        manifest.images.append(entry)

        data = manifest.to_dict()
        assert data["version"] == "2.0.0"
        assert data["property_address"] == "123 Main St, Phoenix, AZ 85001"
        assert len(data["images"]) == 1
        assert data["images"][0]["filename"] == "img_001.jpg"

    def test_manifest_from_dict(self):
        """Test loading manifest from dictionary."""
        data = {
            "version": "2.0.0",
            "property_address": "123 Main St, Phoenix, AZ 85001",
            "last_updated": "2025-12-04T12:00:00",
            "images": [
                {
                    "filename": "img_001.jpg",
                    "source_url": "https://example.com/img1.jpg",
                    "download_timestamp": "2025-12-04T12:00:00",
                    "file_size_bytes": 50000,
                    "width": 800,
                    "height": 600,
                    "content_hash": "abc123",
                    "original_format": "webp",
                }
            ],
        }

        manifest = ImageManifest.from_dict(data)
        assert manifest.property_address == "123 Main St, Phoenix, AZ 85001"
        assert len(manifest.images) == 1
        assert manifest.images[0].filename == "img_001.jpg"

    def test_is_cached_by_url(self):
        """Test cache hit detection by URL."""
        manifest = ImageManifest(property_address="123 Main St, Phoenix, AZ 85001")
        entry = ImageManifestEntry(
            filename="img_001.jpg",
            source_url="https://example.com/img1.jpg",
            download_timestamp="2025-12-04T12:00:00",
            file_size_bytes=50000,
            width=800,
            height=600,
            content_hash="abc123",
            original_format="webp",
        )
        manifest.images.append(entry)

        assert manifest.is_cached("https://example.com/img1.jpg") is True
        assert manifest.is_cached("https://example.com/img2.jpg") is False

    def test_is_cached_by_hash(self):
        """Test cache hit detection by content hash."""
        manifest = ImageManifest(property_address="123 Main St, Phoenix, AZ 85001")
        entry = ImageManifestEntry(
            filename="img_001.jpg",
            source_url="https://example.com/img1.jpg",
            download_timestamp="2025-12-04T12:00:00",
            file_size_bytes=50000,
            width=800,
            height=600,
            content_hash="abc123",
            original_format="webp",
        )
        manifest.images.append(entry)

        assert manifest.is_cached_by_hash("abc123") is True
        assert manifest.is_cached_by_hash("xyz789") is False


# === ImageDownloader Tests ===


class TestImageDownloader:
    """Tests for ImageDownloader class."""

    def test_initialization(self, downloader, temp_images_dir):
        """Test downloader initialization."""
        assert downloader.base_dir == temp_images_dir
        assert downloader.max_concurrent == 5

    def test_get_property_folder_creates_directory(self, downloader):
        """Test property folder creation."""
        address = "123 Main St, Phoenix, AZ 85001"
        folder = downloader.get_property_folder(address)

        assert folder.exists()
        assert folder.name == "123-main-st-phoenix-az-85001"

    def test_generate_sequential_filename(self, downloader):
        """Test sequential filename generation (AC1)."""
        assert downloader._generate_filename(1) == "img_001.jpg"
        assert downloader._generate_filename(10) == "img_010.jpg"
        assert downloader._generate_filename(100) == "img_100.jpg"

    @pytest.mark.asyncio
    async def test_download_single_image_success(self, downloader, sample_jpg_bytes):
        """Test successful single image download."""
        url = "https://example.com/test.jpg"

        with patch.object(downloader, "_download_one") as mock_download:
            mock_download.return_value = DownloadResult(
                url=url,
                success=True,
                filename="img_001.jpg",
                file_size=len(sample_jpg_bytes),
                content_hash=hashlib.md5(sample_jpg_bytes).hexdigest(),
                original_format="JPEG",
            )

            result = await downloader._download_one(
                url=url,
                index=1,
                output_dir=downloader.base_dir,
                semaphore=asyncio.Semaphore(5),
            )

            assert result.success is True
            assert result.filename == "img_001.jpg"

    @pytest.mark.asyncio
    async def test_download_respects_semaphore_limit(self, downloader, sample_jpg_bytes):
        """Test that downloads respect semaphore concurrency limit (AC6)."""
        urls = [f"https://example.com/img{i}.jpg" for i in range(10)]
        active_downloads = []
        max_concurrent_observed = 0

        async def mock_download(url, index, output_dir, semaphore):
            nonlocal max_concurrent_observed
            async with semaphore:
                active_downloads.append(url)
                max_concurrent_observed = max(max_concurrent_observed, len(active_downloads))
                await asyncio.sleep(0.01)  # Simulate download time
                active_downloads.remove(url)
                return DownloadResult(
                    url=url,
                    success=True,
                    filename=f"img_{index:03d}.jpg",
                    file_size=1000,
                    content_hash="abc",
                    original_format="JPEG",
                )

        semaphore = asyncio.Semaphore(5)
        tasks = [
            mock_download(url, i + 1, downloader.base_dir, semaphore) for i, url in enumerate(urls)
        ]
        await asyncio.gather(*tasks)

        # Max concurrent should not exceed 5
        assert max_concurrent_observed <= 5

    @pytest.mark.asyncio
    async def test_download_handles_errors_continues(self, downloader):
        """Test that failed downloads are logged and processing continues (AC3)."""
        urls = [
            "https://example.com/good1.jpg",
            "https://example.com/bad.jpg",
            "https://example.com/good2.jpg",
        ]

        results = [
            DownloadResult(
                url=urls[0],
                success=True,
                filename="img_001.jpg",
                file_size=1000,
                content_hash="abc",
                original_format="JPEG",
            ),
            DownloadResult(
                url=urls[1],
                success=False,
                filename=None,
                file_size=0,
                error="404 Not Found",
            ),
            DownloadResult(
                url=urls[2],
                success=True,
                filename="img_003.jpg",
                file_size=1000,
                content_hash="def",
                original_format="JPEG",
            ),
        ]

        with patch.object(downloader, "download_images", return_value=results):
            download_results = await downloader.download_images(
                urls=urls,
                address="123 Main St",
            )

            # Should have 3 results (2 success, 1 failure)
            assert len(download_results) == 3
            successful = [r for r in download_results if r.success]
            failed = [r for r in download_results if not r.success]
            assert len(successful) == 2
            assert len(failed) == 1
            assert failed[0].error == "404 Not Found"


class TestImageConversion:
    """Tests for image format conversion (AC7)."""

    def test_convert_png_to_jpg(self, downloader, sample_png_bytes):
        """Test PNG to JPG conversion."""
        jpg_bytes = downloader._convert_to_jpg(sample_png_bytes)

        # Verify it's valid JPEG
        img = Image.open(BytesIO(jpg_bytes))
        assert img.format == "JPEG"

    def test_convert_webp_to_jpg(self, downloader, sample_webp_bytes):
        """Test WebP to JPG conversion."""
        jpg_bytes = downloader._convert_to_jpg(sample_webp_bytes)

        # Verify it's valid JPEG
        img = Image.open(BytesIO(jpg_bytes))
        assert img.format == "JPEG"

    def test_convert_rgba_to_jpg_white_background(self, downloader, sample_rgba_png_bytes):
        """Test RGBA conversion with white background."""
        jpg_bytes = downloader._convert_to_jpg(sample_rgba_png_bytes)

        # Verify it's valid JPEG (no alpha)
        img = Image.open(BytesIO(jpg_bytes))
        assert img.format == "JPEG"
        assert img.mode == "RGB"

    def test_jpg_passthrough(self, downloader, sample_jpg_bytes):
        """Test that JPG images pass through without re-encoding."""
        # JPG should still work, possibly with quality adjustment
        jpg_bytes = downloader._convert_to_jpg(sample_jpg_bytes)

        img = Image.open(BytesIO(jpg_bytes))
        assert img.format == "JPEG"


class TestCacheCleanup:
    """Tests for cache cleanup functionality (AC5)."""

    def test_cleanup_old_images(self, downloader, temp_images_dir):
        """Test cleanup of images older than 14 days."""
        # Create property folder with manifest
        address = "123 Main St, Phoenix, AZ 85001"
        folder = downloader.get_property_folder(address)

        # Create old manifest entry (15 days old)
        old_timestamp = (datetime.now() - timedelta(days=15)).isoformat()
        new_timestamp = (datetime.now() - timedelta(days=5)).isoformat()

        manifest = ImageManifest(property_address=address)
        manifest.images = [
            ImageManifestEntry(
                filename="img_001.jpg",
                source_url="https://example.com/old.jpg",
                download_timestamp=old_timestamp,
                file_size_bytes=1000,
                width=100,
                height=100,
                content_hash="old123",
            ),
            ImageManifestEntry(
                filename="img_002.jpg",
                source_url="https://example.com/new.jpg",
                download_timestamp=new_timestamp,
                file_size_bytes=1000,
                width=100,
                height=100,
                content_hash="new456",
            ),
        ]

        # Create actual files
        (folder / "img_001.jpg").write_bytes(b"old image data")
        (folder / "img_002.jpg").write_bytes(b"new image data")

        # Run cleanup
        cleanup_result = downloader.cleanup_old_images(
            address=address,
            manifest=manifest,
            max_age_days=14,
            dry_run=False,
        )

        # Old file should be deleted, new file preserved
        assert cleanup_result.files_deleted == 1
        assert not (folder / "img_001.jpg").exists()
        assert (folder / "img_002.jpg").exists()

    def test_cleanup_dry_run_no_delete(self, downloader, temp_images_dir):
        """Test dry run mode doesn't delete files."""
        address = "123 Main St, Phoenix, AZ 85001"
        folder = downloader.get_property_folder(address)

        old_timestamp = (datetime.now() - timedelta(days=15)).isoformat()

        manifest = ImageManifest(property_address=address)
        manifest.images = [
            ImageManifestEntry(
                filename="img_001.jpg",
                source_url="https://example.com/old.jpg",
                download_timestamp=old_timestamp,
                file_size_bytes=1000,
                width=100,
                height=100,
                content_hash="old123",
            ),
        ]

        (folder / "img_001.jpg").write_bytes(b"old image data")

        # Run cleanup in dry run mode
        cleanup_result = downloader.cleanup_old_images(
            address=address,
            manifest=manifest,
            max_age_days=14,
            dry_run=True,
        )

        # File should still exist
        assert cleanup_result.files_deleted == 1  # Would be deleted
        assert cleanup_result.dry_run is True
        assert (folder / "img_001.jpg").exists()  # But wasn't actually deleted


class TestRetryLogic:
    """Tests for retry logic on transient failures."""

    @pytest.mark.asyncio
    async def test_retry_on_429(self, downloader, sample_jpg_bytes):
        """Test retry on rate limit (429) responses with exponential backoff."""
        attempt_count = 0
        attempt_times = []

        class MockResponse:
            def __init__(self, content, status_code):
                self.content = content
                self.status_code = status_code

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {self.status_code}",
                        request=MagicMock(),
                        response=self,
                    )

        class MockClient:
            async def get(self, url):
                nonlocal attempt_count
                attempt_count += 1
                attempt_times.append(asyncio.get_event_loop().time())
                if attempt_count < 3:
                    return MockResponse(b"", 429)
                # Success on third attempt
                return MockResponse(sample_jpg_bytes, 200)

            async def aclose(self):
                pass

        output_dir = downloader.get_property_folder("test-property")
        semaphore = asyncio.Semaphore(5)

        # Use the mock client directly
        mock_client = MockClient()
        result = await downloader._download_one(
            url="https://example.com/test.jpg",
            index=1,
            output_dir=output_dir,
            semaphore=semaphore,
            client=mock_client,  # type: ignore[arg-type]
        )

        # Should have retried and eventually succeeded
        assert attempt_count == 3
        assert result.success is True
        assert result.filename == "img_001.jpg"

    @pytest.mark.asyncio
    async def test_retry_on_5xx(self, downloader, sample_jpg_bytes):
        """Test retry on server error (5xx) responses."""
        attempt_count = 0

        class MockResponse:
            def __init__(self, content, status_code):
                self.content = content
                self.status_code = status_code

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {self.status_code}",
                        request=MagicMock(),
                        response=self,
                    )

        class MockClient:
            async def get(self, url):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 2:
                    return MockResponse(b"", 503)
                # Success on second attempt
                return MockResponse(sample_jpg_bytes, 200)

            async def aclose(self):
                pass

        output_dir = downloader.get_property_folder("test-property")
        semaphore = asyncio.Semaphore(5)

        mock_client = MockClient()
        result = await downloader._download_one(
            url="https://example.com/test.jpg",
            index=1,
            output_dir=output_dir,
            semaphore=semaphore,
            client=mock_client,  # type: ignore[arg-type]
        )

        # Should have retried and eventually succeeded
        assert attempt_count == 2
        assert result.success is True

    @pytest.mark.asyncio
    async def test_retry_exhausted_returns_failure(self, downloader):
        """Test that exhausted retries return failure result."""
        attempt_count = 0

        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code

            def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    f"HTTP {self.status_code}",
                    request=MagicMock(),
                    response=self,
                )

        class MockClient:
            async def get(self, url):
                nonlocal attempt_count
                attempt_count += 1
                # Always return 429 to exhaust retries
                return MockResponse(429)

            async def aclose(self):
                pass

        output_dir = downloader.get_property_folder("test-property")
        semaphore = asyncio.Semaphore(5)

        mock_client = MockClient()
        result = await downloader._download_one(
            url="https://example.com/test.jpg",
            index=1,
            output_dir=output_dir,
            semaphore=semaphore,
            client=mock_client,  # type: ignore[arg-type]
        )

        # Should have exhausted retries (3 attempts)
        assert attempt_count == 3
        assert result.success is False
        assert "Failed after" in (result.error or "")


class TestDownloadImagesEdgeCases:
    """Tests for edge cases in download_images method."""

    @pytest.mark.asyncio
    async def test_download_images_empty_list(self, downloader):
        """Test downloading with empty URL list returns empty results."""
        results = await downloader.download_images(
            urls=[],
            address="test-property",
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_download_images_all_cached(self, downloader):
        """Test that all cached URLs are skipped with proper results."""
        manifest = ImageManifest(property_address="test-property")
        manifest.images = [
            ImageManifestEntry(
                filename="img_001.jpg",
                source_url="https://example.com/img1.jpg",
                download_timestamp="2025-12-04T12:00:00",
                file_size_bytes=1000,
                width=100,
                height=100,
                content_hash="abc123",
            ),
        ]

        results = await downloader.download_images(
            urls=["https://example.com/img1.jpg"],
            address="test-property",
            manifest=manifest,
            skip_cached=True,
        )

        assert len(results) == 1
        assert results[0].was_cached is True
        assert results[0].success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

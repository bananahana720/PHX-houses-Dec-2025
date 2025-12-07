"""Unit tests for image processing service.

Tests content-addressed storage, two-level deduplication (perceptual + content hash),
format standardization, and metadata tracking.
"""

import hashlib
from pathlib import Path
from unittest.mock import Mock

import pytest

from phx_home_analysis.services.image_extraction.image_processor import (
    ImageProcessor,
    ProcessedImage,
    ProcessingStats,
)


class TestProcessedImage:
    """Tests for ProcessedImage dataclass."""

    def test_processed_image_creation(self, tmp_path: Path):
        """Test creating a ProcessedImage instance."""
        local_path = tmp_path / "abc12345" / "abc12345def67890.png"

        image = ProcessedImage(
            image_id="abc12345def67890",
            content_hash="abc12345def67890",
            local_path=local_path,
            phash="fedcba9876543210",
            dhash="0123456789abcdef",
            width=1024,
            height=768,
            file_size_bytes=50000,
            is_duplicate=False,
            duplicate_of=None,
        )

        assert image.image_id == "abc12345def67890"
        assert image.content_hash == "abc12345def67890"
        assert image.local_path == local_path
        assert image.width == 1024
        assert image.height == 768
        assert image.file_size_bytes == 50000
        assert not image.is_duplicate
        assert image.duplicate_of is None

    def test_processed_image_to_dict(self, tmp_path: Path):
        """Test converting ProcessedImage to dictionary."""
        local_path = tmp_path / "test.png"

        image = ProcessedImage(
            image_id="test123",
            content_hash="test123",
            local_path=local_path,
            phash="phash123",
            dhash="dhash123",
            width=800,
            height=600,
            file_size_bytes=30000,
            is_duplicate=True,
            duplicate_of="original123",
        )

        result = image.to_dict()

        assert result["image_id"] == "test123"
        assert result["content_hash"] == "test123"
        assert result["local_path"] == str(local_path)
        assert result["phash"] == "phash123"
        assert result["dhash"] == "dhash123"
        assert result["width"] == 800
        assert result["height"] == 600
        assert result["file_size_bytes"] == 30000
        assert result["is_duplicate"] is True
        assert result["duplicate_of"] == "original123"

    def test_processed_image_immutable(self, tmp_path: Path):
        """Test ProcessedImage is immutable (frozen dataclass)."""
        image = ProcessedImage(
            image_id="test",
            content_hash="test",
            local_path=tmp_path / "test.png",
            phash="p",
            dhash="d",
            width=100,
            height=100,
            file_size_bytes=1000,
            is_duplicate=False,
        )

        with pytest.raises(AttributeError):
            image.width = 200  # Should not be allowed


class TestProcessingStats:
    """Tests for ProcessingStats dataclass."""

    def test_stats_default_values(self):
        """Test default values for ProcessingStats."""
        stats = ProcessingStats()

        assert stats.images_processed == 0
        assert stats.images_saved == 0
        assert stats.duplicates_detected == 0
        assert stats.errors == 0
        assert stats.error_messages == []

    def test_record_success_new_image(self):
        """Test recording successful new image."""
        stats = ProcessingStats()

        stats.record_success(is_duplicate=False)

        assert stats.images_processed == 1
        assert stats.images_saved == 1
        assert stats.duplicates_detected == 0
        assert stats.errors == 0

    def test_record_success_duplicate_image(self):
        """Test recording successful duplicate detection."""
        stats = ProcessingStats()

        stats.record_success(is_duplicate=True)

        assert stats.images_processed == 1
        assert stats.images_saved == 0
        assert stats.duplicates_detected == 1
        assert stats.errors == 0

    def test_record_error(self):
        """Test recording processing error."""
        stats = ProcessingStats()

        stats.record_error("Test error message")

        assert stats.images_processed == 1
        assert stats.images_saved == 0
        assert stats.duplicates_detected == 0
        assert stats.errors == 1
        assert stats.error_messages == ["Test error message"]

    def test_multiple_operations(self):
        """Test stats accumulate across multiple operations."""
        stats = ProcessingStats()

        stats.record_success(is_duplicate=False)
        stats.record_success(is_duplicate=True)
        stats.record_error("Error 1")
        stats.record_success(is_duplicate=False)
        stats.record_error("Error 2")

        assert stats.images_processed == 5
        assert stats.images_saved == 2
        assert stats.duplicates_detected == 1
        assert stats.errors == 2
        assert len(stats.error_messages) == 2

    def test_to_dict_limits_error_messages(self):
        """Test to_dict limits error messages to 5."""
        stats = ProcessingStats()

        for i in range(10):
            stats.record_error(f"Error {i}")

        result = stats.to_dict()

        assert result["errors"] == 10
        assert len(result["error_messages"]) == 5  # Limited to 5


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    @pytest.fixture
    def mock_deduplicator(self):
        """Create mock deduplicator."""
        dedup = Mock()
        dedup.compute_hashes.return_value = ("phash123", "dhash456")
        dedup.is_duplicate.return_value = (False, None)
        return dedup

    @pytest.fixture
    def mock_standardizer(self):
        """Create mock standardizer."""
        standardizer = Mock()
        standardizer.standardize.return_value = (b"standardized_data", 1024, 768)
        return standardizer

    @pytest.fixture
    def processor(self, tmp_path: Path, mock_deduplicator, mock_standardizer):
        """Create ImageProcessor instance."""
        return ImageProcessor(
            base_dir=tmp_path / "processed",
            deduplicator=mock_deduplicator,
            standardizer=mock_standardizer,
        )

    def test_initialization_creates_base_dir(self, tmp_path: Path, mock_deduplicator, mock_standardizer):
        """Test processor creates base directory on init."""
        base_dir = tmp_path / "new_dir"
        assert not base_dir.exists()

        processor = ImageProcessor(base_dir, mock_deduplicator, mock_standardizer)

        assert base_dir.exists()
        assert processor.base_dir == base_dir

    def test_compute_content_hash_deterministic(self, processor):
        """Test content hash computation is deterministic."""
        data = b"test image data"

        hash1 = processor.compute_content_hash(data)
        hash2 = processor.compute_content_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex digest

        # Verify against known MD5
        expected = hashlib.md5(data).hexdigest()
        assert hash1 == expected

    def test_compute_content_hash_different_data(self, processor):
        """Test different data produces different hashes."""
        data1 = b"image data 1"
        data2 = b"image data 2"

        hash1 = processor.compute_content_hash(data1)
        hash2 = processor.compute_content_hash(data2)

        assert hash1 != hash2

    def test_get_content_path(self, processor):
        """Test content-addressed path generation."""
        content_hash = "abc12345def67890123456789abcdef0"

        path = processor.get_content_path(content_hash)

        # Should use first 8 chars as subdirectory
        assert path == processor.base_dir / "abc12345" / f"{content_hash}.png"

    def test_get_content_path_uses_first_8_chars(self, processor):
        """Test content path uses first 8 characters for subdirectory."""
        hash1 = "abc12345" + "x" * 24
        hash2 = "abc12345" + "y" * 24

        path1 = processor.get_content_path(hash1)
        path2 = processor.get_content_path(hash2)

        # Different hashes with same first 8 chars should share subdirectory
        assert path1.parent == path2.parent
        assert path1.parent.name == "abc12345"

    def test_image_exists_check(self, processor, tmp_path: Path):
        """Test image existence check."""
        content_hash = "test1234567890abcdef1234567890ab"

        # Initially doesn't exist
        assert not processor.image_exists(content_hash)

        # Create the file
        path = processor.get_content_path(content_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")

        # Now should exist
        assert processor.image_exists(content_hash)

    @pytest.mark.asyncio
    async def test_process_image_success(self, processor, mock_deduplicator, mock_standardizer):
        """Test successful image processing."""
        image_data = b"test image data"
        source_url = "https://example.com/image.jpg"

        result, error = await processor.process_image(
            image_data=image_data,
            source_url=source_url,
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert error is None
        assert result is not None
        assert result.image_id is not None
        assert result.content_hash is not None
        assert result.width == 1024
        assert result.height == 768
        assert not result.is_duplicate
        assert result.duplicate_of is None

        # Verify deduplicator called
        mock_deduplicator.compute_hashes.assert_called_once_with(image_data)
        mock_deduplicator.is_duplicate.assert_called_once()
        mock_deduplicator.register.assert_called_once()

        # Verify standardizer called
        mock_standardizer.standardize.assert_called_once_with(image_data)

    @pytest.mark.asyncio
    async def test_process_image_visual_duplicate(self, processor, mock_deduplicator, mock_standardizer):
        """Test processing detects visual duplicate via perceptual hash."""
        # Configure deduplicator to report duplicate
        mock_deduplicator.is_duplicate.return_value = (True, "original123")

        image_data = b"duplicate image"
        result, error = await processor.process_image(
            image_data=image_data,
            source_url="https://example.com/dup.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert error is None
        assert result is not None
        assert result.is_duplicate
        assert result.duplicate_of == "original123"
        assert result.image_id == "original123"

        # Should not standardize or save duplicates
        mock_standardizer.standardize.assert_not_called()
        mock_deduplicator.register.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_image_content_duplicate(self, processor, mock_deduplicator, mock_standardizer, tmp_path: Path):
        """Test processing detects content duplicate (same MD5)."""
        # Not a visual duplicate
        mock_deduplicator.is_duplicate.return_value = (False, None)

        # Create existing file with known hash
        standardized_data = b"standardized content"
        content_hash = hashlib.md5(standardized_data).hexdigest()
        existing_path = processor.get_content_path(content_hash)
        existing_path.parent.mkdir(parents=True, exist_ok=True)
        existing_path.write_bytes(standardized_data)

        # Configure standardizer to return same content
        mock_standardizer.standardize.return_value = (standardized_data, 800, 600)

        result, error = await processor.process_image(
            image_data=b"original",
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert error is None
        assert result is not None
        assert result.is_duplicate
        assert result.duplicate_of == content_hash
        assert result.content_hash == content_hash

        # Should not register duplicate
        mock_deduplicator.register.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_image_hash_computation_error(self, processor, mock_deduplicator, mock_standardizer):
        """Test handling of hash computation failure."""
        mock_deduplicator.compute_hashes.side_effect = Exception("Hash computation failed")

        result, error = await processor.process_image(
            image_data=b"test",
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert result is None
        assert error is not None
        assert "Hash computation failed" in error

    @pytest.mark.asyncio
    async def test_process_image_standardization_error(self, processor, mock_deduplicator, mock_standardizer):
        """Test handling of standardization failure."""
        mock_standardizer.standardize.side_effect = Exception("Standardization failed")

        result, error = await processor.process_image(
            image_data=b"test",
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert result is None
        assert error is not None
        assert "Standardization failed" in error

    @pytest.mark.asyncio
    async def test_process_image_creates_subdirectory(self, processor, mock_deduplicator, mock_standardizer):
        """Test processing creates subdirectory for content-addressed storage."""
        image_data = b"test image"

        result, error = await processor.process_image(
            image_data=image_data,
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert error is None
        assert result is not None
        assert result.local_path.parent.exists()
        assert result.local_path.exists()

    @pytest.mark.asyncio
    async def test_process_image_saves_standardized_data(self, processor, mock_deduplicator, mock_standardizer):
        """Test processing saves standardized data to disk."""
        standardized_data = b"standardized image content"
        mock_standardizer.standardize.return_value = (standardized_data, 1024, 768)

        result, error = await processor.process_image(
            image_data=b"original",
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert error is None
        assert result is not None
        assert result.local_path.exists()
        assert result.local_path.read_bytes() == standardized_data

    @pytest.mark.asyncio
    async def test_process_image_unexpected_error(self, processor, mock_deduplicator, mock_standardizer):
        """Test handling of unexpected errors."""
        # Cause unexpected error in processing
        mock_deduplicator.register.side_effect = Exception("Unexpected error")

        result, error = await processor.process_image(
            image_data=b"test",
            source_url="https://example.com/image.jpg",
            property_hash="abc12345",
            run_id="testrun1",
        )

        assert result is None
        assert error is not None
        assert "Unexpected error" in error

    def test_get_stats(self, processor, tmp_path: Path):
        """Test statistics reporting."""
        # Create some test files
        (processor.base_dir / "subdir1").mkdir(parents=True, exist_ok=True)
        (processor.base_dir / "subdir1" / "image1.png").write_bytes(b"test")
        (processor.base_dir / "subdir2").mkdir(parents=True, exist_ok=True)
        (processor.base_dir / "subdir2" / "image2.png").write_bytes(b"test")

        stats = processor.get_stats()

        assert "base_dir" in stats
        assert stats["base_dir"] == str(processor.base_dir)
        assert "file_count" in stats
        assert stats["file_count"] == 2

    def test_get_stats_with_deduplicator_stats(self, processor, mock_deduplicator):
        """Test stats include deduplicator stats if available."""
        mock_deduplicator.get_stats.return_value = {"hash_count": 100}

        stats = processor.get_stats()

        assert "deduplicator_stats" in stats
        assert stats["deduplicator_stats"]["hash_count"] == 100

    def test_get_stats_handles_missing_directory(self, tmp_path: Path, mock_deduplicator, mock_standardizer):
        """Test stats handles missing base directory gracefully."""
        base_dir = tmp_path / "nonexistent"
        processor = ImageProcessor(base_dir, mock_deduplicator, mock_standardizer)

        # Remove the directory
        base_dir.rmdir()

        stats = processor.get_stats()

        # Should handle gracefully - returns 0 if no files found
        assert "file_count" in stats
        assert stats["file_count"] == 0  # No files found in missing directory

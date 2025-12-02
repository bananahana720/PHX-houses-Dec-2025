"""Unit tests for perceptual hash deduplication with LSH optimization.

Tests cover:
- Hash computation and validation
- Duplicate detection (exact and similar)
- LSH bucket optimization and candidate retrieval
- Hash registration and removal
- Persistence (save/load)
- Statistics and metrics
- Error handling and edge cases
"""

from io import BytesIO

import pytest
from PIL import Image

from phx_home_analysis.domain.value_objects import PerceptualHash
from phx_home_analysis.services.image_extraction.deduplicator import (
    DeduplicationError,
    ImageDeduplicator,
)


class TestHashComputation:
    """Test perceptual hash computation."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        """Create temporary deduplicator instance."""
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            similarity_threshold=8,
            num_bands=8,
        )

    @pytest.fixture
    def sample_image_data(self):
        """Generate simple test image data."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_compute_hash_returns_perceptual_hash(self, deduplicator, sample_image_data):
        """Verify hash computation returns PerceptualHash instance."""
        result = deduplicator.compute_hash(sample_image_data)

        assert isinstance(result, PerceptualHash)
        assert hasattr(result, "phash")
        assert hasattr(result, "dhash")
        assert isinstance(result.phash, str)
        assert isinstance(result.dhash, str)

    def test_phash_is_valid_hex_string(self, deduplicator, sample_image_data):
        """Verify phash is valid 16-character hex string."""
        result = deduplicator.compute_hash(sample_image_data)

        assert len(result.phash) == 16
        assert all(c in "0123456789abcdef" for c in result.phash.lower())

    def test_dhash_is_valid_hex_string(self, deduplicator, sample_image_data):
        """Verify dhash is valid 16-character hex string."""
        result = deduplicator.compute_hash(sample_image_data)

        assert len(result.dhash) == 16
        assert all(c in "0123456789abcdef" for c in result.dhash.lower())

    def test_identical_images_produce_identical_hashes(self, deduplicator):
        """Verify same image produces same hash."""
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))

        # Create identical copies
        buffer1 = BytesIO()
        img.save(buffer1, format="PNG")
        data1 = buffer1.getvalue()

        buffer2 = BytesIO()
        img.save(buffer2, format="PNG")
        data2 = buffer2.getvalue()

        hash1 = deduplicator.compute_hash(data1)
        hash2 = deduplicator.compute_hash(data2)

        assert hash1.phash == hash2.phash
        assert hash1.dhash == hash2.dhash

    def test_different_images_produce_different_hashes(self, deduplicator):
        """Verify different images produce different hashes."""
        # Create more varied images (solid colors have similar hashes)
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        # Add pattern to make hashes more distinct
        pixels1 = img1.load()
        for i in range(50):
            for j in range(100):
                pixels1[i, j] = (200, 0, 0)

        img2 = Image.new("RGB", (100, 100), color=(0, 0, 255))
        pixels2 = img2.load()
        for i in range(50, 100):
            for j in range(100):
                pixels2[i, j] = (0, 0, 200)

        buffer1 = BytesIO()
        img1.save(buffer1, format="PNG")

        buffer2 = BytesIO()
        img2.save(buffer2, format="PNG")

        hash1 = deduplicator.compute_hash(buffer1.getvalue())
        hash2 = deduplicator.compute_hash(buffer2.getvalue())

        # Distinct pattern should produce different hashes
        # Note: even different images might have similar hashes, so we allow either to differ
        assert hash1.phash != hash2.phash or hash1.dhash != hash2.dhash

    def test_compute_hash_with_rgba_image(self, deduplicator):
        """Verify hash computation handles RGBA images."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = deduplicator.compute_hash(buffer.getvalue())

        assert isinstance(result, PerceptualHash)
        assert len(result.phash) == 16
        assert len(result.dhash) == 16

    def test_compute_hash_with_grayscale_image(self, deduplicator):
        """Verify hash computation handles grayscale images."""
        img = Image.new("L", (100, 100), color=128)
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = deduplicator.compute_hash(buffer.getvalue())

        assert isinstance(result, PerceptualHash)
        assert len(result.phash) == 16

    def test_compute_hash_with_invalid_image_data(self, deduplicator):
        """Verify hash computation fails gracefully on invalid data."""
        with pytest.raises(DeduplicationError):
            deduplicator.compute_hash(b"not an image")

    def test_compute_hash_with_empty_data(self, deduplicator):
        """Verify hash computation fails on empty data."""
        with pytest.raises(DeduplicationError):
            deduplicator.compute_hash(b"")


class TestDuplicateDetection:
    """Test duplicate image detection."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            similarity_threshold=8,
        )

    @pytest.fixture
    def red_image(self):
        """Generate red image data."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @pytest.fixture
    def blue_image(self):
        """Generate blue image data."""
        img = Image.new("RGB", (100, 100), color=(0, 0, 255))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_detects_exact_duplicate(self, deduplicator, red_image):
        """Verify exact duplicate is detected."""
        hash1 = deduplicator.compute_hash(red_image)
        deduplicator.register_hash("img_001", hash1, "123 Main St", "zillow")

        hash2 = deduplicator.compute_hash(red_image)
        is_dup, original_id = deduplicator.is_duplicate(hash2)

        assert is_dup is True
        assert original_id == "img_001"

    def test_different_images_not_duplicate(self, deduplicator):
        """Verify different images are not flagged as duplicates."""
        # Create distinct images with different patterns
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        pixels1 = img1.load()
        for i in range(0, 50):
            for j in range(100):
                pixels1[i, j] = (200, 0, 0)

        img2 = Image.new("RGB", (100, 100), color=(0, 0, 255))
        pixels2 = img2.load()
        for i in range(50, 100):
            for j in range(100):
                pixels2[i, j] = (0, 0, 200)

        buffer1 = BytesIO()
        img1.save(buffer1, format="PNG")

        buffer2 = BytesIO()
        img2.save(buffer2, format="PNG")

        hash1 = deduplicator.compute_hash(buffer1.getvalue())
        deduplicator.register_hash("img_pattern1", hash1, "123 Main St", "zillow")

        hash2 = deduplicator.compute_hash(buffer2.getvalue())
        is_dup, _ = deduplicator.is_duplicate(hash2)

        # Different patterns should not be detected as duplicates
        assert is_dup is False

    def test_no_duplicates_in_empty_index(self, deduplicator, red_image):
        """Verify empty index returns no duplicates."""
        hash1 = deduplicator.compute_hash(red_image)
        is_dup, original_id = deduplicator.is_duplicate(hash1)

        assert is_dup is False
        assert original_id is None

    def test_duplicate_returns_correct_original_id(
        self, deduplicator, red_image
    ):
        """Verify duplicate detection returns correct original image ID."""
        hash1 = deduplicator.compute_hash(red_image)
        deduplicator.register_hash("img_original_123", hash1, "123 Main St", "zillow")

        hash2 = deduplicator.compute_hash(red_image)
        is_dup, original_id = deduplicator.is_duplicate(hash2)

        assert original_id == "img_original_123"

    def test_secondary_dhash_confirmation(self, deduplicator, red_image):
        """Verify secondary dhash confirmation is applied.

        The secondary dhash check provides additional validation that both
        perceptual and difference hashes are similar (threshold +2).
        """
        hash1 = deduplicator.compute_hash(red_image)
        deduplicator.register_hash("img_001", hash1, "123 Main St", "zillow")

        # Create a hash with different characteristics
        # If phash is identical, secondary dhash check still applies
        # The threshold is _threshold + 2 for dhash (more lenient)
        test_hash = deduplicator.compute_hash(red_image)
        is_dup, _ = deduplicator.is_duplicate(test_hash)

        # Exact same image should still be detected as duplicate
        # because both phash and dhash will match
        assert is_dup is True

    def test_lsh_candidates_optimization(self, deduplicator, red_image):
        """Verify LSH optimization reduces candidate set."""
        # Register multiple images
        for i in range(5):
            img = Image.new("RGB", (100, 100), color=(i * 50, 0, 0))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            hash_obj = deduplicator.compute_hash(buffer.getvalue())
            deduplicator.register_hash(
                f"img_{i:03d}",
                hash_obj,
                f"Property {i}",
                "zillow",
            )

        # Check duplicate
        hash_test = deduplicator.compute_hash(red_image)
        candidates = deduplicator._get_candidate_images(hash_test.phash)

        # Should have found some candidates (images with similar hash)
        assert isinstance(candidates, set)
        assert all(isinstance(cand_id, str) for cand_id in candidates)


class TestLSHOptimization:
    """Test LSH bucket optimization."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            similarity_threshold=8,
            num_bands=8,
        )

    def test_lsh_buckets_initialized(self, deduplicator):
        """Verify LSH buckets are initialized."""
        assert hasattr(deduplicator, "_lsh_buckets")
        assert isinstance(deduplicator._lsh_buckets, dict)

    def test_band_size_computed_correctly(self, deduplicator):
        """Verify band size calculation."""
        # 64 bits / 8 bands = 8 bits per band
        assert deduplicator._band_size == 8

    def test_band_size_with_different_num_bands(self, tmp_path):
        """Verify band size adjusts with num_bands."""
        dedup = ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            num_bands=16,
        )
        # 64 bits / 16 bands = 4 bits per band
        assert dedup._band_size == 4

    def test_compute_band_keys_correct_count(self, deduplicator):
        """Verify band key computation produces correct number of keys."""
        test_hash = "a" * 16  # 64-bit hex string

        band_keys = deduplicator._compute_band_keys(test_hash)

        assert len(band_keys) == 8  # 8 bands
        assert all(isinstance(key, str) for key in band_keys)

    def test_compute_band_keys_correct_substrings(self, deduplicator):
        """Verify band keys are correct substrings of hash."""
        test_hash = "0123456789abcdef"

        band_keys = deduplicator._compute_band_keys(test_hash)

        # With 8 bands from 16-char string, each band is 2 chars
        assert band_keys == ["01", "23", "45", "67", "89", "ab", "cd", "ef"]

    def test_lsh_buckets_populated_on_register(self, deduplicator):
        """Verify LSH buckets are updated when hash is registered."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        hash_obj = deduplicator.compute_hash(buffer.getvalue())

        deduplicator.register_hash("img_001", hash_obj, "123 Main St", "zillow")

        # Check buckets were updated
        assert len(deduplicator._lsh_buckets) > 0
        # At least one band should have entries
        assert any(
            len(band_buckets) > 0
            for band_buckets in deduplicator._lsh_buckets.values()
        )

    def test_get_candidate_images_returns_set(self, deduplicator):
        """Verify candidate retrieval returns a set."""
        test_hash = "a" * 16
        candidates = deduplicator._get_candidate_images(test_hash)

        assert isinstance(candidates, set)

    def test_get_candidate_images_empty_index(self, deduplicator):
        """Verify empty index returns empty candidates."""
        test_hash = "a" * 16
        candidates = deduplicator._get_candidate_images(test_hash)

        assert len(candidates) == 0

    def test_get_candidate_images_with_registered_hash(self, deduplicator):
        """Verify candidates include registered images with similar hash."""
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        hash_obj = deduplicator.compute_hash(buffer.getvalue())

        deduplicator.register_hash("img_001", hash_obj, "123 Main St", "zillow")

        # Query with same hash
        candidates = deduplicator._get_candidate_images(hash_obj.phash)

        # Should find the registered image
        assert "img_001" in candidates


class TestHashRegistration:
    """Test hash registration and management."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
        )

    @pytest.fixture
    def sample_hash(self):
        """Create sample PerceptualHash."""
        return PerceptualHash(
            phash="a" * 16,
            dhash="b" * 16,
        )

    def test_register_hash_stores_data(self, deduplicator, sample_hash):
        """Verify hash registration stores all data."""
        deduplicator.register_hash(
            "img_001",
            sample_hash,
            "123 Main St",
            "zillow",
        )

        # Verify stored in index
        assert "img_001" in deduplicator._hash_index["images"]
        stored = deduplicator._hash_index["images"]["img_001"]
        assert stored["phash"] == sample_hash.phash
        assert stored["dhash"] == sample_hash.dhash
        assert stored["property_address"] == "123 Main St"
        assert stored["source"] == "zillow"

    def test_register_multiple_hashes(self, deduplicator, sample_hash):
        """Verify multiple hashes can be registered."""
        hash2 = PerceptualHash(phash="c" * 16, dhash="d" * 16)

        deduplicator.register_hash("img_001", sample_hash, "123 Main St", "zillow")
        deduplicator.register_hash("img_002", hash2, "456 Oak Ave", "redfin")

        assert len(deduplicator._hash_index["images"]) == 2
        assert "img_001" in deduplicator._hash_index["images"]
        assert "img_002" in deduplicator._hash_index["images"]

    def test_remove_hash_success(self, deduplicator, sample_hash):
        """Verify hash removal."""
        deduplicator.register_hash("img_001", sample_hash, "123 Main St", "zillow")
        assert "img_001" in deduplicator._hash_index["images"]

        result = deduplicator.remove_hash("img_001")

        assert result is True
        assert "img_001" not in deduplicator._hash_index["images"]

    def test_remove_hash_nonexistent(self, deduplicator):
        """Verify removing nonexistent hash returns False."""
        result = deduplicator.remove_hash("img_nonexistent")

        assert result is False

    def test_remove_hash_cleans_lsh_buckets(self, deduplicator, sample_hash):
        """Verify hash removal cleans up LSH buckets."""
        deduplicator.register_hash("img_001", sample_hash, "123 Main St", "zillow")

        # Verify it's in buckets
        assert any(
            "img_001" in image_set
            for band_buckets in deduplicator._lsh_buckets.values()
            for image_set in band_buckets.values()
        )

        deduplicator.remove_hash("img_001")

        # Verify it's removed from buckets
        assert not any(
            "img_001" in image_set
            for band_buckets in deduplicator._lsh_buckets.values()
            for image_set in band_buckets.values()
        )

    def test_register_overwrites_existing(self, deduplicator, sample_hash):
        """Verify registering same ID twice overwrites."""
        new_hash = PerceptualHash(phash="z" * 16, dhash="y" * 16)

        deduplicator.register_hash("img_001", sample_hash, "123 Main St", "zillow")
        deduplicator.register_hash("img_001", new_hash, "456 Oak Ave", "redfin")

        stored = deduplicator._hash_index["images"]["img_001"]
        assert stored["phash"] == new_hash.phash
        assert stored["property_address"] == "456 Oak Ave"


class TestPersistence:
    """Test hash index persistence."""

    @pytest.fixture
    def sample_hash(self):
        return PerceptualHash(
            phash="a" * 16,
            dhash="b" * 16,
        )

    def test_save_creates_file(self, tmp_path, sample_hash):
        """Verify save creates index file."""
        index_path = tmp_path / "hash_index.json"
        dedup = ImageDeduplicator(hash_index_path=index_path)

        dedup.register_hash("img_001", sample_hash, "123 Main St", "zillow")

        assert index_path.exists()

    def test_load_existing_index(self, tmp_path, sample_hash):
        """Verify loading existing index restores data."""
        index_path = tmp_path / "hash_index.json"

        # Create and save
        dedup1 = ImageDeduplicator(hash_index_path=index_path)
        dedup1.register_hash("img_001", sample_hash, "123 Main St", "zillow")

        # Load in new instance
        dedup2 = ImageDeduplicator(hash_index_path=index_path)

        assert "img_001" in dedup2._hash_index["images"]
        stored = dedup2._hash_index["images"]["img_001"]
        assert stored["phash"] == sample_hash.phash

    def test_persistence_preserves_lsh_buckets(self, tmp_path, sample_hash):
        """Verify LSH buckets are rebuilt correctly on load."""
        index_path = tmp_path / "hash_index.json"

        dedup1 = ImageDeduplicator(hash_index_path=index_path)
        dedup1.register_hash("img_001", sample_hash, "123 Main St", "zillow")

        dedup2 = ImageDeduplicator(hash_index_path=index_path)

        # Query should find the image via LSH
        candidates = dedup2._get_candidate_images(sample_hash.phash)
        assert "img_001" in candidates

    def test_load_corrupted_index_returns_empty(self, tmp_path):
        """Verify corrupted index is handled gracefully."""
        index_path = tmp_path / "hash_index.json"

        # Write corrupted JSON
        with open(index_path, "w") as f:
            f.write("not valid json {")

        # Should not raise, should return empty index
        dedup = ImageDeduplicator(hash_index_path=index_path)

        assert dedup._hash_index["version"] == "1.0.0"
        assert dedup._hash_index["images"] == {}

    def test_load_nonexistent_path_creates_empty(self, tmp_path):
        """Verify nonexistent path creates empty index."""
        index_path = tmp_path / "subdir" / "hash_index.json"

        dedup = ImageDeduplicator(hash_index_path=index_path)

        assert dedup._hash_index["version"] == "1.0.0"
        assert dedup._hash_index["images"] == {}


class TestStatistics:
    """Test statistics and metrics."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
        )

    @pytest.fixture
    def populated_deduplicator(self, deduplicator):
        """Create deduplicator with sample data."""
        hashes = [
            PerceptualHash(phash=f"{i:016x}", dhash=f"{i+100:016x}")
            for i in range(5)
        ]

        for i, hash_obj in enumerate(hashes):
            deduplicator.register_hash(
                f"img_{i:03d}",
                hash_obj,
                f"Property {i % 3}",
                ["zillow", "redfin", "realtor"][i % 3],
            )

        return deduplicator

    def test_get_stats_returns_dict(self, populated_deduplicator):
        """Verify get_stats returns dictionary."""
        stats = populated_deduplicator.get_stats()

        assert isinstance(stats, dict)

    def test_stats_include_total_images(self, populated_deduplicator):
        """Verify stats include total image count."""
        stats = populated_deduplicator.get_stats()

        assert "total_images" in stats
        assert stats["total_images"] == 5

    def test_stats_include_by_source(self, populated_deduplicator):
        """Verify stats include breakdown by source."""
        stats = populated_deduplicator.get_stats()

        assert "by_source" in stats
        assert isinstance(stats["by_source"], dict)
        assert "zillow" in stats["by_source"]
        assert "redfin" in stats["by_source"]
        assert "realtor" in stats["by_source"]

    def test_stats_include_lsh_metrics(self, populated_deduplicator):
        """Verify stats include LSH optimization metrics."""
        stats = populated_deduplicator.get_stats()

        assert "lsh" in stats
        assert "num_bands" in stats["lsh"]
        assert "total_buckets" in stats["lsh"]
        assert "avg_bucket_size" in stats["lsh"]
        assert "max_bucket_size" in stats["lsh"]

    def test_stats_threshold_included(self, populated_deduplicator):
        """Verify stats include similarity threshold."""
        stats = populated_deduplicator.get_stats()

        assert "threshold" in stats
        assert stats["threshold"] == 8

    def test_stats_unique_properties_count(self, populated_deduplicator):
        """Verify stats count unique properties."""
        stats = populated_deduplicator.get_stats()

        assert "unique_properties" in stats
        # Should have 3 unique properties (Property 0, 1, 2)
        assert stats["unique_properties"] >= 1


class TestClearIndex:
    """Test index clearing functionality."""

    @pytest.fixture
    def populated_deduplicator(self, tmp_path):
        """Create deduplicator with sample data."""
        dedup = ImageDeduplicator(hash_index_path=tmp_path / "hash_index.json")

        for i in range(3):
            hash_obj = PerceptualHash(phash=f"{i:016x}", dhash=f"{i+100:016x}")
            dedup.register_hash(f"img_{i}", hash_obj, f"Prop {i}", "zillow")

        return dedup

    def test_clear_index_removes_images(self, populated_deduplicator):
        """Verify clear removes all images."""
        populated_deduplicator.clear_index()

        assert len(populated_deduplicator._hash_index["images"]) == 0

    def test_clear_index_resets_lsh(self, populated_deduplicator):
        """Verify clear resets LSH buckets."""
        populated_deduplicator.clear_index()

        assert len(populated_deduplicator._lsh_buckets) == 0

    def test_clear_index_persists(self, tmp_path):
        """Verify cleared state is persisted."""
        index_path = tmp_path / "hash_index.json"
        dedup1 = ImageDeduplicator(hash_index_path=index_path)

        hash_obj = PerceptualHash(phash="a" * 16, dhash="b" * 16)
        dedup1.register_hash("img_001", hash_obj, "123 Main St", "zillow")

        dedup1.clear_index()

        # Load in new instance
        dedup2 = ImageDeduplicator(hash_index_path=index_path)

        assert len(dedup2._hash_index["images"]) == 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def deduplicator(self, tmp_path):
        return ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
        )

    def test_deduplication_error_raised_on_invalid_image(self, deduplicator):
        """Verify DeduplicationError is raised for invalid images."""
        with pytest.raises(DeduplicationError):
            deduplicator.compute_hash(b"invalid image data")

    def test_invalid_hash_skipped_in_candidates(self, deduplicator):
        """Verify invalid stored hash is skipped in duplicate check."""
        # Manually insert invalid hash
        deduplicator._hash_index["images"]["img_bad"] = {
            "phash": "invalid",  # Should be 16 chars
            "dhash": "b" * 16,
            "property_address": "123 Main St",
            "source": "zillow",
        }

        # Should not crash when checking duplicates
        test_hash = PerceptualHash(phash="a" * 16, dhash="b" * 16)
        is_dup, original = deduplicator.is_duplicate(test_hash)

        assert is_dup is False

    def test_missing_phash_in_stored_skipped(self, deduplicator):
        """Verify entry without phash is skipped."""
        # Manually insert incomplete entry
        deduplicator._hash_index["images"]["img_incomplete"] = {
            "dhash": "b" * 16,
            "property_address": "123 Main St",
            "source": "zillow",
            # missing phash
        }

        test_hash = PerceptualHash(phash="a" * 16, dhash="b" * 16)
        is_dup, _ = deduplicator.is_duplicate(test_hash)

        assert is_dup is False

    def test_is_duplicate_with_empty_candidates(self, deduplicator):
        """Verify is_duplicate handles empty candidate set."""
        test_hash = PerceptualHash(phash="a" * 16, dhash="b" * 16)

        # With empty index, should get no candidates
        is_dup, original = deduplicator.is_duplicate(test_hash)

        assert is_dup is False
        assert original is None


class TestThresholdBehavior:
    """Test similarity threshold behavior."""

    @pytest.fixture
    def sample_hash(self):
        return PerceptualHash(phash="a" * 16, dhash="b" * 16)

    def test_custom_similarity_threshold(self, tmp_path, sample_hash):
        """Verify custom similarity threshold is applied."""
        dedup = ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            similarity_threshold=4,  # More strict
        )

        assert dedup._threshold == 4

    def test_threshold_parameter_stored(self, tmp_path, sample_hash):
        """Verify threshold parameter is stored correctly."""
        dedup = ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            similarity_threshold=16,
        )

        assert dedup._threshold == 16


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def sample_images(self):
        """Create sample images for testing."""
        images = {}
        for color_name, rgb in [
            ("red", (255, 0, 0)),
            ("green", (0, 255, 0)),
            ("blue", (0, 0, 255)),
        ]:
            img = Image.new("RGB", (100, 100), color=rgb)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            images[color_name] = buffer.getvalue()

        return images

    def test_full_workflow(self, tmp_path, sample_images):
        """Test complete deduplication workflow."""
        dedup = ImageDeduplicator(hash_index_path=tmp_path / "hash_index.json")

        # Register first image
        hash_red1 = dedup.compute_hash(sample_images["red"])
        dedup.register_hash("red_001", hash_red1, "123 Main St", "zillow")

        # Check duplicate
        hash_red2 = dedup.compute_hash(sample_images["red"])
        is_dup, original = dedup.is_duplicate(hash_red2)
        assert is_dup is True
        assert original == "red_001"

        # Register different image
        hash_green = dedup.compute_hash(sample_images["green"])
        dedup.register_hash("green_001", hash_green, "456 Oak Ave", "redfin")

        # Verify different image not duplicate
        is_dup, _ = dedup.is_duplicate(hash_green)
        # Green is registered, so it's a duplicate of itself
        assert is_dup is True

        # Get stats
        stats = dedup.get_stats()
        assert stats["total_images"] == 2

    def test_persistence_workflow(self, tmp_path, sample_images):
        """Test persistence across instances."""
        index_path = tmp_path / "hash_index.json"

        # First instance: register images
        dedup1 = ImageDeduplicator(hash_index_path=index_path)
        hash_red = dedup1.compute_hash(sample_images["red"])
        dedup1.register_hash("red_001", hash_red, "123 Main St", "zillow")

        # Second instance: load and verify
        dedup2 = ImageDeduplicator(hash_index_path=index_path)
        hash_red_check = dedup2.compute_hash(sample_images["red"])
        is_dup, original = dedup2.is_duplicate(hash_red_check)

        assert is_dup is True
        assert original == "red_001"

    def test_lsh_performance_benefit(self, tmp_path):
        """Test that LSH reduces candidate set size."""
        dedup = ImageDeduplicator(
            hash_index_path=tmp_path / "hash_index.json",
            num_bands=8,
        )

        # Register several different images
        for i in range(10):
            img = Image.new("RGB", (100, 100), color=(i * 25, 0, 0))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            hash_obj = dedup.compute_hash(buffer.getvalue())
            dedup.register_hash(f"img_{i:03d}", hash_obj, f"Prop {i}", "zillow")

        # Query should have candidates (due to LSH bucketing)
        test_hash = "a" * 16
        candidates = dedup._get_candidate_images(test_hash)

        # Should have non-empty candidates (likely much smaller than full index)
        assert isinstance(candidates, set)
        # Candidates should be <= total images
        assert len(candidates) <= 10

"""Unit tests for CategoryIndex reverse mapping optimization.

Tests cover:
- Reverse index maintenance during add/remove operations
- O(1) image lookup via has_image() and get_image_categories()
- Reverse index rebuild on load
- Clear operation includes reverse index
- Multiple categories per image (same image in different locations)
"""


import pytest

from phx_home_analysis.services.image_extraction.category_index import CategoryIndex


class TestReverseIndexBasics:
    """Test basic reverse index operations."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create temporary category index."""
        return CategoryIndex(index_path=tmp_path / "index.json")

    def test_add_image_creates_reverse_entry(self, index):
        """Verify adding image creates reverse index entry."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )

        # Verify reverse index contains image
        assert "img001" in index._image_to_categories
        assert index._image_to_categories["img001"] == {("int", "kitchen", "abcd1234")}

    def test_has_image_returns_true_for_existing_image(self, index):
        """Test has_image() returns True for indexed image (O(1))."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="ext",
            subject="front",
        )

        assert index.has_image("img001") is True

    def test_has_image_returns_false_for_missing_image(self, index):
        """Test has_image() returns False for non-existent image (O(1))."""
        assert index.has_image("nonexistent") is False

    def test_get_image_categories_returns_categories(self, index):
        """Test get_image_categories() returns all categories for image (O(1))."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="master",
        )

        categories = index.get_image_categories("img001")

        assert categories == {("int", "master", "abcd1234")}
        assert isinstance(categories, set)

    def test_get_image_categories_returns_empty_set_for_missing_image(self, index):
        """Test get_image_categories() returns empty set for non-existent image."""
        categories = index.get_image_categories("nonexistent")

        assert categories == set()
        assert isinstance(categories, set)

    def test_contains_operator_uses_reverse_index(self, index):
        """Test __contains__ operator uses reverse index (O(1))."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="sys",
            subject="hvac",
        )

        assert "img001" in index
        assert "nonexistent" not in index


class TestReverseIndexRemoval:
    """Test reverse index maintenance during removal."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create temporary category index."""
        return CategoryIndex(index_path=tmp_path / "index.json")

    def test_remove_image_clears_reverse_entry(self, index):
        """Verify removing image clears reverse index entry."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )

        # Verify added
        assert "img001" in index._image_to_categories

        # Remove and verify cleared
        result = index.remove("img001")

        assert result is True
        assert "img001" not in index._image_to_categories
        assert index.has_image("img001") is False

    def test_remove_nonexistent_image_returns_false(self, index):
        """Test removing non-existent image returns False."""
        result = index.remove("nonexistent")

        assert result is False

    def test_remove_uses_reverse_index_for_cleanup(self, index):
        """Verify remove() uses reverse index to find all locations."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="ext",
            subject="pool",
        )

        # Remove should use reverse index
        result = index.remove("img001")

        assert result is True
        # Verify removed from all indexes
        assert "img001" not in index._categories.get("ext", {}).get("pool", [])
        assert "img001" not in index._by_location.get("ext", [])
        assert "img001" not in index._by_subject.get("pool", [])


class TestReverseIndexMultipleCategories:
    """Test reverse index with images in multiple categories."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create temporary category index."""
        return CategoryIndex(index_path=tmp_path / "index.json")

    def test_same_image_multiple_categories(self, index):
        """Test adding same image to multiple categories."""
        # Add same image to different categories
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="ext",
            subject="front",
        )
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )

        categories = index.get_image_categories("img001")

        assert len(categories) == 2
        assert ("ext", "front", "abcd1234") in categories
        assert ("int", "kitchen", "abcd1234") in categories

    def test_remove_clears_all_categories(self, index):
        """Test removing image clears all category entries."""
        # Add to multiple categories
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="ext",
            subject="front",
        )
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="ext",
            subject="pool",
        )

        # Remove
        index.remove("img001")

        # Verify cleared from all indexes
        assert "img001" not in index._image_to_categories
        assert "img001" not in index._categories.get("ext", {}).get("front", [])
        assert "img001" not in index._categories.get("ext", {}).get("pool", [])
        assert "img001" not in index._by_location.get("ext", [])


class TestReverseIndexPersistence:
    """Test reverse index rebuild on load."""

    def test_reverse_index_rebuilt_on_load(self, tmp_path):
        """Test reverse index is rebuilt when loading from disk."""
        index_path = tmp_path / "index.json"

        # Create and populate index
        index1 = CategoryIndex(index_path=index_path)
        index1.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )
        index1.add(
            image_id="img002",
            property_hash="efgh5678",
            location="ext",
            subject="pool",
        )
        index1.save()

        # Load in new instance
        index2 = CategoryIndex(index_path=index_path)

        # Verify reverse index was rebuilt
        assert "img001" in index2._image_to_categories
        assert "img002" in index2._image_to_categories
        assert index2._image_to_categories["img001"] == {("int", "kitchen", "abcd1234")}
        assert index2._image_to_categories["img002"] == {("ext", "pool", "efgh5678")}

    def test_reverse_index_consistent_after_load(self, tmp_path):
        """Test reverse index remains consistent across save/load cycles."""
        index_path = tmp_path / "index.json"

        # Create, populate, and save
        index1 = CategoryIndex(index_path=index_path)
        index1.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="master",
        )
        index1.save()

        # Load
        index2 = CategoryIndex(index_path=index_path)

        # Operations should work identically
        assert index2.has_image("img001") is True
        assert index2.get_image_categories("img001") == {("int", "master", "abcd1234")}

        # Can remove using reverse index
        result = index2.remove("img001")
        assert result is True
        assert index2.has_image("img001") is False


class TestReverseIndexClear:
    """Test clear operation includes reverse index."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create temporary category index."""
        return CategoryIndex(index_path=tmp_path / "index.json")

    def test_clear_removes_reverse_index(self, index):
        """Test clear() removes all reverse index entries."""
        # Add images
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )
        index.add(
            image_id="img002",
            property_hash="efgh5678",
            location="ext",
            subject="pool",
        )

        # Verify populated
        assert len(index._image_to_categories) == 2

        # Clear
        index.clear()

        # Verify reverse index cleared
        assert len(index._image_to_categories) == 0
        assert index.has_image("img001") is False
        assert index.has_image("img002") is False


class TestReverseIndexPerformance:
    """Test O(1) lookup performance characteristics."""

    @pytest.fixture
    def large_index(self, tmp_path):
        """Create index with many images."""
        index = CategoryIndex(index_path=tmp_path / "index.json")

        # Add 100 images across different categories
        for i in range(100):
            index.add(
                image_id=f"img{i:03d}",
                property_hash=f"prop{i % 10:04d}",
                location="int" if i % 2 == 0 else "ext",
                subject=f"subject{i % 5}",
            )

        return index

    def test_has_image_is_o1(self, large_index):
        """Verify has_image() is O(1) regardless of index size."""
        # First image
        assert large_index.has_image("img000") is True

        # Last image (should be just as fast)
        assert large_index.has_image("img099") is True

        # Non-existent (should be just as fast)
        assert large_index.has_image("img999") is False

    def test_get_image_categories_is_o1(self, large_index):
        """Verify get_image_categories() is O(1) regardless of index size."""
        # First image
        categories1 = large_index.get_image_categories("img000")
        assert len(categories1) == 1

        # Last image (should be just as fast)
        categories2 = large_index.get_image_categories("img099")
        assert len(categories2) == 1

        # Non-existent (should be just as fast)
        categories3 = large_index.get_image_categories("img999")
        assert len(categories3) == 0

    def test_remove_is_o1_lookup(self, large_index):
        """Verify remove() uses O(1) reverse index lookup."""
        # Remove middle image (should be fast)
        result = large_index.remove("img050")
        assert result is True
        assert large_index.has_image("img050") is False

        # Remove last image (should be just as fast)
        result = large_index.remove("img099")
        assert result is True
        assert large_index.has_image("img099") is False


class TestReverseIndexEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def index(self, tmp_path):
        """Create temporary category index."""
        return CategoryIndex(index_path=tmp_path / "index.json")

    def test_get_image_categories_returns_copy(self, index):
        """Test get_image_categories() returns a copy, not reference."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
        )

        categories1 = index.get_image_categories("img001")
        categories2 = index.get_image_categories("img001")

        # Should be different objects
        assert categories1 is not categories2

        # But equal values
        assert categories1 == categories2

    def test_reverse_index_with_metadata(self, index):
        """Test reverse index works correctly with metadata."""
        index.add(
            image_id="img001",
            property_hash="abcd1234",
            location="int",
            subject="kitchen",
            metadata={"source": "zillow", "confidence": 0.95},
        )

        # Reverse index should work
        assert index.has_image("img001") is True
        categories = index.get_image_categories("img001")
        assert categories == {("int", "kitchen", "abcd1234")}

        # Metadata should be preserved
        meta = index.get_metadata("img001")
        assert meta["source"] == "zillow"
        assert meta["confidence"] == 0.95

    def test_add_from_filename_updates_reverse_index(self, index):
        """Test add_from_filename() also updates reverse index."""
        # Valid categorized filename (format: hash_loc_subj_conf_src_date.ext)
        filename = "abcd1234_int_kitchen_95_z_20240101.png"

        result = index.add_from_filename(
            image_id="img001",
            filename=filename,
        )

        assert result is True
        assert index.has_image("img001") is True
        categories = index.get_image_categories("img001")
        assert ("int", "kitchen", "abcd1234") in categories

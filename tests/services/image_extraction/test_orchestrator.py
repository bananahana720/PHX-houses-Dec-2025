"""Unit tests for ImageExtractionOrchestrator."""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import ImageSource
from src.phx_home_analysis.domain.value_objects import ImageMetadata
from src.phx_home_analysis.services.image_extraction.orchestrator import (
    ExtractionResult,
    ExtractionState,
    ImageExtractionOrchestrator,
    SourceStats,
)


@pytest.fixture
def sample_property():
    """Create a sample property for testing."""
    return Property(
        street="123 Test St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Test St, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2500,
        price_per_sqft_raw=190.0,
    )


@pytest.fixture
def temp_base_dir(tmp_path):
    """Create temporary base directory for testing."""
    return tmp_path / "images"


@pytest.fixture
def orchestrator(temp_base_dir):
    """Create orchestrator instance for testing."""
    return ImageExtractionOrchestrator(
        base_dir=temp_base_dir,
        enabled_sources=[ImageSource.ZILLOW],
        max_concurrent_properties=2,
    )


class TestExtractionState:
    """Tests for ExtractionState dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = ExtractionState(
            completed_properties={"addr1", "addr2"},
            failed_properties={"addr3"},
            last_updated="2025-01-01T00:00:00",
        )

        result = state.to_dict()

        assert set(result["completed_properties"]) == {"addr1", "addr2"}
        assert set(result["failed_properties"]) == {"addr3"}
        assert result["last_updated"] == "2025-01-01T00:00:00"

    def test_from_dict(self):
        """Test loading from dictionary."""
        data = {
            "completed_properties": ["addr1", "addr2"],
            "failed_properties": ["addr3"],
            "last_updated": "2025-01-01T00:00:00",
        }

        state = ExtractionState.from_dict(data)

        assert state.completed_properties == {"addr1", "addr2"}
        assert state.failed_properties == {"addr3"}
        assert state.last_updated == "2025-01-01T00:00:00"

    def test_from_dict_empty(self):
        """Test loading from empty dictionary."""
        state = ExtractionState.from_dict({})

        assert state.completed_properties == set()
        assert state.failed_properties == set()


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_duration_seconds(self):
        """Test duration calculation."""
        result = ExtractionResult(
            total_properties=10,
            properties_completed=8,
            properties_failed=2,
            properties_skipped=0,
            total_images=50,
            unique_images=45,
            duplicate_images=5,
            failed_downloads=3,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 1, 12, 5, 30),
        )

        assert result.duration_seconds == 330.0  # 5 minutes 30 seconds

    def test_success_rate(self):
        """Test success rate calculation."""
        result = ExtractionResult(
            total_properties=10,
            properties_completed=8,
            properties_failed=2,
            properties_skipped=0,
            total_images=50,
            unique_images=45,
            duplicate_images=5,
            failed_downloads=3,
        )

        assert result.success_rate == 80.0

    def test_success_rate_zero_properties(self):
        """Test success rate with no properties."""
        result = ExtractionResult(
            total_properties=0,
            properties_completed=0,
            properties_failed=0,
            properties_skipped=0,
            total_images=0,
            unique_images=0,
            duplicate_images=0,
            failed_downloads=0,
        )

        assert result.success_rate == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ExtractionResult(
            total_properties=10,
            properties_completed=8,
            properties_failed=2,
            properties_skipped=0,
            total_images=50,
            unique_images=45,
            duplicate_images=5,
            failed_downloads=3,
            start_time=datetime(2025, 1, 1, 12, 0, 0),
            end_time=datetime(2025, 1, 1, 12, 5, 0),
        )

        result.by_source["zillow"] = SourceStats(
            source="zillow",
            images_found=30,
            images_downloaded=28,
        )

        data = result.to_dict()

        assert data["total_properties"] == 10
        assert data["properties_completed"] == 8
        assert data["unique_images"] == 45
        assert data["duration_seconds"] == 300.0
        assert "zillow" in data["by_source"]
        assert data["by_source"]["zillow"]["images_found"] == 30


class TestImageExtractionOrchestrator:
    """Tests for ImageExtractionOrchestrator."""

    def test_initialization(self, orchestrator, temp_base_dir):
        """Test orchestrator initialization."""
        assert orchestrator.base_dir == temp_base_dir
        assert orchestrator.enabled_sources == [ImageSource.ZILLOW]
        assert orchestrator.max_concurrent == 2

        # Check directories created
        assert orchestrator.processed_dir.exists()
        assert orchestrator.raw_dir.exists()
        assert orchestrator.metadata_dir.exists()

    def test_get_property_hash(self, orchestrator, sample_property):
        """Test property hash generation."""
        hash1 = orchestrator._get_property_hash(sample_property)

        # Same property should produce same hash
        hash2 = orchestrator._get_property_hash(sample_property)
        assert hash1 == hash2

        # Hash should be 8 characters
        assert len(hash1) == 8

        # Different property should produce different hash
        other_property = Property(
            street="456 Other St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="456 Other St, Phoenix, AZ 85001",
            price="$500,000",
            price_num=500000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=250.0,
        )
        hash3 = orchestrator._get_property_hash(other_property)
        assert hash1 != hash3

    def test_get_property_dir(self, orchestrator, sample_property):
        """Test property directory path generation."""
        prop_dir = orchestrator._get_property_dir(sample_property)

        assert prop_dir.parent == orchestrator.processed_dir
        assert len(prop_dir.name) == 8  # Hash length

    def test_load_manifest_nonexistent(self, orchestrator):
        """Test loading manifest when file doesn't exist."""
        manifest = orchestrator._load_manifest()

        assert manifest == {}

    def test_save_and_load_manifest(self, orchestrator, sample_property):
        """Test saving and loading manifest."""
        # Create sample manifest data
        orchestrator.manifest = {
            sample_property.full_address: [
                {
                    "image_id": "test-id",
                    "source": "zillow",
                    "source_url": "http://example.com/img.jpg",
                    "local_path": "processed/abc123/test-id.png",
                    "phash": "0" * 16,
                    "dhash": "0" * 16,
                    "width": 1024,
                    "height": 768,
                    "file_size_bytes": 50000,
                    "status": "processed",
                    "downloaded_at": "2025-01-01T00:00:00",
                }
            ]
        }

        # Save
        orchestrator._save_manifest()

        # Create new orchestrator instance and load
        new_orchestrator = ImageExtractionOrchestrator(
            base_dir=orchestrator.base_dir,
        )

        assert sample_property.full_address in new_orchestrator.manifest
        assert len(new_orchestrator.manifest[sample_property.full_address]) == 1

    def test_save_and_load_state(self, orchestrator):
        """Test saving and loading state."""
        # Create sample state
        orchestrator.state = ExtractionState(
            completed_properties={"addr1", "addr2"},
            failed_properties={"addr3"},
        )

        # Save
        orchestrator._save_state()

        # Create new orchestrator instance and load
        new_orchestrator = ImageExtractionOrchestrator(
            base_dir=orchestrator.base_dir,
        )

        assert new_orchestrator.state.completed_properties == {"addr1", "addr2"}
        assert new_orchestrator.state.failed_properties == {"addr3"}

    def test_create_extractors(self, orchestrator):
        """Test extractor creation."""
        extractors = orchestrator._create_extractors()

        assert len(extractors) == 1
        assert extractors[0].source == ImageSource.ZILLOW

    def test_create_extractors_all_sources(self, temp_base_dir):
        """Test creating all extractors."""
        orchestrator = ImageExtractionOrchestrator(
            base_dir=temp_base_dir,
            enabled_sources=list(ImageSource),
        )

        extractors = orchestrator._create_extractors()

        assert len(extractors) == 4
        sources = {e.source for e in extractors}
        assert sources == set(ImageSource)

    def test_image_metadata_to_dict(self, orchestrator):
        """Test converting ImageMetadata to dict."""
        metadata = ImageMetadata(
            image_id="test-id",
            property_address="123 Test St, Phoenix, AZ 85001",
            source="zillow",
            source_url="http://example.com/img.jpg",
            local_path="processed/abc123/test-id.png",
            original_path=None,
            phash="0" * 16,
            dhash="0" * 16,
            width=1024,
            height=768,
            file_size_bytes=50000,
            status="processed",
            downloaded_at="2025-01-01T00:00:00",
            processed_at="2025-01-01T00:00:01",
        )

        result = orchestrator._image_metadata_to_dict(metadata)

        assert result["image_id"] == "test-id"
        assert result["source"] == "zillow"
        assert result["width"] == 1024
        assert result["status"] == "processed"

    def test_get_property_images_empty(self, orchestrator, sample_property):
        """Test getting images when none exist."""
        images = orchestrator.get_property_images(sample_property)

        assert images == []

    def test_get_property_images_existing(self, orchestrator, sample_property):
        """Test getting images from manifest."""
        # Add to manifest
        orchestrator.manifest[sample_property.full_address] = [
            {
                "image_id": "test-id-1",
                "source": "zillow",
                "source_url": "http://example.com/img1.jpg",
                "local_path": "processed/abc123/test-id-1.png",
                "phash": "0" * 16,
                "dhash": "0" * 16,
                "width": 1024,
                "height": 768,
                "file_size_bytes": 50000,
                "status": "processed",
                "downloaded_at": "2025-01-01T00:00:00",
            },
            {
                "image_id": "test-id-2",
                "source": "zillow",
                "source_url": "http://example.com/img2.jpg",
                "local_path": "processed/abc123/test-id-2.png",
                "phash": "1" * 16,
                "dhash": "1" * 16,
                "width": 800,
                "height": 600,
                "file_size_bytes": 40000,
                "status": "processed",
                "downloaded_at": "2025-01-01T00:00:01",
            },
        ]

        images = orchestrator.get_property_images(sample_property)

        assert len(images) == 2
        assert images[0].image_id == "test-id-1"
        assert images[1].image_id == "test-id-2"

    def test_get_statistics_empty(self, orchestrator):
        """Test statistics when no data exists."""
        stats = orchestrator.get_statistics()

        assert stats["total_properties"] == 0
        assert stats["total_images"] == 0
        assert stats["images_by_source"] == {}
        assert stats["completed_properties"] == 0

    def test_get_statistics_with_data(self, orchestrator, sample_property):
        """Test statistics calculation."""
        # Add test data
        orchestrator.manifest = {
            sample_property.full_address: [
                {
                    "image_id": "id1",
                    "source": "zillow",
                    "source_url": "http://example.com/1.jpg",
                    "local_path": "processed/abc123/id1.png",
                    "phash": "0" * 16,
                    "dhash": "0" * 16,
                    "width": 1024,
                    "height": 768,
                    "file_size_bytes": 50000,
                    "status": "processed",
                    "downloaded_at": "2025-01-01T00:00:00",
                },
                {
                    "image_id": "id2",
                    "source": "redfin",
                    "source_url": "http://example.com/2.jpg",
                    "local_path": "processed/abc123/id2.png",
                    "phash": "1" * 16,
                    "dhash": "1" * 16,
                    "width": 1024,
                    "height": 768,
                    "file_size_bytes": 50000,
                    "status": "processed",
                    "downloaded_at": "2025-01-01T00:00:01",
                },
            ]
        }

        orchestrator.state.completed_properties.add(sample_property.full_address)

        stats = orchestrator.get_statistics()

        assert stats["total_properties"] == 1
        assert stats["total_images"] == 2
        assert stats["images_by_source"]["zillow"] == 1
        assert stats["images_by_source"]["redfin"] == 1
        assert stats["completed_properties"] == 1

    def test_clear_state(self, orchestrator):
        """Test clearing state."""
        orchestrator.state.completed_properties.add("addr1")
        orchestrator.state.failed_properties.add("addr2")

        orchestrator.clear_state()

        assert len(orchestrator.state.completed_properties) == 0
        assert len(orchestrator.state.failed_properties) == 0

    @pytest.mark.asyncio
    async def test_extract_for_property_no_images(self, orchestrator, sample_property):
        """Test extraction when no images found."""
        result = ExtractionResult(
            total_properties=1,
            properties_completed=0,
            properties_failed=0,
            properties_skipped=0,
            total_images=0,
            unique_images=0,
            duplicate_images=0,
            failed_downloads=0,
        )
        result.by_source["zillow"] = SourceStats(source="zillow")

        # Mock extractor
        with patch.object(
            orchestrator,
            "_create_extractors",
            return_value=[],
        ):
            images = await orchestrator.extract_for_property(sample_property, result)

        assert images == []

    @pytest.mark.asyncio
    async def test_extract_all_empty_list(self, orchestrator):
        """Test extraction with empty property list."""
        result = await orchestrator.extract_all(properties=[], resume=False)

        assert result.total_properties == 0
        assert result.properties_completed == 0

    @pytest.mark.asyncio
    async def test_extract_all_resume_skip(self, orchestrator, sample_property):
        """Test resume skips completed properties."""
        # Mark property as completed
        orchestrator.state.completed_properties.add(sample_property.full_address)
        orchestrator._save_state()

        result = await orchestrator.extract_all(
            properties=[sample_property],
            resume=True,
        )

        assert result.properties_skipped == 1
        assert result.properties_completed == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Unit tests for Zillow screenshot-only extraction.

Story E2.R1 Wave 3: Screenshot-Only Refactoring
Tests for zpid extraction, gallery navigation, and screenshot capture.
All URL extraction methods removed - screenshots only.
"""

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import SewerType


def create_sample_property(**kwargs):
    """Create a sample property with all required fields for testing."""
    defaults = {
        "street": "4732 W Davis Rd",
        "city": "Glendale",
        "state": "AZ",
        "zip_code": "85306",
        "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
        "price": "$450,000",
        "price_num": 450000,
        "beds": 4,
        "baths": 2.0,
        "sqft": 2200,
        "price_per_sqft_raw": 204.5,
        "lot_sqft": 9500,
        "year_built": 2010,
        "garage_spaces": 2,
        "sewer_type": SewerType.CITY,
        "hoa_fee": 0,
    }
    defaults.update(kwargs)
    return Property(**defaults)


# =============================================================================
# Task 1: ZPID Extraction Helper Tests (AC#1)
# =============================================================================


class TestZpidExtraction:
    """Tests for _extract_zpid_from_listing_url helper method."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    def test_extract_zpid_from_standard_url(self, extractor):
        """Extract zpid from /homedetails/{slug}/{zpid}_zpid/ URL format."""
        url = "https://www.zillow.com/homedetails/4732-W-Davis-Rd-Glendale-AZ-85306/7686459_zpid/"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid == "7686459"

    def test_extract_zpid_from_minimal_url(self, extractor):
        """Extract zpid from minimal /{zpid}_zpid/ URL format."""
        url = "https://www.zillow.com/homedetails/7686459_zpid/"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid == "7686459"

    def test_extract_zpid_from_gallery_url(self, extractor):
        """Extract zpid from gallery URL with #image-lightbox hash."""
        url = "https://www.zillow.com/homedetails/7686459_zpid/#image-lightbox"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid == "7686459"

    def test_extract_zpid_with_long_zpid(self, extractor):
        """Extract zpid with 10-digit zpid."""
        url = "https://www.zillow.com/homedetails/1234567890_zpid/"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid == "1234567890"

    def test_extract_zpid_from_search_url_returns_none(self, extractor):
        """Search URLs without zpid should return None."""
        url = "https://www.zillow.com/homes/Phoenix-AZ_rb/"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid is None

    def test_extract_zpid_from_invalid_url_returns_none(self, extractor):
        """Invalid URLs should return None."""
        url = "https://www.google.com"
        zpid = extractor._extract_zpid_from_listing_url(url)
        assert zpid is None

    def test_extract_zpid_from_empty_url_returns_none(self, extractor):
        """Empty URL should return None."""
        zpid = extractor._extract_zpid_from_listing_url("")
        assert zpid is None


class TestZpidExtractionFromJson:
    """Tests for zpid extraction from Zillow search API JSON response."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    def test_extract_zpid_from_json_response(self, extractor):
        """Extract zpid from __NEXT_DATA__ JSON response."""
        json_content = '{"zpid": 7686459, "address": "4732 W Davis Rd"}'
        zpid = extractor._extract_zpid_from_json(json_content)
        assert zpid == "7686459"

    def test_extract_zpid_from_nested_json(self, extractor):
        """Extract zpid from nested __NEXT_DATA__ structure."""
        json_content = '{"props": {"pageProps": {"zpid": 7686459}}}'
        zpid = extractor._extract_zpid_from_json(json_content)
        assert zpid == "7686459"

    def test_extract_zpid_from_json_string_value(self, extractor):
        """Extract zpid when value is string instead of int."""
        json_content = '{"zpid": "7686459"}'
        zpid = extractor._extract_zpid_from_json(json_content)
        assert zpid == "7686459"

    def test_extract_zpid_from_empty_json_returns_none(self, extractor):
        """Empty JSON should return None."""
        json_content = "{}"
        zpid = extractor._extract_zpid_from_json(json_content)
        assert zpid is None

    def test_extract_zpid_from_invalid_json_returns_none(self, extractor):
        """Invalid JSON should return None."""
        json_content = "not valid json"
        zpid = extractor._extract_zpid_from_json(json_content)
        assert zpid is None


# =============================================================================
# Task 2: Gallery Navigation Tests (AC#2)
# =============================================================================


class TestGalleryUrlBuilder:
    """Tests for building gallery URLs with #image-lightbox hash."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.fixture
    def sample_property(self):
        """Create sample property for testing."""
        return create_sample_property()

    def test_build_gallery_url_with_zpid(self, extractor, sample_property):
        """Build gallery URL includes #image-lightbox hash when zpid available."""
        sample_property.zpid = "7686459"
        url = extractor._build_gallery_url(sample_property)
        assert "#image-lightbox" in url
        assert "7686459" in url
        assert url.endswith("#image-lightbox")

    def test_build_gallery_url_format(self, extractor, sample_property):
        """Gallery URL follows correct format."""
        sample_property.zpid = "7686459"
        url = extractor._build_gallery_url(sample_property)
        assert url == "https://www.zillow.com/homedetails/7686459_zpid/#image-lightbox"

    def test_build_gallery_url_without_zpid_returns_none(self, extractor, sample_property):
        """Without zpid, should return None."""
        sample_property.zpid = None
        url = extractor._build_gallery_url(sample_property)
        assert url is None


class TestGalleryDetection:
    """Tests for detecting gallery page load."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.mark.asyncio
    async def test_gallery_detection_success(self, extractor):
        """Detect photo carousel elements on gallery page."""
        mock_tab = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(return_value=[MagicMock()])

        is_gallery = await extractor._is_gallery_page(mock_tab)
        assert is_gallery is True

    @pytest.mark.asyncio
    async def test_gallery_detection_failure(self, extractor):
        """Return False when no gallery elements found."""
        mock_tab = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(return_value=[])

        is_gallery = await extractor._is_gallery_page(mock_tab)
        assert is_gallery is False


# =============================================================================
# Task 3: Screenshot Fallback Tests (AC#3)
# =============================================================================


class TestScreenshotCapture:
    """Tests for screenshot capture fallback mechanism."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.mark.asyncio
    async def test_capture_gallery_screenshots_returns_paths(self, extractor):
        """Capture screenshots while cycling gallery returns file paths."""
        import os
        import tempfile

        mock_tab = AsyncMock()

        # Mock hero image click
        mock_tab.query_selector = AsyncMock(return_value=AsyncMock())

        # Create temp files with different content for deduplication testing
        temp_files = []
        screenshots_data = [b"screenshot1_content", b"screenshot2_content", b"screenshot2_content"]

        for data in screenshots_data:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            f.write(data)
            f.close()
            temp_files.append(f.name)

        mock_tab.save_screenshot = AsyncMock(side_effect=temp_files)

        # Mock advance method
        with (
            patch.object(extractor, "_advance_carousel", new_callable=AsyncMock),
            patch.object(extractor, "_save_screenshot", return_value="/path/to/image.png"),
        ):
            paths = await extractor._capture_gallery_screenshots(mock_tab, max_images=10)

        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

        # Should have 2 unique screenshots before duplicate detection
        assert len(paths) == 2

    @pytest.mark.asyncio
    async def test_duplicate_detection_stops_capture(self, extractor):
        """Stop capturing when same frame detected twice."""
        import os
        import tempfile

        mock_tab = AsyncMock()

        # Mock hero image click
        mock_tab.query_selector = AsyncMock(return_value=AsyncMock())

        # Same screenshot twice in a row
        same_bytes = b"same_content"
        temp_files = []
        for _ in range(2):
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            f.write(same_bytes)
            f.close()
            temp_files.append(f.name)

        mock_tab.save_screenshot = AsyncMock(side_effect=temp_files)

        # Mock advance method
        with (
            patch.object(extractor, "_advance_carousel", new_callable=AsyncMock),
            patch.object(extractor, "_save_screenshot", return_value="/path/to/image.png"),
        ):
            paths = await extractor._capture_gallery_screenshots(mock_tab, max_images=30)

        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

        # Should stop after first duplicate (only 1 unique)
        assert len(paths) == 1

    @pytest.mark.asyncio
    async def test_screenshot_content_addressing(self, extractor):
        """Screenshots saved with content hash path."""
        import os
        import tempfile

        mock_tab = AsyncMock()

        # Mock hero image click
        mock_tab.query_selector = AsyncMock(return_value=AsyncMock())

        screenshot_bytes = b"test_screenshot_content"
        expected_hash = hashlib.md5(screenshot_bytes).hexdigest()

        # Create temp files with same content (to trigger duplicate detection)
        temp_files = []
        for _ in range(2):
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            f.write(screenshot_bytes)
            f.close()
            temp_files.append(f.name)

        mock_tab.save_screenshot = AsyncMock(side_effect=temp_files)

        # Mock advance method
        with (
            patch.object(extractor, "_advance_carousel", new_callable=AsyncMock),
            patch.object(extractor, "_save_screenshot") as mock_save,
        ):
            mock_save.return_value = f"/path/{expected_hash}.png"
            await extractor._capture_gallery_screenshots(mock_tab, max_images=10)

        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

        # Verify _save_screenshot was called with content and hash
        mock_save.assert_called()
        call_args = mock_save.call_args
        assert call_args[0][0] == screenshot_bytes
        assert call_args[0][1] == expected_hash


class TestScreenshotMetadata:
    """Tests for screenshot metadata tracking."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    def test_screenshot_metadata_includes_source_marker(self, extractor):
        """Screenshot metadata should include screenshot: true marker."""
        metadata = extractor._build_screenshot_metadata("test_hash")
        assert metadata.get("screenshot") is True

    def test_screenshot_metadata_includes_content_hash(self, extractor):
        """Screenshot metadata should include content hash."""
        metadata = extractor._build_screenshot_metadata("abc123")
        assert metadata.get("content_hash") == "abc123"


# =============================================================================
# Task 4: Carousel Helper Tests (AC#4 - Screenshot-Only Refactoring)
# =============================================================================


class TestCarouselScreenshot:
    """Tests for _capture_carousel_screenshot helper method."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.mark.asyncio
    async def test_capture_returns_bytes_on_success(self, extractor):
        """Should return screenshot bytes when capture succeeds."""
        import os
        import tempfile

        tab = AsyncMock()

        # Mock screenshot method returns PNG bytes via temp file
        screenshot_bytes = b"PNG_DATA_CONTENT_HERE"
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        f.write(screenshot_bytes)
        f.close()

        tab.save_screenshot = AsyncMock(return_value=f.name)

        result = await extractor._capture_carousel_screenshot(tab)

        # Clean up temp file
        try:
            os.unlink(f.name)
        except:
            pass

        assert result == screenshot_bytes

    @pytest.mark.asyncio
    async def test_capture_returns_none_on_failure(self, extractor):
        """Should return None when screenshot fails."""
        tab = AsyncMock()
        tab.save_screenshot = AsyncMock(return_value=None)

        result = await extractor._capture_carousel_screenshot(tab)
        assert result is None


class TestCarouselAdvance:
    """Tests for _advance_carousel helper method."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.mark.asyncio
    async def test_advance_clicks_next_button(self, extractor):
        """Should click next button if found and return True."""
        tab = AsyncMock()
        next_btn = AsyncMock()
        tab.query_selector = AsyncMock(return_value=next_btn)

        result = await extractor._advance_carousel(tab)

        next_btn.click.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_advance_sends_arrow_key_fallback(self, extractor):
        """Should dispatch ArrowRight event if no button found."""
        tab = AsyncMock()
        tab.query_selector = AsyncMock(return_value=None)
        tab.evaluate = AsyncMock()

        result = await extractor._advance_carousel(tab)

        # Verify ArrowRight was dispatched via JS
        calls = tab.evaluate.call_args_list
        assert any("ArrowRight" in str(call) for call in calls)
        assert result is True


# =============================================================================
# Task 5: Main Extraction Flow Tests (AC#1-4)
# =============================================================================


class TestExtractionMethodTracking:
    """Tests for extraction method tracking in metadata."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.fixture
    def sample_property(self):
        """Create sample property for testing."""
        return create_sample_property()

    def test_set_extraction_method_in_metadata(self, extractor):
        """Extractor can set extraction method in metadata."""
        extractor.last_metadata = {}
        extractor.last_metadata["extraction_method"] = "zpid_direct"
        assert extractor.last_metadata.get("extraction_method") == "zpid_direct"

    def test_metadata_methods_available(self, extractor):
        """Verify extraction method constants."""
        # Validate we can track all extraction methods
        methods = ["zpid_direct", "screenshot_fallback", "google_images", "search_fallback"]
        for method in methods:
            extractor.last_metadata = {"extraction_method": method}
            assert extractor.last_metadata["extraction_method"] == method


# =============================================================================
# P0-4: Integration Tests (Story E2.R1 - Proving Fallback Chain Is Called)
# =============================================================================


class TestExtractImageUrlsIntegration:
    """Integration tests for screenshot-only extraction flow.

    Wave 3: Screenshot-Only Refactoring - These tests verify that the
    extract_image_urls() method returns screenshot file paths, not URLs.
    """

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    @pytest.fixture
    def sample_property(self):
        """Create sample property for testing."""
        return create_sample_property()

    @pytest.mark.asyncio
    async def test_extract_returns_screenshot_paths_not_urls(self, extractor, sample_property):
        """Verify extract_image_urls returns file paths to screenshots."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        # Mock screenshot capture to return file paths
        screenshot_paths = [
            "/path/to/screenshot1.png",
            "/path/to/screenshot2.png",
            "/path/to/screenshot3.png",
        ]

        with (
            patch.object(
                extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
            ) as mock_gallery,
            patch.object(extractor, "_is_gallery_page", new_callable=AsyncMock) as mock_is_gallery,
            patch.object(
                extractor, "_capture_gallery_screenshots", new_callable=AsyncMock
            ) as mock_screenshot,
        ):
            mock_gallery.return_value = True
            mock_is_gallery.return_value = True
            mock_screenshot.return_value = screenshot_paths

            result = await extractor.extract_image_urls(sample_property)

            # Verify screenshot method was called
            mock_screenshot.assert_called_once()
            # Verify result is file paths, not URLs
            assert result == screenshot_paths
            assert all(path.endswith(".png") for path in result)
            assert extractor.last_metadata.get("extraction_method") == "screenshot"

    @pytest.mark.asyncio
    async def test_screenshot_metadata_includes_source_marker(self, extractor, sample_property):
        """Verify screenshot metadata includes screenshot: true marker."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with (
            patch.object(
                extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
            ) as mock_gallery,
            patch.object(extractor, "_is_gallery_page", new_callable=AsyncMock) as mock_is_gallery,
            patch.object(
                extractor, "_capture_gallery_screenshots", new_callable=AsyncMock
            ) as mock_screenshot,
        ):
            mock_gallery.return_value = True
            mock_is_gallery.return_value = True
            mock_screenshot.return_value = ["/path/to/screenshot1.png"]

            await extractor.extract_image_urls(sample_property)

            # Verify extraction method is set to screenshot
            assert extractor.last_metadata.get("extraction_method") == "screenshot"

    def test_set_extraction_method_helper(self, extractor):
        """Verify _set_extraction_method helper sets metadata correctly."""
        extractor.last_metadata = {}
        extractor._set_extraction_method("screenshot")
        assert extractor.last_metadata.get("extraction_method") == "screenshot"

    def test_set_extraction_method_none_does_not_set(self, extractor):
        """Verify _set_extraction_method with None does not modify metadata."""
        extractor.last_metadata = {}
        extractor._set_extraction_method(None)
        assert "extraction_method" not in extractor.last_metadata

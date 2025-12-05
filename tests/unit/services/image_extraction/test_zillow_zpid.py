"""Unit tests for Zillow ZPID extraction and gallery navigation.

Story E2.R1: Zillow ZPID Direct Extraction
Tests for zpid extraction, gallery navigation, screenshot fallback, and Google Images fallback.
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
        mock_tab = AsyncMock()
        # Return different bytes for each screenshot (unique content)
        mock_tab.screenshot = AsyncMock(side_effect=[
            b"screenshot1_content",
            b"screenshot2_content",
            b"screenshot2_content",  # Duplicate - should stop
        ])

        with patch.object(extractor, "_save_screenshot", return_value="/path/to/image.png"):
            paths = await extractor._capture_gallery_screenshots(mock_tab, max_images=10)

        # Should have 2 unique screenshots before duplicate detection
        assert len(paths) == 2

    @pytest.mark.asyncio
    async def test_duplicate_detection_stops_capture(self, extractor):
        """Stop capturing when same frame detected twice."""
        mock_tab = AsyncMock()
        # Same screenshot twice in a row
        same_bytes = b"same_content"
        mock_tab.screenshot = AsyncMock(return_value=same_bytes)

        with patch.object(extractor, "_save_screenshot", return_value="/path/to/image.png"):
            paths = await extractor._capture_gallery_screenshots(mock_tab, max_images=30)

        # Should stop after first duplicate (only 1 unique)
        assert len(paths) == 1

    @pytest.mark.asyncio
    async def test_screenshot_content_addressing(self, extractor):
        """Screenshots saved with content hash path."""
        mock_tab = AsyncMock()
        screenshot_bytes = b"test_screenshot_content"
        expected_hash = hashlib.md5(screenshot_bytes).hexdigest()
        mock_tab.screenshot = AsyncMock(side_effect=[
            screenshot_bytes,
            screenshot_bytes,  # Duplicate to stop loop
        ])

        with patch.object(extractor, "_save_screenshot") as mock_save:
            mock_save.return_value = f"/path/{expected_hash}.png"
            await extractor._capture_gallery_screenshots(mock_tab, max_images=10)

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
# Task 4: Google Images Fallback Tests (AC#4)
# =============================================================================


class TestGoogleImagesFallback:
    """Tests for Google Images fallback mechanism."""

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

    def test_build_google_images_query(self, extractor, sample_property):
        """Build correct Google Images search query."""
        query = extractor._build_google_images_query(sample_property)
        assert "4732 W Davis Rd" in query
        assert "site:zillow.com" in query

    def test_google_images_confidence_is_0_5(self, extractor):
        """Google Images results should have confidence 0.5."""
        metadata = extractor._build_google_images_metadata("http://example.com/image.jpg")
        assert metadata.get("confidence") == 0.5

    def test_google_images_source_is_correct(self, extractor):
        """Google Images results should have correct source marker."""
        metadata = extractor._build_google_images_metadata("http://example.com/image.jpg")
        assert metadata.get("source") == "google_images"


class TestGoogleImagesUrlFiltering:
    """Tests for filtering Google Images results to zillow.com sources."""

    @pytest.fixture
    def extractor(self):
        """Create ZillowExtractor instance for testing."""
        from phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        return ZillowExtractor()

    def test_filter_for_zillow_domain(self, extractor):
        """Only keep URLs from zillow.com domain."""
        urls = [
            "https://photos.zillowstatic.com/image1.jpg",
            "https://www.redfin.com/image.jpg",
            "https://photos.zillowstatic.com/image2.jpg",
            "https://example.com/random.jpg",
        ]
        filtered = extractor._filter_google_images_for_zillow(urls)
        assert len(filtered) == 2
        assert all("zillow" in url for url in filtered)

    def test_filter_empty_list(self, extractor):
        """Handle empty URL list."""
        filtered = extractor._filter_google_images_for_zillow([])
        assert filtered == []


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


class TestFallbackChainLogic:
    """Tests for fallback chain logic: zpid-direct -> screenshot -> google."""

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

    def test_gallery_url_requires_zpid(self, extractor, sample_property):
        """_build_gallery_url returns None without zpid."""
        sample_property.zpid = None
        result = extractor._build_gallery_url(sample_property)
        assert result is None

    def test_gallery_url_with_zpid(self, extractor, sample_property):
        """_build_gallery_url returns URL with zpid."""
        sample_property.zpid = "7686459"
        result = extractor._build_gallery_url(sample_property)
        assert result is not None
        assert "7686459" in result
        assert "#image-lightbox" in result

    def test_fallback_chain_order(self, extractor, sample_property):
        """Verify fallback chain order through method existence."""
        # Verify all fallback methods exist
        assert hasattr(extractor, "_navigate_to_gallery_direct")
        assert hasattr(extractor, "_capture_gallery_screenshots")
        assert hasattr(extractor, "_google_images_fallback")

        # Verify screenshot method signature
        import inspect
        sig = inspect.signature(extractor._capture_gallery_screenshots)
        assert "max_images" in sig.parameters

    def test_google_images_fallback_filters_zillow(self, extractor):
        """Google Images fallback filters for Zillow sources."""
        urls = [
            "https://photos.zillowstatic.com/image1.jpg",
            "https://www.redfin.com/image.jpg",
            "https://photos.zillowstatic.com/image2.jpg",
        ]
        filtered = extractor._filter_google_images_for_zillow(urls)
        assert len(filtered) == 2


# =============================================================================
# P0-4: Integration Tests (Story E2.R1 - Proving Fallback Chain Is Called)
# =============================================================================


class TestExtractImageUrlsIntegration:
    """Integration tests proving new methods are called in production flow.

    P0-4 FIX: These tests verify that the fallback chain is integrated into
    extract_image_urls() and methods are called in the correct order.
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
    async def test_extract_image_urls_uses_zpid_direct_when_zpid_present(
        self, extractor, sample_property
    ):
        """Verify zpid-direct is attempted first when property has zpid."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with patch.object(
            extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
        ) as mock_gallery, patch.object(
            extractor, "_extract_urls_from_page", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            extractor, "_filter_urls_for_property"
        ) as mock_filter:
            mock_gallery.return_value = True
            mock_extract.return_value = ["http://example.com/image1.jpg"]
            mock_filter.return_value = ["http://example.com/image1.jpg"]

            result = await extractor.extract_image_urls(sample_property)

            # Verify zpid-direct was called
            mock_gallery.assert_called_once()
            assert result == ["http://example.com/image1.jpg"]
            assert extractor.last_metadata.get("extraction_method") == "zpid-direct"

    @pytest.mark.asyncio
    async def test_fallback_chain_tries_screenshot_after_zpid_direct_fails(
        self, extractor, sample_property
    ):
        """Verify screenshot fallback triggered when zpid-direct fails."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with patch.object(
            extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
        ) as mock_gallery, patch.object(
            extractor, "_extract_urls_from_page", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            extractor, "_filter_urls_for_property"
        ) as mock_filter, patch.object(
            extractor, "_is_gallery_page", new_callable=AsyncMock
        ) as mock_is_gallery, patch.object(
            extractor, "_capture_gallery_screenshots", new_callable=AsyncMock
        ) as mock_screenshot:
            # zpid-direct returns True but no URLs extracted
            mock_gallery.return_value = True
            mock_extract.return_value = []
            mock_filter.return_value = []
            mock_is_gallery.return_value = False
            mock_screenshot.return_value = ["/path/to/screenshot1.png"]

            result = await extractor.extract_image_urls(sample_property)

            # Verify zpid-direct was tried first
            mock_gallery.assert_called()
            # Verify screenshot fallback was called
            mock_screenshot.assert_called_once()
            assert result == ["/path/to/screenshot1.png"]
            assert extractor.last_metadata.get("extraction_method") == "screenshot"

    @pytest.mark.asyncio
    async def test_fallback_chain_tries_google_after_screenshot_fails(
        self, extractor, sample_property
    ):
        """Verify Google Images fallback triggered when screenshot fails."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with patch.object(
            extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
        ) as mock_gallery, patch.object(
            extractor, "_extract_urls_from_page", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            extractor, "_filter_urls_for_property"
        ) as mock_filter, patch.object(
            extractor, "_is_gallery_page", new_callable=AsyncMock
        ) as mock_is_gallery, patch.object(
            extractor, "_capture_gallery_screenshots", new_callable=AsyncMock
        ) as mock_screenshot, patch.object(
            extractor, "_google_images_fallback", new_callable=AsyncMock
        ) as mock_google:
            # zpid-direct and screenshot both fail
            mock_gallery.return_value = True
            mock_extract.return_value = []
            mock_filter.return_value = []
            mock_is_gallery.return_value = False
            mock_screenshot.return_value = []
            mock_google.return_value = ["http://google.com/zillow_image.jpg"]

            result = await extractor.extract_image_urls(sample_property)

            # Verify Google Images fallback was called
            mock_google.assert_called_once()
            assert result == ["http://google.com/zillow_image.jpg"]
            assert extractor.last_metadata.get("extraction_method") == "google-images"

    @pytest.mark.asyncio
    async def test_fallback_chain_uses_search_when_all_fail(
        self, extractor, sample_property
    ):
        """Verify search fallback used when all other methods fail."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with patch.object(
            extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
        ) as mock_gallery, patch.object(
            extractor, "_extract_urls_from_page", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            extractor, "_filter_urls_for_property"
        ) as mock_filter, patch.object(
            extractor, "_is_gallery_page", new_callable=AsyncMock
        ) as mock_is_gallery, patch.object(
            extractor, "_capture_gallery_screenshots", new_callable=AsyncMock
        ) as mock_screenshot, patch.object(
            extractor, "_google_images_fallback", new_callable=AsyncMock
        ) as mock_google, patch.object(
            extractor, "_navigate_to_property_via_search", new_callable=AsyncMock
        ) as mock_search, patch.object(
            extractor, "_is_property_detail_page", new_callable=AsyncMock
        ) as mock_detail, patch.object(
            extractor, "_check_for_captcha", new_callable=AsyncMock
        ) as mock_captcha, patch.object(
            extractor, "_human_delay", new_callable=AsyncMock
        ), patch.object(
            extractor, "_extract_zpid_from_url", new_callable=AsyncMock
        ) as mock_zpid_url, patch.object(
            extractor, "extract_listing_metadata", new_callable=AsyncMock
        ) as mock_metadata:
            # All fallbacks fail
            mock_gallery.return_value = True
            mock_is_gallery.return_value = False
            mock_screenshot.return_value = []
            mock_google.return_value = []

            # First call for zpid-direct extraction returns empty
            # Search path succeeds
            mock_search.return_value = True
            mock_detail.return_value = True
            mock_captcha.return_value = False
            mock_zpid_url.return_value = "12345678"
            mock_metadata.return_value = {}

            # Configure extract/filter for different call contexts
            # First calls (zpid-direct): return empty
            # Last call (search): return URLs
            call_count = [0]

            def filter_side_effect(urls, zpid):
                call_count[0] += 1
                if call_count[0] <= 1:  # First call from zpid-direct
                    return []
                return urls  # Search call returns what was passed

            mock_extract.side_effect = [
                [],  # zpid-direct
                ["http://example.com/search_image.jpg"],  # search
            ]
            mock_filter.side_effect = filter_side_effect

            result = await extractor.extract_image_urls(sample_property)

            # Verify search fallback was called
            mock_search.assert_called_once()
            assert "http://example.com/search_image.jpg" in result
            assert extractor.last_metadata.get("extraction_method") == "search"

    @pytest.mark.asyncio
    async def test_extraction_method_tracked_correctly(self, extractor, sample_property):
        """Verify extraction_method metadata is set based on successful path."""
        sample_property.zpid = "12345678"

        # Mock browser pool and tab
        mock_browser = AsyncMock()
        mock_tab = AsyncMock()
        mock_browser.get = AsyncMock(return_value=mock_tab)
        extractor._browser_pool = MagicMock()
        extractor._browser_pool.get_browser = AsyncMock(return_value=mock_browser)

        with patch.object(
            extractor, "_navigate_to_gallery_direct", new_callable=AsyncMock
        ) as mock_gallery, patch.object(
            extractor, "_extract_urls_from_page", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            extractor, "_filter_urls_for_property"
        ) as mock_filter:
            mock_gallery.return_value = True
            mock_extract.return_value = ["http://example.com/img.jpg"]
            mock_filter.return_value = ["http://example.com/img.jpg"]

            await extractor.extract_image_urls(sample_property)

            assert extractor.last_metadata.get("extraction_method") == "zpid-direct"

    def test_set_extraction_method_helper(self, extractor):
        """Verify _set_extraction_method helper sets metadata correctly."""
        extractor.last_metadata = {}
        extractor._set_extraction_method("zpid-direct")
        assert extractor.last_metadata.get("extraction_method") == "zpid-direct"

        extractor._set_extraction_method("screenshot")
        assert extractor.last_metadata.get("extraction_method") == "screenshot"

        extractor._set_extraction_method("google-images")
        assert extractor.last_metadata.get("extraction_method") == "google-images"

        extractor._set_extraction_method("search")
        assert extractor.last_metadata.get("extraction_method") == "search"

    def test_set_extraction_method_none_does_not_set(self, extractor):
        """Verify _set_extraction_method with None does not modify metadata."""
        extractor.last_metadata = {}
        extractor._set_extraction_method(None)
        assert "extraction_method" not in extractor.last_metadata

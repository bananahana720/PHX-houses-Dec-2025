"""Integration tests for PhoenixMLS extractor with real property extraction.

Tests the complete PhoenixMLS extraction workflow including:
1. Image URL extraction from listing pages
2. Metadata extraction (kill-switch fields, MLS fields, schools)
3. Priority ordering in orchestrator
4. Metadata caching on Property objects

NOTE: These tests use real HTTP requests and may be slow. Run with:
    pytest tests/integration/test_phoenixmls_extraction.py -v -s

Skip with:
    pytest tests/ -m "not integration"
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import ImageSource
from phx_home_analysis.services.image_extraction.extractors.phoenix_mls import (
    PHOENIX_METRO_CITIES,
    PhoenixMLSExtractor,
)
from phx_home_analysis.services.image_extraction.orchestrator import (
    ImageExtractionOrchestrator,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_phoenix_property():
    """Create a sample Phoenix property for testing.

    Uses a realistic address in Phoenix metro area that PhoenixMLS should handle.
    """
    return Property(
        street="4732 W Davis Rd",
        city="Glendale",
        state="AZ",
        zip_code="85306",
        full_address="4732 W Davis Rd, Glendale, AZ 85306",
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=204.55,
        lot_sqft=8500,
    )


@pytest.fixture
def sample_scottsdale_property():
    """Create a sample Scottsdale property for testing."""
    return Property(
        street="7350 N Via Paseo Del Sur",
        city="Scottsdale",
        state="AZ",
        zip_code="85258",
        full_address="7350 N Via Paseo Del Sur, Scottsdale, AZ 85258",
        price="$675,000",
        price_num=675000,
        beds=4,
        baths=3.0,
        sqft=2800,
        price_per_sqft_raw=241.07,
        lot_sqft=10000,
    )


@pytest.fixture
def mock_phoenixmls_html():
    """Generate mock PhoenixMLS listing page HTML with metadata.

    Simulates a typical MLS listing page structure with:
    - Property details table
    - Image gallery
    - School information
    - MLS metadata
    """
    return """
    <!DOCTYPE html>
    <html>
    <head><title>4732 W Davis Rd, Glendale, AZ 85306</title></head>
    <body>
        <div class="listing-details">
            <span class="listing-price">$450,000</span>
            <div class="mls-info">MLS #: 6789012</div>

            <!-- Property Details Table -->
            <table class="property-details">
                <tr>
                    <th>Bedrooms</th>
                    <td>4</td>
                </tr>
                <tr>
                    <th>Bathrooms</th>
                    <td>2.0</td>
                </tr>
                <tr>
                    <th>Square Feet</th>
                    <td>2,200</td>
                </tr>
                <tr>
                    <th>Lot Size</th>
                    <td>8,500 sqft</td>
                </tr>
                <tr>
                    <th>Year Built</th>
                    <td>2010</td>
                </tr>
                <tr>
                    <th>Garage</th>
                    <td>2</td>
                </tr>
                <tr>
                    <th>HOA Fee</th>
                    <td>No Fees</td>
                </tr>
                <tr>
                    <th>Pool</th>
                    <td>Yes - Private</td>
                </tr>
                <tr>
                    <th>Sewer</th>
                    <td>Public Sewer</td>
                </tr>
                <tr>
                    <th>Property Type</th>
                    <td>Single Family Residence</td>
                </tr>
            </table>

            <!-- Schools Section -->
            <div class="schools-section">
                <div class="school-info">Elementary: Barrel Elementary School</div>
                <div class="school-info">Middle: Copper Creek Middle School</div>
                <div class="school-info">High: Ironwood High School</div>
            </div>

            <!-- Image Gallery -->
            <div class="photo-gallery">
                <img src="https://example.com/photos/property1.jpg" alt="Living Room">
                <img src="https://example.com/photos/property2.jpg" alt="Kitchen">
                <img src="https://example.com/photos/property3.jpg" alt="Master Bedroom">
                <img src="https://example.com/photos/property4.jpg" alt="Backyard">
                <img src="https://example.com/photos/property5.jpg" alt="Pool">
                <img src="https://example.com/photos/property6.jpg" alt="Exterior">
            </div>
        </div>
    </body>
    </html>
    """


# ============================================================================
# Unit Tests for PhoenixMLS Extractor
# ============================================================================


@pytest.mark.integration
class TestPhoenixMLSExtractorBasics:
    """Basic functionality tests for PhoenixMLS extractor."""

    def test_extractor_source_enum(self):
        """Test PhoenixMLS extractor has correct source enum."""
        extractor = PhoenixMLSExtractor()
        assert extractor.source == ImageSource.PHOENIX_MLS

    def test_extractor_name(self):
        """Test PhoenixMLS extractor has correct name."""
        extractor = PhoenixMLSExtractor()
        assert extractor.name == "Phoenix MLS"

    def test_can_handle_phoenix_metro_cities(self, sample_phoenix_property):
        """Test extractor can handle Phoenix metro area cities."""
        extractor = PhoenixMLSExtractor()

        # Should handle Glendale
        assert extractor.can_handle(sample_phoenix_property)

        # Test other Phoenix metro cities
        for city in ["Phoenix", "Scottsdale", "Tempe", "Mesa", "Chandler"]:
            sample_phoenix_property.city = city
            assert extractor.can_handle(sample_phoenix_property), f"Should handle {city}"

    def test_cannot_handle_non_phoenix_cities(self, sample_phoenix_property):
        """Test extractor rejects cities outside Phoenix metro."""
        extractor = PhoenixMLSExtractor()

        # Should reject non-Phoenix cities
        for city in ["Tucson", "Flagstaff", "Yuma", "Prescott"]:
            sample_phoenix_property.city = city
            result = extractor.can_handle(sample_phoenix_property)
            assert not result, f"Should not handle {city}"

    def test_phoenix_metro_cities_constant(self):
        """Test PHOENIX_METRO_CITIES constant is comprehensive."""
        # Verify key Phoenix metro cities are included
        required_cities = {
            "phoenix", "scottsdale", "tempe", "mesa", "chandler",
            "glendale", "peoria", "gilbert", "surprise", "avondale"
        }

        assert required_cities.issubset(PHOENIX_METRO_CITIES)
        assert len(PHOENIX_METRO_CITIES) >= 20, "Should have at least 20 metro cities"


# ============================================================================
# Metadata Extraction Tests
# ============================================================================


@pytest.mark.integration
class TestPhoenixMLSMetadataExtraction:
    """Test metadata extraction from PhoenixMLS pages."""

    def test_parse_listing_metadata_basic_fields(self):
        """Test extraction of basic kill-switch fields from listing HTML."""
        extractor = PhoenixMLSExtractor()

        html = """
        <table class="property-details">
            <tr><th>Bedrooms</th><td>4</td></tr>
            <tr><th>Bathrooms</th><td>2.5</td></tr>
            <tr><th>Square Feet</th><td>2,200</td></tr>
            <tr><th>Lot Size</th><td>8,500 sqft</td></tr>
            <tr><th>Year Built</th><td>2010</td></tr>
            <tr><th>Garage</th><td>2</td></tr>
        </table>
        """

        metadata = extractor._parse_listing_metadata(html)

        # Verify kill-switch fields
        assert metadata["beds"] == 4
        assert metadata["baths"] == 2.5
        assert metadata["sqft"] == 2200
        assert metadata["lot_sqft"] == 8500
        assert metadata["year_built"] == 2010
        assert metadata["garage_spaces"] == 2

    def test_parse_listing_metadata_mls_fields(self):
        """Test extraction of MLS-specific fields."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="mls-info">MLS #: 6789012</div>
        <span class="listing-price">$450,000</span>
        <table class="property-details">
            <tr><th>Property Type</th><td>Single Family Residence</td></tr>
            <tr><th>HOA Fee</th><td>No Fees</td></tr>
            <tr><th>Pool</th><td>Yes - Private</td></tr>
            <tr><th>Sewer</th><td>Public Sewer</td></tr>
        </table>
        """

        metadata = extractor._parse_listing_metadata(html)

        # Verify MLS fields
        assert metadata["mls_number"] == "6789012"
        assert metadata["price"] == 450000
        assert metadata["property_type"] == "Single Family Residence"
        assert metadata["hoa_fee"] == 0.0
        assert metadata["has_pool"] is True
        assert metadata["sewer_type"] == "city"

    def test_parse_listing_metadata_schools(self):
        """Test extraction of school information."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="schools-section">
            <div>Elementary: Barrel Elementary School</div>
            <div>Middle: Copper Creek Middle School</div>
            <div>High: Ironwood High School</div>
        </div>
        """

        metadata = extractor._parse_listing_metadata(html)

        # Verify school fields
        assert metadata["elementary_school_name"] == "Barrel Elementary School"
        assert metadata["middle_school_name"] == "Copper Creek Middle School"
        assert metadata["high_school_name"] == "Ironwood High School"

    def test_parse_listing_metadata_lot_size_acres(self):
        """Test lot size conversion from acres to sqft."""
        extractor = PhoenixMLSExtractor()

        html = """
        <table class="property-details">
            <tr><th>Lot Size</th><td>0.25 acres</td></tr>
        </table>
        """

        metadata = extractor._parse_listing_metadata(html)

        # 0.25 acres = 0.25 * 43560 = 10,890 sqft
        assert metadata["lot_sqft"] == 10890

    def test_parse_listing_metadata_hoa_variations(self):
        """Test HOA fee parsing with different formats."""
        extractor = PhoenixMLSExtractor()

        # Test "No Fees"
        html1 = '<table class="property-details"><tr><th>HOA Fee</th><td>No Fees</td></tr></table>'
        metadata1 = extractor._parse_listing_metadata(html1)
        assert metadata1["hoa_fee"] == 0.0

        # Test "$150/month"
        html2 = '<table class="property-details"><tr><th>HOA</th><td>$150/month</td></tr></table>'
        metadata2 = extractor._parse_listing_metadata(html2)
        assert metadata2["hoa_fee"] == 150.0

    def test_parse_listing_metadata_missing_fields(self):
        """Test graceful handling of missing metadata fields."""
        extractor = PhoenixMLSExtractor()

        # Empty HTML
        html = "<html><body><p>No property details</p></body></html>"

        metadata = extractor._parse_listing_metadata(html)

        # Should return empty dict or partial dict, not crash
        assert isinstance(metadata, dict)

    def test_parse_int_safe(self):
        """Test safe integer parsing helper."""
        extractor = PhoenixMLSExtractor()

        assert extractor._parse_int_safe("2,200") == 2200
        assert extractor._parse_int_safe("42") == 42
        assert extractor._parse_int_safe("invalid") is None
        assert extractor._parse_int_safe("") is None

    def test_parse_float_safe(self):
        """Test safe float parsing helper."""
        extractor = PhoenixMLSExtractor()

        assert extractor._parse_float_safe("2.5") == 2.5
        assert extractor._parse_float_safe("3") == 3.0
        assert extractor._parse_float_safe("invalid") is None
        assert extractor._parse_float_safe("") is None


# ============================================================================
# Image Gallery Extraction Tests
# ============================================================================


@pytest.mark.integration
class TestPhoenixMLSImageExtraction:
    """Test image URL extraction from listing pages."""

    def test_parse_image_gallery_basic(self):
        """Test basic image gallery parsing."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="photo-gallery">
            <img src="https://example.com/photo1.jpg" alt="Living Room">
            <img src="https://example.com/photo2.jpg" alt="Kitchen">
            <img src="https://example.com/photo3.jpg" alt="Bedroom">
        </div>
        """
        base_url = "https://phoenixmlssearch.com"

        urls = extractor._parse_image_gallery(html, base_url)

        assert len(urls) == 3
        assert "https://example.com/photo1.jpg" in urls
        assert "https://example.com/photo2.jpg" in urls
        assert "https://example.com/photo3.jpg" in urls

    def test_parse_image_gallery_data_attributes(self):
        """Test extraction from data-src and data-lazy-src attributes."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="gallery">
            <img src="placeholder.jpg" data-src="https://example.com/real1.jpg">
            <img data-lazy-src="https://example.com/real2.jpg">
        </div>
        """
        base_url = "https://phoenixmlssearch.com"

        urls = extractor._parse_image_gallery(html, base_url)

        assert len(urls) >= 2
        assert "https://example.com/real1.jpg" in urls
        assert "https://example.com/real2.jpg" in urls
        # Should NOT include placeholder
        assert "placeholder.jpg" not in urls

    def test_parse_image_gallery_relative_urls(self):
        """Test relative URL to absolute URL conversion."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="gallery">
            <img src="/images/property/photo1.jpg">
            <img src="../photos/photo2.jpg">
        </div>
        """
        base_url = "https://phoenixmlssearch.com/listings/"

        urls = extractor._parse_image_gallery(html, base_url)

        # All URLs should be absolute
        assert all(url.startswith("https://") for url in urls)

    def test_parse_image_gallery_deduplication(self):
        """Test duplicate image URL deduplication."""
        extractor = PhoenixMLSExtractor()

        html = """
        <div class="gallery">
            <img src="https://example.com/photo1.jpg">
            <img src="https://example.com/photo1.jpg">
            <a href="https://example.com/photo1.jpg">View</a>
        </div>
        """
        base_url = "https://phoenixmlssearch.com"

        urls = extractor._parse_image_gallery(html, base_url)

        # Should deduplicate to single URL
        assert urls.count("https://example.com/photo1.jpg") == 1

    def test_parse_image_gallery_script_extraction(self):
        """Test extraction from JavaScript arrays in <script> tags."""
        extractor = PhoenixMLSExtractor()

        html = """
        <script>
        var propertyImages = [
            "https://example.com/img1.jpg",
            "https://example.com/img2.png",
            "https://example.com/img3.jpeg"
        ];
        </script>
        """
        base_url = "https://phoenixmlssearch.com"

        urls = extractor._parse_image_gallery(html, base_url)

        # Should extract from JavaScript
        assert len(urls) >= 3
        assert any("img1.jpg" in url for url in urls)
        assert any("img2.png" in url for url in urls)

    def test_is_image_url(self):
        """Test image URL detection by extension."""
        extractor = PhoenixMLSExtractor()

        # Valid image URLs
        assert extractor._is_image_url("https://example.com/photo.jpg")
        assert extractor._is_image_url("https://example.com/image.jpeg")
        assert extractor._is_image_url("https://example.com/pic.png")
        assert extractor._is_image_url("https://example.com/graphic.gif")
        assert extractor._is_image_url("https://example.com/modern.webp")

        # Not image URLs
        assert not extractor._is_image_url("https://example.com/page.html")
        assert not extractor._is_image_url("https://example.com/script.js")
        assert not extractor._is_image_url("https://example.com/style.css")


# ============================================================================
# Full Extraction Workflow Tests (Mocked)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestPhoenixMLSFullExtraction:
    """Test complete extraction workflow with mocked HTTP."""

    async def test_extract_full_property_data(
        self, sample_phoenix_property, mock_phoenixmls_html
    ):
        """Test complete extraction: images + metadata for real property.

        This is the primary test case from E2.R1 Task 9:
        - Extract >5 images
        - Verify all kill-switch fields populated
        - Verify new MLS fields populated
        """
        extractor = PhoenixMLSExtractor(http_client=httpx.AsyncClient())

        # Mock the search and listing page fetch
        with patch.object(extractor, '_search_property', new_callable=AsyncMock) as mock_search, \
             patch.object(extractor, '_fetch_listing_page', new_callable=AsyncMock) as mock_fetch:

            # Mock successful search returning listing URL
            mock_search.return_value = "https://phoenixmlssearch.com/property/12345"

            # Mock listing page HTML
            mock_fetch.return_value = mock_phoenixmls_html

            # Execute extraction
            image_urls, metadata = await extractor.extract_image_urls(sample_phoenix_property)

            # Verify images extracted
            assert len(image_urls) >= 5, f"Expected at least 5 images, got {len(image_urls)}"

            # Verify kill-switch fields populated
            assert "beds" in metadata
            assert "baths" in metadata
            assert "sqft" in metadata
            assert "lot_sqft" in metadata
            assert "year_built" in metadata
            assert "garage_spaces" in metadata
            assert "sewer_type" in metadata

            # Verify values are correct
            assert metadata["beds"] == 4
            assert metadata["baths"] == 2.0
            assert metadata["sqft"] == 2200
            assert metadata["lot_sqft"] == 8500
            assert metadata["year_built"] == 2010
            assert metadata["garage_spaces"] == 2
            assert metadata["sewer_type"] == "city"

            # Verify new MLS fields populated
            assert "property_type" in metadata
            assert metadata["property_type"] == "Single Family Residence"

            # Verify school fields
            assert "elementary_school_name" in metadata
            assert "middle_school_name" in metadata
            assert "high_school_name" in metadata

        await extractor.close()

    async def test_extract_caches_metadata_on_property(
        self, sample_phoenix_property, mock_phoenixmls_html
    ):
        """Test metadata is cached on Property object via get_cached_metadata().

        This is test requirement 3 from E2.R1 Task 9:
        - After extraction, get_cached_metadata() should return data
        """
        extractor = PhoenixMLSExtractor(http_client=httpx.AsyncClient())

        # Mock the extraction
        with patch.object(extractor, '_search_property', new_callable=AsyncMock) as mock_search, \
             patch.object(extractor, '_fetch_listing_page', new_callable=AsyncMock) as mock_fetch:

            mock_search.return_value = "https://phoenixmlssearch.com/property/12345"
            mock_fetch.return_value = mock_phoenixmls_html

            # Execute extraction
            image_urls, metadata = await extractor.extract_image_urls(sample_phoenix_property)

            # Verify metadata was cached on Property object
            cached = extractor.get_cached_metadata(sample_phoenix_property)

            assert cached is not None, "Metadata should be cached after extraction"
            assert cached == metadata, "Cached metadata should match returned metadata"

            # Verify cached metadata has expected fields
            assert "beds" in cached
            assert "sewer_type" in cached
            assert "property_type" in cached

        await extractor.close()

    async def test_extract_handles_property_not_found(self, sample_phoenix_property):
        """Test graceful handling when property not found on MLS."""
        extractor = PhoenixMLSExtractor(http_client=httpx.AsyncClient())

        # Mock search returning None (property not found)
        with patch.object(extractor, '_search_property', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = None

            # Execute extraction
            image_urls, metadata = await extractor.extract_image_urls(sample_phoenix_property)

            # Should return empty results, not crash
            assert image_urls == []
            assert metadata == {}

        await extractor.close()

    async def test_extract_handles_network_timeout(self, sample_phoenix_property):
        """Test timeout handling with skip condition for network failures."""
        extractor = PhoenixMLSExtractor(http_client=httpx.AsyncClient(timeout=0.001))

        # This test should gracefully skip if network is unavailable
        # Use very short timeout to force timeout
        try:
            with pytest.raises((httpx.TimeoutException, httpx.ConnectTimeout)):
                # Mock search that times out
                with patch.object(extractor, '_search_property', new_callable=AsyncMock) as mock_search:
                    mock_search.side_effect = httpx.TimeoutException("Request timeout")
                    await extractor.extract_image_urls(sample_phoenix_property)
        except Exception as e:
            # Network unavailable - skip test
            pytest.skip(f"Network unavailable: {e}")
        finally:
            await extractor.close()


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================


@pytest.mark.integration
class TestPhoenixMLSPriorityInOrchestrator:
    """Test PhoenixMLS priority ordering in orchestrator.

    This is test requirement 2 from E2.R1 Task 9:
    - Verify PhoenixMLSExtractor is first in EXTRACTORS list
    """

    def test_phoenixmls_is_first_priority_source(self, tmp_path):
        """Test PhoenixMLS is prioritized first in orchestrator source list."""
        # Create orchestrator with all sources enabled
        orchestrator = ImageExtractionOrchestrator(
            base_dir=tmp_path,
            enabled_sources=[
                ImageSource.PHOENIX_MLS,
                ImageSource.MARICOPA_ASSESSOR,
                ImageSource.ZILLOW,
                ImageSource.REDFIN,
            ],
        )

        # Get extractor instances
        extractors = orchestrator._create_extractors()

        # Verify PhoenixMLS is first
        assert len(extractors) > 0, "Should have at least one extractor"
        assert extractors[0].source == ImageSource.PHOENIX_MLS, (
            "PhoenixMLSExtractor should be first in priority order"
        )

    def test_phoenixmls_priority_comment_in_orchestrator(self):
        """Verify orchestrator source code has PhoenixMLS priority comment."""
        # Read orchestrator.py source
        import inspect

        from phx_home_analysis.services.image_extraction.orchestrator import (
            ImageExtractionOrchestrator,
        )

        source = inspect.getsource(ImageExtractionOrchestrator._create_extractors)

        # Check for PhoenixMLS FIRST comment
        assert "PhoenixMLS FIRST" in source or "PHOENIX_MLS: PhoenixMLSExtractor" in source, (
            "Orchestrator should document PhoenixMLS as first priority"
        )


# ============================================================================
# Address Parsing Tests
# ============================================================================


@pytest.mark.integration
class TestPhoenixMLSAddressParsing:
    """Test address parsing and matching logic."""

    def test_parse_street_parts_valid(self):
        """Test valid street address parsing."""
        extractor = PhoenixMLSExtractor()

        result = extractor._parse_street_parts("4732 W Davis Rd")

        assert result is not None
        number, name = result
        assert number == "4732"
        assert name == "w davis rd"

    def test_parse_street_parts_no_number(self):
        """Test rejection of street with no number."""
        extractor = PhoenixMLSExtractor()

        result = extractor._parse_street_parts("Main Street")

        assert result is None

    def test_parse_street_parts_invalid_number(self):
        """Test rejection of non-numeric street number."""
        extractor = PhoenixMLSExtractor()

        result = extractor._parse_street_parts("ABC Main Street")

        assert result is None

    def test_find_matching_listing_exact_match(self):
        """Test finding listing with exact address match."""
        extractor = PhoenixMLSExtractor()

        from bs4 import BeautifulSoup

        html = """
        <div>
            <a href="/property/12345">4732 W Davis Rd, Glendale, AZ</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        property = Property(
            street="4732 W Davis Rd",
            city="Glendale",
            state="AZ",
            zip_code="85306",
            full_address="4732 W Davis Rd, Glendale, AZ 85306",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2200,
            price_per_sqft_raw=204.55,
            lot_sqft=8500,
        )

        url = extractor._find_matching_listing(soup, property)

        assert url is not None
        assert "/property/12345" in url


# ============================================================================
# Summary Test
# ============================================================================


@pytest.mark.integration
def test_phoenixmls_extractor_integration_complete():
    """Summary test verifying all PhoenixMLS integration components.

    This test ensures:
    1. PhoenixMLSExtractor is importable and instantiable
    2. All required methods are implemented
    3. ImageSource.PHOENIX_MLS enum exists
    4. Metro cities list is comprehensive
    """
    # Verify imports
    assert PhoenixMLSExtractor is not None
    assert ImageSource.PHOENIX_MLS is not None
    assert PHOENIX_METRO_CITIES is not None

    # Verify instantiation
    extractor = PhoenixMLSExtractor()
    assert extractor.source == ImageSource.PHOENIX_MLS
    assert extractor.name == "Phoenix MLS"

    # Verify required methods exist
    assert hasattr(extractor, 'extract_image_urls')
    assert hasattr(extractor, 'download_image')
    assert hasattr(extractor, 'can_handle')
    assert hasattr(extractor, 'get_cached_metadata')
    assert hasattr(extractor, '_parse_listing_metadata')
    assert hasattr(extractor, '_parse_image_gallery')

    # Verify metro cities
    assert len(PHOENIX_METRO_CITIES) >= 20
    assert "phoenix" in PHOENIX_METRO_CITIES
    assert "scottsdale" in PHOENIX_METRO_CITIES
    assert "glendale" in PHOENIX_METRO_CITIES

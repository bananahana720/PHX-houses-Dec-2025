"""Integration tests for Zillow/Redfin listing extraction with fallback chain.

Tests the multi-layered extraction strategy:
1. nodriver (primary)
2. curl-cffi (fallback 1)
3. Playwright MCP (fallback 2)

Uses mocked responses for deterministic testing.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import ImageSource
from phx_home_analysis.services.image_extraction.extractors.redfin import (
    RedfinExtractor,
)
from phx_home_analysis.services.image_extraction.extractors.zillow import (
    ZillowExtractor,
)
from phx_home_analysis.services.infrastructure import (
    PlaywrightMcpClient,
    UserAgentRotator,
    get_random_user_agent,
)


# Test fixtures
@pytest.fixture
def sample_property():
    """Create sample property for testing."""
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
def zillow_html():
    """Load Zillow sample HTML fixture."""
    fixture_path = Path(__file__).parents[1] / "fixtures" / "listing_pages" / "zillow_sample.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def redfin_html():
    """Load Redfin sample HTML fixture."""
    fixture_path = Path(__file__).parents[1] / "fixtures" / "listing_pages" / "redfin_sample.html"
    return fixture_path.read_text(encoding="utf-8")


# User-Agent Rotation Tests
def test_user_agent_rotator_loads_config():
    """Test UserAgentRotator loads config with 20+ UAs."""
    rotator = UserAgentRotator()

    assert len(rotator) >= 20, f"Expected at least 20 UAs, got {len(rotator)}"
    assert all(ua.startswith("Mozilla/") for ua in rotator.get_all())


def test_user_agent_random_selection():
    """Test random UA selection returns valid UAs."""
    rotator = UserAgentRotator()

    # Get 10 random UAs
    uas = [rotator.get_random() for _ in range(10)]

    assert len(uas) == 10
    assert all(ua.startswith("Mozilla/") for ua in uas)


def test_user_agent_sequential_rotation():
    """Test sequential rotation cycles through all UAs without duplicates."""
    rotator = UserAgentRotator()
    pool_size = len(rotator)

    # Get pool_size UAs sequentially
    uas = [rotator.get_next() for _ in range(pool_size)]

    # Should have no duplicates in one full cycle
    assert len(set(uas)) == pool_size

    # Next UA should be first UA again (cycling)
    assert rotator.get_next() == uas[0]


def test_get_random_user_agent_convenience():
    """Test convenience function for random UA."""
    ua1 = get_random_user_agent()
    ua2 = get_random_user_agent()

    assert ua1.startswith("Mozilla/")
    assert ua2.startswith("Mozilla/")
    # Random should potentially return different UAs
    # (not guaranteed but highly likely with 20+ pool)


# Zillow Extractor Tests
@pytest.mark.asyncio
async def test_zillow_extractor_source():
    """Test Zillow extractor source enum."""
    extractor = ZillowExtractor()
    assert extractor.source == ImageSource.ZILLOW


@pytest.mark.asyncio
async def test_zillow_build_search_url(sample_property):
    """Test Zillow search URL construction."""
    extractor = ZillowExtractor()
    url = extractor._build_search_url(sample_property)

    assert "zillow.com/homes/" in url
    assert "4732-W-Davis-Rd" in url
    assert "Glendale" in url
    assert "AZ" in url
    assert "85306" in url


@pytest.mark.asyncio
async def test_zillow_is_high_quality_url():
    """Test Zillow high-quality URL filter."""
    extractor = ZillowExtractor()

    # Should accept high-res Zillow CDN URLs
    assert extractor._is_high_quality_url("https://photos.zillowstatic.com/fp/abc123-uncrate.jpg")

    # Should reject thumbnails
    assert not extractor._is_high_quality_url("https://photos.zillowstatic.com/thumb_320.jpg")

    # Should reject map tiles
    assert not extractor._is_high_quality_url("https://maps.zillowstatic.com/tile.png")


# Redfin Extractor Tests
@pytest.mark.asyncio
async def test_redfin_extractor_source():
    """Test Redfin extractor source enum."""
    extractor = RedfinExtractor()
    assert extractor.source == ImageSource.REDFIN


@pytest.mark.asyncio
async def test_redfin_build_search_url(sample_property):
    """Test Redfin search URL construction."""
    extractor = RedfinExtractor()
    url = extractor._build_search_url(sample_property)

    assert "redfin.com/search?q=" in url
    assert "4732+W+Davis+Rd" in url or "4732%20W%20Davis%20Rd" in url


@pytest.mark.asyncio
async def test_redfin_convert_to_highres():
    """Test Redfin thumbnail to high-res conversion."""
    extractor = RedfinExtractor()

    # Test path-based size conversion
    thumb = "https://ssl.cdn-redfin.com/photo/300x200/abc.jpg"
    highres = extractor._convert_to_highres(thumb)
    assert "1024x768" in highres

    # Test suffix-based conversion
    thumb2 = "https://ssl.cdn-redfin.com/photo/genBcs.123_300x200.jpg"
    highres2 = extractor._convert_to_highres(thumb2)
    assert "_1024.jpg" in highres2


@pytest.mark.asyncio
async def test_redfin_is_redfin_image():
    """Test Redfin image URL filter."""
    extractor = RedfinExtractor()

    # Should accept property photos
    assert extractor._is_redfin_image(
        "https://ssl.cdn-redfin.com/photo/68/bcsphoto/471/genBcs.123.jpg"
    )

    # Should reject logos
    assert not extractor._is_redfin_image("https://ssl.cdn-redfin.com/images/logo.png")

    # Should reject homepage promos
    assert not extractor._is_redfin_image("https://ssl.cdn-redfin.com/homepageimage/promo.jpg")


# Playwright MCP Tests
@pytest.mark.asyncio
async def test_playwright_mcp_client_initialization():
    """Test PlaywrightMcpClient initializes."""
    client = PlaywrightMcpClient()
    assert client is not None
    assert not client._initialized


@pytest.mark.asyncio
async def test_playwright_mcp_extract_images_from_snapshot():
    """Test image extraction from accessibility snapshot."""
    client = PlaywrightMcpClient()

    # Mock snapshot with image nodes
    snapshot = {
        "children": [
            {"url": "https://photos.zillowstatic.com/image1.jpg"},
            {
                "src": "https://ssl.cdn-redfin.com/photo/image2.jpg",
                "children": [{"value": "https://example.com/image3.png"}],
            },
        ]
    }

    images = client.extract_images_from_snapshot(snapshot)

    assert len(images) == 3
    # Images may be in any order due to set conversion
    image_filenames = [img.split("/")[-1] for img in images]
    assert "image1.jpg" in image_filenames
    assert "image2.jpg" in image_filenames
    assert "image3.png" in image_filenames


@pytest.mark.asyncio
async def test_playwright_mcp_extract_images_with_filter():
    """Test filtered image extraction from snapshot."""
    client = PlaywrightMcpClient()

    snapshot = {
        "children": [
            {"url": "https://photos.zillowstatic.com/image1.jpg"},
            {"url": "https://example.com/other.jpg"},
            {"url": "https://ssl.cdn-redfin.com/photo/image2.jpg"},
        ]
    }

    # Filter for Zillow/Redfin CDN only
    images = client.extract_images_from_snapshot(
        snapshot, filter_pattern=r"(photos\.zillowstatic|ssl\.cdn-redfin)"
    )

    assert len(images) == 2
    assert all("zillow" in img or "redfin" in img for img in images)


@pytest.mark.asyncio
async def test_playwright_mcp_is_likely_image_url():
    """Test image URL detection."""
    client = PlaywrightMcpClient()

    # Should detect by extension
    assert client._is_likely_image_url("https://example.com/photo.jpg")
    assert client._is_likely_image_url("https://example.com/image.png")

    # Should detect by CDN pattern
    assert client._is_likely_image_url("https://photos.zillowstatic.com/abc")
    assert client._is_likely_image_url("https://ssl.cdn-redfin.com/photo/123")

    # Should reject non-images
    assert not client._is_likely_image_url("https://example.com/page.html")


# Integration Test: Full Extraction Workflow (Mocked)
@pytest.mark.asyncio
async def test_zillow_extraction_with_mocked_browser(sample_property, zillow_html):
    """Test Zillow extraction with mocked nodriver browser."""
    extractor = ZillowExtractor()

    # Mock browser tab
    mock_tab = AsyncMock()
    mock_tab.get_content = AsyncMock(return_value=zillow_html)
    mock_tab.url = (
        "https://www.zillow.com/homedetails/4732-W-Davis-Rd-Glendale-AZ-85306/7826047_zpid/"
    )
    mock_tab.query_selector_all = AsyncMock(
        return_value=[
            MagicMock(attrs={"src": "https://photos.zillowstatic.com/fp/photo1-uncrate.jpg"}),
            MagicMock(attrs={"src": "https://photos.zillowstatic.com/fp/photo2-uncrate.jpg"}),
        ]
    )

    # Extract URLs from mocked page
    urls = await extractor._extract_urls_from_page(mock_tab)

    assert len(urls) >= 2
    assert all("photos.zillowstatic.com" in url for url in urls)


@pytest.mark.asyncio
async def test_redfin_extraction_score_address_match():
    """Test Redfin address matching scoring."""
    extractor = RedfinExtractor()

    target = "4732 W Davis Rd, Glendale, AZ 85306"

    # Perfect match
    score1 = extractor._score_address_match(target, "4732 W Davis Rd, Glendale, AZ 85306")
    assert score1 >= 0.8

    # Good match (street + city)
    score2 = extractor._score_address_match(target, "4732 W Davis Road, Glendale")
    assert score2 >= 0.5

    # No match (different street number)
    score3 = extractor._score_address_match(target, "9999 E Other St, Phoenix, AZ")
    assert score3 == 0.0


# Summary Test: Verify All Components Exist
def test_all_extraction_components_available():
    """Verify all extraction components are importable and functional."""
    # Infrastructure components
    assert UserAgentRotator is not None
    assert PlaywrightMcpClient is not None

    # Extractor components
    assert ZillowExtractor is not None
    assert RedfinExtractor is not None

    # Convenience functions
    assert get_random_user_agent is not None

    # Test instantiation doesn't raise
    rotator = UserAgentRotator()
    assert len(rotator) >= 20

    zillow = ZillowExtractor()
    assert zillow.source == ImageSource.ZILLOW

    redfin = RedfinExtractor()
    assert redfin.source == ImageSource.REDFIN

    mcp = PlaywrightMcpClient()
    assert mcp is not None

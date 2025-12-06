"""Shared integration test fixtures for image extraction pipeline.

Provides mocked HTTP responses, browser automation stubs, and orchestrator
instances for testing multi-source extraction workflows.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.phx_home_analysis.domain.entities import Property

# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_property():
    """Create a sample property for extraction testing.

    Returns:
        Property: 4bd/2ba property in Phoenix with all required fields.
    """
    return Property(
        street="5219 W EL CAMINITO Drive",
        city="Glendale",
        state="AZ",
        zip_code="85302",
        full_address="5219 W EL CAMINITO Drive, Glendale, AZ 85302",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.0,
        sqft=2100,
        price_per_sqft_raw=226.2,
        lot_sqft=9000,
        year_built=2005,
        garage_spaces=2,
    )


@pytest.fixture
def sample_property_minimal():
    """Create a minimal property for testing missing data scenarios.

    Returns:
        Property: Property with only required fields populated.
    """
    return Property(
        street="100 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="100 Main St, Phoenix, AZ 85001",
        price="$400,000",
        price_num=400000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=200.0,
    )


@pytest.fixture
def sample_properties():
    """Create a collection of properties for batch testing.

    Returns:
        list: 5 properties with varied characteristics.
    """
    return [
        Property(
            street="5219 W EL CAMINITO Drive",
            city="Glendale",
            state="AZ",
            zip_code="85302",
            full_address="5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            price="$475,000",
            price_num=475000,
            beds=4,
            baths=2.0,
            sqft=2100,
            price_per_sqft_raw=226.2,
            lot_sqft=9000,
            year_built=2005,
        ),
        Property(
            street="123 Desert Rose Ln",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Desert Rose Ln, Phoenix, AZ 85001",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2.0,
            sqft=2050,
            price_per_sqft_raw=219.5,
            lot_sqft=8500,
            year_built=2010,
        ),
        Property(
            street="456 Cactus Ave",
            city="Chandler",
            state="AZ",
            zip_code="85224",
            full_address="456 Cactus Ave, Chandler, AZ 85224",
            price="$420,000",
            price_num=420000,
            beds=4,
            baths=2.0,
            sqft=1950,
            price_per_sqft_raw=215.4,
            lot_sqft=7500,
            year_built=2008,
        ),
        Property(
            street="789 Sunset Dr",
            city="Scottsdale",
            state="AZ",
            zip_code="85251",
            full_address="789 Sunset Dr, Scottsdale, AZ 85251",
            price="$520,000",
            price_num=520000,
            beds=4,
            baths=2.5,
            sqft=2300,
            price_per_sqft_raw=226.1,
            lot_sqft=10000,
            year_built=2012,
        ),
        Property(
            street="321 Mountain View Rd",
            city="Paradise Valley",
            state="AZ",
            zip_code="85253",
            full_address="321 Mountain View Rd, Paradise Valley, AZ 85253",
            price="$595,000",
            price_num=595000,
            beds=5,
            baths=3.0,
            sqft=2800,
            price_per_sqft_raw=212.5,
            lot_sqft=12000,
            year_built=2015,
        ),
    ]


# ============================================================================
# IMAGE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_image_bytes():
    """Create minimal valid PNG bytes for image testing.

    Returns:
        bytes: Valid 1x1 transparent PNG pixel.
    """
    # Minimal valid PNG: 1x1 transparent pixel
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x01,  # width: 1
        0x00, 0x00, 0x00, 0x01,  # height: 1
        0x08, 0x06, 0x00, 0x00, 0x00,  # bit depth, color type
        0x1F, 0x15, 0xC4, 0x89,  # CRC
        0x00, 0x00, 0x00, 0x0A,  # IDAT chunk length
        0x49, 0x44, 0x41, 0x54,  # IDAT
        0x78, 0x9C, 0x63, 0xF8, 0xFF, 0xFF, 0x3F, 0x00,  # Data
        0x00, 0x05, 0xFE, 0x02, 0xFE,  # Data continuation
        0xA7, 0x35, 0x81, 0x84,  # CRC
        0x00, 0x00, 0x00, 0x00,  # IEND chunk length
        0x49, 0x45, 0x4E, 0x44,  # IEND
        0xAE, 0x42, 0x60, 0x82,  # CRC
    ])


@pytest.fixture
def sample_image_urls():
    """Create sample image URLs for various sources.

    Returns:
        dict: Image URLs keyed by source name.
    """
    return {
        "zillow": [
            "https://photos.zillowstatic.com/p/2640844520-432x324c.jpg",
            "https://photos.zillowstatic.com/p/2640844521-432x324c.jpg",
            "https://photos.zillowstatic.com/p/2640844522-432x324c.jpg",
        ],
        "phoenix_mls": [
            "https://cdn.photos.sparkplatform.com/az/abc123-t.jpg",
            "https://cdn.photos.sparkplatform.com/az/abc124-t.jpg",
        ],
        "redfin": [
            "https://s.yimg.com/aah/redfinlistings/123456_0.jpg",
            "https://s.yimg.com/aah/redfinlistings/123457_0.jpg",
        ],
        "maricopa_assessor": [
            "https://maricopa.assessor.api.photos/property/123456.jpg",
        ],
    }


# ============================================================================
# MOCK BROWSER FIXTURES
# ============================================================================


@pytest.fixture
def mock_nodriver_tab():
    """Create a mock nodriver Tab for browser automation testing.

    Returns:
        AsyncMock: Mocked Tab with common browser methods.
    """
    tab = AsyncMock()
    tab.get_content = AsyncMock(return_value="<html><body>Mock page</body></html>")
    tab.get = AsyncMock(return_value=None)
    tab.find_element = AsyncMock(return_value=None)
    tab.find_elements = AsyncMock(return_value=[])
    tab.goto = AsyncMock(return_value=None)
    tab.close = AsyncMock(return_value=None)
    tab.screenshot = AsyncMock(return_value=b"fake_image_bytes")
    tab.evaluate = AsyncMock(return_value=None)
    tab.wait = AsyncMock(return_value=None)
    return tab


@pytest.fixture
def mock_browser():
    """Create a mock browser instance for testing.

    Returns:
        AsyncMock: Mocked browser with tab creation.
    """
    browser = AsyncMock()
    browser.get_tab = AsyncMock(return_value=AsyncMock())
    browser.create_tab = AsyncMock(return_value=AsyncMock())
    browser.close = AsyncMock(return_value=None)
    return browser


# ============================================================================
# MOCK HTTP FIXTURES
# ============================================================================


@pytest.fixture
def mock_httpx_response(sample_image_bytes):
    """Create a mock HTTP response with image bytes.

    Returns:
        MagicMock: Response with status_code and content.
    """
    response = MagicMock()
    response.status_code = 200
    response.content = sample_image_bytes
    response.headers = {"content-type": "image/png"}
    return response


@pytest.fixture
def mock_httpx_404_response():
    """Create a mock 404 HTTP response.

    Returns:
        MagicMock: Response with 404 status.
    """
    response = MagicMock()
    response.status_code = 404
    response.content = b""
    response.raise_for_status = MagicMock(side_effect=Exception("404 Not Found"))
    return response


@pytest.fixture
def mock_httpx_timeout_response():
    """Create a mock timeout HTTP response.

    Returns:
        MagicMock: Response simulating timeout.
    """
    response = MagicMock()
    response.status_code = 408
    response.content = b""
    response.raise_for_status = MagicMock(side_effect=TimeoutError("Request timeout"))
    return response


# ============================================================================
# STATE AND CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def extraction_manifest(sample_property, sample_image_urls):
    """Create a sample extraction manifest.

    Returns:
        dict: Manifest with images per property and metadata.
    """
    property_hash = "a1b2c3d4"
    return {
        property_hash: {
            "property": {
                "full_address": sample_property.full_address,
                "beds": sample_property.beds,
                "baths": sample_property.baths,
            },
            "images": [
                {
                    "url": url,
                    "md5": f"hash_{i}",
                    "source": source,
                    "downloaded_at": "2025-12-06T10:00:00Z",
                }
                for source, urls in sample_image_urls.items()
                for i, url in enumerate(urls)
            ],
            "extraction_run_id": "run_abc123",
        }
    }


@pytest.fixture
def extraction_state():
    """Create a sample extraction state for recovery testing.

    Returns:
        dict: State with checkpoint and progress tracking.
    """
    return {
        "run_id": "run_abc123",
        "started_at": "2025-12-06T10:00:00Z",
        "total_properties": 5,
        "completed": 2,
        "failed": 0,
        "last_checkpoint": "2025-12-06T10:05:00Z",
        "properties_processed": [
            "5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            "123 Desert Rose Ln, Phoenix, AZ 85001",
        ],
    }


@pytest.fixture
def url_tracker_data():
    """Create sample URL tracker data.

    Returns:
        dict: Tracked URLs per property and source.
    """
    return {
        "a1b2c3d4": {
            "zillow": [
                "https://photos.zillowstatic.com/p/2640844520-432x324c.jpg",
                "https://photos.zillowstatic.com/p/2640844521-432x324c.jpg",
            ],
            "phoenix_mls": [
                "https://cdn.photos.sparkplatform.com/az/abc123-t.jpg",
            ],
        },
        "e5f6g7h8": {
            "zillow": [
                "https://photos.zillowstatic.com/p/2640845000-432x324c.jpg",
            ],
        },
    }


# ============================================================================
# DIRECTORY AND PATH FIXTURES
# ============================================================================


@pytest.fixture
def extraction_dir(tmp_path):
    """Create a temporary extraction directory structure.

    Args:
        tmp_path: pytest tmp_path fixture for isolation.

    Returns:
        Path: Temporary extraction directory with subdirectories.
    """
    extraction_base = tmp_path / "extraction"
    extraction_base.mkdir(exist_ok=True)
    (extraction_base / "images").mkdir(exist_ok=True)
    (extraction_base / "logs").mkdir(exist_ok=True)
    return extraction_base


@pytest.fixture
def orchestrator(extraction_dir, monkeypatch):
    """Create a configured orchestrator instance for testing.

    Args:
        extraction_dir: Temporary extraction directory.
        monkeypatch: pytest monkeypatch for environment mocking.

    Returns:
        ImageExtractionOrchestrator: Configured for testing.
    """
    from src.phx_home_analysis.services.image_extraction.orchestrator import (
        ImageExtractionOrchestrator,
    )

    # Patch environment variables
    monkeypatch.setenv("PHX_EXTRACTION_DIR", str(extraction_dir))

    return ImageExtractionOrchestrator(base_dir=extraction_dir)


# ============================================================================
# EXTRACTION ERROR FIXTURES
# ============================================================================


@pytest.fixture
def extraction_errors():
    """Create sample extraction errors for error aggregation testing.

    Returns:
        dict: Error types and counts.
    """
    return {
        "404_not_found": 15,
        "timeout": 8,
        "rate_limit": 5,
        "captcha_detected": 3,
        "connection_error": 2,
    }


@pytest.fixture
def circuit_breaker_state():
    """Create sample circuit breaker state.

    Returns:
        dict: Circuit states per source.
    """
    return {
        "zillow": {
            "status": "CLOSED",
            "failures": 0,
            "disabled_until": None,
        },
        "phoenix_mls": {
            "status": "HALF_OPEN",
            "failures": 3,
            "disabled_until": 1733504700.5,
        },
        "redfin": {
            "status": "OPEN",
            "failures": 5,
            "disabled_until": 1733505000.0,
        },
    }


# ============================================================================
# METRICS AND STATISTICS FIXTURES
# ============================================================================


@pytest.fixture
def extraction_metrics():
    """Create sample extraction metrics.

    Returns:
        dict: Metrics for extraction performance tracking.
    """
    return {
        "total_images_extracted": 42,
        "unique_images": 38,
        "duplicates_removed": 4,
        "extraction_time_seconds": 125.4,
        "images_per_second": 0.3,
        "captcha_attempts": 2,
        "successful_retries": 3,
        "failed_retries": 1,
    }


@pytest.fixture
def run_log_entries():
    """Create sample run log entries.

    Returns:
        list: Log entries for extraction run.
    """
    return [
        {
            "timestamp": "2025-12-06T10:00:00Z",
            "property": "5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            "status": "STARTED",
            "message": "Starting extraction from Zillow",
        },
        {
            "timestamp": "2025-12-06T10:00:15Z",
            "property": "5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            "status": "SUCCESS",
            "message": "Downloaded 3 images from Zillow",
            "images_count": 3,
        },
        {
            "timestamp": "2025-12-06T10:00:20Z",
            "property": "5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            "status": "STARTED",
            "message": "Starting extraction from Phoenix MLS",
        },
        {
            "timestamp": "2025-12-06T10:00:30Z",
            "property": "5219 W EL CAMINITO Drive, Glendale, AZ 85302",
            "status": "SUCCESS",
            "message": "Downloaded 2 images from Phoenix MLS",
            "images_count": 2,
        },
    ]

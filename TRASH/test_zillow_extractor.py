"""Quick validation script for ZillowExtractor implementation.

This script tests:
1. ZillowExtractor can be imported
2. Properties are correctly implemented
3. Interface matches base class requirements
"""

import asyncio
from src.phx_home_analysis.services.image_extraction.extractors.zillow import ZillowExtractor
from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import ImageSource


async def test_zillow_extractor():
    """Test ZillowExtractor basic functionality."""
    print("Testing ZillowExtractor implementation...")

    # Test 1: Instantiation
    extractor = ZillowExtractor(headless=True, timeout=30.0)
    print("✓ ZillowExtractor instantiated successfully")

    # Test 2: Source property
    assert extractor.source == ImageSource.ZILLOW, "Source should be ZILLOW"
    print(f"✓ Source property: {extractor.source.display_name}")

    # Test 3: Name property (inherited from base)
    assert extractor.name == "Zillow", f"Expected 'Zillow', got '{extractor.name}'"
    print(f"✓ Name property: {extractor.name}")

    # Test 4: Rate limit delay
    assert extractor.rate_limit_delay == 0.5, f"Expected 0.5s, got {extractor.rate_limit_delay}s"
    print(f"✓ Rate limit delay: {extractor.rate_limit_delay}s")

    # Test 5: Build search URL
    test_property = Property(
        street="1234 N Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="1234 N Main St, Phoenix, AZ 85001",
        price="$500,000",
        price_num=500000,
        beds=4,
        baths=2.5,
        sqft=2500,
        price_per_sqft_raw=200.0,
    )

    url = extractor._build_search_url(test_property)
    assert "zillow.com" in url, "URL should contain zillow.com"
    assert "1234" in url or "Main" in url, "URL should contain address components"
    print(f"✓ Search URL built: {url}")

    # Test 6: High quality URL filtering
    test_urls = [
        ("https://photos.zillowstatic.com/fp/123-uncrate.jpg", True),
        ("https://photos.zillowstatic.com/fp/123-thumb.jpg", False),
        ("https://example.com/small-photo.jpg", False),
        ("https://example.com/logo.png", False),
    ]

    for url, expected in test_urls:
        result = extractor._is_high_quality_url(url)
        assert result == expected, f"URL {url} should be {expected}, got {result}"
    print("✓ High quality URL filtering works correctly")

    # Test 7: can_handle (should return True for all properties by default)
    assert extractor.can_handle(test_property), "Should handle all properties"
    print("✓ can_handle() returns True")

    # Test 8: Close method
    await extractor.close()
    print("✓ Cleanup completed successfully")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_zillow_extractor())

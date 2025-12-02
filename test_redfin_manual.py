"""Manual test script for Redfin extractor.

This script demonstrates the Redfin extractor functionality
without requiring a full test suite setup.
"""

import asyncio
import logging
from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.services.image_extraction.extractors.redfin import (
    RedfinExtractor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_redfin_extractor():
    """Test Redfin extractor with sample property."""
    # Create sample property (real Phoenix area listing)
    property = Property(
        street="4732 W Davis Rd",
        city="Glendale",
        state="AZ",
        zip_code="85306",
        full_address="4732 W Davis Rd, Glendale, AZ 85306",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.0,
        sqft=2241,
        price_per_sqft_raw=211.96,
    )

    # Initialize extractor (uses StealthExtractionConfig from env)
    extractor = RedfinExtractor()

    try:
        print(f"\n{'='*60}")
        print(f"Testing Redfin Extractor")
        print(f"{'='*60}")
        print(f"Property: {property.full_address}")
        print(f"Source: {extractor.source.display_name}")
        print(f"Base URL: {extractor.source.base_url}")
        print(f"Rate limit: {extractor.rate_limit_delay}s")
        print(f"Can handle: {extractor.can_handle(property)}")

        # Show generated URL for verification
        search_url = extractor._build_search_url(property)
        print(f"Generated URL: {search_url}")

        # Extract image URLs
        print(f"\n{'='*60}")
        print("Extracting image URLs...")
        print(f"{'='*60}")

        urls = await extractor.extract_image_urls(property)

        print(f"\nFound {len(urls)} image URLs:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")

        # Download first image if available
        if urls:
            print(f"\n{'='*60}")
            print("Downloading first image...")
            print(f"{'='*60}")

            image_data, content_type = await extractor.download_image(urls[0])
            print(f"Downloaded: {len(image_data)} bytes")
            print(f"Content-Type: {content_type}")

            # Save to file
            output_path = "test_redfin_image.jpg"
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"Saved to: {output_path}")

        print(f"\n{'='*60}")
        print("Test completed successfully!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(test_redfin_extractor())

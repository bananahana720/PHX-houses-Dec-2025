"""Test script for Redfin interactive search implementation.

This script tests the updated Redfin extractor with interactive search
for the property: 2353 W Tierra Buena Ln, Phoenix, AZ 85023
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.services.image_extraction.extractors.redfin import RedfinExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Enable debug logging for Redfin extractor
logging.getLogger("phx_home_analysis.services.image_extraction.extractors.redfin").setLevel(
    logging.DEBUG
)


async def test_redfin_interactive_search():
    """Test Redfin extractor with interactive search."""
    # Create test property with all required fields
    test_property = Property(
        street="2353 W Tierra Buena Ln",
        city="Phoenix",
        state="AZ",
        zip_code="85023",
        full_address="2353 W Tierra Buena Ln, Phoenix, AZ 85023",
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=225.0,
        lot_sqft=8000,
        year_built=2000,
    )

    print("\n" + "=" * 80)
    print("Testing Redfin Interactive Search")
    print("=" * 80)
    print(f"Property: {test_property.full_address}")
    print("=" * 80 + "\n")

    # Initialize extractor
    extractor = RedfinExtractor()
    print("Extractor initialized. Starting extraction...\n")

    try:
        # Extract image URLs
        urls = await extractor.extract_image_urls(test_property)

        print("\n" + "=" * 80)
        print(f"Extraction Results: {len(urls)} images found")
        print("=" * 80)

        if urls:
            print("\nImage URLs:")
            for i, url in enumerate(urls, 1):
                print(f"{i:2d}. {url}")

            print("\n" + "=" * 80)
            print("[SUCCESS] Images extracted successfully!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("[WARNING] No images found")
            print("This could mean:")
            print("  1. Property not found on Redfin")
            print("  2. Interactive search failed to find/click results")
            print("  3. Bot detection triggered")
            print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("[ERROR] Extraction failed")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up resources
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(test_redfin_interactive_search())

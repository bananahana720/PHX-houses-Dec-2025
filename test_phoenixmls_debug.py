"""
Debug script for PhoenixMLS Search autocomplete navigation issue.

This script captures detailed debugging info for:
1. Autocomplete detection
2. MLS# extraction
3. Direct URL construction
4. Page navigation
5. Final page state
"""
import asyncio
import logging
import sys
from pathlib import Path

# Set DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    stream=sys.stdout
)

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.services.image_extraction.extractors.phoenix_mls_search import (
    PhoenixMLSSearchExtractor,
)


async def test_with_debug():
    """Test PhoenixMLS Search with detailed debug output."""

    # Create extractor
    extractor = PhoenixMLSSearchExtractor()

    # Create test property with all required fields
    prop = Property(
        street='5219 W EL CAMINITO Dr',
        city='Glendale',
        state='AZ',
        zip_code='85302',
        full_address='5219 W EL CAMINITO Dr, Glendale, AZ 85302',
        price='$500,000',
        price_num=500000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=250.0
    )

    print('\n' + '='*80)
    print('PHOENIXMLS SEARCH NAVIGATION DEBUG TEST')
    print('='*80)
    print(f'Test Property: {prop.full_address}')
    print('Expected MLS#: 6937912')
    print('='*80 + '\n')

    try:
        # Run extraction
        urls = await extractor.extract_image_urls(prop)

        print('\n' + '='*80)
        print('EXTRACTION RESULTS')
        print('='*80)
        print(f'Image URLs extracted: {len(urls)}')
        print(f'Metadata: {extractor.last_metadata}')

        if urls:
            print('\nFirst 5 URLs:')
            for i, url in enumerate(urls[:5]):
                print(f'  {i+1}. {url}')
        else:
            print('\n⚠️  NO IMAGES EXTRACTED')

            # Try to get more debug info from the extractor
            if hasattr(extractor, '_last_page_html'):
                page_html = extractor._last_page_html
                print(f'\nFinal page HTML length: {len(page_html)} chars')

                # Check for signs of listing page
                if 'SparkPlatform' in page_html or 'cdn.photos.sparkplatform.com' in page_html:
                    print('✓ Found SparkPlatform CDN references (listing page indicator)')
                else:
                    print('✗ NO SparkPlatform CDN references found')

                if 'gallery' in page_html.lower():
                    print('✓ Found gallery element')
                else:
                    print('✗ NO gallery element found')

                # Check for signs of search results page
                if 'autocomplete' in page_html.lower():
                    print('⚠️  Still on search page (autocomplete found in HTML)')

                if 'simple-search' in page_html.lower():
                    print('⚠️  Still on search page (simple-search found in HTML)')

                # Check for error messages
                if '404' in page_html or 'not found' in page_html.lower():
                    print('⚠️  404 or not found error detected')

                # Save page HTML for manual inspection
                debug_file = Path('debug_phoenixmls_final_page.html')
                debug_file.write_text(page_html, encoding='utf-8')
                print(f'\n📄 Final page HTML saved to: {debug_file.absolute()}')

        print('='*80 + '\n')

    except Exception as e:
        print('\n' + '='*80)
        print('EXTRACTION FAILED')
        print('='*80)
        print(f'Error: {type(e).__name__}: {e}')

        import traceback
        print('\nFull traceback:')
        traceback.print_exc()
        print('='*80 + '\n')


if __name__ == '__main__':
    asyncio.run(test_with_debug())

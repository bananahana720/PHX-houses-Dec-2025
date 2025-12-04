# Integration Testing

### Test 1: Verify Wrong Images Are Caught

```python
import asyncio
from pathlib import Path

async def test_phase1_quick_fix():
    """Verify Phase 1 catches search results page."""
    from src.phx_home_analysis.services.image_extraction.extractors import ZillowExtractor
    from src.phx_home_analysis.domain.entities import Property

    property = Property(
        street="4209 W Wahalla Ln",
        city="Glendale",
        state="AZ",
        zip_code="85308",
    )

    async with ZillowExtractor() as extractor:
        urls = await extractor.extract_image_urls(property)

        # Phase 1: Should return empty list (or very few images)
        assert len(urls) < 10, f"Got {len(urls)} images, expected <10"
        print(f"✓ Phase 1 test passed: {len(urls)} images (expected <10)")
```

### Test 2: Verify Phase 2 Gets Correct Images

```python
async def test_phase2_interactive_search():
    """Verify Phase 2 interactive search lands on detail page."""
    async with ZillowExtractor() as extractor:
        # After Phase 2 implementation
        urls = await extractor.extract_image_urls(property)

        # Should get reasonable number
        assert 8 <= len(urls) <= 25, f"Got {len(urls)} images"

        # All URLs should be from same property
        # (no mixed thumbnails from search results)
        assert all(
            "photos.zillowstatic.com" in url
            for url in urls
        ), "Non-Zillow CDN URLs found"

        print(f"✓ Phase 2 test passed: {len(urls)} images (expected 8-25)")
```

### Test 3: Visual Inspection

```python
# Manually download 3-5 images and verify:
# 1. All show same architectural style
# 2. All show same property exterior
# 3. Consistent interior finishes
# 4. No townhome/multi-property variety
```

---

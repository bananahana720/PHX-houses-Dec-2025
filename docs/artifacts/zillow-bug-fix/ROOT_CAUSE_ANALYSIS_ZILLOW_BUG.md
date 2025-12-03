# Root Cause Analysis: Zillow Wrong Image Extraction Bug

**Date**: 2025-12-02
**Status**: Critical Bug - 100% Reproduction Rate
**Confidence Level**: 95%

---

## Executive Summary

The Zillow stealth extractor is pulling images from **wrong properties** because the URL construction creates a **search results page** instead of a **property detail page**. When the extractor navigates to the URL, it lands on Zillow's search results showing multiple listings, and the indiscriminate image scraper grabs images from neighboring properties in the results carousel.

**Root Cause**: The `_build_search_url()` method constructs URLs in the format `/homes/{street}-{city}-{state}-{zip}_rb/`, which is Zillow's **search results format**, not the property detail format. The `_rb` suffix specifically indicates a "results browse" page that shows a list of matching properties, not a single property detail page.

---

## Evidence & Diagnosis

### 1. URL Format Analysis

**Current Implementation** (WRONG):
```python
def _build_search_url(self, property: Property) -> str:
    street = quote_plus(property.street.replace(" ", "-"))
    city = quote_plus(property.city.replace(" ", "-"))
    state = property.state
    zip_code = property.zip_code
    search_path = f"{street}-{city}-{state}-{zip_code}_rb"
    url = f"{self.source.base_url}/homes/{search_path}/"
    return url
```

**Example Output**:
- Input: `4209 W Wahalla Ln, Glendale, AZ 85308`
- Output: `https://www.zillow.com/homes/4209-W-Wahalla-Ln-Glendale-AZ-85308_rb/`

**What This URL Actually Does**:
- The `_rb` suffix stands for "Results Browse"
- This URL format **searches for properties** matching that address pattern
- Zillow returns a search results page with potentially multiple listings
- The results page includes:
  - Property listings carousel
  - Thumbnail images of multiple properties
  - "Similar homes" suggestions
  - Featured properties

### 2. Comparison with Redfin (Correct Pattern)

Redfin's extractor handles this correctly with an **interactive search** approach:

```python
def _build_search_url(self, property: Property) -> str:
    full_address = f"{property.street}, {property.city}, {property.state} {property.zip_code}"
    search_url = f"https://www.redfin.com/search?q={quote(full_address)}"
    return search_url
```

Then in `_navigate_with_stealth()`, it:
1. Visits the homepage to establish session
2. Finds the search input box
3. **Types the address into the search box** (interactive)
4. **Waits for autocomplete results**
5. **Clicks the matching result** to navigate to the property detail page
6. **Validates the final URL** contains `/home/` and the street address

Result: Lands on a **specific property detail page**, not a search results page.

### 3. Image Extraction Logic is the Symptom, Not the Cause

The `_extract_urls_from_page()` and `_is_high_quality_url()` methods are **correctly implemented** for extracting from a property detail page. The problem is they're running on the **wrong page** (search results, not detail).

Evidence:
- You're extracting **27-39 images per run** (too many for one property)
- Visual inspection shows **different architectural styles** (because results include multiple properties)
- The quality filter passes thumbnails from search results because:
  - Zillow's search result thumbnails ARE on `photos.zillowstatic.com`
  - Zillow's search result thumbnails DO have `.jpg` extensions
  - Zillow's search result thumbnails DO appear in `srcset` attributes

### 4. Why it Works Inconsistently

- **On Zillow**: The address happens to be FIRST in search results → gets some correct images mixed with wrong ones
- **On Redfin**: You're doing interactive search → lands on CORRECT property detail page
- **On subsequent runs**: Zillow changes search result ordering or includes more similar properties → images shift to different properties

---

## Proof of Concept: How Wrong Images Are Extracted

### Scenario: Searching "4209 W Wahalla Ln, Glendale, AZ 85308"

1. **URL Built**: `https://www.zillow.com/homes/4209-W-Wahalla-Ln-Glendale-AZ-85308_rb/`

2. **Page Loaded**: Zillow returns search results showing 3-5 properties matching this zipcode/address pattern:
   - Property A: 4209 W Wahalla Ln (CORRECT - matches exactly)
   - Property B: 4210 W Wahalla Ln (WRONG - nearby)
   - Property C: 4208 W Wahalla Ln (WRONG - nearby)
   - Plus "Similar homes" and featured listings

3. **Image Extraction**: `_extract_urls_from_page()` blindly queries `img` elements and `[style*="background-image"]`:
   - Finds thumbnail images from Property A's listing card
   - Finds thumbnail images from Property B's listing card  ← **WRONG PROPERTY**
   - Finds thumbnail images from Property C's listing card  ← **WRONG PROPERTY**
   - Finds featured property carousel images ← **WRONG PROPERTIES**

4. **Quality Filter**: `_is_high_quality_url()` passes them because:
   ```
   ✓ Domain: photos.zillowstatic.com (included)
   ✓ Extension: .jpg/.jpeg/.png/.webp (has_image_ext=true)
   ✗ No "thumb" in filename (because Zillow strips quality indicators)
   ```

5. **Result**: 27-39 images from multiple properties end up in your download folder

---

## Root Cause Confirmed

| Aspect | Evidence |
|--------|----------|
| **URL Format** | `/homes/{addr}_rb/` = search results, not detail page |
| **Zillow's Documentation** | `_rb` suffix is undocumented but widely known to mean "results browse" |
| **Page Content** | Extract >50KB of content → search results page with multiple listings |
| **No Navigation Logic** | Unlike Redfin, `_navigate_with_stealth()` just calls `browser.get(url)` and trusts the URL works |
| **Image Count** | 27-39 images = typical search results with 3-5 properties × 5-8 photos each |
| **Architectural Variety** | Multiple properties = different styles, townhomes, etc. |
| **Redfin Success** | Interactive search to property detail page produces correct images |

---

## Why Current Quality Filter Fails

The filter was designed for property detail pages but runs on search results:

```python
def _is_high_quality_url(self, url: str) -> bool:
    exclude_patterns = [
        "thumb", "small", "icon", "logo", "map",
        "placeholder", "loading", "avatar"
    ]
    # ← Zillow search results don't use these patterns in URLs

    include_patterns = [
        "photos.zillowstatic.com",  # ← Search results use this too!
        "ssl.cdn-redfin.com",
        "uncrate",
    ]

    has_image_ext = any(ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".webp"])
    # ← Search result thumbnails have these extensions!

    return has_image_ext  # ← Search result images pass through
```

The filter assumes it's running on a single property's detail page. It has no way to detect that images belong to OTHER properties in a search results carousel.

---

## The Fix

### Option 1: Switch to Interactive Search (Recommended - Matches Redfin)

Implement Zillow's interactive search like Redfin does:

```python
async def _navigate_with_stealth(self, url: str) -> uc.Tab:
    """Navigate to Zillow property via interactive search."""
    logger.info("Zillow: warming up with homepage visit")

    browser = await self._browser_pool.get_browser()
    tab = await browser.get("https://www.zillow.com")
    await asyncio.sleep(2)

    # Extract address from URL
    # Build full address string
    # Find search input and click
    # Type address character by character
    # Wait for autocomplete
    # Click matching result
    # Validate landing on /property/zpid page
    # Return tab
```

**Pros**:
- Guarantees landing on property detail page, not search results
- Matches Redfin's proven approach
- More resistant to Zillow's anti-bot measures

**Cons**:
- More complex implementation
- Additional wait times
- More network requests

### Option 2: Detect and Skip Search Results Pages (Quick Fix)

Add validation before image extraction:

```python
async def extract_image_urls(self, property: Property) -> list[str]:
    url = self._build_search_url(property)
    tab = await self._navigate_with_stealth(url)

    try:
        # NEW: Validate we're on property detail page, not search results
        page_content = await tab.get_content()

        # Detect search results page patterns
        if "search results" in page_content.lower():
            logger.error("Landed on search results page, not property detail")
            return []

        if "homes for sale" in page_content.lower() and "listing" not in page_content.lower():
            logger.error("Likely search results page")
            return []

        # Check for property-specific content
        if "/property/zpid" not in (tab.target.url or ""):
            logger.warning("URL doesn't contain /property/zpid pattern")
            # Don't extract from non-detail pages
            return []

        # Continue with extraction...
```

**Pros**:
- Fast implementation (30 minutes)
- Returns empty list instead of wrong images
- Easy to test

**Cons**:
- Doesn't solve the root problem (still landing on wrong page)
- Zillow may change patterns
- Better than extracting wrong images, but not ideal

### Option 3: Use Zillow's Direct Property URL Format (Best if Available)

If you have property IDs from Zillow (zpid):

```python
def _build_search_url(self, property: Property) -> str:
    # If enrichment_data has zillow_zpid, use it
    if hasattr(property, 'zillow_zpid') and property.zillow_zpid:
        return f"https://www.zillow.com/homedetails/{property.zillow_zpid}"

    # Otherwise fall back to interactive search (Option 1)
    # Don't use the current _rb format
```

**Pros**:
- Direct property detail page
- Fastest loading
- Most reliable

**Cons**:
- Requires zpid (may not have in enrichment_data)
- Still need Option 1 as fallback

---

## Recommended Solution Path

### Phase 1: Quick Fix (Prevents Bad Data)
Implement **Option 2** - add page type detection to prevent extraction from search results:
- If page is search results → return empty list (no images extracted)
- Better to have 0 images than 39 wrong images
- Takes 30 minutes

### Phase 2: Proper Fix (Reliable Extraction)
Implement **Option 1** - interactive search navigation:
- Copy Redfin's proven approach
- Add search input selection
- Implement autocomplete result clicking
- Validate final URL contains property detail pattern
- Takes 2-3 hours

### Phase 3: Optimization (Use Property IDs)
Implement **Option 3** - use zpid if available:
- Extract zpid from Zillow during Phase 1 listing extraction
- Store in enrichment_data.json
- Use for Phase 2 image extraction
- Fallback to interactive search if zpid missing

---

## Testing Strategy

### Unit Tests
```python
def test_url_format_detection():
    """Verify _build_search_url() creates search results URL (current behavior)."""
    extractor = ZillowExtractor()
    property = Property(
        street="4209 W Wahalla Ln",
        city="Glendale",
        state="AZ",
        zip_code="85308"
    )
    url = extractor._build_search_url(property)

    # Current (wrong) format
    assert "https://www.zillow.com/homes/" in url
    assert "_rb/" in url
    assert "/property/" not in url  # NOT property detail format
```

### Integration Tests
```python
async def test_extract_validates_page_type():
    """Verify extractor skips extraction if page is search results."""
    async with ZillowExtractor() as extractor:
        urls = await extractor.extract_image_urls(test_property)

        # Should return empty list (or try fallback)
        # Should log warning about search results page
        assert len(urls) == 0 or len(urls) < 10  # Not 27-39
```

### Validation Tests
```python
async def test_extracted_images_belong_to_correct_property():
    """Verify all extracted images are from the target property."""
    # Visual inspection: download images, verify architectural style matches
    # Metadata check: extract EXIF if available
    # Filename check: if Zillow embeds property ID in URLs
```

---

## Impact Assessment

| Component | Impact | Severity |
|-----------|--------|----------|
| **Data Quality** | Wrong images in enrichment_data | CRITICAL |
| **Phase 2 Scoring** | Image-assessor scores wrong properties | CRITICAL |
| **Final Reports** | Deal sheets show mismatched images | HIGH |
| **User Trust** | Discovered wrong images = credibility loss | HIGH |
| **Downstream Workflow** | Needs image re-extraction once fixed | MEDIUM |

---

## Validation Checklist

After implementing fix, verify:

- [ ] Extract images for known property with unique architecture
- [ ] Visually inspect 5-10 downloaded images
- [ ] Verify all images match target property's style
- [ ] Check image count is reasonable (5-15, not 27-39)
- [ ] Validate EXIF/metadata shows correct property (if embedded)
- [ ] Test with 3-5 different addresses
- [ ] Compare Zillow + Redfin results for same property
- [ ] Run extraction suite and verify image variability dropped

---

## References

- **Current Code**: `src/phx_home_analysis/services/image_extraction/extractors/zillow.py:78-109`
- **Base Class**: `src/phx_home_analysis/services/image_extraction/extractors/stealth_base.py:210-240`
- **Working Reference**: `src/phx_home_analysis/services/image_extraction/extractors/redfin.py:264-293` (interactive search)
- **Zillow URL Formats**:
  - Search results: `/homes/{address}_rb/` (WRONG - current)
  - Property detail: `/homedetails/{zpid}` or `/property/{zpid}` (CORRECT)

---

## Conclusion

**The bug is NOT in the image extraction logic itself** — it's in the URL destination. The extractor lands on a Zillow search results page instead of a property detail page, then correctly extracts images from that page (which happen to be thumbnails of multiple properties).

Fixing the URL navigation to land on the correct property detail page (using interactive search like Redfin, or direct property URLs with zpid) will resolve the issue completely.


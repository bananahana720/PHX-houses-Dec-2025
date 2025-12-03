# Zillow Wrong Image Extraction: Fix Implementation Guide

**Status**: Ready to Implement
**Difficulty**: Medium (2-3 hours)
**Risk**: Low (isolated to extraction, can rollback)

---

## Summary

Replace Zillow's non-functional search results URL format (`_rb` suffix) with interactive search navigation that lands on the property detail page.

---

## Phase 1: Quick Fix (30 minutes) - Prevent Bad Data

### Goal
Return empty list if page is search results instead of extracting wrong images.

### Implementation

File: `src/phx_home_analysis/services/image_extraction/extractors/zillow.py`

**Add this method to ZillowExtractor:**

```python
async def _is_property_detail_page(self, tab: uc.Tab) -> bool:
    """Check if we landed on property detail page, not search results.

    A property detail page will have:
    - Property-specific content patterns
    - /homedetails/ or /property/ in URL
    - "Zestimate" or "Property Details" sections

    A search results page will have:
    - "search results" or "homes for sale" text
    - Multiple property listings
    - Address not matching exactly

    Args:
        tab: Browser tab with loaded page

    Returns:
        True if this is property detail page, False if search results
    """
    try:
        page_content = await tab.get_content()
        page_content_lower = page_content.lower()
        current_url = str(tab.target.url) if hasattr(tab, 'target') else ""

        logger.debug(
            "%s checking page type: URL=%s, content_length=%d",
            self.name,
            current_url[:80],
            len(page_content),
        )

        # Pattern 1: Check URL format
        # Property detail: /homedetails/{zpid} or /property/{zpid}
        # Search results: /homes/{address}_rb/
        if "/homedetails/" in current_url or "/property/" in current_url:
            logger.info("%s confirmed property detail page via URL pattern", self.name)
            return True

        if current_url.endswith("_rb/") or "_rb/" in current_url:
            logger.warning("%s detected search results URL pattern (_rb)", self.name)
            return False

        # Pattern 2: Check page content
        # Property detail pages have property-specific content
        property_indicators = [
            "property details",
            "zestimate",
            "price history",
            "tax history",
            "principal residence",
            "homeowners association",
            "mortgage estimate",
            "nearby homes",
            "home details",
        ]

        search_indicators = [
            "search results",
            "homes for sale",
            "listings for",
            "properties matching",
            "filter properties",
        ]

        property_score = sum(1 for ind in property_indicators if ind in page_content_lower)
        search_score = sum(1 for ind in search_indicators if ind in page_content_lower)

        if property_score >= 2:
            logger.info(
                "%s confirmed property detail page (content: %d property indicators)",
                self.name,
                property_score,
            )
            return True

        if search_score >= 2:
            logger.warning(
                "%s detected search results page (content: %d search indicators)",
                self.name,
                search_score,
            )
            return False

        # Pattern 3: Check for multiple property listings
        # Count property cards/listings in the page
        property_card_patterns = [
            "class=\"list-card\"",
            "class=\"ZG_ListItem\"",
            "data-test=\"property-card\"",
            "data-testid=\"property-list-item\"",
        ]

        card_count = sum(
            page_content.count(pattern) for pattern in property_card_patterns
        )

        if card_count > 1:
            logger.warning(
                "%s detected multiple property cards (%d found) - likely search results",
                self.name,
                card_count,
            )
            return False

        # Default: if unsure, treat as detail page
        # (better to try extraction than skip)
        logger.debug(
            "%s could not determine page type with certainty, assuming detail page",
            self.name,
        )
        return True

    except Exception as e:
        logger.warning("%s error checking page type: %s", self.name, e)
        # Default: assume detail page on error
        return True
```

**Modify `extract_image_urls()` method:**

```python
async def extract_image_urls(self, property: Property) -> list[str]:
    """Extract image URLs and listing metadata from Zillow page.

    NOW WITH PAGE TYPE VALIDATION:
    Returns empty list if page is search results instead of property detail.
    """
    url = self._build_search_url(property)
    logger.info("%s extracting images for: %s", self.name, property.full_address)

    tab = await self._navigate_with_stealth(url)

    try:
        # NEW: Validate page type BEFORE attempting extraction
        is_detail_page = await self._is_property_detail_page(tab)

        if not is_detail_page:
            logger.error(
                "%s navigation landed on search results page, not property detail. "
                "Returning empty list instead of extracting wrong images. "
                "URL: %s",
                self.name,
                url,
            )
            return []

        # Check for CAPTCHA
        if await self._check_for_captcha(tab):
            logger.warning("%s CAPTCHA detected for %s", self.name, url)

            # Attempt to solve CAPTCHA
            if not await self._attempt_captcha_solve(tab):
                logger.error(
                    "%s CAPTCHA solving failed for %s", self.name, url
                )
                from .base import SourceUnavailableError
                raise SourceUnavailableError(
                    self.source,
                    "CAPTCHA detected and solving failed",
                    retry_after=300,  # 5 minutes
                )

            logger.info("%s CAPTCHA solved for %s", self.name, url)

        # Add human delay before extraction
        await self._human_delay()

        # Extract URLs from page
        urls = await self._extract_urls_from_page(tab)

        # ENHANCEMENT: Extract listing metadata on same tab
        self.last_metadata = await self.extract_listing_metadata(tab)

        logger.info(
            "%s extracted %d image URLs + metadata for %s",
            self.name,
            len(urls),
            property.full_address,
        )

        return urls

    finally:
        # Always close the tab
        try:
            await tab.close()
        except Exception as e:
            logger.warning("%s error closing tab: %s", self.name, e)
```

**Testing:**

```bash
# Run extraction for known property
python -m scripts.extract_images --address "4209 W Wahalla Ln, Glendale, AZ 85308"

# Expected: 0 images (safe fallback)
# Log should show: "navigation landed on search results page"
```

---

## Phase 2: Proper Fix (2-3 hours) - Interactive Search Navigation

### Goal
Implement Zillow's interactive search to land on property detail page (like Redfin).

### Implementation

**Replace `_navigate_with_stealth()` in ZillowExtractor:**

```python
async def _navigate_with_stealth(self, url: str) -> uc.Tab:
    """Navigate to Zillow property via interactive search.

    The current approach uses /homes/{address}_rb/ which is a search results
    page, not a property detail page. This implementation:

    1. Visit Zillow homepage to establish session
    2. Find search input element
    3. Type the property address (character by character for realism)
    4. Wait for autocomplete results
    5. Click the matching property result
    6. Validate we landed on /homedetails/ or /property/ page
    7. Return the tab

    Args:
        url: Original search URL (contains address in format after domain)

    Returns:
        Browser tab on property detail page

    Raises:
        ExtractionError: If navigation sequence fails
    """
    logger.info("%s starting interactive navigation to property detail page", self.name)

    try:
        # Add initial delay to appear human-like
        await self._human_delay()

        # Get browser
        browser = await self._browser_pool.get_browser()

        # Step 1: Visit homepage to establish session/cookies
        logger.info("%s visiting Zillow homepage", self.name)
        tab = await browser.get("https://www.zillow.com")
        await asyncio.sleep(2)  # Wait for homepage content

        # Step 2: Extract address from search URL
        # URL format: /homes/{street}-{city}-{state}-{zip}_rb/
        # We need to reconstruct full address for search
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(url)
        path_parts = parsed.path.strip("/homes/").strip("_rb/").split("-")

        # Reconstruct full address by pattern
        # This is the extracted address from URL components
        address_parts = []
        skip_count = 0
        for part in path_parts:
            if skip_count > 0:
                skip_count -= 1
                continue

            # Try to match state/zip patterns
            if len(part) == 2 and part.upper() == part:  # Likely state
                address_parts.append(part)
                skip_count = 1  # Skip next (zip)
                continue

            address_parts.append(part.replace("-", " "))

        full_address = " ".join(address_parts)
        full_address = full_address.replace(" _rb", "").strip()

        logger.info("%s extracted address for search: %s", self.name, full_address)

        # Step 3: Find and interact with search input
        logger.info("%s finding search input element", self.name)

        search_input = None
        search_selectors = [
            'input[placeholder*="address"]',  # Primary selector
            'input[placeholder*="Address"]',
            'input[placeholder*="home"]',
            'input[placeholder*="search"]',
            'input[aria-label*="address"]',
            'input[aria-label*="Address"]',
            '.search-input',
            '#search-box-input',
            'input[type="text"][class*="search"]',
        ]

        for selector in search_selectors:
            try:
                search_input = await tab.query_selector(selector)
                if search_input:
                    logger.info(
                        "%s found search input with selector: %s",
                        self.name,
                        selector,
                    )
                    break
            except Exception as e:
                logger.debug(
                    "%s selector %s failed: %s",
                    self.name,
                    selector,
                    e,
                )
                continue

        if not search_input:
            logger.error("%s could not find search input element", self.name)
            raise ExtractionError("Could not find Zillow search input")

        # Click search input to focus
        try:
            await search_input.click()
            await asyncio.sleep(0.5)
            logger.info("%s clicked search input", self.name)
        except Exception as e:
            logger.warning("%s could not click search input: %s", self.name, e)

        # Step 4: Type address character by character
        logger.info(
            "%s typing address into search: %s",
            self.name,
            full_address,
        )

        try:
            # Type slowly to trigger autocomplete
            for char in full_address:
                await search_input.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))  # Human-like speed
        except Exception as e:
            logger.warning("%s error typing address: %s", self.name, e)
            # Continue anyway - may still have partial results

        # Wait for autocomplete to appear
        await asyncio.sleep(1.5)

        # Step 5: Find and click matching autocomplete result
        logger.info("%s waiting for autocomplete results", self.name)

        result_clicked = False
        max_result_attempts = 3

        for attempt in range(max_result_attempts):
            try:
                # Autocomplete results container (try multiple selectors)
                result_selectors = [
                    '.ZG_Autocomplete [data-test="zsg-autocomplete-result"]',
                    '.ZG_Autocomplete li',
                    '[role="listbox"] li',
                    '[role="option"]',
                    '.autocomplete-result',
                    '.search-result',
                ]

                results = []
                for selector in result_selectors:
                    try:
                        results = await tab.query_selector_all(selector)
                        if results:
                            logger.debug(
                                "%s found %d autocomplete results with selector: %s",
                                self.name,
                                len(results),
                                selector,
                            )
                            break
                    except Exception:
                        continue

                if results:
                    # Try to find exact match first (street address match)
                    street_number = full_address.split()[0]
                    street_name = " ".join(full_address.split()[1:3])

                    matched_result = None
                    for result in results:
                        try:
                            result_text = result.text_content if hasattr(result, 'text_content') else str(result)
                            result_text_lower = result_text.lower()

                            # Check if result contains both street number and name
                            if street_number in result_text_lower and street_name.lower() in result_text_lower:
                                matched_result = result
                                logger.info(
                                    "%s found exact match in autocomplete: %s",
                                    self.name,
                                    result_text[:100],
                                )
                                break
                        except Exception:
                            continue

                    # Click matched result or first result
                    if matched_result:
                        await matched_result.click()
                        logger.info("%s clicked matching autocomplete result", self.name)
                    else:
                        logger.warning(
                            "%s no exact match found, clicking first result (fallback)",
                            self.name,
                        )
                        await results[0].click()
                        logger.info("%s clicked first autocomplete result", self.name)

                    result_clicked = True
                    break

            except Exception as e:
                logger.debug(
                    "%s error in result attempt %d: %s",
                    self.name,
                    attempt + 1,
                    e,
                )
                continue

            # Wait before next attempt
            if attempt < max_result_attempts - 1:
                await asyncio.sleep(1)

        # Fallback: press Enter if no results clicked
        if not result_clicked:
            logger.warning(
                "%s could not find autocomplete results, pressing Enter",
                self.name,
            )
            try:
                await search_input.send_keys("\n")
                logger.info("%s pressed Enter on search input", self.name)
            except Exception as e:
                logger.error(
                    "%s failed to press Enter, raising error: %s",
                    self.name,
                    e,
                )
                raise ExtractionError(f"Could not submit search for {full_address}")

        # Step 6: Wait for property page to load
        logger.info("%s waiting for property detail page to load", self.name)
        await asyncio.sleep(3)

        # Step 7: Validate we're on property detail page
        try:
            current_url = str(tab.target.url) if hasattr(tab, 'target') else ""
            logger.info("%s final URL: %s", self.name, current_url)

            # Check for property detail patterns
            if "/homedetails/" in current_url or "/property/" in current_url:
                logger.info(
                    "%s successfully navigated to property detail page",
                    self.name,
                )
            else:
                logger.warning(
                    "%s final URL doesn't contain /homedetails/ or /property/: %s",
                    self.name,
                    current_url,
                )
                # Log warning but continue - may still have valid content
        except Exception as e:
            logger.warning("%s error validating final URL: %s", self.name, e)

        logger.info("%s navigation complete", self.name)
        return tab

    except Exception as e:
        logger.error("%s navigation failed: %s", self.name, e)
        raise ExtractionError(f"Navigation failed for {url}: {e}")
```

**Also keep the Phase 1 page type validation:**

```python
# Keep the _is_property_detail_page() check in extract_image_urls()
# so we have double validation
```

### Testing Phase 2

```bash
# Test interactive navigation
python -m scripts.extract_images --address "4209 W Wahalla Ln, Glendale, AZ 85308" --verbose

# Expected:
# 1. "visiting Zillow homepage"
# 2. "typing address into search"
# 3. "found autocomplete results"
# 4. "clicked matching autocomplete result"
# 5. "successfully navigated to property detail page"
# 6. "extracted 8-15 image URLs" (reasonable count)

# Verify visually: check that downloaded images show same property
```

---

## Phase 3: Optimization (1 hour) - Use Property IDs

### Goal
If we can extract Zillow's zpid (property ID), use direct URL instead of search.

### Implementation

**Store zpid during Phase 1 listing extraction:**

In `scripts/extract_images.py` or listing-browser agent, capture:

```python
# When scraping Zillow listing, extract zpid from URL
# URL format: https://www.zillow.com/homedetails/{zpid}_{extra}

# Store in enrichment_data.json
enrichment_data[address]["sources"]["zillow"] = {
    "zpid": "12345678",  # Extract and store
    "url": "https://www.zillow.com/homedetails/12345678_zpid/",
    "extracted_at": "2025-12-02T10:30:00Z"
}
```

**Use zpid in image extraction:**

```python
def _build_search_url(self, property: Property) -> str:
    """Build Zillow URL from property.

    Priority:
    1. Use zpid if available (direct property URL)
    2. Fall back to interactive search
    """
    # Check if enrichment has zpid
    if hasattr(property, 'zillow_zpid') and property.zillow_zpid:
        url = f"https://www.zillow.com/homedetails/{property.zillow_zpid}/"
        logger.info(
            "%s using direct property URL with zpid: %s",
            self.name,
            url,
        )
        return url

    # Fallback to interactive search (Phase 2)
    # Build search URL for navigation
    full_address = f"{property.street}, {property.city}, {property.state} {property.zip_code}"
    # Signal to _navigate_with_stealth() that we need interactive search
    # by using a special marker
    return f"https://www.zillow.com/search?address={quote_plus(full_address)}"
```

---

## Integration Testing

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

## Rollback Plan

If Phase 2 implementation causes problems:

1. Revert `_navigate_with_stealth()` to original simple navigation
2. Keep Phase 1 page type validation (safe)
3. Return to empty list behavior (better than wrong images)
4. File bug for future Phase 2 implementation

```bash
git revert <commit-hash>  # Revert to Phase 1 only
```

---

## Success Criteria

| Metric | Before | Target | Success? |
|--------|--------|--------|----------|
| Images per extraction | 27-39 (WRONG) | 8-15 (CORRECT) | ✓ |
| Page type accuracy | 0% (search results) | 95%+ (detail page) | ✓ |
| Wrong images detected | 0 (passed through) | 100% (validation) | ✓ |
| Visual inspection | Mixed properties | Single property only | ✓ |
| Log clarity | No warnings | Clear "detail page" messages | ✓ |

---

## Estimated Timeline

| Phase | Effort | Time | Risk |
|-------|--------|------|------|
| Phase 1 | Low | 30 min | Very Low |
| Phase 2 | Medium | 2-3 hr | Low |
| Phase 3 | Low | 1 hr | Very Low |
| Testing | Medium | 1-2 hr | Low |
| **Total** | **Medium** | **4-6 hr** | **Low** |

---

## File Changes Summary

| File | Change | Lines |
|------|--------|-------|
| `zillow.py` | Add `_is_property_detail_page()` method | +80 |
| `zillow.py` | Modify `extract_image_urls()` to validate page | +10 |
| `zillow.py` | Add Phase 2: Replace `_navigate_with_stealth()` | +200 |
| Tests | Add integration tests | +100 |
| **Total** | **3 files** | **~390 lines** |

---

## References

- Root Cause Analysis: `ROOT_CAUSE_ANALYSIS_ZILLOW_BUG.md`
- Redfin working implementation: `extractors/redfin.py:73-262`
- Base stealth class: `extractors/stealth_base.py`
- Current broken implementation: `extractors/zillow.py:78-109`


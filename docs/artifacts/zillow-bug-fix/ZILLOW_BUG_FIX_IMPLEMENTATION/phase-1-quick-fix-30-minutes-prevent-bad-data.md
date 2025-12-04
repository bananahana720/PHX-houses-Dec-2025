# Phase 1: Quick Fix (30 minutes) - Prevent Bad Data

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

# Phase 2: Proper Fix (2-3 hours) - Interactive Search Navigation

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

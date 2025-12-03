# Zillow Bug Fix - Line-by-Line Reference

## File: `src/phx_home_analysis/services/image_extraction/extractors/zillow.py`

### FIX #1: Enhanced `_is_property_detail_page()` Method

#### FIX #1C: Strict URL Validation (Early Return)
- **Lines 1253-1261**: Check for `_rb` suffix (search results marker)
  ```python
  # FIX #1C: Strict URL validation - must have /homedetails/ AND _zpid, reject _rb
  url_lower = current_url.lower()
  if "_rb/" in url_lower or "_rb?" in url_lower:
      logger.warning(...)
      return False
  ```

#### FIX #1C: Require /homedetails/ Path
- **Lines 1268-1276**: In fast-path validation, require /homedetails/
  ```python
  if detail_url or canonical_detail:
      # Additional validation: must contain /homedetails/ path
      if "/homedetails/" not in url_lower:
          logger.warning(...)
          return False
      logger.info(...)
      return True
  ```

#### FIX #1A: zpid Counting Detection
- **Lines 1313-1321**: Reject if zpid count > 15
  ```python
  # FIX #1A: zpid counting - detail pages have 1-5 zpid refs, search results have 10+
  zpid_count = content_lower.count("zpid")
  if zpid_count > 15:
      logger.warning(...)
      return False
  ```

#### FIX #1B: Property Card Counting
- **Lines 1323-1332**: Reject if card_count > 3
  ```python
  # FIX #1B: Property card counting - more than 3 property cards = search results
  card_patterns = ["property-card", "list-card", "search-card", "styledpropertycard"]
  card_count = sum(content_lower.count(p) for p in card_patterns)
  if card_count > 3:
      logger.warning(...)
      return False
  ```

#### Enhanced Logging
- **Line 1355**: Log all diagnostic counts
  ```python
  logger.warning(
      "%s Could not confirm property detail page (indicators: %d, zpid_count: %d, card_count: %d, URL: %s)",
      ...
  )
  ```

---

### FIX #5: New Helper Method `_score_address_match()`

- **Lines 1368-1414**: New method (47 lines)
  ```python
  def _score_address_match(self, target: str, result_text: str) -> float:
      """FIX #5: Score how well autocomplete result matches target address (0.0-1.0)."""
      # Street number: 0.5 points (must match)
      # Street name: 0.3 points (proportional)
      # City: 0.2 points (bonus)
      # Returns: 0.0-1.0 score
  ```

**Used by**: Autocomplete selection (FIX #5 integration at lines 1629-1644)

---

### FIX #2: Enhanced Search Input Selectors

- **Lines 1440-1458**: Expanded selector list (11 selectors)
  ```python
  # FIX #2: Enhanced search input selectors (2025-compatible list)
  search_selectors = [
      # Primary: data-testid (most stable)
      'input[data-testid="search-bar-input"]',
      'input[id="search-box-input"]',
      # Secondary: ARIA attributes
      'input[aria-label*="search"]',
      'input[aria-label*="Search"]',
      # Tertiary: placeholder text
      'input[placeholder*="Enter an address"]',
      'input[placeholder*="Address"]',
      'input[placeholder*="Search"]',
      # Fallback: class-based
      'input[class*="SearchBox"]',
      'input[class*="search-input"]',
      'header input[type="text"]',
      'nav input[type="text"]',
  ]
  ```

**Usage**: Lines 1461-1526 (existing selector retry loop, unchanged)

---

### FIX #3: Enhanced Autocomplete Selectors

- **Lines 1558-1574**: Expanded selector list (10 selectors)
  ```python
  # FIX #3: Enhanced autocomplete selectors (address-specific patterns)
  autocomplete_selectors = [
      # Primary: data-testid (most stable)
      '[data-testid="search-result-list"] [data-testid="search-result"]',
      '[data-testid="address-suggestion"]',
      # Secondary: role-based
      '[role="listbox"] [role="option"]',
      '[role="option"][data-address]',
      'li[role="option"]',
      # Tertiary: class-based
      '.search-suggestions-list li',
      'ul[data-testid="search-results"] li',
      'li[data-type="address"]',
      # Fallback
      '.autocomplete-item',
      '.suggestion-item a',
  ]
  ```

---

### FIX #5: Address Matching Integration

- **Lines 1624-1668**: Replace simple selection with smart scoring
  ```python
  # FIX #5: Score address matches and click best match with score >= 0.5
  best_suggestion = None
  best_score = 0.0

  for element in elements:
      try:
          result_text = await element.text_content()
          if result_text:
              score = self._score_address_match(full_address, result_text)
              if score > best_score:
                  best_score = score
                  best_suggestion = element
                  if score >= 0.8:  # Excellent match, can stop early
                      break
      except Exception:
          continue

  if best_suggestion and best_score >= 0.5:
      suggestion = best_suggestion
      logger.info(...)
  elif elements:
      # Fallback: use first element if no good scoring match
      suggestion = elements[0]
      logger.info(...)
  ```

**Logic**:
- Lines 1630-1644: Score each suggestion
- Lines 1646-1661: Accept >= 0.5, fallback to first if no match
- Line 1668: Click the selected suggestion

---

### FIX #4: Safety Check in `extract_image_urls()`

- **Lines 1747-1759**: After URL extraction, re-validate if count > 25
  ```python
  # FIX #4: Safety check - too many URLs suggests we're on search results
  if len(urls) > 25:
      logger.warning(...)
      if not await self._is_property_detail_page(tab):
          logger.error(...)
          return []
  ```

**Placement**: After line 1745 (`urls = await self._extract_urls_from_page(...)`)

---

## Summary by Line Range

| FIX | Component | Lines | Type | Length |
|-----|-----------|-------|------|--------|
| #1C | URL validation (early) | 1253-1261 | Check | 9 |
| #1C | URL validation (fast-path) | 1268-1276 | Check | 9 |
| #1A | zpid counting | 1313-1321 | Check | 9 |
| #1B | card counting | 1323-1332 | Check | 10 |
| Log | Enhanced logging | 1355 | Log | 1 |
| #5 | New method signature | 1368-1380 | Method | 13 |
| #5 | Street number scoring | 1390-1396 | Logic | 7 |
| #5 | Street name scoring | 1398-1406 | Logic | 9 |
| #5 | City scoring | 1408-1413 | Logic | 6 |
| #2 | Search selectors | 1440-1458 | Selectors | 19 |
| #3 | Autocomplete selectors | 1558-1574 | Selectors | 17 |
| #5 | Address scoring loop | 1624-1644 | Logic | 21 |
| #5 | Accept/fallback logic | 1646-1662 | Logic | 17 |
| #4 | Safety check | 1747-1759 | Check | 13 |

**Total New Lines**: 147 (47 method + 100 integration)

---

## Key Line Numbers to Remember

| Landmark | Line(s) | Purpose |
|----------|---------|---------|
| `_is_property_detail_page()` start | 1229 | Enhanced validation method |
| URL _rb check | 1255 | First defense layer |
| zpid_count check | 1315 | Second defense layer |
| card_count check | 1325 | Third defense layer |
| `_score_address_match()` | 1368-1414 | New helper method |
| Search selectors | 1442-1457 | 11 patterns (vs 4 old) |
| Autocomplete selectors | 1560-1573 | 10 patterns (vs 8 old) |
| Autocomplete scoring | 1629-1644 | Score each suggestion |
| extract_image_urls() | 1697 | Main extraction method |
| URL safety check | 1748-1759 | Final gate before return |

---

## Testing Line Numbers

To test individual fixes, focus on these lines:

**Test FIX #1**:
- Set breakpoint at 1255 for URL validation
- Set breakpoint at 1315 for zpid counting
- Set breakpoint at 1325 for card counting

**Test FIX #2**:
- Verify `search_selectors` list at 1442-1457 has 11 items
- Debug selector matching at 1463-1480

**Test FIX #3**:
- Verify `autocomplete_selectors` list at 1560-1573 has 10 items
- Debug element selection at 1577-1605

**Test FIX #4**:
- Set breakpoint at 1748
- Monitor for log message about URL count

**Test FIX #5**:
- Call `_score_address_match()` directly (line 1368)
- Set breakpoint at 1637 to debug scoring
- Verify best_suggestion selection at 1646

---

## Git Blame/Show Commands

To see the exact changes for each fix:

```bash
# Show all FIX lines
git show HEAD:src/phx_home_analysis/services/image_extraction/extractors/zillow.py | grep -n "FIX #"

# Show FIX #1 changes
git diff HEAD~1 HEAD src/phx_home_analysis/services/image_extraction/extractors/zillow.py | grep -A5 "FIX #1"

# Show full file around FIX
git show HEAD:src/phx_home_analysis/services/image_extraction/extractors/zillow.py | sed -n '1253,1365p'
```

---

## Navigation in Editor

**VS Code Quick Navigation**:
- `Ctrl+G` → Go to line
- `Ctrl+F` → Search for "FIX #"
- `Ctrl+Shift+F` → Search across files

**Find specific fixes**:
- FIX #1A: `Ctrl+G` → 1315
- FIX #1B: `Ctrl+G` → 1325
- FIX #1C: `Ctrl+G` → 1255 and 1270
- FIX #2: `Ctrl+G` → 1442
- FIX #3: `Ctrl+G` → 1560
- FIX #4: `Ctrl+G` → 1748
- FIX #5: `Ctrl+G` → 1368 (method) or 1629 (integration)


# Debug Notes: PhoenixMLS Search Autocomplete & Performance Fixes

**Date:** 2025-12-06
**Session:** Debug Session 2 (Evening)
**Duration:** ~3 hours
**Property Tested:** 5219 W EL CAMINITO Dr, Glendale, AZ 85302
**Related Spec:** tech-spec-phoenixmls-search-nodriver.md

---

## Session Overview

**Goal:** Fix autocomplete detection and eliminate 90+ second hangs
**Results:** Performance improved 5x (77s → 16s), autocomplete working, but 0 images extracted
**Status:** ⚠️ PARTIAL SUCCESS (autocomplete fixed, navigation still blocked)

---

## Problems Identified

### Problem 1: Autocomplete Selector Mismatch
**Symptom:** 77-second timeout waiting for autocomplete results that never appeared
**Root Cause:** Using `li[class*='result']` selector for standard `<ul>/<li>` autocomplete, but PhoenixMLS uses ARIA tree pattern with `role='treeitem'`
**Evidence:** Live HTML inspection showed:
```html
<div role="tree">
  <div role="treeitem" aria-label="5219 W EL CAMINITO Drive...">
    5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)
  </div>
</div>
```

### Problem 2: No Timeout Protection
**Symptom:** 90+ second hangs when autocomplete never appeared
**Root Cause:** Infinite wait loop with no hard timeout
**Impact:** Made debugging extremely slow and painful

### Problem 3: Text Extraction Failures
**Symptom:** Found `role='treeitem'` elements but couldn't extract text content
**Root Cause:** Multiple nodriver element access patterns needed (`.text`, `.text_all`, `.get_attribute()`, etc.)
**Impact:** Autocomplete found but scoring failed, preventing click

---

## Solutions Implemented

### Fix 1: ARIA Tree Selector (Lines 254-263)
**Change:** Replaced `li[class*='result']` with `[role='treeitem']`
```python
# OLD (failed)
autocomplete_items = await tab.select_all("li[class*='result']")

# NEW (works)
autocomplete_items = await tab.select_all("[role='treeitem']")
```
**File:** `phoenix_mls_search.py:254-263`
**Impact:** Autocomplete detection now succeeds in <1 second

### Fix 2: 10-Second Hard Timeout (Lines 296-305)
**Change:** Added `asyncio.wait_for()` wrapper around autocomplete wait
```python
try:
    autocomplete_items = await asyncio.wait_for(
        tab.select_all("[role='treeitem']"),
        timeout=10.0
    )
except asyncio.TimeoutError:
    logger.warning("Autocomplete timed out after 10s")
    return []
```
**File:** `phoenix_mls_search.py:296-305`
**Impact:** Worst-case execution time capped at 16s (down from 90s+)

### Fix 3: 5-Strategy Text Extraction Fallback (Lines 318-377)
**Change:** Implemented comprehensive element text extraction with fallbacks
```python
async def _extract_element_text(self, element) -> str:
    """Extract text from element using multiple strategies."""
    # Strategy 1: Direct .text property
    # Strategy 2: .text_all property (includes children)
    # Strategy 3: aria-label attribute
    # Strategy 4: textContent JavaScript property
    # Strategy 5: innerText JavaScript property
```
**File:** `phoenix_mls_search.py:318-377`
**Impact:** Text extraction now succeeds with score 0.85 for MLS-containing options

### Fix 4: MLS# Pattern Priority Boost (Lines 489-542)
**Change:** Added +15% score bonus for autocomplete options containing "(MLS #)"
```python
# Boost score for options with explicit MLS numbers
if "(MLS #)" in option_text or "MLS#" in option_text:
    score += 0.15
```
**File:** `phoenix_mls_search.py:489-542`
**Impact:** Ensures MLS-tagged options rank higher than generic address matches

---

## Test Results (Property: 5219 W EL CAMINITO Dr)

### Before Fixes (Debug Session 1)
- Duration: 77 seconds
- Autocomplete detection: FAILED (timeout)
- Images extracted: 0
- Cause: Selector mismatch + no timeout protection

### After Fixes (Debug Session 2)
- Duration: 16.2 seconds (5x improvement)
- Autocomplete detection: ✅ SUCCESS
- Autocomplete scoring: 0.85 for both top options
- Autocomplete click: ✅ SUCCESS
- Images extracted: ❌ 0 (NEW PROBLEM)

**Console Output:**
```
Phoenix MLS Search result 1 scored 0.85: 5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)
Phoenix MLS Search result 2 scored 0.85: 5219 W El Caminito Drive, Glendale, AZ 85302 / 4719507 (MLS #)
Phoenix MLS Search clicking autocomplete match with score 0.85
Phoenix MLS Search search submitted successfully
Phoenix MLS Search extracted 0 image URLs  ← CRITICAL ISSUE
```

---

## Remaining Critical Issue

### Zero Images Extracted
**Status:** BLOCKED
**Impact:** Complete blocker for PhoenixMLS reliability pivot
**Analysis:**
1. Autocomplete click succeeds
2. Search submission succeeds
3. But page does NOT navigate to listing detail page
4. Therefore, SparkPlatform image gallery selectors find nothing

**Next Debug Steps:**
1. Capture HTML after autocomplete click to see current page state
2. Check if results page has thumbnail images we can extract directly
3. Verify if "View Details" button click is needed after autocomplete
4. Investigate if autocomplete click should trigger navigation (may need manual URL construction)

---

## Performance Analysis

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total duration | 77s | 16s | -79% |
| Autocomplete wait | 77s | <1s | -99% |
| Worst-case timeout | None | 10s | Capped |
| Success rate | 0% | 0% | No change (different blocker) |

---

## Code Changes Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `phoenix_mls_search.py:254-263` | 10 | ARIA tree selector fix |
| `phoenix_mls_search.py:296-305` | 10 | 10-second timeout protection |
| `phoenix_mls_search.py:318-377` | 60 | 5-strategy text extraction |
| `phoenix_mls_search.py:489-542` | 54 | MLS# priority scoring |

---

## Lessons Learned

1. **Live HTML inspection critical:** Static analysis of web forms is unreliable - must inspect actual DOM structure
2. **ARIA patterns vary:** Autocomplete isn't always `<ul>/<li>` - check for `role='tree'`, `role='listbox'`, etc.
3. **Timeout protection mandatory:** Never wait indefinitely for UI elements in stealth browser automation
4. **Text extraction is fragile:** nodriver elements require multiple access strategies (property vs attribute vs JS eval)
5. **Performance wins don't equal functionality:** 5x speedup is great, but still 0% success rate on core objective

---

## Next Session Priorities

1. **HIGH:** Debug navigation after autocomplete click
2. **HIGH:** Verify listing detail page URL construction
3. **MEDIUM:** Check if results page has extractable images
4. **LOW:** Refine timeout values based on network conditions

---

## References

- **Parent spec:** `tech-spec-phoenixmls-search-nodriver.md`
- **Source code:** `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls_search.py`
- **Test file:** `tests/unit/services/image_extraction/test_phoenix_mls_search_navigation.py`
- **Related extractors:** `zillow.py`, `redfin.py` (fallback chain)

---

**END OF DEBUG NOTES**

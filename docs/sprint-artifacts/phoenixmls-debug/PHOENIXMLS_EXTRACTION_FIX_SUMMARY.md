# PhoenixMLS Extraction Gap - Quick Fix Summary

## Problem
- **Expected:** 43 gallery images
- **Actual:** 7 unique images extracted
- **Gap:** 81% of images missing

## Root Cause
Current implementation extracts **thumbnail URLs** (`-t.jpg`) from static HTML instead of **full-size URLs** (`-o.jpg`).

## Evidence
| Metric | Value |
|--------|-------|
| Thumbnails available on page | 43 |
| Unique IDs in thumbnails | 43 |
| Current unique IDs extracted | 7 |
| URL pattern found | 45 SparkPlatform images |

## URL Pattern Discovery

### Current (Wrong)
```
Input:  cdn.photos.sparkplatform.com/az/20251023213131892099000000-t.jpg
Size:   65x42px (thumbnail)
```

### Required (Correct)
```
Output: cdn.photos.sparkplatform.com/az/20251023213131892099000000-o.jpg
Size:   3000x2000px (full property photo)
```

## Solution

**Transform:** Replace `-t.jpg` with `-o.jpg` in all thumbnail URLs

```python
def convert_to_full_size(thumbnail_url: str) -> str:
    return thumbnail_url.replace('-t.jpg', '-o.jpg')

# Example:
input  = "cdn.photos.sparkplatform.com/az/20251023213131892099000000-t.jpg"
output = "cdn.photos.sparkplatform.com/az/20251023213131892099000000-o.jpg"
```

## Implementation Location

**File:** `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py`

**Method:** `_parse_image_gallery()` (lines 293-378)

**Changes Needed:**
1. Add regex pattern for `-t.jpg` URLs
2. Transform to `-o.jpg`
3. Deduplicate by 20-digit ID
4. Return full-size URLs

## Expected Outcome

| Before | After |
|--------|-------|
| 7 unique images | 43 unique images |
| 65x42px (tiny) | 3000x2000px (full) |
| Thumbnail quality | Production quality |

## Verification

Test on: `5219 W El Caminito Dr, Glendale, AZ 85302`
- Live page has 43 images visible
- Extraction should return 43 URLs
- All URLs should be accessible
- Images should be high-quality (3000x2000px)

## Files Modified
- [ ] `phoenix_mls.py` - `_parse_image_gallery()` method
- [ ] Add unit tests for URL transformation
- [ ] Update extraction documentation

## Implementation Effort
- **Complexity:** LOW (simple string replacement + dedup)
- **Risk:** VERY LOW (adds functionality, doesn't break existing)
- **Testing:** 30 minutes
- **Deployment:** Safe to deploy immediately after testing


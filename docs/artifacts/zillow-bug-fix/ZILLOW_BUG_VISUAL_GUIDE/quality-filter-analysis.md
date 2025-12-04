# Quality Filter Analysis

### Why Current Filter Fails on Search Results

```python
def _is_high_quality_url(self, url: str) -> bool:
    # Exclude patterns
    exclude_patterns = ["thumb", "small", "icon", "logo", "map",
                       "placeholder", "loading", "avatar"]

    for pattern in exclude_patterns:
        if pattern in url_lower:
            return False  # Exclude these

    # Include patterns
    include_patterns = ["photos.zillowstatic.com", "ssl.cdn-redfin.com"]

    for pattern in include_patterns:
        if pattern in url_lower:
            return True  # Include these

    # Default: accept if has image extension
    has_image_ext = any(ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".webp"])
    return has_image_ext
```

**Why it passes search result images:**

| Check | Search Result Thumbnail | Reason |
|-------|------------------------|--------|
| Exclude "thumb"? | NO - not in filename | Zillow URL: `photos.zillowstatic.com/...abc123.jpg` |
| Include "photos.zillowstatic.com"? | YES ✓ | **PASSES** - search results use this CDN too! |
| Has .jpg extension? | YES ✓ | **PASSES** - thumbnails have extensions |
| Result | ✓ PASSES FILTER | Images from search results slip through |

**What it should do:**

The filter needs context: "Am I on a property detail page or search results page?"

Without context, it can't distinguish:
- Property gallery image (want) vs. Search result thumbnail (reject)
- Both use same CDN: `photos.zillowstatic.com`
- Both have same file extensions: `.jpg`

This is why Phase 1 adds `_is_property_detail_page()` validation BEFORE extraction.

---

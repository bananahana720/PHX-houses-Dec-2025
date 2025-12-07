# ImageProcessor Integration - Implementation Summary

## Task Completed
Successfully wired `ImageProcessor` into the NEW orchestrator path (`extract_for_property_with_tracking` → `_extract_for_property_locked`).

## Files Modified
- `src/phx_home_analysis/services/image_extraction/orchestrator.py`

## Changes Made

### 1. Added Import (Line 49)
```python
from .image_processor import ImageProcessor
```

### 2. Instantiated ImageProcessor in `__init__` (Lines 313-317)
```python
self.image_processor = ImageProcessor(
    base_dir=self.processed_dir,
    deduplicator=self.deduplicator,
    standardizer=self.standardizer,
)
```

### 3. Replaced Manual Processing with ImageProcessor Call (Lines 1304-1329)
**Before:** Manual perceptual hashing, duplicate checking, standardization, and file I/O

**After:**
```python
# Process image using ImageProcessor
processed_image, error = await self.image_processor.process_image(
    image_data=image_data,
    source_url=url,
    property_hash=property_hash,
    run_id=self.run_id,
)

if error:
    # Processing failed
    logger.warning(f"Failed to process {url}: {error}")
    source_stats.images_failed += 1
    result.failed_downloads += 1
    prop_changes.errors += 1
    prop_changes.error_messages.append(f"Processing failed: {url}")
    self._stats_accumulator["extraction_errors"] += 1
    continue

if not processed_image:
    # Shouldn't happen, but handle gracefully
    logger.error(f"ImageProcessor returned None for {url}")
    source_stats.images_failed += 1
    result.failed_downloads += 1
    prop_changes.errors += 1
    self._stats_accumulator["extraction_errors"] += 1
    continue
```

### 4. Updated Duplicate Handling (Lines 1331-1347)
```python
# Handle duplicates (processed_image is from ImageProcessor)
if processed_image.is_duplicate:
    logger.debug(
        f"Duplicate detected: {url} (matches {processed_image.duplicate_of})"
    )
    source_stats.duplicates_detected += 1
    result.duplicate_images += 1
    prop_changes.duplicates += 1

    # Register URL to track it
    if incremental and processed_image.duplicate_of:
        self.url_tracker.register_url(
            url=url,
            image_id=processed_image.duplicate_of,
            property_hash=property_hash,
            content_hash=content_hash,
            source=extractor.source.value,
        )
    continue
```

### 5. Simplified Metadata Creation (Lines 1350-1370)
**Before:** 74 lines of manual standardization, file writing, dimension extraction, and hash registration

**After:** 21 lines using `ProcessedImage` data
```python
# New unique image - create metadata
now = datetime.now().astimezone().isoformat()
metadata = ImageMetadata(
    image_id=processed_image.image_id,
    property_address=property.full_address,
    source=extractor.source.value,
    source_url=url,
    local_path=str(processed_image.local_path.relative_to(self.base_dir)),
    original_path=None,
    phash=processed_image.phash,
    dhash=processed_image.dhash,
    width=processed_image.width,
    height=processed_image.height,
    file_size_bytes=processed_image.file_size_bytes,
    status=ImageStatus.PROCESSED.value,
    downloaded_at=now,
    processed_at=now,
    property_hash=property_hash,
    created_by_run_id=self.run_id,
    content_hash=processed_image.content_hash,
)
```

### 6. Updated URL Tracker Registration (Lines 1373-1381)
Now uses `processed_image.image_id` instead of local `image_id` variable.

### 7. Updated Statistics Tracking (Line 1385, 1395)
```python
prop_changes.new_image_ids.append(processed_image.image_id)
logger.debug(f"Saved new image: {processed_image.image_id[:8]}.png")
```

## Code Removed
- Manual `deduplicator.compute_hash()` call
- Manual `deduplicator.is_duplicate()` check
- Manual `standardizer.standardize()` call
- Manual file I/O (`with open(local_path, "wb")`)
- Manual directory creation logic
- Manual `deduplicator.register_hash()` call
- ~70 lines of scattered processing logic

## Benefits
1. **Encapsulation**: Image processing logic consolidated in single service
2. **Maintainability**: Changes to processing logic only require updating `ImageProcessor`
3. **Testability**: `ImageProcessor` can be tested independently (26 unit tests)
4. **Consistency**: Same processing logic applied across all code paths
5. **Error Handling**: Centralized error handling with clear error messages
6. **Content-Addressed Storage**: Automatic handling via `ImageProcessor`

## Storage Path
Images saved to: `data/property_images/processed/{hash[:8]}/{hash}.png`

## Tests Passing
- 26 ImageProcessor unit tests ✅
- 70 total tests in image_extraction module ✅
- No breaking changes to existing functionality ✅

## OLD Path (Preserved)
The OLD path (`extract_for_property()`) remains unchanged for backwards compatibility.

## Next Steps (If Needed)
1. Consider migrating OLD path to use `ImageProcessor`
2. Add integration tests for orchestrator with `ImageProcessor`
3. Monitor performance in production

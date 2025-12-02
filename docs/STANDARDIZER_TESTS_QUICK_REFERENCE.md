# Image Standardizer Unit Tests - Quick Reference

**Location:** `tests/unit/test_standardizer.py`
**Tests:** 61 (all passing)
**Coverage:** 93%
**Lines:** 767

## Quick Test Map

### Running Tests
```bash
# Run all tests
pytest tests/unit/test_standardizer.py -v

# Run specific test class
pytest tests/unit/test_standardizer.py::TestFileSizeLimits -v

# Run with coverage
pytest tests/unit/test_standardizer.py --cov=phx_home_analysis.services.image_extraction.standardizer

# Run single test
pytest tests/unit/test_standardizer.py::TestFormatConversion::test_converts_jpeg_to_png -v
```

## Test Classes at a Glance

| Class | Tests | Focus | Key Assert |
|-------|-------|-------|-----------|
| TestFileSizeLimits | 4 | 50MB max file size | Rejects > 50MB |
| TestImageResizing | 8 | Max 1024px, aspect ratio | `max(size) <= 1024` |
| TestFormatConversion | 8 | All formats -> PNG RGB | `format == "PNG"` |
| TestInvalidInput | 7 | Corrupted data rejection | `ImageProcessingError` |
| TestMagicByteValidation | 5 | Security - file signatures | Magic bytes verified |
| TestDecompressionBombProtection | 2 | Pixel limit (15K x 12K) | `MAX_IMAGE_PIXELS` set |
| TestDimensionInfo | 3 | `get_dimensions()` helper | Returns (width, height) |
| TestFormatDetection | 4 | `get_format()` helper | Returns format string |
| TestImageInfo | 4 | `get_info()` helper | Complete metadata |
| TestOutputQuality | 4 | Output validity | Can re-open as image |
| TestEdgeCases | 5 | Boundary conditions | 1x1, 1024x1024, extreme ratios |
| TestConfigurationOptions | 4 | Init parameters | Custom dimensions work |
| TestErrorMessages | 3 | Error quality | Clear, informative messages |

## Security Controls Tested

### File Size Protection
- Files > 50MB rejected immediately (prevents memory exhaustion)
- `test_rejects_oversized_file`, `test_is_valid_image_rejects_oversized`

### Magic Byte Validation
- JPEG (FF D8 FF), PNG (89 50 4E...), GIF (GIF87a/89a) accepted
- Non-image data rejected before PIL processing
- `TestMagicByteValidation` (5 tests)

### Decompression Bomb Prevention
- PIL.Image.MAX_IMAGE_PIXELS = 178,956,970 (~ 15K x 12K pixels)
- Prevents zip-bomb style attacks
- `test_pixel_limit_is_set`

### Content Validation
- Truncated/corrupted files rejected
- Empty data rejected
- Invalid formats rejected
- `TestInvalidInput` (7 tests)

## Format Support Matrix

| Format | Test | Notes |
|--------|------|-------|
| JPEG | ✓ (test_converts_jpeg_to_png) | Converted to PNG |
| PNG | ✓ (test_accepts_valid_png_magic) | Passed through |
| GIF | ✓ (test_accepts_gif_magic) | Converted to PNG |
| RGBA | ✓ (test_converts_rgba_to_rgb) | White bg composite |
| Grayscale | ✓ (test_handles_grayscale) | Converted to RGB |
| Palette | ✓ (test_handles_palette_mode) | Converted to RGB |
| LA (Gray+Alpha) | ✓ (test_handles_grayscale_with_alpha) | Converted to RGB |

## Dimension Testing

| Scenario | Test | Expected Behavior |
|----------|------|------------------|
| Oversized (2000x2000) | test_resizes_oversized_image | -> 1024x1024 |
| Wide (3000x1000) | test_resizes_wide_image | -> 1024x~341 |
| Tall (1000x3000) | test_resizes_tall_image | -> ~341x1024 |
| Small (100x100) | test_does_not_upscale_small_images | No change |
| At boundary (1024x1024) | test_1024x1024_boundary | No change |
| Over boundary (1025x1025) | test_1025x1025_just_over_boundary | -> 1024x1024 |
| Extreme ratio (10000x100) | test_extreme_aspect_ratio | -> 1024x~102 |

## Configuration Parameters

```python
ImageStandardizer(
    max_dimension: int = 1024,      # Max width or height
    output_format: str = "PNG"      # Output format
)
```

### Tested Configurations
- Default (1024 x PNG) - standard case
- Custom 512px max - smaller output
- Custom 2048px max - larger output
- Custom output_format - PNG validated

## Helper Methods Tested

| Method | Purpose | Tests |
|--------|---------|-------|
| `standardize(bytes)` | Main processing pipeline | 40+ tests |
| `get_dimensions(bytes)` | Get image width, height | TestDimensionInfo (3) |
| `get_format(bytes)` | Detect image format | TestFormatDetection (4) |
| `get_info(bytes)` | Complete metadata | TestImageInfo (4) |
| `is_valid_image(bytes)` | Validation check | TestFileSizeLimits, TestInvalidInput |
| `_validate_magic_bytes(bytes)` | Internal security check | TestMagicByteValidation (5) |
| `_convert_color_mode(Image)` | Color conversion | Tested via standardize() |
| `_resize_if_needed(Image)` | Dimension standardization | TestImageResizing (8) |

## Error Cases Verified

| Error Type | Test | Expected Exception |
|------------|------|-------------------|
| Oversized file | test_rejects_oversized_file | ImageProcessingError |
| Invalid magic bytes | test_rejects_invalid_magic_bytes | ImageProcessingError |
| Non-image data | test_rejects_non_image_data | ImageProcessingError |
| Empty data | test_rejects_empty_data | ImageProcessingError |
| Truncated image | test_rejects_truncated_image | ImageProcessingError |
| Corrupted file | test_rejects_random_binary_data | ImageProcessingError |

## Test Fixtures

```python
@pytest.fixture
def standardizer(self):
    """All test classes use this fixture"""
    return ImageStandardizer(max_dimension=1024)
```

Standard configuration: 1024px max, PNG output

## Key Assertions Used

```python
# Size checks
assert len(result) > 0
assert max(result_img.size) <= 1024

# Format checks
assert result[:8] == b"\x89PNG\r\n\x1a\n"
assert result_img.format == "PNG"
assert result_img.mode == "RGB"

# Behavior checks
assert result_img.size == (100, 100)  # Not upscaled
assert 1.9 <= ratio <= 2.1  # Aspect ratio preserved

# Error checks
with pytest.raises(ImageProcessingError):
    standardizer.standardize(invalid_data)

# Metadata checks
assert info["has_alpha"] is False
assert info["needs_resize"] is True
```

## Coverage Gaps (7 uncovered lines)

1. WebP detection (rare format, not commonly used)
2. Some grayscale resize edge cases
3. Specific corrupted file boundaries
4. Uncommon error type combinations

**Assessment:** Core functionality fully covered. Gaps are edge cases.

## Related Documentation

- Full summary: `docs/TEST_STANDARDIZER_SUMMARY.md`
- Source code: `src/phx_home_analysis/services/image_extraction/standardizer.py`
- Exception: `ImageProcessingError` in same module

## Quick Debugging

**Test fails locally but passes in CI?**
- Check PIL/Pillow version (tests with 10.x+)
- Verify Python 3.12+ (tested with 3.12.11)

**Slow test execution?**
- Normal: 7-8 seconds for all 61 tests
- If >15 seconds: Check system load, PIL compilation issues

**Coverage not showing right percentage?**
- Use full module path: `--cov=phx_home_analysis.services.image_extraction.standardizer`
- Not relative paths

## Test Maintenance Notes

- Tests are independent (no shared state)
- Fixtures create fresh ImageStandardizer for each test
- PIL in-memory processing (no temp files)
- No external dependencies needed

---

**Last Updated:** 2025-12-02
**Maintainer Notes:** All 61 tests passing. 93% coverage acceptable - 8 uncovered lines are rare edge cases and alternative formats.

# Image Extraction Orchestrator

## Overview

The `ImageExtractionOrchestrator` coordinates image extraction across multiple sources (Zillow, Redfin, Maricopa County Assessor, Phoenix MLS) with deduplication, standardization, and state persistence.

## Location

**File:** `src/phx_home_analysis/services/image_extraction/orchestrator.py`

## Key Features

### 1. Multi-Source Extraction
- Extracts images from all enabled sources concurrently
- Configurable source selection
- Rate limiting per source
- Automatic retry with exponential backoff

### 2. Deduplication
- Perceptual hashing (pHash + dHash)
- Cross-source duplicate detection
- Persistent hash index
- Configurable similarity threshold

### 3. Image Standardization
- Converts all images to PNG format
- Resizes to maximum 1024x1024 (preserves aspect ratio)
- High-quality Lanczos resampling
- Consistent color mode (RGB)

### 4. State Persistence
- Resumable extraction (skips completed properties)
- Progress tracking across runs
- Manifest JSON with all image metadata
- Hash index for deduplication

### 5. Progress Tracking
- Per-source statistics
- Success/failure tracking
- Duplicate detection counts
- Duration and success rate metrics

## Usage

### Basic Usage

```python
from pathlib import Path
from phx_home_analysis.services.image_extraction.orchestrator import (
    ImageExtractionOrchestrator,
)
from phx_home_analysis.domain.enums import ImageSource

# Initialize orchestrator
orchestrator = ImageExtractionOrchestrator(
    base_dir=Path("data/images"),
    enabled_sources=[ImageSource.ZILLOW, ImageSource.REDFIN],
    max_concurrent_properties=3,
)

# Extract images for properties
properties = [...]  # List of Property entities
result = await orchestrator.extract_all(
    properties=properties,
    resume=True,  # Skip already completed
)

# Print results
print(f"Completed: {result.properties_completed}/{result.total_properties}")
print(f"Unique images: {result.unique_images}")
print(f"Duplicates: {result.duplicate_images}")
```

### Configuration Options

```python
orchestrator = ImageExtractionOrchestrator(
    base_dir=Path("data/images"),
    enabled_sources=[ImageSource.ZILLOW, ImageSource.REDFIN],  # Sources to use
    max_concurrent_properties=3,  # Parallel property processing
    deduplication_threshold=8,  # Hamming distance for duplicates
    max_dimension=1024,  # Maximum image dimension (pixels)
)
```

### Retrieve Images for a Property

```python
# Get all images for a specific property
images = orchestrator.get_property_images(property)

for img in images:
    print(f"Source: {img.source}")
    print(f"Path: {img.local_path}")
    print(f"Size: {img.width}x{img.height}")
```

### Get Overall Statistics

```python
stats = orchestrator.get_statistics()

print(f"Total properties: {stats['total_properties']}")
print(f"Total images: {stats['total_images']}")
print(f"Images by source: {stats['images_by_source']}")
```

### Resume Interrupted Extraction

```python
# First run - processes 5 properties
result1 = await orchestrator.extract_all(
    properties=properties[:5],
    resume=False,
)

# Later run - resumes and processes remaining
result2 = await orchestrator.extract_all(
    properties=properties,  # All properties
    resume=True,  # Skips first 5
)
```

## Directory Structure

```
data/images/
├── processed/           # Standardized PNG images
│   ├── {property_hash}/
│   │   ├── {uuid1}.png
│   │   ├── {uuid2}.png
│   │   └── ...
│   └── ...
├── raw/                 # Raw downloaded images (optional)
└── metadata/            # Tracking files
    ├── image_manifest.json      # All image metadata
    ├── hash_index.json          # Deduplication hashes
    └── extraction_state.json    # Progress tracking
```

## Data Structures

### ExtractionResult

Returned from `extract_all()`:

```python
@dataclass
class ExtractionResult:
    total_properties: int
    properties_completed: int
    properties_failed: int
    properties_skipped: int
    total_images: int
    unique_images: int
    duplicate_images: int
    failed_downloads: int
    by_source: dict[str, SourceStats]
    start_time: datetime
    end_time: datetime

    @property
    def duration_seconds(self) -> float: ...

    @property
    def success_rate(self) -> float: ...
```

### ImageMetadata

Stored in manifest for each image:

```python
@dataclass(frozen=True)
class ImageMetadata:
    image_id: str
    property_address: str
    source: str
    source_url: str
    local_path: str
    phash: str
    dhash: str
    width: int
    height: int
    file_size_bytes: int
    status: str
    downloaded_at: str
    processed_at: str
    is_duplicate: bool
    duplicate_of: Optional[str]
```

## Workflow

1. **Initialize** - Load manifest, hash index, state
2. **Filter** - Skip completed properties if resuming
3. **Extract** - For each property:
   - Create extractors for enabled sources
   - Extract image URLs from each source
   - Download images with retry logic
   - Compute perceptual hashes
   - Check for duplicates
   - Standardize (resize, convert to PNG)
   - Save to processed directory
   - Register hash in index
   - Create metadata
4. **Track** - Update statistics, save state periodically
5. **Finalize** - Save final manifest and state

## Error Handling

- **SourceUnavailableError** - Source down or rate limited
- **ImageDownloadError** - Download failed after retries
- **DeduplicationError** - Hash computation failed
- **ImageProcessingError** - Standardization failed

All errors are logged; processing continues for other images.

## Performance Considerations

- **Concurrency**: Max concurrent properties configurable (default: 3)
- **Rate Limiting**: Per-source delays (0.5-2.0 seconds)
- **Retries**: Exponential backoff (max 3 attempts)
- **Periodic Saves**: State saved every 5 properties

## Example Output

### Extraction Result

```
Extraction complete: 8/10 succeeded, 45 unique images, 5 duplicates
Duration: 245.3 seconds
Success rate: 80.0%

By Source:
  zillow:
    Properties: 8
    Images found: 30
    Downloaded: 28
    Duplicates: 3
    Failed: 2
  redfin:
    Properties: 8
    Images found: 25
    Downloaded: 22
    Duplicates: 2
    Failed: 3
```

### Image Manifest Structure

```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-30T14:30:00-07:00",
  "properties": {
    "123 Main St, Phoenix, AZ 85001": [
      {
        "image_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "source": "zillow",
        "source_url": "https://photos.zillowstatic.com/...",
        "local_path": "processed/abc12345/a1b2c3d4.png",
        "phash": "0123456789abcdef",
        "dhash": "fedcba9876543210",
        "width": 1024,
        "height": 768,
        "file_size_bytes": 523840,
        "status": "processed",
        "downloaded_at": "2025-11-30T14:25:30-07:00",
        "processed_at": "2025-11-30T14:25:31-07:00"
      }
    ]
  }
}
```

## Testing

**Location:** `tests/services/image_extraction/test_orchestrator.py`

Run tests:
```bash
pytest tests/services/image_extraction/test_orchestrator.py -v
```

**Coverage:** 21/24 tests passing (87.5%)
- All synchronous methods: ✓
- State persistence: ✓
- Manifest operations: ✓
- Statistics: ✓
- Async tests: Pending pytest-asyncio configuration

## Integration

### With Property Pipeline

```python
from phx_home_analysis.pipeline.loader import PropertyLoader
from phx_home_analysis.services.image_extraction.orchestrator import (
    ImageExtractionOrchestrator,
)

# Load properties
loader = PropertyLoader()
properties = loader.load_from_csv("phx_homes.csv")

# Extract images
orchestrator = ImageExtractionOrchestrator(
    base_dir=Path("data/images"),
)
result = await orchestrator.extract_all(properties)

# Images are now available for AI analysis
for prop in properties:
    images = orchestrator.get_property_images(prop)
    # Pass to AI model...
```

## Dependencies

- **httpx**: Async HTTP client
- **Pillow**: Image processing
- **imagehash**: Perceptual hashing
- **playwright**: Browser automation (for Zillow/Redfin)

## Maintenance

### Clear State (Start Fresh)

```python
orchestrator.clear_state()
```

### Rebuild Hash Index

Delete `data/images/metadata/hash_index.json` and re-run extraction.

### Update Configuration

Modify orchestrator initialization parameters and re-run.

## Future Enhancements

1. **Parallel Source Extraction** - Process sources concurrently per property
2. **Image Classification** - Auto-categorize (exterior, kitchen, etc.)
3. **Quality Filtering** - Reject low-resolution or corrupted images
4. **Compression** - Optional JPEG compression for storage
5. **CDN Integration** - Upload to cloud storage
6. **Smart Resume** - Partial property completion tracking

## See Also

- `ImageDeduplicator` - Perceptual hash deduplication
- `ImageStandardizer` - Format conversion and resizing
- `extractors/` - Source-specific image extraction
- `examples/image_extraction_example.py` - Complete examples

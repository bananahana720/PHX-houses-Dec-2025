# Image Extraction CLI Guide

## Overview

The `extract_images.py` CLI script orchestrates image extraction from multiple property listing sources with deduplication, standardization, and resumable operations.

## Installation

### Dependencies

All required dependencies are specified in `pyproject.toml`:

```bash
# Install project with dependencies
uv pip install -e .

# Install Playwright browsers (required for Zillow/Redfin)
python -m playwright install chromium
```

### Environment Variables

Some extractors require API credentials:

```bash
# Maricopa County Assessor (optional)
export MARICOPA_ASSESSOR_TOKEN="your-token-here"

# Phoenix MLS (optional)
export PHOENIX_MLS_API_KEY="your-api-key-here"
```

## Usage

### Basic Commands

```bash
# Extract from all sources for all properties
python scripts/extract_images.py --all

# Single property extraction
python scripts/extract_images.py --address "4732 W Davis Rd, Glendale, AZ 85306"

# Specific sources only
python scripts/extract_images.py --all --sources zillow,redfin

# Dry run (discover URLs without downloading)
python scripts/extract_images.py --all --dry-run

# Verbose logging
python scripts/extract_images.py --all -v
```

### Resumable Operations

The orchestrator tracks extraction state for resumable operations:

```bash
# Resume from previous run (default behavior)
python scripts/extract_images.py --all --resume

# Fresh start (ignore previous state)
python scripts/extract_images.py --all --fresh
```

**State Files:**
- `data/property_images/metadata/extraction_state.json` - Tracks completed properties
- `data/property_images/metadata/image_manifest.json` - Image metadata catalog
- `data/property_images/metadata/hash_index.json` - Perceptual hash index for deduplication

### Source Selection

Available sources:
- `maricopa_assessor` - Maricopa County Assessor (requires auth token)
- `zillow` - Zillow listings (uses Playwright browser automation)
- `redfin` - Redfin listings (uses Playwright browser automation)
- `phoenix_mls` - Phoenix MLS (optional API key)

```bash
# County assessor only
python scripts/extract_images.py --all --sources maricopa_assessor

# Zillow and Redfin only
python scripts/extract_images.py --all --sources zillow,redfin
```

### Output Control

```bash
# Custom output directory
python scripts/extract_images.py --all --output-dir /path/to/images

# Custom CSV file
python scripts/extract_images.py --all --csv /path/to/properties.csv
```

## Output Structure

```
data/property_images/
├── processed/           # Standardized images (PNG, deduplicated)
│   └── <property_hash>/
│       ├── <uuid>.png
│       └── ...
├── metadata/            # Extraction metadata
│   ├── extraction_state.json
│   ├── image_manifest.json
│   └── hash_index.json
└── raw/                 # (Optional) Original downloaded images
```

## Features

### 1. Multi-Source Extraction

Coordinates extraction across multiple sources in parallel:
- Each source has custom URL discovery logic
- Source-specific rate limiting respected
- Graceful handling of source unavailability

### 2. Perceptual Hash Deduplication

Detects duplicate images across sources using pHash:
- Compares perceptual similarity (not byte-exact)
- Hamming distance threshold for matches
- Prevents saving duplicate images

### 3. Image Standardization

Converts all images to consistent format:
- PNG format (lossless)
- Maximum dimension: 1024px (preserves aspect ratio)
- Consistent quality for analysis

### 4. State Persistence

Tracks extraction progress for resumption:
- Per-property completion tracking
- Failed properties tracked separately
- Safe interrupt with Ctrl+C

### 5. Progress Tracking

Real-time progress updates:
```
[1/25 - 4.0%] 4732 W Davis Rd, Glendale, AZ 85306
  Images extracted: 8

[2/25 - 8.0%] 2353 W Tierra Buena Ln, Phoenix, AZ 85023
  Images extracted: 12
```

### 6. Summary Statistics

Comprehensive extraction summary:
```
============================================================
Summary
============================================================
Properties: 23 processed, 2 failed
Images: 245 total, 198 unique, 47 duplicates

By source:
  maricopa_assessor: 45 images
  zillow: 120 images
  redfin: 33 images

Duration: 12m 34s
Success rate: 92.0%
============================================================
```

## Troubleshooting

### CAPTCHA Detection (Zillow/Redfin)

Browser automation may trigger CAPTCHA challenges:

```
ERROR: Zillow unavailable: Zillow CAPTCHA or block page detected
```

**Solutions:**
- Add delays between requests (`--max-concurrent=1`)
- Use rotating User-Agents
- Extract during off-peak hours
- Consider manual intervention for small datasets

### Missing API Tokens

Some extractors require authentication:

```
WARNING: MARICOPA_ASSESSOR_TOKEN not set - extractor will fail authentication
```

**Solutions:**
- Set environment variables (see Installation)
- Exclude source: `--sources zillow,redfin` (skip assessor)
- Contact data provider for API access

### Property Not Found

Extractors may not find listings for all properties:

```
WARNING: Property not found on Phoenix MLS: <address>
```

**Reasons:**
- Property no longer listed
- Address format mismatch
- Source doesn't cover this location
- Listing is off-market

**This is normal** - some sources won't have all properties.

### Network Errors

Transient network issues may occur:

```
ERROR: Failed to download <url>: Connection timeout
```

**Solutions:**
- Retry with `--resume` (already completed properties skipped)
- Increase timeout in orchestrator configuration
- Check network connectivity

## Performance

### Concurrency

Default: 3 properties processed in parallel

```python
# In orchestrator initialization
max_concurrent_properties=3
```

**Trade-offs:**
- Higher = faster extraction, more server load
- Lower = slower but more polite to servers

### Rate Limiting

Each source has configured rate limits:
- Maricopa Assessor: 1 request/second
- Zillow: 2 seconds/request
- Redfin: 1.5 seconds/request
- Phoenix MLS: 0.5 seconds/request

### Expected Duration

For 25 properties with all sources:
- Dry run: ~2-5 minutes
- Full extraction: ~15-30 minutes
- Depends on images per property (avg 8-12)

## Examples

### Extract for Deal Sheet Generation

```bash
# Extract images for top-tier properties only
python scripts/extract_images.py --csv data/unicorn_properties.csv --all

# Output will be in data/property_images/processed/<property_hash>/
```

### Update Images for Single Property

```bash
# Fresh extraction for one property
python scripts/extract_images.py \
  --address "4732 W Davis Rd, Glendale, AZ 85306" \
  --fresh
```

### Bulk Extract with Source Filtering

```bash
# Extract from free sources only (no API tokens needed)
python scripts/extract_images.py --all \
  --sources zillow,redfin \
  -v
```

## Integration with Analysis Pipeline

The extracted images can be used for:

1. **Deal Sheet Generation** (`scripts/deal_sheets.py`)
   - Loads images from manifest
   - Includes property photos in PDFs

2. **Manual Assessment** (visual scoring)
   - Kitchen layout scoring
   - Natural light assessment
   - Interior aesthetics evaluation

3. **Computer Vision Analysis** (future)
   - Automated room detection
   - Amenity classification
   - Condition assessment

## See Also

- `src/phx_home_analysis/services/image_extraction/` - Orchestrator implementation
- `src/phx_home_analysis/services/image_extraction/extractors/` - Source-specific extractors
- `pyproject.toml` - Dependencies configuration

# BUCKET 5: Image Pipeline Architecture

### Current Implementation

#### 5.1 Storage Structure

**Physical Organization**:
```
data/property_images/
├── raw/                    # Original downloads (unused currently)
├── processed/              # Categorized images
│   └── {property_hash}/    # 8-char hash per property
│       ├── {image_id}_{metadata}.png
│       └── ...
└── metadata/               # Pipeline state & indexes
    ├── extraction_state.json         # Extraction progress
    ├── address_folder_lookup.json    # Address -> hash mapping
    ├── image_manifest.json           # Complete image inventory
    ├── hash_index.json               # Perceptual hash database
    ├── url_tracker.json              # URL deduplication
    ├── pipeline_runs.json            # Run history & audit trail
    └── run_history/                  # Per-run detailed logs
```

**Key Metrics** (from `address_folder_lookup.json`):
- 35+ properties indexed
- Average 50-80 images per property
- Total estimated: 1,750-2,800 images across portfolio
- Image folders hash to 8-character IDs (consistent across phases)

#### 5.2 Image Naming Convention

**Format**: `{hash}_{location}_{subject}_{confidence}_{source}_{date}[_{seq}].png`

**Example**: `ef7cd95f_int_kitchen_95_z_20241201.png`

**Components**:

| Field | Values | Purpose | Example |
|-------|--------|---------|---------|
| hash | 8-char hex | Property identifier | `ef7cd95f` |
| location | `ext`, `int`, `sys`, `feat` | Exterior/Interior/System/Feature | `int` |
| subject | `kitchen`, `master`, `pool`, `roof`, `laundry`, `bedroom`, `bathroom`, `living`, `hvac`, `sewer` | Room/system type | `kitchen` |
| confidence | `00-99` | AI confidence % | `95` |
| source | `z`, `r`, `m`, `p`, `u` | Zillow, Redfin, Maricopa, Phoenix MLS, Unknown | `z` |
| date | `YYYYMMDD` | Listing/capture date | `20241201` |
| sequence | `00-99` (optional) | For multiple images in same category | `02` |

**Implementation**: `src/phx_home_analysis/services/image_extraction/naming.py`
- `ImageName` dataclass with validation
- Parse/generate functions with collision detection
- Regex pattern matching: `^[a-f0-9]{8}_(ext|int|sys|feat)_[a-z_]+_\d{2}_[zrmpu]_\d{8}(_\d{2})?\.png$`
- Sequence auto-increment when duplicates detected

**Quality**: Metadata-rich, reversible, sortable, enables fast bulk operations.

#### 5.3 Deduplication System

**Technology**: Perceptual hashing with Locality Sensitive Hashing (LSH) optimization

**Implementation**: `src/phx_home_analysis/services/image_extraction/deduplicator.py`

**Algorithms**:
- **pHash** (primary): Perceptual hash - robust to scaling, compression, minor edits
- **dHash** (secondary): Difference hash - catches cropped variants
- **LSH Bucketing** (optimization): 64-bit hash split into 8 bands
  - Reduces O(n²) comparison to O(n) average case
  - Bucketing: each band acts as hash-based lookup key
  - Candidate matching: only compare images sharing band signatures

**Similarity Threshold**:
- pHash Hamming distance ≤ 8 = duplicate
- dHash confirmation: distance ≤ 10

**Persistence**:
- `hash_index.json`: All image hashes with metadata
  - Schema: `{ version, images: { image_id: { phash, dhash, property_address, source } } }`
- LSH buckets rebuilt in-memory on load (O(n) startup, O(1) lookup)
- Atomic writes with tempfile+rename pattern

**Statistics Tracked**:
```json
{
  "total_images": 2847,
  "by_source": { "zillow": 1204, "redfin": 890, "maricopa_assessor": 753 },
  "unique_properties": 35,
  "lsh": {
    "num_bands": 8,
    "total_buckets": 450,
    "avg_bucket_size": 6.3,
    "max_bucket_size": 24
  }
}
```

**Performance**: Hash computation ~50ms/image, LSH lookup ~1ms (vs 2847ms brute force)

#### 5.4 Image Metadata & Linking

**Data Relationships**:

1. **Image Manifest** (`image_manifest.json`):
   ```json
   {
     "version": "1.0.0",
     "last_updated": "ISO8601",
     "properties": {
       "4560 E Sunrise Dr, Phoenix, AZ 85044": [
         {
           "image_id": "UUID",
           "source": "zillow|redfin|maricopa_assessor|phoenix_mls",
           "source_url": "https://...",
           "local_path": "processed/{hash}/{id}.png",
           "phash": "64-char hex",
           "dhash": "64-char hex",
           "width": int,
           "height": int,
           "file_size_bytes": int,
           "status": "downloaded|processed|failed",
           "downloaded_at": "ISO8601",
           "processed_at": "ISO8601"
         }
       ]
     }
   }
   ```

2. **Address Lookup** (`address_folder_lookup.json`):
   ```json
   {
     "4732 W Davis Rd, Glendale, AZ 85306": {
       "folder": "686067a4",
       "image_count": 98,
       "path": "data/property_images/processed/686067a4/"
     }
   }
   ```

3. **URL Deduplication** (`url_tracker.json`):
   - Tracks which URLs have been downloaded
   - Prevents redundant fetches on re-runs
   - Enables incremental extraction

**Linking Strategy**:
- Primary key: `full_address` (canonical property identifier)
- Foreign key: folder hash (8-char) and image UUID
- Every image → property via manifest lookup
- Every property → folder via address lookup
- Cross-validation: manifest property address must exist in CSV/enrichment_data.json

**Data Quality Checks**:
- Image exists on disk before manifest entry
- Source URL accessible (circuit breaker tracked)
- Hash consistency (phash/dhash computed and verified)
- Manifest size matches folder contents (within tolerance)

#### 5.5 Categorization & Tagging

**Categorization Service**: `src/phx_home_analysis/services/image_extraction/categorization_service.py`

**Categories**:
- **Location** (where in property):
  - `ext` (exterior): Facade, driveway, landscaping, pool exterior
  - `int` (interior): Rooms, hallways, living areas
  - `sys` (systems): HVAC, electrical, plumbing
  - `feat` (features): Finishes, appliances, special elements

- **Subject** (what in image):
  - Rooms: `kitchen`, `master`, `bedroom`, `bathroom`, `living`, `dining`, `laundry`, `garage`
  - Systems: `hvac`, `roof`, `sewer`, `plumbing`, `electrical`, `pool`
  - Features: `fireplace`, `flooring`, `windows`, `skylights`, `appliances`

**Confidence Scoring**:
- 0-99 confidence % (AI vision model output or manual assignment)
- Encoded in filename for quick filtering: `ef7cd95f_int_kitchen_95_z_20241201.png` = 95% confidence
- Filtering: `--min-confidence 85` would exclude lower-confidence images

**Enabling Fast Queries**:
```python
# Find all kitchen images from Zillow
kitchen_images = [f for f in os.listdir(folder) if "_kitchen_" in f and "_z_" in f]

# Find high-confidence interiors
high_conf_interiors = [f for f in files if "_int_" in f and int(f.split("_")[3]) >= 90]

# Find all images of specific property from last 7 days
recent = [f for f in files if f.startswith("ef7cd95f_") and date > cutoff]
```

---

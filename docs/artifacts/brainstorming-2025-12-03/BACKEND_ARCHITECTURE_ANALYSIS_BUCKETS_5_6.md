# Backend Architecture Analysis: Buckets 5 & 6
## Image Pipeline & Scraping/Automation Infrastructure

**Date**: 2025-12-03
**Analyst**: Backend Architect
**Scope**: Image extraction orchestration, stealth scraping patterns, background job infrastructure
**Status**: Comprehensive gap analysis with recommendations

---

## Executive Summary

The PHX Houses project has **well-architected image extraction and scraping foundations** with sophisticated infrastructure for anti-bot detection avoidance. However, the pipeline operates **synchronously within CLI invocations** rather than as a true asynchronous background job system. The current architecture is suitable for small-scale operations but will need decoupling and worker-based processing for production scale.

### Key Findings

| Aspect | Current State | Maturity | Risk |
|--------|---------------|----------|------|
| **Image Storage** | Hash-based folder structure with atomic writes | **Good** | Low |
| **Deduplication** | LSH-optimized perceptual hashing | **Excellent** | Very Low |
| **Naming Convention** | Metadata-encoded filenames (location, subject, confidence, source, date) | **Excellent** | Very Low |
| **Stealth Scraping** | nodriver + curl_cffi with proxy rotation and circuit breakers | **Very Good** | Low |
| **State Persistence** | Atomic JSON writes with crash recovery capability | **Good** | Low |
| **Concurrency Control** | asyncio-based property-level parallelism (3 concurrent max) | **Adequate** | Medium |
| **Background Jobs** | **Missing** - all work synchronous/CLI-driven | **Poor** | **HIGH** |
| **Job Queue** | **Not implemented** | **Critical Gap** | **CRITICAL** |
| **Worker Processes** | **Not implemented** | **Critical Gap** | **CRITICAL** |
| **Progress Tracking** | Extraction state + run history logs | **Good** | Low |
| **Error Recovery** | Retry logic + circuit breakers + state resumption | **Very Good** | Very Low |

---

## BUCKET 5: Image Pipeline Architecture

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

## BUCKET 6: Scraping & Automation Architecture

### Current Implementation

#### 6.1 Stealth Extraction Pattern

**Multi-Source Approach**:

| Source | Technology | Auth | Anti-Bot | Status |
|--------|-----------|------|----------|--------|
| **Zillow** | nodriver + curl_cffi | None | PerimeterX bypass | Working |
| **Redfin** | nodriver + curl_cffi | None | CF Challenge bypass | Implemented |
| **Phoenix MLS** | Playwright MCP | API Key | Basic | Implemented |
| **Maricopa Assessor** | httpx async | API Token | Rate limiting | Working |

#### 6.2 Browser Automation: Non-Headless Stealth

**Architecture**: `src/phx_home_analysis/services/infrastructure/browser_pool.py`

**Stealth Techniques**:

1. **Non-Headless Operation**:
   - Headless browsers detectable via timing analysis and DOM differences
   - Running visible improves detection evasion significantly
   - Problem: UI overhead on CI/CD servers

2. **Isolation Modes** (to keep browser hidden):
   ```python
   # From extract_images.py --isolation option
   "virtual"     # Virtual Display Driver (xvfb on Linux, custom on Windows)
   "secondary"   # Secondary monitor (if available)
   "off_screen"  # Position window off visible screen bounds
   "minimize"    # Start minimized (fallback)
   "none"        # No isolation (for dev/testing)
   ```

   **Implementation Strategy**:
   - Virtual display preferred (totally hidden, realistic rendering)
   - Secondary monitor fallback (if multi-display available)
   - Off-screen positioning (window at negative coordinates)
   - Minimize as last resort (user may see minimize/restore)

3. **Browser Profile Rotation**:
   - User-Agent rotation via curl_cffi
   - JavaScript fingerprint spoofing
   - Cookie/session management per property
   - Proxy rotation (webshare integration)

4. **Timing Human-Like**:
   - Random delays between requests (0.5-3s)
   - Request queuing: max 3 concurrent properties
   - Rate limiting: 0.2-0.5s between API calls
   - Exponential backoff on 429/503 responses

#### 6.3 Circuit Breaker Pattern

**Implementation**: `src/phx_home_analysis/services/image_extraction/orchestrator.py` - `SourceCircuitBreaker`

**States**:
```
CLOSED (normal) --[3 failures]--> OPEN (disabled)
                                     |
                            [300s timeout]
                                     v
                              HALF-OPEN (testing)
                                     |
                        [2 successes or 1 failure]
                                     v
                              CLOSED or OPEN
```

**Configuration**:
- Failure threshold: 3 consecutive failures
- Reset timeout: 300s (5 minutes)
- Half-open success count: 2 (confirms recovery)
- Per-source tracking (Zillow, Redfin, etc. independently)

**Benefits**:
- Prevents cascade failures (e.g., rate-limit one source, kill all extraction)
- Graceful degradation (other sources continue)
- Automatic recovery testing (circuit self-heals)
- Detailed status logging for ops visibility

**Example Output**:
```
Circuit OPEN for redfin - disabled for 300s after 3 failures
Circuit HALF-OPEN for redfin - testing recovery
Circuit CLOSED for redfin - source recovered
```

#### 6.4 Async Concurrency Model

**Architecture**: `src/phx_home_analysis/services/image_extraction/orchestrator.py`

**Concurrency Levels**:

1. **Property Level** (outer loop):
   - Max 3 concurrent properties (default)
   - asyncio.Semaphore(3) to limit resource usage
   - Per property: sequentially extract all sources then process

2. **Source Level** (inner loop):
   - Per property, sources run sequentially (to avoid IP conflicts)
   - e.g., finish Zillow for prop A before starting Redfin for prop A

3. **Download Level**:
   - Image downloads within a source: parallel via asyncio.gather
   - 10-20 concurrent downloads per source
   - HTTP/2 connection pooling (curl_cffi enables multiplexing)

**Flow**:
```python
async def extract_all(properties):
    semaphore = asyncio.Semaphore(max_concurrent=3)

    async def extract_property(prop):
        async with semaphore:
            for source in enabled_sources:
                images = await source_extractor.extract(prop)  # sequential
                await download_and_process(images)              # parallel

    await asyncio.gather(*[extract_property(p) for p in properties])
```

**Rationale**:
- Property-level semaphore: resource constraint (CPU, disk I/O, bandwidth)
- Sequential sources per property: avoids rate-limit triggering from same IP
- Parallel downloads: maximizes throughput within one source

#### 6.5 State Persistence & Resumability

**State File**: `data/property_images/metadata/extraction_state.json`

```json
{
  "completed_properties": ["4732 W Davis Rd, Glendale, AZ 85306"],
  "failed_properties": [],
  "property_last_checked": {
    "4560 E Sunrise Dr, Phoenix, AZ 85044": "2025-12-03T09:59:32.294059-05:00"
  },
  "last_updated": "2025-12-03T09:59:32.298061-05:00"
}
```

**Run History**: `data/property_images/metadata/pipeline_runs.json`

```json
{
  "runs": [
    {
      "run_id": "test_2025-12-01T00:15",
      "mode": "--test",
      "started_at": "ISO8601",
      "completed_at": "ISO8601",
      "properties_requested": 5,
      "properties_completed": 5,
      "properties_failed": 0,
      "images_extracted": 89,
      "sources_used": ["zillow"],
      "sources_blocked": ["redfin"],
      "phase_results": {...},
      "properties": [
        {
          "address": "...",
          "hash": "...",
          "score": 375,
          "tier": "contender"
        }
      ],
      "notes": "..."
    }
  ]
}
```

**Crash Recovery**:
- State persisted after each property completes (not after each image)
- On resume: skips completed_properties, retries failed_properties
- URL tracker prevents re-downloading same URL
- Hash index ensures no duplicate processing

**Usage**:
```bash
# Interrupted run - resume from where stopped
python scripts/extract_images.py --all --resume

# Start fresh, ignore previous state
python scripts/extract_images.py --all --fresh

# Dry run - discover URLs without downloading
python scripts/extract_images.py --all --dry-run
```

#### 6.6 User Isolation & Session Management

**Current Model**: Synchronous CLI-driven

**Isolation Level**: **File-based** (not user-based)

**Issues**:
- Single user at a time (blocking others via file locks)
- No per-user job tracking
- No request isolation (one CLI run affects all users)
- No queuing mechanism for concurrent requests

**Example Problem**:
```
User A: python scripts/extract_images.py --all  # Takes 2 hours
User B: python scripts/extract_images.py --address "123 Main St"  # Blocks or corrupts state
```

---

## Gap Analysis: Current vs. Vision

### BUCKET 5 Gaps: Image Pipeline

| Gap | Current | Vision | Priority |
|-----|---------|--------|----------|
| **Image Alerts** | Silent processing | Console warnings for large batches (>100 new images) | Medium |
| **Deduplication Alerts** | Logged to file only | Visible warnings on duplicate detection | Low |
| **Categorization** | Filename-encoded only | Separate metadata sidecar for richer tagging | Medium |
| **Storage Versioning** | Single version | Versioned snapshots for rollback | Low |
| **Retention Policy** | None | Auto-archive old images (>90 days) | Low |
| **Disk Usage Monitoring** | None | Threshold alerts when approaching quota | Medium |

### BUCKET 6 Gaps: Scraping & Automation

| Gap | Current | Vision | Priority |
|-----|---------|--------|----------|
| **Background Jobs** | **Missing** | Job queue + worker pool | **CRITICAL** |
| **Job Queuing** | **Missing** | Redis/RabbitMQ task queue | **CRITICAL** |
| **Worker Processes** | **Missing** | Dedicated workers for extraction/processing | **CRITICAL** |
| **User Isolation** | **None** | Per-user job tracking + request queuing | **HIGH** |
| **Job Monitoring** | Run history logs | Real-time dashboard + alerting | **MEDIUM** |
| **Job Cancellation** | No | Graceful cancellation + cleanup | **MEDIUM** |
| **Distributed Extraction** | Single process | Multi-machine distributed scraping | **LOW** |
| **Rate Limit Awareness** | Circuit breaker only | Adaptive rate limiting based on server response codes | **MEDIUM** |
| **Proxy Management** | Manual config | Automatic proxy rotation + health checks | **MEDIUM** |

---

## Architectural Recommendations

### Phase 1: Immediate (Add Async Job Queuing)

#### 1.1 Decouple from CLI: Event-Driven Architecture

**Pattern**: Producer-Consumer with Message Queue

```
┌─────────────────┐
│   User/CLI      │
│  (Producer)     │
└────────┬────────┘
         │
         v
    ┌────────────┐
    │  Job Queue │ (Redis or in-memory)
    │  (FIFO)    │
    └────────────┘
         │
         v
┌─────────────────────────────┐
│   Image Extraction Worker   │
│   (Consumer, subscribed)    │
└────────┬────────────────────┘
         │
         v
    ┌──────────────┐
    │ Disk Storage │
    │   + Metrics  │
    └──────────────┘
```

**Technology Choices**:

| Technology | Pros | Cons | Recommendation |
|-----------|------|------|-----------------|
| **Redis Queues** (RQ) | Simple, in-process workers, Python-native | Limited to single machine (need cluster) | Good for MVP |
| **Celery** + RabbitMQ | Distributed, scalable, battle-tested | Complex setup, resource overhead | Good for scale |
| **Apache Kafka** | High-throughput, durable, event streaming | Operational complexity, overkill for v1 | Future |
| **In-Memory Queue** (asyncio) | No external dependency, fast | Single process, no persistence | Dev/test only |

**Recommendation for PHX Houses**: Start with **Redis + RQ** (or Celery if async/worker experience exists)

#### 1.2 Job Model

```python
# jobs/image_extraction.py

class ImageExtractionJob:
    """Represents one image extraction request."""

    id: str                           # UUID
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    user_id: str                      # If auth exists
    status: str                       # pending, in_progress, completed, failed, cancelled

    # Input
    properties: list[str]             # Addresses or --all
    sources: list[str]                # zillow, redfin, etc.

    # Output & Progress
    total_properties: int
    completed_properties: int
    failed_properties: int
    total_images: int
    new_images: int
    duplicate_images: int

    # Error tracking
    error_message: str | None
    failed_properties_list: list[str]

    # Timestamps for monitoring
    progress_updated_at: datetime
```

#### 1.3 Worker Architecture

```python
# workers/image_extraction_worker.py

from rq import Worker
from redis import Redis

class ImageExtractionWorker:
    """Worker process subscribing to image extraction jobs."""

    def __init__(self, redis_conn):
        self.redis = redis_conn
        self.worker = Worker(['image_extraction'], connection=redis_conn)

    def start(self):
        """Start consuming jobs."""
        self.worker.work(with_scheduler=False)

def extract_images_job(job_id, properties, sources, isolation_mode):
    """Actual job function - runs in worker context."""
    job = ImageExtractionJob.get(job_id)
    job.status = "in_progress"
    job.started_at = datetime.now()
    job.save()

    try:
        # Existing orchestrator logic
        orchestrator = ImageExtractionOrchestrator(...)
        result = await orchestrator.extract_all(properties, sources)

        job.completed_properties = result.properties_completed
        job.total_images = result.total_images
        job.new_images = result.unique_images
        job.duplicate_images = result.duplicate_images
        job.status = "completed"

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
    finally:
        job.completed_at = datetime.now()
        job.save()

# Usage from API/CLI:
# queue.enqueue(extract_images_job,
#     job_id=str(uuid4()),
#     properties=["4732 W Davis Rd"],
#     sources=["zillow", "redfin"],
#     isolation_mode="virtual")
```

#### 1.4 API Endpoint for Job Management

```python
# api/image_extraction.py (Flask/FastAPI)

from flask import Blueprint, request, jsonify

extraction_bp = Blueprint('extraction', __name__)

@extraction_bp.post('/api/extraction/jobs')
def create_extraction_job():
    """Enqueue a new extraction job."""
    data = request.json

    properties = data.get('properties') or data.get('all')
    sources = data.get('sources', ['zillow', 'redfin'])

    job = extraction_queue.enqueue(
        extract_images_job,
        job_id=str(uuid4()),
        properties=properties,
        sources=sources,
        isolation_mode=data.get('isolation_mode', 'virtual')
    )

    return jsonify({
        'job_id': job.id,
        'status': 'queued',
        'created_at': datetime.now().isoformat()
    }), 202

@extraction_bp.get('/api/extraction/jobs/<job_id>')
def get_job_status(job_id):
    """Get status of extraction job."""
    job = ImageExtractionJob.get(job_id)

    return jsonify({
        'job_id': job_id,
        'status': job.status,
        'progress': {
            'total_properties': job.total_properties,
            'completed_properties': job.completed_properties,
            'failed_properties': job.failed_properties,
            'total_images': job.total_images,
            'new_images': job.new_images
        },
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error': job.error_message
    })

@extraction_bp.delete('/api/extraction/jobs/<job_id>')
def cancel_job(job_id):
    """Cancel a running extraction job."""
    job = Queue.fetch_job(job_id)
    job.cancel()
    return jsonify({'status': 'cancelled'})
```

#### 1.5 Console Alerts for Large Batches

```python
# From orchestrator: Alert when >100 new images detected

if result.unique_images > 100:
    print("\n" + "=" * 70)
    print("WARNING: Large batch of new images detected")
    print("=" * 70)
    print(f"New images: {result.unique_images}")
    print(f"Duplicates: {result.duplicate_images}")
    print(f"Total this run: {result.total_images}")
    print(f"Storage: {total_size_gb:.2f} GB")
    print("\nRecommendations:")
    print("  - Verify image sources are current and correct")
    print("  - Check for listing database updates")
    print("  - Monitor disk space (current usage may grow)")
    print("=" * 70 + "\n")

    # Log to metrics system
    logger.warning(f"Large image batch: {result.unique_images} new images")
```

### Phase 2: Production Readiness (Monitoring & Scaling)

#### 2.1 Job Monitoring Dashboard

**Metrics to Track**:
- Queue depth (pending jobs)
- Active workers (count, health)
- Job success rate (%)
- Median job duration (minutes)
- Extraction rate (images/minute)
- Source-specific success rates

**Dashboard** (Grafana + Prometheus):
```
┌─────────────────────────────────────┐
│   Image Extraction Dashboard        │
├─────────────────────────────────────┤
│ Queue Depth: 23 jobs pending        │
│ Active Workers: 3/5 healthy         │
│                                     │
│ Success Rate: 94.2% (last 24h)      │
│ Median Duration: 12.3 min           │
│                                     │
│ By Source:                          │
│  Zillow:     450 imgs/h             │
│  Redfin:     320 imgs/h (blocked 5%)│
│  Maricopa:   180 imgs/h             │
│                                     │
│ Recent Failures:                    │
│  - Redfin circuit open (5m ago)     │
│  - Zillow timeout (12m ago)         │
└─────────────────────────────────────┘
```

#### 2.2 Adaptive Rate Limiting

```python
# Based on HTTP response codes from sources

class AdaptiveRateLimiter:
    """Adjusts rate based on server feedback."""

    def __init__(self):
        self.rates = {
            'zillow': 0.5,      # seconds between requests
            'redfin': 0.5,
            'maricopa': 1.0,    # official API, slower
        }

    def handle_response(self, source: str, status_code: int, headers: dict):
        """Adjust rate based on response."""

        if status_code == 429:  # Too Many Requests
            # Increase delay: 500ms -> 1s -> 2s
            self.rates[source] *= 2
            logger.warning(f"{source}: rate limit hit, backoff to {self.rates[source]}s")

        elif status_code == 503:  # Service Unavailable
            # Increase delay significantly
            self.rates[source] *= 3
            logger.warning(f"{source}: service unavailable, backoff to {self.rates[source]}s")

        elif status_code == 200 and 'Retry-After' in headers:
            # Server suggests retry delay
            retry_after = int(headers['Retry-After'])
            self.rates[source] = max(self.rates[source], retry_after + 1)

        elif status_code == 200:
            # Success - gradually reduce delay (recovery)
            self.rates[source] = self.rates[source] * 0.95
```

#### 2.3 Distributed Worker Pool

**Architecture for Multi-Machine Extraction**:

```
┌──────────────────────────────────────────────────────────┐
│                    Redis Queue                           │
│                  (central, shared)                       │
└──────────────────────────────────────────────────────────┘
         │         │         │         │
         v         v         v         v
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │ Worker │ │ Worker │ │ Worker │ │ Worker │
    │   #1   │ │   #2   │ │   #3   │ │   #4   │
    │ (US)   │ │ (US)   │ │ (EU)   │ │ (APAC) │
    └────────┘ └────────┘ └────────┘ └────────┘
         │         │         │         │
         └─────────┴─────────┴─────────┘
                   │
         ┌─────────────────────┐
         │  Shared Storage     │
         │  (S3 or NFS)        │
         │  images/metadata    │
         └─────────────────────┘
```

**Benefits**:
- Distribute load across multiple machines
- Faster extraction (parallel properties)
- Resilience (worker failure doesn't block all jobs)
- Geographic diversity (different IP blocks per region)

---

## Implementation Roadmap

### Q1 2025: Foundation

1. **Week 1-2**: Design job model + RQ infrastructure
2. **Week 3-4**: Implement job queue + worker
3. **Week 5-6**: Migrate existing extract_images.py to worker job
4. **Week 7**: Testing + API endpoint implementation
5. **Week 8**: Monitoring + alerting setup

### Q2 2025: Observability & Scale

1. **Monitoring dashboard** (Prometheus + Grafana)
2. **Adaptive rate limiting** (response-based feedback)
3. **Multi-worker support** (horizontal scaling)
4. **Job cancellation** (graceful shutdown)

### Q3 2025: Advanced Features

1. **Distributed extraction** (geographic load balancing)
2. **Proxy auto-rotation** (health checks)
3. **Image categorization** sidecar metadata
4. **Storage archival** (old images → cold storage)

---

## Data Flow: Current vs. Recommended

### Current (Synchronous)

```
User Input → CLI Parse → ImageExtractionOrchestrator
                             ↓
                        Async Extract
                        (3 concurrent)
                             ↓
              Download & Deduplicate → Update JSON
                             ↓
                          Print Summary
                             ↓
                         Exit (Success/Fail)
```

**Problem**: User blocked for 30+ minutes, single point of failure

### Recommended (Async + Queue)

```
User Request → REST API → Job Queue (Redis)
                              ↓
                    [Job stored + assigned ID]
                              ↓
                        Return 202 Accepted
                      (user gets job_id immediately)
                              ↓
                    [Background Worker picks up]
                              ↓
             Async Extract (3 concurrent props)
                              ↓
         Download & Deduplicate (parallel images)
                              ↓
            Update JSON + Job Status + Metrics
                              ↓
                      [Job marked complete]
                              ↓
User polls /api/extraction/jobs/{id} for progress
    → Can cancel, check status, download results
```

**Benefits**:
- User not blocked
- Multiple requests queued (not dropped)
- Progress visibility in real-time
- Cancellation support
- Worker failures don't lose jobs
- Easy to scale (add more workers)

---

## Critical Implementation Notes

### State & Atomicity

The current system uses **atomic writes** for state persistence:

```python
# CORRECT: atomic write pattern (existing code)
fd, temp_path = tempfile.mkstemp(dir=base_dir, suffix=".tmp")
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f)
    os.replace(temp_path, original_path)  # atomic on POSIX & Windows
except:
    os.unlink(temp_path)
```

**MUST PRESERVE** in job-based architecture. Add to job status updates:

```python
# Update job status atomically
job_dict = job.to_dict()
fd, temp_path = tempfile.mkstemp()
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(job_dict, f)
    os.replace(temp_path, job_path)
```

### Backward Compatibility

**Do NOT break** existing tools:

1. **Keep existing CLI**: `python scripts/extract_images.py --all` should still work
2. **Option 1 (Recommended)**: CLI enqueues job, polls status, prints summary
3. **Option 2 (Simple)**: Sync mode flag `--sync` for blocking behavior

```python
# Option 1: CLI becomes thin wrapper
def main():
    args = parse_args()

    job = extraction_queue.enqueue(extract_images_job, ...)
    print(f"Job queued: {job.id}")

    # Poll until done (backward compatible)
    while job.get_status() != 'completed':
        time.sleep(1)

    print(job.result)
```

### Error Recovery & Restart

Job queue + persistent state = **natural recovery**:

1. Worker crashes → Redis retains job → next worker picks it up
2. Partial extraction → resume via `property_last_checked` + URL tracker
3. Corrupted state → job marked failed, manually requeue

---

## Monitoring & Alerting Strategy

### Key Metrics

| Metric | Type | Alert Threshold | Owner |
|--------|------|-----------------|-------|
| Queue depth | Gauge | > 50 jobs | Ops |
| Job duration | Histogram | > 60 min (p95) | Dev |
| Success rate | Counter | < 90% | Dev |
| Source circuit status | Gauge | Open > 2h | Ops |
| Disk usage | Gauge | > 85% quota | Ops |
| New images batch size | Gauge | > 100 | Dev/QA |

### Alert Examples

```yaml
# Prometheus alerting rules
alert: ImageExtractionQueueLarge
  expr: image_extraction_queue_depth > 50
  for: 5m
  action: Notify #ops, page oncall if > 100

alert: ExtractionWorkerDown
  expr: up{job="extraction_worker"} == 0
  for: 1m
  action: Page oncall

alert: SourceCircuitOpen
  expr: extraction_source_circuit_open > 2h
  action: Notify #ops
```

---

## Security Considerations

### User Isolation (Future)

When multi-user support added:

1. **Job ownership**: job.user_id = authenticated user
2. **Access control**: Only user can view/cancel own job
3. **Quotas**: Per-user max concurrent jobs, max images/day
4. **Audit trail**: Log all extraction requests with user + timestamp

### Sensitive Data

**Images may contain**:
- Interior layouts (security risk)
- License plates
- Personal information in signs

**Mitigations**:
- Images stored in private filesystem (not public CDN)
- Access logs for image downloads
- EXIF data stripped (existing: standardizer does this)
- Retention policy (>90 days = archive/delete)

### API Security

When exposing `/api/extraction/` endpoints:

1. Require authentication (OAuth/API key)
2. Rate limit per user (10 jobs/hour)
3. Validate input (source, properties exist)
4. Sanitize error messages (don't expose internal paths)
5. Use HTTPS only

---

## Testing Strategy

### Unit Tests

```python
# Test job model
def test_image_extraction_job_creation():
    job = ImageExtractionJob(properties=["addr"], sources=["zillow"])
    assert job.status == "pending"
    assert job.started_at is None

# Test worker picks up job
def test_worker_processes_job():
    job_id = extraction_queue.enqueue(extract_images_job, ...).id
    # Simulate worker
    worker.work(burst=True)
    job = ImageExtractionJob.get(job_id)
    assert job.status in ["completed", "failed"]

# Test state resumption
def test_extract_resume_from_partial_state():
    state = ExtractionState.from_dict({
        "completed_properties": ["addr1"],
        "failed_properties": [],
        "property_last_checked": {"addr1": "..."}
    })
    # Re-run should skip addr1
    properties = [Property(full_address=addr) for addr in ["addr1", "addr2"]]
    remaining = [p for p in properties if p.full_address not in state.completed_properties]
    assert len(remaining) == 1
```

### Integration Tests

```python
# Test end-to-end job flow
def test_extraction_job_end_to_end(redis_conn, tmp_path):
    # Setup
    queue = Queue(connection=redis_conn)

    # Enqueue
    job = queue.enqueue(extract_images_job,
        job_id=str(uuid4()),
        properties=["4732 W Davis Rd, Glendale, AZ 85306"],
        sources=["zillow"],
        isolation_mode="minimize"
    )

    # Process
    worker = Worker([queue], connection=redis_conn)
    worker.work(burst=True)

    # Verify
    job.refresh()
    assert job.get_status() == "completed"
    assert job.result.total_images > 0
    assert (tmp_path / "property_images" / "processed").exists()
```

---

## Cost & Resource Implications

### Infrastructure Additions

| Component | Cost (AWS) | Purpose |
|-----------|-----------|---------|
| **Redis** (Elasticache small) | $15/mo | Job queue + state |
| **Additional EC2** (t3.medium) | $30/mo | Worker #1 |
| **Prometheus + Grafana** | $10/mo | Monitoring |
| **S3 storage** (500GB images) | $12/mo | Offsite backup |
| **Total** | ~$67/mo | vs. current $0 (local only) |

### Resource Usage

**Per Extraction Job** (5 properties):
- CPU: 40% utilization (async I/O heavy)
- Memory: 500MB (browser, images in RAM)
- Disk I/O: 1GB written
- Network: 200MB downloaded + 100MB upstream
- Duration: 12-18 minutes

**Scaling** (10 concurrent jobs):
- Need: 2x t3.medium workers + Redis
- Total cost: ~$100/month for infrastructure

---

## FAQ & Troubleshooting

### Q: What if worker crashes mid-extraction?

**A**: Job stays in Redis queue. Next worker picks it up. State resumption via `property_last_checked` skips already-processed properties.

### Q: Can I keep synchronous CLI behavior?

**A**: Yes. Option 1: CLI polls job status until done (transparent async). Option 2: Add `--sync` flag for blocking behavior.

### Q: How do I monitor queue depth?

**A**: Prometheus export via `/metrics` endpoint. Key metric: `rq_job_queue_depth{queue="image_extraction"}`.

### Q: What if Redis goes down?

**A**: Jobs in Redis are lost. Mitigation: Use Redis persistence (RDB snapshots). Or fallback to local queue file (less ideal).

### Q: How do I scale to multiple machines?

**A**: All workers point to same Redis instance. Add workers on new machines. Load automatically distributed.

---

## Summary of Recommendations

### Must Have (P0)

1. **Background job queuing** (Redis + RQ or Celery)
2. **Worker architecture** (decouple from CLI)
3. **Job model** with status tracking
4. **API endpoint** for job submission + status polling
5. **Atomic state updates** (preserve existing patterns)

### Should Have (P1)

1. **Monitoring dashboard** (queue depth, success rate, source status)
2. **Graceful job cancellation**
3. **Large batch alerts** (>100 new images console warning)
4. **Adaptive rate limiting** (response-based feedback)
5. **Job retry logic** (exponential backoff, max 3 retries)

### Nice to Have (P2)

1. **Distributed workers** (multi-machine)
2. **Proxy auto-rotation** (health checks)
3. **Storage archival** (old images → cold storage)
4. **User isolation** (per-user quotas, audit trail)
5. **Image categorization** metadata sidecar

---

## Conclusion

The PHX Houses project has **strong foundations** for image extraction and stealth scraping:
- Sophisticated perceptual hashing with LSH optimization
- Robust deduplication and state persistence
- Circuit breaker pattern for resilience
- Clean separation of concerns (extractors, deduplicators, categorizers)

**Critical gap**: Synchronous, single-process architecture limits scalability and user experience. Adding background job queuing + worker processes is essential for production readiness.

**Next step**: Implement Phase 1 (job queuing + worker) in Q1 2025 to unblock multi-user scenario and improve reliability.

---

## References

**Current Code**:
- Image extraction: `src/phx_home_analysis/services/image_extraction/`
- Orchestrator: `src/phx_home_analysis/services/image_extraction/orchestrator.py`
- CLI script: `scripts/extract_images.py`
- Stealth extraction: `src/phx_home_analysis/services/infrastructure/stealth_http_client.py`
- Deduplication: `src/phx_home_analysis/services/image_extraction/deduplicator.py`
- Naming: `src/phx_home_analysis/services/image_extraction/naming.py`

**Metadata**:
- Address lookup: `data/property_images/metadata/address_folder_lookup.json`
- Image manifest: `data/property_images/metadata/image_manifest.json`
- Extraction state: `data/property_images/metadata/extraction_state.json`
- Pipeline runs: `data/property_images/metadata/pipeline_runs.json`

**External Documentation**:
- [RQ (Redis Queue) Documentation](https://python-rq.org/)
- [Celery Distributed Task Queue](https://docs.celeryproject.org/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Locality Sensitive Hashing (LSH)](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [nodriver (UC Browser Automation)](https://github.com/ultrafunkamsterdam/nodriver)


# Architectural Recommendations

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

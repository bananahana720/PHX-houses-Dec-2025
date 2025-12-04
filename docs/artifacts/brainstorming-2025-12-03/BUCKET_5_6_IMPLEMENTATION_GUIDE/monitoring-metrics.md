# Monitoring & Metrics

### Prometheus Metrics Export

**File**: `src/phx_home_analysis/metrics/extraction.py`

```python
"""Prometheus metrics for image extraction."""

from prometheus_client import Counter, Gauge, Histogram

# Job metrics
jobs_created = Counter(
    'extraction_jobs_created_total',
    'Total extraction jobs created',
    ['source']
)

jobs_completed = Counter(
    'extraction_jobs_completed_total',
    'Total extraction jobs completed',
    ['source', 'status']  # status = success|failure
)

job_duration = Histogram(
    'extraction_job_duration_seconds',
    'Job duration in seconds',
    buckets=(60, 300, 600, 1800, 3600)
)

queue_depth = Gauge(
    'extraction_queue_depth',
    'Current queue depth (pending jobs)'
)

images_extracted = Counter(
    'extraction_images_total',
    'Total images extracted',
    ['source', 'status']  # status = new|duplicate
)

# Worker metrics
workers_active = Gauge(
    'extraction_workers_active',
    'Number of active workers'
)

source_circuit_status = Gauge(
    'extraction_source_circuit_open',
    'Circuit breaker status',
    ['source']  # 1 = open, 0 = closed
)
```

**Integration** in job function:
```python
def extract_images_job(...):
    from phx_home_analysis.metrics.extraction import job_duration

    with job_duration.time():
        # ... extraction code ...
```

---

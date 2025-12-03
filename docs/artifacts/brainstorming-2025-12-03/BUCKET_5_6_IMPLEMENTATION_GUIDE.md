# Implementation Guide: Background Job Architecture
## Buckets 5 & 6 - Phase 1 (Q1 2025)

---

## Quick Start: Job Queue Integration

### 1. Dependencies

```bash
# Add to requirements.txt
redis==5.0.0              # Redis client
rq==1.15.0                # Redis Queue
python-rq-dashboard==0.14.0  # Job monitoring UI
prometheus-client==0.19.0  # Metrics export
```

### 2. Redis Setup

**Development** (Docker):
```bash
# Start Redis container
docker run -d -p 6379:6379 --name redis-dev redis:7-alpine

# Test connection
redis-cli ping  # Should print PONG
```

**Production** (AWS ElastiCache):
```bash
# Create small cluster (cache.t3.micro)
# Configure security group to allow access from workers
# Set parameter group: maxmemory-policy=noevict
# Enable automatic backups (daily)
```

### 3. File Structure

```
phx-houses-dec-2025/
├── src/phx_home_analysis/
│   ├── jobs/                 # NEW: Job definitions
│   │   ├── __init__.py
│   │   ├── models.py         # Job dataclass
│   │   └── image_extraction.py  # extract_images_job function
│   ├── workers/              # NEW: Worker processes
│   │   ├── __init__.py
│   │   └── image_extraction.py  # ImageExtractionWorker class
│   ├── api/                  # NEW: REST endpoints (if using Flask/FastAPI)
│   │   ├── __init__.py
│   │   └── extraction_routes.py
│   └── config/
│       ├── settings.py       # MODIFY: Add Redis config
│       └── constants.py
├── scripts/
│   ├── extract_images.py    # MODIFY: Add --sync/--async flags
│   ├── worker_image_extraction.py  # NEW: Start worker process
│   └── api_server.py        # NEW: Start API server (optional)
├── tests/
│   ├── unit/
│   │   └── test_jobs.py    # NEW: Job tests
│   └── integration/
│       └── test_extraction_job.py  # NEW: E2E tests
├── docker/
│   ├── worker.Dockerfile   # NEW: Worker container
│   └── docker-compose.yml  # NEW: Local dev stack
└── docs/
    ├── BACKEND_ARCHITECTURE_ANALYSIS_BUCKETS_5_6.md  # Architecture doc
    └── BUCKET_5_6_IMPLEMENTATION_GUIDE.md  # THIS FILE
```

---

## Step-by-Step Implementation

### Step 1: Job Model (Day 1-2)

**File**: `src/phx_home_analysis/jobs/models.py`

```python
"""Job models for image extraction."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4
import json

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ImageExtractionJob:
    """Represents one image extraction request."""

    # Identification
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # User/context (for multi-user support)
    user_id: Optional[str] = None  # Can add later
    session_id: Optional[str] = None

    # Input
    properties: list[str] = field(default_factory=list)  # Addresses or empty for --all
    sources: list[str] = field(default_factory=lambda: ["zillow", "redfin"])
    isolation_mode: str = "virtual"  # From --isolation arg
    dry_run: bool = False

    # State
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None

    # Progress (updated during execution)
    total_properties: int = 0
    completed_properties: int = 0
    failed_properties: int = 0
    total_images: int = 0
    new_images: int = 0
    duplicate_images: int = 0
    progress_updated_at: datetime = field(default_factory=datetime.now)

    # Results
    failed_properties_list: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON/Redis storage."""
        return {
            k: v.isoformat() if isinstance(v, datetime) else v.value if isinstance(v, Enum) else v
            for k, v in asdict(self).items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ImageExtractionJob':
        """Deserialize from dictionary."""
        # Handle datetime fields
        for field_name in ['created_at', 'started_at', 'completed_at', 'progress_updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        # Handle enum fields
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = JobStatus(data['status'])

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, job_dir: Path = Path("data/jobs")) -> None:
        """Persist job to disk as fallback/audit trail."""
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / f"{self.id}.json"

        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, job_id: str, job_dir: Path = Path("data/jobs")) -> Optional['ImageExtractionJob']:
        """Load job from disk."""
        path = job_dir / f"{job_id}.json"
        if not path.exists():
            return None

        with open(path) as f:
            return cls.from_dict(json.load(f))
```

### Step 2: Redis Queue Setup (Day 2)

**File**: `src/phx_home_analysis/config/settings.py` (ADD section)

```python
"""Redis and job queue configuration."""

from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD")
    url: Optional[str] = os.getenv("REDIS_URL")  # For cloud Redis

    @property
    def connection_string(self) -> str:
        """Get Redis connection string."""
        if self.url:
            return self.url
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

@dataclass
class JobQueueConfig:
    """Job queue configuration."""
    redis_config: RedisConfig = field(default_factory=RedisConfig)
    default_queue_name: str = "image_extraction"
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
    job_timeout: int = int(os.getenv("JOB_TIMEOUT", "3600"))  # 1 hour
    job_result_ttl: int = int(os.getenv("JOB_RESULT_TTL", "604800"))  # 7 days

# Usage:
# queue_config = JobQueueConfig()
# redis_url = queue_config.redis_config.connection_string
```

### Step 3: Job Function (Day 3)

**File**: `src/phx_home_analysis/jobs/image_extraction.py`

```python
"""Job function for image extraction."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from rq import get_current_job
from rq.job import Job

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.services.image_extraction import ImageExtractionOrchestrator

from .models import ImageExtractionJob, JobStatus

logger = logging.getLogger(__name__)

def extract_images_job(job_id: str, properties: list[str], sources: list[str],
                       isolation_mode: str = "virtual", dry_run: bool = False) -> dict:
    """
    Job function for image extraction.

    This runs in worker context. Progress updates are persisted to both:
    1. Redis (for real-time polling)
    2. Job disk file (for audit trail)

    Args:
        job_id: UUID of job
        properties: List of addresses (or empty for --all)
        sources: List of sources to extract from
        isolation_mode: Browser isolation mode
        dry_run: Preview mode without downloading

    Returns:
        Result dict with summary statistics

    Raises:
        Exception: If extraction fails (RQ will mark job as failed)
    """
    # Get job object from RQ for metadata storage
    rq_job = get_current_job()

    # Load or create job model
    job = ImageExtractionJob.load(job_id)
    if not job:
        job = ImageExtractionJob(
            id=job_id,
            properties=properties,
            sources=sources,
            isolation_mode=isolation_mode,
            dry_run=dry_run
        )

    job.status = JobStatus.IN_PROGRESS
    job.started_at = datetime.now()
    job.save()

    try:
        # Load properties from CSV
        repo = CsvPropertyRepository(csv_file_path=Path("data/phx_homes.csv"))

        if properties:
            # Single or multiple specific properties
            all_properties = repo.load_all()
            selected = [p for p in all_properties if p.full_address in properties]
        else:
            # All properties
            selected = repo.load_all()

        logger.info(f"Job {job_id}: Extracting images for {len(selected)} properties")
        job.total_properties = len(selected)
        job.save()

        # Initialize orchestrator
        orchestrator = ImageExtractionOrchestrator(
            base_dir=Path("data/property_images"),
            enabled_sources=[s.lower() for s in sources],
            max_concurrent_properties=3
        )

        # Run extraction (async)
        result = asyncio.run(orchestrator.extract_all(
            properties=selected,
            resume=True
        ))

        # Update job with results
        job.completed_properties = result.properties_completed
        job.failed_properties = result.properties_failed
        job.total_images = result.total_images
        job.new_images = result.unique_images
        job.duplicate_images = result.duplicate_images
        job.failed_properties_list = []  # Could populate from result

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        job.save()

        logger.info(f"Job {job_id}: COMPLETED - {result.total_images} images")

        # Return summary for RQ job result
        return {
            "job_id": job_id,
            "status": "completed",
            "total_properties": result.properties_completed,
            "total_images": result.total_images,
            "new_images": result.unique_images,
            "duplicates": result.duplicate_images,
            "duration_seconds": result.duration_seconds
        }

    except Exception as e:
        logger.error(f"Job {job_id}: FAILED - {str(e)}", exc_info=True)

        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now()
        job.save()

        raise  # RQ will catch and mark job as failed

def extract_images_async(properties: list[str], sources: list[str],
                        isolation_mode: str = "virtual",
                        dry_run: bool = False) -> ImageExtractionJob:
    """
    Enqueue an image extraction job.

    Usage:
        job = extract_images_async(
            properties=["4732 W Davis Rd, Glendale, AZ 85306"],
            sources=["zillow", "redfin"]
        )
        print(f"Job queued: {job.id}")
    """
    from redis import Redis
    from rq import Queue

    from phx_home_analysis.config.settings import JobQueueConfig

    config = JobQueueConfig()
    redis_conn = Redis.from_url(config.redis_config.connection_string)
    queue = Queue("image_extraction", connection=redis_conn)

    job = ImageExtractionJob(
        properties=properties,
        sources=sources,
        isolation_mode=isolation_mode,
        dry_run=dry_run
    )

    # Enqueue job
    rq_job = queue.enqueue(
        extract_images_job,
        job_id=job.id,
        properties=properties,
        sources=sources,
        isolation_mode=isolation_mode,
        dry_run=dry_run,
        job_timeout=3600  # 1 hour
    )

    job.save()  # Also save to disk
    return job
```

### Step 4: Worker Process (Day 3-4)

**File**: `src/phx_home_analysis/workers/image_extraction.py`

```python
"""Worker process for image extraction jobs."""

import logging
from redis import Redis
from rq import Worker, Queue
from rq.job import JobStatus

from phx_home_analysis.config.settings import JobQueueConfig
from phx_home_analysis.jobs.image_extraction import extract_images_job

logger = logging.getLogger(__name__)

class ImageExtractionWorker:
    """Worker process for image extraction jobs."""

    def __init__(self, worker_id: str = "worker-1", max_jobs: int = 1):
        """Initialize worker.

        Args:
            worker_id: Unique identifier for this worker
            max_jobs: Max jobs to process before restart
        """
        self.worker_id = worker_id
        self.max_jobs = max_jobs

        # Setup Redis connection
        config = JobQueueConfig()
        self.redis_conn = Redis.from_url(config.redis_config.connection_string)

        # Create queue and worker
        self.queue = Queue("image_extraction", connection=self.redis_conn)
        self.worker = Worker(
            [self.queue],
            connection=self.redis_conn,
            name=worker_id,
            default_result_ttl=config.job_result_ttl,
            job_timeout=config.job_timeout
        )

        logger.info(f"Worker {worker_id} initialized")

    def start(self):
        """Start consuming jobs from queue."""
        logger.info(f"Worker {self.worker_id}: Starting (max_jobs={self.max_jobs})")

        try:
            self.worker.work(
                with_scheduler=False,
                max_jobs=self.max_jobs,  # Restart after N jobs
                logging_level="INFO"
            )
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id}: Shutdown requested")
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Error - {e}", exc_info=True)
            raise

    def get_status(self) -> dict:
        """Get worker status for monitoring."""
        return {
            "worker_id": self.worker_id,
            "state": self.worker.get_state(),
            "current_job": self.worker.get_current_job(),
            "total_jobs": self.worker.total_jobs if hasattr(self.worker, 'total_jobs') else 0
        }

if __name__ == "__main__":
    import sys

    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = ImageExtractionWorker(worker_id=worker_id)
    worker.start()
```

**Script to start worker**: `scripts/worker_image_extraction.py`

```python
#!/usr/bin/env python
"""Start image extraction worker."""

import logging
import sys
from pathlib import Path

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from phx_home_analysis.workers.image_extraction import ImageExtractionWorker

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = ImageExtractionWorker(worker_id=worker_id, max_jobs=10)
    worker.start()
```

### Step 5: API Endpoints (Day 4-5)

**File**: `src/phx_home_analysis/api/extraction_routes.py`

```python
"""API endpoints for image extraction jobs."""

from datetime import datetime
from uuid import uuid4

from flask import Blueprint, request, jsonify, current_app
from redis import Redis
from rq import Queue

from phx_home_analysis.config.settings import JobQueueConfig
from phx_home_analysis.jobs.models import ImageExtractionJob
from phx_home_analysis.jobs.image_extraction import extract_images_job

extraction_bp = Blueprint('extraction', __name__, url_prefix='/api/extraction')

def get_redis_connection():
    """Get or create Redis connection."""
    if not hasattr(current_app, 'redis'):
        config = JobQueueConfig()
        current_app.redis = Redis.from_url(config.redis_config.connection_string)
    return current_app.redis

@extraction_bp.post('/jobs')
def create_job():
    """Create and enqueue an image extraction job.

    Request JSON:
    {
        "properties": ["4732 W Davis Rd, Glendale, AZ 85306"],  # or empty for --all
        "sources": ["zillow", "redfin"],  # optional, defaults to all
        "isolation_mode": "virtual",  # optional
        "dry_run": false  # optional
    }

    Response (202 Accepted):
    {
        "job_id": "uuid",
        "status": "queued",
        "created_at": "ISO8601"
    }
    """
    data = request.get_json() or {}

    # Validate input
    properties = data.get('properties') or []
    sources = data.get('sources') or ['zillow', 'redfin']
    isolation_mode = data.get('isolation_mode', 'virtual')
    dry_run = data.get('dry_run', False)

    # Create job
    job_id = str(uuid4())
    job = ImageExtractionJob(
        id=job_id,
        properties=properties,
        sources=sources,
        isolation_mode=isolation_mode,
        dry_run=dry_run
    )

    # Enqueue
    redis = get_redis_connection()
    queue = Queue('image_extraction', connection=redis)

    rq_job = queue.enqueue(
        extract_images_job,
        job_id=job_id,
        properties=properties,
        sources=sources,
        isolation_mode=isolation_mode,
        dry_run=dry_run,
        job_timeout=3600
    )

    # Save job metadata
    job.save()

    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'created_at': job.created_at.isoformat()
    }), 202

@extraction_bp.get('/jobs/<job_id>')
def get_job(job_id):
    """Get job status and progress.

    Response (200 OK):
    {
        "job_id": "uuid",
        "status": "in_progress|completed|failed",
        "progress": {
            "total_properties": 5,
            "completed_properties": 2,
            "failed_properties": 0,
            "total_images": 150,
            "new_images": 120,
            "duplicate_images": 30
        },
        "started_at": "ISO8601",
        "completed_at": null,
        "error": null
    }
    """
    # Load job from disk
    job = ImageExtractionJob.load(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'job_id': job.id,
        'status': job.status.value,
        'progress': {
            'total_properties': job.total_properties,
            'completed_properties': job.completed_properties,
            'failed_properties': job.failed_properties,
            'total_images': job.total_images,
            'new_images': job.new_images,
            'duplicate_images': job.duplicate_images
        },
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error': job.error_message
    }), 200

@extraction_bp.delete('/jobs/<job_id>')
def cancel_job(job_id):
    """Cancel a job.

    Response (200 OK):
    {
        "job_id": "uuid",
        "status": "cancelled"
    }
    """
    redis = get_redis_connection()
    queue = Queue('image_extraction', connection=redis)

    # Get RQ job and delete it
    from rq.job import Job
    rq_job = Job.fetch(job_id, connection=redis)
    rq_job.cancel()

    # Mark job as cancelled
    job = ImageExtractionJob.load(job_id)
    if job:
        from phx_home_analysis.jobs.models import JobStatus
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        job.save()

    return jsonify({
        'job_id': job_id,
        'status': 'cancelled'
    }), 200

def register_routes(app):
    """Register extraction routes with Flask app."""
    app.register_blueprint(extraction_bp)
```

### Step 6: CLI Integration (Day 5)

**Modify**: `scripts/extract_images.py`

Add arguments for job mode:

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(...)

    # ... existing args ...

    # Job mode
    parser.add_argument(
        "--async",
        action="store_true",
        help="Run as background job (enqueue and return immediately)"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        help="Check status of existing job (requires --async)"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        default=True,
        help="Wait for job completion (default for backward compatibility)"
    )

    return parser.parse_args()

async def main() -> int:
    args = parse_args()

    # ... existing validation ...

    # Check job status if requested
    if args.job_id:
        from phx_home_analysis.jobs.models import ImageExtractionJob
        job = ImageExtractionJob.load(args.job_id)
        if not job:
            print(f"Job not found: {args.job_id}", file=sys.stderr)
            return 1

        print(f"Job {job.id}: {job.status.value}")
        print(f"  Progress: {job.completed_properties}/{job.total_properties} properties")
        print(f"  Images: {job.total_images} total, {job.new_images} new")
        if job.error_message:
            print(f"  Error: {job.error_message}")
        return 0 if job.status.value == "completed" else 1

    # Async mode: enqueue and return
    if args.async:
        from phx_home_analysis.jobs.image_extraction import extract_images_async

        # Determine properties
        if args.all:
            properties = []
        else:
            properties = [args.address]

        job = extract_images_async(
            properties=properties,
            sources=enabled_sources or None,
            isolation_mode=isolation_mode,
            dry_run=args.dry_run
        )

        print(f"Job enqueued: {job.id}")
        print(f"Check status: python scripts/extract_images.py --job-id {job.id}")
        return 0

    # Sync mode (default, for backward compatibility)
    # ... existing async/await code ...
```

---

## Testing

### Unit Tests

**File**: `tests/unit/test_jobs.py`

```python
"""Tests for job model and functions."""

import pytest
from datetime import datetime
from phx_home_analysis.jobs.models import ImageExtractionJob, JobStatus

def test_job_creation():
    job = ImageExtractionJob(
        properties=["addr1"],
        sources=["zillow"]
    )
    assert job.status == JobStatus.PENDING
    assert job.started_at is None
    assert job.total_properties == 0

def test_job_serialization():
    job = ImageExtractionJob(properties=["addr1"])
    data = job.to_dict()
    assert isinstance(data, dict)
    assert data['properties'] == ["addr1"]

    # Should be able to deserialize
    job2 = ImageExtractionJob.from_dict(data)
    assert job2.id == job.id
    assert job2.properties == job.properties

def test_job_progress_update():
    job = ImageExtractionJob()
    job.total_properties = 5
    job.completed_properties = 2
    job.total_images = 100
    job.save()

    # Should be able to load
    loaded = ImageExtractionJob.load(job.id)
    assert loaded.completed_properties == 2
    assert loaded.total_images == 100
```

### Integration Tests

**File**: `tests/integration/test_extraction_job.py`

```python
"""Integration tests for extraction job end-to-end."""

import pytest
from unittest.mock import patch, MagicMock
from rq.job import JobStatus as RQJobStatus
from phx_home_analysis.jobs.image_extraction import extract_images_job
from phx_home_analysis.jobs.models import ImageExtractionJob, JobStatus

@pytest.fixture
def mock_rq_job():
    """Mock RQ job context."""
    with patch('phx_home_analysis.jobs.image_extraction.get_current_job') as mock:
        mock.return_value = MagicMock()
        yield mock

def test_extraction_job_success(mock_rq_job, tmp_path):
    """Test extraction job completes successfully."""
    # Setup mock orchestrator
    with patch('phx_home_analysis.jobs.image_extraction.ImageExtractionOrchestrator') as mock_orch:
        mock_result = MagicMock()
        mock_result.properties_completed = 1
        mock_result.properties_failed = 0
        mock_result.total_images = 50
        mock_result.unique_images = 45
        mock_result.duplicate_images = 5
        mock_result.duration_seconds = 120

        mock_orch.return_value.extract_all = MagicMock(return_value=mock_result)

        # Run job
        result = extract_images_job(
            job_id="test-job",
            properties=["addr1"],
            sources=["zillow"]
        )

        # Verify results
        assert result['status'] == 'completed'
        assert result['total_images'] == 50
        assert result['new_images'] == 45

        # Verify job state persisted
        job = ImageExtractionJob.load("test-job")
        assert job.status == JobStatus.COMPLETED
        assert job.completed_properties == 1
```

---

## Deployment

### Docker Compose (Development)

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  worker:
    build:
      context: ..
      dockerfile: docker/worker.Dockerfile
    depends_on:
      redis:
        condition: service_healthy
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      LOG_LEVEL: INFO
    volumes:
      - ../data:/app/data
      - ../src:/app/src
    restart: always

  rq-dashboard:
    image: eoranged/rq-dashboard:latest
    ports:
      - "9181:9181"
    depends_on:
      - redis
    environment:
      RQ_DASHBOARD_REDIS_URL: redis://redis:6379

volumes:
  redis_data:
```

**File**: `docker/worker.Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src /app/src
COPY scripts /app/scripts
COPY data /app/data

# Set Python path
ENV PYTHONPATH=/app

# Start worker
CMD ["python", "-m", "phx_home_analysis.workers.image_extraction", "docker-worker"]
```

**Usage**:
```bash
# Start stack
docker-compose -f docker/docker-compose.yml up

# View RQ Dashboard
# http://localhost:9181

# Stop
docker-compose -f docker/docker-compose.yml down
```

---

## Monitoring & Metrics

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

## Next Steps

1. **Week 1-2**: Implement steps 1-3 (job model, Redis, job function)
2. **Week 3**: Implement step 4 (worker)
3. **Week 4**: Implement steps 5-6 (API, CLI integration)
4. **Week 5**: Testing, Docker setup, monitoring
5. **Week 6**: Documentation, training, production deployment

---

## Troubleshooting

### Q: Worker not processing jobs?

**A**: Check:
1. Redis connection: `redis-cli ping`
2. Queue name matches: "image_extraction" in both job and worker
3. Worker logs: `docker logs <worker_container>`
4. RQ Dashboard: http://localhost:9181 (if using docker-compose)

### Q: Job stuck in pending?

**A**:
1. Start worker: `python scripts/worker_image_extraction.py`
2. Check Redis: `redis-cli llen rq:queue:image_extraction`
3. Check job: `redis-cli get rq:job:<job_id>:status`

### Q: Large batch alerts not showing?

**A**: Add to orchestrator summary printing:
```python
if result.unique_images > 100:
    print("\n" + "=" * 70)
    print("WARNING: Large batch of new images")
    # ... detailed output ...
```

---

## References

- [RQ Documentation](https://python-rq.org/docs/)
- [Redis Python Client](https://github.com/redis/redis-py)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Flask Blueprints](https://flask.palletsprojects.com/blueprints/)


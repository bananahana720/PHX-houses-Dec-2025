# job_queue/CLAUDE.md

---
last_updated: 2025-12-03
updated_by: Claude Code
staleness_hours: 72
---

## Purpose

Persistent job queue service for the image extraction pipeline. Provides durable, resumable job processing with real-time progress visibility integrated with `work_items.json`.

### Key Benefits
- **Crash Resilience**: Jobs survive process crashes and restarts
- **Non-Blocking**: Submit jobs and continue working
- **Progress Visibility**: Real-time status in `work_items.json`
- **Configurable Concurrency**: Respect rate limits and system resources
- **Retry Logic**: Exponential backoff for transient failures

## Contents

| File | Purpose |
|------|---------|
| `__init__.py` | Public API exports |
| `models.py` | Job, JobStatus, JobResult, JobQueueState dataclasses |
| `queue.py` | JobQueue - persistent job storage and CRUD |
| `executor.py` | JobExecutor - async worker pool with retry logic |
| `progress.py` | ProgressTracker - work_items.json integration |
| `integration.py` | Bridge to ImageExtractionOrchestrator |

## Architecture

```
                                    +-----------------+
                                    | work_items.json |
                                    +--------+--------+
                                             ^
                                             | sync
                                    +--------+--------+
 +-------------+    enqueue    +----+ ProgressTracker +----+
 |   CLI       +-------------->+    +-----------------+    |
 | --queue     |               |                           |
 +-------------+               |    +---------------+      |
                               |    |   JobQueue    |      |
                               |    | (persistent)  |<-----+
                               |    +-------+-------+
                               |            |
                               |    +-------v-------+
                               |    |  JobExecutor  |
                               |    | (async pool)  |
                               |    +-------+-------+
                               |            |
                               |    +-------v-------+
                               +----+   Handlers    |
                                    | (extraction)  |
                                    +---------------+
```

## Quick Reference

### CLI Usage

```bash
# Queue mode (persistent, resumable)
python scripts/extract_images.py --all --queue

# Single property
python scripts/extract_images.py --address "123 Main St" --queue

# Check status
python scripts/extract_images.py --status

# Custom concurrency
python scripts/extract_images.py --all --queue --max-concurrent 10

# Retry failed jobs
python scripts/extract_images.py --retry-failed

# Clear queue
python scripts/extract_images.py --clear-queue
```

### Programmatic Usage

```python
from phx_home_analysis.services.job_queue import (
    JobQueue,
    JobExecutor,
    JobType,
    create_extraction_handler,
)

# Create queue
queue = JobQueue(state_file=Path("data/job_queue.json"))

# Enqueue jobs
job = queue.enqueue("123 Main St", sources=["zillow"])
jobs = queue.enqueue_batch(["Addr 1", "Addr 2", "Addr 3"])

# Create executor
executor = JobExecutor(queue, max_concurrent=5)

# Register handler
handler = create_extraction_handler()
executor.register_handler(JobType.IMAGE_EXTRACTION, handler)

# Run (blocking until complete)
await executor.start()

# Or run in background
from phx_home_analysis.services.job_queue import BackgroundExecutor
bg = BackgroundExecutor(queue)
await bg.start()  # Returns immediately
# ... do other work ...
await bg.stop()
```

### Status Checking

```python
from phx_home_analysis.services.job_queue import (
    get_queue_status,
    format_queue_status,
)

status = get_queue_status()
print(format_queue_status(status))

# Output:
# ============================================================
# Job Queue Status
# ============================================================
#
# Pending:   5
# Running:   2
# Completed: 10
# Failed:    1
# Total:     18
# ETA:       3m 45s
# ...
```

## Job Lifecycle

```
PENDING ─────────────────────────────────────────────────────────┐
    │                                                            │
    v                                                            │
RUNNING ──────────────────┬──────────────────┬──────────────────┤
    │                     │                  │                  │
    │ success             │ failure          │ cancelled        │
    v                     v                  v                  │
COMPLETED             RETRYING ─────────> FAILED              CANCELLED
                          │                  ^
                          │ retry            │ max retries
                          └──────────────────┘
```

### State Transitions

| From | To | Trigger |
|------|----|---------|
| PENDING | RUNNING | Executor picks up job |
| RUNNING | COMPLETED | Handler returns success |
| RUNNING | RETRYING | Handler fails, retries remain |
| RUNNING | FAILED | Handler fails, no retries |
| RUNNING | CANCELLED | User/system cancellation |
| RETRYING | RUNNING | Retry attempt begins |
| RETRYING | FAILED | Max retries exceeded |

## Job Model

```python
@dataclass
class Job:
    id: str                    # 8-char UUID prefix
    job_type: JobType          # IMAGE_EXTRACTION, COUNTY_DATA, etc.
    address: str               # Property address
    sources: list[str]         # ["zillow", "redfin"]
    status: JobStatus          # PENDING, RUNNING, etc.
    priority: int              # Higher = processed first
    created_at: str            # ISO timestamp
    started_at: str | None     # When execution began
    completed_at: str | None   # When finished (success/fail)
    progress: JobProgress      # Real-time progress tracking
    result: JobResult | None   # Outcome data
    error: str | None          # Error message if failed
    retry_count: int           # Current retry attempt
    max_retries: int           # Max attempts (default: 3)
```

### JobProgress

```python
@dataclass
class JobProgress:
    percent: float          # 0.0 - 1.0
    current_step: str       # "Downloading from Zillow"
    items_completed: int    # 5
    items_total: int        # 10
    current_source: str     # "zillow"
```

### JobResult

```python
@dataclass
class JobResult:
    success: bool
    images_extracted: int
    duplicates_detected: int
    errors: list[str]
    sources_completed: dict[str, int]
    duration_seconds: float
```

## Integration with work_items.json

The `ProgressTracker` synchronizes job progress with `work_items.json`:

```json
{
  "work_items": [
    {
      "address": "123 Main St",
      "extraction_progress": {
        "job_id": "abc12345",
        "status": "running",
        "percent": 0.5,
        "current_step": "Downloading from Zillow",
        "current_source": "zillow",
        "items_completed": 15,
        "items_total": 30,
        "started_at": "2025-12-03T10:00:00Z",
        "last_update": "2025-12-03T10:05:00Z"
      },
      "phases": {
        "phase1_listing": {
          "status": "in_progress"
        }
      }
    }
  ],
  "extraction_stats": {
    "total_jobs": 20,
    "pending": 8,
    "running": 2,
    "completed": 9,
    "failed": 1,
    "avg_duration_seconds": 45.2,
    "estimated_remaining_seconds": 360
  }
}
```

## Executor Configuration

### Concurrency

```python
executor = JobExecutor(
    queue,
    max_concurrent=5,          # Max parallel jobs
    min_retry_delay=1.0,       # Initial backoff (seconds)
    max_retry_delay=60.0,      # Max backoff cap
    retry_jitter=0.5,          # Randomization factor
)
```

### Retry Logic

Uses exponential backoff with jitter:
```
delay = min(min_delay * 2^retry_count, max_delay)
delay += delay * jitter * random()
```

Example with defaults (1s min, 60s max, 0.5 jitter):
- Retry 1: 1-1.5s
- Retry 2: 2-3s
- Retry 3: 4-6s
- ...capped at 60-90s

## Persistence

### Queue State File (data/job_queue.json)

```json
{
  "version": "1.0.0",
  "created_at": "2025-12-03T00:00:00Z",
  "updated_at": "2025-12-03T10:05:00Z",
  "total_submitted": 50,
  "total_completed": 40,
  "total_failed": 2,
  "jobs": [
    { "id": "abc12345", "address": "...", "status": "pending", ... }
  ]
}
```

### Atomic Writes

All state files use atomic writes (temp file + rename) to prevent corruption from crashes.

## Error Handling

### Transient vs Permanent Failures

Handlers should return `JobResult(success=False, errors=[...])` for failures:
- Transient failures (network, rate limiting) trigger retry
- Permanent failures (property not found) should set `max_retries=0` or use `can_retry=False`

### Stuck Job Recovery

Jobs stuck in RUNNING state (process crash) are automatically reset on executor startup:

```python
# Reset jobs running > 1 hour
queue.reset_stuck_jobs(timeout_seconds=3600)
```

## Testing

```bash
# Run tests
pytest tests/unit/services/test_job_queue.py -v

# With coverage
pytest tests/unit/services/test_job_queue.py --cov=src/phx_home_analysis/services/job_queue
```

## Key Learnings

1. **Deduplication**: `enqueue()` returns existing job if address already queued and not terminal
2. **Priority Ordering**: Higher priority jobs processed first, then FIFO within same priority
3. **Retry Jobs First**: Jobs in RETRYING state processed before PENDING
4. **Progress Callbacks**: Non-blocking - use `asyncio.create_task()` for callbacks
5. **State Locking**: Queue mutations are single-process safe; multi-process needs external lock

## Dependencies

### Uses
- `phx_home_analysis.services.image_extraction.ImageExtractionOrchestrator`
- `phx_home_analysis.repositories.csv_repository.CsvPropertyRepository`
- `data/work_items.json` (via ProgressTracker)

### Used By
- `scripts/extract_images.py` (--queue mode)
- `.claude/agents/listing-browser.md` (potential future integration)

## References

- Job queue models: `models.py:1-400`
- Queue operations: `queue.py:1-450`
- Executor: `executor.py:1-350`
- Progress tracking: `progress.py:1-300`
- Integration: `integration.py:1-200`
- Tests: `tests/unit/services/test_job_queue.py`

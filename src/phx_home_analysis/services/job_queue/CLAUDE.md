---
last_updated: 2025-12-04T00:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# job_queue

## Purpose
Persistent, async job queue for image extraction pipeline. Provides durable job storage (survives crashes), semaphore-based concurrency control, exponential backoff retry logic, and real-time progress syncing to `work_items.json`.

## Contents
| File | Purpose |
|------|---------|
| `queue.py` | Persistent queue state with atomic writes; job CRUD and lifecycle |
| `executor.py` | Async worker pool with semaphore, retry logic, progress callbacks |
| `models.py` | Job, JobStatus, JobProgress, JobResult, JobQueueState dataclasses |
| `progress.py` | ProgressTracker - syncs job state to work_items.json |
| `integration.py` | Handler factory for ImageExtractionOrchestrator |
| `__init__.py` | Public exports (JobQueue, JobExecutor, BackgroundExecutor, etc.) |

## Key Patterns
- **Atomic persistence**: Temp file + rename prevents corruption from crashes
- **Race condition guard** (executor.py:167-169): Skip if job already in active_jobs dict before acquiring semaphore
- **Exponential backoff**: min_delay × 2^retry_count + jitter, capped at max_delay
- **Priority ordering**: RETRYING jobs before PENDING; then by priority+FIFO

## Recent Change
**executor.py:167-169** - Added race condition prevention: check `if job.id in self._active_jobs` before semaphore.acquire() to prevent duplicate processing in concurrent loops.

## Tasks
- [ ] Add multi-process locking for shared queue scenarios `P:M`
- [ ] Implement job batching UI for progress dashboard `P:L`
- [ ] Add metrics export (Prometheus format) `P:L`

## Learnings
- **Job deduplication**: enqueue() returns existing if address queued and not terminal (idempotent)
- **Stuck job recovery**: Executor auto-resets jobs stuck in RUNNING >1hr on start()
- **State locking**: Single-process safe via JSON atomicity; multi-process needs external lock

## Refs
- Job lifecycle: `models.py:22-50`
- Queue CRUD: `queue.py:137-516`
- Executor loop: `executor.py:113-190`
- Progress syncing: `progress.py`
- Integration: `integration.py:39+`

## Deps
← Imports from:
  - `phx_home_analysis.services.image_extraction.ImageExtractionOrchestrator`
  - `phx_home_analysis.repositories.csv_repository.CsvPropertyRepository`
  - `data/work_items.json` (via ProgressTracker)

→ Used by:
  - `scripts/extract_images.py --queue` (CLI)
  - Integration tests

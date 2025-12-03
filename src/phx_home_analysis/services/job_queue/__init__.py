"""Job queue service for persistent, resumable extraction jobs.

Provides a file-based job queue with:
- Persistent storage (survives crashes)
- Async execution with concurrency control
- Exponential backoff retry logic
- Progress tracking integrated with work_items.json
- Real-time visibility into extraction status

Architecture:
    JobQueue (queue.py)
        Persistent job storage with atomic writes
        Job lifecycle management (enqueue, update, query)

    JobExecutor (executor.py)
        Async worker pool with semaphore-based concurrency
        Retry logic with exponential backoff
        Progress callbacks for visibility

    ProgressTracker (progress.py)
        Real-time updates to work_items.json
        Phase status synchronization
        Aggregate statistics

    Integration (integration.py)
        Bridge to ImageExtractionOrchestrator
        Convenience functions for common operations

Usage:
    # Direct queue usage
    from phx_home_analysis.services.job_queue import JobQueue, Job

    queue = JobQueue()
    job = queue.enqueue("123 Main St", sources=["zillow"])
    pending = queue.get_pending()
    queue.update_progress(job.id, percent=0.5)

    # Full extraction pipeline
    from phx_home_analysis.services.job_queue import run_queued_extraction

    results = await run_queued_extraction(max_concurrent=5)

    # Check status
    from phx_home_analysis.services.job_queue import (
        get_queue_status,
        format_queue_status,
    )

    status = get_queue_status()
    print(format_queue_status(status))

See Also:
    - scripts/extract_images.py: CLI interface
    - .claude/skills/state-management/SKILL.md: State management patterns
"""

from .executor import BackgroundExecutor, JobExecutor
from .integration import (
    create_batch_extraction_jobs,
    create_extraction_handler,
    format_queue_status,
    get_queue_status,
    run_queued_extraction,
)
from .models import Job, JobProgress, JobQueueState, JobResult, JobStatus, JobType
from .progress import (
    ProgressTracker,
    create_completion_callback,
    create_progress_callback,
)
from .queue import JobQueue

__all__ = [
    # Models
    "Job",
    "JobStatus",
    "JobType",
    "JobProgress",
    "JobResult",
    "JobQueueState",
    # Queue
    "JobQueue",
    # Executor
    "JobExecutor",
    "BackgroundExecutor",
    # Progress
    "ProgressTracker",
    "create_progress_callback",
    "create_completion_callback",
    # Integration
    "create_extraction_handler",
    "create_batch_extraction_jobs",
    "run_queued_extraction",
    "get_queue_status",
    "format_queue_status",
]

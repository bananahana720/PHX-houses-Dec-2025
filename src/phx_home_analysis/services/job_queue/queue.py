"""Persistent job queue with file-based storage.

Provides a durable job queue that survives process crashes and restarts.
Jobs are persisted to JSON with atomic writes to prevent corruption.

Features:
    - Persistent storage with atomic writes (temp file + rename)
    - Job deduplication by address
    - Priority-based ordering
    - Query methods for different job states
    - Statistics and health monitoring

Thread Safety:
    This queue is designed for single-process use with asyncio.
    For multi-process scenarios, external locking would be required.

Usage:
    queue = JobQueue(Path("data/job_queue.json"))
    job = queue.enqueue("123 Main St", sources=["zillow", "redfin"])
    pending = queue.get_pending()
    queue.update_job(job.id, status=JobStatus.RUNNING)
"""

import json
import logging
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .models import Job, JobQueueState, JobResult, JobStatus, JobType

logger = logging.getLogger(__name__)


class JobQueue:
    """Persistent job queue with file-based storage.

    Jobs are stored in a JSON file and survive process restarts.
    All write operations use atomic file replacement to prevent
    corruption from crashes.

    Attributes:
        state_file: Path to the queue state JSON file
        state: Current queue state (loaded on init)
    """

    def __init__(
        self,
        state_file: Path | str = Path("data/job_queue.json"),
        auto_save: bool = True,
    ):
        """Initialize the job queue.

        Args:
            state_file: Path to persistent state file
            auto_save: If True, save after every mutation
        """
        self.state_file = Path(state_file)
        self.auto_save = auto_save
        self.state = self._load_state()
        self._job_index: dict[str, Job] = {}
        self._rebuild_index()

    def _load_state(self) -> JobQueueState:
        """Load queue state from disk.

        Returns:
            JobQueueState (empty if file doesn't exist or is corrupted)
        """
        if not self.state_file.exists():
            logger.info(f"Creating new job queue at {self.state_file}")
            return JobQueueState()

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            state = JobQueueState.from_dict(data)
            logger.info(
                f"Loaded job queue: {len(state.jobs)} jobs, "
                f"{sum(1 for j in state.jobs if j.status == JobStatus.PENDING)} pending"
            )
            return state
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load job queue: {e}")
            # Try to preserve corrupted file for debugging
            if self.state_file.exists():
                backup_path = self.state_file.with_suffix(".json.corrupted")
                try:
                    self.state_file.rename(backup_path)
                    logger.info(f"Backed up corrupted queue to {backup_path}")
                except OSError:
                    pass
            return JobQueueState()

    def _save_state(self) -> None:
        """Save queue state to disk atomically.

        Uses temp file + rename pattern to prevent corruption from
        crashes during write.
        """
        self.state.updated_at = datetime.now(timezone.utc).isoformat()

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write using temp file + rename
        fd, temp_path = tempfile.mkstemp(
            dir=self.state_file.parent,
            prefix="job_queue_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, indent=2)
            os.replace(temp_path, self.state_file)
            logger.debug("Saved job queue state")
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _rebuild_index(self) -> None:
        """Rebuild job index from state."""
        self._job_index = {job.id: job for job in self.state.jobs}

    def _maybe_save(self) -> None:
        """Save if auto_save is enabled."""
        if self.auto_save:
            self._save_state()

    # -------------------------------------------------------------------------
    # Job Submission
    # -------------------------------------------------------------------------

    def enqueue(
        self,
        address: str,
        sources: list[str] | None = None,
        job_type: JobType = JobType.IMAGE_EXTRACTION,
        priority: int = 0,
        metadata: dict | None = None,
        max_retries: int = 3,
    ) -> Job:
        """Add a job to the queue.

        If a job for this address already exists and is not in a terminal
        state, returns the existing job (no duplicate).

        Args:
            address: Property address
            sources: List of extraction sources (default: all)
            job_type: Type of job
            priority: Higher priority jobs are processed first
            metadata: Additional job data
            max_retries: Max retry attempts on failure

        Returns:
            The created or existing Job
        """
        # Check for existing non-terminal job for this address
        existing = self.get_job_by_address(address)
        if existing and not existing.status.is_terminal():
            logger.info(f"Job already exists for {address}: {existing.id}")
            return existing

        # Create new job
        job = Job(
            job_type=job_type,
            address=address,
            sources=sources or [],
            priority=priority,
            metadata=metadata or {},
            max_retries=max_retries,
        )

        self.state.jobs.append(job)
        self._job_index[job.id] = job
        self.state.total_submitted += 1

        self._maybe_save()

        logger.info(f"Enqueued job {job.id} for {address}")
        return job

    def enqueue_batch(
        self,
        addresses: list[str],
        sources: list[str] | None = None,
        job_type: JobType = JobType.IMAGE_EXTRACTION,
        priority: int = 0,
    ) -> list[Job]:
        """Add multiple jobs to the queue.

        Skips addresses that already have non-terminal jobs.

        Args:
            addresses: List of property addresses
            sources: List of extraction sources
            job_type: Type of job
            priority: Job priority

        Returns:
            List of created or existing Jobs
        """
        jobs = []
        for address in addresses:
            job = self.enqueue(
                address=address,
                sources=sources,
                job_type=job_type,
                priority=priority,
            )
            jobs.append(job)

        logger.info(f"Enqueued batch of {len(jobs)} jobs")
        return jobs

    # -------------------------------------------------------------------------
    # Job Retrieval
    # -------------------------------------------------------------------------

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job or None if not found
        """
        return self._job_index.get(job_id)

    def get_job_by_address(self, address: str) -> Job | None:
        """Get the most recent job for an address.

        Args:
            address: Property address

        Returns:
            Most recent Job for this address or None
        """
        # Search in reverse order to find most recent
        for job in reversed(self.state.jobs):
            if job.address == address:
                return job
        return None

    def get_pending(self, limit: int | None = None) -> list[Job]:
        """Get pending jobs ordered by priority (highest first).

        Args:
            limit: Maximum jobs to return

        Returns:
            List of pending Jobs sorted by priority
        """
        pending = [j for j in self.state.jobs if j.status == JobStatus.PENDING]
        # Sort by priority (descending), then by created_at (ascending)
        pending.sort(key=lambda j: (-j.priority, j.created_at))

        if limit:
            return pending[:limit]
        return pending

    def get_running(self) -> list[Job]:
        """Get currently running jobs.

        Returns:
            List of jobs in RUNNING or RETRYING state
        """
        return [j for j in self.state.jobs if j.status.is_active()]

    def get_retrying(self) -> list[Job]:
        """Get jobs waiting to retry.

        Returns:
            List of jobs in RETRYING state
        """
        return [j for j in self.state.jobs if j.status == JobStatus.RETRYING]

    def get_completed(self, limit: int | None = None) -> list[Job]:
        """Get completed jobs, most recent first.

        Args:
            limit: Maximum jobs to return

        Returns:
            List of completed Jobs
        """
        completed = [j for j in self.state.jobs if j.status == JobStatus.COMPLETED]
        completed.sort(key=lambda j: j.completed_at or "", reverse=True)

        if limit:
            return completed[:limit]
        return completed

    def get_failed(self, limit: int | None = None) -> list[Job]:
        """Get failed jobs, most recent first.

        Args:
            limit: Maximum jobs to return

        Returns:
            List of failed Jobs
        """
        failed = [j for j in self.state.jobs if j.status == JobStatus.FAILED]
        failed.sort(key=lambda j: j.completed_at or "", reverse=True)

        if limit:
            return failed[:limit]
        return failed

    def get_all(self) -> list[Job]:
        """Get all jobs.

        Returns:
            List of all Jobs
        """
        return list(self.state.jobs)

    def filter_jobs(
        self,
        predicate: Callable[[Job], bool],
        limit: int | None = None,
    ) -> list[Job]:
        """Filter jobs using a predicate function.

        Args:
            predicate: Function that takes a Job and returns bool
            limit: Maximum jobs to return

        Returns:
            Filtered list of Jobs
        """
        result = [j for j in self.state.jobs if predicate(j)]
        if limit:
            return result[:limit]
        return result

    # -------------------------------------------------------------------------
    # Job Updates
    # -------------------------------------------------------------------------

    def update_job(self, job_id: str, **updates) -> Job | None:
        """Update job fields.

        Args:
            job_id: Job identifier
            **updates: Field names and values to update

        Returns:
            Updated Job or None if not found

        Supported updates:
            - status: JobStatus
            - progress: JobProgress or dict
            - result: JobResult or dict
            - error: str
            - Any other Job field
        """
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return None

        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
            else:
                logger.warning(f"Unknown job field: {key}")

        self._maybe_save()
        return job

    def mark_running(self, job_id: str) -> Job | None:
        """Mark a job as running.

        Args:
            job_id: Job identifier

        Returns:
            Updated Job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.mark_running()
        self._maybe_save()

        logger.info(f"Job {job_id} started: {job.address}")
        return job

    def mark_completed(self, job_id: str, result: JobResult) -> Job | None:
        """Mark a job as completed.

        Args:
            job_id: Job identifier
            result: Job result data

        Returns:
            Updated Job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.mark_completed(result)
        self.state.total_completed += 1
        self._maybe_save()

        logger.info(
            f"Job {job_id} completed: {result.images_extracted} images "
            f"in {result.duration_seconds:.1f}s"
        )
        return job

    def mark_failed(
        self,
        job_id: str,
        error: str,
        can_retry: bool = True,
    ) -> Job | None:
        """Mark a job as failed.

        If can_retry is True and retries remain, moves to RETRYING state.
        Otherwise moves to FAILED state.

        Args:
            job_id: Job identifier
            error: Error message
            can_retry: Whether to attempt retry

        Returns:
            Updated Job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.mark_failed(error, can_retry)

        if job.status == JobStatus.FAILED:
            self.state.total_failed += 1

        self._maybe_save()

        if job.status == JobStatus.RETRYING:
            logger.info(f"Job {job_id} will retry ({job.retry_count}/{job.max_retries}): {error}")
        else:
            logger.error(f"Job {job_id} failed permanently: {error}")

        return job

    def mark_cancelled(self, job_id: str) -> Job | None:
        """Mark a job as cancelled.

        Args:
            job_id: Job identifier

        Returns:
            Updated Job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.mark_cancelled()
        self._maybe_save()

        logger.info(f"Job {job_id} cancelled")
        return job

    def update_progress(
        self,
        job_id: str,
        percent: float | None = None,
        current_step: str | None = None,
        items_completed: int | None = None,
        items_total: int | None = None,
        current_source: str | None = None,
    ) -> Job | None:
        """Update job progress.

        Args:
            job_id: Job identifier
            percent: Completion percentage (0.0 - 1.0)
            current_step: Description of current operation
            items_completed: Number of items processed
            items_total: Total items to process
            current_source: Current extraction source

        Returns:
            Updated Job or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        job.update_progress(
            percent=percent,
            current_step=current_step,
            items_completed=items_completed,
            items_total=items_total,
            current_source=current_source,
        )

        # Don't auto-save on every progress update (too expensive)
        # Caller can save explicitly if needed
        return job

    # -------------------------------------------------------------------------
    # Queue Management
    # -------------------------------------------------------------------------

    def clear_completed(self, keep_recent: int = 100) -> int:
        """Remove old completed jobs.

        Args:
            keep_recent: Number of recent completed jobs to keep

        Returns:
            Number of jobs removed
        """
        completed = [j for j in self.state.jobs if j.status == JobStatus.COMPLETED]
        completed.sort(key=lambda j: j.completed_at or "", reverse=True)

        to_remove = set(j.id for j in completed[keep_recent:])
        original_count = len(self.state.jobs)

        self.state.jobs = [j for j in self.state.jobs if j.id not in to_remove]
        self._rebuild_index()

        removed = original_count - len(self.state.jobs)
        if removed > 0:
            self._maybe_save()
            logger.info(f"Cleared {removed} old completed jobs")

        return removed

    def clear_failed(self) -> int:
        """Remove all failed jobs.

        Returns:
            Number of jobs removed
        """
        original_count = len(self.state.jobs)
        self.state.jobs = [j for j in self.state.jobs if j.status != JobStatus.FAILED]
        self._rebuild_index()

        removed = original_count - len(self.state.jobs)
        if removed > 0:
            self._maybe_save()
            logger.info(f"Cleared {removed} failed jobs")

        return removed

    def reset_stuck_jobs(self, timeout_seconds: int = 3600) -> int:
        """Reset jobs stuck in RUNNING state.

        Jobs that have been running longer than timeout_seconds are
        reset to PENDING or RETRYING state.

        Args:
            timeout_seconds: Max seconds a job can run before reset

        Returns:
            Number of jobs reset
        """
        reset_count = 0
        now = datetime.now(timezone.utc)

        for job in self.state.jobs:
            if job.status == JobStatus.RUNNING and job.started_at:
                started = datetime.fromisoformat(job.started_at)
                elapsed = (now - started).total_seconds()

                if elapsed > timeout_seconds:
                    if job.can_retry():
                        job.status = JobStatus.RETRYING
                        job.retry_count += 1
                        job.error = f"Timed out after {elapsed:.0f}s"
                    else:
                        job.mark_failed("Timed out (max retries exceeded)")
                    reset_count += 1

        if reset_count > 0:
            self._maybe_save()
            logger.warning(f"Reset {reset_count} stuck jobs")

        return reset_count

    def retry_failed(self, job_id: str | None = None) -> int:
        """Retry failed jobs.

        Args:
            job_id: Specific job to retry, or None for all failed

        Returns:
            Number of jobs reset for retry
        """
        reset_count = 0

        for job in self.state.jobs:
            if job_id and job.id != job_id:
                continue

            if job.status == JobStatus.FAILED:
                job.status = JobStatus.PENDING
                job.retry_count = 0
                job.error = None
                job.result = None
                job.started_at = None
                job.completed_at = None
                reset_count += 1

        if reset_count > 0:
            self._maybe_save()
            logger.info(f"Reset {reset_count} failed jobs for retry")

        return reset_count

    def clear_all(self) -> None:
        """Clear all jobs and reset state.

        WARNING: This removes all job history.
        """
        self.state = JobQueueState()
        self._rebuild_index()
        self._save_state()
        logger.warning("Cleared all jobs from queue")

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Get queue statistics.

        Returns:
            Dict with job counts, timing, and health metrics
        """
        return self.state.get_stats()

    def get_next_job(self) -> Job | None:
        """Get the next job to process.

        Returns highest priority pending job, or a job waiting to retry.

        Returns:
            Job to process or None if queue is empty
        """
        # First check for jobs that need retry
        retrying = self.get_retrying()
        if retrying:
            # Return oldest retry first
            retrying.sort(key=lambda j: j.last_retry_at or "")
            return retrying[0]

        # Then get next pending job
        pending = self.get_pending(limit=1)
        if pending:
            return pending[0]

        return None

    def save(self) -> None:
        """Explicitly save queue state.

        Use when auto_save is disabled or after batch updates.
        """
        self._save_state()

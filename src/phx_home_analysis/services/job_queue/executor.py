"""Async job executor with concurrency control and retry logic.

Provides a worker pool that processes jobs from the queue with:
- Configurable concurrency limits
- Exponential backoff for retries
- Graceful shutdown support
- Progress callbacks for visibility
- Error isolation (one job failure doesn't affect others)

Usage:
    queue = JobQueue()
    executor = JobExecutor(queue, max_concurrent=5)

    # Start processing (non-blocking)
    await executor.start()

    # Or process with callback
    async def on_progress(job):
        print(f"{job.address}: {job.progress.percent:.0%}")

    await executor.start(on_progress=on_progress)

    # Graceful shutdown
    await executor.stop()
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine

from .models import Job, JobResult, JobStatus, JobType
from .queue import JobQueue

logger = logging.getLogger(__name__)


# Type alias for job handler functions
JobHandler = Callable[[Job, "JobExecutor"], Coroutine[Any, Any, JobResult]]

# Type alias for progress callbacks
ProgressCallback = Callable[[Job], Coroutine[Any, Any, None]]


class JobExecutor:
    """Async job executor with worker pool.

    Manages concurrent job execution with:
    - Semaphore-based concurrency control
    - Exponential backoff retry logic
    - Progress tracking and callbacks
    - Graceful shutdown support

    Attributes:
        queue: JobQueue instance
        max_concurrent: Maximum parallel jobs
        running: Whether executor is running
        handlers: Dict of JobType -> handler function
    """

    def __init__(
        self,
        queue: JobQueue,
        max_concurrent: int = 5,
        min_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        retry_jitter: float = 0.5,
    ):
        """Initialize the executor.

        Args:
            queue: JobQueue to process
            max_concurrent: Maximum concurrent jobs
            min_retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds
            retry_jitter: Randomization factor for retry delays (0-1)
        """
        self.queue = queue
        self.max_concurrent = max_concurrent
        self.min_retry_delay = min_retry_delay
        self.max_retry_delay = max_retry_delay
        self.retry_jitter = retry_jitter

        self._running = False
        self._stop_event = asyncio.Event()
        self._semaphore: asyncio.Semaphore | None = None
        self._active_jobs: dict[str, asyncio.Task] = {}
        self._handlers: dict[JobType, JobHandler] = {}
        self._on_progress: ProgressCallback | None = None
        self._on_complete: ProgressCallback | None = None

    @property
    def running(self) -> bool:
        """Check if executor is running."""
        return self._running

    def register_handler(
        self,
        job_type: JobType,
        handler: JobHandler,
    ) -> None:
        """Register a handler for a job type.

        Args:
            job_type: Type of job to handle
            handler: Async function that takes (Job, JobExecutor) and returns JobResult
        """
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for {job_type.value}")

    async def start(
        self,
        on_progress: ProgressCallback | None = None,
        on_complete: ProgressCallback | None = None,
        process_existing: bool = True,
    ) -> None:
        """Start the executor.

        Begins processing jobs from the queue. This method runs until
        stop() is called or all jobs are complete.

        Args:
            on_progress: Callback for job progress updates
            on_complete: Callback when a job completes
            process_existing: If True, process existing pending jobs
        """
        if self._running:
            logger.warning("Executor already running")
            return

        self._running = True
        self._stop_event.clear()
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._on_progress = on_progress
        self._on_complete = on_complete

        logger.info(
            f"Starting executor with {self.max_concurrent} workers"
        )

        # Reset any stuck jobs from previous runs
        stuck_count = self.queue.reset_stuck_jobs(timeout_seconds=3600)
        if stuck_count:
            logger.warning(f"Reset {stuck_count} stuck jobs from previous run")

        try:
            while self._running:
                # Check for stop signal
                if self._stop_event.is_set():
                    break

                # Get next job
                job = self.queue.get_next_job()

                if not job:
                    # No pending jobs - check if any are running
                    if not self._active_jobs:
                        logger.info("No jobs to process, exiting")
                        break
                    # Wait for running jobs to complete
                    await asyncio.sleep(0.5)
                    continue

                # Acquire semaphore and start job
                await self._semaphore.acquire()

                # Create task for this job
                task = asyncio.create_task(self._process_job(job))
                self._active_jobs[job.id] = task

                # Clean up completed tasks
                self._cleanup_completed_tasks()

        except asyncio.CancelledError:
            logger.info("Executor cancelled")
        finally:
            # Wait for active jobs to complete
            if self._active_jobs:
                logger.info(f"Waiting for {len(self._active_jobs)} active jobs")
                await asyncio.gather(*self._active_jobs.values(), return_exceptions=True)

            self._running = False
            self._active_jobs.clear()

    async def stop(self, wait: bool = True, timeout: float = 30.0) -> None:
        """Stop the executor gracefully.

        Args:
            wait: If True, wait for running jobs to complete
            timeout: Maximum seconds to wait for jobs
        """
        logger.info("Stopping executor...")
        self._stop_event.set()

        if wait and self._active_jobs:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_jobs.values(), return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout waiting for {len(self._active_jobs)} jobs, "
                    "cancelling remaining tasks"
                )
                for task in self._active_jobs.values():
                    task.cancel()

        self._running = False
        logger.info("Executor stopped")

    async def process_job(
        self,
        job: Job,
        handler: JobHandler | None = None,
    ) -> JobResult:
        """Process a single job directly.

        For use when you want to process a specific job outside the
        normal queue flow (e.g., for testing or one-off execution).

        Args:
            job: Job to process
            handler: Handler to use (falls back to registered handler)

        Returns:
            JobResult from processing
        """
        if handler:
            return await self._execute_with_handler(job, handler)
        return await self._execute_job(job)

    async def _process_job(self, job: Job) -> None:
        """Process a job with retry logic.

        This is the internal job processing method that handles:
        - State transitions (pending -> running -> complete/failed)
        - Retry logic with exponential backoff
        - Progress callbacks
        - Error handling

        Args:
            job: Job to process
        """
        try:
            # Mark as running
            self.queue.mark_running(job.id)

            # Notify progress
            if self._on_progress:
                await self._on_progress(job)

            # Execute the job
            result = await self._execute_job(job)

            # Mark as complete or failed
            if result.success:
                self.queue.mark_completed(job.id, result)
            else:
                error_msg = "; ".join(result.errors) if result.errors else "Unknown error"
                self.queue.mark_failed(job.id, error_msg, can_retry=True)

                # Handle retry with backoff
                if job.status == JobStatus.RETRYING:
                    delay = self._calculate_retry_delay(job.retry_count)
                    logger.info(
                        f"Job {job.id} will retry in {delay:.1f}s "
                        f"(attempt {job.retry_count}/{job.max_retries})"
                    )
                    await asyncio.sleep(delay)

            # Notify completion
            if self._on_complete:
                await self._on_complete(job)

        except asyncio.CancelledError:
            logger.info(f"Job {job.id} cancelled")
            self.queue.mark_cancelled(job.id)
            raise

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}", exc_info=True)
            self.queue.mark_failed(job.id, str(e), can_retry=True)

        finally:
            # Release semaphore
            if self._semaphore:
                self._semaphore.release()

            # Remove from active jobs
            self._active_jobs.pop(job.id, None)

    async def _execute_job(self, job: Job) -> JobResult:
        """Execute job using registered handler.

        Args:
            job: Job to execute

        Returns:
            JobResult from handler
        """
        handler = self._handlers.get(job.job_type)
        if not handler:
            logger.error(f"No handler registered for job type: {job.job_type}")
            return JobResult(
                success=False,
                errors=[f"No handler for job type: {job.job_type}"],
            )

        return await self._execute_with_handler(job, handler)

    async def _execute_with_handler(
        self,
        job: Job,
        handler: JobHandler,
    ) -> JobResult:
        """Execute job with a specific handler.

        Args:
            job: Job to execute
            handler: Handler function to use

        Returns:
            JobResult from handler
        """
        start_time = time.time()

        try:
            result = await handler(job, self)
            result.duration_seconds = time.time() - start_time
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Handler error for {job.id}: {e}", exc_info=True)
            return JobResult(
                success=False,
                errors=[str(e)],
                duration_seconds=duration,
            )

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay before next retry using exponential backoff.

        Args:
            retry_count: Number of retries so far

        Returns:
            Delay in seconds
        """
        # Exponential backoff: min_delay * 2^retry_count
        delay = self.min_retry_delay * (2 ** retry_count)
        delay = min(delay, self.max_retry_delay)

        # Add jitter to prevent thundering herd
        if self.retry_jitter > 0:
            jitter = delay * self.retry_jitter * random.random()
            delay += jitter

        return delay

    def _cleanup_completed_tasks(self) -> None:
        """Remove completed tasks from active jobs dict."""
        completed = [
            job_id
            for job_id, task in self._active_jobs.items()
            if task.done()
        ]
        for job_id in completed:
            del self._active_jobs[job_id]

    def update_job_progress(
        self,
        job_id: str,
        percent: float | None = None,
        current_step: str | None = None,
        items_completed: int | None = None,
        items_total: int | None = None,
        current_source: str | None = None,
    ) -> None:
        """Update progress for an active job.

        Convenience method for handlers to report progress.

        Args:
            job_id: Job ID to update
            percent: Completion percentage (0.0 - 1.0)
            current_step: Description of current operation
            items_completed: Items processed so far
            items_total: Total items to process
            current_source: Current source being processed
        """
        job = self.queue.update_progress(
            job_id,
            percent=percent,
            current_step=current_step,
            items_completed=items_completed,
            items_total=items_total,
            current_source=current_source,
        )

        # Trigger progress callback if set
        if job and self._on_progress:
            asyncio.create_task(self._on_progress(job))

    def get_active_jobs(self) -> list[Job]:
        """Get list of currently active jobs.

        Returns:
            List of jobs being processed
        """
        return [
            job
            for job in self.queue.get_running()
            if job.id in self._active_jobs
        ]

    def get_stats(self) -> dict:
        """Get executor statistics.

        Returns:
            Dict with execution stats
        """
        queue_stats = self.queue.get_stats()
        return {
            **queue_stats,
            "running": self._running,
            "active_jobs": len(self._active_jobs),
            "max_concurrent": self.max_concurrent,
        }


class BackgroundExecutor:
    """Executor that runs in the background.

    Wraps JobExecutor to run in a background task, allowing
    non-blocking job submission and monitoring.

    Usage:
        bg_executor = BackgroundExecutor(queue)
        await bg_executor.start()

        # Submit jobs
        job = queue.enqueue("123 Main St")

        # Check status
        stats = bg_executor.get_stats()

        # Stop when done
        await bg_executor.stop()
    """

    def __init__(
        self,
        queue: JobQueue,
        max_concurrent: int = 5,
    ):
        """Initialize background executor.

        Args:
            queue: JobQueue to process
            max_concurrent: Maximum concurrent jobs
        """
        self.executor = JobExecutor(queue, max_concurrent)
        self._task: asyncio.Task | None = None

    def register_handler(self, job_type: JobType, handler: JobHandler) -> None:
        """Register a handler for a job type."""
        self.executor.register_handler(job_type, handler)

    async def start(
        self,
        on_progress: ProgressCallback | None = None,
        on_complete: ProgressCallback | None = None,
    ) -> None:
        """Start background processing.

        Returns immediately after starting the background task.
        """
        if self._task and not self._task.done():
            logger.warning("Background executor already running")
            return

        self._task = asyncio.create_task(
            self.executor.start(
                on_progress=on_progress,
                on_complete=on_complete,
            )
        )
        logger.info("Started background executor")

    async def stop(self, wait: bool = True, timeout: float = 30.0) -> None:
        """Stop background processing."""
        await self.executor.stop(wait=wait, timeout=timeout)
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            self._task = None

    @property
    def running(self) -> bool:
        """Check if background executor is running."""
        return self._task is not None and not self._task.done()

    def get_stats(self) -> dict:
        """Get executor statistics."""
        return self.executor.get_stats()

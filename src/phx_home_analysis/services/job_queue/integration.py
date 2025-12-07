"""Integration with existing extraction pipeline.

Bridges the job queue system with the existing ImageExtractionOrchestrator,
providing a handler function that the executor can use to process jobs.

Usage:
    from phx_home_analysis.services.job_queue import (
        JobQueue,
        JobExecutor,
        create_extraction_handler,
    )

    queue = JobQueue()
    executor = JobExecutor(queue)

    # Register the extraction handler
    handler = create_extraction_handler(output_dir=Path("data/property_images"))
    executor.register_handler(JobType.IMAGE_EXTRACTION, handler)

    # Start processing
    await executor.start()
"""

import logging
import time
from pathlib import Path
from typing import Any

from ...domain.enums import ImageSource
from ...repositories.csv_repository import CsvPropertyRepository
from ..image_extraction import ImageExtractionOrchestrator
from .executor import JobExecutor
from .models import Job, JobResult, JobType

logger = logging.getLogger(__name__)


def create_extraction_handler(
    output_dir: Path = Path("data/property_images"),
    csv_path: Path = Path("data/phx_homes.csv"),
    max_concurrent_sources: int = 3,
    deduplication_threshold: int = 8,
) -> "JobHandler":
    """Create an extraction handler for the job executor.

    The handler integrates with the existing ImageExtractionOrchestrator
    to perform the actual image extraction work.

    Args:
        output_dir: Directory for extracted images
        csv_path: Path to properties CSV
        max_concurrent_sources: Max parallel source extractions
        deduplication_threshold: Hamming distance for duplicates

    Returns:
        Async handler function for image extraction jobs
    """
    # Load property repository
    repo = CsvPropertyRepository(csv_file_path=csv_path)

    async def extraction_handler(job: Job, executor: JobExecutor) -> JobResult:
        """Handle image extraction job.

        Args:
            job: Job to process
            executor: Executor for progress updates

        Returns:
            JobResult with extraction statistics
        """
        start_time = time.time()
        errors: list[str] = []
        sources_completed: dict[str, int] = {}

        try:
            # Find the property
            property = repo.load_by_address(job.address)
            if not property:
                return JobResult(
                    success=False,
                    errors=[f"Property not found: {job.address}"],
                    duration_seconds=time.time() - start_time,
                )

            # Parse sources from job
            enabled_sources = None
            if job.sources:
                source_map = {
                    "maricopa_assessor": ImageSource.MARICOPA_ASSESSOR,
                    "zillow": ImageSource.ZILLOW,
                    "redfin": ImageSource.REDFIN,
                    "phoenix_mls": ImageSource.PHOENIX_MLS,
                }
                enabled_sources = [source_map[s] for s in job.sources if s in source_map]

            # Create orchestrator
            orchestrator = ImageExtractionOrchestrator(
                base_dir=output_dir,
                enabled_sources=enabled_sources,
                max_concurrent_properties=1,  # Single property
                deduplication_threshold=deduplication_threshold,
            )

            # Update job progress
            executor.update_job_progress(
                job.id,
                percent=0.1,
                current_step="Starting extraction",
                items_total=len(orchestrator.enabled_sources),
            )

            # Run extraction
            result = await orchestrator.extract_all(
                properties=[property],
                resume=True,
                incremental=True,
            )

            # Update progress to complete
            executor.update_job_progress(
                job.id,
                percent=1.0,
                current_step="Complete",
                items_completed=len(orchestrator.enabled_sources),
            )

            # Build sources completed dict
            for source_name, stats in result.by_source.items():
                sources_completed[source_name] = stats.images_downloaded

            # Check for failures
            if result.properties_failed > 0:
                errors.append("Extraction had failures")

            return JobResult(
                success=result.properties_completed > 0,
                images_extracted=result.unique_images,
                duplicates_detected=result.duplicate_images,
                errors=errors,
                sources_completed=sources_completed,
                duration_seconds=result.duration_seconds,
                metadata={
                    "total_images": result.total_images,
                    "failed_downloads": result.failed_downloads,
                },
            )

        except Exception as e:
            logger.error(f"Extraction error for {job.address}: {e}", exc_info=True)
            return JobResult(
                success=False,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    return extraction_handler


def create_batch_extraction_jobs(
    queue: "JobQueue",
    addresses: list[str] | None = None,
    sources: list[str] | None = None,
    csv_path: Path = Path("data/phx_homes.csv"),
) -> list[Job]:
    """Create extraction jobs for multiple properties.

    Args:
        queue: JobQueue to add jobs to
        addresses: Specific addresses (None = all from CSV)
        sources: Extraction sources to use
        csv_path: Path to properties CSV

    Returns:
        List of created/existing jobs
    """
    if addresses is None:
        # Load all addresses from CSV
        repo = CsvPropertyRepository(csv_file_path=csv_path)
        properties = repo.load_all()
        addresses = [p.full_address for p in properties]

    return queue.enqueue_batch(
        addresses=addresses,
        sources=sources,
        job_type=JobType.IMAGE_EXTRACTION,
    )


async def run_queued_extraction(
    addresses: list[str] | None = None,
    sources: list[str] | None = None,
    max_concurrent: int = 5,
    output_dir: Path = Path("data/property_images"),
    csv_path: Path = Path("data/phx_homes.csv"),
    queue_path: Path = Path("data/job_queue.json"),
    work_items_path: Path = Path("data/work_items.json"),
) -> dict[str, Any]:
    """Run extraction using the job queue system.

    Convenience function that sets up the full queue/executor/tracker
    stack and runs extraction.

    Args:
        addresses: Specific addresses (None = all)
        sources: Extraction sources
        max_concurrent: Maximum parallel jobs
        output_dir: Image output directory
        csv_path: Properties CSV path
        queue_path: Job queue state path
        work_items_path: Work items path

    Returns:
        Dict with execution statistics
    """
    from .progress import (
        ProgressTracker,
        create_completion_callback,
        create_progress_callback,
    )
    from .queue import JobQueue

    # Initialize components
    queue = JobQueue(state_file=queue_path)
    tracker = ProgressTracker(work_items_path=work_items_path, queue=queue)

    # Create jobs
    jobs = create_batch_extraction_jobs(
        queue=queue,
        addresses=addresses,
        sources=sources,
        csv_path=csv_path,
    )

    logger.info(f"Created {len(jobs)} extraction jobs")

    # Create executor
    from .executor import JobExecutor

    executor = JobExecutor(queue, max_concurrent=max_concurrent)

    # Register handler
    handler = create_extraction_handler(
        output_dir=output_dir,
        csv_path=csv_path,
    )
    executor.register_handler(JobType.IMAGE_EXTRACTION, handler)

    # Create callbacks
    on_progress = create_progress_callback(tracker)
    on_complete = create_completion_callback(tracker)

    # Run extraction
    start_time = time.time()
    await executor.start(
        on_progress=on_progress,
        on_complete=on_complete,
    )
    duration = time.time() - start_time

    # Get final stats
    stats = queue.get_stats()

    return {
        "jobs_submitted": len(jobs),
        "jobs_completed": stats.get("completed_count", 0),
        "jobs_failed": stats.get("failed_count", 0),
        "duration_seconds": duration,
        "queue_stats": stats,
    }


def get_queue_status(
    queue_path: Path = Path("data/job_queue.json"),
) -> dict[str, Any]:
    """Get current queue status.

    Args:
        queue_path: Path to queue state file

    Returns:
        Dict with queue status information
    """
    from .queue import JobQueue

    queue = JobQueue(state_file=queue_path, auto_save=False)
    stats = queue.get_stats()

    # Get active job details
    running = queue.get_running()
    pending = queue.get_pending(limit=5)

    return {
        "stats": stats,
        "running_jobs": [
            {
                "id": j.id,
                "address": j.address,
                "progress": j.progress.percent,
                "current_step": j.progress.current_step,
                "elapsed_seconds": j.elapsed_seconds(),
            }
            for j in running
        ],
        "next_pending": [
            {
                "id": j.id,
                "address": j.address,
                "priority": j.priority,
                "created_at": j.created_at,
            }
            for j in pending
        ],
    }


def format_queue_status(status: dict[str, Any]) -> str:
    """Format queue status for display.

    Args:
        status: Status dict from get_queue_status()

    Returns:
        Formatted string for console output
    """
    stats = status.get("stats", {})
    running = status.get("running_jobs", [])
    pending = status.get("next_pending", [])

    lines = [
        "=" * 60,
        "Job Queue Status",
        "=" * 60,
        "",
        f"Pending:   {stats.get('pending_count', 0)}",
        f"Running:   {stats.get('running_count', 0)}",
        f"Completed: {stats.get('completed_count', 0)}",
        f"Failed:    {stats.get('failed_count', 0)}",
        f"Total:     {stats.get('total_jobs', 0)}",
    ]

    if stats.get("estimated_remaining_seconds"):
        mins = int(stats["estimated_remaining_seconds"] // 60)
        secs = int(stats["estimated_remaining_seconds"] % 60)
        lines.append(f"ETA:       {mins}m {secs}s")

    if running:
        lines.append("")
        lines.append("Running Jobs:")
        for job in running:
            elapsed = int(job.get("elapsed_seconds", 0))
            lines.append(
                f"  [{job['id']}] {job['address'][:40]} - {job['progress']:.0%} ({elapsed}s)"
            )

    if pending:
        lines.append("")
        lines.append("Next Pending:")
        for job in pending[:3]:
            lines.append(f"  [{job['id']}] {job['address'][:50]}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)

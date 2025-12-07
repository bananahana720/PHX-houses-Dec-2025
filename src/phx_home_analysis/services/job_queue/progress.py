"""Progress tracking with work_items.json integration.

Provides real-time progress updates to the pipeline state file,
enabling visibility into extraction progress from external tools
and the multi-agent orchestration system.

Features:
    - Real-time updates to work_items.json
    - Aggregate statistics for batch operations
    - ETA calculation based on historical performance
    - Phase status synchronization

Integration:
    The ProgressTracker bridges the job queue with the pipeline
    state tracking system. When a job completes, it updates both:
    1. The job queue (job_queue.json)
    2. The pipeline state (work_items.json)

Usage:
    tracker = ProgressTracker()
    tracker.update_extraction_progress(job)
    tracker.update_phase_status("123 Main St", "phase1_listing", "completed")
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Job, JobStatus
from .queue import JobQueue

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Real-time progress updates to work_items.json.

    Synchronizes job queue progress with the pipeline state file
    that the multi-agent orchestrator uses for tracking.

    Attributes:
        work_items_path: Path to work_items.json
        queue: Optional JobQueue for aggregate stats
    """

    def __init__(
        self,
        work_items_path: Path | str = Path("data/work_items.json"),
        queue: JobQueue | None = None,
    ):
        """Initialize the progress tracker.

        Args:
            work_items_path: Path to work_items.json
            queue: JobQueue for aggregate statistics
        """
        self.work_items_path = Path(work_items_path)
        self.queue = queue

    def _load_work_items(self) -> dict[str, Any]:
        """Load work_items.json.

        Returns:
            Work items data or empty structure if file doesn't exist
        """
        if not self.work_items_path.exists():
            return {
                "session": {},
                "work_items": [],
                "summary": {},
            }

        try:
            with open(self.work_items_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load work_items.json: {e}")
            return {
                "session": {},
                "work_items": [],
                "summary": {},
            }

    def _save_work_items(self, data: dict[str, Any]) -> None:
        """Save work_items.json atomically.

        Args:
            data: Work items data to save
        """
        self.work_items_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=self.work_items_path.parent,
            prefix="work_items_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.work_items_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _find_work_item(
        self,
        data: dict[str, Any],
        address: str,
    ) -> tuple[int, dict[str, Any] | None]:
        """Find work item by address.

        Args:
            data: Work items data
            address: Property address

        Returns:
            Tuple of (index, work_item) or (-1, None) if not found
        """
        for idx, item in enumerate(data.get("work_items", [])):
            if item.get("address") == address:
                return idx, item
        return -1, None

    def update_extraction_progress(self, job: Job) -> None:
        """Update work_items.json with current extraction progress.

        Adds/updates an 'extraction_progress' section for the property
        with current job status and progress.

        Args:
            job: Job with current progress
        """
        data = self._load_work_items()
        idx, work_item = self._find_work_item(data, job.address)

        if idx == -1:
            logger.debug(f"Work item not found for {job.address}, skipping update")
            return

        # Update or create extraction_progress section
        if "extraction_progress" not in work_item:
            work_item["extraction_progress"] = {}

        progress = work_item["extraction_progress"]
        progress["job_id"] = job.id
        progress["status"] = job.status.value
        progress["percent"] = job.progress.percent
        progress["current_step"] = job.progress.current_step
        progress["current_source"] = job.progress.current_source
        progress["items_completed"] = job.progress.items_completed
        progress["items_total"] = job.progress.items_total
        progress["retry_count"] = job.retry_count
        progress["started_at"] = job.started_at
        progress["last_update"] = datetime.now(timezone.utc).isoformat()

        if job.result:
            progress["images_extracted"] = job.result.images_extracted
            progress["duplicates_detected"] = job.result.duplicates_detected
            progress["errors"] = job.result.errors[:5]  # Limit error list

        if job.error:
            progress["error"] = job.error

        # Update the work item
        data["work_items"][idx] = work_item
        self._save_work_items(data)

        logger.debug(
            f"Updated extraction progress for {job.address}: "
            f"{job.progress.percent:.0%} ({job.status.value})"
        )

    def update_phase_status(
        self,
        address: str,
        phase: str,
        status: str,
        completed_at: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update phase status for a property.

        Args:
            address: Property address
            phase: Phase name (e.g., "phase1_listing")
            status: Phase status ("pending", "in_progress", "completed", "failed")
            completed_at: ISO timestamp if completed
            error: Error message if failed
        """
        data = self._load_work_items()
        idx, work_item = self._find_work_item(data, address)

        if idx == -1:
            logger.debug(f"Work item not found for {address}")
            return

        # Ensure phases dict exists
        if "phases" not in work_item:
            work_item["phases"] = {}

        # Update phase
        if phase not in work_item["phases"]:
            work_item["phases"][phase] = {}

        work_item["phases"][phase]["status"] = status

        if completed_at:
            work_item["phases"][phase]["completed"] = completed_at

        if error:
            work_item["phases"][phase]["error"] = error

        # Update work item status based on phases
        work_item["last_updated"] = datetime.now(timezone.utc).isoformat()
        work_item["status"] = self._calculate_work_item_status(work_item)

        data["work_items"][idx] = work_item
        self._update_summary(data)
        self._save_work_items(data)

        logger.info(f"Updated {phase} for {address}: {status}")

    def _calculate_work_item_status(self, work_item: dict[str, Any]) -> str:
        """Calculate overall work item status from phases.

        Args:
            work_item: Work item dict

        Returns:
            Overall status string
        """
        phases = work_item.get("phases", {})

        # Check for any failed phases
        if any(p.get("status") == "failed" for p in phases.values()):
            return "failed"

        # Check for any in_progress phases
        if any(p.get("status") == "in_progress" for p in phases.values()):
            return "in_progress"

        # Check if all required phases are complete
        required_phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
        ]
        if all(phases.get(p, {}).get("status") == "completed" for p in required_phases):
            return "complete"

        # Otherwise pending
        return "pending"

    def _update_summary(self, data: dict[str, Any]) -> None:
        """Update the summary section of work_items.json.

        Args:
            data: Work items data
        """
        work_items = data.get("work_items", [])

        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "complete": 0,
            "completed": 0,
            "failed": 0,
            "blocked": 0,
        }

        for item in work_items:
            status = item.get("status", "pending")
            if status in status_counts:
                status_counts[status] += 1

        # Combine complete and completed
        status_counts["completed"] += status_counts.pop("complete", 0)

        data["summary"] = {
            "total_properties": len(work_items),
            **status_counts,
        }

    def update_aggregate_stats(self) -> None:
        """Update aggregate job statistics in work_items.json.

        Uses the queue to calculate overall progress and ETA.
        """
        if not self.queue:
            return

        stats = self.queue.get_stats()
        data = self._load_work_items()

        # Add or update extraction_stats section
        data["extraction_stats"] = {
            "total_jobs": stats.get("total_jobs", 0),
            "pending": stats.get("pending_count", 0),
            "running": stats.get("running_count", 0),
            "completed": stats.get("completed_count", 0),
            "failed": stats.get("failed_count", 0),
            "avg_duration_seconds": stats.get("avg_duration_seconds", 0),
            "estimated_remaining_seconds": stats.get("estimated_remaining_seconds"),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        self._save_work_items(data)
        logger.debug("Updated aggregate extraction stats")

    def sync_job_completion(self, job: Job) -> None:
        """Sync job completion to work_items.json phase status.

        When a job completes (success or failure), updates the
        corresponding phase in work_items.json.

        Args:
            job: Completed job
        """
        # Map job type to phase name
        phase_map = {
            "image_extraction": "phase1_listing",
            "county_data": "phase0_county",
            "map_analysis": "phase1_map",
            "scoring": "phase3_synthesis",
        }

        phase = phase_map.get(job.job_type.value)
        if not phase:
            logger.debug(f"No phase mapping for job type: {job.job_type}")
            return

        if job.status == JobStatus.COMPLETED:
            self.update_phase_status(
                address=job.address,
                phase=phase,
                status="completed",
                completed_at=job.completed_at,
            )
        elif job.status == JobStatus.FAILED:
            self.update_phase_status(
                address=job.address,
                phase=phase,
                status="failed",
                error=job.error,
            )
        elif job.status.is_active():
            self.update_phase_status(
                address=job.address,
                phase=phase,
                status="in_progress",
            )

    def get_extraction_summary(self) -> dict[str, Any]:
        """Get extraction progress summary.

        Returns:
            Dict with extraction statistics
        """
        data = self._load_work_items()
        work_items = data.get("work_items", [])

        # Count properties by extraction status
        extraction_status = {
            "not_started": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
        }

        total_images = 0
        for item in work_items:
            progress = item.get("extraction_progress", {})
            status = progress.get("status", "pending")

            if status == "completed":
                extraction_status["completed"] += 1
                total_images += progress.get("images_extracted", 0)
            elif status in ("running", "retrying"):
                extraction_status["in_progress"] += 1
            elif status == "failed":
                extraction_status["failed"] += 1
            else:
                extraction_status["not_started"] += 1

        return {
            "total_properties": len(work_items),
            **extraction_status,
            "total_images_extracted": total_images,
            "aggregate_stats": data.get("extraction_stats", {}),
        }


def create_progress_callback(
    tracker: ProgressTracker,
) -> "ProgressCallback":
    """Create a progress callback for the executor.

    Args:
        tracker: ProgressTracker instance

    Returns:
        Async callback function for job progress
    """

    async def on_progress(job: Job) -> None:
        tracker.update_extraction_progress(job)

    return on_progress


def create_completion_callback(
    tracker: ProgressTracker,
) -> "ProgressCallback":
    """Create a completion callback for the executor.

    Args:
        tracker: ProgressTracker instance

    Returns:
        Async callback function for job completion
    """

    async def on_complete(job: Job) -> None:
        tracker.sync_job_completion(job)
        tracker.update_aggregate_stats()

    return on_complete

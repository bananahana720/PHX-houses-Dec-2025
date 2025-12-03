"""Job queue data models for extraction pipeline.

Defines the core data structures for persistent job queue management:
- Job: Individual work item with state tracking
- JobStatus: State machine for job lifecycle
- JobResult: Outcome container for completed/failed jobs
- JobQueueState: Persistent queue state for crash recovery

Security:
    - All datetime fields use timezone-aware ISO format
    - Job IDs use secure random generation (UUID)
    - Serialization handles None values safely
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class JobStatus(str, Enum):
    """Job lifecycle states.

    State transitions:
        PENDING -> RUNNING (executor picks up job)
        RUNNING -> COMPLETED (success)
        RUNNING -> FAILED (unrecoverable error)
        RUNNING -> RETRYING (transient failure, will retry)
        RUNNING -> CANCELLED (user/system cancellation)
        RETRYING -> RUNNING (retry attempt begins)
        RETRYING -> FAILED (max retries exceeded)

    Note: PENDING is the only valid initial state.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

    def is_terminal(self) -> bool:
        """Check if this is a terminal state (no further transitions)."""
        return self in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    def is_active(self) -> bool:
        """Check if job is currently being processed."""
        return self in (JobStatus.RUNNING, JobStatus.RETRYING)


class JobType(str, Enum):
    """Types of jobs supported by the queue.

    IMAGE_EXTRACTION: Extract images from listing sources (Zillow, Redfin, etc.)
    COUNTY_DATA: Extract data from Maricopa County Assessor API
    MAP_ANALYSIS: Geographic analysis (schools, safety, orientation)
    SCORING: Calculate property scores and tier classification
    """

    IMAGE_EXTRACTION = "image_extraction"
    COUNTY_DATA = "county_data"
    MAP_ANALYSIS = "map_analysis"
    SCORING = "scoring"


@dataclass
class JobProgress:
    """Progress tracking for a running job.

    Attributes:
        percent: Completion percentage (0.0 - 1.0)
        current_step: Human-readable description of current operation
        items_completed: Number of items processed
        items_total: Total items to process
        current_source: For multi-source jobs, the active source
        last_update: Timestamp of last progress update
    """

    percent: float = 0.0
    current_step: str = ""
    items_completed: int = 0
    items_total: int = 0
    current_source: str | None = None
    last_update: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "percent": self.percent,
            "current_step": self.current_step,
            "items_completed": self.items_completed,
            "items_total": self.items_total,
            "current_source": self.current_source,
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobProgress":
        """Create from dictionary."""
        return cls(
            percent=data.get("percent", 0.0),
            current_step=data.get("current_step", ""),
            items_completed=data.get("items_completed", 0),
            items_total=data.get("items_total", 0),
            current_source=data.get("current_source"),
            last_update=data.get(
                "last_update", datetime.now(timezone.utc).isoformat()
            ),
        )


@dataclass
class JobResult:
    """Outcome of a completed or failed job.

    Attributes:
        success: Whether job completed successfully
        images_extracted: Number of unique images saved (for extraction jobs)
        duplicates_detected: Number of duplicate images skipped
        errors: List of error messages encountered
        sources_completed: Dict of source name -> images extracted
        duration_seconds: Total execution time
        metadata: Additional result data (e.g., listing metadata)
    """

    success: bool = True
    images_extracted: int = 0
    duplicates_detected: int = 0
    errors: list[str] = field(default_factory=list)
    sources_completed: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "images_extracted": self.images_extracted,
            "duplicates_detected": self.duplicates_detected,
            "errors": self.errors,
            "sources_completed": self.sources_completed,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobResult":
        """Create from dictionary."""
        return cls(
            success=data.get("success", True),
            images_extracted=data.get("images_extracted", 0),
            duplicates_detected=data.get("duplicates_detected", 0),
            errors=data.get("errors", []),
            sources_completed=data.get("sources_completed", {}),
            duration_seconds=data.get("duration_seconds", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Job:
    """Individual job in the queue.

    Represents a single extraction task for one property. Jobs are
    persistent and survive crashes - the queue can resume from where
    it left off.

    Attributes:
        id: Unique job identifier (8-char UUID prefix)
        job_type: Type of job (extraction, county data, etc.)
        address: Property address being processed
        sources: List of sources to extract from (e.g., ["zillow", "redfin"])
        status: Current job state
        priority: Job priority (higher = processed first), default 0
        created_at: When job was created
        started_at: When job began execution (None if not started)
        completed_at: When job finished (None if not complete)
        progress: Current progress tracking
        result: Job outcome (None until complete/failed)
        error: Error message if failed (None otherwise)
        retry_count: Number of retry attempts made
        max_retries: Maximum retry attempts before permanent failure
        last_retry_at: Timestamp of last retry attempt
        metadata: Additional job-specific data
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    job_type: JobType = JobType.IMAGE_EXTRACTION
    address: str = ""
    sources: list[str] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    started_at: str | None = None
    completed_at: str | None = None
    progress: JobProgress = field(default_factory=JobProgress)
    result: JobResult | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = JobStatus(self.status)
        if isinstance(self.job_type, str):
            self.job_type = JobType(self.job_type)
        # Ensure progress is JobProgress instance
        if isinstance(self.progress, dict):
            self.progress = JobProgress.from_dict(self.progress)
        # Ensure result is JobResult instance if present
        if isinstance(self.result, dict):
            self.result = JobResult.from_dict(self.result)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "job_type": self.job_type.value,
            "address": self.address,
            "sources": self.sources,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_retry_at": self.last_retry_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """Create from dictionary.

        Handles missing fields gracefully for backward compatibility.
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            job_type=JobType(data.get("job_type", "image_extraction")),
            address=data.get("address", ""),
            sources=data.get("sources", []),
            status=JobStatus(data.get("status", "pending")),
            priority=data.get("priority", 0),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            progress=JobProgress.from_dict(data.get("progress", {})),
            result=(
                JobResult.from_dict(data["result"])
                if data.get("result")
                else None
            ),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            last_retry_at=data.get("last_retry_at"),
            metadata=data.get("metadata", {}),
        )

    def can_retry(self) -> bool:
        """Check if job can be retried.

        Returns:
            True if retry_count < max_retries
        """
        return self.retry_count < self.max_retries

    def mark_running(self) -> None:
        """Transition job to RUNNING state."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.progress = JobProgress(
            current_step="Starting...",
            last_update=datetime.now(timezone.utc).isoformat(),
        )

    def mark_completed(self, result: JobResult) -> None:
        """Transition job to COMPLETED state."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.result = result
        self.progress.percent = 1.0
        self.progress.current_step = "Completed"

    def mark_failed(self, error: str, can_retry: bool = True) -> None:
        """Transition job to FAILED or RETRYING state.

        Args:
            error: Error message describing the failure
            can_retry: If True and retries remain, move to RETRYING
        """
        self.error = error

        if can_retry and self.can_retry():
            self.status = JobStatus.RETRYING
            self.retry_count += 1
            self.last_retry_at = datetime.now(timezone.utc).isoformat()
            self.progress.current_step = f"Retry {self.retry_count}/{self.max_retries}"
        else:
            self.status = JobStatus.FAILED
            self.completed_at = datetime.now(timezone.utc).isoformat()
            self.result = JobResult(
                success=False,
                errors=[error],
            )

    def mark_cancelled(self) -> None:
        """Transition job to CANCELLED state."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def update_progress(
        self,
        percent: float | None = None,
        current_step: str | None = None,
        items_completed: int | None = None,
        items_total: int | None = None,
        current_source: str | None = None,
    ) -> None:
        """Update job progress.

        Only updates fields that are provided (not None).
        """
        if percent is not None:
            self.progress.percent = min(1.0, max(0.0, percent))
        if current_step is not None:
            self.progress.current_step = current_step
        if items_completed is not None:
            self.progress.items_completed = items_completed
        if items_total is not None:
            self.progress.items_total = items_total
        if current_source is not None:
            self.progress.current_source = current_source
        self.progress.last_update = datetime.now(timezone.utc).isoformat()

    def elapsed_seconds(self) -> float:
        """Calculate elapsed time since job started.

        Returns:
            Seconds since started_at, or 0.0 if not started
        """
        if not self.started_at:
            return 0.0

        start = datetime.fromisoformat(self.started_at)
        now = datetime.now(timezone.utc)
        return (now - start).total_seconds()


@dataclass
class JobQueueState:
    """Persistent queue state for crash recovery.

    Stores all jobs (pending, running, completed, failed) with metadata
    for queue management and statistics.

    Attributes:
        jobs: List of all jobs in the queue
        version: Schema version for migration support
        created_at: When queue was first created
        updated_at: Last modification timestamp
        total_submitted: Cumulative jobs submitted (for statistics)
        total_completed: Cumulative jobs completed successfully
        total_failed: Cumulative jobs that failed permanently
    """

    jobs: list[Job] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_submitted": self.total_submitted,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "jobs": [job.to_dict() for job in self.jobs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobQueueState":
        """Create from dictionary."""
        jobs = [Job.from_dict(j) for j in data.get("jobs", [])]
        return cls(
            jobs=jobs,
            version=data.get("version", "1.0.0"),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
            updated_at=data.get(
                "updated_at", datetime.now(timezone.utc).isoformat()
            ),
            total_submitted=data.get("total_submitted", len(jobs)),
            total_completed=data.get("total_completed", 0),
            total_failed=data.get("total_failed", 0),
        )

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dict with counts by status and timing information
        """
        by_status = {status.value: 0 for status in JobStatus}
        for job in self.jobs:
            by_status[job.status.value] += 1

        pending = [j for j in self.jobs if j.status == JobStatus.PENDING]
        running = [j for j in self.jobs if j.status.is_active()]

        # Calculate average completion time from recent completed jobs
        completed_jobs = [
            j for j in self.jobs if j.status == JobStatus.COMPLETED and j.result
        ]
        avg_duration = 0.0
        if completed_jobs:
            durations = [j.result.duration_seconds for j in completed_jobs[-10:]]
            avg_duration = sum(durations) / len(durations)

        # Estimate remaining time
        remaining_count = len(pending) + len(running)
        estimated_seconds = remaining_count * avg_duration if avg_duration > 0 else None

        return {
            "by_status": by_status,
            "pending_count": len(pending),
            "running_count": len(running),
            "completed_count": by_status["completed"],
            "failed_count": by_status["failed"],
            "total_jobs": len(self.jobs),
            "total_submitted": self.total_submitted,
            "total_completed_cumulative": self.total_completed,
            "total_failed_cumulative": self.total_failed,
            "avg_duration_seconds": avg_duration,
            "estimated_remaining_seconds": estimated_seconds,
        }

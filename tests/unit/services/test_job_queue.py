"""Unit tests for job queue service.

Tests cover:
- Job model lifecycle (creation, state transitions, serialization)
- JobQueue persistence and CRUD operations
- Priority ordering and deduplication
- JobExecutor concurrency and retry logic
"""

import asyncio

import pytest

from phx_home_analysis.services.job_queue import (
    Job,
    JobExecutor,
    JobQueue,
    JobQueueState,
    JobResult,
    JobStatus,
    JobType,
)

# =============================================================================
# Job Model Tests
# =============================================================================


class TestJob:
    """Tests for Job model."""

    def test_job_creation_defaults(self):
        """Test job creation with defaults."""
        job = Job(address="123 Main St")

        assert job.id is not None
        assert len(job.id) == 8
        assert job.address == "123 Main St"
        assert job.status == JobStatus.PENDING
        assert job.job_type == JobType.IMAGE_EXTRACTION
        assert job.priority == 0
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.sources == []
        assert job.started_at is None
        assert job.completed_at is None

    def test_job_creation_with_values(self):
        """Test job creation with custom values."""
        job = Job(
            id="test1234",
            address="456 Oak Ave",
            sources=["zillow", "redfin"],
            priority=5,
            max_retries=5,
        )

        assert job.id == "test1234"
        assert job.address == "456 Oak Ave"
        assert job.sources == ["zillow", "redfin"]
        assert job.priority == 5
        assert job.max_retries == 5

    def test_job_mark_running(self):
        """Test transitioning job to running state."""
        job = Job(address="123 Main St")
        job.mark_running()

        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert job.progress.current_step == "Starting..."

    def test_job_mark_completed(self):
        """Test transitioning job to completed state."""
        job = Job(address="123 Main St")
        job.mark_running()

        result = JobResult(
            success=True,
            images_extracted=10,
            duplicates_detected=2,
        )
        job.mark_completed(result)

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result.images_extracted == 10
        assert job.progress.percent == 1.0

    def test_job_mark_failed_with_retry(self):
        """Test transitioning job to retrying state."""
        job = Job(address="123 Main St", max_retries=3)
        job.mark_running()
        job.mark_failed("Connection timeout", can_retry=True)

        assert job.status == JobStatus.RETRYING
        assert job.retry_count == 1
        assert job.error == "Connection timeout"
        assert job.completed_at is None  # Not complete until max retries

    def test_job_mark_failed_max_retries(self):
        """Test job fails permanently after max retries."""
        job = Job(address="123 Main St", max_retries=2)
        job.retry_count = 2  # Already at max

        job.mark_running()
        job.mark_failed("Connection timeout", can_retry=True)

        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.result.success is False

    def test_job_mark_cancelled(self):
        """Test job cancellation."""
        job = Job(address="123 Main St")
        job.mark_running()
        job.mark_cancelled()

        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None

    def test_job_update_progress(self):
        """Test progress updates."""
        job = Job(address="123 Main St")
        job.mark_running()

        job.update_progress(
            percent=0.5,
            current_step="Downloading from Zillow",
            items_completed=5,
            items_total=10,
            current_source="zillow",
        )

        assert job.progress.percent == 0.5
        assert job.progress.current_step == "Downloading from Zillow"
        assert job.progress.items_completed == 5
        assert job.progress.items_total == 10
        assert job.progress.current_source == "zillow"

    def test_job_serialization(self):
        """Test job to_dict and from_dict."""
        job = Job(
            id="abc12345",
            address="123 Main St",
            sources=["zillow"],
            priority=3,
        )
        job.mark_running()
        job.update_progress(percent=0.5, current_step="Testing")

        # Serialize
        data = job.to_dict()
        assert data["id"] == "abc12345"
        assert data["address"] == "123 Main St"
        assert data["status"] == "running"
        assert data["progress"]["percent"] == 0.5

        # Deserialize
        restored = Job.from_dict(data)
        assert restored.id == job.id
        assert restored.address == job.address
        assert restored.status == job.status
        assert restored.progress.percent == 0.5

    def test_job_can_retry(self):
        """Test can_retry logic."""
        job = Job(address="123 Main St", max_retries=3)

        assert job.can_retry() is True

        job.retry_count = 2
        assert job.can_retry() is True

        job.retry_count = 3
        assert job.can_retry() is False


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_is_terminal(self):
        """Test terminal state detection."""
        assert JobStatus.COMPLETED.is_terminal() is True
        assert JobStatus.FAILED.is_terminal() is True
        assert JobStatus.CANCELLED.is_terminal() is True
        assert JobStatus.PENDING.is_terminal() is False
        assert JobStatus.RUNNING.is_terminal() is False
        assert JobStatus.RETRYING.is_terminal() is False

    def test_is_active(self):
        """Test active state detection."""
        assert JobStatus.RUNNING.is_active() is True
        assert JobStatus.RETRYING.is_active() is True
        assert JobStatus.PENDING.is_active() is False
        assert JobStatus.COMPLETED.is_active() is False


# =============================================================================
# JobQueue Tests
# =============================================================================


class TestJobQueue:
    """Tests for JobQueue."""

    @pytest.fixture
    def queue_file(self, tmp_path):
        """Create temporary queue file."""
        return tmp_path / "job_queue.json"

    @pytest.fixture
    def queue(self, queue_file):
        """Create queue instance."""
        return JobQueue(state_file=queue_file)

    def test_queue_creation(self, queue, queue_file):
        """Test queue creation."""
        assert queue.state_file == queue_file
        assert len(queue.state.jobs) == 0

    def test_enqueue_job(self, queue):
        """Test enqueueing a job."""
        job = queue.enqueue(
            address="123 Main St",
            sources=["zillow", "redfin"],
        )

        assert job.id is not None
        assert job.address == "123 Main St"
        assert job.sources == ["zillow", "redfin"]
        assert job.status == JobStatus.PENDING
        assert len(queue.state.jobs) == 1

    def test_enqueue_deduplication(self, queue):
        """Test that duplicate jobs are not created."""
        job1 = queue.enqueue(address="123 Main St")
        job2 = queue.enqueue(address="123 Main St")

        # Should return existing job
        assert job1.id == job2.id
        assert len(queue.state.jobs) == 1

    def test_enqueue_batch(self, queue):
        """Test batch enqueueing."""
        addresses = ["123 Main St", "456 Oak Ave", "789 Pine Rd"]
        jobs = queue.enqueue_batch(addresses=addresses)

        assert len(jobs) == 3
        assert len(queue.state.jobs) == 3

    def test_get_pending(self, queue):
        """Test getting pending jobs."""
        queue.enqueue(address="Low Priority", priority=1)
        queue.enqueue(address="High Priority", priority=10)
        queue.enqueue(address="Medium Priority", priority=5)

        pending = queue.get_pending()

        assert len(pending) == 3
        # Should be ordered by priority (highest first)
        assert pending[0].address == "High Priority"
        assert pending[1].address == "Medium Priority"
        assert pending[2].address == "Low Priority"

    def test_get_job(self, queue):
        """Test getting job by ID."""
        job = queue.enqueue(address="123 Main St")
        retrieved = queue.get_job(job.id)

        assert retrieved is not None
        assert retrieved.id == job.id
        assert retrieved.address == job.address

    def test_get_job_by_address(self, queue):
        """Test getting job by address."""
        queue.enqueue(address="123 Main St")
        job = queue.get_job_by_address("123 Main St")

        assert job is not None
        assert job.address == "123 Main St"

    def test_mark_running(self, queue):
        """Test marking job as running."""
        job = queue.enqueue(address="123 Main St")
        queue.mark_running(job.id)

        updated = queue.get_job(job.id)
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None

    def test_mark_completed(self, queue):
        """Test marking job as completed."""
        job = queue.enqueue(address="123 Main St")
        queue.mark_running(job.id)

        result = JobResult(success=True, images_extracted=10)
        queue.mark_completed(job.id, result)

        updated = queue.get_job(job.id)
        assert updated.status == JobStatus.COMPLETED
        assert updated.result.images_extracted == 10

    def test_mark_failed(self, queue):
        """Test marking job as failed."""
        job = queue.enqueue(address="123 Main St", max_retries=2)
        queue.mark_running(job.id)
        queue.mark_failed(job.id, "Error message", can_retry=True)

        updated = queue.get_job(job.id)
        assert updated.status == JobStatus.RETRYING
        assert updated.retry_count == 1

    def test_get_stats(self, queue):
        """Test queue statistics."""
        queue.enqueue(address="Pending 1")
        queue.enqueue(address="Pending 2")

        job = queue.enqueue(address="Completed")
        queue.mark_running(job.id)
        queue.mark_completed(job.id, JobResult(success=True))

        stats = queue.get_stats()
        assert stats["pending_count"] == 2
        assert stats["completed_count"] == 1
        assert stats["total_jobs"] == 3

    def test_persistence(self, queue_file):
        """Test queue persistence across instances."""
        # Create and populate queue
        queue1 = JobQueue(state_file=queue_file)
        queue1.enqueue(address="123 Main St", sources=["zillow"])
        queue1.enqueue(address="456 Oak Ave", sources=["redfin"])

        # Create new queue instance
        queue2 = JobQueue(state_file=queue_file)

        assert len(queue2.state.jobs) == 2
        assert queue2.get_job_by_address("123 Main St") is not None
        assert queue2.get_job_by_address("456 Oak Ave") is not None

    def test_get_next_job(self, queue):
        """Test getting next job to process."""
        queue.enqueue(address="Low", priority=1)
        queue.enqueue(address="High", priority=10)

        next_job = queue.get_next_job()
        assert next_job.address == "High"

    def test_get_next_job_retrying_first(self, queue):
        """Test that retrying jobs are processed before pending."""
        pending = queue.enqueue(address="Pending", priority=10)
        retrying = queue.enqueue(address="Retrying")
        queue.mark_running(retrying.id)
        queue.mark_failed(retrying.id, "Error", can_retry=True)

        next_job = queue.get_next_job()
        assert next_job.address == "Retrying"

    def test_clear_completed(self, queue):
        """Test clearing old completed jobs."""
        # Create some completed jobs
        for i in range(10):
            job = queue.enqueue(address=f"Property {i}")
            queue.mark_running(job.id)
            queue.mark_completed(job.id, JobResult(success=True))

        # Add a pending job
        queue.enqueue(address="Pending")

        # Clear all but 3 completed
        removed = queue.clear_completed(keep_recent=3)

        assert removed == 7
        assert len(queue.get_completed()) == 3
        assert len(queue.get_pending()) == 1

    def test_retry_failed(self, queue):
        """Test retrying failed jobs."""
        job = queue.enqueue(address="Failed Job", max_retries=1)
        queue.mark_running(job.id)
        queue.mark_failed(job.id, "Error", can_retry=True)
        # Fail again to reach max retries
        queue.mark_running(job.id)
        queue.mark_failed(job.id, "Error again", can_retry=True)

        assert job.status == JobStatus.FAILED

        # Retry failed jobs
        count = queue.retry_failed()
        assert count == 1

        updated = queue.get_job(job.id)
        assert updated.status == JobStatus.PENDING
        assert updated.retry_count == 0


# =============================================================================
# JobExecutor Tests
# =============================================================================


class TestJobExecutor:
    """Tests for JobExecutor."""

    @pytest.fixture
    def queue_file(self, tmp_path):
        """Create temporary queue file."""
        return tmp_path / "job_queue.json"

    @pytest.fixture
    def queue(self, queue_file):
        """Create queue instance."""
        return JobQueue(state_file=queue_file)

    @pytest.fixture
    def executor(self, queue):
        """Create executor instance."""
        return JobExecutor(queue, max_concurrent=2)

    @pytest.mark.asyncio
    async def test_executor_creation(self, executor):
        """Test executor creation."""
        assert executor.max_concurrent == 2
        assert executor.running is False

    @pytest.mark.asyncio
    async def test_executor_with_handler(self, queue, executor):
        """Test executor processes jobs with handler."""
        # Track processed jobs
        processed = []

        async def test_handler(job: Job, exec: JobExecutor) -> JobResult:
            processed.append(job.address)
            await asyncio.sleep(0.01)  # Simulate work
            return JobResult(success=True, images_extracted=5)

        executor.register_handler(JobType.IMAGE_EXTRACTION, test_handler)

        # Add jobs
        queue.enqueue(address="Job 1")
        queue.enqueue(address="Job 2")
        queue.enqueue(address="Job 3")

        # Run executor
        await executor.start()

        # Verify all jobs processed
        assert len(processed) == 3
        assert "Job 1" in processed
        assert "Job 2" in processed
        assert "Job 3" in processed

        # Verify job states
        stats = queue.get_stats()
        assert stats["completed_count"] == 3
        assert stats["pending_count"] == 0

    @pytest.mark.asyncio
    async def test_executor_concurrency_limit(self, queue, executor):
        """Test executor respects concurrency limit."""
        max_concurrent_seen = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def test_handler(job: Job, exec: JobExecutor) -> JobResult:
            nonlocal max_concurrent_seen, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent_seen:
                    max_concurrent_seen = current_concurrent

            await asyncio.sleep(0.05)  # Simulate work

            async with lock:
                current_concurrent -= 1

            return JobResult(success=True)

        executor.register_handler(JobType.IMAGE_EXTRACTION, test_handler)

        # Add more jobs than concurrency limit
        for i in range(5):
            queue.enqueue(address=f"Job {i}")

        await executor.start()

        # Should never exceed max_concurrent
        assert max_concurrent_seen <= 2

    @pytest.mark.asyncio
    async def test_executor_handles_failure(self, queue, executor):
        """Test executor handles job failures."""
        call_count = 0

        async def failing_handler(job: Job, exec: JobExecutor) -> JobResult:
            nonlocal call_count
            call_count += 1
            return JobResult(success=False, errors=["Test failure"])

        executor.register_handler(JobType.IMAGE_EXTRACTION, failing_handler)

        job = queue.enqueue(address="Failing Job", max_retries=2)
        await executor.start()

        # Job should have been retried
        assert call_count >= 1

        # Job should eventually fail
        updated = queue.get_job(job.id)
        assert updated.status in (JobStatus.FAILED, JobStatus.RETRYING)

    @pytest.mark.asyncio
    async def test_executor_stop(self, queue, executor):
        """Test graceful executor stop."""
        started = asyncio.Event()

        async def slow_handler(job: Job, exec: JobExecutor) -> JobResult:
            started.set()
            await asyncio.sleep(1.0)  # Long running
            return JobResult(success=True)

        executor.register_handler(JobType.IMAGE_EXTRACTION, slow_handler)
        queue.enqueue(address="Slow Job")

        # Start in background
        task = asyncio.create_task(executor.start())

        # Wait for job to start
        await started.wait()

        # Stop executor
        await executor.stop(wait=False, timeout=0.1)

        # Should have stopped
        assert executor.running is False


# =============================================================================
# JobQueueState Tests
# =============================================================================


class TestJobQueueState:
    """Tests for JobQueueState."""

    def test_state_serialization(self):
        """Test state serialization."""
        state = JobQueueState()
        job = Job(address="123 Main St")
        state.jobs.append(job)
        state.total_submitted = 1

        data = state.to_dict()
        assert len(data["jobs"]) == 1
        assert data["total_submitted"] == 1

        restored = JobQueueState.from_dict(data)
        assert len(restored.jobs) == 1
        assert restored.jobs[0].address == "123 Main St"

    def test_state_stats(self):
        """Test state statistics."""
        state = JobQueueState()

        # Add various job states
        pending = Job(address="Pending")
        state.jobs.append(pending)

        running = Job(address="Running")
        running.mark_running()
        state.jobs.append(running)

        completed = Job(address="Completed")
        completed.mark_completed(JobResult(success=True, duration_seconds=10.0))
        state.jobs.append(completed)

        stats = state.get_stats()
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["running"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["pending_count"] == 1
        assert stats["running_count"] == 1

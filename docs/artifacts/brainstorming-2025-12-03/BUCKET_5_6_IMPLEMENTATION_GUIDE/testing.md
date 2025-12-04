# Testing

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

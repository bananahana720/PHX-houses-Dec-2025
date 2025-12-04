# Testing Strategy

### Unit Tests

```python
# Test job model
def test_image_extraction_job_creation():
    job = ImageExtractionJob(properties=["addr"], sources=["zillow"])
    assert job.status == "pending"
    assert job.started_at is None

# Test worker picks up job
def test_worker_processes_job():
    job_id = extraction_queue.enqueue(extract_images_job, ...).id
    # Simulate worker
    worker.work(burst=True)
    job = ImageExtractionJob.get(job_id)
    assert job.status in ["completed", "failed"]

# Test state resumption
def test_extract_resume_from_partial_state():
    state = ExtractionState.from_dict({
        "completed_properties": ["addr1"],
        "failed_properties": [],
        "property_last_checked": {"addr1": "..."}
    })
    # Re-run should skip addr1
    properties = [Property(full_address=addr) for addr in ["addr1", "addr2"]]
    remaining = [p for p in properties if p.full_address not in state.completed_properties]
    assert len(remaining) == 1
```

### Integration Tests

```python
# Test end-to-end job flow
def test_extraction_job_end_to_end(redis_conn, tmp_path):
    # Setup
    queue = Queue(connection=redis_conn)

    # Enqueue
    job = queue.enqueue(extract_images_job,
        job_id=str(uuid4()),
        properties=["4732 W Davis Rd, Glendale, AZ 85306"],
        sources=["zillow"],
        isolation_mode="minimize"
    )

    # Process
    worker = Worker([queue], connection=redis_conn)
    worker.work(burst=True)

    # Verify
    job.refresh()
    assert job.get_status() == "completed"
    assert job.result.total_images > 0
    assert (tmp_path / "property_images" / "processed").exists()
```

---

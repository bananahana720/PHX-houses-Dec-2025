# Critical Implementation Notes

### State & Atomicity

The current system uses **atomic writes** for state persistence:

```python
# CORRECT: atomic write pattern (existing code)
fd, temp_path = tempfile.mkstemp(dir=base_dir, suffix=".tmp")
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f)
    os.replace(temp_path, original_path)  # atomic on POSIX & Windows
except:
    os.unlink(temp_path)
```

**MUST PRESERVE** in job-based architecture. Add to job status updates:

```python
# Update job status atomically
job_dict = job.to_dict()
fd, temp_path = tempfile.mkstemp()
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(job_dict, f)
    os.replace(temp_path, job_path)
```

### Backward Compatibility

**Do NOT break** existing tools:

1. **Keep existing CLI**: `python scripts/extract_images.py --all` should still work
2. **Option 1 (Recommended)**: CLI enqueues job, polls status, prints summary
3. **Option 2 (Simple)**: Sync mode flag `--sync` for blocking behavior

```python
# Option 1: CLI becomes thin wrapper
def main():
    args = parse_args()

    job = extraction_queue.enqueue(extract_images_job, ...)
    print(f"Job queued: {job.id}")

    # Poll until done (backward compatible)
    while job.get_status() != 'completed':
        time.sleep(1)

    print(job.result)
```

### Error Recovery & Restart

Job queue + persistent state = **natural recovery**:

1. Worker crashes → Redis retains job → next worker picks it up
2. Partial extraction → resume via `property_last_checked` + URL tracker
3. Corrupted state → job marked failed, manually requeue

---

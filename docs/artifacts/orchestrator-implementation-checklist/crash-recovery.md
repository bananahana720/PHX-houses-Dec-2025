# Crash Recovery

### Step 19: Check for Interrupted Work
```python
def check_for_interrupted_work(state):
    """Resume interrupted properties from last checkpoint."""

    in_progress = state.get("in_progress_properties", [])

    if not in_progress:
        return []

    print(f"\nFound {len(in_progress)} interrupted properties:")

    resume_queue = []
    for addr in in_progress:
        phases = state.get("phase_status", {}).get(addr, {})
        last_phase = get_last_completed_phase(phases)
        next_phase = get_next_phase(last_phase)

        print(f"  - {addr}: Last completed: {last_phase}, Resume from: {next_phase}")
        resume_queue.append({"address": addr, "resume_phase": next_phase})

    return resume_queue
```

---

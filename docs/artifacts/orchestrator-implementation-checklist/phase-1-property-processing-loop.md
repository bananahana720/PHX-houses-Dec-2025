# Phase 1: Property Processing Loop

### Step 5: Initialize Progress Tracking
```python
batch_id = "test" if test_mode else f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
counters = {
    "completed": 0,
    "failed": 0,
    "skipped": len(to_skip),
    "unicorns": 0,
    "contenders": 0,
    "pass": 0,
    "research_created": 0,
    "research_completed": 0
}
```

### Step 6: Process Each Property
```python
for idx, address in enumerate(to_process):
    # Update progress display
    show_progress_banner(
        batch_id=batch_id,
        test_mode=test_mode,
        current=idx + 1,
        total=len(to_process),
        address=address,
        phase="phase1_listing",
        counters=counters
    )

    # Execute property analysis
    result = analyze_property(address, state)

    # Update counters
    update_counters(result, counters)

    # Update progress again
    show_progress_banner(...)
```

---

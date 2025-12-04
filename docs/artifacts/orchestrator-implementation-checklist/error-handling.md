# Error Handling

### Step 18: Handle Agent Failures
```python
def handle_error(address: str, phase: str, error: Exception):
    """Handle agent failure with checkpoint and retry logic."""

    state = load_extraction_state()

    # Update phase status
    checkpoint_phase(address, phase, "failed")

    # Increment retry count
    retry_count = state.get("retry_counts", {}).get(address, 0) + 1
    state["retry_counts"][address] = retry_count

    # Add to failed properties if not max retries
    if retry_count < 3:
        if address not in state["failed_properties"]:
            state["failed_properties"].append(address)
        print(f"  Retry {retry_count}/3 - will retry later")
    else:
        print(f"  Max retries reached - skipping permanently")

    # Remove from in-progress
    if address in state["in_progress_properties"]:
        state["in_progress_properties"].remove(address)

    save_state(state)
```

---

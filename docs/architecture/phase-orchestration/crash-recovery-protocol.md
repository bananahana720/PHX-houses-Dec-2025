# Crash Recovery Protocol

On restart, the work_items.json system ensures safe resumption:

```python
def recover_from_crash(property_address: str, work_items: dict) -> dict:
    """Recover property processing from crash.

    Returns next phase to execute and any warnings.
    """
    # Find work item by address
    work_item = None
    for item in work_items['work_items']:
        if item['address'] == property_address:
            work_item = item
            break

    if not work_item:
        return {"next_phase": 0, "warnings": ["No state found, starting fresh"]}

    phase_status = work_item.get("phase_status", {})

    # Find last completed phase
    phases = [
        "phase0_county",
        "phase05_cost",
        "phase1_listing",
        "phase1_map",
        "phase2a_exterior",
        "phase2b_interior",
        "phase3_synthesis",
        "phase4_report"
    ]
    last_complete = -1

    for i, phase in enumerate(phases):
        status = phase_status.get(phase)
        if status == "in_progress":
            # Crash during this phase - re-validate and retry
            return {
                "next_phase": i,
                "warnings": [f"{phase} was in_progress at crash - will retry"],
                "retry": True
            }
        elif status in ["complete", "skipped"]:
            last_complete = i
        elif status == "failed":
            # Check retry count
            if work_item.get("retry_count", 0) >= 3:
                return {
                    "next_phase": None,
                    "skip_reason": "max_retries_exceeded",
                    "warnings": [f"{phase} failed 3+ times"]
                }

    # Resume from next phase
    next_phase = last_complete + 1 if last_complete < len(phases) - 1 else None

    return {
        "next_phase": next_phase,
        "warnings": [],
        "last_complete": phases[last_complete] if last_complete >= 0 else None
    }
```

### Recovery Messages

Display clear status on recovery:

```
RECOVERY STATUS
===============
Session: session_20251202_123456 (resumed)
Property: 123 Main St, Phoenix, AZ 85001
Last Checkpoint: phase05_cost (complete)
Crashed During: phase1_listing (in_progress)
Action: Retry Phase 1 (attempt 2/3)
Prerequisites: Verified (phase0_county, phase05_cost complete)
Last Commit: abc12345 (previous property)
```

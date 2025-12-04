---
name: state-management
description: Manage pipeline state, checkpoints, and crash recovery via extraction_state.json and work_items.json. Track multi-phase workflows, handle retries, and implement crash recovery with atomic writes. Use when orchestrating multi-step pipelines or needing to resume after interruption.
allowed-tools: Read, Write, Bash(python:*)
---

# State Management Skill

Manage analysis pipeline state for crash recovery, checkpointing, and progress tracking.

## State Files

| File | Purpose |
|------|---------|
| `data/work_items.json` | Pipeline progress tracking |
| `data/property_images/metadata/extraction_state.json` | Image extraction state |
| `data/property_images/metadata/image_manifest.json` | Image registry |
| `data/research_tasks.json` | Pending research queue |

## Phase Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently executing |
| `complete` | Successfully finished |
| `failed` | Error, may retry |
| `skipped` | Intentionally bypassed |

## extraction_state.json Schema

```json
{
  "$schema": "extraction_state_v2",
  "completed_properties": ["addr1"],
  "failed_properties": ["addr2"],
  "in_progress_properties": ["addr3"],
  "retry_counts": {"addr2": 2},
  "phase_status": {
    "addr3": {
      "phase0_county": "complete",
      "phase1_listing": "in_progress",
      "phase2_images": "pending"
    }
  },
  "last_updated": "ISO-8601"
}
```

## Atomic Write Pattern

```python
import json
import os

def save_state_atomic(state: dict, path: str) -> None:
    """Atomic write: temp file + rename."""
    state["last_updated"] = datetime.now().isoformat()
    temp_path = f"{path}.tmp"
    with open(temp_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(temp_path, path)  # Atomic on POSIX
```

## Checkpoint Protocol

```python
def checkpoint(property: str, phase: str, status: str) -> None:
    state = load_state()

    # Update phase status
    if property not in state["phase_status"]:
        state["phase_status"][property] = {}
    state["phase_status"][property][phase] = status

    # Update property lists
    if status == "complete":
        move_to_list(state, property, "completed_properties")
    elif status == "failed":
        state["retry_counts"][property] = state["retry_counts"].get(property, 0) + 1
        if state["retry_counts"][property] >= 3:
            move_to_list(state, property, "failed_properties")

    save_state_atomic(state, STATE_FILE)
```

## Crash Recovery

```python
def recover_crashed_properties() -> list:
    """Find properties to resume after crash."""
    state = load_state()

    for prop in state["in_progress_properties"]:
        phases = state["phase_status"].get(prop, {})
        # Find last complete phase
        resume_from = find_incomplete_phase(phases)
        yield {"address": prop, "resume_from": resume_from}
```

## Single Writer Rule

```
CRITICAL: Only orchestrators modify state files.
Sub-agents MUST return data, NOT write to state.
Orchestrator aggregates and writes atomically.
```

## Best Practices

1. **Atomic writes only** - Use temp + rename pattern
2. **Checkpoint frequently** - After each phase completion
3. **Track retries** - Max 3 retries before permanent failure
4. **Single writer** - Only orchestrator writes state
5. **Validate on load** - Check schema before using
6. **Resume support** - Always check for in_progress on startup

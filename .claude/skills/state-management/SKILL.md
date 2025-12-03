---
name: state-management
description: Manage pipeline state, checkpoints, and crash recovery via extraction_state.json and related metadata files. Use when tracking multi-phase workflows, handling retries, or implementing crash recovery.
allowed-tools: Read, Write, Bash(python:*)
---

# State Management Skill

Expert at managing analysis pipeline state for crash recovery, checkpointing, and progress tracking.

## State Files

| File | Purpose |
|------|---------|
| `data/property_images/metadata/extraction_state.json` | Pipeline state & checkpoints |
| `data/property_images/metadata/image_manifest.json` | Image registry |
| `data/property_images/metadata/address_folder_lookup.json` | Address-to-folder mapping |
| `data/property_images/metadata/pipeline_runs.json` | Run history |
| `data/research_tasks.json` | Pending research tasks queue |

## extraction_state.json Schema (v2)

```json
{
  "$schema": "extraction_state_v2",
  "completed_properties": ["addr1", "addr2"],
  "failed_properties": ["addr3"],
  "in_progress_properties": ["addr4"],
  "retry_counts": {
    "addr3": 2
  },
  "phase_status": {
    "addr4": {
      "phase0_county": "complete",
      "phase1_listing": "complete",
      "phase1_map": "in_progress",
      "phase2_images": "pending",
      "phase3_synthesis": "pending"
    }
  },
  "last_checkpoint": {
    "batch_id": "batch_001",
    "property_index": 5,
    "timestamp": "ISO-8601"
  },
  "stats": {
    "total_attempted": 10,
    "success_rate": 0.8
  },
  "last_updated": "ISO-8601"
}
```

## Phase Status Values

| Phase | Valid States |
|-------|--------------|
| `phase0_county` | pending, in_progress, complete, failed, skipped |
| `phase1_listing` | pending, in_progress, complete, failed |
| `phase1_map` | pending, in_progress, complete, failed |
| `phase2_images` | pending, in_progress, complete, failed, skipped |
| `phase3_synthesis` | pending, in_progress, complete, failed |

## Core Operations

### Load State (with validation)

```python
import json
from datetime import datetime

def load_state() -> dict:
    """Load and validate extraction state."""
    try:
        state = json.load(open("data/property_images/metadata/extraction_state.json"))
    except FileNotFoundError:
        return create_empty_state()

    if not validate_state(state):
        return create_empty_state()
    return state

def validate_state(state: dict) -> bool:
    """Validate extraction_state.json schema."""
    required = ["completed_properties", "failed_properties", "in_progress_properties"]
    return all(k in state and isinstance(state[k], list) for k in required)

def create_empty_state() -> dict:
    """Create fresh state object."""
    return {
        "$schema": "extraction_state_v2",
        "completed_properties": [],
        "failed_properties": [],
        "in_progress_properties": [],
        "retry_counts": {},
        "phase_status": {},
        "last_checkpoint": None,
        "stats": {"total_attempted": 0, "success_rate": 0.0},
        "last_updated": datetime.now().isoformat()
    }
```

### Save State (atomic)

```python
import os

def save_state(state: dict) -> None:
    """Atomic state save with backup."""
    path = "data/property_images/metadata/extraction_state.json"
    temp = path + ".tmp"
    backup = path + ".bak"

    # Update timestamp
    state["last_updated"] = datetime.now().isoformat()

    # Backup existing
    if os.path.exists(path):
        import shutil
        shutil.copy(path, backup)

    # Atomic write
    with open(temp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(temp, path)
```

### Triage Property

```python
def triage_property(address: str, state: dict) -> tuple[bool, str]:
    """Determine if property should be processed.

    Returns:
        (should_process, reason) tuple
    """
    if address in state.get("completed_properties", []):
        return False, "already_completed"

    if address in state.get("failed_properties", []):
        retry_count = state.get("retry_counts", {}).get(address, 0)
        if retry_count >= 3:
            return False, "max_retries"
        return True, f"retry_{retry_count + 1}"

    return True, "new"
```

### Update Phase Status

```python
def update_phase(address: str, phase: str, status: str) -> None:
    """Update phase status for a property."""
    state = load_state()

    if address not in state.get("phase_status", {}):
        state.setdefault("phase_status", {})[address] = {}

    state["phase_status"][address][phase] = status

    # Move to in_progress if starting
    if status == "in_progress" and address not in state["in_progress_properties"]:
        state["in_progress_properties"].append(address)

    save_state(state)
```

### Mark Property Complete

```python
def mark_complete(address: str) -> None:
    """Mark property as successfully completed."""
    state = load_state()

    # Move to completed
    if address not in state["completed_properties"]:
        state["completed_properties"].append(address)

    # Remove from in_progress and failed
    if address in state["in_progress_properties"]:
        state["in_progress_properties"].remove(address)
    if address in state["failed_properties"]:
        state["failed_properties"].remove(address)

    # Clear retry count
    state.get("retry_counts", {}).pop(address, None)

    # Update stats
    state["stats"]["total_attempted"] = len(state["completed_properties"]) + len(state["failed_properties"])
    state["stats"]["success_rate"] = len(state["completed_properties"]) / max(1, state["stats"]["total_attempted"])

    save_state(state)
```

### Mark Property Failed

```python
def mark_failed(address: str, error: str = None) -> None:
    """Mark property as failed with retry increment."""
    state = load_state()

    # Increment retry count
    retry_counts = state.setdefault("retry_counts", {})
    retry_counts[address] = retry_counts.get(address, 0) + 1

    # Add to failed if not already
    if address not in state["failed_properties"]:
        state["failed_properties"].append(address)

    # Remove from in_progress
    if address in state["in_progress_properties"]:
        state["in_progress_properties"].remove(address)

    save_state(state)
```

## Crash Recovery

```python
def recover_from_crash() -> list[dict]:
    """Find properties to resume after crash.

    Returns:
        List of {address, resume_from_phase} dicts
    """
    state = load_state()
    recovery_list = []

    for address in state.get("in_progress_properties", []):
        phases = state.get("phase_status", {}).get(address, {})

        # Find last complete phase
        phase_order = ["phase0_county", "phase1_listing", "phase1_map", "phase2_images", "phase3_synthesis"]
        resume_phase = phase_order[0]

        for phase in phase_order:
            if phases.get(phase) == "complete":
                idx = phase_order.index(phase)
                if idx + 1 < len(phase_order):
                    resume_phase = phase_order[idx + 1]

        recovery_list.append({
            "address": address,
            "resume_from_phase": resume_phase,
            "phases_complete": [p for p in phase_order if phases.get(p) == "complete"]
        })

    return recovery_list
```

## Address Folder Lookup

```python
def get_image_folder(address: str) -> str | None:
    """Get image folder path for address."""
    try:
        lookup = json.load(open("data/property_images/metadata/address_folder_lookup.json"))
        mapping = lookup.get("mappings", {}).get(address)
        return mapping["path"] if mapping else None
    except FileNotFoundError:
        return None

def set_image_folder(address: str, folder_hash: str, image_count: int) -> None:
    """Register image folder for address."""
    path = "data/property_images/metadata/address_folder_lookup.json"
    try:
        lookup = json.load(open(path))
    except FileNotFoundError:
        lookup = {"version": "1.0.0", "mappings": {}}

    lookup["mappings"][address] = {
        "folder": folder_hash,
        "image_count": image_count,
        "path": f"data/property_images/processed/{folder_hash}/"
    }

    with open(path, "w") as f:
        json.dump(lookup, f, indent=2)
```

## Best Practices

1. **Always validate state before use** - Corrupted state can cause data loss
2. **Use atomic writes** - Prevent partial writes on crash
3. **Maintain backup files** - Enable manual recovery
4. **Checkpoint frequently** - After each phase completion
5. **Clear in_progress on completion** - Prevents re-processing
6. **Never exceed 3 retries** - Fail fast to avoid infinite loops

# Phase 3: Helper Functions

### Step 12: Checkpoint Phase
```python
def checkpoint_phase(address: str, phase: str, status: str):
    """Update phase status and checkpoint after each phase."""
    state = load_extraction_state()

    # Ensure property is tracked
    if address not in state["in_progress_properties"]:
        state["in_progress_properties"].append(address)

    # Update phase status
    if address not in state.get("phase_status", {}):
        state["phase_status"][address] = {}
    state["phase_status"][address][phase] = status

    # Update checkpoint
    state["last_checkpoint"] = {
        "property_address": address,
        "phase": phase,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    state["last_updated"] = datetime.now().isoformat()
    safe_update_state(state, EXTRACTION_STATE_PATH)
```

### Step 13: Progress Banner
```python
def show_progress_banner(batch_id, test_mode, current, total, address, phase, counters):
    """Display real-time progress banner."""

    # Calculate progress bar
    pct = int((current / total) * 100)
    filled = int((current / total) * 20)
    bar = "█" * filled + "░" * (20 - filled)

    mode = f"TEST (5 max)" if test_mode else f"FULL BATCH ({total} properties)"

    print(f"""
=== Property Analysis Progress ===
Batch: {batch_id}
Mode: {mode}

Progress: [{bar}] {current}/{total} ({pct}%)
Current: {address}
Phase: {phase}

Completed: {counters['completed']} | Failed: {counters['failed']} | Skipped: {counters['skipped']}
Unicorns: {counters['unicorns']} | Contenders: {counters['contenders']} | Pass: {counters['pass']}

Research Tasks:
  Created this run: {counters['research_created']}
  Completed this run: {counters['research_completed']}
  Pending: {counters.get('research_pending', 0)}

Last Error: {counters.get('last_error', 'None')}
""")
```

### Step 14: Research Task Creation
```python
from uuid import uuid4

def create_research_task(address: str, field: str, reason: str):
    """Create a research task in research_tasks.json."""

    tasks = json.load(open("data/research_tasks.json"))

    task = {
        "id": f"task_{uuid4().hex[:8]}",
        "property_address": address,
        "field": field,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
        "priority": "high" if field in ["roof_age", "hvac_age"] else "medium",
        "assigned_agent": "image-assessor",
        "fallback_command": f'python scripts/estimate_ages.py --property "{address}"'
    }

    tasks["pending_tasks"].append(task)
    tasks["last_updated"] = datetime.now().isoformat()

    with open("data/research_tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)
```

### Step 15: Safe State Update
```python
import shutil
import tempfile

def safe_update_state(new_data: dict, filepath: str):
    """Validate schema before writing, with backup."""

    if not validate_extraction_state(new_data):
        raise ValueError("Invalid schema - refusing to write")

    # Backup existing file
    if os.path.exists(filepath):
        shutil.copy(filepath, filepath + ".bak")

    # Atomic write pattern
    temp_path = filepath + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(new_data, f, indent=2)
    os.replace(temp_path, filepath)  # Atomic on POSIX/Windows NTFS
```

---

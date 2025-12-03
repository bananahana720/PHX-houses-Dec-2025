# Orchestrator Implementation Checklist

**Purpose:** Step-by-step guide for implementing the enhanced analyze-property orchestrator

---

## Prerequisites

Before implementing, verify these files exist:

- [x] `.claude/AGENT_BRIEFING.md` - Agent operational context
- [x] `.claude/commands/analyze-property.md` - Enhanced orchestrator spec (665 lines)
- [x] `data/property_images/metadata/extraction_state.json` - v2 schema
- [x] `data/research_tasks.json` - v1 schema
- [x] `scripts/estimate_ages.py` - Fallback age estimation
- [x] `data/phx_homes.csv` - Property listing data
- [x] `data/enrichment_data.json` - Property enrichment data

---

## Phase 0: Initialization

### Step 1: Parse Arguments
```python
import sys

args = sys.argv[1:]
test_mode = "--test" in args
batch_mode = "--all" in args or test_mode
single_address = None if batch_mode else args[0] if args else None
```

### Step 2: Load State Files
```python
import json
from pathlib import Path

# Load extraction state with validation
state = load_extraction_state("data/property_images/metadata/extraction_state.json")
validate_extraction_state(state)  # Ensure v2 schema

# Load research tasks
research_tasks = json.load(open("data/research_tasks.json"))
pending_count = len(research_tasks.get("pending_tasks", []))

if pending_count > 0:
    print(f"Note: {pending_count} research tasks pending - agents will attempt pickup")
```

### Step 3: Determine Scope
```python
# Load properties from CSV
with open("data/phx_homes.csv") as f:
    properties = [line.strip() for line in f.readlines()[1:]]  # Skip header

if test_mode:
    properties = properties[:5]
    print(f"TEST MODE: Limited to {len(properties)} properties")
```

### Step 4: Apply Triage
```python
completed = set(state.get("completed_properties", []))
failed = state.get("failed_properties", [])
retry_counts = state.get("retry_counts", {})

to_process = []
to_skip = []

for prop in properties:
    if prop in completed:
        to_skip.append({"address": prop, "reason": "already_completed"})
    elif prop in failed and retry_counts.get(prop, 0) >= 3:
        to_skip.append({"address": prop, "reason": "max_retries"})
    else:
        to_process.append(prop)

print(f"Scope: {len(to_process)} to process, {len(to_skip)} skipped")
```

---

## Phase 1: Property Processing Loop

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

## Phase 2: Property Analysis Implementation

### Step 7: Execute Phase 1 (Parallel)
```python
def analyze_property(address: str, state: dict) -> dict:
    """Execute full 4-phase analysis for single property."""

    # Mark as in-progress
    if address not in state["in_progress_properties"]:
        state["in_progress_properties"].append(address)
    save_state(state)

    # Phase 1: Listing + Map (parallel)
    listing_result = launch_agent("listing-browser", address)
    map_result = launch_agent("map-analyzer", address)

    # Update checkpoints
    checkpoint_phase(address, "phase1_listing", listing_result["status"])
    checkpoint_phase(address, "phase1_map", map_result["status"])

    return {
        "phase1_listing": listing_result,
        "phase1_map": map_result
    }
```

### Step 8: Execute Phase 2 (Sequential)
```python
    # Phase 2: Image assessment
    if listing_result["data"].get("image_count", 0) == 0:
        checkpoint_phase(address, "phase2_images", "skipped")
        image_result = {"status": "skipped", "reason": "no_images"}
    else:
        image_result = launch_agent("image-assessor", address)
        checkpoint_phase(address, "phase2_images", image_result["status"])

        # Check for missing age data
        handle_research_tasks(address, image_result)

    return {
        **results,
        "phase2_images": image_result
    }
```

### Step 9: Handle Research Tasks
```python
def handle_research_tasks(address: str, image_result: dict):
    """Create and resolve research tasks for missing age data."""

    missing_fields = []
    for field in ["roof_age", "hvac_age", "pool_equipment_age"]:
        if field not in image_result["data"] or image_result["data"][field] is None:
            missing_fields.append(field)

    if missing_fields:
        # Create research tasks
        for field in missing_fields:
            create_research_task(address, field, "visual_assessment_failed")

        # Execute fallback
        subprocess.run([
            "python", "scripts/estimate_ages.py",
            "--property", address
        ])

        # Mark tasks as completed
        mark_tasks_completed(address, missing_fields, "auto-estimated")
```

### Step 10: Execute Phase 3 (Synthesis)
```python
    # Phase 3: Scoring
    score_result = calculate_final_score(
        listing=listing_result["data"],
        map_data=map_result["data"],
        images=image_result["data"]
    )

    checkpoint_phase(address, "phase3_synthesis", "complete")

    # Move to completed
    state["in_progress_properties"].remove(address)
    state["completed_properties"].append(address)
    state["stats"]["total_attempted"] += 1
    save_state(state)

    return {
        **results,
        "phase3_synthesis": score_result
    }
```

### Step 11: Execute Phase 4 (Report)
```python
    # Phase 4: Generate report
    report = generate_property_report(
        address=address,
        listing=listing_result["data"],
        map_data=map_result["data"],
        images=image_result["data"],
        score=score_result["data"]
    )

    return {
        **results,
        "phase4_report": report,
        "tier": score_result["data"]["tier"],
        "total_score": score_result["data"]["total"]
    }
```

---

## Phase 3: Helper Functions

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

## Phase 4: Finalization

### Step 16: Generate Summary Report
```python
def generate_summary_report(counters, test_mode, research_tasks):
    """Generate final batch summary."""

    print(f"""
{'='*60}
Batch Complete
{'='*60}

Results:
- Attempted: {counters['completed'] + counters['failed']}
- Completed: {counters['completed']}
- Skipped (already done): {counters['skipped']}
- Failed this run: {counters['failed']}

Tier Distribution:
- Unicorns found: {counters['unicorns']}
- Contenders found: {counters['contenders']}
- Pass: {counters['pass']}

Research Tasks:
- Created: {counters['research_created']}
- Auto-completed: {counters['research_completed']}
- Pending manual review: {len(research_tasks['pending_tasks'])}
""")

    if test_mode:
        success_rate = counters['completed'] / (counters['completed'] + counters['failed'])
        recommendation = "Yes" if success_rate >= 0.8 else "No - fix errors first"
        print(f"\nReady for full batch: {recommendation}")
```

### Step 17: Verification
```python
def verify_completion(state, test_mode):
    """Verify all state files updated correctly."""

    # Check no properties stuck in progress
    in_progress = state.get("in_progress_properties", [])
    if in_progress:
        print(f"WARNING: {len(in_progress)} properties still in progress")
        for addr in in_progress:
            phases = state.get("phase_status", {}).get(addr, {})
            print(f"  - {addr}: {phases}")

    # Verify stats
    total_attempted = state["stats"]["total_attempted"]
    completed_count = len(state["completed_properties"])
    success_rate = completed_count / total_attempted if total_attempted > 0 else 0

    print(f"\nVerification:")
    print(f"  Total attempted: {total_attempted}")
    print(f"  Completed: {completed_count}")
    print(f"  Success rate: {success_rate:.1%}")
```

---

## Error Handling

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

## Crash Recovery

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

## Testing Checklist

- [ ] Test mode with 5 properties runs successfully
- [ ] Progress banner updates correctly
- [ ] Phase checkpoints save after each phase
- [ ] Research tasks created for missing ages
- [ ] Fallback estimation executed
- [ ] Crash recovery resumes from correct phase
- [ ] Batch summary accurate
- [ ] No properties stuck in in_progress after completion
- [ ] State files have valid v2 schema

---

## File Locations

**Input:**
- `data/phx_homes.csv` - Property list
- `data/enrichment_data.json` - Enrichment data
- `data/property_images/metadata/extraction_state.json` - Pipeline state
- `data/research_tasks.json` - Research queue

**Output:**
- `data/property_images/metadata/extraction_state.json` - Updated with phase_status
- `data/enrichment_data.json` - Updated with scores
- `data/property_images/processed/{hash}/` - Downloaded images
- `data/research_tasks.json` - Updated with new/completed tasks

---

*Implementation checklist for analyze-property orchestrator*
*Based on: .claude/commands/analyze-property.md (665 lines)*
*Date: 2025-11-30*

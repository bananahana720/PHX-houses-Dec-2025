# work_items.json Schema Documentation

## Overview

**File**: `data/work_items.json`
**Version**: 1.0
**Purpose**: Pipeline state management and checkpoint tracking for multi-phase property analysis
**Format**: JSON
**Atomicity**: Critical - always use atomic write patterns (temp file + rename)

The `work_items.json` file tracks the progress of property analysis through the six-phase pipeline, maintaining work item status, phase completion checkpoints, and session metadata. It enables crash recovery, progress monitoring, and multi-property batch processing.

---

## Root Structure

```json
{
  "session": {object},
  "work_items": [array],
  "summary": {object},
  "updated_at": "ISO8601 timestamp"
}
```

| Field | Type | Required | Description | Updated By |
|-------|------|----------|-------------|------------|
| `session` | object | yes | Session metadata (ID, mode, progress) | WorkItemsRepository.initialize_session() |
| `work_items` | array | yes | Array of work item objects (one per property) | WorkItemsRepository (phase checkpoints) |
| `summary` | object | yes | Aggregated statistics (counts by status) | WorkItemsRepository (auto-calculated) |
| `updated_at` | string (ISO8601) | yes | UTC timestamp of last update | WorkItemsRepository.save_state() |

---

## Session Object

Tracks the overall pipeline execution context.

```json
{
  "session_id": "session_20251204_030000_a1b2c3d4",
  "started_at": "2025-12-04T03:00:00+00:00",
  "mode": "batch",
  "total_items": 30,
  "current_index": 5
}
```

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `session_id` | string | yes | Format: `session_YYYYMMDD_HHMMSS_xxxxxxxx` | Unique session identifier; generated on initialization; includes timestamp and 8-char hex suffix |
| `started_at` | string (ISO8601) | yes | UTC datetime | Session start timestamp; timezone-aware; used for stale item detection |
| `mode` | string | yes | `"batch"` or `"single"` | Execution mode: batch (multiple addresses) or single (one address) |
| `total_items` | integer | yes | 1-∞ | Total number of properties to process in this session |
| `current_index` | integer | yes | 0-total_items | Current 0-based index in work_items array; used for resume tracking |

### Session Initialization Example

```python
repo.initialize_session(
    mode="batch",
    addresses=[
        "4417 W Sandra Cir",
        "2353 W Tierra Buena Ln",
        "4732 W Davis Rd"
    ]
)
```

Results in:
```json
{
  "session_id": "session_20251204_030000_a1b2c3d4",
  "started_at": "2025-12-04T03:00:00.000000+00:00",
  "mode": "batch",
  "total_items": 3,
  "current_index": 0
}
```

---

## Work Items Array

Array of work item objects, one per property address. Each work item tracks overall status and per-phase completion.

```json
{
  "work_items": [
    {
      "id": "a1b2c3d4",
      "address": "4417 W Sandra Cir",
      "index": 0,
      "status": "in_progress",
      "phases": {
        "phase0_county": {...},
        "phase1_listing": {...},
        "phase1_map": {...},
        "phase2_images": {...},
        "phase3_synthesis": {...},
        "phase4_report": {...}
      },
      "created_at": "2025-12-04T03:00:00.000000+00:00",
      "updated_at": "2025-12-04T03:05:30.000000+00:00"
    }
  ]
}
```

### Work Item Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | 8-character lowercase hex hash derived from address; used for quick identification |
| `address` | string | yes | Full property address (primary key for lookup); e.g., "4417 W Sandra Cir, Phoenix, AZ 85021" |
| `index` | integer | yes | 0-based position in work_items array; matches position in original addresses list |
| `status` | string | yes | Overall work item status (see WorkItemStatus enum below) |
| `phases` | object | yes | Per-phase status tracking (all 6 phases required) |
| `created_at` | string (ISO8601) | yes | UTC timestamp when work item was created |
| `updated_at` | string (ISO8601) | yes | UTC timestamp of last phase checkpoint or status change |

### WorkItemStatus Enum

Valid values for `work_item.status`. Controls which transitions are allowed.

| Status | Transitions | Description | Trigger |
|--------|-----------|-------------|---------|
| `pending` | → `in_progress`, `blocked` | Initial state; waiting for processing | initialize_session() |
| `in_progress` | → `completed`, `failed`, `blocked` | At least one phase is running | checkpoint_phase_start() |
| `completed` | (terminal) | All phases completed successfully | All phases = completed |
| `failed` | → `in_progress` | At least one phase failed; can retry | Any phase fails |
| `blocked` | → `in_progress` | Cannot proceed (dependency unmet, resource exhausted) | Manually set by orchestrator |

### Status Transition Rules

```
┌─────────┐
│ pending │ ← Initial state
└────┬────┘
     │
     ├─→ in_progress (phase_start)
     │   ├─→ completed (all phases done)
     │   ├─→ failed (any phase fails)
     │   └─→ blocked (resource limit, dependency)
     │
     └─→ blocked (upfront blocker)
         └─→ in_progress (unblock)

Terminal states: completed, (failed can retry)
```

**Status Update Logic** (implemented in `_update_work_item_status()`):
- If ALL phases = completed → status = `completed`
- Else if ANY phase = failed → status = `failed`
- Else if ANY phase = in_progress → status = `in_progress`
- Else if ANY phase = blocked → status = `blocked`
- Else → status = `pending`

---

## Phase Object

Each phase in the `phases` map tracks execution state and error details.

```json
{
  "phases": {
    "phase0_county": {
      "status": "completed",
      "started_at": "2025-12-04T03:00:30.000000+00:00",
      "completed_at": "2025-12-04T03:02:15.000000+00:00",
      "retry_count": 0
    },
    "phase1_listing": {
      "status": "failed",
      "started_at": "2025-12-04T03:02:20.000000+00:00",
      "completed_at": "2025-12-04T03:04:00.000000+00:00",
      "error_message": "Zillow returned 429 (rate limited)",
      "retry_count": 2,
      "stale_reset_at": null
    },
    "phase1_map": {
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "retry_count": 0
    }
  }
}
```

### Phase Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | yes | Phase execution status (see PhaseStatus enum) |
| `started_at` | string (ISO8601) \| null | no | UTC timestamp when phase execution began; null if never started |
| `completed_at` | string (ISO8601) \| null | no | UTC timestamp when phase finished (success or failure); null if not completed |
| `error_message` | string \| null | no | Error description if phase failed; null if not failed |
| `retry_count` | integer | yes | Number of times phase has been retried after failure; starts at 0 |
| `stale_reset_at` | string (ISO8601) \| null | no | UTC timestamp if phase was reset due to staleness timeout; indicates recovery from hanging process |

### PhaseStatus Enum

Valid values for `phase.status`. Independent of work item status (though work item status is derived from phase statuses).

| Status | Transitions | Description | Duration |
|--------|-----------|-------------|----------|
| `pending` | → `in_progress`, `skipped` | Initial state; phase not yet started | (indefinite) |
| `in_progress` | → `completed`, `failed` | Phase is actively executing | <30 min (stale timeout) |
| `completed` | (terminal) | Phase finished successfully | Fixed |
| `failed` | → `in_progress` | Phase execution failed; can be retried | Fixed |
| `skipped` | (terminal) | Phase skipped (e.g., no images available, not applicable) | Fixed |

### Phase Transition Rules

```
pending ──────→ in_progress ──→ completed (terminal)
  │                  │
  │                  └──→ failed ──→ in_progress (retry)
  │
  └──────→ skipped (terminal)
```

### Stale Detection

Phases with `status = "in_progress"` that have been running for > 30 minutes (STALE_TIMEOUT_MINUTES) are automatically reset to `pending` when the state is loaded.

**Stale Reset Behavior:**
1. On `load_state()`: `_reset_stale_items()` scans all work items
2. For each in_progress phase: Calculate elapsed time = now - started_at
3. If elapsed > 30 minutes:
   - Set status back to `pending`
   - Set `stale_reset_at` to current timestamp
   - Log warning: "Reset stale in_progress item: [address].[phase]"
   - Update work item status based on new phase statuses

**Purpose:** Recovers from crashed/hung agents that left phases in limbo.

---

## Phase Details by Stage

### Phase 0: County Data (phase0_county)

Extracts foundational property data from Maricopa County Assessor API.

| Field | Source | Kill-Switch Impact |
|-------|--------|-------------------|
| `lot_sqft` | County Assessor API | SOFT: 1.0 severity if not 7k-15k |
| `year_built` | County Assessor API | SOFT: 2.0 severity if >= 2024 |
| `garage_spaces` | County Assessor API | SOFT: 1.5 severity if < 2 |
| `sewer_type` | County Assessor API | SOFT: 2.5 severity if not "city" |

**Typical Duration**: 5-10 seconds per property

### Phase 1: Listing Data (phase1_listing)

Extracts property listing information from Zillow or Redfin using stealth browser automation.

| Field | Source | Extracted |
|-------|--------|-----------|
| `list_price` | Zillow/Redfin | Base listing price |
| `hoa_fee` | Zillow/Redfin | Monthly HOA fee; HARD fail if > $0 |
| `beds` | Zillow/Redfin | Bedrooms; HARD fail if < 4 |
| `baths` | Zillow/Redfin | Bathrooms; HARD fail if < 2 |

**Typical Duration**: 30-60 seconds per property (includes rate limiting)

### Phase 1: Map Data (phase1_map)

Analyzes geographic context: schools, safety, orientation, flood risk.

| Field | Source | Used For |
|-------|--------|----------|
| `school_rating` | GreatSchools API | Section A: Location scoring (max 40 pts) |
| `orientation` | Satellite imagery analysis | Section A: Sun orientation scoring (max 30 pts) |
| `safety_neighborhood_score` | Crime API | Section A: Crime/safety scoring (max 40 pts) |
| `flood_zone` | FEMA API | Section A: Flood risk (max 30 pts) |
| `walk_score` | WalkScore API | Section A: Walkability (max 30 pts) |

**Typical Duration**: 20-40 seconds per property

### Phase 2: Image Assessment (phase2_images)

Visual inspection of property images (interior + exterior) by advanced image analysis model.

| Scores | Scale | Combines Into |
|--------|-------|----------------|
| `kitchen_score` | 0-10 | Interior (Section C) |
| `master_suite_score` | 0-10 | Interior (Section C) |
| `natural_light_score` | 0-10 | Interior (Section C) |
| `ceiling_condition_score` | 0-10 | Interior (Section C) |
| `fireplace_score` | 0-10 | Interior (Section C) |
| `laundry_score` | 0-10 | Interior (Section C) |
| `aesthetics_score` | 0-10 | Interior (Section C) |
| `roof_condition_score` | 0-10 | Exterior (Section B) |
| `pool_condition_score` | 0-10 | Exterior (Section B) |
| `hvac_condition_score` | 0-10 | Exterior (Section B) |
| `backyard_appeal_score` | 0-10 | Exterior (Section B) |

**Prerequisites**: Phase 1 listing must complete (images downloaded first)

**Typical Duration**: 3-5 minutes (model processing time)

### Phase 3: Synthesis (phase3_synthesis)

Combines all data sources into final kill-switch verdict and 605-point score.

| Field | Calculation |
|-------|-----------|
| `kill_switch_passed` | Evaluates all 5 HARD + 4 SOFT criteria |
| `kill_switch_failures` | List of failed criteria |
| `total_score` | Weighted sum of all sections (max 605) |
| `tier` | Classification: unicorn (>484), contender (363-483), pass (<363), failed (kill-switch) |

**Typical Duration**: 2-5 seconds per property

### Phase 4: Report Generation (phase4_report)

Generates HTML deal sheets and visualizations for human review.

| Artifact | Purpose |
|----------|---------|
| `deal_sheet.html` | Property summary with scores and visual charts |
| `radar_chart.html` | 6-axis scoring visualization |
| `comparison_chart.html` | Tier distribution across portfolio |

**Typical Duration**: 10-30 seconds per property

---

## Summary Object

Auto-calculated aggregation of work item statuses. Useful for progress monitoring and dashboard displays.

```json
{
  "summary": {
    "total": 30,
    "pending": 8,
    "in_progress": 2,
    "completed": 18,
    "failed": 2,
    "blocked": 0,
    "completion_percentage": 60.0
  }
}
```

| Field | Type | Calculation | Purpose |
|-------|------|-----------|---------|
| `total` | integer | Count of all work_items | Total properties in batch |
| `pending` | integer | Count where status = "pending" | Awaiting processing |
| `in_progress` | integer | Count where status = "in_progress" | Currently being processed |
| `completed` | integer | Count where status = "completed" | Successfully finished |
| `failed` | integer | Count where status = "failed" | Encountered errors |
| `blocked` | integer | Count where status = "blocked" | Blocked on dependencies |
| `completion_percentage` | float | (completed / total) × 100 | Progress as percentage |

**Recalculation**: The summary is automatically recalculated and updated by `WorkItemsRepository.save_state()` before every write. It should never be manually edited.

---

## Checkpoint Operations

### Initializing a Session

```python
from src.phx_home_analysis.repositories import WorkItemsRepository

repo = WorkItemsRepository("data/work_items.json")
repo.initialize_session(
    mode="batch",
    addresses=[
        "4417 W Sandra Cir",
        "2353 W Tierra Buena Ln",
        "4732 W Davis Rd"
    ]
)
```

**Result**: Creates work_items.json with 3 work items, all status=pending, all phases=pending.

### Checkpointing Phase Start

```python
repo.checkpoint_phase_start(
    address="4417 W Sandra Cir",
    phase="phase0_county"
)
```

**State Changes**:
- `work_items[0].phases.phase0_county.status` = "in_progress"
- `work_items[0].phases.phase0_county.started_at` = now
- `work_items[0].status` = "in_progress" (derived)
- `updated_at` = now

### Checkpointing Phase Complete

**Success**:
```python
repo.checkpoint_phase_complete(
    address="4417 W Sandra Cir",
    phase="phase0_county"
)
```

**State Changes**:
- `work_items[0].phases.phase0_county.status` = "completed"
- `work_items[0].phases.phase0_county.completed_at` = now
- `work_items[0].status` = "pending" (still, until all phases done)
- `summary` recalculated

**Failure**:
```python
repo.checkpoint_phase_complete(
    address="4417 W Sandra Cir",
    phase="phase0_county",
    error_message="HTTP 429: Rate limited"
)
```

**State Changes**:
- `work_items[0].phases.phase0_county.status` = "failed"
- `work_items[0].phases.phase0_county.completed_at` = now
- `work_items[0].phases.phase0_county.error_message` = "HTTP 429: Rate limited"
- `work_items[0].phases.phase0_county.retry_count` = 1
- `work_items[0].status` = "failed" (derived)

---

## Backup and Recovery

### Automatic Backups

Each `save_state()` operation creates a timestamped backup before writing.

**Backup File Naming**: `work_items.20251204_142530.bak.json`

**Retention Policy**: Keep last 10 backups; older backups are automatically deleted.

### Manual Backup Access

List backups:
```bash
ls -lh data/work_items.*.bak.json | tail -10
```

Restore from specific backup:
```python
import shutil
shutil.copy("data/work_items.20251204_140000.bak.json", "data/work_items.json")
```

---

## Validation Rules

### Structural Requirements

1. **File must be valid JSON**
   - Parseable by `json.load()`
   - Top-level must be object with required keys: session, work_items, summary, updated_at

2. **Session must exist and be non-empty**
   - Required fields: session_id, started_at, mode, total_items, current_index
   - session_id must match pattern: `session_YYYYMMDD_HHMMSS_[a-f0-9]{8}`
   - mode must be "batch" or "single"
   - current_index must be 0 ≤ index ≤ total_items

3. **Work items array must not be empty (if initialized)**
   - Each work item requires: id, address, index, status, phases, created_at, updated_at
   - id must be 8-char lowercase hex
   - status must be one of: pending, in_progress, completed, failed, blocked
   - phases object must have exactly 6 keys: phase0_county, phase1_listing, phase1_map, phase2_images, phase3_synthesis, phase4_report
   - Each phase must have: status (required), started_at (optional), completed_at (optional), error_message (optional), retry_count (required)

4. **Phase status must be valid**
   - Valid statuses: pending, in_progress, completed, failed, skipped
   - started_at must be null if status = pending
   - completed_at must be non-null if status = completed or failed

5. **Summary counts must match work items**
   - total = len(work_items)
   - pending = count(status="pending")
   - in_progress = count(status="in_progress")
   - completed = count(status="completed")
   - failed = count(status="failed")
   - blocked = count(status="blocked")

### Status Transition Validation

Defined in `WorkItemsRepository.VALID_PHASE_TRANSITIONS`:

```python
VALID_PHASE_TRANSITIONS = {
    None: [PhaseStatus.PENDING.value],
    PhaseStatus.PENDING.value: [PhaseStatus.IN_PROGRESS.value, PhaseStatus.SKIPPED.value],
    PhaseStatus.IN_PROGRESS.value: [PhaseStatus.COMPLETED.value, PhaseStatus.FAILED.value],
    PhaseStatus.FAILED.value: [PhaseStatus.IN_PROGRESS.value],  # Retry
    PhaseStatus.COMPLETED.value: [],  # Terminal
    PhaseStatus.SKIPPED.value: [],  # Terminal
}
```

**Validation Enforcement**:
- `checkpoint_phase_start()` validates transition to "in_progress"
- `checkpoint_phase_complete()` validates transition to "completed" or "failed"
- All invalid transitions raise `ValueError`

---

## Example: Full Work Item Lifecycle

**Initialization (T=0)**:
```json
{
  "id": "a1b2c3d4",
  "address": "4417 W Sandra Cir",
  "index": 0,
  "status": "pending",
  "phases": {
    "phase0_county": {"status": "pending", "retry_count": 0},
    "phase1_listing": {"status": "pending", "retry_count": 0},
    ...
  },
  "created_at": "2025-12-04T03:00:00.000000+00:00",
  "updated_at": "2025-12-04T03:00:00.000000+00:00"
}
```

**Phase 0 Starts (T+5s)**:
```json
{
  "status": "in_progress",
  "phases": {
    "phase0_county": {
      "status": "in_progress",
      "started_at": "2025-12-04T03:00:05.000000+00:00",
      "retry_count": 0
    },
    ...
  },
  "updated_at": "2025-12-04T03:00:05.000000+00:00"
}
```

**Phase 0 Completes (T+10s)**:
```json
{
  "status": "pending",  # Derived: phase 0 done, others pending
  "phases": {
    "phase0_county": {
      "status": "completed",
      "started_at": "2025-12-04T03:00:05.000000+00:00",
      "completed_at": "2025-12-04T03:00:10.000000+00:00",
      "retry_count": 0
    },
    "phase1_listing": {"status": "pending", "retry_count": 0},
    ...
  },
  "updated_at": "2025-12-04T03:00:10.000000+00:00"
}
```

**Phase 1 Listing Fails (T+50s)**:
```json
{
  "status": "failed",  # Derived: phase 1 failed
  "phases": {
    "phase0_county": {"status": "completed", ...},
    "phase1_listing": {
      "status": "failed",
      "started_at": "2025-12-04T03:00:15.000000+00:00",
      "completed_at": "2025-12-04T03:00:45.000000+00:00",
      "error_message": "HTTP 429: Rate limited by Zillow",
      "retry_count": 1
    },
    ...
  },
  "updated_at": "2025-12-04T03:00:45.000000+00:00"
}
```

**Retry Phase 1 Listing (T+65s)**:
```json
{
  "status": "in_progress",  # Derived: phase 1 restarted, in_progress
  "phases": {
    "phase1_listing": {
      "status": "in_progress",
      "started_at": "2025-12-04T03:01:05.000000+00:00",  # New start time
      "error_message": "HTTP 429: Rate limited by Zillow",  # Preserved
      "retry_count": 1  # Still 1; incremented on next fail
    },
    ...
  },
  "updated_at": "2025-12-04T03:01:05.000000+00:00"
}
```

**All Phases Complete (T+5min)**:
```json
{
  "status": "completed",  # Derived: ALL phases completed
  "phases": {
    "phase0_county": {"status": "completed", ...},
    "phase1_listing": {"status": "completed", ...},
    "phase1_map": {"status": "completed", ...},
    "phase2_images": {"status": "completed", ...},
    "phase3_synthesis": {"status": "completed", ...},
    "phase4_report": {"status": "completed", ...}
  },
  "updated_at": "2025-12-04T03:05:30.000000+00:00"
}
```

---

## Common Patterns and Anti-Patterns

### CORRECT: Checkpointing a Phase

```python
repo = WorkItemsRepository("data/work_items.json")

try:
    # Do phase work
    result = extract_county_data(address)

    # Checkpoint success
    repo.checkpoint_phase_complete(address, "phase0_county")

except Exception as e:
    # Checkpoint failure with error message
    repo.checkpoint_phase_complete(
        address,
        "phase0_county",
        error_message=str(e)
    )
```

### WRONG: Manually Editing Status

```python
# DON'T DO THIS - breaks state machine
state = repo.load_state()
work_item = next(i for i in state["work_items"] if i["address"] == addr)
work_item["status"] = "completed"  # Wrong! Doesn't validate transition
repo.save_state(state)
```

### CORRECT: Retrieving Work Item Status

```python
work_item = repo.get_work_item(address)
if work_item["status"] == "completed":
    print(f"{address}: All phases done")
elif work_item["status"] == "failed":
    print(f"{address}: Processing failed")
    failed_phases = [
        phase for phase, info in work_item["phases"].items()
        if info["status"] == "failed"
    ]
    print(f"Failed phases: {failed_phases}")
```

### WRONG: Assuming JSON is a Dict

```python
# DON'T DO THIS - work_items.json is a specific structure
with open("data/work_items.json") as f:
    items = json.load(f)
    item = items[address]  # TypeError! items is dict with session/work_items/summary keys

# CORRECT:
with open("data/work_items.json") as f:
    state = json.load(f)
    item = next(i for i in state["work_items"] if i["address"] == address)
```

---

## Integration Points

### Orchestration

The `work_items.json` file is the primary state machine driving the analysis pipeline:

1. **Orchestrator** reads `work_items.json` to determine:
   - Which properties have pending phases
   - Which properties are blocked or failed
   - Current progress (for resumable batch processing)

2. **Agents** checkpoint phase start/completion:
   - Phase 0 Agent (County) → checkpoints phase0_county
   - Phase 1 Agents (Listing, Map) → checkpoint phase1_listing, phase1_map
   - Phase 2 Agent (Images) → checkpoints phase2_images
   - Phase 3 Synthesis → checkpoints phase3_synthesis
   - Phase 4 Report → checkpoints phase4_report

3. **CLI** reads `work_items.json` for:
   - Progress display: `jq '.summary' data/work_items.json`
   - Failed items: `jq '.work_items[] | select(.status=="failed")' data/work_items.json`
   - Resume from checkpoint: `current_index` in session

### Data Consistency

- **work_items.json** tracks pipeline progress (phase states)
- **enrichment_data.json** stores property data (scores, analysis results)

**Reconciliation**: A property may exist in enrichment_data.json but be pending/missing in work_items.json if initialized before all properties were extracted.

---

## Implementation Reference

**Repository Class**: `src/phx_home_analysis/repositories/work_items_repository.py`

| Method | Purpose | Updates |
|--------|---------|---------|
| `initialize_session(mode, addresses)` | Create session and work items | Creates work_items.json with all items pending |
| `checkpoint_phase_start(address, phase)` | Mark phase as starting | Phase status → in_progress |
| `checkpoint_phase_complete(address, phase, error_message)` | Mark phase complete/failed | Phase status → completed/failed; updates work item status |
| `get_work_item(address)` | Retrieve single work item | Read-only |
| `get_pending_items()` | Get all unstarted items | Read-only |
| `get_incomplete_items()` | Get all non-completed items | Read-only |
| `load_state()` | Load full state (handles stale reset) | Resets in_progress items > 30min old |
| `save_state(state)` | Persist state (atomic) | Creates backup, writes temp, atomic rename |

**Enum Classes**: `src/phx_home_analysis/domain/enums.py`

| Enum | Values | Purpose |
|------|--------|---------|
| `PhaseStatus` | pending, in_progress, completed, failed, skipped | Phase-level status |
| `WorkItemStatus` | pending, in_progress, completed, failed, blocked | Work item (property) status |

---

## Troubleshooting

### Issue: "Invalid JSON in work_items.json"

**Cause**: File corrupted during write (no atomic pattern used)

**Fix**:
```bash
# Restore from backup
cp data/work_items.YYYYMMDD_HHMMSS.bak.json data/work_items.json

# Or reinitialize (loses checkpoint progress)
python -c "
from src.phx_home_analysis.repositories import WorkItemsRepository
repo = WorkItemsRepository('data/work_items.json')
repo.initialize_session('batch', ['addr1', 'addr2'])
"
```

### Issue: "Work item not found for address"

**Cause**: Address not in session during initialization

**Fix**:
```python
# Check if work item exists
work_item = repo.get_work_item(address)
if work_item is None:
    print(f"{address} not in current session")
    # Add to enrichment_data.json but won't be tracked in work_items until re-initialized
```

### Issue: "Invalid phase transition"

**Cause**: Attempted transition not in VALID_PHASE_TRANSITIONS

**Fix**: Follow state machine rules:
- pending → in_progress (phase_start) or skipped
- in_progress → completed or failed
- failed → in_progress (retry)
- completed and skipped are terminal

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-04 | Initial schema documentation; covers all fields, transitions, examples, and recovery patterns |

---

## Related Files

- **Implementation**: `src/phx_home_analysis/repositories/work_items_repository.py`
- **Enums**: `src/phx_home_analysis/domain/enums.py` (PhaseStatus, WorkItemStatus)
- **State Data**: `data/work_items.json` (actual state file)
- **Enrichment Data**: `data/enrichment_data.json` (property analysis data)
- **CLI**: `scripts/phx_home_analyzer.py` (uses WorkItemsRepository)
- **Commands**: `.claude/commands/analyze-property.md` (orchestrator using work_items)

---

**Last Updated**: 2025-12-04
**Schema Version**: 1.0
**Status**: Complete documentation with full reference, examples, and troubleshooting

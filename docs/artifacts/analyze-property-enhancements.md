# analyze-property.md Enhancement Summary

**Date:** 2025-11-30
**File:** `.claude/commands/analyze-property.md`
**Original Lines:** 338
**Enhanced Lines:** 665
**Lines Added:** 327

---

## Overview

Enhanced the multi-agent property analysis orchestrator with test mode, phase checkpoints, progress tracking, and research queue integration. These additions enable:

1. **Validation before full batch** - Test mode processes 5 properties first
2. **Crash recovery** - Resume from last checkpoint after interruption
3. **Real-time progress** - Visual progress bars and status updates
4. **Automated research** - Missing data triggers fallback estimation

---

## Key Enhancements

### 1. Test Mode (--test flag)

**Location:** Lines 71-115

**Purpose:** Validate pipeline with 5 properties before committing to full batch

**Features:**
- Processes first 5 properties from CSV (after header)
- Applies normal triage (skip completed/max-retry)
- Full Phase 1-4 workflow execution
- Summary report with readiness assessment
- Does NOT auto-continue to full batch

**Success Criteria:**
- 5/5 properties processed or triaged
- No unhandled errors
- State files updated correctly
- Research tasks created as needed

**Example Output:**
```
=== TEST MODE: Processing First 5 Properties ===

Property 1/5: 2353 W Tierra Buena Ln
  Status: success
  Tier: CONTENDER (345/600 pts)

...

Test Summary:
- Attempted: 5
- Completed: 4
- Skipped: 1 (already done)
- Unicorns: 0
- Contenders: 3
- Pass: 1

Ready for full batch: Yes
```

---

### 2. Phase Checkpoint Protocol

**Location:** Lines 137-176

**Purpose:** Track progress at each phase for crash recovery

**Implementation:**
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

**Checkpoint Phases:**
- `phase1_listing` - After listing-browser completes
- `phase1_map` - After map-analyzer completes
- `phase2_images` - After image-assessor completes (or "skipped" if no images)
- `phase3_synthesis` - After scoring completes

**Integration:**
- Updated after each agent completes
- Enables resume from failure point
- Stored in extraction_state.json v2

---

### 3. Progress Display

**Location:** Lines 180-200

**Purpose:** Real-time visibility into batch processing

**Format:**
```
=== Property Analysis Progress ===
Batch: batch_001
Mode: FULL BATCH (33 properties)

Progress: [████████░░░░░░░░] 8/33 (24%)
Current: 4209 W Wahalla Ln, Glendale, AZ
Phase: phase2_images (in_progress)

Completed: 7 | Failed: 1 | Skipped: 0
Unicorns: 0 | Contenders: 5 | Pass: 2

Research Tasks Pending: 3
Last Error: None
```

**Updates:**
- After each property begins
- After each phase completes
- Shows tier distribution in real-time

---

### 4. Research Queue Integration

**Location:** Lines 204-240

**Purpose:** Automated handling of missing data fields

**Workflow:**

**At Orchestrator Start:**
1. Read `data/research_tasks.json`
2. Count pending tasks
3. Log if agents will attempt pickup

**During Image Assessment (Phase 2):**
1. If image-assessor can't determine roof_age/hvac_age/pool_equipment_age:
   - Create research task
   - Execute fallback: `python scripts/estimate_ages.py --property "ADDRESS"`
   - Update enrichment_data.json with estimates
   - Mark task completed (source: "auto-estimated")

**At Orchestrator End:**
1. Report research tasks created
2. Report research tasks completed
3. Report remaining pending tasks

**Task Format:**
```python
{
    "id": "task_a3f9b012",
    "property_address": "123 Main St, Phoenix, AZ",
    "field": "roof_age",
    "reason": "no_roof_images",
    "created_at": "2025-11-30T12:00:00",
    "priority": "high",
    "assigned_agent": "image-assessor",
    "fallback_command": "python scripts/estimate_ages.py --property \"123 Main St\""
}
```

---

### 5. Crash Recovery

**Location:** Lines 570-620

**Purpose:** Resume interrupted batch processing without re-work

**Strategy:**

**1. Load State with Validation**
- Try primary extraction_state.json
- Fall back to .bak if corrupted
- Initialize fresh if both missing

**2. Check In-Progress Properties**
- Identify interrupted properties
- Determine last completed phase
- Report resume plan

**3. Resume from Last Phase**
- Don't re-run completed phases
- Continue from next incomplete phase
- Move to completed when all phases done

**Example Resume:**
```
Found 1 property interrupted:
  - 123 Main St: Last completed phase: phase1_map

Action: Resume from Phase 2 (image-assessor)
```

---

### 6. Enhanced Batch Mode

**Location:** Lines 454-545

**Enhancements:**
- Test mode limiting (first 5 properties)
- Research queue check at start
- Progress banner with dynamic updates
- Per-property phase tracking
- Research task creation/completion tracking
- Enhanced summary report

**Updated Summary Report:**
```
Batch Complete:
- Attempted: 33
- Completed: 30
- Skipped (already done): 0
- Skipped (max retries): 1
- Failed this run: 2
- Unicorns found: 3
- Contenders found: 18
- Pass: 9

Research Tasks:
- Created: 5
- Auto-completed: 5
- Pending manual review: 0
```

---

### 7. Enhanced Error Handling

**Location:** Lines 548-566

**Updates:**
- Mark failed phase in checkpoint
- Increment retry_count
- Add to failed_properties if retry_count < 3
- Skip permanently if retry_count >= 3
- Continue to next property in batch mode

**Error Actions:**
| Error | Action |
|-------|--------|
| Agent fails | Mark phase "failed", log, continue with partial |
| No images | Mark phase2_images "skipped", note in report |
| Rate limited | Backoff retry, update retry_count |
| Max retries | Skip permanently, note in summary |

---

### 8. Pre-Execution Checks

**Location:** Lines 60-68

**Added:**
- Research queue check
- Pending task count
- Agent pickup notification

**Example:**
```bash
# Check for pending research tasks
cat data/research_tasks.json

Note: 3 research tasks pending - agents will attempt pickup
```

---

### 9. Enhanced Verification

**Location:** Lines 635-665

**Additions:**

**Single Property Mode:**
- Verify enrichment_data.json updated
- Verify property in completed_properties
- Verify all phase_status entries
- List research tasks created/completed

**Batch/Test Mode:**
- Verify extraction_state.json stats
- Verify success_rate calculation
- Check no properties stuck in in_progress
- Verify all completed have phase_status
- Report research_tasks.json changes

**Research Task Verification:**
```bash
python -c "
import json
from datetime import datetime, timedelta
tasks = json.load(open('data/research_tasks.json'))
recent = [t for t in tasks.get('pending_tasks', [])
          if datetime.fromisoformat(t['created_at']) > datetime.now() - timedelta(hours=1)]
print(f'Recent tasks: {len(recent)}')
"
```

---

## Integration Points

### With extraction_state.json v2:
- Uses `phase_status` dict for checkpoint tracking
- Updates `in_progress_properties` during processing
- Moves to `completed_properties` after Phase 3
- Uses `retry_counts` for error handling
- Updates `last_checkpoint` after each phase

### With research_tasks.json v1:
- Reads pending tasks at start
- Creates tasks for missing age data
- Executes fallback estimation scripts
- Marks tasks completed with source
- Reports at end

### With Orchestration Workflow:
- Phase 1: Update checkpoints for listing + map
- Phase 2: Check ages, create tasks, run fallback
- Phase 3: Update checkpoint, move to completed
- Phase 4: Generate report with research task info

---

## File Structure

**New Sections Added:**
1. Test Mode (--test) - Complete specification
2. Phase Checkpoint Protocol - Implementation pattern
3. Progress Display - Real-time banner format
4. Research Queue Integration - Full workflow
5. Crash Recovery - Resume strategy

**Enhanced Sections:**
1. Input Parsing - Added --test flag
2. Pre-Execution State Check - Added research queue check
3. Phase 1-3 - Added checkpoint updates
4. Batch Mode Behavior - Added test mode, progress tracking
5. Error Handling - Added checkpoint updates
6. Verification - Added phase/research verification

---

## Schema Compatibility

### extraction_state.json v2:
```json
{
  "$schema": "extraction_state_v2",
  "completed_properties": [],
  "failed_properties": [],
  "in_progress_properties": [],
  "retry_counts": {},
  "phase_status": {
    "property_address": {
      "phase1_listing": "complete",
      "phase1_map": "complete",
      "phase2_images": "in_progress",
      "phase3_synthesis": "pending"
    }
  },
  "last_checkpoint": {
    "property_address": "...",
    "phase": "phase2_images",
    "status": "in_progress",
    "timestamp": "ISO-8601"
  },
  "stats": {
    "total_attempted": 10,
    "success_rate": 0.8
  },
  "last_updated": "ISO-8601"
}
```

### research_tasks.json v1:
```json
{
  "$schema": "research_tasks_v1",
  "pending_tasks": [
    {
      "id": "task_...",
      "property_address": "...",
      "field": "roof_age|hvac_age|pool_equipment_age",
      "reason": "no_roof_images|unclear_equipment",
      "created_at": "ISO-8601",
      "priority": "high|medium|low",
      "assigned_agent": "image-assessor|null",
      "fallback_command": "python scripts/estimate_ages.py ..."
    }
  ],
  "completed_tasks": [],
  "last_updated": "ISO-8601"
}
```

---

## Usage Examples

### Test Mode
```bash
/analyze-property --test
```

### Single Property
```bash
/analyze-property "123 Main St, Phoenix, AZ 85001"
```

### Full Batch
```bash
/analyze-property --all
```

---

## Benefits

1. **Risk Reduction:** Test mode validates before full batch
2. **Reliability:** Crash recovery prevents lost work
3. **Visibility:** Real-time progress tracking
4. **Automation:** Research tasks auto-estimated
5. **Debugging:** Phase checkpoints pinpoint failures
6. **Efficiency:** Resume from last checkpoint, not from scratch

---

## Implementation Status

- [x] Test mode specification
- [x] Phase checkpoint protocol
- [x] Progress display format
- [x] Research queue integration
- [x] Crash recovery strategy
- [x] Enhanced batch mode
- [x] Error handling updates
- [x] Verification enhancements

**Ready for orchestrator implementation.**

---

*Generated: 2025-11-30*
*File: C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\.claude\commands\analyze-property.md*
*Original: 338 lines → Enhanced: 665 lines (+327 lines)*

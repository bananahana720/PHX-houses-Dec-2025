---
allowed-tools: Task, Read, Glob, Grep, Bash(python:*), Write, Edit, Skill
argument-hint: <address> or --all or --test [--strict] [--skip-phase=N] [--resume|--fresh]
description: Multi-agent property analysis with visual browsing
---

# Multi-Agent Property Analysis Orchestrator

Orchestrate multi-phase property analysis using specialized agents and skills.

## STEP 0: GET YOUR BEARINGS (MANDATORY)

Before ANY property analysis, orient yourself to current pipeline state.

**CRITICAL: Read `.claude/AGENT_BRIEFING.md` for quick state orientation.**

```bash
# 1. Confirm working directory
pwd

# 2. Check pipeline state (work_items.json - NEW)
cat data/work_items.json | python -c "
import json,sys
d=json.load(sys.stdin)
print(f'Session: {d[\"session\"][\"session_id\"]}')
print(f'Progress: {d[\"summary\"][\"completed\"]}/{d[\"session\"][\"total_items\"]}')
print(f'Current Index: {d[\"session\"][\"current_index\"]}')
print(f'In Progress: {d[\"summary\"][\"in_progress\"]}')
print(f'Failed: {d[\"summary\"][\"failed\"]}')
"

# 3. Count properties to process
echo "CSV properties:" && wc -l < data/phx_homes.csv
echo "Enriched properties:" && cat data/enrichment_data.json | python -c "import json,sys; print(len(json.load(sys.stdin)))"

# 4. Check metadata files exist
ls -la data/property_images/metadata/

# 5. Review recent git history (property commits)
git log --oneline -10 --grep="feat(property)"

# 6. Check pending research tasks
cat data/research_tasks.json 2>/dev/null | head -20 || echo "No research tasks file"

# 7. Check session blocking status (if resuming)
cat data/session_cache.json 2>/dev/null || echo "Fresh session"
```

**DO NOT PROCEED** until you understand:
- How many properties are completed vs remaining
- Current pipeline state and session ID
- Any blocked sources from previous runs
- Git commit history (properties should have individual commits)

## Arguments: $ARGUMENTS

| Argument | Action |
|----------|--------|
| `--test` | Process first 5 properties (validation mode) |
| `--all` | Process all properties from CSV |
| `<address>` | Single property analysis |

### Execution Flags

| Flag | Behavior |
|------|----------|
| `--strict` | Fail fast on any prerequisite failure (default: warn and continue) |
| `--skip-phase=N` | Skip specified phase (for debugging/recovery) |
| `--resume` | Resume from last checkpoint (default behavior) |
| `--fresh` | Clear all checkpoints, start from Phase 0 |

### --strict Mode Behavior

When `--strict` is enabled:

```python
def execute_phase_strict(phase: int, property_data: dict) -> bool:
    """Execute phase in strict mode.

    In strict mode:
    - ANY prerequisite failure → immediate stop
    - Warnings are treated as errors
    - Partial data not accepted
    """
    prereq_check = check_phase_prerequisites(phase, property_data)

    if not prereq_check["can_proceed"]:
        raise PhasePrerequisiteError(
            phase=phase,
            missing=prereq_check["missing_prerequisites"],
            skip_reason=prereq_check["skip_reason"]
        )

    if prereq_check["warnings"]:
        raise PhasePrerequisiteWarning(
            phase=phase,
            warnings=prereq_check["warnings"]
        )

    # Execute phase...
```

### Default Mode (Non-Strict) Behavior

When `--strict` is NOT enabled:

```python
def execute_phase_default(phase: int, property_data: dict) -> bool:
    """Execute phase in default (lenient) mode.

    In default mode:
    - Prerequisites failures → skip phase with logged reason
    - Warnings → log and continue
    - Partial data accepted
    """
    prereq_check = check_phase_prerequisites(phase, property_data)

    if not prereq_check["can_proceed"]:
        log_warning(f"Skipping Phase {phase}: {prereq_check['skip_reason']}")
        update_phase_status(phase, "skipped", reason=prereq_check["skip_reason"])
        return False  # Phase skipped

    for warning in prereq_check["warnings"]:
        log_warning(f"Phase {phase} warning: {warning}")

    # Execute phase with available data...
```

### Usage Examples

```bash
# Strict mode - fail on any issue
/analyze-property "123 Main St" --strict

# Default mode - continue with warnings
/analyze-property "123 Main St"

# Skip Phase 1 (use existing data)
/analyze-property "123 Main St" --skip-phase=1

# Fresh start - clear all checkpoints
/analyze-property "123 Main St" --fresh
```

## Required Skills

Load skills as needed during orchestration:
- **property-data** - Load/query/update property data
- **state-management** - Checkpointing & crash recovery
- **kill-switch** - Buyer criteria validation
- **county-assessor** - Phase 0 data extraction
- **cost-efficiency** - Monthly cost estimation
- **scoring** - Calculate & assign tiers
- **deal-sheets** - Generate reports

## State Management (work_items.json)

### Schema Overview

```json
{
  "schema_version": "1.0.0",
  "session": {
    "session_id": "session_20251202_123456",
    "start_time": "2025-12-02T12:34:56",
    "mode": "batch|single|test",
    "total_items": 25,
    "current_index": 5
  },
  "work_items": [
    {
      "index": 0,
      "address": "123 Main St, Phoenix, AZ 85001",
      "hash": "abc123de",
      "status": "pending|in_progress|complete|failed",
      "locked_by": null,
      "locked_at": null,
      "phase_status": {
        "phase0_county": "complete",
        "phase05_cost": "complete",
        "phase1_listing": "in_progress",
        "phase1_map": "pending",
        "phase2a_exterior": "pending",
        "phase2b_interior": "pending",
        "phase3_synthesis": "pending",
        "phase4_report": "pending"
      },
      "retry_count": 0,
      "last_updated": "2025-12-02T12:45:00",
      "commit_sha": null,
      "errors": []
    }
  ],
  "summary": {
    "pending": 15,
    "in_progress": 1,
    "complete": 8,
    "failed": 1
  }
}
```

### Property-Level Locking

Before modifying any property data:

```python
from datetime import datetime
import json
from pathlib import Path

def acquire_work_item_lock(work_items: dict, index: int, session_id: str) -> bool:
    """Acquire lock on work item for exclusive access.

    Returns True if lock acquired, False if already locked by another session.
    """
    item = work_items['work_items'][index]

    # Check if already locked by different session
    if item.get('locked_by') and item['locked_by'] != session_id:
        lock_age = datetime.now() - datetime.fromisoformat(item['locked_at'])
        if lock_age.total_seconds() < 3600:  # 1 hour stale lock timeout
            return False

    # Acquire lock
    item['locked_by'] = session_id
    item['locked_at'] = datetime.now().isoformat()
    return True

def release_work_item_lock(work_items: dict, index: int):
    """Release lock on work item."""
    item = work_items['work_items'][index]
    item['locked_by'] = None
    item['locked_at'] = None

# Usage in orchestrator
work_items = load_work_items()
if not acquire_work_item_lock(work_items, idx, session_id):
    log_warning(f"Property {address} locked by another session - skipping")
    continue

try:
    # ... do work ...
finally:
    release_work_item_lock(work_items, idx)
    save_work_items(work_items)
```

### Atomic Updates

Use temp file + rename pattern to prevent corruption:

```python
def save_work_items_atomic(work_items: dict, path: Path):
    """Atomically save work_items.json to prevent corruption."""
    import tempfile
    import shutil

    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=path.parent,
        prefix='work_items_',
        suffix='.tmp',
        delete=False
    ) as tmp:
        json.dump(work_items, tmp, indent=2)
        tmp_path = Path(tmp.name)

    # Atomic rename
    shutil.move(str(tmp_path), str(path))
```

## Session Blocking Cache

Track source blocking status (resets each run):

```python
session_blocking = {"zillow": None, "redfin": None, "google_maps": None}
# None=untested, True=blocked, False=working
```

## Phase Workflow

## Phase Prerequisites

Each phase has explicit dependencies that MUST be satisfied before execution.

### Prerequisite Validation Protocol

Before executing any phase, check:
1. **Previous phase status**: Must be "complete" or "skipped" (not "pending", "in_progress", or "failed")
2. **Required data present**: Fields needed by this phase exist in enrichment_data.json
3. **No blocking errors**: Previous phase didn't fail with fatal error

### Prerequisites by Phase

| Phase | Requires | Required Data | Fatal if Missing |
|-------|----------|---------------|------------------|
| 0: County | Nothing | address | Yes |
| 0.5: Cost | Phase 0 complete | list_price, lot_sqft | No (uses defaults) |
| 1: Listing | Phase 0 ≠ failed | lot_sqft, year_built | No (can estimate) |
| 1: Map | Phase 0 ≠ failed | address, (lat/lon optional) | No |
| 2A: Exterior | Phase 1 listing complete | images in folder | Yes (skip phase) |
| 2B: Interior | Phase 2A complete | exterior scores | No (independent scoring) |
| 3: Synthesis | Phase 0 + Phase 0.5 + Phase 1 complete | kill_switch_passed, monthly_cost, scores | No (partial scoring) |
| 4: Report | Phase 3 complete | total_score, tier | Yes |

### Prerequisite Check Code

```python
def check_phase_prerequisites(phase: int, property_state: dict, enrichment: dict) -> dict:
    """Check if phase prerequisites are satisfied.

    Returns:
        {
            "can_proceed": bool,
            "missing_prerequisites": list[str],
            "warnings": list[str],
            "skip_reason": str | None
        }
    """
    result = {"can_proceed": True, "missing_prerequisites": [], "warnings": [], "skip_reason": None}

    phase_status = property_state.get("phase_status", {})

    if phase == 0:
        # Phase 0 has no prerequisites
        return result

    elif phase == 0.5:
        # Phase 0.5 requires Phase 0 complete
        if phase_status.get("phase0_county") != "complete":
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase0_county not complete")
            result["skip_reason"] = "county_data_required_for_cost"

    elif phase == 1:
        # Requires Phase 0 not failed
        if phase_status.get("phase0_county") == "failed":
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase0_county failed")
            result["skip_reason"] = "county_data_failed"

    elif phase == "2a":
        # Requires Phase 1 listing complete with images
        if phase_status.get("phase1_listing") not in ["complete", "skipped"]:
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase1_listing not complete")

        # Check if images exist
        images_folder = get_images_folder(enrichment.get("full_address"))
        if not images_folder or not any(images_folder.iterdir()):
            result["can_proceed"] = False
            result["skip_reason"] = "no_images_available"

    elif phase == "2b":
        # Phase 2B (interior) requires Phase 2A (exterior) complete
        if phase_status.get("phase2a_exterior") not in ["complete", "skipped"]:
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase2a_exterior not complete")
            result["skip_reason"] = "exterior_assessment_required_first"

    elif phase == 3:
        # Requires Phase 0, Phase 0.5, and at least one Phase 1 task complete
        required_phases = ["phase0_county"]
        optional_phases = ["phase05_cost"]  # Cost estimation enhances scoring
        phase1_options = ["phase1_listing", "phase1_map"]

        for req in required_phases:
            if phase_status.get(req) not in ["complete", "skipped"]:
                result["warnings"].append(f"{req} not complete - scoring may be incomplete")

        for opt in optional_phases:
            if phase_status.get(opt) not in ["complete", "skipped"]:
                result["warnings"].append(f"{opt} not complete - CostEfficiencyScorer will use defaults")

        if not any(phase_status.get(opt) == "complete" for opt in phase1_options):
            result["can_proceed"] = False
            result["missing_prerequisites"].append("no Phase 1 tasks completed")

    elif phase == 4:
        # Requires Phase 3 complete
        if phase_status.get("phase3_synthesis") != "complete":
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase3_synthesis not complete")

    return result
```

### Phase Execution Protocol

For EACH phase, before spawning agents or running scripts:

```
1. CHECK PREREQUISITES
   └─ Run check_phase_prerequisites(phase_num, state, enrichment)
   └─ If can_proceed=False AND strict_mode → STOP with error
   └─ If can_proceed=False AND !strict_mode → SKIP phase, log reason
   └─ If warnings AND strict_mode → STOP with warning
   └─ If warnings AND !strict_mode → LOG warnings, continue

2. VERIFY AGENT AVAILABILITY (for agent-based phases)
   └─ Check agent definition exists
   └─ Verify required skills are loadable
   └─ Confirm MCP tools available (if needed)

3. LOG PHASE START
   └─ Update work_items.json: phase_status[phaseN] = "in_progress"
   └─ Log: "Starting Phase N for {address}"

4. EXECUTE PHASE
   └─ Run agent(s) or script(s)
   └─ Capture return value

5. VALIDATE RESULTS
   └─ Check return status: success|partial|failed
   └─ Verify expected fields populated
   └─ If partial AND strict_mode → treat as failure

6. UPDATE STATE
   └─ If success: phase_status[phaseN] = "complete"
   └─ If partial (default): phase_status[phaseN] = "complete" + warnings
   └─ If failed: phase_status[phaseN] = "failed", increment retry_count
```

### Phase 0: County Data

**Prerequisites:** None (first phase)

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(0, state, enrichment)
# Always proceeds (phase 0 has no prerequisites)
```

**Execution:**
```bash
# Single
python scripts/extract_county_data.py --address "{ADDRESS}" --update-only

# Batch
python scripts/extract_county_data.py --all --update-only
```

**Fields**: lot_sqft, year_built, garage_spaces, has_pool, livable_sqft

**Post-execution validation:**
```python
required_fields = ["lot_sqft", "year_built", "garage_spaces"]
for field in required_fields:
    if enrichment.get(field) is None:
        log_warning(f"Phase 0 missing {field} - will use defaults")
```

**Early kill-switch check:**
```python
from scripts.lib.kill_switch import evaluate_kill_switches, KillSwitchVerdict

verdict, severity, failures, results = evaluate_kill_switches(enrichment)
if verdict == KillSwitchVerdict.FAIL:
    # Still complete Phase 0, but mark property as FAILED
    update_property_tier("FAILED", reason=failures)
    # In strict mode, stop here
    # In default mode, continue for data collection but skip scoring
elif verdict == KillSwitchVerdict.WARNING:
    # Still viable but needs review
    log_warning(f"Kill-switch warnings: {failures}")
# else: PASS - continue normally
```

**Checkpoint**: `phase0_county = "complete"`

### Phase 0.5: Cost Estimation

**Purpose:** Calculate monthly ownership costs for CostEfficiencyScorer

**Prerequisites:**
- Phase 0 must be complete (need property data for cost calculation)

**Implementation:** Inline service call (no CLI script required)

```python
from pathlib import Path
from phx_home_analysis.services.cost_estimation import MonthlyCostEstimator
from phx_home_analysis.services.data_cache import PropertyDataCache

# Load property data
cache = PropertyDataCache()
enrichment = cache.get_enrichment_data(Path("data/enrichment_data.json"))
property_data = enrichment.get(address, {})

# Calculate costs
estimator = MonthlyCostEstimator()
estimate = estimator.estimate(
    price=property_data.get("price", 0),
    sqft=property_data.get("sqft", 0),
    hoa_fee=property_data.get("hoa_fee", 0),
    has_pool=property_data.get("has_pool", False),
    solar_status=property_data.get("solar_status", "none")
)

# Update enrichment data
property_data["monthly_cost"] = estimate.total_monthly
property_data["cost_breakdown"] = estimate.to_dict()

# Save updated enrichment
cache.update_enrichment_data(enrichment, Path("data/enrichment_data.json"))
```

**Fields Updated:**
- `monthly_cost`: Total monthly ownership cost
- `cost_breakdown`: Detailed cost components (mortgage, tax, insurance, HOA, utilities, maintenance, pool, solar)

**Post-execution validation:**
```python
if enrichment.get("monthly_cost") is None:
    log_warning("Cost estimation failed - CostEfficiencyScorer will use defaults")
    enrichment["monthly_cost"] = 0  # Will be flagged by scorer
```

**Fatal if Missing:** No - CostEfficiencyScorer uses defaults if cost unavailable

**Checkpoint**: `phase05_cost = "complete"`

### Phase 1: Data Collection (Parallel)

**Prerequisites:**
- Phase 0 must not be failed
- Address must be present

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(1, state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return
```

**CRITICAL**: Use stealth browsers for Zillow/Redfin (PerimeterX protection).

#### Option A: Direct Script (Preferred)

```bash
# Stealth extraction - bypasses PerimeterX
python scripts/extract_images.py --address "{ADDRESS}" --sources zillow,redfin
```

#### Option B: Agent Delegation

Launch listing-browser and map-analyzer in parallel:

```
Task (model: haiku, subagent: listing-browser)
Target: {ADDRESS}
Skills: property-data, state-management, listing-extraction, kill-switch
MUST use: python scripts/extract_images.py (stealth browser)
DO NOT use: Playwright MCP for Zillow/Redfin (will be blocked)

Task (model: haiku, subagent: map-analyzer)
Target: {ADDRESS}
Skills: property-data, state-management, map-analysis, arizona-context
Analyze schools, safety, orientation, distances
```

**Checkpoints**: `phase1_listing`, `phase1_map`

### Phase 2A: Exterior Assessment (Sequential)

**NEW: Phase 2 is now split into 2A (Exterior) and 2B (Interior)**

**Prerequisites:**
- Phase 1 listing must be complete (images downloaded)
- Images folder must contain at least 1 image

**Pre-execution check:**
```python
prereq = check_phase_prerequisites("2a", state, enrichment)

if not prereq["can_proceed"]:
    if prereq["skip_reason"] == "no_images_available":
        log_info("Phase 2A skipped: No images available for visual assessment")
        update_phase_status("phase2a_exterior", "skipped", reason="no_images")
        update_phase_status("phase2b_interior", "skipped", reason="no_images")
        # Use default scores (5.0) for Section B exterior
        apply_default_exterior_scores(enrichment)
        return
    else:
        handle_prerequisite_failure(prereq, strict_mode)
        return
```

**Agent spawn (only if prerequisites satisfied):**
```
Task (model: sonnet, subagent: image-assessor)
Target: {ADDRESS}
Phase: 2A (Exterior)
Skills: property-data, image-assessment, arizona-context-lite, scoring
Score Section B exterior (80 pts): roof, backyard, pool
Estimate ages: roof, HVAC, pool equipment
```

**Output:**
- `roof_score` (0-50 pts)
- `backyard_score` (0-40 pts)
- `pool_score` (0-20 pts if pool exists)
- `roof_age_estimate`
- `pool_age_estimate`

**Checkpoint**: `phase2a_exterior = "complete"`

### Phase 2B: Interior Assessment (Sequential)

**Prerequisites:**
- Phase 2A must be complete (exterior assessment done first)

**Pre-execution check:**
```python
prereq = check_phase_prerequisites("2b", state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return
```

**Agent spawn:**
```
Task (model: sonnet, subagent: image-assessor)
Target: {ADDRESS}
Phase: 2B (Interior)
Skills: property-data, image-assessment, arizona-context-lite, scoring
Score Section C interior (190 pts): kitchen, master, light, ceilings, fireplace, laundry, aesthetics
```

**Output:**
- `kitchen_score` (0-40 pts)
- `master_score` (0-40 pts)
- `light_score` (0-30 pts)
- `ceiling_score` (0-30 pts)
- `fireplace_score` (0-20 pts)
- `laundry_score` (0-20 pts)
- `aesthetics_score` (0-10 pts)

**Checkpoint**: `phase2b_interior = "complete"`

### Phase 3: Synthesis & Scoring

**Prerequisites:**
- Phase 0 must be complete
- Phase 0.5 should be complete (cost estimation for CostEfficiencyScorer)
- At least one Phase 1 task must be complete

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(3, state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return

for warning in prereq["warnings"]:
    log_warning(f"Phase 3: {warning}")
```

**Use existing scripts** (Axiom 10: Reuse Logic):

```bash
python scripts/analyze.py
cat data/phx_homes_ranked.csv | head -20
```

**Scoring Components:**
- **PropertyScorer**: 600-point weighted scoring (Location, Systems, Interior)
- **CostEfficiencyScorer**: Evaluates monthly_cost vs quality score ratio
  - Uses `monthly_cost` from Phase 0.5
  - Flags properties exceeding $4k/month budget
  - Identifies value opportunities (high score, low cost)

**Tier Assignment** (600-point scale):
- UNICORN: >480 pts (80%+)
- CONTENDER: 360-480 pts (60-80%)
- PASS: <360 pts (<60%)
- FAILED: Kill-switch failure

**Checkpoint**: `phase3_synthesis`, move to `completed_properties`

### Phase 4: Report Generation

**Prerequisites:**
- Phase 3 must be complete

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(4, state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return
```

**Execution:**
```bash
python -m scripts.deal_sheets --property "{ADDRESS}"
```

Generate markdown summary with tier, scores, strengths, concerns, and recommendation.

**Checkpoint**: `phase4_report = "complete"`

## Git Commit Protocol

### Commit After Each Property

After all phases complete for a property, commit changes to preserve progress and enable recovery.

#### Commit Points Table

| When | Files to Stage | Rationale |
|------|----------------|-----------|
| After Phase 0+0.5 | enrichment_data.json, work_items.json | County + cost data acquired |
| After Phase 1 | enrichment_data.json, work_items.json, images/*, metadata/*.json | Listing + map data complete |
| After Phase 2 | enrichment_data.json, work_items.json | Visual scores assigned |
| After Phase 3+4 | enrichment_data.json, work_items.json, ranked.csv, deal_sheets/* | Final scoring + report |
| Property complete | All of the above | Full property checkpoint |

#### Commit Message Template

```bash
# Stage files
git add data/enrichment_data.json data/work_items.json

# If Phase 1 completed (images)
if [ -d "data/property_images/processed/{hash}" ]; then
  git add "data/property_images/processed/{hash}/*"
  git add data/property_images/metadata/*.json
fi

# If Phase 4 completed (report)
if ls reports/deal_sheets/*{hash}* 1> /dev/null 2>&1; then
  git add "reports/deal_sheets/*{hash}*"
fi

# Commit with structured message
git commit -m "$(cat <<'EOF'
feat(property): Complete {address_short} - {tier} ({score}/600)

Property: {full_address}
Hash: {hash}
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✓ | Synthesis ✓ | Report ✓
Kill-switch: {PASS|WARNING|FAIL}
Tier: {tier}
Score: {score}/600
Monthly Cost: ${monthly_cost}

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Update work_items.json with commit SHA
python -c "
import json
from pathlib import Path
import subprocess

# Get commit SHA
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()

# Update work_items.json
work_items_path = Path('data/work_items.json')
work_items = json.loads(work_items_path.read_text())

# Find property by hash
for item in work_items['work_items']:
    if item['hash'] == '{hash}':
        item['commit_sha'] = sha
        break

work_items_path.write_text(json.dumps(work_items, indent=2))
"
```

#### Example Commit Messages

```
feat(property): Complete 4732 W Davis Rd - CONTENDER (412/600)

Property: 4732 W Davis Rd, Glendale, AZ 85306
Hash: ef7cd95f
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✓ | Synthesis ✓ | Report ✓
Kill-switch: PASS
Tier: CONTENDER
Score: 412/600
Monthly Cost: $3,245

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
feat(property): Complete 2353 W Tierra Buena Ln - FAILED (0/600)

Property: 2353 W Tierra Buena Ln, Phoenix, AZ 85023
Hash: abc12345
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✗ | Synthesis ✗ | Report ✗
Kill-switch: FAIL (HOA fee: $250/mo)
Tier: FAILED
Score: 0/600
Monthly Cost: N/A

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Merge Conflict Prevention

#### Property-Level Locking (Already Covered Above)

See "State Management (work_items.json)" → "Property-Level Locking" section.

#### Serialized Updates

**Orchestrator Pattern:**
1. Collect all phase updates in memory
2. Single atomic write per property completion
3. Use temp file + rename pattern (see `save_work_items_atomic`)

```python
# BAD: Multiple writes per property
for phase in phases:
    execute_phase(phase)
    save_work_items(work_items)  # ❌ N writes

# GOOD: Single write per property
phase_results = []
for phase in phases:
    result = execute_phase(phase)
    phase_results.append(result)

# Apply all updates at once
for result in phase_results:
    update_phase_status(work_items, result)

save_work_items_atomic(work_items, work_items_path)  # ✓ 1 write
```

## Batch Processing

### Triage

```python
# Skip if:
# - status == "complete" (in work_items.json)
# - retry_count >= 3
# For --test: limit to first 5 from CSV
```

### Sequential Processing

```
for property in to_process:
    1. Acquire lock (work_items.json)
    2. Phase 0 (county) → early kill-switch check
    3. Phase 0.5 (cost) → monthly cost estimation
    4. Phase 1 (listing + map) → parallel
    5. Phase 2A (exterior) → if images exist
    6. Phase 2B (interior) → if Phase 2A complete
    7. Phase 3 (synthesis) → includes CostEfficiencyScorer
    8. Phase 4 (report)
    9. Update work_items.json
   10. Git commit property completion
   11. Release lock
```

### Progress Display

```
Processing: 5/25 properties
Current: 123 Main St, Phoenix, AZ 85001
Phase: 2B (Interior Assessment)
Completed: 4 | Failed: 0 | Skipped: 1
Unicorns: 1 | Contenders: 2 | Pass: 1

Session: session_20251202_123456
Locked: 123 Main St
Last Commit: ef7cd95f (4732 W Davis Rd - CONTENDER)
```

## Optimization Rules

1. **Check data completeness** before spawning agents
2. **Skip if complete** - Don't reprocess finished properties (check work_items.json)
3. **Test one first** - Verify source not blocked before batch
4. **Fail fast** - After 3 consecutive same errors, skip source
5. **Commit frequently** - One commit per property for crash recovery

## Error Handling

| Error | Action |
|-------|--------|
| Agent fails | Log, mark phase "failed", continue with partial |
| No images | Mark phase2a_exterior, phase2b_interior "skipped" |
| Rate limited | Backoff, retry, increment retry_count |
| Max retries | Skip permanently |
| Lock conflict | Skip property (another session owns it) |

**Always generate report with available data.**

## Crash Recovery with work_items.json

On restart, the work_items.json system ensures safe resumption:

### Recovery Protocol

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

## Verification

### Single Property

- [ ] enrichment_data.json updated
- [ ] work_items.json shows complete
- [ ] All phase_status entries complete/skipped
- [ ] Git commit created with property hash
- [ ] commit_sha populated in work_items.json

### Batch

- [ ] Stats match property counts
- [ ] No properties stuck in in_progress
- [ ] Summary report generated
- [ ] Git log shows individual property commits
- [ ] work_items.json summary accurate

## Summary Report

```
ANALYSIS COMPLETE
=================
Session: session_20251202_123456
Attempted: 25
Completed: 23
Failed: 2

Tier Breakdown:
- Unicorns: 3
- Contenders: 12
- Pass: 6
- Failed: 2

Git Commits: 23 (1 per completed property)
Research Tasks Pending: 4

Next Steps:
- Review failed properties: 2353 W Tierra Buena Ln, 8426 E Lincoln Dr
- Run: git log --oneline --grep="feat(property)" to see all commits
```

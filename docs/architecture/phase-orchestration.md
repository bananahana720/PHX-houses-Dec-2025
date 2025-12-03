# Phase Orchestration Protocol

Detailed phase workflow for the multi-agent property analysis pipeline.

## Phase Dependencies

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

## Phase 0: County Data

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

## Phase 0.5: Cost Estimation

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

## Phase 1: Data Collection (Parallel)

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

### Option A: Direct Script (Preferred)

```bash
# Stealth extraction - bypasses PerimeterX
python scripts/extract_images.py --address "{ADDRESS}" --sources zillow,redfin
```

### Option B: Agent Delegation

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

## Phase 2A: Exterior Assessment

**NEW: Phase 2 is now split into 2A (Exterior) and 2B (Interior)**

**Prerequisites:**
- Phase 1 listing must be complete (images downloaded)
- Images folder must contain at least 1 image

### Pre-Spawn Validation Protocol (MANDATORY)

Before spawning the image-assessor agent, ALWAYS run validation using the dedicated script:

#### Step 1: Validate Prerequisites

```bash
python scripts/validate_phase_prerequisites.py --address "$ADDRESS" --phase phase2_images --json
```

**If exit code 0 (can_spawn=true):**
- Parse the JSON output to get the `context` dict
- Extract key fields: `image_folder`, `image_count`, `property_data` (year_built, lot_sqft, beds, baths, has_pool)
- Proceed to spawn the agent with validated context

**If exit code 1 (can_spawn=false):**
- Read the `reason` field from JSON output
- Report to user: "BLOCKED: {reason}"
- DO NOT spawn the agent
- Suggest remediation based on reason:
  - "Phase 1 listing not complete" -> Run Phase 1 first
  - "No image folder mapping found" -> Run `python scripts/extract_images.py --address "$ADDRESS"`
  - "Image folder exists but contains no images" -> Re-run image extraction

#### Step 2: Data Quality Check (Recommended)

```bash
python scripts/validate_phase_prerequisites.py --reconcile --address "$ADDRESS" --repair --json
```

- If issues found and repaired, re-run Step 1 validation
- If issues persist after repair, warn user but allow spawn if Step 1 passed
- Check `completeness_score` and `accuracy_score` - warn if below 0.7

#### Step 3: Include Validated Context in Spawn Prompt

When spawning the image-assessor, include the pre-verified context from validation:

```markdown
## Pre-Verified Context (Orchestrator Validated)

**Target Property:** {context.address}
**Phase:** 2A (Exterior Assessment)

### Prerequisites Verified:
- [x] Phase 1 Status: {context.phase_status.phase1_listing}
- [x] Image Folder: {context.image_folder} (exists: YES)
- [x] Image Count: {context.image_count}
- [x] Year Built: {context.property_data.year_built}

### Property Data Snapshot:
- Lot: {context.property_data.lot_sqft} sqft
- Beds/Baths: {context.property_data.beds}/{context.property_data.baths}
- Has Pool: {context.property_data.has_pool}
- Orientation: {context.property_data.orientation}
- Square Footage: {context.property_data.sqft}

**PROCEED:** All prerequisites verified - begin exterior assessment.
```

### Agent Spawn Example

```python
import subprocess
import json

def validate_and_spawn_phase2(address: str, strict_mode: bool) -> bool:
    """Validate prerequisites before spawning Phase 2 agent."""

    # Run validation script
    result = subprocess.run(
        ["python", "scripts/validate_phase_prerequisites.py",
         "--address", address, "--phase", "phase2_images", "--json"],
        capture_output=True,
        text=True
    )

    try:
        validation = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Script failed - use fallback or abort
        if strict_mode:
            raise ValidationError(f"Validation script failed: {result.stderr}")
        log_warning("Validation script failed, using fallback")
        validation = {"can_spawn": False, "reason": "Validation script error"}

    if not validation["can_spawn"]:
        reason = validation.get("reason", "Unknown reason")
        log_error(f"BLOCKED: {reason}")

        if strict_mode:
            raise PhasePrerequisiteError(phase="2A", reason=reason)

        update_phase_status("phase2a_exterior", "skipped", reason=reason)
        update_phase_status("phase2b_interior", "skipped", reason=reason)
        return False

    # Extract validated context for agent prompt
    context = validation.get("context", {})
    spawn_phase2_agent(address, context)
    return True
```

**Agent spawn (only if prerequisites satisfied):**
```
Task (model: sonnet, subagent: image-assessor)
Target: {ADDRESS}
Phase: 2A (Exterior)
Skills: property-data, image-assessment, arizona-context-lite, scoring

## Pre-Verified Context
- Image Folder: {context.image_folder}
- Image Count: {context.image_count}
- Year Built: {context.property_data.year_built}
- Has Pool: {context.property_data.has_pool}
- Lot Size: {context.property_data.lot_sqft} sqft

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

## Phase 2B: Interior Assessment

**Prerequisites:**
- Phase 2A must be complete (exterior assessment done first)
- Same image folder validation applies

**Pre-execution check:**

```python
def validate_and_spawn_phase2b(address: str, strict_mode: bool) -> bool:
    """Validate prerequisites before spawning Phase 2B agent."""

    # First, verify Phase 2A is complete via work_items.json
    work_items = load_work_items()
    item = find_work_item(address, work_items)

    if not item:
        log_error(f"BLOCKED: Property '{address}' not in work_items.json")
        return False

    phase2a_status = item.get("phases", {}).get("phase2a_exterior", {}).get("status")
    if phase2a_status not in ["complete", "skipped"]:
        log_error(f"BLOCKED: Phase 2A not complete (status: {phase2a_status})")
        if strict_mode:
            raise PhasePrerequisiteError(phase="2B", reason="Phase 2A not complete")
        update_phase_status("phase2b_interior", "skipped", reason="phase2a_incomplete")
        return False

    # Run validation script for image folder verification
    result = subprocess.run(
        ["python", "scripts/validate_phase_prerequisites.py",
         "--address", address, "--phase", "phase2_images", "--json"],
        capture_output=True,
        text=True
    )

    try:
        validation = json.loads(result.stdout)
    except json.JSONDecodeError:
        if strict_mode:
            raise ValidationError(f"Validation script failed: {result.stderr}")
        log_warning("Validation script failed, using Phase 2A context")
        validation = {"can_spawn": True, "context": {"address": address}}

    if not validation["can_spawn"]:
        reason = validation.get("reason", "Unknown reason")
        log_error(f"BLOCKED: {reason}")
        update_phase_status("phase2b_interior", "skipped", reason=reason)
        return False

    # Include Phase 2A results in context
    context = validation.get("context", {})
    context["phase2a_complete"] = True
    context["exterior_scores_available"] = True

    spawn_phase2b_agent(address, context)
    return True
```

**Agent spawn with validated context:**
```
Task (model: sonnet, subagent: image-assessor)
Target: {ADDRESS}
Phase: 2B (Interior)
Skills: property-data, image-assessment, arizona-context-lite, scoring

## Pre-Verified Context (Orchestrator Validated)

**Target Property:** {context.address}
**Phase:** 2B (Interior Assessment)

### Prerequisites Verified:
- [x] Phase 2A Status: complete
- [x] Image Folder: {context.image_folder} (exists: YES)
- [x] Image Count: {context.image_count}
- [x] Year Built: {context.property_data.year_built}

### Property Data Snapshot:
- Lot: {context.property_data.lot_sqft} sqft
- Beds/Baths: {context.property_data.beds}/{context.property_data.baths}
- Has Pool: {context.property_data.has_pool}
- Square Footage: {context.property_data.sqft}

**PROCEED:** All prerequisites verified - begin interior assessment.

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

## Phase 3: Synthesis & Scoring

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

**Use existing scripts**:

```bash
python scripts/analyze.py
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

## Phase 4: Report Generation

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

## Batch Processing Protocol

### Sequential Processing Flow

```
for property in to_process:
    1. Acquire lock (work_items.json)
    2. Phase 0 (county) → early kill-switch check
    3. Phase 0.5 (cost) → monthly cost estimation
    4. Phase 1 (listing + map) → parallel
    5. PRE-SPAWN VALIDATION for Phase 2:
       └─ python scripts/validate_phase_prerequisites.py --address "$ADDRESS" --phase phase2_images --json
       └─ If exit code 1 → log BLOCKED, skip Phase 2A/2B
       └─ If exit code 0 → extract context for agent spawn
    6. Phase 2A (exterior) → spawn with validated context
    7. Phase 2B (interior) → spawn with validated context (if Phase 2A complete)
    8. Phase 3 (synthesis) → includes CostEfficiencyScorer
    9. Phase 4 (report)
   10. Update work_items.json
   11. Git commit property completion
   12. Release lock
```

### Triage

```python
# Skip if:
# - status == "complete" (in work_items.json)
# - retry_count >= 3
# For --test: limit to first 5 from CSV
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

## Crash Recovery Protocol

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

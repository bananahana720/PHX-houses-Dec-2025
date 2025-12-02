---
allowed-tools: Task, Read, Glob, Grep, Bash(python:*), Write, Edit, Skill
argument-hint: <address> or --all or --test [--strict] [--skip-phase=N] [--resume|--fresh]
description: Multi-agent property analysis with visual browsing
---

# Multi-Agent Property Analysis Orchestrator

Orchestrate multi-phase property analysis using specialized agents and skills.

## STEP 0: GET YOUR BEARINGS (MANDATORY)

Before ANY property analysis, orient yourself to current pipeline state:

```bash
# 1. Confirm working directory
pwd

# 2. Check pipeline state
cat data/property_images/metadata/extraction_state.json | python -c "import json,sys; d=json.load(sys.stdin); print(f'Completed: {len(d.get(\"completed_properties\",[]))}, In Progress: {len(d.get(\"in_progress_properties\",[]))}, Failed: {len(d.get(\"failed_properties\",[]))}')"

# 3. Count properties to process
echo "CSV properties:" && wc -l < data/phx_homes.csv
echo "Enriched properties:" && cat data/enrichment_data.json | python -c "import json,sys; print(len(json.load(sys.stdin)))"

# 4. Check metadata files exist
ls -la data/property_images/metadata/

# 5. Review recent git history
git log --oneline -5

# 6. Check pending research tasks
cat data/research_tasks.json 2>/dev/null | head -20 || echo "No research tasks file"

# 7. Check session blocking status (if resuming)
cat data/session_cache.json 2>/dev/null || echo "Fresh session"
```

**DO NOT PROCEED** until you understand:
- How many properties are completed vs remaining
- Current pipeline state
- Any blocked sources from previous runs

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
| 2: Images | Phase 1 listing complete | images in folder | Yes (skip phase) |
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

    elif phase == 2:
        # Requires Phase 1 listing complete with images
        if phase_status.get("phase1_listing") not in ["complete", "skipped"]:
            result["can_proceed"] = False
            result["missing_prerequisites"].append("phase1_listing not complete")

        # Check if images exist
        images_folder = get_images_folder(enrichment.get("full_address"))
        if not images_folder or not any(images_folder.iterdir()):
            result["can_proceed"] = False
            result["skip_reason"] = "no_images_available"

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
   └─ Update extraction_state.json: phase_status[phaseN] = "in_progress"
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

### Phase 2: Visual Assessment (Sequential)

**Prerequisites:**
- Phase 1 listing must be complete (images downloaded)
- Images folder must contain at least 1 image

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(2, state, enrichment)

if not prereq["can_proceed"]:
    if prereq["skip_reason"] == "no_images_available":
        log_info("Phase 2 skipped: No images available for visual assessment")
        update_phase_status("phase2_images", "skipped", reason="no_images")
        # Use default scores (5.0) for Section C
        apply_default_interior_scores(enrichment)
        return
    else:
        handle_prerequisite_failure(prereq, strict_mode)
        return
```

**Agent spawn (only if prerequisites satisfied):**
```
Task (model: sonnet, subagent: image-assessor)
Target: {ADDRESS}
Skills: property-data, image-assessment, arizona-context, scoring
Score Section C (190 pts): kitchen, master, light, ceilings, fireplace, laundry, aesthetics
```

**If missing ages**: `python scripts/estimate_ages.py --property "{ADDRESS}"`

**Checkpoint**: `phase2_images`

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

## Batch Processing

### Triage

```python
# Skip if:
# - In completed_properties
# - retry_count >= 3
# For --test: limit to first 5 from CSV
```

### Sequential Processing

```
for property in to_process:
    1. Phase 0 (county) → early kill-switch check
    2. Phase 0.5 (cost) → monthly cost estimation
    3. Phase 1 (listing + map) → parallel
    4. Phase 2 (images) → if images exist
    5. Phase 3 (synthesis) → includes CostEfficiencyScorer
    6. Phase 4 (report)
    7. Update checkpoints
```

### Progress Display

```
Processing: 5/25 properties
Current: 123 Main St, Phoenix, AZ 85001
Phase: 2 (Image Assessment)
Completed: 4 | Failed: 0 | Skipped: 1
Unicorns: 1 | Contenders: 2 | Pass: 1
```

## Optimization Rules

1. **Check data completeness** before spawning agents
2. **Skip if complete** - Don't reprocess finished properties
3. **Test one first** - Verify source not blocked before batch
4. **Fail fast** - After 3 consecutive same errors, skip source

## Error Handling

| Error | Action |
|-------|--------|
| Agent fails | Log, mark phase "failed", continue with partial |
| No images | Mark phase2_images "skipped" |
| Rate limited | Backoff, retry, increment retry_count |
| Max retries | Skip permanently |

**Always generate report with available data.**

## Crash Recovery with Prerequisite Awareness

On restart, the prerequisite system ensures safe resumption:

### Recovery Protocol

```python
def recover_from_crash(property_address: str) -> dict:
    """Recover property processing from crash.

    Returns next phase to execute and any warnings.
    """
    state = load_extraction_state()
    property_state = state.get("properties", {}).get(property_address, {})

    if not property_state:
        return {"next_phase": 0, "warnings": ["No state found, starting fresh"]}

    phase_status = property_state.get("phase_status", {})

    # Find last completed phase
    phases = ["phase0_county", "phase05_cost", "phase1_listing", "phase1_map", "phase2_images", "phase3_synthesis"]
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
            if property_state.get("retry_count", 0) >= 3:
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
Property: 123 Main St, Phoenix, AZ 85001
Last Checkpoint: phase05_cost (complete)
Crashed During: phase1_listing (in_progress)
Action: Retry Phase 1 (attempt 2/3)
Prerequisites: Verified (phase0_county, phase05_cost complete)
```

## Verification

### Single Property

- [ ] enrichment_data.json updated
- [ ] extraction_state.json shows complete
- [ ] All phase_status entries complete/skipped

### Batch

- [ ] Stats match property counts
- [ ] No properties stuck in in_progress
- [ ] Summary report generated

## Summary Report

```
ANALYSIS COMPLETE
=================
Attempted: 25
Completed: 23
Failed: 2

Tier Breakdown:
- Unicorns: 3
- Contenders: 12
- Pass: 6
- Failed: 2

Research Tasks Pending: 4
```

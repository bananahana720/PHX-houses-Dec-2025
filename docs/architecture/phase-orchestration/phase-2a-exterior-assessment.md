# Phase 2A: Exterior Assessment

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
Task (model: opus, subagent: image-assessor)
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

# Phase 2B: Interior Assessment

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
Task (model: opus, subagent: image-assessor)
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

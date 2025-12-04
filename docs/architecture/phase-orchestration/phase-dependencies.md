# Phase Dependencies

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

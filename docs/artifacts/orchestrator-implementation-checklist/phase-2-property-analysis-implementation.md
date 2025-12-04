# Phase 2: Property Analysis Implementation

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

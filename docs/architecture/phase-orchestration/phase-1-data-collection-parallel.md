# Phase 1: Data Collection (Parallel)

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

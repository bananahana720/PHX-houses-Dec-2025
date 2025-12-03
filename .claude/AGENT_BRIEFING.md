# Agent Briefing: PHX Houses Pipeline

**Purpose:** 5-second state orientation for spawned agents in multi-phase property analysis workflows.

---

## Critical Behavior (Agent-Level)

- [x] Always read this briefing before starting work
- [x] Check `work_items.json` for current phase and property status
- [x] Validate prerequisites before Phase 2 (images + Phase 1 complete)
- [x] Update state files atomically (read-modify-write with locks)
- [x] Return structured JSON results per protocol
- Never do:
  - [x] Start Phase 2 without Phase 1 completion
  - [x] Overwrite data without reading current state first
  - [x] Leave status as `in_progress` on exit (always set `completed` or `failed`)

---

## Data Structure Reference

### Critical: Know Your Data Types

| File | Type | Key Field | Access Pattern |
|------|------|-----------|----------------|
| `enrichment_data.json` | **LIST** | `full_address` | Iterate to find |
| `work_items.json` | Dict | `work_items` (list) | `data["work_items"]` |
| `address_folder_lookup.json` | Dict | `mappings[address]` | Direct key lookup |
| `phx_homes.csv` | CSV | `full_address` | pandas or csv module |

### enrichment_data.json (LIST, not dict!)

```python
# CORRECT - It's a list, search by address
data = json.loads(file_content)  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG - These will fail
prop = data[address]      # TypeError: list indices must be integers
prop = data.get(address)  # AttributeError: 'list' has no 'get'
```

### address_folder_lookup.json

```python
# CORRECT - Access via mappings key
lookup = json.loads(file_content)
mapping = lookup.get("mappings", {}).get(address)
if mapping:
    folder = mapping["folder"]      # e.g., "686067a4"
    path = mapping["path"]          # e.g., "data/property_images/processed/686067a4/"
    count = mapping["image_count"]
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `'list' object has no attribute 'get'` | Treating enrichment as dict | Use list iteration |
| `KeyError: 'address'` | Wrong key in lookup | Use `lookup["mappings"][address]` |
| `TypeError: string indices` | Lookup returned string | Check if result is dict |

---

## Key Files

| File | Purpose | Mode | Critical Fields |
|------|---------|------|-----------------|
| `data/work_items.json` | Pipeline state | RW | `properties[].phase_status` |
| `data/enrichment_data.json` | Property data (LIST) | RW | `[].full_address`, `[].listing` |
| `data/property_images/metadata/extraction_state.json` | Image state | RW | `[address].status` |
| `data/property_images/metadata/address_folder_lookup.json` | Address→folder | R | `mappings[address]` |
| `data/phx_homes.csv` | Source listings | R | `address`, `price` |

---

## Agent Roles

| Agent | Phase | Model | Purpose | Outputs |
|-------|-------|-------|---------|---------|
| listing-browser | 1 | Haiku | Zillow/Redfin extraction | price, beds, baths, HOA |
| map-analyzer | 1 | Haiku | Geographic analysis | schools, safety, orientation |
| image-assessor | 2 | Sonnet | Interior scoring (190 pts) | 7 interior scores (0-10 each) |

### Skills by Agent

| Agent | Required Skills |
|-------|-----------------|
| listing-browser | `listing-extraction`, `property-data`, `state-management` |
| map-analyzer | `map-analysis`, `property-data`, `arizona-context-lite` |
| image-assessor | `image-assessment`, `property-data`, `arizona-context-lite` |

---

## Phase Dependencies

```
Phase 0: County API (independent)
    └── lot_sqft, year_built, garage_spaces, pool

Phase 1: Listing + Map (parallel)
    ├── listing-browser → price, beds, baths, HOA, images
    └── map-analyzer → schools, safety, orientation
              │
              ▼ (requires Phase 1 complete)

Phase 2: Image Assessment
    └── image-assessor → 7 interior scores (Section C: 190 pts)
              │
              ▼ (requires Phase 2 complete)

Phase 3: Synthesis
    └── total_score, tier, kill_switch_verdict
              │
              ▼

Phase 4: Reports
    └── deal_sheets, visualizations
```

**Rules:**
- Phase 0 is optional, runs anytime
- Phase 1 agents run in parallel
- Phase 2 **blocks** until Phase 1 `completed`
- Phase 3 **blocks** until Phase 2 `completed`

---

## Pre-Work Checklist

```python
# 1. Load state
work_items = json.load(open('data/work_items.json'))
enrichment = json.load(open('data/enrichment_data.json'))  # LIST!

# 2. Find property
prop = next(p for p in work_items['properties'] if p['address'] == target_address)

# 3. Check not already complete
if prop['phase_status'].get(f'phase_{current_phase}') == 'completed':
    print("WARNING: Already processed")

# 4. Phase 2 prerequisites
if current_phase == 2:
    assert prop['phase_status']['phase_1'] == 'completed'
    enrich_prop = next((p for p in enrichment if p['full_address'] == target_address), None)
    assert enrich_prop and 'images' in enrich_prop

# 5. Set in-progress
prop['phase_status'][f'phase_{current_phase}'] = 'in_progress'
json.dump(work_items, open('data/work_items.json', 'w'), indent=2)
```

---

## Post-Work Protocol

```python
# 1. Update enrichment (LIST - find by address)
enrich_prop = next((p for p in enrichment if p['full_address'] == target_address), None)
if enrich_prop:
    enrich_prop['listing'] = {'price': 425000, 'beds': 4, ...}
json.dump(enrichment, open('data/enrichment_data.json', 'w'), indent=2)

# 2. Update phase status
prop['phase_status'][f'phase_{current_phase}'] = 'completed'
prop['last_updated'] = datetime.now().isoformat()
json.dump(work_items, open('data/work_items.json', 'w'), indent=2)

# 3. Return structured result
result = {
    'status': 'success',
    'address': target_address,
    'phase': current_phase,
    'data': {...},
    'warnings': [],
    'next_steps': []
}
```

---

## Error Recovery

### File Not Found

```python
if not os.path.exists('data/work_items.json'):
    print("CRITICAL: work_items.json not found")
    print("→ Ask orchestrator to initialize with /analyze-property")
    sys.exit(1)
```

### Missing Images (Phase 2)

```python
manifest = json.load(open('data/property_images/metadata/image_manifest.json'))
folder_hash = get_folder_hash(target_address)
if folder_hash not in manifest or len(manifest[folder_hash]) == 0:
    print(f"No images for {target_address}")
    print("→ Run: python scripts/extract_images.py --address '{address}'")
    return {'status': 'retry', 'reason': 'missing_images'}
```

### Stale State (Stuck in_progress)

```python
for prop in work_items['properties']:
    for phase, status in prop['phase_status'].items():
        if status == 'in_progress':
            age = datetime.now() - datetime.fromisoformat(prop['last_updated'])
            if age.seconds > 600:  # 10 min timeout
                print(f"Resetting stuck {phase} for {prop['address']}")
                prop['phase_status'][phase] = 'pending'
```

---

## Phase Exit Criteria

| Phase | Required Outputs | Quality Gates |
|-------|------------------|---------------|
| 0 | lot_sqft, year_built, garage_spaces | Assessor API data |
| 1 | price, beds, baths, HOA, school_rating, safety_score | All required fields |
| 2 | kitchen, master, light, ceilings, fireplace, laundry, aesthetics | All 7 scores (0-10) |
| 3 | monthly_cost, total_score, tier, kill_switch_verdict | Verdict rendered |
| 4 | deal_sheet.html | Report generated |

---

## Common Failure Modes

| Issue | Symptom | Recovery |
|-------|---------|----------|
| Browser detection | 403, CAPTCHA | Use stealth browser rotation |
| Missing images | KeyError on paths | Run `extract_images.py` |
| Stale state | Stuck `in_progress` | Reset to `pending` after 10 min |
| Data conflict | Lost updates | Use FileLock for atomic writes |

---

## Environment

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `MARICOPA_ASSESSOR_TOKEN` | County API access | Phase 0 |

| Path | Purpose |
|------|---------|
| `data/` | Property data, state files |
| `data/property_images/` | Downloaded images |
| `data/property_images/metadata/` | Manifests, lookups |
| `reports/` | Generated deal sheets |

---

## Agent Spawn Template

```python
task_description = f"""
You are the {agent_name} agent for the PHX Houses pipeline.

**Target Property:** {address}

**Prerequisites Verified:**
- Phase 1 status: {phase_1_status}
- Images available: {len(images)} photos
- Year built: {year_built}

**Required Outputs:**
{output_list}

**Skills to Load:** {skills}

**State Files to Update:**
- data/enrichment_data.json (LIST - find by full_address)
- data/work_items.json (update phase_status)

**Pre-Work:** Read `.claude/AGENT_BRIEFING.md`
**Post-Work:** Return structured JSON result
"""
```

---

## Emergency Actions

| Issue | Action |
|-------|--------|
| Pipeline stuck | Reset `in_progress` older than 10 min to `pending` |
| Data corruption | Restore from `.bak` file |
| Session confusion | Check `session.session_id` in work_items |
| Agent unresponsive | Kill process, reset status, retry |

---

**Version:** 1.2 | **Updated:** 2025-12-03

*Optimized for sub-5-second orientation. Full docs in `../CLAUDE.md`.*

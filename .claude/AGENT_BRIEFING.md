# Agent Briefing: PHX Houses Pipeline

**Purpose:** 5-second state orientation for spawned agents in multi-phase property analysis workflows.

---

## Quick State Check Commands

```bash
# Current session summary (one-liner)
python -c "import json; s=json.load(open('data/work_items.json')); print(f\"Session: {s['session']['session_id'][:8]}... | Progress: {s['summary']['completed']}/{s['session']['total_items']} | Phase: {s['session']['current_phase']}\")"

# Check specific property status
python -c "import json; props=json.load(open('data/work_items.json'))['properties']; target='4732 W Davis Rd'; print([p for p in props if target.lower() in p['address'].lower()][0])"

# List incomplete properties
python -c "import json; props=json.load(open('data/work_items.json'))['properties']; incomplete=[p['address'] for p in props if not all(s=='completed' for s in p['phase_status'].values())]; print('\n'.join(incomplete[:5]))"

# Session metadata
python -c "import json; s=json.load(open('data/work_items.json'))['session']; print(f\"Started: {s['started_at']}\\nMode: {s['mode']}\\nSkip phases: {s.get('skip_phases', [])}\")"
```

---

## Key File Locations

| File | Purpose | Access | Critical Fields |
|------|---------|--------|-----------------|
| `data/work_items.json` | Pipeline state & progress | RW | `properties[].phase_status`, `session.current_phase` |
| `data/enrichment_data.json` | Property enrichment data | RW | `[address].listing`, `[address].location`, `[address].images` |
| `data/property_images/metadata/extraction_state.json` | Image extraction state | RW | `[address].status`, `[address].sources` |
| `data/property_images/metadata/address_folder_lookup.json` | Address → folder mapping | R | `[address]` → folder hash |
| `data/property_images/metadata/image_manifest.json` | Downloaded images inventory | R | `[folder_hash][]` → image paths |
| `data/phx_homes.csv` | Source listing data | R | `address`, `price`, `beds`, `baths` |
| `data/field_lineage.json` | Data provenance tracking | RW | `[address].[field].source`, `.timestamp` |

---

## Agent Role Summary

### listing-browser (Haiku)
**Phase:** 1
**Purpose:** Extract listing data from Zillow/Redfin using stealth browsers
**Skills:** `listing-extraction`, `property-data`, `state-management`
**Outputs:** Price, beds, baths, sqft, HOA, description, listing URL
**Duration:** ~30-60s per property

### map-analyzer (Haiku)
**Phase:** 1 (parallel with listing-browser)
**Purpose:** Geographic analysis via Google Maps, GreatSchools, crime data
**Skills:** `map-analysis`, `property-data`, `arizona-context-lite`
**Outputs:** School ratings, safety scores, commute times, sun orientation, distances
**Duration:** ~45-90s per property

### image-assessor (Sonnet)
**Phase:** 2
**Purpose:** Visual scoring of interior quality (Section C: 190 pts)
**Skills:** `image-assessment`, `property-data`, `arizona-context-lite`
**Outputs:** Kitchen (40), Master (40), Light (30), Ceilings (30), Fireplace (20), Laundry (20), Aesthetics (10)
**Prerequisites:** Phase 1 complete, images downloaded
**Duration:** ~2-5 min per property (multi-image analysis)

---

## Pre-Work Checklist

Before starting any task:

1. **Load Current State:**
   ```python
   import json
   work_items = json.load(open('data/work_items.json'))
   enrichment = json.load(open('data/enrichment_data.json'))
   ```

2. **Check Property Status:**
   ```python
   target_address = "4732 W Davis Rd, Glendale, AZ 85306"
   prop = next(p for p in work_items['properties'] if p['address'] == target_address)
   current_phase = work_items['session']['current_phase']
   ```

3. **Verify Not Already Complete:**
   ```python
   if prop['phase_status'].get(f'phase_{current_phase}') == 'completed':
       print(f"⚠️  Property already processed for Phase {current_phase}")
       # Skip or ask for confirmation
   ```

4. **Check Prerequisites:**
   ```python
   # Phase 2 requires Phase 1 complete
   if current_phase == 2:
       assert prop['phase_status']['phase_1'] == 'completed', "Phase 1 not complete"
       assert target_address in enrichment, "No enrichment data"
       assert 'images' in enrichment[target_address], "No images downloaded"
   ```

5. **Load Required Context:**
   ```python
   # Image assessment needs year_built for era calibration
   if current_phase == 2:
       year_built = enrichment[target_address].get('year_built')
       pool_exists = enrichment[target_address].get('has_pool', False)
   ```

6. **Update Status to In-Progress:**
   ```python
   prop['phase_status'][f'phase_{current_phase}'] = 'in_progress'
   json.dump(work_items, open('data/work_items.json', 'w'), indent=2)
   ```

---

## Post-Work Protocol

After completing task:

1. **Update Enrichment Data:**
   ```python
   enrichment[target_address]['listing'] = {
       'price': 425000,
       'beds': 4,
       'baths': 2.0,
       # ... other fields
   }
   json.dump(enrichment, open('data/enrichment_data.json', 'w'), indent=2)
   ```

2. **Update Phase Status:**
   ```python
   prop['phase_status'][f'phase_{current_phase}'] = 'completed'
   prop['last_updated'] = datetime.now().isoformat()
   json.dump(work_items, open('data/work_items.json', 'w'), indent=2)
   ```

3. **Update Summary Counters:**
   ```python
   work_items['summary']['completed'] += 1
   work_items['summary']['in_progress'] -= 1
   ```

4. **Return Structured JSON Result:**
   ```python
   result = {
       'status': 'success',
       'address': target_address,
       'phase': current_phase,
       'data': {
           # Extracted/analyzed data
       },
       'warnings': [],  # Any issues encountered
       'next_steps': []  # What needs to happen next
   }
   ```

5. **Log Data Lineage (if applicable):**
   ```python
   # Update field_lineage.json with source attribution
   lineage[target_address]['price'] = {
       'value': 425000,
       'source': 'zillow_listing',
       'timestamp': datetime.now().isoformat(),
       'confidence': 'high'
   }
   ```

---

## Error Recovery Patterns

### File Not Found

```python
# work_items.json missing
if not os.path.exists('data/work_items.json'):
    print("❌ CRITICAL: work_items.json not found")
    print("→ Ask orchestrator to initialize session with /analyze-property")
    sys.exit(1)

# enrichment_data.json missing
if not os.path.exists('data/enrichment_data.json'):
    print("⚠️  Creating new enrichment_data.json")
    json.dump({}, open('data/enrichment_data.json', 'w'))
```

### Images Missing (Phase 2)

```python
# Check image manifest
manifest_path = 'data/property_images/metadata/image_manifest.json'
if not os.path.exists(manifest_path):
    print("❌ Image manifest not found - images not extracted")
    print("→ Run: python scripts/extract_images.py --address '{address}'")
    return {'status': 'error', 'reason': 'images_not_extracted'}

# Check specific property images
manifest = json.load(open(manifest_path))
folder_hash = get_folder_hash(target_address)
if folder_hash not in manifest or len(manifest[folder_hash]) == 0:
    print(f"❌ No images found for {target_address}")
    print("→ Attempting extraction...")
    # Trigger extraction or mark for retry
    return {'status': 'retry', 'reason': 'missing_images'}
```

### Previous Phase Failed

```python
# Check phase dependencies
current_phase = 2
prev_phase_status = prop['phase_status'].get('phase_1')

if prev_phase_status != 'completed':
    print(f"❌ Cannot start Phase {current_phase} - Phase 1 status: {prev_phase_status}")

    if prev_phase_status == 'failed':
        print("→ Review Phase 1 errors and retry")
    elif prev_phase_status == 'in_progress':
        print("→ Wait for Phase 1 to complete")
    elif prev_phase_status is None:
        print("→ Phase 1 not started - trigger Phase 1 agents first")

    return {'status': 'blocked', 'reason': f'phase_1_{prev_phase_status}'}
```

### Partial Data (Incomplete Phase 1)

```python
# Validate Phase 1 completeness before Phase 2
required_fields = ['listing.price', 'listing.beds', 'location.school_rating']

missing = []
for field in required_fields:
    keys = field.split('.')
    value = enrichment[target_address]
    for key in keys:
        value = value.get(key, {})
    if not value:
        missing.append(field)

if missing:
    print(f"⚠️  Incomplete Phase 1 data: {missing}")
    print("→ Rerun Phase 1 or mark fields as N/A")
    # Decide: proceed with warnings or fail
```

---

## Phase Dependencies Chart

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE DEPENDENCY FLOW                    │
└─────────────────────────────────────────────────────────────┘

Phase 0: County Data (Optional - can run anytime)
┌───────────────────┐
│ County Assessor   │  Outputs: lot_sqft, year_built, garage, pool
│ (API)             │  Independent - no dependencies
└───────────────────┘
         │
         ↓ (enriches)

Phase 1: Listing + Map (Parallel execution)
┌───────────────────┐     ┌───────────────────┐
│ listing-browser   │     │ map-analyzer      │
│ (Haiku)           │     │ (Haiku)           │
│                   │     │                   │
│ Zillow/Redfin     │     │ Google Maps       │
│ Price, beds, HOA  │     │ Schools, safety   │
└───────────────────┘     └───────────────────┘
         │                         │
         └────────┬────────────────┘
                  ↓
            [Phase 1 Complete]
                  │
                  ↓ (requires)

Phase 2: Image Assessment
┌───────────────────┐
│ image-assessor    │  Prerequisites:
│ (Sonnet)          │  - Phase 1 complete
│                   │  - Images downloaded
│ Interior scoring  │  - year_built known (era calibration)
└───────────────────┘
         │
         ↓

Phase 3: Cost Estimation + Synthesis
┌───────────────────┐
│ Cost calculator   │  Prerequisites:
│ Scoring engine    │  - All phases complete
│ Kill-switch check │  - All required fields populated
└───────────────────┘
         │
         ↓

Phase 4: Report Generation
┌───────────────────┐
│ Deal sheets       │  Prerequisites:
│ Visualizations    │  - Scoring complete
│ Rankings          │  - Kill-switch verdict rendered
└───────────────────┘
```

**Key Rules:**
- Phase 0 is **optional** and can run independently at any time
- Phase 1 agents run **in parallel** (listing-browser + map-analyzer)
- Phase 2 **blocks** until Phase 1 is `completed`
- Phase 3 **blocks** until Phase 2 is `completed`
- Phase 4 runs after all analysis phases complete

**Skip Logic:**
```python
# Check if phases can be skipped
session = work_items['session']
skip_phases = session.get('skip_phases', [])

if current_phase in skip_phases:
    print(f"⏭️  Skipping Phase {current_phase} per session config")
    prop['phase_status'][f'phase_{current_phase}'] = 'skipped'
    # Move to next phase
```

---

## Common Failure Modes

### 1. Browser Detection (Phase 1 - Listing)
**Symptom:** 403 Forbidden, CAPTCHA challenges
**Cause:** PerimeterX/Cloudflare bot detection
**Recovery:**
```python
# Use stealth browser rotation
from src.phx_home_analysis.services.infrastructure.browser_pool import BrowserPool
pool = BrowserPool(stealth_mode=True)
# Retry with different user-agent/fingerprint
```

### 2. Missing Images (Phase 2)
**Symptom:** `KeyError` on image paths, empty manifest
**Cause:** Phase 1 didn't trigger image extraction
**Recovery:**
```bash
# Manual extraction
python scripts/extract_images.py --address "4732 W Davis Rd"
# Then retry Phase 2
```

### 3. Stale State (All Phases)
**Symptom:** Status shows `in_progress` but no agent running
**Cause:** Crashed agent didn't update status
**Recovery:**
```python
# Reset stuck properties
for prop in work_items['properties']:
    for phase, status in prop['phase_status'].items():
        if status == 'in_progress':
            age = datetime.now() - datetime.fromisoformat(prop['last_updated'])
            if age.seconds > 600:  # 10 min timeout
                print(f"⚠️  Resetting stuck {phase} for {prop['address']}")
                prop['phase_status'][phase] = 'pending'
```

### 4. Data Conflict (Write Race)
**Symptom:** Lost updates, overwritten data
**Cause:** Multiple agents writing simultaneously
**Recovery:**
```python
# Always read-modify-write atomically
import json
import os
import time
from filelock import FileLock

lock_path = 'data/enrichment_data.json.lock'
with FileLock(lock_path, timeout=10):
    data = json.load(open('data/enrichment_data.json'))
    data[address]['new_field'] = value
    json.dump(data, open('data/enrichment_data.json', 'w'), indent=2)
```

---

## Quick Reference: Phase Exit Criteria

| Phase | Required Outputs | Quality Gates |
|-------|------------------|---------------|
| 0 | lot_sqft, year_built, garage_spaces | Data from Assessor API |
| 1 | price, beds, baths, HOA, school_rating, safety_score | All required fields populated |
| 2 | kitchen_score, master_score, light_score, ceilings_score | All 7 interior scores (0-10) |
| 3 | monthly_cost, total_score, tier, kill_switch_verdict | Scoring complete, verdict rendered |
| 4 | deal_sheet.html, property in rankings | Report generated |

---

## Environmental Context

```python
# Project root detection
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Key paths
DATA_DIR = f"{PROJECT_ROOT}/data"
IMAGES_DIR = f"{DATA_DIR}/property_images"
METADATA_DIR = f"{IMAGES_DIR}/metadata"
REPORTS_DIR = f"{PROJECT_ROOT}/reports"

# Required environment variables
MARICOPA_ASSESSOR_TOKEN = os.getenv('MARICOPA_ASSESSOR_TOKEN')  # Phase 0
```

---

## Agent Spawn Template

When spawning a new agent task:

```python
# Example: Spawn image-assessor for specific property
task_description = f"""
You are the image-assessor agent for the PHX Houses pipeline.

**Your Task:** Analyze interior images for property and score Section C (190 pts).

**Target Property:** {address}

**Prerequisites Verified:**
- Phase 1 status: {phase_1_status}
- Images available: {len(images)} photos
- Year built: {year_built} (era: {era})

**Required Outputs:**
- Kitchen score (0-10)
- Master bedroom score (0-10)
- Natural light score (0-10)
- Ceiling quality score (0-10)
- Fireplace score (0-10)
- Laundry setup score (0-10)
- Overall aesthetics score (0-10)
- Detailed reasoning for each score

**Skills to Load:** image-assessment, property-data, arizona-context-lite

**State Files to Update:**
- data/enrichment_data.json (add scores to [address].images.assessment)
- data/work_items.json (update phase_status.phase_2 to 'completed')

**Pre-Work:** Read `.claude/AGENT_BRIEFING.md` for orientation.

**Post-Work:** Return structured JSON result per protocol.
"""
```

---

## Logging & Debugging

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check recent activity
import json
work_items = json.load(open('data/work_items.json'))
recent = sorted(work_items['properties'],
                key=lambda p: p.get('last_updated', ''),
                reverse=True)[:5]
for prop in recent:
    print(f"{prop['address']}: {prop['phase_status']}")

# Trace data lineage
lineage = json.load(open('data/field_lineage.json'))
field_history = lineage.get(address, {}).get('price', {})
print(f"Price source: {field_history.get('source')} at {field_history.get('timestamp')}")
```

---

## Emergency Contacts

| Issue | Action |
|-------|--------|
| Pipeline stuck | Check `work_items.json` for `in_progress` older than 10 min, reset to `pending` |
| Data corruption | Restore from `data/enrichment_data.json.bak` (auto-created on writes) |
| Session confusion | Check `session.session_id` in `work_items.json` - ensure single active session |
| Agent unresponsive | Kill process, check logs, reset phase status, retry |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
**Maintainer:** Claude Code Orchestrator

*This briefing is optimized for sub-5-second orientation. Refer to full documentation in `../CLAUDE.md` for detailed specifications.*

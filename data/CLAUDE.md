---
last_updated: 2025-12-02
updated_by: Claude Code
staleness_hours: 12
---

# data/

## Purpose

Central repository for property data, pipeline state, and extraction results. This directory contains the critical state files that drive the multi-phase property analysis pipeline, including enriched property data, workflow tracking, and extracted images.

**WARNING: This is a CRITICAL directory. Files here are checked frequently by agents and orchestrators. Staleness threshold is 12 hours.**

## Critical State Files

| File | Purpose | Schema Type | Access Pattern | Staleness |
|------|---------|-------------|----------------|-----------|
| `enrichment_data.json` | Master property data store (LIST of dicts) | PropertyEnrichment v2.0.0 | Read/write by all phases | 12h |
| `work_items.json` | Pipeline progress tracking | work_items_v1 | Read/update by orchestrator | 12h |
| `phx_homes.csv` | Source listing data | CSV | Read-only reference | 168h |
| `field_lineage.json` | Data provenance tracking | field_lineage_v1 | Append-only by phases | 24h |
| `quality_baseline.json` | Data quality metrics | quality_metrics_v1 | Updated by validation | 24h |

### enrichment_data.json Structure

**CRITICAL: This is a LIST, not a dict. Always use atomic write patterns (write to temp, rename).**

```json
[
  {
    "_schema_metadata": {
      "version": "2.0.0",
      "created_at": "ISO8601",
      "migrated_at": null,
      "migrated_from": null
    },
    "full_address": "string (PRIMARY KEY)",
    "lot_sqft": "int (Phase 0)",
    "year_built": "int (Phase 0)",
    "garage_spaces": "int (Phase 0)",
    "list_price": "int (Phase 1 listing)",
    "hoa_fee": "int (Phase 1 listing)",
    "school_rating": "float (Phase 1 map)",
    "orientation": "string (Phase 1 map)",
    "safety_neighborhood_score": "int (Phase 1 map)",
    "interior_total": "int (Phase 2)",
    "exterior_total": "int (Phase 2)",
    "total_score": "int (Phase 3)",
    "tier": "string (Phase 3)",
    "kill_switch_passed": "bool",
    "kill_switch_failures": "list[string]"
  }
]
```

### work_items.json Structure

```json
{
  "$schema": "work_items_v1",
  "session": {
    "session_id": "string",
    "started_at": "ISO8601",
    "mode": "batch|single",
    "total_items": "int",
    "current_index": "int"
  },
  "work_items": [
    {
      "id": "string (8-char hash)",
      "address": "string",
      "status": "pending|in_progress|complete|failed|blocked",
      "phases": {
        "phase0_county": {"status": "...", "completed": "ISO8601"},
        "phase1_listing": {"status": "...", "completed": "ISO8601"},
        "phase1_map": {"status": "...", "completed": "ISO8601"},
        "phase2_images": {"status": "...", "completed": "ISO8601"},
        "phase3_synthesis": {"status": "...", "completed": "ISO8601"},
        "phase4_report": {"status": "...", "completed": "ISO8601"}
      }
    }
  ]
}
```

## Supporting Files

| File | Purpose | Updated By |
|------|---------|------------|
| `phx_homes_ranked.csv` | Scored property export | Phase 3 synthesis |
| `enrichment_template.json` | Schema template for new properties | Manual/setup |
| `geocoded_homes.json` | Geocoding cache | Phase 1 map |
| `orientation_estimates.json` | Orientation cache | Phase 1 map |
| `extraction_results.json` | Image extraction results | Phase 1 listing |
| `extraction_report_YYYYMMDD.json` | Daily extraction reports | Phase 1 listing |
| `research_tasks.json` | Manual research tracking | Human analysts |
| `image_assessment_*.json` | Phase 2 assessment cache | Phase 2 images |

## Subdirectories

### property_images/

Extracted listing images and metadata for visual assessment.

```
property_images/
├── raw/              # Original downloaded images by property hash
├── processed/        # Categorized images by property hash
└── metadata/         # Image pipeline state and tracking
    ├── extraction_state.json       # Image extraction state
    ├── address_folder_lookup.json  # Address → hash mapping
    ├── image_manifest.json         # Image inventory
    ├── url_tracker.json            # Image URL deduplication
    ├── hash_index.json             # Hash → address lookup
    ├── pipeline_runs.json          # Extraction run history
    └── run_history/                # Per-run logs
```

**Key Access Pattern**: Use `address_folder_lookup.json` to find property hash, then access `processed/{hash}/` for categorized images.

### archive/

Historical data snapshots and deprecated files. Not accessed by pipeline.

### raw_exports/

Manual Zillow/Redfin HTML exports (legacy). Superseded by stealth extraction scripts.

## Data Schemas

### PropertyEnrichment v2.0.0

Defined in: `src/phx_home_analysis/validation/schemas.py`

**Key Fields by Phase:**
- **Phase 0 (County)**: lot_sqft, year_built, garage_spaces, sewer_type, tax_annual
- **Phase 1 Listing**: list_price, hoa_fee, beds, baths
- **Phase 1 Map**: school_rating, orientation, safety_neighborhood_score, distance_to_grocery_miles
- **Phase 2 Images**: interior_total, exterior_total, kitchen_score, roof_condition
- **Phase 3 Synthesis**: total_score, tier, kill_switch_passed

### WorkItems v1

Defined in: `scripts/lib/state_management.py`

**Work Item States**: pending → in_progress → complete|failed|blocked

**Phase States**: pending → in_progress → complete|failed

## Access Patterns

### Reading Property Data
```python
# CORRECT: Load as list
with open("data/enrichment_data.json") as f:
    properties = json.load(f)  # Returns list
prop = next(p for p in properties if p["full_address"] == addr)

# WRONG: Assuming dict
with open("data/enrichment_data.json") as f:
    properties = json.load(f)  # This IS a list, not dict
prop = properties[addr]  # TypeError!
```

### Writing Property Data (Atomic)
```python
# CORRECT: Atomic write pattern
import json, os, tempfile

with open("data/enrichment_data.json") as f:
    properties = json.load(f)

# Modify properties list
properties[idx]["new_field"] = value

# Atomic write
fd, temp_path = tempfile.mkstemp(dir="data/", prefix="enrichment_", suffix=".tmp")
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(properties, f, indent=2)
    os.replace(temp_path, "data/enrichment_data.json")  # Atomic on POSIX
except:
    os.unlink(temp_path)
    raise
```

### Checking Phase Prerequisites
```bash
# Validate before spawning Phase 2
python scripts/validate_phase_prerequisites.py \
  --address "123 Main St" \
  --phase phase2_images \
  --json
```

## Pending Tasks

- [ ] Implement data retention policy for old extraction reports
- [ ] Add automated backup for enrichment_data.json (hourly snapshots)
- [ ] Create data reconciliation script for work_items ↔ enrichment_data sync
- [ ] Document image categorization taxonomy in property_images/metadata/

## Key Learnings

### Data Integrity

1. **enrichment_data.json is a LIST**: Always iterate/filter, never index by address. Use atomic writes (temp file + rename) to prevent corruption.

2. **work_items.json Race Conditions**: Only one orchestrator should modify work_items.json at a time. Agents should read-only unless explicitly updating their phase status.

3. **Phase Dependencies**: Phase 2 (images) REQUIRES Phase 1 (listing) completion. Always validate with `validate_phase_prerequisites.py` before spawning image assessor.

4. **Image Folder Lookup**: Use `property_images/metadata/address_folder_lookup.json` to map address → hash. Never hardcode folder names.

5. **Staleness Matters**: enrichment_data.json and work_items.json have 12-hour staleness thresholds. Check timestamps before spawning agents.

### Common Errors

1. **TypeError: list indices must be integers**: Attempted dict access on enrichment_data.json. Solution: Use list comprehension/filter.

2. **FileNotFoundError: image folder not found**: Forgot to check address_folder_lookup.json. Always validate image folder exists before Phase 2 spawn.

3. **JSONDecodeError on enrichment_data.json**: Concurrent writes without atomic pattern. Always use tempfile + os.replace().

4. **KeyError on work_items**: Property not in work_items.json but exists in enrichment_data.json. Run reconciliation script.

## Dependencies

**Consumed By:**
- `scripts/phx_home_analyzer.py` - Reads enrichment_data.json for scoring
- `scripts/extract_county_data.py` - Updates enrichment_data.json Phase 0 fields
- `scripts/extract_images.py` - Updates extraction_state.json, writes to property_images/
- `scripts/validate_phase_prerequisites.py` - Validates work_items.json and image folders
- `.claude/agents/listing-browser.md` - Updates Phase 1 fields in enrichment_data.json
- `.claude/agents/map-analyzer.md` - Updates Phase 1 map fields
- `.claude/agents/image-assessor.md` - Updates Phase 2 fields
- `.claude/commands/analyze-property.md` - Orchestrates via work_items.json

**References:**
- Schema definitions: `src/phx_home_analysis/validation/schemas.py:1-200`
- State management: `scripts/lib/state_management.py:1-150`
- Property data access: `.claude/skills/property-data/SKILL.md`
- Validation script: `scripts/validate_phase_prerequisites.py:1-300`

## Quick Commands

```bash
# View current pipeline status
jq '.work_items[] | select(.status != "complete")' data/work_items.json

# Find property by address in enrichment_data.json
jq '.[] | select(.full_address == "123 Main St")' data/enrichment_data.json

# Check Phase 2 readiness
python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images

# List properties with images
ls data/property_images/processed/

# Reconcile data inconsistencies
python scripts/validate_phase_prerequisites.py --reconcile --all --repair
```

---

**Last Manual Review**: 2025-12-02
**Staleness Threshold**: 12 hours (CRITICAL)
**Next Review Due**: Check timestamps on enrichment_data.json and work_items.json before each agent spawn

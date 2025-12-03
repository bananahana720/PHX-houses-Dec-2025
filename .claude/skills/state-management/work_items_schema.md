# Work Items Schema (v1)

Multi-phase property analysis state tracking with phase-level granularity.

## Schema Overview

`work_items.json` tracks the complete state of property analysis pipelines, enabling:
- **Crash recovery**: Resume from last checkpoint
- **Phase tracking**: Granular status per analysis phase
- **Merge safety**: Property-level locks prevent conflicts
- **Progress monitoring**: Real-time summary statistics
- **Audit trail**: Commit SHA tracking per phase

## Full Schema

```json
{
  "$schema": "work_items_v1",
  "session": {
    "session_id": "session_20251202_143022",
    "started_at": "2025-12-02T14:30:22Z",
    "mode": "batch",
    "total_items": 25,
    "current_index": 5,
    "runtime_seconds": 3421,
    "last_checkpoint": "2025-12-02T15:27:03Z"
  },
  "blocked_sources": {
    "zillow": {
      "blocked": false,
      "last_check": "2025-12-02T15:00:00Z",
      "error": null
    },
    "redfin": {
      "blocked": true,
      "last_check": "2025-12-02T14:45:00Z",
      "error": "403 PerimeterX challenge detected"
    },
    "realtor": {
      "blocked": false,
      "last_check": "2025-12-02T15:00:00Z",
      "error": null
    }
  },
  "work_items": [
    {
      "id": "ef7cd95f",
      "address": "4732 W Davis Rd, Glendale, AZ 85306",
      "status": "completed",
      "phases": {
        "phase0_county": {
          "status": "complete",
          "started": "2025-12-02T14:30:25Z",
          "completed": "2025-12-02T14:30:47Z",
          "commit_sha": "abc123def456",
          "data_fields": ["lot_sqft", "year_built", "garage_spaces", "has_pool"]
        },
        "phase05_cost": {
          "status": "complete",
          "started": "2025-12-02T14:30:48Z",
          "completed": "2025-12-02T14:31:15Z",
          "commit_sha": "def456ghi789",
          "data_fields": ["monthly_cost", "cost_breakdown"]
        },
        "phase1_listing": {
          "status": "complete",
          "started": "2025-12-02T14:31:20Z",
          "completed": "2025-12-02T14:32:45Z",
          "commit_sha": "ghi789jkl012",
          "data_fields": ["price", "beds", "baths", "listing_url", "images_discovered"],
          "sources_checked": ["zillow", "redfin"]
        },
        "phase1_map": {
          "status": "complete",
          "started": "2025-12-02T14:32:50Z",
          "completed": "2025-12-02T14:35:30Z",
          "commit_sha": "jkl012mno345",
          "data_fields": ["school_rating", "crime_score", "supermarket_distance"]
        },
        "phase2_images": {
          "status": "complete",
          "started": "2025-12-02T14:35:35Z",
          "completed": "2025-12-02T14:42:10Z",
          "commit_sha": "mno345pqr678",
          "data_fields": ["image_scores", "interior_quality"],
          "images_processed": 24,
          "images_deduped": 18
        },
        "phase3_synthesis": {
          "status": "complete",
          "started": "2025-12-02T14:42:15Z",
          "completed": "2025-12-02T14:43:00Z",
          "commit_sha": "pqr678stu901",
          "data_fields": ["total_score", "tier", "kill_switch_result"]
        },
        "phase4_report": {
          "status": "complete",
          "started": "2025-12-02T14:43:05Z",
          "completed": "2025-12-02T14:43:30Z",
          "commit_sha": "stu901vwx234",
          "output_path": "reports/deal_sheets/03_4732_w_davis_rd.html"
        }
      },
      "tier": "CONTENDER",
      "total_score": 412,
      "kill_switch": {
        "passed": true,
        "failures": [],
        "severity": 0.0
      },
      "retry_count": 0,
      "error_log": [],
      "completed_at": "2025-12-02T14:43:30Z",
      "locked_by": null,
      "locked_at": null
    }
  ],
  "summary": {
    "completed": 5,
    "in_progress": 1,
    "pending": 19,
    "failed": 0,
    "skipped": 0,
    "tiers": {
      "UNICORN": 1,
      "CONTENDER": 3,
      "PASS": 1,
      "FAILED": 0
    }
  },
  "last_updated": "2025-12-02T15:27:03Z"
}
```

## Field Definitions

### Session Object

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier: `session_YYYYMMDD_HHMMSS` |
| `started_at` | ISO-8601 | Session start timestamp |
| `mode` | enum | `batch` \| `single` \| `test` |
| `total_items` | int | Total properties in batch |
| `current_index` | int | Current processing index (0-based) |
| `runtime_seconds` | int | Total runtime since session start |
| `last_checkpoint` | ISO-8601 | Last state file write timestamp |

### Blocked Sources Object

Tracks listing source availability (anti-bot detection).

| Field | Type | Description |
|-------|------|-------------|
| `blocked` | boolean | Is source currently blocked? |
| `last_check` | ISO-8601 | Last check timestamp |
| `error` | string \| null | Last error message if blocked |

**Sources:** `zillow`, `redfin`, `realtor`

### Work Item Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Property hash (8-char MD5 of address) |
| `address` | string | Full property address |
| `status` | enum | Work item status (see below) |
| `phases` | object | Phase-level status tracking (see below) |
| `tier` | enum | `UNICORN` \| `CONTENDER` \| `PASS` \| null |
| `total_score` | int \| null | Final score (0-600) |
| `kill_switch` | object | Kill-switch result (see below) |
| `retry_count` | int | Number of retry attempts |
| `error_log` | array | Error history `[{timestamp, phase, error}]` |
| `completed_at` | ISO-8601 \| null | Completion timestamp |
| `locked_by` | string \| null | Agent/process holding lock |
| `locked_at` | ISO-8601 \| null | Lock acquisition timestamp |

### Work Item Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not yet started |
| `in_progress` | Currently processing |
| `completed` | All phases complete |
| `failed` | Unrecoverable error |
| `skipped` | Intentionally skipped (kill-switch fail, etc.) |

### Phase Object Structure

Each phase tracks:

```json
{
  "status": "complete",
  "started": "ISO-8601",
  "completed": "ISO-8601",
  "commit_sha": "git_commit_sha",
  "data_fields": ["field1", "field2"],
  "error": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | enum | `pending` \| `in_progress` \| `complete` \| `failed` \| `skipped` |
| `started` | ISO-8601 \| null | Phase start timestamp |
| `completed` | ISO-8601 \| null | Phase completion timestamp |
| `commit_sha` | string \| null | Git commit SHA after phase completion |
| `data_fields` | array | Fields written to enrichment_data.json |
| `error` | string \| null | Error message if failed |

**Phase-specific fields:**

- **phase1_listing**: `sources_checked` (array of source names)
- **phase2_images**: `images_processed` (int), `images_deduped` (int)
- **phase4_report**: `output_path` (string)

### Phase Definitions

| Phase | Name | Description |
|-------|------|-------------|
| `phase0_county` | County Data | Maricopa County Assessor API extraction |
| `phase05_cost` | Cost Estimation | Monthly housing cost calculation |
| `phase1_listing` | Listing Data | Zillow/Redfin/Realtor extraction |
| `phase1_map` | Map Analysis | Schools, crime, distances, orientation |
| `phase2_images` | Image Assessment | Visual scoring (Section C: 190 pts) |
| `phase3_synthesis` | Scoring | Kill-switch + scoring + tier assignment |
| `phase4_report` | Report Generation | Deal sheet HTML generation |

### Kill-Switch Object

```json
{
  "passed": true,
  "failures": [],
  "severity": 0.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `passed` | boolean | Did property pass kill-switch? |
| `failures` | array | List of failed criteria `["no_hoa", "sewer_type"]` |
| `severity` | float | Soft criteria severity score (0.0-6.0) |

### Summary Object

Real-time aggregation across all work items.

| Field | Type | Description |
|-------|------|-------------|
| `completed` | int | Count of completed work items |
| `in_progress` | int | Count of in-progress work items |
| `pending` | int | Count of pending work items |
| `failed` | int | Count of failed work items |
| `skipped` | int | Count of skipped work items |
| `tiers` | object | Count by tier: `{UNICORN, CONTENDER, PASS, FAILED}` |

## Merge Conflict Prevention

### Property-Level Locks

**Before processing a property:**
```python
work_item["locked_by"] = "agent_listing_browser"
work_item["locked_at"] = datetime.utcnow().isoformat() + "Z"
save_work_items()
```

**After completing a phase:**
```python
# Update phase status
work_item["phases"]["phase1_listing"]["status"] = "complete"
work_item["phases"]["phase1_listing"]["completed"] = timestamp
work_item["phases"]["phase1_listing"]["commit_sha"] = get_git_commit_sha()

# Release lock if all phases complete
if all_phases_complete(work_item):
    work_item["locked_by"] = None
    work_item["locked_at"] = None
    work_item["status"] = "completed"
    work_item["completed_at"] = timestamp

save_work_items()
```

### Atomic Updates Pattern

```python
from src.phx_home_analysis.services.state_management import WorkItemsManager

with WorkItemsManager() as wim:
    work_item = wim.get_work_item(property_hash)

    # Lock check
    if work_item["locked_by"] and work_item["locked_by"] != agent_name:
        raise WorkItemLockedError(f"Property locked by {work_item['locked_by']}")

    # Acquire lock
    wim.lock_work_item(property_hash, agent_name)

    # Update phase
    wim.update_phase(
        property_hash,
        phase="phase1_listing",
        status="complete",
        data_fields=["price", "beds", "baths"],
        commit_sha="abc123"
    )

    # Auto-saves on context exit
```

## Git Commit Integration

**Commit SHA Tracking:**
- Each phase completion records the git commit SHA
- Enables audit trail: "Which code version produced this data?"
- Supports rollback: "Revert to state before commit X"

**Recommended workflow:**
```bash
# After phase completion
git add data/enrichment_data.json data/work_items.json
git commit -m "phase1_listing: 4732 W Davis Rd completed"

# Record commit SHA in work_items.json
work_item["phases"]["phase1_listing"]["commit_sha"] = $(git rev-parse HEAD)
```

## Crash Recovery Strategy

**On startup:**
1. Load work_items.json
2. Check for `in_progress` work items
3. Check lock timestamps (if > 30 min old, consider stale)
4. Reset stale locks to `pending`
5. Resume from first `pending` item

**Example recovery logic:**
```python
def recover_stale_locks(work_items, timeout_minutes=30):
    now = datetime.utcnow()
    for item in work_items["work_items"]:
        if item["locked_by"] and item["locked_at"]:
            locked_at = datetime.fromisoformat(item["locked_at"].replace("Z", "+00:00"))
            if (now - locked_at).total_seconds() > timeout_minutes * 60:
                logger.warning(f"Stale lock detected: {item['address']} locked by {item['locked_by']}")
                item["locked_by"] = None
                item["locked_at"] = None
                item["status"] = "pending"

                # Reset incomplete phases
                for phase, data in item["phases"].items():
                    if data["status"] == "in_progress":
                        data["status"] = "pending"
```

## State File Location

**Path:** `data/work_items.json`

**Backup strategy:**
- Automatic backup on migration: `data/work_items.json.pre_migration.bak`
- Periodic snapshots: `data/work_items.{timestamp}.snapshot.json`
- Git tracking: Commit after each batch completion

## Usage Examples

### Initialize New Session

```python
from src.phx_home_analysis.services.state_management import WorkItemsManager

wim = WorkItemsManager()
wim.init_session(
    mode="batch",
    properties=[
        {"hash": "ef7cd95f", "address": "4732 W Davis Rd, Glendale, AZ 85306"},
        # ... more properties
    ]
)
```

### Update Phase Status

```python
wim.update_phase(
    property_hash="ef7cd95f",
    phase="phase1_listing",
    status="complete",
    data_fields=["price", "beds", "baths", "listing_url"],
    sources_checked=["zillow", "redfin"],
    commit_sha="abc123def456"
)
```

### Check Progress

```python
summary = wim.get_summary()
print(f"Completed: {summary['completed']}/{summary['total']}")
print(f"Unicorns: {summary['tiers']['UNICORN']}")
```

### Query Work Items

```python
# Get next pending item
next_item = wim.get_next_pending()

# Get items by status
in_progress = wim.get_by_status("in_progress")

# Get items by tier
unicorns = wim.get_by_tier("UNICORN")
```

## Migration from extraction_state.json

Use migration script: `scripts/migrate_to_work_items.py`

```bash
# Dry run (validation only)
python scripts/migrate_to_work_items.py --dry-run

# Execute migration (creates backup by default)
python scripts/migrate_to_work_items.py

# Execute without backup
python scripts/migrate_to_work_items.py --no-backup
```

**Mapping:**
- `extraction_state.json` → phase2_images status (optional, may not exist)
- `enrichment_data.json` → completed phases + data fields
- `phx_homes.csv` → full property list

**Phase Status Inference:**
- Checks for required fields in enrichment data
- If fields exist and non-null → `complete`
- Otherwise → `pending`
- Overall status: All phases complete → `completed`, Any in progress → `in_progress`, Mixed → `in_progress`

**Phase Field Requirements:**
- `phase0_county`: lot_sqft, year_built
- `phase05_cost`: monthly_cost
- `phase1_listing`: price, beds, baths
- `phase1_map`: school_rating
- `phase2_images`: image_scores
- `phase3_synthesis`: total_score, tier
- `phase4_report`: Inferred from deal sheet existence

## Validation Rules

1. **Session ID uniqueness**: No duplicate session_ids
2. **Property hash uniqueness**: No duplicate work item IDs
3. **Status consistency**: `completed` items must have all phases complete
4. **Lock consistency**: `locked_by` requires `locked_at` and vice versa
5. **Phase timestamps**: `completed` must be >= `started`
6. **Tier validation**: `tier` only set if `status == "completed"`
7. **Summary accuracy**: Summary counts must match work item statuses

## Future Enhancements

- **Phase dependencies**: Enforce phase ordering (can't start phase2 before phase1)
- **Parallel execution**: Multi-agent concurrent processing with distributed locks
- **Retry policies**: Exponential backoff per phase
- **Data lineage**: Link to quality metadata in field_lineage.json
- **Time estimates**: Predict completion time based on historical data
- **Agent metrics**: Track per-agent success rates and performance

## See Also

- `.claude/skills/state-management/SKILL.md` - State management skill
- `scripts/migrate_to_work_items.py` - Migration script
- `src/phx_home_analysis/services/state_management/` - Implementation

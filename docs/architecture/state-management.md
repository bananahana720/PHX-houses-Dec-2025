# State Management Protocol

Comprehensive guide to work_items.json schema, locking, and atomic updates.

## work_items.json Schema

Complete schema definition for the pipeline state file.

```json
{
  "schema_version": "1.0.0",
  "session": {
    "session_id": "session_20251202_123456",
    "start_time": "2025-12-02T12:34:56",
    "mode": "batch|single|test",
    "total_items": 25,
    "current_index": 5
  },
  "work_items": [
    {
      "index": 0,
      "address": "123 Main St, Phoenix, AZ 85001",
      "hash": "abc123de",
      "status": "pending|in_progress|complete|failed",
      "locked_by": null,
      "locked_at": null,
      "phase_status": {
        "phase0_county": "complete",
        "phase05_cost": "complete",
        "phase1_listing": "in_progress",
        "phase1_map": "pending",
        "phase2a_exterior": "pending",
        "phase2b_interior": "pending",
        "phase3_synthesis": "pending",
        "phase4_report": "pending"
      },
      "retry_count": 0,
      "last_updated": "2025-12-02T12:45:00",
      "commit_sha": null,
      "errors": []
    }
  ],
  "summary": {
    "pending": 15,
    "in_progress": 1,
    "complete": 8,
    "failed": 1
  }
}
```

## Property-Level Locking

Before modifying any property data, acquire an exclusive lock:

```python
from datetime import datetime
import json
from pathlib import Path

def acquire_work_item_lock(work_items: dict, index: int, session_id: str) -> bool:
    """Acquire lock on work item for exclusive access.

    Returns True if lock acquired, False if already locked by another session.
    """
    item = work_items['work_items'][index]

    # Check if already locked by different session
    if item.get('locked_by') and item['locked_by'] != session_id:
        lock_age = datetime.now() - datetime.fromisoformat(item['locked_at'])
        if lock_age.total_seconds() < 3600:  # 1 hour stale lock timeout
            return False

    # Acquire lock
    item['locked_by'] = session_id
    item['locked_at'] = datetime.now().isoformat()
    return True

def release_work_item_lock(work_items: dict, index: int):
    """Release lock on work item."""
    item = work_items['work_items'][index]
    item['locked_by'] = None
    item['locked_at'] = None

# Usage in orchestrator
work_items = load_work_items()
if not acquire_work_item_lock(work_items, idx, session_id):
    log_warning(f"Property {address} locked by another session - skipping")
    continue

try:
    # ... do work ...
finally:
    release_work_item_lock(work_items, idx)
    save_work_items(work_items)
```

## Atomic Updates

Use temp file + rename pattern to prevent corruption:

```python
def save_work_items_atomic(work_items: dict, path: Path):
    """Atomically save work_items.json to prevent corruption."""
    import tempfile
    import shutil

    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=path.parent,
        prefix='work_items_',
        suffix='.tmp',
        delete=False
    ) as tmp:
        json.dump(work_items, tmp, indent=2)
        tmp_path = Path(tmp.name)

    # Atomic rename
    shutil.move(str(tmp_path), str(path))
```

## Session Blocking Cache

Track source blocking status (resets each run):

```python
session_blocking = {"zillow": None, "redfin": None, "google_maps": None}
# None=untested, True=blocked, False=working
```

## Merge Conflict Prevention

### Serialized Updates

**Orchestrator Pattern:**
1. Collect all phase updates in memory
2. Single atomic write per property completion
3. Use temp file + rename pattern

```python
# BAD: Multiple writes per property
for phase in phases:
    execute_phase(phase)
    save_work_items(work_items)  # ❌ N writes

# GOOD: Single write per property
phase_results = []
for phase in phases:
    result = execute_phase(phase)
    phase_results.append(result)

# Apply all updates at once
for result in phase_results:
    update_phase_status(work_items, result)

save_work_items_atomic(work_items, work_items_path)  # ✓ 1 write
```

## Git Commit Protocol

### Commit After Each Property

After all phases complete for a property, commit changes to preserve progress and enable recovery.

#### Commit Points Table

| When | Files to Stage | Rationale |
|------|----------------|-----------|
| After Phase 0+0.5 | enrichment_data.json, work_items.json | County + cost data acquired |
| After Phase 1 | enrichment_data.json, work_items.json, images/*, metadata/*.json | Listing + map data complete |
| After Phase 2 | enrichment_data.json, work_items.json | Visual scores assigned |
| After Phase 3+4 | enrichment_data.json, work_items.json, ranked.csv, deal_sheets/* | Final scoring + report |
| Property complete | All of the above | Full property checkpoint |

#### Commit Message Template

```bash
# Stage files
git add data/enrichment_data.json data/work_items.json

# If Phase 1 completed (images)
if [ -d "data/property_images/processed/{hash}" ]; then
  git add "data/property_images/processed/{hash}/*"
  git add data/property_images/metadata/*.json
fi

# If Phase 4 completed (report)
if ls reports/deal_sheets/*{hash}* 1> /dev/null 2>&1; then
  git add "reports/deal_sheets/*{hash}*"
fi

# Commit with structured message
git commit -m "$(cat <<'EOF'
feat(property): Complete {address_short} - {tier} ({score}/605)

Property: {full_address}
Hash: {hash}
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✓ | Synthesis ✓ | Report ✓
Kill-switch: {PASS|WARNING|FAIL}
Tier: {tier}
Score: {score}/605
Monthly Cost: ${monthly_cost}

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Update work_items.json with commit SHA
python -c "
import json
from pathlib import Path
import subprocess

# Get commit SHA
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()

# Update work_items.json
work_items_path = Path('data/work_items.json')
work_items = json.loads(work_items_path.read_text())

# Find property by hash
for item in work_items['work_items']:
    if item['hash'] == '{hash}':
        item['commit_sha'] = sha
        break

work_items_path.write_text(json.dumps(work_items, indent=2))
"
```

#### Example Commit Messages

```
feat(property): Complete 4732 W Davis Rd - CONTENDER (412/605)

Property: 4732 W Davis Rd, Glendale, AZ 85306
Hash: ef7cd95f
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✓ | Synthesis ✓ | Report ✓
Kill-switch: PASS
Tier: CONTENDER
Score: 412/605
Monthly Cost: $3,245

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
feat(property): Complete 2353 W Tierra Buena Ln - FAILED (0/605)

Property: 2353 W Tierra Buena Ln, Phoenix, AZ 85023
Hash: abc12345
Phases: County ✓ | Cost ✓ | Listing ✓ | Map ✓ | Images ✗ | Synthesis ✗ | Report ✗
Kill-switch: FAIL (HOA fee: $250/mo)
Tier: FAILED
Score: 0/605
Monthly Cost: N/A

🤖 Generated with Claude Code Pipeline

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Error Handling

| Error | Action |
|-------|--------|
| Agent fails | Log, mark phase "failed", continue with partial |
| No images | Mark phase2a_exterior, phase2b_interior "skipped" |
| Rate limited | Backoff, retry, increment retry_count |
| Max retries | Skip permanently |
| Lock conflict | Skip property (another session owns it) |

**Always generate report with available data.**

## Verification Checklists

### Single Property

- [ ] enrichment_data.json updated
- [ ] work_items.json shows complete
- [ ] All phase_status entries complete/skipped
- [ ] Git commit created with property hash
- [ ] commit_sha populated in work_items.json

### Batch

- [ ] Stats match property counts
- [ ] No properties stuck in in_progress
- [ ] Summary report generated
- [ ] Git log shows individual property commits
- [ ] work_items.json summary accurate

## Summary Report Template

```
ANALYSIS COMPLETE
=================
Session: session_20251202_123456
Attempted: 25
Completed: 23
Failed: 2

Tier Breakdown:
- Unicorns: 3
- Contenders: 12
- Pass: 6
- Failed: 2

Git Commits: 23 (1 per completed property)
Research Tasks Pending: 4

Next Steps:
- Review failed properties: 2353 W Tierra Buena Ln, 8426 E Lincoln Dr
- Run: git log --oneline --grep="feat(property)" to see all commits
```

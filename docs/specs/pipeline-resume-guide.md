# Pipeline Resume Capability Guide

## Overview

The pipeline resume capability allows interrupted analysis runs to continue from the last checkpoint, avoiding re-processing completed work. This is essential for handling crashes, timeouts, and long-running batch operations.

## Quick Start

```python
from phx_home_analysis.pipeline import ResumePipeline
from phx_home_analysis.repositories import WorkItemsRepository

# Create repository and resumer
repo = WorkItemsRepository("data/work_items.json")
resumer = ResumePipeline(repo)

# Check if resume is possible
if resumer.can_resume():
    state = resumer.load_and_validate()
    pending = resumer.get_pending_addresses()
    print(f"Resuming with {len(pending)} pending addresses")
else:
    print("No state to resume from")
```

## CLI Usage

### Default Behavior (Resume)

When running the pipeline, it automatically resumes from the last checkpoint if one exists:

```bash
python scripts/pipeline_cli.py run --all
```

### Force Fresh Start

To ignore previous progress and start over:

```bash
python scripts/pipeline_cli.py run --all --fresh
```

The previous state is backed up to `work_items.{timestamp}.backup.json`.

### Force Resume (Bypass Validation)

To resume even when validation warnings occur:

```bash
python scripts/pipeline_cli.py run --all --force-resume
```

### Check Status

View current pipeline status:

```bash
python scripts/pipeline_cli.py status
```

## State File

Pipeline state is stored in `data/work_items.json`:

```json
{
  "session": {
    "session_id": "session_20251204_120000_a1b2c3d4",
    "started_at": "2025-12-04T12:00:00+00:00",
    "mode": "batch",
    "total_items": 50,
    "schema_version": "1.0.0"
  },
  "work_items": [
    {
      "address": "123 Main St, Phoenix, AZ 85001",
      "status": "pending",
      "phases": {
        "phase0_county": {"status": "completed"},
        "phase1_listing": {"status": "pending"}
      }
    }
  ],
  "summary": {
    "total": 50,
    "pending": 25,
    "completed": 20,
    "failed": 5,
    "blocked": 0
  }
}
```

### Item Statuses

| Status | Description |
|--------|-------------|
| `pending` | Awaiting processing |
| `in_progress` | Currently being processed |
| `completed` | Successfully finished all phases |
| `failed` | Failed after exceeding retry attempts |
| `blocked` | Cannot proceed due to kill-switch failure or missing prerequisites |

## Stale Item Recovery

Items stuck in "in_progress" for more than 30 minutes are automatically reset to "pending" on resume. This prevents work from being blocked by crashed processes.

**Example Log Output:**
```
WARNING Reset stale in_progress item: 123 Main St (elapsed: 40.0m)
```

The original error message (if any) is preserved in `previous_error` for debugging.

## Error Recovery

### Corrupt State File

If the state file is corrupted, the pipeline will display a clear error:

```
Error: State file corrupted: JSON parse error at line 5: Expecting ',' delimiter
Suggestion: Run with --fresh to start over (estimated data loss: 12 items)
```

### Schema Version Mismatch

If the state file has an incompatible schema version:

```
Error: State file version mismatch: expected 1.0.0, found 2.0.0
Suggestion: Run with --fresh to start over or migrate state manually
```

### Session Mismatch

If the session ID doesn't match (e.g., concurrent runs), a warning is displayed. Use `--force-resume` to bypass.

## Backup Management

- Backups are created automatically before fresh starts
- Backup filename format: `work_items.{timestamp}.backup.json`
- Up to 10 most recent backups are kept
- Older backups are automatically deleted

## API Reference

### ResumePipeline Class

```python
class ResumePipeline:
    STALE_TIMEOUT_MINUTES = 30  # Reset items stuck longer than this
    MAX_RETRIES = 3             # Retry failed items up to this count
    CURRENT_SCHEMA_VERSION = "1.0.0"
```

#### Methods

| Method | Description |
|--------|-------------|
| `can_resume()` | Returns `True` if valid state exists to resume |
| `load_and_validate()` | Loads and validates state, raises `StateValidationError` on failure |
| `reset_stale_items()` | Resets items stuck >30 minutes, returns list of reset addresses |
| `get_pending_addresses()` | Returns addresses needing processing |
| `get_completed_addresses()` | Returns already-completed addresses |
| `get_resume_summary()` | Returns statistics dict (session_id, counts) |
| `prepare_fresh_start(addresses)` | Backs up state and initializes new session |
| `estimate_data_loss()` | Returns count of completed items that would be re-processed |

### StateValidationError Exception

```python
class StateValidationError(Exception):
    message: str          # Human-readable error
    details: dict         # Additional context (e.g., field names)
    suggestion: str       # Actionable recommendation
```

## Implementation Notes

For developers integrating with the resume capability:

1. **Use WorkItemsRepository** for all state operations
2. **Call checkpoint_phase_start()** before phase execution
3. **Call checkpoint_phase_complete()** after phase completes
4. **Use ResumePipeline.can_resume()** to check if resume is possible
5. **Use ResumePipeline.get_pending_addresses()** to get work items

### Example Integration

```python
from phx_home_analysis.pipeline import ResumePipeline
from phx_home_analysis.repositories import WorkItemsRepository

def run_pipeline(addresses: list[str], fresh: bool = False):
    repo = WorkItemsRepository("data/work_items.json")
    resumer = ResumePipeline(repo, fresh=fresh)

    if fresh:
        backup = resumer.prepare_fresh_start(addresses)
        print(f"Backed up to: {backup}")
        addresses_to_process = addresses
    elif resumer.can_resume():
        state = resumer.load_and_validate()
        addresses_to_process = resumer.get_pending_addresses()
        summary = resumer.get_resume_summary()
        print(f"Resuming {summary['session_id']}: {len(addresses_to_process)} pending")
    else:
        repo.initialize_session(mode="batch", addresses=addresses)
        addresses_to_process = addresses

    for address in addresses_to_process:
        repo.checkpoint_phase_start(address, "phase0_county")
        # ... execute phase ...
        repo.checkpoint_phase_complete(address, "phase0_county")
```

## Troubleshooting

### "Cannot resume - no valid state"

The work_items.json file either doesn't exist or has an empty/invalid session. Run with explicit addresses or `--all` to start a new session.

### "Stale items detected"

This is normal - items left in "in_progress" for >30 minutes are automatically reset. Check logs for which items were reset.

### "Version mismatch"

The state file was created with a different schema version. Either:
1. Use `--fresh` to start over
2. Manually migrate the state file

### High data loss estimate

Before using `--fresh`, check `resumer.estimate_data_loss()` to see how many completed items would need re-processing. Consider whether the existing progress is worth preserving.

## Related Documentation

- [WorkItemsRepository](../architecture/work-items-repository.md) - State management details
- [PhaseCoordinator](../architecture/phase-coordinator.md) - Phase execution flow
- [Pipeline Overview](../specs/phase-execution-guide.md) - Complete pipeline documentation

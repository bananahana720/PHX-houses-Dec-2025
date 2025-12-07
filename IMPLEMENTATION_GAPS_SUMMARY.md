# Data Pipeline Gaps Implementation Summary

## Implementation Status

### GAP 1: State Backup (StateManager) - ✅ COMPLETE

**File:** `src/phx_home_analysis/services/image_extraction/state_manager.py`

**Changes Made:**
1. Added `_create_backup()` method (lines 159-182)
   - Creates timestamped backups in `backups/` subdirectory
   - Returns Path to backup or None if state file doesn't exist

2. Added `_cleanup_old_backups(keep_count=10)` method (lines 184-208)
   - Removes old backups, keeping only most recent N
   - Sorted by modification time

3. Added `restore_from_backup(backup_path=None)` method (lines 210-254)
   - Restores from specific backup or most recent if None
   - Creates backup of current state before restoring
   - Clears cached state to force reload

4. Updated `save()` method (lines 256-298)
   - Calls `_create_backup()` before saving
   - Calls `_cleanup_old_backups(keep_count=10)` after successful save

**Benefits:**
- Automatic backup on every save
- Protection against data corruption
- Easy recovery from bad states
- Automatic cleanup prevents disk bloat

---

### GAP 2: work_items.json Integration (Orchestrator) - ⚠️ PARTIAL

**File:** `src/phx_home_analysis/services/image_extraction/orchestrator.py`

**Changes Completed:**
1. Added `work_items_path` parameter to `__init__()` (line 262)
2. Stored `self.work_items_path` in instance (line 284)

**Changes Still Needed:**

#### Add Helper Methods (after line 527):

```python
def _update_work_item_phase(self, property_address: str, status: str) -> None:
    """Update phase2_images status in work_items.json.

    Args:
        property_address: Full property address
        status: Status to set ("complete", "failed", "in_progress")
    """
    if not self.work_items_path or not self.work_items_path.exists():
        return

    try:
        # Load work items
        with open(self.work_items_path, encoding="utf-8") as f:
            work_items = json.load(f)

        # Update phase status for this property
        properties = work_items.get("properties", {})
        if property_address in properties:
            properties[property_address]["phase_status"]["phase2_images"] = status
            properties[property_address]["updated_at"] = datetime.now().isoformat()
            work_items["updated_at"] = datetime.now().isoformat()

            # Atomic write
            self._atomic_json_write_sync(self.work_items_path, work_items)
            logger.debug(f"Updated work_items phase2_images={status} for {property_address}")
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to update work_items.json: {e}")

def _atomic_json_write_sync(self, path: Path, data: dict) -> None:
    """Write JSON atomically using temp file + rename (synchronous).

    Args:
        path: Target file path
        data: Data to serialize as JSON
    """
    import tempfile

    fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

#### Update extract_for_property_with_tracking (around line 1100):

After line where property extraction completes successfully, add:
```python
# Update work_items.json if configured
self._update_work_item_phase(property.full_address, "complete")
```

After line where property extraction fails, add:
```python
# Update work_items.json if configured
self._update_work_item_phase(property.full_address, "failed")
```

**Location:** In the `extract_all()` method within the async with semaphore block, after lines 712-730.

---

### GAP 3: Kill-Switch Pre-Validation (Orchestrator) - ❌ NOT STARTED

**File:** `src/phx_home_analysis/services/image_extraction/orchestrator.py`

**Changes Needed:**

#### Update `extract_all()` signature (line 610):

```python
async def extract_all(
    self,
    properties: list[Property],
    resume: bool = True,
    incremental: bool = True,
    force: bool = False,
    skip_kill_switch: bool = False,  # NEW PARAMETER
) -> ExtractionResult:
```

#### Add kill-switch filtering logic (after line 640, before processing):

```python
# Kill-switch pre-validation (GAP 3)
if not skip_kill_switch:
    from ...services.kill_switch.filter import KillSwitchFilter

    kill_switch_filter = KillSwitchFilter()
    properties_before = len(properties)
    passed_properties, failed_properties = kill_switch_filter.filter_properties(properties)

    if failed_properties:
        skipped_count = len(failed_properties)
        logger.info(
            f"Kill-switch pre-validation: {skipped_count}/{properties_before} properties failed"
        )

        # Log reasons for each failed property
        for prop in failed_properties:
            failure_reasons = ", ".join(prop.kill_switch_failures)
            logger.debug(
                f"Skipped {prop.full_address}: {failure_reasons}"
            )

        # Update result stats
        result.properties_skipped += skipped_count

    # Continue with only properties that passed kill-switches
    properties = passed_properties
    logger.info(f"Processing {len(properties)} properties after kill-switch filtering")
else:
    logger.info("Kill-switch pre-validation skipped (skip_kill_switch=True)")
```

**Benefits:**
- Avoids wasting resources extracting images for properties that will fail
- Clear logging of why properties were skipped
- Optional override with `skip_kill_switch` parameter for debugging

---

## Testing Requirements

### Unit Tests Needed

**File:** `tests/unit/test_state_manager.py`

Add tests for:
1. `test_create_backup()` - Verifies backup creation
2. `test_cleanup_old_backups()` - Verifies old backups are removed
3. `test_restore_from_backup()` - Verifies restore functionality
4. `test_restore_from_specific_backup()` - Verifies restore from specific path
5. `test_save_creates_backup()` - Verifies save() calls _create_backup()

**File:** `tests/unit/test_orchestrator.py` (may need to create)

Add tests for:
1. `test_work_items_update_on_completion()` - Verifies work_items updated
2. `test_work_items_update_on_failure()` - Verifies failure status updated
3. `test_kill_switch_filtering()` - Verifies properties filtered correctly
4. `test_kill_switch_skip_parameter()` - Verifies skip parameter works
5. `test_kill_switch_logging()` - Verifies skip reasons logged

### Integration Tests Needed

**File:** `tests/integration/test_image_extraction_pipeline.py`

1. End-to-end test with kill-switch filtering enabled
2. Test with work_items.json integration
3. Test backup/restore workflow

---

## Manual Testing Steps

1. **Test State Backup:**
   ```bash
   # Run extraction, verify backups created
   python scripts/extract_images.py --test
   ls data/property_images/metadata/backups/
   # Should see timestamped backup files
   ```

2. **Test work_items.json Integration:**
   ```bash
   # Verify phase2_images status updates
   python scripts/extract_images.py --test
   cat data/work_items.json | jq '.properties[].phase_status.phase2_images'
   # Should see "complete" or "failed" statuses
   ```

3. **Test Kill-Switch Filtering:**
   ```bash
   # Add property with HOA to test data
   # Run extraction, verify it's skipped
   python scripts/extract_images.py --test 2>&1 | grep "Kill-switch"
   # Should see skip message
   ```

---

## Next Steps

1. ✅ Complete GAP 2 by adding the helper methods
2. ✅ Complete GAP 3 by adding kill-switch filtering
3. ✅ Write unit tests for all three gaps
4. ✅ Run integration tests
5. ✅ Update documentation
6. ✅ Create PR with all changes

---

## Files Modified

- ✅ `src/phx_home_analysis/services/image_extraction/state_manager.py`
- ⚠️ `src/phx_home_analysis/services/image_extraction/orchestrator.py` (partial)
- ❌ `tests/unit/test_state_manager.py` (needs new tests)
- ❌ `tests/unit/test_orchestrator.py` (may need to create)

---

## Estimated Effort

- GAP 1 (State Backup): ✅ 2 hours - COMPLETE
- GAP 2 (work_items): ⚠️ 1 hour remaining (add methods + call sites)
- GAP 3 (Kill-Switch): ❌ 2 hours (implementation + testing)
- Testing: ❌ 3 hours (unit + integration tests)

**Total Remaining:** ~6 hours

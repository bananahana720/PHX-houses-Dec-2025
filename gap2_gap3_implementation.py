"""
Code snippets to add to orchestrator.py for GAP 2 and GAP 3 implementation.

This file contains the complete methods to add to the ImageExtractionOrchestrator class.
"""

# ============================================================================
# GAP 2: work_items.json Integration
# ============================================================================
# Add these methods after the _get_property_hash method (around line 527)


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


# ============================================================================
# GAP 2: Call _update_work_item_phase after property extraction
# ============================================================================
# In extract_all() method, within the async completion loop (around line 712-730):
#
# After successful completion (around line 716):
#     self._update_work_item_phase(prop.full_address, "complete")
#
# After failure (around line 726):
#     self._update_work_item_phase(prop.full_address, "failed")


# ============================================================================
# GAP 3: Kill-Switch Pre-Validation
# ============================================================================
# Modify extract_all() signature (line 610) to add skip_kill_switch parameter:
#
# async def extract_all(
#     self,
#     properties: list[Property],
#     resume: bool = True,
#     incremental: bool = True,
#     force: bool = False,
#     skip_kill_switch: bool = False,  # NEW
# ) -> ExtractionResult:


# Add this code after line 640 (after run logging starts), before HTTP client init:

"""
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
            logger.debug(f"Skipped {prop.full_address}: {failure_reasons}")

        # Update result stats
        result.properties_skipped += skipped_count

    # Continue with only properties that passed kill-switches
    properties = passed_properties
    logger.info(f"Processing {len(properties)} properties after kill-switch filtering")
else:
    logger.info("Kill-switch pre-validation skipped (skip_kill_switch=True)")

# Update total_properties in result to match filtered count
result.total_properties = len(properties)
"""

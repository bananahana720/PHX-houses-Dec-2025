"""Pipeline-specific error handling for work_items.json integration.

Provides functions to update work_items.json when errors occur,
tracking per-item failures with error details.

Usage:
    from phx_home_analysis.errors.pipeline import mark_item_failed, get_failure_summary

    try:
        await process_property(address)
    except Exception as e:
        mark_item_failed(work_items_path, address, "phase1_listing", e)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ErrorCategory, format_error_message, get_error_category

logger = logging.getLogger(__name__)


def mark_item_failed(
    work_items_path: Path,
    address: str,
    phase: str,
    error: Exception,
    can_retry: bool = False,
) -> None:
    """Mark a work item as failed in work_items.json.

    Updates the work item's phase status to 'failed' and records
    error details for debugging and reporting.

    Args:
        work_items_path: Path to work_items.json
        address: Property address that failed
        phase: Phase that failed (e.g., 'phase1_listing')
        error: The exception that caused the failure
        can_retry: If True, set status to 'retrying' instead of 'failed'
    """
    if not work_items_path.exists():
        logger.warning(f"work_items.json not found at {work_items_path}")
        return

    with open(work_items_path, encoding="utf-8") as f:
        data = json.load(f)

    # Find the work item
    item_found = False
    for item in data.get("work_items", []):
        if item.get("address") == address:
            item_found = True
            # Update phase status
            if "phases" not in item:
                item["phases"] = {}
            if phase not in item["phases"]:
                item["phases"][phase] = {}

            category = get_error_category(error)
            status = "retrying" if (can_retry and category == ErrorCategory.TRANSIENT) else "failed"

            item["phases"][phase]["status"] = status
            item["phases"][phase]["failed_at"] = datetime.now(timezone.utc).isoformat()
            item["phases"][phase]["error"] = format_error_message(error, phase)
            item["phases"][phase]["error_category"] = category.value

            item["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Log inside loop to ensure category is in scope
            logger.info(f"Marked {address}/{phase} as {status}")
            break

    if not item_found:
        logger.warning(f"Work item not found for address: {address}")
        return

    # Update summary counts - always recalculate
    summary = data.get("summary", {})
    failed_count = sum(
        1
        for item in data.get("work_items", [])
        for phase_data in item.get("phases", {}).values()
        if phase_data.get("status") == "failed"
    )
    summary["failed"] = failed_count
    data["summary"] = summary

    data["last_checkpoint"] = datetime.now(timezone.utc).isoformat()

    # Atomic write
    temp_path = work_items_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    temp_path.replace(work_items_path)


def get_failure_summary(work_items_path: Path) -> dict[str, Any]:
    """Get summary of all failed items from work_items.json.

    Returns:
        Dict with failure counts, failed addresses, and error details
    """
    if not work_items_path.exists():
        return {"failed_count": 0, "failures": []}

    with open(work_items_path, encoding="utf-8") as f:
        data = json.load(f)

    failures: list[dict[str, Any]] = []
    for item in data.get("work_items", []):
        for phase, phase_data in item.get("phases", {}).items():
            if phase_data.get("status") == "failed":
                failures.append(
                    {
                        "address": item.get("address"),
                        "phase": phase,
                        "error": phase_data.get("error"),
                        "error_category": phase_data.get("error_category"),
                        "failed_at": phase_data.get("failed_at"),
                    }
                )

    return {
        "failed_count": len(failures),
        "failures": failures,
    }


def clear_failure_status(
    work_items_path: Path,
    address: str,
    phase: str,
) -> None:
    """Clear the failure status for a work item phase (for retry scenarios).

    Args:
        work_items_path: Path to work_items.json
        address: Property address
        phase: Phase to clear failure status from
    """
    if not work_items_path.exists():
        logger.warning(f"work_items.json not found at {work_items_path}")
        return

    with open(work_items_path, encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("work_items", []):
        if item.get("address") == address:
            if "phases" in item and phase in item["phases"]:
                phase_data = item["phases"][phase]
                phase_data["status"] = "pending"
                phase_data.pop("failed_at", None)
                phase_data.pop("error", None)
                phase_data.pop("error_category", None)
                item["last_updated"] = datetime.now(timezone.utc).isoformat()
            break

    # Recalculate failed count
    summary = data.get("summary", {})
    failed_count = sum(
        1
        for item in data.get("work_items", [])
        for phase_data in item.get("phases", {}).values()
        if phase_data.get("status") == "failed"
    )
    summary["failed"] = failed_count
    data["summary"] = summary
    data["last_checkpoint"] = datetime.now(timezone.utc).isoformat()

    # Atomic write
    temp_path = work_items_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    temp_path.replace(work_items_path)

    logger.info(f"Cleared failure status for {address}/{phase}")


__all__ = [
    "mark_item_failed",
    "get_failure_summary",
    "clear_failure_status",
]

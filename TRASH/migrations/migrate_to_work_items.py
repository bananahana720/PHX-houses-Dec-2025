#!/usr/bin/env python3
"""
Migrate extraction_state.json to work_items.json schema v1.

Usage:
    python scripts/migrate_to_work_items.py [--dry-run] [--backup]

Reads:
    - data/extraction_state.json (legacy phase2 state)
    - data/enrichment_data.json (property data + completed phases)
    - data/phx_homes.csv (full property list)

Writes:
    - data/work_items.json (new unified state)
    - data/work_items.json.pre_migration.bak (optional backup)

Exit codes:
    0 - Success
    1 - Validation error
    2 - File not found
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def property_hash(address: str) -> str:
    """Generate 8-char MD5 hash of address."""
    return hashlib.md5(address.lower().encode()).hexdigest()[:8]


def load_json(path: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def load_csv(path: Path) -> list[dict]:
    """Load CSV file with error handling."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)


def save_json(data: dict, path: Path, dry_run: bool = False):
    """Save JSON file with pretty formatting."""
    if dry_run:
        print(f"[DRY RUN] Would write to: {path}")
        return

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote: {path}")


def backup_file(path: Path, dry_run: bool = False):
    """Create backup of existing file."""
    if not path.exists():
        return

    backup_path = path.with_suffix(path.suffix + ".pre_migration.bak")

    if dry_run:
        print(f"[DRY RUN] Would backup: {path} -> {backup_path}")
        return

    import shutil
    shutil.copy2(path, backup_path)
    print(f"✓ Backup created: {backup_path}")


def infer_phase_status(prop_data: dict, phase: str) -> dict:
    """
    Infer phase status from enrichment data.

    Logic:
        - If required fields exist and are non-null → complete
        - Otherwise → pending
    """
    phase_field_map = {
        "phase0_county": ["lot_sqft", "year_built"],
        "phase05_cost": ["monthly_cost"],
        "phase1_listing": ["price", "beds", "baths"],
        "phase1_map": ["school_rating"],
        "phase2_images": ["image_scores"],
        "phase3_synthesis": ["total_score", "tier"],
        "phase4_report": [],  # Inferred from deal sheet existence
    }

    required_fields = phase_field_map.get(phase, [])

    # Check if all required fields exist and are non-null
    has_data = all(
        field in prop_data and prop_data[field] is not None
        for field in required_fields
    )

    if has_data:
        return {
            "status": "complete",
            "started": None,  # Unknown
            "completed": prop_data.get("last_updated"),
            "commit_sha": None,  # Unknown
            "data_fields": required_fields,
            "error": None,
        }
    else:
        return {
            "status": "pending",
            "started": None,
            "completed": None,
            "commit_sha": None,
            "data_fields": [],
            "error": None,
        }


def infer_work_item_status(phases: dict) -> str:
    """Determine overall work item status from phases."""
    statuses = {phase["status"] for phase in phases.values()}

    if "failed" in statuses:
        return "failed"
    elif all(s == "complete" for s in statuses):
        return "completed"
    elif "in_progress" in statuses:
        return "in_progress"
    elif all(s == "pending" for s in statuses):
        return "pending"
    else:
        # Mixed complete/pending
        return "in_progress"


def migrate_extraction_state(
    extraction_state: dict,
    enrichment_data: list[dict],
    properties: list[dict],
) -> dict:
    """
    Migrate to work_items.json schema.

    Args:
        extraction_state: Legacy extraction_state.json data
        enrichment_data: enrichment_data.json property data (list of properties)
        properties: List of properties from phx_homes.csv

    Returns:
        work_items.json structure
    """
    # Initialize session
    # Note: Using utcnow() for consistency with existing codebase
    # Can be migrated to datetime.now(timezone.utc) in future refactor
    now = datetime.utcnow()
    session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}"

    # Index enrichment data by property hash
    enrichment_by_hash = {}
    for prop_data in enrichment_data:
        address = prop_data.get("full_address", "")
        if address:
            prop_hash_val = property_hash(address)
            enrichment_by_hash[prop_hash_val] = prop_data

    work_items_data = {
        "$schema": "work_items_v1",
        "session": {
            "session_id": session_id,
            "started_at": now.isoformat() + "Z",
            "mode": "batch",
            "total_items": len(properties),
            "current_index": 0,
            "runtime_seconds": 0,
            "last_checkpoint": now.isoformat() + "Z",
        },
        "blocked_sources": {
            "zillow": {"blocked": False, "last_check": now.isoformat() + "Z", "error": None},
            "redfin": {"blocked": False, "last_check": now.isoformat() + "Z", "error": None},
            "realtor": {"blocked": False, "last_check": now.isoformat() + "Z", "error": None},
        },
        "work_items": [],
        "summary": {
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "failed": 0,
            "skipped": 0,
            "tiers": {"UNICORN": 0, "CONTENDER": 0, "PASS": 0, "FAILED": 0},
        },
        "last_updated": now.isoformat() + "Z",
    }

    # Map properties to work items
    for prop in properties:
        # Try both 'address' and 'full_address' (CSV compatibility)
        address = prop.get("full_address") or prop.get("address", "")
        address = address.strip()
        if not address:
            continue

        prop_hash = property_hash(address)
        prop_data = enrichment_by_hash.get(prop_hash, {})

        # Infer phase statuses
        phases = {
            "phase0_county": infer_phase_status(prop_data, "phase0_county"),
            "phase05_cost": infer_phase_status(prop_data, "phase05_cost"),
            "phase1_listing": infer_phase_status(prop_data, "phase1_listing"),
            "phase1_map": infer_phase_status(prop_data, "phase1_map"),
            "phase2_images": infer_phase_status(prop_data, "phase2_images"),
            "phase3_synthesis": infer_phase_status(prop_data, "phase3_synthesis"),
            "phase4_report": infer_phase_status(prop_data, "phase4_report"),
        }

        # Handle legacy extraction_state.json (phase2 images only)
        if extraction_state and "properties" in extraction_state:
            legacy_prop = extraction_state["properties"].get(prop_hash, {})
            legacy_status = legacy_prop.get("status", "pending")

            if legacy_status == "completed":
                phases["phase2_images"]["status"] = "complete"
                phases["phase2_images"]["completed"] = legacy_prop.get("last_updated")
            elif legacy_status == "failed":
                phases["phase2_images"]["status"] = "failed"
                phases["phase2_images"]["error"] = legacy_prop.get("error")

        # Determine work item status
        status = infer_work_item_status(phases)

        # Extract tier and score
        tier = prop_data.get("tier")
        total_score = prop_data.get("total_score")

        # Kill-switch data
        kill_switch_data = prop_data.get("kill_switch_result", {})
        kill_switch = {
            "passed": kill_switch_data.get("passed", True),
            "failures": kill_switch_data.get("failures", []),
            "severity": kill_switch_data.get("severity", 0.0),
        }

        work_item = {
            "id": prop_hash,
            "address": address,
            "status": status,
            "phases": phases,
            "tier": tier,
            "total_score": total_score,
            "kill_switch": kill_switch,
            "retry_count": 0,
            "error_log": [],
            "completed_at": prop_data.get("last_updated") if status == "completed" else None,
            "locked_by": None,
            "locked_at": None,
        }

        work_items_data["work_items"].append(work_item)

        # Update summary
        work_items_data["summary"][status] += 1

        if tier and tier in work_items_data["summary"]["tiers"]:
            work_items_data["summary"]["tiers"][tier] += 1

    return work_items_data


def validate_work_items(data: dict) -> list[str]:
    """
    Validate work_items.json structure.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Schema version
    if data.get("$schema") != "work_items_v1":
        errors.append("Invalid or missing $schema")

    # Session required fields
    session = data.get("session", {})
    required_session = ["session_id", "started_at", "mode", "total_items"]
    for field in required_session:
        if field not in session:
            errors.append(f"Missing session.{field}")

    # Work items
    work_items = data.get("work_items", [])
    if not isinstance(work_items, list):
        errors.append("work_items must be a list")
        return errors

    seen_ids = set()
    for idx, item in enumerate(work_items):
        # Unique IDs
        item_id = item.get("id")
        if not item_id:
            errors.append(f"Work item {idx} missing id")
        elif item_id in seen_ids:
            errors.append(f"Duplicate work item id: {item_id}")
        else:
            seen_ids.add(item_id)

        # Required fields
        required_item = ["address", "status", "phases"]
        for field in required_item:
            if field not in item:
                errors.append(f"Work item {item_id} missing {field}")

        # Phase structure
        phases = item.get("phases", {})
        expected_phases = [
            "phase0_county", "phase05_cost", "phase1_listing",
            "phase1_map", "phase2_images", "phase3_synthesis", "phase4_report"
        ]
        for phase in expected_phases:
            if phase not in phases:
                errors.append(f"Work item {item_id} missing phase {phase}")
            else:
                phase_data = phases[phase]
                if "status" not in phase_data:
                    errors.append(f"Work item {item_id} phase {phase} missing status")

        # Lock consistency
        locked_by = item.get("locked_by")
        locked_at = item.get("locked_at")
        if (locked_by is None) != (locked_at is None):
            errors.append(f"Work item {item_id} has inconsistent lock state")

        # Status consistency
        if item.get("status") == "completed":
            if not all(p.get("status") == "complete" for p in phases.values()):
                errors.append(f"Work item {item_id} marked completed but has incomplete phases")

    # Summary validation
    summary = data.get("summary", {})
    status_sum = sum(summary.get(s, 0) for s in ["completed", "in_progress", "pending", "failed", "skipped"])
    if status_sum != len(work_items):
        errors.append(f"Summary counts ({status_sum}) don't match work items ({len(work_items)})")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Migrate extraction_state.json to work_items.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without writing files",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup of existing work_items.json (default: True)",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Skip backup creation",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("work_items.json Migration")
    print("=" * 70)
    print()

    # File paths
    extraction_state_path = PROJECT_ROOT / "data" / "extraction_state.json"
    enrichment_path = PROJECT_ROOT / "data" / "enrichment_data.json"
    csv_path = PROJECT_ROOT / "data" / "phx_homes.csv"
    output_path = PROJECT_ROOT / "data" / "work_items.json"

    # Load input files
    print("Loading input files...")
    extraction_state = {}
    if extraction_state_path.exists():
        extraction_state = load_json(extraction_state_path)
        print(f"✓ Loaded: {extraction_state_path}")
    else:
        print(f"ℹ Skipping (not found): {extraction_state_path}")

    enrichment_data = load_json(enrichment_path)
    print(f"✓ Loaded: {enrichment_path}")

    properties = load_csv(csv_path)
    print(f"✓ Loaded: {csv_path} ({len(properties)} properties)")
    print()

    # Perform migration
    print("Migrating to work_items.json schema...")
    work_items_data = migrate_extraction_state(
        extraction_state, enrichment_data, properties
    )
    print(f"✓ Created {len(work_items_data['work_items'])} work items")
    print()

    # Validate
    print("Validating work_items.json...")
    errors = validate_work_items(work_items_data)

    if errors:
        print("✗ VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        print()
        sys.exit(1)

    print("✓ Validation passed")
    print()

    # Summary statistics
    summary = work_items_data["summary"]
    print("Migration Summary:")
    print(f"  Total properties: {len(work_items_data['work_items'])}")
    print(f"  Completed:        {summary['completed']}")
    print(f"  In Progress:      {summary['in_progress']}")
    print(f"  Pending:          {summary['pending']}")
    print(f"  Failed:           {summary['failed']}")
    print(f"  Skipped:          {summary['skipped']}")
    print()
    print("  Tiers:")
    print(f"    UNICORN:        {summary['tiers']['UNICORN']}")
    print(f"    CONTENDER:      {summary['tiers']['CONTENDER']}")
    print(f"    PASS:           {summary['tiers']['PASS']}")
    print(f"    FAILED:         {summary['tiers']['FAILED']}")
    print()

    if args.dry_run:
        print("[DRY RUN] Migration complete. No files written.")
        print()
        print("Preview (first 3 work items):")
        for item in work_items_data["work_items"][:3]:
            print(f"  {item['id']}: {item['address']} - {item['status']}")
        return

    # Backup existing file
    if args.backup and output_path.exists():
        backup_file(output_path)

    # Write output
    save_json(work_items_data, output_path)
    print()
    print("=" * 70)
    print("Migration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

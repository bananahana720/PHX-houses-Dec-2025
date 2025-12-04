#!/usr/bin/env python3
"""
Reconcile image manifest with filesystem to detect and fix data loss.

This script compares:
1. image_manifest.json entries vs actual files on disk
2. address_folder_lookup.json counts vs actual file counts
3. Detects orphaned files (on disk but not in manifest)
4. Detects missing files (in manifest but not on disk)

Usage:
    python scripts/reconcile_image_manifest.py --check     # Read-only check
    python scripts/reconcile_image_manifest.py --repair    # Fix discrepancies
    python scripts/reconcile_image_manifest.py --backup    # Create backup before repair
    python scripts/reconcile_image_manifest.py --address "123 Main St"  # Single property

Exit codes:
    0 = All OK (no issues found)
    1 = Issues found (use --repair to fix)
    2 = Error during execution
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Data file paths
DATA_DIR = Path(__file__).parent.parent / "data"
MANIFEST_PATH = DATA_DIR / "property_images" / "metadata" / "image_manifest.json"
LOOKUP_PATH = DATA_DIR / "property_images" / "metadata" / "address_folder_lookup.json"
PROCESSED_DIR = DATA_DIR / "property_images" / "processed"
BACKUP_DIR = DATA_DIR / "property_images" / "backups"


def load_manifest() -> dict:
    """Load image manifest."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {"version": "1.0.0", "properties": {}}


def load_lookup() -> dict:
    """Load address folder lookup."""
    if LOOKUP_PATH.exists():
        with open(LOOKUP_PATH) as f:
            return json.load(f)
    return {"version": "1.0.0", "mappings": {}}


def save_manifest(manifest: dict) -> None:
    """Save manifest with atomic write."""
    temp_path = MANIFEST_PATH.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(manifest, f, indent=2)
    temp_path.replace(MANIFEST_PATH)


def save_lookup(lookup: dict) -> None:
    """Save lookup with atomic write."""
    temp_path = LOOKUP_PATH.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(lookup, f, indent=2)
    temp_path.replace(LOOKUP_PATH)


def create_backup() -> Path:
    """Create timestamped backup of manifest and lookup."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)

    if MANIFEST_PATH.exists():
        shutil.copy2(MANIFEST_PATH, backup_path / "image_manifest.json")
    if LOOKUP_PATH.exists():
        shutil.copy2(LOOKUP_PATH, backup_path / "address_folder_lookup.json")

    print(f"Created backup at: {backup_path}")
    return backup_path


def check_property(
    address: str,
    manifest_entries: list,
    folder_hash: str,
    verbose: bool = False
) -> dict:
    """Check a single property for discrepancies.

    Returns:
        Dict with 'missing', 'orphaned', 'count_mismatch' keys
    """
    folder_path = PROCESSED_DIR / folder_hash
    if not folder_path.exists():
        return {
            "missing": [e["image_id"] for e in manifest_entries],
            "orphaned": [],
            "count_mismatch": True,
            "manifest_count": len(manifest_entries),
            "disk_count": 0,
        }

    # Get files on disk
    disk_files = {f.stem for f in folder_path.glob("*.png")}

    # Get files in manifest
    manifest_ids = {e["image_id"] for e in manifest_entries}

    # Find discrepancies
    missing = manifest_ids - disk_files
    orphaned = disk_files - manifest_ids

    result = {
        "missing": list(missing),
        "orphaned": list(orphaned),
        "count_mismatch": len(disk_files) != len(manifest_entries),
        "manifest_count": len(manifest_entries),
        "disk_count": len(disk_files),
    }

    if verbose and (missing or orphaned):
        print(f"\n  {address} ({folder_hash}):")
        if missing:
            print(f"    Missing on disk: {len(missing)} files")
        if orphaned:
            print(f"    Orphaned on disk: {len(orphaned)} files")
        print(f"    Manifest: {len(manifest_entries)}, Disk: {len(disk_files)}")

    return result


def reconcile_all(
    manifest: dict,
    lookup: dict,
    repair: bool = False,
    verbose: bool = False,
    target_address: str | None = None,
) -> dict:
    """Check all properties for discrepancies.

    Args:
        manifest: Image manifest data
        lookup: Address folder lookup data
        repair: If True, fix discrepancies
        verbose: Print detailed output
        target_address: If set, only check this address

    Returns:
        Summary of issues found
    """
    issues = {
        "total_missing": 0,
        "total_orphaned": 0,
        "properties_with_issues": 0,
        "lookup_updates": 0,
        "details": {},
    }

    properties = manifest.get("properties", {})

    for address, entries in properties.items():
        if target_address and address != target_address:
            continue

        # Get folder hash from lookup
        lookup_entry = lookup.get("mappings", {}).get(address, {})
        folder_hash = lookup_entry.get("folder")

        if not folder_hash:
            # Try to derive from address (normalize)
            import hashlib
            folder_hash = hashlib.md5(address.encode()).hexdigest()[:8]
            if verbose:
                print(f"Warning: No folder hash for {address}, using derived: {folder_hash}")

        result = check_property(address, entries, folder_hash, verbose)

        if result["missing"] or result["orphaned"]:
            issues["properties_with_issues"] += 1
            issues["total_missing"] += len(result["missing"])
            issues["total_orphaned"] += len(result["orphaned"])
            issues["details"][address] = result

            if repair:
                # Update lookup with actual disk count
                actual_count = result["disk_count"]
                if address in lookup.get("mappings", {}):
                    old_count = lookup["mappings"][address].get("image_count", 0)
                    if old_count != actual_count:
                        lookup["mappings"][address]["image_count"] = actual_count
                        lookup["mappings"][address]["last_reconciled"] = datetime.now().isoformat()
                        issues["lookup_updates"] += 1
                        if verbose:
                            print(f"  Updated lookup: {old_count} -> {actual_count}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile image manifest with filesystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read-only check for discrepancies (default)",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Fix discrepancies (updates counts in lookup)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before making changes",
    )
    parser.add_argument(
        "--address",
        type=str,
        help="Check only a specific property address",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output",
    )

    args = parser.parse_args()

    # Default to check mode
    if not args.repair:
        args.check = True

    try:
        manifest = load_manifest()
        lookup = load_lookup()

        if args.backup and args.repair:
            create_backup()

        print("=" * 60)
        print("Image Manifest Reconciliation")
        print("=" * 60)
        print(f"Mode: {'REPAIR' if args.repair else 'CHECK (read-only)'}")
        if args.address:
            print(f"Target: {args.address}")
        print()

        issues = reconcile_all(
            manifest=manifest,
            lookup=lookup,
            repair=args.repair,
            verbose=args.verbose,
            target_address=args.address,
        )

        # Print summary
        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Properties with issues: {issues['properties_with_issues']}")
        print(f"Total missing files: {issues['total_missing']}")
        print(f"Total orphaned files: {issues['total_orphaned']}")

        if args.repair:
            print(f"Lookup entries updated: {issues['lookup_updates']}")

            # Save changes
            if issues['lookup_updates'] > 0:
                save_lookup(lookup)
                print("Saved updated lookup file")

        print("=" * 60)

        if issues["properties_with_issues"] > 0:
            if not args.repair:
                print("\nRun with --repair to fix discrepancies")
            return 1

        print("\nAll OK - no issues found")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

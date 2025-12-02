#!/usr/bin/env python3
"""
CLI tool for archiving property data.

Archives properties from enrichment_data.json to the archive directory.
Supports single property, batch, and stale-property archival.

Usage:
    python scripts/archive_properties.py --stale               # Archive all stale
    python scripts/archive_properties.py --stale --threshold 7 # Custom threshold
    python scripts/archive_properties.py --address "123 Main"  # Single property
    python scripts/archive_properties.py --list                # List archives
    python scripts/archive_properties.py --restore abc123      # Restore by hash
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phx_home_analysis.services.lifecycle import PropertyArchiver, StalenessDetector


def cmd_archive_stale(args: argparse.Namespace) -> int:
    """Archive all stale properties."""
    archiver = PropertyArchiver(
        enrichment_path=args.data_file,
        archive_dir=args.archive_dir,
    )

    print(f"Archiving stale properties (threshold: {args.threshold} days)...")

    # First show what would be archived
    detector = StalenessDetector(
        enrichment_path=args.data_file,
        threshold_days=args.threshold,
    )
    report = detector.analyze()

    if not report.has_stale_properties:
        print("No stale properties found.")
        return 0

    print(f"Found {report.stale_count} stale properties:")
    for prop in report.stale_properties[:10]:
        print(f"  - {prop.full_address} ({prop.staleness_days} days)")
    if report.stale_count > 10:
        print(f"  ... and {report.stale_count - 10} more")

    if not args.yes:
        confirm = input("\nProceed with archival? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return 0

    # Archive
    result = archiver.archive_stale_properties(threshold_days=args.threshold)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(result.summary())

    return 0 if result.all_succeeded else 1


def cmd_archive_address(args: argparse.Namespace) -> int:
    """Archive a single property by address."""
    archiver = PropertyArchiver(
        enrichment_path=args.data_file,
        archive_dir=args.archive_dir,
    )

    if not archiver.property_exists(args.address):
        print(f"Error: Property not found: {args.address}", file=sys.stderr)
        return 1

    if not args.yes:
        confirm = input(f"Archive '{args.address}'? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return 0

    result = archiver.archive_property(args.address)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    elif result.success:
        print(f"Archived: {result.full_address}")
        print(f"  Hash: {result.property_hash}")
        print(f"  Path: {result.archive_path}")
    else:
        print(f"Failed: {result.error_message}", file=sys.stderr)
        return 1

    return 0


def cmd_list_archives(args: argparse.Namespace) -> int:
    """List all archive files."""
    archiver = PropertyArchiver(
        enrichment_path=args.data_file,
        archive_dir=args.archive_dir,
    )

    archives = archiver.list_archives()

    if not archives:
        print("No archives found.")
        return 0

    print(f"Archive directory: {args.archive_dir}")
    print(f"Total archives: {len(archives)}")
    print()

    for archive in archives:
        # Load and display summary
        try:
            with open(archive) as f:
                data = json.load(f)
            address = data.get("full_address", "Unknown")
            prop_hash = data.get("property_hash", archive.stem.split("_")[0])
            archived_at = data.get("archived_at", "Unknown")
            print(f"  [{prop_hash}] {address}")
            print(f"      Archived: {archived_at}")
            print(f"      File: {archive.name}")
        except Exception as e:
            print(f"  {archive.name}: Error reading - {e}")

    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    """Restore an archived property."""
    archiver = PropertyArchiver(
        enrichment_path=args.data_file,
        archive_dir=args.archive_dir,
    )

    # Get archive info first
    archived_data = archiver.get_archive(args.hash)
    if not archived_data:
        print(f"Error: No archive found for hash: {args.hash}", file=sys.stderr)
        return 1

    address = archived_data.get("full_address", "Unknown")
    print(f"Found archive: {address}")

    if not args.yes:
        confirm = input("Restore this property? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return 0

    result = archiver.restore_property(args.hash)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    elif result.success:
        print(f"Restored: {result.full_address}")
    else:
        print(f"Failed: {result.error_message}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive property data from enrichment database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/archive_properties.py --stale               # Archive stale properties
  python scripts/archive_properties.py --stale --threshold 7 # 7-day threshold
  python scripts/archive_properties.py --address "123 Main"  # Archive specific property
  python scripts/archive_properties.py --list                # List all archives
  python scripts/archive_properties.py --restore abc123      # Restore by hash
        """,
    )

    # Global options
    parser.add_argument(
        "--data-file",
        "-d",
        type=Path,
        default=PROJECT_ROOT / "data" / "enrichment_data.json",
        help="Path to enrichment_data.json",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "archive",
        help="Directory for archive files",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts",
    )

    # Commands (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--stale",
        action="store_true",
        help="Archive all stale properties",
    )
    group.add_argument(
        "--address",
        type=str,
        metavar="ADDRESS",
        help="Archive a specific property by address",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="List all archive files",
    )
    group.add_argument(
        "--restore",
        type=str,
        metavar="HASH",
        dest="hash",
        help="Restore an archived property by hash",
    )

    # Stale-specific options
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=30,
        help="Staleness threshold in days (default: 30)",
    )

    args = parser.parse_args()

    # Validate data file exists
    if not args.data_file.exists() and not args.list:
        print(f"Error: Data file not found: {args.data_file}", file=sys.stderr)
        return 1

    # Route to command
    if args.stale:
        return cmd_archive_stale(args)
    elif args.address:
        return cmd_archive_address(args)
    elif args.list:
        return cmd_list_archives(args)
    elif args.hash:
        return cmd_restore(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())

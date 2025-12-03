#!/usr/bin/env python3
"""Schema migration CLI tool for data files.

This tool detects, validates, and migrates schema versions for property data files
like enrichment_data.json.

Usage:
    # Check current schema version
    python scripts/migrate_schema.py --file data/enrichment_data.json --check

    # Migrate to latest version
    python scripts/migrate_schema.py --file data/enrichment_data.json --to 2.0.0

    # Migrate to latest version with auto-detection
    python scripts/migrate_schema.py --file data/enrichment_data.json --to latest

    # Add version metadata to file without migration
    python scripts/migrate_schema.py --file data/enrichment_data.json --add-metadata

    # Dry run (show what would happen without modifying file)
    python scripts/migrate_schema.py --file data/enrichment_data.json --to 2.0.0 --dry-run

Examples:
    # Check version of enrichment data
    python scripts/migrate_schema.py --file data/enrichment_data.json --check

    # Migrate enrichment data to version 2.0.0
    python scripts/migrate_schema.py --file data/enrichment_data.json --to 2.0.0

    # Migrate with backup
    python scripts/migrate_schema.py --file data/enrichment_data.json --to latest --backup
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from phx_home_analysis.services.schema import (
    SchemaMetadata,
    SchemaMigrator,
    SchemaVersion,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> dict | list:
    """Load JSON file and return parsed data.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data (dict or list)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: dict | list, file_path: Path) -> None:
    """Save data to JSON file with consistent formatting.

    Args:
        data: Data to save
        file_path: Destination path
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved to {file_path}")


def create_backup(file_path: Path) -> Path:
    """Create a timestamped backup of the file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".{timestamp}.bak.json")
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup: {backup_path}")
    return backup_path


def check_version(file_path: Path, verbose: bool = True) -> SchemaVersion:
    """Check and display the schema version of a file.

    Args:
        file_path: Path to JSON file
        verbose: If True, print detailed version info

    Returns:
        Detected SchemaVersion
    """
    data = load_json_file(file_path)
    migrator = SchemaMigrator()
    version = migrator.get_version(data)
    current = SchemaVersion.current()

    if verbose:
        print(f"\n{'='*60}")
        print(f"File: {file_path}")
        print(f"{'='*60}")
        print(f"Detected Version: {version.value}")
        print(f"Current Version:  {current.value}")

        if version < current:
            print("\nStatus: OUTDATED - Migration recommended")
            print(f"Run: python scripts/migrate_schema.py --file {file_path} --to latest")
        elif version == current:
            print("\nStatus: UP TO DATE")
        else:
            print("\nStatus: FUTURE VERSION (unknown)")

        # Check for metadata
        if isinstance(data, list) and data:
            first_record = data[0]
            if isinstance(first_record, dict) and "_schema_metadata" in first_record:
                metadata = SchemaMetadata.from_dict(first_record["_schema_metadata"])
                print("\nMetadata:")
                print(f"  Created At: {metadata.created_at}")
                if metadata.migrated_at:
                    print(f"  Migrated At: {metadata.migrated_at}")
                    print(f"  Migrated From: {metadata.migrated_from}")
            else:
                print("\nMetadata: NOT PRESENT")
        elif isinstance(data, dict) and "_schema_metadata" in data:
            metadata = SchemaMetadata.from_dict(data["_schema_metadata"])
            print("\nMetadata:")
            print(f"  Created At: {metadata.created_at}")
            if metadata.migrated_at:
                print(f"  Migrated At: {metadata.migrated_at}")
                print(f"  Migrated From: {metadata.migrated_from}")
        else:
            print("\nMetadata: NOT PRESENT")

        print(f"{'='*60}\n")

    return version


def migrate_file(
    file_path: Path,
    target_version: str,
    dry_run: bool = False,
    backup: bool = True,
) -> bool:
    """Migrate a file to the target schema version.

    Args:
        file_path: Path to JSON file to migrate
        target_version: Target version string ("2.0.0" or "latest")
        dry_run: If True, don't write changes
        backup: If True, create backup before migration

    Returns:
        True if migration was successful, False otherwise
    """
    data = load_json_file(file_path)
    migrator = SchemaMigrator()

    # Determine target
    if target_version.lower() == "latest":
        target = SchemaVersion.current()
    else:
        try:
            target = SchemaVersion.from_string(target_version)
        except ValueError:
            logger.error(f"Invalid target version: {target_version}")
            logger.error(f"Valid versions: {[v.value for v in SchemaVersion]}")
            return False

    current = migrator.get_version(data)

    print(f"\n{'='*60}")
    print("Schema Migration")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    print(f"Current Version: {current.value}")
    print(f"Target Version:  {target.value}")
    print(f"Dry Run: {dry_run}")
    print(f"{'='*60}")

    if current == target:
        print(f"\nNo migration needed - already at version {target.value}")
        return True

    if current > target:
        logger.error(f"Cannot downgrade from {current.value} to {target.value}")
        print("\nDowngrade not supported. Use a backup from the older version.")
        return False

    # Perform migration
    try:
        print(f"\nMigrating from {current.value} to {target.value}...")
        migrated_data = migrator.migrate(data, target)

        if dry_run:
            print(f"\n[DRY RUN] Would write migrated data to {file_path}")
            print("[DRY RUN] No changes made")
        else:
            if backup:
                create_backup(file_path)

            save_json_file(migrated_data, file_path)
            print("\nMigration complete!")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def add_metadata(
    file_path: Path,
    dry_run: bool = False,
    backup: bool = True,
) -> bool:
    """Add schema version metadata to a file without migration.

    Args:
        file_path: Path to JSON file
        dry_run: If True, don't write changes
        backup: If True, create backup before modification

    Returns:
        True if successful, False otherwise
    """
    data = load_json_file(file_path)
    migrator = SchemaMigrator()

    # Check if metadata already exists
    has_metadata = False
    if isinstance(data, list) and data:
        if isinstance(data[0], dict) and "_schema_metadata" in data[0]:
            has_metadata = True
    elif isinstance(data, dict) and "_schema_metadata" in data:
        has_metadata = True

    if has_metadata:
        print("File already has _schema_metadata - no changes needed")
        return True

    # Add metadata
    version = migrator.get_version(data)
    data_with_metadata = migrator.add_version_metadata(data, version)

    print(f"\n{'='*60}")
    print("Adding Schema Metadata")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    print(f"Detected Version: {version.value}")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n[DRY RUN] Would add _schema_metadata to {file_path}")
        print("[DRY RUN] No changes made")
    else:
        if backup:
            create_backup(file_path)

        save_json_file(data_with_metadata, file_path)
        print("\nMetadata added successfully!")

    return True


def list_versions() -> None:
    """List all available schema versions with descriptions."""
    print(f"\n{'='*60}")
    print("Available Schema Versions")
    print(f"{'='*60}")

    for version in SchemaVersion:
        marker = " (current)" if version == SchemaVersion.current() else ""
        print(f"  {version.value}{marker}")

    print("\nVersion History:")
    print("  1.0.0 - Original schema (no _schema_metadata)")
    print("          Basic property fields")
    print("  2.0.0 - Current schema with all fields")
    print("          Added: crime, flood, walkability, noise, zoning, demographics")
    print("          Added: _schema_metadata for version tracking")
    print(f"{'='*60}\n")


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Schema migration tool for property data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Check schema version:
    python scripts/migrate_schema.py --file data/enrichment_data.json --check

  Migrate to latest version:
    python scripts/migrate_schema.py --file data/enrichment_data.json --to latest

  Migrate with dry run:
    python scripts/migrate_schema.py --file data/enrichment_data.json --to 2.0.0 --dry-run

  Add metadata only:
    python scripts/migrate_schema.py --file data/enrichment_data.json --add-metadata

  List available versions:
    python scripts/migrate_schema.py --list-versions
        """,
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Path to JSON file to check/migrate",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current schema version (read-only)",
    )

    parser.add_argument(
        "--to",
        dest="target_version",
        type=str,
        help="Target schema version (e.g., '2.0.0' or 'latest')",
    )

    parser.add_argument(
        "--add-metadata",
        action="store_true",
        help="Add _schema_metadata field without migration",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before migration",
    )

    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List all available schema versions",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --list-versions
    if args.list_versions:
        list_versions()
        return 0

    # Validate file argument for other operations
    if not args.file:
        parser.error("--file is required unless using --list-versions")

    file_path = args.file
    if not file_path.is_absolute():
        file_path = project_root / file_path

    # Handle operations
    if args.check:
        try:
            check_version(file_path)
            return 0
        except Exception as e:
            logger.error(f"Failed to check version: {e}")
            return 1

    if args.add_metadata:
        try:
            success = add_metadata(
                file_path,
                dry_run=args.dry_run,
                backup=not args.no_backup,
            )
            return 0 if success else 1
        except Exception as e:
            logger.error(f"Failed to add metadata: {e}")
            return 1

    if args.target_version:
        try:
            success = migrate_file(
                file_path,
                args.target_version,
                dry_run=args.dry_run,
                backup=not args.no_backup,
            )
            return 0 if success else 1
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return 1

    # Default: show help if no action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

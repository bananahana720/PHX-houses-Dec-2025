"""CLI script for extracting property data from Maricopa County Assessor API.

Extracts official county property data (lot size, year built, garage, sewer, pool)
and merges it into enrichment_data.json for kill-switch evaluation.

Supports two API modes:
- Official API (requires MARICOPA_ASSESSOR_TOKEN) - Complete data
- ArcGIS Public API (no auth) - Basic data fallback

Usage:
    # Extract data for all properties in phx_homes.csv
    python scripts/extract_county_data.py --all

    # Single property
    python scripts/extract_county_data.py --address "4732 W Davis Rd"

    # Dry run (preview without saving)
    python scripts/extract_county_data.py --all --dry-run

    # Update only missing fields in enrichment_data.json
    python scripts/extract_county_data.py --all --update-only

    # Verbose output
    python scripts/extract_county_data.py --all -v
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData
from phx_home_analysis.services.quality import DataSource, LineageTracker
from phx_home_analysis.validation.deduplication import compute_property_hash


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract property data from Maricopa County Assessor API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Property selection (mutually exclusive)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--all",
        action="store_true",
        help="Extract data for all properties in phx_homes.csv",
    )
    selection.add_argument(
        "--address",
        type=str,
        help="Extract data for a single property by street address",
    )

    # Operation modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without saving",
    )
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only fill missing fields, don't overwrite existing values",
    )

    # File paths
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/phx_homes.csv"),
        help="Input CSV file with properties (default: data/phx_homes.csv)",
    )
    parser.add_argument(
        "--enrichment",
        type=Path,
        default=Path("data/enrichment_data.json"),
        help="Enrichment JSON file to update (default: data/enrichment_data.json)",
    )

    # Other options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.5,
        help="Seconds between API calls (default: 1.5)",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def load_enrichment(path: Path) -> dict:
    """Load existing enrichment data.

    Handles both list and dict formats. Converts list format to dict keyed by full_address.
    """
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Convert list format to dict format
    if isinstance(data, list):
        return {item.get("full_address"): item for item in data if item.get("full_address")}
    return data


def save_enrichment(path: Path, data: dict) -> None:
    """Save enrichment data to JSON.

    Converts dict format back to list format for storage.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dict back to list format
    data_list = [
        {"full_address": addr, **props}
        for addr, props in data.items()
    ]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)


def should_update_field(
    entry: dict,
    field_name: str,
    county_value: any,
    logger: logging.Logger,
) -> tuple[bool, str]:
    """Determine if a field should be updated with county data.

    Args:
        entry: Existing enrichment entry for the property
        field_name: Name of the field to update
        county_value: New value from county data
        logger: Logger for warnings

    Returns:
        Tuple of (should_update: bool, reason: str)
    """
    existing_value = entry.get(field_name)
    source_field = f"{field_name}_source"
    existing_source = entry.get(source_field, "")

    # Never overwrite manually researched data
    if existing_source in ("manual", "manual_research", "user", "web_research"):
        logger.warning(
            f"  {field_name}: PRESERVING manual research value {existing_value} "
            f"(source={existing_source}) - county has {county_value}"
        )
        return False, f"Preserving manual research (source={existing_source})"

    # If no existing value, always update
    if existing_value is None:
        return True, "No existing value"

    # If values match, no need to update
    if existing_value == county_value:
        return False, "Values match"

    # Conflict: county differs from existing non-manual value
    # Log but still update (county is authoritative for non-manual data)
    logger.info(
        f"  {field_name}: Updating {existing_value} → {county_value} "
        f"(existing source: {existing_source or 'unknown'})"
    )
    return True, f"Updating: {existing_value} → {county_value}"


def merge_parcel_into_enrichment(
    existing: dict,
    full_address: str,
    parcel: ParcelData,
    update_only: bool = False,
    logger: logging.Logger | None = None,
    lineage_tracker: LineageTracker | None = None,
) -> tuple[dict, dict]:
    """Merge parcel data into existing enrichment entry.

    Args:
        existing: Existing enrichment data dict
        full_address: Property full address (key)
        parcel: Extracted parcel data
        update_only: If True, only fill None/missing fields
        logger: Logger for conflict reporting
        lineage_tracker: Optional LineageTracker to record field updates

    Returns:
        Tuple of (updated enrichment dict, conflict report dict)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    entry = existing.get(full_address, {}).copy()
    conflicts = {
        "preserved_manual": [],
        "updated": [],
        "skipped_no_change": [],
        "new_fields": [],
    }

    # Compute property hash for lineage tracking
    prop_hash = compute_property_hash(full_address) if lineage_tracker else None

    # Fields to merge from parcel
    merge_fields = {
        "lot_sqft": parcel.lot_sqft,
        "year_built": parcel.year_built,
        "garage_spaces": parcel.garage_spaces,
        "sewer_type": parcel.sewer_type,
        "has_pool": parcel.has_pool,
        "tax_annual": parcel.tax_annual,
    }

    for field, value in merge_fields.items():
        if value is not None:
            existing_value = entry.get(field)

            if update_only:
                # Only set if missing or None
                if existing_value is None:
                    entry[field] = value
                    conflicts["new_fields"].append(field)

                    # Track lineage for new field
                    if lineage_tracker and prop_hash:
                        lineage_tracker.record_field(
                            property_hash=prop_hash,
                            field_name=field,
                            source=DataSource.ASSESSOR_API,
                            confidence=DataSource.ASSESSOR_API.default_confidence,
                            original_value=value,
                            notes=f"County API source: {parcel.source}"
                        )
            else:
                # Check if we should update
                should_update, reason = should_update_field(entry, field, value, logger)

                if should_update:
                    entry[field] = value
                    if existing_value is None:
                        conflicts["new_fields"].append(field)
                    else:
                        conflicts["updated"].append({
                            "field": field,
                            "old": existing_value,
                            "new": value,
                            "reason": reason,
                        })

                    # Track lineage for updated field
                    if lineage_tracker and prop_hash:
                        lineage_tracker.record_field(
                            property_hash=prop_hash,
                            field_name=field,
                            source=DataSource.ASSESSOR_API,
                            confidence=DataSource.ASSESSOR_API.default_confidence,
                            original_value=value,
                            notes=f"County API source: {parcel.source}, updated from {existing_value}"
                        )
                else:
                    if "manual" in reason.lower():
                        conflicts["preserved_manual"].append({
                            "field": field,
                            "value": existing_value,
                            "county_value": value,
                            "reason": reason,
                        })
                    else:
                        conflicts["skipped_no_change"].append(field)

    # Add coordinates if available (from ArcGIS fallback)
    if parcel.latitude and parcel.longitude:
        for coord_field, coord_value in [("latitude", parcel.latitude), ("longitude", parcel.longitude)]:
            if not update_only or entry.get(coord_field) is None:
                existing_coord = entry.get(coord_field)
                should_update, reason = should_update_field(entry, coord_field, coord_value, logger)
                if should_update:
                    entry[coord_field] = coord_value
                    if existing_coord is None:
                        conflicts["new_fields"].append(coord_field)

                    # Track lineage for coordinates
                    if lineage_tracker and prop_hash:
                        lineage_tracker.record_field(
                            property_hash=prop_hash,
                            field_name=coord_field,
                            source=DataSource.ASSESSOR_API,
                            confidence=0.90,  # Slightly lower confidence for ArcGIS coordinates
                            original_value=coord_value,
                            notes="ArcGIS API coordinates"
                        )

    return entry, conflicts


def print_banner(num_properties: int, args: argparse.Namespace) -> None:
    """Print startup banner."""
    print()
    print("=" * 60)
    print("Maricopa County Assessor Data Extraction")
    print("=" * 60)
    print(f"Properties: {num_properties}")
    print(f"Enrichment file: {args.enrichment}")
    mode = "Dry run" if args.dry_run else "Update-only" if args.update_only else "Full extraction"
    print(f"Mode: {mode}")
    print(f"Rate limit: {args.rate_limit}s between API calls")
    print("=" * 60)
    print()


def print_parcel_summary(parcel: ParcelData) -> None:
    """Print extracted parcel data."""
    print(f"  APN: {parcel.apn}")
    print(f"  Source: {parcel.source}")
    print(f"  lot_sqft: {parcel.lot_sqft}")
    print(f"  year_built: {parcel.year_built}")
    print(f"  garage_spaces: {parcel.garage_spaces}")
    print(f"  sewer_type: {parcel.sewer_type}")
    print(f"  has_pool: {parcel.has_pool}")
    print(f"  tax_annual: {parcel.tax_annual}")
    if parcel.latitude:
        print(f"  coordinates: ({parcel.latitude}, {parcel.longitude})")


def print_summary(results: list, failed: list, all_conflicts: dict) -> None:
    """Print extraction summary with conflict report."""
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Successfully extracted: {len(results)} properties")
    print(f"Failed: {len(failed)} properties")

    if failed:
        print("\nFailed addresses:")
        for addr in failed[:10]:
            print(f"  - {addr}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # Conflict summary
    print("\n" + "=" * 60)
    print("Conflict Report")
    print("=" * 60)

    preserved_count = sum(len(c["preserved_manual"]) for c in all_conflicts.values())
    updated_count = sum(len(c["updated"]) for c in all_conflicts.values())
    new_count = sum(len(c["new_fields"]) for c in all_conflicts.values())

    print(f"Fields preserved (manual research): {preserved_count}")
    print(f"Fields updated (county override): {updated_count}")
    print(f"New fields added: {new_count}")

    # Show preserved manual fields
    if preserved_count > 0:
        print("\nManually researched fields preserved:")
        for addr, conflicts in all_conflicts.items():
            if conflicts["preserved_manual"]:
                print(f"\n  {addr}:")
                for item in conflicts["preserved_manual"]:
                    print(f"    - {item['field']}: kept {item['value']} (county had {item['county_value']})")

    # Show updated fields (conflicts resolved)
    if updated_count > 0:
        print("\nFields updated (county data authoritative):")
        shown = 0
        max_show = 10
        for addr, conflicts in all_conflicts.items():
            if conflicts["updated"] and shown < max_show:
                print(f"\n  {addr}:")
                for item in conflicts["updated"][:3]:  # Show max 3 per property
                    print(f"    - {item['field']}: {item['old']} → {item['new']}")
                    shown += 1
                    if shown >= max_show:
                        break
        if updated_count > shown:
            print(f"\n  ... and {updated_count - shown} more updates")

    print("=" * 60)


async def main() -> int:
    """Main async entry point."""
    args = parse_args()
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate CSV exists
    if not args.csv.exists():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        return 1

    # Load properties from CSV
    try:
        repo = CsvPropertyRepository(args.csv)
        all_properties = repo.load_all()
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        return 1

    # Filter to requested properties
    if args.all:
        properties = all_properties
    else:
        # Find matching property by street address
        street_lower = args.address.lower()
        properties = [p for p in all_properties if street_lower in p.street.lower()]
        if not properties:
            print(f"No property found matching: {args.address}", file=sys.stderr)
            return 1

    if not properties:
        print("No properties to process", file=sys.stderr)
        return 1

    print_banner(len(properties), args)

    # Load existing enrichment data
    enrichment = load_enrichment(args.enrichment)
    logger.info(f"Loaded {len(enrichment)} existing enrichment records")

    # Initialize lineage tracker
    lineage_file = Path("data/field_lineage.json")
    tracker = LineageTracker(lineage_file)
    logger.info(f"Loaded lineage tracker with {tracker.property_count()} properties")

    # Extract data
    results = []
    failed = []
    all_conflicts = {}

    async with MaricopaAssessorClient(rate_limit_seconds=args.rate_limit) as client:
        for i, prop in enumerate(properties, 1):
            print(f"[{i}/{len(properties)}] {prop.street}")

            try:
                parcel = await client.extract_for_address(prop.street)

                if not parcel:
                    print("  No data found")
                    failed.append(prop.full_address)
                    continue

                print_parcel_summary(parcel)
                results.append((prop.full_address, parcel))

                # Merge into enrichment with conflict tracking and lineage
                if not args.dry_run:
                    updated_entry, conflicts = merge_parcel_into_enrichment(
                        enrichment,
                        prop.full_address,
                        parcel,
                        args.update_only,
                        logger,
                        tracker,
                    )
                    enrichment[prop.full_address] = updated_entry
                    all_conflicts[prop.full_address] = conflicts

            except Exception as e:
                logger.error(f"  Error: {e}")
                failed.append(prop.full_address)

    # Save updated enrichment
    if not args.dry_run and results:
        save_enrichment(args.enrichment, enrichment)
        logger.info(f"Saved {len(enrichment)} records to {args.enrichment}")

        # Save lineage tracker
        tracker.save()
        logger.info(f"Saved lineage data to {lineage_file}")

    print_summary(results, failed, all_conflicts)

    # Print lineage report
    if not args.dry_run and results:
        print()
        print(tracker.generate_report())

    return 0 if len(failed) < len(properties) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Requires: uv pip install -e .
from phx_home_analysis.domain.entities import Property
from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData
from phx_home_analysis.services.quality import LineageTracker


@dataclass
class ExtractionResult:
    """Result of a single property extraction for concurrent processing."""

    full_address: str
    street: str
    parcel: ParcelData | None
    error: str | None = None

    @property
    def success(self) -> bool:
        """Return True if extraction succeeded with valid parcel data."""
        return self.parcel is not None and self.error is None


async def extract_single_property(
    client: MaricopaAssessorClient,
    prop: Property,
    semaphore: asyncio.Semaphore,
) -> ExtractionResult:
    """Extract data for a single property with semaphore-controlled concurrency.

    Args:
        client: Assessor API client
        prop: Property to extract
        semaphore: Semaphore to limit concurrent requests

    Returns:
        ExtractionResult with parcel data or error
    """
    async with semaphore:
        try:
            parcel = await client.extract_for_address(prop.street)
            return ExtractionResult(
                full_address=prop.full_address,
                street=prop.street,
                parcel=parcel,
            )
        except Exception as e:
            return ExtractionResult(
                full_address=prop.full_address,
                street=prop.street,
                parcel=None,
                error=str(e),
            )


async def extract_batch_concurrent(
    client: MaricopaAssessorClient,
    properties: list[Property],
    max_concurrent: int = 5,
    progress_callback: Callable[[int, int, ExtractionResult], None] | None = None,
) -> list[ExtractionResult]:
    """Extract data for multiple properties concurrently.

    Uses asyncio.Semaphore to limit concurrent requests to avoid
    overwhelming the API server while still achieving significant
    speedup over sequential processing.

    Args:
        client: Assessor API client
        properties: List of properties to extract
        max_concurrent: Maximum concurrent requests (default 5)
        progress_callback: Optional callback for progress updates,
            receives (current_index, total_count, result)

    Returns:
        List of ExtractionResults in same order as input properties
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def extract_with_progress(prop: Property, index: int) -> ExtractionResult:
        result = await extract_single_property(client, prop, semaphore)
        if progress_callback:
            progress_callback(index + 1, len(properties), result)
        return result

    tasks = [extract_with_progress(prop, i) for i, prop in enumerate(properties)]

    return await asyncio.gather(*tasks)


def validate_path(path: Path, base_dir: Path, arg_name: str) -> Path:
    """Validate that path is within allowed directory to prevent path traversal.

    Security: Prevents path traversal attacks (e.g., --csv ../../etc/passwd)
    by ensuring all file paths remain within the project directory.

    Args:
        path: Path from CLI argument
        base_dir: Project base directory (allowed root)
        arg_name: Argument name for error messages

    Returns:
        Resolved absolute path

    Raises:
        SystemExit: If path traversal attempt detected
    """
    # Resolve to absolute path, following symlinks
    resolved = path.resolve()
    base_resolved = base_dir.resolve()

    # Check that resolved path starts with base directory
    # Use os.path for reliable cross-platform comparison
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        # Path is outside base directory - potential path traversal attack
        print(f"Error: {arg_name} path '{path}' is outside project directory", file=sys.stderr)
        print(f"Allowed base: {base_resolved}", file=sys.stderr)
        sys.exit(1)

    return resolved


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
        default=0.5,
        help="Seconds between API calls per worker (default: 0.5)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent API requests (default: 5)",
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
    """Save enrichment data to JSON atomically with backup.

    Converts dict format back to list format for storage.
    Uses atomic write pattern to prevent corruption on crash.
    """
    from phx_home_analysis.utils.file_ops import atomic_json_save

    # Convert dict back to list format
    data_list = [
        {"full_address": addr, **props}
        for addr, props in data.items()
    ]

    backup = atomic_json_save(path, data_list, create_backup=True)
    if backup:
        logging.getLogger(__name__).info(f"Created backup: {backup}")


def print_banner(num_properties: int, args: argparse.Namespace) -> None:
    """Print startup banner with concurrency settings."""
    print()
    print("=" * 60)
    print("Maricopa County Assessor Data Extraction")
    print("=" * 60)
    print(f"Properties: {num_properties}")
    print(f"Enrichment file: {args.enrichment}")
    mode = "Dry run" if args.dry_run else "Update-only" if args.update_only else "Full extraction"
    print(f"Mode: {mode}")
    print(f"Concurrency: {args.max_concurrent} concurrent requests")
    print(f"Rate limit: {args.rate_limit}s between requests per worker")
    # Estimate time based on concurrent processing
    estimated_time = (num_properties / args.max_concurrent) * args.rate_limit
    print(f"Estimated time: ~{estimated_time:.1f}s (vs ~{num_properties * 1.5:.1f}s sequential)")
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

    # Security: Validate paths are within project directory to prevent path traversal
    base_dir = Path(__file__).parent.parent
    args.csv = validate_path(args.csv, base_dir, "--csv")
    args.enrichment = validate_path(args.enrichment, base_dir, "--enrichment")

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

    # Initialize lineage tracker and merge service
    lineage_file = Path("data/field_lineage.json")
    tracker = LineageTracker(lineage_file)
    logger.info(f"Loaded lineage tracker with {tracker.property_count()} properties")

    # Initialize merge service with lineage tracking
    from phx_home_analysis.services.enrichment import EnrichmentMergeService

    merge_service = EnrichmentMergeService(lineage_tracker=tracker)

    # Extract data using concurrent processing
    results = []
    failed = []
    all_conflicts: dict[str, dict] = {}

    # Progress callback for real-time updates
    def on_progress(current: int, total: int, result: ExtractionResult) -> None:
        status = "OK" if result.success else "FAILED" if result.error else "NO DATA"
        print(f"[{current}/{total}] {result.street} - {status}")
        if result.parcel:
            print_parcel_summary(result.parcel)
        elif result.error:
            print(f"  Error: {result.error}")

    print(f"\nExtracting with {args.max_concurrent} concurrent requests...")
    print("(HTTP/2 enabled for multiplexed connections)\n")

    async with MaricopaAssessorClient(rate_limit_seconds=args.rate_limit) as client:
        extraction_results = await extract_batch_concurrent(
            client,
            properties,
            max_concurrent=args.max_concurrent,
            progress_callback=on_progress,
        )

    # Process results after concurrent extraction completes
    for result in extraction_results:
        if result.success:
            results.append((result.full_address, result.parcel))

            # Merge into enrichment with conflict tracking and lineage
            if not args.dry_run:
                merge_result = merge_service.merge_parcel(
                    enrichment,
                    result.full_address,
                    result.parcel,
                    args.update_only,
                )
                enrichment[result.full_address] = merge_result.updated_entry
                # Convert to legacy dict format for backward compatibility with print_summary
                all_conflicts[result.full_address] = merge_result.to_legacy_dict()
        else:
            failed.append(result.full_address)
            if result.error:
                logger.error(f"Failed {result.street}: {result.error}")

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

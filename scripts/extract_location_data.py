"""CLI script for extracting location data from multiple sources.

Orchestrates extraction from crime, walk score, schools, noise, flood zones,
census demographics, and zoning data sources with crash recovery and state
management.

Supported sources:
- crime: Crime statistics (ZIP-level, SpotCrime)
- walkscore: Walk Score, Transit Score, Bike Score
- schools: School ratings (GreatSchools)
- noise: Noise levels (HowLoud)
- flood: FEMA flood zones (coordinate-based)
- census: Census demographics (ZIP-level)
- zoning: Zoning codes (Maricopa County)

Usage:
    # Extract all sources for all properties
    python scripts/extract_location_data.py --all

    # Single property
    python scripts/extract_location_data.py --address "4732 W Davis Rd"

    # All properties in ZIP
    python scripts/extract_location_data.py --zip 85306

    # Filter to specific sources
    python scripts/extract_location_data.py --all --sources crime,flood,census

    # Dry run (preview without extracting)
    python scripts/extract_location_data.py --all --dry-run

    # Start fresh (ignore previous state)
    python scripts/extract_location_data.py --all --fresh

    # Resume from last state (default)
    python scripts/extract_location_data.py --all --resume

    # Verbose output
    python scripts/extract_location_data.py --all -v
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Requires: uv pip install -e .
from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.services.enrichment import EnrichmentMergeService
from phx_home_analysis.services.location_data import (
    LocationDataOrchestrator,
    LocationStateManager,
)
from phx_home_analysis.services.quality import LineageTracker


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract location data from multiple sources",
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
    selection.add_argument(
        "--zip",
        type=str,
        help="Extract data for all properties in a ZIP code",
    )

    # Source filtering
    parser.add_argument(
        "--sources",
        type=str,
        help="Comma-separated list of sources to extract (e.g., 'crime,flood,census'). "
        "Available: crime, walkscore, schools, noise, flood, census, zoning. Default: all sources.",
    )

    # Operation modes
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from previous state (default)",
    )
    mode.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh, ignore previous state",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without actually extracting",
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
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("data/location_extraction_state.json"),
        help="State file for crash recovery (default: data/location_extraction_state.json)",
    )

    # Other options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent extractions (default: 3)",
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
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        # Path is outside base directory - potential path traversal attack
        print(f"Error: {arg_name} path '{path}' is outside project directory", file=sys.stderr)
        print(f"Allowed base: {base_resolved}", file=sys.stderr)
        sys.exit(1)

    return resolved


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
    data_list = [{"full_address": addr, **props} for addr, props in data.items()]

    backup = atomic_json_save(path, data_list, create_backup=True)
    if backup:
        logging.getLogger(__name__).info("Created backup: %s", backup)


def print_banner(num_properties: int, sources: list[str], args: argparse.Namespace) -> None:
    """Print startup banner with extraction settings."""
    print()
    print("=" * 70)
    print("Location Data Extraction Orchestrator")
    print("=" * 70)
    print(f"Properties: {num_properties}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Enrichment file: {args.enrichment}")
    print(f"State file: {args.state_file}")
    mode = "Dry run" if args.dry_run else "Fresh start" if args.fresh else "Resume"
    print(f"Mode: {mode}")
    print(f"Max concurrent: {args.max_concurrent}")
    print("=" * 70)
    print()


def print_summary(
    orchestrator: LocationDataOrchestrator,
    state: LocationStateManager,
    total_properties: int,
    extracted_count: int,
    skipped_count: int,
    failed_count: int,
) -> None:
    """Print extraction summary."""
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total properties: {total_properties}")
    print(f"Extracted: {extracted_count}")
    print(f"Skipped (already completed): {skipped_count}")
    print(f"Failed: {failed_count}")
    print()
    print("Per-source completion:")
    for source in orchestrator.SOURCES:
        if source in orchestrator.enabled_sources:
            completed = len(state._state.source_completed.get(source, set()))
            print(f"  {source:12s}: {completed:4d} properties")
    print()
    print(f"State saved to: {state.state_file}")
    print("=" * 70)


async def main() -> int:
    """Main async entry point."""
    args = parse_args()
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Security: Validate paths are within project directory to prevent path traversal
    base_dir = Path(__file__).parent.parent
    args.csv = validate_path(args.csv, base_dir, "--csv")
    args.enrichment = validate_path(args.enrichment, base_dir, "--enrichment")
    args.state_file = validate_path(args.state_file, base_dir, "--state-file")

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
    elif args.address:
        # Find matching property by street address
        street_lower = args.address.lower()
        properties = [p for p in all_properties if street_lower in p.street.lower()]
        if not properties:
            print(f"No property found matching: {args.address}", file=sys.stderr)
            return 1
    elif args.zip:
        # Filter by ZIP code
        properties = [p for p in all_properties if p.zip_code == args.zip]
        if not properties:
            print(f"No properties found in ZIP: {args.zip}", file=sys.stderr)
            return 1
    else:
        print("Error: Must specify --all, --address, or --zip", file=sys.stderr)
        return 1

    # Parse sources
    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]
        # Validate sources
        valid_sources = LocationDataOrchestrator.SOURCES
        invalid = set(sources) - set(valid_sources)
        if invalid:
            print(f"Error: Invalid sources: {invalid}", file=sys.stderr)
            print(f"Valid sources: {', '.join(valid_sources)}", file=sys.stderr)
            return 1

    # Initialize state manager
    state_manager = LocationStateManager(args.state_file)
    if args.fresh:
        logger.info("Fresh start requested, resetting state")
        state_manager.reset()

    # Print banner
    enabled_sources = sources or LocationDataOrchestrator.SOURCES
    print_banner(len(properties), enabled_sources, args)

    if args.dry_run:
        print("DRY RUN - Would extract for:")
        for i, prop in enumerate(properties[:10], 1):
            print(f"  {i}. {prop.full_address}")
        if len(properties) > 10:
            print(f"  ... and {len(properties) - 10} more")
        return 0

    # Load existing enrichment data
    enrichment = load_enrichment(args.enrichment)
    logger.info("Loaded %d existing enrichment records", len(enrichment))

    # Initialize lineage tracker and merge service
    lineage_file = Path("data/field_lineage.json")
    tracker = LineageTracker(lineage_file)
    merge_service = EnrichmentMergeService(lineage_tracker=tracker)

    # Initialize orchestrator
    orchestrator = LocationDataOrchestrator(
        state_manager=state_manager,
        enabled_sources=sources,
    )

    # Extract data
    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        print("Extracting location data...\n")

        for i, prop in enumerate(properties, 1):
            from phx_home_analysis.validation.deduplication import compute_property_hash

            prop_hash = compute_property_hash(prop.full_address)

            # Check if already completed
            if state_manager.is_property_completed(prop_hash):
                logger.info(
                    "[%d/%d] SKIPPING %s (already completed)", i, len(properties), prop.full_address
                )
                skipped_count += 1
                continue

            logger.info("[%d/%d] Extracting: %s", i, len(properties), prop.full_address)

            try:
                # Extract location data
                location_data = await orchestrator.extract_for_property(prop, skip_completed=True)

                # Merge into enrichment
                enrichment_update = location_data.to_enrichment_dict()
                if enrichment_update:
                    # Get or create entry
                    entry = enrichment.get(prop.full_address, {})

                    # Merge updates (simple dict update for now)
                    # TODO: Use EnrichmentMergeService.merge_location_data() when available
                    entry.update(enrichment_update)
                    enrichment[prop.full_address] = entry

                    logger.info("  ✓ Merged %d fields", len(enrichment_update))

                extracted_count += 1
                state_manager.mark_property_completed(prop_hash)

            except Exception as e:
                logger.error("  ✗ Failed: %s", e)
                failed_count += 1
                state_manager.mark_property_failed(prop_hash)

            # Save state after each property
            state_manager.save()

    finally:
        # Close orchestrator (closes all extractors)
        await orchestrator.close()

    # Save updated enrichment
    if extracted_count > 0:
        save_enrichment(args.enrichment, enrichment)
        logger.info("Saved %d records to %s", len(enrichment), args.enrichment)

        # Save lineage tracker
        tracker.save()
        logger.info("Saved lineage data to %s", lineage_file)

    # Print summary
    print_summary(
        orchestrator,
        state_manager,
        len(properties),
        extracted_count,
        skipped_count,
        failed_count,
    )

    # Print lineage report
    if extracted_count > 0:
        print()
        print(tracker.generate_report())

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

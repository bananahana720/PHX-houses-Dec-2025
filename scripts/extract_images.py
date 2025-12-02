"""CLI script for extracting property images from multiple sources.

Extracts images from Zillow, Redfin, Phoenix MLS, and Maricopa County Assessor
for properties in phx_homes.csv. Features:
- Multi-source extraction with perceptual hash deduplication
- State persistence for resumable operations
- Progress tracking and summary statistics
- Dry-run mode for URL discovery without download
- Source filtering for targeted extraction

Usage:
    # Extract from all sources for all properties
    python scripts/extract_images.py --all

    # Single property
    python scripts/extract_images.py --address "123 Main St, Phoenix, AZ 85001"

    # Specific sources only
    python scripts/extract_images.py --all --sources maricopa_assessor,zillow

    # Dry run (discover URLs without downloading)
    python scripts/extract_images.py --all --dry-run

    # Resume interrupted run
    python scripts/extract_images.py --all --resume

    # Fresh start (ignore previous state)
    python scripts/extract_images.py --all --fresh

    # Verbose output
    python scripts/extract_images.py --all -v
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Requires: uv pip install -e .
from phx_home_analysis.domain.enums import ImageSource
from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.services.image_extraction import ImageExtractionOrchestrator


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Extract property images from multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Property selection (mutually exclusive)
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument(
        "--all",
        action="store_true",
        help="Extract images for all properties in phx_homes.csv",
    )
    selection_group.add_argument(
        "--address",
        type=str,
        help="Extract images for a single property by full address",
    )

    # Source filtering
    parser.add_argument(
        "--sources",
        type=str,
        help=(
            "Comma-separated list of sources to extract from. "
            "Options: maricopa_assessor, zillow, redfin, phoenix_mls. "
            "Default: all sources"
        ),
    )

    # Operation modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover URLs but don't download images",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from previous state, skipping completed properties (default)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore previous state and start fresh",
    )

    # Output control
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/property_images"),
        help="Output directory for images (default: data/property_images)",
    )

    # Configuration
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/phx_homes.csv"),
        help="Path to properties CSV file (default: data/phx_homes.csv)",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def parse_sources(sources_str: str | None) -> list[ImageSource] | None:
    """Parse comma-separated sources string into ImageSource list.

    Args:
        sources_str: Comma-separated source names or None

    Returns:
        List of ImageSource enums or None for all sources

    Raises:
        ValueError: If unknown source specified
    """
    if not sources_str:
        return None

    source_map = {
        "maricopa_assessor": ImageSource.MARICOPA_ASSESSOR,
        "zillow": ImageSource.ZILLOW,
        "redfin": ImageSource.REDFIN,
        "phoenix_mls": ImageSource.PHOENIX_MLS,
    }

    sources = []
    for name in sources_str.split(","):
        name = name.strip().lower()
        if name not in source_map:
            raise ValueError(
                f"Unknown source '{name}'. Valid options: {', '.join(source_map.keys())}"
            )
        sources.append(source_map[name])

    return sources


def print_banner(args: argparse.Namespace, num_properties: int, sources: list[ImageSource]) -> None:
    """Print startup banner with configuration.

    Args:
        args: Parsed arguments
        num_properties: Number of properties to process
        sources: List of enabled sources
    """
    print()
    print("=" * 60)
    print("Image Extraction Pipeline")
    print("=" * 60)
    print(f"Properties: {num_properties}")
    print(f"Sources: {', '.join(s.display_name for s in sources)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Mode: {'Dry run' if args.dry_run else 'Full extraction'}")
    print(f"Resume: {'Yes' if args.resume and not args.fresh else 'No (fresh start)'}")
    print("=" * 60)
    print()


def print_progress(current: int, total: int, address: str, images_count: int) -> None:
    """Print progress update for a property.

    Args:
        current: Current property number
        total: Total properties
        address: Property address
        images_count: Number of images extracted
    """
    pct = (current / total) * 100
    print(f"[{current}/{total} - {pct:.1f}%] {address}")
    print(f"  Images extracted: {images_count}")


def print_summary(result, dry_run: bool) -> None:
    """Print extraction summary statistics.

    Args:
        result: ExtractionResult from orchestrator
        dry_run: Whether this was a dry run
    """
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Properties: {result.properties_completed} processed, {result.properties_failed} failed")

    if result.properties_skipped > 0:
        print(f"           {result.properties_skipped} skipped (already completed)")

    if dry_run:
        print(f"Images discovered: {result.total_images}")
    else:
        print(f"Images: {result.total_images} total, {result.unique_images} unique, {result.duplicate_images} duplicates")

    if result.failed_downloads > 0:
        print(f"Failed downloads: {result.failed_downloads}")

    print()
    print("By source:")
    for source_name, stats in result.by_source.items():
        if dry_run:
            print(f"  {source_name}: {stats.images_found} images discovered")
        else:
            print(
                f"  {source_name}: {stats.images_downloaded} images, "
                f"{stats.duplicates_detected} duplicates, "
                f"{stats.images_failed} failed"
            )

    if result.duration_seconds > 0:
        print()
        mins = int(result.duration_seconds // 60)
        secs = int(result.duration_seconds % 60)
        print(f"Duration: {mins}m {secs}s")
        print(f"Success rate: {result.success_rate:.1f}%")

    print("=" * 60)


async def main() -> int:
    """Main execution function.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    args = parse_args()

    # Configure logging
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validate CSV exists
        if not args.csv.exists():
            print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
            return 1

        # Load properties
        logger.info(f"Loading properties from {args.csv}")
        repo = CsvPropertyRepository(csv_file_path=args.csv)

        if args.all:
            properties = repo.load_all()
        else:
            # Single property lookup
            property = repo.load_by_address(args.address)
            if not property:
                print(f"Error: Property not found: {args.address}", file=sys.stderr)
                return 1
            properties = [property]

        if not properties:
            print("Error: No properties loaded", file=sys.stderr)
            return 1

        logger.info(f"Loaded {len(properties)} properties")

        # Parse sources
        try:
            sources = parse_sources(args.sources)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Initialize orchestrator
        orchestrator = ImageExtractionOrchestrator(
            base_dir=args.output_dir,
            enabled_sources=sources,
            max_concurrent_properties=3,  # Limit concurrency to be nice to servers
        )

        # Clear state if fresh start requested
        if args.fresh:
            logger.info("Fresh start requested, clearing previous state")
            orchestrator.clear_state()

        # Get enabled sources (use all if not specified)
        enabled_sources = sources or list(ImageSource)

        # Print banner
        print_banner(args, len(properties), enabled_sources)

        # Run extraction
        result = await orchestrator.extract_all(
            properties=properties,
            resume=args.resume and not args.fresh,
        )

        # Print summary
        print_summary(result, args.dry_run)

        # Return success if at least some properties succeeded
        if result.properties_completed > 0:
            return 0
        elif result.properties_failed > 0:
            print("Error: All properties failed", file=sys.stderr)
            return 1
        else:
            print("Warning: No properties were processed", file=sys.stderr)
            return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. State has been saved.")
        print("Run with --resume to continue from this point.")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

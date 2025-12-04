"""CLI script for extracting property images from multiple sources.

Extracts images from Zillow, Redfin, Phoenix MLS, and Maricopa County Assessor
for properties in phx_homes.csv. Features:
- Multi-source extraction with perceptual hash deduplication
- State persistence for resumable operations
- Progress tracking and summary statistics
- Dry-run mode for URL discovery without download
- Source filtering for targeted extraction
- Job queue mode for async, non-blocking execution (--queue)
- Real-time status visibility (--status)

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

    # Queue mode (persistent, resumable, with progress visibility)
    python scripts/extract_images.py --all --queue

    # Check queue status
    python scripts/extract_images.py --status

    # Queue with custom concurrency
    python scripts/extract_images.py --all --queue --max-concurrent 10
"""

import argparse
import asyncio
import logging
import os
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

    # Property selection (mutually exclusive, required unless --show-displays)
    selection_group = parser.add_mutually_exclusive_group(required=False)
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

    # Browser isolation (for non-headless stealth mode)
    parser.add_argument(
        "--isolation",
        type=str,
        choices=["virtual", "secondary", "off_screen", "minimize", "none"],
        default="virtual",
        help=(
            "Browser window isolation mode for non-headless stealth operation. "
            "Options: virtual (Virtual Display Driver), secondary (secondary monitor), "
            "off_screen (position off-screen), minimize (start minimized), "
            "none (no isolation). Default: virtual"
        ),
    )
    parser.add_argument(
        "--show-displays",
        action="store_true",
        help="Show detected displays and exit (useful for debugging isolation)",
    )

    # Job queue options
    parser.add_argument(
        "--queue",
        action="store_true",
        help=(
            "Use job queue mode for persistent, resumable extraction. "
            "Jobs survive crashes and can be monitored with --status."
        ),
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show queue status and exit (pending, running, completed jobs)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent jobs in queue mode (default: 5)",
    )
    parser.add_argument(
        "--clear-queue",
        action="store_true",
        help="Clear all jobs from the queue and exit",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Reset failed jobs to pending and exit",
    )

    # Cache cleanup options
    parser.add_argument(
        "--clean-images",
        action="store_true",
        help="Remove images older than 14 days from cache and exit",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=14,
        help="Maximum age in days for --clean-images (default: 14)",
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
    # Get headless mode from environment
    headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
    isolation_display = "n/a (headless)" if headless else args.isolation

    print()
    print("=" * 60)
    print("Image Extraction Pipeline")
    print("=" * 60)
    print(f"Properties: {num_properties}")
    print(f"Sources: {', '.join(s.display_name for s in sources)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Mode: {'Dry run' if args.dry_run else 'Full extraction'}")
    print(f"Resume: {'Yes' if args.resume and not args.fresh else 'No (fresh start)'}")
    print(f"Browser isolation: {isolation_display}")
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


def map_isolation_mode(mode: str) -> str:
    """Map CLI isolation mode to config value.

    Args:
        mode: CLI isolation mode (virtual, secondary, off_screen, minimize, none)

    Returns:
        Config isolation mode value
    """
    mode_map = {
        "virtual": "virtual_display",
        "secondary": "secondary_display",
        "off_screen": "off_screen",
        "minimize": "minimize",
        "none": "none",
    }
    return mode_map.get(mode, "virtual_display")


async def handle_queue_commands(args: argparse.Namespace, logger: logging.Logger) -> int | None:
    """Handle queue-related commands that exit early.

    Args:
        args: Parsed arguments
        logger: Logger instance

    Returns:
        Exit code if handled, None if not a queue command
    """
    from phx_home_analysis.services.job_queue import (
        JobQueue,
        format_queue_status,
        get_queue_status,
    )

    queue_path = Path("data/job_queue.json")

    # Handle --status
    if args.status:
        status = get_queue_status(queue_path)
        print(format_queue_status(status))
        return 0

    # Handle --clear-queue
    if args.clear_queue:
        queue = JobQueue(state_file=queue_path)
        queue.clear_all()
        print("Queue cleared.")
        return 0

    # Handle --retry-failed
    if args.retry_failed:
        queue = JobQueue(state_file=queue_path)
        count = queue.retry_failed()
        if count > 0:
            print(f"Reset {count} failed jobs to pending.")
        else:
            print("No failed jobs to retry.")
        return 0

    return None


async def run_queued_extraction(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Run extraction using job queue mode.

    Args:
        args: Parsed arguments
        logger: Logger instance

    Returns:
        Exit code
    """
    from phx_home_analysis.services.job_queue import (
        Job,
        JobExecutor,
        JobQueue,
        JobType,
        ProgressTracker,
        create_completion_callback,
        create_extraction_handler,
        create_progress_callback,
        format_queue_status,
        get_queue_status,
    )

    queue_path = Path("data/job_queue.json")
    work_items_path = Path("data/work_items.json")

    # Initialize queue
    queue = JobQueue(state_file=queue_path)
    tracker = ProgressTracker(work_items_path=work_items_path, queue=queue)

    # Parse source list for jobs
    source_list = None
    if args.sources:
        source_list = [s.strip().lower() for s in args.sources.split(",")]

    # Load properties and create jobs
    repo = CsvPropertyRepository(csv_file_path=args.csv)

    if args.all:
        properties = repo.load_all()
        addresses = [p.full_address for p in properties]
    elif args.address:
        property = repo.load_by_address(args.address)
        if not property:
            print(f"Error: Property not found: {args.address}", file=sys.stderr)
            return 1
        addresses = [property.full_address]
    else:
        print("Error: --all or --address required for --queue mode", file=sys.stderr)
        return 1

    # Enqueue jobs
    jobs = queue.enqueue_batch(
        addresses=addresses,
        sources=source_list,
        job_type=JobType.IMAGE_EXTRACTION,
    )

    new_jobs = sum(1 for j in jobs if j.status.value == "pending")
    existing_jobs = len(jobs) - new_jobs

    print()
    print("=" * 60)
    print("Job Queue Extraction")
    print("=" * 60)
    print(f"Total addresses: {len(addresses)}")
    print(f"New jobs created: {new_jobs}")
    print(f"Existing jobs: {existing_jobs}")
    print(f"Max concurrent: {args.max_concurrent}")
    print("=" * 60)
    print()

    # Create executor
    executor = JobExecutor(queue, max_concurrent=args.max_concurrent)

    # Register handler
    handler = create_extraction_handler(
        output_dir=args.output_dir,
        csv_path=args.csv,
    )
    executor.register_handler(JobType.IMAGE_EXTRACTION, handler)

    # Create callbacks
    on_progress = create_progress_callback(tracker)
    on_complete = create_completion_callback(tracker)

    # Progress display callback
    async def print_job_progress(job: Job) -> None:
        if job.status.value == "running":
            print(
                f"[{job.id}] {job.address[:40]} - "
                f"{job.progress.percent:.0%} {job.progress.current_step}"
            )

    # Combine callbacks
    async def combined_progress(job: Job) -> None:
        await on_progress(job)
        await print_job_progress(job)

    async def combined_complete(job: Job) -> None:
        await on_complete(job)
        status = "OK" if job.status.value == "completed" else job.status.value.upper()
        images = job.result.images_extracted if job.result else 0
        print(f"[{job.id}] {job.address[:40]} - {status} ({images} images)")

    try:
        # Run extraction
        await executor.start(
            on_progress=combined_progress,
            on_complete=combined_complete,
        )

        # Print final status
        print()
        status = get_queue_status(queue_path)
        print(format_queue_status(status))

        # Return based on results
        stats = queue.get_stats()
        if stats.get("failed_count", 0) > 0:
            return 1 if stats.get("completed_count", 0) == 0 else 0
        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted. Jobs have been saved.")
        print("Run with --queue again to resume, or --status to check progress.")
        await executor.stop(wait=False)
        return 1


async def run_cleanup(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Run cache cleanup operation.

    Args:
        args: Parsed arguments
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for error)
    """
    from phx_home_analysis.services.image_extraction.downloader import (
        ImageDownloader,
        ImageManifest,
    )

    output_dir = args.output_dir
    max_age_days = args.max_age_days
    dry_run = args.dry_run

    print()
    print("=" * 60)
    print("Image Cache Cleanup")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Max age (days): {max_age_days}")
    print(f"Mode: {'Dry run (preview only)' if dry_run else 'Live (will delete files)'}")
    print("=" * 60)
    print()

    if not output_dir.exists():
        print(f"Error: Output directory does not exist: {output_dir}", file=sys.stderr)
        return 1

    downloader = ImageDownloader(base_dir=output_dir)

    total_deleted = 0
    total_space = 0
    properties_cleaned = 0

    # Find all property folders
    for folder in output_dir.iterdir():
        if not folder.is_dir():
            continue

        manifest_path = folder / "images_manifest.json"
        if not manifest_path.exists():
            # Check for legacy manifest in metadata/image_manifest.json
            legacy_path = output_dir / "metadata" / "image_manifest.json"
            if not legacy_path.exists():
                continue

        # Load manifest
        try:
            manifest = ImageManifest.load(manifest_path, folder.name)
        except Exception as e:
            logger.warning(f"Failed to load manifest for {folder.name}: {e}")
            continue

        # Run cleanup
        result = downloader.cleanup_old_images(
            address=manifest.property_address or folder.name,
            manifest=manifest,
            max_age_days=max_age_days,
            dry_run=dry_run,
        )

        if result.files_deleted > 0:
            properties_cleaned += 1
            total_deleted += result.files_deleted
            total_space += result.space_reclaimed_bytes

            action = "Would delete" if dry_run else "Deleted"
            print(f"{folder.name}: {action} {result.files_deleted} files")

            # Save updated manifest
            if not dry_run:
                manifest.save(manifest_path)

    print()
    print("=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    action = "Would delete" if dry_run else "Deleted"
    print(f"Properties affected: {properties_cleaned}")
    print(f"Files {action.lower()}: {total_deleted}")
    print(f"Space {'to reclaim' if dry_run else 'reclaimed'}: {total_space / 1024 / 1024:.2f} MB")
    print("=" * 60)

    return 0


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

    # Handle --clean-images option
    if args.clean_images:
        return await run_cleanup(args, logger)

    # Handle --show-displays option
    if args.show_displays:
        from phx_home_analysis.services.infrastructure import get_display_summary

        print()
        print("Display Detection")
        print("=" * 60)
        print(get_display_summary())
        print("=" * 60)
        return 0

    # Handle queue commands that exit early
    queue_result = await handle_queue_commands(args, logger)
    if queue_result is not None:
        return queue_result

    # Handle --queue mode
    if args.queue:
        if not args.all and not args.address:
            print("Error: --all or --address required for --queue mode", file=sys.stderr)
            return 1
        return await run_queued_extraction(args, logger)

    # Validate that --all or --address is provided for extraction
    if not args.all and not args.address:
        print("Error: one of the arguments --all --address is required", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        return 1

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

        # Set browser isolation mode in environment for StealthExtractionConfig
        isolation_mode = map_isolation_mode(args.isolation)
        os.environ["BROWSER_ISOLATION"] = isolation_mode
        logger.info(f"Browser isolation mode set to: {isolation_mode}")

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

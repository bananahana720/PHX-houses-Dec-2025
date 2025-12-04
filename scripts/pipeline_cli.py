#!/usr/bin/env python3
"""Pipeline CLI for PHX Home Analysis.

This CLI provides a single entry point for executing the complete property
analysis pipeline with progress reporting and state management.

Usage:
    python scripts/pipeline_cli.py --all
    python scripts/pipeline_cli.py --test
    python scripts/pipeline_cli.py "123 Main St, Phoenix, AZ 85001"
    python scripts/pipeline_cli.py --status

Examples:
    # Process all properties from CSV
    python scripts/pipeline_cli.py --all

    # Process first 5 properties (test mode)
    python scripts/pipeline_cli.py --test

    # Process a single property
    python scripts/pipeline_cli.py "123 Main St, Phoenix, AZ 85001"

    # Show current pipeline status
    python scripts/pipeline_cli.py --status

    # Resume from checkpoint (default)
    python scripts/pipeline_cli.py --all --resume

    # Fresh start, clear all checkpoints
    python scripts/pipeline_cli.py --all --fresh

    # Strict mode - fail fast on errors
    python scripts/pipeline_cli.py --all --strict

    # Skip a specific phase
    python scripts/pipeline_cli.py --all --skip-phase 1
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phx_home_analysis.pipeline.phase_coordinator import PhaseCoordinator  # noqa: E402
from phx_home_analysis.pipeline.progress import PipelineStats, ProgressReporter  # noqa: E402

if TYPE_CHECKING:
    pass

# Data file paths
DATA_DIR = PROJECT_ROOT / "data"
CSV_FILE = DATA_DIR / "phx_homes.csv"
ENRICHMENT_FILE = DATA_DIR / "enrichment_data.json"
WORK_ITEMS_FILE = DATA_DIR / "work_items.json"

app = typer.Typer(
    name="pipeline",
    help="PHX Home Analysis Pipeline CLI",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def validate_exclusive_modes(
    address: str | None,
    all_properties: bool,
    test: bool,
    status: bool,
) -> None:
    """Validate that exactly one execution mode is specified.

    Args:
        address: Single property address
        all_properties: Process all properties flag
        test: Test mode (first 5) flag
        status: Status query flag

    Raises:
        typer.BadParameter: If not exactly one mode is specified
    """
    modes_selected = sum([bool(address), all_properties, test, status])

    if modes_selected == 0:
        raise typer.BadParameter(
            "Specify one of: <address>, --all, --test, or --status"
        )

    if modes_selected > 1:
        raise typer.BadParameter(
            "Cannot combine: <address>, --all, --test, and --status are mutually exclusive"
        )


def validate_skip_phase(skip_phase: int | None) -> int | None:
    """Validate skip-phase argument is in valid range.

    Args:
        skip_phase: Phase number to skip

    Returns:
        Validated phase number or None

    Raises:
        typer.BadParameter: If phase number is invalid
    """
    if skip_phase is not None:
        if skip_phase < 0 or skip_phase > 4:
            raise typer.BadParameter(
                f"--skip-phase must be 0-4, got {skip_phase}"
            )
    return skip_phase


def load_addresses_from_csv(csv_path: Path, limit: int | None = None) -> list[str]:
    """Load property addresses from CSV file.

    Args:
        csv_path: Path to the CSV file
        limit: Optional limit on number of addresses to return

    Returns:
        List of full addresses

    Raises:
        typer.Exit: If CSV file not found or invalid
    """
    if not csv_path.exists():
        console.print(f"[red]Error: CSV file not found: {csv_path}[/red]")
        raise typer.Exit(code=2)

    import csv

    addresses: list[str] = []
    try:
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try different column names for address
                full_address = (
                    row.get("full_address")
                    or row.get("address")
                    or row.get("Address")
                    or row.get("FULL_ADDRESS")
                )
                if full_address:
                    addresses.append(full_address.strip())
                    if limit and len(addresses) >= limit:
                        break
    except (csv.Error, UnicodeDecodeError) as e:
        console.print(f"[red]Error reading CSV: {e}[/red]")
        raise typer.Exit(code=3) from None

    return addresses


def run_async(coro: asyncio.coroutines) -> None:
    """Run async coroutine in event loop.

    Args:
        coro: Coroutine to run
    """
    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user[/yellow]")
        raise typer.Exit(code=130) from None


@app.command()
def main(
    address: Annotated[
        str | None,
        typer.Argument(
            help="Single property address to analyze",
            show_default=False,
        ),
    ] = None,
    all_properties: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Process all properties from CSV",
        ),
    ] = False,
    test: Annotated[
        bool,
        typer.Option(
            "--test",
            help="Process first 5 properties (validation mode)",
        ),
    ] = False,
    status: Annotated[
        bool,
        typer.Option(
            "--status",
            help="Show current pipeline status",
        ),
    ] = False,
    resume: Annotated[
        bool,
        typer.Option(
            "--resume/--fresh",
            help="Resume from checkpoint (default) or start fresh",
        ),
    ] = True,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Fail fast on any prerequisite failure",
        ),
    ] = False,
    skip_phase: Annotated[
        int | None,
        typer.Option(
            "--skip-phase",
            help="Skip specified phase (0-4)",
            min=0,
            max=4,
        ),
    ] = None,
) -> None:
    """Execute property analysis pipeline.

    The pipeline processes properties through phases:
    - Phase 0: County API data extraction
    - Phase 1a: Listing extraction (parallel)
    - Phase 1b: Map analysis (parallel)
    - Phase 2: Image assessment
    - Phase 3: Scoring synthesis
    - Phase 4: Deal sheet generation

    Exit Codes:
        0: Success
        1: General error
        2: File not found
        3: Data loading error
        130: Interrupted by user
    """
    # Validate mutually exclusive options
    validate_exclusive_modes(address, all_properties, test, status)

    # Validate skip_phase if provided
    skip_phases: set[int] = set()
    if skip_phase is not None:
        skip_phase = validate_skip_phase(skip_phase)
        skip_phases.add(skip_phase)

    # Initialize progress reporter
    reporter = ProgressReporter(console=console)

    # Handle --status mode
    if status:
        show_pipeline_status(reporter)
        return

    # Handle --fresh mode confirmation
    if not resume:
        confirm_fresh_start()

    # Determine properties to process
    properties: list[str] = []

    if address:
        properties = [address]
        console.print(f"[cyan]Single property mode: {address}[/cyan]")
    elif test:
        properties = load_addresses_from_csv(CSV_FILE, limit=5)
        console.print(f"[cyan]Test mode: Processing first {len(properties)} properties[/cyan]")
    elif all_properties:
        properties = load_addresses_from_csv(CSV_FILE)
        console.print(f"[cyan]Batch mode: Processing {len(properties)} properties[/cyan]")

    if not properties:
        console.print("[red]No properties to process[/red]")
        raise typer.Exit(code=1)

    # Create coordinator and execute
    coordinator = PhaseCoordinator(
        progress_reporter=reporter,
        strict=strict,
        resume=resume,
    )

    # Run the pipeline
    run_async(
        coordinator.execute_pipeline(
            properties=properties,
            skip_phases=skip_phases,
        )
    )

    # Show final summary
    reporter.show_completion_summary()


def show_pipeline_status(reporter: ProgressReporter) -> None:
    """Display current pipeline status.

    Args:
        reporter: Progress reporter instance
    """
    console.print("\n[bold cyan]Pipeline Status[/bold cyan]\n")

    # Load work_items.json if exists
    if WORK_ITEMS_FILE.exists():
        import json

        try:
            with WORK_ITEMS_FILE.open() as f:
                work_items = json.load(f)

            # Count properties by status
            stats = PipelineStats()
            stats.total = len(work_items.get("properties", {}))

            for prop_data in work_items.get("properties", {}).values():
                prop_status = prop_data.get("status", "pending")
                if prop_status == "pending":
                    stats.pending += 1
                elif prop_status == "in_progress":
                    stats.in_progress += 1
                elif prop_status == "complete":
                    stats.complete += 1
                    # Count tiers
                    tier = prop_data.get("tier", "").upper()
                    if tier == "UNICORN":
                        stats.unicorns += 1
                    elif tier == "CONTENDER":
                        stats.contenders += 1
                    elif tier == "PASS":
                        stats.passed += 1
                elif prop_status == "failed":
                    stats.failed += 1

            reporter.stats = stats
            reporter.show_status_table()

        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[red]Error reading work_items.json: {e}[/red]")
            raise typer.Exit(code=3) from None
    else:
        console.print("[yellow]No pipeline state found (work_items.json not found)[/yellow]")
        console.print("Run [cyan]--all[/cyan] or [cyan]--test[/cyan] to start processing")


def confirm_fresh_start() -> None:
    """Confirm fresh start when --fresh is specified.

    Raises:
        typer.Abort: If user declines confirmation
    """
    console.print(
        "\n[yellow]WARNING: --fresh will clear all checkpoints and start from Phase 0[/yellow]"
    )
    confirmed = typer.confirm("Are you sure you want to proceed?")
    if not confirmed:
        console.print("[red]Aborted[/red]")
        raise typer.Abort()


if __name__ == "__main__":
    app()

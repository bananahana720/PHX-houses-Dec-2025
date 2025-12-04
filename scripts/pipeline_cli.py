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

    # Dry-run mode - validate without processing
    python scripts/pipeline_cli.py --all --dry-run

    # JSON output mode
    python scripts/pipeline_cli.py --status --json
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Coroutine
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import typer
from rich.console import Console

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phx_home_analysis.pipeline.phase_coordinator import PhaseCoordinator  # noqa: E402
from phx_home_analysis.pipeline.progress import PipelineStats, ProgressReporter  # noqa: E402

if TYPE_CHECKING:
    pass


# Estimated seconds per property per phase for time estimation
# NOTE: These durations should align with Phase enum in phase_coordinator.py
# Update these values if phase structure changes
PHASE_DURATIONS = {
    "county_api": 2,
    "listing": 5,
    "map": 3,
    "images": 10,
    "synthesis": 5,
    "report": 2,
}
TOTAL_SECONDS_PER_PROPERTY = sum(PHASE_DURATIONS.values())


@dataclass
class CSVValidationError:
    """Represents a single CSV validation error."""

    row_number: int
    field: str
    message: str

    def __str__(self) -> str:
        """Return formatted error message with row number.

        Returns:
            String in format "Row N: message"
        """
        return f"Row {self.row_number}: {self.message}"


@dataclass
class CSVValidationResult:
    """Result of CSV validation."""

    is_valid: bool
    valid_addresses: list[str] = field(default_factory=list)
    errors: list[CSVValidationError] = field(default_factory=list)
    total_rows: int = 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

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


def validate_csv_with_errors(csv_path: Path, limit: int | None = None) -> CSVValidationResult:
    """Validate CSV file with detailed row-level error reporting.

    Args:
        csv_path: Path to the CSV file
        limit: Optional limit on number of addresses to validate

    Returns:
        CSVValidationResult with validation status, valid addresses, and errors
    """
    import csv

    result = CSVValidationResult(is_valid=True)

    if not csv_path.exists():
        result.is_valid = False
        result.errors.append(
            CSVValidationError(
                row_number=0,
                field="file",
                message=f"CSV file not found: {csv_path}",
            )
        )
        return result

    try:
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Check for address column
            address_columns = ["full_address", "address", "Address", "FULL_ADDRESS"]
            has_address_column = any(col in headers for col in address_columns)

            if not has_address_column:
                result.is_valid = False
                result.errors.append(
                    CSVValidationError(
                        row_number=0,
                        field="header",
                        message="Missing required address column (expected: full_address, address, Address, or FULL_ADDRESS)",
                    )
                )
                return result

            # Excel-style row numbering: header is row 1, first data row is row 2
            for row_idx, row in enumerate(reader, start=2):
                result.total_rows += 1

                # Try different column names for address
                full_address = (
                    row.get("full_address")
                    or row.get("address")
                    or row.get("Address")
                    or row.get("FULL_ADDRESS")
                )

                if not full_address or not full_address.strip():
                    result.is_valid = False
                    result.errors.append(
                        CSVValidationError(
                            row_number=row_idx,
                            field="address",
                            message="Empty or missing address",
                        )
                    )
                else:
                    result.valid_addresses.append(full_address.strip())

                if limit and len(result.valid_addresses) >= limit:
                    break

    except (csv.Error, UnicodeDecodeError) as e:
        result.is_valid = False
        result.errors.append(
            CSVValidationError(
                row_number=0,
                field="file",
                message=f"Error reading CSV: {e}",
            )
        )

    return result


def format_time_estimate(seconds: int) -> str:
    """Format seconds into human-readable time estimate.

    Args:
        seconds: Total seconds

    Returns:
        Formatted time string (e.g., "5 minutes 30 seconds")
    """
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if remaining_seconds == 0:
        return f"{minutes} minutes"
    return f"{minutes} minutes {remaining_seconds} seconds"


def run_dry_run(
    csv_path: Path,
    limit: int | None,
    json_output: bool,
) -> None:
    """Execute dry-run mode: validate CSV without API calls.

    Args:
        csv_path: Path to CSV file
        limit: Optional limit on properties
        json_output: Output results in JSON format
    """
    validation = validate_csv_with_errors(csv_path, limit)

    if json_output:
        # JSON output mode
        output = {
            "status": "valid" if validation.is_valid else "invalid",
            "dry_run": True,
            "total_rows": validation.total_rows,
            "valid_addresses": len(validation.valid_addresses),
            "error_count": validation.error_count,
            "errors": [str(e) for e in validation.errors],
        }
        if validation.is_valid:
            estimated_seconds = len(validation.valid_addresses) * TOTAL_SECONDS_PER_PROPERTY
            output["estimated_time_seconds"] = estimated_seconds
            output["estimated_time_human"] = format_time_estimate(estimated_seconds)
        print(json.dumps(output, indent=2))
    else:
        # Rich console output
        if validation.is_valid:
            console.print("\n[bold green]CSV Validation: PASSED[/bold green]")
            console.print(f"  Valid properties: {len(validation.valid_addresses)}")

            estimated_seconds = len(validation.valid_addresses) * TOTAL_SECONDS_PER_PROPERTY
            console.print(f"  Estimated processing time: {format_time_estimate(estimated_seconds)}")
            console.print("\n[cyan]Dry-run complete. No API calls made.[/cyan]")
        else:
            console.print("\n[bold red]CSV Validation: FAILED[/bold red]")
            console.print(f"\nFound {validation.error_count} error(s):\n")
            for error in validation.errors:
                console.print(f"  [red]{error}[/red]")
            console.print("\n[yellow]Processing blocked until errors are resolved.[/yellow]")
            raise typer.Exit(code=1)


def run_async(coro: Coroutine[Any, Any, None]) -> None:
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
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate input without making API calls",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output results in JSON format",
        ),
    ] = False,
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
        validated_phase = validate_skip_phase(skip_phase)
        if validated_phase is not None:
            skip_phases.add(validated_phase)

    # Initialize progress reporter
    reporter = ProgressReporter(console=console)

    # Handle --status mode
    if status:
        show_pipeline_status(reporter, json_output=json_output)
        return

    # Handle --dry-run mode
    if dry_run:
        limit = 5 if test else None
        run_dry_run(CSV_FILE, limit=limit, json_output=json_output)
        return

    # Handle --fresh mode confirmation
    if not resume:
        confirm_fresh_start()

    # Determine properties to process
    properties: list[str] = []

    if address:
        properties = [address]
        if not json_output:
            console.print(f"[cyan]Single property mode: {address}[/cyan]")
    elif test:
        properties = load_addresses_from_csv(CSV_FILE, limit=5)
        if not json_output:
            console.print(f"[cyan]Test mode: Processing first {len(properties)} properties[/cyan]")
    elif all_properties:
        properties = load_addresses_from_csv(CSV_FILE)
        if not json_output:
            console.print(f"[cyan]Batch mode: Processing {len(properties)} properties[/cyan]")

    if not properties:
        if not json_output:
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


def show_pipeline_status(reporter: ProgressReporter, json_output: bool = False) -> None:
    """Display current pipeline status.

    Args:
        reporter: Progress reporter instance
        json_output: Output results in JSON format
    """
    # Load work_items.json if exists
    if WORK_ITEMS_FILE.exists():
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

            if json_output:
                output = {
                    "status": "ok",
                    "pipeline_state": "found",
                    "statistics": {
                        "total": stats.total,
                        "pending": stats.pending,
                        "in_progress": stats.in_progress,
                        "complete": stats.complete,
                        "failed": stats.failed,
                    },
                    "tiers": {
                        "unicorns": stats.unicorns,
                        "contenders": stats.contenders,
                        "passed": stats.passed,
                    },
                }
                print(json.dumps(output, indent=2))
            else:
                console.print("\n[bold cyan]Pipeline Status[/bold cyan]\n")
                reporter.show_status_table()

        except (json.JSONDecodeError, KeyError) as e:
            if json_output:
                output = {
                    "status": "error",
                    "error": f"Error reading work_items.json: {e}",
                }
                print(json.dumps(output, indent=2))
            else:
                console.print(f"[red]Error reading work_items.json: {e}[/red]")
            raise typer.Exit(code=3) from None
    else:
        if json_output:
            output = {
                "status": "ok",
                "pipeline_state": "not_found",
                "message": "No pipeline state found (work_items.json not found)",
            }
            print(json.dumps(output, indent=2))
        else:
            console.print("\n[bold cyan]Pipeline Status[/bold cyan]\n")
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

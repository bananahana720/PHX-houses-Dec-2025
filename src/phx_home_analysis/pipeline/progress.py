"""Progress reporter for pipeline execution.

This module provides the ProgressReporter class that displays real-time
progress information during pipeline execution using the rich library.

Features:
    - Progress bar with percentage and ETA
    - Status table with property counts
    - Tier breakdown summary
    - Rolling average ETA calculation

Usage:
    from phx_home_analysis.pipeline import ProgressReporter

    reporter = ProgressReporter()
    reporter.start_batch(total=100)
    reporter.update_property(0, "123 Main St", "Phase 0")
    reporter.complete_property(success=True, tier="UNICORN")
    reporter.show_status_table()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeRemainingColumn
from rich.table import Table

if TYPE_CHECKING:
    pass


@dataclass
class PipelineStats:
    """Statistics for pipeline execution tracking.

    Attributes:
        total: Total number of properties to process
        pending: Number of properties not yet started
        in_progress: Number of properties currently being processed
        complete: Number of successfully completed properties
        failed: Number of properties that failed processing
        unicorns: Count of UNICORN tier properties
        contenders: Count of CONTENDER tier properties
        passed: Count of PASS tier properties
        start_time: When pipeline execution started
        phase_durations: List of phase execution durations for ETA calculation
    """

    total: int = 0
    pending: int = 0
    in_progress: int = 0
    complete: int = 0
    failed: int = 0
    unicorns: int = 0
    contenders: int = 0
    passed: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    phase_durations: list[float] = field(default_factory=list)

    @property
    def elapsed(self) -> timedelta:
        """Calculate elapsed time since pipeline start.

        Returns:
            Time elapsed since start_time
        """
        return datetime.now() - self.start_time

    @property
    def eta(self) -> timedelta | None:
        """Calculate estimated time remaining based on rolling average.

        Returns:
            Estimated time remaining, or None if insufficient data
        """
        if not self.phase_durations or self.complete == 0:
            return None

        # Use rolling average of last 5 property durations per story requirement
        recent_durations = self.phase_durations[-5:]
        avg_duration = mean(recent_durations)

        # Estimate remaining work
        remaining = self.total - self.complete - self.failed
        if remaining <= 0:
            return timedelta(seconds=0)

        return timedelta(seconds=avg_duration * remaining)

    def reset(self) -> None:
        """Reset all statistics for a new batch."""
        self.total = 0
        self.pending = 0
        self.in_progress = 0
        self.complete = 0
        self.failed = 0
        self.unicorns = 0
        self.contenders = 0
        self.passed = 0
        self.start_time = datetime.now()
        self.phase_durations = []


class ProgressReporter:
    """Reporter for pipeline execution progress using rich library.

    Provides progress bars, status tables, and tier breakdown displays
    for real-time monitoring of pipeline execution.

    Example:
        >>> reporter = ProgressReporter()
        >>> reporter.start_batch(total=100)
        >>> for i in range(100):
        ...     reporter.update_property(i, f"Property {i}", "Phase 0")
        ...     reporter.complete_property(success=True, tier="CONTENDER")
        >>> reporter.show_completion_summary()
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the progress reporter.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()
        self.stats = PipelineStats()
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None
        self._current_description: str = ""

    def start_batch(self, total: int) -> None:
        """Start progress tracking for batch processing.

        Creates a progress bar and initializes statistics.

        Args:
            total: Total number of properties to process
        """
        self.stats = PipelineStats(total=total, pending=total)

        # Create progress bar with columns
        self._progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("*"),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

        # Add task for tracking
        self._task_id = self._progress.add_task(
            description="Initializing...",
            total=total,
        )

        # Start the progress display
        self._progress.start()

        self.console.print(f"\n[bold cyan]Starting batch processing of {total} properties[/bold cyan]\n")

    def stop_batch(self) -> None:
        """Stop batch progress tracking."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_id = None

    def update_property(self, index: int, address: str, phase: str = "") -> None:
        """Update progress for current property.

        Args:
            index: Current property index (0-based)
            address: Property address being processed
            phase: Current phase description
        """
        if not self._progress or self._task_id is None:
            return

        # Truncate long addresses
        display_addr = address[:35] + "..." if len(address) > 35 else address

        # Build description
        if phase:
            description = f"[{index + 1}/{self.stats.total}] {phase}: {display_addr}"
        else:
            description = f"[{index + 1}/{self.stats.total}] {display_addr}"

        self._current_description = description
        self._progress.update(self._task_id, description=description, completed=index)

        # Update pending/in_progress counts
        self.stats.pending = max(0, self.stats.total - index - 1 - self.stats.complete - self.stats.failed)
        self.stats.in_progress = 1

    def complete_property(self, success: bool, tier: str | None = None) -> None:
        """Mark current property as complete and update statistics.

        Args:
            success: Whether the property was processed successfully
            tier: Property tier if successful (UNICORN, CONTENDER, PASS)
        """
        if success:
            self.stats.complete += 1
            if tier:
                tier_upper = tier.upper()
                if tier_upper == "UNICORN":
                    self.stats.unicorns += 1
                elif tier_upper == "CONTENDER":
                    self.stats.contenders += 1
                elif tier_upper == "PASS":
                    self.stats.passed += 1
        else:
            self.stats.failed += 1

        self.stats.in_progress = 0

        # Update progress bar
        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=self.stats.complete + self.stats.failed,
            )

    def record_phase_duration(self, duration_seconds: float) -> None:
        """Record phase execution duration for ETA calculation.

        Args:
            duration_seconds: Time taken for the phase
        """
        if duration_seconds > 0:
            self.stats.phase_durations.append(duration_seconds)

    def show_status_table(self) -> None:
        """Display rich status table with current pipeline state."""
        table = Table(title="Pipeline Status", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Properties", str(self.stats.total))
        table.add_row("Pending", str(self.stats.pending))
        table.add_row("In Progress", str(self.stats.in_progress))
        table.add_row("Complete", f"[green]{self.stats.complete}[/green]")
        table.add_row("Failed", f"[red]{self.stats.failed}[/red]" if self.stats.failed else "0")

        # Format elapsed time
        elapsed = self.stats.elapsed
        elapsed_str = str(elapsed).split(".")[0]  # Remove microseconds
        table.add_row("Elapsed Time", elapsed_str)

        # Add ETA if available
        eta = self.stats.eta
        if eta:
            eta_str = str(eta).split(".")[0]  # Remove microseconds
            table.add_row("ETA", eta_str)

        self.console.print(table)

        # Show tier breakdown if we have completed properties
        if self.stats.complete > 0:
            self._show_tier_breakdown()

    def _show_tier_breakdown(self) -> None:
        """Display tier breakdown table."""
        tier_table = Table(title="Tier Breakdown", show_header=True, header_style="bold yellow")
        tier_table.add_column("Tier", style="bold", width=15)
        tier_table.add_column("Count", justify="right", width=10)
        tier_table.add_column("Percentage", justify="right", width=12)

        total_scored = self.stats.unicorns + self.stats.contenders + self.stats.passed

        if total_scored > 0:
            tier_table.add_row(
                "[bold magenta]UNICORN[/bold magenta]",
                str(self.stats.unicorns),
                f"{self.stats.unicorns / total_scored * 100:.1f}%",
            )
            tier_table.add_row(
                "[bold blue]CONTENDER[/bold blue]",
                str(self.stats.contenders),
                f"{self.stats.contenders / total_scored * 100:.1f}%",
            )
            tier_table.add_row(
                "[bold green]PASS[/bold green]",
                str(self.stats.passed),
                f"{self.stats.passed / total_scored * 100:.1f}%",
            )
        else:
            tier_table.add_row("UNICORN", "0", "0%")
            tier_table.add_row("CONTENDER", "0", "0%")
            tier_table.add_row("PASS", "0", "0%")

        self.console.print(tier_table)

    def show_completion_summary(self) -> None:
        """Display final completion summary."""
        self.console.print("\n" + "=" * 70)
        self.console.print("[bold green]PIPELINE EXECUTION COMPLETE[/bold green]")
        self.console.print("=" * 70 + "\n")

        # Show final status
        self.show_status_table()

        # Show success rate
        total_processed = self.stats.complete + self.stats.failed
        if total_processed > 0:
            success_rate = self.stats.complete / total_processed * 100
            self.console.print(f"\n[bold]Success Rate:[/bold] {success_rate:.1f}%")

        # Show top tier counts
        if self.stats.unicorns > 0:
            self.console.print(f"[bold magenta]Found {self.stats.unicorns} UNICORN properties![/bold magenta]")

        self.console.print()

    def print_error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """Print a warning message.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def print_info(self, message: str) -> None:
        """Print an informational message.

        Args:
            message: Info message to display
        """
        self.console.print(f"[cyan]{message}[/cyan]")

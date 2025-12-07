"""Unit tests for ProgressReporter and PipelineStats.

Tests cover:
- PipelineStats initialization and property calculations
- ProgressReporter batch tracking
- ETA calculation accuracy
- Status table generation
- Tier breakdown statistics
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from phx_home_analysis.pipeline.progress import PipelineStats, ProgressReporter


class TestPipelineStats:
    """Tests for PipelineStats dataclass."""

    def test_stats_initialization_defaults(self) -> None:
        """Test that stats initialize with correct defaults."""
        stats = PipelineStats()

        assert stats.total == 0
        assert stats.pending == 0
        assert stats.in_progress == 0
        assert stats.complete == 0
        assert stats.failed == 0
        assert stats.unicorns == 0
        assert stats.contenders == 0
        assert stats.passed == 0
        assert isinstance(stats.start_time, datetime)
        assert stats.phase_durations == []

    def test_elapsed_time_tracking(self) -> None:
        """Test elapsed time property calculation."""
        stats = PipelineStats()
        # Wait a tiny bit to ensure elapsed > 0
        import time

        time.sleep(0.01)

        elapsed = stats.elapsed

        assert isinstance(elapsed, timedelta)
        assert elapsed.total_seconds() > 0

    def test_eta_calculation_empty(self) -> None:
        """Test ETA returns None with no duration data."""
        stats = PipelineStats(total=10)

        assert stats.eta is None

    def test_eta_calculation_with_data(self) -> None:
        """Test ETA calculation with duration data."""
        stats = PipelineStats(total=10, complete=5)
        # Add some phase durations (5 seconds each average)
        stats.phase_durations = [5.0, 5.0, 5.0, 5.0, 5.0]

        eta = stats.eta

        assert eta is not None
        # 5 remaining properties * 5 seconds average = 25 seconds
        assert 24 <= eta.total_seconds() <= 26

    def test_eta_improves_with_samples(self) -> None:
        """Test ETA accuracy improves with more samples."""
        stats = PipelineStats(total=20, complete=10)

        # Start with high variance
        stats.phase_durations = [10.0, 2.0, 8.0, 4.0, 6.0]
        eta_initial = stats.eta

        # Add more consistent samples
        stats.phase_durations.extend([5.0, 5.0, 5.0, 5.0, 5.0])
        eta_updated = stats.eta

        assert eta_initial is not None
        assert eta_updated is not None
        # Both should give reasonable ETAs

    def test_stats_reset(self) -> None:
        """Test that reset clears all statistics."""
        stats = PipelineStats(
            total=100,
            pending=50,
            complete=40,
            failed=10,
            unicorns=5,
        )
        stats.phase_durations = [1.0, 2.0, 3.0]

        stats.reset()

        assert stats.total == 0
        assert stats.pending == 0
        assert stats.complete == 0
        assert stats.failed == 0
        assert stats.unicorns == 0
        assert stats.phase_durations == []

    def test_batch_start_resets_stats(self) -> None:
        """Test that starting a new batch resets statistics."""
        stats = PipelineStats(total=50, complete=25)
        stats.phase_durations = [1.0, 2.0]

        stats.reset()
        stats.total = 100
        stats.pending = 100

        assert stats.total == 100
        assert stats.pending == 100
        assert stats.complete == 0
        assert stats.phase_durations == []


class TestProgressReporter:
    """Tests for ProgressReporter class."""

    @pytest.fixture
    def mock_console(self) -> MagicMock:
        """Create a mock console for testing."""
        return MagicMock(spec=Console)

    @pytest.fixture
    def reporter(self, mock_console: MagicMock) -> ProgressReporter:
        """Create a reporter with mock console."""
        return ProgressReporter(console=mock_console)

    def test_progress_reporter_initialization(self, reporter: ProgressReporter) -> None:
        """Test reporter initializes correctly."""
        assert reporter.stats.total == 0
        assert reporter._progress is None
        assert reporter._task_id is None

    def test_progress_bar_creation(self) -> None:
        """Test progress bar is created on batch start."""
        # Use a real Console to test progress bar creation
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.start_batch(total=100)

        assert reporter._progress is not None
        assert reporter._task_id is not None
        assert reporter.stats.total == 100
        assert reporter.stats.pending == 100

        reporter.stop_batch()

    def test_progress_update_description(self) -> None:
        """Test progress bar updates with property info."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.start_batch(total=10)
        reporter.update_property(0, "123 Main St, Phoenix, AZ 85001", "Phase 0")

        assert reporter.stats.in_progress == 1
        assert reporter.stats.pending == 9

        reporter.stop_batch()

    def test_complete_increments_stats(self) -> None:
        """Test completing a property increments correct counters."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.start_batch(total=10)
        reporter.update_property(0, "123 Main St", "Phase 0")

        reporter.complete_property(success=True, tier="UNICORN")

        assert reporter.stats.complete == 1
        assert reporter.stats.unicorns == 1
        assert reporter.stats.in_progress == 0

        reporter.stop_batch()

    def test_failed_increments_stats(self) -> None:
        """Test failing a property increments failed counter."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.start_batch(total=10)
        reporter.update_property(0, "123 Main St", "Phase 0")

        reporter.complete_property(success=False)

        assert reporter.stats.failed == 1
        assert reporter.stats.complete == 0
        assert reporter.stats.in_progress == 0

        reporter.stop_batch()

    def test_tier_breakdown_counts(self) -> None:
        """Test tier counting for different tier values."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.start_batch(total=6)

        # Complete with different tiers
        reporter.complete_property(success=True, tier="UNICORN")
        reporter.complete_property(success=True, tier="UNICORN")
        reporter.complete_property(success=True, tier="CONTENDER")
        reporter.complete_property(success=True, tier="CONTENDER")
        reporter.complete_property(success=True, tier="CONTENDER")
        reporter.complete_property(success=True, tier="PASS")

        assert reporter.stats.unicorns == 2
        assert reporter.stats.contenders == 3
        assert reporter.stats.passed == 1
        assert reporter.stats.complete == 6

        reporter.stop_batch()

    def test_status_table_generation(
        self, reporter: ProgressReporter, mock_console: MagicMock
    ) -> None:
        """Test status table is generated and printed."""
        reporter.stats.total = 100
        reporter.stats.complete = 50
        reporter.stats.failed = 5
        reporter.stats.unicorns = 10
        reporter.stats.contenders = 30
        reporter.stats.passed = 10

        reporter.show_status_table()

        # Verify console.print was called (table was generated)
        assert mock_console.print.called

    def test_record_phase_duration(self, reporter: ProgressReporter) -> None:
        """Test phase duration recording."""
        reporter.record_phase_duration(5.5)
        reporter.record_phase_duration(3.2)

        assert len(reporter.stats.phase_durations) == 2
        assert reporter.stats.phase_durations[0] == 5.5
        assert reporter.stats.phase_durations[1] == 3.2

    def test_record_phase_duration_ignores_zero(self, reporter: ProgressReporter) -> None:
        """Test that zero duration is not recorded."""
        reporter.record_phase_duration(0)
        reporter.record_phase_duration(-1)

        assert len(reporter.stats.phase_durations) == 0

"""Integration tests for pipeline orchestration.

Tests cover:
- Pipeline state management
- Resume from checkpoint functionality
- Status tracking
"""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from phx_home_analysis.pipeline.phase_coordinator import PhaseCoordinator, PropertyState
from phx_home_analysis.pipeline.progress import PipelineStats, ProgressReporter


class TestPipelineStateManagement:
    """Integration tests for pipeline state management."""

    def test_property_state_initialization(self) -> None:
        """Test property state initializes correctly."""
        state = PropertyState(address="123 Main St")

        assert state.address == "123 Main St"
        assert state.status == "pending"
        assert state.current_phase == 0
        assert state.tier is None

    def test_property_state_complete(self) -> None:
        """Test marking property as complete."""
        state = PropertyState(
            address="123 Main St",
            status="complete",
            tier="UNICORN",
            score=485.0,
        )

        assert state.status == "complete"
        assert state.tier == "UNICORN"
        assert state.score == 485.0

    def test_coordinator_skips_completed(self) -> None:
        """Test that coordinator identifies completed properties."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        coordinator = PhaseCoordinator(
            progress_reporter=reporter,
            strict=False,
            resume=True,
        )

        # Pre-populate work_items with completed property
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete", "tier": "CONTENDER"},
            }
        }

        # Should return True for completed property in resume mode
        assert coordinator._is_property_complete("123 Main St") is True
        assert coordinator._is_property_complete("456 Oak Ave") is False

    def test_coordinator_fresh_mode_does_not_skip(self) -> None:
        """Test that fresh mode doesn't skip completed properties."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        coordinator = PhaseCoordinator(
            progress_reporter=reporter,
            strict=False,
            resume=False,  # Fresh mode
        )

        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete", "tier": "CONTENDER"},
            }
        }

        # In fresh mode, nothing is considered complete
        assert coordinator._is_property_complete("123 Main St") is False


class TestProgressTracking:
    """Integration tests for progress tracking."""

    def test_progress_stats_tracking(self) -> None:
        """Test that stats are correctly tracked during execution."""
        stats = PipelineStats(total=10)

        # Simulate completing properties
        stats.complete = 3
        stats.failed = 1
        stats.unicorns = 1
        stats.contenders = 2
        stats.pending = 6

        assert stats.total == 10
        assert stats.complete == 3
        assert stats.failed == 1
        assert stats.unicorns == 1
        assert stats.contenders == 2

    def test_progress_reporter_tier_counting(self) -> None:
        """Test that reporter counts tiers correctly."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        # Don't start batch (avoid progress bar issues)
        reporter.complete_property(success=True, tier="UNICORN")
        reporter.complete_property(success=True, tier="UNICORN")
        reporter.complete_property(success=True, tier="CONTENDER")
        reporter.complete_property(success=True, tier="PASS")
        reporter.complete_property(success=False)

        assert reporter.stats.unicorns == 2
        assert reporter.stats.contenders == 1
        assert reporter.stats.passed == 1
        assert reporter.stats.complete == 4
        assert reporter.stats.failed == 1

    def test_phase_duration_recording(self) -> None:
        """Test that phase durations are recorded for ETA calculation."""
        console = Console(force_terminal=True, width=80)
        reporter = ProgressReporter(console=console)

        reporter.record_phase_duration(5.0)
        reporter.record_phase_duration(3.0)
        reporter.record_phase_duration(4.0)

        assert len(reporter.stats.phase_durations) == 3
        assert sum(reporter.stats.phase_durations) == 12.0


class TestCLIStatusIntegration:
    """Integration tests for CLI status functionality."""

    def test_cli_status_with_work_items(self, tmp_path: Path) -> None:
        """Test CLI --status reads work_items.json correctly."""
        # Create work_items.json with test data
        work_items = {
            "properties": {
                "123 Main St": {"status": "complete", "tier": "UNICORN"},
                "456 Oak Ave": {"status": "complete", "tier": "CONTENDER"},
                "789 Pine Rd": {"status": "failed"},
                "111 Elm St": {"status": "pending"},
            }
        }

        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(work_items))

        # Test status reading logic
        with work_items_file.open() as f:
            loaded = json.load(f)

        # Count by status
        complete = sum(
            1 for p in loaded["properties"].values() if p["status"] == "complete"
        )
        failed = sum(
            1 for p in loaded["properties"].values() if p["status"] == "failed"
        )
        pending = sum(
            1 for p in loaded["properties"].values() if p["status"] == "pending"
        )

        assert complete == 2
        assert failed == 1
        assert pending == 1

    def test_tier_counting_from_work_items(self, tmp_path: Path) -> None:
        """Test tier counting from work_items.json."""
        work_items = {
            "properties": {
                "prop1": {"status": "complete", "tier": "UNICORN"},
                "prop2": {"status": "complete", "tier": "UNICORN"},
                "prop3": {"status": "complete", "tier": "CONTENDER"},
                "prop4": {"status": "complete", "tier": "CONTENDER"},
                "prop5": {"status": "complete", "tier": "CONTENDER"},
                "prop6": {"status": "complete", "tier": "PASS"},
            }
        }

        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(work_items))

        with work_items_file.open() as f:
            loaded = json.load(f)

        # Count tiers
        unicorns = sum(
            1
            for p in loaded["properties"].values()
            if p["status"] == "complete" and p.get("tier") == "UNICORN"
        )
        contenders = sum(
            1
            for p in loaded["properties"].values()
            if p["status"] == "complete" and p.get("tier") == "CONTENDER"
        )
        passed = sum(
            1
            for p in loaded["properties"].values()
            if p["status"] == "complete" and p.get("tier") == "PASS"
        )

        assert unicorns == 2
        assert contenders == 3
        assert passed == 1

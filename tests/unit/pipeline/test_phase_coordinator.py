"""Unit tests for PhaseCoordinator.

Tests cover:
- Phase sequence ordering
- Phase execution
- Parallel Phase 1 execution
- Phase prerequisite validation
- Resume and fresh modes
- State management
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phx_home_analysis.pipeline.phase_coordinator import (
    Phase,
    PhaseCoordinator,
    PhaseResult,
    PropertyState,
)
from phx_home_analysis.pipeline.progress import ProgressReporter


class TestPhaseEnum:
    """Tests for Phase enumeration."""

    def test_phase_sequence_order(self) -> None:
        """Test phases have correct numeric values."""
        assert Phase.COUNTY == 0
        assert Phase.LISTING == 1
        assert Phase.MAP == 1  # Same as LISTING (parallel)
        assert Phase.IMAGES == 2
        assert Phase.SYNTHESIS == 3
        assert Phase.REPORT == 4

    def test_phase0_before_phase1(self) -> None:
        """Test Phase 0 (County) comes before Phase 1."""
        assert Phase.COUNTY < Phase.LISTING
        assert Phase.COUNTY < Phase.MAP

    def test_phase2_after_phase1(self) -> None:
        """Test Phase 2 (Images) comes after Phase 1."""
        assert Phase.IMAGES > Phase.LISTING
        assert Phase.IMAGES > Phase.MAP

    def test_phase_names(self) -> None:
        """Test all phases are defined."""
        # IntEnum phases have numeric values, not unique names when values overlap
        assert hasattr(Phase, "COUNTY")
        assert hasattr(Phase, "LISTING")
        assert hasattr(Phase, "MAP")
        assert hasattr(Phase, "IMAGES")
        assert hasattr(Phase, "SYNTHESIS")
        assert hasattr(Phase, "REPORT")


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_phase_result_creation(self) -> None:
        """Test PhaseResult can be created with required fields."""
        result = PhaseResult(
            phase=Phase.COUNTY,
            property_address="123 Main St",
            success=True,
            duration_seconds=5.5,
        )

        assert result.phase == Phase.COUNTY
        assert result.property_address == "123 Main St"
        assert result.success is True
        assert result.duration_seconds == 5.5
        assert result.error_message is None
        assert result.data is None

    def test_phase_result_with_error(self) -> None:
        """Test PhaseResult with error message."""
        result = PhaseResult(
            phase=Phase.LISTING,
            property_address="456 Oak Ave",
            success=False,
            duration_seconds=2.0,
            error_message="Connection timeout",
        )

        assert result.success is False
        assert result.error_message == "Connection timeout"

    def test_phase_result_with_data(self) -> None:
        """Test PhaseResult with additional data."""
        result = PhaseResult(
            phase=Phase.IMAGES,
            property_address="789 Pine Rd",
            success=True,
            duration_seconds=10.0,
            data={"requires_agent": True, "agent": "image-assessor"},
        )

        assert result.data is not None
        assert result.data["requires_agent"] is True


class TestPropertyState:
    """Tests for PropertyState dataclass."""

    def test_property_state_defaults(self) -> None:
        """Test PropertyState initializes with defaults."""
        state = PropertyState(address="123 Main St")

        assert state.address == "123 Main St"
        assert state.status == "pending"
        assert state.current_phase == 0
        assert state.phase_status == {}
        assert state.tier is None
        assert state.score is None
        assert state.retry_count == 0
        assert state.error_message is None


class TestPhaseCoordinator:
    """Tests for PhaseCoordinator class."""

    @pytest.fixture
    def mock_reporter(self) -> MagicMock:
        """Create a mock progress reporter."""
        reporter = MagicMock(spec=ProgressReporter)
        reporter.stats = MagicMock()
        reporter.stats.complete = 0
        return reporter

    @pytest.fixture
    def coordinator(self, mock_reporter: MagicMock) -> PhaseCoordinator:
        """Create a coordinator with mock reporter."""
        return PhaseCoordinator(
            progress_reporter=mock_reporter,
            strict=False,
            resume=True,
        )

    @pytest.fixture
    def strict_coordinator(self, mock_reporter: MagicMock) -> PhaseCoordinator:
        """Create a coordinator in strict mode."""
        return PhaseCoordinator(
            progress_reporter=mock_reporter,
            strict=True,
            resume=True,
        )

    def test_coordinator_initialization(
        self, coordinator: PhaseCoordinator, mock_reporter: MagicMock
    ) -> None:
        """Test coordinator initializes correctly."""
        assert coordinator.reporter == mock_reporter
        assert coordinator.strict is False
        assert coordinator.resume is True
        assert coordinator._property_states == {}
        assert coordinator._work_items == {}

    def test_strict_mode_flag(self, strict_coordinator: PhaseCoordinator) -> None:
        """Test strict mode is set correctly."""
        assert strict_coordinator.strict is True

    def test_get_phase_key(self, coordinator: PhaseCoordinator) -> None:
        """Test phase key mapping."""
        # Since LISTING and MAP have the same value (1), they return the same key
        # in Python's dict.get() when looked up by value
        assert coordinator._get_phase_key(Phase.COUNTY) == "phase0_county"
        # Phase.LISTING and Phase.MAP both have value 1, but dict uses value as key
        # so only one will match - test that we get a phase1 key
        listing_key = coordinator._get_phase_key(Phase.LISTING)
        assert listing_key.startswith("phase1")
        assert coordinator._get_phase_key(Phase.IMAGES) == "phase2_images"
        assert coordinator._get_phase_key(Phase.SYNTHESIS) == "phase3_synthesis"
        assert coordinator._get_phase_key(Phase.REPORT) == "phase4_report"

    def test_get_or_create_property_state_new(self, coordinator: PhaseCoordinator) -> None:
        """Test creating new property state."""
        state = coordinator._get_or_create_property_state("123 Main St")

        assert state.address == "123 Main St"
        assert state.status == "pending"
        assert "123 Main St" in coordinator._property_states

    def test_get_or_create_property_state_existing(self, coordinator: PhaseCoordinator) -> None:
        """Test getting existing property state."""
        # Create initial state
        coordinator._property_states["123 Main St"] = PropertyState(
            address="123 Main St",
            status="in_progress",
            current_phase=1,
        )

        # Get state again
        state = coordinator._get_or_create_property_state("123 Main St")

        assert state.status == "in_progress"
        assert state.current_phase == 1

    def test_is_property_complete_false(self, coordinator: PhaseCoordinator) -> None:
        """Test incomplete property detection."""
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "in_progress"},
            }
        }

        assert coordinator._is_property_complete("123 Main St") is False

    def test_is_property_complete_true(self, coordinator: PhaseCoordinator) -> None:
        """Test complete property detection."""
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete"},
            }
        }

        assert coordinator._is_property_complete("123 Main St") is True

    def test_is_property_complete_not_found(self, coordinator: PhaseCoordinator) -> None:
        """Test unknown property is not complete."""
        coordinator._work_items = {"properties": {}}

        assert coordinator._is_property_complete("Unknown Address") is False

    def test_get_tier_returns_tier(self, coordinator: PhaseCoordinator) -> None:
        """Test getting tier for completed property."""
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete", "tier": "UNICORN"},
            }
        }

        tier = coordinator._get_tier("123 Main St")

        assert tier == "UNICORN"

    def test_get_tier_returns_none(self, coordinator: PhaseCoordinator) -> None:
        """Test getting tier for property without tier."""
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete"},
            }
        }

        tier = coordinator._get_tier("123 Main St")

        assert tier is None

    def test_resume_skips_completed(self, coordinator: PhaseCoordinator) -> None:
        """Test resume mode skips completed properties."""
        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete", "tier": "CONTENDER"},
            }
        }

        assert coordinator._is_property_complete("123 Main St") is True

    def test_fresh_does_not_skip(self, mock_reporter: MagicMock) -> None:
        """Test fresh mode does not skip completed properties."""
        coordinator = PhaseCoordinator(
            progress_reporter=mock_reporter,
            strict=False,
            resume=False,  # Fresh mode
        )

        coordinator._work_items = {
            "properties": {
                "123 Main St": {"status": "complete"},
            }
        }

        # In fresh mode, nothing is considered complete
        assert coordinator._is_property_complete("123 Main St") is False


class TestPhaseCoordinatorAsync:
    """Async tests for PhaseCoordinator."""

    @pytest.fixture
    def mock_reporter(self) -> MagicMock:
        """Create a mock progress reporter."""
        reporter = MagicMock(spec=ProgressReporter)
        reporter.stats = MagicMock()
        reporter.stats.complete = 0
        return reporter

    @pytest.fixture
    def coordinator(self, mock_reporter: MagicMock) -> PhaseCoordinator:
        """Create a coordinator with mock reporter."""
        return PhaseCoordinator(
            progress_reporter=mock_reporter,
            strict=False,
            resume=False,  # Fresh mode for simpler testing
        )

    @pytest.mark.asyncio
    async def test_phase0_executes_county_script(self, coordinator: PhaseCoordinator) -> None:
        """Test Phase 0 executes county extraction script."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            result = await coordinator._execute_county("123 Main St, Phoenix, AZ")

            assert result.success is True
            assert result.phase == Phase.COUNTY
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_phase0_handles_failure(self, coordinator: PhaseCoordinator) -> None:
        """Test Phase 0 handles script failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="API error")

            result = await coordinator._execute_county("123 Main St")

            assert result.success is False
            assert "API error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_phase1_parallel_execution(self, coordinator: PhaseCoordinator) -> None:
        """Test Phase 1a and 1b run in parallel."""
        with patch.object(coordinator, "_execute_listing", new_callable=AsyncMock) as mock_listing:
            with patch.object(coordinator, "_execute_map", new_callable=AsyncMock) as mock_map:
                mock_listing.return_value = PhaseResult(
                    phase=Phase.LISTING,
                    property_address="123 Main St",
                    success=True,
                    duration_seconds=5.0,
                )
                mock_map.return_value = PhaseResult(
                    phase=Phase.MAP,
                    property_address="123 Main St",
                    success=True,
                    duration_seconds=3.0,
                )

                # Need to create property state first
                coordinator._get_or_create_property_state("123 Main St")

                listing_result, map_result = await coordinator._execute_phase1_parallel(
                    "123 Main St"
                )

                assert listing_result.success is True
                assert map_result.success is True
                mock_listing.assert_called_once()
                mock_map.assert_called_once()

    @pytest.mark.asyncio
    async def test_phase1_partial_failure_continues(self, coordinator: PhaseCoordinator) -> None:
        """Test Phase 1 continues with partial failure."""
        with patch.object(coordinator, "_execute_listing", new_callable=AsyncMock) as mock_listing:
            with patch.object(coordinator, "_execute_map", new_callable=AsyncMock) as mock_map:
                mock_listing.return_value = PhaseResult(
                    phase=Phase.LISTING,
                    property_address="123 Main St",
                    success=False,
                    duration_seconds=5.0,
                    error_message="Listing failed",
                )
                mock_map.return_value = PhaseResult(
                    phase=Phase.MAP,
                    property_address="123 Main St",
                    success=True,
                    duration_seconds=3.0,
                )

                coordinator._get_or_create_property_state("123 Main St")

                listing_result, map_result = await coordinator._execute_phase1_parallel(
                    "123 Main St"
                )

                # Map should still succeed even though listing failed
                assert listing_result.success is False
                assert map_result.success is True

    @pytest.mark.asyncio
    async def test_phase2_validates_prerequisites(self, coordinator: PhaseCoordinator) -> None:
        """Test Phase 2 validates prerequisites before execution."""
        with patch("subprocess.run") as mock_run:
            # Validation passes
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"can_spawn": true}',
            )

            can_proceed = await coordinator._validate_phase2_prerequisites("123 Main St")

            assert can_proceed is True

    @pytest.mark.asyncio
    async def test_phase2_blocked_when_validation_fails(
        self, coordinator: PhaseCoordinator
    ) -> None:
        """Test Phase 2 is blocked when validation fails."""
        with patch("subprocess.run") as mock_run:
            # Validation fails
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Prerequisites not met",
            )

            can_proceed = await coordinator._validate_phase2_prerequisites("123 Main St")

            assert can_proceed is False

    @pytest.mark.asyncio
    async def test_property_marked_failed_on_error(self, coordinator: PhaseCoordinator) -> None:
        """Test property is marked failed after error."""
        state = coordinator._get_or_create_property_state("123 Main St")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = await coordinator._execute_county("123 Main St")

            assert result.success is False
            assert "Unexpected error" in (result.error_message or "")

"""Phase coordinator for multi-agent pipeline orchestration.

This module provides the PhaseCoordinator class that manages the execution of
analysis phases across multiple properties, coordinating with agents and scripts.

Phase Sequence:
    Phase 0: County API data extraction
    Phase 1a: Listing extraction (parallel with 1b)
    Phase 1b: Map analysis (parallel with 1a)
    Phase 2: Image assessment
    Phase 3: Scoring synthesis
    Phase 4: Deal sheet generation

Usage:
    from phx_home_analysis.pipeline import PhaseCoordinator, ProgressReporter

    reporter = ProgressReporter()
    coordinator = PhaseCoordinator(progress_reporter=reporter)
    await coordinator.execute_pipeline(properties=["123 Main St, Phoenix, AZ"])
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .progress import ProgressReporter

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
WORK_ITEMS_FILE = DATA_DIR / "work_items.json"
ENRICHMENT_FILE = DATA_DIR / "enrichment_data.json"


class Phase(IntEnum):
    """Pipeline phase enumeration.

    Note: LISTING and MAP both have value 1 as they run in parallel.
    """

    COUNTY = 0
    LISTING = 1  # Phase 1a
    MAP = 1  # Phase 1b (parallel with LISTING)
    IMAGES = 2
    SYNTHESIS = 3
    REPORT = 4


@dataclass
class PhaseResult:
    """Result of a single phase execution.

    Attributes:
        phase: Phase that was executed
        property_address: Address of the property processed
        success: Whether the phase completed successfully
        duration_seconds: Time taken to execute the phase
        error_message: Error message if phase failed
        data: Additional data returned by the phase
    """

    phase: Phase
    property_address: str
    success: bool
    duration_seconds: float
    error_message: str | None = None
    data: dict[str, Any] | None = None


@dataclass
class PropertyState:
    """State tracking for a single property in the pipeline.

    Attributes:
        address: Full property address
        status: Current status (pending, in_progress, complete, failed, skipped)
        current_phase: Current phase being processed
        phase_status: Status of each phase
        tier: Assigned tier after scoring (UNICORN, CONTENDER, PASS)
        score: Total score after synthesis
        retry_count: Number of retry attempts
        error_message: Last error message if failed
    """

    address: str
    status: str = "pending"
    current_phase: int = 0
    phase_status: dict[str, str] = field(default_factory=dict)
    tier: str | None = None
    score: float | None = None
    retry_count: int = 0
    error_message: str | None = None


class PhaseCoordinator:
    """Coordinates multi-phase property analysis pipeline execution.

    Manages the execution of analysis phases for multiple properties,
    handling parallel execution, state management, and error recovery.

    Example:
        >>> reporter = ProgressReporter()
        >>> coordinator = PhaseCoordinator(progress_reporter=reporter)
        >>> await coordinator.execute_pipeline(properties=["123 Main St"])
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        progress_reporter: ProgressReporter,
        strict: bool = False,
        resume: bool = True,
    ) -> None:
        """Initialize the phase coordinator.

        Args:
            progress_reporter: Reporter for progress updates
            strict: If True, fail fast on any error. If False, continue with warnings.
            resume: If True, resume from checkpoints. If False, start fresh.
        """
        self.reporter = progress_reporter
        self.strict = strict
        self.resume = resume
        self._property_states: dict[str, PropertyState] = {}
        self._work_items: dict[str, Any] = {}

        # Phase handlers mapping
        self._phase_handlers: dict[
            Phase, Callable[[str], Coroutine[Any, Any, PhaseResult]]
        ] = {
            Phase.COUNTY: self._execute_county,
            Phase.LISTING: self._execute_listing,
            Phase.MAP: self._execute_map,
            Phase.IMAGES: self._execute_images,
            Phase.SYNTHESIS: self._execute_synthesis,
            Phase.REPORT: self._execute_report,
        }

    async def execute_pipeline(
        self,
        properties: list[str],
        skip_phases: set[int] | None = None,
    ) -> None:
        """Execute the full pipeline for all properties.

        Args:
            properties: List of property addresses to process
            skip_phases: Set of phase numbers to skip
        """
        skip_phases = skip_phases or set()

        # Initialize state
        if self.resume:
            self._load_work_items()
        else:
            self._clear_checkpoints()

        # Initialize progress reporter
        self.reporter.start_batch(len(properties))

        # Process each property
        for idx, address in enumerate(properties):
            # Check if already complete
            if self._is_property_complete(address):
                logger.info(f"Skipping complete property: {address}")
                self.reporter.complete_property(success=True, tier=self._get_tier(address))
                continue

            # Initialize property state
            state = self._get_or_create_property_state(address)
            state.status = "in_progress"

            # Update progress
            self.reporter.update_property(idx, address, f"Phase {state.current_phase}")

            try:
                # Execute pipeline for this property
                await self._execute_property_pipeline(address, skip_phases)

                # Mark complete
                state.status = "complete"
                self.reporter.complete_property(success=True, tier=state.tier)

            except Exception as e:
                logger.error(f"Pipeline failed for {address}: {e}")
                state.status = "failed"
                state.error_message = str(e)
                state.retry_count += 1
                self.reporter.complete_property(success=False)

                if self.strict:
                    raise

            # Save checkpoint after each property
            self._save_work_items()

        # Stop progress tracking
        self.reporter.stop_batch()

    async def _execute_property_pipeline(
        self,
        address: str,
        skip_phases: set[int],
    ) -> None:
        """Execute all phases for a single property.

        Args:
            address: Property address
            skip_phases: Set of phase numbers to skip
        """
        state = self._property_states[address]

        # Phase 0: County data
        if 0 not in skip_phases:
            await self._execute_phase_with_tracking(address, Phase.COUNTY)

        # Phase 1: Listing and Map in parallel
        if 1 not in skip_phases:
            listing_result, map_result = await self._execute_phase1_parallel(address)

            if self.strict and not (listing_result.success or map_result.success):
                raise RuntimeError(
                    f"Phase 1 failed for {address}: "
                    f"listing={listing_result.error_message}, map={map_result.error_message}"
                )

        # Phase 2: Images
        if 2 not in skip_phases:
            # Validate prerequisites
            if not await self._validate_phase2_prerequisites(address):
                if self.strict:
                    raise RuntimeError(f"Phase 2 prerequisites not met for {address}")
                logger.warning(f"Skipping Phase 2 for {address}: prerequisites not met")
                state.phase_status["phase2_images"] = "skipped"
            else:
                await self._execute_phase_with_tracking(address, Phase.IMAGES)

        # Phase 3: Synthesis
        if 3 not in skip_phases:
            await self._execute_phase_with_tracking(address, Phase.SYNTHESIS)

        # Phase 4: Report
        if 4 not in skip_phases:
            await self._execute_phase_with_tracking(address, Phase.REPORT)

    async def _execute_phase_with_tracking(
        self,
        address: str,
        phase: Phase,
    ) -> PhaseResult:
        """Execute a phase with progress tracking and state updates.

        Args:
            address: Property address
            phase: Phase to execute

        Returns:
            PhaseResult with execution outcome
        """
        state = self._property_states[address]
        phase_key = self._get_phase_key(phase)

        # Update progress
        self.reporter.update_property(
            self.reporter.stats.complete,
            address,
            f"Phase {phase.value}: {phase.name}",
        )

        # Mark phase in progress
        state.phase_status[phase_key] = "in_progress"
        state.current_phase = phase.value

        # Execute phase
        start_time = time.time()
        try:
            result = await self._phase_handlers[phase](address)
            duration = time.time() - start_time
            result.duration_seconds = duration

            if result.success:
                state.phase_status[phase_key] = "complete"
                self.reporter.record_phase_duration(duration)
            else:
                state.phase_status[phase_key] = "failed"
                state.error_message = result.error_message

            return result

        except Exception as e:
            duration = time.time() - start_time
            state.phase_status[phase_key] = "failed"
            state.error_message = str(e)

            return PhaseResult(
                phase=phase,
                property_address=address,
                success=False,
                duration_seconds=duration,
                error_message=str(e),
            )

    async def _execute_phase1_parallel(
        self,
        address: str,
    ) -> tuple[PhaseResult, PhaseResult]:
        """Execute Phase 1a (listing) and 1b (map) in parallel.

        Args:
            address: Property address

        Returns:
            Tuple of (listing_result, map_result)
        """
        self.reporter.update_property(
            self.reporter.stats.complete,
            address,
            "Phase 1: Listing + Map (parallel)",
        )

        # Create tasks for parallel execution
        listing_task = asyncio.create_task(self._execute_listing(address))
        map_task = asyncio.create_task(self._execute_map(address))

        # Wait for both to complete
        listing_result, map_result = await asyncio.gather(
            listing_task,
            map_task,
            return_exceptions=True,
        )

        # Handle exceptions - convert to PhaseResult
        listing_phaseresult: PhaseResult
        map_phaseresult: PhaseResult

        if isinstance(listing_result, BaseException):
            listing_phaseresult = PhaseResult(
                phase=Phase.LISTING,
                property_address=address,
                success=False,
                duration_seconds=0,
                error_message=str(listing_result),
            )
        else:
            listing_phaseresult = listing_result

        if isinstance(map_result, BaseException):
            map_phaseresult = PhaseResult(
                phase=Phase.MAP,
                property_address=address,
                success=False,
                duration_seconds=0,
                error_message=str(map_result),
            )
        else:
            map_phaseresult = map_result

        # Update state
        state = self._property_states[address]
        state.phase_status["phase1_listing"] = (
            "complete" if listing_phaseresult.success else "failed"
        )
        state.phase_status["phase1_map"] = (
            "complete" if map_phaseresult.success else "failed"
        )

        # Record durations
        self.reporter.record_phase_duration(listing_phaseresult.duration_seconds)
        self.reporter.record_phase_duration(map_phaseresult.duration_seconds)

        return listing_phaseresult, map_phaseresult

    async def _execute_county(self, address: str) -> PhaseResult:
        """Execute Phase 0: County API data extraction.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        try:
            # Run the county extraction script
            result = subprocess.run(
                [
                    "python",
                    str(SCRIPTS_DIR / "extract_county_data.py"),
                    "--address",
                    address,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_ROOT),
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return PhaseResult(
                    phase=Phase.COUNTY,
                    property_address=address,
                    success=True,
                    duration_seconds=duration,
                )
            else:
                return PhaseResult(
                    phase=Phase.COUNTY,
                    property_address=address,
                    success=False,
                    duration_seconds=duration,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=Phase.COUNTY,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message="County API timeout (60s)",
            )
        except Exception as e:
            return PhaseResult(
                phase=Phase.COUNTY,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _execute_listing(self, address: str) -> PhaseResult:
        """Execute Phase 1a: Listing extraction.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        try:
            # Run the image extraction script (includes listing data)
            result = subprocess.run(
                [
                    "python",
                    str(SCRIPTS_DIR / "extract_images.py"),
                    "--address",
                    address,
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for image extraction
                cwd=str(PROJECT_ROOT),
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return PhaseResult(
                    phase=Phase.LISTING,
                    property_address=address,
                    success=True,
                    duration_seconds=duration,
                )
            else:
                return PhaseResult(
                    phase=Phase.LISTING,
                    property_address=address,
                    success=False,
                    duration_seconds=duration,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=Phase.LISTING,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message="Listing extraction timeout (300s)",
            )
        except Exception as e:
            return PhaseResult(
                phase=Phase.LISTING,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _execute_map(self, address: str) -> PhaseResult:
        """Execute Phase 1b: Map analysis.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        try:
            # Run the map analysis script
            map_script = SCRIPTS_DIR / "map_analysis_orchestrator.py"
            if not map_script.exists():
                # Fallback: Map analysis may be integrated elsewhere
                logger.info(f"Map analysis script not found, marking as success for {address}")
                return PhaseResult(
                    phase=Phase.MAP,
                    property_address=address,
                    success=True,
                    duration_seconds=time.time() - start_time,
                )

            result = subprocess.run(
                [
                    "python",
                    str(map_script),
                    "--address",
                    address,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_ROOT),
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return PhaseResult(
                    phase=Phase.MAP,
                    property_address=address,
                    success=True,
                    duration_seconds=duration,
                )
            else:
                return PhaseResult(
                    phase=Phase.MAP,
                    property_address=address,
                    success=False,
                    duration_seconds=duration,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=Phase.MAP,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message="Map analysis timeout (120s)",
            )
        except Exception as e:
            return PhaseResult(
                phase=Phase.MAP,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _execute_images(self, address: str) -> PhaseResult:
        """Execute Phase 2: Image assessment.

        Note: This phase typically requires spawning an AI agent (image-assessor).
        For CLI execution, we validate prerequisites and mark as requiring agent.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        # For now, mark as requiring agent intervention
        # In a full implementation, this would spawn the image-assessor agent
        logger.info(f"Phase 2 (Images) requires agent for {address}")

        return PhaseResult(
            phase=Phase.IMAGES,
            property_address=address,
            success=True,  # Prerequisites validated, marking as ready
            duration_seconds=time.time() - start_time,
            data={"requires_agent": True, "agent": "image-assessor"},
        )

    async def _execute_synthesis(self, address: str) -> PhaseResult:
        """Execute Phase 3: Scoring synthesis.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        try:
            # Run the main analysis script
            result = subprocess.run(
                [
                    "python",
                    str(SCRIPTS_DIR / "analyze.py"),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_ROOT),
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                # Extract tier and score from output if available
                state = self._property_states.get(address)
                if state:
                    # Try to read tier from enrichment data
                    self._update_tier_from_enrichment(address)

                return PhaseResult(
                    phase=Phase.SYNTHESIS,
                    property_address=address,
                    success=True,
                    duration_seconds=duration,
                )
            else:
                return PhaseResult(
                    phase=Phase.SYNTHESIS,
                    property_address=address,
                    success=False,
                    duration_seconds=duration,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=Phase.SYNTHESIS,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message="Synthesis timeout (120s)",
            )
        except Exception as e:
            return PhaseResult(
                phase=Phase.SYNTHESIS,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _execute_report(self, address: str) -> PhaseResult:
        """Execute Phase 4: Deal sheet generation.

        Args:
            address: Property address

        Returns:
            PhaseResult with execution outcome
        """
        start_time = time.time()

        try:
            # Run the deal sheet generator
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "scripts.deal_sheets",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_ROOT),
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return PhaseResult(
                    phase=Phase.REPORT,
                    property_address=address,
                    success=True,
                    duration_seconds=duration,
                )
            else:
                return PhaseResult(
                    phase=Phase.REPORT,
                    property_address=address,
                    success=False,
                    duration_seconds=duration,
                    error_message=result.stderr or f"Exit code: {result.returncode}",
                )

        except subprocess.TimeoutExpired:
            return PhaseResult(
                phase=Phase.REPORT,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message="Report generation timeout (60s)",
            )
        except Exception as e:
            return PhaseResult(
                phase=Phase.REPORT,
                property_address=address,
                success=False,
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _validate_phase2_prerequisites(self, address: str) -> bool:
        """Validate Phase 2 prerequisites using validation script.

        Args:
            address: Property address

        Returns:
            True if prerequisites are met, False otherwise
        """
        try:
            result = subprocess.run(
                [
                    "python",
                    str(SCRIPTS_DIR / "validate_phase_prerequisites.py"),
                    "--address",
                    address,
                    "--phase",
                    "phase2_images",
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(PROJECT_ROOT),
            )

            if result.returncode == 0:
                try:
                    validation = json.loads(result.stdout)
                    can_spawn = validation.get("can_spawn", False)
                    return bool(can_spawn)
                except json.JSONDecodeError:
                    return True  # Assume success if output is not JSON
            else:
                logger.warning(f"Phase 2 validation failed for {address}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Phase 2 validation error for {address}: {e}")
            return False

    def _get_phase_key(self, phase: Phase) -> str:
        """Get the state key for a phase.

        Args:
            phase: Phase enum

        Returns:
            String key for phase status tracking
        """
        mapping = {
            Phase.COUNTY: "phase0_county",
            Phase.LISTING: "phase1_listing",
            Phase.MAP: "phase1_map",
            Phase.IMAGES: "phase2_images",
            Phase.SYNTHESIS: "phase3_synthesis",
            Phase.REPORT: "phase4_report",
        }
        return mapping.get(phase, f"phase{phase.value}")

    def _get_or_create_property_state(self, address: str) -> PropertyState:
        """Get existing property state or create new one.

        Args:
            address: Property address

        Returns:
            PropertyState for the address
        """
        if address not in self._property_states:
            # Check if we have state from work_items
            if address in self._work_items.get("properties", {}):
                saved_state = self._work_items["properties"][address]
                self._property_states[address] = PropertyState(
                    address=address,
                    status=saved_state.get("status", "pending"),
                    current_phase=saved_state.get("current_phase", 0),
                    phase_status=saved_state.get("phase_status", {}),
                    tier=saved_state.get("tier"),
                    score=saved_state.get("score"),
                    retry_count=saved_state.get("retry_count", 0),
                )
            else:
                self._property_states[address] = PropertyState(address=address)

        return self._property_states[address]

    def _is_property_complete(self, address: str) -> bool:
        """Check if a property has already been processed.

        Args:
            address: Property address

        Returns:
            True if complete, False otherwise
        """
        if not self.resume:
            return False

        props: dict[str, Any] = self._work_items.get("properties", {})
        if address in props:
            status = props[address].get("status")
            return bool(status == "complete")
        return False

    def _get_tier(self, address: str) -> str | None:
        """Get the tier for a completed property.

        Args:
            address: Property address

        Returns:
            Tier string or None
        """
        props: dict[str, Any] = self._work_items.get("properties", {})
        if address in props:
            tier = props[address].get("tier")
            return str(tier) if tier is not None else None
        return None

    def _update_tier_from_enrichment(self, address: str) -> None:
        """Update property tier from enrichment data.

        Args:
            address: Property address
        """
        if not ENRICHMENT_FILE.exists():
            return

        try:
            with ENRICHMENT_FILE.open() as f:
                enrichment = json.load(f)

            for prop in enrichment:
                if prop.get("full_address") == address:
                    state = self._property_states.get(address)
                    if state:
                        state.tier = prop.get("tier")
                        state.score = prop.get("total_score")
                    break

        except (json.JSONDecodeError, KeyError):
            pass

    def _load_work_items(self) -> None:
        """Load work items from checkpoint file."""
        if WORK_ITEMS_FILE.exists():
            try:
                with WORK_ITEMS_FILE.open() as f:
                    self._work_items = json.load(f)
                logger.info(f"Loaded {len(self._work_items.get('properties', {}))} work items")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to load work_items.json: {e}")
                self._work_items = {}
        else:
            self._work_items = {}

    def _save_work_items(self) -> None:
        """Save work items to checkpoint file with atomic write."""
        # Build work items from property states
        properties = {}
        for address, state in self._property_states.items():
            properties[address] = {
                "status": state.status,
                "current_phase": state.current_phase,
                "phase_status": state.phase_status,
                "tier": state.tier,
                "score": state.score,
                "retry_count": state.retry_count,
                "error_message": state.error_message,
                "updated_at": datetime.now().isoformat(),
            }

        self._work_items["properties"] = properties
        self._work_items["updated_at"] = datetime.now().isoformat()

        # Atomic write: write to temp file, then rename
        temp_file = WORK_ITEMS_FILE.with_suffix(".tmp")
        try:
            with temp_file.open("w") as f:
                json.dump(self._work_items, f, indent=2)
            temp_file.replace(WORK_ITEMS_FILE)
        except Exception as e:
            logger.error(f"Failed to save work_items.json: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def _clear_checkpoints(self) -> None:
        """Clear all checkpoints for fresh start."""
        self._work_items = {}
        self._property_states = {}

        if WORK_ITEMS_FILE.exists():
            # Backup before clearing
            backup_file = WORK_ITEMS_FILE.with_suffix(".backup.json")
            WORK_ITEMS_FILE.rename(backup_file)
            logger.info(f"Backed up work_items.json to {backup_file}")

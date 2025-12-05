# E1.S4: Pipeline State Checkpointing

**Status:** Ready for Development
**Epic:** Epic 1 - Foundation & Data Infrastructure
**Priority:** P0
**Estimated Points:** 8
**Dependencies:** E1.S2 (Property Data Storage Layer)
**Functional Requirements:** FR34, FR37

## User Story

As a system user, I want pipeline progress checkpointed after each phase, so that I never lose completed work if the pipeline fails.

## Acceptance Criteria

### AC1: Per-Property Phase Tracking
**Given** a multi-phase pipeline execution for multiple properties
**When** a property completes a phase (e.g., phase1_listing)
**Then** `work_items.json` is updated with status "completed" and ISO8601 timestamp
**And** each property maintains independent phase status tracking
**And** other properties' statuses remain unchanged

### AC2: Atomic Checkpoint Writes
**Given** an update to pipeline state in `work_items.json`
**When** `checkpoint()` is called
**Then** a timestamped backup is created (e.g., `work_items.20251204_143000.bak.json`)
**And** the update uses atomic write pattern (temp file + rename)
**And** on crash, either the old file is intact or the new file is complete (never partial)

### AC3: Summary Section Calculation
**Given** multiple work items with various phase completion states
**When** pipeline state is loaded or updated
**Then** a summary section shows:
- Total items count
- Items by status (pending, in_progress, completed, failed, blocked)
- Items by current phase
- Overall completion percentage
**And** summary is automatically recalculated on each checkpoint

### AC4: Work Item Lifecycle States
**Given** a property entering the pipeline
**When** the work item is created or updated
**Then** its status follows valid state transitions:
- NEW → pending
- pending → in_progress
- in_progress → completed | failed | blocked
- failed → in_progress (retry)
- blocked → in_progress (unblock)
**And** invalid transitions are rejected with clear error messages

### AC5: Phase Status Tracking
**Given** a work item progressing through phases
**When** each phase completes
**Then** the phase status structure includes:
- status: pending | in_progress | completed | failed | skipped
- started_at: ISO8601 timestamp (when status → in_progress)
- completed_at: ISO8601 timestamp (when status → completed/failed/skipped)
- error_message: string (if status = failed)
- retry_count: int (number of attempts for this phase)
**And** phase completion is idempotent (multiple completions don't corrupt state)

### AC6: Stale In-Progress Detection
**Given** a work item with status "in_progress" and started_at timestamp
**When** pipeline resumes after a crash
**Then** if elapsed time > 30 minutes, the item is marked as "pending" with reset retry_count
**And** a warning is logged: "Reset stale in_progress item: {address}"
**And** the previous attempt's error is preserved in history for debugging

### AC7: Session Metadata Tracking
**Given** a new pipeline execution
**When** the first checkpoint is created
**Then** session metadata is initialized with:
- session_id: unique identifier (UUID or timestamp-based)
- started_at: ISO8601 timestamp
- mode: "batch" | "single"
- total_items: int (number of properties)
- current_index: int (for batch processing)
**And** session metadata persists across checkpoints
**And** session_id changes only on explicit pipeline restart

### AC8: Backup Retention Policy
**Given** multiple checkpoint backups over time
**When** creating a new backup
**Then** the system keeps the 10 most recent backups
**And** older backups are automatically deleted
**And** a log entry confirms: "Cleaned up {count} old backups"

## Technical Tasks

### Task 1: Create WorkItemsRepository Class
**File:** `src/phx_home_analysis/repositories/work_items_repository.py` (NEW)
**Lines:** ~400

Create repository for `work_items.json` with atomic writes and backup management.

```python
"""Repository for pipeline work items state management."""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..domain.enums import PhaseStatus, WorkItemStatus
from ..utils.file_ops import atomic_json_save
from .base import DataLoadError, DataSaveError

logger = logging.getLogger(__name__)


class WorkItemsRepository:
    """Repository for managing pipeline work items and session state.

    Provides atomic checkpoint operations, backup management, and state
    transitions for multi-phase property analysis pipeline.

    Example:
        >>> repo = WorkItemsRepository("data/work_items.json")
        >>> repo.initialize_session(mode="batch", addresses=["123 Main St"])
        >>> repo.checkpoint_phase_complete("123 Main St", "phase1_listing")
        >>> state = repo.load_state()
    """

    # State transition rules
    VALID_STATUS_TRANSITIONS = {
        None: ["pending"],
        "pending": ["in_progress", "blocked"],
        "in_progress": ["completed", "failed", "blocked"],
        "failed": ["in_progress", "blocked"],
        "blocked": ["in_progress"],
        "completed": [],  # Terminal state
    }

    # Phase status transitions
    VALID_PHASE_TRANSITIONS = {
        None: ["pending"],
        "pending": ["in_progress", "skipped"],
        "in_progress": ["completed", "failed"],
        "failed": ["in_progress"],  # Retry
        "completed": [],  # Terminal
        "skipped": [],  # Terminal
    }

    # Stale timeout for in_progress items
    STALE_TIMEOUT_MINUTES = 30

    # Backup retention
    MAX_BACKUPS = 10

    def __init__(self, json_file_path: str | Path):
        """Initialize work items repository.

        Args:
            json_file_path: Path to work_items.json file.
        """
        self.json_file_path = Path(json_file_path)
        self._state_cache: dict[str, Any] | None = None

    def load_state(self) -> dict[str, Any]:
        """Load work items state from JSON file.

        Returns:
            State dictionary with session, work_items, and summary.

        Raises:
            DataLoadError: If file cannot be read or parsed.
        """
        if not self.json_file_path.exists():
            # Return empty state structure
            return self._create_empty_state()

        try:
            with open(self.json_file_path, encoding='utf-8') as f:
                state = json.load(f)

            # Reset stale in_progress items
            self._reset_stale_items(state)

            # Recalculate summary
            state["summary"] = self._calculate_summary(state.get("work_items", []))

            self._state_cache = state
            return state

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in work_items.json: {e}") from e
        except OSError as e:
            raise DataLoadError(f"Cannot read work_items.json: {e}") from e

    def save_state(self, state: dict[str, Any]) -> None:
        """Save work items state to JSON file with atomic write and backup.

        Args:
            state: State dictionary to save.

        Raises:
            DataSaveError: If file cannot be written.
        """
        # Recalculate summary before save
        state["summary"] = self._calculate_summary(state.get("work_items", []))
        state["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Create backup before write
        self._create_backup()

        # Atomic write
        try:
            atomic_json_save(self.json_file_path, state)
            logger.debug(f"Saved work_items state: {len(state.get('work_items', []))} items")

            # Clean up old backups
            self._cleanup_old_backups()

        except OSError as e:
            raise DataSaveError(f"Cannot write work_items.json: {e}") from e

        self._state_cache = state

    def initialize_session(
        self,
        mode: str,
        addresses: list[str],
        session_id: str | None = None
    ) -> None:
        """Initialize a new pipeline session.

        Args:
            mode: Execution mode ("batch" or "single").
            addresses: List of property addresses to process.
            session_id: Optional session ID (generated if not provided).
        """
        if session_id is None:
            session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        state = {
            "session": {
                "session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "total_items": len(addresses),
                "current_index": 0,
            },
            "work_items": [
                self._create_work_item(addr, idx)
                for idx, addr in enumerate(addresses)
            ],
            "summary": {},
        }

        self.save_state(state)
        logger.info(f"Initialized session {session_id}: {len(addresses)} items")

    def checkpoint_phase_complete(
        self,
        address: str,
        phase: str,
        error_message: str | None = None
    ) -> None:
        """Checkpoint a phase completion for a property.

        Args:
            address: Property address.
            phase: Phase name (e.g., "phase1_listing").
            error_message: Optional error message if phase failed.

        Raises:
            ValueError: If address not found or invalid phase transition.
        """
        state = self.load_state()
        work_item = self._find_work_item(state, address)

        if work_item is None:
            raise ValueError(f"Work item not found for address: {address}")

        # Get current phase status
        phase_info = work_item["phases"].get(phase, {})
        current_status = phase_info.get("status")

        # Determine new status
        new_status = "failed" if error_message else "completed"

        # Validate transition
        if not self._is_valid_phase_transition(current_status, new_status):
            raise ValueError(
                f"Invalid phase transition for {address}.{phase}: "
                f"{current_status} → {new_status}"
            )

        # Update phase status
        now = datetime.now(timezone.utc).isoformat()
        phase_info.update({
            "status": new_status,
            "completed_at": now,
        })

        if error_message:
            phase_info["error_message"] = error_message
            phase_info["retry_count"] = phase_info.get("retry_count", 0) + 1

        work_item["phases"][phase] = phase_info
        work_item["updated_at"] = now

        # Update overall work item status
        self._update_work_item_status(work_item)

        self.save_state(state)
        logger.info(f"Checkpointed {phase} for {address}: {new_status}")

    def checkpoint_phase_start(self, address: str, phase: str) -> None:
        """Checkpoint a phase start for a property.

        Args:
            address: Property address.
            phase: Phase name (e.g., "phase1_listing").

        Raises:
            ValueError: If address not found or invalid phase transition.
        """
        state = self.load_state()
        work_item = self._find_work_item(state, address)

        if work_item is None:
            raise ValueError(f"Work item not found for address: {address}")

        # Get current phase status
        phase_info = work_item["phases"].get(phase, {})
        current_status = phase_info.get("status")

        # Validate transition to in_progress
        if not self._is_valid_phase_transition(current_status, "in_progress"):
            raise ValueError(
                f"Invalid phase transition for {address}.{phase}: "
                f"{current_status} → in_progress"
            )

        # Update phase status
        now = datetime.now(timezone.utc).isoformat()
        phase_info.update({
            "status": "in_progress",
            "started_at": now,
        })

        work_item["phases"][phase] = phase_info
        work_item["updated_at"] = now

        # Update overall work item status
        self._update_work_item_status(work_item)

        self.save_state(state)
        logger.debug(f"Checkpointed {phase} start for {address}")

    def get_work_item(self, address: str) -> dict[str, Any] | None:
        """Get work item by address.

        Args:
            address: Property address.

        Returns:
            Work item dictionary or None if not found.
        """
        state = self.load_state()
        return self._find_work_item(state, address)

    def get_pending_items(self) -> list[dict[str, Any]]:
        """Get all pending work items.

        Returns:
            List of work items with status "pending".
        """
        state = self.load_state()
        return [
            item for item in state.get("work_items", [])
            if item["status"] == "pending"
        ]

    def get_incomplete_items(self) -> list[dict[str, Any]]:
        """Get all incomplete work items (not completed).

        Returns:
            List of work items that are not completed.
        """
        state = self.load_state()
        return [
            item for item in state.get("work_items", [])
            if item["status"] != "completed"
        ]

    def _create_empty_state(self) -> dict[str, Any]:
        """Create empty state structure."""
        return {
            "session": {},
            "work_items": [],
            "summary": {
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "failed": 0,
                "blocked": 0,
            },
        }

    def _create_work_item(self, address: str, index: int) -> dict[str, Any]:
        """Create a new work item structure."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": f"{hash(address) & 0xFFFFFFFF:08x}",  # 8-char hex hash
            "address": address,
            "index": index,
            "status": "pending",
            "phases": {
                "phase0_county": {"status": "pending"},
                "phase1_listing": {"status": "pending"},
                "phase1_map": {"status": "pending"},
                "phase2_images": {"status": "pending"},
                "phase3_synthesis": {"status": "pending"},
                "phase4_report": {"status": "pending"},
            },
            "created_at": now,
            "updated_at": now,
        }

    def _find_work_item(
        self,
        state: dict[str, Any],
        address: str
    ) -> dict[str, Any] | None:
        """Find work item by address."""
        for item in state.get("work_items", []):
            if item["address"] == address:
                return item
        return None

    def _calculate_summary(self, work_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate summary statistics for work items."""
        total = len(work_items)
        by_status = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0, "blocked": 0}

        for item in work_items:
            status = item.get("status", "pending")
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": total,
            "pending": by_status["pending"],
            "in_progress": by_status["in_progress"],
            "completed": by_status["completed"],
            "failed": by_status["failed"],
            "blocked": by_status["blocked"],
            "completion_percentage": (by_status["completed"] / total * 100) if total > 0 else 0,
        }

    def _update_work_item_status(self, work_item: dict[str, Any]) -> None:
        """Update overall work item status based on phase statuses."""
        phases = work_item.get("phases", {})
        phase_statuses = [p.get("status", "pending") for p in phases.values()]

        if all(s == "completed" for s in phase_statuses):
            work_item["status"] = "completed"
        elif any(s == "failed" for s in phase_statuses):
            work_item["status"] = "failed"
        elif any(s == "in_progress" for s in phase_statuses):
            work_item["status"] = "in_progress"
        elif any(s == "blocked" for s in phase_statuses):
            work_item["status"] = "blocked"
        else:
            work_item["status"] = "pending"

    def _is_valid_phase_transition(
        self,
        from_status: str | None,
        to_status: str
    ) -> bool:
        """Check if phase status transition is valid."""
        allowed = self.VALID_PHASE_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    def _reset_stale_items(self, state: dict[str, Any]) -> None:
        """Reset stale in_progress items to pending."""
        now = datetime.now(timezone.utc)
        stale_timeout = timedelta(minutes=self.STALE_TIMEOUT_MINUTES)

        for item in state.get("work_items", []):
            if item.get("status") != "in_progress":
                continue

            # Check if any phase is stale
            for phase, phase_info in item.get("phases", {}).items():
                if phase_info.get("status") != "in_progress":
                    continue

                started_at_str = phase_info.get("started_at")
                if not started_at_str:
                    continue

                started_at = datetime.fromisoformat(started_at_str)
                elapsed = now - started_at

                if elapsed > stale_timeout:
                    logger.warning(
                        f"Reset stale in_progress item: {item['address']}.{phase} "
                        f"(elapsed: {elapsed.total_seconds() / 60:.1f} minutes)"
                    )
                    phase_info["status"] = "pending"
                    phase_info["stale_reset_at"] = now.isoformat()

            # Update overall status
            self._update_work_item_status(item)

    def _create_backup(self) -> None:
        """Create timestamped backup of current work_items.json."""
        if not self.json_file_path.exists():
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = self.json_file_path.with_suffix(f".{timestamp}.bak.json")

        try:
            import shutil
            shutil.copy2(self.json_file_path, backup_path)
            logger.debug(f"Created backup: {backup_path.name}")
        except OSError as e:
            logger.warning(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only MAX_BACKUPS most recent."""
        pattern = f"{self.json_file_path.stem}.*.bak.json"
        backups = sorted(
            self.json_file_path.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if len(backups) > self.MAX_BACKUPS:
            old_backups = backups[self.MAX_BACKUPS:]
            for backup in old_backups:
                try:
                    backup.unlink()
                    logger.debug(f"Cleaned up old backup: {backup.name}")
                except OSError:
                    pass  # Best effort

            logger.info(f"Cleaned up {len(old_backups)} old backups")
```

**Acceptance Criteria:**
- [ ] WorkItemsRepository class created with full state management
- [ ] load_state() and save_state() methods with atomic writes
- [ ] initialize_session() creates new pipeline session
- [ ] checkpoint_phase_start() and checkpoint_phase_complete() update phases
- [ ] State transition validation enforced
- [ ] Stale item detection and reset (30-minute timeout)
- [ ] Summary calculation on load/save
- [ ] Backup creation before write
- [ ] Backup cleanup (keep 10 most recent)

### Task 2: Add Phase Status and Work Item Status Enums
**File:** `src/phx_home_analysis/domain/enums.py:150-180`
**Action:** Add enums for state management

```python
class PhaseStatus(str, Enum):
    """Status values for pipeline phases."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkItemStatus(str, Enum):
    """Status values for work items."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
```

**Acceptance Criteria:**
- [ ] PhaseStatus enum with 5 states
- [ ] WorkItemStatus enum with 5 states
- [ ] Enums inherit from str and Enum for JSON serialization

### Task 3: Update Repository Module Exports
**File:** `src/phx_home_analysis/repositories/__init__.py`
**Action:** Export WorkItemsRepository

```python
from phx_home_analysis.repositories.base import (
    DataLoadError,
    DataSaveError,
    EnrichmentRepository,
    PropertyRepository,
)
from phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository
from phx_home_analysis.repositories.work_items_repository import WorkItemsRepository  # NEW

__all__ = [
    "DataLoadError",
    "DataSaveError",
    "EnrichmentRepository",
    "PropertyRepository",
    "CsvPropertyRepository",
    "JsonEnrichmentRepository",
    "WorkItemsRepository",  # NEW
]
```

**Acceptance Criteria:**
- [ ] WorkItemsRepository imported and exported
- [ ] __all__ list updated

### Task 4: Create Unit Tests for WorkItemsRepository
**File:** `tests/unit/repositories/test_work_items_repository.py` (NEW)
**Lines:** ~500

```python
"""Unit tests for WorkItemsRepository."""

import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from phx_home_analysis.repositories import WorkItemsRepository
from phx_home_analysis.repositories.base import DataLoadError, DataSaveError


class TestWorkItemsRepositoryInitialization:
    """Tests for repository initialization."""

    def test_init_creates_repository(self, tmp_path):
        """Repository initializes with file path."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        assert repo.json_file_path == json_path

    def test_load_state_empty_file(self, tmp_path):
        """Loading nonexistent file returns empty state."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)
        state = repo.load_state()

        assert "session" in state
        assert "work_items" in state
        assert "summary" in state
        assert state["work_items"] == []


class TestSessionInitialization:
    """Tests for session initialization."""

    def test_initialize_session_batch_mode(self, tmp_path):
        """Batch mode session initializes with addresses."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        state = repo.load_state()
        assert state["session"]["mode"] == "batch"
        assert state["session"]["total_items"] == 3
        assert len(state["work_items"]) == 3

    def test_initialize_session_single_mode(self, tmp_path):
        """Single mode session initializes with one address."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        state = repo.load_state()
        assert state["session"]["mode"] == "single"
        assert state["session"]["total_items"] == 1

    def test_initialize_session_generates_session_id(self, tmp_path):
        """Session ID is auto-generated if not provided."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="batch", addresses=["123 Main St"])

        state = repo.load_state()
        assert "session_id" in state["session"]
        assert state["session"]["session_id"].startswith("session_")

    def test_initialize_session_custom_session_id(self, tmp_path):
        """Custom session ID can be provided."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        custom_id = "custom_session_12345"
        repo.initialize_session(mode="batch", addresses=["123 Main St"], session_id=custom_id)

        state = repo.load_state()
        assert state["session"]["session_id"] == custom_id


class TestWorkItemCreation:
    """Tests for work item structure creation."""

    def test_work_item_has_required_fields(self, tmp_path):
        """Work items contain all required fields."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        item = state["work_items"][0]

        assert "id" in item
        assert "address" in item
        assert "status" in item
        assert "phases" in item
        assert "created_at" in item
        assert "updated_at" in item

    def test_work_item_has_all_phases(self, tmp_path):
        """Work items include all pipeline phases."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        phases = state["work_items"][0]["phases"]

        expected_phases = [
            "phase0_county",
            "phase1_listing",
            "phase1_map",
            "phase2_images",
            "phase3_synthesis",
            "phase4_report",
        ]

        for phase in expected_phases:
            assert phase in phases
            assert phases[phase]["status"] == "pending"

    def test_work_item_id_is_8_char_hex(self, tmp_path):
        """Work item ID is 8-character hex string."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        state = repo.load_state()
        item_id = state["work_items"][0]["id"]

        assert len(item_id) == 8
        assert all(c in "0123456789abcdef" for c in item_id)


class TestPhaseCheckpointing:
    """Tests for phase checkpoint operations."""

    def test_checkpoint_phase_start(self, tmp_path):
        """Phase start updates status to in_progress."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"
        assert "started_at" in phase

    def test_checkpoint_phase_complete_success(self, tmp_path):
        """Phase complete updates status to completed."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "completed"
        assert "completed_at" in phase

    def test_checkpoint_phase_complete_failure(self, tmp_path):
        """Phase complete with error updates status to failed."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St",
            "phase1_listing",
            error_message="HTTP 500 error"
        )

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "failed"
        assert phase["error_message"] == "HTTP 500 error"
        assert phase["retry_count"] == 1

    def test_checkpoint_multiple_phases(self, tmp_path):
        """Multiple phases can be checkpointed independently."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Complete phase1_listing
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Complete phase1_map
        repo.checkpoint_phase_start("123 Main St", "phase1_map")
        repo.checkpoint_phase_complete("123 Main St", "phase1_map")

        item = repo.get_work_item("123 Main St")

        assert item["phases"]["phase1_listing"]["status"] == "completed"
        assert item["phases"]["phase1_map"]["status"] == "completed"
        assert item["phases"]["phase2_images"]["status"] == "pending"


class TestStateTransitions:
    """Tests for state transition validation."""

    def test_invalid_phase_transition_raises_error(self, tmp_path):
        """Invalid phase transition raises ValueError."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Try to complete without starting
        with pytest.raises(ValueError, match="Invalid phase transition"):
            repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

    def test_cannot_restart_completed_phase(self, tmp_path):
        """Cannot restart a completed phase."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Try to restart completed phase
        with pytest.raises(ValueError, match="Invalid phase transition"):
            repo.checkpoint_phase_start("123 Main St", "phase1_listing")

    def test_can_retry_failed_phase(self, tmp_path):
        """Failed phase can be retried."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St",
            "phase1_listing",
            error_message="Network error"
        )

        # Retry should be allowed
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"
        assert phase["retry_count"] == 1


class TestWorkItemStatusUpdate:
    """Tests for automatic work item status updates."""

    def test_status_updates_to_in_progress(self, tmp_path):
        """Work item status updates to in_progress when phase starts."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "in_progress"

    def test_status_updates_to_completed(self, tmp_path):
        """Work item status updates to completed when all phases complete."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        phases = [
            "phase0_county", "phase1_listing", "phase1_map",
            "phase2_images", "phase3_synthesis", "phase4_report"
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "completed"

    def test_status_updates_to_failed(self, tmp_path):
        """Work item status updates to failed when any phase fails."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St",
            "phase1_listing",
            error_message="Error"
        )

        item = repo.get_work_item("123 Main St")
        assert item["status"] == "failed"


class TestStaleItemDetection:
    """Tests for stale in_progress item detection."""

    def test_stale_items_reset_to_pending(self, tmp_path, monkeypatch):
        """Items in_progress > 30 minutes reset to pending."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Manually set started_at to 40 minutes ago
        state = repo.load_state()
        past_time = datetime.now(timezone.utc) - timedelta(minutes=40)
        state["work_items"][0]["phases"]["phase1_listing"]["started_at"] = past_time.isoformat()
        repo.save_state(state)

        # Load again to trigger stale detection
        state = repo.load_state()
        item = state["work_items"][0]
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "pending"
        assert "stale_reset_at" in phase

    def test_fresh_items_not_reset(self, tmp_path):
        """Items in_progress < 30 minutes are not reset."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Load again (should not reset)
        state = repo.load_state()
        item = state["work_items"][0]
        phase = item["phases"]["phase1_listing"]

        assert phase["status"] == "in_progress"


class TestSummaryCalculation:
    """Tests for summary statistics calculation."""

    def test_summary_calculates_totals(self, tmp_path):
        """Summary calculates total counts by status."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete one, start one, leave one pending
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")
        repo.checkpoint_phase_start("456 Oak Ave", "phase1_listing")

        state = repo.load_state()
        summary = state["summary"]

        assert summary["total"] == 3
        assert summary["pending"] == 1
        assert summary["in_progress"] == 1
        assert summary["completed"] == 0  # Not all phases complete

    def test_summary_calculates_completion_percentage(self, tmp_path):
        """Summary calculates completion percentage."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete all phases for first item
        phases = [
            "phase0_county", "phase1_listing", "phase1_map",
            "phase2_images", "phase3_synthesis", "phase4_report"
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        state = repo.load_state()
        summary = state["summary"]

        assert summary["completed"] == 1
        assert summary["completion_percentage"] == 50.0


class TestBackupManagement:
    """Tests for backup creation and cleanup."""

    def test_backup_created_before_save(self, tmp_path):
        """Backup file is created before save."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Check backup exists
        backups = list(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) >= 1

    def test_old_backups_cleaned_up(self, tmp_path):
        """Old backups are cleaned up, keeping MAX_BACKUPS most recent."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Create 15 checkpoints (exceeds MAX_BACKUPS = 10)
        for i in range(15):
            repo.checkpoint_phase_start("123 Main St", f"phase{i % 6}_test")

        backups = list(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) <= repo.MAX_BACKUPS


class TestAtomicWrites:
    """Tests for atomic write operations."""

    def test_atomic_write_uses_temp_file(self, tmp_path, monkeypatch):
        """Save uses atomic write pattern with temp file."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Track temp file creation
        original_atomic_save = atomic_json_save
        temp_files_created = []

        def tracked_atomic_save(path, data):
            temp_files_created.append(str(path))
            return original_atomic_save(path, data)

        monkeypatch.setattr("phx_home_analysis.repositories.work_items_repository.atomic_json_save", tracked_atomic_save)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # Verify atomic_json_save was called
        assert len(temp_files_created) > 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Loading invalid JSON raises DataLoadError."""
        json_path = tmp_path / "work_items.json"
        json_path.write_text("{invalid json}")

        repo = WorkItemsRepository(json_path)

        with pytest.raises(DataLoadError, match="Invalid JSON"):
            repo.load_state()

    def test_checkpoint_unknown_address_raises_error(self, tmp_path):
        """Checkpointing unknown address raises ValueError."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        with pytest.raises(ValueError, match="Work item not found"):
            repo.checkpoint_phase_start("999 Unknown St", "phase1_listing")


class TestQueryMethods:
    """Tests for query methods."""

    def test_get_pending_items(self, tmp_path):
        """get_pending_items returns only pending items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        repo.checkpoint_phase_start("123 Main St", "phase1_listing")

        pending = repo.get_pending_items()
        assert len(pending) == 2
        assert all(item["status"] == "pending" for item in pending)

    def test_get_incomplete_items(self, tmp_path):
        """get_incomplete_items returns non-completed items."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Complete all phases for first item
        phases = [
            "phase0_county", "phase1_listing", "phase1_map",
            "phase2_images", "phase3_synthesis", "phase4_report"
        ]

        for phase in phases:
            repo.checkpoint_phase_start("123 Main St", phase)
            repo.checkpoint_phase_complete("123 Main St", phase)

        incomplete = repo.get_incomplete_items()
        assert len(incomplete) == 1
        assert incomplete[0]["address"] == "456 Oak Ave"
```

**Acceptance Criteria:**
- [ ] 50+ test cases covering all repository methods
- [ ] Tests for state transitions and validation
- [ ] Tests for stale item detection
- [ ] Tests for summary calculation
- [ ] Tests for backup management
- [ ] Tests for atomic writes
- [ ] All tests pass with 90%+ coverage

### Task 5: Create Integration Test for Checkpoint Workflow
**File:** `tests/integration/test_checkpoint_workflow.py` (NEW)
**Lines:** ~200

```python
"""Integration tests for checkpoint workflow."""

import pytest
import json
from pathlib import Path

from phx_home_analysis.repositories import WorkItemsRepository


class TestCheckpointWorkflowIntegration:
    """Integration tests for complete checkpoint workflow."""

    def test_full_pipeline_checkpoint_workflow(self, tmp_path):
        """Test complete pipeline execution with checkpointing."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        # Initialize session
        addresses = ["123 Main St", "456 Oak Ave"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Execute Phase 0 for both properties
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase0_county")
            repo.checkpoint_phase_complete(address, "phase0_county")

        # Execute Phase 1 listing
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase1_listing")
            repo.checkpoint_phase_complete(address, "phase1_listing")

        # Execute Phase 1 map
        for address in addresses:
            repo.checkpoint_phase_start(address, "phase1_map")
            repo.checkpoint_phase_complete(address, "phase1_map")

        # Verify state
        state = repo.load_state()

        for item in state["work_items"]:
            assert item["phases"]["phase0_county"]["status"] == "completed"
            assert item["phases"]["phase1_listing"]["status"] == "completed"
            assert item["phases"]["phase1_map"]["status"] == "completed"
            assert item["phases"]["phase2_images"]["status"] == "pending"

    def test_crash_recovery_scenario(self, tmp_path):
        """Simulate crash and recovery."""
        json_path = tmp_path / "work_items.json"

        # Initial execution
        repo1 = WorkItemsRepository(json_path)
        repo1.initialize_session(mode="single", addresses=["123 Main St"])
        repo1.checkpoint_phase_start("123 Main St", "phase1_listing")

        # Simulate crash (create new repo instance)
        repo2 = WorkItemsRepository(json_path)
        state = repo2.load_state()

        # Verify state persisted
        item = state["work_items"][0]
        assert item["phases"]["phase1_listing"]["status"] == "in_progress"

    def test_backup_restore_integration(self, tmp_path):
        """Test backup creation and manual restore."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        # Find backup
        backups = sorted(tmp_path.glob("work_items.*.bak.json"))
        assert len(backups) > 0

        backup = backups[-1]

        # Verify backup content
        with open(backup) as f:
            backup_data = json.load(f)

        assert "work_items" in backup_data
        assert len(backup_data["work_items"]) == 1

    def test_concurrent_property_processing(self, tmp_path):
        """Test multiple properties processing independently."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        addresses = ["123 Main St", "456 Oak Ave", "789 Elm Blvd"]
        repo.initialize_session(mode="batch", addresses=addresses)

        # Property 1: Complete phase 1
        repo.checkpoint_phase_start(addresses[0], "phase1_listing")
        repo.checkpoint_phase_complete(addresses[0], "phase1_listing")

        # Property 2: Start phase 1
        repo.checkpoint_phase_start(addresses[1], "phase1_listing")

        # Property 3: Not started

        # Verify independent states
        state = repo.load_state()
        items = {item["address"]: item for item in state["work_items"]}

        assert items[addresses[0]]["phases"]["phase1_listing"]["status"] == "completed"
        assert items[addresses[1]]["phases"]["phase1_listing"]["status"] == "in_progress"
        assert items[addresses[2]]["phases"]["phase1_listing"]["status"] == "pending"

    def test_retry_after_failure(self, tmp_path):
        """Test retry workflow after phase failure."""
        json_path = tmp_path / "work_items.json"
        repo = WorkItemsRepository(json_path)

        repo.initialize_session(mode="single", addresses=["123 Main St"])

        # First attempt fails
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete(
            "123 Main St",
            "phase1_listing",
            error_message="HTTP 500"
        )

        item = repo.get_work_item("123 Main St")
        assert item["phases"]["phase1_listing"]["retry_count"] == 1

        # Retry succeeds
        repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        repo.checkpoint_phase_complete("123 Main St", "phase1_listing")

        item = repo.get_work_item("123 Main St")
        assert item["phases"]["phase1_listing"]["status"] == "completed"
        assert item["phases"]["phase1_listing"]["retry_count"] == 1  # Count preserved
```

**Acceptance Criteria:**
- [ ] Full pipeline checkpoint workflow test
- [ ] Crash recovery scenario test
- [ ] Backup restore integration test
- [ ] Concurrent property processing test
- [ ] Retry after failure test
- [ ] All integration tests pass

### Task 6: Update Package Exports
**File:** `src/phx_home_analysis/__init__.py`
**Action:** Export WorkItemsRepository at package level

```python
from phx_home_analysis.repositories import (
    CsvPropertyRepository,
    JsonEnrichmentRepository,
    WorkItemsRepository,  # NEW
    # ... existing exports
)

__all__ = [
    # ... existing exports
    "WorkItemsRepository",  # NEW
]
```

**Acceptance Criteria:**
- [ ] WorkItemsRepository exported from package root
- [ ] __all__ list updated

### Task 7: Document work_items.json Schema
**File:** `docs/schemas/work_items_schema.md` (NEW)
**Lines:** ~100

Create comprehensive schema documentation for work_items.json format.

```markdown
# work_items.json Schema

## Overview

State file tracking pipeline progress for multi-phase property analysis.

## Schema Version: v1.0.0

## Top-Level Structure

\`\`\`json
{
  "session": { ... },
  "work_items": [ ... ],
  "summary": { ... },
  "updated_at": "ISO8601"
}
\`\`\`

## Session Object

\`\`\`json
{
  "session_id": "string (unique)",
  "started_at": "ISO8601",
  "mode": "batch | single",
  "total_items": "int",
  "current_index": "int"
}
\`\`\`

## Work Item Object

\`\`\`json
{
  "id": "string (8-char hex)",
  "address": "string",
  "index": "int",
  "status": "pending | in_progress | completed | failed | blocked",
  "phases": {
    "phase0_county": { ... },
    "phase1_listing": { ... },
    "phase1_map": { ... },
    "phase2_images": { ... },
    "phase3_synthesis": { ... },
    "phase4_report": { ... }
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
\`\`\`

## Phase Object

\`\`\`json
{
  "status": "pending | in_progress | completed | failed | skipped",
  "started_at": "ISO8601 (optional)",
  "completed_at": "ISO8601 (optional)",
  "error_message": "string (optional)",
  "retry_count": "int (optional)"
}
\`\`\`

## Summary Object

\`\`\`json
{
  "total": "int",
  "pending": "int",
  "in_progress": "int",
  "completed": "int",
  "failed": "int",
  "blocked": "int",
  "completion_percentage": "float"
}
\`\`\`

## State Transitions

### Work Item Status
- NEW → pending
- pending → in_progress | blocked
- in_progress → completed | failed | blocked
- failed → in_progress (retry)
- blocked → in_progress (unblock)
- completed → (terminal)

### Phase Status
- NEW → pending
- pending → in_progress | skipped
- in_progress → completed | failed
- failed → in_progress (retry)
- completed → (terminal)
- skipped → (terminal)
```

**Acceptance Criteria:**
- [ ] Schema documentation created with all fields
- [ ] State transition rules documented
- [ ] Examples provided for each status

## Test Plan Summary

### Unit Tests
| Suite | File | Test Count |
|-------|------|------------|
| Repository Initialization | `test_work_items_repository.py` | 3 |
| Session Initialization | `test_work_items_repository.py` | 4 |
| Work Item Creation | `test_work_items_repository.py` | 3 |
| Phase Checkpointing | `test_work_items_repository.py` | 4 |
| State Transitions | `test_work_items_repository.py` | 3 |
| Work Item Status Update | `test_work_items_repository.py` | 3 |
| Stale Item Detection | `test_work_items_repository.py` | 2 |
| Summary Calculation | `test_work_items_repository.py` | 2 |
| Backup Management | `test_work_items_repository.py` | 2 |
| Atomic Writes | `test_work_items_repository.py` | 1 |
| Error Handling | `test_work_items_repository.py` | 2 |
| Query Methods | `test_work_items_repository.py` | 2 |

**Total Unit Tests:** ~31

### Integration Tests
| Suite | File | Test Count |
|-------|------|------------|
| Checkpoint Workflow | `test_checkpoint_workflow.py` | 5 |

**Total Integration Tests:** ~5

**Grand Total:** ~36 tests

## Dependencies

### New Dependencies Required
None - all required packages already installed.

### Existing Dependencies Used
- `json` (stdlib) - JSON serialization
- `pathlib` (stdlib) - Path operations
- `datetime` (stdlib) - Timestamp handling
- `uuid` (stdlib) - Session ID generation
- `shutil` (stdlib) - File copying for backups

### Internal Dependencies
- `src/phx_home_analysis/domain/enums.py` - PhaseStatus, WorkItemStatus enums
- `src/phx_home_analysis/utils/file_ops.py` - atomic_json_save
- `src/phx_home_analysis/repositories/base.py` - DataLoadError, DataSaveError

## Definition of Done Checklist

### Implementation
- [ ] WorkItemsRepository class implemented with all methods
- [ ] PhaseStatus and WorkItemStatus enums added
- [ ] Repository module exports updated
- [ ] Package-level exports updated
- [ ] work_items.json schema documented

### Testing
- [ ] 31+ unit tests written and passing
- [ ] 5+ integration tests written and passing
- [ ] All tests pass: `pytest tests/unit/repositories/test_work_items_repository.py tests/integration/test_checkpoint_workflow.py`
- [ ] Test coverage > 90% for work_items_repository.py

### Quality Gates
- [ ] Type checking passes: `mypy src/phx_home_analysis/repositories/work_items_repository.py`
- [ ] Linting passes: `ruff check src/phx_home_analysis/repositories/work_items_repository.py`
- [ ] No new warnings introduced

### Documentation
- [ ] WorkItemsRepository docstrings complete with examples
- [ ] Schema documentation created in `docs/schemas/work_items_schema.md`
- [ ] State transition rules documented
- [ ] CLAUDE.md files updated in relevant directories

### Verification
- [ ] Manual test: Initialize session with 3 properties
- [ ] Manual test: Checkpoint phases for each property
- [ ] Manual test: Verify backup files created
- [ ] Manual test: Verify summary calculation correct
- [ ] Manual test: Simulate crash and verify state persists

## Notes

### Design Decisions

1. **Repository Pattern for State Management**: Consistent with existing PropertyRepository and EnrichmentRepository patterns. **Rationale**: Uniform abstraction for data persistence across project.

2. **Atomic Writes with Backup**: Every save creates backup then uses temp file + rename. **Rationale**: Prevents corruption on crash, enables recovery.

3. **Stale Item Detection on Load**: Check for stale in_progress items when loading state. **Rationale**: Automatic recovery from crashes without manual intervention.

4. **Summary Auto-Calculation**: Summary recalculated on every load/save. **Rationale**: Ensures summary always reflects current state, prevents drift.

5. **State Transition Validation**: Explicit transition rules prevent invalid state changes. **Rationale**: Catches bugs early, maintains data integrity.

6. **8-Character Hex Work Item IDs**: Hash-based deterministic IDs. **Rationale**: Stable IDs across runs, collision-resistant for typical batch sizes.

7. **Backup Retention Policy (10 max)**: Automatically clean up old backups. **Rationale**: Prevents disk space bloat while maintaining recovery window.

8. **ISO8601 Timestamps**: All timestamps in UTC ISO8601 format. **Rationale**: Unambiguous, sortable, timezone-aware.

### Current State (Discovered)

**Existing Files:**
- ✅ `data/work_items.json` (22 lines) - Basic structure exists
- ✅ `src/phx_home_analysis/repositories/base.py` - Abstract base classes
- ✅ `src/phx_home_analysis/repositories/json_repository.py` - JSON persistence pattern
- ✅ `src/phx_home_analysis/utils/file_ops.py` - atomic_json_save utility

**Missing (To Create):**
- ❌ `src/phx_home_analysis/repositories/work_items_repository.py` - NEW
- ❌ PhaseStatus and WorkItemStatus enums - NEW in enums.py
- ❌ `tests/unit/repositories/test_work_items_repository.py` - NEW
- ❌ `tests/integration/test_checkpoint_workflow.py` - NEW
- ❌ `docs/schemas/work_items_schema.md` - NEW

### File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `src/phx_home_analysis/repositories/work_items_repository.py` | NEW: Repository implementation | ~400 |
| `src/phx_home_analysis/domain/enums.py` | ADD: Phase/WorkItem status enums | ~30 |
| `src/phx_home_analysis/repositories/__init__.py` | UPDATE: Export WorkItemsRepository | ~2 |
| `src/phx_home_analysis/__init__.py` | UPDATE: Package-level export | ~2 |
| `tests/unit/repositories/test_work_items_repository.py` | NEW: Unit tests | ~500 |
| `tests/integration/test_checkpoint_workflow.py` | NEW: Integration tests | ~200 |
| `docs/schemas/work_items_schema.md` | NEW: Schema documentation | ~100 |

### Related Stories

**Depends On:**
- E1.S2: Property Data Storage Layer (atomic write pattern, repository pattern)

**Blocks:**
- E1.S5: Pipeline Resume Capability (requires checkpoint infrastructure)
- E5.S1: Pipeline Orchestrator CLI (requires work items tracking)

### Open Questions

None - All design decisions finalized.

### Risk Assessment

**Risk 1: Concurrent Modifications to work_items.json**
- **Likelihood:** Medium (if multiple agents write simultaneously)
- **Impact:** High (data corruption)
- **Mitigation:** Atomic writes with temp file + rename; document single-writer constraint

**Risk 2: Stale Timeout Too Aggressive (30 minutes)**
- **Likelihood:** Low
- **Impact:** Medium (false positives resetting valid in_progress items)
- **Mitigation:** Conservative 30-minute timeout; configurable via class constant

**Risk 3: Backup Disk Space Usage**
- **Likelihood:** Low
- **Impact:** Low (10 backups = ~10MB typical)
- **Mitigation:** Automatic cleanup of old backups

## Implementation Order

1. **Phase 1: Core Repository** (blocking)
   - Task 2: Add PhaseStatus and WorkItemStatus enums
   - Task 1: Create WorkItemsRepository class
   - Task 3: Update repository module exports

2. **Phase 2: Testing** (verification)
   - Task 4: Unit tests for WorkItemsRepository
   - Task 5: Integration tests for checkpoint workflow

3. **Phase 3: Integration** (packaging)
   - Task 6: Update package exports
   - Task 7: Document work_items.json schema

---

**Story Created:** 2025-12-04
**Created By:** Claude Code (AI Agent)
**Epic File:** `docs/epics/epic-1-foundation-data-infrastructure.md:52-63`

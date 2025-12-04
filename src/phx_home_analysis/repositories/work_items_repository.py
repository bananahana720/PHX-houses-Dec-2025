"""Repository for pipeline work items state management."""

import json
import logging
import shutil
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
        >>> repo.checkpoint_phase_start("123 Main St", "phase1_listing")
        >>> repo.checkpoint_phase_complete("123 Main St", "phase1_listing")
        >>> state = repo.load_state()
    """

    # State transition rules
    VALID_STATUS_TRANSITIONS = {
        None: [WorkItemStatus.PENDING.value],
        WorkItemStatus.PENDING.value: [WorkItemStatus.IN_PROGRESS.value, WorkItemStatus.BLOCKED.value],
        WorkItemStatus.IN_PROGRESS.value: [WorkItemStatus.COMPLETED.value, WorkItemStatus.FAILED.value, WorkItemStatus.BLOCKED.value],
        WorkItemStatus.FAILED.value: [WorkItemStatus.IN_PROGRESS.value, WorkItemStatus.BLOCKED.value],
        WorkItemStatus.BLOCKED.value: [WorkItemStatus.IN_PROGRESS.value],
        WorkItemStatus.COMPLETED.value: [],  # Terminal state
    }

    # Phase status transitions
    VALID_PHASE_TRANSITIONS = {
        None: [PhaseStatus.PENDING.value],
        PhaseStatus.PENDING.value: [PhaseStatus.IN_PROGRESS.value, PhaseStatus.SKIPPED.value],
        PhaseStatus.IN_PROGRESS.value: [PhaseStatus.COMPLETED.value, PhaseStatus.FAILED.value],
        PhaseStatus.FAILED.value: [PhaseStatus.IN_PROGRESS.value],  # Retry
        PhaseStatus.COMPLETED.value: [],  # Terminal
        PhaseStatus.SKIPPED.value: [],  # Terminal
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
                state: dict[str, Any] = json.load(f)

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
        new_status = PhaseStatus.FAILED.value if error_message else PhaseStatus.COMPLETED.value

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
        if not self._is_valid_phase_transition(current_status, PhaseStatus.IN_PROGRESS.value):
            raise ValueError(
                f"Invalid phase transition for {address}.{phase}: "
                f"{current_status} → {PhaseStatus.IN_PROGRESS.value}"
            )

        # Update phase status
        now = datetime.now(timezone.utc).isoformat()
        phase_info.update({
            "status": PhaseStatus.IN_PROGRESS.value,
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
            if item["status"] == WorkItemStatus.PENDING.value
        ]

    def get_incomplete_items(self) -> list[dict[str, Any]]:
        """Get all incomplete work items (not completed).

        Returns:
            List of work items that are not completed.
        """
        state = self.load_state()
        return [
            item for item in state.get("work_items", [])
            if item["status"] != WorkItemStatus.COMPLETED.value
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
            "status": WorkItemStatus.PENDING.value,
            "phases": {
                "phase0_county": {"status": PhaseStatus.PENDING.value},
                "phase1_listing": {"status": PhaseStatus.PENDING.value},
                "phase1_map": {"status": PhaseStatus.PENDING.value},
                "phase2_images": {"status": PhaseStatus.PENDING.value},
                "phase3_synthesis": {"status": PhaseStatus.PENDING.value},
                "phase4_report": {"status": PhaseStatus.PENDING.value},
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
        work_items: list[dict[str, Any]] = state.get("work_items", [])
        for item in work_items:
            if item["address"] == address:
                return item
        return None

    def _calculate_summary(self, work_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate summary statistics for work items."""
        total = len(work_items)
        by_status = {
            WorkItemStatus.PENDING.value: 0,
            WorkItemStatus.IN_PROGRESS.value: 0,
            WorkItemStatus.COMPLETED.value: 0,
            WorkItemStatus.FAILED.value: 0,
            WorkItemStatus.BLOCKED.value: 0
        }

        for item in work_items:
            status = item.get("status", WorkItemStatus.PENDING.value)
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": total,
            "pending": by_status[WorkItemStatus.PENDING.value],
            "in_progress": by_status[WorkItemStatus.IN_PROGRESS.value],
            "completed": by_status[WorkItemStatus.COMPLETED.value],
            "failed": by_status[WorkItemStatus.FAILED.value],
            "blocked": by_status[WorkItemStatus.BLOCKED.value],
            "completion_percentage": (by_status[WorkItemStatus.COMPLETED.value] / total * 100) if total > 0 else 0.0,
        }

    def _update_work_item_status(self, work_item: dict[str, Any]) -> None:
        """Update overall work item status based on phase statuses.

        Status Logic:
        - completed: ALL phases completed
        - failed: ANY phase failed
        - in_progress: ANY phase actively in_progress
        - blocked: ANY phase blocked (and none in_progress)
        - pending: All other cases (all pending, or mix of completed/pending with none active)
        """
        phases = work_item.get("phases", {})
        phase_statuses = [p.get("status", PhaseStatus.PENDING.value) for p in phases.values()]

        # All phases completed -> completed
        if all(s == PhaseStatus.COMPLETED.value for s in phase_statuses):
            work_item["status"] = WorkItemStatus.COMPLETED.value
        # Any phase failed -> failed
        elif any(s == PhaseStatus.FAILED.value for s in phase_statuses):
            work_item["status"] = WorkItemStatus.FAILED.value
        # Any phase actively in_progress -> in_progress
        elif any(s == PhaseStatus.IN_PROGRESS.value for s in phase_statuses):
            work_item["status"] = WorkItemStatus.IN_PROGRESS.value
        # Any phase blocked -> blocked
        elif any(s == WorkItemStatus.BLOCKED.value for s in phase_statuses):
            work_item["status"] = WorkItemStatus.BLOCKED.value
        # All other cases (all pending, or partial completion) -> pending
        else:
            work_item["status"] = WorkItemStatus.PENDING.value

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
            if item.get("status") != WorkItemStatus.IN_PROGRESS.value:
                continue

            # Check if any phase is stale
            for phase, phase_info in item.get("phases", {}).items():
                if phase_info.get("status") != PhaseStatus.IN_PROGRESS.value:
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
                    phase_info["status"] = PhaseStatus.PENDING.value
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

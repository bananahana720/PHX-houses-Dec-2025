"""Pipeline resume capability with crash recovery.

Provides ResumePipeline class that:
- Loads state from WorkItemsRepository
- Resets stale in_progress items
- Validates state consistency
- Coordinates with PhaseCoordinator for execution

Example:
    >>> from phx_home_analysis.repositories import WorkItemsRepository
    >>> repo = WorkItemsRepository("data/work_items.json")
    >>> resumer = ResumePipeline(repo)
    >>> if resumer.can_resume():
    ...     pending = resumer.get_pending_addresses()
    ...     # Process pending addresses
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..repositories import WorkItemsRepository

from ..repositories.base import DataLoadError

logger = logging.getLogger(__name__)


class StateValidationError(Exception):
    """Raised when work_items.json validation fails.

    Provides detailed error information and suggestions for recovery.

    Attributes:
        message: Human-readable error description.
        details: Dictionary with additional context (e.g., field names, expected values).
        suggestion: Actionable recommendation for resolving the error.

    Example:
        >>> try:
        ...     resumer.load_and_validate()
        ... except StateValidationError as e:
        ...     print(f"Error: {e}")
        ...     print(f"Suggestion: {e.suggestion}")
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Initialize StateValidationError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional context.
            suggestion: Optional actionable recommendation for resolving the error.
        """
        super().__init__(message)
        self.details = details or {}
        self.suggestion = suggestion


class ResumePipeline:
    """Manages pipeline resume from checkpointed state.

    Handles loading saved state, resetting stale items, and coordinating
    with PhaseCoordinator for continued execution.

    The resume pipeline provides crash recovery by:
    1. Loading existing state from work_items.json
    2. Resetting items stuck in 'in_progress' for too long (>30 minutes)
    3. Validating state schema and session consistency
    4. Providing lists of pending/completed addresses

    Example:
        >>> repo = WorkItemsRepository("data/work_items.json")
        >>> resumer = ResumePipeline(repo)
        >>> if resumer.can_resume():
        ...     state = resumer.load_and_validate()
        ...     reset = resumer.reset_stale_items()
        ...     pending = resumer.get_pending_addresses()
        ...     pipeline.run(addresses=pending)
    """

    # Configuration
    STALE_TIMEOUT_MINUTES = 30
    MAX_RETRIES = 3
    CURRENT_SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        work_items_repo: WorkItemsRepository,
        fresh: bool = False,
    ) -> None:
        """Initialize resume pipeline handler.

        Args:
            work_items_repo: Repository for work items state.
            fresh: If True, ignore existing state and start fresh.
        """
        self.repo = work_items_repo
        self.fresh = fresh
        self._state: dict[str, Any] | None = None

    def can_resume(self) -> bool:
        """Check if resume is possible.

        Returns True if:
        - fresh flag is not set
        - Valid state file exists with a session_id

        Returns:
            True if valid state exists and can be resumed.
        """
        if self.fresh:
            logger.debug("Resume disabled: fresh flag is set")
            return False

        try:
            state = self.repo.load_state()
            return bool(state.get("session", {}).get("session_id"))
        except DataLoadError:
            return False

    def load_and_validate(self) -> dict[str, Any]:
        """Load and validate state from repository.

        Performs validation:
        1. JSON parsing (via repository)
        2. Schema version compatibility
        3. Required fields presence (session, work_items)

        Returns:
            Validated state dictionary.

        Raises:
            StateValidationError: If state is invalid with details and suggestion.
        """
        try:
            state = self.repo.load_state()
        except DataLoadError as e:
            raise StateValidationError(
                message=f"State file corrupted: {e}",
                suggestion="Run with --fresh to start over",
            ) from e

        # Validate schema version
        version = state.get("session", {}).get("schema_version", "1.0.0")
        if not self._is_compatible_version(version):
            raise StateValidationError(
                message=f"State file version mismatch: expected {self.CURRENT_SCHEMA_VERSION}, found {version}",
                details={"expected": self.CURRENT_SCHEMA_VERSION, "found": version},
                suggestion="Run with --fresh to start over or migrate state manually",
            )

        # Validate required fields
        required = ["session", "work_items"]
        for field in required:
            if field not in state:
                raise StateValidationError(
                    message=f"State file invalid: missing required field '{field}'",
                    details={"missing": field},
                    suggestion="Run with --fresh to start over",
                )

        self._state = state
        return state

    def reset_stale_items(self) -> list[str]:
        """Reset items stuck in in_progress for too long.

        Items with phases stuck in 'in_progress' status for more than
        STALE_TIMEOUT_MINUTES (30 minutes) are reset to 'pending'.
        Previous error messages are preserved in phase history.

        Note:
            This method modifies the internal state but does NOT persist changes.
            Caller must call `repo.save_state(self._state)` after this method
            if persistence is required.

        Returns:
            List of addresses that were reset.
        """
        if not self._state:
            return []

        reset_addresses = []
        now = datetime.now(timezone.utc)

        for item in self._state.get("work_items", []):
            if item.get("status") != "in_progress":
                continue

            # Check each phase
            for _phase_key, phase_info in item.get("phases", {}).items():
                if phase_info.get("status") != "in_progress":
                    continue

                started_at_str = phase_info.get("started_at")
                if not started_at_str:
                    continue

                started_at = datetime.fromisoformat(started_at_str)
                elapsed_minutes = (now - started_at).total_seconds() / 60

                if elapsed_minutes > self.STALE_TIMEOUT_MINUTES:
                    logger.warning(
                        f"Reset stale in_progress item: {item['address']} "
                        f"(elapsed: {elapsed_minutes:.1f}m)"
                    )
                    phase_info["status"] = "pending"
                    phase_info["stale_reset_at"] = now.isoformat()
                    # Preserve error for debugging
                    if phase_info.get("error_message"):
                        phase_info["previous_error"] = phase_info.pop("error_message")
                    reset_addresses.append(item["address"])

            # Update overall status if any phase was reset
            if item["address"] in reset_addresses:
                item["status"] = "pending"

        return reset_addresses

    def get_pending_addresses(self) -> list[str]:
        """Get list of addresses that need processing.

        Returns addresses that:
        - Have status 'pending'
        - Have status 'failed' with retry_count < MAX_RETRIES

        Returns:
            List of property addresses to process.
        """
        if not self._state:
            return []

        pending = []
        for item in self._state.get("work_items", []):
            status = item.get("status", "pending")
            retry_count = item.get("retry_count", 0)

            if status == "pending":
                pending.append(item["address"])
            elif status == "failed" and retry_count < self.MAX_RETRIES:
                pending.append(item["address"])

        return pending

    def get_completed_addresses(self) -> list[str]:
        """Get list of addresses already completed.

        Returns:
            List of completed property addresses.
        """
        if not self._state:
            return []

        return [
            item["address"]
            for item in self._state.get("work_items", [])
            if item.get("status") == "completed"
        ]

    def get_resume_summary(self) -> dict[str, Any]:
        """Get summary of resume state.

        Returns:
            Dictionary with resume statistics including:
            - session_id: Current session identifier
            - started_at: Session start timestamp
            - total_items: Total number of work items
            - pending: Count of pending items
            - completed: Count of completed items
            - failed: Count of failed items
            - blocked: Count of blocked items
        """
        if not self._state:
            return {}

        summary = self._state.get("summary", {})
        session = self._state.get("session", {})

        return {
            "session_id": session.get("session_id"),
            "started_at": session.get("started_at"),
            "total_items": summary.get("total", 0),
            "pending": summary.get("pending", 0),
            "completed": summary.get("completed", 0),
            "failed": summary.get("failed", 0),
            "blocked": summary.get("blocked", 0),
        }

    def prepare_fresh_start(self, addresses: list[str]) -> str | None:
        """Prepare for fresh start by backing up existing state.

        Creates a timestamped backup of the current state file before
        initializing a new session with the provided addresses.

        Args:
            addresses: New list of addresses to process.

        Returns:
            Path to backup file if backup was created, None otherwise.
        """
        backup_path = None

        # Backup existing state if it exists
        if self.repo.json_file_path.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = self.repo.json_file_path.with_suffix(f".{timestamp}.backup.json")
            shutil.copy2(self.repo.json_file_path, backup_path)
            logger.info(f"Fresh start: backed up previous state to {backup_path}")

            # Warn about data loss
            try:
                old_state = self.repo.load_state()
                completed = len(
                    [i for i in old_state.get("work_items", []) if i.get("status") == "completed"]
                )
                if completed > 0:
                    logger.warning(
                        f"Previous session had {completed} completed items that will be re-processed"
                    )
            except DataLoadError:
                pass

        # Initialize new session
        self.repo.initialize_session(mode="batch", addresses=addresses)

        return str(backup_path) if backup_path else None

    def estimate_data_loss(self) -> int:
        """Estimate items that would be lost on fresh start.

        Calculates the number of completed items that would need to be
        re-processed if a fresh start is performed.

        Returns:
            Number of completed items that would be re-processed.
        """
        try:
            state = self.repo.load_state()
            return len([i for i in state.get("work_items", []) if i.get("status") == "completed"])
        except DataLoadError:
            return 0

    def _is_compatible_version(self, version: str) -> bool:
        """Check if schema version is compatible.

        Currently accepts all 1.x versions as compatible.
        Logs when version differs from current for migration awareness.

        Args:
            version: Version string to check.

        Returns:
            True if version is compatible.
        """
        if not version.startswith("1."):
            return False
        current_version = "1.0"
        if version != current_version and version != f"{current_version}.0":
            logger.info(f"State version {version} is compatible with {current_version}")
        return True

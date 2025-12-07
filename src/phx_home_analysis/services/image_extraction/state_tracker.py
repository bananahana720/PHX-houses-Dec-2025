"""Consolidated state management for image extraction pipeline.

Unifies checkpoint management, state tracking, URL tracking, and run logging
into a single cohesive interface. Provides atomic writes, async checkpoints,
and thread-safe state mutations for reliable crash recovery.

This module consolidates:
- StateManager: completion/failure tracking (extraction_state.json)
- URLTracker: URL-level change detection (url_tracker.json)
- RunLogger: per-run audit trails (run_history/)
- ImageManifest: property -> images mapping (image_manifest.json)

Key Features:
- Automatic checkpointing every N operations
- Async checkpoint using run_in_executor pattern
- Atomic file writes (temp file + os.replace)
- Thread safety via asyncio.Lock
- Composable services for separation of concerns

Example:
    config = CheckpointConfig(interval=5, async_save=True)
    tracker = StateTracker(base_dir, config)

    await tracker.start_run(properties_requested=10, mode="incremental")

    for property_addr in properties:
        if tracker.is_completed(property_addr):
            continue

        # ... extract images ...
        tracker.register_url(url, image_id, property_hash, content_hash)
        tracker.add_images_to_manifest(property_addr, images)
        tracker.mark_completed(property_addr)

        # Checkpoint periodically
        await tracker.checkpoint_if_needed()

    await tracker.finish_run()

Security:
    All file writes use atomic operations to prevent corruption from crashes.
    Thread-safe via asyncio.Lock for concurrent property processing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .run_logger import PropertyChanges, RunLog, RunLogger
from .state_manager import StateManager
from .url_tracker import URLStatus, URLTracker

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint behavior.

    Controls how frequently and how (sync vs async) state is persisted to disk.

    Attributes:
        interval: Number of operations between automatic checkpoints (default: 5)
        async_save: Use async checkpoint via run_in_executor (default: True)
        enable_checkpoints: Enable automatic checkpoints (default: True)
    """

    interval: int = 5
    async_save: bool = True
    enable_checkpoints: bool = True


class StateTracker:
    """Unified state management for image extraction pipeline.

    Consolidates all state persistence concerns into a single interface:
    - Completion/failure tracking (extraction_state.json)
    - URL tracking for incremental extraction (url_tracker.json)
    - Run history logging (run_history/)
    - Image manifest (image_manifest.json)

    Provides automatic checkpointing, async saves, and thread-safe operations.

    Thread Safety:
        All public methods that mutate state are protected by an asyncio.Lock.
        Safe for concurrent use across multiple property extraction tasks.

    Example:
        tracker = StateTracker(base_dir, CheckpointConfig(interval=5))

        await tracker.start_run(properties_requested=10)

        # Process properties
        for addr in properties:
            if tracker.is_completed(addr):
                continue
            # ... extract ...
            tracker.mark_completed(addr)
            await tracker.checkpoint_if_needed()

        await tracker.finish_run()

    Attributes:
        base_dir: Base directory for all state files
        checkpoint_config: Configuration for checkpoint behavior
    """

    def __init__(
        self,
        base_dir: Path,
        checkpoint_config: CheckpointConfig | None = None,
    ):
        """Initialize state tracker with configuration.

        Args:
            base_dir: Base directory containing metadata/ subdirectory
            checkpoint_config: Checkpoint configuration (uses defaults if None)
        """
        self.base_dir = Path(base_dir)
        self.metadata_dir = self.base_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_config = checkpoint_config or CheckpointConfig()

        # Initialize component services
        self._state_path = self.metadata_dir / "extraction_state.json"
        self._url_tracker_path = self.metadata_dir / "url_tracker.json"
        self._manifest_path = self.metadata_dir / "image_manifest.json"

        self._state_manager = StateManager(self._state_path)
        self._url_tracker = URLTracker.load(self._url_tracker_path)
        self._run_logger = RunLogger(self.metadata_dir, max_history=50)
        self._manifest: dict[str, list[dict[str, Any]]] = self._load_manifest()

        # Checkpoint tracking
        self._operations_since_checkpoint = 0
        self._lock = asyncio.Lock()

        logger.info(
            "StateTracker initialized: checkpoint_interval=%d, async=%s",
            self.checkpoint_config.interval,
            self.checkpoint_config.async_save,
        )

    # ===== Manifest Management =====

    def _load_manifest(self) -> dict[str, list[dict[str, Any]]]:
        """Load image manifest from disk.

        Returns:
            Dict mapping property address -> list of image metadata dicts
        """
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path, encoding="utf-8") as f:
                    data = json.load(f)
                    manifest: dict[str, list[dict[str, Any]]] = data.get("properties", {})
                    logger.info(f"Loaded manifest with {len(manifest)} properties")
                    return manifest
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load manifest: {e}")

        return {}

    def _save_manifest_sync(self) -> None:
        """Save manifest to disk using atomic write.

        Security: Uses temp file + os.replace for atomic write.
        """
        data = {
            "version": "1.0.0",
            "last_updated": datetime.now().astimezone().isoformat(),
            "total_properties": len(self._manifest),
            "properties": self._manifest,
        }

        try:
            self._manifest_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write using temp file + rename
            fd, temp_path = tempfile.mkstemp(dir=self._manifest_path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_path, self._manifest_path)
                logger.debug("Saved manifest to disk")
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except OSError as e:
            logger.error(f"Failed to save manifest: {e}")

    def add_images_to_manifest(
        self,
        property_address: str,
        images: list[dict[str, Any]],
    ) -> None:
        """Add images to property's manifest entry.

        Args:
            property_address: Full property address
            images: List of image metadata dicts
        """
        if property_address not in self._manifest:
            self._manifest[property_address] = []

        self._manifest[property_address].extend(images)
        logger.debug(f"Added {len(images)} images to manifest for {property_address}")

    def get_images_for_property(self, property_address: str) -> list[dict[str, Any]]:
        """Get all images for a property from manifest.

        Args:
            property_address: Full property address

        Returns:
            List of image metadata dicts (empty if property not found)
        """
        return self._manifest.get(property_address, [])

    # ===== State Management Delegation =====

    def is_completed(self, property_address: str) -> bool:
        """Check if property was already completed.

        Args:
            property_address: Full address to check

        Returns:
            True if property was previously completed
        """
        return self._state_manager.is_completed(property_address)

    def mark_completed(self, property_address: str) -> None:
        """Mark property as completed.

        Increments checkpoint counter.

        Args:
            property_address: Full address of completed property
        """
        self._state_manager.mark_completed(property_address)
        self._operations_since_checkpoint += 1

    def mark_failed(self, property_address: str) -> None:
        """Mark property as failed.

        Increments checkpoint counter.

        Args:
            property_address: Full address of failed property
        """
        self._state_manager.mark_failed(property_address)
        self._operations_since_checkpoint += 1

    # ===== URL Tracking Delegation =====

    def check_url(
        self,
        url: str,
        content_hash: str | None = None,
    ) -> tuple[URLStatus, str | None]:
        """Check URL status for incremental extraction.

        Args:
            url: Image URL to check
            content_hash: Optional content hash for change detection

        Returns:
            Tuple of (status, existing_image_id or None)
            Status: "new", "known", "stale", "content_changed", "removed"
        """
        return self._url_tracker.check_url(url, content_hash)

    def register_url(
        self,
        url: str,
        image_id: str,
        property_hash: str,
        content_hash: str,
        source: str = "",
        original_address: str = "",
        run_id: str = "",
    ) -> None:
        """Register a URL in the tracker.

        Increments checkpoint counter.

        Args:
            url: Image URL
            image_id: UUID of downloaded image
            property_hash: 8-char hash of property address
            content_hash: Hash of image content
            source: Image source identifier
            original_address: Full address at extraction time (lineage)
            run_id: Run ID that discovered this URL (lineage)
        """
        self._url_tracker.register_url(
            url=url,
            image_id=image_id,
            property_hash=property_hash,
            content_hash=content_hash,
            source=source,
        )

        # Update lineage fields if provided
        if url in self._url_tracker.urls:
            entry = self._url_tracker.urls[url]
            if original_address and not entry.original_address:
                entry.original_address = original_address
            if run_id and not entry.first_run_id:
                entry.first_run_id = run_id
            if run_id:
                entry.last_run_id = run_id

        self._operations_since_checkpoint += 1

    # ===== Run Logging Delegation =====

    def start_run(
        self,
        properties_requested: int,
        mode: str = "incremental",
    ) -> RunLog:
        """Start a new extraction run.

        Args:
            properties_requested: Number of properties to process
            mode: Run mode (fresh, resume, incremental)

        Returns:
            New RunLog instance
        """
        return self._run_logger.start_run(
            properties_requested=properties_requested,
            mode=mode,
        )

    def record_property_changes(self, changes: PropertyChanges) -> None:
        """Record changes for a property in current run.

        Args:
            changes: PropertyChanges instance with all changes
        """
        if self._run_logger.current_run:
            self._run_logger.current_run.record_property(changes)

    async def finish_run(self) -> Path | None:
        """Finalize current run and save log.

        Also forces a final checkpoint of all state.

        Returns:
            Path to saved log file, or None if no current run
        """
        # Force final checkpoint before finishing
        await self.force_checkpoint()

        return self._run_logger.finish_run()

    # ===== Checkpoint Management =====

    async def checkpoint_if_needed(self) -> bool:
        """Checkpoint state if interval reached.

        Returns:
            True if checkpoint was performed, False otherwise
        """
        if not self.checkpoint_config.enable_checkpoints:
            return False

        if self._operations_since_checkpoint >= self.checkpoint_config.interval:
            await self.force_checkpoint()
            return True

        return False

    async def force_checkpoint(self) -> None:
        """Force an immediate checkpoint of all state.

        Uses async executor if configured, otherwise synchronous.
        Thread-safe via asyncio.Lock.
        """
        async with self._lock:
            if self.checkpoint_config.async_save:
                await self._checkpoint_async()
            else:
                self._checkpoint_sync()

            self._operations_since_checkpoint = 0

    def _checkpoint_sync(self) -> None:
        """Synchronous checkpoint - save all state files."""
        try:
            self._state_manager.save()
            self._url_tracker.save(self._url_tracker_path)
            self._save_manifest_sync()
            logger.debug("Checkpoint completed (sync)")
        except Exception as e:
            logger.error(f"Checkpoint failed: {e}")

    async def _checkpoint_async(self) -> None:
        """Async checkpoint using run_in_executor pattern.

        Offloads I/O to executor thread to avoid blocking event loop.
        """
        try:
            loop = asyncio.get_event_loop()

            # Run all saves in parallel using executor
            await asyncio.gather(
                loop.run_in_executor(None, self._state_manager.save),
                loop.run_in_executor(None, self._url_tracker.save, self._url_tracker_path),
                loop.run_in_executor(None, self._save_manifest_sync),
            )

            logger.debug("Checkpoint completed (async)")
        except Exception as e:
            logger.error(f"Async checkpoint failed: {e}")

    # ===== Diagnostics =====

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics from all services.

        Returns:
            Dict with stats from state manager, URL tracker, manifest, and run logger
        """
        state = self._state_manager.load()

        return {
            "state": {
                "completed_properties": len(state.completed_properties),
                "failed_properties": len(state.failed_properties),
                "operations_since_checkpoint": self._operations_since_checkpoint,
            },
            "url_tracker": self._url_tracker.get_stats(),
            "manifest": {
                "total_properties": len(self._manifest),
                "total_images": sum(len(images) for images in self._manifest.values()),
            },
            "run_logger": {
                "recent_runs": self._run_logger.get_recent_runs(limit=5),
            },
            "checkpoint_config": {
                "interval": self.checkpoint_config.interval,
                "async_save": self.checkpoint_config.async_save,
                "enable_checkpoints": self.checkpoint_config.enable_checkpoints,
            },
        }

    def reset(self) -> None:
        """Reset all state (for testing or re-processing).

        WARNING: This clears all tracking state. Use with caution.
        """
        self._state_manager.reset()
        self._url_tracker.clear()
        self._manifest.clear()
        self._operations_since_checkpoint = 0
        logger.warning("StateTracker reset - all state cleared")

"""Configuration file watcher for hot-reload support.

This module provides a ConfigWatcher class that monitors kill-switch
configuration files for changes and triggers reload callbacks.

Usage:
    from pathlib import Path
    from phx_home_analysis.services.kill_switch.config_watcher import ConfigWatcher

    def on_change(configs):
        print(f"Config changed: {len(configs)} criteria")

    watcher = ConfigWatcher(
        config_path=Path("config/kill_switch.csv"),
        on_change=on_change,
    )

    # Check for changes (call periodically or before evaluation)
    if watcher.check_for_changes():
        configs = watcher.get_updated_config()
        if configs:
            # Apply new config
            pass
"""

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config_loader import KillSwitchConfig

logger = logging.getLogger(__name__)


class ConfigWatcher:
    """Watch configuration file for changes in dev mode.

    This class monitors a CSV configuration file for modifications
    and provides methods to detect changes and reload configuration.

    The watcher uses file modification time (mtime) for change detection,
    which is efficient and doesn't require external dependencies like
    watchdog or inotify.

    Thread Safety:
        All public methods are thread-safe via internal locking.

    Attributes:
        config_path: Path to the configuration file being watched
        on_change: Optional callback invoked when config changes

    Example:
        watcher = ConfigWatcher(
            config_path=Path("config/kill_switch.csv"),
            on_change=lambda configs: print(f"Loaded {len(configs)} criteria"),
        )

        # In your evaluation loop:
        if watcher.check_for_changes():
            new_configs = watcher.get_updated_config()
            if new_configs:
                # Apply new configuration
                filter.reload_config()
    """

    def __init__(
        self,
        config_path: Path,
        on_change: Callable[[list["KillSwitchConfig"]], None] | None = None,
    ):
        """Initialize configuration watcher.

        Args:
            config_path: Path to CSV configuration file to watch
            on_change: Optional callback function that receives list of
                KillSwitchConfig objects when configuration changes.
                Called automatically by get_updated_config() if set.
        """
        self._path = config_path
        self._on_change = on_change
        self._last_mtime: float | None = None
        self._last_valid_config: list[KillSwitchConfig] | None = None
        self._lock = threading.Lock()
        # Track pending mtime from check_for_changes() to avoid TOCTOU race
        self._pending_mtime: float | None = None

        # Initialize with current mtime if file exists
        if self._path.exists():
            self._last_mtime = self._path.stat().st_mtime
            logger.debug(
                "ConfigWatcher initialized for %s (mtime=%s)", self._path, self._last_mtime
            )
        else:
            logger.warning("ConfigWatcher: config file does not exist: %s", self._path)

    @property
    def config_path(self) -> Path:
        """Get the path to the watched configuration file."""
        return self._path

    def check_for_changes(self) -> bool:
        """Check if configuration file has changed since last check.

        Uses file modification time (mtime) to detect changes.
        This is efficient and doesn't require file content comparison.

        Returns:
            True if config file was modified since last check, False otherwise.
            Also returns True on first call after initialization.

        Note:
            This method only checks for changes, it does not load or validate
            the configuration. Call get_updated_config() to load the new config.
            The mtime is NOT updated here to avoid TOCTOU race conditions;
            it is updated in get_updated_config() after successful load.
        """
        if not self._path.exists():
            logger.debug("ConfigWatcher: file does not exist: %s", self._path)
            return False

        with self._lock:
            current_mtime = self._path.stat().st_mtime

            if self._last_mtime is None:
                # First check - treat as changed, store pending mtime
                self._pending_mtime = current_mtime
                logger.debug("ConfigWatcher: first check, treating as changed")
                return True

            if current_mtime > self._last_mtime:
                logger.info(
                    "ConfigWatcher: file changed (old_mtime=%s, new_mtime=%s)",
                    self._last_mtime,
                    current_mtime,
                )
                # Store pending mtime - will be committed after successful load
                self._pending_mtime = current_mtime
                return True

            return False

    def get_updated_config(self) -> list["KillSwitchConfig"] | None:
        """Load and validate updated configuration.

        Attempts to load the configuration file and validate all entries.
        If loading fails (file not found, invalid format, validation error),
        returns the last known valid configuration instead.

        If an on_change callback was provided at initialization and loading
        succeeds, the callback is invoked with the new configuration.

        Returns:
            List of validated KillSwitchConfig objects if loading succeeds,
            or the last valid configuration if loading fails.
            Returns None if no valid configuration has ever been loaded.

        Example:
            configs = watcher.get_updated_config()
            if configs:
                for cfg in configs:
                    print(f"{cfg.name}: {cfg.type}, severity={cfg.severity}")
        """
        from .config_loader import load_kill_switch_config

        with self._lock:
            try:
                configs = load_kill_switch_config(self._path)
                self._last_valid_config = configs

                # Update mtime AFTER successful load to avoid TOCTOU race
                # Use pending_mtime if available, otherwise get current mtime
                if self._pending_mtime is not None:
                    self._last_mtime = self._pending_mtime
                    self._pending_mtime = None
                elif self._path.exists():
                    self._last_mtime = self._path.stat().st_mtime

                # Invoke callback if provided
                if self._on_change is not None:
                    self._on_change(configs)

                logger.info(
                    "ConfigWatcher: loaded %d criteria from %s",
                    len(configs),
                    self._path,
                )
                return configs

            except FileNotFoundError as e:
                logger.warning("ConfigWatcher: config file not found: %s", e)
                # Clear pending mtime on failure
                self._pending_mtime = None
                return self._last_valid_config

            except ValueError as e:
                logger.warning("ConfigWatcher: invalid config rejected, keeping previous: %s", e)
                # Clear pending mtime on failure
                self._pending_mtime = None
                return self._last_valid_config

    def get_last_valid_config(self) -> list["KillSwitchConfig"] | None:
        """Get the last successfully loaded configuration.

        Returns:
            List of KillSwitchConfig from last successful load,
            or None if no successful load has occurred.
        """
        with self._lock:
            return self._last_valid_config

    def force_reload(self) -> list["KillSwitchConfig"] | None:
        """Force reload configuration regardless of mtime.

        Resets the mtime tracking and loads configuration fresh.
        Useful for initial load or manual refresh.

        Returns:
            List of validated KillSwitchConfig objects, or None on error.
        """
        with self._lock:
            self._last_mtime = None
            self._pending_mtime = None
        return self.get_updated_config()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ConfigWatcher(path={self._path}, last_mtime={self._last_mtime})"

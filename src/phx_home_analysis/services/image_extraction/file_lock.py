"""Cross-process file locking for concurrent extraction safety."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Failed to acquire lock within timeout."""

    pass


class FileLock:
    """
    Cross-process file lock using atomic file creation.

    Works on Windows and Unix. Uses the fact that creating a file
    with O_CREAT | O_EXCL is atomic and fails if file exists.

    Usage:
        lock = FileLock(Path("myfile.lock"))
        with lock:
            # Critical section
            pass
    """

    def __init__(
        self,
        lock_path: Path,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
        stale_timeout: float = 300.0,  # 5 minutes
    ):
        """
        Initialize file lock.

        Args:
            lock_path: Path to lock file
            timeout: Max seconds to wait for lock
            poll_interval: Seconds between acquisition attempts
            stale_timeout: Seconds after which lock is considered stale
        """
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.stale_timeout = stale_timeout
        self._acquired = False

    def acquire(self) -> bool:
        """
        Acquire the lock.

        Returns:
            True if lock acquired, False if timeout

        Raises:
            LockAcquisitionError if timeout exceeded
        """
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                # Atomic file creation - fails if exists
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # Write PID and timestamp for debugging
                content = f"{os.getpid()}:{time.time()}"
                os.write(fd, content.encode())
                os.close(fd)
                self._acquired = True
                logger.debug(f"Acquired lock: {self.lock_path}")
                return True

            except FileExistsError:
                # Lock exists - check if stale
                if self._is_stale():
                    logger.warning(f"Removing stale lock: {self.lock_path}")
                    self._force_release()
                    continue

                # Wait and retry
                time.sleep(self.poll_interval)

            except OSError as e:
                logger.error(f"Lock acquisition error: {e}")
                time.sleep(self.poll_interval)

        raise LockAcquisitionError(
            f"Failed to acquire lock {self.lock_path} within {self.timeout}s"
        )

    def release(self) -> None:
        """Release the lock."""
        if self._acquired and self.lock_path.exists():
            try:
                self.lock_path.unlink()
                logger.debug(f"Released lock: {self.lock_path}")
            except OSError as e:
                logger.error(f"Failed to release lock: {e}")
            finally:
                self._acquired = False

    def _is_stale(self) -> bool:
        """Check if existing lock is stale (old or dead process)."""
        if not self.lock_path.exists():
            return False

        try:
            content = self.lock_path.read_text()
            pid_str, timestamp_str = content.split(":")
            pid = int(pid_str)
            timestamp = float(timestamp_str)

            # Check if process is still alive
            if not self._process_exists(pid):
                return True

            # Check if lock is too old
            age = time.time() - timestamp
            if age > self.stale_timeout:
                return True

            return False

        except (ValueError, OSError):
            # Corrupted lock file - treat as stale
            return True

    def _process_exists(self, pid: int) -> bool:
        """Check if process with given PID exists."""
        try:
            os.kill(pid, 0)  # Signal 0 = check existence
            return True
        except (OSError, ProcessLookupError):
            return False

    def _force_release(self) -> None:
        """Force remove lock file (for stale locks)."""
        try:
            self.lock_path.unlink()
        except OSError:
            pass

    def __enter__(self) -> FileLock:
        """Context manager entry - acquire lock."""
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit - release lock."""
        self.release()

    @contextmanager
    def locked(self) -> Generator[None, None, None]:
        """Alternative context manager syntax."""
        self.acquire()
        try:
            yield
        finally:
            self.release()


class PropertyLock(FileLock):
    """Lock for a specific property during extraction."""

    def __init__(self, locks_dir: Path, property_hash: str, **kwargs: object) -> None:
        lock_path = locks_dir / f"{property_hash}.lock"
        super().__init__(lock_path, **kwargs)  # type: ignore[arg-type]
        self.property_hash = property_hash


class ManifestLock(FileLock):
    """Lock for manifest file updates."""

    def __init__(self, locks_dir: Path, **kwargs: object) -> None:
        lock_path = locks_dir / "manifest.lock"
        super().__init__(lock_path, timeout=10.0, **kwargs)  # type: ignore[arg-type]

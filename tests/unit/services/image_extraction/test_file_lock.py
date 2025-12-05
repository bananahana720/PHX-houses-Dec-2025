"""Tests for file locking mechanism."""
from pathlib import Path

import pytest

from phx_home_analysis.services.image_extraction.file_lock import (
    FileLock,
    LockAcquisitionError,
    ManifestLock,
    PropertyLock,
)


class TestFileLock:
    """Tests for FileLock class."""

    def test_acquire_release(self, tmp_path: Path):
        """Test basic acquire and release."""
        lock = FileLock(tmp_path / "test.lock")

        assert not lock._acquired
        lock.acquire()
        assert lock._acquired
        assert (tmp_path / "test.lock").exists()

        lock.release()
        assert not lock._acquired
        assert not (tmp_path / "test.lock").exists()

    def test_context_manager(self, tmp_path: Path):
        """Test context manager usage."""
        lock_path = tmp_path / "test.lock"

        with FileLock(lock_path):
            assert lock_path.exists()

        assert not lock_path.exists()

    def test_concurrent_acquisition_blocks(self, tmp_path: Path):
        """Test that second acquisition blocks."""
        lock_path = tmp_path / "test.lock"
        lock1 = FileLock(lock_path, timeout=0.5)
        lock2 = FileLock(lock_path, timeout=0.5)

        lock1.acquire()

        with pytest.raises(LockAcquisitionError):
            lock2.acquire()

        lock1.release()

    def test_stale_lock_detection(self, tmp_path: Path):
        """Test that stale locks are detected and removed."""
        lock_path = tmp_path / "test.lock"

        # Create a fake stale lock with invalid PID
        lock_path.write_text("999999:0")  # Old timestamp, likely dead PID

        lock = FileLock(lock_path, stale_timeout=0)  # Immediate stale
        lock.acquire()  # Should succeed after removing stale
        assert lock._acquired
        lock.release()

    def test_lock_content_format(self, tmp_path: Path):
        """Test lock file contains PID and timestamp."""
        lock_path = tmp_path / "test.lock"
        lock = FileLock(lock_path)
        lock.acquire()

        content = lock_path.read_text()
        parts = content.split(":")
        assert len(parts) == 2

        import os
        assert int(parts[0]) == os.getpid()
        assert float(parts[1]) > 0

        lock.release()


class TestPropertyLock:
    """Tests for PropertyLock class."""

    def test_creates_correct_path(self, tmp_path: Path):
        """Test lock path is correct."""
        lock = PropertyLock(tmp_path, "abc12345")
        assert lock.lock_path == tmp_path / "abc12345.lock"
        assert lock.property_hash == "abc12345"


class TestManifestLock:
    """Tests for ManifestLock class."""

    def test_creates_correct_path(self, tmp_path: Path):
        """Test manifest lock path."""
        lock = ManifestLock(tmp_path)
        assert lock.lock_path == tmp_path / "manifest.lock"
        assert lock.timeout == 10.0  # Shorter default timeout

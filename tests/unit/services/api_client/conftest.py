"""Shared fixtures for API client tests."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "api_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

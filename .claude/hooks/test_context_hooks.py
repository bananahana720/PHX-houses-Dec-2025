#!/usr/bin/env python3
"""
Tests for context management hooks.

Run with: pytest .claude/hooks/test_context_hooks.py -v
"""

import os
import sys
import time
from pathlib import Path

import pytest

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.claude_md_utils import (
    TEMPLATE_MARKER,
    check_claude_md_exists,
    create_from_template,
    is_excluded_directory,
    is_naked_template,
    is_stale,
    parse_frontmatter,
)
from lib.delta_logger import (
    check_directory_has_claude_md,
    clear_session_log,
    get_modified_directories,
    get_session_deltas,
    log_delta,
)
from lib.reference_parser import (
    check_reference_freshness,
    has_line_reference,
    parse_line_reference,
    validate_line_reference,
)


class TestClaudeMdUtils:
    """Tests for claude_md_utils module."""

    def test_check_claude_md_exists_true(self, tmp_path):
        """Test detection of existing CLAUDE.md."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test")
        assert check_claude_md_exists(tmp_path) is True

    def test_check_claude_md_exists_false(self, tmp_path):
        """Test detection of missing CLAUDE.md."""
        assert check_claude_md_exists(tmp_path) is False

    def test_is_excluded_directory(self):
        """Test excluded directory detection."""
        assert is_excluded_directory(".git") is True
        assert is_excluded_directory("node_modules") is True
        assert is_excluded_directory("__pycache__") is True
        assert is_excluded_directory("src") is False
        assert is_excluded_directory("tests") is False

    def test_is_excluded_directory_nested(self):
        """Test excluded directory detection in nested paths."""
        assert is_excluded_directory("project/node_modules/package") is True
        assert is_excluded_directory("project/.git/objects") is True
        assert is_excluded_directory("project/src/utils") is False

    def test_parse_frontmatter_valid(self, tmp_path):
        """Test parsing valid frontmatter."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """---
last_updated: 2025-12-03
updated_by: Claude Code
staleness_hours: 24
---
# Content
"""
        )
        fm = parse_frontmatter(claude_md)
        assert fm["last_updated"] == "2025-12-03"
        assert fm["updated_by"] == "Claude Code"
        assert fm["staleness_hours"] == 24

    def test_parse_frontmatter_no_frontmatter(self, tmp_path):
        """Test parsing file without frontmatter."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Just content\n\nNo frontmatter here.")
        fm = parse_frontmatter(claude_md)
        assert fm == {}

    def test_is_stale_fresh_file(self, tmp_path):
        """Test freshness check for recently modified file."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Fresh")
        assert is_stale(claude_md, threshold_hours=24) is False

    def test_is_stale_old_file(self, tmp_path):
        """Test staleness check for old file."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Old")
        # Set mtime to 48 hours ago
        old_time = time.time() - (48 * 3600)
        os.utime(claude_md, (old_time, old_time))
        assert is_stale(claude_md, threshold_hours=24) is True

    def test_is_naked_template_with_marker(self, tmp_path):
        """Test detection of template marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(f"{TEMPLATE_MARKER}\n# Template\n[PURPOSE]")
        assert is_naked_template(claude_md) is True

    def test_is_naked_template_filled(self, tmp_path):
        """Test detection of filled template."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            """---
last_updated: 2025-12-03
---
# Actual Content

This directory contains utility functions.
"""
        )
        assert is_naked_template(claude_md) is False

    def test_create_from_template(self, tmp_path):
        """Test template creation."""
        target_dir = tmp_path / "subdir"
        target_dir.mkdir()

        result = create_from_template(target_dir)
        assert result is not None
        assert (target_dir / "CLAUDE.md").exists()

        content = (target_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert TEMPLATE_MARKER in content


class TestReferenceParser:
    """Tests for reference_parser module."""

    def test_parse_line_reference_with_L(self):
        """Test parsing :L pattern."""
        file_path, start, end = parse_line_reference("src/main.py:L42")
        assert file_path == "src/main.py"
        assert start == 42
        assert end is None

    def test_parse_line_reference_range(self):
        """Test parsing line range."""
        file_path, start, end = parse_line_reference("src/main.py:L10-L20")
        assert file_path == "src/main.py"
        assert start == 10
        assert end == 20

    def test_parse_line_reference_no_reference(self):
        """Test parsing path without reference."""
        file_path, start, end = parse_line_reference("src/main.py")
        assert file_path == "src/main.py"
        assert start is None
        assert end is None

    def test_has_line_reference(self):
        """Test line reference detection."""
        assert has_line_reference("src/main.py:L42") is True
        assert has_line_reference("src/main.py:42") is True
        assert has_line_reference("src/main.py") is False

    def test_check_reference_freshness_missing_file(self, tmp_path):
        """Test freshness check for missing file."""
        is_stale, msg = check_reference_freshness(tmp_path / "missing.py")
        assert is_stale is True
        assert "not found" in msg

    def test_check_reference_freshness_recent_file(self, tmp_path):
        """Test freshness check for recently modified file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# content")
        is_stale, msg = check_reference_freshness(test_file)
        assert is_stale is True  # File was just modified
        assert "modified" in msg.lower()

    def test_validate_line_reference(self, tmp_path):
        """Test full reference validation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# content")

        has_warning, msg = validate_line_reference(f"{test_file}:L10")
        # Recently created file should trigger warning
        assert has_warning is True


class TestDeltaLogger:
    """Tests for delta_logger module."""

    def test_log_delta(self, tmp_path, monkeypatch):
        """Test logging a delta."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()

        result = log_delta("test.py", "modify", line_delta=10)
        assert result is True

        deltas = get_session_deltas()
        assert len(deltas) == 1
        assert deltas[0]["file_path"] == "test.py"
        assert deltas[0]["change_type"] == "modify"
        assert deltas[0]["line_delta"] == 10

    def test_check_directory_has_claude_md(self, tmp_path):
        """Test directory CLAUDE.md check."""
        # Without CLAUDE.md
        test_file = tmp_path / "test.py"
        test_file.write_text("# content")
        assert check_directory_has_claude_md(test_file) is False

        # With CLAUDE.md
        (tmp_path / "CLAUDE.md").write_text("# Context")
        assert check_directory_has_claude_md(test_file) is True

    def test_get_modified_directories(self, tmp_path, monkeypatch):
        """Test getting modified directories."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()

        log_delta("src/a.py", "modify")
        log_delta("tests/b.py", "create")

        dirs = get_modified_directories()
        assert "src" in str(dirs) or len(dirs) >= 1

    def test_clear_session_log(self, tmp_path, monkeypatch):
        """Test clearing session log."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()

        log_delta("test.py", "modify")
        assert len(get_session_deltas()) > 0

        clear_session_log()
        assert len(get_session_deltas()) == 0


class TestHookIntegration:
    """Integration tests for hooks."""

    def test_file_size_hook_imports(self):
        """Test that file_size_conditional_hook can import lib."""
        # This tests the import mechanism
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from lib.claude_md_utils import check_claude_md_exists

            assert callable(check_claude_md_exists)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_delta_tracker_hook_imports(self):
        """Test that delta_tracker_hook can import lib."""
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from lib.delta_logger import log_delta_async

            assert callable(log_delta_async)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Shared utilities for Claude Code context management hooks.

Modules:
- claude_md_utils: CLAUDE.md file operations (discovery, staleness, templates)
- reference_parser: Line reference validation (:L42 patterns)
- delta_logger: Async session delta logging
"""

from .claude_md_utils import (
    check_claude_md_exists,
    create_from_template,
    is_naked_template,
    is_stale,
    parse_frontmatter,
)
from .delta_logger import check_directory_has_claude_md, log_delta_async
from .reference_parser import check_reference_freshness, parse_line_reference

__all__ = [
    # claude_md_utils
    "check_claude_md_exists",
    "is_stale",
    "is_naked_template",
    "create_from_template",
    "parse_frontmatter",
    # reference_parser
    "parse_line_reference",
    "check_reference_freshness",
    # delta_logger
    "log_delta_async",
    "check_directory_has_claude_md",
]

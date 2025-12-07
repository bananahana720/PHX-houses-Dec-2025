"""
Shared utilities for Claude Code context management hooks.

Modules:
- claude_md_utils: CLAUDE.md file operations (discovery, staleness, templates)
- reference_parser: Line reference validation (:L42 patterns)
- delta_logger: Async session delta logging
- exclusions: Shared directory exclusion patterns
- hook_io: Standardized JSON I/O for hook input/output
- config: Centralized configuration for all hooks
"""

from .claude_md_utils import (
    check_claude_md_exists,
    create_from_template,
    is_naked_template,
    is_stale,
    parse_frontmatter,
)
from .config import (
    CLAUDE_MD_CONFIG,
    FILE_SIZE_THRESHOLDS,
    HOOK_CONFIG,
    REFERENCE_CONFIG,
    SECURITY_CONFIG,
    SESSION_CONFIG,
)
from .delta_logger import check_directory_has_claude_md, log_delta_async
from .exclusions import (
    EXCLUDED_DIRS,
    SKIP_PATTERNS,
    normalize_path,
    should_exclude_directory,
    should_skip_logging,
)
from .hook_io import (
    approve,
    block,
    get_command,
    get_file_path,
    get_session_id,
    get_tool_input,
    get_tool_name,
    read_hook_input,
    warn,
    write_hook_output,
)
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
    # exclusions
    "EXCLUDED_DIRS",
    "SKIP_PATTERNS",
    "normalize_path",
    "should_exclude_directory",
    "should_skip_logging",
    # hook_io
    "read_hook_input",
    "write_hook_output",
    "get_tool_name",
    "get_tool_input",
    "get_file_path",
    "get_command",
    "get_session_id",
    "approve",
    "block",
    "warn",
    # config
    "CLAUDE_MD_CONFIG",
    "FILE_SIZE_THRESHOLDS",
    "HOOK_CONFIG",
    "REFERENCE_CONFIG",
    "SECURITY_CONFIG",
    "SESSION_CONFIG",
]

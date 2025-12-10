#!/usr/bin/env python3
"""
Centralized configuration for Claude Code hooks.

All thresholds, paths, and settings should be defined here
to ensure consistency and easy maintenance.
"""


# =============================================================================
# File Size Thresholds
# =============================================================================
FILE_SIZE_THRESHOLDS = {
    "main_agent_lines": 750,  # from file_size_conditional_hook.py:155
    "subagent_lines": 10_000,  # from file_size_conditional_hook.py:168
}

# =============================================================================
# CLAUDE.md Configuration
# =============================================================================
CLAUDE_MD_CONFIG = {
    "oversized_threshold_lines": 100,  # from stop_hygiene_hook.py:38
    "stale_threshold_hours": 24,  # from stop_hygiene_hook.py:39, lib/claude_md_utils.py:43
    "display_limit": 5,  # from stop_hygiene_hook.py:40
}

# =============================================================================
# Reference Validation
# =============================================================================
REFERENCE_CONFIG = {
    "freshness_hours": 4,  # from lib/reference_parser.py:26
}

# =============================================================================
# Session Management
# =============================================================================
SESSION_CONFIG = {
    "max_log_archives": 10,  # from session_cleanup_hook.py:109
    "delta_log_path": ".claude/session-delta.log",
    "learnings_log_path": ".claude/session-learnings.json",
}

# =============================================================================
# Security Reminder
# =============================================================================
SECURITY_CONFIG = {
    "state_cleanup_days": 30,  # from security_reminder_hook.py:143
    "cleanup_probability": 0.1,  # from security_reminder_hook.py:228 (10%)
}

# =============================================================================
# Hook Behavior
# =============================================================================
HOOK_CONFIG = {
    "format_timeout_seconds": 30,  # from format_python_hook.py:37
    "format_line_length": 100,  # from format_python_hook.py:34
}

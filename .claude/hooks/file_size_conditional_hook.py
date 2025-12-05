#!/usr/bin/env python3
"""
PreToolUse hook for Read tool: Context management and file size validation.

Performs three checks before allowing file reads:
1. CLAUDE.md Discovery - Ensure directory has CLAUDE.md (create if missing)
2. Reference Validation - Warn if :L line references may be stale
3. File Size Check - Block large files to prevent context bloat

Exit codes:
- 0: Allow read
- 1: Warning (stale CLAUDE.md, stale reference) - proceed with message
- 2: Block (file too large)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import shared utilities
# Use try/except for graceful degradation if lib not available
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from lib.claude_md_utils import (
        check_claude_md_exists,
        create_from_template,
        is_excluded_directory,
        is_naked_template,
        is_stale,
    )
    from lib.reference_parser import has_line_reference, validate_line_reference

    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False

# Load input from stdin
data = json.load(sys.stdin)

# Check if we're in a subtask
flag_file = ".claude_in_subtask.flag"
is_main_agent = not os.path.exists(flag_file)

# Get file path from tool input
file_path = data.get("tool_input", {}).get("file_path")
offset = data.get("tool_input", {}).get("offset", 0)
limit = data.get("tool_input", {}).get("limit", 0)

if not file_path:
    sys.exit(0)

path = Path(file_path)

# ============================================================================
# CHECK 1: CLAUDE.md Discovery (only if lib available)
# ============================================================================
if LIB_AVAILABLE and path.exists():
    target_dir = path.parent if path.is_file() else path

    # Skip excluded directories
    if not is_excluded_directory(target_dir):
        claude_md_path = target_dir / "CLAUDE.md"

        if not check_claude_md_exists(target_dir):
            # Create CLAUDE.md from template
            created_path = create_from_template(target_dir)
            if created_path:
                # Silent creation - just proceed
                pass
        else:
            # Check if stale (>24h)
            if is_stale(claude_md_path, threshold_hours=24):
                print(
                    f"⚠️ CLAUDE.md in {target_dir} is stale (>24h). Consider updating.",
                    file=sys.stderr,
                )
                # Exit 1 = warning, but proceed
                # We continue to other checks rather than exiting here

            # Check if naked template
            if is_naked_template(claude_md_path):
                print(
                    f"⚠️ CLAUDE.md in {target_dir} is an unfilled template. "
                    "Please populate with directory context.",
                    file=sys.stderr,
                )

# ============================================================================
# CHECK 2: Reference Validation (only if lib available)
# ============================================================================
if LIB_AVAILABLE and file_path:
    if has_line_reference(file_path):
        has_warning, warning_msg = validate_line_reference(file_path)
        if has_warning and warning_msg:
            print(f"⚠️ {warning_msg}", file=sys.stderr)
            # Warning only, continue to file size check

# ============================================================================
# CHECK 3: File Size Check (original logic)
# ============================================================================
if file_path and os.path.exists(file_path):

    def is_binary_file(filepath):
        """Check if a file is binary by looking for null bytes in first chunk"""
        try:
            with open(filepath, "rb") as f:
                chunk = f.read(8192)
                if not chunk:
                    return False
                if b"\x00" in chunk:
                    return True
                try:
                    chunk.decode("utf-8")
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception:
            return True

    # Skip line count check for binary files
    if is_binary_file(file_path):
        sys.exit(0)

    def _count_lines_fast(path: str) -> int:
        total = 0
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                total += chunk.count(b"\n")
        return total

    def _get_line_count(path: str) -> int:
        if shutil.which("wc"):
            try:
                out = subprocess.check_output(["wc", "-l", path])
                return int(out.split()[0])
            except Exception:
                pass
        return _count_lines_fast(path)

    line_count = _get_line_count(file_path)

    # Determine if this is a full file read (no limit specified)
    is_full_read = limit == 0 or limit is None

    # Compute effective number of lines to be read
    if limit and limit > 0:
        effective_lines = min(limit, max(0, line_count - offset))
    else:
        effective_lines = max(0, line_count - offset)

    # Only block if: main agent + full file read + file > 750 lines
    if is_main_agent and is_full_read and line_count > 750:
        error_msg = f"""File has {line_count} lines (threshold: 750) and this is a full file read.

Please either:
1. Use offset/limit parameters to read specific sections (e.g., offset=0, limit=500)
2. Use Grep tool or ripgrep (rg) to search for specific patterns
3. Delegate to a subagent: Task tool with subagent_type=Explore

Example partial read:
    Read file_path="{file_path}" offset=0 limit=500
"""
        print(error_msg, file=sys.stderr)
        sys.exit(2)
    elif (not is_main_agent) and line_count > 10_000:
        error_msg = f"""File too large ({line_count} lines) even for subagent analysis (threshold: 10,000).

Consider these alternatives:
1. Read specific sections using offset/limit parameters
2. Use Grep tool or the rg bash command to search for specific patterns
"""
        print(error_msg, file=sys.stderr)
        sys.exit(2)

# All checks passed
sys.exit(0)

#!/usr/bin/env python3
import os
import json
import sys
import subprocess
import shutil


data = json.load(sys.stdin)

# Check if we're in a subtask
flag_file = '.claude_in_subtask.flag'
is_main_agent = not os.path.exists(flag_file)
# if os.path.exists(flag_file):
#     print(json.dumps({"decision": "approve"}))
#     sys.exit(0)

# Check file size
file_path = data.get("tool_input", {}).get("file_path")
offset = data.get("tool_input", {}).get("offset",0)
limit = data.get("tool_input", {}).get("limit",0) # 0 if absent

if file_path and os.path.exists(file_path):
    # Check if this is a binary file by examining its content
    def is_binary_file(filepath):
        """Check if a file is binary by looking for null bytes in first chunk"""
        try:
            with open(filepath, 'rb') as f:
                # Read first 8192 bytes (or less if file is smaller)
                chunk = f.read(8192)
                if not chunk:  # Empty file
                    return False
                
                # Files with null bytes are likely binary
                if b'\x00' in chunk:
                    return True
                
                # Try to decode as UTF-8
                try:
                    chunk.decode('utf-8')
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception:
            # If we can't read the file, assume it's binary to be safe
            return True
    
    # Skip line count check for binary files
    if is_binary_file(file_path):
        sys.exit(0)
    
    import shutil

    def _count_lines_fast(path: str) -> int:
        # Chunked binary read; counts b'\n' so works for CRLF too
        total = 0
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                total += chunk.count(b'\n')
        return total

    def _get_line_count(path: str) -> int:
        # If wc is available (macOS/Linux/WSL), we can use it; otherwise pure Python
        if shutil.which('wc'):
            try:
                out = subprocess.check_output(['wc', '-l', path])
                # wc output is like: "<num> <path>"
                return int(out.split()[0])
            except Exception:
                # Fallback if wc fails for any reason
                pass
        return _count_lines_fast(path)

    line_count = _get_line_count(file_path)

    
    # Compute effective number of lines to be read
    if limit > 0:
        # If limit is specified, we read from offset to offset+limit
        effective_lines = min(limit, max(0, line_count - offset))
    else:
        # If no limit, we read from offset to end of file
        effective_lines = max(0, line_count - offset)

    if is_main_agent and line_count > 750:
        error_msg = f"""File has {line_count} lines (threshold: 750).

Please utilize ripgrep (rg), Grep (capital G*), or delegate the analysis to a SUB-AGENT using your Task tool
to avoid bloating your context with the file content.

Example:
    Use the Task tool with subagent_type=Explore to analyze {file_path}
"""
        print(error_msg, file=sys.stderr)
        sys.exit(2)
    elif (not is_main_agent) and line_count > 10_000:
        # File is too large even for subagent
        error_msg = f"""File too large ({line_count} lines) even for subagent analysis (threshold: 10,000).

Consider these alternatives:
1. Read specific sections using offset/limit parameters
2. Use Grep tool or the rg bash command to search for specific patterns
"""
        print(error_msg, file=sys.stderr)
        sys.exit(2)

# File size is acceptable, allow reading
sys.exit(0)
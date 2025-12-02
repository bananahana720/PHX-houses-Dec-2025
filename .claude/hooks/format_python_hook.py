#!/usr/bin/env python3
"""
PostToolUse hook: Formats Python files with black and ruff after Edit/Write operations.
"""
import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
        file_path = data.get("tool_input", {}).get("file_path", "")

        # Only process Python files
        if not file_path.endswith('.py'):
            sys.exit(0)

        # Verify file exists
        if not Path(file_path).exists():
            print(f"WARNING: File not found: {file_path}", file=sys.stderr)
            sys.exit(0)

        # Run black formatter
        try:
            subprocess.run(
                ["black", "--line-length", "100", file_path],
                capture_output=True,
                check=True,
                timeout=30
            )
            print(f"INFO: Formatted with black: {file_path}", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Black formatting failed: {e.stderr.decode()}", file=sys.stderr)
        except FileNotFoundError:
            print("WARNING: black not found in PATH", file=sys.stderr)

        # Run ruff linter with auto-fix
        try:
            subprocess.run(
                ["ruff", "check", "--fix", file_path],
                capture_output=True,
                check=False,  # Don't fail on lint errors
                timeout=30
            )
            print(f"INFO: Checked with ruff: {file_path}", file=sys.stderr)
        except FileNotFoundError:
            print("WARNING: ruff not found in PATH", file=sys.stderr)

        # Always allow (exit 0)
        sys.exit(0)

    except Exception as e:
        # On any error, just allow
        print(f"WARNING: Hook error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

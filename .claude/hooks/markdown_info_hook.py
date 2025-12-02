#!/usr/bin/env python3
"""
PostToolUse hook: Logs info when markdown files are modified.
"""
import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
        file_path = data.get("tool_input", {}).get("file_path", "")

        # Check if it's a markdown file
        if file_path.endswith('.md'):
            print(f"INFO: Markdown file modified: {file_path}", file=sys.stderr)

        # Always allow (exit 0)
        sys.exit(0)

    except Exception as e:
        # On any error, just allow
        sys.exit(0)


if __name__ == "__main__":
    main()

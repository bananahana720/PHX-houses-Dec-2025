#!/usr/bin/env python3
"""
UserPromptSubmit hook: Reminds user to use rg instead of grep in prompts.
"""
import json
import re
import sys


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "")

        # Check if prompt contains grep (but not git grep or history grep)
        if re.search(r'\bgrep\s', prompt):
            if not re.search(r'\b(git|history)\s+grep', prompt):
                print("REMINDER: Use rg (ripgrep) instead of grep", file=sys.stderr)

        # Always allow (exit 0)
        sys.exit(0)

    except Exception:
        # On any error, just allow the prompt
        sys.exit(0)


if __name__ == "__main__":
    main()

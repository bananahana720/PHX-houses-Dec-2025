#!/usr/bin/env python3
"""Pre-commit hook to verify architecture documentation consistency.

Checks that key architectural values match across documentation files.
Prevents drift between docs and implementation.

Usage:
    python .claude/hooks/architecture-consistency-check.py

Exit Codes:
    0 - All checks passed
    1 - Inconsistencies found
"""

import re
import sys
from pathlib import Path
from typing import NamedTuple


class ConsistencyCheck(NamedTuple):
    name: str
    pattern: str
    expected: str
    files: list[str]


# Define expected values and where to check
CHECKS = [
    ConsistencyCheck(
        name="Scoring Total",
        pattern=r"605\s*(?:pts?|points?)",
        expected="605",
        files=[
            "CLAUDE.md",
            "docs/architecture/scoring-system-architecture.md",
            "docs/architecture/executive-summary.md",
        ],
    ),
    ConsistencyCheck(
        name="HARD Kill-Switch Count",
        pattern=r"(\d+)\s*HARD",
        expected="5",
        files=[
            "CLAUDE.md",
            "docs/architecture/kill-switch-architecture.md",
            "docs/architecture/core-architectural-decisions.md",
        ],
    ),
    ConsistencyCheck(
        name="SOFT Kill-Switch Count",
        pattern=r"(\d+)\s*SOFT",
        expected="4",
        files=[
            "CLAUDE.md",
            "docs/architecture/kill-switch-architecture.md",
            "docs/architecture/core-architectural-decisions.md",
        ],
    ),
    ConsistencyCheck(
        name="Unicorn Threshold",
        pattern=r"(?:Unicorn[^0-9]*[>>=]?\s*|UNICORN_THRESHOLD\s*=\s*)(48[0-9]|49[0-9]|50[0-9])",
        expected="48",  # Match 480-509 range
        files=[
            "CLAUDE.md",
            "docs/architecture/scoring-system-architecture.md",
        ],
    ),
]


def check_file(filepath: Path, check: ConsistencyCheck) -> tuple[bool, str]:
    """Check a single file for expected pattern."""
    if not filepath.exists():
        return True, f"  ⚠️  {filepath} not found (skipped)"

    content = filepath.read_text(encoding="utf-8")
    matches = re.findall(check.pattern, content, re.IGNORECASE)

    if not matches:
        return True, f"  ℹ️  {filepath}: No mention of {check.name}"

    # Check if any match contains expected value
    for match in matches:
        if check.expected in str(match):
            return True, f"  ✅ {filepath}: Found '{check.expected}'"

    return False, f"  ❌ {filepath}: Expected '{check.expected}', found {matches}"


def main() -> int:
    """Run all consistency checks."""
    project_root = Path(__file__).parent.parent.parent
    all_passed = True
    results = []

    print("🔍 Architecture Consistency Check")
    print("=" * 50)

    for check in CHECKS:
        print(f"\n📋 {check.name} (expected: {check.expected})")
        check_passed = True

        for filepath in check.files:
            full_path = project_root / filepath
            passed, message = check_file(full_path, check)
            print(message)
            if not passed:
                check_passed = False
                all_passed = False

        if check_passed:
            results.append(f"✅ {check.name}")
        else:
            results.append(f"❌ {check.name}")

    print("\n" + "=" * 50)
    print("Summary:")
    for result in results:
        print(f"  {result}")

    if all_passed:
        print("\n✅ All architecture consistency checks passed!")
        return 0
    else:
        print("\n❌ Architecture inconsistencies detected!")
        print("Please update documentation to match implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

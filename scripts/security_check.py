#!/usr/bin/env python
"""Run security vulnerability scan on dependencies."""
import subprocess
import sys


def main() -> int:
    """Execute pip-audit security scan with strict mode.

    Returns:
        0 if no vulnerabilities found, 1 if vulnerabilities detected
    """
    print("Running pip-audit security scan...")
    print("-" * 70)

    result = subprocess.run(
        ["pip-audit", "--strict"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("-" * 70)
        print("SECURITY ISSUES FOUND:")
        print(result.stderr)
        print("-" * 70)
        return 1

    print("-" * 70)
    print("✓ No known vulnerabilities found")
    print("-" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

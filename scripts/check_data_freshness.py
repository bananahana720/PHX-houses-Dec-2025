#!/usr/bin/env python3
"""
CLI tool for checking property data freshness.

Generates staleness reports for properties in enrichment_data.json,
identifying records that haven't been updated within a threshold period.

Usage:
    python scripts/check_data_freshness.py                    # Default 30-day threshold
    python scripts/check_data_freshness.py --threshold 14     # Custom threshold
    python scripts/check_data_freshness.py --json             # JSON output
    python scripts/check_data_freshness.py --addresses-only   # Just list stale addresses
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phx_home_analysis.services.lifecycle import StalenessDetector


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check property data freshness and generate staleness reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_data_freshness.py                    # Default 30-day check
  python scripts/check_data_freshness.py --threshold 7      # 7-day threshold
  python scripts/check_data_freshness.py --json             # JSON output
  python scripts/check_data_freshness.py --addresses-only   # List addresses only
        """,
    )

    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=30,
        help="Days after which data is considered stale (default: 30)",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output report as JSON",
    )
    parser.add_argument(
        "--addresses-only",
        "-a",
        action="store_true",
        help="Only output stale property addresses (one per line)",
    )
    parser.add_argument(
        "--data-file",
        "-d",
        type=Path,
        default=PROJECT_ROOT / "data" / "enrichment_data.json",
        help="Path to enrichment_data.json",
    )

    args = parser.parse_args()

    # Validate data file exists
    if not args.data_file.exists():
        print(f"Error: Data file not found: {args.data_file}", file=sys.stderr)
        return 1

    # Create detector and analyze
    try:
        detector = StalenessDetector(
            enrichment_path=args.data_file,
            threshold_days=args.threshold,
        )
        report = detector.analyze()
    except Exception as e:
        print(f"Error analyzing data: {e}", file=sys.stderr)
        return 1

    # Output based on format
    if args.addresses_only:
        for prop in report.stale_properties:
            print(prop.full_address)
    elif args.json:
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print(report.summary())

    # Return non-zero if stale properties found (useful for CI)
    return 1 if report.has_stale_properties else 0


if __name__ == "__main__":
    sys.exit(main())

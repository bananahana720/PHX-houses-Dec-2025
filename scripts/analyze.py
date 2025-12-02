#!/usr/bin/env python
"""CLI entry point for PHX Home Analysis pipeline.

This script provides a command-line interface for running the complete home
analysis pipeline. It loads data from CSV and JSON, applies kill-switch filters,
scores properties, and generates ranked output.

Usage:
    # Run with defaults (data/phx_homes.csv, data/enrichment_data.json)
    python scripts/analyze.py

    # Run with custom input files
    python scripts/analyze.py --input data/phx_homes.csv --enrichment data/enrichment_data.json

    # Run with custom output location
    python scripts/analyze.py --output reports/csv/results.csv

    # Analyze single property
    python scripts/analyze.py --single "123 Main St, Phoenix, AZ 85001"

    # Verbose output
    python scripts/analyze.py --verbose

Exit Codes:
    0 - Success
    1 - General error
    2 - File not found error
    3 - Data loading error
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phx_home_analysis import AnalysisPipeline, AppConfig, ProjectPaths
from phx_home_analysis.repositories import DataLoadError, DataSaveError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output.

    Args:
        verbose: If True, enable DEBUG level logging. Otherwise INFO level.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="PHX Home Analysis - Analyze Phoenix area home listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults
  python scripts/analyze.py

  # Custom input files
  python scripts/analyze.py --input data/phx_homes.csv --enrichment data/enrichment_data.json

  # Analyze single property
  python scripts/analyze.py --single "123 Main St, Phoenix, AZ 85001"

  # Verbose output
  python scripts/analyze.py --verbose
        """,
    )

    parser.add_argument(
        "-i", "--input",
        type=Path,
        help="Input CSV file with property listings (default: data/phx_homes.csv)",
    )

    parser.add_argument(
        "-e", "--enrichment",
        type=Path,
        help="Enrichment JSON file with manual data (default: data/enrichment_data.json)",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output CSV file for ranked results (default: reports/csv/phx_homes_ranked.csv)",
    )

    parser.add_argument(
        "-s", "--single",
        type=str,
        help="Analyze single property by full address",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug output",
    )

    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Base directory for project (default: current directory)",
    )

    return parser.parse_args()


def run_pipeline(
    input_csv: Path | None = None,
    enrichment_json: Path | None = None,
    output_csv: Path | None = None,
    base_dir: Path | None = None,
) -> int:
    """Run the complete analysis pipeline.

    Args:
        input_csv: Path to input CSV file
        enrichment_json: Path to enrichment JSON file
        output_csv: Path to output CSV file
        base_dir: Base directory for project

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Build config with custom paths if provided
        if input_csv or enrichment_json or output_csv:
            paths = ProjectPaths.from_base_dir(base_dir)

            # Override specific paths if provided
            if input_csv:
                paths = ProjectPaths(
                    base_dir=paths.base_dir,
                    input_csv=input_csv,
                    enrichment_json=paths.enrichment_json,
                    output_csv=paths.output_csv,
                )
            if enrichment_json:
                paths = ProjectPaths(
                    base_dir=paths.base_dir,
                    input_csv=paths.input_csv,
                    enrichment_json=enrichment_json,
                    output_csv=paths.output_csv,
                )
            if output_csv:
                paths = ProjectPaths(
                    base_dir=paths.base_dir,
                    input_csv=paths.input_csv,
                    enrichment_json=paths.enrichment_json,
                    output_csv=output_csv,
                )

            config = AppConfig.default(base_dir=base_dir)
            config = AppConfig(
                paths=paths,
                buyer=config.buyer,
                arizona=config.arizona,
            )
        else:
            config = AppConfig.default(base_dir=base_dir)

        # Verify input files exist
        if not config.paths.input_csv.exists():
            logging.error(f"Input CSV not found: {config.paths.input_csv}")
            return 2

        if not config.paths.enrichment_json.exists():
            logging.error(f"Enrichment JSON not found: {config.paths.enrichment_json}")
            return 2

        # Ensure output directory exists
        config.paths.output_csv.parent.mkdir(parents=True, exist_ok=True)

        # Create and run pipeline
        pipeline = AnalysisPipeline(config=config)
        result = pipeline.run()

        # Print summary
        print()
        print(result.summary_text())

        return 0

    except DataLoadError as e:
        logging.error(f"Data loading error: {e}")
        return 3
    except DataSaveError as e:
        logging.error(f"Data saving error: {e}")
        return 3
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def analyze_single_property(
    address: str,
    base_dir: Path | None = None,
) -> int:
    """Analyze a single property by address.

    Args:
        address: Full address to search for
        base_dir: Base directory for project

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        config = AppConfig.default(base_dir=base_dir)

        # Verify input files exist
        if not config.paths.input_csv.exists():
            logging.error(f"Input CSV not found: {config.paths.input_csv}")
            return 2

        if not config.paths.enrichment_json.exists():
            logging.error(f"Enrichment JSON not found: {config.paths.enrichment_json}")
            return 2

        # Create pipeline and analyze
        pipeline = AnalysisPipeline(config=config)
        property_obj = pipeline.analyze_single(address)

        if not property_obj:
            logging.error(f"Property not found: {address}")
            return 2

        # Print results
        print()
        print("="*70)
        print(f"PROPERTY ANALYSIS: {property_obj.full_address}")
        print("="*70)
        print(f"Price: {property_obj.price} ({property_obj.beds} bed, {property_obj.baths} bath)")
        print(f"Sqft: {property_obj.sqft:,}")
        print(f"Lot: {property_obj.lot_sqft:,} sqft" if property_obj.lot_sqft else "Lot: Unknown")
        print(f"Year Built: {property_obj.year_built}" if property_obj.year_built else "Year Built: Unknown")
        print()

        if property_obj.kill_switch_passed:
            print("KILL SWITCH: PASSED")
            if property_obj.score_breakdown:
                print(f"TOTAL SCORE: {property_obj.score_breakdown.total_score:.1f}/600")
                print(f"TIER: {property_obj.tier.value.upper()}")
                print()
                print("Score Breakdown:")
                print(f"  Location: {property_obj.score_breakdown.location_total:.1f}/230")
                print(f"  Systems:  {property_obj.score_breakdown.systems_total:.1f}/180")
                print(f"  Interior: {property_obj.score_breakdown.interior_total:.1f}/190")
        else:
            print("KILL SWITCH: FAILED")
            print("Failure reasons:")
            for failure in property_obj.kill_switch_failures:
                print(f"  - {failure}")

        print("="*70)
        print()

        return 0

    except DataLoadError as e:
        logging.error(f"Data loading error: {e}")
        return 3
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code
    """
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Single property analysis mode
    if args.single:
        return analyze_single_property(
            address=args.single,
            base_dir=args.base_dir,
        )

    # Full pipeline mode
    return run_pipeline(
        input_csv=args.input,
        enrichment_json=args.enrichment,
        output_csv=args.output,
        base_dir=args.base_dir,
    )


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Measure and save quality baseline metrics.

This script measures current data quality across all properties and saves
baseline metrics to track improvement over time. Unlike quality_check.py
(which is a CI/CD gate that fails if quality < threshold), this script is
designed to be run BEFORE making changes to establish a baseline.

Usage:
    python scripts/quality_baseline.py                    # Measure and display
    python scripts/quality_baseline.py --save             # Save to baseline file
    python scripts/quality_baseline.py --compare          # Compare to saved baseline
    python scripts/quality_baseline.py --output FILE      # Custom output file
    python scripts/quality_baseline.py --verbose          # Show per-property details

Exit Codes:
    0 - Success
    1 - Error (no data found, file not found, etc.)
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phx_home_analysis.services.quality import (
    QualityMetricsCalculator,
    LineageTracker,
    QualityScore,
)

# Default paths
DEFAULT_BASELINE_FILE = Path("data/quality_baseline.json")
DEFAULT_DATA_DIR = Path("data")


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the quality baseline script.

    Args:
        verbose: Enable debug logging if True.

    Returns:
        Configured logger instance.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def load_property_data(data_dir: Path) -> list[dict[str, Any]]:
    """Load property data from enrichment JSON and CSV.

    Prefers enrichment_data.json as the primary source since it contains
    the most complete data. Falls back to phx_homes.csv if needed.

    Args:
        data_dir: Path to data directory.

    Returns:
        List of property data dictionaries.

    Raises:
        FileNotFoundError: If no data files are found.
    """
    properties = []

    # Try to load from enrichment_data.json
    enrichment_file = data_dir / "enrichment_data.json"
    if enrichment_file.exists():
        with open(enrichment_file, encoding="utf-8") as f:
            enrichment = json.load(f)

        # Handle both list and dict formats
        if isinstance(enrichment, list):
            # List format: each item has full_address field
            for item in enrichment:
                prop_data = {"address": item.get("full_address", "")}
                prop_data.update(item)
                properties.append(prop_data)
        elif isinstance(enrichment, dict):
            # Dict format: address is the key
            for address, data in enrichment.items():
                prop_data = {"address": address}
                prop_data.update(data)
                properties.append(prop_data)

    # Fallback: try CSV file
    if not properties:
        csv_file = data_dir / "phx_homes.csv"
        if csv_file.exists():
            with open(csv_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize field names and convert types
                    prop_data = {
                        "address": row.get("full_address", row.get("address", "")),
                        "beds": int(row.get("beds", 0)) if row.get("beds") else None,
                        "baths": float(row.get("baths", 0)) if row.get("baths") else None,
                        "sqft": int(row.get("sqft", 0)) if row.get("sqft") else None,
                        "price": row.get("price_num", row.get("price")),
                        "lot_sqft": int(row.get("lot_sqft", 0)) if row.get("lot_sqft") else None,
                        "year_built": int(row.get("year_built", 0)) if row.get("year_built") else None,
                        "garage_spaces": int(row.get("garage_spaces", 0)) if row.get("garage_spaces") else None,
                        "sewer_type": row.get("sewer_type"),
                    }
                    properties.append(prop_data)

    if not properties:
        raise FileNotFoundError(
            f"No property data found in {data_dir}. "
            "Expected enrichment_data.json or phx_homes.csv"
        )

    return properties


def load_confidences(data_dir: Path) -> dict[str, dict[str, float]]:
    """Load field confidence data from lineage tracker.

    Args:
        data_dir: Path to data directory.

    Returns:
        Dictionary mapping addresses to field confidence dictionaries.
    """
    lineage_file = data_dir / "field_lineage.json"
    if not lineage_file.exists():
        return {}

    try:
        tracker = LineageTracker(lineage_file)
        # The tracker stores by property hash
        # For now, return empty if no lineage data
        return {}
    except Exception:
        return {}


def measure_baseline(
    data_dir: Path,
    logger: Optional[logging.Logger] = None,
) -> dict[str, Any]:
    """Measure current quality metrics across all properties.

    Args:
        data_dir: Path to data directory.
        logger: Optional logger for output.

    Returns:
        Dictionary with baseline metrics including:
        - avg_completeness: Average field completeness across properties
        - avg_confidence: Average high-confidence percentage
        - avg_overall: Average overall quality score
        - property_count: Number of properties analyzed
        - quality_tiers: Count of properties in each tier
        - missing_fields_freq: Frequency of each missing field
        - low_quality_count: Properties below 80% quality
    """
    logger = logger or logging.getLogger(__name__)

    # Load data
    properties = load_property_data(data_dir)
    confidences = load_confidences(data_dir)

    logger.info(f"Loaded {len(properties)} properties from {data_dir}")

    # Calculate quality for each property
    calculator = QualityMetricsCalculator()
    scores, aggregate = calculator.calculate_batch(properties, confidences)

    # Count quality tiers
    tier_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    for score in scores:
        tier_counts[score.quality_tier] += 1

    # Count missing field frequency
    missing_field_freq: dict[str, int] = {}
    for score in scores:
        for field in score.missing_fields:
            missing_field_freq[field] = missing_field_freq.get(field, 0) + 1

    # Count low quality properties (below 80%)
    low_quality_count = sum(1 for s in scores if s.overall_score < 0.80)

    # Build metrics dictionary
    metrics = {
        "avg_completeness": aggregate.completeness,
        "avg_confidence": aggregate.high_confidence_pct,
        "avg_overall": aggregate.overall_score,
        "property_count": len(properties),
        "quality_tiers": tier_counts,
        "missing_fields_freq": dict(sorted(
            missing_field_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )),
        "low_quality_count": low_quality_count,
        "excellent_pct": tier_counts["excellent"] / len(properties) if properties else 0,
        "passing_pct": (tier_counts["excellent"] + tier_counts["good"]) / len(properties) if properties else 0,
    }

    return metrics


def save_baseline(
    metrics: dict[str, Any],
    output_path: Path,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Save baseline metrics to JSON file.

    Args:
        metrics: Dictionary of baseline metrics.
        output_path: Path to save the baseline file.
        logger: Optional logger for output.
    """
    logger = logger or logging.getLogger(__name__)

    baseline = {
        "measured_at": datetime.now().isoformat(),
        "version": "1.0",
        "metrics": metrics,
    }

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    logger.info(f"Baseline saved to {output_path}")


def load_baseline(baseline_path: Path) -> dict[str, Any]:
    """Load saved baseline metrics.

    Args:
        baseline_path: Path to the baseline JSON file.

    Returns:
        Dictionary containing baseline data.

    Raises:
        FileNotFoundError: If baseline file doesn't exist.
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")

    with open(baseline_path, encoding="utf-8") as f:
        return json.load(f)


def compare_to_baseline(
    current: dict[str, Any],
    baseline_path: Path,
    logger: Optional[logging.Logger] = None,
) -> dict[str, Any]:
    """Compare current metrics to saved baseline.

    Args:
        current: Current metrics dictionary.
        baseline_path: Path to saved baseline file.
        logger: Optional logger for output.

    Returns:
        Dictionary with comparison results.
    """
    logger = logger or logging.getLogger(__name__)

    baseline = load_baseline(baseline_path)
    baseline_metrics = baseline["metrics"]

    print()
    print("=" * 60)
    print("Quality Improvement Report")
    print("=" * 60)
    print(f"Baseline from: {baseline['measured_at']}")
    print(f"Current time:  {datetime.now().isoformat()}")
    print()

    # Compare core metrics
    comparison_fields = [
        ("avg_completeness", "Completeness"),
        ("avg_confidence", "High Confidence"),
        ("avg_overall", "Overall Score"),
        ("excellent_pct", "Excellent Tier %"),
        ("passing_pct", "Passing (Good+) %"),
    ]

    deltas = {}
    print("-" * 60)
    print(f"{'Metric':<25} {'Baseline':>12} {'Current':>12} {'Delta':>12}")
    print("-" * 60)

    for key, label in comparison_fields:
        old = baseline_metrics.get(key, 0)
        new = current.get(key, 0)
        delta = new - old
        deltas[key] = delta

        # Format arrow indicator
        if delta > 0.001:
            arrow = "+"
            indicator = "IMPROVED"
        elif delta < -0.001:
            arrow = ""
            indicator = "DECLINED"
        else:
            arrow = ""
            indicator = "="

        print(f"{label:<25} {old:>11.1%} {new:>11.1%} {arrow}{delta:>+10.1%}")

    print("-" * 60)

    # Compare property counts
    old_count = baseline_metrics.get("property_count", 0)
    new_count = current.get("property_count", 0)
    print(f"{'Property Count':<25} {old_count:>12} {new_count:>12} {new_count - old_count:>+12}")

    old_low = baseline_metrics.get("low_quality_count", 0)
    new_low = current.get("low_quality_count", 0)
    print(f"{'Low Quality (<80%)':<25} {old_low:>12} {new_low:>12} {new_low - old_low:>+12}")

    print("-" * 60)

    # Compare tier distribution
    print("\nQuality Tier Distribution:")
    print(f"{'Tier':<15} {'Baseline':>12} {'Current':>12} {'Delta':>12}")
    print("-" * 51)

    old_tiers = baseline_metrics.get("quality_tiers", {})
    new_tiers = current.get("quality_tiers", {})

    for tier in ["excellent", "good", "fair", "poor"]:
        old_val = old_tiers.get(tier, 0)
        new_val = new_tiers.get(tier, 0)
        delta = new_val - old_val
        print(f"{tier.capitalize():<15} {old_val:>12} {new_val:>12} {delta:>+12}")

    print()

    # Summary
    overall_delta = deltas.get("avg_overall", 0)
    if overall_delta > 0.05:
        print("SUMMARY: Significant quality improvement detected!")
    elif overall_delta > 0:
        print("SUMMARY: Quality improved since baseline.")
    elif overall_delta < -0.05:
        print("SUMMARY: WARNING - Quality has declined significantly!")
    elif overall_delta < 0:
        print("SUMMARY: Quality has declined slightly since baseline.")
    else:
        print("SUMMARY: Quality unchanged from baseline.")

    return {
        "deltas": deltas,
        "baseline_date": baseline["measured_at"],
        "current_date": datetime.now().isoformat(),
    }


def display_metrics(
    metrics: dict[str, Any],
    verbose: bool = False,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Display current quality metrics in a formatted report.

    Args:
        metrics: Dictionary of quality metrics.
        verbose: Show detailed breakdown if True.
        logger: Optional logger for output.
    """
    logger = logger or logging.getLogger(__name__)

    print()
    print("=" * 60)
    print("Current Quality Metrics")
    print("=" * 60)
    print(f"Measured at: {datetime.now().isoformat()}")
    print()

    # Core metrics
    print("-" * 60)
    print(f"{'Metric':<30} {'Value':>15}")
    print("-" * 60)
    print(f"{'Total Properties':<30} {metrics['property_count']:>15}")
    print(f"{'Average Completeness':<30} {metrics['avg_completeness']:>14.1%}")
    print(f"{'Average Confidence':<30} {metrics['avg_confidence']:>14.1%}")
    print(f"{'Average Overall Score':<30} {metrics['avg_overall']:>14.1%}")
    print("-" * 60)

    # Quality tier breakdown
    print("\nQuality Tier Distribution:")
    print(f"{'Tier':<15} {'Count':>10} {'Percentage':>15}")
    print("-" * 40)

    tiers = metrics.get("quality_tiers", {})
    total = metrics["property_count"]

    for tier in ["excellent", "good", "fair", "poor"]:
        count = tiers.get(tier, 0)
        pct = count / total if total else 0
        print(f"{tier.capitalize():<15} {count:>10} {pct:>14.1%}")

    print("-" * 40)
    print(f"{'Passing (Good+)':<15} {tiers.get('excellent', 0) + tiers.get('good', 0):>10} {metrics['passing_pct']:>14.1%}")
    print()

    # Missing fields (if any)
    missing_freq = metrics.get("missing_fields_freq", {})
    if missing_freq:
        print("Most Frequently Missing Fields:")
        print(f"{'Field':<25} {'Missing Count':>15} {'% Missing':>15}")
        print("-" * 55)

        for field, count in list(missing_freq.items())[:10]:
            pct = count / total if total else 0
            print(f"{field:<25} {count:>15} {pct:>14.1%}")

        if len(missing_freq) > 10:
            print(f"... and {len(missing_freq) - 10} more fields")
        print()

    # Summary assessment
    overall = metrics["avg_overall"]
    if overall >= 0.95:
        assessment = "EXCELLENT - Data quality is production-ready"
    elif overall >= 0.80:
        assessment = "GOOD - Minor improvements recommended"
    elif overall >= 0.60:
        assessment = "FAIR - Significant gaps need attention"
    else:
        assessment = "POOR - Critical data quality issues"

    print(f"Assessment: {assessment}")
    print()


def main() -> int:
    """Main entry point for quality baseline script.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    parser = argparse.ArgumentParser(
        description="Measure and save quality baseline metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Measure and display current quality
    python scripts/quality_baseline.py

    # Save baseline before making changes
    python scripts/quality_baseline.py --save

    # Compare current quality to saved baseline
    python scripts/quality_baseline.py --compare

    # Save to custom file
    python scripts/quality_baseline.py --save --output data/baseline_v2.json
        """,
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save metrics to baseline file",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare current metrics to saved baseline",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BASELINE_FILE,
        help=f"Baseline file path (default: {DEFAULT_BASELINE_FILE})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Data directory path (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    try:
        # Measure current metrics
        metrics = measure_baseline(args.data_dir, logger)

        if args.compare:
            # Compare to saved baseline
            try:
                compare_to_baseline(metrics, args.output, logger)
            except FileNotFoundError as e:
                logger.error(str(e))
                logger.info("Run with --save first to create a baseline")
                return 1
        elif args.save:
            # Save baseline
            save_baseline(metrics, args.output, logger)
            display_metrics(metrics, args.verbose, logger)
            print(f"Baseline saved to: {args.output}")
        else:
            # Just display current metrics
            display_metrics(metrics, args.verbose, logger)

        return 0

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

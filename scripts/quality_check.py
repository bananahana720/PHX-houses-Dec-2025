#!/usr/bin/env python
"""CI/CD quality gate - fail if quality < 95%.

This script loads all property data and calculates quality metrics.
It exits with code 1 if average quality is below 95%, exit code 0 otherwise.

Usage:
    python scripts/quality_check.py [--threshold 0.95] [--verbose]

Exit Codes:
    0 - Quality gate passed
    1 - Quality gate failed (below threshold)
    2 - Error loading data or configuration issue
"""

import argparse
import logging
import sys
from pathlib import Path

# Requires: uv pip install -e .
from phx_home_analysis.services.quality import (
    LineageTracker,
    QualityMetricsCalculator,
)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the quality check script.

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


def load_property_data(data_dir: Path) -> list[dict]:
    """Load property data from enrichment JSON and CSV using cache.

    Args:
        data_dir: Path to data directory.

    Returns:
        List of property data dictionaries.
    """
    from phx_home_analysis.services.data_cache import PropertyDataCache

    cache = PropertyDataCache()
    properties = []

    # Try to load from enrichment_data.json
    enrichment_file = data_dir / "enrichment_data.json"
    if enrichment_file.exists():
        enrichment = cache.get_enrichment_data(enrichment_file)

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
            csv_data = cache.get_csv_data(csv_file)
            for row in csv_data:
                # Normalize field names
                prop_data = {
                    "address": row.get("full_address", row.get("address", "")),
                    "beds": int(row.get("beds", 0)) if row.get("beds") else None,
                    "baths": float(row.get("baths", 0)) if row.get("baths") else None,
                    "sqft": int(row.get("sqft", 0)) if row.get("sqft") else None,
                    "price": row.get("price_num", row.get("price")),
                }
                properties.append(prop_data)

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

    tracker = LineageTracker(lineage_file)
    confidences = {}

    # The tracker stores by property hash, but we need to map to addresses
    # For now, return empty if no lineage data
    # In production, you'd maintain a hash-to-address mapping

    return confidences


def main() -> int:
    """Main entry point for quality check script.

    Returns:
        Exit code: 0 for pass, 1 for fail, 2 for error.
    """
    parser = argparse.ArgumentParser(
        description="CI/CD quality gate - check property data quality"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Quality threshold (default: 0.95 = 95%%)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Path to data directory (default: data/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Fail if no property data found",
    )

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        logger.error("Threshold must be between 0.0 and 1.0")
        return 2

    logger.info("=" * 60)
    logger.info("PHX Home Analysis - Quality Gate Check")
    logger.info("=" * 60)
    logger.info(f"Threshold: {args.threshold:.1%}")
    logger.info(f"Data directory: {args.data_dir}")

    # Load property data
    try:
        properties = load_property_data(args.data_dir)
    except Exception as e:
        logger.error(f"Failed to load property data: {e}")
        return 2

    if not properties:
        if args.fail_on_missing:
            logger.error("No property data found")
            return 1
        else:
            logger.warning("No property data found - skipping quality check")
            return 0

    logger.info(f"Loaded {len(properties)} properties")

    # Load confidence data
    try:
        confidences = load_confidences(args.data_dir)
    except Exception as e:
        logger.warning(f"Failed to load confidence data: {e}")
        confidences = {}

    # Calculate quality metrics
    calculator = QualityMetricsCalculator()
    scores, aggregate = calculator.calculate_batch(properties, confidences)

    # Report results
    logger.info("-" * 60)
    logger.info("Quality Metrics Summary")
    logger.info("-" * 60)
    logger.info(f"Completeness:      {aggregate.completeness:.1%}")
    logger.info(f"High Confidence:   {aggregate.high_confidence_pct:.1%}")
    logger.info(f"Overall Score:     {aggregate.overall_score:.1%}")
    logger.info(f"Quality Tier:      {aggregate.quality_tier.upper()}")

    if aggregate.missing_fields:
        logger.info(f"Missing Fields:    {', '.join(aggregate.missing_fields)}")

    if aggregate.low_confidence_fields:
        logger.info(
            f"Low Confidence:    {', '.join(aggregate.low_confidence_fields)}"
        )

    # Individual property stats
    passing = sum(1 for s in scores if s.overall_score >= args.threshold)
    failing = len(scores) - passing
    logger.info(f"Properties Passing: {passing}/{len(scores)}")

    if failing > 0 and args.verbose:
        logger.info("-" * 60)
        logger.info("Low Quality Properties:")
        for i, score in enumerate(scores):
            if score.overall_score < args.threshold:
                addr = properties[i].get("address", f"Property {i}")
                logger.info(f"  - {addr}: {score.overall_score:.1%}")

    # Generate improvement suggestions
    suggestions = calculator.get_improvement_suggestions(aggregate)
    if suggestions and aggregate.overall_score < args.threshold:
        logger.info("-" * 60)
        logger.info("Improvement Suggestions:")
        for suggestion in suggestions:
            logger.info(f"  - {suggestion}")

    logger.info("-" * 60)

    # Quality gate decision
    if aggregate.overall_score >= args.threshold:
        logger.info(f"PASSED: Quality score {aggregate.overall_score:.1%} >= {args.threshold:.1%}")
        return 0
    else:
        logger.error(
            f"FAILED: Quality score {aggregate.overall_score:.1%} < {args.threshold:.1%}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

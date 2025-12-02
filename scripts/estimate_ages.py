"""CLI script for programmatic age estimation of roof, HVAC, and pool equipment.

Provides fallback age estimation when visual analysis is unavailable or incomplete.
Uses Arizona-specific assumptions for equipment lifespans and replacement cycles.

Features:
- Arizona-specific estimation models for roof, HVAC, and pool equipment
- Single property or batch processing
- Confidence metadata for estimated values
- Research task tracking and completion marking
- Dry-run mode for preview before committing changes
- Atomic file updates with state preservation

Usage:
    # Single property
    python scripts/estimate_ages.py --property "4209 W Wahalla Ln, Glendale, AZ 85308"

    # All properties with null ages
    python scripts/estimate_ages.py --all

    # Dry run (show what would be estimated)
    python scripts/estimate_ages.py --all --dry-run

    # Verbose output
    python scripts/estimate_ages.py --all -v
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class EstimationResult:
    """Result of age estimation for a single property."""

    full_address: str
    year_built: int
    roof_age: Optional[int]
    roof_confidence: str
    hvac_age: Optional[int]
    hvac_confidence: str
    pool_equipment_age: Optional[int]
    pool_confidence: str
    has_pool: bool


def estimate_roof_age(year_built: int) -> tuple[int, str]:
    """Estimate roof age based on property year built.

    Arizona tile roofs typically last 20-30 years, asphalt shingles 15-20 years.
    This estimation assumes typical replacement cycles.

    Args:
        year_built: Year the property was originally built

    Returns:
        Tuple of (estimated_age_years, confidence_string)
    """
    current_year = 2025
    property_age = current_year - year_built

    if property_age <= 20:
        # Likely original roof (tile/shingle)
        return (property_age, "estimated_original")
    elif property_age <= 40:
        # Likely one replacement cycle
        return (max(0, property_age - 20), "estimated_one_replacement")
    else:
        # Multiple replacement cycles - estimate based on typical 25-year cycle
        return (min(10, property_age % 25), "estimated_multiple_replacements")


def estimate_hvac_age(year_built: int) -> tuple[int, str]:
    """Estimate HVAC system age based on property year built.

    Arizona HVAC systems have shorter lifespans (10-15 years) due to extreme heat
    and year-round cooling demands compared to other climates.

    Args:
        year_built: Year the property was originally built

    Returns:
        Tuple of (estimated_age_years, confidence_string)
    """
    current_year = 2025
    property_age = current_year - year_built

    if property_age <= 15:
        # Likely original or first major repair
        return (property_age, "estimated_original")
    else:
        # Estimate based on 12-year replacement cycle
        return (property_age % 12, "estimated_replacement_cycle")


def estimate_pool_equipment_age(year_built: int, has_pool: bool) -> tuple[Optional[int], str]:
    """Estimate pool equipment age based on property year built.

    Pool equipment in Arizona lasts approximately 8-12 years due to intense
    UV exposure, heat cycling, and mineral-heavy water.

    Args:
        year_built: Year the property was originally built
        has_pool: Whether the property has a pool

    Returns:
        Tuple of (estimated_age_years, confidence_string)
        Returns (None, "no_pool") if property has no pool
    """
    if not has_pool:
        return (None, "no_pool")

    current_year = 2025
    property_age = current_year - year_built

    # Estimate based on 10-year replacement cycle for pool equipment
    return (min(10, property_age % 10), "estimated_replacement_cycle")


def load_enrichment_data(path: Path) -> list[dict]:
    """Load enrichment data from JSON file.

    Args:
        path: Path to enrichment_data.json

    Returns:
        List of property enrichment dictionaries

    Raises:
        FileNotFoundError: If enrichment data file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    if not path.exists():
        raise FileNotFoundError(f"Enrichment data file not found: {path}")

    with open(path, "r") as f:
        return json.load(f)


def load_research_tasks(path: Path) -> dict:
    """Load research task tracking file.

    Args:
        path: Path to research_tasks.json

    Returns:
        Research tasks dictionary with pending_tasks and completed_tasks

    Raises:
        FileNotFoundError: If research tasks file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    if not path.exists():
        # Initialize if doesn't exist
        return {
            "$schema": "research_tasks_v1",
            "pending_tasks": [],
            "completed_tasks": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    with open(path, "r") as f:
        return json.load(f)


def save_enrichment_data(data: list[dict], path: Path) -> None:
    """Save enrichment data to JSON file with atomic write.

    Uses temp file + rename pattern to ensure atomicity.

    Args:
        data: List of property enrichment dictionaries
        path: Path to enrichment_data.json
    """
    # Create temp file in same directory for atomic rename
    temp_path = path.with_stem(path.stem + ".tmp")

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        # Atomic rename
        temp_path.replace(path)
    except Exception as e:
        # Cleanup temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def save_research_tasks(data: dict, path: Path) -> None:
    """Save research tasks to JSON file with atomic write.

    Args:
        data: Research tasks dictionary
        path: Path to research_tasks.json
    """
    # Update timestamp
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    temp_path = path.with_stem(path.stem + ".tmp")

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise


def find_properties_needing_estimates(
    enrichment_data: list[dict],
) -> list[dict]:
    """Find properties with missing age estimates.

    Args:
        enrichment_data: List of enrichment data dictionaries

    Returns:
        Filtered list of properties needing age estimates
    """
    needs_estimate = []
    for prop in enrichment_data:
        # Check if any age field is missing
        if (
            prop.get("roof_age") is None
            or prop.get("hvac_age") is None
            or (prop.get("has_pool") and prop.get("pool_equipment_age") is None)
        ):
            needs_estimate.append(prop)

    return needs_estimate


def estimate_property_ages(enrichment_data: list[dict], property_address: Optional[str] = None) -> list[EstimationResult]:
    """Estimate ages for properties.

    Args:
        enrichment_data: List of enrichment data dictionaries
        property_address: Specific address to estimate, or None for all needing estimates

    Returns:
        List of EstimationResult objects

    Raises:
        ValueError: If property address not found
    """
    results = []

    if property_address:
        # Single property lookup
        prop = None
        for p in enrichment_data:
            if p.get("full_address") == property_address:
                prop = p
                break

        if not prop:
            raise ValueError(f"Property not found: {property_address}")

        properties = [prop]
    else:
        # All properties needing estimates
        properties = find_properties_needing_estimates(enrichment_data)

    for prop in properties:
        year_built = prop.get("year_built")
        if not year_built:
            continue

        roof_age, roof_conf = estimate_roof_age(year_built)
        hvac_age, hvac_conf = estimate_hvac_age(year_built)
        pool_age, pool_conf = estimate_pool_equipment_age(year_built, prop.get("has_pool", False))

        results.append(
            EstimationResult(
                full_address=prop.get("full_address", ""),
                year_built=year_built,
                roof_age=roof_age,
                roof_confidence=roof_conf,
                hvac_age=hvac_age,
                hvac_confidence=hvac_conf,
                pool_equipment_age=pool_age,
                pool_confidence=pool_conf,
                has_pool=prop.get("has_pool", False),
            )
        )

    return results


def apply_estimations(
    enrichment_data: list[dict],
    estimations: list[EstimationResult],
) -> list[dict]:
    """Apply estimation results back to enrichment data.

    Updates properties with estimated ages and confidence metadata.

    Args:
        enrichment_data: Original enrichment data list
        estimations: List of EstimationResult objects

    Returns:
        Updated enrichment data list
    """
    # Create lookup map for quick updates
    estimations_map = {e.full_address: e for e in estimations}

    for prop in enrichment_data:
        addr = prop.get("full_address")
        if addr not in estimations_map:
            continue

        est = estimations_map[addr]

        # Only update if currently null
        if prop.get("roof_age") is None:
            prop["roof_age"] = est.roof_age
            prop["roof_age_confidence"] = est.roof_confidence

        if prop.get("hvac_age") is None:
            prop["hvac_age"] = est.hvac_age
            prop["hvac_age_confidence"] = est.hvac_confidence

        if prop.get("has_pool") and prop.get("pool_equipment_age") is None:
            prop["pool_equipment_age"] = est.pool_equipment_age
            prop["pool_equipment_age_confidence"] = est.pool_confidence

    return enrichment_data


def mark_tasks_completed(research_tasks: dict, completed_count: int) -> dict:
    """Mark age estimation tasks as completed in research task tracking.

    Args:
        research_tasks: Research tasks dictionary
        completed_count: Number of properties estimated

    Returns:
        Updated research tasks dictionary
    """
    task = {
        "task_type": "age_estimation",
        "description": f"Estimated roof, HVAC, and pool equipment ages for {completed_count} properties",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "properties_updated": completed_count,
    }

    if "completed_tasks" not in research_tasks:
        research_tasks["completed_tasks"] = []

    research_tasks["completed_tasks"].append(task)

    return research_tasks


def print_banner(total_properties: int, dry_run: bool) -> None:
    """Print startup banner.

    Args:
        total_properties: Number of properties to process
        dry_run: Whether this is a dry run
    """
    print()
    print("=" * 60)
    print("Age Estimation Pipeline")
    print("=" * 60)
    print(f"Properties to process: {total_properties}")
    print(f"Mode: {'Dry run (preview only)' if dry_run else 'Live update'}")
    print("=" * 60)
    print()


def print_estimations(results: list[EstimationResult]) -> None:
    """Print estimation results.

    Args:
        results: List of EstimationResult objects
    """
    if not results:
        print("No properties requiring estimates found.")
        return

    print(f"Estimations for {len(results)} properties:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result.full_address}")
        print(f"   Year Built: {result.year_built}")
        print(f"   Roof: {result.roof_age} years ({result.roof_confidence})")
        print(f"   HVAC: {result.hvac_age} years ({result.hvac_confidence})")

        if result.has_pool:
            print(f"   Pool Equipment: {result.pool_equipment_age} years ({result.pool_confidence})")
        else:
            print(f"   Pool Equipment: N/A (no pool)")

        print()


def print_summary(results: list[EstimationResult], dry_run: bool) -> None:
    """Print summary statistics.

    Args:
        results: List of EstimationResult objects
        dry_run: Whether this was a dry run
    """
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Properties processed: {len(results)}")

    if dry_run:
        print("Status: DRY RUN (no changes committed)")
    else:
        print("Status: Changes saved to enrichment_data.json")
        print("        Tasks recorded in research_tasks.json")

    print("=" * 60)
    print()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Estimate property ages (roof, HVAC, pool equipment) based on year built",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Property selection (mutually exclusive)
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument(
        "--all",
        action="store_true",
        help="Estimate ages for all properties with missing age data",
    )
    selection_group.add_argument(
        "--property",
        type=str,
        help="Estimate ages for a single property by full address",
    )

    # Operation modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview estimations without writing to files",
    )

    # Output control
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    # Configuration
    parser.add_argument(
        "--enrichment-data",
        type=Path,
        default=Path("data/enrichment_data.json"),
        help="Path to enrichment data file (default: data/enrichment_data.json)",
    )
    parser.add_argument(
        "--research-tasks",
        type=Path,
        default=Path("data/research_tasks.json"),
        help="Path to research tasks file (default: data/research_tasks.json)",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    """Main execution function.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    args = parse_args()

    # Configure logging
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Load enrichment data
        logger.info(f"Loading enrichment data from {args.enrichment_data}")
        enrichment_data = load_enrichment_data(args.enrichment_data)

        # Determine target properties
        if args.all:
            target_properties = find_properties_needing_estimates(enrichment_data)
        else:
            # Single property - we'll validate it exists during estimation
            target_properties = None

        # Print banner
        if args.all:
            print_banner(len(target_properties) if target_properties else 0, args.dry_run)
        else:
            print_banner(1, args.dry_run)

        # Estimate ages
        try:
            if args.property:
                results = estimate_property_ages(enrichment_data, args.property)
            else:
                results = estimate_property_ages(enrichment_data)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Print estimations
        print_estimations(results)

        # Apply estimations if not dry run
        if not args.dry_run and results:
            logger.info(f"Applying estimations to {len(results)} properties")
            enrichment_data = apply_estimations(enrichment_data, results)

            # Save enrichment data
            logger.info(f"Saving enrichment data to {args.enrichment_data}")
            save_enrichment_data(enrichment_data, args.enrichment_data)

            # Load and update research tasks
            logger.info(f"Loading research tasks from {args.research_tasks}")
            research_tasks = load_research_tasks(args.research_tasks)

            logger.info("Marking age estimation tasks as completed")
            research_tasks = mark_tasks_completed(research_tasks, len(results))

            logger.info(f"Saving research tasks to {args.research_tasks}")
            save_research_tasks(research_tasks, args.research_tasks)

        # Print summary
        print_summary(results, args.dry_run)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in data file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

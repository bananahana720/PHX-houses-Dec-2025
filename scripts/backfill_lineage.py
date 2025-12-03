#!/usr/bin/env python
"""Backfill lineage data for all properties in enrichment_data.json.

Scans existing enrichment data and creates lineage entries for all fields,
using {field}_source annotations where available, otherwise inferring defaults.

Usage:
    python scripts/backfill_lineage.py
    python scripts/backfill_lineage.py --dry-run  # Preview without saving
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phx_home_analysis.services.quality import DataSource, LineageTracker
from phx_home_analysis.validation.deduplication import compute_property_hash

# Field categories for default source inference
COUNTY_FIELDS = {
    "lot_sqft",
    "year_built",
    "garage_spaces",
    "has_pool",
    "tax_annual",
    "livable_sqft",
    "latitude",
    "longitude",
}

LISTING_FIELDS = {
    "beds",
    "baths",
    "sqft",
    "price",
    "price_num",
    "list_price",
}

MANUAL_FIELDS = {
    "sewer_type",
    "hoa_fee",
    "commute_minutes",
    "school_district",
    "school_rating",
    "orientation",
    "distance_to_grocery_miles",
    "distance_to_highway_miles",
    "solar_status",
    "solar_lease_monthly",
    "pool_equipment_age",
    "roof_age",
    "hvac_age",
    "distance_to_park_miles",
    "safety_neighborhood_score",
    "parks_walkability_score",
    "noise_level",
}

ASSESSMENT_FIELDS = {
    "kitchen_layout_score",
    "master_suite_score",
    "natural_light_score",
    "high_ceilings_score",
    "laundry_area_score",
    "aesthetics_score",
    "backyard_utility_score",
    "fireplace_present",
    "fireplace_score",
    "kitchen_quality_score",
    "master_quality_score",
    "ceiling_height_score",
    "laundry_score",
}

# Source annotation suffixes to check
SOURCE_ANNOTATIONS = ("_source", "_src", "_origin")

# Fields that are metadata or computed (skip these)
SKIP_FIELDS = {
    "full_address",
    "monthly_cost",
    "cost_breakdown",
    "kill_switch_passed",
    "kill_switch_failures",
    "kill_switch_result",
    "interior_assessment_date",
    "_last_updated",
    "_last_county_sync",
}


def infer_source(field_name: str, entry: dict) -> DataSource:
    """Infer data source for a field based on annotations or field type.

    Args:
        field_name: Name of the field
        entry: Full enrichment entry

    Returns:
        Inferred DataSource enum value
    """
    # Check for explicit source annotation
    for suffix in SOURCE_ANNOTATIONS:
        source_field = f"{field_name}{suffix}"
        if source_field in entry:
            source_str = str(entry[source_field]).lower()
            if "manual" in source_str or "user" in source_str:
                return DataSource.MANUAL
            if "web" in source_str:
                return DataSource.WEB_SCRAPE
            if "county" in source_str or "assessor" in source_str or "api" in source_str:
                return DataSource.ASSESSOR_API
            if "listing" in source_str or "csv" in source_str:
                return DataSource.CSV
            if "ai" in source_str or "inference" in source_str:
                return DataSource.AI_INFERENCE
            if "default" in source_str:
                return DataSource.DEFAULT

    # Check for *_confidence fields that indicate estimation
    conf_field = f"{field_name}_confidence"
    if conf_field in entry:
        conf_str = str(entry[conf_field]).lower()
        if "estimated" in conf_str:
            return DataSource.AI_INFERENCE

    # Infer from field category
    if field_name in COUNTY_FIELDS:
        return DataSource.ASSESSOR_API
    if field_name in LISTING_FIELDS:
        return DataSource.CSV
    if field_name in MANUAL_FIELDS:
        return DataSource.MANUAL
    if field_name in ASSESSMENT_FIELDS:
        return DataSource.MANUAL

    # Default
    return DataSource.DEFAULT


def should_skip_field(field_name: str, value) -> bool:
    """Determine if a field should be skipped during backfill.

    Args:
        field_name: Name of the field
        value: Field value

    Returns:
        True if field should be skipped
    """
    # Skip None values
    if value is None:
        return True

    # Skip metadata fields
    if field_name in SKIP_FIELDS:
        return True

    # Skip source annotation fields
    if any(field_name.endswith(suffix) for suffix in SOURCE_ANNOTATIONS):
        return True

    # Skip confidence annotation fields
    if field_name.endswith("_confidence"):
        return True

    # Skip data_source annotation fields
    if field_name.endswith("_data_source"):
        return True

    # Skip private/internal fields
    if field_name.startswith("_"):
        return True

    return False


def backfill_property(
    tracker: LineageTracker,
    prop_hash: str,
    entry: dict,
    dry_run: bool = False,
) -> dict:
    """Backfill lineage for a single property.

    Args:
        tracker: LineageTracker instance
        prop_hash: Property hash
        entry: Enrichment entry dict
        dry_run: If True, don't actually record

    Returns:
        Dict of {field: source} for reporting
    """
    results = {}

    for field, value in entry.items():
        # Skip fields that shouldn't be tracked
        if should_skip_field(field, value):
            continue

        source = infer_source(field, entry)
        results[field] = source.value

        if not dry_run:
            tracker.record_field(
                property_hash=prop_hash,
                field_name=field,
                source=source,
                confidence=source.default_confidence,
                original_value=value,
                notes="Backfilled from enrichment_data.json",
            )

    return results


def main():
    """Main entry point for backfill script."""
    parser = argparse.ArgumentParser(description="Backfill lineage data for enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    parser.add_argument(
        "--enrichment",
        type=Path,
        default=Path("data/enrichment_data.json"),
    )
    parser.add_argument(
        "--lineage",
        type=Path,
        default=Path("data/field_lineage.json"),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Load enrichment data
    print(f"Loading enrichment data from {args.enrichment}")
    with open(args.enrichment, encoding="utf-8") as f:
        data = json.load(f)

    # Handle list format
    if isinstance(data, list):
        entries = {item["full_address"]: item for item in data}
    else:
        entries = data

    print(f"Found {len(entries)} properties")

    # Initialize lineage tracker
    tracker = LineageTracker(args.lineage)
    existing_count = tracker.property_count()
    print(f"Existing lineage records: {existing_count} properties")

    # Count existing total fields
    existing_total_fields = sum(tracker.field_count(compute_property_hash(addr)) for addr in entries)
    print(f"Existing tracked fields: {existing_total_fields}")

    # Backfill each property
    total_fields = 0
    source_counts: dict[str, int] = {}

    for address, entry in entries.items():
        prop_hash = compute_property_hash(address)
        results = backfill_property(tracker, prop_hash, entry, args.dry_run)
        total_fields += len(results)

        # Count by source
        for field, source in results.items():
            source_counts[source] = source_counts.get(source, 0) + 1

        if args.verbose or args.dry_run:
            print(f"\n{address} ({prop_hash}):")
            for field, source in sorted(results.items()):
                print(f"  {field}: {source}")

    # Print source breakdown
    print("\n" + "=" * 60)
    print("Source Breakdown")
    print("=" * 60)
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (count / total_fields * 100) if total_fields else 0
        print(f"  {source:20s}: {count:4d} fields ({pct:5.1f}%)")

    # Save if not dry run
    if not args.dry_run:
        tracker.save()
        new_count = tracker.property_count()

        print("\n" + "=" * 60)
        print("Backfill Complete!")
        print("=" * 60)
        print(f"Properties with lineage: {existing_count} -> {new_count}")
        print(f"Total fields tracked: {total_fields}")
        print(f"Lineage coverage: {new_count}/{len(entries)} properties ({new_count/len(entries)*100:.1f}%)")
    else:
        print(f"\n[DRY RUN] Would track {total_fields} fields for {len(entries)} properties")

    return 0


if __name__ == "__main__":
    sys.exit(main())

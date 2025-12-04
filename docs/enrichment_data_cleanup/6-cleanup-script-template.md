# 6. Cleanup Script Template

**File:** `scripts/cleanup_enrichment_data.py` (SKELETON ONLY)

```python
#!/usr/bin/env python3
"""Clean up enrichment_data.json based on documented plan.

DANGER: This script modifies production data. Use --dry-run first.

Usage:
    python scripts/cleanup_enrichment_data.py --dry-run      # Show changes
    python scripts/cleanup_enrichment_data.py --apply         # Apply changes
    python scripts/cleanup_enrichment_data.py --phase=1       # Phase 1 only
"""

import argparse
import json
from pathlib import Path
from typing import Any

# Phase 1: Remove synonym duplicates
SYNONYM_REMOVALS = {
    "ceiling_height_score": "high_ceilings_score",
    "ceiling_height_score_source": None,  # Remove entirely
    "kitchen_quality_score": "kitchen_layout_score",
    "kitchen_quality_score_source": None,
    "master_quality_score": "master_suite_score",
    "master_quality_score_source": None,
    "laundry_score": "laundry_area_score",
    "laundry_score_source": None,
    "list_price": None,  # Duplicate of CSV
}

# Phase 2: Remove computed fields
COMPUTED_FIELDS = {
    "cost_breakdown",
    "monthly_cost",
    "kill_switch_passed",
    "kill_switch_failures",
    "sqft",  # Duplicate of CSV
    "price",  # Duplicate of CSV
}

# Phase 3: Investigate before removal
ORPHANED_SOURCES = {
    "data_source",
    "distance_to_park_miles_source",
    "orientation_source",
    # ... (17 total - see section 3.1)
}

ORPHANED_CONFIDENCE = {
    "assessment_confidence",
    "confidence_breakdown",
    "image_assessment_confidence",
    "interior_assessment_confidence",
    "interior_confidence",
    "section_c_confidence",
    # Keep: hvac_age_confidence, pool_equipment_age_confidence, roof_age_confidence
}

INTERIOR_ALIASES = {
    "interior_ceilings_score",
    "interior_fireplace_score",
    "interior_kitchen_score",
    "interior_laundry_score",
    "interior_light_score",
    "interior_master_score",
}


def cleanup_property(prop: dict[str, Any], phase: int) -> dict[str, Any]:
    """Remove fields based on cleanup phase.

    Args:
        prop: Property dictionary from enrichment_data.json
        phase: Cleanup phase (1, 2, or 3)

    Returns:
        Cleaned property dictionary
    """
    cleaned = prop.copy()

    if phase >= 1:
        for field, canonical in SYNONYM_REMOVALS.items():
            if canonical is None:
                cleaned.pop(field, None)  # Remove entirely
            else:
                # Could validate they have same value before removal
                cleaned.pop(field, None)

    if phase >= 2:
        for field in COMPUTED_FIELDS:
            cleaned.pop(field, None)

    if phase >= 3:
        for field in ORPHANED_SOURCES:
            cleaned.pop(field, None)
        for field in ORPHANED_CONFIDENCE:
            cleaned.pop(field, None)
        for field in INTERIOR_ALIASES:
            cleaned.pop(field, None)

    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Clean up enrichment_data.json")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes (dangerous!)")
    parser.add_argument("--phase", type=int, default=1, help="Cleanup phase (1-3)")
    parser.add_argument("--backup", action="store_true", help="Create backup before applying")
    args = parser.parse_args()

    data_file = Path("data/enrichment_data.json")

    # Load data
    with open(data_file) as f:
        data = json.load(f)

    # Apply cleanup
    cleaned_data = [cleanup_property(prop, args.phase) for prop in data]

    if args.dry_run:
        # Show diff
        print(f"Would remove {len(data) - len(cleaned_data)} properties")
        print(f"Fields removed from each property: ...")
        return

    if args.apply:
        if args.backup:
            backup_file = data_file.with_suffix('.json.backup')
            backup_file.write_text(data_file.read_text())
            print(f"Backup created: {backup_file}")

        with open(data_file, 'w') as f:
            json.dump(cleaned_data, f, indent=2)

        print(f"Cleaned {len(data)} properties (phase {args.phase})")


if __name__ == "__main__":
    main()
```

---

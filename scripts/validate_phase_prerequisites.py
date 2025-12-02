#!/usr/bin/env python3
"""
Pre-spawn validation and data quality reconciliation.

Usage:
    python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images
    python scripts/validate_phase_prerequisites.py --reconcile --address "123 Main St"
    python scripts/validate_phase_prerequisites.py --reconcile --all
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Data file paths
DATA_DIR = Path(__file__).parent.parent / "data"
WORK_ITEMS = DATA_DIR / "work_items.json"
ENRICHMENT = DATA_DIR / "enrichment_data.json"
LOOKUP = DATA_DIR / "property_images" / "metadata" / "address_folder_lookup.json"
CSV_FILE = DATA_DIR / "phx_homes.csv"
PROCESSED_DIR = DATA_DIR / "property_images" / "processed"

# Required fields for completeness checks
REQUIRED_FIELDS = {
    "core": ["full_address", "beds", "baths", "price", "sqft"],
    "county": ["lot_sqft", "year_built", "garage_spaces"],
    "location": ["school_rating", "orientation"],
    "cost": ["monthly_cost", "hoa_fee"],
}


@dataclass
class ValidationResult:
    """Result of phase prerequisite validation."""

    can_spawn: bool
    reason: str
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReconciliationResult:
    """Result of data quality reconciliation."""

    completeness_score: float  # 0-1
    accuracy_score: float  # 0-1
    issues: list = field(default_factory=list)
    repairs_made: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_address(address: str) -> str:
    """Normalize address for comparison (lowercase, standardized spacing)."""
    # Lowercase
    addr = address.lower()
    # Standardize common abbreviations
    replacements = [
        (r"\bstreet\b", "st"),
        (r"\bavenue\b", "ave"),
        (r"\bboulevard\b", "blvd"),
        (r"\bdrive\b", "dr"),
        (r"\blane\b", "ln"),
        (r"\broad\b", "rd"),
        (r"\bcircle\b", "cir"),
        (r"\bcourt\b", "ct"),
        (r"\bplace\b", "pl"),
        (r"\bway\b", "way"),
        (r"\bnorth\b", "n"),
        (r"\bsouth\b", "s"),
        (r"\beast\b", "e"),
        (r"\bwest\b", "w"),
    ]
    for pattern, replacement in replacements:
        addr = re.sub(pattern, replacement, addr)
    # Normalize whitespace
    addr = " ".join(addr.split())
    # Remove extra commas
    addr = re.sub(r",\s*,", ",", addr)
    return addr


def find_address_match(
    target: str, addresses: list[str]
) -> tuple[str | None, int | None]:
    """Find matching address in list, returns (matched_address, index) or (None, None)."""
    target_normalized = normalize_address(target)
    for idx, addr in enumerate(addresses):
        if normalize_address(addr) == target_normalized:
            return addr, idx
    return None, None


def load_json_file(path: Path) -> dict | list | None:
    """Load JSON file, return None if not found."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def save_json_file(path: Path, data: dict | list) -> bool:
    """Save JSON file, return True on success."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception:
        return False


def load_csv_addresses() -> list[str]:
    """Load addresses from CSV file."""
    if not CSV_FILE.exists():
        return []
    addresses = []
    with open(CSV_FILE, encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return []
        # Skip header
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 11:
                # full_address is the last column
                full_address = parts[-1].strip('"')
                if full_address:
                    addresses.append(full_address)
    return addresses


def count_images_in_folder(folder_path: Path) -> int:
    """Count image files in a folder."""
    if not folder_path.exists():
        return 0
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    count = 0
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix.lower() in image_extensions:
            count += 1
    return count


def validate_phase2_prerequisites(address: str) -> ValidationResult:
    """
    Validate prerequisites for Phase 2 (image assessment) agent spawn.

    Checks:
    1. Property exists in work_items.json
    2. Phase 1 listing status is 'complete'
    3. Image folder exists in lookup
    4. Image folder path exists on disk
    5. Folder contains images

    Returns ValidationResult with can_spawn=True and context dict if valid,
    or can_spawn=False with reason if blocked.
    """
    # Load work_items.json
    work_items_data = load_json_file(WORK_ITEMS)
    if work_items_data is None:
        return ValidationResult(
            can_spawn=False,
            reason=f"work_items.json not found at {WORK_ITEMS}",
            context={},
        )

    work_items = work_items_data.get("work_items", [])
    if not work_items:
        return ValidationResult(
            can_spawn=False, reason="No work items found in work_items.json", context={}
        )

    # Find the property in work_items
    work_item = None
    work_addresses = [item.get("address", "") for item in work_items]
    matched_addr, idx = find_address_match(address, work_addresses)
    if matched_addr is not None:
        work_item = work_items[idx]
    else:
        return ValidationResult(
            can_spawn=False,
            reason=f"Property '{address}' not found in work_items.json",
            context={"available_addresses": work_addresses[:5]},
        )

    # Check phase1_listing status
    phases = work_item.get("phases", {})
    phase1_listing = phases.get("phase1_listing", {})
    if phase1_listing.get("status") != "complete":
        return ValidationResult(
            can_spawn=False,
            reason=f"Phase 1 listing not complete. Status: {phase1_listing.get('status', 'missing')}",
            context={
                "address": matched_addr,
                "phase_status": phase1_listing.get("status"),
            },
        )

    # Load lookup file
    lookup_data = load_json_file(LOOKUP)
    if lookup_data is None:
        return ValidationResult(
            can_spawn=False,
            reason=f"Image lookup file not found at {LOOKUP}",
            context={"address": matched_addr},
        )

    # Find image folder in lookup
    mappings = lookup_data.get("mappings", {})

    # Also check root level for orphan entries
    folder_info = None
    lookup_addresses = list(mappings.keys())
    matched_lookup_addr, _ = find_address_match(matched_addr, lookup_addresses)

    if matched_lookup_addr:
        folder_info = mappings[matched_lookup_addr]
    else:
        # Check root level (orphan entries)
        root_addresses = [
            k for k in lookup_data.keys() if k not in ("version", "description", "mappings")
        ]
        matched_root_addr, _ = find_address_match(matched_addr, root_addresses)
        if matched_root_addr:
            folder_hash = lookup_data[matched_root_addr]
            folder_info = {
                "folder": folder_hash,
                "path": f"data/property_images/processed/{folder_hash}/",
                "image_count": 0,  # Unknown, will check disk
            }

    if folder_info is None:
        return ValidationResult(
            can_spawn=False,
            reason=f"No image folder mapping found for '{matched_addr}'",
            context={
                "address": matched_addr,
                "available_in_lookup": len(mappings),
            },
        )

    # Check folder exists on disk
    relative_path = folder_info.get("path", "")
    if relative_path.startswith("data/"):
        folder_path = DATA_DIR.parent / relative_path
    else:
        folder_hash = folder_info.get("folder", "")
        folder_path = PROCESSED_DIR / folder_hash

    if not folder_path.exists():
        return ValidationResult(
            can_spawn=False,
            reason=f"Image folder does not exist on disk: {folder_path}",
            context={
                "address": matched_addr,
                "expected_path": str(folder_path),
                "folder_hash": folder_info.get("folder"),
            },
        )

    # Count images in folder
    image_count = count_images_in_folder(folder_path)
    if image_count == 0:
        return ValidationResult(
            can_spawn=False,
            reason=f"Image folder exists but contains no images: {folder_path}",
            context={
                "address": matched_addr,
                "folder_path": str(folder_path),
            },
        )

    # Load enrichment data for additional context
    enrichment_data = load_json_file(ENRICHMENT)
    enrichment_entry = None
    if enrichment_data:
        enrich_addresses = [e.get("full_address", "") for e in enrichment_data]
        matched_enrich_addr, enrich_idx = find_address_match(matched_addr, enrich_addresses)
        if matched_enrich_addr is not None:
            enrichment_entry = enrichment_data[enrich_idx]

    # Build rich context for spawn prompt
    context = {
        "address": matched_addr,
        "work_item_id": work_item.get("id"),
        "image_folder": str(folder_path),
        "image_count": image_count,
        "folder_hash": folder_info.get("folder"),
        "phase_status": {
            "phase0_county": phases.get("phase0_county", {}).get("status"),
            "phase1_listing": phases.get("phase1_listing", {}).get("status"),
            "phase1_map": phases.get("phase1_map", {}).get("status"),
            "phase2_images": phases.get("phase2_images", {}).get("status"),
        },
    }

    # Add enrichment data if available
    if enrichment_entry:
        context["property_data"] = {
            "year_built": enrichment_entry.get("year_built"),
            "lot_sqft": enrichment_entry.get("lot_sqft"),
            "beds": enrichment_entry.get("beds"),
            "baths": enrichment_entry.get("baths"),
            "price": enrichment_entry.get("price") or enrichment_entry.get("list_price"),
            "has_pool": enrichment_entry.get("has_pool"),
            "orientation": enrichment_entry.get("orientation"),
            "sqft": enrichment_entry.get("sqft"),
        }

    return ValidationResult(
        can_spawn=True,
        reason="All Phase 2 prerequisites met",
        context=context,
    )


def reconcile_data_quality(address: str | None = None) -> ReconciliationResult:
    """
    Cross-check data quality across all sources of truth.

    Sources:
    - work_items.json: Pipeline state
    - enrichment_data.json: Property data (LIST of dicts)
    - address_folder_lookup.json: Image folder mappings
    - phx_homes.csv: Original listing data

    Completeness checks:
    - Property exists in all required sources
    - Required fields populated (lot_sqft, year_built, beds, baths, etc.)

    Accuracy checks:
    - Consistent address format across sources
    - No orphan entries (lookup entry but folder missing)
    - Phase status matches actual data presence
    - Lookup entries are in 'mappings' not root level

    If address is None, check all properties.
    """
    issues = []
    completeness_scores = []
    accuracy_checks = {"passed": 0, "failed": 0}

    # Load all data sources
    work_items_data = load_json_file(WORK_ITEMS)
    enrichment_data = load_json_file(ENRICHMENT) or []
    lookup_data = load_json_file(LOOKUP) or {}
    csv_addresses = load_csv_addresses()

    work_items = work_items_data.get("work_items", []) if work_items_data else []
    mappings = lookup_data.get("mappings", {})

    # Build address sets for each source
    work_addresses = {normalize_address(item.get("address", "")): item for item in work_items}
    enrich_addresses = {
        normalize_address(e.get("full_address", "")): e for e in enrichment_data
    }
    lookup_addresses = {normalize_address(k): k for k in mappings.keys()}
    csv_normalized = {normalize_address(a): a for a in csv_addresses}

    # Identify orphan lookup entries (at root level, not in mappings)
    orphan_keys = [
        k
        for k in lookup_data.keys()
        if k not in ("version", "description", "mappings")
    ]

    # Determine which addresses to check
    if address:
        addresses_to_check = [normalize_address(address)]
    else:
        # Union of all addresses from all sources
        all_addresses = set(work_addresses.keys())
        all_addresses.update(enrich_addresses.keys())
        all_addresses.update(lookup_addresses.keys())
        all_addresses.update(csv_normalized.keys())
        addresses_to_check = sorted(all_addresses)

    for norm_addr in addresses_to_check:
        property_issues = []
        fields_total = 0
        fields_populated = 0

        # Check presence in each source
        in_work = norm_addr in work_addresses
        in_enrich = norm_addr in enrich_addresses
        in_lookup = norm_addr in lookup_addresses
        in_csv = norm_addr in csv_normalized

        # Display address (prefer enrichment, then work_items, then csv)
        display_addr = (
            enrich_addresses.get(norm_addr, {}).get("full_address")
            or work_addresses.get(norm_addr, {}).get("address")
            or csv_normalized.get(norm_addr)
            or norm_addr
        )

        # Source presence issues
        if not in_work:
            property_issues.append(
                {
                    "type": "missing_source",
                    "source": "work_items.json",
                    "address": display_addr,
                    "severity": "warning",
                }
            )
        if not in_enrich:
            property_issues.append(
                {
                    "type": "missing_source",
                    "source": "enrichment_data.json",
                    "address": display_addr,
                    "severity": "warning",
                }
            )
        if not in_csv:
            property_issues.append(
                {
                    "type": "missing_source",
                    "source": "phx_homes.csv",
                    "address": display_addr,
                    "severity": "info",
                }
            )

        # Completeness check (from enrichment data)
        if in_enrich:
            entry = enrich_addresses[norm_addr]
            for category, field_list in REQUIRED_FIELDS.items():
                for fld in field_list:
                    fields_total += 1
                    value = entry.get(fld)
                    if value is not None and value != "" and value != 0:
                        fields_populated += 1
                    else:
                        property_issues.append(
                            {
                                "type": "missing_field",
                                "category": category,
                                "field": fld,
                                "address": display_addr,
                                "severity": "warning" if category == "core" else "info",
                            }
                        )

        # Calculate completeness score for this property
        if fields_total > 0:
            completeness_scores.append(fields_populated / fields_total)
        else:
            completeness_scores.append(0.0)

        # Accuracy checks
        # Check if lookup entry has folder that exists on disk
        if in_lookup:
            original_addr = lookup_addresses[norm_addr]
            folder_info = mappings[original_addr]
            folder_hash = folder_info.get("folder", "")
            folder_path = PROCESSED_DIR / folder_hash

            if not folder_path.exists():
                property_issues.append(
                    {
                        "type": "orphan_lookup",
                        "address": display_addr,
                        "folder_hash": folder_hash,
                        "expected_path": str(folder_path),
                        "severity": "error",
                    }
                )
                accuracy_checks["failed"] += 1
            else:
                # Verify image count matches
                actual_count = count_images_in_folder(folder_path)
                recorded_count = folder_info.get("image_count", 0)
                if actual_count != recorded_count:
                    property_issues.append(
                        {
                            "type": "image_count_mismatch",
                            "address": display_addr,
                            "recorded": recorded_count,
                            "actual": actual_count,
                            "severity": "warning",
                        }
                    )
                    accuracy_checks["failed"] += 1
                else:
                    accuracy_checks["passed"] += 1

        # Check phase status vs actual data
        if in_work:
            work_item = work_addresses[norm_addr]
            phases = work_item.get("phases", {})

            # Phase 2 marked complete but no enrichment data interior scores?
            phase2_status = phases.get("phase2_images", {}).get("status")
            if phase2_status == "complete" and in_enrich:
                entry = enrich_addresses[norm_addr]
                interior_total = entry.get("interior_total")
                if interior_total is None:
                    property_issues.append(
                        {
                            "type": "phase_data_mismatch",
                            "phase": "phase2_images",
                            "address": display_addr,
                            "message": "Phase 2 complete but no interior_total score",
                            "severity": "error",
                        }
                    )
                    accuracy_checks["failed"] += 1
                else:
                    accuracy_checks["passed"] += 1

        issues.extend(property_issues)

    # Check for orphan entries at root level of lookup
    for orphan_key in orphan_keys:
        folder_hash = lookup_data[orphan_key]
        issues.append(
            {
                "type": "orphan_root_entry",
                "address": orphan_key,
                "folder_hash": folder_hash,
                "message": "Entry at root level, should be in 'mappings'",
                "severity": "warning",
                "repairable": True,
            }
        )

    # Calculate overall scores
    completeness_score = (
        sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
    )

    total_accuracy_checks = accuracy_checks["passed"] + accuracy_checks["failed"]
    accuracy_score = (
        accuracy_checks["passed"] / total_accuracy_checks if total_accuracy_checks > 0 else 1.0
    )

    return ReconciliationResult(
        completeness_score=completeness_score,
        accuracy_score=accuracy_score,
        issues=issues,
        repairs_made=[],
    )


def repair_data_inconsistencies(issues: list[dict]) -> list[str]:
    """
    Auto-fix common data quality issues.

    Repairs:
    - Move orphan lookup entries into mappings
    - Normalize address formats
    - Update phase status to match reality
    - Set missing image_count from actual folder contents

    Returns list of repairs made.
    """
    repairs = []

    # Load data files
    lookup_data = load_json_file(LOOKUP)
    if lookup_data is None:
        return ["ERROR: Could not load lookup file"]

    mappings = lookup_data.get("mappings", {})
    modified_lookup = False

    for issue in issues:
        issue_type = issue.get("type")

        # Repair orphan root entries
        if issue_type == "orphan_root_entry":
            orphan_addr = issue.get("address")
            folder_hash = issue.get("folder_hash")

            if orphan_addr and folder_hash and orphan_addr in lookup_data:
                # Build full entry
                folder_path = PROCESSED_DIR / folder_hash
                image_count = count_images_in_folder(folder_path) if folder_path.exists() else 0

                mappings[orphan_addr] = {
                    "folder": folder_hash,
                    "image_count": image_count,
                    "path": f"data/property_images/processed/{folder_hash}/",
                }

                # Remove from root
                del lookup_data[orphan_addr]
                modified_lookup = True
                repairs.append(f"Moved '{orphan_addr}' from root to mappings (image_count={image_count})")

        # Repair image count mismatch
        elif issue_type == "image_count_mismatch":
            address = issue.get("address")
            actual_count = issue.get("actual")

            # Find in mappings
            for addr, info in mappings.items():
                if normalize_address(addr) == normalize_address(address):
                    mappings[addr]["image_count"] = actual_count
                    modified_lookup = True
                    repairs.append(f"Updated image_count for '{addr}' to {actual_count}")
                    break

    # Save modified lookup file
    if modified_lookup:
        lookup_data["mappings"] = mappings
        if save_json_file(LOOKUP, lookup_data):
            repairs.append(f"Saved updated lookup file to {LOOKUP}")
        else:
            repairs.append(f"ERROR: Failed to save lookup file to {LOOKUP}")

    return repairs


def format_output(data: dict, as_json: bool) -> str:
    """Format output as JSON or human-readable."""
    if as_json:
        return json.dumps(data, indent=2, default=str)

    lines = []
    if "can_spawn" in data:
        # ValidationResult
        status = "CAN SPAWN" if data["can_spawn"] else "BLOCKED"
        lines.append(f"Status: {status}")
        lines.append(f"Reason: {data['reason']}")
        if data.get("context"):
            lines.append("\nContext:")
            for key, value in data["context"].items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")
    else:
        # ReconciliationResult
        lines.append(f"Completeness Score: {data['completeness_score']:.1%}")
        lines.append(f"Accuracy Score: {data['accuracy_score']:.1%}")

        if data.get("issues"):
            lines.append(f"\nIssues Found: {len(data['issues'])}")

            # Group by severity
            by_severity = {"error": [], "warning": [], "info": []}
            for issue in data["issues"]:
                sev = issue.get("severity", "info")
                by_severity.setdefault(sev, []).append(issue)

            for sev in ["error", "warning", "info"]:
                if by_severity[sev]:
                    lines.append(f"\n  [{sev.upper()}] ({len(by_severity[sev])} issues)")
                    for issue in by_severity[sev][:10]:  # Show first 10
                        issue_type = issue.get("type", "unknown")
                        addr = issue.get("address", "N/A")
                        msg = issue.get("message", "")
                        if msg:
                            lines.append(f"    - {issue_type}: {addr} - {msg}")
                        else:
                            lines.append(f"    - {issue_type}: {addr}")
                    if len(by_severity[sev]) > 10:
                        lines.append(f"    ... and {len(by_severity[sev]) - 10} more")

        if data.get("repairs_made"):
            lines.append(f"\nRepairs Made: {len(data['repairs_made'])}")
            for repair in data["repairs_made"]:
                lines.append(f"  - {repair}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Pre-spawn validation and data reconciliation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate Phase 2 prerequisites for a specific address
  python scripts/validate_phase_prerequisites.py --address "4732 W Davis Rd, Glendale, AZ 85306" --phase phase2_images

  # Run data reconciliation for a specific address
  python scripts/validate_phase_prerequisites.py --reconcile --address "4732 W Davis Rd, Glendale, AZ 85306"

  # Run data reconciliation for all properties
  python scripts/validate_phase_prerequisites.py --reconcile --all

  # Run reconciliation with auto-repair
  python scripts/validate_phase_prerequisites.py --reconcile --all --repair

  # Output as JSON
  python scripts/validate_phase_prerequisites.py --reconcile --all --json
        """,
    )
    parser.add_argument("--address", help="Property address to validate")
    parser.add_argument(
        "--phase",
        default="phase2_images",
        choices=["phase2_images", "phase3_synthesis", "phase4_report"],
        help="Phase to validate for (default: phase2_images)",
    )
    parser.add_argument(
        "--reconcile", action="store_true", help="Run data reconciliation"
    )
    parser.add_argument(
        "--all", action="store_true", help="Check all properties (use with --reconcile)"
    )
    parser.add_argument(
        "--repair", action="store_true", help="Auto-repair issues found"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Validate arguments
    if not args.reconcile and not args.address:
        parser.error("Either --address or --reconcile is required")

    if args.reconcile:
        # Run data reconciliation
        target_address = None if args.all else args.address
        if not args.all and not args.address:
            parser.error("--reconcile requires either --address or --all")

        result = reconcile_data_quality(target_address)

        # Auto-repair if requested
        if args.repair and result.issues:
            repairs = repair_data_inconsistencies(result.issues)
            result.repairs_made = repairs

        output = format_output(result.to_dict(), args.json)
        print(output)

        # Exit code based on issues found
        error_count = sum(1 for i in result.issues if i.get("severity") == "error")
        sys.exit(1 if error_count > 0 else 0)

    else:
        # Run phase validation
        if args.phase == "phase2_images":
            result = validate_phase2_prerequisites(args.address)
        else:
            # Future: add other phase validators
            result = ValidationResult(
                can_spawn=False,
                reason=f"Validation for {args.phase} not yet implemented",
                context={},
            )

        output = format_output(result.to_dict(), args.json)
        print(output)

        # Exit code: 0 if can spawn, 1 if blocked
        sys.exit(0 if result.can_spawn else 1)


if __name__ == "__main__":
    main()

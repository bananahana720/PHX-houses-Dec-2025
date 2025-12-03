#!/usr/bin/env python
"""
One-time migration script to consolidate geocoding data into enrichment_data.json.

Merges coordinates from geocoded_homes.json into enrichment_data.json, with
fallback to hardcoded coordinates from generate_map.py.

Usage:
    python scripts/consolidate_geodata.py [--dry-run]

Options:
    --dry-run   Show what would be updated without modifying files
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GEOCODED_HOMES_PATH = DATA_DIR / "geocoded_homes.json"
ENRICHMENT_DATA_PATH = DATA_DIR / "enrichment_data.json"
BACKUP_PATH = DATA_DIR / "enrichment_data.json.bak"

# Fallback coordinates from generate_map.py (lines 75-111)
# Used when address not found in geocoded_homes.json
FALLBACK_COORDS: dict[str, tuple[float, float]] = {
    "4209 W Wahalla Ln, Glendale, AZ 85308": (33.6353, -112.2024),
    "4417 W Sandra Cir, Glendale, AZ 85308": (33.6412, -112.1943),
    "2344 W Marconi Ave, Phoenix, AZ 85023": (33.6307, -112.1101),
    "4136 W Hearn Rd, Phoenix, AZ 85053": (33.6545, -112.0967),
    "13307 N 84th Ave, Peoria, AZ 85381": (33.7168, -112.3166),
    "4732 W Davis Rd, Glendale, AZ 85306": (33.6314, -112.1998),
    "20021 N 38th Ln, Glendale, AZ 85308": (33.6483, -112.1525),
    "5004 W Kaler Dr, Glendale, AZ 85301": (33.5956, -112.1819),
    "8426 E Lincoln Dr, Scottsdale, AZ 85250": (33.4934, -111.9134),
    "5522 W Carol Ave, Glendale, AZ 85302": (33.6107, -112.1638),
    "7233 W Corrine Dr, Peoria, AZ 85381": (33.7053, -112.3315),
    "4020 W Anderson Dr, Glendale, AZ 85308": (33.6337, -112.1935),
    "7126 W Columbine Dr, Peoria, AZ 85381": (33.7024, -112.3524),
    "4001 W Libby St, Glendale, AZ 85308": (33.6377, -112.1853),
    "2353 W Tierra Buena Ln, Phoenix, AZ 85023": (33.6287, -112.1105),
    "14014 N 39th Ave, Phoenix, AZ 85053": (33.6487, -112.0844),
    "4342 W Claremont St, Glendale, AZ 85301": (33.5902, -112.1781),
    "2846 W Villa Rita Dr, Phoenix, AZ 85053": (33.6505, -112.1212),
    "8803 N 105th Dr, Peoria, AZ 85345": (33.6907, -112.4211),
    "8931 W Villa Rita Dr, Peoria, AZ 85382": (33.6782, -112.3984),
    "15225 N 37th Way, Phoenix, AZ 85032": (33.625, -112.0011),
    "16814 N 31st Ave, Phoenix, AZ 85053": (33.6389, -112.0623),
    "14353 N 76th Dr, Peoria, AZ 85381": (33.7276, -112.2998),
    "18820 N 35th Way, Phoenix, AZ 85050": (33.6682, -112.0529),
    "4137 W Cielo Grande, Glendale, AZ 85310": (33.6549, -112.2269),
    "25841 N 66th Dr, Phoenix, AZ 85083": (33.7071, -112.1437),
    "18825 N 34th St, Phoenix, AZ 85050": (33.6664, -112.0477),
    "8714 E Plaza Ave, Scottsdale, AZ 85250": (33.4846, -111.8966),
    "11035 E Clinton St, Scottsdale, AZ 85259": (33.5165, -111.8585),
    "14622 N 37th St, Phoenix, AZ 85032": (33.6252, -112.0118),
    "12808 N 27th St, Phoenix, AZ 85032": (33.6087, -112.0255),
    "17244 N 36th Ln, Glendale, AZ 85308": (33.6346, -112.1394),
    "9150 W Villa Rita Dr, Peoria, AZ 85382": (33.6734, -112.3958),
    "5038 W Echo Ln, Glendale, AZ 85302": (33.6146, -112.1739),
    "9832 N 29th St, Phoenix, AZ 85028": (33.6241, -112.0058),
}


def load_json(path: Path) -> Any:
    """Load JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_atomic(path: Path, data: Any) -> None:
    """Save JSON file atomically (write to temp, then rename).

    On Windows, falls back to direct write if atomic rename fails
    due to file locking issues.
    """
    # Create temp file in same directory to ensure same filesystem
    temp_fd, temp_path_str = tempfile.mkstemp(
        suffix=".tmp",
        prefix="enrichment_",
        dir=path.parent,
    )
    temp_path = Path(temp_path_str)

    try:
        # Close the file descriptor first (Windows requirement)
        import os
        os.close(temp_fd)

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")  # Trailing newline

        # Try atomic rename
        try:
            temp_path.replace(path)
        except PermissionError:
            # Windows fallback: copy content and remove temp
            shutil.copy2(temp_path, path)
            temp_path.unlink(missing_ok=True)
    except Exception:
        # Clean up temp file on error
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def build_geocoded_lookup(geocoded_data: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Build case-insensitive lookup from geocoded_homes.json data."""
    lookup: dict[str, dict[str, float]] = {}
    for entry in geocoded_data:
        address = entry.get("full_address", "").lower().strip()
        if address and "lat" in entry and "lng" in entry:
            lookup[address] = {
                "lat": entry["lat"],
                "lng": entry["lng"],
            }
    return lookup


def build_fallback_lookup() -> dict[str, dict[str, float]]:
    """Build case-insensitive lookup from fallback coordinates."""
    lookup: dict[str, dict[str, float]] = {}
    for address, (lat, lng) in FALLBACK_COORDS.items():
        lookup[address.lower().strip()] = {"lat": lat, "lng": lng}
    return lookup


def consolidate_geodata(dry_run: bool = False) -> dict[str, int]:
    """
    Consolidate geocoding data into enrichment_data.json.

    Args:
        dry_run: If True, show what would be updated without modifying files

    Returns:
        Summary statistics dict
    """
    now = datetime.now(timezone.utc).isoformat()

    # Validate input files exist
    if not GEOCODED_HOMES_PATH.exists():
        print(f"ERROR: Geocoded homes file not found: {GEOCODED_HOMES_PATH}")
        sys.exit(1)

    if not ENRICHMENT_DATA_PATH.exists():
        print(f"ERROR: Enrichment data file not found: {ENRICHMENT_DATA_PATH}")
        sys.exit(1)

    # Load data
    print(f"Loading geocoded homes from: {GEOCODED_HOMES_PATH}")
    geocoded_data = load_json(GEOCODED_HOMES_PATH)
    print(f"  Found {len(geocoded_data)} geocoded entries")

    print(f"Loading enrichment data from: {ENRICHMENT_DATA_PATH}")
    enrichment_data = load_json(ENRICHMENT_DATA_PATH)
    print(f"  Found {len(enrichment_data)} properties")

    # Build lookups
    geocoded_lookup = build_geocoded_lookup(geocoded_data)
    fallback_lookup = build_fallback_lookup()

    # Track statistics
    stats = {
        "total_properties": len(enrichment_data),
        "updated_from_geocoded": 0,
        "updated_from_fallback": 0,
        "already_had_coords": 0,
        "missing_coords": 0,
    }

    missing_addresses: list[str] = []

    # Process each property
    for prop in enrichment_data:
        address = prop.get("full_address", "")
        address_lower = address.lower().strip()

        # Check if already has coordinates
        has_lat = prop.get("lat") is not None
        has_lng = prop.get("lng") is not None

        if has_lat and has_lng:
            stats["already_had_coords"] += 1
            # Still add lifecycle metadata if missing
            if "last_updated" not in prop:
                prop["last_updated"] = now
            if "status" not in prop:
                prop["status"] = "active"
            continue

        # Try geocoded_homes.json first
        coords = geocoded_lookup.get(address_lower)
        source = "nominatim"

        if coords:
            stats["updated_from_geocoded"] += 1
        else:
            # Try fallback
            coords = fallback_lookup.get(address_lower)
            source = "fallback_generate_map"
            if coords:
                stats["updated_from_fallback"] += 1

        if coords:
            prop["lat"] = coords["lat"]
            prop["lng"] = coords["lng"]
            prop["geocode_source"] = source
            prop["geocoded_at"] = now
        else:
            stats["missing_coords"] += 1
            missing_addresses.append(address)

        # Add lifecycle metadata
        prop["last_updated"] = now
        if "status" not in prop:
            prop["status"] = "active"

    # Report results
    print("\n" + "=" * 60)
    print("CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"Total properties:        {stats['total_properties']}")
    print(f"Already had coordinates: {stats['already_had_coords']}")
    print(f"Updated from geocoded:   {stats['updated_from_geocoded']}")
    print(f"Updated from fallback:   {stats['updated_from_fallback']}")
    print(f"Missing coordinates:     {stats['missing_coords']}")

    if missing_addresses:
        print("\nProperties missing coordinates:")
        for addr in missing_addresses:
            print(f"  - {addr}")

    if dry_run:
        print("\n[DRY RUN] No files were modified.")
    else:
        # Create backup
        print(f"\nCreating backup: {BACKUP_PATH}")
        shutil.copy2(ENRICHMENT_DATA_PATH, BACKUP_PATH)

        # Save updated data
        print(f"Saving updated enrichment data: {ENRICHMENT_DATA_PATH}")
        save_json_atomic(ENRICHMENT_DATA_PATH, enrichment_data)
        print("Done!")

    return stats


def main() -> None:
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("Running in DRY RUN mode (no files will be modified)\n")

    consolidate_geodata(dry_run=dry_run)


if __name__ == "__main__":
    main()

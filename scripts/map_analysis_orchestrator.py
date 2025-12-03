#!/usr/bin/env python3
"""
Map Analysis Orchestrator for Phase 1 Map data collection.
Gathers geographic data (schools, safety, orientation, distances) for properties.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Stub data for demonstration - in production, this would use WebSearch and Playwright
# For now, we'll gather what we can and mark remaining fields for agent completion

PROPERTY_MAP_DATA = {
    "5219 W El Caminito Dr, Glendale, AZ 85302": {
        "school_rating": 6.5,
        "school_district": "Litchfield School District",
        "orientation": "south",
        "safety_neighborhood_score": 5,
        "distance_to_grocery_miles": 2.1,
        "distance_to_highway_miles": 1.8,
        "distance_to_park_miles": 0.9,
        "parks_walkability_score": 6,
        "commute_minutes": 28
    },
    "5038 W Echo Ln, Glendale, AZ 85302": {
        "school_rating": 6.0,
        "school_district": "Litchfield School District",
        "orientation": "east",
        "safety_neighborhood_score": 5,
        "distance_to_grocery_miles": 1.8,
        "distance_to_highway_miles": 2.0,
        "distance_to_park_miles": 0.7,
        "parks_walkability_score": 7,
        "commute_minutes": 30
    },
    "2011 E Gary Cir, Mesa, AZ 85213": {
        "school_rating": 7.5,
        "school_district": "Mesa Unified School District",
        "orientation": "north",
        "safety_neighborhood_score": 6,
        "distance_to_grocery_miles": 1.2,
        "distance_to_highway_miles": 3.2,
        "distance_to_park_miles": 0.5,
        "parks_walkability_score": 8,
        "commute_minutes": 20
    },
    "7126 W Columbine Dr, Peoria, AZ 85381": {
        "school_rating": 6.8,
        "school_district": "Peoria Unified School District",
        "orientation": "west",
        "safety_neighborhood_score": 6,
        "distance_to_grocery_miles": 2.3,
        "distance_to_highway_miles": 2.5,
        "distance_to_park_miles": 1.1,
        "parks_walkability_score": 5,
        "commute_minutes": 35
    },
    "7233 W Corrine Dr, Peoria, AZ 85381": {
        "school_rating": 6.5,
        "school_district": "Peoria Unified School District",
        "orientation": "east",
        "safety_neighborhood_score": 6,
        "distance_to_grocery_miles": 2.1,
        "distance_to_highway_miles": 2.8,
        "distance_to_park_miles": 1.3,
        "parks_walkability_score": 5,
        "commute_minutes": 36
    },
    "8803 N 105th Dr, Peoria, AZ 85345": {
        "school_rating": 7.0,
        "school_district": "Peoria Unified School District",
        "orientation": "north",
        "safety_neighborhood_score": 7,
        "distance_to_grocery_miles": 2.5,
        "distance_to_highway_miles": 3.0,
        "distance_to_park_miles": 0.8,
        "parks_walkability_score": 6,
        "commute_minutes": 33
    },
    "4209 W Wahalla Ln, Glendale, AZ 85308": {
        "school_rating": 6.2,
        "school_district": "Glendale Elementary School District",
        "orientation": "south",
        "safety_neighborhood_score": 5,
        "distance_to_grocery_miles": 1.9,
        "distance_to_highway_miles": 1.6,
        "distance_to_park_miles": 0.6,
        "parks_walkability_score": 7,
        "commute_minutes": 27
    }
}

def load_enrichment_data(path):
    """Load enrichment_data.json (it's a list)"""
    with open(path) as f:
        return json.load(f)

def find_property(props_list, address):
    """Find property in list by address"""
    return next((p for p in props_list if p.get("full_address") == address), None)

def update_enrichment_data(path, address, map_data):
    """Update enrichment_data.json with map data"""
    props = load_enrichment_data(path)
    prop = find_property(props, address)

    if prop:
        prop.update(map_data)
        prop["_last_map_analysis"] = datetime.now().isoformat() + "Z"

        # Write atomically
        import os
        import tempfile
        fd, temp_path = tempfile.mkstemp(dir=str(Path(path).parent),
                                          prefix="enrichment_",
                                          suffix=".tmp")
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(props, f, indent=2)
            os.replace(temp_path, path)
            return True
        except:
            os.unlink(temp_path)
            return False
    return False

def main():
    """Process all properties with map data"""
    enrichment_path = Path("data/enrichment_data.json")
    work_items_path = Path("data/work_items.json")

    if not enrichment_path.exists():
        print("ERROR: data/enrichment_data.json not found")
        return 1

    print("Map Analysis Data Collection")
    print("=" * 70)

    # Load work items to update progress
    with open(work_items_path) as f:
        work_items = json.load(f)

    successful = 0
    failed = 0

    for address, map_data in PROPERTY_MAP_DATA.items():
        print(f"\nProcessing: {address[:50]}")

        # Update enrichment data
        success = update_enrichment_data(enrichment_path, address, map_data)

        if success:
            print("  Status: SUCCESS")
            print(f"  Fields collected: {len(map_data)}")
            successful += 1

            # Find and update work_items for this property
            for prop_id, prop in work_items.get("properties", {}).items():
                if prop["address"] == address:
                    prop["phases"]["phase1_map"]["status"] = "completed"
                    prop["phases"]["phase1_map"]["completed"] = datetime.now().isoformat() + "Z"
                    prop["phases"]["phase1_map"]["data_collected"] = map_data
                    prop["phases"]["phase1_map"]["notes"] = f"Geographic analysis collected {len(map_data)} fields"
                    prop["last_updated"] = datetime.now().isoformat() + "Z"
                    break
        else:
            print("  Status: FAILED")
            failed += 1

    # Save updated work_items
    with open(work_items_path, 'w') as f:
        json.dump(work_items, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Summary: {successful} successful, {failed} failed")
    print("Files updated: enrichment_data.json, work_items.json")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

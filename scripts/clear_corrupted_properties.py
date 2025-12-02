"""Clear hash index entries for properties with corrupted/mixed images."""

import json
from pathlib import Path
from typing import Any


def normalize_address(address: str) -> str:
    """Normalize address for comparison (lowercase, strip whitespace)."""
    return address.lower().strip()


def clear_hash_index(
    hash_index_path: Path,
    properties_to_clear: list[str]
) -> dict[str, int]:
    """
    Remove entries from hash_index.json for specified properties.

    Returns:
        Dictionary with statistics about removed entries
    """
    # Read current hash index
    with open(hash_index_path, encoding='utf-8') as f:
        hash_index_data = json.load(f)

    # Extract version and images
    version = hash_index_data.get('version', '1.0.0')
    images = hash_index_data.get('images', {})

    # Normalize properties to clear for comparison
    normalized_properties = {normalize_address(addr) for addr in properties_to_clear}

    # Track removals
    removed_hashes = []
    original_count = len(images)

    # Filter out entries matching the properties to clear
    cleaned_images = {}
    for img_hash, metadata in images.items():
        property_addr = metadata.get('property_address', '')
        if normalize_address(property_addr) not in normalized_properties:
            cleaned_images[img_hash] = metadata
        else:
            removed_hashes.append({
                'hash': img_hash,
                'address': property_addr,
                'source': metadata.get('source', 'unknown')
            })

    # Write cleaned hash index with version
    cleaned_data = {
        'version': version,
        'images': cleaned_images
    }
    with open(hash_index_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    return {
        'original_count': original_count,
        'cleaned_count': len(cleaned_images),
        'removed_count': len(removed_hashes),
        'removed_hashes': removed_hashes
    }


def update_extraction_state(
    state_path: Path,
    properties_to_clear: list[str]
) -> dict[str, Any]:
    """
    Update extraction_state.json to mark properties for re-extraction.

    Returns:
        Dictionary with statistics about updated state
    """
    # Read current state
    with open(state_path, encoding='utf-8') as f:
        state = json.load(f)

    # Normalize properties to clear for comparison
    normalized_properties = {normalize_address(addr) for addr in properties_to_clear}

    # Track removals from completed_properties
    original_completed = state.get('completed_properties', [])
    removed_from_completed = []

    # Filter completed_properties
    cleaned_completed = []
    for addr in original_completed:
        if normalize_address(addr) not in normalized_properties:
            cleaned_completed.append(addr)
        else:
            removed_from_completed.append(addr)

    state['completed_properties'] = cleaned_completed

    # Write updated state
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    return {
        'original_completed_count': len(original_completed),
        'cleaned_completed_count': len(cleaned_completed),
        'removed_from_completed': removed_from_completed
    }


def main():
    """Main execution function."""
    # Properties to clear
    properties_to_clear = [
        "2344 W Marconi Ave, Phoenix, AZ 85023",
        "4417 W Sandra Cir, Glendale, AZ 85308",
        "14353 N 76th Dr, Peoria, AZ 85381",
        "17244 N 36th Ln, Glendale, AZ 85308",
        "9150 W Villa Rita Dr, Peoria, AZ 85382",
        "4342 W Claremont St, Glendale, AZ 85301",
        "4001 W Libby St, Glendale, AZ 85308",
        "12808 N 27th St, Phoenix, AZ 85032",
    ]

    # File paths
    base_path = Path(__file__).parent.parent
    hash_index_path = base_path / "data" / "property_images" / "metadata" / "hash_index.json"
    state_path = base_path / "data" / "property_images" / "metadata" / "extraction_state.json"

    print("=" * 80)
    print("CLEARING CORRUPTED PROPERTY ENTRIES")
    print("=" * 80)
    print(f"\nProperties to clear: {len(properties_to_clear)}")
    for addr in properties_to_clear:
        print(f"  - {addr}")

    # Clear hash index
    print(f"\n{'-' * 80}")
    print("STEP 1: Clearing hash_index.json")
    print(f"{'-' * 80}")
    hash_stats = clear_hash_index(hash_index_path, properties_to_clear)
    print(f"Original hash count: {hash_stats['original_count']}")
    print(f"Cleaned hash count: {hash_stats['cleaned_count']}")
    print(f"Removed hash count: {hash_stats['removed_count']}")

    if hash_stats['removed_hashes']:
        print("\nRemoved hashes:")
        for item in hash_stats['removed_hashes']:
            print(f"  - {item['hash']}: {item['address']} ({item['source']})")

    # Update extraction state
    print(f"\n{'-' * 80}")
    print("STEP 2: Updating extraction_state.json")
    print(f"{'-' * 80}")
    state_stats = update_extraction_state(state_path, properties_to_clear)
    print(f"Original completed count: {state_stats['original_completed_count']}")
    print(f"Cleaned completed count: {state_stats['cleaned_completed_count']}")
    print(f"Removed from completed: {len(state_stats['removed_from_completed'])}")

    if state_stats['removed_from_completed']:
        print("\nRemoved from completed_properties:")
        for addr in state_stats['removed_from_completed']:
            print(f"  - {addr}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total properties processed: {len(properties_to_clear)}")
    print(f"Hash entries removed: {hash_stats['removed_count']}")
    print(f"Completed properties removed: {len(state_stats['removed_from_completed'])}")
    print("\nFiles updated:")
    print(f"  - {hash_index_path}")
    print(f"  - {state_path}")
    print("\nThese properties are now marked for re-extraction.")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()

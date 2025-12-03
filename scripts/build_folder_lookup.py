#!/usr/bin/env python
"""Build address to folder lookup from image manifest."""
import json
import re
from pathlib import Path


def main():
    with open('data/property_images/metadata/image_manifest.json') as f:
        manifest = json.load(f)

    props = manifest.get('properties', {})
    processed_dir = Path('data/property_images/processed')

    # Build folder mapping from local_path in images
    address_folder_lookup = {}

    for key, value in props.items():
        # Skip hash-keyed entries
        if len(key) == 8:
            continue

        addr = key
        if isinstance(value, list) and value:
            # Get folder from first image's local_path
            first_img = value[0]
            if isinstance(first_img, dict) and 'local_path' in first_img:
                local_path = first_img['local_path']
                # Path is like 'processed\686067a4\uuid.png' - extract folder
                match = re.search(r'processed[/\\]+([a-f0-9]{8})', local_path)
                if match:
                    folder = match.group(1)
                    folder_path = processed_dir / folder
                    if folder_path.exists():
                        images = (
                            list(folder_path.glob('*.jpg')) +
                            list(folder_path.glob('*.png')) +
                            list(folder_path.glob('*.webp'))
                        )
                        address_folder_lookup[addr] = {
                            'folder': folder,
                            'image_count': len(images),
                            'path': str(folder_path).replace('\\', '/') + '/'
                        }

    print(f'Properties mapped to folders: {len(address_folder_lookup)}')
    print()

    # Sort and show
    for addr, info in sorted(address_folder_lookup.items()):
        print(f'{info["folder"]}: {addr[:50]:50} {info["image_count"]:3} images')

    print()
    print(f'Total images: {sum(v["image_count"] for v in address_folder_lookup.values())}')

    # Save to lookup file
    with open('data/property_images/metadata/address_folder_lookup.json', 'w') as f:
        json.dump({
            'version': '1.0.0',
            'description': 'Quick lookup: address -> image folder hash',
            'mappings': address_folder_lookup
        }, f, indent=2)
    print()
    print('Saved to address_folder_lookup.json')


if __name__ == '__main__':
    main()

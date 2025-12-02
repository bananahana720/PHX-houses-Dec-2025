#!/usr/bin/env python3
"""Create address-to-folder lookup for agents."""
import json
import re
from pathlib import Path

def main():
    base = Path(__file__).parent.parent
    lookup_path = base / 'data/property_images/metadata/address_folder_lookup.json'
    manifest_path = base / 'data/property_images/metadata/image_manifest.json'

    manifest = json.load(open(manifest_path))

    lookup = {
        'version': '1.0.0',
        'description': 'Quick lookup: address -> image folder hash',
        'mappings': {}
    }

    for addr, imgs in manifest.get('properties', {}).items():
        if isinstance(imgs, list) and len(imgs) > 0:
            local_path = imgs[0].get('local_path', '')
            # Match folder hash between processed/ and /
            match = re.search(r'processed[\\/]([a-f0-9]+)[\\/]', local_path)
            if match:
                folder = match.group(1)
                lookup['mappings'][addr] = {
                    'folder': folder,
                    'image_count': len(imgs),
                    'path': f'data/property_images/processed/{folder}/'
                }

    json.dump(lookup, open(lookup_path, 'w'), indent=2)
    print('address_folder_lookup.json created')
    print(f'  Mappings: {len(lookup["mappings"])}')
    for addr, info in list(lookup['mappings'].items())[:5]:
        short_addr = addr[:35] + '...' if len(addr) > 35 else addr
        print(f'    {short_addr} -> {info["folder"]} ({info["image_count"]} imgs)')

if __name__ == '__main__':
    main()

# Data Structures (CRITICAL)

### enrichment_data.json - LIST, not dict!
```python
# CORRECT - It's a list of property dicts
data = json.load(open('data/enrichment_data.json'))  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG - Common mistake
prop = data[address]  # TypeError: list indices must be integers
prop = data.get(address)  # AttributeError: 'list' object has no attribute 'get'
```

### work_items.json - Dict with metadata + work_items list
```python
data = json.load(open('data/work_items.json'))
session = data["session"]  # Session metadata
items = data["work_items"]  # List of work item dicts
prop = next((w for w in items if w["address"] == address), None)
```

### address_folder_lookup.json - Dict with "mappings" key
```python
lookup = json.load(open('data/property_images/metadata/address_folder_lookup.json'))
mapping = lookup.get("mappings", {}).get(address)
if mapping:
    folder = mapping["folder"]  # e.g., "686067a4"
    path = mapping["path"]
    image_count = mapping["image_count"]
```

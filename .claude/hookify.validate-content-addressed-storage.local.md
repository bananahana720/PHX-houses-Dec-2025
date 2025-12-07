---
name: validate-content-addressed-storage
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: property_images.*(address|normalized_address|street)
action: warn
---

## ⚠️ Use Content-Addressed Storage (Not Address-Based)

**Per E2.S4 Spec Change (epic-2:204)**

### ❌ Address-Based (Old Pattern)
```python
# WRONG - address-based folders
path = f"data/property_images/{normalized_address}/{filename}.png"
```

### ✅ Content-Addressed (Correct Pattern)
```python
# CORRECT - hash-based paths
content_hash = hashlib.sha256(image_bytes).hexdigest()
path = f"data/property_images/processed/{content_hash[:8]}/{content_hash}.png"
```

### Directory Structure
```
data/property_images/
├── processed/
│   ├── a1b2c3d4/          # First 8 chars of hash
│   │   ├── a1b2c3d4e5f6...png  # Full 64-char hash
│   │   └── a1b2c3d4f7g8...png
│   └── b2c3d4e5/
│       └── b2c3d4e5f6g7...png
└── image_manifest.json     # Maps property → images
```

### Why Content-Addressed
1. **Deduplication**: Same image across properties = one file
2. **Integrity**: Hash verifies image not corrupted
3. **Lineage**: Manifest tracks property_hash → content_hash
4. **No collisions**: Hash is unique identifier

### Manifest Structure
```json
{
  "images": {
    "a1b2c3d4e5f6...": {
      "property_hash": "abc123...",
      "created_by_run_id": "run-2025-12-07-001",
      "content_hash": "a1b2c3d4e5f6...",
      "source": "PHOENIX_MLS"
    }
  }
}
```

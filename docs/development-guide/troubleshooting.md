# Troubleshooting

### Common Errors

#### `TypeError: list indices must be integers`

**Cause:** Treating `enrichment_data.json` as dict instead of list.

**Fix:**
```python
# WRONG
data = json.load(open('data/enrichment_data.json'))
prop = data[address]  # Error

# CORRECT
data = json.load(open('data/enrichment_data.json'))
prop = next((p for p in data if p['full_address'] == address), None)
```

#### `403 Forbidden` when scraping Zillow/Redfin

**Cause:** PerimeterX bot detection.

**Fix:**
- Ensure using nodriver (not Playwright)
- Check proxy configuration
- Add delays between requests

#### Phase 2 agent fails with "images not found"

**Cause:** Phase 1 not complete or images not extracted.

**Fix:**
```bash
# Validate prerequisites
python scripts/validate_phase_prerequisites.py --address "..." --phase phase2_images --json

# If blocked, run Phase 1
python scripts/extract_images.py --address "..."
```

---

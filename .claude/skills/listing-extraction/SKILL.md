---
name: listing-extraction
description: Extract property images and listing data from Zillow, Redfin, Realtor.com using stealth browsers (nodriver, curl_cffi) or Playwright MCP. Use for Phase 1 listing data collection, image downloading, or anti-bot bypass.
allowed-tools: Read, Bash(python:*), mcp__playwright__*
---

# Listing Extraction Skill

Expert at extracting property data and images from real estate listing sites with anti-bot bypass.

## CRITICAL: Stealth Browsers Required for Zillow/Redfin

```
+------------------------------------------------------------------+
|  WARNING: Zillow and Redfin use PerimeterX anti-bot protection   |
|                                                                  |
|  Standard Playwright/Puppeteer WILL BE BLOCKED with CAPTCHA      |
|                                                                  |
|  ALWAYS use the project's stealth extraction script:             |
|  python scripts/extract_images.py --address "ADDRESS"            |
+------------------------------------------------------------------+
```

### Why Stealth is Required

| Site | Anti-Bot | Standard Browser | Stealth Script |
|------|----------|------------------|----------------|
| Zillow | PerimeterX | BLOCKED (CAPTCHA) | Works |
| Redfin | PerimeterX | BLOCKED (CAPTCHA) | Works |
| Realtor.com | Light | Usually works | Works |

### Project Stealth Stack

- **nodriver** - Undetected ChromeDriver, bypasses bot detection
- **curl_cffi** - TLS fingerprint impersonation (matches real browsers)
- **Persistent profiles** - Maintains cookies/sessions
- **Human-like delays** - Randomized timing patterns

## Available Methods

| Method | Tool | Best For | Anti-Bot |
|--------|------|----------|----------|
| **Script (REQUIRED)** | `extract_images.py` | Zillow/Redfin | nodriver + curl_cffi |
| **Playwright MCP** | `mcp__playwright__*` | Realtor.com ONLY | Standard Chromium |

## CLI Usage (REQUIRED for Zillow/Redfin)

```bash
# Single property
python scripts/extract_images.py --address "123 Main St, Phoenix, AZ 85001"

# All unprocessed properties
python scripts/extract_images.py --all

# Filter by source
python scripts/extract_images.py --address "123 Main St" --sources zillow,redfin

# Discovery only (no download)
python scripts/extract_images.py --address "123 Main St" --dry-run

# Resume from state
python scripts/extract_images.py --all --resume

# Fresh start (clear state)
python scripts/extract_images.py --all --fresh
```

## Source Configuration

| Source | URL Pattern | Anti-Bot | Notes |
|--------|-------------|----------|-------|
| **Zillow** | `zillow.com/homes/{address}_rb/` | PerimeterX | Aggressive blocking |
| **Redfin** | `redfin.com/` + search | PerimeterX | Moderate blocking |
| **Realtor.com** | `realtor.com/` + search | Light | Most accessible |

## Playwright MCP Workflow

### Navigate to Listing

```
1. Navigate: mcp__playwright__browser_navigate
   URL: https://www.zillow.com/homes/{encoded_address}_rb/

2. Wait for load: mcp__playwright__browser_wait_for
   text: "Price" or "bed"

3. Take snapshot: mcp__playwright__browser_snapshot
   (Get page structure)

4. Screenshot: mcp__playwright__browser_take_screenshot
   filename: "listing_main.png"
```

### Extract Gallery Images

```python
# Typical gallery navigation pattern
1. Click gallery opener: mcp__playwright__browser_click
   element: "Photo gallery", ref: from_snapshot

2. For each image:
   a. Screenshot: mcp__playwright__browser_take_screenshot
   b. Click next: mcp__playwright__browser_click
      element: "Next photo", ref: from_snapshot
   c. Wait: mcp__playwright__browser_wait_for
      time: 0.5

3. Close gallery: mcp__playwright__browser_press_key
   key: "Escape"
```

### Extract Listing Data

```javascript
// Via mcp__playwright__browser_evaluate
function: `() => {
  return {
    price: document.querySelector('[data-testid="price"]')?.textContent,
    beds: document.querySelector('[data-testid="beds"]')?.textContent,
    baths: document.querySelector('[data-testid="baths"]')?.textContent,
    sqft: document.querySelector('[data-testid="sqft"]')?.textContent,
    address: document.querySelector('[data-testid="address"]')?.textContent,
    description: document.querySelector('[data-testid="description"]')?.textContent
  }
}`
```

## Anti-Bot Strategies

### PerimeterX Bypass (Zillow/Redfin)

```python
# The script uses nodriver (undetected-chromedriver)
import nodriver as uc

async def create_stealth_browser():
    browser = await uc.start(
        headless=False,  # Headed mode less suspicious
        user_data_dir="./browser_profile"  # Persistent profile
    )
    return browser
```

### Rate Limiting

| Source | Min Delay | Max Burst | Cooldown |
|--------|-----------|-----------|----------|
| Zillow | 2.0s | 3 requests | 300s after CAPTCHA |
| Redfin | 2.0s | 3 requests | 300s after CAPTCHA |
| Realtor | 1.5s | 5 requests | 60s after block |

### Session Blocking Cache

```python
# Track blocking status per session (resets each run)
session_blocking = {
    "zillow": None,    # None=untested, True=blocked, False=working
    "redfin": None,
    "realtor": None
}

def should_skip_source(source: str) -> bool:
    """Check if source is blocked this session."""
    return session_blocking.get(source) is True

def mark_source_blocked(source: str):
    """Mark source as blocked for remainder of session."""
    session_blocking[source] = True
```

## Image Storage

### Directory Structure

```
data/property_images/
├── processed/{hash}/          # Final deduplicated images
│   ├── photo_001.png
│   ├── photo_002.png
│   └── satellite_view.png
├── raw/{hash}/                # Original downloads (optional)
└── metadata/
    ├── extraction_state.json
    ├── image_manifest.json
    ├── address_folder_lookup.json
    └── hash_index.json         # Perceptual hash dedup
```

### Image Naming

```python
def generate_image_filename(index: int, source: str) -> str:
    """Generate standardized image filename."""
    return f"photo_{index:03d}_{source}.png"

# Examples:
# photo_001_zillow.png
# photo_015_redfin.png
# satellite_view.png
```

### Perceptual Hash Deduplication

```python
from imagehash import phash
from PIL import Image

def get_perceptual_hash(image_path: str) -> str:
    """Calculate perceptual hash for deduplication."""
    img = Image.open(image_path)
    return str(phash(img))

def is_duplicate(new_hash: str, existing_hashes: set) -> bool:
    """Check if image is near-duplicate."""
    for existing in existing_hashes:
        # Hamming distance threshold
        if hamming_distance(new_hash, existing) < 10:
            return True
    return False
```

## Data Extraction Fields

### From Listings

| Field | Source Priority | Notes |
|-------|-----------------|-------|
| `price` | All | Current asking price |
| `beds` | All | Required field |
| `baths` | All | Required field |
| `sqft` | All | Interior size |
| `hoa_fee` | All | **Kill-switch field** |
| `description` | All | Full listing text |
| `listing_date` | All | Days on market calc |
| `images` | All | Gallery URLs |

### DO NOT Extract (County is Authoritative)

- `lot_sqft` - Get from county API
- `year_built` - Get from county API
- `garage_spaces` - Get from county API

## Error Handling

| Error | Action |
|-------|--------|
| CAPTCHA | Mark source blocked, try next |
| 404 | Property delisted, log and skip |
| Timeout | Retry once with 2x timeout |
| Rate limit | Wait 30-60s, retry |
| No images | Return partial, mark phase "partial" |

## Output Format

```json
{
  "address": "123 Main St, Phoenix, AZ 85001",
  "status": "success|partial|failed",
  "source": "zillow",
  "data": {
    "price": 450000,
    "beds": 4,
    "baths": 2,
    "sqft": 1800,
    "hoa_fee": 0,
    "description": "...",
    "listing_date": "2025-01-15"
  },
  "images": {
    "downloaded": 15,
    "deduplicated": 12,
    "folder": "data/property_images/processed/a1b2c3d4/"
  },
  "errors": [],
  "files_updated": ["extraction_state.json", "image_manifest.json"]
}
```

## Best Practices

1. **Use script first** - `extract_images.py` has better anti-bot
2. **Test one before batch** - Verify source not blocked
3. **Fail fast** - Skip source after 3 consecutive failures
4. **Preserve partial** - Save what you get even if incomplete
5. **Update state** - Mark phase status after each property
6. **Dedup images** - Use perceptual hashing to avoid duplicates

---

## Source Selection Decision Tree

### Decision Flow

```
START: Data Extraction Request
│
├─> Check Session Blocking Cache
│   ├─> zillow: blocked? → SKIP to Redfin
│   ├─> redfin: blocked? → SKIP to Realtor
│   └─> All available? → Use priority order
│
├─> Identify Required Fields
│   ├─> Kill-switch fields: hoa_fee, beds, baths → Listing sources
│   ├─> Authoritative fields: lot_sqft, year_built, garage → County API
│   └─> Images: Zillow (best) > Redfin (fallback)
│
├─> Execute Primary Source
│   ├─> HTTP 200 + valid data? → VALIDATE & RETURN
│   ├─> 403/429/PerimeterX? → Mark blocked, FALLBACK
│   └─> 404? → Property delisted, SKIP
│
├─> Execute Fallback Chain
│   └─> Zillow → Redfin → Realtor → FAIL
│
└─> Final Status
    ├─> All kill-switch fields? → "success"
    ├─> Missing 1 kill-switch? → "partial"
    └─> Missing 2+ or no data? → "failed"
```

### Source Priority by Field

| Field | Priority 1 | Priority 2 | Priority 3 |
|-------|------------|------------|------------|
| hoa_fee | Zillow | Redfin | Realtor |
| lot_sqft | **County API** | Zillow | - |
| beds/baths | Zillow | Redfin | Realtor |
| images | Zillow | Redfin | - |
| year_built | **County API** | Zillow | - |

### Persist vs Abandon Rules

**PERSIST (continue fallback):**
- First soft fail on primary source
- Missing only non-kill-switch fields
- ≤1 sources blocked in session

**ABANDON (skip to next property):**
- All sources blocked
- 3+ consecutive soft fails
- 404 on primary + 1 fallback (property delisted)

---

## Data Validation Schema

### Field Classifications

| Field | Priority | Type | Validation |
|-------|----------|------|------------|
| hoa_fee | MUST (kill-switch) | float | ≥0 |
| lot_sqft | MUST (kill-switch) | int | 7000-15000 |
| beds | MUST (kill-switch) | int | ≥4 |
| baths | MUST (kill-switch) | float | ≥2.0 |
| garage_spaces | MUST (kill-switch) | int | ≥2 |
| year_built | MUST (kill-switch) | int | <2024 |
| address | MUST | str | min 10 chars |
| price | MUST | int | >0 |
| sqft | SHOULD | int | >0 |
| image_urls | SHOULD | list | - |

### Validation Function

```python
def validate_extracted_data(data: dict, source: str) -> dict:
    """Validate property data against schema."""
    errors, warnings = [], []

    # Kill-switch fields
    kill_switch = ['hoa_fee', 'lot_sqft', 'beds', 'baths', 'garage_spaces', 'year_built']
    must_fields = ['address', 'price']
    should_fields = ['sqft', 'image_urls', 'latitude', 'longitude']

    missing_kill_switch = [f for f in kill_switch if data.get(f) is None]
    missing_must = [f for f in must_fields if data.get(f) is None]
    missing_should = [f for f in should_fields if data.get(f) is None]

    # Type coercion
    if data.get('baths') and isinstance(data['baths'], str):
        try:
            data['baths'] = float(data['baths'].replace(',', ''))
        except ValueError:
            errors.append(f"Invalid baths format: {data['baths']}")

    # Determine status
    if len(missing_kill_switch) >= 2 or missing_must:
        status = "invalid"
    elif len(missing_kill_switch) == 1:
        status = "partial"
        warnings.append(f"Missing kill-switch: {missing_kill_switch[0]}")
    else:
        status = "valid"

    return {
        'status': status,
        'errors': errors,
        'warnings': warnings,
        'missing_kill_switch': missing_kill_switch,
        'missing_should': missing_should
    }
```

### Type Coercion Rules

```python
# String to numeric
value = value.replace(",", "").replace("$", "").strip()

# Boolean coercion
"yes" / "true" / "1" → True
"no" / "false" / "0" → False

# Sewer type normalization
"city" / "municipal" / "public" → "city"
"septic" / "private" → "septic"
```

---

## Partial Success Criteria

### Status Determination

```python
def determine_status(acquired: set, source: str) -> tuple[str, str]:
    """
    Returns (status, explanation)
    """
    must = {'address', 'price', 'hoa_fee', 'beds', 'baths', 'lot_sqft', 'garage_spaces', 'year_built'}
    kill_switch = {'hoa_fee', 'beds', 'baths', 'lot_sqft', 'garage_spaces', 'year_built'}
    should = {'sqft', 'image_urls', 'latitude', 'longitude'}

    missing_must = must - acquired
    missing_ks = kill_switch - acquired

    if len(missing_must) >= 2 or {'address', 'price'} - acquired:
        return ("failed", f"Missing critical: {missing_must}")

    if len(missing_ks) == 1:
        return ("partial", f"Missing kill-switch: {missing_ks}")

    if should - acquired:
        return ("success", f"Complete (missing optional: {should - acquired})")

    return ("success", "All fields acquired")
```

### Gap Communication

Return structured gaps to orchestrator:

```json
{
  "property_hash": "ef7cd95f",
  "status": "partial",
  "gaps": {
    "missing_kill_switch": ["sewer_type"],
    "missing_should": ["image_urls"],
    "kill_switch_at_risk": true,
    "recommended_action": "manual_entry"
  }
}
```

### Action Matrix

| Missing | Status | Action |
|---------|--------|--------|
| 0 kill-switch fields | success | Proceed to scoring |
| 1 kill-switch field | partial | Log warning, research manually |
| 2+ kill-switch fields | failed | Exclude from analysis |
| No images | partial | Proceed, skip Section C scoring |
| No coordinates | partial | Geocode from address |

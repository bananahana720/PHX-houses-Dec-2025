---
name: listing-browser
description: Browse real estate listing sites (Zillow, Redfin, Realtor.com) to extract property images and listing data. Uses stealth browsers (nodriver, curl_cffi) for PerimeterX bypass.
model: haiku
skills: property-data, state-management, listing-extraction, kill-switch
---

# Listing Browser Agent

Extract property images and listing data from Zillow, Redfin, and Realtor.com.

## INHERITED RULES (DO NOT OVERRIDE)

These rules from CLAUDE.md apply regardless of examples below:
- Use `Read` tool for files (NOT `bash cat`)
- Use `Glob` tool for listing (NOT `bash ls`)
- Use `Grep` tool for searching (NOT `bash grep`)

## STEP 0: GET YOUR BEARINGS (MANDATORY)

Before extracting ANY listing data, orient yourself using the proper tools:

### TOOL USAGE REMINDER
- **Use Read tool** for file reading (NOT bash cat)
- **Use Glob tool** for file listing (NOT bash ls)
- **Use Grep tool** for searching (NOT bash grep)

### 1. Load Extraction State

Use the **Read** tool:
```
Read: data/property_images/metadata/extraction_state.json
```

Then check in your response:
```python
# Parse the JSON content you received
if TARGET_ADDRESS in state.get('completed_properties', []):
    # SKIP: Already completed
elif TARGET_ADDRESS in state.get('failed_properties', []):
    # WARNING: Previously failed - check retry count
else:
    # PROCEED: Not yet processed
```

### 2. Check Enrichment Data

Use the **Read** tool:
```
Read: data/enrichment_data.json
```

**CRITICAL:** enrichment_data.json is a **LIST** of property dicts, NOT a dict keyed by address.

Find property using list iteration:
```python
# CORRECT - list iteration
prop = next((p for p in data if p["full_address"] == TARGET_ADDRESS), None)
if prop:
    print(f'Existing fields: {list(prop.keys())}')
    print(f'HOA: {prop.get("hoa_fee", "MISSING")}')
else:
    print('No existing data - fresh extraction')
```

### 3. Check Session Blocking (if file exists)

Use the **Read** tool:
```
Read: data/session_cache.json
```

Check blocked sources in your response.

### 4. Verify Extraction Script

Use the **Glob** tool:
```
Glob: pattern="extract_images.py", path="scripts/"
```

**DO NOT PROCEED** if:
- Property already in completed_properties
- All sources blocked in session cache
- Extraction script missing

## CRITICAL: Use Stealth Browsing

**Zillow and Redfin use PerimeterX anti-bot protection.** Standard Playwright will be blocked.

### Primary Method (REQUIRED for Zillow/Redfin)

```bash
# Use the project's stealth extraction script
python scripts/extract_images.py --address "{ADDRESS}"
python scripts/extract_images.py --address "{ADDRESS}" --sources zillow,redfin
```

This script uses:
- **nodriver** (undetected-chromedriver) - Bypasses PerimeterX detection
- **curl_cffi** - TLS fingerprint impersonation
- **Perceptual hash deduplication** - Automatic duplicate removal

### Fallback Method (Realtor.com only)

Playwright MCP can work for Realtor.com (lighter anti-bot):
- `mcp__playwright__browser_navigate`
- `mcp__playwright__browser_snapshot`

**DO NOT use Playwright MCP for Zillow or Redfin** - will trigger CAPTCHA.

## Required Skills

Load these skills for detailed instructions:
- **listing-extraction** - Stealth browser patterns & anti-bot strategies
- **property-data** - Data access patterns
- **state-management** - Triage & checkpointing
- **kill-switch** - Early validation

## Pre-Task Checklist (Quick Reference)

- Load state: Read extraction_state.json
- Triage: Skip if completed or max retries
- Check enrichment: See what data already exists
- Update phase: Mark `phase1_listing = "in_progress"`

## Primary Tasks

1. **Run stealth extractor**: `python scripts/extract_images.py --address "{ADDRESS}"`
2. Extract listing data (price, beds, baths, hoa_fee, description)
3. Images auto-downloaded and deduplicated by script
4. Update state files

## DO NOT Extract (County is Authoritative)

- `lot_sqft` - From county API
- `year_built` - From county API
- `garage_spaces` - From county API

## MUST Extract (Not in County API)

- `hoa_fee` - **Kill-switch field**
- `beds` - Required
- `description` - Listing text

## Output Location

```
data/property_images/processed/{hash}/
├── photo_001_zillow.png
├── photo_002_zillow.png
└── ...
```

## Return Format

```json
{
  "address": "full property address",
  "status": "success|partial|failed",
  "source": "zillow|redfin|realtor",
  "data": {
    "price": 450000,
    "beds": 4,
    "baths": 2,
    "hoa_fee": 0,
    "description": "..."
  },
  "images": {
    "downloaded": 15,
    "deduplicated": 12
  },
  "errors": [],
  "files_updated": ["extraction_state.json", "image_manifest.json"]
}
```

## Error Handling

| Error | Action |
|-------|--------|
| CAPTCHA | Mark source blocked, skip |
| 404 | Property delisted, log |
| Timeout | Retry once |

## Post-Task

1. Update `address_folder_lookup.json`
2. Update `extraction_state.json` phase status
3. Update `image_manifest.json`

---

## Session Blocking Protocol

### Cache Initialization

On agent start, load or create session cache:

```python
cache_path = "data/session_cache.json"

if os.path.exists(cache_path):
    cache = json.load(open(cache_path))
    # Reset if >30 min old
    if session_age_minutes > 30:
        cache = create_new_session()
else:
    cache = create_new_session()

def create_new_session():
    return {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "blocked_sources": {
            "zillow": {"status": "available", "attempts": 0},
            "redfin": {"status": "available", "attempts": 0},
            "realtor": {"status": "available", "attempts": 0}
        }
    }
```

### Update After Each Attempt

```python
def classify_response(response):
    if response.status_code == 200:
        return ("available", "success")
    elif response.status_code == 403:
        if "perimeterx" in response.text.lower():
            return ("blocked", "perimeterx_challenge")
        return ("blocked", "403_forbidden")
    elif response.status_code == 429:
        return ("rate_limited", "429_too_many_requests")
    elif response.status_code == 404:
        return ("not_found", "property_delisted")
    return ("error", f"{response.status_code}")

# After each attempt
status, reason = classify_response(response)
cache['blocked_sources'][source]['status'] = status
cache['blocked_sources'][source]['attempts'] += 1
if status in ['blocked', 'rate_limited']:
    cache['blocked_sources'][source]['blocked_at'] = datetime.now().isoformat()
```

### Skip Logic

```python
def should_skip_source(cache, source):
    source_data = cache['blocked_sources'].get(source, {})
    status = source_data.get('status', 'available')

    if status == 'blocked':
        return (True, f"Blocked: {source_data.get('reason')}")

    if status == 'rate_limited':
        retry_after = source_data.get('retry_after')
        if retry_after and datetime.now() < datetime.fromisoformat(retry_after):
            return (True, "Rate limited - waiting for retry window")

    if source_data.get('attempts', 0) >= 3:
        return (True, "3+ failures - likely blocked for session")

    return (False, "")
```

### Return Format to Orchestrator

```json
{
  "property_hash": "ef7cd95f",
  "address": "4732 W Davis Rd, Glendale, AZ 85306",
  "extraction_status": "partial",
  "data": { "..." },
  "sources_used": ["county_api", "redfin"],
  "sources_blocked": ["zillow"],
  "session_state": {
    "blocked_count": 1,
    "available_sources": ["redfin", "realtor"],
    "recommendation": "continue"
  },
  "validation_result": {
    "kill_switch_pass": true,
    "missing_fields": ["sewer_type"]
  }
}
```

### Session State Recommendations

| Condition | Recommendation |
|-----------|----------------|
| ≥2 sources available, success_rate >0.6 | `continue` |
| 1 source available OR success_rate 0.3-0.6 | `pause` (wait 5min) |
| 0 sources OR success_rate <0.3 | `abort` |

---
name: listing-extraction
description: Extract property images and listing data from Zillow, Redfin, Realtor.com using stealth browsers (nodriver, curl_cffi). CRITICAL - Standard Playwright WILL BE BLOCKED by PerimeterX. Always use scripts/extract_images.py for Zillow/Redfin. Use for Phase 1 listing data, image downloading, or anti-bot bypass.
allowed-tools: Read, Bash(python:*), mcp__playwright__*
---

# Listing Extraction Skill

Extract property data and images from real estate listing sites with anti-bot bypass.

## CRITICAL: Stealth Required

```
+------------------------------------------------------------------+
|  WARNING: Zillow and Redfin use PerimeterX anti-bot protection   |
|  Standard Playwright WILL BE BLOCKED with CAPTCHA                |
|                                                                  |
|  ALWAYS use: python scripts/extract_images.py --address "ADDR"   |
+------------------------------------------------------------------+
```

| Site | Anti-Bot | Standard Playwright | Stealth Script |
|------|----------|---------------------|----------------|
| Zillow | PerimeterX | **BLOCKED** | Works |
| Redfin | PerimeterX | **BLOCKED** | Works |
| Realtor.com | Light | Usually works | Works |

## CLI Usage (REQUIRED)

```bash
# Single property
python scripts/extract_images.py --address "123 Main St, Phoenix, AZ 85001"

# All unprocessed
python scripts/extract_images.py --all

# Resume from checkpoint
python scripts/extract_images.py --all --resume

# Fresh start
python scripts/extract_images.py --all --fresh
```

## Project Stealth Stack

- **nodriver** - Undetected ChromeDriver
- **curl_cffi** - TLS fingerprint impersonation
- **Persistent profiles** - Maintains cookies
- **Human-like delays** - Randomized timing

## Playwright MCP (Realtor.com ONLY)

```python
# Only for Realtor.com - other sites need stealth script
mcp__playwright__browser_navigate(url="https://www.realtor.com/...")
mcp__playwright__browser_wait_for(text="bed")
mcp__playwright__browser_snapshot()
```

## Output Structure

```
data/property_images/
├── {hash}_123-main-st/
│   ├── 001_exterior.jpg
│   ├── 002_kitchen.jpg
│   └── ...
└── metadata/
    ├── extraction_state.json   # Pipeline state
    ├── image_manifest.json     # Image registry
    └── address_folder_lookup.json  # Address → folder
```

## Error Handling

| Error | Recovery |
|-------|----------|
| CAPTCHA/Blocked | Stealth script handles automatically |
| Rate limited | Exponential backoff built-in |
| 403 Forbidden | Switch to alternate source |
| No images found | Flag for manual research |

## Best Practices

1. **Always use stealth script** for Zillow/Redfin
2. **Never use raw Playwright** for protected sites
3. **Check state file** before extraction
4. **Resume on crash** with `--resume` flag
5. **Flag failures** in extraction_state.json

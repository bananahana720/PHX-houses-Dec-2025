---
name: block-playwright-zillow
enabled: true
event: bash
pattern: mcp__playwright.*(zillow|redfin|realtor\.com)|playwright.*(zillow|redfin|realtor)
action: block
---

## 🛑 Playwright Blocked for Real Estate Sites

**PerimeterX anti-bot protection will block standard Playwright on:**
- Zillow.com
- Redfin.com
- Realtor.com

### Why This Is Blocked
- These sites use advanced fingerprinting that detects Playwright
- Standard browser automation gets CAPTCHAs and blocks
- API requests fail with 403/429 responses

### Correct Approach

**For image extraction:**
```bash
python scripts/extract_images.py --url "https://www.zillow.com/homedetails/..."
```

**For listing data:**
```python
from phx_home_analysis.services.image_extraction import StealthBrowserClient
async with StealthBrowserClient() as client:
    await client.get(url)
```

### Tools That Work
- `nodriver` (undetected-chromedriver successor)
- `curl_cffi` with browser impersonation
- `scripts/extract_images.py` (combines both)

See `.claude/skills/listing-extraction.md` for full documentation.

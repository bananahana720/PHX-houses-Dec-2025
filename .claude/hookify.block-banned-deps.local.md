---
name: block-banned-deps
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (import\s+selenium|from\s+selenium|import\s+requests\b|from\s+requests\s+import)
action: block
---

## 🛑 Banned Dependency Detected

**Per CLAUDE.md:91 (Blocked dependencies)**

### ❌ Blocked Imports
```python
import selenium           # BLOCKED
from selenium import...   # BLOCKED
import requests           # BLOCKED
from requests import...   # BLOCKED
```

### ✅ Approved Alternatives

| Banned | Use Instead | Reason |
|--------|-------------|--------|
| `selenium` | `nodriver` | Undetected for anti-bot |
| `requests` | `httpx` | Async support, modern API |

### Correct Imports
```python
# For browser automation (stealth)
import nodriver as uc
from nodriver import Browser

# For HTTP requests
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Why These Are Banned
1. **selenium**: Easily detected by PerimeterX, Cloudflare
2. **requests**: Synchronous only, no HTTP/2, deprecated patterns

### Project Dependencies
See `pyproject.toml`:
- `nodriver>=0.48.1` (stealth browser)
- `httpx>=0.28.0` (async HTTP)
- `curl_cffi>=0.9.0` (browser impersonation)

### Exception Process
If you absolutely need these:
1. Document strong justification
2. Get user approval
3. Add to pyproject.toml with comment explaining why

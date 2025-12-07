---
name: require-retry-decorator
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/phx_home_analysis/(services|clients)/.*\.py$
  - field: new_text
    operator: regex_match
    pattern: (httpx\.(get|post|AsyncClient)|async\s+def\s+(fetch|extract|get_))
action: warn
---

## ⚠️ External API Call - Add @retry_with_backoff

**Per E1.S6 and E2 Wave 1 (epic-1:95-106, epic-2:297)**

### Pattern Detected
External HTTP call without retry decorator.

### ✅ Required Pattern
```python
from phx_home_analysis.errors import retry_with_backoff

@retry_with_backoff(max_retries=5, base_delay=1.0)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### Retry Configuration
| Parameter | Value | Reason |
|-----------|-------|--------|
| max_retries | 5 | Industry standard |
| base_delay | 1.0s | Exponential: 1, 2, 4, 8, 16s |
| max_delay | 60s | Cap to avoid infinite wait |
| jitter | True | Prevent thundering herd |

### Transient vs Permanent Errors
```python
TRANSIENT_ERRORS = {429, 500, 502, 503, 504}
PERMANENT_ERRORS = {400, 401, 403, 404}

def is_transient_error(status_code: int) -> bool:
    return status_code in TRANSIENT_ERRORS
```

### What Gets Retried
- ✅ 429 (Rate limited)
- ✅ 500, 502, 503, 504 (Server errors)
- ✅ ConnectionError, TimeoutError
- ❌ 400 (Bad request) - fix the request
- ❌ 401, 403 (Auth) - fix credentials
- ❌ 404 (Not found) - resource doesn't exist

### Error Handling Location
`src/phx_home_analysis/errors/retry.py`

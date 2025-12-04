# 6. Network Security

**Files:**
- `src/phx_home_analysis/services/infrastructure/stealth_http_client.py`
- `src/phx_home_analysis/services/infrastructure/browser_pool.py`

### Findings

#### ✅ STRENGTHS

1. **TLS/SSL Configuration** (orchestrator.py:297-312)
   ```python
   self._http_client = httpx.AsyncClient(
       timeout=30.0,
       follow_redirects=True,
       limits=httpx.Limits(
           max_connections=50,
           max_keepalive_connections=20,
       ),
       headers={"User-Agent": "Mozilla/5.0 ..."}
   )
   ```
   - Uses httpx with modern TLS defaults
   - Certificate validation enabled by default
   - Reasonable connection limits

2. **Retry Logic with Backoff** (stealth_http_client.py:173-311)
   ```python
   for attempt in range(self.max_retries):
       # ... download logic ...
       if attempt < self.max_retries - 1:
           wait_time = 2**attempt  # Exponential backoff
           await asyncio.sleep(wait_time)
   ```
   - Exponential backoff (1s, 2s, 4s)
   - Prevents hammering on failures
   - Respects Retry-After headers (line 197)

3. **Rate Limiting** (stealth_http_client.py:196-208)
   ```python
   if response.status_code == 429:
       retry_after = int(response.headers.get("Retry-After", "60"))
       logger.warning(f"Rate limited, retry after {retry_after}s")
       if attempt < self.max_retries - 1:
           await asyncio.sleep(retry_after)
   ```
   - Honors 429 responses
   - Extracts Retry-After header
   - Delays before retry

4. **Timeout Configuration** (stealth_http_client.py:104)
   ```python
   session_kwargs = {
       "impersonate": "chrome120",
       "timeout": self.timeout,  # Default 30s
   }
   ```
   - 30-second default timeout
   - Prevents indefinite hangs

5. **User-Agent Rotation** (browser_pool.py:39-44)
   ```python
   USER_AGENTS = [
       "Mozilla/5.0 (Windows NT 10.0; ...) Chrome/120.0.0.0",
       "Mozilla/5.0 (Windows NT 10.0; ...) Chrome/119.0.0.0",
       # Multiple realistic user agents
   ]
   ```
   - Realistic Chrome user agents
   - Version variation
   - Avoids bot detection

6. **Stealth Fingerprinting** (stealth_http_client.py:103)
   ```python
   "impersonate": "chrome120"
   ```
   - curl_cffi mimics Chrome TLS fingerprint
   - Harder to detect as bot

#### ⚠️ MEDIUM PRIORITY (P2)

**M-10: Certificate Pinning Not Implemented**

**Location:** `orchestrator.py:297-312`

**Issue:** No certificate pinning for critical domains (county assessor, CDNs). Vulnerable to MITM with compromised CA.

**Remediation:**
```python
import ssl
import certifi
from httpx import HTTPTransport

# Create custom SSL context with pinning
def create_pinned_transport(pins: dict[str, str]) -> HTTPTransport:
    """Create transport with certificate pinning.

    Args:
        pins: Dict mapping hostname to SHA256 fingerprint
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Store pins for verification callback
    ssl_context.pins = pins

    def verify_callback(conn, cert, errno, depth, ok):
        hostname = conn.get_servername()
        if hostname in pins:
            cert_der = cert.digest("sha256")
            if cert_der != pins[hostname]:
                raise ssl.SSLError(f"Certificate pin mismatch for {hostname}")
        return ok

    ssl_context.set_verify_callback(verify_callback)
    return HTTPTransport(ssl_context=ssl_context)

# Usage:
pins = {
    "mcassessor.maricopa.gov": "sha256/ABC123...",
    "photos.zillowstatic.com": "sha256/DEF456...",
}

self._http_client = httpx.AsyncClient(
    transport=create_pinned_transport(pins),
    timeout=30.0,
    # ... rest of config
)
```

**Risk Score:** MEDIUM (requires CA compromise or MITM position)

---

**M-11: No Network Segmentation**

**Location:** N/A (architectural)

**Issue:** Image extraction runs in same network context as other application components. Compromise of extraction service could pivot to other services.

**Recommendation:**
- Run extraction in isolated Docker container with limited network access
- Use network policies to restrict egress to allowed CDN IPs only
- Implement service mesh with mTLS for inter-service communication

**Risk Score:** MEDIUM (architectural improvement)

---

#### ✅ LOW PRIORITY (P3)

**L-3: HTTP/2 Not Required**

**Location:** `orchestrator.py:297`

**Issue:** httpx supports HTTP/2 but it's not enforced. HTTP/2 provides better performance and security features.

**Recommendation:**
```python
import httpx

self._http_client = httpx.AsyncClient(
    timeout=30.0,
    http2=True,  # Enable HTTP/2
    # ... rest of config
)
```

**Risk Score:** LOW (performance optimization, minimal security impact)

---

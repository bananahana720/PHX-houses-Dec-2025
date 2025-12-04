# 1. SSRF Protection

**File:** `src/phx_home_analysis/services/infrastructure/url_validator.py`

### Findings

#### ✅ STRENGTHS (No Issues)

1. **Fail-Closed Design** (Lines 46-58)
   - Default-deny with explicit allowlist
   - Unknown hosts are rejected by default
   - Proper fail-closed error handling

2. **Comprehensive Allowlist** (Lines 61-85)
   - Trusted CDN domains for real estate images
   - Zillow, Redfin, Realtor.com, county assessor sources
   - Google Maps for legitimate map tiles

3. **DNS Rebinding Protection** (Lines 300-354)
   - Resolves hostnames to IPs before fetching
   - Checks resolved IPs against blocked ranges
   - Prevents time-of-check-time-of-use (TOCTOU) attacks

4. **Extensive IP Blocking** (Lines 88-108)
   - RFC 1918 private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
   - Loopback (127.0.0.0/8), link-local (169.254.0.0/16)
   - IPv6 ranges (::1/128, fc00::/7, fe80::/10)
   - Cloud metadata IPs, carrier-grade NAT, multicast, broadcast

5. **Scheme Validation** (Lines 177-188)
   - Only HTTP/HTTPS allowed
   - Blocks file://, ftp://, gopher://, data:// URIs

6. **Raw IP Blocking** (Lines 265-298)
   - Rejects raw IP addresses in strict mode
   - Prevents bypassing DNS-based allowlist

7. **Parent Domain Matching** (Lines 256-262)
   - Allows subdomains (e.g., "img.zillowstatic.com" matches "zillowstatic.com")
   - Reduces maintenance overhead while maintaining security

#### ⚠️ MEDIUM PRIORITY (P2)

**M-1: No URL Redirect Validation**

**Location:** `url_validator.py` (validation happens before fetch, but redirects occur during fetch)
**File Reference:** `stealth_http_client.py:179` (allows redirects without re-validation)

**Issue:** The validator checks URLs before fetching, but the HTTP client allows redirects without re-validation. An attacker could use an allowed CDN domain that redirects to an internal IP.

**Exploitation Scenario:**
```python
# Attacker compromises or registers domain "evil.zillowstatic.com"
# which is allowed by parent domain matching
url = "https://evil.zillowstatic.com/image.jpg"
# URL passes validation
# Server redirects to http://169.254.169.254/latest/meta-data/
# AWS metadata endpoint is accessed
```

**Impact:** Access to cloud metadata endpoints, internal services, or localhost

**Remediation:**
```python
# In stealth_http_client.py download_image() method:

# Option 1: Disable redirects entirely
response = await session.get(url, headers=request_headers, allow_redirects=False)

# Option 2: Validate redirect targets (recommended)
import httpx
response = await session.get(
    url,
    headers=request_headers,
    follow_redirects=True,
    event_hooks={
        'response': [
            lambda r: validator.validate_url(str(r.url))
            if r.is_redirect else None
        ]
    }
)
```

**Risk Score:** MEDIUM (requires domain compromise or DNS hijacking)

---

**M-2: Parent Domain Matching Too Permissive**

**Location:** `url_validator.py:256-262`

**Issue:** The parent domain matching algorithm allows ANY subdomain level, which could be exploited if an attacker registers a subdomain under an allowed domain.

**Example:**
```python
# If "zillowstatic.com" is allowed
# These would also be allowed:
"attacker-subdomain.zillowstatic.com"  # If attacker can register
"xss.photos.zillowstatic.com"           # Multiple levels deep
```

**Impact:** If attacker can register subdomain under allowed domain (via CDN provider, DNS takeover, or subdomain takeover vulnerability)

**Remediation:**
```python
def _is_host_allowed(self, host: str) -> bool:
    """Check if host is in the allowlist with depth limit."""
    if host in self.allowed_hosts:
        return True

    # Only check ONE parent level for security
    parts = host.split(".")
    if len(parts) >= 2:
        parent = ".".join(parts[-2:])  # Only immediate parent
        if parent in self.allowed_hosts:
            return True

    return False
```

**Risk Score:** MEDIUM (requires attacker control over subdomain)

---

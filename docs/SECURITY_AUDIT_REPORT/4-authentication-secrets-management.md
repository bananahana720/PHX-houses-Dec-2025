# 4. Authentication & Secrets Management

**Files:**
- `src/phx_home_analysis/services/image_extraction/extractors/maricopa_assessor.py`
- `src/phx_home_analysis/services/infrastructure/browser_pool.py`

### Findings

#### ✅ STRENGTHS

1. **Environment Variable Secrets** (maricopa_assessor.py:81)
   ```python
   self._token = token or os.getenv("MARICOPA_ASSESSOR_TOKEN")
   ```
   - No hardcoded credentials
   - Environment-based configuration
   - Supports injection for testing

2. **Authentication Failure Handling** (maricopa_assessor.py:214-218)
   ```python
   if response.status_code == 401 or response.status_code == 403:
       raise AuthenticationError(
           self.source,
           f"Authentication failed: {response.status_code}",
       )
   ```
   - Explicit auth error detection
   - Fails securely on 401/403

3. **Token Validation** (maricopa_assessor.py:133-137)
   ```python
   if not self._token:
       raise AuthenticationError(
           self.source,
           "MARICOPA_ASSESSOR_TOKEN environment variable not set",
       )
   ```
   - Early validation before API calls
   - Clear error messages

4. **Proxy Credential Handling** (browser_pool.py:95-108)
   ```python
   self._proxy_has_auth = bool(
       proxy_url and "@" in proxy_url and "://" in proxy_url
   )
   logger.info(
       "BrowserPool configured: proxy=%s (auth=%s)",
       "enabled" if proxy_url else "disabled",
       "yes" if self._proxy_has_auth else "no",
   )
   ```
   - Detects authenticated proxies
   - Uses Chrome extension for proxy auth (avoids command-line exposure)

5. **Proxy Extension Security** (browser_pool.py:163-189)
   - Creates temporary extension for proxy auth
   - Cleanup on error and normal exit
   - Avoids credentials in command-line arguments (visible in process list)

#### 🔴 HIGH PRIORITY (P1)

**H-3: Credentials in Logs**

**Location:** Multiple files (maricopa_assessor.py:206, browser_pool.py:161)

**Issue:** Proxy URLs and API tokens could be logged, exposing credentials.

**Examples:**
```python
# browser_pool.py:161 - logs full proxy URL with credentials
logger.info(
    "Creating proxy authentication extension for: %s",
    self.proxy_url.split("@")[1]  # Still logs host, may log partial creds
)

# maricopa_assessor.py:206 - logs API URL that may contain tokens
url = f"{self.source.base_url}/search/property/?q={query_encoded}"
# If logged, could expose sensitive data
```

**Impact:** Credential exposure in log files, monitoring systems

**Remediation:**
```python
# Create sanitization helper:
def sanitize_url(url: str) -> str:
    """Remove credentials from URL for logging."""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        # Replace with ***
        netloc = f"{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        parsed = parsed._replace(netloc=netloc)
    return urlunparse(parsed)

# Use in logging:
logger.info(
    "Creating proxy extension for: %s",
    sanitize_url(self.proxy_url)
)

# Sanitize all URL logging:
logger.debug("Downloading from %s", sanitize_url(url))
```

**Risk Score:** HIGH (credential exposure in logs)

---

#### ⚠️ MEDIUM PRIORITY (P2)

**M-6: No Token Rotation Support**

**Location:** `maricopa_assessor.py:81`

**Issue:** Tokens are loaded once at initialization. No support for runtime rotation or expiry handling.

**Remediation:**
```python
class MaricopaAssessorExtractor(ImageExtractor):
    def __init__(self, ...):
        self._token = None
        self._token_refresh_fn = None

    def _get_token(self) -> str:
        """Get current valid token with refresh support."""
        if self._token_refresh_fn:
            self._token = self._token_refresh_fn()
        elif not self._token:
            self._token = os.getenv("MARICOPA_ASSESSOR_TOKEN")

        if not self._token:
            raise AuthenticationError(...)

        return self._token

    def set_token_refresh(self, refresh_fn):
        """Register token refresh callback for rotation."""
        self._token_refresh_fn = refresh_fn
```

**Risk Score:** MEDIUM (limits security best practices, not exploitable)

---

**M-7: Proxy Extension Cleanup Timing**

**Location:** `browser_pool.py:336-345`

**Issue:** Proxy extension is only cleaned up when browser closes. If browser crashes, temporary extension directory persists with credentials.

**Remediation:**
```python
import atexit

def __init__(self, ...):
    # Existing code...

    # Register cleanup on process exit
    if self._proxy_extension:
        atexit.register(self._cleanup_proxy_extension)

def _cleanup_proxy_extension(self):
    """Cleanup proxy extension safely."""
    if self._proxy_extension is not None:
        try:
            self._proxy_extension.cleanup()
        except Exception as e:
            logger.error("Error cleaning up proxy extension: %s", e)
        finally:
            self._proxy_extension = None
```

**Risk Score:** MEDIUM (credential exposure via temp files)

---

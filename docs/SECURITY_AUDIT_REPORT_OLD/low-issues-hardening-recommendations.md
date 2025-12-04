# LOW Issues (Hardening Recommendations)

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

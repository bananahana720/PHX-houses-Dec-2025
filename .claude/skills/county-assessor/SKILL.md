---
name: county-assessor
description: Extract property data from Maricopa County Assessor API (lot size, year built, garage, pool, valuations). Use for authoritative property data lookup, Phase 0 data collection, or verifying listing claims.
allowed-tools: Read, Bash(python:*), WebFetch
---

# Maricopa County Assessor API Skill

Expert at extracting authoritative property data from the Maricopa County Assessor's office.

## Environment Setup

**Required:** `MARICOPA_ASSESSOR_TOKEN` environment variable

```bash
export MARICOPA_ASSESSOR_TOKEN="your_token_here"
```

## CLI Usage

```bash
# Single property
python scripts/extract_county_data.py --address "123 Main St, Phoenix, AZ 85001"

# All properties
python scripts/extract_county_data.py --all

# Only update missing fields (preserve existing)
python scripts/extract_county_data.py --all --update-only

# Preview without saving
python scripts/extract_county_data.py --all --dry-run
```

## Fields Retrieved

| Field | API Source | Type | Notes |
|-------|-----------|------|-------|
| `lot_sqft` | LotSize | int | **Kill-switch field** (7k-15k) |
| `year_built` | ConstructionYear | int | **Kill-switch field** (<2024) |
| `garage_spaces` | NumberOfGarages | int | **Kill-switch field** (2+) |
| `has_pool` | Pool sqft | bool | Truthy = has pool |
| `livable_sqft` | LivableSpace | int | Interior square footage |
| `baths` | BathFixtures / 3 | float | Estimated from fixtures |
| `full_cash_value` | Valuations array | int | Tax assessment value |
| `roof_type` | RoofType | str | Tile, shingle, etc. |

## Fields NOT Available

| Field | Where to Get |
|-------|-------------|
| `sewer_type` | Manual lookup (city GIS) |
| `beds` | Listing sites |
| `hoa_fee` | Listing sites |
| `tax_annual` | Treasurer API (separate) |

## API Response Structure

```json
{
  "ParcelNumber": "123-45-678",
  "Address": {
    "FullAddress": "123 MAIN ST",
    "City": "PHOENIX",
    "Zip": "85001"
  },
  "Residence": {
    "LivableSpace": 1850,
    "LotSize": 8500,
    "ConstructionYear": 1998,
    "NumberOfGarages": 2,
    "Pool": 0,
    "BathFixtures": 9,
    "RoofType": "TILE"
  },
  "Valuations": [
    {
      "Year": 2024,
      "FullCashValue": 425000
    }
  ]
}
```

## Direct API Access

```python
import os
import httpx

ASSESSOR_BASE = "https://mcassessor.maricopa.gov/api/v1"

def search_parcel(address: str) -> dict | None:
    """Search for parcel by address."""
    token = os.environ.get("MARICOPA_ASSESSOR_TOKEN")
    if not token:
        raise ValueError("MARICOPA_ASSESSOR_TOKEN not set")

    headers = {"Authorization": f"Bearer {token}"}

    # Search endpoint
    resp = httpx.get(
        f"{ASSESSOR_BASE}/search",
        params={"address": address},
        headers=headers,
        timeout=30
    )

    if resp.status_code != 200:
        return None

    results = resp.json()
    return results[0] if results else None

def get_parcel_details(parcel_number: str) -> dict:
    """Get full parcel details by APN."""
    token = os.environ.get("MARICOPA_ASSESSOR_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.get(
        f"{ASSESSOR_BASE}/parcels/{parcel_number}",
        headers=headers,
        timeout=30
    )

    return resp.json()
```

## Data Extraction Function

```python
def extract_county_data(address: str) -> dict:
    """Extract all available county data for address.

    Returns:
        Dict with county-sourced fields
    """
    parcel = search_parcel(address)
    if not parcel:
        return {"error": "parcel_not_found"}

    details = get_parcel_details(parcel["ParcelNumber"])
    residence = details.get("Residence", {})

    # Extract and transform
    return {
        "parcel_number": parcel["ParcelNumber"],
        "lot_sqft": residence.get("LotSize"),
        "year_built": residence.get("ConstructionYear"),
        "garage_spaces": residence.get("NumberOfGarages", 0),
        "has_pool": bool(residence.get("Pool", 0)),
        "livable_sqft": residence.get("LivableSpace"),
        "baths": round(residence.get("BathFixtures", 0) / 3, 1),
        "roof_type": residence.get("RoofType"),
        "full_cash_value": get_latest_valuation(details),
        "_county_data_source": "maricopa_assessor",
        "_county_data_retrieved": datetime.now().isoformat()
    }

def get_latest_valuation(details: dict) -> int | None:
    """Get most recent full cash value from valuations."""
    valuations = details.get("Valuations", [])
    if not valuations:
        return None

    # Sort by year descending
    sorted_vals = sorted(valuations, key=lambda v: v.get("Year", 0), reverse=True)
    return sorted_vals[0].get("FullCashValue")
```

## Integration with Pipeline

### Phase 0: County Data Extraction

```python
def run_phase0(address: str) -> dict:
    """Execute Phase 0: County data extraction.

    Returns:
        Status dict with extracted data or error
    """
    update_phase(address, "phase0_county", "in_progress")

    try:
        data = extract_county_data(address)

        if "error" in data:
            update_phase(address, "phase0_county", "failed")
            return {"status": "failed", "error": data["error"]}

        # Update enrichment
        update_property(address, data)

        # Early kill-switch check
        passed, failures = check_county_kill_switches(data)
        if not passed:
            update_phase(address, "phase0_county", "complete")
            return {
                "status": "kill_switch_fail",
                "failures": failures,
                "skip_remaining_phases": True
            }

        update_phase(address, "phase0_county", "complete")
        return {"status": "success", "data": data}

    except Exception as e:
        update_phase(address, "phase0_county", "failed")
        return {"status": "error", "error": str(e)}
```

## Error Handling

| Error | Action |
|-------|--------|
| Token missing | Skip county extraction, mark phase "skipped" |
| Parcel not found | Log warning, continue with listing data |
| API timeout | Retry once with longer timeout |
| Rate limit (429) | Wait 60s, retry |
| Invalid address | Try normalized variants |

## Address Normalization

```python
def normalize_address(address: str) -> list[str]:
    """Generate address variants for search.

    Returns:
        List of address variants to try
    """
    variants = [address]

    # Remove unit/apt
    import re
    no_unit = re.sub(r'\s+(apt|unit|#)\s*\S+', '', address, flags=re.I)
    if no_unit != address:
        variants.append(no_unit)

    # Abbreviate direction
    abbrev = address.replace(" North ", " N ").replace(" South ", " S ")
    abbrev = abbrev.replace(" East ", " E ").replace(" West ", " W ")
    if abbrev != address:
        variants.append(abbrev)

    return variants
```

## Best Practices

1. **Run early** - Phase 0 before other agents (authoritative data)
2. **Check token** - Fail gracefully if `MARICOPA_ASSESSOR_TOKEN` not set
3. **Preserve existing** - Use `--update-only` to avoid overwriting manual data
4. **Track source** - Add `_county_data_source` field for audit
5. **Early kill-switch** - Check lot/year/garage before expensive phases

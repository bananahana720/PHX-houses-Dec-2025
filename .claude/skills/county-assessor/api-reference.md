# County Assessor API Reference

This reference file contains detailed API documentation for the Maricopa County Assessor.

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

## Phase 0 Integration

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

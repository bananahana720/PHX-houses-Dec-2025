# Code Examples

### FEMA NFHL Flood Zone Query (Python)

```python
import requests
from typing import Optional, Dict, Any

def get_flood_zone(lat: float, lon: float) -> Dict[str, Any]:
    """
    Query FEMA NFHL for flood zone at given coordinates.

    Args:
        lat: Latitude (e.g., 33.448)
        lon: Longitude (e.g., -112.074)

    Returns:
        Dict with flood zone information
    """
    base_url = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"

    params = {
        "where": "1=1",
        "geometry": f"{lon},{lat}",  # Note: lon,lat order!
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelWithin",
        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE",
        "returnGeometry": "false",
        "f": "json"
    }

    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data.get("features"):
        attrs = data["features"][0]["attributes"]
        return {
            "flood_zone": attrs.get("FLD_ZONE"),
            "zone_subtype": attrs.get("ZONE_SUBTY"),
            "sfha": attrs.get("SFHA_TF") == "T",
            "base_flood_elevation": attrs.get("STATIC_BFE"),
            "high_risk": attrs.get("SFHA_TF") == "T"
        }

    return {
        "flood_zone": "X",  # Default to minimal risk if no data
        "zone_subtype": None,
        "sfha": False,
        "base_flood_elevation": None,
        "high_risk": False,
        "note": "No NFHL data for this location"
    }


# Example usage
if __name__ == "__main__":
    # Phoenix City Hall coordinates
    result = get_flood_zone(lat=33.4484, lon=-112.0740)
    print(f"Flood Zone: {result['flood_zone']}")
    print(f"High Risk (SFHA): {result['high_risk']}")
```

### Maricopa County Assessor API (Python)

```python
# Using the mcaapi package
# pip install mcaapi

import mcaapi

# Set API key (obtain from Maricopa County Assessor's Office)
mcaapi.set_key("YOUR_API_KEY")

def get_property_data(address: str) -> dict:
    """
    Query Maricopa County Assessor for property data.

    Args:
        address: Property address string

    Returns:
        Dict with property information
    """
    # Search for property
    results = mcaapi.Search.all(address)

    if not results:
        return {"error": "Property not found"}

    # Get first match APN
    apn = results[0].get("apn")

    # Get detailed parcel information
    details = mcaapi.Parcel.details(apn)

    # Get valuation history
    valuation = mcaapi.Parcel.valuation(apn)

    return {
        "apn": apn,
        "address": details.get("address"),
        "year_built": details.get("year_built"),
        "lot_sqft": details.get("lot_size"),
        "living_sqft": details.get("living_area"),
        "bedrooms": details.get("bedrooms"),
        "bathrooms": details.get("bathrooms"),
        "pool": details.get("pool"),
        "garage": details.get("garage"),
        "zoning": details.get("zoning"),
        "valuations": valuation
    }


# Example usage
if __name__ == "__main__":
    prop = get_property_data("301 W Jefferson, Phoenix")
    print(f"APN: {prop.get('apn')}")
    print(f"Year Built: {prop.get('year_built')}")
```

### FEMA NFHL Query (cURL)

```bash
# Query flood zone for Phoenix coordinates
curl -X GET "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query" \
  --data-urlencode "where=1=1" \
  --data-urlencode "geometry=-112.074,33.448" \
  --data-urlencode "geometryType=esriGeometryPoint" \
  --data-urlencode "inSR=4326" \
  --data-urlencode "spatialRel=esriSpatialRelWithin" \
  --data-urlencode "outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF" \
  --data-urlencode "returnGeometry=false" \
  --data-urlencode "f=json"
```

### Batch Flood Zone Lookup (Python)

```python
import requests
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_flood_zone_lookup(
    coordinates: List[Dict[str, float]],
    max_workers: int = 5,
    delay_seconds: float = 0.2
) -> List[Dict]:
    """
    Batch lookup flood zones for multiple coordinates.

    Args:
        coordinates: List of {"lat": float, "lon": float} dicts
        max_workers: Concurrent request limit
        delay_seconds: Delay between requests (be nice to FEMA servers)

    Returns:
        List of flood zone results
    """
    results = []

    def lookup_single(coord: Dict) -> Dict:
        time.sleep(delay_seconds)  # Rate limiting
        result = get_flood_zone(coord["lat"], coord["lon"])
        result["input_lat"] = coord["lat"]
        result["input_lon"] = coord["lon"]
        result["address"] = coord.get("address", "")
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(lookup_single, coord): coord
            for coord in coordinates
        }

        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                coord = futures[future]
                results.append({
                    "input_lat": coord["lat"],
                    "input_lon": coord["lon"],
                    "error": str(e)
                })

    return results
```

---

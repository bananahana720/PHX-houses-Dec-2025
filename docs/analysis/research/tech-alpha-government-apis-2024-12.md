# Tech-Alpha: Government API Research Report

**Research Date:** December 2024
**Mission:** Technical research for PHX Houses Analysis Pipeline
**Focus Areas:** Maricopa County Permit API, FEMA National Flood Hazard Layer API

---

## Executive Summary

This report provides technical research findings on government APIs relevant to the PHX Houses Analysis Pipeline project. The research covers two primary areas:

1. **Maricopa County Permit Data** - No direct permit API exists. The county uses the Accela-based Permit Center system (launched June 2024) with web portal access only. However, the **Maricopa County Assessor API** provides excellent property data access with a Python wrapper available.

2. **FEMA National Flood Hazard Layer (NFHL)** - Free, no-authentication REST API access available through ArcGIS services at `hazards.fema.gov`. Direct coordinate-based queries return flood zone designations in JSON format.

**Key Recommendation:** Integrate FEMA NFHL API for flood zone lookup (free, no auth required). For permits, use web scraping or public records requests as no API is available.

---

## Table of Contents

1. [TECH-01: Maricopa County Permit API Access](#tech-01-maricopa-county-permit-api-access)
2. [TECH-02: FEMA National Flood Hazard Layer API](#tech-02-fema-national-flood-hazard-layer-api)
3. [API Specification Tables](#api-specification-tables)
4. [Code Examples](#code-examples)
5. [Implementation Recommendations](#implementation-recommendations)
6. [Sources](#sources)

---

## TECH-01: Maricopa County Permit API Access

### Overview

**Confidence Level: [High]**

Maricopa County does NOT provide a direct API for building permit data. The county launched its new online "Permit Center" system in June 2024, consolidating multiple department systems into a single Accela-based platform.

### Permit Center System (June 2024)

**Confidence Level: [High]**

The Maricopa County Permit Center is an Accela-based system serving multiple departments:

| Department | Code | Permit Types |
|------------|------|--------------|
| Environmental Services | ENV | Environmental permits |
| Planning & Development | PND | Building, mechanical, electrical, plumbing |
| Flood Control District | FCD | Drainage, flood-related |
| Transportation | MCDOT | Right-of-way, road work |

**Key URLs:**
- Permit Center: https://www.maricopa.gov/6003/Maricopa-Countys-Permit-Center
- Historical Permits (1999-June 2024): https://apps.pnd.maricopa.gov/PermitViewer
- Accela Citizen Access: https://accela.maricopa.gov/CitizenAccessMCOSS/

### Permit Types for HVAC/Roof Determination

**Confidence Level: [Medium]**

Arizona building code requires permits for:
- **Mechanical Permits**: HVAC system installation, replacement, or repair
- **Roofing Permits**: Roof replacement (typically required for re-roofing)
- **Building Permits**: Major structural work

Permit records typically include:
- Permit type (Building, Mechanical, Plumbing, Electrical)
- Issue date and expiration date
- Contractor name and license number
- Work description
- Property address/parcel number
- Inspection status

**Limitation:** Without API access, determining HVAC/roof replacement dates requires manual permit search or public records requests.

### Alternative: Maricopa County Assessor API

**Confidence Level: [High]**

While no permit API exists, the **Maricopa County Assessor** provides a robust property data API:

| Feature | Details |
|---------|---------|
| Authentication | API key required (free, request via contact form) |
| Python Wrapper | `mcaapi` package on PyPI |
| Data Available | Parcel details, ownership, valuations, physical features, zoning |
| Documentation | https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf |

**API Request Process:**
1. Visit https://preview.mcassessor.maricopa.gov/contact/
2. Set Subject to "API Token/Question"
3. Provide name, number, and brief note
4. Receive API key via email

### City of Phoenix Permits (Alternative)

**Confidence Level: [Medium]**

For properties within Phoenix city limits (not unincorporated Maricopa County):

| Resource | URL | Access Type |
|----------|-----|-------------|
| PDD Online Permit Search | https://apps-secure.phoenix.gov/pdd/search/permits | Web portal |
| Issued Permits Search | https://apps-secure.phoenix.gov/PDD/Search/IssuedPermit | Web portal + CSV export |
| Phoenix Open Data | https://www.phoenixopendata.com | CKAN API (limited permit data) |

**Note:** Phoenix Open Data includes building permit datasets from the HUD SOCDS database, but these are aggregate statistics, not individual permit records.

### Data Access Options Summary

| Method | Data Freshness | Automation | Cost |
|--------|---------------|------------|------|
| Permit Center Web Portal | Real-time | Manual only | Free |
| Historical Permit Viewer | 1999-2024 | Manual only | Free |
| Public Records Request | Varies | Batch requests | Free |
| Accela API (if enabled) | Real-time | Full automation | Unknown |
| Web Scraping | Real-time | Semi-automated | Free (legal concerns) |

---

## TECH-02: FEMA National Flood Hazard Layer API

### Overview

**Confidence Level: [High]**

FEMA provides free, no-authentication access to the National Flood Hazard Layer (NFHL) through ArcGIS REST services. The NFHL contains flood hazard data covering over 90% of the U.S. population.

### API Endpoints

**Confidence Level: [High]**

**Primary REST Service:**
```
https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer
```

**Key Layers:**

| Layer ID | Name | Description |
|----------|------|-------------|
| 28 | S_Fld_Haz_Ar | Flood Hazard Areas (main layer for zone queries) |
| 17 | Flood Hazard Zone Labels | Label layer |
| 14 | Cross Sections | Hydraulic cross-sections |

**Alternative Endpoints:**
- KMZ Service: `https://hazards.fema.gov/gis/nfhl/rest/services/KMZ/KMZ/MapServer`
- Public NFHL: `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer`

### Authentication Requirements

**Confidence Level: [High]**

| Requirement | Status |
|-------------|--------|
| API Key | **Not required** |
| Registration | **Not required** |
| Rate Limiting | Not officially documented; no known limits for reasonable use |
| TLS Version | TLS 1.2 required (with Cipher Suites) |

**Note:** Applications using Windows 2012 R2 or earlier, or those not supporting TLS 1.2, will fail to connect.

### Query Parameters

**Confidence Level: [High]**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `where` | `1=1` | Required placeholder |
| `geometry` | `-112.074,33.448` | Longitude,Latitude (note order!) |
| `geometryType` | `esriGeometryPoint` | Point query |
| `inSR` | `4326` | Input spatial reference (WGS84) |
| `spatialRel` | `esriSpatialRelWithin` | Spatial relationship |
| `outFields` | `FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE` | Fields to return |
| `returnGeometry` | `false` | Exclude geometry for faster response |
| `f` | `json` or `pjson` | Output format (pjson = pretty JSON) |

### Response Fields (S_Fld_Haz_Ar)

**Confidence Level: [High]**

| Field | Type | Description |
|-------|------|-------------|
| `FLD_ZONE` | String | Flood zone code (A, AE, AH, AO, X, etc.) |
| `ZONE_SUBTY` | String | Zone subtype (FLOODWAY, etc.) |
| `SFHA_TF` | String | Special Flood Hazard Area (T=True, F=False) |
| `STATIC_BFE` | Number | Base Flood Elevation (if constant) |
| `V_DATUM` | String | Vertical datum reference |
| `DEPTH` | Number | Depth for Zone AO areas |
| `DFIRM_ID` | String | Digital Flood Insurance Rate Map ID |
| `SOURCE_CIT` | String | Source citation |

### Flood Zone Codes Reference

**Confidence Level: [High]**

| Zone | Risk Level | Insurance Required? | Description |
|------|------------|---------------------|-------------|
| **A** | High | Yes | 1% annual chance flood, no BFE |
| **AE** | High | Yes | 1% annual chance flood, BFE determined |
| **AH** | High | Yes | Shallow flooding (1-3 ft), ponding |
| **AO** | High | Yes | Shallow flooding, sheet flow |
| **VE** | High (Coastal) | Yes | Coastal high hazard with wave action |
| **X (shaded)** | Moderate | No | 0.2% annual chance (500-year) |
| **X (unshaded)** | Low | No | Minimal flood hazard |
| **D** | Undetermined | No | Possible but undetermined risk |

**Key Insight for PHX Houses:** Most Phoenix metro properties will be in Zone X (unshaded) or Zone D. Properties in A/AE zones near washes or the Salt River require careful evaluation.

### OpenFEMA API (Complementary)

**Confidence Level: [High]**

OpenFEMA provides additional flood-related datasets (not the same as NFHL):

| Feature | Details |
|---------|---------|
| Base URL | `https://www.fema.gov/api/open/v2/` |
| Authentication | **Not required** |
| Rate Limits | Default 1,000 records, max 10,000 per call |
| Datasets | Disaster declarations, NFIP claims, grants, etc. |
| Documentation | https://www.fema.gov/about/openfema/api |

**Relevant Datasets:**
- NFIP Claims (`FimaNfipClaims`)
- NFIP Policies (`FimaNfipPolicies`)

---

## API Specification Tables

### FEMA NFHL REST API

| Specification | Value |
|---------------|-------|
| Base URL | `https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query` |
| Protocol | HTTPS (TLS 1.2 required) |
| Method | GET |
| Authentication | None |
| Response Format | JSON only |
| Max Records | 2,000 per request |
| Rate Limit | Not documented |

### Maricopa County Assessor API

| Specification | Value |
|---------------|-------|
| Base URL | `https://api.mcassessor.maricopa.gov/` |
| Protocol | HTTPS |
| Method | GET |
| Authentication | API Key (header: `Authorization: Token <key>`) |
| Response Format | JSON |
| Python Package | `mcaapi` |
| Documentation | https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf |

### Accela Construct API (If Maricopa Enables)

| Specification | Value |
|---------------|-------|
| Base URL | `https://apis.accela.com` |
| Protocol | HTTPS |
| Method | REST (GET, POST, PUT, DELETE) |
| Authentication | OAuth 2.0 |
| Documentation | https://developer.accela.com/docs/api_reference/api-index.html |

**Note:** Maricopa County's Accela implementation may not have API access enabled for public use.

---

## Code Examples

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

## Implementation Recommendations

### For PHX Houses Analysis Pipeline

#### 1. FEMA NFHL Integration (Recommended)

**Priority: High** | **Effort: Low** | **Confidence: [High]**

Create a new script `scripts/extract_flood_zone.py`:

```python
# Integration approach
# 1. Add flood_zone field to enrichment_data.json schema
# 2. Query FEMA NFHL during Phase 0 (alongside county data)
# 3. Add flood zone to kill-switch criteria:
#    - HARD FAIL: Zone A, AE, AH, AO, VE (SFHA = True)
#    - WARNING: Zone X (shaded), Zone D
#    - PASS: Zone X (unshaded)
```

**Data Model Addition:**
```python
class FloodData(BaseModel):
    flood_zone: str  # "X", "AE", etc.
    zone_subtype: Optional[str]
    sfha: bool  # Special Flood Hazard Area
    base_flood_elevation: Optional[float]
    query_timestamp: datetime
```

#### 2. Maricopa County Assessor API Integration

**Priority: Medium** | **Effort: Medium** | **Confidence: [High]**

The existing `scripts/extract_county_data.py` likely already uses this API. Verify the following fields are being extracted:

- `year_built` - For age calculations
- `lot_sqft` - For kill-switch criteria
- `garage_spaces` - For kill-switch criteria
- `pool` - For Arizona context scoring
- `living_sqft` - For value analysis

#### 3. Permit Data Access (Not Recommended for Automation)

**Priority: Low** | **Effort: High** | **Confidence: [Medium]**

Due to lack of API access, permit data should be:
- Obtained via manual inspection of seller disclosures
- Requested via public records when evaluating serious candidates
- Used for due diligence, not initial screening

#### 4. Future Considerations

**Accela API Monitoring:**
- Monitor Maricopa County for potential API access
- Contact form: https://preview.mcassessor.maricopa.gov/contact/

**OpenFEMA Integration:**
- Consider querying NFIP claims history for property addresses
- High claim counts indicate recurring flood issues

---

## Sources

### Maricopa County Sources

1. [Maricopa County Permit Center](https://www.maricopa.gov/6003/Maricopa-Countys-Permit-Center) - Official permit portal documentation
2. [Maricopa County Assessor API Documentation](https://mcassessor.maricopa.gov/file/home/MC-Assessor-API-Documentation.pdf) - Official API documentation PDF
3. [Maricopa County GIS Open Data](https://data-maricopa.opendata.arcgis.com/) - Open data portal
4. [Maricopa County Assessor's Office](https://mcassessor.maricopa.gov) - Main assessor website
5. [mcaapi Python Package](https://pypi.org/project/mcaapi/) - Python wrapper for Assessor API
6. [Accela Developer Portal](https://developer.accela.com/docs/api_reference/api-index.html) - Accela API documentation
7. [Construction Permit Information](https://www.maricopa.gov/1629/Construction-Permit-Information) - Permit requirements
8. [Historical Permit Viewer](https://apps.pnd.maricopa.gov/PermitViewer) - Pre-2024 permit search

### FEMA NFHL Sources

9. [FEMA National Flood Hazard Layer](https://www.fema.gov/flood-maps/national-flood-hazard-layer) - Official NFHL page
10. [GIS Web Services for FEMA NFHL](https://hazards.fema.gov/femaportal/wps/portal/NFHLWMS) - GIS services portal
11. [FEMA NFHL REST Services](https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer) - REST API endpoint
12. [FEMA's NFHL Viewer](https://www.arcgis.com/apps/webappviewer/index.html?id=8b0adb51996444d4879338b5529aa9cd) - Interactive viewer
13. [OpenFEMA API Documentation](https://www.fema.gov/about/openfema/api) - OpenFEMA API docs
14. [OpenFEMA Data Sets](https://www.fema.gov/about/openfema/data-sets) - Available datasets
15. [FEMA Flood Zones Glossary](https://www.fema.gov/about/glossary/flood-zones) - Zone definitions
16. [NFHL R Package](https://github.com/mikejohnson51/NFHL) - R interface for NFHL
17. [National Flood Hazard Layer Hub](https://gis-fema.hub.arcgis.com/datasets/FEMA::national-flood-hazard-layer-2/about) - ArcGIS Hub

### City of Phoenix Sources

18. [Phoenix PDD Permit Search](https://apps-secure.phoenix.gov/pdd/search/permits) - Permit search portal
19. [Phoenix Open Data](https://www.phoenixopendata.com) - City open data portal
20. [Phoenix Building Permits Dataset](https://www.phoenixopendata.com/dataset/phoenix-az-building-permit-data) - SOCDS data

### Additional Technical Sources

21. [Stack Overflow: FEMA NFHL ArcGIS API Access](https://stackoverflow.com/questions/51563574/fema-nfhl-flood-hazard-zones-arcgis-online-api-access-through-vba) - Query examples
22. [FEMA How to Read Flood Maps](https://www.fema.gov/sites/default/files/documents/how-to-read-flood-insurance-rate-map-tutorial.pdf) - Official tutorial
23. [ClimateCheck: FEMA Flood Zones Explained](https://climatecheck.com/risks/flood/what-are-the-flood-zones-in-fema-maps) - Zone explanations

---

## Appendix A: Sample API Responses

### FEMA NFHL Query Response

```json
{
  "displayFieldName": "FLD_ZONE",
  "fieldAliases": {
    "FLD_ZONE": "FLD_ZONE",
    "ZONE_SUBTY": "ZONE_SUBTY",
    "SFHA_TF": "SFHA_TF",
    "STATIC_BFE": "STATIC_BFE"
  },
  "fields": [
    {"name": "FLD_ZONE", "type": "esriFieldTypeString", "alias": "FLD_ZONE", "length": 55},
    {"name": "ZONE_SUBTY", "type": "esriFieldTypeString", "alias": "ZONE_SUBTY", "length": 72},
    {"name": "SFHA_TF", "type": "esriFieldTypeString", "alias": "SFHA_TF", "length": 1},
    {"name": "STATIC_BFE", "type": "esriFieldTypeDouble", "alias": "STATIC_BFE"}
  ],
  "features": [
    {
      "attributes": {
        "FLD_ZONE": "X",
        "ZONE_SUBTY": null,
        "SFHA_TF": "F",
        "STATIC_BFE": null
      }
    }
  ]
}
```

### Maricopa County Assessor Search Response

```json
{
  "results": [
    {
      "apn": "11219038A",
      "address": "301 W JEFFERSON ST",
      "city": "PHOENIX",
      "zip": "85003",
      "owner": "MARICOPA COUNTY"
    }
  ]
}
```

---

*Report generated by Tech-Alpha research agent for PHX Houses Analysis Pipeline*
*Last updated: December 2024*

# TECH-02: FEMA National Flood Hazard Layer API

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

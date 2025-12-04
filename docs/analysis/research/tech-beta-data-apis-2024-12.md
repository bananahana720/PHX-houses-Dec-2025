# Third-Party Data API Research Report

**Research Focus:** Crime Data, WalkScore, and Energy Usage Estimation APIs
**Date:** December 2024
**Project:** PHX Houses Analysis Pipeline
**Researcher:** Tech-Beta Agent

---

## Executive Summary

This report evaluates third-party APIs for integration into the PHX Houses Analysis Pipeline across three critical domains: crime data, walkability scores, and residential energy usage estimation.

### Key Findings

| Domain | Best Option | Cost | Data Granularity | Confidence |
|--------|-------------|------|------------------|------------|
| Crime Data | Phoenix Open Data + FBI CDE | Free | Address/Zip | High |
| WalkScore | WalkScore API | Free tier (5K/day) | Address | High |
| Energy Estimation | EIA API + BEopt | Free | Home characteristics | Medium |

### Recommendations for PHX Houses Pipeline

1. **Crime Data**: Use Phoenix Open Data Portal (free, address-level) as primary source, FBI Crime Data Explorer as supplemental
2. **WalkScore**: Integrate WalkScore API free tier for initial deployment; evaluate Professional tier if volume exceeds 5K/day
3. **Energy**: Combine EIA statistical data with BEopt/NREL ResStock for Phoenix-specific estimations

---

## TECH-03: Crime Data APIs

### Available Crime Data APIs

#### 1. Phoenix Open Data Portal (Recommended for PHX)

**Overview:** City of Phoenix provides daily-updated crime data through their open data portal.

| Feature | Details | Confidence |
|---------|---------|------------|
| Data URL | `https://phoenixopendata.com/dataset/crime-data` | High |
| Formats | CSV, TSV, JSON, XML | High |
| Update Frequency | Daily (by 11am) | High |
| Historical Range | November 2015 - present | High |
| Cost | Free | High |
| Crimes Included | Homicides, rapes, robberies, aggravated assaults, burglaries, thefts, motor vehicle thefts, arsons, drug offenses | High |

**API Access:**
```
https://www.phoenixopendata.com/dataset/cc08aace-9ca9-467f-b6c1-f0879ab1a358/resource/0ce3411a-2fc6-4302-a33f-167f68608a20/download/crime-data_crime-data_crimestat.csv
```

**Important Note:** As of September 2025, updates are temporarily unavailable. The city is actively working to restore daily updates. [Medium Confidence]

**Sources:**
- [Phoenix Open Data Crime Dataset](https://phoenixopendata.com/dataset/crime-data)
- [Phoenix Police Crime Stats](https://www.phoenix.gov/administration/departments/police/crime-stats-data.html)

---

#### 2. FBI Crime Data Explorer API

**Overview:** Free government API providing Uniform Crime Reporting (UCR) data for the entire United States.

| Feature | Details | Confidence |
|---------|---------|------------|
| Base URL | `https://api.usa.gov/crime/fbi/sapi` | High |
| API Key Required | Yes (free from api.data.gov) | High |
| Cost | Free | High |
| Coverage | National (16,000+ agencies, 95.6% population) | High |
| Data Format | JSON, CSV | High |
| Update Frequency | Quarterly | High |

**Getting Started:**
1. Register for free API key at: https://api.data.gov/signup/
2. Documentation: https://github.com/fbi-cde/crime-data-api

**Data Reporting Systems:**
- **SRS (Summary Reporting System):** Legacy format with aggregated crime counts
- **NIBRS (National Incident-Based Reporting System):** Detailed incident-level data including time of day, demographics, relationships

**2024 Data:** The FBI released data on over 14 million criminal offenses for 2024. [High Confidence]

**Sources:**
- [FBI Crime Data Explorer](https://cde.ucr.cjis.gov/)
- [FBI CDE GitHub](https://github.com/fbi-cde/crime-data-api)
- [DOJ Developer Resources](https://www.justice.gov/developer)

---

#### 3. CrimeOMeter API

**Overview:** Commercial worldwide crime data API with address-level granularity.

| Feature | Details | Confidence |
|---------|---------|------------|
| Base URL | `https://api.crimeometer.com/v2/` | High |
| Authentication | API Key | High |
| Coverage | Worldwide (US focus) | Medium |
| Granularity | Lat/Long coordinates | High |

**Pricing (via RapidAPI):**

| Plan | Calls/Month | Price | Per Request |
|------|-------------|-------|-------------|
| Basic | 10 | Free | - |
| Pro | 100 | $30/month | $0.30 |
| Ultra | 1,000 | $249/month | $0.25 |
| Mega | 5,000 | $490/month | $0.10 |

**API Endpoints:**
- `/crime-incidents` - Raw crime data with granular filters
- `/crime-statistics` - Aggregate neighborhood stats
- `/sex-offenders` - Sex offender registry data

**Example Request:**
```
GET https://api.crimeometer.com/v2/crime-incidents?lat=33.4484&lon=-112.0740&datetime_ini=2024-01-01&datetime_end=2024-12-31&distance=0.5mi
```

[Medium Confidence - pricing may vary]

**Sources:**
- [CrimeOMeter Official](https://www.crimeometer.com/crime-data-api)
- [RapidAPI CrimeOMeter](https://rapidapi.com/crimeometer/api/crimeometer/pricing)

---

#### 4. NeighborhoodScout / Location Inc. (Enterprise)

**Overview:** Premium enterprise-grade crime data with 98% accurate neighborhood crime risk scoring.

| Feature | Details | Confidence |
|---------|---------|------------|
| Data Points | 9 million+ processed crimes | High |
| Coverage | 100% US coverage | High |
| Granularity | Address-specific via SecurityGauge | High |
| Delivery | API or Bulk File | High |
| Starting Price | $5,000/year | Medium |

**Crime Categories:** Murder, rape, robbery, assault, burglary, theft, motor vehicle theft

**Limitations:**
- Not for external website display
- Enterprise licensing required
- Contact required for API access

**Sources:**
- [Location Inc. Crime Data Licensing](https://locationinc.com/license-neighborhoodscout-crime-data/)
- [NeighborhoodScout Data](https://api.locationinc.com/about-the-data)

---

#### 5. SpotCrime

**Overview:** Crime mapping service with limited unofficial API access.

| Feature | Details | Confidence |
|---------|---------|------------|
| Official API | Contact required (api@spotcrime.com) | High |
| Unofficial Wrappers | Available but unstable | High |
| Pricing | Not published; contact for quote | Low |
| Stability | Keys change frequently; not recommended for production | High |

**Warning:** SpotCrime actively discourages unofficial API usage. For reliable municipal data, consider https://municipal.systems/ instead. [High Confidence]

**Sources:**
- [SpotCrime Blog - API](https://blog.spotcrime.com/2019/03/the-spotcrime-api.html)
- [GitHub - spotcrime wrapper](https://github.com/yocontra/spotcrime)

---

#### 6. BestPlaces

**Status:** No public API found. Website provides crime statistics for comparison purposes but does not advertise developer API access. [Medium Confidence]

**Recommendation:** Contact BestPlaces directly for data licensing inquiries.

---

### Crime Data API Comparison Matrix

| Provider | Free Tier | Address-Level | Phoenix Data | API Quality | Best For |
|----------|-----------|---------------|--------------|-------------|----------|
| Phoenix Open Data | Yes | Yes | Excellent | Good | Local PHX analysis |
| FBI CDE | Yes | No (city-level) | Yes | Excellent | National comparisons |
| CrimeOMeter | 10 calls | Yes | Yes | Good | Production apps |
| NeighborhoodScout | No | Yes | Yes | Enterprise | High-volume commercial |
| SpotCrime | No | Yes | Unknown | Poor | Avoid |

---

## TECH-04: WalkScore API Integration

### WalkScore API Overview

**Official Documentation:** https://www.walkscore.com/professional/api.php

| Feature | Details | Confidence |
|---------|---------|------------|
| Base URL | `https://api.walkscore.com` | High |
| Authentication | API Key (wsapikey) | High |
| Coverage | US, Canada, Australia, New Zealand | High |
| Response Format | JSON, XML | High |

### Available Scores

| Score Type | Range | Description |
|------------|-------|-------------|
| Walk Score | 0-100 | Walkability to errands |
| Transit Score | 0-100 | Public transit accessibility |
| Bike Score | 0-100 | Bike infrastructure quality |

### API Endpoints

#### 1. Score API (Main)
```
GET https://api.walkscore.com/score
    ?format=json
    &address=1234+Main+St+Phoenix+AZ+85001
    &lat=33.4484
    &lon=-112.0740
    &transit=1
    &bike=1
    &wsapikey=YOUR_API_KEY
```

**Response Fields:**
- `walkscore` (integer 0-100)
- `description` (e.g., "Walker's Paradise", "Car-Dependent")
- `transit.score` (integer 0-100)
- `bike.score` (integer 0-100)

#### 2. Public Transit API
```
Base URL: https://transit.walkscore.com
Coverage: 350+ transit agencies
```

Six available API calls for transit stop/route data. [High Confidence]

#### 3. Travel Time API
```
Endpoint: https://api.walkscore.com/traveltime/
Modes: drive, walk, bike, transit
Limit: 60 minutes maximum trip duration
```

#### 4. Travel Time Polygon API
```
Endpoint: https://api2.walkscore.com/api/v1/traveltime_polygon/json
Method: GET, POST
Purpose: Generate commute shed polygons
```

### Rate Limits & Quotas

| Tier | Widget Views/Day | API Calls/Day | Additional APIs |
|------|------------------|---------------|-----------------|
| Free | 1,000 | 5,000 | No |
| Professional | Higher | Higher | Yes (Score Details, Transit, Travel Time) |
| Enterprise | Custom | Custom | Yes + multi-domain |

**Quota Enforcement:** Exceeding quota returns 4xx status code. [High Confidence]

### Pricing

| Tier | Cost | Notes |
|------|------|-------|
| Free | $0 | 5,000 calls/day, basic scores only |
| Professional | Contact sales | Score Details, Transit API, Travel Time API |
| Enterprise | Contact sales | Multi-domain, high-volume |

**Contact:** professional@walkscore.com or (253) 256-1634

**Sources:**
- [WalkScore API Documentation](https://www.walkscore.com/professional/api.php)
- [WalkScore APIs Overview](https://www.walkscore.com/professional/walk-score-apis.php)
- [WalkScore Pricing](https://www.walkscore.com/professional/pricing.php)

### Terms of Service Key Points

**Prohibited:**
- Bulk downloads
- Caching/storing scores without written consent
- Modifying WalkScore content
- Reverse engineering

**Required:**
- Follow branding requirements
- Attribution/linking to WalkScore

**Termination:** WalkScore reserves right to terminate access at any time for any reason. [High Confidence]

**Sources:**
- [WalkScore Terms of Use](https://www.walkscore.com/professional/terms-of-use.php)

### Python Integration Example

```python
import requests

def get_walkscore(address: str, lat: float, lon: float, api_key: str) -> dict:
    """
    Get Walk Score, Transit Score, and Bike Score for an address.
    """
    base_url = "https://api.walkscore.com/score"
    params = {
        "format": "json",
        "address": address,
        "lat": lat,
        "lon": lon,
        "transit": 1,
        "bike": 1,
        "wsapikey": api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    data = response.json()
    return {
        "walk_score": data.get("walkscore"),
        "walk_description": data.get("description"),
        "transit_score": data.get("transit", {}).get("score"),
        "bike_score": data.get("bike", {}).get("score")
    }

# Example usage for Phoenix property
result = get_walkscore(
    address="123 Main St Phoenix AZ 85001",
    lat=33.4484,
    lon=-112.0740,
    api_key="YOUR_API_KEY"
)
```

---

## TECH-08: Energy Usage Estimation APIs

### Overview

Residential energy estimation APIs fall into three categories:
1. **Statistical Data APIs** - Historical consumption patterns
2. **Simulation Tools** - Physics-based energy modeling
3. **Utility Data APIs** - Actual meter data access

---

### 1. EIA (Energy Information Administration) API

**Overview:** Free government API providing comprehensive energy statistics.

| Feature | Details | Confidence |
|---------|---------|------------|
| Base URL | `https://api.eia.gov/v2/` | High |
| Authentication | API Key (free) | High |
| Cost | Free | High |
| Coverage | National, state, utility-level | High |
| Data Types | Consumption, prices, sales, customers | High |

**Registration:** https://www.eia.gov/opendata/

**Residential Data Endpoint:**
```
GET https://api.eia.gov/v2/electricity/retail-sales/data
    ?api_key=YOUR_KEY
    &data[]=sales
    &data[]=price
    &facets[sectorid][]=RES
    &facets[stateid][]=AZ
    &frequency=monthly
```

**RECS (Residential Energy Consumption Survey):**
- 2024 data collection ongoing
- 18,500+ household sample (largest ever)
- Sub-annual estimates planned for 2024 RECS

**Arizona-Specific Energy Patterns:**
- Average US residential: 10,715 kWh/year (~893 kWh/month)
- Southern region (includes AZ): 13,376 kWh/year (highest due to A/C)
- Energy intensity decreases with newer construction

**Sources:**
- [EIA API Documentation](https://www.eia.gov/opendata/documentation.php)
- [EIA Developer Portal](https://www.eia.gov/developer/)
- [EIA RECS](https://www.eia.gov/consumption/residential/)

---

### 2. DOE Home Energy Score API

**Overview:** Official DOE API for home energy scoring (requires Qualified Assessor credentials).

| Feature | Details | Confidence |
|---------|---------|------------|
| Protocol | SOAP | High |
| Access | Restricted to DOE-approved Qualified Assessors | High |
| Environments | Production, Sandbox, Sandbeta | High |
| Cost | Free (with credentials) | Medium |

**API Documentation:** https://hes-documentation.labworks.org/home/api-definitions

**Authentication Flow:**
1. Call `get_session_token` with assessor username/password
2. Use returned `session_key` for subsequent API calls

**Limitation:** Requires DOE Qualified Assessor certification for production access. [High Confidence]

**Sources:**
- [HEScore API Documentation](https://hes-documentation.labworks.org/home/api-definitions)

---

### 3. NREL Tools (BEopt, ResStock, OCHRE)

#### BEopt (Building Energy Optimization)

**Overview:** Free residential energy modeling tool using EnergyPlus engine.

| Feature | Details | Confidence |
|---------|---------|------------|
| Cost | Free (open-source) | High |
| Engine | EnergyPlus | High |
| Accuracy | Within 1% aggregate, up to 30% individual variance | High |
| Batch Mode | Yes | High |
| Current Version | 3.0.1 Beta | High |

**Capabilities:**
- New construction and retrofit analysis
- Single-family and multi-family buildings
- Cost-optimal efficiency package identification
- Batch simulation via command-line

**Sources:**
- [BEopt NREL](https://www.nrel.gov/buildings/beopt)
- [BEopt DOE](https://www.energy.gov/eere/buildings/building-energy-optimization-beopt-software)

#### ResStock (Residential Building Stock Model)

**Overview:** Large-scale residential building stock energy model with pre-computed datasets.

| Feature | Details | Confidence |
|---------|---------|------------|
| Cost | Free | High |
| Latest Dataset | ResStock 2024.2 | High |
| Sample Size | 2.2 million dwelling unit models | High |
| Coverage | All 50 US states (including AK, HI as of 2024.2) | High |
| Granularity | 15-minute intervals | High |

**2024.2 Dataset Features:**
- Electric vehicles modeling
- Updated utility rates
- HVAC demand flexibility
- Electric panel estimations
- Improved geothermal heat pump modeling

**Data Access Methods:**
1. Direct CSV downloads from https://resstock.nrel.gov/datasets
2. AWS S3/Athena queries
3. OpenEI Data Lake

**Research Finding:** ResStock has identified $49 billion in potential annual utility bill savings through cost-effective efficiency improvements. [High Confidence]

**Sources:**
- [ResStock Datasets](https://resstock.nrel.gov/datasets)
- [ResStock GitHub](https://github.com/NREL/resstock)
- [NREL Buildings Data Tools](https://www.nrel.gov/buildings/data-tools)

#### OCHRE (Object-oriented Controllable High-resolution Residential Energy)

**Overview:** Python-based residential energy model for advanced controls and optimization.

| Feature | Details | Confidence |
|---------|---------|------------|
| Language | Python | High |
| Equipment Models | HVAC, water heaters, EVs, solar PV, batteries | High |
| Integration | BEopt, ResStock, foresee, HELICS | High |
| Use Case | Demand-side management modeling | High |

---

### 4. Green Button / UtilityAPI

#### Green Button Standard

**Overview:** Industry standard for utility customer energy data access.

| Feature | Details | Confidence |
|---------|---------|------------|
| Protocol | REST API (Atom+XML) | High |
| Standard | NAESB REQ.21 ESPI | High |
| Data Types | Electricity, gas, water | High |
| Operations | Download My Data, Connect My Data | High |

**Key Concepts:**
- **Download My Data:** Customer downloads own data file
- **Connect My Data:** Machine-to-machine authorized data transfer

**Participating Utilities (partial list):** PG&E, SDG&E, Southern California Edison, Austin Energy, National Grid, Pepco, etc.

**Note:** Neither SRP nor APS appear in the standard Green Button participating utilities list. [Medium Confidence]

**Sources:**
- [Green Button DOE](https://www.energy.gov/data/green-button)
- [Green Button Developers](https://green-button.github.io/developers/)
- [Green Button Alliance](https://www.greenbuttondata.org/)

#### UtilityAPI

**Overview:** Third-party platform providing unified utility data access including Green Button Connect hosting.

| Feature | Details | Confidence |
|---------|---------|------------|
| APS Support | Yes (via UtilityAPI) | High |
| Coverage | Multiple utilities nationwide | High |
| Pricing | Contact for quote | Low |
| Features | Bill data, interval data, Green Button hosting | High |

**APS Integration:**
- Utility identifier: "APS"
- Tariff data available
- Access via `GET /files/known_tariffs_json`

**Sources:**
- [UtilityAPI - APS](https://utilityapi.com/docs/utilities/aps)
- [UtilityAPI Green Button Docs](https://utilityapi.com/docs/greenbutton)

---

### 5. Arcadia Platform

**Overview:** Enterprise utility data platform with 95% US coverage.

| Feature | Details | Confidence |
|---------|---------|------------|
| Coverage | 50+ countries, 95% US utility accounts | High |
| Products | Plug (usage data), Signal (tariff calculator) | High |
| Interval Data | 15, 30, 60 minute | High |
| Tariff Database | 30,000+ North American tariffs | High |
| Pricing | Enterprise; contact for quote | Low |

**Products:**
1. **Plug:** Utility bill and interval data aggregation
2. **Signal:** Tariff lookup and cost calculation engine

**Developer Docs:** https://docs.arcadia.com/

**Sources:**
- [Arcadia Platform](https://www.arcadia.com/platform)
- [Arcadia Plug](https://www.arcadia.com/products/plug)

---

### Arizona Utility Considerations

#### SRP (Salt River Project)

| Feature | Details | Confidence |
|---------|---------|------------|
| Public API | Not found | Medium |
| Customer Tools | Online usage tracker, mobile app | High |
| Green Button | Not in participating list | Medium |
| Recommendation | Check UtilityAPI or Arcadia for access | Medium |

#### APS (Arizona Public Service)

| Feature | Details | Confidence |
|---------|---------|------------|
| UtilityAPI Access | Yes | High |
| Tariff Data | Available via UtilityAPI | High |
| Demand Response | Smart thermostat, battery, water heater programs | High |

---

### Energy Estimation Formula (Rule of Thumb)

For quick estimates without API access:

```python
def estimate_monthly_kwh(square_footage: int, region: str = "south") -> float:
    """
    Rough estimate of monthly kWh based on square footage.

    National average: ~0.5 kWh/sqft/month
    Southern region (AZ): ~0.67 kWh/sqft/month (higher A/C usage)
    """
    multipliers = {
        "national": 0.5,
        "south": 0.67,  # AZ, TX, FL, etc.
        "northeast": 0.45,
        "midwest": 0.48
    }

    return square_footage * multipliers.get(region, 0.5)

# Example: 2000 sqft home in Phoenix
monthly_kwh = estimate_monthly_kwh(2000, "south")  # ~1,340 kWh/month
```

**Adjustment Factors:**
- Homes built before 1950: +64% energy intensity
- Homes built 2016+: baseline
- Pool: +$100-150/month (5,000+ kWh/year in AZ)

[Medium Confidence - based on EIA RECS data]

---

### Energy API Comparison Matrix

| Provider | Cost | Actual Data | Estimated | PHX Coverage | Best For |
|----------|------|-------------|-----------|--------------|----------|
| EIA API | Free | No | Statistical | State-level | Baselines |
| HEScore | Free* | No | Yes | National | Official ratings |
| BEopt | Free | No | Yes (simulation) | Any location | Deep analysis |
| ResStock | Free | No | Yes (modeled) | National | Stock analysis |
| UtilityAPI | Paid | Yes (with auth) | No | APS yes | Actual bills |
| Arcadia | Paid | Yes (with auth) | Yes | ~95% US | Enterprise |
| Green Button | Varies | Yes (with auth) | No | Limited AZ | Direct utility |

*Requires DOE Qualified Assessor credentials

---

## Integration Recommendations for PHX Houses Pipeline

### Phase 1: Immediate Integration (Low Cost)

1. **Crime Data:**
   - Primary: Phoenix Open Data Portal (free, daily updates)
   - Supplemental: FBI Crime Data Explorer (free, quarterly)
   - Implementation: Add to Phase 1 map-analyzer agent

2. **WalkScore:**
   - Use free tier (5,000 calls/day)
   - Store scores in enrichment_data.json
   - Add to Section A (Location) scoring

3. **Energy Estimation:**
   - Use EIA statistical data + square footage formula
   - Integrate ResStock Arizona data for climate-adjusted estimates

### Phase 2: Enhanced Integration (Budget Required)

1. **Crime Data:**
   - Evaluate CrimeOMeter Pro ($30/month) for address-level granularity
   - Consider NeighborhoodScout ($5K/year) for comprehensive risk scores

2. **WalkScore:**
   - Upgrade to Professional for Transit/Travel Time APIs
   - Enables commute time calculations

3. **Energy Estimation:**
   - Evaluate UtilityAPI for APS actual bill access
   - Consider Arcadia for multi-utility coverage

### Implementation Priority

| Priority | API | Estimated Effort | Value |
|----------|-----|------------------|-------|
| High | Phoenix Open Data | 2-4 hours | High |
| High | WalkScore Free | 2-4 hours | High |
| Medium | FBI CDE | 4-8 hours | Medium |
| Medium | EIA + ResStock | 8-16 hours | Medium |
| Low | CrimeOMeter | 4-8 hours | Medium |
| Low | UtilityAPI | 8-16 hours | Low |

### Proposed Schema Additions

```python
# enrichment_data.json additions
{
    "crime_data": {
        "source": "phoenix_open_data",
        "incidents_1yr_radius_0.5mi": 42,
        "violent_crime_rate": 4.2,
        "property_crime_rate": 18.7,
        "last_updated": "2024-12-03"
    },
    "walkability": {
        "walk_score": 65,
        "transit_score": 38,
        "bike_score": 52,
        "walk_description": "Somewhat Walkable",
        "source": "walkscore_api"
    },
    "energy_estimate": {
        "estimated_monthly_kwh": 1340,
        "estimated_monthly_cost": 174.20,
        "methodology": "eia_regional_sqft",
        "confidence": "medium"
    }
}
```

---

## Sources

### Crime Data APIs
- [Phoenix Open Data - Crime Data](https://phoenixopendata.com/dataset/crime-data)
- [Phoenix Police Crime Stats](https://www.phoenix.gov/administration/departments/police/crime-stats-data.html)
- [FBI Crime Data Explorer](https://cde.ucr.cjis.gov/)
- [FBI CDE GitHub](https://github.com/fbi-cde/crime-data-api)
- [DOJ Developer Resources](https://www.justice.gov/developer)
- [CrimeOMeter API](https://www.crimeometer.com/crime-data-api)
- [RapidAPI - CrimeOMeter Pricing](https://rapidapi.com/crimeometer/api/crimeometer/pricing)
- [Location Inc. Crime Data](https://locationinc.com/license-neighborhoodscout-crime-data/)
- [NeighborhoodScout Data Sources](https://api.locationinc.com/about-the-data)
- [SpotCrime Blog - API](https://blog.spotcrime.com/2019/03/the-spotcrime-api.html)

### WalkScore API
- [WalkScore API Documentation](https://www.walkscore.com/professional/api.php)
- [WalkScore APIs Overview](https://www.walkscore.com/professional/walk-score-apis.php)
- [WalkScore Pricing](https://www.walkscore.com/professional/pricing.php)
- [WalkScore Terms of Use](https://www.walkscore.com/professional/terms-of-use.php)
- [WalkScore Sample Code](https://www.walkscore.com/professional/api-sample-code.php)

### Energy Usage Estimation
- [EIA API Documentation](https://www.eia.gov/opendata/documentation.php)
- [EIA Developer Portal](https://www.eia.gov/developer/)
- [EIA RECS](https://www.eia.gov/consumption/residential/)
- [DOE Building Energy Modeling](https://www.energy.gov/eere/buildings/building-energy-modeling)
- [DOE BPD API](https://www.energy.gov/eere/buildings/application-programming-interface)
- [BEopt NREL](https://www.nrel.gov/buildings/beopt)
- [ResStock Datasets](https://resstock.nrel.gov/datasets)
- [ResStock GitHub](https://github.com/NREL/resstock)
- [HEScore API Documentation](https://hes-documentation.labworks.org/home/api-definitions)
- [Green Button DOE](https://www.energy.gov/data/green-button)
- [Green Button Developers](https://green-button.github.io/developers/)
- [UtilityAPI - APS](https://utilityapi.com/docs/utilities/aps)
- [UtilityAPI Green Button Docs](https://utilityapi.com/docs/greenbutton)
- [Arcadia Platform](https://www.arcadia.com/platform)

---

*Report generated December 2024 for PHX Houses Analysis Pipeline*

# TECH-08: Energy Usage Estimation APIs

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

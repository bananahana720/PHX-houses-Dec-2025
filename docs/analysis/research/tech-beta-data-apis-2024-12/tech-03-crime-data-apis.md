# TECH-03: Crime Data APIs

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

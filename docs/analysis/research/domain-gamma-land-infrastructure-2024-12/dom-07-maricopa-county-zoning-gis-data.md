# DOM-07: Maricopa County Zoning GIS Data

### 1. Public Data Availability

**[High Confidence]** Maricopa County zoning data is publicly and freely available through multiple official portals:

#### Primary Data Sources

| Portal | URL | Description |
|--------|-----|-------------|
| Assessor's Parcel Viewer | [maps.mcassessor.maricopa.gov](https://maps.mcassessor.maricopa.gov/) | Parcel-level property data, search by APN or address |
| GIS Open Data Portal | [data-maricopa.opendata.arcgis.com](https://data-maricopa.opendata.arcgis.com/) | Downloadable shapefiles, daily updates |
| Interactive Parcel Maps | [maricopa.gov/4035](https://www.maricopa.gov/4035/Interactive-Parcel-Maps) | Planning & Development zoning layers |
| GIS Mapping Applications | [maricopa.gov/3942](https://www.maricopa.gov/3942/GIS-Mapping-Applications) | Various mapping tools including PlanNet |

#### Available Data Layers

- Parcel boundaries and ownership
- Zoning classifications
- Floodplain designations (updated February 2024 for Lower Gila River)
- Aerial imagery dating back to 1930
- Building permits, zoning cases, code violations
- Tax lien status

**Source:** [Maricopa County GIS Homepage](https://www.maricopa.gov/507/GIS-Maps)

### 2. Zoning Classification System

**[High Confidence]** Maricopa County and Phoenix City have separate zoning ordinances with different classification systems.

#### Maricopa County Rural Districts

| District | Minimum Lot Size | Max Lot Coverage | Purpose |
|----------|------------------|------------------|---------|
| Rural-190 | 190,000 sq ft (~4.4 acres) | 5% | Conserve farms, open land, prevent urban-ag conflicts |
| Rural-70 | 70,000 sq ft (~1.6 acres) | 5% | Foster orderly growth in rural areas |
| Rural-43 | 43,560 sq ft (1 acre) | 25% (increased from 15% via TA2012033) | Larger residential lots |

**Source:** [Maricopa County Zoning Ordinance PDF](https://www.maricopa.gov/DocumentCenter/View/4785/Maricopa-County-Zoning-Ordinance-PDF)

#### City of Phoenix Residential Districts

| District | Description | Notes |
|----------|-------------|-------|
| RE-43 | Residential Estate (1 acre min) | Only applies to land zoned RE-43 prior to Sept 13, 1981 |
| RE-35 | One-family residence | |
| R1-18 to R1-6 | Single-family residential | Number indicates min lot size (000s sq ft) |
| R-2 to R-5 | Multiple-family residential | Higher density allowed |

**Source:** [Phoenix Zoning Ordinance Chapter 6](https://phoenix.municipal.codes/ZO/6)

### 3. How to Access Parcel-Level Zoning Information

**[High Confidence]** Multiple search methods available:

#### Assessor's Parcel Viewer Search Options

1. **By Parcel Number (APN):** Format flexible - 13275013 or 132-75-013
2. **By Owner Name:** e.g., "Smith John"
3. **By Subdivision Name:** e.g., "Oak Park"
4. **By Address:** Standard format - [number] [street direction] [street name] [type]

**Tips:**
- Street direction must be abbreviated: E, N, W, S, NE, NW, SE, SW
- Street type should be abbreviated: ST, AVE, PL, LN
- City, state, zip code can be omitted from queries

**Source:** [Parcel Viewer Help](https://maps.mcassessor.maricopa.gov/help/t_search.html)

#### Data Download Options

- GIS Open Data Portal provides free downloads in common formats
- No request form required for most datasets
- Parcel shapefiles for entire county available
- Custom data requests: $30 standard (3-7 business days) or $60 expedited

**Source:** [Maricopa County Data Requests](https://www.maricopa.gov/509/Data-Requests)

### 4. Impact of Zoning on Residential Property Value

**[Medium Confidence]** Limited direct Phoenix-specific academic research found; findings based on policy analyses and planning documents.

#### Key Findings

1. **Housing Cost Impact:** Home prices in Phoenix area rose 216% since 2000 while wages rose only 48%. Restrictive zoning that limits multi-family housing contributes to this affordability gap.

2. **Rental Market:** From August 2017 to August 2023, Arizona rental prices surged 53%. 53% of Phoenix-area renters are now cost-burdened (spending 30%+ of income on rent).

3. **Recent Reform (HB2721):** Arizona's "missing middle" housing bill (May 2024) mandates cities over 75,000 allow duplexes/triplexes/fourplexes within 1 mile of central business district by January 2026.

4. **Rezoning Activity:** July 2024 - July 2025, Phoenix rezoned 670+ acres (~70 parcels) projected to deliver ~6,400 new housing units with $1.05B in CRE projects.

**Sources:**
- [Pew Research: Restrictive Zoning in Arizona](https://www.pew.org/en/research-and-analysis/articles/2023/12/07/restrictive-zoning-is-raising-housing-costs-and-homelessness-in-arizona)
- [Common Sense Institute: Zoning Reform and Arizona's Housing Market](https://www.commonsenseinstituteus.org/arizona/research/housing-and-our-community/zoning-reform-and-arizonas-housing-market)

### PHX Houses System Integration

**Recommendation:** Use Assessor's Parcel Viewer API/data for automated lot size verification against zoning minimums. Cross-reference with kill-switch lot size criteria (7k-15k sqft preference).

---

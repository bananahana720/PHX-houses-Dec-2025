# Data Source Architecture

## Overview

This document defines the authoritative data source hierarchy for the PHX Houses Analysis Pipeline. PhoenixMLS is the canonical primary source for property listing data following the Epic 2 pivot (2025-12-05).

## Data Source Hierarchy

| Priority | Source | Data Types | Confidence | Notes |
|----------|--------|------------|------------|-------|
| **1 (Primary)** | PhoenixMLS | Listing data (70+ fields), Images | 95%+ | Canonical MLS feed, no anti-bot |
| **2 (Authoritative)** | Maricopa County Assessor | Lot size, Year built, Garage spaces | 100% | Legal record of property |
| **3 (Fallback)** | Zillow ZPID | Images only | 85% | Fallback when PhoenixMLS images unavailable |
| **4 (Fallback)** | Redfin | Images only | 80% | Secondary fallback for images |
| **5 (Enhancement)** | Google Maps | Orientation, Proximity | 90% | Scoring enhancement |
| **6 (Enhancement)** | GreatSchools | School ratings | 95% | Scoring enhancement |

## PhoenixMLS (Canonical Primary)

### Strategic Decision

PhoenixMLS was adopted as the canonical primary data source during Epic 2 remediation (E2.R1, 2025-12-05) after Zillow's PerimeterX anti-bot system created a critical blocker (BLOCK-001).

**Rationale:**
- **Authoritative**: Direct MLS feed, not scraped data
- **Complete**: 70+ fields extracted vs original 10
- **Reliable**: No CAPTCHA, no aggressive anti-bot
- **Kill-Switch Coverage**: 100% (all 8 fields available)

### Extracted Fields (70+)

#### Kill-Switch Fields (8/8 = 100%)
| Field | MLS Key | Kill-Switch |
|-------|---------|-------------|
| HOA Fee | `hoa_fee` | HARD: must be $0 |
| Solar Lease | `solar_lease_status` | HARD: must not be leased |
| Bedrooms | `beds` | HARD: ≥4 |
| Bathrooms | `baths` | HARD: ≥2 |
| Square Feet | `sqft` | HARD: >1800 |
| Sewer Type | `sewer_type` | SOFT: city preferred |
| Year Built | `year_built` | SOFT: ≤2023 |
| Garage Spaces | `garage_spaces` | SOFT: ≥2 indoor |
| Lot Size | `lot_sqft` | SOFT: 7k-15k |

#### MLS Metadata Fields
- MLS Number, Status, List Date, List Price
- DOM (Days on Market), Price Changes
- Agent Info, Brokerage, Office

#### Property Details (35+ fields)
- Construction, Roof, Pool, HVAC
- Features, Amenities, Appliances
- Parking, Garage Type, Carport

#### Geographic Fields
- Subdivision, School District, Tax Parcel
- Coordinates (lat/lng), Zip Code

### Integration Point
```
src/phx_home_analysis/services/image_extraction/phoenixmls/
├── extractor.py      # PhoenixMLSExtractor class
├── field_mapping.py  # MLS_FIELD_MAPPING (70+ fields)
└── parser.py         # HTML parsing utilities
```

## Maricopa County Assessor (Authoritative)

Legal record for property characteristics. Used for Phase 0 data collection.

**Fields:**
- Lot Size (authoritative, overrides MLS)
- Year Built (authoritative)
- Garage Spaces (verified)
- Property Valuation

**API:** Requires `MARICOPA_ASSESSOR_TOKEN`

## Zillow/Redfin (Image Fallback)

Used ONLY for image extraction when PhoenixMLS images unavailable.

**Limitations:**
- Zillow: PerimeterX anti-bot (CAPTCHA risk)
- Redfin: CDN 404 errors common

**Usage Pattern:**
```
if phoenixmls_images.empty():
    try_zillow_zpid_extraction()
    if still_empty():
        try_redfin_fallback()
```

## Phase-to-Source Mapping

| Phase | Primary Source | Data Retrieved |
|-------|----------------|----------------|
| 0 | Maricopa County Assessor | Lot, Year, Garage (authoritative) |
| 1a | PhoenixMLS | Listing data (70+ fields) |
| 1b | PhoenixMLS → Zillow → Redfin | Property images |
| 1c | Google Maps | Orientation, Proximity |
| 1d | GreatSchools | School ratings |
| 2 | Image files (local) | Visual assessment |
| 3 | Aggregated data | Score synthesis |

## Data Confidence Scoring

Each field has a confidence score based on source:

| Source | Base Confidence |
|--------|-----------------|
| Maricopa County Assessor | 1.00 (authoritative) |
| PhoenixMLS | 0.95 (canonical MLS) |
| CSV Input | 0.90 (user provided) |
| Zillow/Redfin | 0.75 (scraped) |
| AI Assessment | 0.70 (model inference) |

See `EnrichmentData._field_provenance` for implementation.

## Historical Context

### Pre-Pivot (before 2025-12-05)
- Primary: Zillow → Redfin fallback
- Problem: CAPTCHA (BLOCK-001), limited fields (10)

### Post-Pivot (E2.R1+)
- Primary: PhoenixMLS (canonical)
- Result: 70+ fields, 100% kill-switch coverage
- Zillow/Redfin: Images only (fallback)

---

*Last Updated: 2025-12-07*
*Related: Epic 2 Supplemental Retro, ADR-06, E2.R1-R3*

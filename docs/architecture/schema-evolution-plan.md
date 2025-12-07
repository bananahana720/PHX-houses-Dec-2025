# Schema Evolution Plan: New External Data Sources Integration

**Version:** 1.0.0
**Date:** 2025-12-07
**Status:** Draft
**Author:** Claude Code (Sonnet 4.5)

---

## Executive Summary

This document outlines the schema evolution strategy for integrating five new external data sources into the PHX Houses analysis pipeline. The plan addresses schema versioning, field additions, migration procedures, and backward compatibility while maintaining data integrity across the 160+ existing fields.

**Current State:**
- Schema Version: v2.0.0
- Fields: 160+ in `EnrichmentDataSchema`
- Pydantic Models: 30+
- Migration Infrastructure: Existing (`src/phx_home_analysis/services/schema/versioning.py`)

**New Data Sources:**
1. OpenStreetMap (Geofabrik Arizona extract, 270MB)
2. Google Places API
3. Google Air Quality API
4. SchoolDigger API
5. Census Bureau ACS

**Deliverables:**
- Schema v2.1.0 (additive fields only)
- Schema v3.0.0 (breaking changes if needed)
- Migration scripts and rollback procedures
- Field definitions with validation rules
- Provenance tracking enhancements

---

## Table of Contents

1. [Schema Version Roadmap](#1-schema-version-roadmap)
2. [New Field Groups](#2-new-field-groups)
3. [Migration Strategy](#3-migration-strategy)
4. [Field Definitions](#4-field-definitions)
5. [Provenance Tracking](#5-provenance-tracking)
6. [Validation Rules](#6-validation-rules)
7. [Testing Strategy](#7-testing-strategy)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Performance Considerations](#9-performance-considerations)
10. [Security & Privacy](#10-security--privacy)

---

## 1. Schema Version Roadmap

### 1.1 Version Timeline

```
v2.0.0 (Current)
    |
    ├─> v2.1.0 (Additive: OSM, Places, AQI) - Target: Week 1
    |       ↓
    |       New optional fields for POI proximity, air quality
    |       No breaking changes
    |       Backward compatible
    |
    └─> v2.2.0 (Additive: SchoolDigger, Census) - Target: Week 2
            ↓
            Enhanced school data, demographics
            No breaking changes
            Backward compatible
            |
            └─> v3.0.0 (Breaking: Nested Structure) - Target: Week 4
                    ↓
                    Reorganize flat fields into nested groups
                    Deprecate old field names
                    Migration required
```

### 1.2 Version Compatibility Matrix

| Version | Backward Compatible | Forward Compatible | Migration Required | Notes |
|---------|--------------------|--------------------|-------------------|-------|
| v2.0.0 → v2.1.0 | ✅ Yes | ⚠️ Partial | ❌ No | New fields are optional |
| v2.1.0 → v2.2.0 | ✅ Yes | ⚠️ Partial | ❌ No | Additional optional fields |
| v2.2.0 → v3.0.0 | ❌ No | ❌ No | ✅ Yes | Nested structure, field renames |

### 1.3 Deprecation Policy

**For v3.0.0 Breaking Changes:**
- Deprecation warnings introduced in v2.2.0
- Grace period: 2 releases (v2.2.0, v2.3.0)
- Removal: v3.0.0
- Automated migration script provided

---

## 2. New Field Groups

### 2.1 Overview

| Field Group | Prefix | Source | Fields Count | Version | Priority |
|-------------|--------|--------|--------------|---------|----------|
| OpenStreetMap | `osm_*` | Geofabrik AZ | 15 | v2.1.0 | High |
| Google Places | `places_*` | Google Places API | 12 | v2.1.0 | High |
| Air Quality | `air_quality_*` | Google AQI API | 8 | v2.1.0 | Medium |
| Schools Enhanced | `school_*` | SchoolDigger API | 10 | v2.2.0 | High |
| Census Demographics | `census_*` | Census ACS API | 18 | v2.2.0 | Medium |

**Total New Fields:** 63 (all optional)

### 2.2 Field Naming Conventions

**Pattern:** `{source_prefix}_{category}_{metric}_{unit?}`

**Examples:**
- `osm_poi_grocery_distance_mi` - Distance to nearest grocery (OpenStreetMap)
- `places_restaurant_count_1mi` - Restaurant count within 1 mile (Google Places)
- `air_quality_aqi_live` - Live Air Quality Index (Google AQI)
- `school_elementary_percentile_state` - Elementary school state percentile (SchoolDigger)
- `census_tract_median_income` - Tract median household income (Census)

**Unit Suffixes:**
- `_mi` - miles (STANDARDIZED - replaces legacy `_miles` suffix from v2.0.0)
- `_ft` - feet
- `_min` - minutes (drive time)
- `_count` - count/number
- `_pct` - percentage (0-100)
- `_score` - score (0-100 or 0-10)
- No suffix for enums, booleans, categorical data

**IMPORTANT:** All new distance fields in v2.1.0+ use `_mi` suffix for consistency.
Legacy v2.0.0 fields with `_miles` suffix will be deprecated in v3.0.0 (see Appendix A).

---

## 3. Migration Strategy

### 3.1 Backward Compatibility Approach

**v2.0.0 → v2.1.0 / v2.2.0 (Additive Migrations):**

1. **All new fields are optional** (Pydantic `Field(None, ...)`)
2. Existing v2.0.0 data remains valid
3. No field deletions or renames
4. No type changes to existing fields
5. Schema version metadata updated automatically

**Example:**

```python
# v2.0.0 data (valid in v2.1.0)
{
    "full_address": "123 Main St",
    "beds": 4,
    "baths": 2.5,
    "_schema_metadata": {"version": "2.0.0"}
}

# v2.1.0 data (with new fields)
{
    "full_address": "123 Main St",
    "beds": 4,
    "baths": 2.5,
    "osm_poi_grocery_distance_mi": 0.8,  # NEW
    "places_restaurant_count_1mi": 15,   # NEW
    "_schema_metadata": {"version": "2.1.0"}
}
```

### 3.2 Migration Script Template

**Location:** `scripts/migrate_schema_v2_1.py`

```python
#!/usr/bin/env python3
"""Migrate enrichment_data.json from v2.0.0 to v2.1.0.

This migration is additive - no existing fields are modified.
New optional fields for OSM, Places, and Air Quality data.

Usage:
    python scripts/migrate_schema_v2_1.py --file data/enrichment_data.json --dry-run
    python scripts/migrate_schema_v2_1.py --file data/enrichment_data.json --backup
"""

import argparse
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from phx_home_analysis.services.schema import (
    SchemaMetadata,
    SchemaMigrator,
    SchemaVersion,
)

logger = logging.getLogger(__name__)


def migrate_v2_0_to_v2_1(data: list[dict]) -> list[dict]:
    """Migrate data from v2.0.0 to v2.1.0.

    Additive migration - no existing data is modified.
    New fields are added only when external APIs are called.

    Args:
        data: List of property records (v2.0.0 format)

    Returns:
        List of property records (v2.1.0 format, identical to input)
    """
    # v2.1.0 is purely additive - no transformation needed
    # New fields will be populated by external API integrations
    logger.info(f"Migrating {len(data)} properties to v2.1.0 (additive migration)")

    # Update schema metadata only
    now = datetime.now(timezone.utc).isoformat()
    if data and isinstance(data[0], dict):
        data[0]["_schema_metadata"] = {
            "version": "2.1.0",
            "migrated_at": now,
            "migrated_from": "2.0.0",
            "created_at": data[0].get("_schema_metadata", {}).get("created_at", now),
        }

    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate enrichment_data.json from v2.0.0 to v2.1.0"
    )
    parser.add_argument("--file", type=Path, required=True, help="Path to enrichment_data.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--backup", action="store_true", help="Create timestamped backup")

    args = parser.parse_args()

    # Load current data
    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)

    # Detect current version
    migrator = SchemaMigrator()
    current_version = migrator.get_version(data)

    if current_version.value != "2.0.0":
        logger.error(f"Expected v2.0.0, got {current_version.value}")
        return 1

    # Migrate
    migrated_data = migrate_v2_0_to_v2_1(data)

    if args.dry_run:
        print(f"[DRY RUN] Would update {args.file} to v2.1.0")
        print(f"[DRY RUN] No data changes (additive migration)")
        return 0

    # Backup if requested
    if args.backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = args.file.with_suffix(f".{timestamp}.v2_0_0.bak.json")
        shutil.copy2(args.file, backup_path)
        logger.info(f"Created backup: {backup_path}")

    # Write migrated data
    with open(args.file, "w", encoding="utf-8") as f:
        json.dump(migrated_data, f, indent=2)

    logger.info(f"Successfully migrated to v2.1.0")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
```

### 3.3 Rollback Procedures

**Automatic Rollback (Backup-Based):**

```bash
# List available backups
ls -lh data/*.bak.json

# Restore from backup
cp data/enrichment_data.20251207_143022.v2_0_0.bak.json data/enrichment_data.json

# Verify version
python scripts/migrate_schema.py --file data/enrichment_data.json --check
```

**Manual Rollback (Field Removal):**

```python
# scripts/rollback_v2_1_to_v2_0.py
def rollback_v2_1_to_v2_0(data: list[dict]) -> list[dict]:
    """Remove v2.1.0 fields to restore v2.0.0 schema."""
    v2_1_fields = {
        # OSM fields
        "osm_poi_grocery_distance_mi",
        "osm_poi_pharmacy_distance_mi",
        # ... (all v2.1 fields)
    }

    for record in data:
        for field in v2_1_fields:
            record.pop(field, None)

        # Update metadata
        record["_schema_metadata"] = {
            "version": "2.0.0",
            "migrated_at": datetime.now(timezone.utc).isoformat(),
            "migrated_from": "2.1.0",
        }

    return data
```

---

## 4. Field Definitions

### 4.1 OpenStreetMap Fields (v2.1.0)

**Source:** Geofabrik Arizona extract (270MB, updated daily)
**Confidence:** 0.90 (high quality, community-verified)
**Freshness:** Weekly refresh recommended

```python
# Add to EnrichmentDataSchema

# POI Proximity (calculated via road network, not straight-line)
osm_poi_grocery_distance_mi: float | None = Field(
    None, ge=0, le=50, description="Road distance to nearest grocery store (miles)"
)
osm_poi_pharmacy_distance_mi: float | None = Field(
    None, ge=0, le=50, description="Road distance to nearest pharmacy (miles)"
)
osm_poi_hospital_distance_mi: float | None = Field(
    None, ge=0, le=100, description="Road distance to nearest hospital (miles)"
)
osm_poi_park_distance_mi: float | None = Field(
    None, ge=0, le=25, description="Road distance to nearest park (miles)"
)
osm_poi_school_distance_mi: float | None = Field(
    None, ge=0, le=25, description="Road distance to nearest school (miles)"
)
osm_poi_transit_distance_mi: float | None = Field(
    None, ge=0, le=10, description="Road distance to nearest transit stop (miles)"
)

# Road Network Analysis
osm_road_primary_distance_mi: float | None = Field(
    None, ge=0, le=10, description="Distance to nearest primary road (miles)"
)
osm_road_highway_distance_mi: float | None = Field(
    None, ge=0, le=25, description="Distance to nearest highway on-ramp (miles)"
)
osm_road_highway_name: str | None = Field(
    None, max_length=100, description="Name of nearest highway (e.g., I-10, Loop 101)"
)

# Land Use Classification (from OSM landuse tags)
osm_landuse_residential_pct: float | None = Field(
    None, ge=0, le=100, description="Percent residential land use within 0.5mi (percent)"
)
osm_landuse_commercial_pct: float | None = Field(
    None, ge=0, le=100, description="Percent commercial land use within 0.5mi (percent)"
)
osm_landuse_industrial_pct: float | None = Field(
    None, ge=0, le=100, description="Percent industrial land use within 0.5mi (percent)"
)
osm_landuse_park_pct: float | None = Field(
    None, ge=0, le=100, description="Percent park/recreation land use within 0.5mi (percent)"
)

# Network Metrics
osm_network_intersection_count_1mi: int | None = Field(
    None, ge=0, le=1000, description="Number of road intersections within 1 mile"
)
osm_network_connectivity_score: float | None = Field(
    None, ge=0, le=100, description="Street network connectivity score (0-100, higher=better)"
)

# Metadata
osm_data_fetched_at: str | None = Field(
    None, description="ISO timestamp when OSM data was fetched"
)
```

**Validation Logic:**

```python
from pydantic import Field, field_validator, model_validator, ValidationInfo

@field_validator("osm_landuse_residential_pct", "osm_landuse_commercial_pct",
                 "osm_landuse_industrial_pct", "osm_landuse_park_pct")
@classmethod
def validate_landuse_sum(cls, v: float | None, info: ValidationInfo) -> float | None:
    """Validate that land use percentages sum to ≤100%."""
    if v is None:
        return None

    # Sum all landuse fields present
    landuse_fields = [
        "osm_landuse_residential_pct",
        "osm_landuse_commercial_pct",
        "osm_landuse_industrial_pct",
        "osm_landuse_park_pct",
    ]
    total = sum(getattr(info.data, f, 0) or 0 for f in landuse_fields)

    if total > 100.1:  # Allow small floating point error
        raise ValueError(f"Land use percentages sum to {total}%, exceeds 100%")

    return v
```

### 4.2 Google Places API Fields (v2.1.0)

**Source:** Google Places API
**Cost:** $0.017 per Nearby Search + $0.00 per Place Details (Basic Data)
**Rate Limit:** 100 requests/second
**Confidence:** 0.85 (high quality, Google-verified)
**Freshness:** Monthly refresh recommended

```python
# Add to EnrichmentDataSchema

# Nearby Amenity Counts (within 1 mile radius)
places_restaurant_count_1mi: int | None = Field(
    None, ge=0, le=500, description="Number of restaurants within 1 mile"
)
places_grocery_count_1mi: int | None = Field(
    None, ge=0, le=50, description="Number of grocery stores within 1 mile"
)
places_cafe_count_1mi: int | None = Field(
    None, ge=0, le=200, description="Number of cafes within 1 mile"
)
places_pharmacy_count_1mi: int | None = Field(
    None, ge=0, le=50, description="Number of pharmacies within 1 mile"
)
places_gym_count_1mi: int | None = Field(
    None, ge=0, le=50, description="Number of gyms/fitness centers within 1 mile"
)

# Nearest Amenity Details
places_grocery_nearest_name: str | None = Field(
    None, max_length=200, description="Name of nearest grocery store"
)
places_grocery_nearest_rating: float | None = Field(
    None, ge=1.0, le=5.0, description="Google rating of nearest grocery (1-5 stars)"
)
places_grocery_nearest_distance_mi: float | None = Field(
    None, ge=0, le=25, description="Distance to nearest grocery (straight-line miles)"
)
places_grocery_nearest_review_count: int | None = Field(
    None, ge=0, description="Number of reviews for nearest grocery"
)

# Aggregate Quality Metrics
places_avg_restaurant_rating_1mi: float | None = Field(
    None, ge=1.0, le=5.0, description="Average rating of restaurants within 1 mile"
)
places_total_amenities_1mi: int | None = Field(
    None, ge=0, le=1000, description="Total amenities (all types) within 1 mile"
)

# Metadata
places_data_fetched_at: str | None = Field(
    None, description="ISO timestamp when Places data was fetched"
)
```

### 4.3 Google Air Quality API Fields (v2.1.0)

**Source:** Google Air Quality API
**Cost:** $0.01 per request (Current Conditions)
**Rate Limit:** 1000 requests/day (free tier)
**Confidence:** 0.95 (EPA-grade sensors)
**Freshness:** Daily refresh recommended

```python
# Add to EnrichmentDataSchema

# Live Air Quality (renamed from planned air_quality_aqi_current to avoid collision with v2.0.0 field)
air_quality_aqi_live: int | None = Field(
    None, ge=0, le=500, description="Live Air Quality Index from Google AQI API (0-500)"
)
air_quality_category_current: str | None = Field(
    None, description="AQI category: Good/Moderate/Unhealthy/VeryUnhealthy/Hazardous"
)
air_quality_primary_pollutant: str | None = Field(
    None, description="Primary pollutant: PM2.5/PM10/O3/NO2/SO2/CO"
)

# Pollutant Breakdown (μg/m³)
air_quality_pm25_ugm3: float | None = Field(
    None, ge=0, le=500, description="PM2.5 concentration (μg/m³)"
)
air_quality_pm10_ugm3: float | None = Field(
    None, ge=0, le=600, description="PM10 concentration (μg/m³)"
)
air_quality_o3_ppb: float | None = Field(
    None, ge=0, le=200, description="Ozone concentration (ppb)"
)
air_quality_no2_ppb: float | None = Field(
    None, ge=0, le=100, description="NO2 concentration (ppb)"
)

# Metadata
air_quality_data_fetched_at: str | None = Field(
    None, description="ISO timestamp when AQI data was fetched"
)
```

**Validation:**

```python
@field_validator("air_quality_category_current")
@classmethod
def validate_aqi_category(cls, v: str | None) -> str | None:
    """Validate AQI category matches EPA standard categories."""
    if v is None:
        return None

    valid_categories = {
        "Good",
        "Moderate",
        "UnhealthyForSensitiveGroups",
        "Unhealthy",
        "VeryUnhealthy",
        "Hazardous",
    }

    if v not in valid_categories:
        raise ValueError(f"Invalid AQI category: {v}. Must be one of {valid_categories}")

    return v
```

### 4.4 SchoolDigger API Fields (v2.2.0)

**Source:** SchoolDigger API
**Cost:** Free tier (5,000 requests/month) or Premium ($99/mo for 100k)
**Rate Limit:** 50 requests/second (premium)
**Confidence:** 0.90 (state test score data)
**Freshness:** Annual refresh (scores updated yearly)

```python
# Add to EnrichmentDataSchema

# School Boundaries (replaces simple name-based matching)
school_elementary_id: str | None = Field(
    None, max_length=50, description="SchoolDigger ID for assigned elementary school"
)
school_middle_id: str | None = Field(
    None, max_length=50, description="SchoolDigger ID for assigned middle school"
)
school_high_id: str | None = Field(
    None, max_length=50, description="SchoolDigger ID for assigned high school"
)

# Distance Calculations (from property to school)
school_elementary_distance_mi: float | None = Field(
    None, ge=0, le=25, description="Distance to assigned elementary school (miles)"
)
school_middle_distance_mi: float | None = Field(
    None, ge=0, le=50, description="Distance to assigned middle school (miles)"
)
school_high_distance_mi: float | None = Field(
    None, ge=0, le=50, description="Distance to assigned high school (miles)"
)

# Rankings (State and National Percentile)
school_elementary_percentile_state: float | None = Field(
    None, ge=0, le=100, description="Elementary school state percentile (0-100, higher=better)"
)
school_middle_percentile_state: float | None = Field(
    None, ge=0, le=100, description="Middle school state percentile (0-100)"
)
school_high_percentile_state: float | None = Field(
    None, ge=0, le=100, description="High school state percentile (0-100)"
)
# NOTE: school_composite_percentile_state is a COMPUTED PROPERTY, not an input field
# It is calculated via @model_validator based on the three percentile fields above
# See "Composite Calculation" section below for implementation

# Metadata
school_data_fetched_at: str | None = Field(
    None, description="ISO timestamp when SchoolDigger data was fetched"
)
```

**Composite Calculation (Computed Property):**

The `school_composite_percentile_state` field is NOT an input field. It is automatically calculated
via a Pydantic `@model_validator` when all three school percentile fields are present:

```python
from pydantic import Field, model_validator

@model_validator(mode="after")
def calculate_composite_school_percentile(self) -> "EnrichmentDataSchema":
    """Calculate weighted composite school percentile.

    Weight: Elementary 40%, Middle 30%, High 30%
    Only calculate if all three percentiles are present.

    This is a COMPUTED field, not an input field - do not set it directly.
    """
    elem = self.school_elementary_percentile_state
    middle = self.school_middle_percentile_state
    high = self.school_high_percentile_state

    if elem is not None and middle is not None and high is not None:
        self.school_composite_percentile_state = (
            elem * 0.4 + middle * 0.3 + high * 0.3
        )

    return self
```

### 4.5 Census Bureau ACS Fields (v2.2.0)

**Source:** Census Bureau American Community Survey (5-Year Estimates)
**Cost:** Free
**Rate Limit:** None officially, respect 1 req/sec guideline
**Confidence:** 0.95 (official government data)
**Freshness:** Annual refresh (ACS data updated yearly)

```python
# Add to EnrichmentDataSchema

# Census Tract Identification (already exists)
# census_tract: str | None  # Already in v2.0.0

# Demographics (Tract-Level)
census_tract_population: int | None = Field(
    None, ge=0, le=100000, description="Total population in census tract"
)
census_tract_population_density_sqmi: float | None = Field(
    None, ge=0, le=50000, description="Population density (people per square mile)"
)
census_tract_median_age: float | None = Field(
    None, ge=0, le=100, description="Median age in census tract (years)"
)
census_tract_pct_owner_occupied: float | None = Field(
    None, ge=0, le=100, description="Percent of housing units that are owner-occupied"
)
census_tract_pct_renter_occupied: float | None = Field(
    None, ge=0, le=100, description="Percent of housing units that are renter-occupied"
)

# Income Statistics (Tract-Level)
# census_tract_median_income: int | None  # Already in v2.0.0
census_tract_mean_income: int | None = Field(
    None, ge=0, description="Mean household income in tract (dollars)"
)
census_tract_pct_below_poverty: float | None = Field(
    None, ge=0, le=100, description="Percent of population below poverty line"
)
census_tract_gini_index: float | None = Field(
    None, ge=0, le=1.0, description="Gini coefficient (0=equality, 1=inequality)"
)

# Housing Statistics (Tract-Level)
# census_tract_median_home_value: int | None  # Already in v2.0.0
census_tract_mean_home_value: int | None = Field(
    None, ge=0, description="Mean home value in tract (dollars)"
)
census_tract_median_year_built: int | None = Field(
    None, ge=1800, le=2030, description="Median year housing units were built"
)
census_tract_pct_single_family: float | None = Field(
    None, ge=0, le=100, description="Percent of housing units that are single-family detached"
)

# Education (Tract-Level)
census_tract_pct_bachelors_plus: float | None = Field(
    None, ge=0, le=100, description="Percent of adults 25+ with bachelor's degree or higher"
)
census_tract_pct_high_school_plus: float | None = Field(
    None, ge=0, le=100, description="Percent of adults 25+ with high school diploma or higher"
)

# Employment (Tract-Level)
census_tract_unemployment_rate: float | None = Field(
    None, ge=0, le=100, description="Unemployment rate (percent)"
)
census_tract_median_commute_min: float | None = Field(
    None, ge=0, le=180, description="Median commute time (minutes)"
)

# Commute Mode (Tract-Level)
census_tract_pct_drive_alone: float | None = Field(
    None, ge=0, le=100, description="Percent who commute by driving alone"
)
census_tract_pct_public_transit: float | None = Field(
    None, ge=0, le=100, description="Percent who commute by public transit"
)

# Metadata
census_data_year: int | None = Field(
    None, ge=2010, le=2030, description="ACS survey year (e.g., 2022 for 2018-2022 5-year)"
)
census_data_fetched_at: str | None = Field(
    None, description="ISO timestamp when Census data was fetched"
)
```

---

## 5. Provenance Tracking

### 5.1 Source Confidence Levels

**Confidence Scoring (0.0-1.0):**

| Source | Base Confidence | Factors | Decay Rate |
|--------|----------------|---------|------------|
| OpenStreetMap | 0.90 | Community verification, daily updates | -0.01/week |
| Google Places | 0.85 | Google verified, business churn | -0.02/month |
| Google Air Quality | 0.95 | EPA sensors, real-time | -0.10/day |
| SchoolDigger | 0.90 | State test scores, annual | -0.05/year |
| Census ACS | 0.95 | Official government, large sample | -0.02/year |

**Confidence Adjustments:**
- API error/timeout: -0.20
- Partial data returned: -0.10
- Cached data (stale): See decay rate

### 5.2 Freshness Requirements

**Recommended Refresh Intervals:**

```python
# config/freshness_policy.py
from datetime import timedelta

FRESHNESS_POLICY = {
    "osm": {
        "interval": timedelta(weeks=1),  # Weekly refresh
        "critical": False,  # Can use stale data if API down
        "max_stale": timedelta(weeks=4),
    },
    "places": {
        "interval": timedelta(days=30),  # Monthly refresh
        "critical": False,
        "max_stale": timedelta(days=90),
    },
    "air_quality": {
        "interval": timedelta(days=1),  # Daily refresh
        "critical": False,  # AQI changes rapidly
        "max_stale": timedelta(days=7),
    },
    "schooldigger": {
        "interval": timedelta(days=365),  # Annual refresh
        "critical": False,  # Scores update yearly
        "max_stale": timedelta(days=730),
    },
    "census": {
        "interval": timedelta(days=365),  # Annual refresh
        "critical": False,  # ACS data updated yearly
        "max_stale": timedelta(days=1825),  # 5 years (ACS survey period)
    },
}
```

### 5.3 Enhanced Provenance Tracking

**Use Existing FieldProvenance Pattern:**

The codebase already has a robust `FieldProvenance` class (see `src/phx_home_analysis/domain/entities.py:14-40`)
for tracking field-level data lineage. Use this existing pattern for all new fields:

```python
from dataclasses import dataclass, field

@dataclass
class FieldProvenance:
    """Provenance metadata for a single field.

    Tracks the source, confidence, and timestamp of data for quality assessment
    and lineage tracking.

    Attributes:
        data_source: Data source identifier (e.g., "osm_overpass", "google_places").
        confidence: Confidence score (0.0-1.0).
        fetched_at: ISO 8601 timestamp when data was retrieved.
        agent_id: Optional agent identifier that populated the field.
        phase: Optional phase identifier (e.g., "phase0", "phase1", "phase2").
        derived_from: List of source field names for derived values.
    """
    data_source: str
    confidence: float
    fetched_at: str  # ISO 8601 timestamp
    agent_id: str | None = None
    phase: str | None = None
    derived_from: list[str] = field(default_factory=list)
```

**Usage Pattern for New Fields:**

```python
# When setting OSM fields
enrichment_data.set_field_provenance(
    field_name="osm_poi_grocery_distance_mi",
    source="osm_overpass",
    confidence=0.90,
    fetched_at="2025-12-07T14:30:00Z",
    phase="phase1"
)

# When setting Google Places fields
enrichment_data.set_field_provenance(
    field_name="places_restaurant_count_1mi",
    source="google_places_api",
    confidence=0.85,
    fetched_at="2025-12-07T14:35:00Z",
    phase="phase1"
)

# When setting computed fields
enrichment_data.set_field_provenance(
    field_name="school_composite_percentile_state",
    source="computed",
    confidence=0.90,
    fetched_at="2025-12-07T14:40:00Z",
    derived_from=[
        "school_elementary_percentile_state",
        "school_middle_percentile_state",
        "school_high_percentile_state"
    ]
)
```

**Confidence Score Guidelines:**

| Data Source | Confidence | Rationale |
|-------------|-----------|-----------|
| OSM Overpass API | 0.90 | Community-verified, high quality |
| Google Places API | 0.85 | Google-verified businesses |
| Google AQI API | 0.95 | EPA-grade sensors |
| SchoolDigger API | 0.90 | State test score data |
| Census ACS API | 0.95 | Official government data |
| Computed fields | 0.85-0.95 | Based on source field confidences |

**DO NOT use nested `_provenance` dict fields** - this conflicts with the existing `FieldProvenance` pattern.
The `*_data_fetched_at` fields in each section are metadata fields, not provenance tracking.

---

## 6. Validation Rules

### 6.1 Cross-Field Validation

**Geographic Consistency:**

```python
@model_validator(mode="after")
def validate_geographic_consistency(self) -> "EnrichmentDataSchema":
    """Ensure geographic data is internally consistent.

    Checks:
    - OSM road distance >= straight-line distance
    - Place counts match individual amenity counts
    - Census tract matches property location
    """
    # Check OSM road distance >= OSM straight-line distance
    if (
        self.osm_poi_grocery_distance_mi is not None
        and self.places_grocery_nearest_distance_mi is not None
    ):
        if self.osm_poi_grocery_distance_mi < self.places_grocery_nearest_distance_mi * 0.9:
            # Allow 10% tolerance for different data sources
            logger.warning(
                f"OSM road distance ({self.osm_poi_grocery_distance_mi}mi) < "
                f"Places straight-line distance ({self.places_grocery_nearest_distance_mi}mi)"
            )

    # Check total amenities >= sum of individual counts
    if self.places_total_amenities_1mi is not None:
        individual_counts = sum(
            getattr(self, f, 0) or 0
            for f in [
                "places_restaurant_count_1mi",
                "places_grocery_count_1mi",
                "places_cafe_count_1mi",
                "places_pharmacy_count_1mi",
                "places_gym_count_1mi",
            ]
        )
        if individual_counts > self.places_total_amenities_1mi:
            raise ValueError(
                f"Sum of individual amenity counts ({individual_counts}) "
                f"exceeds total ({self.places_total_amenities_1mi})"
            )

    return self
```

### 6.2 Data Quality Checks

**Implement in `scripts/validate_new_fields.py`:**

```python
def validate_enrichment_data_quality(data: list[dict]) -> dict:
    """Validate data quality for new fields.

    Returns:
        Quality report with warnings and errors.
    """
    report = {
        "total_records": len(data),
        "warnings": [],
        "errors": [],
        "field_coverage": {},
    }

    new_fields_v2_1 = [
        "osm_poi_grocery_distance_mi",
        "places_restaurant_count_1mi",
        "air_quality_aqi_live",
    ]

    new_fields_v2_2 = [
        "school_elementary_percentile_state",
        "census_tract_median_income",
    ]

    for field in new_fields_v2_1 + new_fields_v2_2:
        non_null_count = sum(1 for r in data if r.get(field) is not None)
        coverage_pct = (non_null_count / len(data)) * 100
        report["field_coverage"][field] = {
            "count": non_null_count,
            "coverage_pct": coverage_pct,
        }

        # Warn if coverage < 80% (expected for new fields during rollout)
        if coverage_pct < 80 and coverage_pct > 0:
            report["warnings"].append(
                f"{field}: Low coverage ({coverage_pct:.1f}%), expected during rollout"
            )

    return report
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Test New Field Validation:**

```python
# tests/unit/test_schema_v2_1_validation.py
import pytest
from pydantic import ValidationError

from phx_home_analysis.validation.schemas import EnrichmentDataSchema


def test_osm_landuse_percentages_sum_constraint():
    """Test that land use percentages cannot exceed 100%."""
    with pytest.raises(ValidationError, match="exceeds 100%"):
        EnrichmentDataSchema(
            full_address="123 Main St",
            osm_landuse_residential_pct=60.0,
            osm_landuse_commercial_pct=30.0,
            osm_landuse_industrial_pct=15.0,  # Sum = 105%
            osm_landuse_park_pct=5.0,
        )


def test_air_quality_category_validation():
    """Test AQI category must be valid EPA category."""
    with pytest.raises(ValidationError, match="Invalid AQI category"):
        EnrichmentDataSchema(
            full_address="123 Main St",
            air_quality_category_current="ExtremelyBad",  # Invalid
        )


def test_school_composite_percentile_calculation():
    """Test composite school percentile is calculated correctly."""
    schema = EnrichmentDataSchema(
        full_address="123 Main St",
        school_elementary_percentile_state=80.0,
        school_middle_percentile_state=70.0,
        school_high_percentile_state=90.0,
    )

    # Expected: 80*0.4 + 70*0.3 + 90*0.3 = 32 + 21 + 27 = 80
    assert schema.school_composite_percentile_state == pytest.approx(80.0)


def test_census_data_year_range():
    """Test census data year is within valid range."""
    with pytest.raises(ValidationError):
        EnrichmentDataSchema(
            full_address="123 Main St",
            census_data_year=2005,  # Too old
        )
```

### 7.2 Integration Tests

**Test External API Integration:**

```python
# tests/integration/test_osm_integration.py
import pytest
from unittest.mock import patch, Mock

from phx_home_analysis.services.osm import OSMClient


@pytest.mark.integration
def test_osm_poi_query_real_api():
    """Test OSM POI query against real Overpass API (slow test)."""
    client = OSMClient()

    # Query near known location (Phoenix City Hall)
    result = client.query_nearby_pois(
        lat=33.4484,
        lon=-112.0740,
        radius_mi=1.0,
        poi_types=["grocery", "pharmacy"],
    )

    assert "grocery" in result
    assert len(result["grocery"]) > 0
    assert result["grocery"][0]["distance_mi"] < 1.0


@pytest.mark.integration
@patch("httpx.Client.get")
def test_places_api_error_handling(mock_get):
    """Test Places API error handling and retry logic."""
    from phx_home_analysis.services.places import PlacesClient

    # Simulate API error
    mock_get.side_effect = [
        Mock(status_code=500),  # First attempt fails
        Mock(status_code=200, json=lambda: {"results": []}),  # Retry succeeds
    ]

    client = PlacesClient(api_key="test_key")
    result = client.nearby_search(lat=33.4484, lon=-112.0740, radius_m=1609)

    assert result == []
    assert mock_get.call_count == 2  # Verify retry occurred
```

### 7.3 Migration Tests

**Test Schema Migration:**

```python
# tests/integration/test_schema_migration_v2_1.py
import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from phx_home_analysis.services.schema import SchemaMigrator, SchemaVersion


def test_v2_0_to_v2_1_migration_preserves_data():
    """Test that v2.0 -> v2.1 migration preserves all existing data."""
    v2_0_data = [
        {
            "full_address": "123 Main St",
            "beds": 4,
            "baths": 2.5,
            "lot_sqft": 10000,
            "_schema_metadata": {"version": "2.0.0"},
        }
    ]

    migrator = SchemaMigrator()
    v2_1_data = migrator.migrate(v2_0_data, SchemaVersion.V2_1)

    # Verify existing fields unchanged
    assert v2_1_data[0]["full_address"] == "123 Main St"
    assert v2_1_data[0]["beds"] == 4
    assert v2_1_data[0]["baths"] == 2.5

    # Verify metadata updated
    assert v2_1_data[0]["_schema_metadata"]["version"] == "2.1.0"
    assert v2_1_data[0]["_schema_metadata"]["migrated_from"] == "2.0.0"


def test_v2_1_data_validates_against_schema():
    """Test that migrated v2.1 data validates against EnrichmentDataSchema."""
    from phx_home_analysis.validation.schemas import EnrichmentDataSchema

    v2_1_record = {
        "full_address": "123 Main St",
        "beds": 4,
        "baths": 2.5,
        "osm_poi_grocery_distance_mi": 0.8,  # New field
        "places_restaurant_count_1mi": 15,    # New field
    }

    # Should not raise ValidationError
    schema = EnrichmentDataSchema(**v2_1_record)
    assert schema.osm_poi_grocery_distance_mi == 0.8
```

---

## 8. Rollback Procedures

### 8.1 Automated Rollback Script

**Location:** `scripts/rollback_schema.py`

```python
#!/usr/bin/env python3
"""Rollback enrichment_data.json to previous schema version.

Usage:
    # List available backups
    python scripts/rollback_schema.py --list-backups

    # Rollback to specific backup
    python scripts/rollback_schema.py --restore data/enrichment_data.20251207_143022.v2_0_0.bak.json

    # Rollback to previous version (uses latest backup)
    python scripts/rollback_schema.py --auto-rollback
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def list_backups(data_dir: Path) -> list[Path]:
    """List all backup files in chronological order."""
    backups = sorted(data_dir.glob("enrichment_data.*.bak.json"), reverse=True)
    return backups


def restore_backup(backup_path: Path, target_path: Path, create_backup: bool = True) -> None:
    """Restore a backup file to the target location.

    Args:
        backup_path: Path to backup file to restore
        target_path: Path to write restored data (usually data/enrichment_data.json)
        create_backup: Whether to create a backup of current file before restoring
    """
    if create_backup and target_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_rollback_backup = target_path.with_suffix(f".{timestamp}.pre_rollback.bak.json")
        shutil.copy2(target_path, pre_rollback_backup)
        print(f"Created pre-rollback backup: {pre_rollback_backup}")

    shutil.copy2(backup_path, target_path)
    print(f"Restored {backup_path} to {target_path}")

    # Verify restored file
    with open(target_path, encoding="utf-8") as f:
        data = json.load(f)

    version = "unknown"
    if isinstance(data, list) and data and "_schema_metadata" in data[0]:
        version = data[0]["_schema_metadata"].get("version", "unknown")

    print(f"Restored schema version: {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback schema to previous version")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Data directory")
    parser.add_argument("--list-backups", action="store_true", help="List available backups")
    parser.add_argument("--restore", type=Path, help="Restore specific backup file")
    parser.add_argument("--auto-rollback", action="store_true", help="Auto-rollback to latest backup")

    args = parser.parse_args()

    if args.list_backups:
        backups = list_backups(args.data_dir)
        if not backups:
            print("No backups found")
            return 0

        print(f"\nFound {len(backups)} backups:\n")
        for backup in backups:
            # Extract version from filename if present
            parts = backup.stem.split(".")
            version = parts[1] if len(parts) > 1 and parts[1].startswith("v") else "unknown"
            print(f"  {backup.name} (version: {version})")

        return 0

    if args.restore:
        if not args.restore.exists():
            print(f"Error: Backup file not found: {args.restore}")
            return 1

        target = args.data_dir / "enrichment_data.json"
        restore_backup(args.restore, target)
        return 0

    if args.auto_rollback:
        backups = list_backups(args.data_dir)
        if not backups:
            print("Error: No backups available for auto-rollback")
            return 1

        latest_backup = backups[0]
        target = args.data_dir / "enrichment_data.json"

        print(f"Auto-rolling back to latest backup: {latest_backup.name}")
        restore_backup(latest_backup, target)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
```

### 8.2 Manual Rollback Checklist

**If automated rollback fails:**

1. **Identify target version:**
   ```bash
   ls -lh data/*.bak.json
   # Select backup with desired version (e.g., v2_0_0)
   ```

2. **Verify backup integrity:**
   ```bash
   python -m json.tool data/enrichment_data.20251207_143022.v2_0_0.bak.json > /dev/null
   echo $?  # Should be 0 (valid JSON)
   ```

3. **Create pre-rollback backup:**
   ```bash
   cp data/enrichment_data.json data/enrichment_data.$(date +%Y%m%d_%H%M%S).pre_rollback.bak.json
   ```

4. **Restore backup:**
   ```bash
   cp data/enrichment_data.20251207_143022.v2_0_0.bak.json data/enrichment_data.json
   ```

5. **Verify schema version:**
   ```bash
   python scripts/migrate_schema.py --file data/enrichment_data.json --check
   ```

6. **Test application:**
   ```bash
   python scripts/phx_home_analyzer.py --address "123 Main St" --dry-run
   ```

---

## 9. Performance Considerations

### 9.1 API Rate Limits & Cost

**Cost Estimation (per 100 properties):**

| API | Requests/Property | Cost/Request | Total Cost | Notes |
|-----|------------------|--------------|------------|-------|
| OSM Overpass | 1 | $0.00 | $0.00 | Free, self-hosted option available |
| Google Places | 3 | $0.017 (Nearby) | $5.10 | Nearby Search + Place Details |
| Google AQI | 1 | $0.01 | $1.00 | Current Conditions |
| SchoolDigger | 3 | $0.00 (free tier) | $0.00 | Free up to 5k/month |
| Census API | 1 | $0.00 | $0.00 | Free, no rate limit |
| **TOTAL** | **9** | - | **$6.10** | **Per 100 properties** |

**Annual Cost (500 properties, monthly refresh):**
- Monthly API calls: 500 properties × 9 APIs = 4,500 requests
- Monthly cost: ~$30.50
- Annual cost: ~$366

**Optimization Strategies:**
1. **Caching:** Cache OSM, SchoolDigger, Census data (low churn)
2. **Batch Requests:** Use Places API batch requests where possible
3. **Conditional Refresh:** Only refresh AQI daily, others weekly/monthly
4. **Free Tier Management:** Stay within SchoolDigger free tier (5k/mo)

### 9.2 Data Storage Growth

**Current v2.0.0:**
- ~160 fields × 500 properties ≈ 80,000 field values
- Estimated size: ~5 MB (enrichment_data.json)

**After v2.1.0:**
- +35 fields (OSM, Places, AQI)
- New size: ~6.1 MB (+22%)

**After v2.2.0:**
- +28 fields (SchoolDigger, Census)
- New size: ~7.2 MB (+44% from v2.0.0)

**After v3.0.0 (nested structure):**
- Same field count, reorganized
- Size: ~7.5 MB (+50% from v2.0.0, minor overhead from nesting)

**Mitigation:**
- Compress backups: `gzip data/*.bak.json` (80-90% reduction)
- Archive old runs: Move to `archive/run_{date}/`
- Consider database: If exceeds 50 MB, migrate to SQLite/PostgreSQL

### 9.3 Query Performance

**Impact on Load Times:**

| Operation | v2.0.0 | v2.1.0 | v2.2.0 | Notes |
|-----------|--------|--------|--------|-------|
| Load JSON | 45 ms | 55 ms | 65 ms | +44% due to file size |
| Validate (Pydantic) | 120 ms | 140 ms | 160 ms | +33% due to more validators |
| Filter (kill-switch) | 10 ms | 10 ms | 10 ms | No impact (same fields) |
| Score (605pt) | 25 ms | 25 ms | 30 ms | Minor impact (new scoring) |

**Optimization:**
- Use `orjson` for faster JSON parsing (3-5x faster than stdlib)
- Lazy validation: Only validate fields when accessed
- Index by address: Use dict lookup instead of list scan

---

## 10. Security & Privacy

### 10.1 PII Considerations

**New Data Sources - PII Risk Assessment:**

| Source | PII Risk | Data Type | Mitigation |
|--------|----------|-----------|------------|
| OSM | Low | Public POIs, roads | No individual data |
| Google Places | Low | Business names, ratings | No individual data |
| Google AQI | None | Environmental data | No individual data |
| SchoolDigger | Low | School names, scores | No student data |
| Census ACS | None | Aggregated tract data | No individual data |

**No new PII fields introduced.** All data is aggregated or public.

### 10.2 API Key Management

**Environment Variables:**

```bash
# .env (never commit to git)
GOOGLE_PLACES_API_KEY=AIzaSyC...
GOOGLE_AIR_QUALITY_API_KEY=AIzaSyD...
SCHOOLDIGGER_API_KEY=sd_live_...

# OSM Overpass: No key required (public API)
# Census API: No key required (public API)
```

**Key Rotation Policy:**
- Rotate Google API keys: Quarterly
- Monitor usage: Weekly via Google Cloud Console
- Set spending limits: $100/month cap

### 10.3 Data Retention

**Backup Retention Policy:**

```python
# config/backup_policy.py
from datetime import timedelta

BACKUP_RETENTION = {
    "daily_backups": timedelta(days=7),    # Keep 7 days
    "weekly_backups": timedelta(days=30),  # Keep 4 weeks
    "monthly_backups": timedelta(days=365), # Keep 12 months
    "version_backups": None,  # Keep forever (v2.0.0, v2.1.0, etc.)
}
```

**Automated Cleanup:**

```bash
# cron job: Clean old backups (runs weekly)
0 3 * * 0 python scripts/cleanup_old_backups.py --policy config/backup_policy.py
```

---

## Appendix A: Complete Field List by Version

### v2.0.0 Fields (160 total)

See `src/phx_home_analysis/validation/schemas.py:218-559` for complete list.

**Highlights:**
- Core property: `beds`, `baths`, `sqft`, `lot_sqft`, `year_built`, etc.
- Kill-switch: `hoa_fee`, `garage_spaces`, `sewer_type`
- Location: `school_rating`, `safety_neighborhood_score`, `orientation`
- Systems: `roof_age`, `hvac_age`, `pool_equipment_age`
- Interior: `kitchen_layout_score`, `master_suite_score`, `natural_light_score`
- Crime: `violent_crime_index`, `property_crime_index`, `crime_risk_level`
- Flood: `flood_zone`, `flood_insurance_required`
- Walkability: `walk_score`, `transit_score`, `bike_score`
- Zoning: `zoning_code`, `zoning_category`
- Demographics: `census_tract`, `median_household_income`, `median_home_value`

**Legacy Distance Fields (v2.0.0 - to be deprecated in v3.0.0):**

NOTE: Some v2.0.0 distance fields use `_miles` suffix instead of the standardized `_mi` suffix.
These will be deprecated in v3.0.0 in favor of the new OSM/Places fields with consistent `_mi` naming:

| v2.0.0 Field (Legacy) | v2.1.0+ Replacement | Status |
|-----------------------|---------------------|--------|
| `distance_to_grocery_miles` | `osm_poi_grocery_distance_mi` | Deprecated in v3.0.0 |
| `distance_to_highway_miles` | `osm_road_highway_distance_mi` | Deprecated in v3.0.0 |
| `distance_to_park_miles` | `osm_poi_park_distance_mi` | Deprecated in v3.0.0 |

**Migration Path:**
- v2.1.0: Both old (`_miles`) and new (`_mi`) fields coexist
- v2.2.0: Deprecation warnings added for `_miles` fields
- v3.0.0: Legacy `_miles` fields removed, only `_mi` fields remain

### v2.1.0 New Fields (35 total)

**OpenStreetMap (15):**
- `osm_poi_grocery_distance_mi`
- `osm_poi_pharmacy_distance_mi`
- `osm_poi_hospital_distance_mi`
- `osm_poi_park_distance_mi`
- `osm_poi_school_distance_mi`
- `osm_poi_transit_distance_mi`
- `osm_road_primary_distance_mi`
- `osm_road_highway_distance_mi`
- `osm_road_highway_name`
- `osm_landuse_residential_pct`
- `osm_landuse_commercial_pct`
- `osm_landuse_industrial_pct`
- `osm_landuse_park_pct`
- `osm_network_intersection_count_1mi`
- `osm_network_connectivity_score`

**Google Places (12):**
- `places_restaurant_count_1mi`
- `places_grocery_count_1mi`
- `places_cafe_count_1mi`
- `places_pharmacy_count_1mi`
- `places_gym_count_1mi`
- `places_grocery_nearest_name`
- `places_grocery_nearest_rating`
- `places_grocery_nearest_distance_mi`
- `places_grocery_nearest_review_count`
- `places_avg_restaurant_rating_1mi`
- `places_total_amenities_1mi`
- `places_data_fetched_at`

**Google Air Quality (8):**
- `air_quality_aqi_live`
- `air_quality_category_current`
- `air_quality_primary_pollutant`
- `air_quality_pm25_ugm3`
- `air_quality_pm10_ugm3`
- `air_quality_o3_ppb`
- `air_quality_no2_ppb`
- `air_quality_data_fetched_at`

### v2.2.0 New Fields (28 total)

**SchoolDigger (10):**
- `school_elementary_id`
- `school_middle_id`
- `school_high_id`
- `school_elementary_distance_mi`
- `school_middle_distance_mi`
- `school_high_distance_mi`
- `school_elementary_percentile_state`
- `school_middle_percentile_state`
- `school_high_percentile_state`
- `school_data_fetched_at`

**Computed Fields (not input):**
- `school_composite_percentile_state` (calculated from elem/middle/high percentiles)

**Census ACS (18):**
- `census_tract_population`
- `census_tract_population_density_sqmi`
- `census_tract_median_age`
- `census_tract_pct_owner_occupied`
- `census_tract_pct_renter_occupied`
- `census_tract_mean_income`
- `census_tract_pct_below_poverty`
- `census_tract_gini_index`
- `census_tract_mean_home_value`
- `census_tract_median_year_built`
- `census_tract_pct_single_family`
- `census_tract_pct_bachelors_plus`
- `census_tract_pct_high_school_plus`
- `census_tract_unemployment_rate`
- `census_tract_median_commute_min`
- `census_tract_pct_drive_alone`
- `census_tract_pct_public_transit`
- `census_data_year`

**Total v2.2.0 Fields:** 160 (v2.0.0) + 35 (v2.1.0) + 28 (v2.2.0) = **223 fields**

---

## Appendix B: API Integration Checklist

### Per-Source Integration Tasks

**For each data source (OSM, Places, AQI, SchoolDigger, Census):**

- [ ] **Client Implementation**
  - [ ] Create `services/{source}/client.py`
  - [ ] Implement retry logic with exponential backoff
  - [ ] Add rate limiting (respect API limits)
  - [ ] Add timeout handling (10s default)
  - [ ] Log API requests/responses

- [ ] **Service Layer**
  - [ ] Create `services/{source}/service.py`
  - [ ] Implement caching (Redis or file-based)
  - [ ] Add freshness checks (see Section 5.2)
  - [ ] Calculate confidence scores
  - [ ] Handle partial data gracefully

- [ ] **Schema Updates**
  - [ ] Add new fields to `EnrichmentDataSchema`
  - [ ] Add field validators
  - [ ] Add cross-field validators
  - [ ] Update schema version

- [ ] **Testing**
  - [ ] Unit tests for client
  - [ ] Unit tests for service
  - [ ] Integration tests (mock API)
  - [ ] Integration tests (real API, slow)
  - [ ] Schema validation tests

- [ ] **Documentation**
  - [ ] API reference (endpoint, auth, rate limits)
  - [ ] Field descriptions
  - [ ] Example usage
  - [ ] Cost estimation

- [ ] **Configuration**
  - [ ] Add API key to `.env.example`
  - [ ] Add to `config/api_config.yaml`
  - [ ] Add freshness policy
  - [ ] Add cost tracking

- [ ] **Monitoring**
  - [ ] Log API errors
  - [ ] Track API costs
  - [ ] Alert on rate limit exceeded
  - [ ] Alert on API down

---

## Appendix C: Migration Timeline

### Week 1: v2.1.0 (OSM, Places, AQI)

**Days 1-2: OSM Integration**
- Implement `services/osm/client.py`
- Add OSM fields to schema
- Write unit + integration tests

**Days 3-4: Google Places Integration**
- Implement `services/places/client.py`
- Add Places fields to schema
- Write unit + integration tests

**Day 5: Google Air Quality Integration**
- Implement `services/air_quality/client.py`
- Add AQI fields to schema
- Write unit + integration tests

**Days 6-7: v2.1.0 Release**
- Update migration script
- Run full test suite
- Deploy to production
- Monitor API costs

### Week 2: v2.2.0 (SchoolDigger, Census)

**Days 1-3: SchoolDigger Integration**
- Implement `services/schooldigger/client.py`
- Add school fields to schema
- Implement composite percentile calculation
- Write unit + integration tests

**Days 4-5: Census ACS Integration**
- Implement `services/census/client.py`
- Add Census fields to schema
- Write unit + integration tests

**Days 6-7: v2.2.0 Release**
- Update migration script
- Run full test suite
- Deploy to production
- Monitor performance

### Week 3-4: v3.0.0 (Breaking Changes - Future)

**Nested Structure Redesign:**
- Group fields into logical nested objects
- Update Pydantic models
- Write migration script (flatten → nested)
- Comprehensive testing
- Gradual rollout with deprecation warnings

---

## Appendix D: Troubleshooting Guide

### Common Migration Issues

**Issue:** `ValidationError: Land use percentages exceed 100%`

**Cause:** OSM data quality issue or rounding errors
**Solution:**
```python
# Normalize land use percentages to sum to 100%
def normalize_landuse(record: dict) -> dict:
    landuse_fields = [
        "osm_landuse_residential_pct",
        "osm_landuse_commercial_pct",
        "osm_landuse_industrial_pct",
        "osm_landuse_park_pct",
    ]

    total = sum(record.get(f, 0) or 0 for f in landuse_fields)
    if total > 100:
        scale_factor = 100 / total
        for field in landuse_fields:
            if record.get(field):
                record[field] *= scale_factor

    return record
```

---

**Issue:** `Google Places API 429 - Rate Limit Exceeded`

**Cause:** Exceeded 100 req/sec limit
**Solution:**
- Add rate limiter: `from ratelimit import limits, sleep_and_retry`
- Reduce batch size: Process 50 properties at a time
- Add exponential backoff: Wait 60s, then retry

---

**Issue:** `SchoolDigger API returns null for school boundaries`

**Cause:** Property outside school district coverage
**Solution:**
- Fall back to nearest school (distance-based)
- Log warning for manual review
- Set confidence to 0.5 (estimated assignment)

---

**Issue:** Migration script crashes midway through

**Cause:** Insufficient memory or corrupted data
**Solution:**
- Process in batches: 100 properties at a time
- Add checkpointing: Save progress every 100 records
- Resume from checkpoint on crash

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-07 | Claude Code (Sonnet 4.5) | Initial draft |

---

**End of Schema Evolution Plan**

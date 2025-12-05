# PHX Houses - Data Models

**Generated:** 2025-12-05
**Primary Framework:** Pydantic 2.12.5 + dataclasses

---

## Overview

PHX Houses uses a Domain-Driven Design approach with:

- **Entities** - Mutable business objects with identity (`Property`)
- **Value Objects** - Immutable data containers (`Address`, `Score`, `ScoreBreakdown`)
- **Enums** - Domain constants with behavior (`Tier`, `Orientation`, `SolarStatus`)

---

## Core Entity: Property

The `Property` class is the **aggregate root** with 156+ fields:

```python
@dataclass
class Property:
    """Real estate property entity with complete analysis data."""

    # ═══════════════════════════════════════════════════════════
    # ADDRESS FIELDS (5 fields)
    # ═══════════════════════════════════════════════════════════
    street: str                    # "123 Main St"
    city: str                      # "Phoenix"
    state: str                     # "AZ"
    zip_code: str                  # "85001"
    full_address: str              # "123 Main St, Phoenix, AZ 85001"

    # ═══════════════════════════════════════════════════════════
    # LISTING DATA (from CSV) (6 fields)
    # ═══════════════════════════════════════════════════════════
    price: str                     # Formatted: "$475,000"
    price_num: int | None          # Parsed: 475000
    beds: int                      # 4
    baths: float                   # 2.5
    sqft: int                      # 2200
    price_per_sqft_raw: float      # 215.91

    # ═══════════════════════════════════════════════════════════
    # COUNTY ASSESSOR DATA (5 fields)
    # ═══════════════════════════════════════════════════════════
    lot_sqft: int | None           # 8500
    year_built: int | None         # 2005
    garage_spaces: int | None      # 2
    sewer_type: SewerType | None   # SewerType.CITY
    tax_annual: float | None       # 3500.00

    # ═══════════════════════════════════════════════════════════
    # HOA AND LOCATION (7 fields)
    # ═══════════════════════════════════════════════════════════
    hoa_fee: float | None          # 0 = no HOA
    commute_minutes: int | None    # 25
    school_district: str | None    # "Paradise Valley Unified"
    school_rating: float | None    # 8.5 (GreatSchools 1-10)
    orientation: Orientation | None # Orientation.NORTH
    distance_to_grocery_miles: float | None  # 1.2
    distance_to_highway_miles: float | None  # 0.8

    # ═══════════════════════════════════════════════════════════
    # ARIZONA-SPECIFIC (6 fields)
    # ═══════════════════════════════════════════════════════════
    solar_status: SolarStatus | None  # SolarStatus.OWNED
    solar_lease_monthly: int | None   # 0 (owned) or monthly payment
    has_pool: bool | None             # True
    pool_equipment_age: int | None    # 5 years
    roof_age: int | None              # 10 years
    hvac_age: int | None              # 8 years

    # ═══════════════════════════════════════════════════════════
    # GEOCODING (2 fields)
    # ═══════════════════════════════════════════════════════════
    latitude: float | None         # 33.4484
    longitude: float | None        # -112.0740

    # ═══════════════════════════════════════════════════════════
    # ANALYSIS RESULTS (populated by pipeline)
    # ═══════════════════════════════════════════════════════════
    kill_switch_passed: bool = False
    kill_switch_failures: list[str] = field(default_factory=list)
    score_breakdown: ScoreBreakdown | None = None
    tier: Tier | None = None
    risk_assessments: list[RiskAssessment] = field(default_factory=list)
    renovation_estimates: list[RenovationEstimate] = field(default_factory=list)
```

**Location:** `src/phx_home_analysis/domain/entities.py:43-200`

---

## Value Objects

### ScoreBreakdown (605-point System)

```python
@dataclass(frozen=True)
class ScoreBreakdown:
    """Immutable score breakdown across three sections."""

    section_a: int = 0   # Location (max 250)
    section_b: int = 0   # Systems (max 175)
    section_c: int = 0   # Interior (max 180)

    @property
    def total(self) -> int:
        """Total score (max 605)."""
        return self.section_a + self.section_b + self.section_c

    @property
    def percentage(self) -> float:
        """Score as percentage of maximum."""
        return (self.total / 605) * 100

    @property
    def section_a_percentage(self) -> float:
        return (self.section_a / 250) * 100

    @property
    def section_b_percentage(self) -> float:
        return (self.section_b / 175) * 100

    @property
    def section_c_percentage(self) -> float:
        return (self.section_c / 180) * 100
```

**Location:** `src/phx_home_analysis/domain/value_objects.py:138-231`

### Address

```python
@dataclass(frozen=True)
class Address:
    """Normalized address value object."""

    street: str
    city: str
    state: str
    zip_code: str

    @property
    def full(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

    @property
    def normalized(self) -> str:
        """Lowercase, stripped for comparison."""
        return self.full.lower().strip()
```

**Location:** `src/phx_home_analysis/domain/value_objects.py:10-45`

### RiskAssessment

```python
@dataclass(frozen=True)
class RiskAssessment:
    """Risk assessment for a property attribute."""

    category: str          # "structural", "financial", "environmental"
    level: RiskLevel       # HIGH, MEDIUM, LOW
    description: str       # Human-readable description
    mitigation: str | None # Suggested mitigation
```

### ImageMetadata (E2.S4)

```python
@dataclass(frozen=True)
class ImageMetadata:
    """Metadata for a property image with lineage tracking."""

    content_hash: str           # SHA-256 of image content
    property_hash: str          # Hash linking to property
    source: ImageSource         # ZILLOW, REDFIN, ASSESSOR
    category: str | None        # "exterior", "kitchen", "bedroom"
    created_by_run_id: str      # Run that created this image
    downloaded_at: str          # ISO 8601 timestamp
    original_url: str           # Source URL
    file_path: str              # Local file path
```

---

## Enums

### Tier (Classification)

```python
class Tier(Enum):
    """Property classification tier."""

    UNICORN = "unicorn"       # >480 points (80%+)
    CONTENDER = "contender"   # 360-480 points (60-80%)
    PASS = "pass"             # <360 points (<60%)

    @property
    def min_score(self) -> int:
        return {
            Tier.UNICORN: 481,
            Tier.CONTENDER: 360,
            Tier.PASS: 0,
        }[self]
```

### Orientation (Arizona-specific)

```python
class Orientation(Enum):
    """Property orientation for sun exposure analysis."""

    NORTH = "N"
    NORTHEAST = "NE"
    EAST = "E"
    SOUTHEAST = "SE"
    SOUTH = "S"
    SOUTHWEST = "SW"
    WEST = "W"
    NORTHWEST = "NW"

    @property
    def base_score(self) -> int:
        """Base score for orientation (higher = better cooling)."""
        scores = {
            Orientation.NORTH: 30,      # Best - least sun
            Orientation.NORTHEAST: 25,
            Orientation.NORTHWEST: 25,
            Orientation.EAST: 20,
            Orientation.SOUTH: 15,
            Orientation.SOUTHEAST: 10,
            Orientation.SOUTHWEST: 5,
            Orientation.WEST: 0,        # Worst - afternoon sun
        }
        return scores[self]
```

### SolarStatus

```python
class SolarStatus(Enum):
    """Solar panel ownership status."""

    OWNED = "owned"     # Solar panels owned (asset)
    LEASED = "leased"   # Solar panels leased (liability)
    NONE = "none"       # No solar panels

    @property
    def is_problematic(self) -> bool:
        """Leased solar is a liability."""
        return self == SolarStatus.LEASED
```

### SewerType

```python
class SewerType(Enum):
    """Sewer connection type."""

    CITY = "city"         # City sewer (preferred)
    SEPTIC = "septic"     # Septic system (kill-switch fail)
    UNKNOWN = "unknown"   # Unknown (needs verification)
```

---

## Data Files

### phx_homes.csv (Listings)

```csv
full_address,price,beds,baths,sqft,price_per_sqft
"123 Main St, Phoenix, AZ 85001","$475,000",4,2.5,2200,215.91
"456 Oak Ave, Glendale, AZ 85301","$425,000",4,2.0,1850,229.73
```

### enrichment_data.json (Enrichment)

```json
{
  "123 Main St, Phoenix, AZ 85001": {
    "lot_sqft": 8500,
    "year_built": 2005,
    "garage_spaces": 2,
    "sewer_type": "city",
    "hoa_fee": 0,
    "school_rating": 8.5,
    "orientation": "N",
    "has_pool": true,
    "solar_status": "owned"
  }
}
```

### work_items.json (Pipeline State)

```json
{
  "items": [
    {
      "address": "123 Main St, Phoenix, AZ 85001",
      "status": "completed",
      "phase_0_complete": true,
      "phase_1_complete": true,
      "phase_2_complete": true,
      "phase_3_complete": true,
      "retry_count": 0,
      "last_updated": "2025-12-05T10:30:00Z"
    }
  ],
  "summary": {
    "total": 50,
    "completed": 45,
    "pending": 3,
    "failed": 2
  }
}
```

---

## Pydantic Schemas

### PropertySchema (Validation)

```python
class PropertySchema(BaseModel):
    """Pydantic schema for property validation."""

    full_address: str = Field(..., min_length=10)
    price_num: int = Field(..., gt=0)
    beds: int = Field(..., ge=1, le=10)
    baths: float = Field(..., ge=1, le=10)
    sqft: int = Field(..., gt=500, lt=20000)
    lot_sqft: int | None = Field(None, gt=1000)
    year_built: int | None = Field(None, ge=1900, le=2025)

    @field_validator('full_address')
    def validate_address(cls, v: str) -> str:
        if not any(state in v for state in ['AZ', 'Arizona']):
            raise ValueError('Address must be in Arizona')
        return v
```

### EnrichmentSchema

```python
class EnrichmentSchema(BaseModel):
    """Schema for enrichment data validation."""

    lot_sqft: int | None = Field(None, gt=0)
    year_built: int | None = Field(None, ge=1900, le=2025)
    garage_spaces: int | None = Field(None, ge=0, le=10)
    sewer_type: SewerType | None = None
    hoa_fee: float | None = Field(None, ge=0)
    school_rating: float | None = Field(None, ge=1, le=10)
    orientation: Orientation | None = None
    has_pool: bool | None = None
    solar_status: SolarStatus | None = None

    model_config = ConfigDict(use_enum_values=True)
```

---

## Field Provenance (Lineage)

```python
@dataclass
class FieldProvenance:
    """Tracks source and confidence of field values."""

    data_source: str       # "assessor_api", "zillow", "manual"
    confidence: float      # 0.0-1.0
    fetched_at: str        # ISO 8601 timestamp
    agent_id: str | None   # Agent that populated the field
    phase: str | None      # "phase0", "phase1", etc.
    derived_from: list[str] = field(default_factory=list)
```

**Confidence by Source:**

| Source | Confidence |
|--------|------------|
| Assessor API | 0.95 |
| CSV Import | 0.90 |
| Web Scraping | 0.75 |
| AI Inference | 0.70 |

---

## Data Quality

### Quality Metrics

```python
@dataclass
class DataQuality:
    """Quality metrics for a property record."""

    completeness: float    # % of required fields populated
    confidence: float      # Average confidence across fields
    freshness_days: int    # Days since last update
    has_warnings: bool     # Any quality warnings
    warnings: list[str]    # Specific warning messages
```

### Quality Calculation

```
Quality Score = (Completeness × 0.6) + (Confidence × 0.4)

Tiers:
- Excellent: ≥95%
- Good: 80-94%
- Fair: 60-79%
- Poor: <60%
```

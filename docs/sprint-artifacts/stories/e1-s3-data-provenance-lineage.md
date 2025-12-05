# E1.S3: Data Provenance and Lineage Tracking

**Status:** Ready for Development
**Epic:** Epic 1 - Foundation & Data Infrastructure
**Priority:** P0
**Estimated Points:** 8
**Dependencies:** E1.S2 (Property Data Storage Layer)
**Functional Requirements:** FR8, FR39

## User Story

As a system user, I want every data field to track its source, confidence, and timestamp, so that I can assess data reliability, trace issues, and understand which agent/phase populated each section.

## Acceptance Criteria

### AC1: Provenance Metadata in Enrichment Records
**Given** a property field is updated during Phase 0/1/2 pipeline execution
**When** the field is written to `enrichment_data.json`
**Then** the record includes:
- `data_source` - Source identifier (e.g., "assessor_api", "zillow", "ai_inference")
- `confidence` - Float from 0.0 to 1.0
- `fetched_at` - ISO 8601 timestamp

### AC2: Confidence Calibration by Source
**Given** data from different sources (County Assessor, Zillow, Image Assessment)
**When** confidence scores are assigned
**Then** confidence mapping follows specification:
- County Assessor API: 0.95
- Google Maps API: 0.90
- GreatSchools API: 0.90
- Zillow/Redfin scraping: 0.85
- Image Assessment (AI): 0.80
- AI Inference (fallback): 0.70
- Manual entry: 0.85
- CSV input: 0.90
- Default/assumed values: 0.50

### AC3: Derived Data Provenance
**Given** a derived field computed from multiple sources (e.g., cost_efficiency_score)
**When** the derived value is recorded
**Then** provenance includes:
- `primary_source` - Main data source used
- `sources` - Array of contributing sources
- `confidence` - Minimum confidence among all sources (conservative)

### AC4: Agent/Phase Attribution
**Given** enrichment data populated by listing-browser (Phase 1) or image-assessor (Phase 2)
**When** viewing property enrichment data
**Then** users can determine:
- Which agent/phase populated each section
- Timestamp of last update
- Confidence level displayed as High (≥0.90), Medium (0.70-0.89), or Low (<0.70)

### AC5: Lineage Query Capability
**Given** a property hash and field name
**When** querying the `LineageTracker` service
**Then** the system returns:
- Complete provenance history for that field
- All updates with timestamps
- Confidence evolution over time

### AC6: Provenance Persistence
**Given** lineage data tracked during pipeline execution
**When** the pipeline completes or crashes
**Then** provenance data persists to `data/field_lineage.json` with atomic writes
**And** can be restored on pipeline restart

### AC7: Low Confidence Field Reporting
**Given** a property with enrichment data
**When** quality metrics are calculated
**Then** the system identifies and reports:
- All fields with confidence < 0.80
- Missing required fields
- Overall quality tier (Excellent ≥0.95, Good ≥0.80, Fair ≥0.60, Poor <0.60)

### AC8: Provenance in Deal Sheets
**Given** deal sheet generation for a property
**When** the HTML report is created
**Then** data confidence is visually indicated:
- High confidence (≥0.90): Green indicator, no warning
- Medium confidence (0.70-0.89): Yellow indicator, "Verify" badge
- Low confidence (<0.70): Red indicator, "Unverified" badge

## Technical Tasks

### Task 1: Add Provenance Fields to EnrichmentData Entity
**File:** `src/phx_home_analysis/domain/entities.py:388-503`
**Action:** Add field-level provenance metadata structure

**Current Implementation Status:** EnrichmentData exists but lacks inline provenance fields.

**Implementation:**
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FieldProvenance:
    """Provenance metadata for a single field.

    Attributes:
        source: Data source identifier.
        confidence: Confidence score (0.0-1.0).
        fetched_at: ISO 8601 timestamp when data was retrieved.
        derived_from: List of source fields for derived values.
    """
    source: str
    confidence: float
    fetched_at: str  # ISO 8601
    derived_from: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class EnrichmentData:
    """Enrichment data for a property from external research.

    Existing fields remain unchanged. New optional field added:
    """

    full_address: str
    normalized_address: str | None = None

    # Existing fields...
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    # ... all existing fields ...

    # NEW: Field-level provenance metadata
    _provenance: dict[str, FieldProvenance] = field(default_factory=dict)

    def set_field_provenance(
        self,
        field_name: str,
        source: str,
        confidence: float,
        fetched_at: str | None = None,
        derived_from: list[str] | None = None
    ) -> None:
        """Set provenance metadata for a field.

        Args:
            field_name: Name of the field.
            source: Data source identifier (e.g., "assessor_api", "zillow").
            confidence: Confidence score (0.0-1.0).
            fetched_at: ISO 8601 timestamp (defaults to now).
            derived_from: Source fields for derived values.
        """
        if fetched_at is None:
            fetched_at = datetime.now().isoformat()

        self._provenance[field_name] = FieldProvenance(
            source=source,
            confidence=confidence,
            fetched_at=fetched_at,
            derived_from=derived_from or []
        )

    def get_field_provenance(self, field_name: str) -> FieldProvenance | None:
        """Get provenance metadata for a field.

        Returns:
            FieldProvenance if set, None otherwise.
        """
        return self._provenance.get(field_name)

    def get_low_confidence_fields(self, threshold: float = 0.80) -> list[str]:
        """Get fields with confidence below threshold.

        Args:
            threshold: Confidence threshold (default 0.80).

        Returns:
            List of field names with confidence < threshold.
        """
        return [
            field_name
            for field_name, prov in self._provenance.items()
            if prov.confidence < threshold
        ]
```

**Acceptance Criteria:**
- [ ] `FieldProvenance` dataclass added with source, confidence, fetched_at, derived_from
- [ ] `_provenance` dict field added to `EnrichmentData`
- [ ] `set_field_provenance()` method implemented
- [ ] `get_field_provenance()` method implemented
- [ ] `get_low_confidence_fields()` method implemented
- [ ] Validation ensures confidence is 0.0-1.0

### Task 2: Extend DataSource Enum with New Sources
**File:** `src/phx_home_analysis/services/quality/models.py:13-58`
**Action:** Add missing data sources to enum

**Current State:** DataSource enum exists with 13 sources and default_confidence property.

**Enhancement:**
```python
class DataSource(Enum):
    """Source of property data."""

    # Existing sources (unchanged)
    CSV = "csv"
    ASSESSOR_API = "assessor_api"
    WEB_SCRAPE = "web_scrape"
    AI_INFERENCE = "ai_inference"
    MANUAL = "manual"
    DEFAULT = "default"
    BESTPLACES = "bestplaces"
    AREAVIBES = "areavibes"
    WALKSCORE = "walkscore"
    FEMA = "fema"
    GREATSCHOOLS = "greatschools"
    HOWLOUD = "howloud"
    CENSUS = "census"
    MARICOPA_GIS = "maricopa_gis"

    # NEW: Add missing sources
    ZILLOW = "zillow"
    REDFIN = "redfin"
    GOOGLE_MAPS = "google_maps"
    IMAGE_ASSESSMENT = "image_assessment"

    @property
    def default_confidence(self) -> float:
        """Get default confidence score for this data source."""
        confidence_map = {
            # Existing mappings (unchanged)
            DataSource.CSV: 0.90,
            DataSource.ASSESSOR_API: 0.95,
            DataSource.WEB_SCRAPE: 0.75,
            DataSource.AI_INFERENCE: 0.70,
            DataSource.MANUAL: 0.85,
            DataSource.DEFAULT: 0.50,
            DataSource.BESTPLACES: 0.80,
            DataSource.AREAVIBES: 0.80,
            DataSource.WALKSCORE: 0.90,
            DataSource.FEMA: 0.95,
            DataSource.GREATSCHOOLS: 0.90,  # Updated from 0.85 to 0.90 per spec
            DataSource.HOWLOUD: 0.75,
            DataSource.CENSUS: 0.95,
            DataSource.MARICOPA_GIS: 0.95,

            # NEW mappings per AC2
            DataSource.ZILLOW: 0.85,
            DataSource.REDFIN: 0.85,
            DataSource.GOOGLE_MAPS: 0.90,
            DataSource.IMAGE_ASSESSMENT: 0.80,
        }
        return confidence_map.get(self, 0.50)
```

**Acceptance Criteria:**
- [ ] ZILLOW, REDFIN, GOOGLE_MAPS, IMAGE_ASSESSMENT sources added
- [ ] Confidence mapping updated per AC2 specification
- [ ] GREATSCHOOLS confidence updated to 0.90 (was 0.85)

### Task 3: Integrate Provenance Tracking with JSON Repository
**File:** `src/phx_home_analysis/repositories/json_repository.py`
**Lines:** ~320 (enhancements to existing methods)

**Action:** Update repository to persist and load provenance metadata

**Implementation:**
```python
# In JsonEnrichmentRepository class

def _enrichment_to_dict(self, enrichment: EnrichmentData) -> dict:
    """Convert EnrichmentData object to dictionary for JSON serialization.

    Enhancement: Include provenance metadata for all tracked fields.
    """
    from ..utils.address_utils import normalize_address

    # Ensure normalized_address is present
    normalized = enrichment.normalized_address or normalize_address(enrichment.full_address)

    base_dict = {
        'full_address': enrichment.full_address,
        'normalized_address': normalized,
        'lot_sqft': enrichment.lot_sqft,
        'year_built': enrichment.year_built,
        # ... all existing fields ...
    }

    # NEW: Add provenance metadata section
    if enrichment._provenance:
        base_dict['_provenance'] = {
            field_name: {
                'source': prov.source,
                'confidence': prov.confidence,
                'fetched_at': prov.fetched_at,
                'derived_from': prov.derived_from,
            }
            for field_name, prov in enrichment._provenance.items()
        }

    return base_dict


def _dict_to_enrichment(self, data: dict) -> EnrichmentData:
    """Convert dictionary to EnrichmentData object.

    Enhancement: Load provenance metadata if present.
    """
    from ..utils.address_utils import normalize_address

    full_address = data['full_address']
    normalized = data.get('normalized_address') or normalize_address(full_address)

    enrichment = EnrichmentData(
        full_address=full_address,
        normalized_address=normalized,
        lot_sqft=data.get('lot_sqft'),
        year_built=data.get('year_built'),
        # ... all existing fields ...
    )

    # NEW: Load provenance metadata if present
    if '_provenance' in data:
        for field_name, prov_data in data['_provenance'].items():
            enrichment.set_field_provenance(
                field_name=field_name,
                source=prov_data['source'],
                confidence=prov_data['confidence'],
                fetched_at=prov_data['fetched_at'],
                derived_from=prov_data.get('derived_from', [])
            )

    return enrichment
```

**Acceptance Criteria:**
- [ ] `_enrichment_to_dict()` serializes provenance to `_provenance` key
- [ ] `_dict_to_enrichment()` loads provenance from `_provenance` key
- [ ] Backward compatible (missing `_provenance` doesn't break load)
- [ ] Atomic write pattern maintained

### Task 4: Create ProvenanceService for Standardized Tracking
**File:** `src/phx_home_analysis/services/quality/provenance_service.py` (NEW)
**Lines:** ~150

**Implementation:**
```python
"""Provenance tracking service for standardized field updates."""

import logging
from datetime import datetime

from .lineage import LineageTracker
from .models import DataSource
from ...domain.entities import EnrichmentData

logger = logging.getLogger(__name__)


class ProvenanceService:
    """Service for recording provenance metadata consistently.

    Provides high-level API for scripts/agents to record data updates
    with proper confidence scoring and timestamp tracking.

    Attributes:
        lineage_tracker: LineageTracker instance for persistence.

    Example:
        service = ProvenanceService()
        service.record_batch(
            enrichment=property_data,
            property_hash="ef7cd95f",
            source=DataSource.ASSESSOR_API,
            fields={'lot_sqft': 9500, 'year_built': 2005}
        )
    """

    def __init__(self, lineage_tracker: LineageTracker | None = None):
        """Initialize provenance service.

        Args:
            lineage_tracker: LineageTracker instance (creates new if None).
        """
        self.lineage_tracker = lineage_tracker or LineageTracker()

    def record_field(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        field_name: str,
        source: DataSource,
        value: any,
        confidence: float | None = None,
        notes: str | None = None
    ) -> None:
        """Record provenance for a single field update.

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address (first 8 chars).
            field_name: Name of the field being updated.
            source: Data source providing the value.
            value: The actual field value.
            confidence: Override confidence (uses source default if None).
            notes: Optional notes about the update.
        """
        if confidence is None:
            confidence = source.default_confidence

        timestamp = datetime.now().isoformat()

        # Update EnrichmentData provenance
        enrichment.set_field_provenance(
            field_name=field_name,
            source=source.value,
            confidence=confidence,
            fetched_at=timestamp
        )

        # Track in LineageTracker for historical queries
        self.lineage_tracker.record_field(
            property_hash=property_hash,
            field_name=field_name,
            source=source,
            confidence=confidence,
            original_value=value,
            notes=notes
        )

        logger.debug(
            f"Recorded provenance: {property_hash}.{field_name} "
            f"from {source.value} (confidence: {confidence:.2f})"
        )

    def record_batch(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        source: DataSource,
        fields: dict[str, any],
        confidence: float | None = None,
        notes: str | None = None
    ) -> None:
        """Record provenance for multiple fields from the same source.

        Convenience method for batch updates (e.g., County Assessor API response).

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address.
            source: Data source for all fields.
            fields: Dictionary mapping field names to values.
            confidence: Override confidence (uses source default if None).
            notes: Optional notes about the batch.
        """
        if confidence is None:
            confidence = source.default_confidence

        for field_name, value in fields.items():
            self.record_field(
                enrichment=enrichment,
                property_hash=property_hash,
                field_name=field_name,
                source=source,
                value=value,
                confidence=confidence,
                notes=notes
            )

        logger.info(
            f"Recorded batch provenance: {len(fields)} fields "
            f"from {source.value} for {property_hash}"
        )

    def record_derived(
        self,
        enrichment: EnrichmentData,
        property_hash: str,
        field_name: str,
        source: DataSource,
        value: any,
        derived_from: list[str],
        confidence: float | None = None
    ) -> None:
        """Record provenance for a derived field.

        For fields computed from other fields (e.g., cost_efficiency_score),
        tracks the source fields and uses minimum confidence (conservative).

        Args:
            enrichment: EnrichmentData entity to update.
            property_hash: MD5 hash of property address.
            field_name: Name of the derived field.
            source: Primary data source (often AI_INFERENCE).
            value: The computed value.
            derived_from: List of source field names.
            confidence: Override confidence (uses minimum of sources if None).
        """
        if confidence is None:
            # Use minimum confidence among source fields (conservative)
            source_confidences = [
                enrichment.get_field_provenance(src_field).confidence
                for src_field in derived_from
                if enrichment.get_field_provenance(src_field)
            ]
            confidence = min(source_confidences) if source_confidences else source.default_confidence

        timestamp = datetime.now().isoformat()

        # Update EnrichmentData provenance
        enrichment.set_field_provenance(
            field_name=field_name,
            source=source.value,
            confidence=confidence,
            fetched_at=timestamp,
            derived_from=derived_from
        )

        # Track in LineageTracker
        self.lineage_tracker.record_field(
            property_hash=property_hash,
            field_name=field_name,
            source=source,
            confidence=confidence,
            original_value=value,
            notes=f"Derived from: {', '.join(derived_from)}"
        )

        logger.debug(
            f"Recorded derived provenance: {property_hash}.{field_name} "
            f"from {source.value} (confidence: {confidence:.2f}, "
            f"sources: {len(derived_from)})"
        )

    def save(self) -> None:
        """Persist lineage data to disk."""
        self.lineage_tracker.save()
```

**Acceptance Criteria:**
- [ ] `ProvenanceService` class created with record_field, record_batch, record_derived methods
- [ ] Integrates with both `EnrichmentData._provenance` and `LineageTracker`
- [ ] Derived field confidence uses minimum of source confidences (conservative)
- [ ] Batch updates handled efficiently

### Task 5: Add Confidence Display Helpers
**File:** `src/phx_home_analysis/services/quality/confidence_display.py` (NEW)
**Lines:** ~80

**Implementation:**
```python
"""Confidence display utilities for reports and UI."""

from enum import Enum


class ConfidenceLevel(Enum):
    """Human-readable confidence levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @classmethod
    def from_score(cls, confidence: float) -> "ConfidenceLevel":
        """Convert confidence score to level.

        Args:
            confidence: Float from 0.0 to 1.0.

        Returns:
            ConfidenceLevel enum.
        """
        if confidence >= 0.90:
            return cls.HIGH
        elif confidence >= 0.70:
            return cls.MEDIUM
        else:
            return cls.LOW

    @property
    def color(self) -> str:
        """Get color indicator for confidence level.

        Returns:
            Color name for UI display.
        """
        colors = {
            ConfidenceLevel.HIGH: "green",
            ConfidenceLevel.MEDIUM: "yellow",
            ConfidenceLevel.LOW: "red",
        }
        return colors[self]

    @property
    def badge(self) -> str:
        """Get badge text for confidence level.

        Returns:
            Badge text for reports.
        """
        badges = {
            ConfidenceLevel.HIGH: "",  # No badge needed
            ConfidenceLevel.MEDIUM: "Verify",
            ConfidenceLevel.LOW: "Unverified",
        }
        return badges[self]


def format_confidence(confidence: float, include_badge: bool = True) -> str:
    """Format confidence score for display.

    Args:
        confidence: Float from 0.0 to 1.0.
        include_badge: Whether to include badge text.

    Returns:
        Formatted string (e.g., "High (0.95)" or "Medium (0.82) [Verify]").
    """
    level = ConfidenceLevel.from_score(confidence)
    score_str = f"{confidence:.2f}"

    parts = [level.value, f"({score_str})"]
    if include_badge and level.badge:
        parts.append(f"[{level.badge}]")

    return " ".join(parts)


def get_confidence_html(confidence: float) -> str:
    """Generate HTML badge for confidence display.

    Args:
        confidence: Float from 0.0 to 1.0.

    Returns:
        HTML string with colored badge.
    """
    level = ConfidenceLevel.from_score(confidence)
    badge_text = level.badge or "Verified"

    return f'<span class="confidence-badge confidence-{level.color}">{badge_text}</span>'
```

**Acceptance Criteria:**
- [ ] `ConfidenceLevel` enum with HIGH/MEDIUM/LOW
- [ ] `from_score()` converts 0.0-1.0 to level per AC4 thresholds
- [ ] `color` and `badge` properties for UI display
- [ ] `format_confidence()` for text reports
- [ ] `get_confidence_html()` for HTML reports

### Task 6: Update Deal Sheet Template with Confidence Indicators
**File:** `scripts/deal_sheets/templates.py:1-200`
**Action:** Add confidence badges to data sections

**Implementation:**
```python
# Add import at top
from phx_home_analysis.services.quality.confidence_display import get_confidence_html

# In _render_property_details() method, enhance field display:
def _render_property_details(self, property_data: dict) -> str:
    """Render property details section with confidence indicators."""
    enrichment = property_data.get('enrichment', {})
    provenance = enrichment.get('_provenance', {})

    details_html = []

    for field_name, display_name in FIELD_DISPLAY_NAMES.items():
        value = enrichment.get(field_name)
        if value is not None:
            # Get confidence if available
            confidence_html = ""
            if field_name in provenance:
                prov = provenance[field_name]
                confidence_html = get_confidence_html(prov['confidence'])

            details_html.append(
                f"<div class='field-row'>"
                f"<span class='field-label'>{display_name}:</span> "
                f"<span class='field-value'>{value}</span> "
                f"{confidence_html}"
                f"</div>"
            )

    return "\n".join(details_html)
```

**CSS Addition:**
```css
/* In deal sheet base CSS */
.confidence-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.85em;
    font-weight: bold;
    margin-left: 8px;
}

.confidence-green {
    background-color: #28a745;
    color: white;
}

.confidence-yellow {
    background-color: #ffc107;
    color: black;
}

.confidence-red {
    background-color: #dc3545;
    color: white;
}
```

**Acceptance Criteria:**
- [ ] Deal sheet template displays confidence badges
- [ ] High confidence (green) shows no badge
- [ ] Medium confidence (yellow) shows "Verify" badge
- [ ] Low confidence (red) shows "Unverified" badge
- [ ] CSS styling matches specification

### Task 7: Add Provenance to Phase 0/1/2 Data Collection Scripts
**File:** Multiple scripts in `scripts/`
**Action:** Update scripts to record provenance when writing enrichment data

**Phase 0 - County Assessor (`scripts/extract_county_data.py`):**
```python
from phx_home_analysis.services.quality.provenance_service import ProvenanceService
from phx_home_analysis.services.quality.models import DataSource

# In main extraction loop
provenance_service = ProvenanceService()

for property in properties:
    # ... fetch assessor data ...

    # Record provenance for County Assessor fields
    provenance_service.record_batch(
        enrichment=enrichment,
        property_hash=property_hash,
        source=DataSource.ASSESSOR_API,
        fields={
            'lot_sqft': assessor_data['lot_sqft'],
            'year_built': assessor_data['year_built'],
            'garage_spaces': assessor_data['garage_spaces'],
            'sewer_type': assessor_data['sewer_type'],
            'tax_annual': assessor_data['tax_annual'],
        }
    )

# Save lineage at end
provenance_service.save()
```

**Phase 1 - Zillow/Redfin (`scripts/extract_images.py`):**
```python
# Record provenance for scraped fields
provenance_service.record_batch(
    enrichment=enrichment,
    property_hash=property_hash,
    source=DataSource.ZILLOW,  # or DataSource.REDFIN
    fields={
        'hoa_fee': listing_data['hoa_fee'],
        'school_rating': listing_data['school_rating'],
        'orientation': listing_data['orientation'],
    }
)
```

**Phase 2 - Image Assessment (`.claude/agents/image-assessor.md` instructions):**
```python
# In image assessment agent instructions
"""
After scoring images, record provenance:

provenance_service.record_batch(
    enrichment=enrichment,
    property_hash=property_hash,
    source=DataSource.IMAGE_ASSESSMENT,
    fields={
        'kitchen_layout_score': 8,
        'master_suite_score': 7,
        'natural_light_score': 9,
        # ... all Phase 2 scores ...
    }
)
"""
```

**Acceptance Criteria:**
- [ ] Phase 0 script records provenance for County Assessor fields
- [ ] Phase 1 script records provenance for Zillow/Redfin fields
- [ ] Phase 2 agent instructions include provenance recording
- [ ] All scripts call `provenance_service.save()` at end

### Task 8: Add Quality Metrics Calculation
**File:** `src/phx_home_analysis/services/quality/metrics.py` (enhance existing)
**Lines:** ~100 additions

**Implementation:**
```python
"""Enhanced quality metrics with provenance-based scoring."""

from ...domain.entities import EnrichmentData
from .models import QualityScore

# Required fields for quality assessment
REQUIRED_FIELDS = [
    'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
    'hoa_fee', 'school_rating', 'orientation',
    'kitchen_layout_score', 'master_suite_score', 'natural_light_score',
]

HIGH_CONFIDENCE_THRESHOLD = 0.80


def calculate_property_quality(enrichment: EnrichmentData) -> QualityScore:
    """Calculate quality score based on completeness and confidence.

    Quality formula (from epic spec):
    - Completeness: 60% weight (% of required fields present)
    - Confidence: 40% weight (% of fields with high confidence ≥0.80)

    Args:
        enrichment: EnrichmentData entity with provenance.

    Returns:
        QualityScore with completeness, confidence, and overall metrics.
    """
    # Calculate completeness
    present_fields = [
        field for field in REQUIRED_FIELDS
        if getattr(enrichment, field, None) is not None
    ]
    completeness = len(present_fields) / len(REQUIRED_FIELDS)

    missing_fields = [f for f in REQUIRED_FIELDS if f not in present_fields]

    # Calculate confidence metrics
    high_confidence_count = 0
    low_confidence_fields = []

    for field in present_fields:
        prov = enrichment.get_field_provenance(field)
        if prov:
            if prov.confidence >= HIGH_CONFIDENCE_THRESHOLD:
                high_confidence_count += 1
            else:
                low_confidence_fields.append(field)

    high_confidence_pct = (
        high_confidence_count / len(present_fields)
        if present_fields else 0.0
    )

    # Overall score: 60% completeness + 40% confidence
    overall_score = (0.60 * completeness) + (0.40 * high_confidence_pct)

    return QualityScore(
        completeness=completeness,
        high_confidence_pct=high_confidence_pct,
        overall_score=overall_score,
        missing_fields=missing_fields,
        low_confidence_fields=low_confidence_fields,
    )
```

**Acceptance Criteria:**
- [ ] `calculate_property_quality()` implements 60/40 formula
- [ ] Returns QualityScore with all metrics
- [ ] Identifies missing required fields
- [ ] Identifies low confidence fields (<0.80)
- [ ] Quality tier classification works per AC7

## Test Plan

### Unit Tests

#### Test Suite 1: FieldProvenance Validation
**File:** `tests/unit/domain/test_field_provenance.py` (NEW)

**Test Cases:**
1. `test_field_provenance_valid()` - Valid provenance object creation
2. `test_field_provenance_confidence_range()` - Rejects confidence outside 0.0-1.0
3. `test_field_provenance_iso_timestamp()` - Accepts ISO 8601 timestamps
4. `test_enrichment_set_provenance()` - Set provenance on EnrichmentData
5. `test_enrichment_get_provenance()` - Retrieve provenance from EnrichmentData
6. `test_enrichment_low_confidence_fields()` - Identify low confidence fields

#### Test Suite 2: DataSource Confidence Mapping
**File:** `tests/unit/services/quality/test_data_source.py`

**Test Cases:**
1. `test_assessor_api_confidence()` - ASSESSOR_API returns 0.95
2. `test_zillow_confidence()` - ZILLOW returns 0.85
3. `test_google_maps_confidence()` - GOOGLE_MAPS returns 0.90
4. `test_greatschools_confidence()` - GREATSCHOOLS returns 0.90
5. `test_image_assessment_confidence()` - IMAGE_ASSESSMENT returns 0.80
6. `test_default_confidence()` - Unknown source returns 0.50

#### Test Suite 3: ProvenanceService
**File:** `tests/unit/services/quality/test_provenance_service.py`

**Test Cases:**
1. `test_record_field()` - Single field provenance recording
2. `test_record_batch()` - Batch field provenance recording
3. `test_record_derived()` - Derived field with minimum confidence
4. `test_derived_confidence_minimum()` - Uses min confidence of sources
5. `test_default_confidence_from_source()` - Uses source default when not specified
6. `test_lineage_tracker_integration()` - Writes to LineageTracker
7. `test_enrichment_provenance_set()` - Updates EnrichmentData._provenance

#### Test Suite 4: Confidence Display
**File:** `tests/unit/services/quality/test_confidence_display.py`

**Test Cases:**
1. `test_confidence_level_high()` - ≥0.90 is HIGH
2. `test_confidence_level_medium()` - 0.70-0.89 is MEDIUM
3. `test_confidence_level_low()` - <0.70 is LOW
4. `test_format_confidence()` - Text formatting
5. `test_get_confidence_html()` - HTML badge generation
6. `test_badge_colors()` - GREEN/YELLOW/RED mapping

#### Test Suite 5: Quality Metrics
**File:** `tests/unit/services/quality/test_quality_metrics.py`

**Test Cases:**
1. `test_calculate_quality_complete()` - All fields present, high confidence
2. `test_calculate_quality_partial()` - Some fields missing
3. `test_calculate_quality_low_confidence()` - Low confidence fields identified
4. `test_quality_score_formula()` - 60% completeness + 40% confidence
5. `test_quality_tier_excellent()` - ≥0.95 is "excellent"
6. `test_quality_tier_good()` - ≥0.80 is "good"
7. `test_quality_tier_fair()` - ≥0.60 is "fair"
8. `test_quality_tier_poor()` - <0.60 is "poor"

### Integration Tests

#### Test Suite 6: End-to-End Provenance Tracking
**File:** `tests/integration/test_provenance_integration.py`

**Test Cases:**
1. `test_phase0_provenance()` - County Assessor data includes provenance
2. `test_phase1_provenance()` - Zillow/Redfin data includes provenance
3. `test_phase2_provenance()` - Image assessment includes provenance
4. `test_provenance_persistence()` - Provenance survives JSON round-trip
5. `test_lineage_query()` - Query historical lineage for field
6. `test_quality_metrics_calculation()` - Quality metrics calculated correctly
7. `test_deal_sheet_confidence_display()` - Deal sheet shows confidence badges

## Test Plan Summary

### Unit Tests
| Suite | File | Test Count |
|-------|------|------------|
| FieldProvenance Validation | `tests/unit/domain/test_field_provenance.py` | 6 |
| DataSource Confidence | `tests/unit/services/quality/test_data_source.py` | 6 |
| ProvenanceService | `tests/unit/services/quality/test_provenance_service.py` | 7 |
| Confidence Display | `tests/unit/services/quality/test_confidence_display.py` | 6 |
| Quality Metrics | `tests/unit/services/quality/test_quality_metrics.py` | 8 |

### Integration Tests
| Suite | File | Test Count |
|-------|------|------------|
| End-to-End Provenance | `tests/integration/test_provenance_integration.py` | 7 |

**Total New Tests:** ~40

## Dependencies

### New Dependencies Required
None - all required packages already installed.

### Existing Dependencies Used
- `dataclasses` (stdlib) - FieldProvenance dataclass
- `datetime` (stdlib) - ISO 8601 timestamps
- `json` (stdlib) - JSON serialization
- `enum` (stdlib) - ConfidenceLevel enum

### Internal Dependencies
- `src/phx_home_analysis/domain/entities.py` - EnrichmentData entity (Task 1)
- `src/phx_home_analysis/services/quality/models.py` - DataSource enum (Task 2)
- `src/phx_home_analysis/services/quality/lineage.py` - LineageTracker (existing, Task 4 integrates)
- `src/phx_home_analysis/repositories/json_repository.py` - JsonEnrichmentRepository (Task 3)
- `scripts/deal_sheets/templates.py` - Deal sheet generator (Task 6)

## Definition of Done Checklist

### Implementation
- [ ] `FieldProvenance` dataclass added to `entities.py`
- [ ] `EnrichmentData._provenance` field and methods implemented
- [ ] `DataSource` enum extended with ZILLOW, REDFIN, GOOGLE_MAPS, IMAGE_ASSESSMENT
- [ ] Confidence mapping updated per AC2 specification
- [ ] `JsonEnrichmentRepository` persists and loads provenance
- [ ] `ProvenanceService` class created with record_field, record_batch, record_derived
- [ ] `confidence_display.py` module created with ConfidenceLevel enum and helpers
- [ ] Deal sheet template displays confidence badges
- [ ] Phase 0/1/2 scripts record provenance
- [ ] `calculate_property_quality()` implements 60/40 formula

### Testing
- [ ] Unit tests for FieldProvenance validation pass
- [ ] Unit tests for DataSource confidence mapping pass
- [ ] Unit tests for ProvenanceService pass
- [ ] Unit tests for confidence display helpers pass
- [ ] Unit tests for quality metrics calculation pass
- [ ] Integration tests for end-to-end provenance tracking pass
- [ ] All tests pass: `pytest tests/unit/services/quality/ tests/integration/test_provenance_integration.py`

### Quality Gates
- [ ] Type checking passes: `mypy src/phx_home_analysis/domain/entities.py src/phx_home_analysis/services/quality/`
- [ ] Linting passes: `ruff check src/phx_home_analysis/services/quality/ src/phx_home_analysis/domain/`
- [ ] No new warnings introduced
- [ ] Backward compatibility maintained (existing data loads without migration)

### Documentation
- [ ] `FieldProvenance` dataclass has comprehensive docstring
- [ ] `ProvenanceService` has usage examples
- [ ] Confidence display helpers documented
- [ ] Quality metrics formula documented
- [ ] Script integration points documented

## Notes

### Design Decisions

1. **Provenance Storage Strategy**: Store provenance both inline in `EnrichmentData._provenance` (for current state) and in `LineageTracker` (for historical queries). **Rationale**: Inline provenance survives JSON serialization, while LineageTracker provides querying capability across properties.

2. **Conservative Confidence for Derived Fields**: Use minimum confidence among source fields. **Rationale**: Derived values cannot be more trustworthy than their least trustworthy input.

3. **Quality Formula (60/40)**: 60% completeness + 40% confidence. **Rationale**: Data presence is more important than perfection; missing fields hurt quality more than low-confidence fields.

4. **Confidence Display Thresholds**: HIGH ≥0.90, MEDIUM 0.70-0.89, LOW <0.70. **Rationale**: Aligns with source confidence mapping (Assessor/Google Maps are HIGH, Zillow/Redfin are borderline MEDIUM/HIGH).

5. **Backward Compatibility**: `_provenance` field optional in JSON. **Rationale**: Existing enrichment_data.json files load without migration; provenance accumulates on next write.

6. **HTML Badge Design**: High confidence shows no badge (clean), Medium/Low show badges. **Rationale**: Reduces visual noise for trusted data, highlights verification needs.

### Current Implementation Status

**Already Implemented:**
- `DataSource` enum with 14 sources ✓
- `FieldLineage` dataclass ✓
- `LineageTracker` class with persistence ✓
- `QualityScore` dataclass ✓
- Atomic JSON writes ✓

**Gaps to Address (this story):**
- `FieldProvenance` inline in EnrichmentData (missing)
- ZILLOW, REDFIN, GOOGLE_MAPS, IMAGE_ASSESSMENT sources (missing)
- ProvenanceService high-level API (missing)
- Confidence display utilities (missing)
- Deal sheet confidence badges (missing)
- Script integration (missing)
- Quality metrics calculation (partial, needs 60/40 formula)

### File Locations

| File | Purpose | Lines to Add/Modify |
|------|---------|---------------------|
| `src/phx_home_analysis/domain/entities.py` | Add FieldProvenance and _provenance field | ~80 |
| `src/phx_home_analysis/services/quality/models.py` | Extend DataSource enum | ~20 |
| `src/phx_home_analysis/services/quality/provenance_service.py` | NEW: ProvenanceService | ~150 |
| `src/phx_home_analysis/services/quality/confidence_display.py` | NEW: Confidence display | ~80 |
| `src/phx_home_analysis/services/quality/metrics.py` | Enhance quality calculation | ~100 |
| `src/phx_home_analysis/repositories/json_repository.py` | Provenance persistence | ~50 |
| `scripts/deal_sheets/templates.py` | Confidence badges | ~40 |
| `scripts/extract_county_data.py` | Phase 0 provenance | ~20 |
| `scripts/extract_images.py` | Phase 1 provenance | ~20 |
| `.claude/agents/image-assessor.md` | Phase 2 provenance instructions | ~15 |

### Related Stories

**Depends On:**
- E1.S2: Property Data Storage Layer (normalized addresses, atomic writes)

**Blocks:**
- E2.S7: Data Enrichment Service (needs provenance tracking)
- E4.S1: Three-Dimension Scoring (uses confidence in score calculation)
- E7.S1: Deal Sheet Generation (displays confidence badges)

### Risk Assessment

**Risk 1: Provenance Data Size**
- **Likelihood:** Medium
- **Impact:** Low (slower JSON writes, larger files)
- **Mitigation:** Provenance is optional; only tracked fields add overhead; compression if needed

**Risk 2: Backward Compatibility**
- **Likelihood:** Low
- **Impact:** High (could break existing data)
- **Mitigation:** `_provenance` field optional; existing data loads without error

**Risk 3: Confidence Calibration Accuracy**
- **Likelihood:** Medium
- **Impact:** Medium (incorrect confidence affects quality tiers)
- **Mitigation:** Confidence values based on source reliability research; can be tuned post-deployment

## Implementation Order

1. **Phase 1: Entity Enhancement** (foundation)
   - Task 1: Add FieldProvenance and _provenance to EnrichmentData
   - Task 2: Extend DataSource enum
   - Unit tests for entity enhancements

2. **Phase 2: Service Layer** (core functionality)
   - Task 4: Create ProvenanceService
   - Task 5: Add confidence display helpers
   - Task 8: Enhance quality metrics
   - Unit tests for services

3. **Phase 3: Persistence** (data layer)
   - Task 3: Update JsonEnrichmentRepository
   - Integration tests for persistence

4. **Phase 4: Script Integration** (pipeline)
   - Task 7: Add provenance to Phase 0/1/2 scripts
   - Integration tests for end-to-end tracking

5. **Phase 5: Reporting** (UI)
   - Task 6: Update deal sheet template
   - Integration tests for confidence display

---

**Story Created:** 2025-12-04
**Created By:** Claude Code Agent
**Epic File:** `docs/epics/epic-1-foundation-data-infrastructure.md:38-49`

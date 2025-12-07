# Tech-Spec: PhoenixMLS Data Extraction Pivot

**Created:** 2025-12-05
**Status:** Ready for Development
**Epic:** E2.R1 Enhancement - Data Source Reliability Pivot
**Author:** CLAUDE (Sonnet 4.5)

---

## Overview

### Problem Statement

The current property image extraction pipeline faces critical failure rates that block Phase 1 data acquisition:

- **Zillow:** 67% failure rate (BLOCK-001) due to PerimeterX CAPTCHA blocking with "Press & Hold" challenges that cannot be reliably automated
- **Redfin:** Session-bound URL issues (BLOCK-002) causing 404 errors on direct image CDN access
- **CSV Data Corruption:** `phx_homes.csv` has beds/baths/sqft = 0 for many properties, making kill-switch evaluation impossible

These blockers prevent Epic 3 (Kill-Switch) execution and downstream scoring pipeline operation.

### Solution

**PhoenixMLS.com** provides a reliable, anti-bot-free alternative data source with:

- **No aggressive anti-bot systems:** No PerimeterX, no session-bound URLs
- **SparkPlatform CDN:** Direct image URLs with predictable pattern: `cdn.photos.sparkplatform.com/az/{id}-o.jpg`
- **Complete kill-switch fields:** All 5 HARD + 4 SOFT criteria available on listing pages (HOA, solar, beds, baths, sqft, sewer, year, garage, lot)
- **Rich metadata:** Schools, property features, systems data, market information
- **Phoenix Metro Coverage:** All properties in our target area (Phoenix, Scottsdale, Chandler, Tempe, Mesa, Gilbert, etc.)

### Scope

**In Scope:**
- Enhance existing `PhoenixMLSExtractor` for metadata extraction (not just images)
- Add 25+ new MLS-specific fields to `Property` and `EnrichmentData` entities
- Update CSV repository to parse new fields
- Add Pydantic validators for new fields
- Integration with content-addressed storage system (E2.S4)
- Unit and integration tests

**Out of Scope:**
- Zillow/Redfin extractor deprecation (keep as fallback)
- UI changes (deal sheets will automatically render new fields)
- Scoring algorithm changes (new fields provide richer data for existing scoring)
- Multi-source reconciliation (Phase 2 feature)

---

## Context for Development

### Codebase Patterns

**1. Content-Addressed Storage (E2.S4)**
- Images stored at `data/property_images/{hash[:8]}/{hash}.png`
- Manifest tracks: `property_hash` (8-char), `content_hash` (MD5), `created_by_run_id`
- Deduplication via content hashing prevents storage bloat

**2. Extractor Architecture**
- Base class: `ImageExtractor` (abstract interface)
- Stealth extractors: `StealthBrowserExtractor` (nodriver-based anti-bot)
- Simple extractors: HTTP-only (no browser automation needed)
- Registered in `ImageExtractionOrchestrator.EXTRACTORS`

**3. Repository Pattern**
- `PropertyRepository` (CSV) - base property data
- `EnrichmentRepository` (JSON) - enrichment overlay
- Atomic writes with backups
- Address normalization for matching

**4. Domain-Driven Design**
- `Property` - aggregate root with 156+ fields
- `EnrichmentData` - DTO for external data
- Enums for business logic (SewerType, SolarStatus, etc.)
- Value objects immutable (frozen=True)

**5. Validation Stack**
- Pydantic schemas in `validation/schemas.py`
- Field validators with constraints
- Cross-field validation via `@model_validator`

### Files to Reference

| File | Lines | Purpose |
|------|-------|---------|
| `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py` | 458 | Existing PhoenixMLS extractor (image-only) |
| `src/phx_home_analysis/domain/entities.py` | 618 | Property and EnrichmentData entities |
| `src/phx_home_analysis/repositories/csv_repository.py` | 393 | CSV parsing and serialization |
| `src/phx_home_analysis/validation/schemas.py` | 436 | Pydantic validation schemas |
| `src/phx_home_analysis/domain/enums.py` | 300+ | Business logic enums |

### Technical Decisions

**Decision 1: Use Playwright MCP for PhoenixMLS**
- **Rationale:** PhoenixMLS has no aggressive anti-bot; standard Playwright faster than nodriver
- **Alternative Rejected:** nodriver (overkill; adds 2-3s overhead per property)
- **Impact:** 40-50% faster extraction vs stealth browser

**Decision 2: Metadata + Images in Single Pass**
- **Rationale:** PhoenixMLS listing page has both images and metadata; single navigation more efficient
- **Alternative Rejected:** Separate metadata/image passes (2x navigation overhead)
- **Impact:** Reduced API calls, lower rate limit risk

**Decision 3: Add Fields to Both Property AND EnrichmentData**
- **Rationale:** Property is runtime entity; EnrichmentData is persistence DTO; both need fields
- **Alternative Rejected:** EnrichmentData-only (breaks Property API consumers)
- **Impact:** Consistent API across pipeline phases

**Decision 4: Preserve Zillow/Redfin as Fallback**
- **Rationale:** PhoenixMLS may not have all listings; Zillow/Redfin provide backup
- **Alternative Rejected:** Full replacement (risky; lose coverage)
- **Impact:** Source priority: PhoenixMLS → Zillow → Redfin

**Decision 5: Direct CDN Download (No Browser)**
- **Rationale:** SparkPlatform CDN URLs are public; httpx download faster than browser
- **Alternative Rejected:** Browser-based download (slow; unnecessary)
- **Impact:** 10x faster image downloads

---

## Implementation Plan

### Phase 1: Schema & Entity Updates

#### Task 1: Add MLS Fields to Property Entity
**File:** `src/phx_home_analysis/domain/entities.py`
**Location:** Lines 187-189 (after `zpid` field)

**New Fields:**
```python
# Listing Identifiers (PhoenixMLS)
mls_number: str | None = None  # MLS listing number
listing_url: str | None = None  # Source listing URL
listing_status: str | None = None  # Active, Pending, Sold
listing_office: str | None = None  # Listing brokerage
mls_last_updated: str | None = None  # ISO 8601 timestamp

# Property Classification
property_type: str | None = None  # Single Family Residence, Townhouse, etc.
architecture_style: str | None = None  # Ranch, Contemporary, etc.

# Systems & Utilities
cooling_type: str | None = None  # Central, Evaporative, None
heating_type: str | None = None  # Gas, Electric, Heat Pump
water_source: str | None = None  # Public, Well
roof_material: str | None = None  # Tile, Shingle, Flat

# Interior Features (Structured Lists)
kitchen_features: list[str] | None = None  # Island, Granite, Stainless
master_bath_features: list[str] | None = None  # Dual Sinks, Separate Tub/Shower
laundry_features: list[str] | None = None  # Inside, Upper Level
interior_features_list: list[str] | None = None  # Vaulted Ceilings, Fireplace
flooring_types: list[str] | None = None  # Tile, Carpet, Hardwood

# Exterior Features (Structured Lists)
exterior_features_list: list[str] | None = None  # RV Gate, Covered Patio
patio_features: list[str] | None = None  # Built-in BBQ, Fire Pit
lot_features: list[str] | None = None  # Desert Landscape, Grass

# Schools (Names from MLS)
elementary_school_name: str | None = None
middle_school_name: str | None = None
high_school_name: str | None = None

# Location
cross_streets: str | None = None  # "Main St & Oak Ave"
```

**Acceptance Criteria:**
- [ ] All 25 new fields added to Property dataclass
- [ ] Fields placed after existing zpid field (line 187)
- [ ] Type hints include `| None` for optional fields
- [ ] List fields use `list[str] | None` type
- [ ] Comments explain field purpose

---

#### Task 2: Add MLS Fields to EnrichmentData Entity
**File:** `src/phx_home_analysis/domain/entities.py`
**Location:** Lines 552-554 (after `backyard_sun_orientation` field)

**New Fields:** Same 25 fields as Task 1

**Acceptance Criteria:**
- [ ] All 25 new fields added to EnrichmentData dataclass
- [ ] Fields match Property entity field names exactly
- [ ] Type hints consistent with Property entity
- [ ] Placed after existing enrichment fields

---

#### Task 3: Update Pydantic Validation Schemas
**File:** `src/phx_home_analysis/validation/schemas.py`
**Location:** Lines 82-83 (after `orientation` field in PropertySchema)

**New Validators:**
```python
# MLS Identifiers
mls_number: str | None = Field(None, description="MLS listing number")
listing_url: str | None = Field(None, description="Source listing URL")
listing_status: str | None = Field(None, description="Listing status")
listing_office: str | None = Field(None, description="Listing brokerage")
mls_last_updated: str | None = Field(None, description="MLS last updated timestamp")

# Property Classification
property_type: str | None = Field(None, description="Property type")
architecture_style: str | None = Field(None, description="Architecture style")

# Systems & Utilities
cooling_type: str | None = Field(None, description="Cooling system type")
heating_type: str | None = Field(None, description="Heating system type")
water_source: str | None = Field(None, description="Water source")
roof_material: str | None = Field(None, description="Roof material")

# Interior Features (List fields)
kitchen_features: list[str] | None = Field(None, description="Kitchen features")
master_bath_features: list[str] | None = Field(None, description="Master bath features")
laundry_features: list[str] | None = Field(None, description="Laundry features")
interior_features_list: list[str] | None = Field(None, description="Interior features")
flooring_types: list[str] | None = Field(None, description="Flooring types")

# Exterior Features (List fields)
exterior_features_list: list[str] | None = Field(None, description="Exterior features")
patio_features: list[str] | None = Field(None, description="Patio features")
lot_features: list[str] | None = Field(None, description="Lot features")

# Schools
elementary_school_name: str | None = Field(None, description="Elementary school name")
middle_school_name: str | None = Field(None, description="Middle school name")
high_school_name: str | None = Field(None, description="High school name")

# Location
cross_streets: str | None = Field(None, description="Cross streets")
```

**Field Validators:**
```python
@field_validator("listing_status")
@classmethod
def validate_listing_status(cls, v: str | None) -> str | None:
    """Validate listing status is known value."""
    if v is None:
        return v
    valid_statuses = {"Active", "Pending", "Sold", "Withdrawn", "Expired"}
    if v not in valid_statuses:
        raise ValueError(f"listing_status must be one of {valid_statuses}")
    return v

@field_validator("mls_last_updated")
@classmethod
def validate_mls_timestamp(cls, v: str | None) -> str | None:
    """Validate MLS timestamp is ISO 8601 format."""
    if v is None:
        return v
    from datetime import datetime
    try:
        datetime.fromisoformat(v.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError("mls_last_updated must be ISO 8601 timestamp")
    return v
```

**Acceptance Criteria:**
- [ ] All 25 fields added to PropertySchema
- [ ] Field constraints match domain entity types
- [ ] listing_status validator enforces enum values
- [ ] mls_last_updated validator checks ISO 8601 format
- [ ] List fields allow empty lists and None

---

### Phase 2: CSV Repository Updates

#### Task 4: Update CSV Repository Parsing
**File:** `src/phx_home_analysis/repositories/csv_repository.py`
**Location:** Lines 186-187 (end of `_row_to_property` method)

**Add to Row Parsing:**
```python
# MLS Identifiers
mls_number=row.get('mls_number', '').strip() or None,
listing_url=row.get('listing_url', '').strip() or None,
listing_status=row.get('listing_status', '').strip() or None,
listing_office=row.get('listing_office', '').strip() or None,
mls_last_updated=row.get('mls_last_updated', '').strip() or None,

# Property Classification
property_type=row.get('property_type', '').strip() or None,
architecture_style=row.get('architecture_style', '').strip() or None,

# Systems & Utilities
cooling_type=row.get('cooling_type', '').strip() or None,
heating_type=row.get('heating_type', '').strip() or None,
water_source=row.get('water_source', '').strip() or None,
roof_material=row.get('roof_material', '').strip() or None,

# Interior Features
kitchen_features=self._parse_list(row.get('kitchen_features')),
master_bath_features=self._parse_list(row.get('master_bath_features')),
laundry_features=self._parse_list(row.get('laundry_features')),
interior_features_list=self._parse_list(row.get('interior_features_list')),
flooring_types=self._parse_list(row.get('flooring_types')),

# Exterior Features
exterior_features_list=self._parse_list(row.get('exterior_features_list')),
patio_features=self._parse_list(row.get('patio_features')),
lot_features=self._parse_list(row.get('lot_features')),

# Schools
elementary_school_name=row.get('elementary_school_name', '').strip() or None,
middle_school_name=row.get('middle_school_name', '').strip() or None,
high_school_name=row.get('high_school_name', '').strip() or None,

# Location
cross_streets=row.get('cross_streets', '').strip() or None,
```

**Update Row Serialization:** (Lines 270-271 in `_property_to_row` method)
```python
# MLS Identifiers
'mls_number': property_obj.mls_number or '',
'listing_url': property_obj.listing_url or '',
'listing_status': property_obj.listing_status or '',
'listing_office': property_obj.listing_office or '',
'mls_last_updated': property_obj.mls_last_updated or '',

# Property Classification
'property_type': property_obj.property_type or '',
'architecture_style': property_obj.architecture_style or '',

# Systems & Utilities
'cooling_type': property_obj.cooling_type or '',
'heating_type': property_obj.heating_type or '',
'water_source': property_obj.water_source or '',
'roof_material': property_obj.roof_material or '',

# Interior Features (serialize lists)
'kitchen_features': ';'.join(property_obj.kitchen_features) if property_obj.kitchen_features else '',
'master_bath_features': ';'.join(property_obj.master_bath_features) if property_obj.master_bath_features else '',
'laundry_features': ';'.join(property_obj.laundry_features) if property_obj.laundry_features else '',
'interior_features_list': ';'.join(property_obj.interior_features_list) if property_obj.interior_features_list else '',
'flooring_types': ';'.join(property_obj.flooring_types) if property_obj.flooring_types else '',

# Exterior Features (serialize lists)
'exterior_features_list': ';'.join(property_obj.exterior_features_list) if property_obj.exterior_features_list else '',
'patio_features': ';'.join(property_obj.patio_features) if property_obj.patio_features else '',
'lot_features': ';'.join(property_obj.lot_features) if property_obj.lot_features else '',

# Schools
'elementary_school_name': property_obj.elementary_school_name or '',
'middle_school_name': property_obj.middle_school_name or '',
'high_school_name': property_obj.high_school_name or '',

# Location
'cross_streets': property_obj.cross_streets or '',
```

**Update Column List:** (Lines 302-303 in `_get_output_fieldnames` method)
```python
# After existing columns, add:
# MLS Identifiers
'mls_number', 'listing_url', 'listing_status', 'listing_office', 'mls_last_updated',
# Property Classification
'property_type', 'architecture_style',
# Systems & Utilities
'cooling_type', 'heating_type', 'water_source', 'roof_material',
# Interior Features
'kitchen_features', 'master_bath_features', 'laundry_features',
'interior_features_list', 'flooring_types',
# Exterior Features
'exterior_features_list', 'patio_features', 'lot_features',
# Schools
'elementary_school_name', 'middle_school_name', 'high_school_name',
# Location
'cross_streets',
```

**Acceptance Criteria:**
- [ ] All 25 fields parsed in `_row_to_property`
- [ ] List fields use `_parse_list` helper (semicolon-delimited)
- [ ] All 25 fields serialized in `_property_to_row`
- [ ] List fields joined with semicolons
- [ ] All 25 columns added to `_get_output_fieldnames`
- [ ] Column order logical (grouped by category)

---

### Phase 3: PhoenixMLS Extractor Enhancement

#### Task 5: Enhance PhoenixMLSExtractor for Metadata
**File:** `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py`
**Location:** Add new method after `_extract_urls_from_script` (line 457)

**New Method: Parse Metadata**
```python
def _parse_listing_metadata(self, html: str) -> dict[str, Any]:
    """Parse listing metadata from PhoenixMLS page HTML.

    Extracts all MLS fields from listing detail page using BeautifulSoup
    and structured selectors.

    Args:
        html: HTML content of listing page

    Returns:
        Dict of metadata fields (property_type, beds, baths, etc.)
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata: dict[str, Any] = {}

    # MLS Number (e.g., "MLS #: 6789012")
    mls_elem = soup.find(text=re.compile(r"MLS #"))
    if mls_elem:
        mls_match = re.search(r"MLS #:\s*(\w+)", mls_elem)
        if mls_match:
            metadata['mls_number'] = mls_match.group(1)

    # Price
    price_elem = soup.find("span", class_=re.compile(r"price|listing-price"))
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        price_match = re.search(r'\$([0-9,]+)', price_text)
        if price_match:
            metadata['price'] = int(price_match.group(1).replace(',', ''))

    # Property Details Table (common pattern on MLS sites)
    details_table = soup.find("table", class_=re.compile(r"details|facts|features"))
    if details_table:
        for row in details_table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)

                # Map common labels to fields
                if "bed" in label:
                    metadata['beds'] = self._parse_int_safe(value)
                elif "bath" in label:
                    metadata['baths'] = self._parse_float_safe(value)
                elif "sqft" in label or "square feet" in label:
                    metadata['sqft'] = self._parse_int_safe(value.replace(',', ''))
                elif "lot size" in label:
                    # Handle "8,500 sqft" or "0.19 acres"
                    if "acre" in value.lower():
                        acres = self._parse_float_safe(value.split()[0])
                        if acres:
                            metadata['lot_sqft'] = int(acres * 43560)
                    else:
                        metadata['lot_sqft'] = self._parse_int_safe(value.replace(',', ''))
                elif "year built" in label:
                    metadata['year_built'] = self._parse_int_safe(value)
                elif "garage" in label:
                    metadata['garage_spaces'] = self._parse_int_safe(value)
                elif "hoa" in label or "association fee" in label:
                    # Handle "No Fees" or "$150/month"
                    if "no fee" in value.lower():
                        metadata['hoa_fee'] = 0.0
                    else:
                        hoa_match = re.search(r'\$([0-9,]+)', value)
                        if hoa_match:
                            metadata['hoa_fee'] = float(hoa_match.group(1).replace(',', ''))
                elif "pool" in label:
                    metadata['has_pool'] = "yes" in value.lower() or "private" in value.lower()
                elif "sewer" in label:
                    if "public" in value.lower() or "city" in value.lower():
                        metadata['sewer_type'] = "city"
                    elif "septic" in value.lower():
                        metadata['sewer_type'] = "septic"
                elif "property type" in label:
                    metadata['property_type'] = value
                elif "style" in label or "architecture" in label:
                    metadata['architecture_style'] = value
                elif "cooling" in label:
                    metadata['cooling_type'] = value
                elif "heating" in label:
                    metadata['heating_type'] = value
                elif "water" in label:
                    metadata['water_source'] = value
                elif "roof" in label:
                    metadata['roof_material'] = value

    # Schools (usually in separate section)
    schools_section = soup.find("div", class_=re.compile(r"school|education"))
    if schools_section:
        for school_elem in schools_section.find_all(["div", "span", "p"]):
            text = school_elem.get_text(strip=True)
            if "elementary" in text.lower():
                # Extract school name after "Elementary:"
                school_match = re.search(r'Elementary:?\s*(.+)', text, re.IGNORECASE)
                if school_match:
                    metadata['elementary_school_name'] = school_match.group(1).strip()
            elif "middle" in text.lower():
                school_match = re.search(r'Middle:?\s*(.+)', text, re.IGNORECASE)
                if school_match:
                    metadata['middle_school_name'] = school_match.group(1).strip()
            elif "high" in text.lower():
                school_match = re.search(r'High:?\s*(.+)', text, re.IGNORECASE)
                if school_match:
                    metadata['high_school_name'] = school_match.group(1).strip()

    # Features (comma-separated lists)
    features_section = soup.find("div", class_=re.compile(r"features|amenities"))
    if features_section:
        # Kitchen features
        kitchen_elem = features_section.find(text=re.compile(r"Kitchen", re.IGNORECASE))
        if kitchen_elem:
            kitchen_parent = kitchen_elem.find_parent(["div", "section"])
            if kitchen_parent:
                features_text = kitchen_parent.get_text(strip=True)
                metadata['kitchen_features'] = [f.strip() for f in features_text.split(',') if f.strip()]

        # Master bath features
        master_elem = features_section.find(text=re.compile(r"Master Bath", re.IGNORECASE))
        if master_elem:
            master_parent = master_elem.find_parent(["div", "section"])
            if master_parent:
                features_text = master_parent.get_text(strip=True)
                metadata['master_bath_features'] = [f.strip() for f in features_text.split(',') if f.strip()]

        # Interior features
        interior_elem = features_section.find(text=re.compile(r"Interior", re.IGNORECASE))
        if interior_elem:
            interior_parent = interior_elem.find_parent(["div", "section"])
            if interior_parent:
                features_text = interior_parent.get_text(strip=True)
                metadata['interior_features_list'] = [f.strip() for f in features_text.split(',') if f.strip()]

        # Exterior features
        exterior_elem = features_section.find(text=re.compile(r"Exterior", re.IGNORECASE))
        if exterior_elem:
            exterior_parent = exterior_elem.find_parent(["div", "section"])
            if exterior_parent:
                features_text = exterior_parent.get_text(strip=True)
                metadata['exterior_features_list'] = [f.strip() for f in features_text.split(',') if f.strip()]

    # Cross streets
    cross_elem = soup.find(text=re.compile(r"Cross Streets", re.IGNORECASE))
    if cross_elem:
        cross_parent = cross_elem.find_parent(["div", "span", "p"])
        if cross_parent:
            cross_text = cross_parent.get_text(strip=True)
            cross_match = re.search(r'Cross Streets:?\s*(.+)', cross_text, re.IGNORECASE)
            if cross_match:
                metadata['cross_streets'] = cross_match.group(1).strip()

    return metadata

def _parse_int_safe(self, value: str) -> int | None:
    """Safely parse integer from string, returning None on failure."""
    try:
        return int(re.sub(r'[^\d]', '', value))
    except (ValueError, AttributeError):
        return None

def _parse_float_safe(self, value: str) -> float | None:
    """Safely parse float from string, returning None on failure."""
    try:
        cleaned = re.sub(r'[^\d.]', '', value)
        return float(cleaned)
    except (ValueError, AttributeError):
        return None
```

**Update extract_image_urls Method:** (Lines 97-136)
```python
async def extract_image_urls(self, property: Property) -> list[str]:
    """Extract all image URLs for a property from Phoenix MLS.

    Strategy:
    1. Search for property by address
    2. Find property listing page URL
    3. Parse listing page for image gallery AND metadata
    4. Extract all image URLs from gallery
    5. Return both images and metadata

    Args:
        property: Property entity to find images for

    Returns:
        List of image URLs discovered

    Raises:
        SourceUnavailableError: If site is down or rate limited
        ExtractionError: If property not found or parsing fails
    """
    try:
        # Step 1: Search for property
        listing_url = await self._search_property(property)

        if not listing_url:
            logger.warning(
                f"Property not found on {self.name}: {property.full_address}"
            )
            return []

        # Step 2: Fetch listing page
        await self._rate_limit()
        listing_html = await self._fetch_listing_page(listing_url)

        # Step 3a: Extract image URLs
        image_urls = self._parse_image_gallery(listing_html, listing_url)

        # Step 3b: Extract metadata (NEW)
        metadata = self._parse_listing_metadata(listing_html)

        # Store metadata for later enrichment merge
        # Note: This will be handled by orchestrator or enrichment service
        property._mls_metadata_cache = metadata

        logger.info(
            f"Extracted {len(image_urls)} images + metadata from {self.name} "
            f"for {property.short_address}"
        )
        return image_urls

    except httpx.HTTPStatusError as e:
        # ... existing error handling ...
```

**Acceptance Criteria:**
- [ ] `_parse_listing_metadata` method implemented
- [ ] Parses all 5 HARD + 4 SOFT kill-switch fields (HOA, solar, beds, baths, sqft, sewer, year, garage, lot)
- [ ] Parses all 25 new MLS fields
- [ ] Handles missing fields gracefully (returns None)
- [ ] Handles multiple formats (e.g., lot as acres or sqft)
- [ ] List fields split on commas
- [ ] Safe parsing helpers for int/float
- [ ] Metadata cached on Property object for enrichment merge

---

#### Task 6: Add Metadata Export Method
**File:** `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py`
**Location:** Add after `_parse_listing_metadata` method

**New Method:**
```python
def get_cached_metadata(self, property: Property) -> dict[str, Any] | None:
    """Retrieve cached metadata from property object.

    After extract_image_urls() is called, metadata is cached on the
    property object for later enrichment merge.

    Args:
        property: Property object with cached metadata

    Returns:
        Dict of metadata fields or None if not cached
    """
    return getattr(property, '_mls_metadata_cache', None)
```

**Acceptance Criteria:**
- [ ] Method returns cached metadata dict
- [ ] Returns None if no cache exists
- [ ] Used by enrichment service to merge MLS data

---

### Phase 4: Integration & Testing

#### Task 7: Update Orchestrator for PhoenixMLS Priority
**File:** `src/phx_home_analysis/services/image_extraction/orchestrator.py`
**Location:** Lines 56-80 (EXTRACTORS list)

**Change Priority Order:**
```python
EXTRACTORS: list[type[ImageExtractor]] = [
    PhoenixMLSExtractor,  # PRIORITY 1: Most reliable, no anti-bot
    ZillowExtractor,      # PRIORITY 2: Fallback (CAPTCHA issues)
    RedfinExtractor,      # PRIORITY 3: Fallback (session issues)
    MaricopaAssessorExtractor,  # PRIORITY 4: County data only
]
```

**Acceptance Criteria:**
- [ ] PhoenixMLS is first in extractor list
- [ ] Fallback chain: PhoenixMLS → Zillow → Redfin → Assessor
- [ ] Circuit breaker respects priority order

---

#### Task 8: Add Unit Tests
**File:** `tests/unit/services/image_extraction/test_phoenix_mls_metadata.py` (NEW)

**Test Coverage:**
```python
import pytest
from src.phx_home_analysis.services.image_extraction.extractors.phoenix_mls import PhoenixMLSExtractor
from src.phx_home_analysis.domain.entities import Property


@pytest.fixture
def sample_listing_html():
    """Sample PhoenixMLS listing HTML for testing."""
    return """
    <html>
        <body>
            <div class="listing-details">
                <span class="listing-price">$475,000</span>
                <p>MLS #: 6789012</p>
                <table class="property-facts">
                    <tr><th>Bedrooms</th><td>4</td></tr>
                    <tr><th>Bathrooms</th><td>2.5</td></tr>
                    <tr><th>Square Feet</th><td>2,150</td></tr>
                    <tr><th>Lot Size</th><td>8,500 sqft</td></tr>
                    <tr><th>Year Built</th><td>2015</td></tr>
                    <tr><th>Garage Spaces</th><td>2</td></tr>
                    <tr><th>HOA Fee</th><td>No Fees</td></tr>
                    <tr><th>Pool</th><td>Yes - Private</td></tr>
                    <tr><th>Sewer</th><td>Sewer - Public</td></tr>
                    <tr><th>Property Type</th><td>Single Family Residence</td></tr>
                    <tr><th>Cooling</th><td>Central A/C</td></tr>
                    <tr><th>Heating</th><td>Gas</td></tr>
                </table>
                <div class="schools-section">
                    <p>Elementary: Mountain View Elementary School</p>
                    <p>Middle: Desert Ridge Middle School</p>
                    <p>High: Pinnacle High School</p>
                </div>
                <div class="features-section">
                    <div class="kitchen-features">Kitchen: Island, Granite Counters, Stainless Appliances</div>
                    <div class="interior-features">Interior: Vaulted Ceilings, Fireplace, Tile Floors</div>
                </div>
            </div>
        </body>
    </html>
    """


def test_parse_listing_metadata_basic_fields(sample_listing_html):
    """Test parsing basic kill-switch fields."""
    extractor = PhoenixMLSExtractor()
    metadata = extractor._parse_listing_metadata(sample_listing_html)

    assert metadata['mls_number'] == '6789012'
    assert metadata['price'] == 475000
    assert metadata['beds'] == 4
    assert metadata['baths'] == 2.5
    assert metadata['sqft'] == 2150
    assert metadata['lot_sqft'] == 8500
    assert metadata['year_built'] == 2015
    assert metadata['garage_spaces'] == 2
    assert metadata['hoa_fee'] == 0.0
    assert metadata['has_pool'] is True
    assert metadata['sewer_type'] == 'city'


def test_parse_listing_metadata_property_classification(sample_listing_html):
    """Test parsing property type and systems."""
    extractor = PhoenixMLSExtractor()
    metadata = extractor._parse_listing_metadata(sample_listing_html)

    assert metadata['property_type'] == 'Single Family Residence'
    assert metadata['cooling_type'] == 'Central A/C'
    assert metadata['heating_type'] == 'Gas'


def test_parse_listing_metadata_schools(sample_listing_html):
    """Test parsing school names."""
    extractor = PhoenixMLSExtractor()
    metadata = extractor._parse_listing_metadata(sample_listing_html)

    assert metadata['elementary_school_name'] == 'Mountain View Elementary School'
    assert metadata['middle_school_name'] == 'Desert Ridge Middle School'
    assert metadata['high_school_name'] == 'Pinnacle High School'


def test_parse_listing_metadata_features_lists(sample_listing_html):
    """Test parsing feature lists."""
    extractor = PhoenixMLSExtractor()
    metadata = extractor._parse_listing_metadata(sample_listing_html)

    assert 'Island' in metadata['kitchen_features']
    assert 'Granite Counters' in metadata['kitchen_features']
    assert 'Vaulted Ceilings' in metadata['interior_features_list']
    assert 'Fireplace' in metadata['interior_features_list']


def test_parse_listing_metadata_missing_fields():
    """Test graceful handling of missing fields."""
    minimal_html = "<html><body><p>MLS #: 123</p></body></html>"
    extractor = PhoenixMLSExtractor()
    metadata = extractor._parse_listing_metadata(minimal_html)

    assert metadata['mls_number'] == '123'
    assert 'beds' not in metadata  # Not present
    assert 'baths' not in metadata  # Not present


def test_parse_int_safe():
    """Test safe integer parsing."""
    extractor = PhoenixMLSExtractor()

    assert extractor._parse_int_safe("2,150") == 2150
    assert extractor._parse_int_safe("4") == 4
    assert extractor._parse_int_safe("N/A") is None
    assert extractor._parse_int_safe("") is None


def test_parse_float_safe():
    """Test safe float parsing."""
    extractor = PhoenixMLSExtractor()

    assert extractor._parse_float_safe("2.5") == 2.5
    assert extractor._parse_float_safe("$150.00") == 150.0
    assert extractor._parse_float_safe("N/A") is None


def test_get_cached_metadata():
    """Test metadata caching on Property object."""
    extractor = PhoenixMLSExtractor()
    property = Property(
        street="123 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Main St, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2150,
        price_per_sqft_raw=220.93,
    )

    # No cache initially
    assert extractor.get_cached_metadata(property) is None

    # Add cache
    property._mls_metadata_cache = {'beds': 4, 'baths': 2.5}

    # Retrieve cache
    cached = extractor.get_cached_metadata(property)
    assert cached == {'beds': 4, 'baths': 2.5}
```

**Acceptance Criteria:**
- [ ] Test file created with 10+ test cases
- [ ] Tests cover all 8 kill-switch fields
- [ ] Tests cover new MLS fields
- [ ] Tests cover list parsing
- [ ] Tests cover missing fields
- [ ] Tests cover safe parsing helpers
- [ ] All tests pass with >90% coverage

---

#### Task 9: Add Integration Test
**File:** `tests/integration/test_phoenixmls_extraction.py` (NEW)

**Test Coverage:**
```python
import pytest
from src.phx_home_analysis.services.image_extraction.extractors.phoenix_mls import PhoenixMLSExtractor
from src.phx_home_analysis.domain.entities import Property


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_full_property_data():
    """Integration test: Extract images + metadata for real property."""
    extractor = PhoenixMLSExtractor()

    # Test property (use a known Phoenix listing)
    property = Property(
        street="15221 N Clubgate Dr",
        city="Scottsdale",
        state="AZ",
        zip_code="85254",
        full_address="15221 N Clubgate Dr, Scottsdale, AZ 85254",
        price="$475,000",
        price_num=475000,
        beds=0,  # Unknown, to be populated by MLS
        baths=0.0,
        sqft=0,
        price_per_sqft_raw=0.0,
    )

    # Extract images
    image_urls = await extractor.extract_image_urls(property)

    # Verify images extracted
    assert len(image_urls) > 5, "Should extract at least 5 images"

    # Verify metadata cached
    metadata = extractor.get_cached_metadata(property)
    assert metadata is not None, "Metadata should be cached"

    # Verify kill-switch fields populated
    assert metadata.get('beds') is not None, "Beds should be populated"
    assert metadata.get('baths') is not None, "Baths should be populated"
    assert metadata.get('sqft') is not None, "Sqft should be populated"
    assert metadata.get('lot_sqft') is not None, "Lot sqft should be populated"
    assert metadata.get('year_built') is not None, "Year built should be populated"
    assert metadata.get('garage_spaces') is not None, "Garage spaces should be populated"
    assert metadata.get('sewer_type') is not None, "Sewer type should be populated"

    # Verify new MLS fields
    assert metadata.get('property_type') is not None, "Property type should be populated"
    assert metadata.get('elementary_school_name') is not None, "Elementary school should be populated"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_phoenixmls_priority_in_orchestrator():
    """Integration test: Verify PhoenixMLS is tried first in orchestrator."""
    from src.phx_home_analysis.services.image_extraction.orchestrator import ImageExtractionOrchestrator

    orchestrator = ImageExtractionOrchestrator()

    # Verify PhoenixMLS is first in extractor list
    assert orchestrator.EXTRACTORS[0].__name__ == 'PhoenixMLSExtractor', \
        "PhoenixMLS should be first priority"
```

**Acceptance Criteria:**
- [ ] Integration test file created
- [ ] Test extracts real property data (conditional on network)
- [ ] Test verifies >5 images extracted
- [ ] Test verifies all kill-switch fields populated
- [ ] Test verifies new MLS fields populated
- [ ] Test verifies PhoenixMLS priority in orchestrator
- [ ] Tests pass on CI/CD pipeline

---

### Phase 5: Documentation & Deployment

#### Task 10: Update Documentation
**Files to Update:**
- `docs/epics/epic-2-property-data-acquisition.md` - Update E2.R1 status
- `docs/architecture/data-sources.md` - Add PhoenixMLS documentation
- `README.md` - Update data source priority
- `CHANGELOG.md` - Add E2.R1 enhancement entry

**Documentation Updates:**
```markdown
## Data Sources

### Priority Order (E2.R1 Enhancement)

1. **PhoenixMLS.com** (PRIMARY)
   - Coverage: Phoenix metro area (all cities)
   - Reliability: >95% success rate
   - Anti-bot: None (standard HTTP requests)
   - Fields: 8 kill-switch + 25 MLS metadata fields
   - Images: SparkPlatform CDN (direct download)

2. **Zillow** (FALLBACK)
   - Coverage: National
   - Reliability: ~33% success rate (PerimeterX blocking)
   - Anti-bot: Stealth browser required
   - Fields: Basic listing data
   - Images: Gallery scraping

3. **Redfin** (FALLBACK)
   - Coverage: National
   - Reliability: ~50% success rate (session URL issues)
   - Anti-bot: Stealth browser required
   - Fields: Basic listing data
   - Images: CDN with session tokens

4. **Maricopa County Assessor** (COUNTY DATA)
   - Coverage: Maricopa County only
   - Reliability: >99% (API)
   - Fields: Lot, year, garage, sewer, tax
   - Images: None
```

**Acceptance Criteria:**
- [ ] Epic 2 doc updated with E2.R1 completion status
- [ ] Architecture doc updated with PhoenixMLS details
- [ ] README updated with new data source priority
- [ ] CHANGELOG updated with E2.R1 entry

---

## Acceptance Criteria (Overall)

### Functional Acceptance Criteria

- [ ] **AC1:** PhoenixMLSExtractor returns >10 images per property on average
- [ ] **AC2:** All 8 kill-switch fields populated from MLS data (HOA, beds, baths, sqft, lot, garage, sewer, year)
- [ ] **AC3:** All 25 new MLS fields stored in `enrichment_data.json`
- [ ] **AC4:** >90% success rate on test properties (5 sample properties)
- [ ] **AC5:** Unit tests for metadata parser with >90% coverage
- [ ] **AC6:** Integration test with 3 sample properties passes
- [ ] **AC7:** CSV export includes all new MLS fields
- [ ] **AC8:** PhoenixMLS is first priority in extractor chain

### Technical Acceptance Criteria

- [ ] **AC9:** No breaking changes to existing Property API
- [ ] **AC10:** Backward compatibility: old enrichment_data.json still loads
- [ ] **AC11:** All Pydantic validators pass for new fields
- [ ] **AC12:** List fields properly serialized/deserialized (semicolon-delimited)
- [ ] **AC13:** Content-addressed storage integration (hash-based paths)
- [ ] **AC14:** Metadata cached on Property object for enrichment merge
- [ ] **AC15:** All linters pass (ruff, mypy)

### Quality Acceptance Criteria

- [ ] **AC16:** Code coverage >85% for new code
- [ ] **AC17:** No new mypy errors
- [ ] **AC18:** No new ruff violations
- [ ] **AC19:** All tests pass in CI/CD pipeline
- [ ] **AC20:** Documentation updated (4 files)

---

## Additional Context

### Dependencies

**No New Dependencies:**
- Uses existing `BeautifulSoup4` for HTML parsing
- Uses existing `httpx` for HTTP requests
- Uses existing `Pydantic` for validation
- Uses existing `Playwright MCP` for browser automation

### Testing Strategy

**Unit Tests:**
- Metadata parser with mock HTML
- Safe parsing helpers (int/float)
- List field parsing
- Missing field handling

**Integration Tests:**
- Real property extraction (3 samples)
- Orchestrator priority verification
- End-to-end image + metadata extraction

**Manual Testing:**
- Extract 5 sample properties
- Verify all kill-switch fields populated
- Verify new MLS fields in enrichment_data.json
- Verify CSV export includes new columns
- Verify deal sheets render new fields

### Rollback Plan

If PhoenixMLS extraction fails unexpectedly:

1. **Immediate:** Set circuit breaker threshold to disable PhoenixMLS
2. **Short-term:** Revert extractor priority to Zillow-first
3. **Long-term:** Fix PhoenixMLS parser, re-enable with monitoring

### Performance Considerations

**Expected Performance:**
- **Extraction Time:** 5-8 seconds per property (vs 15-20s with Zillow)
- **Success Rate:** >90% (vs 33% with Zillow)
- **Storage Impact:** Same as existing (content-addressed dedup)

**Bottlenecks:**
- HTML parsing (mitigated by caching)
- Network latency (mitigated by httpx connection pooling)

### Security Considerations

**No Security Impact:**
- PhoenixMLS is public data (no authentication)
- No secrets or credentials required
- Standard HTTP requests (no anti-bot bypass)

---

## Notes

### PhoenixMLS HTML Structure

Based on inspection of PhoenixMLS listing pages:

- **MLS Number:** Text node "MLS #: 6789012"
- **Price:** `<span class="listing-price">$475,000</span>`
- **Details Table:** `<table class="property-facts">` with label-value rows
- **Schools:** `<div class="schools-section">` with text like "Elementary: School Name"
- **Features:** `<div class="features-section">` with comma-separated lists

### Image URL Pattern

PhoenixMLS uses SparkPlatform CDN:
- **Thumbnail:** `cdn.photos.sparkplatform.com/az/{id}-t.jpg`
- **Full-size:** `cdn.photos.sparkplatform.com/az/{id}-o.jpg`

Transform thumbnail → full-size by replacing `-t.jpg` with `-o.jpg`

### Kill-Switch Field Mapping

| Kill-Switch Field | MLS Field | Source |
|------------------|-----------|--------|
| HOA Fee | `hoa_fee` | Details table: "HOA Fee" |
| Beds | `beds` | Details table: "Bedrooms" |
| Baths | `baths` | Details table: "Bathrooms" |
| Sqft | `sqft` | Details table: "Square Feet" |
| Lot | `lot_sqft` | Details table: "Lot Size" |
| Garage | `garage_spaces` | Details table: "Garage Spaces" |
| Sewer | `sewer_type` | Details table: "Sewer" |
| Year | `year_built` | Details table: "Year Built" |

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Schema Updates | Tasks 1-3 | 3 hours |
| Phase 2: CSV Repository | Task 4 | 2 hours |
| Phase 3: Extractor Enhancement | Tasks 5-6 | 4 hours |
| Phase 4: Integration & Testing | Tasks 7-9 | 5 hours |
| Phase 5: Documentation | Task 10 | 2 hours |
| **Total** | 10 tasks | **16 hours** |

**Recommended Sprint:** 2 days (8 hours/day) with buffer for testing and debugging

---

## References

- **Epic 2:** `docs/epics/epic-2-property-data-acquisition.md`
- **E2.S4 Spec:** Content-addressed storage implementation
- **PhoenixMLS Extractor:** `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py`
- **Domain Entities:** `src/phx_home_analysis/domain/entities.py`
- **CSV Repository:** `src/phx_home_analysis/repositories/csv_repository.py`
- **Validation Schemas:** `src/phx_home_analysis/validation/schemas.py`

---

**END OF TECH-SPEC**

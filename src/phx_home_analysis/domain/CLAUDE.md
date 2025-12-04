---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# domain

## Purpose

Defines core domain entities (Property, EnrichmentData) and value objects (Address, Score, RiskAssessment) that encapsulate business logic and establish the ubiquitous language for the analysis pipeline. Implements domain-driven design patterns to prevent logic duplication across services.

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Package exports - Property, EnrichmentData, Address, Score, Tier, Orientation, SewerType, SolarStatus, RiskLevel, RiskAssessment, ScoreBreakdown, RenovationEstimate |
| `entities.py` | Core domain entities: Property (150+ fields), EnrichmentData (data transfer object) |
| `enums.py` | Behavioral enums: Tier, Orientation (Arizona-specific), SolarStatus, SewerType, RiskLevel, ImageSource, ImageStatus, FloodZone, CrimeRiskLevel |
| `value_objects.py` | Immutable value objects: Address, Score, ScoreBreakdown, RiskAssessment, RenovationEstimate, PerceptualHash, ImageMetadata |

## Key Entities & Concepts

### Property Entity (entities.py:13-385)
Main aggregate representing a real estate property with 156+ fields spanning listing data, county assessor, enrichment, analysis results, and manual assessments.

**Field Groups:**
- Address (5 fields): street, city, state, zip_code, full_address
- Listing (9 fields): price, price_num, beds, baths, sqft, price_per_sqft_raw, etc.
- County Assessor (5 fields): lot_sqft, year_built, garage_spaces, sewer_type, tax_annual
- Location (7 fields): hoa_fee, school_district, school_rating, orientation, distances, commute
- Arizona-specific (6 fields): solar_status, solar_lease_monthly, has_pool, equipment ages
- Analysis Results (5 fields): kill_switch_passed, failures, score_breakdown, tier, risk_assessments
- Interior Assessment (8 fields): kitchen, master_suite, natural_light, ceilings, fireplace, laundry, aesthetics, backyard
- Location Analysis (30+ fields): crime indices, flood zone, walk/transit/bike scores, noise, zoning, schools, air quality

**Computed Properties:**
- `address` (Address value object)
- `price_per_sqft`, `has_hoa`, `age_years`, `total_score`
- `is_unicorn`, `is_contender`, `is_failed` (tier helpers)
- `total_monthly_cost`, `effective_price`, `high_risks`

### EnrichmentData Entity (entities.py:387-520)
Data transfer object mirroring Property fields, used for loading/merging enrichment from JSON. Does not store computed scores - scores computed fresh at runtime.

### Address Value Object (value_objects.py:12-44)
Immutable address with computed display formats.
- Properties: `full_address`, `short_address`, `__str__`
- Frozen=True for immutability

### Score Value Object (value_objects.py:47-100)
Immutable scoring criterion with validation.
- Fields: criterion (name), base_score (0-10 scale), weight (max pts), note
- Validation: base_score in [0-10], weight >= 0
- Computed: `weighted_score` (base/10 * weight), `percentage`

### ScoreBreakdown Value Object (value_objects.py:138-229)
Immutable aggregation of 600-point scoring system (Location 230, Systems 180, Interior 190).
- Collections: location_scores, systems_scores, interior_scores (list[Score])
- Computed: section totals, total_score (0-600), percentages

### RiskAssessment Value Object (value_objects.py:103-135)
Immutable risk tracking for identified concerns.
- Fields: category, level (RiskLevel enum), description, mitigation
- Properties: score (from level), is_high_risk

### RenovationEstimate Value Object (value_objects.py:232-309)
Immutable renovation cost estimate across 9 categories (cosmetic, kitchen, bathrooms, flooring, HVAC, roof, pool, landscaping, other).
- Validation: All costs >= 0
- Computed: `total`, `major_items` (>$1k sorted)

### PerceptualHash & ImageMetadata (value_objects.py:312-449)
Immutable image tracking for deduplication and metadata.
- PerceptualHash: phash, dhash (64-bit hex), hamming_distance, is_similar_to
- ImageMetadata: image_id, address, source, URL, path, hashes, dimensions, status, timestamps

## Enums with Business Logic

| Enum | Properties | Purpose |
|------|-----------|---------|
| **Tier** | color, label, icon, from_score() | Unicorn (>480), Contender (360-480), Pass (<360), Failed |
| **Orientation** | cooling_cost_multiplier, base_score (0-10 AZ), description | North=10pts (best), West=0pts (worst cooling) |
| **SolarStatus** | is_problematic, description | Owned (asset), Leased (liability), None (no burden) |
| **SewerType** | is_acceptable, description | City=acceptable, Septic=unacceptable for kill-switch |
| **RiskLevel** | score (0-10), css_class, color | HIGH/MEDIUM/LOW/POSITIVE/UNKNOWN |
| **ImageSource** | display_name, base_url, requires_browser, rate_limit | Zillow, Redfin, Assessor, MLS |
| **ImageStatus** | is_terminal, is_success, description | Pipeline state: Pending, Downloading, Processed, Failed |
| **FloodZone** | risk_level, requires_insurance | FEMA zones: X, A, AE, AH, AO, VE |
| **CrimeRiskLevel** | from_index() | LOW, MODERATE, HIGH, VERY_HIGH from indices |

## Architecture Patterns

### Domain-Driven Design
- Entities (Property, EnrichmentData) encapsulate business concepts
- Value objects (Address, Score, RiskAssessment) replace primitives
- Enums carry business logic (Orientation.base_score, SolarStatus.is_problematic)
- Prevent logic duplication across services

### Aggregate Pattern
- Property is aggregate root with owned collections (kill_switch_failures, risk_assessments)
- EnrichmentData is external object, not part of aggregate

### Value Object Immutability
- Address, Score, RiskAssessment, RenovationEstimate, PerceptualHash, ImageMetadata frozen=True
- Enables safe sharing and prevents unintended mutations
- Validates constraints in __post_init__

### Rich Domain Objects
- Computed properties (price_per_sqft, total_monthly_cost, is_unicorn)
- Self-validating (Score raises ValueError on base_score > 10)
- Arizona-specific factors encoded (Orientation scoring, pool costs, HVAC lifespans)

## Learnings

- **Property fields extensive but organized**: 156 lines organized by source (CSV, County Assessor, Phase 1/2/4 enrichment, manual assessment, location analysis)
- **EnrichmentData mirrors Property**: Enables easy merge via field-by-field copy; no computed scores stored
- **Tier classification one-liner**: `Tier.from_score(property.total_score, property.kill_switch_passed)` prevents tier logic duplication
- **Orientation scoring Arizona-specific**: North=10 (best cooling), West=0 (worst); used across services without hardcoding
- **Image deduplication built-in**: PerceptualHash and ImageMetadata enable multi-wave extraction with duplicate detection
- **Enum properties reduce service bloat**: Tier colors/icons, Orientation scoring, SolarStatus rules live in domain not services
- **SolarStatus tracks liability**: Leased solar is burden (2.5pt severity), not asset; factored into cost calculations

## Refs

- Property entity: `entities.py:13-385`
- EnrichmentData entity: `entities.py:387-520`
- Address value object: `value_objects.py:12-44`
- Score value object: `value_objects.py:47-100`
- ScoreBreakdown: `value_objects.py:138-229`
- Tier.from_score(): `enums.py:116-135`
- Orientation.base_score: `enums.py:243-263`
- SolarStatus.is_problematic: `enums.py:146-155`
- Package exports: `__init__.py:1-45`

## Deps

← Imports from:
- Standard library only: dataclasses, enum, typing (no internal imports)

→ Imported by:
- All services: kill_switch, scoring, cost_estimation, quality, lifecycle
- All repositories: csv_repository, json_repository
- All validation and reporters
- Pipeline orchestrator
- Test suite (unit, integration)

---

**Immutability Focus**: All value objects frozen=True (Address, Score, RiskAssessment, RenovationEstimate, PerceptualHash, ImageMetadata) prevent unintended mutations. Entities (Property, EnrichmentData) mutable to allow pipeline processing.

**Package Version**: 1.0.0
**Lines**: 520 total (entities + enums + value_objects)

# BUCKET 2: BUY-BOX CRITERIA - DETAILED ANALYSIS

### Kill-Switch Criteria (Buyer Gatekeeping)

**Architecture**: Two-tier system (HARD + SOFT with severity accumulation)

#### HARD Criteria (Instant Fail)
| Criterion | Requirement | Implementation | Status |
|-----------|-------------|-----------------|--------|
| **HOA** | $0/month | Checks `hoa_fee == 0` | COMPLETE |
| **Bedrooms** | ≥4 | Checks `beds >= 4` | COMPLETE |
| **Bathrooms** | ≥2 | Checks `baths >= 2` | COMPLETE |

**Location**: `scripts/lib/kill_switch.py:116-164` (wrapper) → `src/phx_home_analysis/services/kill_switch/constants.py`

**Notes**:
- Hard failures result in instant FAIL verdict (no severity calculation)
- Boolean logic is clear and unambiguous
- Field mapping: CSV columns to entity attributes

#### SOFT Criteria (Severity Weighted)
| Criterion | Requirement | Severity | Implementation | Status |
|-----------|-------------|----------|-----------------|--------|
| **Sewer** | City (no septic) | 2.5 | Checks `sewer_type == "city"` | COMPLETE |
| **Year Built** | <2024 | 2.0 | Checks `year_built < current_year` | COMPLETE |
| **Garage** | ≥2 spaces | 1.5 | Checks `garage_spaces >= 2` | COMPLETE |
| **Lot Size** | 7k-15k sqft | 1.0 | Checks `7000 <= lot_sqft <= 15000` | COMPLETE |

**Verdict Logic** (from `scripts/lib/kill_switch.py:254-272`):
```
if any HARD fails → FAIL (instant)
else if severity_score >= 3.0 → FAIL
else if severity_score >= 1.5 → WARNING
else → PASS
```

**Example Accumulation**:
- Sewer (2.5) + Year Built (2.0) = 4.5 severity → **FAIL** (exceeds 3.0 threshold)
- Garage (1.5) + Lot Size (1.0) = 2.5 severity → **WARNING** (between 1.5-3.0)
- Garage (1.5) alone = 1.5 severity → **WARNING** (at threshold)
- Garage (1.5) + Lot Size (1.0) but passes garage → **PASS** (0 severity, < 1.5)

**Implementation Quality**: High
- Clear enumeration in `KILL_SWITCH_CRITERIA` dict
- Symmetric handling of missing data (permissive, passes with "Unknown")
- Service layer separation for testability
- Backward compatibility shim in scripts/lib

---

### 600-Point Scoring System

**Structure**: Three weighted sections with 18 sub-criteria

#### SECTION A: LOCATION & ENVIRONMENT (250 pts max)
Reflects vision's "Location" dimension + aspects of "Climate"

| Criterion | Max Pts | Data Source | Vision Coverage | Status |
|-----------|---------|-------------|-----------------|--------|
| School District | 42 | GreatSchools (1-10 → 42pts) | Schools ✓ | COMPLETE |
| Quietness | 30 | Distance to highways (miles) | Commute/vibe ✓ | COMPLETE |
| Crime Index | 47 | BestPlaces/AreaVibes composite | Safety ✓ | COMPLETE |
| Supermarket | 23 | Distance to grocery (miles) | Amenities ✓ | COMPLETE |
| Parks/Walk | 23 | Manual + Walk Score | Amenities ✓ | COMPLETE |
| Sun Orientation | 25 | Satellite imagery (N/E/S/W) | Climate heat ✓ | COMPLETE |
| Flood Risk | 23 | FEMA zones | Flood/heat risk ✓ | COMPLETE |
| Walk/Transit | 22 | Walk Score composite | Commute ✓ | COMPLETE |
| Air Quality | 15 | EPA AirNow AQI | (NEW, not in vision) | ADDED |

**Section A Implementation Quality**: Excellent
- All major vision dimensions covered
- Data sources clearly documented
- Arizona-specific tuning (flood zones, orientation impact)
- Interpretation visible (e.g., W-facing = 0pts vs N-facing = 25pts for cooling costs)

**Missing from Vision for Location**:
- Zoning classification (not captured)
- Growth/development trajectory (not modeled)
- School quality vs proximity tradeoff (only proximity, no trend)

#### SECTION B: LOT & SYSTEMS (170 pts max)
Reflects vision's "Condition" dimension + "Economics" (cost efficiency)

| Criterion | Max Pts | Data Source | Vision Coverage | Status |
|-----------|---------|-------------|-----------------|--------|
| Roof Condition | 45 | Age-based (new/good/fair/aging) | Condition ✓ | COMPLETE |
| Backyard Utility | 35 | Lot sqft - house sqft estimate | Resale outdoor ✓ | COMPLETE |
| Plumbing/Electrical | 35 | Year built inference | Condition ✓ | COMPLETE |
| Pool Condition | 20 | Equipment age (if pool present) | Resale/Condition | COMPLETE |
| Cost Efficiency | 35 | Monthly cost calculation | Economics ✓ | COMPLETE |

**Cost Efficiency Detail** (35 pts):
```
$3,000/mo or less → 35 pts (very affordable)
$3,500/mo → 25.7 pts
$4,000/mo → 17.5 pts (at budget)
$4,500/mo → 8.2 pts (stretching)
$5,000+/mo → 0 pts (exceeds target)
```

Includes:
- Mortgage (7% rate, 30yr, $50k down default)
- Property tax (0.66% effective rate)
- Homeowners insurance ($6.50 per $1k value)
- HOA + Solar lease (if present)
- Pool maintenance ($200-400/mo)
- HVAC/roof replacement reserves
- Utilities ($0.08/sqft + baselines)

**Section B Implementation Quality**: Good
- Clear "bones over cosmetics" approach (age-based, not finish)
- Arizona-specific cost factors included (HVAC 12yr lifespan, pool equipment 8yr)
- Monthly cost captures total ownership burden
- Some estimation required (house sqft from lot, year_built inference)

**Missing from Vision for Condition/Economics**:
- Foundation inspection/concrete slab issues (not scored)
- Plumbing material specifics (copper vs PEX not distinguished)
- Electrical panel capacity (200A assumed, not validated)
- Property tax trends by school district (not differentiated)
- Commute cost not monetized (distance captured, not $ impact on budget)

#### SECTION C: INTERIOR & FEATURES (180 pts max)
Reflects vision's "Condition" (layout) + "Resale" dimensions

| Criterion | Max Pts | Data Source | Vision Coverage | Status |
|-----------|---------|-------------|-----------------|--------|
| Kitchen Layout | 40 | Visual inspection (photos) | Resale/Condition ✓ | PARTIAL |
| Master Suite | 35 | Visual inspection | Condition ✓ | PARTIAL |
| Natural Light | 30 | Visual inspection | Condition ✓ | PARTIAL |
| High Ceilings | 25 | Visual/description data | Resale ✓ | PARTIAL |
| Fireplace | 20 | Presence + type (gas/wood) | Resale minor | PARTIAL |
| Laundry Area | 20 | Location + quality | Condition ✓ | PARTIAL |
| Aesthetics | 10 | Curb appeal + finishes | Resale ✓ | PARTIAL |

**Section C Implementation Status**: PARTIAL
- **Scoring logic defined** in `scoring_weights.py` with rubrics
- **Data capture relies on image assessment agent** (Phase 2, manual visual scoring)
- **Not all properties have photo data** in Phase 1 (extraction incomplete in many cases)
- **Requires Phase 2 image-assessor agent** to populate scores
- Default to neutral (5-10pt range) when data missing

**Missing from Vision for Interior/Resale**:
- Garage quality/climate control (not in interior section, barely in kill-switch)
- Outdoor living spaces detail (pool present, but patio quality not scored)
- Storage capacity (laundry area captured, but general storage not)
- Parking spaces beyond garage (not modeled)
- Energy efficiency/modern systems (implicit in age, not explicit)
- Layout flow/floor plan quality (only kitchen, master captured)

---

# 3. Scoring Weight Updates

### 3.1 Current Scoring Configuration

**Source:** `src/phx_home_analysis/config/scoring_weights.py`

```python
# Current Section A: Location & Environment (250 pts)
school_district: int = 42
quietness: int = 30
crime_index: int = 47
supermarket_proximity: int = 23
parks_walkability: int = 23
sun_orientation: int = 25
flood_risk: int = 23
walk_transit: int = 22
air_quality: int = 15
# TOTAL: 250 pts

# Current Section B: Lot & Systems (170 pts)
roof_condition: int = 45
backyard_utility: int = 35
plumbing_electrical: int = 35
pool_condition: int = 20
cost_efficiency: int = 35
# TOTAL: 170 pts

# Current Section C: Interior & Features (180 pts)
kitchen_layout: int = 40
master_suite: int = 35
natural_light: int = 30
high_ceilings: int = 25
fireplace: int = 20
laundry_area: int = 20
aesthetics: int = 10
# TOTAL: 180 pts

# GRAND TOTAL: 600 pts
```

### 3.2 Section A: Location (250 pts -> 225 pts)

#### Proposed Changes

To accommodate the new HVAC scoring criterion (25 pts) in Section B, Section A is reduced by 25 pts across lower-priority criteria:

| Criterion | Current | Proposed | Delta | Rationale |
|-----------|---------|----------|-------|-----------|
| school_district | 42 | 42 | 0 | High priority - GreatSchools rating critical |
| quietness | 30 | 25 | -5 | Still important but less than safety |
| crime_index | 47 | 47 | 0 | High priority - safety is paramount |
| supermarket_proximity | 23 | 18 | -5 | Convenience factor, car-dependent area |
| parks_walkability | 23 | 18 | -5 | Convenience factor, less critical |
| sun_orientation | 25 | 25 | 0 | Critical for AZ cooling costs |
| flood_risk | 23 | 18 | -5 | Most Phoenix properties Zone X |
| walk_transit | 22 | 17 | -5 | Phoenix is car-dependent |
| air_quality | 15 | 15 | 0 | Keep as baseline |
| **TOTAL** | **250** | **225** | **-25** | |

```python
# PROPOSED Section A Updates in scoring_weights.py

# SECTION A: LOCATION & ENVIRONMENT (225 pts - reduced from 250)
school_district: int = 42    # Unchanged - high priority
quietness: int = 25          # Reduced from 30 (-5) - still important
crime_index: int = 47        # Unchanged - safety paramount
supermarket_proximity: int = 18  # Reduced from 23 (-5) - convenience
parks_walkability: int = 18  # Reduced from 23 (-5) - convenience
sun_orientation: int = 25    # Unchanged - critical for AZ
flood_risk: int = 18         # Reduced from 23 (-5) - most are Zone X
walk_transit: int = 17       # Reduced from 22 (-5) - car-dependent area
air_quality: int = 15        # Unchanged - baseline health factor
```

### 3.3 Section B: Lot & Systems (170 pts -> 195 pts)

#### New Criterion: HVAC Condition (25 pts)

```python
# CHANGE: Add HVAC Condition scoring (25 pts max)
# RATIONALE: Domain-Alpha Building Systems Research shows:
#   - Arizona HVAC lifespan: 8-15 years (not 20+ years nationally)
#   - Replacement cost: $11,000-$26,000 for full system
#   - Arizona heat (115F+ summers) accelerates wear
#   - Efficiency degradation significant after 10 years

# BEFORE:
# No explicit HVAC scoring criterion

# AFTER:
# Add hvac_condition: int = 25 to Section B

"""
hvac_condition (25 pts max):
    HVAC system age and condition assessment
    Arizona-specific: Systems degrade faster due to extreme heat

    Scoring logic:
        - New/Recent (0-5 years): 25 pts - Full efficiency, no concerns
        - Good (6-10 years): 20 pts - Normal wear, 5+ years remaining
        - Aging (11-15 years): 12 pts - Approaching replacement window
        - End-of-life (16+ years): 5 pts - Replacement likely needed soon
        - Unknown: 12.5 pts (neutral)

    Data source: Listing description, county records, visual inspection
    Research basis: Domain-Alpha Building Systems (HVAC lifespan 8-15 years in AZ)

    Note: Score assumes original HVAC unless replacement documented.
    Age calculated as: current_year - hvac_install_year (or year_built if unknown)
"""
```

#### Proposed Section B Configuration

| Criterion | Current | Proposed | Delta | Rationale |
|-----------|---------|----------|-------|-----------|
| roof_condition | 45 | 45 | 0 | Critical - expensive replacement |
| backyard_utility | 35 | 35 | 0 | Important for AZ outdoor living |
| plumbing_electrical | 35 | 35 | 0 | Infrastructure assessment |
| pool_condition | 20 | 20 | 0 | Equipment concerns in AZ heat |
| cost_efficiency | 35 | 35 | 0 | Critical for budget adherence |
| **hvac_condition** | **0** | **25** | **+25** | **NEW: Critical for AZ** |
| **TOTAL** | **170** | **195** | **+25** | |

```python
# PROPOSED Section B in scoring_weights.py

# SECTION B: LOT & SYSTEMS (195 pts - increased from 170)
roof_condition: int = 45        # Unchanged - critical infrastructure
backyard_utility: int = 35      # Unchanged - AZ outdoor living
plumbing_electrical: int = 35   # Unchanged - infrastructure
pool_condition: int = 20        # Unchanged - AZ-specific concern
cost_efficiency: int = 35       # Unchanged - budget critical
hvac_condition: int = 25        # NEW - Arizona HVAC lifespan 8-15 years
```

### 3.4 Section C: Interior (180 pts - Unchanged)

No changes proposed for Section C. Interior scoring criteria remain appropriate.

```python
# SECTION C: INTERIOR & FEATURES (180 pts - unchanged)
kitchen_layout: int = 40
master_suite: int = 35
natural_light: int = 30
high_ceilings: int = 25
fireplace: int = 20
laundry_area: int = 20
aesthetics: int = 10
```

### 3.5 Point Reallocation Summary

| Section | Current | Proposed | Delta |
|---------|---------|----------|-------|
| **A: Location & Environment** | 250 | 225 | -25 |
| **B: Lot & Systems** | 170 | 195 | +25 |
| **C: Interior & Features** | 180 | 180 | 0 |
| **GRAND TOTAL** | **600** | **600** | **0** |

**Verification:** 225 + 195 + 180 = 600 (correct)

---

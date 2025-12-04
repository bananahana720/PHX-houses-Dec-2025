# 2. CONFIGURATION VALUES

### Kill Switch Criteria

**Defined in:** `phx_home_analyzer.py` (lines 83-91), `deal_sheets.py` (lines 15-51)

| Criterion | Field | Threshold | Description |
|-----------|-------|-----------|-------------|
| HOA | `hoa_fee` | == 0 or None | Must be NO HOA |
| Sewer | `sewer_type` | == "city" or None | Must be City Sewer |
| Garage | `garage_spaces` | >= 2 or None | Minimum 2-Car Garage |
| Beds | `beds` | >= 4 | Minimum 4 Bedrooms |
| Baths | `baths` | >= 2 | Minimum 2 Bathrooms |
| Lot Size | `lot_sqft` | 7000-15000 or None | Lot 7,000-15,000 sqft |
| Year Built | `year_built` | < 2024 or None | No New Builds |

**Duplication:** Kill switch definitions exist in TWO files with different implementations

### Scoring Weights

**Defined in:** `phx_home_analyzer.py` (lines 271-297)

#### Section A: Location & Environment (150 points)
- School District Rating: 5 × 10 = 50 pts
- Quietness/Noise: 5 × 10 = 50 pts
- Safety/Neighborhood: 5 × 10 = 50 pts
- Supermarket Proximity: 4 × 10 = 40 pts
- Walkability: 3 × 10 = 30 pts
- Sun Orientation: 3 × 10 = 30 pts

#### Section B: Lot & Systems (160 points)
- Roof Condition: 5 × 10 = 50 pts
- Backyard Utility: 4 × 10 = 40 pts
- Plumbing/Electrical: 4 × 10 = 40 pts
- Pool Condition: 3 × 10 = 30 pts

#### Section C: Interior & Features (190 points)
- Kitchen Layout: 4 × 10 = 40 pts
- Master Suite: 4 × 10 = 40 pts
- Natural Light: 3 × 10 = 30 pts
- High Ceilings: 3 × 10 = 30 pts
- Fireplace: 2 × 10 = 20 pts
- Laundry Area: 2 × 10 = 20 pts
- Aesthetics: 1 × 10 = 10 pts

**Total:** 500 points

### Tier Thresholds

**Defined in:** `phx_home_analyzer.py` (lines 312-317)

| Tier | Score Range |
|------|-------------|
| Unicorn | > 400 points |
| Contender | 300-400 points |
| Pass | < 300 points |

### Renovation Cost Estimates

**Defined in:** `renovation_gap.py` (lines 20-78)

#### Roof Costs (lines 20-31)
```python
roof_age < 10:        $0
roof_age <= 15:       $5,000
roof_age <= 20:       $10,000
roof_age > 20:        $18,000
roof_age unknown:     $8,000
```

#### HVAC Costs (lines 34-43)
```python
hvac_age < 8:         $0
hvac_age <= 12:       $3,000
hvac_age > 12:        $8,000
hvac_age unknown:     $4,000
```

#### Pool Costs (lines 46-58)
```python
no pool:              $0
pool_age < 5:         $0
pool_age <= 10:       $3,000
pool_age > 10:        $8,000
pool_age unknown:     $5,000
```

#### Plumbing Costs (lines 61-70)
```python
year_built >= 2000:   $0
year_built >= 1990:   $2,000
year_built >= 1980:   $5,000
year_built < 1980:    $10,000
```

#### Kitchen Costs (lines 73-78)
```python
year_built < 1990 AND score_interior ≈ 95.0:  $15,000
otherwise:                                      $0
```

### Risk Categories

**Defined in:** `risk_report.py` (lines 44-151)

#### Noise Risk (Highway Distance)
```python
< 0.5 miles:  HIGH
0.5-1.0 mi:   MEDIUM
> 1.0 mi:     LOW
```

#### Infrastructure Risk (Year Built)
```python
< 1970:       HIGH
1970-1989:    MEDIUM
>= 1990:      LOW
```

#### Solar Risk (Ownership)
```python
"leased":     HIGH
"owned":      POSITIVE
"none":       LOW
```

#### Cooling Risk (Orientation)
```python
W, SW:        HIGH
S, SE:        MEDIUM
N, NE, NW, E: LOW
```

#### School Risk (GreatSchools Rating)
```python
< 6.0:        HIGH
6.0-7.5:      MEDIUM
> 7.5:        LOW
```

#### Lot Size Risk
```python
< 7,500 sqft: MEDIUM
>= 7,500:     LOW
```

### Risk Scoring

**Defined in:** `risk_report.py` (lines 36-41)

```python
HIGH:     3 points
MEDIUM:   1 point
UNKNOWN:  1 point
LOW:      0 points
POSITIVE: 0 points
```

### Sun Orientation Cooling Costs

**Defined in:** `sun_orientation_analysis.py` (lines 20-30)

Annual cooling cost impact by orientation:
```python
'N':   $0      (Best - baseline)
'NE':  $100
'E':   $200
'SE':  $400
'S':   $300
'SW':  $400
'W':   $600    (Worst)
'NW':  $100
'Unknown': $250
```

### Value Zone Boundaries

**Defined in:** `value_spotter.py` (lines 45-46)

```python
value_zone_min_score = 365
value_zone_max_price = 550000
```

### Map Configuration

**Defined in:** `golden_zone_map.py` (lines 18-26)

```python
PHOENIX_CENTER = (33.55, -112.05)
ZOOM_LEVEL = 10
GROCERY_RADIUS_MILES = 1.5
HIGHWAY_BUFFER_MILES = 1.0
MILES_TO_METERS = 1609.34
```

### Highway Coordinates

**Defined in:** `golden_zone_map.py` (lines 29-54)

Hardcoded lat/long for I-17, I-10, Loop-101 (36 coordinate pairs)

### Geocoding Rate Limit

**Defined in:** `geocode_homes.py` (line 152)

```python
rate_limit_delay=1.0  # seconds between requests
```

---

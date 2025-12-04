# Scoring System Architecture

### 605-Point Weighted System

**AUTHORITATIVE SOURCE:** `src/phx_home_analysis/config/scoring_weights.py`

#### Section A: Location & Environment (250 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| school_district | 42 pts | GreatSchools rating x 4.2 |
| quietness | 30 pts | Distance to highways (>2mi=30, <0.25mi=0) |
| crime_index | 47 pts | 60% violent + 40% property crime (0-100 scale / 2.13) |
| supermarket_proximity | 23 pts | Distance to grocery (<0.5mi=23, >3mi=2.8) |
| parks_walkability | 23 pts | Parks, sidewalks, trails (manual 0-10 x 2.3) |
| sun_orientation | 25 pts | N=25, E=18.75, S=12.5, W=0 |
| flood_risk | 23 pts | Zone X=23, X-Shaded=18.4, A/AE=4.6-6.9, VE=0 |
| walk_transit | 22 pts | 40% walk + 40% transit + 20% bike (0-100 / 4.5) |
| air_quality | 15 pts | AQI 0-50=15, 51-100=12, 101-150=7.5, 151+=1.5-4.5 |

#### Section B: Lot & Systems (175 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| roof_condition | 45 pts | Age: 0-5yr=45, 6-10=36, 11-15=22.5, 16-20=9, >20=0 |
| backyard_utility | 35 pts | Usable sqft: >4k=35, 2-4k=26.25, 1-2k=17.5, <1k=8.75 |
| plumbing_electrical | 35 pts | Year: 2010+=35, 2000-09=30.6, 90-99=21.9, 80-89=13.1, <80=4.4 |
| pool_condition | 20 pts | No pool=10, Equip 0-3yr=20, 4-7=17, 8-12=10, >12=3 |
| cost_efficiency | 35 pts | Monthly: <=$3k=35, $3.5k=25.7, $4k=17.5, $4.5k=8.2, >$5k=0 |
| solar_status | 5 pts | Owned=5, Loan=3, None=2.5, Unknown=2, Leased=0 |

#### Section C: Interior & Features (180 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| kitchen_layout | 40 pts | Visual: open concept, island, appliances, pantry (0-10 x 4) |
| master_suite | 35 pts | Visual: size, closet, bathroom quality (0-10 x 3.5) |
| natural_light | 30 pts | Visual: windows, skylights, brightness (0-10 x 3) |
| high_ceilings | 25 pts | Vaulted=25, 10ft+=20.8, 9ft=12.5, 8ft=8.3, <8ft=0 |
| fireplace | 20 pts | Gas=20, Wood=15, Decorative=5, None=0 |
| laundry_area | 20 pts | Dedicated upstairs=20, Any floor=15, Closet=10, Garage=5, None=0 |
| aesthetics | 10 pts | Visual: curb appeal, finishes, modern vs dated (0-10) |

### Tier Classification (Updated)

```python
class TierClassifier:
    """Classify properties into tiers based on 605-point scale."""

    UNICORN_THRESHOLD = 484    # 80% of 605
    CONTENDER_THRESHOLD = 363  # 60% of 605

    def classify(self, total_score: float) -> Tier:
        if total_score > self.UNICORN_THRESHOLD:
            return Tier.UNICORN
        elif total_score >= self.CONTENDER_THRESHOLD:
            return Tier.CONTENDER
        else:
            return Tier.PASS
```

---

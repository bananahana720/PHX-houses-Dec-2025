---
name: arizona-context
description: Arizona-specific real estate considerations including solar leases, pool economics, sun orientation, HVAC lifespans, and desert climate impacts. Use when evaluating AZ properties, estimating costs, or understanding regional factors.
allowed-tools: Read
---

# Arizona Real Estate Context Skill

Expert at Arizona-specific property evaluation factors that differ significantly from other markets.

## Sun Orientation (Critical for AZ)

### Scoring Impact

| Orientation | Summer Impact | Cooling Cost | Score |
|-------------|---------------|--------------|-------|
| **North** | Minimal direct | Lowest | 30/30 |
| **Northeast** | Morning only | Low | 25/30 |
| **East** | AM exposure | Moderate-Low | 20/30 |
| **Northwest** | Some PM | Moderate | 25/30 |
| **South** | Moderate all-day | Moderate | 10/30 |
| **Southeast** | AM + midday | Moderate-High | 5/30 |
| **Southwest** | Brutal PM | High | 5/30 |
| **West** | Brutal PM | Highest | 0/30 |

### Why It Matters

- **West-facing**: 20-30% higher summer cooling bills
- **Afternoon sun**: Peak rates (3-8 PM) = most expensive electricity
- **Morning sun**: Off-peak rates, manageable heat gain
- **Window exposure**: West windows without shade = major cost driver

### Assessment Checklist

- [ ] Front door orientation
- [ ] Primary living room window direction
- [ ] Master bedroom window direction
- [ ] Pool location relative to afternoon sun
- [ ] Covered patio orientation

## Solar Panel Economics

### Ownership Status

| Status | Monthly Impact | Transfer Risk | Score Impact |
|--------|----------------|---------------|--------------|
| **Owned** | -$100-200 savings | None | +10 pts |
| **Leased** | +$100-200 cost | HIGH | -20 pts |
| **None** | $0 | None | 0 pts |

### Leased Solar Red Flags

```
WARNING: Solar lease transfers can:
- Require buyer credit approval
- Add $15-25k balloon to close
- Monthly payment escalators (2-3%/year)
- 20-year commitment inherited
- Roof replacement complications
```

### Questions to Ask

1. Is the system owned or leased?
2. If leased, who is the lessor? (Vivint, SunRun, Tesla)
3. What is the monthly payment?
4. What is the escalation rate?
5. How many years remain on lease?
6. Is there a buyout option? At what price?

### Cost Model

```python
def calculate_solar_impact(status: str, lease_monthly: float = 0, years_remaining: int = 0) -> dict:
    """Calculate solar panel financial impact."""
    if status == "owned":
        return {
            "monthly_savings": 150,  # Average AZ
            "total_value_add": 15000,
            "risk": "none"
        }
    elif status == "leased":
        escalator = 1.025  # 2.5%/year typical
        total_payments = sum(
            lease_monthly * (escalator ** year) * 12
            for year in range(years_remaining)
        )
        return {
            "monthly_cost": lease_monthly,
            "total_liability": total_payments,
            "risk": "high",
            "transfer_risk": "credit_check_required"
        }
    return {"monthly_savings": 0, "risk": "none"}
```

### Solar Lease Evaluation Decision Tree

When evaluating a property with solar panels, follow this chain-of-thought process:

```
1. OWNERSHIP DETERMINATION
   └─ Is system owned or leased?
      ├─ OWNED → Value-add (+10 pts), proceed to Step 4
      ├─ LEASED → Continue to Step 2
      └─ UNKNOWN → Research required (ask listing agent), assume LEASED for scoring

2. LEASE LIABILITY ASSESSMENT (if leased)
   └─ Calculate total remaining liability:
      remaining_years × monthly_payment × (1 + escalator)^avg_year
   └─ Example: 15 years × $175/mo × 1.025^7.5 = ~$38,500 liability

3. TRANSFER RISK EVALUATION (if leased)
   └─ Check lessor reputation:
      ├─ SunRun/Vivint → Moderate difficulty, credit check required
      ├─ Tesla/SolarCity → Variable, may require negotiation
      └─ Small/unknown lessor → HIGH RISK, may block sale
   └─ Check buyer qualification:
      └─ If lease payment > $200/mo → May affect DTI ratio

4. FINAL SCORING
   └─ OWNED: +10 pts (asset)
   └─ LEASED (good terms): -10 pts (minor liability)
   └─ LEASED (bad terms): -20 pts (significant liability)
   └─ LEASED (transfer risk): -30 pts + flag for buyer review
```

**Decision Output Format:**
```json
{
  "solar_status": "leased|owned|none",
  "score_impact": -20,
  "reasoning": "Leased system with 15yr remaining, $175/mo + 2.5% escalator = ~$38k liability",
  "transfer_risk": "moderate",
  "action_required": "Verify buyer can assume lease, request payoff quote"
}
```

## Pool Economics (AZ-Specific)

### Monthly Costs

| Category | Low | Average | High |
|----------|-----|---------|------|
| Service | $80 | $125 | $200 |
| Chemicals | $30 | $50 | $80 |
| Electricity | $40 | $75 | $120 |
| **Monthly Total** | $150 | $250 | $400 |

### Equipment Replacement

| Component | Lifespan | Replacement Cost |
|-----------|----------|------------------|
| Pool pump | 8-12 years | $800-2,000 |
| Filter | 5-10 years | $500-1,500 |
| Heater | 5-10 years | $2,000-5,000 |
| Salt cell | 3-7 years | $500-1,000 |
| Resurface | 10-15 years | $5,000-15,000 |

### Pool Age Assessment

```python
def score_pool_equipment(has_pool: bool, equipment_age: int | None) -> tuple[int, str]:
    """Score pool based on equipment age.

    Returns:
        (score, notes) tuple
    """
    if not has_pool:
        return 10, "No pool (lower maintenance)"

    if equipment_age is None:
        return 5, "Pool present, equipment age unknown"

    if equipment_age <= 3:
        return 10, f"Pool with new equipment ({equipment_age}yr)"
    elif equipment_age <= 7:
        return 7, f"Pool equipment moderate age ({equipment_age}yr)"
    elif equipment_age <= 12:
        return 4, f"Pool equipment aging ({equipment_age}yr) - budget $3-5k"
    else:
        return 2, f"Pool equipment old ({equipment_age}yr) - budget $8-15k"
```

### Pool Value Decision Logic

Evaluate whether pool is net positive or negative for the buyer:

```
1. BUYER PREFERENCE CHECK
   └─ Does buyer want pool?
      ├─ YES (explicitly) → Pool is positive factor
      ├─ NO (explicitly) → Pool is NEGATIVE (deduct $5-10k value)
      └─ NEUTRAL → Continue to economic analysis

2. EQUIPMENT AGE ASSESSMENT
   └─ Equipment age known?
      ├─ ≤5 years → Minor ongoing costs ($200-250/mo)
      ├─ 5-10 years → Moderate costs + $3-5k budget next 3yr
      ├─> 10 years → High risk, budget $8-15k next 2yr
      └─ UNKNOWN → Assume 10 years, flag for inspection

3. NET VALUE CALCULATION
   └─ Pool adds value IF:
      - Equipment < 5 years old AND
      - Buyer wants pool AND
      - Property priced < $500k (pool is expected amenity at higher prices)
   └─ Pool subtracts value IF:
      - Equipment > 10 years (immediate $8-15k expense)
      - Buyer doesn't want pool
      - Monthly costs push total payment over budget

4. SCORING ADJUSTMENT
   └─ New equipment + wanted: +15 pts
   └─ Moderate equipment + wanted: +5 pts
   └─ Old equipment OR unwanted: 0 pts (neutral)
   └─ Old equipment + unwanted: -10 pts
```

**Buyer Assumption (PHX Houses Project):**
This buyer is NEUTRAL on pools. Score pools based purely on economic impact:
- New equipment (≤5yr): +5 pts (low maintenance burden)
- Moderate (5-10yr): 0 pts (neutral)
- Old (>10yr): -5 pts (liability)
- No pool: +10 pts (lower monthly costs)

## HVAC Considerations

### Arizona HVAC Lifespan

| Component | National Avg | Arizona Avg | Notes |
|-----------|--------------|-------------|-------|
| AC unit | 15-20 years | 10-15 years | Extreme heat stress |
| Furnace | 20-25 years | 15-20 years | Less critical in AZ |
| Ductwork | 20-25 years | 15-20 years | Heat degradation |

### HVAC Red Flags

- Units older than 12 years in AZ
- Single-zone in 2-story homes
- Undersized for square footage (3+ ton for 2000+ sqft)
- R-22 refrigerant systems (phase-out)

### Assessment

```python
def assess_hvac_risk(year_built: int, hvac_age: int | None) -> dict:
    """Assess HVAC replacement risk."""
    if hvac_age is None:
        # Estimate from year built
        hvac_age = 2024 - year_built if year_built else 15

    if hvac_age <= 5:
        return {"risk": "low", "budget": 0, "years_remaining": 10}
    elif hvac_age <= 10:
        return {"risk": "moderate", "budget": 3000, "years_remaining": 5}
    elif hvac_age <= 15:
        return {"risk": "high", "budget": 8000, "years_remaining": 2}
    else:
        return {"risk": "critical", "budget": 12000, "years_remaining": 0}
```

### HVAC Age Estimation Fallback

When hvac_age is unknown, use this estimation protocol:

```
1. CHECK DATA SOURCES IN ORDER
   ├─ Listing mentions "new HVAC" → Age = 1-3 years
   ├─ Listing mentions "updated HVAC" → Age = 3-7 years
   ├─ County assessor records → Check permit history
   ├─ Photos show unit → Visual age estimation
   └─ None available → Derive from year_built

2. YEAR_BUILT DERIVATION (fallback)
   └─ Default assumption: HVAC replaced every 12-15 years in AZ

   year_built_age = 2025 - year_built

   if year_built_age <= 15:
       estimated_hvac_age = year_built_age  # Original
   elif year_built_age <= 30:
       estimated_hvac_age = year_built_age - 15  # One replacement
   else:
       estimated_hvac_age = year_built_age % 15  # Multiple replacements

   # Apply Arizona degradation factor
   confidence = "low" if no visual/listing confirmation

3. VISUAL ESTIMATION FROM PHOTOS
   └─ Unit visible? Look for:
      - Rust/weathering → 10+ years
      - Clean housing, modern controls → 5-10 years
      - Brand visible (Trane, Carrier recent models) → 0-5 years

4. OUTPUT FORMAT
   {
     "hvac_age": 12,
     "estimation_method": "year_built_derivation",
     "confidence": "low",
     "reasoning": "Built 1998 (27yr), assume one replacement at ~15yr mark",
     "recommendation": "Request service records or inspection"
   }
```

**When to Flag for Research:**
- Unicorn candidate with unknown HVAC → MUST research before finalizing tier
- Contender with unknown HVAC → Research if otherwise strong
- Pass tier → OK to use estimation

**Integration with estimate_ages.py:**
```bash
# When manual research needed:
python scripts/estimate_ages.py --property "{address}" --field hvac_age
```

## Roof Considerations

### Arizona Roof Types

| Type | Lifespan (AZ) | Cost/sqft | Best For |
|------|---------------|-----------|----------|
| Tile | 30-50 years | $8-15 | Most homes |
| Shingle | 15-20 years | $4-7 | Budget |
| Foam | 15-20 years | $5-8 | Flat roofs |
| Metal | 40-60 years | $10-18 | Durability |

### UV/Heat Impact

- Arizona sun degrades roofing 30-40% faster than national average
- Tile underlayment fails even if tiles look fine
- Shingles crack and curl in extreme heat
- Foam roofs need recoating every 5-7 years

## Monsoon/Flood Considerations

### Risk Zones

- **Zone A/AE**: High flood risk, flood insurance required
- **Zone X**: Moderate/minimal risk
- **Zone D**: Undetermined

### Monsoon Damage Patterns

- Wash/drainage proximity
- Slope direction (water flow)
- Roof drainage capacity
- Foundation settling from soil expansion/contraction

## Cost Summary Card

```
ARIZONA PROPERTY HIDDEN COSTS
=============================
Pool (if present):        $250-400/month
Solar Lease (if leased):  $100-200/month
Higher AC bills:          $200-400/month (summer)
HVAC replacement:         $8-15k every 12-15 years
Roof replacement:         $10-25k every 20-30 years
Landscaping (desert):     $50-150/month

ORIENTATION PENALTY (West-facing):
- +20-30% cooling costs
- Estimated: $50-100/month extra
```

## Phoenix Cost Baseline Example

**Reference Property: Typical 4bed/2bath in 85032 (Paradise Valley Village)**

### Monthly Operating Costs
| Category | Summer | Winter | Annual Avg |
|----------|--------|--------|------------|
| **Electricity** | $350 | $120 | $220 |
| **Water** | $80 | $60 | $70 |
| **Gas** | $30 | $60 | $45 |
| **Trash/Recycling** | $30 | $30 | $30 |
| **Landscaping** | $100 | $100 | $100 |
| **TOTAL UTILITIES** | **$590** | **$370** | **$465** |

### Impact Modifiers
| Factor | Monthly Impact | Notes |
|--------|----------------|-------|
| West-facing | +$50-100 | Peak cooling load |
| Pool present | +$200-300 | Service + chemicals + energy |
| Solar owned | -$100-150 | Offsets peak rates |
| Solar leased | +$150-200 | Additional monthly burden |
| Oversized lot (10k+) | +$50 | Extra landscaping |
| Poor insulation (pre-1990) | +$50-100 | HVAC works harder |

### Annual Reserve Budget
| Item | Annual Reserve | 10-Year Budget |
|------|----------------|----------------|
| HVAC maintenance | $300 | N/A |
| HVAC replacement | $800 | $8,000 |
| Roof maintenance | $200 | N/A |
| Roof replacement | $1,500 | $15,000 |
| Plumbing repairs | $200 | $2,000 |
| Pool equipment | $500 | $5,000 (if pool) |
| **TOTAL RESERVE** | **$3,500/yr** | **$35,000** |

**Use this baseline when:**
- Estimating total monthly costs for deal sheets
- Comparing properties (add/subtract modifiers)
- Setting buyer expectations for hidden costs

## Best Practices

1. **Always check orientation** - West-facing is major cost driver
2. **Solar ownership verification** - Leases are liabilities, not assets
3. **Pool equipment inspection** - Age determines near-term costs
4. **HVAC age priority** - 12+ year systems need replacement budgeting
5. **Roof underlayment** - Tile roofs hide underlayment failure

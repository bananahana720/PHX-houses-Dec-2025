# Architecture Quick Reference
## PHX Houses Analysis Pipeline

**Last Updated**: December 3, 2025
**For Details**: See CROSS_CUTTING_ANALYSIS.md

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ANALYSIS PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: County Data    Phase 1a: Images    Phase 1b: Maps │
│  (extract_county_data)   (image-browser)     (map-analyzer)  │
│         │                      │                   │         │
│         └──────────────────────┴───────────────────┘         │
│                       │                                      │
│                  Phase 2: Assessment                         │
│                  (image-assessor)                            │
│                       │                                      │
│                  Phase 3: Scoring                            │
│                  (phx_home_analyzer)                         │
│                       │                                      │
│                  Phase 4: Reports                            │
│                  (generate_all_reports)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘

State: work_items.json (per-property progress)
Data:  enrichment_data.json (property fields)
Config: constants.py (scoring weights, kill-switch criteria)
```

---

## Data Model

### Property Lifecycle

```
CSV Listing
    ↓
[Property entity with: address, beds, baths, sqft, price]
    ↓
Enrich with: county_data, images, location_scores
    ↓
Kill-Switch Filter
    ├─ HARD: HOA=0, beds≥4, baths≥2
    └─ SOFT: sewer, garage, lot, year (severity weighted)
    ↓
Score (600 pts max)
    ├─ Location (230 pts): schools, safety, orientation, quietness
    ├─ Systems (180 pts): roof, plumbing, pool, cost
    └─ Interior (190 pts): kitchen, master, light, ceilings
    ↓
Classify Tier
    ├─ Unicorn: >480 pts
    ├─ Contender: 360-480 pts
    └─ Pass: <360 pts
```

---

## Traceability Matrix

### What Can Be Traced Today?

| Level | Entity | Trackable | Missing |
|-------|--------|-----------|---------|
| **Property** | Address | ✅ Full sequence | Backwards: links to fields |
| **Field** | lot_sqft | ❌ Only _last_updated | Source, confidence, version |
| **Phase** | phase1_map | ✅ Status, timestamp | Duration, errors, logs |
| **Score** | total_score=425 | ❌ Only final number | Per-strategy contribution |
| **Decision** | Kill-switch FAIL | ❌ Only verdict | Severity breakdown, severity_total |
| **Data** | enrichment_data.json | ✅ Last modified time | Lineage per field |

### Current Traceability Gaps

```
Property A (123 Main St)
├─ enrichment_data.json
│  ├─ lot_sqft: 9387
│  │  └─ ? Where from? (County? Zillow? Manual?)
│  ├─ orientation: south
│  │  └─ ? Who assessed? (Script? Human? When?)
│  └─ _last_updated: 2025-12-03
│     └─ ? What changed since last update?
│
├─ work_items.json
│  ├─ phase0_county: completed
│  │  └─ ? What data was extracted? Duration? Errors?
│  └─ phase1_map: completed
│     └─ ? Completed by which agent? How long?
│
└─ Scoring Result: 425 points
   ├─ ? Which strategies contributed?
   ├─ ? How did school rating (8/10) convert to points?
   └─ ? How much did orientation impact score?
```

---

## Kill-Switch Criteria

### Hard Criteria (Instant Fail)

| Criterion | Requirement | Example Failure |
|-----------|-------------|-----------------|
| NO HOA | hoa_fee = 0 | Property with $150/month HOA → FAIL |
| Min Beds | beds ≥ 4 | 3-bed property → FAIL |
| Min Baths | baths ≥ 2 | 1.5-bath property → FAIL |

### Soft Criteria (Severity Accumulation)

| Criterion | Requirement | Severity | Example |
|-----------|-------------|----------|---------|
| City Sewer | sewer_type = "city" | 2.5 | Septic → +2.5 severity |
| Year Built | year_built < 2024 | 2.0 | Built 2023 → +2.0 severity |
| Garage Spaces | spaces ≥ 2 | 1.5 | 1-car garage → +1.5 severity |
| Lot Size | 7,000 - 15,000 sqft | 1.0 | 20,000 sqft → +1.0 severity |

**Verdict Logic:**
- Total severity ≥ 3.0 → FAIL
- 1.5 ≤ severity < 3.0 → WARNING
- severity < 1.5 → PASS

### Example Verdict Calculation

```
Property: 123 Main St

Soft Criteria Check:
├─ Sewer: Septic (not city) → severity +2.5
├─ Year: 1983 (before 2024) → severity +2.0
├─ Garage: 1 space (need 2) → severity +1.5
└─ Lot: 9,387 sqft (within 7k-15k) → severity 0

TOTAL SEVERITY: 6.0
FAIL THRESHOLD: 3.0
VERDICT: FAIL (severity 6.0 > threshold 3.0)
```

---

## Scoring System (600 Points)

### Section A: Location & Environment (230 pts)

| Subsection | Points | Input | Example |
|-----------|--------|-------|---------|
| School District | 45 | GreatSchools 1-10 | Rating 8 = 36 pts |
| Quietness | 30 | Distance to highway | 2+ miles = 30 pts |
| Safety | 50 | Crime index 0-100 | Index 80 = 40 pts |
| Supermarket | 25 | Distance (miles) | < 0.5 miles = 25 pts |
| Parks | 25 | Walkability score | High access = 25 pts |
| Orientation | 25 | N/S/E/W direction | North = 25 pts, West = 0 pts |
| Flood Risk | 25 | FEMA flood zone | Zone X = 25 pts |

### Section B: Lot & Systems (180 pts)

| Subsection | Points | Input | Example |
|-----------|--------|-------|---------|
| Roof Condition | 45 | Year built | New (0-5 yrs) = 45 pts |
| Backyard | 35 | Usable space | Spacious = 35 pts |
| Plumbing/Electrical | 40 | Year built | 2010+ = 40 pts |
| Pool Equipment | 20 | Equipment age | New (0-3 yrs) = 20 pts |
| Cost Efficiency | 40 | Monthly cost | $3-4k/mo = 40 pts |

### Section C: Interior (190 pts)

| Subsection | Points | Input | Example |
|-----------|--------|-------|---------|
| Kitchen | 40 | Visual inspection | Modern open = 40 pts |
| Master Suite | 35 | Visual inspection | Spacious = 35 pts |
| Natural Light | 30 | Windows/skylights | Many windows = 30 pts |
| High Ceilings | 25 | Ceiling height | Vaulted = 25 pts |
| Fireplace | 20 | Presence/type | Gas = 20 pts |
| Laundry | 20 | Location/quality | Dedicated room = 20 pts |
| Aesthetics | 10 | Overall appeal | Modern/clean = 10 pts |

### Tier Classification

| Tier | Points | Percentage | Interpretation |
|------|--------|-----------|-----------------|
| Unicorn | > 480 | > 80% | Exceptional - act immediately |
| Contender | 360-480 | 60-80% | Strong - worth serious consideration |
| Pass | < 360 | < 60% | Acceptable but unremarkable |

---

## Data Evolvability

### Current State (Hard to Change)

```
To change kill-switch garage criterion from 1.5 to 1.8:
1. Edit: src/phx_home_analysis/config/constants.py
2. Change: SEVERITY_WEIGHT_GARAGE = 1.8
3. Run: python scripts/phx_home_analyzer.py --all
4. Problem: Can't re-score old properties without re-running phases

To add new criterion (e.g., "no flood zone AE"):
1. Edit: src/phx_home_analysis/services/kill_switch/criteria.py
2. Add new FloodZoneKillSwitch class
3. Edit: src/phx_home_analysis/services/kill_switch/filter.py
4. Add to default kill switches
5. Problem: Hard-coded in multiple places
```

### Desired State (Easier to Change)

```
Kill-switch criteria in: data/buyer_profile.json
{
  "version": "1.0.0",
  "hard_criteria": [
    {"name": "no_hoa", "field": "hoa_fee", "operator": "==", "threshold": 0},
    {"name": "min_beds", "field": "beds", "operator": ">=", "threshold": 4}
  ],
  "soft_criteria": [
    {"name": "garage", "field": "garage_spaces", "operator": ">=", "threshold": 2, "severity": 1.8}
  ]
}

Benefits:
✅ No code changes needed
✅ Can A/B test different profiles
✅ Automatic audit trail of changes
✅ Can rollback if criteria too strict
```

---

## Explainability Gaps

### What Users Don't Know

| Question | Current | Needed |
|----------|---------|--------|
| "Why was this FAIL?" | Failures list | Verdict explanation with severity breakdown |
| "Why score 425?" | Just the number | Per-strategy breakdown (school +36, orientation +15, etc.) |
| "How confident is location?" | Unknown | Confidence score (0.85 = HIGH) per field |
| "What if orientation changed?" | Must re-run | Instant sensitivity analysis |
| "Why did score change?" | No lineage | Scoring run dates and deltas |

### Example: Missing Explanation

```
Property: 123 Main St
Status: FAILED

Current (Opaque):
  kill_switch_failures = ["garage_spaces: 1 < 2"]
  kill_switch_passed = False

Needed (Transparent):
  VERDICT: FAIL (accumulated severity = 6.0 > 3.0)

  ISSUES:
  1. Garage: 1 space (need 2+) → severity 1.5
     Impact: Inconvenient for family living

  2. Year: Built 1983 (not pre-2024) → severity 2.0
     Impact: Potential aging HVAC (lifespan 10-15 yrs in AZ)

  3. Sewer: Unknown if city → severity 2.5
     Impact: If septic, adds maintenance burden

  TOTAL: 6.0 severity (exceeds 3.0 threshold)

  RECOMMENDATION: Multiple improvements needed
  - Adding 1-car garage would reduce severity to 4.5 (still FAIL)
  - Confirming city sewer would reduce by 2.5 (net 3.5, still FAIL)
  - Both together would hit 2.0 (PASS threshold)
```

---

## Configuration Locations

| Configuration | Current Location | Type | Changeable |
|---------------|-----------------|------|-----------|
| Kill-switch criteria | constants.py | Code | ❌ Requires code edit |
| Scoring weights | scoring_weights.py | Code | ❌ Requires code edit |
| Phase names | work_items.json | JSON | ⚠️ Hard-coded references elsewhere |
| Tier thresholds | scoring_weights.py | Code | ❌ Requires code edit |
| Cost rates (HVAC, pool, etc.) | constants.py | Code | ❌ Requires code edit |
| Timeout limits | constants.py | Code | ❌ Requires code edit |

**Ideal**: All configuration in `data/` directory as JSON files

---

## File Organization

### Critical Files (Modify Carefully)

```
data/
├─ enrichment_data.json          [LIST, not dict - use atomic writes!]
├─ work_items.json                [Pipeline state - timestamp on every update]
└─ property_images/
   ├─ processed/                  [Categorized images by property]
   └─ metadata/
      ├─ extraction_state.json
      ├─ address_folder_lookup.json
      └─ pipeline_runs.json
```

### Source Code Key Files

```
src/phx_home_analysis/
├─ config/
│  ├─ constants.py               [Kill-switch, scoring, cost constants]
│  └─ scoring_weights.py         [600-point system definition]
├─ domain/
│  ├─ entities.py                [Property, EnrichmentData]
│  ├─ enums.py                   [Tier, Orientation, SolarStatus]
│  └─ value_objects.py           [Score, ScoreBreakdown]
├─ services/
│  ├─ kill_switch/
│  │  ├─ filter.py               [Orchestrator]
│  │  └─ criteria.py             [Individual criteria]
│  ├─ scoring/
│  │  ├─ scorer.py               [Orchestrator]
│  │  └─ strategies/              [18+ scoring strategies]
│  └─ ...other services
└─ pipeline/
   └─ orchestrator.py            [Main workflow coordinator]
```

---

## Risk Scorecard

### High-Risk Issues (Fix First)

| Risk | Severity | Likelihood | Impact |
|------|----------|-----------|--------|
| Concurrent writes to enrichment_data.json | CRITICAL | MEDIUM | Data corruption |
| No traceability for scoring changes | HIGH | MEDIUM | Can't explain decisions |
| Hard-coded phase names | HIGH | MEDIUM | Blocks adding phases |
| No graceful degradation | MEDIUM | HIGH | Entire batch fails if one phase fails |

### Medium-Risk Issues

| Risk | Severity | Likelihood | Impact |
|------|----------|-----------|--------|
| No inter-phase communication | MEDIUM | MEDIUM | Blocked phases can't signal |
| No cost tracking | MEDIUM | LOW | Budget overruns possible |
| Serial property processing | MEDIUM | MEDIUM | Slow execution |
| Stale data not detected | MEDIUM | MEDIUM | Scoring based on old info |

---

## Quick Fix Checklist

### This Week
- [ ] Add atomic write pattern check to all JSON updates
- [ ] Create field-level metadata template for enrichment_data.json
- [ ] Document where each field comes from (source mapping)
- [ ] Create example scoring explanation for one property

### Next Week
- [ ] Extract kill-switch criteria to buyer_profile.json
- [ ] Extract scoring weights to scoring_config.json
- [ ] Implement kill-switch verdict explanation generator
- [ ] Add confidence field to all enrichment data

### Month 2
- [ ] Implement parallel property processing
- [ ] Create cost tracking and budget alerts
- [ ] Add automatic retry logic for failed phases
- [ ] Implement graceful degradation for missing data

---

## Key Metrics to Track

### System Health

```
Traceability Score: [Currently 3/10]
├─ Field-level lineage: 0/3
├─ Scoring explanation: 1/3
└─ Verdict explanation: 0/3
Target: 8/10

Evolvability Score: [Currently 5/10]
├─ Configuration externalized: 2/3
├─ Criteria versionable: 1/3
└─ Rollback capability: 0/3
Target: 8/10

Explainability Score: [Currently 4/10]
├─ Scoring breakdown: 1/3
├─ Verdict reasoning: 1/3
└─ Data confidence: 0/3
Target: 8/10

Autonomy Score: [Currently 8/10]
├─ Phase orchestration: 3/3
├─ State validation: 2/3
└─ Parallel processing: 0/3
Target: 9/10
```

### Pipeline Performance

```
Properties processed: [Measure weekly]
Avg processing time per property: [Target: <5 min]
Phase success rate: [Target: >98%]
Cost per property: [Track trending]
Data freshness: [Avg days since last sync]
Scoring lineage captured: [% of properties]
```

---

## Additional Resources

**Full Analysis**: `CROSS_CUTTING_ANALYSIS.md`
**Domain Model**: `src/phx_home_analysis/domain/entities.py`
**Scoring Config**: `src/phx_home_analysis/config/scoring_weights.py`
**Kill-Switch Logic**: `src/phx_home_analysis/services/kill_switch/`
**Pipeline Orchestrator**: `src/phx_home_analysis/pipeline/orchestrator.py`


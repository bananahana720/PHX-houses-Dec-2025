# Cross-Cutting Concerns Architecture Review
## PHX Houses Analysis Pipeline

**Date**: December 3, 2025
**Reviewer**: Claude Code (Software Architect)
**Status**: Comprehensive Analysis
**Scope**: Traceability, Evolvability, Explainability, Autonomy

---

## EXECUTIVE SUMMARY

This real estate analysis pipeline is a **well-architected system** with strong foundations in domain-driven design, but has **critical gaps in cross-cutting concerns** that will cause maintenance pain and obstruct evolution as the system grows.

### Key Findings

| Theme | Status | Risk Level | Impact |
|-------|--------|-----------|--------|
| **Traceability** | WEAK | HIGH | Can't explain why scores changed; blind to data provenance |
| **Evolvability** | MODERATE | HIGH | Hard to re-score; criteria changes break workflow state |
| **Explainability** | WEAK | MEDIUM | Scores lack reasoning chains; users can't understand verdicts |
| **Autonomy** | STRONG | LOW | Phase orchestration is solid; validation gates work |

### Architectural Health Scorecard

```
Domain Model Quality:        8/10  (Rich entities, good enums)
Data Contracts:              7/10  (Pydantic schemas solid, metadata sparse)
State Management:            6/10  (work_items.json exists, lineage missing)
Traceability:               3/10  (No field-level provenance or audit log)
Explainability:             4/10  (Scoring is deterministic but unexplained)
Evolvability:               5/10  (Hard-coded phases, fragile state)
Autonomy:                   8/10  (Phase validation works, state gates prevent chaos)
```

---

## 1. TRACEABILITY ANALYSIS

### Current State: Fragmented and Opaque

#### 1.1 What Traces Exist?

**Good:**
- `work_items.json` tracks phase status per property (pending → in_progress → complete)
- `enrichment_data.json` captures raw field values (lot_sqft, year_built, etc.)
- `_last_county_sync`, `_last_updated`, `_phase1_map_completed` timestamps exist
- Phase completion timestamps recorded in work_items

**Missing:**
- **No field-level lineage**: Can't trace where each field came from (County API vs. listing vs. manual?)
- **No scoring audit trail**: Cannot see which scoring strategies contributed to final score
- **No data provenance links**: enrichment_data.json has no `source`, `confidence`, or `lineage_id` fields
- **No user attribution**: Unknown who assessed which images for Section C scoring
- **No version history**: Can't compare old vs. new scores when criteria change
- **No reasoning chains**: Why did a property fail? Which severity threshold was crossed?

#### 1.2 Architecture Problems

**Problem 1: No Provenance Model**

```python
# Current: Just raw values
{
  "full_address": "123 Main St",
  "lot_sqft": 9387,
  "year_built": 1983,
  "_last_updated": "2025-12-03T03:24:41",
  # WHERE did these come from? Assessor API? Zillow? Manual?
  # HOW confident are these? 0.95? 0.70?
  # WHO validated this? Human? Script?
}

# Needed: Provenance per field
{
  "full_address": "123 Main St",
  "lot_sqft": {
    "value": 9387,
    "source": "maricopa_assessor_api",      # Phase 0
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py",
  },
  "orientation": {
    "value": "south",
    "source": "satellite_visual_estimate",  # Phase 1
    "phase": "phase1_map",
    "confidence": 0.65,
    "extracted_at": "2025-12-03T05:30:00",
    "validated_by": "map-analyzer",
    "notes": "Medium confidence - satellite view, not on-site"
  }
}
```

**Problem 2: No Scoring Lineage**

Scoring happens in `PropertyScorer` (orchestrator) + 18+ strategy classes. Final score exists, but:

```python
# Current: Only final output
{
  "full_address": "123 Main St",
  "total_score": 425,
  "tier": "contender",
  "score_breakdown": {
    "location": 180,
    "systems": 95,
    "interior": 150
  }
  # HOW did location reach 180? Which sub-scores?
  # If orientation is 0 and schools is 50, what's the middle 130?
  # Can't explain to user WHY this property scored 425
}

# Needed: Detailed reasoning
{
  "scoring_run_id": "abc123-2025-12-03",
  "scored_at": "2025-12-03T06:00:00",
  "strategies_applied": [
    {
      "strategy": "SchoolDistrictScorer",
      "phase": "phase1_map",
      "input": {"school_rating": 8.0},
      "output": {"points": 36, "max_possible": 45},
      "reasoning": "GreatSchools 8/10 = 36/45 (80%)"
    },
    {
      "strategy": "OrientationScorer",
      "phase": "phase1_map",
      "input": {"orientation": "south"},
      "output": {"points": 15, "max_possible": 25},
      "reasoning": "South-facing = moderate (15/25); North would be 25/25"
    },
    # ... all 18 strategies ...
  ],
  "section_summaries": [
    {"name": "Location", "total": 180, "max": 230},
    {"name": "Systems", "total": 95, "max": 180},
    {"name": "Interior", "total": 150, "max": 190}
  ]
}
```

**Problem 3: No Kill-Switch Audit**

Kill-switch failures are recorded, but verdict reasoning is lost:

```python
# Current: Just verdict
{
  "full_address": "123 Main St",
  "kill_switch_passed": False,
  "kill_switch_failures": ["garage_spaces: 1 < 2"]
  # Why is severity a problem? Which soft criteria cumulated?
  # What was severity total? How close to failure threshold?
}

# Needed: Detailed verdict reasoning
{
  "kill_switch_verdict": {
    "verdict": "FAIL",
    "verdict_reason": "severity >= 3.0 (soft criteria accumulated)",
    "evaluated_at": "2025-12-03T03:25:00",
    "evaluator": "KillSwitchFilter",
    "hard_failures": [],  # Empty = passed all hard criteria
    "soft_criteria_results": [
      {
        "criterion": "city_sewer",
        "requirement": "city",
        "actual": "septic",
        "passed": False,
        "severity": 2.5,
        "notes": "Septic systems add maintenance burden"
      },
      {
        "criterion": "garage_spaces",
        "requirement": ">= 2",
        "actual": 1,
        "passed": False,
        "severity": 1.5,
        "notes": "1-car garage inconvenient for family"
      }
    ],
    "total_severity": 4.0,
    "severity_threshold": 3.0,
    "severity_warning_threshold": 1.5,
  }
}
```

#### 1.3 Traceability Impact

**When criteria change** (e.g., "orientation bonus now 30pts instead of 25pts"):
- Can't re-score without re-running all phases
- No audit trail to show impact of change
- Users can't explain "Why did Property X drop from 480 to 475?"

**When data sources conflict** (County API says year_built=1985, Zillow says 1987):
- No provenance to know which source to trust
- No confidence scores to weight the conflict
- Manual review required for every disagreement

**When scoring algorithms improve**:
- Can't baseline old scores for comparison
- No lineage to show which properties were affected by which strategies
- Regression testing requires manual spot-checking

### Recommendations

#### Short-term (1-2 weeks)
1. **Add field-level metadata** to `enrichment_data.json`:
   - Wrap raw values in objects with `value`, `source`, `confidence`, `extracted_at`
   - Preserve backward compatibility with fallback to raw values
   - Update `EnrichmentDataSchema` to allow metadata fields

2. **Create `field_lineage.json`** state file:
   ```json
   {
     "properties": [
       {
         "address": "123 Main St",
         "fields": {
           "lot_sqft": {"source": "maricopa_assessor_api", "phase": "phase0_county"},
           "orientation": {"source": "satellite_visual_estimate", "phase": "phase1_map"}
         }
       }
     ]
   }
   ```

3. **Add scoring lineage capture** in `PropertyScorer`:
   ```python
   # In PropertyScorer.score()
   lineage = {
       "run_id": generate_run_id(),
       "scored_at": datetime.now(),
       "strategies": []
   }
   # Each strategy appends to lineage before final score
   property.scoring_lineage = lineage
   ```

#### Medium-term (3-4 weeks)
1. **Implement versioned scoring system**:
   - Store scoring runs with version numbers
   - Allow rollback to previous scoring algorithm
   - Compare scores across versions

2. **Create scoring explanation generator**:
   ```python
   def explain_score(property: Property, include_breakdown=True):
       """Generate human-readable explanation of score."""
       return f"""
       Property: {property.full_address}

       LOCATION SCORE: {location_score}/230
       - School District: {school_score}/45 (GreatSchools {rating}/10)
       - Safety: {safety_score}/50 (crime index {index})
       - Orientation: {orientation_score}/25 (facing {orientation})

       SYSTEMS SCORE: {systems_score}/180
       - Roof: {roof_score}/50 (built {year}, {age} years old)
       - Plumbing/Electrical: {plumbing_score}/40

       INTERIOR SCORE: {interior_score}/190
       - Kitchen: {kitchen_score}/40
       - Master Suite: {suite_score}/40

       TOTAL: {total}/600 → {tier}
       """
   ```

3. **Implement confidence-aware field aggregation**:
   ```python
   def merge_enrichment(listing_data, enrichment_data):
       """Merge with confidence weighting."""
       # If enrichment_data.year_built has confidence 0.95
       # and listing_data.year_built has confidence 0.70
       # Use enrichment (0.95 wins)
       # Store both with provenance
   ```

#### Long-term (ongoing)
1. **Audit log system** for all property changes:
   - Who changed what field, when, from what to what
   - Supports regulatory compliance (FTC, local real estate laws)

2. **Time-series property snapshots**:
   - Save complete property state before/after each phase
   - Enables "what if" analysis when criteria change

3. **Data lineage visualization**:
   - Graph showing how property data flowed through pipeline
   - Which sources contributed to final verdict

---

## 2. EVOLVABILITY ANALYSIS

### Current State: Phase-Locked, Hard to Change

#### 2.1 What Prevents Change?

**Problem 1: Hard-Coded Phase Dependencies**

```python
# In work_items.json, phase sequence is implicit:
{
  "phases": {
    "phase0_county": {"status": "completed"},
    "phase1_listing": {"status": "pending"},
    "phase1_map": {"status": "completed"},
    "phase2_images": {"status": "pending"},
    "phase3_synthesis": {"status": "pending"},
    "phase4_report": {"status": "pending"}
  }
}

# Problem: Phase names are strings, dependencies are implicit
# If you want to add "phase1b_market_analysis" between phase1 and phase2,
# entire orchestration breaks:
# - /analyze-property command hard-codes phase names
# - validate_phase_prerequisites.py checks for "phase2_images" exactly
# - agents/image-assessor.md mentions "phase2_images" explicitly
# - AnalysisPipeline.run() has phase order hard-coded

# Current phase sequence (HARD-CODED):
# phase0_county (county API)
#   ↓
# phase1_listing (extract images)
# phase1_map (geographic data) [parallel to phase1_listing]
#   ↓
# phase2_images (assess interior/exterior)
#   ↓
# phase3_synthesis (score)
#   ↓
# phase4_report (generate reports)

# Desired: Declarative phase graph
PHASE_DAG = {
    "phase0_county": {
        "display_name": "County Data Extraction",
        "dependencies": [],
        "timeout_seconds": 60,
        "retryable": True
    },
    "phase1_listing": {
        "display_name": "Image Extraction",
        "dependencies": [],
        "timeout_seconds": 300,
        "retryable": True
    },
    "phase1_map": {
        "display_name": "Geographic Analysis",
        "dependencies": [],
        "timeout_seconds": 120,
        "retryable": True
    },
    "phase2_images": {
        "display_name": "Image Assessment",
        "dependencies": ["phase1_listing"],  # Explicit dependency
        "timeout_seconds": 600,
        "retryable": False  # Vision assessment not idempotent
    },
    "phase3_synthesis": {
        "display_name": "Scoring & Classification",
        "dependencies": ["phase0_county", "phase1_listing", "phase1_map", "phase2_images"],
        "timeout_seconds": 60,
        "retryable": True
    },
    "phase4_report": {
        "display_name": "Report Generation",
        "dependencies": ["phase3_synthesis"],
        "timeout_seconds": 120,
        "retryable": True
    }
}
```

**Problem 2: Criteria Hard-Coded in Config**

Kill-switch criteria are in `constants.py`:

```python
# src/phx_home_analysis/config/constants.py
SEVERITY_WEIGHT_SEWER: Final[float] = 2.5
SEVERITY_WEIGHT_YEAR_BUILT: Final[float] = 2.0
SEVERITY_WEIGHT_GARAGE: Final[float] = 1.5
SEVERITY_WEIGHT_LOT_SIZE: Final[float] = 1.0
SEVERITY_FAIL_THRESHOLD: Final[float] = 3.0

# Problem: To change criteria:
# 1. Modify constants.py
# 2. Re-run all properties (can't re-score without re-phase)
# 3. No audit of "what changed"
# 4. No rollback if new criteria are worse

# Desired: Criteria as first-class objects
{
  "buyer_profile_version": "1.2.0",
  "created_at": "2025-12-03",
  "hard_criteria": [
    {
      "name": "no_hoa",
      "field": "hoa_fee",
      "operator": "==",
      "threshold": 0,
      "fail_severity": "INSTANT"
    },
    {
      "name": "min_bedrooms",
      "field": "beds",
      "operator": ">=",
      "threshold": 4,
      "fail_severity": "INSTANT"
    }
  ],
  "soft_criteria": [
    {
      "name": "city_sewer",
      "field": "sewer_type",
      "operator": "==",
      "threshold": "city",
      "severity_weight": 2.5
    },
    {
      "name": "garage_spaces",
      "field": "garage_spaces",
      "operator": ">=",
      "threshold": 2,
      "severity_weight": 1.5
    }
  ],
  "severity_thresholds": {
    "fail": 3.0,
    "warning": 1.5
  }
}
```

**Problem 3: Raw Data Not Preserved**

If scoring strategy changes, you can't re-apply new scoring to old data:

```python
# enrichment_data.json has:
{
  "full_address": "123 Main St",
  "kitchen_layout_score": 8,  # Score, not raw data!
  "master_suite_score": 7,
  # Problem: Can't change scoring rubric because we lost the images!
  # Images in property_images/processed/ but no link to which image
  # showed kitchen vs. master suite
}

# Needed: Preserve raw inputs
{
  "full_address": "123 Main St",
  "section_c_raw_data": {
    "kitchen_layout": {
      "visual_observations": ["open_concept", "island_seating", "modern_appliances"],
      "image_references": ["kitchen_001.jpg", "kitchen_002.jpg"],
      "assessor_notes": "Very functional modern kitchen"
    },
    "master_suite": {
      "visual_observations": ["large_bedroom", "walk_in_closet", "en_suite_bath"],
      "image_references": ["master_001.jpg", "master_002.jpg"],
      "assessor_notes": "Spacious with good natural light"
    }
  },
  "scoring_history": [
    {
      "scoring_version": "1.0.0",
      "kitchen_score": 8,
      "master_score": 7
    },
    {
      "scoring_version": "1.1.0",  # If rubric changed
      "kitchen_score": 7,
      "master_score": 8
    }
  ]
}
```

**Problem 4: No Feature Flags or Gradual Rollout**

All-or-nothing criteria changes:

```python
# Can't do: "Use new confidence threshold for 20% of properties first"
# Can't do: "A/B test two scoring strategies"
# Can't do: "Gradually migrate from manual assessment to AI"

# Needed: Feature flag system
{
  "feature_flags": {
    "use_ai_exterior_assessment": {
      "enabled": true,
      "rollout_percentage": 25,  # Gradually roll out
      "started_at": "2025-12-01",
      "target_completion": "2025-12-15"
    },
    "use_new_school_rating_api": {
      "enabled": false,
      "rollout_percentage": 0,
      "scheduled_for": "2025-12-10"
    }
  }
}
```

#### 2.2 Evolvability Impact

| Change Type | Current | Desired |
|-------------|---------|---------|
| **Criteria change** (e.g., garage from 1.5 to 1.8) | Modify constants.py, re-run all | Update buyer_profile.json, automatic re-eval |
| **Add new criterion** (e.g., "no basement") | Modify KillSwitchFilter class | Add to buyer_profile.json |
| **Add new phase** (e.g., "phase1b_market_data") | Modify work_items schema, orchestrator, agents | Add to PHASE_DAG config |
| **Change scoring rubric** | Modify strategy classes, re-score all | Update scoring_weights.json, preserve raw data |
| **Rollback failed change** | Manual revert in code, re-run | Revert JSON config, automatic rollback |
| **A/B test new strategy** | Not possible | Use feature flags |

### Recommendations

#### Short-term (1-2 weeks)
1. **Externalize buyer profile** to JSON:
   ```yaml
   # data/buyer_profile.json
   {
     "version": "1.0.0",
     "hard_criteria": [...],
     "soft_criteria": [...],
     "severity_thresholds": {...}
   }
   ```
   - Load in KillSwitchFilter constructor instead of hardcoded constants
   - Add validation schema

2. **Extract phase DAG** to config:
   ```yaml
   # data/phase_configuration.json
   {
     "phases": {
       "phase0_county": {...},
       "phase1_listing": {...}
     },
     "execution_order": [
       ["phase0_county"],
       ["phase1_listing", "phase1_map"],  # Parallel
       ["phase2_images"],
       ["phase3_synthesis"],
       ["phase4_report"]
     ]
   }
   ```

3. **Create scoring configuration** file:
   ```yaml
   # data/scoring_configuration.json
   {
     "version": "1.0.0",
     "sections": [
       {"name": "location", "max_points": 230},
       {"name": "systems", "max_points": 180},
       {"name": "interior", "max_points": 190}
     ],
     "strategies": [...]  # List of scoring strategies with weights
   }
   ```

#### Medium-term (3-4 weeks)
1. **Implement configuration versioning**:
   - Track which config version was used for each scoring run
   - Allow "what if" re-scoring with different config
   - Store config alongside results

2. **Create migration system** for data schema:
   - Script to upgrade enrichment_data.json when schema changes
   - Rollback capability
   - Validation before/after migration

3. **Implement re-scoring orchestration**:
   ```python
   # Allow: python scripts/re_score.py --from-config v1.0.0 --to-config v1.1.0 --properties all
   # Generates migration report showing impact
   ```

#### Long-term (ongoing)
1. **Evaluation-as-code framework**:
   - Define criteria in a DSL (domain-specific language) or graph format
   - Easier to reason about criteria dependencies
   - Automatic visualization of decision trees

2. **Rolling deployment strategy**:
   - Feature flags for criteria changes
   - Canary deployments (new criteria on 10% first)
   - Automatic rollback if quality metrics degrade

3. **Self-service criteria tuning**:
   - Web UI to adjust weights and thresholds
   - Immediate impact visualization
   - Audit trail of all changes

---

## 3. EXPLAINABILITY ANALYSIS

### Current State: Deterministic But Silent

#### 3.1 Where Is Reasoning?

**Good:**
- Scoring is completely deterministic (no randomness)
- Each strategy has clear logic (e.g., "school rating 8/10 = 36/45 points")
- Kill-switch criteria are explicit (beds, baths, HOA, etc.)

**Missing:**
- **No explanation to users**: Properties lack "why" statements
- **No per-strategy breakdown**: Can't see which scoring strategy contributed what
- **No failure explanations**: Kill-switch failures lack reasoning
- **No confidence in data**: Users don't know if location is high/medium/low confidence
- **No alternatives shown**: "What if orientation were north instead of south?"

#### 3.2 Architecture Problems

**Problem 1: Scoring Black Box**

```python
# PropertyScorer.score() orchestrates 18+ strategies
# Each strategy computes points independently
# Final score is sum of all strategies
# But: Zero explanation of "why did you score this X?"

# Current output:
property.score_breakdown = ScoreBreakdown(
    location=180,
    systems=95,
    interior=150,
    total_score=425
)

# Missing: Detailed reasoning
# What should be:
property.score_explanation = ScoreExplanation(
    total_score=425,
    tier="CONTENDER",
    sections=[
        SectionExplanation(
            name="LOCATION & ENVIRONMENT (180/230)",
            details=[
                StrategyResult(
                    strategy="SchoolDistrictScorer",
                    score=36,
                    max_points=45,
                    data_used={"school_rating": 8.0},
                    reasoning="GreatSchools rating of 8.0/10 = 36/45 points (80%)",
                    confidence="HIGH",
                    source="GreatSchools.org"
                ),
                StrategyResult(
                    strategy="CrimeIndexScorer",
                    score=40,
                    max_points=50,
                    data_used={"violent_crime_index": 85, "property_crime_index": 75},
                    reasoning="Composite index (60% violent + 40% property) = 81 → 40/50 points",
                    confidence="MEDIUM",
                    source="BestPlaces crime data"
                ),
                # ... all 18+ strategies ...
            ]
        )
    ],
    warnings=[
        "Orientation (south) reduces cooling efficiency vs. north-facing",
        "Year built (1983) suggests aging systems - may need replacement",
        "HVAC lifespan in Arizona is 10-15 years; this unit is 42+ years old"
    ]
)
```

**Problem 2: Kill-Switch Verdict Without Context**

```python
# Current:
property.kill_switch_passed = False
property.kill_switch_failures = ["garage_spaces: 1 < 2 required"]

# What user sees: "FAILED" - no explanation of severity or options

# Needed: Nuanced verdict with severity context
property.kill_switch_verdict = KillSwitchVerdict(
    verdict="FAIL",
    verdict_explanation="""
    This property FAILED due to accumulated severity from soft criteria:

    SOFT CRITERIA ISSUES:
    1. Garage: 1 space (required: 2+)
       Severity: 1.5 (inconvenient for family living)

    2. Year Built: 1983 (required: < 2024)
       Severity: 2.0 (potential aging system issues)

    3. Sewer: City/Septic? (required: city)
       Severity: 2.5 (if septic, adds maintenance burden)

    TOTAL SEVERITY: 6.0 (exceeds threshold of 3.0)

    RECOMMENDATION: Even if one issue resolved (e.g., add garage),
    total severity would be 4.5 - still failing. Multiple improvements needed.
    """,
    severity_total=6.0,
    severity_threshold=3.0,
    severity_warning_threshold=1.5,
    hard_failures=[],  # All hard criteria passed
    soft_failures=[
        SoftCriterion(
            name="garage_spaces",
            requirement=">= 2",
            actual=1,
            severity=1.5
        ),
        SoftCriterion(
            name="year_built",
            requirement="< 2024",
            actual=1983,
            severity=2.0
        ),
        SoftCriterion(
            name="sewer_type",
            requirement="city",
            actual="unknown",
            severity=2.5
        )
    ]
)
```

**Problem 3: No Data Quality Signals**

```python
# Current: All fields treated equally
{
  "full_address": "123 Main St",
  "lot_sqft": 9387,              # From assessor (high confidence)
  "school_rating": 7.5,          # From GreatSchools (high confidence)
  "safety_score": 6,             # From BestPlaces (medium confidence)
  "orientation": "south",        # From satellite estimate (medium confidence)
  "kitchen_layout_score": 8,     # From human assessment (unknown confidence)
}

# Problem: User doesn't know which fields are reliable

# Needed: Confidence annotations
{
  "full_address": "123 Main St",
  "lot_sqft": {
    "value": 9387,
    "confidence": 0.95,
    "confidence_label": "HIGH",
    "confidence_reason": "Official county assessor record"
  },
  "school_rating": {
    "value": 7.5,
    "confidence": 0.85,
    "confidence_label": "HIGH",
    "confidence_reason": "GreatSchools official rating"
  },
  "safety_score": {
    "value": 6,
    "confidence": 0.70,
    "confidence_label": "MEDIUM",
    "confidence_reason": "Aggregated from multiple public sources"
  },
  "orientation": {
    "value": "south",
    "confidence": 0.65,
    "confidence_label": "MEDIUM",
    "confidence_reason": "Estimated from satellite imagery"
  },
  "kitchen_layout_score": {
    "value": 8,
    "confidence": 0.60,
    "confidence_label": "MEDIUM",
    "confidence_reason": "Manual visual assessment from 3 photos"
  }
}
```

**Problem 4: No Sensitivity Analysis**

Can't answer: "What if orientation changed to north? How much would score improve?"

```python
# Needed: Scenario analysis
def explain_score_sensitivity(property: Property):
    """Show how score changes with different inputs."""
    return {
        "current_score": 425,
        "if_orientation_north": {
            "new_score": 440,
            "change": "+15 points",
            "reasoning": "North-facing saves cooling costs, orientation strategy +15pts"
        },
        "if_roof_replaced": {
            "new_score": 445,
            "change": "+20 points",
            "reasoning": "New roof = 10pts, plumbing/electrical +10pts (newer systems)"
        },
        "if_garage_2_spaces": {
            "new_score": 455,
            "change": "+30 points",
            "reasoning": "Passes kill-switch, avoids system skip",
            "note": "This alone doesn't change kill-switch (severity still 4.0)"
        },
        "if_all_improvements": {
            "new_score": 485,
            "change": "+60 points",
            "new_tier": "UNICORN",
            "reasoning": "Multiple improvements compound"
        }
    }
```

#### 3.3 Explainability Impact

| User Question | Current | Desired |
|---------------|---------|---------|
| "Why is this property FAILED?" | Check failures list, guess | Read verdict_explanation with severity breakdown |
| "Why is score 425 and not 400?" | No info | See each strategy contribution |
| "How reliable is the school rating?" | Unknown | See confidence: 0.85 (HIGH) - GreatSchools official |
| "What if orientation changed?" | Must re-run pipeline | See sensitivity analysis instantly |
| "Which field is most reliable?" | All equally weighted | See confidence scores per field |
| "Why did my score change between runs?" | No lineage | See scoring run dates and what changed |

### Recommendations

#### Short-term (1-2 weeks)
1. **Add explanation decorator** to PropertyScorer:
   ```python
   class ExplainablePropertyScorer(PropertyScorer):
       def score(self, property: Property) -> tuple[float, ScoreExplanation]:
           explanation = ScoreExplanation(total_score=0)
           for strategy in self.strategies:
               score, reasoning = strategy.score_with_explanation(property)
               explanation.add_strategy_result(strategy.name, score, reasoning)
           property.score_explanation = explanation
           return property.total_score, explanation
   ```

2. **Create KillSwitchVerdict model** with explanation:
   ```python
   @dataclass
   class KillSwitchVerdict:
       verdict: str  # "PASS", "WARNING", "FAIL"
       explanation: str
       severity_total: float
       severity_threshold: float
       hard_failures: list[str]
       soft_failures: list[SoftCriterionResult]
   ```

3. **Add confidence field** to enrichment_data.json:
   - Wrap each field in `{value, confidence, source}`
   - Update `EnrichmentDataSchema` validator

#### Medium-term (3-4 weeks)
1. **Implement scoring explanation UI**:
   - HTML report showing strategy breakdown
   - Visual gauge for each section (0-100%)
   - Warnings for low-confidence data

2. **Create verdict narrative generator**:
   ```python
   def explain_verdict_narrative(property: Property) -> str:
       """Generate human-readable explanation of verdict."""
       # Returns multi-paragraph explanation
       # E.g., "This property FAILED because..."
   ```

3. **Implement scenario analysis**:
   ```python
   def analyze_score_sensitivity(property: Property):
       """Show impact of changing key fields."""
       # Return dict with "what if" scenarios
   ```

#### Long-term (ongoing)
1. **Interactive property explorer**:
   - Show scoring decision tree
   - Hover over fields to see confidence
   - Click "what if" to simulate changes

2. **Comparative explanations**:
   - "Why is Property A (425 pts) better than Property B (400 pts)?"
   - Highlight differences in each section

3. **Natural language explanation generation**:
   - Use LLM to generate readable summaries
   - E.g., "This 1983 home in Peoria has strong schools (8/10) but aging systems..."

---

## 4. AUTONOMY ANALYSIS

### Current State: Phase Orchestration Is Solid

#### 4.1 What Works?

**Good (8/10):**
- ✅ Phase validation gates (`validate_phase_prerequisites.py`) prevent bad spawns
- ✅ Phase dependencies tracked in `work_items.json` (phase0 → phase1 → phase2 → etc.)
- ✅ State recovery: If agent crashes, pipeline resumes from last checkpoint
- ✅ Retry logic exists for failed phases
- ✅ Phase-level timeouts and concurrency limits defined in config

**Weaknesses (3/10):**
- ❌ No cross-property orchestration (must process properties sequentially)
- ❌ No inter-phase communication (phase1 can't signal "skip phase2 for this property")
- ❌ Manual monitoring required (no automatic backoff/escalation)
- ❌ No cost awareness (processes can run forever without budget checks)
- ❌ No self-healing (if 10% of properties fail, entire batch doesn't auto-retry with backoff)

#### 4.2 Current Orchestration Architecture

```python
# /analyze-property command spawns agents sequentially:

def analyze_property(address: str):
    # Load work_items.json
    work_items = load_work_items()

    for work_item in work_items:
        # Phase 0: County data
        if work_item.phases.phase0_county.status == "pending":
            # Run python scripts/extract_county_data.py
            # Update work_items.json

        # Phase 1a: Listing images
        if work_item.phases.phase1_listing.status == "pending":
            # Spawn listing-browser agent
            # Check validate_phase_prerequisites
            # Update work_items.json

        # Phase 1b: Map analysis (parallel)
        if work_item.phases.phase1_map.status == "pending":
            # Spawn map-analyzer agent
            # Update work_items.json

        # Phase 2: Image assessment (blocked if phase1_listing incomplete)
        if (work_item.phases.phase1_listing.status == "completed" and
            work_item.phases.phase2_images.status == "pending"):
            # Validate prerequisites
            if validate_phase_prerequisites(...):
                # Spawn image-assessor agent
                # Update work_items.json
            else:
                # BLOCKED - log reason, continue to next property

        # Phase 3: Synthesis (run all properties at once after phases complete)
        if all_phases_ready():
            # python scripts/phx_home_analyzer.py

        # Phase 4: Reporting
        # python scripts/generate_all_reports.py

# Problem: Serial processing blocks progress
# If property A is blocked on phase 2, property B can't advance
# Better: Process in parallel with dependency awareness
```

#### 4.3 Autonomy Gaps

**Gap 1: No Parallel Property Processing**

```python
# Current: Sequential
for property in properties:
    phase0(property)  # Wait
    phase1(property)  # Wait
    phase2(property)  # Wait

# Takes: 3 hours for 8 properties

# Desired: Parallel with dependency awareness
ExecutionGraph(
    [
        phase0(prop_A), phase0(prop_B), phase0(prop_C),  # Parallel
    ],
    then=[
        phase1_listing(prop_A), phase1_listing(prop_B),  # Parallel
        phase1_map(prop_A), phase1_map(prop_B),          # Parallel
    ],
    then=[
        phase2_images(prop_A), phase2_images(prop_B),    # Parallel (if prerequisites met)
    ],
    then=[
        phase3_synthesis_all(),  # Wait for all
    ]
)

# Takes: 45 minutes (mostly network I/O)
```

**Gap 2: No Inter-Phase Communication**

```python
# Example: Phase 1 listing agent can't tell phase 2 to skip
# Scenario: Zillow/Redfin has no interior photos (rare)
# Current: Phase 2 image assessor tries to assess, fails silently

# Desired: Phase 1 signals to orchestrator
if no_interior_photos:
    work_item.phases.phase2_images.status = "skipped"
    work_item.phases.phase2_images.skip_reason = "No interior photos available"
    # Phase 3 synthesis handles skipped phases gracefully
```

**Gap 3: No Automatic Backoff/Escalation**

```python
# Example: County API times out for 20% of properties
# Current: Entire batch fails, requires manual retry

# Desired: Automatic exponential backoff
retry_count = 0
while retry_count < 3:
    try:
        phase0_county(property)
        break
    except TimeoutError:
        retry_count += 1
        wait_time = 2 ** retry_count  # 2s, 4s, 8s
        sleep(wait_time)

# If all retries fail:
work_item.status = "failed"
work_item.failure_reason = "County API timeout after 3 retries"
send_alert("County API degraded - manual intervention needed")
```

**Gap 4: No Cost Awareness**

```python
# Image extraction can cost $$$:
# - 500 properties × 20 images × Imgur upload = network costs
# - Claude Vision: $0.003 per image × 8000 images = $24

# Current: No budget tracking
# Desired: Cost awareness
cost_budget = {
    "image_extraction": 100.0,  # $100 for Imgur
    "vision_assessment": 50.0,  # $50 for Claude Vision
}

# During execution:
vision_cost = 0.003 * image_count
if vision_cost > cost_budget["vision_assessment"]:
    logger.warning(f"Vision cost would exceed budget: ${vision_cost:.2f} > ${cost_budget['vision_assessment']}")
    # Option 1: Skip remaining properties
    # Option 2: Use cheaper model (Haiku instead of Sonnet)
    # Option 3: Batch images (assess 3 per call instead of 1)
```

**Gap 5: No Degradation Handling**

```python
# Current: All-or-nothing scoring
# If interior assessment fails, entire property skipped

# Desired: Graceful degradation
property.score_breakdown = ScoreBreakdown(
    location=180,  # Successful
    systems=95,    # Successful
    interior=None  # Failed - skip this section
)

property.total_score = 275  # Location + Systems only
property.scoring_notes = "Interior assessment skipped (no photos available)"
property.tier = "PASS_INCOMPLETE"  # Flag as incomplete scoring

# Still provide value: Can rank by available data
```

#### 4.4 Current Strengths

**Phase State Management (8/10):**
```python
# work_items.json tracks progress per property
# Each phase has status: pending → in_progress → completed|failed|blocked
# Prevents double-processing (idempotency key = address + phase)

# Validation gates work well
validate_phase_prerequisites("123 Main St", "phase2_images")
# Returns: can_spawn=True/False, reason="...", context={...}
```

**Crash Recovery (7/10):**
```python
# If orchestrator crashes mid-batch:
# - work_items.json is saved state
# - Agents append to enrichment_data.json atomically
# - Re-running same command resumes from last checkpoint
# - No duplicate processing (phase status prevents re-runs)
```

**Timeout Handling (6/10):**
```python
# config/constants.py defines phase timeouts:
IMAGE_BROWSER_TIMEOUT = 30  # seconds
IMAGE_DOWNLOAD_TIMEOUT = 30

# But: Timeouts are applied, not enforced
# Agents must respect timeout, not automatic
```

### Recommendations

#### Short-term (1-2 weeks)
1. **Implement parallel property processing**:
   ```python
   # Use ThreadPoolExecutor for CPU-bound phases, AsyncIO for I/O
   with ThreadPoolExecutor(max_workers=3) as executor:
       futures = [
           executor.submit(phase0_county, prop)
           for prop in properties
       ]
       for future in as_completed(futures):
           result = future.result()
   ```

2. **Add inter-phase communication** to work_items:
   ```json
   {
     "phases": {
       "phase1_listing": {
         "status": "completed",
         "signals_to_downstream": {
           "no_interior_photos": true,
           "image_count": 12
         }
       }
     }
   }
   ```

3. **Implement automatic retry** logic:
   ```python
   @retry(max_attempts=3, backoff_factor=2)
   def extract_county_data(property):
       # Automatically retries on failure
       pass
   ```

#### Medium-term (3-4 weeks)
1. **Create execution DAG** orchestrator:
   ```python
   dag = ExecutionDAG()
   dag.add_task("phase0", properties, timeout=60)
   dag.add_dependency("phase1_listing", depends_on="phase0")
   dag.add_dependency("phase1_map", depends_on="phase0")
   dag.add_dependency("phase2_images", depends_on="phase1_listing")
   dag.run()  # Handles parallelization automatically
   ```

2. **Implement cost tracking**:
   ```python
   cost_tracker = CostTracker(budget={"vision": 50.0})
   for image in images:
       cost = estimate_vision_cost(image)
       if cost_tracker.remaining < cost:
           logger.warning("Cost budget exceeded")
           break
       result = assess_image_with_vision(image)
       cost_tracker.record(cost)
   ```

3. **Add graceful degradation**:
   ```python
   def score_property_with_fallback(property):
       try:
           interior_score = assess_interior(property)
       except Exception as e:
           logger.warning(f"Interior assessment failed: {e}")
           interior_score = None  # Skip this section

       return calculate_score(property, interior_score=interior_score)
   ```

#### Long-term (ongoing)
1. **Distributed orchestration**:
   - Use Temporal or Airflow for workflow management
   - Cross-agent communication
   - Automatic scaling

2. **Observability and alerting**:
   - Prometheus metrics for phase duration, success rate
   - Alerts for bottlenecks (e.g., "Phase 2 taking 10x longer than expected")
   - Cost monitoring dashboard

3. **Self-healing recovery**:
   - Automatic detection of stalled phases
   - Rollback to last good state
   - Notification to human operators

---

## 5. ARCHITECTURAL RISKS AND TECHNICAL DEBT

### Critical Risks (High Impact, High Probability)

#### Risk 1: Data Integrity on Concurrent Writes
**Status**: HIGH RISK
**Current**: `enrichment_data.json` is a LIST. Concurrent writes without atomic patterns will corrupt file.
**Likelihood**: MEDIUM (will happen if phases run in parallel)
**Impact**: Complete data loss for entire batch

**Mitigation**:
- Always use atomic writes (temp file + os.replace())
- Add file-level locking (fcntl on Unix, msvcrt on Windows)
- Validate JSON integrity before/after writes

#### Risk 2: Lost Images During Extraction
**Status**: HIGH RISK
**Current**: Image URLs tracked in URL tracking, but if extraction crashes mid-property, deduplication logic breaks
**Likelihood**: MEDIUM (network timeouts are common)
**Impact**: Duplicate image downloads, storage bloat

**Mitigation**:
- Checkpoint image extraction per image (not per property)
- Hash images before accepting (prevent duplicates upstream)
- Implement image cleanup/consolidation script

#### Risk 3: Stale Enrichment Data
**Status**: MEDIUM RISK
**Current**: `_last_updated` exists, but no staleness threshold enforcement
**Likelihood**: MEDIUM (humans forget to check)
**Impact**: Scoring based on stale data (old school ratings, moved utilities, etc.)

**Mitigation**:
- Add automatic staleness check at pipeline start
- Block scoring if data older than 30 days
- Implement refresh strategy

### Technical Debt (Medium Impact)

| Debt Item | Location | Effort to Fix | Impact |
|-----------|----------|---------------|--------|
| **Hard-coded phase names** | work_items, agents, orchestrator | 3 days | Blocks adding phases |
| **No scoring lineage** | PropertyScorer | 2 days | Can't explain scores |
| **No kill-switch audit** | KillSwitchFilter | 1 day | Opaque verdicts |
| **No field provenance** | enrichment_data.json schema | 3 days | Can't trace data source |
| **No confidence scoring** | Validation | 2 days | All data equally weighted |
| **Raw data not preserved** | Image assessment | 2 days | Can't re-score images |
| **No cost tracking** | Image extraction | 1 day | Budget overruns possible |
| **Serial property processing** | Orchestrator | 3 days | Slow execution |
| **No inter-phase communication** | work_items schema | 1 day | Blocks can't be signaled |
| **No automatic retry** | Phase execution | 1 day | Manual intervention needed |

### Architectural Smells

1. **Configuration in Code** (constants.py)
   - Kill-switch weights, tier thresholds, cost rates all hard-coded
   - Should be in JSON config files
   - Blocks evolution and A/B testing

2. **God Object** (Property entity)
   - 156 fields across all phases
   - No clear separation of concerns
   - Should split into phase-specific DTOs

3. **Magic Strings** (phase names)
   - "phase0_county", "phase1_listing", etc. in multiple places
   - String-based dependencies are fragile
   - Should use enums or config

4. **Implicit Ordering** (phase dependencies)
   - Phase sequence embedded in orchestrator logic
   - DAG should be explicit (declarative)
   - Would allow easier phase insertion/removal

5. **Lost Context** (scoring)
   - Strategies run independently
   - No shared context or communication
   - Difficult to implement inter-strategy rules

---

## 6. SYSTEM COHERENCE SCORECARD

### Dimensions Assessed

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Consistency** | 7/10 | Data models consistent (Pydantic + dataclasses), but metadata sparse |
| **Completeness** | 6/10 | Core phases complete, but lineage/provenance missing |
| **Correctness** | 8/10 | Business logic correct (no bugs in scoring), but explainability gaps |
| **Clarity** | 5/10 | Code is readable, but intent behind decisions unclear (no docs on criteria) |
| **Cohesion** | 6/10 | Phases are separate, but limited inter-phase communication |
| **Coupling** | 4/10 | High coupling to work_items.json structure, phase names, config locations |
| **Changeability** | 5/10 | Difficult to change criteria, phases, or scoring rubrics without code edits |
| **Testability** | 7/10 | Good unit test coverage, but integration tests limited |
| **Deployability** | 6/10 | State-based phases allow graceful deployment, but no feature flags |
| **Observability** | 4/10 | Logging exists, but no tracing of decisions or cost tracking |

### Overall System Health: 6/10 (MODERATE)

**Strengths**:
- ✅ Well-designed domain models (Property, Tier enums, Value objects)
- ✅ Clean service layer (strategies, validators, repositories)
- ✅ Good phase orchestration with validation gates
- ✅ Deterministic, reproducible scoring

**Weaknesses**:
- ❌ Zero cross-cutting traceability (can't explain decisions)
- ❌ Hard-coded configuration blocks evolution
- ❌ Lost context in scoring (can't see strategy contributions)
- ❌ No data provenance or confidence tracking
- ❌ Sequential processing limits autonomy

---

## 7. RECOMMENDATIONS SUMMARY

### Priority 1: Implement ASAP (Blocking Issues)

| Task | Effort | Impact | Deadline |
|------|--------|--------|----------|
| Add field-level metadata to enrichment_data.json | 3 days | HIGH - Enables traceability | Week 1 |
| Create scoring explanation model | 2 days | HIGH - Enables explainability | Week 1 |
| Extract configuration to JSON files | 3 days | HIGH - Enables evolvability | Week 1 |
| Implement atomic write patterns for concurrent data | 2 days | CRITICAL - Prevents data loss | Week 1 |

### Priority 2: Important (Quality Improvements)

| Task | Effort | Impact | Timeline |
|------|--------|--------|----------|
| Create scoring lineage capture | 2 days | HIGH | Week 2 |
| Implement kill-switch verdict explanations | 1 day | HIGH | Week 2 |
| Add confidence scoring to all fields | 2 days | MEDIUM | Week 2 |
| Implement parallel property processing | 3 days | MEDIUM | Week 3 |

### Priority 3: Nice-to-Have (Long-term Evolution)

| Task | Effort | Impact | Timeline |
|------|--------|--------|----------|
| Versioned configuration and rollback | 3 days | MEDIUM | Month 2 |
| Feature flags for gradual rollout | 2 days | MEDIUM | Month 2 |
| Automatic retry and backoff | 1 day | LOW | Month 2 |
| Cost tracking and budget alerts | 1 day | LOW | Month 2 |

### Estimated Timeline

- **Week 1**: Foundation (traceability, explainability, configuration)
- **Week 2**: Quality (scoring lineage, verdicts, confidence)
- **Week 3**: Performance (parallel processing, optional improvements)
- **Month 2+**: Advanced (versioning, feature flags, cost tracking)

---

## CONCLUSION

This system has **strong fundamentals** (domain models, phase orchestration, validation gates) but **critical gaps in cross-cutting concerns** (traceability, evolvability, explainability).

**Key insight**: The system is built to scale horizontally (add more properties) but not vertically (change criteria, scoring, or phases). The next phase of evolution should prioritize **configurability, explainability, and observability** to unlock the system's full potential.

The recommended approach is iterative:
1. **Foundation**: Add metadata and configuration files (Weeks 1-2)
2. **Intelligence**: Implement scoring/verdict explanations (Week 2)
3. **Performance**: Enable parallel processing (Week 3)
4. **Maturity**: Version criteria, implement feature flags (Month 2+)

This roadmap preserves backward compatibility while addressing the four critical cross-cutting concerns.


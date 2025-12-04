# 3. EXPLAINABILITY ANALYSIS

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

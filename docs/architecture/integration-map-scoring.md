# Integration Map: Scoring System

## Overview

This document maps the data flows and integration points between the kill-switch, scoring, and reporting layers. It identifies cross-module dependencies, integration risks, and mitigation strategies.

---

## Data Flow Diagram

```
                    ┌─────────────────┐
                    │  Property Data  │
                    │  (CSV + JSON)   │
                    └────────┬────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │     PropertyRepository         │
            │   (Load & Merge Data)          │
            └────────────────┬───────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │     KillSwitchFilter           │
            │   (5 HARD + 4 SOFT criteria)   │
            │                                │
            │   Input: Property              │
            │   Output: KillSwitchResult     │
            │     - verdict: PASS/FAIL       │
            │     - severity: float          │
            │     - failed_criteria: list    │
            └────────────────┬───────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │  verdict=FAIL   │          │  verdict=PASS   │
    │                 │          │                 │
    │  tier=FAILED    │          │  Continue to    │
    │  Skip scoring   │          │  Scoring        │
    └─────────────────┘          └────────┬────────┘
                                          │
                                          ▼
                          ┌────────────────────────────────┐
                          │       PropertyScorer           │
                          │   (22 strategies, 605 pts)     │
                          │                                │
                          │   Input: Property              │
                          │   Output: ScoreBreakdown       │
                          │     - location_scores (250)    │
                          │     - systems_scores (175)     │
                          │     - interior_scores (180)    │
                          └────────────────┬───────────────┘
                                           │
                                           ▼
                          ┌────────────────────────────────┐
                          │     TierClassification         │
                          │                                │
                          │   >= 484 pts → Unicorn         │
                          │   >= 363 pts → Contender       │
                          │   < 363 pts  → Pass            │
                          └────────────────┬───────────────┘
                                           │
                                           ▼
                          ┌────────────────────────────────┐
                          │     Reporting Layer            │
                          │                                │
                          │   - ConsoleReporter            │
                          │   - CsvReporter                │
                          │   - HtmlReportGenerator        │
                          │   - DealSheetReporter (E7)     │
                          │                                │
                          │   Input: Property + Breakdown  │
                          │   Output: Reports/Deal Sheets  │
                          └────────────────────────────────┘
```

---

## Module Dependencies

### Import Graph

```
Kill-Switch Layer                    Scoring Layer                    Reporting Layer
─────────────────                    ─────────────                    ───────────────

services/kill_switch/               services/scoring/                 reporters/
├── __init__.py                     ├── __init__.py                   ├── __init__.py
├── filter.py                       ├── scorer.py ◄─────────────────┐ ├── base.py
│   └── imports:                    │   └── imports:              │ ├── console_reporter.py
│       domain/entities.Property    │       domain/entities       │ │   └── imports:
│       domain/enums.SewerType      │       domain/value_objects  │ │       domain/entities
│       config/constants            │       config/scoring_weights│ │       domain/value_objects
│                                   │       strategies/*          │ │       scoring_formatter
├── criteria/                       ├── strategies/               │ ├── deal_sheet_reporter.py
│   ├── hard.py                     │   ├── location.py           │ │   └── imports:
│   └── soft.py                     │   ├── systems.py            │ │       domain/entities
│                                   │   └── interior.py           │ │       domain/value_objects
├── result.py                       ├── explanation.py ◄──────────┼─┤       scoring_formatter
│   └── KillSwitchResult            │   └── ScoringExplainer      │ │
│                                   │                              │ └── scoring_formatter.py
└── consequence_mapper.py           └── base.py                    │     └── imports:
                                        └── ScoringStrategy        │         domain/value_objects
                                                                   │
                                    domain/                        │
                                    ├── entities.py ◄──────────────┼───────────────────────────────┐
                                    │   └── Property               │                               │
                                    │       (score_breakdown)  ────┘                               │
                                    │       (tier)                                                 │
                                    │       (kill_switch_passed)                                   │
                                    │       (kill_switch_result)                                   │
                                    │                                                              │
                                    └── value_objects.py ◄─────────────────────────────────────────┘
                                        └── Score, ScoreBreakdown
```

### Dependency Table

| Module | Imports From | Imported By |
|--------|--------------|-------------|
| `domain/entities.Property` | enums, typing | kill_switch, scoring, reporters |
| `domain/value_objects.Score` | enums | scoring/strategies, reporters |
| `domain/value_objects.ScoreBreakdown` | Score | scoring/scorer, reporters |
| `services/kill_switch/filter` | entities, enums, criteria | pipeline/orchestrator |
| `services/kill_switch/result` | entities, enums | entities, reporters |
| `services/scoring/scorer` | entities, value_objects, strategies | pipeline/orchestrator |
| `services/scoring/explanation` | entities, value_objects, weights | reporters |
| `reporters/scoring_formatter` | value_objects | reporters/* |
| `reporters/deal_sheet_reporter` | entities, value_objects, scoring_formatter | pipeline |

### Circular Dependency Analysis

**No circular dependencies detected.** The import graph is acyclic:

1. `domain` layer has no internal dependencies
2. `services` layer imports only from `domain` and `config`
3. `reporters` layer imports from `domain` and `services`
4. No layer imports from a higher layer

---

## Integration Points

### Kill-Switch to Scoring

| Integration Point | Source | Target | Data Format |
|-------------------|--------|--------|-------------|
| Verdict check | `KillSwitchFilter.evaluate()` | `PropertyScorer.score_all()` | `Property.kill_switch_passed: bool` |
| Result storage | `KillSwitchResult` | `Property.kill_switch_result` | `KillSwitchResult` object |
| Severity value | `KillSwitchResult.total_severity` | Reporting | `float` (0.0 - 10.0) |

**Code Flow:**
```python
# pipeline/orchestrator.py
def process_properties(self, properties: list[Property]) -> list[Property]:
    # Step 1: Kill-switch evaluation
    for prop in properties:
        result = self.kill_switch_filter.evaluate(prop)
        prop.kill_switch_passed = (result.verdict == "PASS")
        prop.kill_switch_result = result

    # Step 2: Scoring (only for passed properties)
    passed = [p for p in properties if p.kill_switch_passed]
    self.scorer.score_all(passed)

    return properties
```

### Scoring to Tier Classification

| Integration Point | Source | Target | Data Format |
|-------------------|--------|--------|-------------|
| Score calculation | `PropertyScorer.score()` | `Property.score_breakdown` | `ScoreBreakdown` |
| Tier assignment | `Tier.from_score()` | `Property.tier` | `Tier` enum |
| Total score | `ScoreBreakdown.total_score` | `Property.total_score` | `float` |

**Tier Classification Logic:**
```python
# domain/enums.py
class Tier(Enum):
    @classmethod
    def from_score(cls, score: float, kill_switch_passed: bool) -> "Tier":
        """Classify tier based on total score and kill switch status.

        Thresholds (605-point scale):
            - Unicorn: >= 484 (80% of 605)
            - Contender: >= 363 (60% of 605)
            - Pass: < 363 (< 60%)
        """
        if not kill_switch_passed:
            return cls.FAILED
        if score >= 484:  # 80% of 605 - Unicorn threshold
            return cls.UNICORN
        if score >= 363:  # 60% of 605 - Contender threshold
            return cls.CONTENDER
        return cls.PASS
```

### Scoring to Reporting

| Integration Point | Source | Target | Data Format |
|-------------------|--------|--------|-------------|
| Score breakdown | `Property.score_breakdown` | `DealSheetReporter` | `ScoreBreakdown` |
| Score explanation | `ScoringExplainer.explain()` | `DealSheetReporter` | `FullScoreExplanation` |
| Formatted display | `ScoringFormatter` | All reporters | `str`, `dict` |

**Reporting Integration:**
```python
# reporters/deal_sheet_reporter.py
def generate(self, properties: list[Property], output_path: Path) -> None:
    for prop in properties:
        # Get score breakdown
        breakdown = prop.score_breakdown

        # Format for display
        summary = ScoringFormatter.format_breakdown_summary(breakdown)

        # Get explanation (optional)
        explainer = ScoringExplainer()
        explanation = explainer.explain(prop, breakdown)

        # Render template
        self._render_deal_sheet(prop, summary, explanation, output_path)
```

---

## Cross-Module Dependencies

### Shared Data Structures

| Structure | Owner | Consumers | Sync Required |
|-----------|-------|-----------|---------------|
| `Property` | domain/entities | All modules | Schema changes require all-module updates |
| `Score` | domain/value_objects | scoring, reporters | Formula changes require test updates |
| `ScoreBreakdown` | domain/value_objects | scoring, reporters | Section max changes require config sync |
| `KillSwitchResult` | kill_switch/result | entities, reporters | Criteria changes require UI updates |

### Configuration Dependencies

| Config | Used By | Impact of Change |
|--------|---------|------------------|
| `ScoringWeights` | scorer, strategies, reporters | Changes scoring behavior, tier thresholds |
| `TierThresholds` | scorer, formatter, reporters | Changes tier classification boundaries |
| `KillSwitchConfig` | filter, criteria | Changes pass/fail behavior |

---

## Integration Risks

### Risk Matrix

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **R1**: Scoring weight drift | High | Medium | Consistency tests in test_scorer.py |
| **R2**: Tier threshold mismatch | High | Low | TierThresholds single source of truth |
| **R3**: Schema changes break reporters | Medium | Medium | Type hints + mypy strict mode |
| **R4**: Kill-switch verdict not propagated | High | Low | Integration tests verify flow |
| **R5**: Score breakdown serialization errors | Medium | Medium | JSON schema validation |
| **R6**: Section max constant drift | High | Low | Constants in ScoreBreakdown, tests verify |

### Detailed Risk Analysis

#### R1: Scoring Weight Drift

**Description:** Individual strategy weights could drift from documented 605-point total.

**Detection:** `TestScoringSystemConsistency` in test_scorer.py asserts:
- `total_possible_score == 605`
- `section_a_max == 250`
- `section_b_max == 175`
- `section_c_max == 180`
- Individual weights sum to section totals

**Mitigation:**
1. Centralized `ScoringWeights` class is single source of truth
2. CI runs weight validation tests on every commit
3. Any weight change requires updating documentation

#### R2: Tier Threshold Mismatch

**Description:** Tier thresholds in `TierThresholds` could mismatch `ScoringFormatter.determine_tier()`.

**Detection:** `TestTierClassification` validates boundary behavior.

**Mitigation:**
1. `ScoringFormatter.determine_tier()` uses hardcoded values matching `TierThresholds`
2. Integration tests verify tier assignment consistency
3. Schema documentation specifies exact thresholds

#### R3: Schema Changes Break Reporters

**Description:** Changes to `ScoreBreakdown` or `Score` could break reporter integrations.

**Detection:** mypy type checking catches signature mismatches.

**Mitigation:**
1. Full type hints on all public APIs
2. `--strict` mypy mode in CI
3. Reporter tests use real `ScoreBreakdown` objects

#### R4: Kill-Switch Verdict Not Propagated

**Description:** `kill_switch_passed` flag could be missing when scoring.

**Detection:** Integration tests in `test_pipeline.py` verify end-to-end flow.

**Mitigation:**
1. `PropertyScorer.score_all()` sets `tier=FAILED` when `kill_switch_passed=False`
2. Pipeline orchestrator enforces evaluation order
3. Property validation checks required fields

#### R5: Score Breakdown Serialization Errors

**Description:** JSON serialization of `ScoreBreakdown` could lose precision or fields.

**Detection:** Round-trip serialization tests.

**Mitigation:**
1. `score_breakdown_schema.md` documents exact JSON format
2. Serialization helpers round to consistent precision
3. Schema validation on deserialization

#### R6: Section Max Constant Drift

**Description:** `ScoreBreakdown.SECTION_A_MAX` could mismatch `ScoringWeights.section_a_max`.

**Detection:** `test_score_breakdown_matches_weights()` asserts equality.

**Mitigation:**
1. Both classes define constants with same values
2. CI test verifies synchronization
3. Documentation cross-references both sources

---

## Cross-Layer Validation Tests

### Test Categories

| Test Category | Location | Purpose |
|---------------|----------|---------|
| Kill-switch → Scoring | `tests/integration/test_pipeline.py` | Verify verdict propagation |
| Scoring → Tier | `tests/unit/test_scorer.py` | Verify tier assignment |
| Scoring → Reporting | `tests/unit/services/scoring/test_explanation.py` | Verify explanation generation |
| Weight consistency | `tests/unit/test_scorer.py` | Verify 605-point system |
| Schema validation | `tests/unit/test_validation.py` | Verify data structures |

### Critical Integration Tests

```python
# tests/integration/test_pipeline.py

def test_kill_switch_failure_prevents_tier_assignment():
    """Verify failed properties get FAILED tier, not scored tier."""
    prop = create_property_with_hoa_fee(200)  # Fails HOA kill-switch
    pipeline.process([prop])

    assert prop.kill_switch_passed is False
    assert prop.tier == Tier.FAILED
    # Score breakdown may still exist for informational purposes

def test_passed_properties_receive_scores():
    """Verify passed properties get full scoring."""
    prop = create_valid_property()
    pipeline.process([prop])

    assert prop.kill_switch_passed is True
    assert prop.score_breakdown is not None
    assert prop.tier in [Tier.UNICORN, Tier.CONTENDER, Tier.PASS]
    assert prop.total_score > 0

def test_tier_thresholds_match_documentation():
    """Verify tier boundaries match documented thresholds."""
    # Unicorn boundary
    assert Tier.from_score(483.9, True) == Tier.CONTENDER
    assert Tier.from_score(484.0, True) == Tier.UNICORN

    # Contender boundary
    assert Tier.from_score(362.9, True) == Tier.PASS
    assert Tier.from_score(363.0, True) == Tier.CONTENDER
```

---

## Recommendations

### Immediate Actions (E4.S0)

1. **Add integration test for kill-switch → scoring flow** in `test_pipeline.py`
2. **Verify `ScoringFormatter` tier logic** matches `Tier.from_score()`
3. **Add JSON round-trip test** for `ScoreBreakdown` serialization

### Future Improvements (E7)

1. **Implement `DealSheetReporter.generate()`** with template rendering
2. **Add schema validation** for `enrichment_data.json` score storage
3. **Create reporter integration tests** using actual scored properties

### Monitoring

1. **CI gate**: All integration tests must pass before merge
2. **Weight drift detection**: Fail CI if weights don't sum to section maxes
3. **Type checking**: mypy strict mode catches schema mismatches

---

## References

- **Kill-switch architecture**: `docs/architecture/kill-switch-architecture.md`
- **Scoring system architecture**: `docs/architecture/scoring-system-architecture.md`
- **ScoreBreakdown schema**: `docs/schemas/score_breakdown_schema.md`
- **Pipeline orchestration**: `src/phx_home_analysis/pipeline/orchestrator.py`

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-10 | Initial integration map created for E4.S0 | Claude Opus 4.5 |

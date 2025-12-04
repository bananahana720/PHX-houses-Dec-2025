# 7. Migration Plan

### 7.1 Update Sequence

```
Phase 1: Constants & Configuration (No Breaking Changes)
├── Update constants.py with new constants
├── Add SEVERITY_WEIGHT_SOLAR_LEASE = 2.5
├── Add HVAC age thresholds
├── Update roof age thresholds
└── Update pool equipment thresholds

Phase 2: Schema Updates
├── Add new fields to validation/schemas.py
├── Update enrichment_data.json schema
└── Add field definitions to property-data skill

Phase 3: Kill-Switch Integration
├── Add SolarLeaseCriterion to criteria.py
├── Update SOFT_SEVERITY_WEIGHTS dict
├── Update evaluate_kill_switches() function
└── Add tests for solar lease criterion

Phase 4: Scoring Integration
├── Implement HvacConditionScorer
├── Add hvac_condition to ScoringWeights dataclass
├── Update scoring_weights.py Section A/B totals
├── Update PropertyScorer to include HVAC
├── Update cost estimation for solar lease

Phase 5: Data Pipeline Updates
├── Update listing-browser agent to detect solar lease
├── Update extraction patterns for HVAC age
├── Update image-assessor for HVAC condition
└── Update deal sheets for new fields

Phase 6: Validation & Testing
├── Run full test suite
├── Re-score sample properties
├── Validate tier distribution
└── Update documentation
```

### 7.2 Backwards Compatibility

**Graceful Handling of Missing Data:**

```python
# Properties without new fields use neutral defaults
DEFAULTS = {
    "solar_status": "unknown",     # Passes kill-switch with yellow flag
    "hvac_age": None,              # Uses neutral score (12.5 pts)
    "hvac_condition": "unknown",   # Uses neutral score
}

# Existing properties scored before migration
# Will receive neutral HVAC score until re-enriched
```

**Data Migration Script:**

```python
# scripts/migrate_scoring_v2.py

def migrate_existing_properties():
    """Add default values for new fields to existing properties."""
    enrichment = load_enrichment_data()

    for address, data in enrichment.items():
        # Add solar_status if missing
        if "solar_status" not in data:
            data["solar_status"] = "unknown"

        # Derive hvac_age from year_built if possible
        if "hvac_age" not in data and data.get("year_built"):
            data["hvac_age"] = 2025 - data["year_built"]

        # Add hvac_condition if missing
        if "hvac_condition" not in data:
            data["hvac_condition"] = "unknown"

    save_enrichment_data(enrichment)
```

### 7.3 Validation Steps

```bash
# 1. Run unit tests
pytest tests/unit/services/kill_switch/ -v
pytest tests/unit/services/scoring/ -v

# 2. Validate constants integrity
python -c "from src.phx_home_analysis.config.constants import *; \
    assert SCORE_SECTION_A_TOTAL + SCORE_SECTION_B_TOTAL + SCORE_SECTION_C_TOTAL == MAX_POSSIBLE_SCORE"

# 3. Re-score sample properties and compare
python scripts/phx_home_analyzer.py --compare-before-after

# 4. Verify tier distribution
python scripts/analyze_tier_distribution.py
```

---

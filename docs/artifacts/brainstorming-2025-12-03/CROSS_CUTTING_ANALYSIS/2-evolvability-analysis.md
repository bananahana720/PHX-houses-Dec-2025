# 2. EVOLVABILITY ANALYSIS

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

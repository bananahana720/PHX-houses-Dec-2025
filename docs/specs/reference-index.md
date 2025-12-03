# PHX Houses Scoring System Improvement - Reference Document Index

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

## Executive Summary

This document catalogs all research, reference materials, and supporting documentation for the scoring system improvement project. It provides quick access to domain expertise, rate data, and implementation references needed across all waves.

**Total Reference Documents:** 15+ documents, ~50,000 words of research

---

## Table of Contents

1. [Core Planning Documents](#core-planning-documents)
2. [Arizona-Specific Research](#arizona-specific-research)
3. [Construction Quality Rubrics](#construction-quality-rubrics)
4. [Rate Data & External Sources](#rate-data--external-sources)
5. [Existing Skill Files](#existing-skill-files)
6. [Code Architecture References](#code-architecture-references)
7. [Testing & Quality References](#testing--quality-references)

---

## Core Planning Documents

### 1. Master Improvement Plan

**File:** `.claude/plans/hidden-squishing-dragonfly.md`
**Word Count:** ~8,000 words
**Status:** Finalized & Validated

**Contents:**
- Project overview and key objectives
- Kill-switch redesign (HARD vs SOFT criteria)
- Data quality architecture (5 layers)
- Scoring redistribution (600 pts maintained)
- Implementation waves (0-6)
- SME validation findings
- User decisions log

**Key Sections for Reference:**
- Lines 17-46: Kill-switch threshold system with severity weights
- Lines 49-78: Data quality architecture (5-layer system)
- Lines 79-109: Cost estimation module design
- Lines 116-155: Implementation waves breakdown
- Lines 158-173: Critical files to modify
- Lines 176-186: User decisions (finalized)
- Lines 189-213: Scoring weight redistribution table
- Lines 219-270: SME validation findings and gaps

**Usage:**
- Wave 0: Reference data quality baseline requirements
- Wave 1: Reference kill-switch severity weights
- Wave 2: Reference cost estimation components
- All waves: Verify against user decisions

**Cross-References:**
- See architecture doc for system design
- See implementation spec for file-by-file changes

---

### 2. Architecture Overview

**File:** `docs/architecture/scoring-improvement-architecture.md`
**Word Count:** ~12,000 words
**Created:** This session

**Contents:**
- System context diagram
- Component architecture (data quality, kill-switch, cost estimation, scoring)
- Data flow diagrams
- Integration points
- Technology stack
- Performance considerations
- Security & testing strategies

**Key Sections:**
- Component Architecture: Detailed subsystem breakdowns
- Data Flow Diagram: End-to-end pipeline visualization
- Integration Points: How components connect
- File Manifest: All new/modified files

**Usage:**
- Session start: Review system context before coding
- Design decisions: Understand component relationships
- Integration: Reference data flow for cross-module work

---

### 3. Implementation Specification

**File:** `docs/specs/implementation-spec.md`
**Word Count:** ~15,000 words (partial - Waves 0-2 detailed)
**Created:** This session

**Contents:**
- Wave 0: Baseline & pre-processing (code samples)
- Wave 1: Kill-switch threshold (code samples + tests)
- Wave 2: Cost estimation (partial, code structure)
- Waves 3-6: Summary structure (to be expanded)

**Key Sections:**
- 0.1 Quality Baseline Script: Full implementation
- 0.2 Data Normalizer: Full module code
- 1.1 Weighted Threshold Logic: Complete code changes
- 1.2 Deal Sheets Integration: Rendering + CSS

**Usage:**
- Before each session: Read relevant wave section
- During implementation: Copy/adapt code samples
- Testing: Use provided test cases

---

### 4. Phase Execution Guide

**File:** `docs/specs/phase-execution-guide.md`
**Word Count:** ~12,000 words
**Created:** This session

**Contents:**
- Session-by-session execution plan
- Entry/exit criteria for each session
- Verification checkpoints
- Rollback procedures
- Troubleshooting guide
- Success metrics

**Key Sections:**
- Session Planning Matrix: Time estimates and dependencies
- Cross-Session Continuity: How to pause/resume
- Troubleshooting Guide: Common issues and solutions

**Usage:**
- Session planning: Determine which wave/session to tackle
- Mid-session: Reference exit criteria and verification steps
- Issues: Consult troubleshooting guide

---

## Arizona-Specific Research

### 5. Government & Environment Reference

**File:** `.claude/skills/arizona-context/reference-government-environment.md`
**Word Count:** ~8,000 words
**Status:** Research complete (per plan document lines 287-295)

**Contents:**
- Government regulations (HOA laws, property tax, solar, pool safety, sewer)
- Environmental factors (heat island, flood zones, air quality, water scarcity)
- Utilities (SRP vs APS rates, water providers, infrastructure age)
- Market factors (insurance costs, pool costs, roof/HVAC lifespan)
- Scoring implications and red flags
- 50+ data source citations

**Key Topics:**
1. **HOA Regulations:**
   - Arizona HOA laws (minimal state oversight)
   - Special assessment risks
   - Governance structures

2. **Solar Considerations:**
   - Owned vs leased systems
   - Transfer complications
   - Cost-benefit analysis

3. **Pool Costs:**
   - Service: $100-150/month
   - Equipment replacement cycles (AZ heat impact)
   - Energy costs: +$50-100/month

4. **HVAC Lifespan:**
   - AZ: 10-15 years (vs 20+ national average)
   - Dual-zone importance for 2-story homes
   - Replacement costs: $4k-8k

5. **Utility Rates:**
   - SRP vs APS tiered pricing
   - Summer peak rates (May-October)
   - Water scarcity impact on rates

**Usage:**
- Wave 2: Reference utility rates for cost estimation
- Scoring decisions: Understand AZ-specific factors
- AI prompts: Provide context for inference

**Integration Points:**
- Cost Estimation: Pool, HVAC, solar costs
- Scoring: Orientation scoring (cooling cost impact)
- Kill-Switch: Sewer type considerations

---

### 6. Arizona Context Lite (Image Assessment)

**File:** `.claude/skills/arizona-context-lite/SKILL.md`
**Word Count:** ~2,000 words
**Status:** Existing (current system)

**Contents:**
- Lightweight AZ context for image assessment
- Pool age estimation from photos
- HVAC age estimation (visual cues)
- Era calibration (1985 vs 1995 vs 2005 vs 2015)

**Key Sections:**
- Pool Equipment Age: Visual indicators of age
- HVAC Outdoor Unit: Visible wear patterns
- Construction Era Markers: Style clues by decade

**Usage:**
- Wave 4: AI inference prompts for visual assessment
- Image scoring: Calibrate against AZ norms

---

## Construction Quality Rubrics

### 7. Exterior Construction Quality Reference

**File:** `.claude/skills/image-assessment/reference-exterior-quality.md`
**Word Count:** ~4,500 words
**Status:** Research complete (per plan lines 296-304)

**Contents:**
- Roof assessment (tile vs shingle vs flat, AZ lifespan adjustments)
- Stucco condition (crack classification, desert climate impact)
- Windows (single vs dual pane identification, Low-E indicators)
- Landscaping (xeriscape value, water savings calculations)
- Pool & outdoor (equipment age scoring, safety compliance)
- Cost impact estimates for each category

**Key Topics:**
1. **Roof Types:**
   - Tile (concrete vs clay): 30-50 year lifespan (AZ conditions)
   - Shingle: 15-25 years (reduced in AZ heat)
   - Flat: 10-15 years (common in older homes)

2. **Stucco Cracks:**
   - Hairline (<1/16"): Normal settling
   - Small (1/16"-1/4"): Monitor
   - Large (>1/4"): Structural concern

3. **Window Efficiency:**
   - Single pane: High cooling costs
   - Dual pane: Standard
   - Low-E coating: Premium (5-15% energy savings)

4. **Xeriscaping:**
   - Water savings: 30-70% vs traditional lawn
   - Property value impact: +2-5% in AZ market
   - Maintenance costs: -$50-100/month

**Usage:**
- Wave 2: Roof condition cost estimates
- Image assessment: Visual scoring rubric
- AI prompts: Exterior quality inference

**Integration Points:**
- Scoring: Roof condition strategy (50 pts)
- Cost Estimation: Maintenance reserve calculations

---

### 8. Interior Construction Quality Reference

**File:** `.claude/skills/image-assessment/reference-interior-quality.md`
**Word Count:** ~6,500 words
**Status:** Research complete (per plan lines 305-313)

**Contents:**
- Kitchen assessment (cabinets, counters, appliances with era adjustments)
- Master suite (bathroom features, bedroom size indicators)
- Natural light, ceilings, fireplace, laundry scoring
- Flooring type identification (hardwood vs laminate vs LVP vs tile)
- Era-based calibration tables (1985 vs 1995 vs 2005 vs 2015 vs 2023)
- Photo quality confidence scoring system

**Key Topics:**
1. **Kitchen Scoring Factors:**
   - Cabinet quality: Particle board (2-4 pts) → Custom wood (9-10 pts)
   - Countertops: Laminate (2-4 pts) → Granite/quartz (8-10 pts)
   - Appliances: Basic (3-5 pts) → Stainless/integrated (8-10 pts)
   - Layout: Galley (2-4 pts) → Open concept (8-10 pts)

2. **Master Suite Scoring:**
   - Bedroom size: <150 sqft (3-5 pts) → >250 sqft (9-10 pts)
   - Closet: Reach-in (2-4 pts) → Walk-in (8-10 pts)
   - Bathroom: Single sink (3-5 pts) → Dual vanity + separate tub (9-10 pts)
   - Privacy: Adjacent to other rooms (2-4 pts) → Separated wing (8-10 pts)

3. **Flooring Identification:**
   - Carpet: Neutral (5 pts), condition-dependent
   - Vinyl/laminate: 3-6 pts depending on quality
   - LVP (luxury vinyl plank): 6-8 pts (modern upgrade)
   - Tile: 7-9 pts (AZ climate appropriate)
   - Hardwood: 8-10 pts (rare/premium in AZ)

4. **Era Calibration:**
   - 1985: Earth tones, popcorn ceilings, linoleum
   - 1995: Builder beige, standard appliances
   - 2005: Granite counters, stainless appliances
   - 2015: Gray tones, open concept, LVP
   - 2023: Smart home, quartz counters, minimalism

**Usage:**
- Image assessment: Score Section C interior features (190 pts)
- Era calibration: Adjust expectations by year built
- AI prompts: Detailed rubric for inference

**Integration Points:**
- Scoring: Section C strategies (kitchen, master, light, ceilings)
- Data Quality: Photo quality confidence scoring

---

## Rate Data & External Sources

### 9. Mortgage Rate Sources

**Provider:** Various financial institutions
**Update Frequency:** Weekly (7-day cache in RateProvider)
**Current Rates (2025-12-01):** To be fetched

**Sources:**
- Freddie Mac Primary Mortgage Market Survey
- Bankrate.com national averages
- Local AZ lenders (Chase, Wells Fargo, PNC)

**Data Structure:**
```python
MortgageRates(
    thirty_year_fixed=0.070,  # 7.0% APR
    fifteen_year_fixed=0.065,  # 6.5% APR
    source='Freddie Mac PMMS',
    last_updated='2025-12-01T10:00:00Z'
)
```

**Usage:**
- Wave 2: RateProvider.get_mortgage_rates()
- Monthly update: Refresh rate cache manually if needed

---

### 10. Homeowner's Insurance Rates (Arizona)

**Provider:** Insurance industry averages
**Update Frequency:** Quarterly
**Current Rates (2025 estimates):**

**Base Annual Premiums:**
- Low end: $1,500/year ($125/month)
- High end: $2,500/year ($208/month)
- Average: $2,000/year ($167/month)

**Adjustment Factors:**
- Sqft: +$0.50 per sqft above 1,500
- Pool: +$300/year ($25/month)
- Year built <1980: +$200-400/year
- Replacement cost value: Base × (property_value / 300,000)

**Sources:**
- Insurance Information Institute
- Arizona Department of Insurance
- Local insurers (State Farm, Allstate, USAA)

**Usage:**
- Wave 2: InsuranceCalculator.calculate()

---

### 11. Utility Rates (SRP/APS)

**Providers:** SRP (Salt River Project), APS (Arizona Public Service)
**Update Frequency:** Annual rate adjustments (typically May 1)

**Electric Rates (2025):**
- Summer (May-Oct): $0.14/kWh
- Winter (Nov-Apr): $0.11/kWh
- Base charge: $15/month
- Typical usage: 1,200-2,500 kWh/month (depends on sqft, cooling)

**Water Rates:**
- Base: $80-120/month (typical single-family)
- Tiered pricing above baseline

**Gas Rates:**
- Base: $30-80/month (if applicable)
- Minimal usage in AZ (heating less critical)

**Sources:**
- SRP.net rate schedules
- APS.com rate schedules
- Arizona Corporation Commission filings

**Usage:**
- Wave 2: UtilityCalculator.calculate()

**Estimation Formula:**
```python
# Electric
monthly_kwh = sqft × cooling_factor × season_factor
cooling_factor = 1.0 + (0.3 if has_pool else 0.0)
season_factor = 1.8 (summer) | 1.0 (winter)
monthly_cost = (monthly_kwh × rate_per_kwh) + base_charge

# Example: 2,000 sqft, no pool, summer
monthly_kwh = 2000 × 1.0 × 1.8 = 3,600 kWh
monthly_cost = (3600 × 0.14) + 15 = $519/month
```

---

## Existing Skill Files

### 12. Kill-Switch Skill (Current)

**File:** `.claude/skills/kill-switch/SKILL.md`
**Word Count:** ~3,200 words
**Status:** TO BE UPDATED in Wave 6

**Current Contents:**
- "All must pass" logic (to be replaced)
- 7 criteria definitions
- Canonical implementation (`scripts/lib/kill_switch.py`)
- Unknown/null handling
- Early exit pattern
- Chain-of-thought evaluation
- Edge case examples

**Sections to Update (Wave 6):**
- Lines 13-23: Replace with HARD/SOFT distinction
- Lines 26-60: Update evaluation logic for weighted threshold
- Lines 176-227: Update chain-of-thought for severity scoring
- Lines 230-324: Update edge case examples with new verdicts

**Preservation:**
- Keep canonical implementation references
- Keep unknown/null handling section
- Keep edge case decision matrix (update verdicts)

---

### 13. Scoring Skill (Current)

**File:** `.claude/skills/scoring/SKILL.md`
**Word Count:** ~3,400 words
**Status:** TO BE UPDATED in Wave 6

**Current Contents:**
- 600-point system overview
- Section A: 250 pts (location)
- Section B: 160 pts (systems)
- Section C: 190 pts (interior)
- Tier classification (UNICORN/CONTENDER/PASS)
- Score calculation examples
- Default values (5.0 neutral)
- Value ratio calculation

**Sections to Update (Wave 6):**
- Lines 15-19: Update Section B (160→180 pts)
- Lines 51-60: Add Pool 30→20, CostEfficiency 40 NEW
- Lines 83-98: Add CostEfficiencyScorer usage example
- Lines 193-228: Update score sanity check for Section B (180 pts)

**New Section to Add:**
- Cost Efficiency Scoring (40 pts max)
- Formula: `max(0, 10 - ((monthly_cost - 3000) / 200))`
- Examples: $3,000/mo → 10 pts, $4,000/mo → 5 pts, $5,000+/mo → 0 pts

---

### 14. Property Data Skill

**File:** `.claude/skills/property-data/SKILL.md`
**Word Count:** ~2,500 words
**Status:** Stable (minimal updates needed)

**Contents:**
- CSV repository usage
- JSON enrichment repository usage
- Property entity structure
- Data access patterns

**Usage:**
- All waves: Reference for data loading
- Wave 3: Integration with Pydantic validation

---

### 15. Deal Sheets Skill

**File:** `.claude/skills/deal-sheets/SKILL.md`
**Word Count:** ~1,800 words
**Status:** TO BE UPDATED in Wave 6 (minor)

**Contents:**
- Deal sheet generation
- Template structure
- Rendering logic

**Updates Needed:**
- Add kill-switch verdict section example
- Add monthly cost display section example
- Add data quality indicator section

---

## Code Architecture References

### 16. Current Kill-Switch Implementation

**File:** `scripts/lib/kill_switch.py`
**Lines:** 365
**Status:** TO BE MODIFIED in Wave 1

**Key Functions:**
- `evaluate_kill_switches()` (lines 203-248): Main evaluation logic
- `apply_kill_switch()` (lines 251-266): Property update wrapper
- `evaluate_kill_switches_for_display()` (lines 300-352): UI-friendly results
- `KILL_SWITCH_CRITERIA` dict (lines 152-195): Criterion definitions

**Modification Points:**
- Add `evaluate_kill_switches_weighted()` function
- Update `KILL_SWITCH_CRITERIA` with type (HARD/SOFT) and severity
- Maintain backward compatibility in existing functions

---

### 17. Current Scoring Weights

**File:** `src/phx_home_analysis/config/scoring_weights.py`
**Lines:** 319
**Status:** TO BE MODIFIED in Wave 2

**Current Weights:**
- Section A: 250 pts (lines 193-199)
- Section B: 160 pts (lines 201-205)
- Section C: 190 pts (lines 207-214)

**Modification Points:**
- Line 198: quietness 50→40
- Line 197: supermarket_proximity 40→30
- Line 205: pool_condition 30→20
- Line 205+: ADD cost_efficiency 40 (new field)

**Properties to Update:**
- `section_b_max` (line 259-267): 160→180
- `total_possible_score` (line 217-244): Verify still 600

---

### 18. Current Scoring Strategies

**File:** `src/phx_home_analysis/services/scoring/strategies/systems.py`
**Lines:** 253
**Status:** TO BE MODIFIED in Wave 2

**Existing Strategies:**
- RoofConditionScorer (lines 19-77)
- BackyardUtilityScorer (lines 79-127)
- PlumbingElectricalScorer (lines 129-188)
- PoolConditionScorer (lines 190-253)

**Addition Point:**
- Add CostEfficiencyScorer class (after line 253)
- Follows same pattern as existing scorers
- Integrates with CostEstimator for monthly cost data

---

### 19. Property Entity Structure

**File:** `src/phx_home_analysis/domain/entities.py`
**Lines:** 372
**Status:** TO BE MODIFIED in Waves 2, 5

**Key Sections:**
- Property dataclass (lines 15-336): Main entity
- Computed properties (lines 113-312): Derived values
- EnrichmentData (lines 339-372): DTO for JSON

**Modification Points (Wave 2):**
- Line 73+: Add `monthly_cost_estimate: Optional[MonthlyCostEstimate]`

**Modification Points (Wave 5):**
- Line 73+: Add `field_lineage: dict[str, FieldLineage]`
- Line 74+: Add `quality_score: Optional[float]`

---

## Testing & Quality References

### 20. Existing Test Structure

**Directory:** `tests/`
**Total Tests:** ~50 (to be expanded to ~200)

**Current Structure:**
```
tests/
├── services/
│   ├── scoring/         # 15 tests
│   └── kill_switch/     # 10 tests (to be expanded)
├── repositories/        # 8 tests
├── domain/              # 5 tests
└── integration/         # 3 tests (to be expanded)
```

**New Tests to Add:**
- Wave 0: `tests/validation/test_normalizer.py` (15 tests)
- Wave 0: `tests/regression/test_baseline.py` (10 tests)
- Wave 1: `tests/services/kill_switch/test_weighted_threshold.py` (20 tests)
- Wave 2: `tests/services/cost_estimation/test_*.py` (30 tests)
- Wave 3: `tests/validation/test_schemas.py` (25 tests)
- Wave 4: `tests/services/ai_enrichment/test_*.py` (20 tests)
- Wave 5: `tests/services/quality/test_*.py` (15 tests)
- Wave 6: `tests/integration/test_*.py` (25 tests)

**Total Target:** ~210 tests

---

## Integration Map

### Data Flow Across References

```
┌─────────────────────────────────────────────────────────┐
│  Reference Documents Used By Each Wave                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Wave 0: Baseline & Pre-Processing                       │
│  └─> Master Plan (data quality section)                  │
│  └─> Implementation Spec (Wave 0)                        │
│  └─> Phase Execution Guide (Session 0.1-0.3)            │
│                                                           │
│  Wave 1: Kill-Switch Threshold                           │
│  └─> Master Plan (kill-switch redesign, severity table)  │
│  └─> Architecture Doc (kill-switch filter diagram)       │
│  └─> Implementation Spec (Wave 1)                        │
│  └─> Current Kill-Switch Skill (for context)             │
│  └─> Phase Execution Guide (Session 1.1-1.3)            │
│                                                           │
│  Wave 2: Cost Estimation                                 │
│  └─> Master Plan (cost estimation module)                │
│  └─> Architecture Doc (cost estimation diagram)          │
│  └─> AZ Government Reference (utility rates)             │
│  └─> Exterior Quality Reference (maintenance costs)      │
│  └─> Rate Data Sources (mortgage, insurance, utilities)  │
│  └─> Implementation Spec (Wave 2)                        │
│  └─> Phase Execution Guide (Session 2.1-2.4)            │
│                                                           │
│  Wave 3: Data Validation                                 │
│  └─> Master Plan (Layer 1: Pydantic validation)          │
│  └─> Architecture Doc (data quality layer)               │
│  └─> Implementation Spec (Wave 3)                        │
│  └─> Property Entity Structure                           │
│  └─> Phase Execution Guide (Session 3.1-3.2)            │
│                                                           │
│  Wave 4: AI Triage                                       │
│  └─> Master Plan (Layer 2: AI inference)                 │
│  └─> AZ Context Lite (for prompt context)                │
│  └─> Interior Quality Reference (for field inference)    │
│  └─> Exterior Quality Reference (for field inference)    │
│  └─> Implementation Spec (Wave 4)                        │
│  └─> Phase Execution Guide (Session 4.1-4.2)            │
│                                                           │
│  Wave 5: Quality & Lineage                               │
│  └─> Master Plan (Layers 3-5: lineage, metrics)          │
│  └─> Architecture Doc (quality metrics)                  │
│  └─> Quality Baseline (Wave 0 output)                    │
│  └─> Implementation Spec (Wave 5)                        │
│  └─> Phase Execution Guide (Session 5.1-5.2)            │
│                                                           │
│  Wave 6: Documentation & Integration                     │
│  └─> ALL REFERENCES (for updates)                        │
│  └─> Kill-Switch Skill (update)                          │
│  └─> Scoring Skill (update)                              │
│  └─> Deal Sheets Skill (update)                          │
│  └─> Master Plan (verify all decisions implemented)      │
│  └─> Phase Execution Guide (Session 6.1-6.3)            │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Reference Cheat Sheet

### By Use Case

**Need to understand severity weights?**
→ Master Plan, lines 17-46

**Need cost estimation rates?**
→ Rate Data Sources (Section 9-11)
→ AZ Government Reference (utilities section)

**Need to score interior features?**
→ Interior Quality Reference (Section 8)
→ Scoring Skill (current, Section C)

**Need to understand current code structure?**
→ Code Architecture References (Section 16-19)

**Need to plan a session?**
→ Phase Execution Guide (relevant wave)

**Need to write tests?**
→ Implementation Spec (test cases provided)
→ Testing & Quality References (Section 20)

**Need Arizona-specific context?**
→ AZ Government Reference (Section 5)
→ AZ Context Lite (Section 6)

**Need to update documentation?**
→ Existing Skill Files (Section 12-15)

---

## Document Maintenance

### When to Update This Index

1. **After completing research:**
   - Add new reference documents discovered
   - Update word counts if significantly changed
   - Add new cross-references

2. **After completing a wave:**
   - Mark documents as "TO BE UPDATED" or "UPDATED"
   - Add new test counts
   - Update integration map

3. **When external rates change:**
   - Update rate data sections
   - Note update dates

### Version Control

- v1.0 (2025-12-01): Initial reference index
- Next Review: After Wave 2 completion (rate data validation)

---

## Related Documents

- `docs/architecture/scoring-improvement-architecture.md` - System architecture
- `docs/specs/implementation-spec.md` - Detailed implementation
- `docs/specs/phase-execution-guide.md` - Session-by-session guide
- `.claude/plans/hidden-squishing-dragonfly.md` - Master plan

---

**End of Reference Index**

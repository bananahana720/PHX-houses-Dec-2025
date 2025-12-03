# Buy-Box Criteria Analysis - Complete Documentation Index

**Analysis Period**: 2025-12-03
**Scope**: Deep dive into Buckets 1 & 2 (Project Vision & Buy-Box Criteria)
**Documents**: 3 comprehensive reports + this index

---

## DOCUMENTS AT A GLANCE

### 1. EXECUTIVE SUMMARY (Start Here!)
**File**: `BUCKETS_1_2_EXECUTIVE_SUMMARY.md`
**Length**: ~8 pages
**Best For**: Quick understanding, stakeholder communication, decision-making

**Contains**:
- High-level findings (80% vision alignment)
- 5 critical insights
- Top 3 priorities for next quarter
- Vision alignment by dimension (Location, Condition, Economics, Climate, Resale)
- Implementation roadmap (3-month plan)
- Risk assessment
- Success metrics
- Comparison table: Vision vs Implementation

**Key Takeaway**:
> "The PHX Houses project has a solid foundation (kill-switch + 600-point scoring) with clear opportunities to improve from 80% → 95%+ vision alignment in 8-12 weeks with focused effort on kill-switch flexibility, foundation assessment, and interpretability."

---

### 2. DETAILED ANALYSIS (Technical Deep Dive)
**File**: `BUYBOX_CRITERIA_ANALYSIS.md`
**Length**: ~25 pages
**Best For**: Technical architects, product leads, comprehensive understanding

**Contains**:
- **Bucket 1**: Project vision & goals breakdown
  - What vision states vs what's implemented
  - Full implementation status assessment
  - Missing/underdeveloped features

- **Bucket 2**: Buy-box criteria detailed analysis
  - Kill-switch criteria (HARD + SOFT)
  - 600-point scoring breakdown (Sections A/B/C)
  - Coverage analysis by vision dimension
  - Interpretability assessment
  - Data preservation architecture
  - Strategic gaps & opportunities (Priorities 1-3)
  - Kill-switch strategy critique
  - Summary scorecard

**Key Findings**:
- Kill-switch system: EXCELLENT (7 criteria, clear logic)
- Scoring system: GOOD (18 criteria, well-documented)
- Arizona-specific: GOOD (60-85% coverage)
- Major gaps: Zoning, foundation, energy efficiency, interpretability
- Quick wins available: Section breakdowns, rubrics, scenario calculator

---

### 3. REFINEMENT ROADMAP (Strategic Action Plan)
**File**: `SCORING_REFINEMENT_ROADMAP.md`
**Length**: ~30 pages
**Best For**: Engineers, product managers, implementation teams

**Contains**:
- **3 Biggest Opportunities** (Quick Start)
  1. Kill-switch flexibility tiers (1-2 weeks, HIGH ROI)
  2. Section-level score breakdowns (1 day, HIGH CLARITY)
  3. Foundation + HVAC assessment (2-3 weeks, HIGH IMPACT)

- **6 Medium-Term Initiatives** (2-4 weeks each)
  4. Commute cost monetization
  5. Visual scoring rubrics for consistency
  6. What-if scenario calculator

- **3 Strategic Initiatives** (1+ months each)
  7. Zoning & development risk layer
  8. Energy efficiency modeling
  9. Decision support dashboard

- **Implementation Details for Each Initiative**:
  - Problem statement
  - Proposed solution (with code examples)
  - Impact assessment
  - Implementation steps
  - File changes needed

- **Priority Matrix**: Visual guide to effort vs impact
- **Recommended Execution Order**: 4 sprints, 3 months
- **Success Metrics**: Near/medium/long-term

**Key Recommendations**:
```
Sprint 1 (2 weeks): Kill-switch flexibility + section breakdowns
Sprint 2 (2 weeks): Foundation/HVAC + visual rubrics + commute cost
Sprint 3 (2-3 weeks): What-if scenarios + percentile ranking + insights
Sprint 4+ (Strategic): Zoning, energy, dashboard
```

---

## HOW TO USE THESE DOCUMENTS

### For Executives/Decision Makers
1. Read **Executive Summary** (10 min)
2. Focus on "Top 3 Priorities" section
3. Review "Implementation Roadmap" for timeline
4. Make go/no-go decision on 3-month plan

### For Product Managers
1. Read **Executive Summary** (10 min)
2. Review "Vision Alignment by Dimension" table
3. Go to **Detailed Analysis** sections on specific dimensions
4. Use **Roadmap** for sprint planning

### For Engineers
1. Read **Executive Summary** (10 min)
2. Jump to **Roadmap** section on specific initiative
3. Review "Implementation Steps" + "File Changes Needed"
4. Use as development checklist

### For Architects
1. Read **Executive Summary** (10 min)
2. Review **Detailed Analysis** "Buy-Box Architecture" section
3. Go to **Roadmap** for architectural implications
4. Check "Comparison: Vision vs Implementation" table

---

## KEY STATISTICS

### Vision Alignment
- **Overall**: 80% → 95% goal (8-12 week effort)
- **By Dimension**:
  - Location: 78% (7/9 factors)
  - Condition: 64% (4.5/7 factors)
  - Economics: 83% (5/6 factors)
  - Climate: 38% (1.5/4 factors)
  - Resale: 42% (2.5/6 factors)
  - Interpretability: 30% (major gap)

### Implementation Status
- **Kill-switch**: 100% complete (7 criteria working)
- **600-point scoring**: 95% complete (18/18 criteria defined)
- **Data preservation**: 100% (CSV + JSON architecture solid)
- **Arizona-specific**: 60-85% (good coverage, some gaps)

### Effort Estimates
- Quick wins (#1-3): 4-7 weeks total
- Medium-term (#4-6): 6-8 weeks total
- Strategic (#7-9): 10-12 weeks total
- **Full implementation**: 8-12 weeks with 1-2 engineers

---

## CRITICAL INSIGHTS FROM ANALYSIS

### Insight #1: Kill-Switch Too Strict
**Current**: NO HOA at all, minimum 4 beds/2 baths
**Problem**: Filters 20-30% of potentially good properties
**Solution**: Add flexibility tiers (CRITICAL, FIRM, SOFT)
**Priority**: HIGH (Priority #1)

### Insight #2: Systems Scores Are Weak
**Current**: Section B averages 56% utilization
**Problem**: Foundation not scored, HVAC implicit, roof aging
**Solution**: Add Foundation + HVAC assessment (40+20 pts)
**Priority**: HIGH (Priority #3)

### Insight #3: Commute Cost Ignored
**Current**: Property cost $3,200/mo regardless of 5-mile or 30-mile commute
**Problem**: Underestimates true affordability burden
**Solution**: Monetize commute (add $100-600/mo depending on distance)
**Priority**: MEDIUM (Priority #4)

### Insight #4: Lack of Interpretability
**Current**: Score 415 = Contender (no explanation)
**Problem**: Users don't understand decision drivers
**Solution**: Section breakdowns + what-if + percentile ranking
**Priority**: MEDIUM (Priority #2)

### Insight #5: Zoning & Growth Not Modeled
**Current**: Zero zoning assessment
**Problem**: Can't evaluate long-term property appreciation/risk
**Solution**: Add Phase 0.5 zoning + development pipeline layer
**Priority**: LOW/STRATEGIC (Priority #7)

---

## QUICK DECISION MATRIX

**Should we proceed with refinements?**

| Factor | Assessment |
|--------|-----------|
| **Vision Alignment** | 80% (good, but could be better) |
| **User Need** | High (interpretability, decision support) |
| **Technical Feasibility** | High (all changes additive, no breaking) |
| **Effort Required** | Medium (8-12 weeks, 1-2 engineers) |
| **ROI** | Very High (impacts 20-30% more properties, better decisions) |
| **Risk Level** | Low (existing system stays working) |
| **Timeline** | Q4 2025 (start immediately) |

**Recommendation**: **PROCEED immediately with Priority #1-3 (4-7 weeks). Follow with strategic initiatives if resources allow.**

---

## HOW THESE INSIGHTS CONNECT

```
VISION (Buckets 1 & 2)
├── Location factors
│   ├── ✓ Implemented (schools, safety, amenities)
│   ├── ✗ Missing (zoning, growth) → Priority #7
│   └── ◐ Weak (commute not monetized) → Priority #4
│
├── Condition factors
│   ├── ✓ Roof, plumbing/electrical
│   ├── ✗ Missing (foundation) → Priority #3
│   └── ◐ Weak (HVAC implicit) → Priority #3
│
├── Economics factors
│   ├── ✓ Tax, HOA, utilities
│   └── ✗ Missing (commute cost) → Priority #4
│
├── Climate factors
│   ├── ◐ Weak (heat implicit) → Priority #8
│   └── ✗ Missing (xeriscape, power modeling) → Priority #8
│
├── Resale factors
│   ├── ◐ Weak (energy implicit, patio missing) → Priority #8
│   └── Limited (outdoor spaces) → Priority #8
│
└── INTERPRETABILITY (all factors)
    └── ✗ Weak (no decision rationale) → Priority #2
        ├── Need: Section breakdowns
        ├── Need: What-if scenarios
        ├── Need: Percentile ranking
        └── Need: Offer strategy guidance → Priority #9
```

---

## FILE ORGANIZATION

```
docs/artifacts/
├── BUCKETS_1_2_EXECUTIVE_SUMMARY.md      ← Start here!
├── BUYBOX_CRITERIA_ANALYSIS.md           ← Technical deep dive
├── SCORING_REFINEMENT_ROADMAP.md         ← Implementation guide
└── ANALYSIS_INDEX.md                     ← This file
```

---

## DOCUMENT LINEAGE & DEPENDENCIES

**For reading in order of detail**:
1. **BUCKETS_1_2_EXECUTIVE_SUMMARY.md** (10-15 min)
   - High-level overview
   - Decision-making summary
   - 3 priorities identified

2. **BUYBOX_CRITERIA_ANALYSIS.md** (30-45 min)
   - Technical breakdown
   - Vision vs implementation details
   - Gap analysis
   - Strategic opportunities explored

3. **SCORING_REFINEMENT_ROADMAP.md** (30-60 min)
   - Implementation details
   - Step-by-step guidance
   - Code examples
   - Sprint planning

4. **ANALYSIS_INDEX.md** (5-10 min) ← You are here
   - Navigation guide
   - Quick reference
   - Decision matrix

---

## CROSS-REFERENCES TO SOURCE CODE

### Kill-Switch System
- **Main implementation**: `src/phx_home_analysis/services/kill_switch/constants.py` (89 lines)
- **Compatibility layer**: `scripts/lib/kill_switch.py` (755 lines)
- **Criteria definitions**: Lines 197-247 in kill_switch.py
- **Verdict logic**: Lines 254-272 in kill_switch.py

### Scoring System
- **Weights definition**: `src/phx_home_analysis/config/scoring_weights.py` (366 lines)
- **Constants**: `src/phx_home_analysis/config/constants.py` (601 lines)
- **Strategies**: `src/phx_home_analysis/services/scoring/strategies/` (5 files)
  - location.py (450+ lines)
  - systems.py (300+ lines)
  - interior.py (200+ lines)
  - cost_efficiency.py (150+ lines)

### Domain Entities
- **Property entity**: `src/phx_home_analysis/domain/entities.py` (100+ lines)
- **Enums**: `src/phx_home_analysis/domain/enums.py`
- **Value objects**: `src/phx_home_analysis/domain/value_objects.py`

### Scripts
- **Main analyzer**: `scripts/phx_home_analyzer.py`
- **County data**: `scripts/extract_county_data.py`
- **Images**: `scripts/extract_images.py`
- **Deal sheets**: `scripts/deal_sheets/renderer.py`

---

## GLOSSARY OF TERMS

**Buckets**: High-level categories in requirements gathering
- Bucket 1: Project Vision & Goals
- Bucket 2: Buy-Box Criteria (Decision DNA)

**Kill-Switch**: Filtering logic that marks properties as PASS/WARNING/FAIL
- HARD criteria: Instant fail (HOA, beds, baths)
- SOFT criteria: Weighted severity (sewer, garage, lot, year)

**Scoring System**: 600-point weighted ranking
- Section A (Location): 250 pts
- Section B (Systems): 170 pts
- Section C (Interior): 180 pts

**Tier**: Classification based on score
- Unicorn: >480 pts (80%+)
- Contender: 360-480 pts (60-80%)
- Pass: <360 pts (<60%)

**Vision Alignment**: How well implementation matches original vision requirements (target: 95%+, current: 80%)

**Arizona-Specific**: Climate/market factors unique to Arizona
- HVAC lifespan (12yr not 20yr)
- Pool ownership costs ($250-400/mo)
- Solar lease treatment (liability not asset)
- Orientation impact (cooling costs)

**Phase**: Pipeline stage for data enrichment
- Phase 0: County API extraction
- Phase 1: Listing images + location data
- Phase 2: Image-based visual assessment
- Phase 3: Scoring + synthesis
- Phase 4: Reporting

---

## NEXT STEPS

### Immediate (This Week)
- [ ] Share Executive Summary with team
- [ ] Review "Top 3 Priorities" as a group
- [ ] Identify owner for Priority #1 (kill-switch flexibility)

### Short-term (Next 2 Weeks)
- [ ] Assign engineers to Priorities #1-3
- [ ] Break down Priority #1 into tasks
- [ ] Set up sprint board with milestones
- [ ] Start Priority #1 implementation

### Medium-term (Weeks 3-8)
- [ ] Complete Priorities #1-3 (section breakdowns, kill-switch, foundation)
- [ ] Review results and impact on property pass rate
- [ ] Plan Priorities #4-6 (commute, rubrics, what-if)

### Long-term (Weeks 9+)
- [ ] Execute Priorities #4-6
- [ ] Consider strategic initiatives (#7-9) based on feedback
- [ ] Plan Q1 2026 roadmap

---

## QUESTIONS TO DISCUSS WITH TEAM

### Strategic Level
1. **Kill-Switch Philosophy**: Should we maintain strict all-or-nothing (HOA $0, 4 beds, 2 baths), or shift to flexibility tiers?
2. **Interpretability**: How important is "understanding why" vs just getting a tier classification?
3. **Scope**: Should we tackle zoning/energy/dashboard now, or defer to Q1 2026?

### Tactical Level
1. **Foundation Assessment**: How to integrate Phase 2 image-assessor into foundation scoring?
2. **Commute Cost**: What work address(es) should we use for commute calculation?
3. **Visual Rubrics**: Who will define the 5-point scoring rubrics for image assessment?

### Data/Architecture Level
1. **Section A Expansion**: If we add zoning (25 pts), do we stay at 600 total or expand?
2. **HVAC Scoring**: Where in Section B does HVAC go if we keep 170 pts limit?
3. **Re-scoring**: Do we automatically recalculate all properties when criteria change?

---

## RESOURCES & REFERENCES

### Project Documentation
- **CLAUDE.md** (project root): High-level project overview
- **toolkit.json**: Tool hierarchy and relationships
- **context-management.json**: State tracking and protocols
- **AGENT_BRIEFING.md**: Agent shared context

### Scoring/Kill-Switch Files
- `src/phx_home_analysis/config/scoring_weights.py` - Detailed weight definitions
- `src/phx_home_analysis/config/constants.py` - All configuration constants
- `scripts/lib/kill_switch.py` - Kill-switch evaluation logic

### Agents
- `.claude/agents/image-assessor.md` - Phase 2 visual scoring (uses rubrics)
- `.claude/agents/map-analyzer.md` - Phase 1 location data
- `.claude/agents/listing-browser.md` - Phase 1 image extraction

### Data Files
- `data/phx_homes.csv` - Base listings
- `data/enrichment_data.json` - Enriched property data
- `data/work_items.json` - Pipeline state tracking

---

## FINAL RECOMMENDATION

**Status**: 80% vision alignment achieved
**Path Forward**: Clear 3-month roadmap to 95%+
**Investment**: 1-2 engineers, 8-12 weeks
**ROI**: Dramatically improved decision support, 20-30% broader property coverage
**Risk**: Low (all additive, no breaking changes)

**Decision**: **Proceed with Priority #1-3 (kill-switch flexibility, section breakdowns, foundation assessment) immediately. Follow with Priorities #4-6 as resources allow. Consider strategic initiatives (#7-9) for Q1 2026.**

---

**Analysis Complete**: 2025-12-03
**Next Review**: Post-implementation (after Priority #1-3 completion)
**Contact**: [Your name/team for questions on this analysis]


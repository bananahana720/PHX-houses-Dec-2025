# Architecture Review - Document Index
## PHX Houses Analysis Pipeline | December 3, 2025

This index guides you through the comprehensive cross-cutting concerns architecture review.

---

## Quick Start (15 minutes)

**Start here if you want the executive summary:**

1. Read: `ARCHITECTURE_REVIEW_SUMMARY.txt` (this document)
   - System health scorecard
   - Key findings for each theme
   - Recommended action plan
   - Risk assessment

2. Skim: `ARCHITECTURE_QUICK_REFERENCE.md`
   - System overview diagram
   - Kill-switch and scoring criteria matrices
   - Configuration locations
   - Risk scorecard

---

## Deep Dive (2-3 hours)

**Read if you're implementing changes or need full context:**

### Theme 1: TRACEABILITY
**Why it matters**: Can't explain why a property scored 425 vs. 400; no audit trail for criteria changes

**Documents**:
- `CROSS_CUTTING_ANALYSIS.md` → Section 1 (Traceability Analysis)
  - Current state: 3/10
  - Problems: No field-level lineage, no scoring audit trail
  - Recommendations: Add metadata, create field_lineage.json, implement scoring lineage
  - Timeline: 1-2 weeks

- `IMPLEMENTATION_EXAMPLES.md` → Section 1 (Traceability Implementation)
  - FieldMetadata dataclass with source, confidence, extracted_at
  - EnrichmentDataWithMetadata wrapper with backward compatibility
  - ScoringStrategyResult and CompleteScoringLineage models
  - ExplainablePropertyScorer that captures lineage

### Theme 2: EVOLVABILITY
**Why it matters**: Can't change kill-switch criteria without code edits; no version history for scores

**Documents**:
- `CROSS_CUTTING_ANALYSIS.md` → Section 2 (Evolvability Analysis)
  - Current state: 5/10
  - Problems: Hard-coded phase dependencies, criteria in config, raw data not preserved
  - Recommendations: Externalize buyer profile, create phase DAG, version configurations
  - Timeline: 3-4 weeks

- `IMPLEMENTATION_EXAMPLES.md` → Section 2 (Evolvability Implementation)
  - Sample buyer_profile.json with hard/soft criteria
  - BuyerProfile loader with dynamic evaluation
  - Phase DAG configuration with execution order
  - ConfigurableKillSwitchFilter that loads criteria from JSON

### Theme 3: EXPLAINABILITY
**Why it matters**: Users can't understand why property FAILED or scored X; no reasoning chains

**Documents**:
- `CROSS_CUTTING_ANALYSIS.md` → Section 3 (Explainability Analysis)
  - Current state: 4/10
  - Problems: Scoring is black box, verdicts lack context, no confidence signals
  - Recommendations: Add scoring explanation, verdict narratives, sensitivity analysis
  - Timeline: 1-2 weeks

- `IMPLEMENTATION_EXAMPLES.md` → Section 3 (Explainability Implementation)
  - KillSwitchVerdictExplanation dataclass with detailed breakdown
  - ExplainableKillSwitchFilter with narrative generation
  - CriterionEvaluation model for transparent criterion checking
  - Example: "Severity 6.0 > threshold 3.0, FAIL" with per-criterion detail

### Theme 4: AUTONOMY
**Why it matters**: Serial property processing is slow; can't parallelize; phases can't communicate

**Documents**:
- `CROSS_CUTTING_ANALYSIS.md` → Section 4 (Autonomy Analysis)
  - Current state: 8/10 (phase orchestration works, but serial processing)
  - Problems: No parallel processing, no inter-phase communication, no cost awareness
  - Recommendations: Parallel orchestrator, DAG-based execution, graceful degradation
  - Timeline: 3-4 weeks

- `IMPLEMENTATION_EXAMPLES.md` → Section 4 (Autonomy Implementation)
  - ParallelPropertyOrchestrator with ThreadPoolExecutor
  - Phase execution with automatic retry and exponential backoff
  - PropertyProcessingResult tracking phases_completed and phases_failed
  - Example: Process 8 properties in parallel, handle dependency blocking

---

## Reference Materials

### Configuration & System Design
- `ARCHITECTURE_QUICK_REFERENCE.md` → Configuration Locations
  - Which settings are hard-coded (❌) vs. configurable (✅)
  - Current location of each configuration
  - Where they should move to

### Risk & Metrics
- `ARCHITECTURE_QUICK_REFERENCE.md` → Risk Scorecard
  - High-risk issues requiring immediate attention
  - Medium-risk technical debt
  - Metrics to establish for system health

### Data Models
- `CROSS_CUTTING_ANALYSIS.md` → Section 1.2 (Architecture Problems)
  - Current enrichment_data.json structure
  - Desired structure with metadata wrapping
  - Backward compatibility strategy

---

## Implementation Timeline

### WEEK 1: Foundation (Critical)
**Effort**: 3 days | **Impact**: HIGH | **Risk**: LOW
- [ ] Add field metadata to enrichment_data.json
- [ ] Create scoring explanation model
- [ ] Extract kill-switch to buyer_profile.json
- [ ] Update validation schemas

**Documents to reference**:
- `IMPLEMENTATION_EXAMPLES.md` Section 1.1 & 2.1
- `CROSS_CUTTING_ANALYSIS.md` Section 1.3 & 2.2

### WEEK 2: Intelligence (Quality)
**Effort**: 3 days | **Impact**: HIGH | **Risk**: LOW
- [ ] Implement scoring lineage capture
- [ ] Create kill-switch verdict explanations
- [ ] Add confidence scoring
- [ ] Build verdict narrative generator

**Documents to reference**:
- `IMPLEMENTATION_EXAMPLES.md` Section 1.2 & 3.1
- `CROSS_CUTTING_ANALYSIS.md` Section 3.2

### WEEK 3: Performance (Autonomy)
**Effort**: 3 days | **Impact**: MEDIUM | **Risk**: MEDIUM
- [ ] Implement parallel property processing
- [ ] Add automatic retry logic
- [ ] Create graceful degradation
- [ ] Implement inter-phase communication

**Documents to reference**:
- `IMPLEMENTATION_EXAMPLES.md` Section 4.1
- `CROSS_CUTTING_ANALYSIS.md` Section 4.3

### MONTH 2: Advanced (Long-term)
**Effort**: 5-7 days | **Impact**: MEDIUM | **Risk**: MEDIUM
- [ ] Versioned configuration system
- [ ] Feature flags for gradual rollout
- [ ] Cost tracking and budget alerts
- [ ] Automatic rollback capability

**Documents to reference**:
- `CROSS_CUTTING_ANALYSIS.md` Sections 1.3, 2.2, 4.3

---

## Key Code Locations to Modify

### Phase 1 Changes (Week 1)
```
src/phx_home_analysis/
├─ domain/value_objects.py          ← Add FieldMetadata
├─ validation/schemas.py             ← Update EnrichmentDataSchema
├─ repositories/json_repository.py   ← Handle metadata wrapping
└─ services/kill_switch/
   └─ buyer_profile.py              ← New file: BuyerProfile loader
```

### Phase 2 Changes (Week 2)
```
src/phx_home_analysis/
├─ services/scoring/
│  ├─ lineage.py                    ← New file: Lineage models
│  └─ scorer.py                     ← Add lineage capture
└─ services/kill_switch/
   ├─ verdict.py                    ← New file: Verdict explanation
   └─ filter.py                     ← Add explanations
```

### Phase 3 Changes (Week 3)
```
src/phx_home_analysis/
├─ pipeline/
│  ├─ phase_dag.py                  ← New file: DAG configuration
│  └─ parallel_orchestrator.py       ← New file: Parallel execution
└─ config/
   └─ constants.py                  ← Remove (move to JSON)
```

---

## Critical Success Factors

**1. Atomicity** (Data Safety)
- Problem: enrichment_data.json is LIST, not dict
- Solution: Always use temp file + os.replace() for writes
- Reference: `CROSS_CUTTING_ANALYSIS.md` Section 5 (Risk 1)

**2. Backward Compatibility** (No Breaking Changes)
- Problem: Existing code expects raw values, not metadata objects
- Solution: Make metadata optional, fallback to raw values
- Reference: `IMPLEMENTATION_EXAMPLES.md` Section 1.1 (FieldMetadata usage)

**3. Minimal Disruption** (Preserve Current Flow)
- Problem: Hard-coded phase names in agents, work_items structure
- Solution: Extend system without replacing; phase names can stay
- Reference: `CROSS_CUTTING_ANALYSIS.md` Section 2.1 (Problem 1)

**4. Validation** (No Data Loss)
- Problem: Migration could corrupt property data
- Solution: Run reconciliation script before/after changes
- Reference: `IMPLEMENTATION_EXAMPLES.md` → Add validation examples

---

## Decision Points for Your Team

### Question 1: Schema Versioning
**Issue**: Do we increment _schema_version for each change?

**Options**:
A) Semantic versioning (1.0.0 → 1.1.0 for backwards-compatible)
B) Timestamp-based (2025-12-03-v1)
C) Auto-migrating (loader handles all versions)

**Recommendation**: Option C (auto-migrating loader)
- Reference: `CROSS_CUTTING_ANALYSIS.md` Section 2.2 (Medium-term recommendations)

### Question 2: Metadata Overhead
**Issue**: Adding metadata fields increases JSON size; OK with trade-off?

**Current**: enrichment_data.json ≈ 50KB
**After**: enrichment_data.json ≈ 150KB (3x growth)

**Options**:
A) Accept overhead (disk is cheap)
B) Compress metadata separately
C) Store in separate file (field_lineage.json)

**Recommendation**: Option A + optional archival of old versions
- Reference: `CROSS_CUTTING_ANALYSIS.md` Section 1.3 (Short-term recommendations)

### Question 3: Parallel Processing Scope
**Issue**: Thread-based or async-based or distributed?

**Options**:
A) ThreadPoolExecutor (simplest, for CPU-bound phases)
B) AsyncIO (better for I/O-bound phases)
C) Celery/Temporal (distributed, for scale)

**Recommendation**: Option A (thread-based) for Week 3, Option C later
- Reference: `IMPLEMENTATION_EXAMPLES.md` Section 4.1

---

## Metrics Dashboard (to be established)

Before implementing changes, set up these metrics:

### System Health (Target: 8/10+ for each)
```
Traceability Score:   [Currently 3/10]
Evolvability Score:   [Currently 5/10]
Explainability Score: [Currently 4/10]
Autonomy Score:       [Currently 8/10]
```

### Pipeline Performance
```
Properties/week:        [Measure baseline]
Time/property:          [Measure baseline]
Phase success rate:     [Measure baseline]
Cost/property:          [Measure baseline]
Data freshness (days):  [Measure baseline]
```

Monitor these weekly during implementation.

---

## FAQ

**Q: Do I need to refactor the Property entity?**
A: No. Add new models alongside existing ones. Reference: Section 1.1 of Implementation Examples

**Q: Will this break existing agents?**
A: No. Agent changes are minimal (they'll just see richer data). Reference: CLAUDE.md for agent protocol

**Q: How do I handle the transition period?**
A: Gradual rollout. Week 1 adds metadata fields (optional); old code ignores them. Week 2+ uses them.

**Q: What if the buyer profile changes frequently?**
A: That's the point! No code changes needed. Just update buyer_profile.json and re-score.

**Q: Can I A/B test different scoring algorithms?**
A: Yes. Create scoring_v1.json and scoring_v2.json, load by feature flag. Reference: Section 2.2

---

## Document Sizes & Read Times

| Document | Size | Read Time | Purpose |
|----------|------|-----------|---------|
| ARCHITECTURE_REVIEW_SUMMARY.txt | 10KB | 15 min | Executive summary |
| ARCHITECTURE_QUICK_REFERENCE.md | 15KB | 20 min | Quick lookup tables |
| CROSS_CUTTING_ANALYSIS.md | 46KB | 90 min | Detailed analysis |
| IMPLEMENTATION_EXAMPLES.md | 41KB | 60 min | Code examples |
| **Total** | **112KB** | **185 min** | **Complete review** |

---

## Next Actions

1. **This week**: Read ARCHITECTURE_REVIEW_SUMMARY.txt + skim QUICK_REFERENCE
2. **Next week**: Deep dive into CROSS_CUTTING_ANALYSIS.md (by theme)
3. **Week 2**: Review IMPLEMENTATION_EXAMPLES.md with team
4. **Week 3**: Create Week 1 implementation tickets

---

## Questions or Clarifications?

Each document has a detailed Table of Contents. Use Ctrl+F to search within documents:
- `CROSS_CUTTING_ANALYSIS.md`: Search for "Problem", "Recommendation", "Risk"
- `IMPLEMENTATION_EXAMPLES.md`: Search for "Before/After" code examples
- `ARCHITECTURE_QUICK_REFERENCE.md`: Use as quick lookup reference

---

**Review Completed**: December 3, 2025
**Reviewer**: Claude Code (Software Architect)
**Status**: Ready for Implementation Planning

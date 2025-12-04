# Section 3: Gap Clusters

### Cluster A: Image Pipeline Infrastructure (12 gaps, IP-01 to IP-12)
**Severity**: 5 CRITICAL, 3 HIGH, 4 MEDIUM
**Total Effort**: 30 days
**Business Impact**: BLOCKING - System cannot handle batch processing >5 properties

**Dependencies**:
1. IP-01 (job queue architecture) - MUST do first
2. IP-02 (job queue implementation) - parallel to IP-01
3. IP-03 (worker pool) - after IP-01/IP-02
4. IP-04 (progress visibility) - parallel to IP-01

**Recommended Order**:
```
Week 1: IP-01, IP-02, IP-04 (foundation + visibility)
Week 2: IP-03 (worker pool), IP-05 (retries), IP-07 (backoff)
Week 3: IP-06, IP-08, IP-09 (resilience)
Week 4: IP-10, IP-11, IP-12 (optimization)
```

### Cluster B: Explainability & Reasoning (4 gaps, XT-09 to XT-12)
**Severity**: 1 CRITICAL, 2 HIGH, 1 LOW
**Total Effort**: 8 days
**Business Impact**: HIGH - UX blocker; users don't understand system output

**Dependencies**:
1. XT-01 (field lineage) - prerequisite for tracing score components
2. Score breakdown structures must be enhanced

**Recommended Order**:
```
Step 1: Enhance PropertyScorer to return reasoning text (3 days)
Step 2: Add KillSwitchFilter explanation generation (1 day)
Step 3: Add CostEstimator component breakdown (2 days)
Step 4: Add TierClassifier "next tier" guidance (2 days)
```

### Cluster C: Traceability & Audit (4 gaps, XT-01 to XT-04)
**Severity**: 1 CRITICAL, 1 HIGH, 2 MEDIUM
**Total Effort**: 10 days
**Business Impact**: MEDIUM - Compliance/audit gap; data quality concerns

**Dependencies**:
1. XT-01 (field lineage) must be done first; blocks XT-02/XT-03

**Recommended Order**:
```
Step 1: Implement field lineage population (3 days)
Step 2: Add schema versioning (2 days)
Step 3: Add mutation audit logging (2 days)
Step 4: Index extraction logs (1 day)
```

### Cluster D: Scoring Enrichment (8 gaps, VB-01 to VB-08)
**Severity**: 2 HIGH, 6 MEDIUM/LOW
**Total Effort**: 25 days
**Business Impact**: MEDIUM - Completeness; impacts property selection accuracy

**Dependencies**:
1. VB-01 (interpretability) requires XT-09 (scoring reasoning)
2. VB-03 (foundation assessment) can be done in parallel with others

**Recommended Order**:
```
Step 1: Implement foundation assessment service (3 days)
Step 2: Add commute cost monetization (2 days)
Step 3: Add zoning/growth risk service (3 days)
Step 4: Enhance energy efficiency (renovation ROI service exists, just integrate)
```

### Cluster E: Architecture Automation (5 gaps, CA-01 to CA-05)
**Severity**: All MEDIUM/LOW
**Total Effort**: 8 days
**Business Impact**: LOW - Nice-to-have; improves maintainability

**Dependencies**: None; can be done anytime

**Recommended Order**:
```
Sequential; low complexity:
Step 1: Implement auto-CLAUDE.md hooks (2 days)
Step 2: Enforce staleness checks (2 days)
Step 3: Add tool violation linter (1 day)
Step 4: Add skill discovery CLI (1 day)
Step 5: Add KB schema validation (1 day)
```

### Cluster F: Evolvability & Configuration (4 gaps, XT-05 to XT-08)
**Severity**: 2 HIGH, 2 MEDIUM
**Total Effort**: 7 days
**Business Impact**: MEDIUM - Blocks A/B testing, configuration management

**Dependencies**: None; can be done in parallel

**Recommended Order**:
```
Step 1: Externalize kill-switch criteria to YAML (1 day)
Step 2: Add scoring weight versioning (1 day)
Step 3: Implement feature flag system (2 days)
Step 4: Move all constants to env vars (2 days)
```

---

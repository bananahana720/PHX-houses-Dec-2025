# Section 7: Implementation Roadmap

### Phase 1: Production Readiness (Weeks 1-4) - FIX BLOCKING ISSUES
**Goals**: Image pipeline operational, scoring explainable, data traceable

```
Week 1: Image Pipeline Foundation (IP-01, IP-02, IP-04, CA-02)
├── Design job queue abstraction (1 day)
├── Implement Pydantic job models (1 day)
├── Wire job queue into orchestrator (1 day)
├── Add progress logging (1 day)
└── Add runtime staleness checks (1 day)
Effort: 5 days | Team: 1 engineer

Week 2: Explanation Layer (XT-09, XT-10, VB-01)
├── Design reasoning generation service (1 day)
├── Implement score explanation templates (1 day)
├── Add kill-switch verdict reasons (1 day)
├── Test with 10 properties (1 day)
└── User acceptance testing (1 day)
Effort: 5 days | Team: 1 engineer

Week 3: Data Lineage (XT-01, XT-02, XT-03)
├── Design lineage recorder service (1 day)
├── Implement field_lineage population (1 day)
├── Add mutation audit logging (1 day)
├── Add schema versioning framework (1 day)
└── Backfill lineage for existing data (1 day)
Effort: 5 days | Team: 1 engineer

Week 4: Scoring Enrichment (VB-03, VB-04, VB-05)
├── Implement foundation assessment (2 days)
├── Add commute cost monetization (1 day)
├── Add zoning/growth risk service (1 day)
└── Integration testing (1 day)
Effort: 5 days | Team: 1 engineer

**End of Phase 1**: System production-ready for batch processing. Can handle 30+ properties with explanations and full audit trail.
```

### Phase 2: Scale & Optimize (Weeks 5-8) - HANDLE LARGE BATCHES
**Goals**: Image extraction parallelized, configuration flexible, autonomous

```
Week 5: Worker Pool (IP-03, IP-05, IP-07)
├── Design worker pool abstraction (1 day)
├── Implement retry logic with backoff (1 day)
├── Integrate rate limit adaptive strategy (1 day)
└── Load testing with 100 properties (2 days)
Effort: 5 days | Team: 1 engineer

Week 6: Configuration Management (XT-05, XT-06, XT-08)
├── Externalize kill-switch criteria to YAML (1 day)
├── Implement criteria versioning (1 day)
├── Move constants to env vars (1 day)
├── Add feature flag system (1 day)
└── Test config hot-reload (1 day)
Effort: 5 days | Team: 1 engineer

Week 7: Foundation Enhancements (VB-06, VB-07, IP-11, IP-12)
├── Enhance energy efficiency modeling (1 day)
├── Integrate renovation ROI service (1 day)
├── Tune LSH deduplication (1 day)
├── Parallelize image standardizer (1 day)
└── Performance benchmarking (1 day)
Effort: 5 days | Team: 1 engineer

Week 8: Architecture Automation (CA-01, CA-04, XT-04, XT-15)
├── Implement auto-CLAUDE.md hooks (1 day)
├── Add skill discovery CLI (0.5 days)
├── Index extraction logs (0.5 days)
├── Add self-healing for transient failures (1 day)
└── Documentation + training (1.5 days)
Effort: 5 days | Team: 1 engineer

**End of Phase 2**: System scales to 1000+ properties. Configuration-driven. Self-healing.
```

### Phase 3: Analytics & Insights (Weeks 9-12) - MOVE FROM FILTERING TO GUIDANCE
**Goals**: Complete scoring enrichment, property recommendations, portfolio analysis

```
Week 9-10: Remaining VB Gaps
├── VB-02: Kill-switch nuance (severity bands, recommendations)
├── VB-08: Flood insurance cost (FEMA zone lookup table)
Effort: 4 days

Week 11: API & Reporting
├── REST API for property analysis
├── Portfolio comparison dashboard
Effort: 5 days

Week 12: Documentation & Knowledge Transfer
├── Architecture documentation
├── Runbooks for operations
├── Training for end users
Effort: 5 days

**End of Phase 3**: System complete. Ready for public release.
```

---

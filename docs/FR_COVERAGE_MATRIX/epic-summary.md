# Epic Summary

### Epic 1: Foundation & Data Infrastructure
**Objective:** Enable reliable data storage, configuration management, and pipeline execution

**Stories:**
1. E1.S1 - Configuration System Setup (FR46, FR47, FR50, FR51)
2. E1.S2 - Property Data Storage Layer (FR7)
3. E1.S3 - Data Provenance and Lineage Tracking (FR8, FR39)
4. E1.S4 - Pipeline State Checkpointing (FR34, FR37)
5. E1.S5 - Pipeline Resume Capability (FR35, FR38)
6. E1.S6 - Transient Error Recovery (FR36, FR56)

**FRs Covered:** FR7, FR8, FR34-39, FR46-51, FR56
**Total:** 17 FRs (P0: 16, P1: 1)
**User Value:** Crash recovery, data integrity, configuration flexibility

---

### Epic 2: Property Data Acquisition
**Objective:** Gather complete property data from multiple sources

**Stories:**
1. E2.S1 - Batch Analysis CLI Entry Point (FR1)
2. E2.S2 - Maricopa County Assessor API Integration (FR2)
3. E2.S3 - Zillow/Redfin Listing Extraction (FR3, FR61, FR62)
4. E2.S4 - Property Image Download and Caching (FR4)
5. E2.S5 - Google Maps API Geographic Data (FR5)
6. E2.S6 - GreatSchools API School Ratings (FR6)
7. E2.S7 - API Integration Infrastructure (FR58, FR59, FR60)

**FRs Covered:** FR1-6, FR58-62
**Total:** 14 FRs (P0: 14, P1: 0)
**User Value:** Multi-source data integration, API reliability, cost efficiency

---

### Epic 3: Kill-Switch Filtering System
**Objective:** Instantly eliminate properties failing non-negotiable criteria

**Stories:**
1. E3.S1 - HARD Kill-Switch Criteria Implementation (FR9)
2. E3.S2 - SOFT Kill-Switch Severity System (FR10, FR12)
3. E3.S3 - Kill-Switch Verdict Evaluation (FR11)
4. E3.S4 - Kill-Switch Failure Explanations (FR13)
5. E3.S5 - Kill-Switch Configuration Management (FR14, FR49)

**FRs Covered:** FR9-14, FR49
**Total:** 6 FRs (P0: 6, P1: 0)
**User Value:** Deal-breaker detection, transparent criteria

---

### Epic 4: Property Scoring Engine
**Objective:** Rank properties by comprehensive 605-point scoring system

**Stories:**
1. E4.S1 - Three-Dimension Score Calculation (FR15)
2. E4.S2 - 22-Strategy Scoring Implementation (FR16, FR25, FR48)
3. E4.S3 - Tier Classification System (FR17)
4. E4.S4 - Score Breakdown Generation (FR18)
5. E4.S5 - Scoring Weight Adjustment and Re-Scoring (FR19)
6. E4.S6 - Score Delta Tracking (FR20)

**FRs Covered:** FR15-20, FR25, FR48
**Total:** 9 FRs (P0: 6, P1: 3)
**User Value:** Transparent scoring, configurable priorities, fast re-scoring

---

### Epic 5: Multi-Agent Pipeline Orchestration
**Objective:** Coordinate automated multi-phase analysis with specialized agents

**Stories:**
1. E5.S1 - Pipeline Orchestrator CLI (FR28, FR53, FR57)
2. E5.S2 - Sequential Phase Coordination (FR29)
3. E5.S3 - Agent Spawning with Model Selection (FR30)
4. E5.S4 - Phase Prerequisite Validation (FR31)
5. E5.S5 - Parallel Phase 1 Execution (FR32)
6. E5.S6 - Multi-Agent Output Aggregation (FR33)

**FRs Covered:** FR28-33, FR53, FR57
**Total:** 9 FRs (P0: 9, P1: 0)
**User Value:** Automated coordination, parallel processing, reliable orchestration

---

### Epic 6: Visual Analysis & Risk Intelligence
**Objective:** Assess property condition and surface hidden risks proactively

**Stories:**
1. E6.S1 - Property Image Visual Assessment (FR21)
2. E6.S2 - Proactive Warning Generation (FR22)
3. E6.S3 - Risk-to-Consequence Mapping (FR23)
4. E6.S4 - Warning Confidence Levels (FR24)
5. E6.S5 - Foundation Issue Identification (FR26)
6. E6.S6 - HVAC Replacement Timeline Estimation (FR27)

**FRs Covered:** FR21-24, FR26, FR27
**Total:** 7 FRs (P0: 3, P1: 4)
**User Value:** Hidden risk detection, AZ-specific intelligence, proactive warnings

---

### Epic 7: Deal Sheet Generation & Reports
**Objective:** Produce actionable mobile-friendly property intelligence reports

**Stories:**
1. E7.S1 - Deal Sheet HTML Generation (FR40, FR52, FR54, FR55)
2. E7.S2 - Deal Sheet Content Structure (FR41)
3. E7.S3 - Score Explanation Narratives (FR42)
4. E7.S4 - Visual Comparisons (FR43)
5. E7.S5 - Risk Checklists for Tours (FR44)
6. E7.S6 - Deal Sheet Regeneration (FR45)

**FRs Covered:** FR40-45, FR52, FR54, FR55
**Total:** 10 FRs (P0: 0, P1: 4 + shared P0 from other epics)

**User Value:** Mobile-ready reports, decision clarity, tour preparation

---

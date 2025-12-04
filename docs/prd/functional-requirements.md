# Functional Requirements

These functional requirements define the complete capability inventory for PHX Houses Analysis Pipeline. Each requirement is testable, implementation-agnostic, and specifies WHO can do WHAT.

### Property Data Acquisition

**FR1:** [P0] User can initiate batch property analysis for multiple properties via CLI command

**FR2:** [P0] System can fetch authoritative property data from Maricopa County Assessor API (lot size, year built, garage spaces, pool, valuations)

**FR3:** [P0] System can extract listing data from Zillow and Redfin (price, HOA fee, images, listing descriptions, property features)

**FR4:** [P0] System can download and cache property images locally for analysis

**FR5:** [P0] System can extract geographic data from Google Maps API (geocoding, distances to points of interest, orientation determination)

**FR6:** [P0] System can fetch school ratings from GreatSchools API (elementary, middle, high school ratings within catchment area)

**FR7:** [P0] System can preserve raw property data separate from derived scores and analysis

**FR8:** [P0] System can track data provenance (source, confidence level, fetch timestamp) for every data field

### Kill-Switch Filtering

**FR9:** [P0] User can define HARD kill-switch criteria that result in instant property rejection

**FR10:** [P0] User can define SOFT kill-switch criteria with severity weights that accumulate toward threshold

**FR11:** [P0] System can evaluate properties against kill-switch criteria and return PASS/FAIL/WARNING verdicts

**FR12:** [P0] System can calculate severity scores for SOFT criteria violations and compare against configurable threshold

**FR13:** [P0] System can provide detailed explanations for kill-switch failures (which criteria failed, severity accumulation details)

**FR14:** [P0] User can update kill-switch criteria and thresholds via configuration files

### Property Scoring

**FR15:** [P0] System can calculate comprehensive property scores across three dimensions (Location, Systems, Interior)

**FR16:** [P0] System can apply 18+ scoring strategies with configurable weights for each dimension

**FR17:** [P0] System can classify properties into tiers based on total score (Unicorn, Contender, Pass)

**FR18:** [P0] System can generate score breakdowns showing point allocation across all scoring dimensions

**FR19:** [P1] User can adjust scoring weights via configuration files and trigger re-scoring without re-analysis

**FR20:** [P1] System can track score deltas when priorities change (show what changed and by how much)

### Risk Intelligence & Warnings

**FR21:** [P0] System can perform visual assessment of property images to estimate condition and identify potential issues

**FR22:** [P0] System can generate proactive warnings for hidden risks (foundation concerns, HVAC age, solar leases, orientation impacts)
- *Acceptance:* Warning precision ≥80% (≤20% false positive rate); each warning includes risk category, severity, evidence source, and recommended action; validated by post-inspection comparison on 5+ toured properties

**FR23:** [P1] System can map risks to tangible consequences ($cost, quality of life impact, resale impact)
- *Acceptance:* Cost estimates within ±30% of actual repair costs; each consequence includes min/max dollar range with Arizona-specific adjustments; validated by comparing to contractor quotes during due diligence

**FR24:** [P1] System can assign confidence levels to warnings based on data quality and source reliability
- *Acceptance:* Confidence calibration: High=90%+ accuracy (authoritative sources), Medium=70-90% (listing/visual), Low=<70% (inference); auto-downgrade when data >14 days old; validated by tracking confidence vs. inspection outcomes

**FR25:** [P0] System can apply Arizona-specific context to risk assessment (HVAC lifespan, pool costs, cooling impacts)
- *Acceptance:* AZ factors applied: HVAC lifespan 10-15 years, pool cost $250-400/month, west-facing penalty $100-200/month, north-facing 30 points; each factor documented with source; validated annually against current pricing

**FR26:** [P1] System can identify properties with potential foundation issues via visual crack pattern recognition
- *Acceptance:* Recall ≥90% (miss rate ≤10%), precision ≥60% (over-flagging acceptable); severity classification (Minor/Moderate/Severe) with crack type and image reference; validated by comparison to professional inspection reports

**FR27:** [P0] System can estimate HVAC replacement timeline based on system age and Arizona climate factors
- *Acceptance:* Timeline accuracy ±2 years; categories: Immediate (≥13 yrs), Near-term (10-12 yrs), Mid-term (5-9 yrs), Long-term (<5 yrs); includes replacement cost estimate ($7k-$12k); validated by comparing to confirmed system age during inspections

### Multi-Agent Pipeline Orchestration

**FR28:** [P0] User can execute the complete multi-phase analysis pipeline via single CLI command

**FR29:** [P0] System can coordinate sequential phase execution (Phase 0 → Phase 1 → Phase 2 → Phase 3)

**FR30:** [P0] System can spawn specialized agents for each phase with appropriate model selection (Haiku for data, Sonnet for vision)

**FR31:** [P0] System can validate phase prerequisites before spawning next agent (mandatory can_spawn checks)

**FR32:** [P0] System can execute Phase 1 sub-tasks in parallel (listing extraction + map analysis)

**FR33:** [P0] System can aggregate multi-agent outputs into unified property data records

### State Management & Reliability

**FR34:** [P0] System can checkpoint pipeline progress after each phase completion

**FR35:** [P0] System can resume interrupted pipeline execution from last successful checkpoint

**FR36:** [P0] System can detect and recover from transient errors (API rate limits, network issues) via retry logic

**FR37:** [P0] System can preserve previous state before risky operations (rollback capability)

**FR38:** [P0] User can validate pipeline state and data integrity via validation scripts

**FR39:** [P0] System can track which phase/agent populated each data field (lineage tracking)

### Analysis Outputs & Reports

**FR40:** [P0] System can generate comprehensive deal sheets for each analyzed property

**FR41:** [P0] Deal sheets can include property summary, score breakdown, tier classification, kill-switch verdict, and warnings

**FR42:** [P1] System can generate score explanation narratives describing WHY properties scored as they did

**FR43:** [P1] System can generate visual comparisons (radar charts, value spotter scatter plots) for property sets

**FR44:** [P1] System can produce risk checklists for property tours and inspections

**FR45:** [P1] User can regenerate deal sheets and visualizations after re-scoring without re-analysis

### Configuration & Extensibility

**FR46:** [P0] User can externalize scoring weights to YAML configuration files

**FR47:** [P0] User can externalize kill-switch criteria to CSV configuration files

**FR48:** [P1] User can define new scoring dimensions by adding strategies to configuration

**FR49:** [P1] User can add new kill-switch criteria without code changes

**FR50:** [P0] System can load configuration files at runtime and validate against schemas

**FR51:** [P0] User can maintain environment-specific configuration overrides (local vs production)

### CLI User Experience

**FR52:** [P0] User can execute manual phase-specific scripts for testing and debugging

**FR53:** [P0] User can pass flags to control pipeline behavior (--all, --test, --resume, --strict, --dry-run)

**FR54:** [P0] User can view structured console output with progress indicators during analysis

**FR55:** [P0] System can generate both human-readable logs and machine-parseable JSON outputs

**FR56:** [P0] User can access detailed error traces with actionable troubleshooting guidance when failures occur

**FR57:** [P0] User can query pipeline status and view pending tasks via status files

### Integration Management

**FR58:** [P0] System can authenticate with external APIs using environment-variable-based secrets

**FR59:** [P0] System can handle API rate limits gracefully with exponential backoff and retry logic

**FR60:** [P0] System can cache API responses to minimize costs and respect rate limits

**FR61:** [P0] System can rotate browser User-Agents and proxies to bypass anti-bot detection

**FR62:** [P0] System can fall back to alternative extraction methods when primary method fails (nodriver → Playwright)

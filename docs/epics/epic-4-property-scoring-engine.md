# Epic 4: Property Scoring Engine

**User Value:** Rank properties by comprehensive quality score (605 points across Location, Systems, Interior) with transparent breakdowns and tier classification.

**PRD Coverage:** FR15-20, FR25, FR27, FR48
**Architecture References:** ADR-03 (605-Point Scoring System), Scoring System Architecture

---

### E4.S0: Infrastructure Setup (Story Zero)

**Priority:** P0 | **Points:** 5 | **Status:** Ready for Dev

**Objective:** Establish test infrastructure, documentation, and integration scaffolding before main scoring work.

**Scope:**
- Test fixtures and golden properties for 22 strategies
- Score breakdown schema documentation
- Reporting layer stubs (E7 integration)
- Integration audit map (kill-switch → scoring → reporting)

**Acceptance Criteria:**
- [ ] `tests/unit/services/scoring/conftest.py` with shared fixtures
- [ ] 3 golden property fixtures (Unicorn, Contender, Pass tiers)
- [ ] `docs/schemas/score_breakdown_schema.md` created
- [ ] Reporting stub handlers documented
- [ ] Integration map documented

**Estimate:** 5.25 hours
**Dependencies:** E3.S5 (complete), E4.S1 (complete)

---

### E4.S1: Three-Dimension Score Calculation

**Priority:** P0 | **Dependencies:** E1.S2, E2.S7 | **FRs:** FR15

**User Story:** As a system user, I want property scores calculated across three dimensions, so that I can see balanced quality assessment.

**Acceptance Criteria:** **Section A (Location):** 250 pts max. **Section B (Lot & Systems):** 175 pts max. **Section C (Interior):** 180 pts max. **Total:** 605 pts. Missing data scores 0 points (not penalty) with LOW confidence and missing data warning. Breakdown includes section subtotals, percentage of max, and scored_at timestamp.

**Technical Notes:** Implement `PropertyScorer` in `src/phx_home_analysis/services/scoring/`. Use `ScoringWeights` from `src/phx_home_analysis/config/scoring_weights.py`. Store in `scoring` section.

**Definition of Done:** PropertyScorer with sections | ScoreBreakdown dataclass | Partial data handling | Unit tests | Data layer integration

---

### E4.S2: 22-Strategy Scoring Implementation

**Priority:** P0 | **Dependencies:** E4.S1 | **FRs:** FR16, FR25, FR48

**User Story:** As a system user, I want 22 scoring strategies with configurable weights, so that I have comprehensive quality assessment.

**Acceptance Criteria:** **Section A (250 pts):** school_district (42), quietness (30), crime_index (47), supermarket (23), parks_walkability (23), sun_orientation (25: N=25, E=18.75, S=12.5, W=0), flood_risk (23), walk_transit (22), air_quality (15). **Section B (175 pts):** roof_condition (45), backyard_utility (35), plumbing_electrical (35), pool_condition (20), cost_efficiency (35), solar_status (5). **Section C (180 pts):** kitchen_layout (40), master_suite (35), natural_light (30), high_ceilings (25), fireplace (20), laundry_area (20), aesthetics (10).

**Technical Notes:** Each strategy class in `src/phx_home_analysis/services/scoring/strategies/` returns 0-10 scale, scaled by weight. Arizona context: HVAC 10-15 year lifespan, pool $250-400/month.

**Definition of Done:** 22 strategy classes | Weight config from YAML | 0-10 scaling | AZ factors applied | Unit tests per strategy

---

### E4.S3: Tier Classification System

**Priority:** P0 | **Dependencies:** E4.S1 | **FRs:** FR17

**User Story:** As a system user, I want properties classified into tiers, so that I can quickly identify the best options.

**Acceptance Criteria:** **Thresholds:** > 484 (80%) = UNICORN 🦄 green, 363-484 (60-80%) = CONTENDER 🥊 amber, < 363 = PASS ⏭️ gray. Configurable thresholds trigger re-classification with logged changes.

**Technical Notes:** Implement `TierClassifier`. Thresholds: 484 (80%), 363 (60%) of 605. Tier enum. Badge colors per UX spec. Store in `scoring.tier`.

**Definition of Done:** TierClassifier | Tier enum with formatting | Badge emoji/color | Configurable thresholds | Unit tests for boundaries

---

### E4.S4: Score Breakdown Generation

**Priority:** P0 | **Dependencies:** E4.S2, E4.S3 | **FRs:** FR18

**User Story:** As a system user, I want detailed score breakdowns, so that I can see exactly how points were earned.

**Acceptance Criteria:** Each section shows earned/max. Each strategy shows earned/weight, ordered by impact. Deal sheet uses Score Gauge component with expandable Collapsible Details. Drilling shows raw input, calculation logic, and confidence.

**Technical Notes:** Implement `ScoreBreakdownGenerator`. Return: sections[] -> strategies[] -> {points, max, source_data, calculation}. Format for JSON and HTML.

**Definition of Done:** Strategy-level breakdown | Impact ordering | Source linkage | HTML formatting | Unit tests

---

### E4.S5: Scoring Weight Adjustment and Re-Scoring

**Priority:** P1 | **Dependencies:** E4.S4 | **FRs:** FR19

**User Story:** As a system user, I want to adjust scoring weights and re-score without re-analysis, so that I can explore different priorities quickly.

**Acceptance Criteria:** Modified weights must total 605 (validation). Re-scoring uses cached data only (no new API calls), completes < 5 min for 100 properties. Score changes show per-section delta with tier changes and re-ranking.

**Technical Notes:** Implement `RescoringService`. In-memory scoring, batch JSON write. CLI: `python scripts/phx_home_analyzer.py --rescore`.

**Definition of Done:** Weight validation | Re-scoring from cache | Performance < 5 min | Delta calculation | CLI command

---

### E4.S6: Score Delta Tracking

**Priority:** P1 | **Dependencies:** E4.S5 | **FRs:** FR20

**User Story:** As a system user, I want to see score changes when priorities shift, so that I can understand the impact of my changes.

**Acceptance Criteria:** Delta report shows old/new/delta per property with tier changes highlighted, sorted by absolute delta. Drill-down shows section and strategy deltas with largest contributors identified. Display uses green (+) / red (-) coloring with arrow notation (🥊 → 🦄).

**Technical Notes:** Implement `ScoreDeltaTracker`. Store previous in `scoring.previous`. Delta = new - old. Output CSV and JSON. Integration with deal sheet comparison.

**Definition of Done:** Previous score preservation | Multi-level deltas | Tier change detection | Report generation | Deal sheet integration

---

# Sprint 3: Kill-Switch & Scoring

> **Epics**: E3, E4
> **Objective**: Filter properties and calculate comprehensive scores
> **Stories**: 11
> **PRD Coverage**: FR9-20, FR25, FR27, FR48

### Epic E3: Kill-Switch Filtering (5 stories)

#### E3.S1 - HARD Kill-Switch Criteria Implementation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S1 |
| **FRs** | FR9 |

**Acceptance Criteria**:
- [ ] KillSwitchFilter orchestrating all 7 HARD criteria
- [ ] HOA = $0 (any positive = FAIL)
- [ ] Beds >= 4
- [ ] Baths >= 2.0
- [ ] Sqft > 1800
- [ ] Lot > 8000 sqft
- [ ] Garage >= 1 indoor
- [ ] Sewer = city (not septic/unknown)
- [ ] Short-circuit on first HARD failure

**Definition of Done**:
- [ ] KillSwitchFilter in `src/phx_home_analysis/services/kill_switch/`
- [ ] Each criterion as separate class
- [ ] CriterionResult(passed, value, note) return type
- [ ] Unit tests for each criterion with boundary cases

---

#### E3.S2 - SOFT Kill-Switch Severity System

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E3.S1 |
| **FRs** | FR10, FR12 |

**Acceptance Criteria**:
- [ ] SoftSeverityEvaluator with accumulation logic
- [ ] Threshold verdicts: FAIL >= 3.0, WARNING 1.5-3.0, PASS < 1.5
- [ ] **Note**: Currently no SOFT criteria per PRD (all 7 are HARD)
- [ ] Structure allows future addition via config

**Definition of Done**:
- [ ] SoftSeverityEvaluator implemented
- [ ] Configuration-driven criterion loading
- [ ] Documentation for adding future SOFT criteria

---

#### E3.S3 - Kill-Switch Verdict Evaluation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E3.S1, E3.S2 |
| **FRs** | FR11 |

**Acceptance Criteria**:
- [ ] KillSwitchResult dataclass with verdict, failed_criteria, severity, details
- [ ] Multi-failure tracking (all failures listed, not just first)
- [ ] Display formatting: PASS=green, WARNING=amber, FAIL=red

**Definition of Done**:
- [ ] Verdict enum: PASS, WARNING, FAIL
- [ ] Store in kill_switch section of property record
- [ ] Unit tests for verdict scenarios

---

#### E3.S4 - Kill-Switch Failure Explanations

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E3.S3 |
| **FRs** | FR13 |

**Acceptance Criteria**:
- [ ] Human-readable explanations (not technical jargon)
- [ ] Consequence descriptions (e.g., "HOA of $150/month adds to ownership cost")
- [ ] Multi-failure summary ("Failed 2 of 7 criteria")
- [ ] HTML formatting for deal sheets (Warning Card component)

**Definition of Done**:
- [ ] KillSwitchExplainer service
- [ ] Consequence mapping templates
- [ ] Integration with UX Warning Card component

---

#### E3.S5 - Kill-Switch Configuration Management

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S1, E3.S3 |
| **FRs** | FR14, FR49 |

**Acceptance Criteria**:
- [ ] CSV parsing: name, type, operator, threshold, severity, description
- [ ] Operators: ==, !=, >=, <=, >, <, in, not_in
- [ ] Hot-reload capability in dev mode
- [ ] Re-evaluation on config change with delta logging

**Definition of Done**:
- [ ] Configuration file: `config/kill_switch.csv`
- [ ] Pydantic model for criterion definition
- [ ] Watch file changes in dev mode

---

### Epic E4: Property Scoring Engine (6 stories)

#### E4.S1 - Three-Dimension Score Calculation [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S2, E2.S7 |
| **FRs** | FR15 |

**Acceptance Criteria**:
- [ ] Section A (Location & Environment): 250 points
- [ ] Section B (Lot & Systems): 175 points
- [ ] Section C (Interior & Features): 180 points
- [ ] **Total: 605 points** (per Architecture)
- [ ] Missing data = 0 points (not penalty), with confidence indicator

**Definition of Done**:
- [ ] PropertyScorer in `src/phx_home_analysis/services/scoring/`
- [ ] ScoringWeights dataclass from `scoring_weights.py`
- [ ] Store in scoring section of property record
- [ ] Unit tests for scoring calculation

---

#### E4.S2 - 22-Strategy Scoring Implementation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E4.S1 |
| **FRs** | FR16, FR25, FR48 |

**Acceptance Criteria**:

**Section A (250 pts)**:
- [ ] school_district: 42 pts (rating x 4.2)
- [ ] quietness: 30 pts (distance to highways)
- [ ] crime_index: 47 pts (weighted score)
- [ ] supermarket: 23 pts (distance)
- [ ] parks_walkability: 23 pts
- [ ] sun_orientation: 25 pts (N=25, E=18.75, S=12.5, W=0)
- [ ] flood_risk: 23 pts (FEMA zone)
- [ ] walk_transit: 22 pts
- [ ] air_quality: 15 pts

**Section B (175 pts)**:
- [ ] roof_condition: 45 pts
- [ ] backyard_utility: 35 pts
- [ ] plumbing_electrical: 35 pts
- [ ] pool_condition: 20 pts
- [ ] cost_efficiency: 35 pts
- [ ] solar_status: 5 pts

**Section C (180 pts)**:
- [ ] kitchen_layout: 40 pts
- [ ] master_suite: 35 pts
- [ ] natural_light: 30 pts
- [ ] high_ceilings: 25 pts
- [ ] fireplace: 20 pts
- [ ] laundry_area: 20 pts
- [ ] aesthetics: 10 pts

**Definition of Done**:
- [ ] 22 strategy classes in `src/phx_home_analysis/services/scoring/strategies/`
- [ ] Each returns 0-10 scale, multiplied by weight
- [ ] Arizona context applied (HVAC 10-15 years, pool $250-400/month)

---

#### E4.S3 - Tier Classification System

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E4.S1 |
| **FRs** | FR17 |

**Acceptance Criteria**:
- [ ] UNICORN: > 484 pts (80% of 605)
- [ ] CONTENDER: 363-484 pts (60-80% of 605)
- [ ] PASS: < 363 pts (<60% of 605)
- [ ] Badge display: unicorn emoji (green), boxing glove (amber), skip (gray)

**Definition of Done**:
- [ ] TierClassifier in scoring services
- [ ] Tier enum with display formatting
- [ ] Configurable thresholds

---

#### E4.S4 - Score Breakdown Generation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E4.S2, E4.S3 |
| **FRs** | FR18 |

**Acceptance Criteria**:
- [ ] Breakdown: sections[] -> strategies[] -> {points, max, source_data, calculation}
- [ ] Strategies ordered by impact (highest first)
- [ ] Source data linkage with drill-down capability
- [ ] HTML formatting for deal sheets (Score Gauge, Collapsible Details)

**Definition of Done**:
- [ ] ScoreBreakdownGenerator service
- [ ] JSON and HTML output formats
- [ ] Integration with UX components

---

#### E4.S5 - Scoring Weight Adjustment and Re-Scoring

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E4.S4 |
| **FRs** | FR19 |

**Acceptance Criteria**:
- [ ] Weight validation: sum must equal 605
- [ ] Re-scoring from cached data (no new API calls)
- [ ] Performance: < 5 minutes for 100 properties
- [ ] CLI: `python scripts/phx_home_analyzer.py --rescore`

**Definition of Done**:
- [ ] RescoringService implemented
- [ ] Weight validation logic
- [ ] Performance optimization (in-memory scoring)

---

#### E4.S6 - Score Delta Tracking

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E4.S5 |
| **FRs** | FR20 |

**Acceptance Criteria**:
- [ ] Old/new score comparison with delta
- [ ] Tier change highlighting (e.g., "Contender -> Unicorn")
- [ ] Multi-level delta: total, section, strategy
- [ ] Report output: CSV and JSON

**Definition of Done**:
- [ ] ScoreDeltaTracker service
- [ ] Previous scores stored in scoring.previous
- [ ] Deal sheet comparison view integration

---

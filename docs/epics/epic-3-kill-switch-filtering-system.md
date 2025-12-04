# Epic 3: Kill-Switch Filtering System

**User Value:** Instantly eliminate properties that fail non-negotiable criteria (HOA, beds, baths, sqft, lot, garage, sewer) before any scoring, saving time on obviously unsuitable properties.

**PRD Coverage:** FR9-14
**Architecture References:** ADR-04 (All Kill-Switch Criteria Are HARD), Kill-Switch Architecture

---

### E3.S1: HARD Kill-Switch Criteria Implementation

**Priority:** P0 | **Dependencies:** E1.S1 | **FRs:** FR9

**User Story:** As a system user, I want HARD kill-switch criteria that instantly reject properties, so that non-negotiable deal-breakers are caught immediately.

**Acceptance Criteria:** Any HARD criterion failing results in immediate "FAIL" verdict with specific criterion identified; no further evaluation after first failure. **7 HARD Criteria:** HOA must be $0, Beds >= 4, Baths >= 2.0, House SQFT > 1800, Lot > 8000 sqft, Garage >= 1 indoor space, Sewer must be "city". Passing all criteria results in "PASS" with all values recorded.

**Technical Notes:** Implement `KillSwitchFilter` in `src/phx_home_analysis/services/kill_switch/`. Each criterion is separate class returning `CriterionResult(passed, value, note)`. Per Architecture: all 7 are HARD (instant fail).

**Definition of Done:** KillSwitchFilter orchestrating 7 criteria | Individual criterion classes | Short-circuit on first failure | Unit tests with boundary cases | Full flow integration test

---

### E3.S2: SOFT Kill-Switch Severity System

**Priority:** P0 | **Dependencies:** E3.S1 | **FRs:** FR10, FR12

**User Story:** As a system user, I want a SOFT severity system for future flexibility, so that I can add non-critical preferences that accumulate.

**Acceptance Criteria:** SOFT criteria accumulate severity scores; total >= 3.0 = FAIL, 1.5-3.0 = WARNING, < 1.5 = PASS. Currently no SOFT criteria active per PRD (all are HARD). System available for future configuration via config file.

**Technical Notes:** Implement `SoftSeverityEvaluator`. Structure allows future addition via `config/kill_switch.csv`. Example future SOFT: "Pool" (severity 0.5 if no pool wanted but present).

**Definition of Done:** SoftSeverityEvaluator | Threshold-based verdicts | Config-driven loading | Unit tests with simulated SOFT | Future addition documentation

---

### E3.S3: Kill-Switch Verdict Evaluation

**Priority:** P0 | **Dependencies:** E3.S1, E3.S2 | **FRs:** FR11

**User Story:** As a system user, I want a clear verdict (PASS/FAIL/WARNING) for each property, so that I can quickly filter properties.

**Acceptance Criteria:** Result includes overall verdict, failed criteria list, severity score, and timestamp. All failed criteria listed (not just first) with actual vs required values and most impactful highlighted. Display: PASS = 🟢, WARNING = 🟡, FAIL = 🔴 (emoji + text for accessibility).

**Technical Notes:** `KillSwitchResult` dataclass with verdict enum (PASS, WARNING, FAIL). Store in `kill_switch` section. Formatting utilities in `src/phx_home_analysis/reporters/`.

**Definition of Done:** KillSwitchResult dataclass | Verdict determination | Multi-failure tracking | Formatted output | Unit tests

---

### E3.S4: Kill-Switch Failure Explanations

**Priority:** P0 | **Dependencies:** E3.S3 | **FRs:** FR13

**User Story:** As a system user, I want detailed explanations for kill-switch failures, so that I understand exactly why a property was rejected.

**Acceptance Criteria:** Explanation includes criterion name, requirement, actual value, and human-readable consequence (e.g., "This property has HOA of $150/month"). Multiple failures ordered by severity with summary ("Failed 2 of 7 criteria"). HTML displays as warning cards with red border per UX spec.

**Technical Notes:** Implement `KillSwitchExplainer`. Consequence mapping: HOA → "$X/month adds to cost", Sewer → "Septic requires $X maintenance". Templates per criterion. Integration with Warning Card component.

**Definition of Done:** Explanation generation | Multi-failure summary | Consequence mapping | HTML formatting | Unit tests

---

### E3.S5: Kill-Switch Configuration Management

**Priority:** P0 | **Dependencies:** E1.S1, E3.S3 | **FRs:** FR14, FR49

**User Story:** As a system user, I want to update kill-switch criteria via configuration files, so that I can adjust non-negotiables without code changes.

**Acceptance Criteria:** CSV parsed with name, type (HARD/SOFT), threshold, severity, description. Invalid configs rejected with clear errors. Hot-reload in dev mode. New criteria evaluated on all properties without affecting existing data. Changed thresholds trigger re-evaluation with logged verdict changes.

**Technical Notes:** Config file: `config/kill_switch.csv`. Columns: name, type, operator, threshold, severity, description. Operators: ==, !=, >=, <=, >, <, in, not_in. Pydantic validation.

**Definition of Done:** CSV parsing and validation | Criterion model | Hot-reload | Re-evaluation on change | Unit tests

---

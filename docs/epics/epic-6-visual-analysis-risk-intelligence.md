# Epic 6: Visual Analysis & Risk Intelligence

**User Value:** Assess property condition through image analysis and proactively surface hidden risks (foundation issues, HVAC age, solar leases) with Arizona-specific context, enabling confident decisions BEFORE emotional investment.

**PRD Coverage:** FR21-24, FR26-27
**Architecture References:** image-assessor Agent, Section C Scoring, Risk Intelligence

---

### E6.S1: Property Image Visual Assessment

**Priority:** P0 | **Dependencies:** E2.S4, E5.S3 | **FRs:** FR21

**User Story:** As a first-time homebuyer, I want visual assessment of property images by an AI agent, so that interior and exterior condition is scored objectively.

**Acceptance Criteria:** **Section C (180 pts):** kitchen_layout (40), master_suite (35), natural_light (30), high_ceilings (25), fireplace (20), laundry_area (20), aesthetics (10). Raw 0-10 scale multiplied by weight. Kitchen: 8-10 = modern open with island, 5-7 = functional dated, 1-4 = major deficiencies. Missing images default to 5.0 with LOW confidence and warning.

**Technical Notes:** image-assessor uses Sonnet with skills: image-assessment, arizona-context-lite, property-data, state-management, scoring. Process up to 15 images. Cost ~$0.02/image.

**Definition of Done:** Assessment prompts with rubrics | 0-10 scoring | Confidence based on image count | Notes capture | Section C integration | Unit tests

---

### E6.S2: Proactive Warning Generation

**Priority:** P0 | **Dependencies:** E4.S2, E6.S1 | **FRs:** FR22

**User Story:** As a first-time homebuyer, I want proactive warnings for hidden risks surfaced automatically, so that I'm informed BEFORE emotional investment.

**Acceptance Criteria:** **6 Risk Categories:** HVAC age, roof condition, foundation concerns, solar leases, pool equipment age, orientation impact. Each warning has severity (High/Medium/Low), consequence, and action. **Warning Card:** High = red 🚨, Medium = amber ⚠️, Low = gray ℹ️. Precision target >= 80% (<=20% false positives).

**Technical Notes:** Implement `WarningGenerator` in `src/phx_home_analysis/services/risk/`. Thresholds in `config/warning_thresholds.yaml`. Templates in `config/warning_templates.yaml`. Warning Card CSS per UX spec.

**Definition of Done:** WarningGenerator with 6 detectors | Severity classification | Consequence generation | Warning Card HTML/CSS | Unit tests | Precision tracking

---

### E6.S3: Risk-to-Consequence Mapping

**Priority:** P1 | **Dependencies:** E6.S2 | **FRs:** FR23

**User Story:** As a first-time homebuyer, I want risks mapped to tangible consequences (dollars, quality of life, resale), so that I understand REAL IMPACT.

**Acceptance Criteria:** Each risk includes: dollar cost range (e.g., "$7K-$12K"), quality of life impact, resale impact, AZ-specific adjustments (+/-30% accuracy). **HVAC:** $7K-$12K, AZ 10-15 year lifespan, summer failure = 20% premium. **Solar lease:** $15K-$25K transfer, 60% financing rejection, 45+ days longer on market. **Pool:** $3K-$8K equipment, $250-400/month ownership.

**Technical Notes:** Implement `ConsequenceMapper`. Cost sources in `docs/analysis/research/`. Store in `warnings[].consequence` with cost_min, cost_max, qol_impact, resale_impact, recommendation.

**Definition of Done:** ConsequenceMapper | QoL descriptions | Resale assessments | AZ calibration | Template system | Unit tests

---

### E6.S4: Warning Confidence Levels

**Priority:** P1 | **Dependencies:** E6.S3 | **FRs:** FR24

**User Story:** As a first-time homebuyer, I want confidence levels displayed on each warning, so that I know how much to trust each alert.

**Acceptance Criteria:** **HIGH (90%+):** County Assessor, FEMA. **MEDIUM (70-90%):** Zillow, Redfin, image assessment. **LOW (<70%):** inferred data. Data >14 days old degrades one level; >30 days degrades two. Display: HIGH = green, MEDIUM = amber, LOW = gray with source and fetch date. Multi-source = minimum confidence.

**Technical Notes:** Confidence: County=0.95, Google=0.90, GreatSchools=0.90, Zillow/Redfin=0.85, Image=0.80, Inferred=0.50-0.70. Age degradation: -0.15 per threshold.

**Definition of Done:** Confidence calculation | Age degradation | Multi-source minimum | Source attribution | Confidence badge CSS | Unit tests

---

### E6.S5: Foundation Issue Identification

**Priority:** P1 | **Dependencies:** E6.S1 | **FRs:** FR26

**User Story:** As a first-time homebuyer, I want potential foundation issues identified via visual analysis, so that I can budget for inspections and avoid surprises.

**Acceptance Criteria:** **Crack Classification:** Minor (<1/8", Low), Moderate (1/8"-1/4", Medium), Severe (>1/4" or stair-step, High). **Patterns:** Vertical = settling, Horizontal = soil pressure, Stair-step = movement. Image references included. Moderate/Severe recommend $300-$500 structural engineer inspection. Repair costs: Minor $500-$2K, Moderate $2K-$10K, Severe $10K-$50K+. Recall >= 90%, Precision >= 60%.

**Technical Notes:** Foundation via image-assessor with specialized prompts. Conservative approach: over-flag rather than under-flag. Store in `image_assessment.foundation`.

**Definition of Done:** Crack detection prompts | Severity classification | Pattern analysis | Cost estimates | Image tracking | Sample image unit tests

---

### E6.S6: HVAC Replacement Timeline Estimation

**Priority:** P0 | **Dependencies:** E6.S4 | **FRs:** FR27

**User Story:** As a first-time homebuyer, I want HVAC replacement timeline estimates with Arizona-specific context, so that I can budget for near-term expenses.

**Acceptance Criteria:** **Categories:** Immediate (>=13 yrs, 0-2 remaining), Near-term (10-12 yrs, 2-5 remaining), Mid-term (5-9 yrs, 5-10 remaining), Long-term (<5 yrs, 10+ remaining). AZ lifespan explicit: 10-15 years vs 20+ national. Cost: $7K-$12K. Unknown age uses year_built with LOW confidence. Visual: Score Gauge showing % lifespan used. Budget recommendation included.

**Technical Notes:** Formula: `remaining_years = max(0, 15 - system_age)`. Store in `hvac_assessment` object. Year_built proxy assumes original unless listing mentions replacement.

**Definition of Done:** Age-based timeline | AZ adjustment | Cost estimation | year_built proxy | Score Gauge display | Budget recommendation | Unit tests

---

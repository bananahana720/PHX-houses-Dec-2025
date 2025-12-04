# Sprint 5: Risk Intelligence

> **Epic**: E6
> **Objective**: Assess property condition and surface hidden risks with Arizona context
> **Stories**: 6
> **PRD Coverage**: FR21-24, FR26-27

### Stories

#### E6.S1 - Property Image Visual Assessment

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E2.S4, E5.S3 |
| **FRs** | FR21 |

**Acceptance Criteria**:
- [ ] Section C scores: kitchen, master, natural_light, ceilings, fireplace, laundry, aesthetics
- [ ] 0-10 scale multiplied by weights
- [ ] Default 5.0 (neutral) for missing images with LOW confidence
- [ ] Notes captured for significant observations

**Definition of Done**:
- [ ] Image assessment prompts for each category
- [ ] Claude Sonnet (vision model) integration
- [ ] Cost tracking (~$0.02 per image)

---

#### E6.S2 - Proactive Warning Generation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E4.S2, E6.S1 |
| **FRs** | FR22 |

**Acceptance Criteria**:
- [ ] Warnings for: HVAC age, roof condition, foundation, solar leases, pool equipment, orientation
- [ ] Severity levels: High, Medium, Low
- [ ] Consequence descriptions in plain language
- [ ] Warning precision >= 80%

**Definition of Done**:
- [ ] WarningGenerator in `src/phx_home_analysis/services/risk/`
- [ ] Warning Card component integration
- [ ] Consequence templates in `config/warning_templates.yaml`

---

#### E6.S3 - Risk-to-Consequence Mapping

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E6.S2 |
| **FRs** | FR23 |

**Acceptance Criteria**:
- [ ] Dollar cost estimates (min-max range)
- [ ] Quality of life impact descriptions
- [ ] Resale impact assessments
- [ ] Arizona-specific cost calibration

**Definition of Done**:
- [ ] ConsequenceMapper service
- [ ] Cost accuracy target: +/-30% of actual
- [ ] Template-based consequence generation

---

#### E6.S4 - Warning Confidence Levels

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E6.S3 |
| **FRs** | FR24 |

**Acceptance Criteria**:
- [ ] HIGH (90%+) for authoritative sources (county, FEMA)
- [ ] MEDIUM (70-90%) for listing/visual data
- [ ] LOW (<70%) for inferred data
- [ ] Age-based degradation: >14 days = -0.15, >30 days = -0.30

**Definition of Done**:
- [ ] Confidence calculation logic
- [ ] Display: High=green, Medium=amber, Low=gray
- [ ] Source attribution visible

---

#### E6.S5 - Foundation Issue Identification

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E6.S1 |
| **FRs** | FR26 |

**Acceptance Criteria**:
- [ ] Visual crack detection: Minor, Moderate, Severe
- [ ] Crack patterns: vertical, horizontal, stair-step
- [ ] Recall >= 90%, Precision >= 60%
- [ ] Recommendation: "Get structural engineer inspection ($300-$500)"

**Definition of Done**:
- [ ] Foundation assessment prompts
- [ ] Conservative approach (over-flag rather than under-flag)
- [ ] Validation against inspection reports

---

#### E6.S6 - HVAC Replacement Timeline Estimation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E6.S4 |
| **FRs** | FR27 |

**Acceptance Criteria**:
- [ ] Categories: Immediate (>=13 yrs), Near-term (10-12 yrs), Mid-term (5-9 yrs), Long-term (<5 yrs)
- [ ] **Arizona factor**: 10-15 year lifespan (not 20+ nationally)
- [ ] Replacement cost estimate: $7K-$12K
- [ ] Proxy from year_built if HVAC age unknown

**Definition of Done**:
- [ ] HVAC timeline logic
- [ ] Budget recommendation included
- [ ] Timeline accuracy: +/-2 years

---

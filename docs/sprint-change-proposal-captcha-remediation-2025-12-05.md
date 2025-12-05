# Sprint Change Proposal: CAPTCHA and Image Extraction Remediation

**Date:** 2025-12-05
**Prepared by:** BMad Correct Course Workflow
**Change Scope:** Moderate
**Approval Status:** ✅ APPROVED (2025-12-05)

---

## 1. Issue Summary

### Problem Statement

Live validation testing on 2025-12-04 revealed that the image extraction system has a **67% failure rate** in production conditions despite all tests passing. Two critical blockers were identified:

1. **BLOCK-001 (Critical):** Zillow CAPTCHA (PerimeterX px-captcha) blocking 100% of extractions. CAPTCHA solve attempts failed with "could not find CAPTCHA button" error.

2. **BLOCK-002 (High):** Redfin CDN URLs returning HTTP 404 errors. Pattern: URLs discovered during extraction become invalid by download time (session-bound or time-limited).

### Discovery Context

- **When:** 2025-12-04, during live validation testing
- **How:** Fresh extraction on 3 test properties post-Epic 2 completion
- **Who Found:** Development team during Epic 2 retrospective preparation

### Evidence

| Property Address | Status | Images | Issues |
|------------------|--------|--------|--------|
| 7233 W Corrine Dr, Peoria, AZ | Partial | 20 | Redfin only, Zillow CAPTCHA blocked |
| 5219 W El Caminito Dr, Glendale, AZ | Failed | 0 | Zillow CAPTCHA, Redfin 404 errors |
| 4560 E Sunrise Dr, Phoenix, AZ | Failed | 0 | Zillow CAPTCHA, Redfin 404 errors |

**Overall Success Rate:** 33% (1 of 3 partial success)

---

## 2. Impact Analysis

### Epic Impact

| Epic | Impact Level | Details |
|------|--------------|---------|
| **Epic 2** | ⚠️ Complete but degraded | Stories marked done; blockers discovered post-completion |
| **Epic 3** | ✅ Low | Kill-Switch has NO image dependency; can proceed |
| **Epic 4** | ⚠️ Medium | Section A/B scoring works; Section C (Interior) limited |
| **Epic 5** | ⚠️ Medium | Phase 1 extraction is critical component |
| **Epic 6** | 🔴 **HIGH** | Visual Analysis completely blocked until remediation |
| **Epic 7** | ⚠️ Medium | Deal sheets enhanced by images but not required |

### Story Impact

| Story | Status | Impact |
|-------|--------|--------|
| E2.S3 | Done ✅ | Code correct; external detection is issue |
| E2.S4 | Done ✅ | Storage infrastructure works; source acquisition fails |
| E6.S1-S6 | Backlog | All blocked until image extraction reliable |

### Artifact Conflicts

| Artifact | Update Needed | Priority |
|----------|---------------|----------|
| `sprint-status.yaml` | Add remediation stories, update blocker status | HIGH |
| `epic-2-*.md` | Add Post-Completion Remediation section | HIGH |
| `epic-3-*.md` | Add Wave 0 preparation section | MEDIUM |
| `architecture.md` | Document anti-bot patterns | MEDIUM |

### Technical Impact

| Component | Status | Notes |
|-----------|--------|-------|
| ZillowExtractor | 🔴 Blocked | PerimeterX CAPTCHA |
| RedfdinExtractor | ⚠️ Degraded | CDN 404 on downloads |
| MaricopaAssessorExtractor | ✅ Working | County API stable |
| Content-addressed storage | ✅ Working | No issues |
| Manifest system | ✅ Working | No issues |

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment (Option 1)

**Decision:** Create remediation stories as "Wave 0" before Epic 3

### Rationale

1. **Code is correct:** 182+ tests pass; issue is external anti-bot detection
2. **Bounded remediation:** Specific fixes to extractors, not architectural redesign
3. **Parallel work possible:** Epic 3 (Kill-Switch) has no image dependency
4. **MVP unblocked:** Core scoring works with County data

### Trade-offs Considered

| Option | Pros | Cons | Selected |
|--------|------|------|----------|
| Direct Adjustment | Clean tracking, parallel work | Adds timeline | ✅ Yes |
| Rollback to in-progress | Accurate status | Doesn't solve issue | ❌ No |
| Defer images from MVP | Fast, low risk | Reduces value | ❌ Backup |

### Effort Estimate

| Task | Estimate | Risk |
|------|----------|------|
| E2.R1 (Zillow zpid) | 4-6 hours | Medium (anti-bot unpredictable) |
| E2.R2 (Redfin session) | 2-4 hours | Low (known pattern) |
| Documentation updates | 1-2 hours | Low |
| **Total** | **7-12 hours** | **Medium** |

### Timeline Impact

- **Best case:** +1 day
- **Worst case:** +2 days
- **Mitigation:** Epic 3 can proceed in parallel

---

## 4. Detailed Change Proposals

### 4.1 Sprint Status Update

**File:** `docs/sprint-artifacts/sprint-status.yaml`

**Changes:**
1. Update blocker status to "remediation-planned"
2. Add remediation story references
3. Add new stories: `2-R1-zillow-zpid-extraction`, `2-R2-redfin-session-download`

### 4.2 Epic 2 Remediation Stories

**File:** `docs/epics/epic-2-property-data-acquisition.md`

**Add:**
- E2.R1: Zillow ZPID Direct Extraction
- E2.R2: Redfin Session-Bound Download

**Acceptance Criteria:**
- Both stories: >80% success rate on 5 test properties
- Updated unit/integration tests

### 4.3 Epic 3 Wave 0

**File:** `docs/epics/epic-3-kill-switch-filtering-system.md`

**Add:** Wave 0 preparation section with validation tasks

### 4.4 Architecture Documentation

**File:** `docs/architecture.md`

**Add:** Anti-Bot Detection Patterns section documenting:
- zpid extraction pattern for Zillow
- Session-bound download pattern for Redfin
- Updated fallback priority chain

---

## 5. Implementation Handoff

### Scope Classification: **Moderate**

Requires backlog reorganization and development team coordination.

### Handoff Recipients

| Role | Responsibility |
|------|----------------|
| **Dev Team** | Implement E2.R1, E2.R2 remediation stories |
| **SM** | Update story/epic files, track progress |
| **Architect** | Review anti-bot strategy if remediation fails |

### Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Zillow extraction | >80% success on 5 test properties |
| Redfin extraction | >80% success on 5 test properties |
| Combined success | >80% overall on live validation |
| Tests | All existing + new tests pass |
| Documentation | Architecture updated with patterns |

### Next Steps

1. **Approve this proposal** - User confirmation
2. **Create remediation stories** - Add E2.R1, E2.R2 to sprint-status.yaml
3. **Run live validation** - Baseline current success rate
4. **Implement remediation** - zpid URLs, session downloads
5. **Validate success** - >80% on 5 properties
6. **Proceed to Epic 3** - Can run in parallel if team capacity allows

---

## 6. Appendix: Proposed Story Content

### E2.R1: Zillow ZPID Direct Extraction

**Priority:** P0 | **Blocker:** BLOCK-001

**Acceptance Criteria:**
- Extract zpid from listing URLs or address search
- Navigate directly to image gallery (less protected path)
- Fallback to Google Images search if zpid unavailable
- Success rate >80% on 5 test properties

**Technical Approach:**
1. Parse zpid from `zillow.com/homedetails/{slug}/{zpid}_zpid/` URLs
2. Navigate to `zillow.com/homedetails/{zpid}_zpid/#image-lightbox`
3. Extract image URLs from lightbox gallery
4. If blocked, fallback to screenshot capture

### E2.R2: Redfin Session-Bound Download

**Priority:** P0 | **Blocker:** BLOCK-002

**Acceptance Criteria:**
- Extract image URLs and download in single browser session
- Use browser's native download capabilities
- Screenshot fallback if download fails
- Success rate >80% on 5 test properties

**Technical Approach:**
1. Keep browser session active during download phase
2. Use page.screenshot() or browser-native download
3. Don't extract URLs then download separately (causes 404)
4. Implement screenshot-capture fallback

---

*Generated by: BMAD Correct Course Workflow v6.0.0-alpha.13*
*Reviewed by: Andrew*
*Approved: 2025-12-05*

---

## Applied Changes

| File | Status |
|------|--------|
| `docs/sprint-artifacts/sprint-status.yaml` | ✅ Updated |
| `docs/epics/epic-2-property-data-acquisition.md` | ✅ Updated |
| `docs/epics/epic-3-kill-switch-filtering-system.md` | ✅ Updated |
| `docs/architecture.md` | ✅ Updated |

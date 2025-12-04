# Existing Skill Files

### 12. Kill-Switch Skill (Current)

**File:** `.claude/skills/kill-switch/SKILL.md`
**Word Count:** ~3,200 words
**Status:** TO BE UPDATED in Wave 6

**Current Contents:**
- "All must pass" logic (to be replaced)
- 7 criteria definitions
- Canonical implementation (`scripts/lib/kill_switch.py`)
- Unknown/null handling
- Early exit pattern
- Chain-of-thought evaluation
- Edge case examples

**Sections to Update (Wave 6):**
- Lines 13-23: Replace with HARD/SOFT distinction
- Lines 26-60: Update evaluation logic for weighted threshold
- Lines 176-227: Update chain-of-thought for severity scoring
- Lines 230-324: Update edge case examples with new verdicts

**Preservation:**
- Keep canonical implementation references
- Keep unknown/null handling section
- Keep edge case decision matrix (update verdicts)

---

### 13. Scoring Skill (Current)

**File:** `.claude/skills/scoring/SKILL.md`
**Word Count:** ~3,400 words
**Status:** TO BE UPDATED in Wave 6

**Current Contents:**
- 600-point system overview
- Section A: 250 pts (location)
- Section B: 160 pts (systems)
- Section C: 190 pts (interior)
- Tier classification (UNICORN/CONTENDER/PASS)
- Score calculation examples
- Default values (5.0 neutral)
- Value ratio calculation

**Sections to Update (Wave 6):**
- Lines 15-19: Update Section B (160→180 pts)
- Lines 51-60: Add Pool 30→20, CostEfficiency 40 NEW
- Lines 83-98: Add CostEfficiencyScorer usage example
- Lines 193-228: Update score sanity check for Section B (180 pts)

**New Section to Add:**
- Cost Efficiency Scoring (40 pts max)
- Formula: `max(0, 10 - ((monthly_cost - 3000) / 200))`
- Examples: $3,000/mo → 10 pts, $4,000/mo → 5 pts, $5,000+/mo → 0 pts

---

### 14. Property Data Skill

**File:** `.claude/skills/property-data/SKILL.md`
**Word Count:** ~2,500 words
**Status:** Stable (minimal updates needed)

**Contents:**
- CSV repository usage
- JSON enrichment repository usage
- Property entity structure
- Data access patterns

**Usage:**
- All waves: Reference for data loading
- Wave 3: Integration with Pydantic validation

---

### 15. Deal Sheets Skill

**File:** `.claude/skills/deal-sheets/SKILL.md`
**Word Count:** ~1,800 words
**Status:** TO BE UPDATED in Wave 6 (minor)

**Contents:**
- Deal sheet generation
- Template structure
- Rendering logic

**Updates Needed:**
- Add kill-switch verdict section example
- Add monthly cost display section example
- Add data quality indicator section

---

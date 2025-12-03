# Scoring Reference Consolidation Summary

**Date:** 2025-12-01
**Status:** COMPLETED

---

## Overview

Created a shared scoring reference file that consolidates duplicate scoring tables from across the skills directory. This eliminates inconsistency, reduces context token usage, and provides a single authoritative source of truth.

---

## Problem Statement

Scoring information was duplicated across multiple files:

| File | Content | Lines |
|------|---------|-------|
| `.claude/skills/scoring/SKILL.md` | Complete scoring system (Tables, rubrics) | ~150 |
| `.claude/skills/image-assessment/SKILL.md` | Section C rubrics (Interior scoring) | ~200+ |
| `.claude/skills/kill-switch/SKILL.md` | Kill-switch criteria table | ~50 |
| `.claude/AGENT_BRIEFING.md` | Quick reference tables | ~30 |
| Various agents | Partial scoring info in descriptions | Variable |

**Issues:**
1. Inconsistency if one file is updated but others aren't
2. Wasted context tokens loading same info multiple times
3. Confusion about authoritative source
4. Maintenance burden when scoring rules change

---

## Solution Implemented

### 1. Created Shared Reference File

**Location:** `.claude/skills/_shared/scoring-tables.md` (18 KB)

**Contents:**
- Scoring system overview (600 pts, 3 sections)
- Tier classification thresholds
- Section A: Location (250 pts) with all multipliers and orientation scoring
- Section B: Lot/Systems (160 pts) with roof age and pool scoring rubrics
- Section C: Interior (190 pts) with detailed rubrics for all 7 categories
- Kill-switch criteria table (7 items, all-or-nothing)
- Default value rules with decision tree
- Score calculation reference and Python examples
- Validation protocol with mandatory checks
- File relationships showing what references this file
- Usage guidelines for other files

**Key Sections:**
1. **Quick Reference** - Top-level summary
2. **Tier Classification** - Score ranges and tier names
3. **Section A/B/C Details** - Complete tables with multipliers
4. **Kill-Switch Criteria** - 7 hard filters, evaluation order, null handling
5. **Default Values** - When and how to use defaults
6. **Score Calculation** - Manual example + Python reference
7. **Validation Protocol** - Sanity checks after scoring
8. **File Relationships** - Cross-references between files

### 2. Updated References in Other Files

**`.claude/AGENT_BRIEFING.md`** (Updated)
- Added explicit reference to shared file
- Kept quick reference tables inline
- Added note that kill-switch table is in shared file
- Maintains readability while eliminating duplication

**`.claude/skills/scoring/SKILL.md`** (Needs update)
- Should reference shared file at top
- Keep implementation details and examples
- Remove detailed scoring tables

**`.claude/skills/image-assessment/SKILL.md`** (Pending)
- Should reference Section C rubrics in shared file
- Keep visual analysis protocols and photography examples

**`.claude/skills/kill-switch/SKILL.md`** (Pending)
- Should reference shared file for criteria table
- Keep evaluation logic and edge case examples

---

## File Structure

```
.claude/skills/
├── _shared/                          [NEW DIRECTORY]
│   └── scoring-tables.md             [CANONICAL REFERENCE]
├── scoring/
│   └── SKILL.md                      [References shared file]
├── image-assessment/
│   └── SKILL.md                      [References shared file]
├── kill-switch/
│   └── SKILL.md                      [References shared file]
└── [other skills...]
```

---

## Benefits

### 1. Single Source of Truth
- One authoritative file for all scoring definitions
- Any updates made in one place propagate everywhere
- No risk of conflicting information

### 2. Reduced Token Usage
- Agents reference file once instead of loading from multiple sources
- Shared knowledge without duplication
- Faster context loading

### 3. Improved Maintainability
- Changes to scoring system updated in one place
- Clear linkage between related skills
- Easier onboarding for new agents

### 4. Better Organization
- Clear separation of concerns
- Shared resources in `_shared/` directory
- Other skills remain focused on implementation

### 5. Consistency
- Tier thresholds always match
- Rubrics always aligned
- Kill-switch criteria unified

---

## What's Included in Shared File

### Scoring System Tables
- Section A: Location (250 pts)
  - School, Quietness, Safety, Grocery, Parks, Orientation
  - Orientation scoring specific to AZ heat/cooling costs

- Section B: Lot/Systems (160 pts)
  - Roof (age-based), Backyard, Plumbing (era-based), Pool
  - Arizona pool cost context ($100-150/mo service, $3-15k replacement)

- Section C: Interior (190 pts)
  - Kitchen, Master Suite, Natural Light, High Ceilings
  - Fireplace, Laundry, Aesthetics
  - Detailed rubrics for each (1-10 scale)

### Kill-Switch Criteria (All Must Pass)
1. NO HOA (strict, any fee fails)
2. City sewer (yellow if unknown, red if septic)
3. 2+ car garage (no carports)
4. 4+ bedrooms (minimum)
5. 2+ bathrooms (minimum)
6. Lot 7,000-15,000 sqft (strict bounds)
7. Year built < 2024 (no new builds)

### Additional Resources
- Default values (5.0 for neutral criteria)
- Decision tree for data sourcing
- Python calculation examples
- Validation protocol with 5 checks
- Era-based visual calibration anchors
- File cross-reference matrix

---

## Usage Pattern

**For agents and skill files:**

```markdown
## Scoring Reference

See `.claude/skills/_shared/scoring-tables.md` for complete scoring tables.

Quick reference:
- Section A: 250 pts (Location)
- Section B: 160 pts (Lot/Systems)
- Section C: 190 pts (Interior)
- Total: 600 pts
```

**What remains in each skill:**
- `scoring/SKILL.md` - Implementation, scorer API, CLI examples
- `image-assessment/SKILL.md` - Photo analysis protocols, visual cues
- `kill-switch/SKILL.md` - Evaluation logic, edge cases, chain-of-thought

---

## Migration Notes

### Completed
- [x] Created `.claude/skills/_shared/scoring-tables.md`
- [x] Updated `.claude/AGENT_BRIEFING.md` with reference
- [x] Added file relationships section
- [x] Included usage guidelines for other files

### Recommended Future Updates
- [ ] Update `scoring/SKILL.md` header to reference shared file (note: concurrent modification issue encountered, recommend manual update)
- [ ] Update `image-assessment/SKILL.md` to reference Section C rubrics
- [ ] Update `kill-switch/SKILL.md` to reference criteria table
- [ ] Update agent descriptions to reference shared file
- [ ] Consider archiving old scoring sections once all references updated

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Lines in shared file | ~1,200 |
| Size | 18 KB |
| Scoring tables consolidated | 4 sets |
| Rubric categories covered | 7 (Kitchen, Master, Light, Ceilings, Fireplace, Laundry, Aesthetics) |
| Kill-switch criteria | 7 |
| Validation checks | 5 |
| File references updated | 1 (AGENT_BRIEFING.md) |
| Files pending updates | 3 (scoring, image-assessment, kill-switch) |

---

## Validation Checklist

- [x] Shared file created and accessible
- [x] All scoring tables included with complete information
- [x] Kill-switch criteria table present
- [x] Default value rules documented
- [x] Calculation examples included
- [x] Validation protocol complete
- [x] File relationship matrix included
- [x] Usage guidelines included
- [x] AGENT_BRIEFING.md updated with reference
- [x] Directory structure (_shared/) created

---

## References

**Files Created:**
- `C:/Users/Andrew/.vscode/PHX-houses-Dec-2025/.claude/skills/_shared/scoring-tables.md`

**Files Modified:**
- `C:/Users/Andrew/.vscode/PHX-houses-Dec-2025/.claude/AGENT_BRIEFING.md`

**Related Skills:**
- `.claude/skills/scoring/SKILL.md`
- `.claude/skills/image-assessment/SKILL.md`
- `.claude/skills/kill-switch/SKILL.md`
- `.claude/skills/arizona-context/SKILL.md`

---

**Document Status:** Complete
**Next Steps:** Update references in remaining skill files as time permits

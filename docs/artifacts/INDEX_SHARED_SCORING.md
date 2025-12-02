# Shared Scoring Reference - Documentation Index

**Project:** PHX Houses Dec 2025
**Date Created:** 2025-12-01
**Status:** Complete and Verified

---

## What Was Done

A shared scoring reference file was created to consolidate duplicate scoring tables from across the project's skills directory. This is a comprehensive guide to accessing and using this new resource.

---

## Files Created

### 1. Canonical Scoring Reference
**Location:** `.claude/skills/_shared/scoring-tables.md`
**Size:** 18 KB (471 lines)
**Purpose:** Single authoritative source for all scoring system information

This file contains:
- 600-point scoring system definition (Sections A, B, C)
- Tier classification thresholds
- Complete rubrics for all 7 interior scoring categories
- All kill-switch criteria (7 items)
- Default value rules with decision tree
- Python calculation examples
- Validation protocols
- File relationship matrix

**Type:** Shared skill resource (frontmatter: `allowed-tools: Read`)

**How to Use:**
```markdown
See `.claude/skills/_shared/scoring-tables.md` for [specific section].
```

---

### 2. _shared Directory README
**Location:** `.claude/skills/_shared/README.md`
**Size:** 2.5 KB
**Purpose:** Documentation for the _shared directory itself

Contains:
- Overview of shared resources
- Description of scoring-tables.md
- Cross-reference matrix
- Guidelines for adding new shared resources
- Directory structure

---

### 3. Consolidation Summary
**Location:** `docs/artifacts/SCORING_CONSOLIDATION_SUMMARY.md`
**Size:** 8.1 KB
**Purpose:** Technical documentation of the consolidation process

Contains:
- Problem statement (duplication issues)
- Solution overview
- File structure changes
- Benefits analysis
- Migration roadmap
- File relationships
- Statistics and checklist

**Use this to understand:** What was consolidated, why, and what changed

---

### 4. Quick Reference Card
**Location:** `docs/artifacts/SCORING_QUICK_REFERENCE.md`
**Size:** 6.5 KB
**Purpose:** Easy-to-scan reference for common scoring tasks

Contains:
- Tier classification table
- All sections at a glance
- Kill-switch criteria summary
- Default values
- Data quality scoring
- Scoring calculation example
- Validation checklist
- Era-based anchors
- Field mappings

**Use this to:** Quickly look up thresholds, categories, or calculation examples

---

### 5. This Index
**Location:** `docs/artifacts/INDEX_SHARED_SCORING.md`
**Purpose:** Navigation guide for all scoring documentation

---

## Quick Navigation

### For Scoring Implementation
1. Start with `.claude/skills/_shared/scoring-tables.md` (canonical)
2. Reference "Score Calculation" section for Python code
3. Use "Validation Protocol" section before finalizing

### For Interior Assessment
1. Go to `scoring-tables.md` → "Section C: Interior"
2. Review rubrics for each of 7 categories
3. Cross-reference with "Era-Based Visual Calibration"

### For Kill-Switch Evaluation
1. Use `scoring-tables.md` → "Kill-Switch Criteria"
2. Check "Unknown/Null Handling" for edge cases
3. Reference "Evaluation Priority Order"

### For Quick Lookup
1. Use `SCORING_QUICK_REFERENCE.md` for fast answers
2. Use field mappings for data structure reference
3. Use validation checklist for before/after scoring

### To Understand Changes
1. Read `SCORING_CONSOLIDATION_SUMMARY.md`
2. Check "File Relationships" table
3. Review "Migration Notes" for what's pending

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Total lines in canonical file | 471 |
| Scoring categories covered | 17 (6 location + 4 systems + 7 interior) |
| Kill-switch criteria | 7 (all must pass) |
| Maximum score | 600 pts |
| Tier thresholds | 2 (480, 360) |
| Default value rules | 9+ scenarios |
| Validation checks | 5 mandatory |
| Total documentation | 35 KB |

---

## File Relationships

```
.claude/skills/_shared/scoring-tables.md (CANONICAL)
  ├── Referenced by: scoring/SKILL.md
  ├── Referenced by: image-assessment/SKILL.md
  ├── Referenced by: kill-switch/SKILL.md
  ├── Referenced by: AGENT_BRIEFING.md
  └── Supporting docs:
      ├── SCORING_CONSOLIDATION_SUMMARY.md
      ├── SCORING_QUICK_REFERENCE.md
      └── _shared/README.md
```

---

## What Was Consolidated

### Removed Duplications
- Section A/B/C scoring tables
- Tier thresholds
- Kill-switch criteria
- Default value rules

### Consolidated From
1. `.claude/skills/scoring/SKILL.md` - Had all tables
2. `.claude/skills/image-assessment/SKILL.md` - Had Section C rubrics
3. `.claude/skills/kill-switch/SKILL.md` - Had criteria table
4. `.claude/AGENT_BRIEFING.md` - Had quick references

### Result
Single file of truth with proper cross-references instead of 4 files with overlapping information.

---

## Using the New System

### When Implementing Scoring
```python
# In your scoring code:
# See `.claude/skills/_shared/scoring-tables.md` for:
# - Multipliers for each category
# - Default values when data missing
# - Validation rules to apply

# Reference the Python calculation example in scoring-tables.md
```

### When Assessing Images
```markdown
# In image assessment:
See `.claude/skills/_shared/scoring-tables.md` Section C for:
- Kitchen rubric (1-10 scale)
- Master suite rubric (1-10 scale)
- Natural light assessment
- Era-based visual anchors for calibration
```

### When Evaluating Kill-Switches
```python
# Before scoring:
# 1. Check `.claude/skills/_shared/scoring-tables.md`
# 2. Use Kill-Switch Criteria table
# 3. Check Evaluation Priority Order (fastest fail-fast)
# 4. Handle unknowns per Unknown/Null Handling section
```

---

## Accessing the Shared File

### Direct Path
```
C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\.claude\skills\_shared\scoring-tables.md
```

### In Markdown Files
```markdown
See `.claude/skills/_shared/scoring-tables.md` for [section].
```

### Via Read Tool
```
Read: C:/Users/Andrew/.vscode/PHX-houses-Dec-2025/.claude/skills/_shared/scoring-tables.md
```

---

## Next Steps

### Immediate
- [x] Create canonical scoring file
- [x] Update AGENT_BRIEFING.md references
- [x] Create supporting documentation

### Short Term
- [ ] Update scoring/SKILL.md with reference
- [ ] Update image-assessment/SKILL.md with reference
- [ ] Update kill-switch/SKILL.md with reference
- [ ] Update agent descriptions

### Medium Term
- [ ] Consider consolidating other duplicate tables
- [ ] Create additional _shared/ resources as needed
- [ ] Update project documentation with reference

---

## Benefits Summary

1. **Single Source of Truth** - One file for all scoring definitions
2. **Reduced Duplication** - Eliminate inconsistency
3. **Faster Maintenance** - Update once, applies everywhere
4. **Better Organization** - Clear _shared/ directory for common resources
5. **Improved Context** - Agents reference file once vs loading from multiple sources
6. **Clear Documentation** - Comprehensive with examples and edge cases

---

## Common Tasks

### I need to know the tier thresholds
→ `SCORING_QUICK_REFERENCE.md` line 3-11, or `scoring-tables.md` "Tier Classification" section

### I'm scoring the interior
→ `scoring-tables.md` "Section C: Interior" or `SCORING_QUICK_REFERENCE.md` "Section C"

### I need to evaluate kill-switches
→ `scoring-tables.md` "Kill-Switch Criteria" section

### I want to understand the changes
→ `SCORING_CONSOLIDATION_SUMMARY.md`

### I need a quick reference
→ `SCORING_QUICK_REFERENCE.md`

### I need to add a new shared resource
→ `.claude/skills/_shared/README.md`

---

## Verification Checklist

- [x] Canonical file created and verified (471 lines)
- [x] All scoring tables included
- [x] Kill-switch criteria documented
- [x] Default value rules explained
- [x] Validation protocols included
- [x] Python examples provided
- [x] File relationships documented
- [x] Quick reference created
- [x] Consolidation summary written
- [x] Directory structure established
- [x] AGENT_BRIEFING.md updated

---

**Last Updated:** 2025-12-01
**Canonical Source:** `.claude/skills/_shared/scoring-tables.md`
**Documentation Status:** Complete
**Ready for Use:** Yes

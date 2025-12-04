# Core Planning Documents

### 1. Master Improvement Plan

**File:** `.claude/plans/hidden-squishing-dragonfly.md`
**Word Count:** ~8,000 words
**Status:** Finalized & Validated

**Contents:**
- Project overview and key objectives
- Kill-switch redesign (HARD vs SOFT criteria)
- Data quality architecture (5 layers)
- Scoring redistribution (600 pts maintained)
- Implementation waves (0-6)
- SME validation findings
- User decisions log

**Key Sections for Reference:**
- Lines 17-46: Kill-switch threshold system with severity weights
- Lines 49-78: Data quality architecture (5-layer system)
- Lines 79-109: Cost estimation module design
- Lines 116-155: Implementation waves breakdown
- Lines 158-173: Critical files to modify
- Lines 176-186: User decisions (finalized)
- Lines 189-213: Scoring weight redistribution table
- Lines 219-270: SME validation findings and gaps

**Usage:**
- Wave 0: Reference data quality baseline requirements
- Wave 1: Reference kill-switch severity weights
- Wave 2: Reference cost estimation components
- All waves: Verify against user decisions

**Cross-References:**
- See architecture doc for system design
- See implementation spec for file-by-file changes

---

### 2. Architecture Overview

**File:** `docs/architecture/scoring-improvement-architecture.md`
**Word Count:** ~12,000 words
**Created:** This session

**Contents:**
- System context diagram
- Component architecture (data quality, kill-switch, cost estimation, scoring)
- Data flow diagrams
- Integration points
- Technology stack
- Performance considerations
- Security & testing strategies

**Key Sections:**
- Component Architecture: Detailed subsystem breakdowns
- Data Flow Diagram: End-to-end pipeline visualization
- Integration Points: How components connect
- File Manifest: All new/modified files

**Usage:**
- Session start: Review system context before coding
- Design decisions: Understand component relationships
- Integration: Reference data flow for cross-module work

---

### 3. Implementation Specification

**File:** `docs/specs/implementation-spec.md`
**Word Count:** ~15,000 words (partial - Waves 0-2 detailed)
**Created:** This session

**Contents:**
- Wave 0: Baseline & pre-processing (code samples)
- Wave 1: Kill-switch threshold (code samples + tests)
- Wave 2: Cost estimation (partial, code structure)
- Waves 3-6: Summary structure (to be expanded)

**Key Sections:**
- 0.1 Quality Baseline Script: Full implementation
- 0.2 Data Normalizer: Full module code
- 1.1 Weighted Threshold Logic: Complete code changes
- 1.2 Deal Sheets Integration: Rendering + CSS

**Usage:**
- Before each session: Read relevant wave section
- During implementation: Copy/adapt code samples
- Testing: Use provided test cases

---

### 4. Phase Execution Guide

**File:** `docs/specs/phase-execution-guide.md`
**Word Count:** ~12,000 words
**Created:** This session

**Contents:**
- Session-by-session execution plan
- Entry/exit criteria for each session
- Verification checkpoints
- Rollback procedures
- Troubleshooting guide
- Success metrics

**Key Sections:**
- Session Planning Matrix: Time estimates and dependencies
- Cross-Session Continuity: How to pause/resume
- Troubleshooting Guide: Common issues and solutions

**Usage:**
- Session planning: Determine which wave/session to tackle
- Mid-session: Reference exit criteria and verification steps
- Issues: Consult troubleshooting guide

---

# County Data Integration - File Map

Visual reference showing which files are updated and their relationships.

## Files Updated (5 total)

```
.claude/
├── commands/
│   └── analyze-property.md ········· [2 EDITS] Orchestrator (adds Phase 0)
│
├── agents/
│   ├── listing-browser.md ·········· [2 EDITS] Phase 1 agent (cross-reference county)
│   ├── map-analyzer.md ············· [1 EDIT]  Phase 1 agent (skip county fields)
│   └── image-assessor.md ··········· [1 EDIT]  Phase 2 agent (use county context)
│
└── AGENT_CONTEXT.md ················ [2 EDITS] Shared context (document script)
```

## New Script (already exists)

```
scripts/
└── extract_county_data.py ·········· [NO CHANGES] Already implemented
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    /analyze-property <address>                  │
│                              ↓                                  │
│              analyze-property.md (Orchestrator)                 │
└─────────────────────────────────────────────────────────────────┘
                               ↓
         ┌─────────────────────┼─────────────────────┐
         ↓                     ↓                     ↓
┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Pre-Execution  │   │  AGENT_CONTEXT   │   │ Research Queue   │
│ State Checks   │   │  (shared context)│   │    Check         │
└────────────────┘   └──────────────────┘   └──────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ ★ NEW: Phase 0 - County Data Extraction                        │
│                                                                 │
│   python scripts/extract_county_data.py --address "..." \      │
│          --update-only                                          │
│                                                                 │
│   Populates:                                                    │
│   • lot_sqft (kill-switch)                                      │
│   • year_built (kill-switch)                                    │
│   • garage_spaces (kill-switch)                                 │
│   • has_pool                                                    │
│   • livable_sqft                                                │
│   • baths (estimated)                                           │
│   • full_cash_value                                             │
│   • roof_type                                                   │
│                                                                 │
│   ↓ Updates enrichment_data.json                                │
│                                                                 │
│   ↓ Check kill-switches                                         │
│   IF kill-switch fails → Mark FAILED, skip Phase 1-4           │
│   IF kill-switch passes → Continue to Phase 1                  │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1 - Data Collection (Parallel)                           │
│                                                                 │
│   ┌───────────────────────┐   ┌───────────────────────┐        │
│   │  listing-browser.md   │   │  map-analyzer.md      │        │
│   │  (Haiku)              │   │  (Haiku)              │        │
│   │                       │   │                       │        │
│   │ • Extract images      │   │ • Orientation         │        │
│   │ • Get listing data    │   │ • School ratings      │        │
│   │ • Note county         │   │ • Skip county fields  │        │
│   │   conflicts           │   │ • Distances           │        │
│   └───────────────────────┘   └───────────────────────┘        │
│            ↓                            ↓                       │
│        Images saved              enrichment_data.json           │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2 - Visual Assessment (Sequential)                       │
│                                                                 │
│   ┌───────────────────────────────────────┐                    │
│   │  image-assessor.md (Sonnet)           │                    │
│   │                                       │                    │
│   │ • Score interior (190 pts)            │                    │
│   │ • Use county data for context:        │                    │
│   │   - year_built → finish expectations  │                    │
│   │   - has_pool → verify photos          │                    │
│   │   - garage_spaces → verify size       │                    │
│   └───────────────────────────────────────┘                    │
│            ↓                                                    │
│    enrichment_data.json                                         │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3 - Synthesis & Scoring                                  │
│                                                                 │
│ • Section A: Location (250 pts) ← map-analyzer                 │
│ • Section B: Lot/Systems (160 pts) ← county + enrichment       │
│ • Section C: Interior (190 pts) ← image-assessor               │
│ • Total: 600 pts                                                │
│ • Tier: UNICORN (>400) | CONTENDER (300-400) | PASS (<300)    │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 4 - Report Generation                                    │
│                                                                 │
│ • Update enrichment_data.json                                   │
│ • Generate markdown report                                      │
│ • Update extraction_state.json                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Edit Locations by File

### 1. `.claude/commands/analyze-property.md`

```
Line ~50:  Add "### 3. Extract County Data" section (PRE-EXECUTION)
           ↓
           Renumber existing sections 3→4, 4→5

Line ~244: Add "### Phase 0: County Data Extraction" section (WORKFLOW)
           ↓
           Before existing "### Phase 1: Data Collection"
```

**Impact:** Orchestrator now runs county extraction before Phase 1

---

### 2. `.claude/AGENT_CONTEXT.md`

```
Line ~231: Expand scripts reference table
           ↓
           Add extract_county_data.py row
           Add "Extract County Data Options" section

Line ~281: Add county data sources note
           ↓
           After enrichment JSON schema
           Documents which fields come from county API
```

**Impact:** All agents can reference county script and understand field sources

---

### 3. `.claude/agents/listing-browser.md`

```
Line ~54:  Add "### 5. Note County Data Availability" section
           ↓
           After existing enrichment check
           Cross-reference county vs listing data

Line ~183: Add "data_source_conflicts" field to return format
           ↓
           In standard JSON return structure
```

**Impact:** Agent detects and reports conflicts between listing and county data

---

### 4. `.claude/agents/map-analyzer.md`

```
Line ~60:  Add "### 5. County Data Cross-Check" section
           ↓
           After existing analysis reference
           Skip extracting fields already from county
```

**Impact:** Agent avoids redundant work, focuses on map-specific data

---

### 5. `.claude/agents/image-assessor.md`

```
Line ~68:  Add "### 5. County Data for Context" section
           ↓
           After existing scores check
           Use county data to inform visual assessment
```

**Impact:** Agent uses year_built and has_pool to adjust expectations

---

## Data Dependencies

```
County API
    ↓
enrichment_data.json ← Phase 0 (county extraction)
    ↓                  Phase 1 (listing-browser, map-analyzer)
    ↓                  Phase 2 (image-assessor)
    ↓
Final scores + tier ← Phase 3 (synthesis)
    ↓
Property report ← Phase 4 (report generation)
```

## Kill-Switch Flow

```
Phase 0 extracts county data
    ↓
Check kill-switches:
    ├─ lot_sqft: 7,000-15,000? ──┐
    ├─ year_built: < 2024? ──────┤
    └─ garage_spaces: >= 2? ─────┤
                                 ↓
                          ┌──────┴──────┐
                          ↓             ↓
                       PASS          FAIL
                          ↓             ↓
                  Continue to    Mark property
                    Phase 1      as "FAILED"
                                       ↓
                                 Skip Phase 1-4
                                       ↓
                                 Next property
```

## File Size Changes

| File | Current Size | Lines Added | % Increase |
|------|--------------|-------------|------------|
| analyze-property.md | ~666 lines | ~60 lines | +9% |
| AGENT_CONTEXT.md | ~457 lines | ~35 lines | +8% |
| listing-browser.md | ~237 lines | ~22 lines | +9% |
| map-analyzer.md | ~298 lines | ~18 lines | +6% |
| image-assessor.md | ~354 lines | ~15 lines | +4% |

Total: ~150 lines added across 5 files

## Cross-References

```
analyze-property.md
    ↓ references
AGENT_CONTEXT.md ← shared by all agents
    ↑ referenced by
    ├─ listing-browser.md
    ├─ map-analyzer.md
    └─ image-assessor.md

All files reference:
- scripts/extract_county_data.py (new Phase 0 script)
- data/enrichment_data.json (data storage)
```

## Edit Order (Dependency-Based)

```
1. AGENT_CONTEXT.md ········· Foundation (edits 3, 4)
   ↓
2. Agent files (parallel):
   ├─ listing-browser.md ···· Edit 5, 6
   ├─ map-analyzer.md ······· Edit 7
   └─ image-assessor.md ····· Edit 8
   ↓
3. analyze-property.md ······ Orchestrator (edits 1, 2)
```

**Rationale:** Edit shared context first, then agents (which reference context), then orchestrator (which calls agents).

## Verification Commands

```bash
# 1. Check all files were updated
grep -c "extract_county_data" \
  .claude/commands/analyze-property.md \
  .claude/AGENT_CONTEXT.md \
  .claude/agents/listing-browser.md \
  .claude/agents/map-analyzer.md \
  .claude/agents/image-assessor.md

# Expected output: 1+ matches per file

# 2. Verify Phase 0 exists
grep "Phase 0: County Data Extraction" .claude/commands/analyze-property.md

# Expected: 1 match

# 3. Check scripts table updated
grep "extract_county_data.py" .claude/AGENT_CONTEXT.md

# Expected: 2+ matches (table + options section)

# 4. Verify all agents reference county data
for agent in listing-browser map-analyzer image-assessor; do
  echo "=== $agent ==="
  grep -i "county" .claude/agents/$agent.md | head -n 3
done

# Expected: Each agent has county-related instructions
```

---

## Quick Reference: What Each File Does

| File | Role | County Integration |
|------|------|-------------------|
| `analyze-property.md` | Orchestrates 5-phase workflow | Adds Phase 0, runs county extraction |
| `AGENT_CONTEXT.md` | Shared context for all agents | Documents county script and fields |
| `listing-browser.md` | Extract listing images/data | Cross-references county data |
| `map-analyzer.md` | Extract geographic data | Skips county-sourced fields |
| `image-assessor.md` | Score interior from photos | Uses county data for context |

---

*Visual reference created: 2025-11-30*
*Shows file relationships and edit locations*

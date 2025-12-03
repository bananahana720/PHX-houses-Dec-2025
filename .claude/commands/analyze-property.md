---
allowed-tools: Task, Read, Glob, Grep, Bash(python:*), Write, Edit, Skill
argument-hint: <address> or --all or --test [--strict] [--skip-phase=N] [--resume|--fresh]
description: Multi-agent property analysis with visual browsing
---

# Multi-Agent Property Analysis Orchestrator

Orchestrate multi-phase property analysis using specialized agents and skills.

## STEP 0: GET YOUR BEARINGS (MANDATORY)

Before ANY property analysis, orient yourself to current pipeline state.

**CRITICAL: Read `.claude/AGENT_BRIEFING.md` for quick state orientation.**

### Tool Usage Rules (MANDATORY)
- Use **Read** tool for files (NOT `bash cat`)
- Use **Glob** tool for listing (NOT `bash ls/find`)
- Use **Grep** tool for searching (NOT `bash grep`)

### 1. Check Pipeline State

Use the **Read** tool to load work_items.json:
```
Read: data/work_items.json
```

Parse in your response to check:
- Session ID and progress
- Current index
- In-progress and failed counts

### 2. Count Properties

Use the **Read** tool:
```
Read: data/phx_homes.csv
Read: data/enrichment_data.json
```

Note: enrichment_data.json is a **LIST** - count with `len(data)`.

### 3. Check Metadata Files

Use the **Glob** tool:
```
Glob: pattern="*.json", path="data/property_images/metadata/"
```

### 4. Check Research Tasks (if exists)

Use the **Read** tool:
```
Read: data/research_tasks.json
```

### 5. Check Session Cache (if resuming)

Use the **Read** tool:
```
Read: data/session_cache.json
```

**DO NOT PROCEED** until you understand:
- How many properties are completed vs remaining
- Current pipeline state and session ID
- Any blocked sources from previous runs

## Arguments: $ARGUMENTS

| Argument | Action |
|----------|--------|
| `--test` | Process first 5 properties (validation mode) |
| `--all` | Process all properties from CSV |
| `<address>` | Single property analysis |

### Execution Flags

| Flag | Behavior |
|------|----------|
| `--strict` | Fail fast on any prerequisite failure (default: warn and continue) |
| `--skip-phase=N` | Skip specified phase (for debugging/recovery) |
| `--resume` | Resume from last checkpoint (default behavior) |
| `--fresh` | Clear all checkpoints, start from Phase 0 |

### --strict Mode Behavior

When `--strict` is enabled:

```python
def execute_phase_strict(phase: int, property_data: dict) -> bool:
    """Execute phase in strict mode.

    In strict mode:
    - ANY prerequisite failure → immediate stop
    - Warnings are treated as errors
    - Partial data not accepted
    """
    prereq_check = check_phase_prerequisites(phase, property_data)

    if not prereq_check["can_proceed"]:
        raise PhasePrerequisiteError(
            phase=phase,
            missing=prereq_check["missing_prerequisites"],
            skip_reason=prereq_check["skip_reason"]
        )

    if prereq_check["warnings"]:
        raise PhasePrerequisiteWarning(
            phase=phase,
            warnings=prereq_check["warnings"]
        )

    # Execute phase...
```

### Default Mode (Non-Strict) Behavior

When `--strict` is NOT enabled:

```python
def execute_phase_default(phase: int, property_data: dict) -> bool:
    """Execute phase in default (lenient) mode.

    In default mode:
    - Prerequisites failures → skip phase with logged reason
    - Warnings → log and continue
    - Partial data accepted
    """
    prereq_check = check_phase_prerequisites(phase, property_data)

    if not prereq_check["can_proceed"]:
        log_warning(f"Skipping Phase {phase}: {prereq_check['skip_reason']}")
        update_phase_status(phase, "skipped", reason=prereq_check["skip_reason"])
        return False  # Phase skipped

    for warning in prereq_check["warnings"]:
        log_warning(f"Phase {phase} warning: {warning}")

    # Execute phase with available data...
```

### Usage Examples

```bash
# Strict mode - fail on any issue
/analyze-property "123 Main St" --strict

# Default mode - continue with warnings
/analyze-property "123 Main St"

# Skip Phase 1 (use existing data)
/analyze-property "123 Main St" --skip-phase=1

# Fresh start - clear all checkpoints
/analyze-property "123 Main St" --fresh
```

## Required Skills

Load skills as needed during orchestration:
- **property-data** - Load/query/update property data
- **state-management** - Checkpointing & crash recovery
- **kill-switch** - Buyer criteria validation
- **county-assessor** - Phase 0 data extraction
- **cost-efficiency** - Monthly cost estimation
- **scoring** - Calculate & assign tiers
- **deal-sheets** - Generate reports

## Pre-Spawn Validation (CRITICAL)

Before spawning Phase 2 agents, ALWAYS use the validation script to verify prerequisites and gather context.

### Validation Script Location

```
scripts/validate_phase_prerequisites.py
```

### Available Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `validate_phase2_prerequisites(address)` | Check if Phase 2 can spawn | `ValidationResult(can_spawn, reason, context)` |
| `reconcile_data_quality(address)` | Cross-check data quality | `ReconciliationResult(completeness_score, accuracy_score, issues)` |
| `repair_data_inconsistencies(issues)` | Auto-fix common issues | List of repairs made |

### CLI Usage

```bash
# Validate Phase 2 prerequisites (JSON output)
python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images --json

# Data quality reconciliation with auto-repair
python scripts/validate_phase_prerequisites.py --reconcile --address "123 Main St" --repair --json

# Reconcile all properties
python scripts/validate_phase_prerequisites.py --reconcile --all --json
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | can_spawn=true OR no errors | Proceed with agent spawn |
| 1 | can_spawn=false OR errors found | Block spawn, report reason |

### ValidationResult Structure (JSON)

```json
{
  "can_spawn": true,
  "reason": "All Phase 2 prerequisites met",
  "context": {
    "address": "123 Main St, Phoenix, AZ 85001",
    "image_folder": "C:/path/to/processed/abc123",
    "image_count": 25,
    "folder_hash": "abc123",
    "phase_status": {
      "phase0_county": "complete",
      "phase1_listing": "complete",
      "phase1_map": "complete",
      "phase2_images": "pending"
    },
    "property_data": {
      "year_built": 2005,
      "lot_sqft": 8500,
      "beds": 4,
      "baths": 2.5,
      "price": 450000,
      "has_pool": true,
      "orientation": "north",
      "sqft": 2200
    }
  }
}
```

### When Spawn is BLOCKED

Common blocking reasons and remediation:

| Reason | Remediation |
|--------|-------------|
| "Phase 1 listing not complete" | Run Phase 1 first |
| "No image folder mapping found" | Run `python scripts/extract_images.py --address "$ADDRESS"` |
| "Image folder does not exist on disk" | Re-run image extraction |
| "Image folder exists but contains no images" | Re-run image extraction with different sources |
| "work_items.json not found" | Initialize pipeline with Phase 0 |
| "Property not found in work_items.json" | Add property to work_items or run from CSV |

## State Management (work_items.json)

**Schema & Locking:** See `docs/architecture/state-management.md`

### Quick Reference

- **Property-level locking**: Acquire lock before modifying, release when done
- **Atomic updates**: Use temp file + rename pattern
- **Session blocking cache**: Track source status per session (zillow, redfin, google_maps)

## Phase Workflow

**Detailed Protocol:** See `docs/architecture/phase-orchestration.md`

### Quick Reference: Phase Dependencies

| Phase | Requires | Script/Agent |
|-------|----------|--------------|
| 0: County | Nothing | `extract_county_data.py` |
| 0.5: Cost | Phase 0 complete | Inline service call |
| 1: Listing | Phase 0 ≠ failed | `extract_images.py` or listing-browser |
| 1: Map | Phase 0 ≠ failed | map-analyzer agent |
| 2A: Exterior | Phase 1 listing complete + images exist | image-assessor agent |
| 2B: Interior | Phase 2A complete | image-assessor agent |
| 3: Synthesis | Phase 0 + 0.5 + at least 1 Phase 1 | `analyze.py` |
| 4: Report | Phase 3 complete | `deal_sheets` |

### Pre-Spawn Validation (Phase 2 ONLY)

Before spawning Phase 2A or 2B agents, ALWAYS validate:

```bash
python scripts/validate_phase_prerequisites.py --address "$ADDRESS" --phase phase2_images --json
```

- Exit code 0 → Spawn with validated context
- Exit code 1 → Block spawn, report reason

## Git Commit Protocol

**Full Details:** See `docs/architecture/state-management.md`

### Quick Reference

- **Commit after each property** to preserve progress
- **Structured message format**: `feat(property): Complete {address} - {tier} ({score}/600)`
- **Stage files**: enrichment_data.json, work_items.json, images/*, reports/*
- **Update commit_sha** in work_items.json after commit

## Batch Processing

**Full Protocol:** See `docs/architecture/phase-orchestration.md`

### Quick Reference

1. **Triage**: Skip if status == "complete" or retry_count >= 3
2. **Sequential**: Process properties one at a time with locking
3. **Progress**: Display current property, phase, completed/failed counts, tier breakdown

## Optimization Rules

1. **Check data completeness** before spawning agents
2. **Skip if complete** - Don't reprocess finished properties (check work_items.json)
3. **Test one first** - Verify source not blocked before batch
4. **Fail fast** - After 3 consecutive same errors, skip source
5. **Commit frequently** - One commit per property for crash recovery

## Error Handling & Recovery

**Full Protocol:** See `docs/architecture/phase-orchestration.md`

### Quick Reference

| Error | Action |
|-------|--------|
| Agent fails | Log, mark phase "failed", continue with partial |
| No images | Mark phase2a/2b "skipped" |
| Rate limited | Backoff, retry, increment retry_count |
| Max retries (3+) | Skip permanently |
| Lock conflict | Skip property (another session owns it) |

### Crash Recovery

On restart, work_items.json enables safe resumption:
- Find last completed phase
- Retry if phase was "in_progress" at crash
- Skip if retry_count >= 3

## Verification & Summary

**Full Details:** See `docs/architecture/state-management.md`

### Single Property Checklist

- [ ] enrichment_data.json updated
- [ ] work_items.json shows complete
- [ ] Git commit created with property hash
- [ ] commit_sha populated in work_items.json

### Batch Summary Template

```
ANALYSIS COMPLETE
Session: {session_id}
Attempted: {total} | Completed: {complete} | Failed: {failed}

Tier Breakdown:
- Unicorns: {count} | Contenders: {count} | Pass: {count} | Failed: {count}

Git Commits: {count} (1 per property)
```

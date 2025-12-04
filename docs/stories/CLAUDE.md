---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# docs/stories

## Purpose
User story repository for the PHX Houses Analysis Pipeline. Tracks implementation-ready stories and architecture prerequisite tasks derived from epics, organized by sprint and epic, with detailed acceptance criteria and file-level technical guidance.

## Contents
| Path | Purpose |
|------|---------|
| `e1-s1-configuration-system-setup.md` | Config system externalization, environment overrides, validation, hot-reload (P0, 8 pts) |
| `e1-s2-property-data-storage-layer.md` | JSON storage layer with atomic writes, backup, address normalization (P0, 5 pts, depends E1.S1) |
| `sprint-0-architecture-prerequisites.md` | PRD alignment sprint: fix scoring 605pt system, kill-switch criteria HARD/SOFT (P0, 8 pts) |

## Key Story Patterns

### E1.S1: Configuration System Setup (8 pts, P0)
**Acceptance Criteria (Given-When-Then format):**
- AC1: Configuration Loading - YAML files load and validate against schemas
- AC2: Environment Overrides - .env variables override YAML config
- AC3: Validation/Error Reporting - Clear error messages with file:line, field names, valid ranges
- AC4: Startup Protection - Invalid config prevents app startup with logged errors
- AC5: Hot-Reload Support - `--watch` flag triggers reload on file change
- AC6: Template Creation - Template files in `config/templates/` with documentation

**Technical Tasks:** Dependencies (pydantic-settings, watchfiles), config schemas, loader, CLI integration

**Dependencies:** None (blocking E1.S2)

### E1.S2: Property Data Storage Layer (5 pts, P0)
**Acceptance Criteria:**
- AC1: JSON Schema Definition - EnrichmentData in JSON with normalized_address, source tracking
- AC2: Atomic Writes - Write-to-temp + atomic rename prevents corruption on crash
- AC3: Backup/Restore - Auto-create timestamped backups, restore_from_backup() recovery
- AC4: Address Normalization - normalize_address() applied to all loaded addresses
- AC5: Data Merge - apply_enrichment_to_property() merges JSON into Property entities
- AC6: CSV Integration - CsvPropertyRepository loads phx_homes.csv, save_all() exports

**Technical Tasks:** EnrichmentData entity (domain/entities.py), JsonEnrichmentRepository (repositories/json_repository.py), atomic_json_save utility

**Dependencies:** E1.S1 (Configuration System Setup must complete first)

### Sprint-0: Architecture Prerequisites (8 pts, P0)
**Acceptance Criteria:**
- AC1: Scoring System Clarification - Confirm 605 or 600 point total, section weights (Location/Systems/Interior)
- AC2: Kill-Switch Criteria - Define 7 HARD criteria (HOA, min beds, min baths, sewer, year, garage, lot)
- AC3: Severity System - SOFT criteria accumulate severity, thresholds (FAIL ≥3.0, WARNING ≥1.5)
- AC4: Buyer Profile - Update max monthly payment target, acceptable ranges
- AC5: Arizona Specifics - Document HVAC (10-15yr), pool ($250-400/mo), solar lease liability

**Critical Blocking Issues Identified:**
- Kill-switch criteria: 7 items but only 3 labeled HARD in spec (need clarification)
- Scoring: Spec shows 605 total but code has 600 (Location 230, Systems 180, Interior 190)
- Lot size: Spec "7k-15k sqft" but unclear if both bounds are hard boundaries
- Garage/sewer: Described as must-haves but severity weights suggest soft criteria

**Dependencies:** None (blocking all Phase Implementation)

## Story Structure

Each story contains:
1. **Metadata:** Status (Ready for Development), Epic, Priority (P0-P3), Points (5-13)
2. **User Story Statement:** "As [role], I want [feature], so that [benefit]"
3. **Acceptance Criteria (6+):** Given-When-Then format, prefixed AC1-AC6
4. **Technical Tasks:** File paths with line numbers, action steps, acceptance criteria
5. **Dependencies:** Explicit story/epic dependencies blocking work

## Tasks
- [x] Identify story organization: sprint-0 prerequisites, then Epic 1 stories (E1.S1 → E1.S2)
- [x] Extract story metadata: status, priority, dependencies, estimated points
- [x] Map acceptance criteria patterns: Given-When-Then format with AC prefix
- [x] Document technical task structure: file paths, line ranges, implementation guidance
- [ ] Track story completion: PRD alignment must complete before Phase Implementation P:H
- [ ] Validate acceptance criteria: Create test cases before marking done P:M

## Learnings
- **Story structure enables clear handoff:** Metadata + user story + 6+ AC + technical tasks with file:line → developer can start immediately
- **Dependency management critical:** Sprint-0 blocks all work; E1.S2 depends on E1.S1 completion; explicit dependency graph prevents ordering errors
- **PRD alignment identified 5 critical inconsistencies:** 605 vs 600 points, missing square footage, lot size logic, garage/sewer criteria, kill-switch severity rules
- **File-level precision:** Each technical task specifies exact path and lines (e.g., `src/phx_home_analysis/config/constants.py:19-23`), enabling AI agents to locate implementation without searching
- **Acceptance criteria as test matrix:** Each AC is testable behavior (Given X, When Y, Then Z) → maps to unit/integration tests
- **Status convention:** "Ready for Development" = refined and ready for assignment (distinct from In Progress/Done)
- **Epic decomposition pattern:** 2-story pattern for Epic 1 (config system → data storage) provides logical dependency chain

## Refs
- **Sprint 0 blocking work:** `sprint-0-architecture-prerequisites.md:1-150`
- **Config system story:** `e1-s1-configuration-system-setup.md:1-100`
- **Data storage story:** `e1-s2-property-data-storage-layer.md:1-150`
- **Story metadata example:** `e1-s1-configuration-system-setup.md:1-6` (Status, Epic, Priority, Points)
- **AC format example:** `e1-s1-configuration-system-setup.md:12-45` (AC1-AC6, Given-When-Then)
- **Technical tasks example:** `e1-s1-configuration-system-setup.md:48-100` (file paths, line ranges, actions)

## Deps
← Imports from:
  - `docs/epics/` - Stories derived from Epic definitions
  - `src/phx_home_analysis/config/constants.py` - Config system targets
  - `src/phx_home_analysis/domain/entities.py` - EnrichmentData schema
  - `.env` - Environment variable overrides

→ Imported by:
  - `.claude/AGENT_BRIEFING.md` - Story context for implementation agents
  - Sprint planning (work_items.json tracking)
  - CI/CD gates (acceptance criteria tests)

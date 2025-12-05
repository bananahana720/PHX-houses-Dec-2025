# Epic 1: Foundation & Data Infrastructure

**Status:** COMPLETED (2025-12-04) - All 6 stories implemented and tested
**Completion Date:** 2025-12-04

**User Value:** Enable reliable data storage, configuration management, and pipeline execution that supports crash recovery and data integrity.

**PRD Coverage:** FR7, FR8, FR34-39, FR46-51, FR56
**Architecture References:** ADR-02 (JSON Storage), Data Architecture, State Management

---

### E1.S1: Configuration System Setup

**Priority:** P0 | **Dependencies:** None | **FRs:** FR46, FR47, FR50, FR51

**User Story:** As a system administrator, I want externalized configuration for scoring weights and kill-switch criteria, so that I can adjust analysis parameters without code changes.

**Acceptance Criteria:** Configuration loads scoring weights from `config/scoring_weights.yaml` and kill-switch criteria from `config/kill_switch.csv`. Environment-specific overrides apply from `.env`. All configuration validates against Pydantic schemas with clear error messages including line numbers and valid examples. Invalid configuration prevents system startup.

**Technical Notes:** ConfigLoader class implemented in `src/phx_home_analysis/config/loader.py` using Pydantic BaseSettings + watchfiles. Configuration schema in `src/phx_home_analysis/validation/config_schemas.py`. Hot-reload via `@loader.watch()` method or CLI `--watch` flag. Environment overrides follow pydantic-settings pattern (`SECTION__FIELD` format). Dependencies added: pydantic-settings, watchfiles.

**Implementation Status:** ✅ COMPLETE | Tests: Unit tests for valid/invalid scenarios

**Definition of Done:** ConfigLoader class implemented | Templates created | Environment overrides working | Unit tests for valid/invalid scenarios | Actionable error messages

---

### E1.S2: Property Data Storage Layer

**Priority:** P0 | **Dependencies:** E1.S1 | **FRs:** FR7

**User Story:** As a system administrator, I want JSON-based property data storage with atomic writes, so that raw data is preserved separately from derived scores and survives crashes.

**Acceptance Criteria:** Writes to `enrichment_data.json` create backup at `.bak` before writing. Writes are atomic (complete or rolled back). File format is a LIST of property dictionaries (not keyed by address). Each record includes `full_address` and `normalized_address`. Lookup uses normalized address matching (lowercase, no punctuation). Backup can be restored after crash.

**Technical Notes:** JsonEnrichmentRepository implemented in `src/phx_home_analysis/repositories/json_repository.py`. CRITICAL: enrichment_data.json is a LIST (not dict). Normalized addresses via `normalize_address()` cached in `normalized_address` field. Atomic writes use temp file + rename. Backups with timestamp before each write. Restore via `restore_from_backup()`.

**Implementation Status:** ✅ COMPLETE | Tests: CRUD, atomic writes, crash recovery

**Definition of Done:** JsonEnrichmentRepository with CRUD | Atomic writes with backup | Address normalization | Unit tests | Crash recovery integration test

---

### E1.S3: Data Provenance and Lineage Tracking

**Priority:** P0 | **Dependencies:** E1.S2 | **FRs:** FR8, FR39

**User Story:** As a system user, I want every data field to track its source, confidence, and timestamp, so that I can assess data reliability and trace issues.

**Acceptance Criteria:** Records include `data_source`, `confidence` (0.0-1.0), and `fetched_at` (ISO 8601). Derived data records primary source plus `sources` array with minimum confidence. Users can see which agent/phase populated each section with High/Medium/Low confidence display.

**Technical Notes:** FieldProvenance dataclass in `src/phx_home_analysis/domain/entities_provenance.py` with source/confidence/fetched_at/derived_from. ProvenanceService in `src/phx_home_analysis/services/quality/`. Confidence: Assessor=0.95, Google=0.90, GreatSchools=0.90, Zillow/Redfin=0.85, Image=0.80, AI=0.70, CSV=0.90. Quality formula: 60% completeness + 40% confidence.

**Implementation Status:** ✅ COMPLETE | Tests: Provenance tracking, confidence calibration

**Definition of Done:** ProvenanceMetadata dataclass | All writes include provenance | Confidence calibration | Lineage query capability | Unit tests

---

### E1.S4: Pipeline State Checkpointing

**Priority:** P0 | **Dependencies:** E1.S2 | **FRs:** FR34, FR37

**User Story:** As a system user, I want pipeline progress checkpointed after each phase, so that I never lose completed work if the pipeline fails.

**Acceptance Criteria:** Phase completion updates `work_items.json` with status "completed" and timestamp. Each property has own phase tracking. Summary section shows overall progress. Checkpoint writes create backup first. No partial writes corrupt state file.

**Technical Notes:** WorkItemsRepository in `src/phx_home_analysis/repositories/work_items_repository.py` (~400 lines). State: session, work_items[], summary. Phase statuses: pending, in_progress, completed, failed, skipped. 30-minute stale detection for in_progress. Backup retention: 10 most recent. State transitions validated.

**Implementation Status:** ✅ COMPLETE | Tests: State transitions, stale detection, backup

**Definition of Done:** WorkItemsRepository with checkpoint ops | Per-property tracking | Summary calculation | Backup-before-write | Unit tests for state transitions

---

### E1.S5: Pipeline Resume Capability

**Priority:** P0 | **Dependencies:** E1.S4 | **FRs:** FR35, FR38

**User Story:** As a system user, I want to resume interrupted pipeline runs from the last checkpoint, so that I don't re-run completed work after failures.

**Acceptance Criteria:** Running with `--resume` loads state, resets items stuck >30 minutes to pending, processes only pending items, skips completed. Corrupt state reports clear validation errors with `--fresh` advice and data loss estimate. Resume merges results without duplicates.

**Technical Notes:** ResumePipeline class in `src/phx_home_analysis/pipeline/resume.py` (~300 lines). Methods: can_resume(), load_and_validate(), reset_stale_items(), get_pending_addresses(), prepare_fresh_start(), estimate_data_loss(). StateValidationError with details/suggestion. CLI flags via PhaseCoordinator (E5.S1).

**Implementation Status:** ✅ COMPLETE | Tests: Resume logic, state validation, merge

**Definition of Done:** Resume logic with stuck detection | State validation | Merge without duplicates | Interruption/resume integration test | Documentation

---

### E1.S6: Transient Error Recovery

**Priority:** P0 | **Dependencies:** E1.S5 | **FRs:** FR36, FR56

**User Story:** As a system user, I want automatic retry with exponential backoff for transient errors, so that temporary API failures don't require manual intervention.

**Acceptance Criteria:** Transient errors (429, 503, timeout) retry with exponential backoff (1s, 2s, 4s, 8s, 16s) up to 5 times, logging each attempt. Exhausted retries mark item "failed" with details and continue to next item. Non-transient errors (400, 401, 404) don't retry and suggest specific actions.

**Technical Notes:** Error handling in `src/phx_home_analysis/errors/` with 3 submodules. ErrorCategory enum via `is_transient_error()`. Transient: 429, 503, 504, 502, 500, ConnectionError, TimeoutError. @retry_with_backoff decorator: exponential (1s,2s,4s,8s,16s, cap 60s) with jitter. Standalone implementation (no tenacity). Pipeline integration via `mark_item_failed()`.

**Implementation Status:** ✅ COMPLETE | Tests: Error classification, retry, integration

**Definition of Done:** Retry decorator | Error categorization | Per-item failure tracking | Actionable error messages | Unit tests

---

## Epic 1 Implementation Summary

**Status:** COMPLETE (6/6 stories) | **Completed:** 2025-12-04
**Code:** ~2500 lines | **Tests:** ~1500 lines (150+ tests)

### Key Implementation Patterns

1. **Repository Pattern**: JsonEnrichmentRepository, WorkItemsRepository with atomic writes
2. **Provenance Tracking**: Field-level metadata (source/confidence/timestamp)
3. **State Machine**: Explicit phase/work item status transitions with validation
4. **Error Classification**: Conservative categorization (unknown=permanent)
5. **Exponential Backoff**: Jitter-enabled retry (1s→16s cap)
6. **Atomic Operations**: Temp file + rename pattern for crash safety

### Files Created

| File | Purpose |
|------|---------|
| `src/phx_home_analysis/config/loader.py` | ConfigLoader with YAML+env |
| `src/phx_home_analysis/repositories/json_repository.py` | JSON storage layer |
| `src/phx_home_analysis/repositories/work_items_repository.py` | State checkpointing |
| `src/phx_home_analysis/pipeline/resume.py` | Resume capability |
| `src/phx_home_analysis/errors/` | Error handling (3 modules) |
| `src/phx_home_analysis/services/quality/provenance_service.py` | Lineage tracking |
| `src/phx_home_analysis/domain/entities_provenance.py` | Provenance dataclass |

### Retrospective Reference

See `docs/sprint-artifacts/epic-1-retro-2025-12-04.md` for lessons learned.

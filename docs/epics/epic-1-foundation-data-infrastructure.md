# Epic 1: Foundation & Data Infrastructure

**User Value:** Enable reliable data storage, configuration management, and pipeline execution that supports crash recovery and data integrity.

**PRD Coverage:** FR7, FR8, FR34-39, FR46-51, FR56
**Architecture References:** ADR-02 (JSON Storage), Data Architecture, State Management

---

### E1.S1: Configuration System Setup

**Priority:** P0 | **Dependencies:** None | **FRs:** FR46, FR47, FR50, FR51

**User Story:** As a system administrator, I want externalized configuration for scoring weights and kill-switch criteria, so that I can adjust analysis parameters without code changes.

**Acceptance Criteria:** Configuration loads scoring weights from `config/scoring_weights.yaml` and kill-switch criteria from `config/kill_switch.csv`. Environment-specific overrides apply from `.env`. All configuration validates against Pydantic schemas with clear error messages including line numbers and valid examples. Invalid configuration prevents system startup.

**Technical Notes:** Implement `ConfigLoader` class in `src/phx_home_analysis/config/` using Pydantic `BaseSettings`. Configuration schema in `src/phx_home_analysis/validation/config_schemas.py`. Support hot-reload for development (`--watch` flag).

**Definition of Done:** ConfigLoader class implemented | Templates created | Environment overrides working | Unit tests for valid/invalid scenarios | Actionable error messages

---

### E1.S2: Property Data Storage Layer

**Priority:** P0 | **Dependencies:** E1.S1 | **FRs:** FR7

**User Story:** As a system administrator, I want JSON-based property data storage with atomic writes, so that raw data is preserved separately from derived scores and survives crashes.

**Acceptance Criteria:** Writes to `enrichment_data.json` create backup at `.bak` before writing. Writes are atomic (complete or rolled back). File format is a LIST of property dictionaries (not keyed by address). Each record includes `full_address` and `normalized_address`. Lookup uses normalized address matching (lowercase, no punctuation). Backup can be restored after crash.

**Technical Notes:** Implement `JsonEnrichmentRepository` in `src/phx_home_analysis/repositories/`. CRITICAL: enrichment_data.json is a LIST. Address normalization: `address.lower().replace(",", "").replace(".", "").strip()`. Use `shutil.copy` for backup, atomic write via temp file + rename.

**Definition of Done:** JsonEnrichmentRepository with CRUD | Atomic writes with backup | Address normalization | Unit tests | Crash recovery integration test

---

### E1.S3: Data Provenance and Lineage Tracking

**Priority:** P0 | **Dependencies:** E1.S2 | **FRs:** FR8, FR39

**User Story:** As a system user, I want every data field to track its source, confidence, and timestamp, so that I can assess data reliability and trace issues.

**Acceptance Criteria:** Records include `data_source`, `confidence` (0.0-1.0), and `fetched_at` (ISO 8601). Derived data records primary source plus `sources` array with minimum confidence. Users can see which agent/phase populated each section with High/Medium/Low confidence display.

**Technical Notes:** Add `ProvenanceMetadata` dataclass. Confidence mapping: County Assessor=0.95, Google Maps=0.90, GreatSchools=0.90, Zillow/Redfin=0.85, Image Assessment=0.80. Implement `ProvenanceTracker` service.

**Definition of Done:** ProvenanceMetadata dataclass | All writes include provenance | Confidence calibration | Lineage query capability | Unit tests

---

### E1.S4: Pipeline State Checkpointing

**Priority:** P0 | **Dependencies:** E1.S2 | **FRs:** FR34, FR37

**User Story:** As a system user, I want pipeline progress checkpointed after each phase, so that I never lose completed work if the pipeline fails.

**Acceptance Criteria:** Phase completion updates `work_items.json` with status "completed" and timestamp. Each property has own phase tracking. Summary section shows overall progress. Checkpoint writes create backup first. No partial writes corrupt state file.

**Technical Notes:** Implement `WorkItemsRepository`. State structure: session, current_phase, work_items[], summary. Phase statuses: pending, in_progress, completed, failed, skipped. 30-minute timeout for in_progress items (auto-reset on resume).

**Definition of Done:** WorkItemsRepository with checkpoint ops | Per-property tracking | Summary calculation | Backup-before-write | Unit tests for state transitions

---

### E1.S5: Pipeline Resume Capability

**Priority:** P0 | **Dependencies:** E1.S4 | **FRs:** FR35, FR38

**User Story:** As a system user, I want to resume interrupted pipeline runs from the last checkpoint, so that I don't re-run completed work after failures.

**Acceptance Criteria:** Running with `--resume` loads state, resets items stuck >30 minutes to pending, processes only pending items, skips completed. Corrupt state reports clear validation errors with `--fresh` advice and data loss estimate. Resume merges results without duplicates.

**Technical Notes:** Implement `resume_pipeline()` in `src/phx_home_analysis/pipeline/`. Timeout detection compares `started_at` with current time. Validation checks session_id consistency and schema version. CLI flag `--resume` is default if state exists.

**Definition of Done:** Resume logic with stuck detection | State validation | Merge without duplicates | Interruption/resume integration test | Documentation

---

### E1.S6: Transient Error Recovery

**Priority:** P0 | **Dependencies:** E1.S5 | **FRs:** FR36, FR56

**User Story:** As a system user, I want automatic retry with exponential backoff for transient errors, so that temporary API failures don't require manual intervention.

**Acceptance Criteria:** Transient errors (429, 503, timeout) retry with exponential backoff (1s, 2s, 4s, 8s, 16s) up to 5 times, logging each attempt. Exhausted retries mark item "failed" with details and continue to next item. Non-transient errors (400, 401, 404) don't retry and suggest specific actions.

**Technical Notes:** Implement `@retry_with_backoff` decorator. Transient: 429, 503, 504, ConnectionError. Non-transient: 400, 401, 403, 404. Use `tenacity` library. Error categorization in `src/phx_home_analysis/errors/`.

**Definition of Done:** Retry decorator | Error categorization | Per-item failure tracking | Actionable error messages | Unit tests

---

# Sprint 1: Foundation & Data Infrastructure

> **Epic**: E1
> **Objective**: Enable reliable data storage, configuration management, and pipeline execution with crash recovery
> **Stories**: 6
> **PRD Coverage**: FR7, FR8, FR34-39, FR46-51, FR56

### Stories

#### E1.S1 - Configuration System Setup [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | None |
| **FRs** | FR46, FR47, FR50, FR51 |

**Acceptance Criteria**:
- [ ] ConfigLoader class implemented with Pydantic validation
- [ ] `scoring_weights.yaml` and `kill_switch.csv` templates created
- [ ] Environment variable overrides working
- [ ] Unit tests for valid/invalid configuration scenarios
- [ ] Error messages include actionable guidance

**Definition of Done**:
- [ ] ConfigLoader in `src/phx_home_analysis/config/`
- [ ] Pydantic BaseSettings for environment variable integration
- [ ] Configuration schema in `src/phx_home_analysis/validation/config_schemas.py`
- [ ] Tests pass with 80%+ coverage on config module

---

#### E1.S2 - Property Data Storage Layer [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S1 |
| **FRs** | FR7 |

**Acceptance Criteria**:
- [ ] JsonEnrichmentRepository with CRUD operations
- [ ] Atomic write with backup-before-modify pattern
- [ ] Address normalization and lookup (lowercase, no punctuation)
- [ ] **CRITICAL**: enrichment_data.json is a LIST (not dict keyed by address)
- [ ] Integration test for crash recovery scenario

**Definition of Done**:
- [ ] Repository in `src/phx_home_analysis/repositories/`
- [ ] Backup created at `enrichment_data.json.bak` before every write
- [ ] Address normalization: `address.lower().replace(',', '').replace('.', '').strip()`
- [ ] Schema defined in `src/phx_home_analysis/validation/schemas.py`

---

#### E1.S3 - Data Provenance and Lineage Tracking

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S2 |
| **FRs** | FR8, FR39 |

**Acceptance Criteria**:
- [ ] ProvenanceMetadata dataclass with source, confidence, fetched_at
- [ ] All data writes include provenance metadata
- [ ] Confidence mapping: County=0.95, Maps=0.90, Schools=0.90, Listing=0.85, Image=0.80
- [ ] Lineage query capability implemented

**Definition of Done**:
- [ ] ProvenanceMetadata dataclass implemented
- [ ] ProvenanceTracker service created
- [ ] Each data section has its own provenance metadata
- [ ] Unit tests for provenance tracking

---

#### E1.S4 - Pipeline State Checkpointing

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S2 |
| **FRs** | FR34, FR37 |

**Acceptance Criteria**:
- [ ] WorkItemsRepository with checkpoint operations
- [ ] Per-property phase tracking
- [ ] State structure: session, current_phase, work_items[], summary
- [ ] Phase statuses: pending, in_progress, completed, failed, skipped
- [ ] 30-minute timeout for in_progress items

**Definition of Done**:
- [ ] WorkItemsRepository for `work_items.json`
- [ ] Checkpoint after each property-phase completion
- [ ] Backup-before-write pattern
- [ ] Unit tests for state transitions

---

#### E1.S5 - Pipeline Resume Capability

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S4 |
| **FRs** | FR35, FR38 |

**Acceptance Criteria**:
- [ ] `--resume` flag loads state from `work_items.json`
- [ ] Items stuck in 'in_progress' >30 minutes reset to 'pending'
- [ ] Only pending items processed, completed items skipped
- [ ] State validation with clear error messages

**Definition of Done**:
- [ ] `resume_pipeline()` function in `src/phx_home_analysis/pipeline/`
- [ ] Timeout detection via started_at comparison
- [ ] Merge strategy: preserve existing, add new
- [ ] Integration test simulating interruption and resume

---

#### E1.S6 - Transient Error Recovery [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S5 |
| **FRs** | FR36, FR56 |

**Acceptance Criteria**:
- [ ] Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
- [ ] Transient errors: 429, 503, 504, ConnectionError
- [ ] Non-transient errors: 400, 401, 403, 404 (no retry)
- [ ] Per-item failure tracking without pipeline abort
- [ ] Actionable error messages with troubleshooting guidance

**Definition of Done**:
- [ ] `@retry_with_backoff` decorator using tenacity library
- [ ] Error categorization in `src/phx_home_analysis/errors/`
- [ ] Unit tests for retry scenarios
- [ ] Error messages include: error type, suggested action

---

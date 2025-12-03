# PHX Houses Analysis Pipeline - Epics and Stories

**Author:** Andrew (PM Agent: John)
**Date:** 2025-12-03
**Project Level:** Personal Decision Support System
**Target Scale:** 100+ properties/month, single user

---

## Executive Summary

This document transforms the PRD's 62 functional requirements into 7 user-value-focused epics containing 42 implementation-ready stories. Each story is sized for completion by a single dev agent in one focused session.

**Epic Structure:**
| Epic | Title | Stories | Primary FRs | User Value |
|------|-------|---------|-------------|------------|
| 1 | Foundation & Data Infrastructure | 6 | FR7, FR8, FR34-39, FR46-51 | Enable reliable data storage and pipeline execution |
| 2 | Property Data Acquisition | 7 | FR1-6, FR58-62 | Gather complete property data from all sources |
| 3 | Kill-Switch Filtering System | 5 | FR9-14 | Instantly eliminate deal-breaker properties |
| 4 | Property Scoring Engine | 6 | FR15-20, FR25, FR27 | Rank properties by comprehensive quality score |
| 5 | Multi-Agent Pipeline Orchestration | 6 | FR28-33 | Coordinate automated property analysis |
| 6 | Visual Analysis & Risk Intelligence | 6 | FR21-24, FR26 | Assess property condition and surface hidden risks |
| 7 | Deal Sheet Generation & Reports | 6 | FR40-45, FR52-57 | Produce actionable property intelligence |

**Total:** 7 Epics, 42 Stories covering all 62 FRs

---

## Functional Requirements Inventory

### Property Data Acquisition (FR1-FR8)
| FR | Description | Priority |
|----|-------------|----------|
| FR1 | User can initiate batch property analysis for multiple properties via CLI command | P0 |
| FR2 | System can fetch authoritative property data from Maricopa County Assessor API | P0 |
| FR3 | System can extract listing data from Zillow and Redfin | P0 |
| FR4 | System can download and cache property images locally for analysis | P0 |
| FR5 | System can extract geographic data from Google Maps API | P0 |
| FR6 | System can fetch school ratings from GreatSchools API | P0 |
| FR7 | System can preserve raw property data separate from derived scores | P0 |
| FR8 | System can track data provenance for every data field | P0 |

### Kill-Switch Filtering (FR9-FR14)
| FR | Description | Priority |
|----|-------------|----------|
| FR9 | User can define HARD kill-switch criteria that result in instant rejection | P0 |
| FR10 | User can define SOFT kill-switch criteria with severity weights | P0 |
| FR11 | System can evaluate properties and return PASS/FAIL/WARNING verdicts | P0 |
| FR12 | System can calculate severity scores for SOFT criteria violations | P0 |
| FR13 | System can provide detailed explanations for kill-switch failures | P0 |
| FR14 | User can update kill-switch criteria via configuration files | P0 |

### Property Scoring (FR15-FR20)
| FR | Description | Priority |
|----|-------------|----------|
| FR15 | System can calculate comprehensive property scores across three dimensions | P0 |
| FR16 | System can apply 18+ scoring strategies with configurable weights | P0 |
| FR17 | System can classify properties into tiers (Unicorn, Contender, Pass) | P0 |
| FR18 | System can generate score breakdowns showing point allocation | P0 |
| FR19 | User can adjust scoring weights and trigger re-scoring without re-analysis | P1 |
| FR20 | System can track score deltas when priorities change | P1 |

### Risk Intelligence & Warnings (FR21-FR27)
| FR | Description | Priority |
|----|-------------|----------|
| FR21 | System can perform visual assessment of property images | P0 |
| FR22 | System can generate proactive warnings for hidden risks | P0 |
| FR23 | System can map risks to tangible consequences | P1 |
| FR24 | System can assign confidence levels to warnings | P1 |
| FR25 | System can apply Arizona-specific context to risk assessment | P0 |
| FR26 | System can identify properties with potential foundation issues | P1 |
| FR27 | System can estimate HVAC replacement timeline | P0 |

### Multi-Agent Pipeline Orchestration (FR28-FR33)
| FR | Description | Priority |
|----|-------------|----------|
| FR28 | User can execute complete multi-phase analysis via single CLI command | P0 |
| FR29 | System can coordinate sequential phase execution | P0 |
| FR30 | System can spawn specialized agents with appropriate model selection | P0 |
| FR31 | System can validate phase prerequisites before spawning next agent | P0 |
| FR32 | System can execute Phase 1 sub-tasks in parallel | P0 |
| FR33 | System can aggregate multi-agent outputs into unified records | P0 |

### State Management & Reliability (FR34-FR39)
| FR | Description | Priority |
|----|-------------|----------|
| FR34 | System can checkpoint pipeline progress after each phase | P0 |
| FR35 | System can resume interrupted pipeline from last checkpoint | P0 |
| FR36 | System can detect and recover from transient errors | P0 |
| FR37 | System can preserve previous state before risky operations | P0 |
| FR38 | User can validate pipeline state and data integrity | P0 |
| FR39 | System can track which phase/agent populated each data field | P0 |

### Analysis Outputs & Reports (FR40-FR45)
| FR | Description | Priority |
|----|-------------|----------|
| FR40 | System can generate comprehensive deal sheets | P0 |
| FR41 | Deal sheets include summary, scores, tier, verdict, warnings | P0 |
| FR42 | System can generate score explanation narratives | P1 |
| FR43 | System can generate visual comparisons (radar, scatter) | P1 |
| FR44 | System can produce risk checklists for property tours | P1 |
| FR45 | User can regenerate deal sheets after re-scoring | P1 |

### Configuration & Extensibility (FR46-FR51)
| FR | Description | Priority |
|----|-------------|----------|
| FR46 | User can externalize scoring weights to YAML configuration | P0 |
| FR47 | User can externalize kill-switch criteria to CSV configuration | P0 |
| FR48 | User can define new scoring dimensions by adding strategies | P1 |
| FR49 | User can add new kill-switch criteria without code changes | P1 |
| FR50 | System can load configuration files at runtime and validate | P0 |
| FR51 | User can maintain environment-specific configuration overrides | P0 |

### CLI User Experience (FR52-FR57)
| FR | Description | Priority |
|----|-------------|----------|
| FR52 | User can execute manual phase-specific scripts | P0 |
| FR53 | User can pass flags to control pipeline behavior | P0 |
| FR54 | User can view structured console output with progress indicators | P0 |
| FR55 | System can generate human-readable logs and JSON outputs | P0 |
| FR56 | User can access detailed error traces with troubleshooting guidance | P0 |
| FR57 | User can query pipeline status and view pending tasks | P0 |

### Integration Management (FR58-FR62)
| FR | Description | Priority |
|----|-------------|----------|
| FR58 | System can authenticate with external APIs using environment secrets | P0 |
| FR59 | System can handle API rate limits with exponential backoff | P0 |
| FR60 | System can cache API responses to minimize costs | P0 |
| FR61 | System can rotate browser User-Agents and proxies | P0 |
| FR62 | System can fall back to alternative extraction methods | P0 |

---

## FR Coverage Matrix

| FR ID | Description | Epic | Story | Status |
|-------|-------------|------|-------|--------|
| FR1 | Batch property analysis via CLI | 2 | E2.S1 | Ready |
| FR2 | Maricopa County Assessor API integration | 2 | E2.S2 | Ready |
| FR3 | Zillow/Redfin listing extraction | 2 | E2.S3 | Ready |
| FR4 | Property image download and caching | 2 | E2.S4 | Ready |
| FR5 | Google Maps API geographic data | 2 | E2.S5 | Ready |
| FR6 | GreatSchools API school ratings | 2 | E2.S6 | Ready |
| FR7 | Raw data preservation | 1 | E1.S2 | Ready |
| FR8 | Data provenance tracking | 1 | E1.S3 | Ready |
| FR9 | HARD kill-switch criteria | 3 | E3.S1 | Ready |
| FR10 | SOFT kill-switch criteria with severity | 3 | E3.S2 | Ready |
| FR11 | Kill-switch verdict evaluation | 3 | E3.S3 | Ready |
| FR12 | Severity score calculation | 3 | E3.S2 | Ready |
| FR13 | Kill-switch failure explanations | 3 | E3.S4 | Ready |
| FR14 | Kill-switch configuration updates | 3 | E3.S5 | Ready |
| FR15 | Three-dimension scoring calculation | 4 | E4.S1 | Ready |
| FR16 | 18+ scoring strategies with weights | 4 | E4.S2 | Ready |
| FR17 | Tier classification (Unicorn/Contender/Pass) | 4 | E4.S3 | Ready |
| FR18 | Score breakdown generation | 4 | E4.S4 | Ready |
| FR19 | Scoring weight adjustment and re-scoring | 4 | E4.S5 | Ready |
| FR20 | Score delta tracking | 4 | E4.S6 | Ready |
| FR21 | Visual property image assessment | 6 | E6.S1 | Ready |
| FR22 | Proactive warning generation | 6 | E6.S2 | Ready |
| FR23 | Risk-to-consequence mapping | 6 | E6.S3 | Ready |
| FR24 | Warning confidence levels | 6 | E6.S4 | Ready |
| FR25 | Arizona-specific context application | 4 | E4.S2 | Ready |
| FR26 | Foundation issue identification | 6 | E6.S5 | Ready |
| FR27 | HVAC replacement timeline estimation | 6 | E6.S6 | Ready |
| FR28 | Single CLI command pipeline execution | 5 | E5.S1 | Ready |
| FR29 | Sequential phase coordination | 5 | E5.S2 | Ready |
| FR30 | Agent spawning with model selection | 5 | E5.S3 | Ready |
| FR31 | Phase prerequisite validation | 5 | E5.S4 | Ready |
| FR32 | Parallel Phase 1 execution | 5 | E5.S5 | Ready |
| FR33 | Multi-agent output aggregation | 5 | E5.S6 | Ready |
| FR34 | Pipeline checkpointing | 1 | E1.S4 | Ready |
| FR35 | Interrupted pipeline resume | 1 | E1.S5 | Ready |
| FR36 | Transient error recovery | 1 | E1.S6 | Ready |
| FR37 | State preservation before risky operations | 1 | E1.S4 | Ready |
| FR38 | Pipeline state validation | 1 | E1.S5 | Ready |
| FR39 | Data lineage tracking | 1 | E1.S3 | Ready |
| FR40 | Deal sheet generation | 7 | E7.S1 | Ready |
| FR41 | Deal sheet content (summary, scores, tier) | 7 | E7.S2 | Ready |
| FR42 | Score explanation narratives | 7 | E7.S3 | Ready |
| FR43 | Visual comparisons (radar, scatter) | 7 | E7.S4 | Ready |
| FR44 | Risk checklists for tours | 7 | E7.S5 | Ready |
| FR45 | Deal sheet regeneration after re-scoring | 7 | E7.S6 | Ready |
| FR46 | YAML scoring weight externalization | 1 | E1.S1 | Ready |
| FR47 | CSV kill-switch criteria externalization | 1 | E1.S1 | Ready |
| FR48 | New scoring dimension definition | 4 | E4.S2 | Ready |
| FR49 | New kill-switch criteria without code | 3 | E3.S5 | Ready |
| FR50 | Configuration loading and validation | 1 | E1.S1 | Ready |
| FR51 | Environment-specific configuration | 1 | E1.S1 | Ready |
| FR52 | Manual phase-specific scripts | 7 | E7.S1 | Ready |
| FR53 | Pipeline behavior flags | 5 | E5.S1 | Ready |
| FR54 | Structured console output with progress | 7 | E7.S1 | Ready |
| FR55 | Human-readable logs and JSON outputs | 7 | E7.S1 | Ready |
| FR56 | Error traces with troubleshooting guidance | 1 | E1.S6 | Ready |
| FR57 | Pipeline status query | 5 | E5.S1 | Ready |
| FR58 | API authentication with environment secrets | 2 | E2.S7 | Ready |
| FR59 | API rate limit handling | 2 | E2.S7 | Ready |
| FR60 | API response caching | 2 | E2.S7 | Ready |
| FR61 | Browser User-Agent and proxy rotation | 2 | E2.S3 | Ready |
| FR62 | Alternative extraction method fallback | 2 | E2.S3 | Ready |

**Coverage Summary:** 62/62 FRs mapped (100%)

---

## Epic 1: Foundation & Data Infrastructure

**User Value:** Enable reliable data storage, configuration management, and pipeline execution that supports crash recovery and data integrity across all subsequent analysis operations.

**PRD Coverage:** FR7, FR8, FR34-39, FR46-51, FR56
**Architecture References:** ADR-02 (JSON Storage), Data Architecture, State Management

---

### Story 1.1: Configuration System Setup

**As a** system administrator,
**I want** externalized configuration for scoring weights and kill-switch criteria,
**So that** I can adjust analysis parameters without code changes.

**Acceptance Criteria:**

**Given** the system is starting up
**When** configuration files are loaded
**Then** scoring weights are read from `config/scoring_weights.yaml`
**And** kill-switch criteria are read from `config/kill_switch.csv`
**And** environment-specific overrides are applied from `.env`
**And** all configuration is validated against Pydantic schemas
**And** invalid configuration raises clear error messages with line numbers

**Given** a configuration file has invalid values
**When** the system attempts to load it
**Then** validation errors specify the exact field and constraint violated
**And** the system refuses to start with incomplete configuration
**And** error message includes example of valid configuration

**Prerequisites:** None (foundation story)

**Technical Notes:**
- Implement `ConfigLoader` class in `src/phx_home_analysis/config/`
- Use Pydantic `BaseSettings` for environment variable integration
- YAML parsing with `pyyaml`, CSV with standard library
- Configuration schema in `src/phx_home_analysis/validation/config_schemas.py`
- Support hot-reload for development (`--watch` flag)

**Definition of Done:**
- [ ] ConfigLoader class implemented with Pydantic validation
- [ ] scoring_weights.yaml and kill_switch.csv templates created
- [ ] Environment variable overrides working
- [ ] Unit tests for valid/invalid configuration scenarios
- [ ] Error messages include actionable guidance

---

### Story 1.2: Property Data Storage Layer

**As a** system administrator,
**I want** JSON-based property data storage with atomic writes,
**So that** raw data is preserved separately from derived scores and survives crashes.

**Acceptance Criteria:**

**Given** a property needs to be saved
**When** the repository writes to `enrichment_data.json`
**Then** a backup is created at `enrichment_data.json.bak` before writing
**And** the write is atomic (complete or rolled back)
**And** the file format is a LIST of property dictionaries (not keyed by address)
**And** each property record includes `full_address` and `normalized_address`

**Given** the system needs to find a property
**When** searching by address
**Then** the lookup uses normalized address matching (lowercase, no punctuation)
**And** the first matching property is returned
**And** None is returned if no match exists

**Given** a write operation fails mid-stream
**When** the system restarts
**Then** the backup file can be restored
**And** no data corruption occurs

**Prerequisites:** E1.S1

**Technical Notes:**
- Implement `JsonEnrichmentRepository` in `src/phx_home_analysis/repositories/`
- CRITICAL: enrichment_data.json is a LIST, not a dict keyed by address
- Address normalization: `address.lower().replace(",", "").replace(".", "").strip()`
- Use `shutil.copy` for backup, then atomic write via temp file + rename
- Schema defined in `src/phx_home_analysis/validation/schemas.py`

**Definition of Done:**
- [ ] JsonEnrichmentRepository with CRUD operations
- [ ] Atomic write with backup-before-modify pattern
- [ ] Address normalization and lookup
- [ ] Unit tests for all repository operations
- [ ] Integration test for crash recovery scenario

---

### Story 1.3: Data Provenance and Lineage Tracking

**As a** system user,
**I want** every data field to track its source, confidence, and timestamp,
**So that** I can assess data reliability and trace issues.

**Acceptance Criteria:**

**Given** data is populated from an external source
**When** the field is written to enrichment_data.json
**Then** the record includes `data_source` (e.g., "maricopa_assessor", "zillow")
**And** the record includes `confidence` (0.0-1.0 scale)
**And** the record includes `fetched_at` (ISO 8601 timestamp)

**Given** data is derived from multiple sources
**When** the final value is determined
**Then** the primary source is recorded
**And** a `sources` array lists all contributing sources
**And** confidence is the minimum of contributing sources

**Given** a user queries data provenance
**When** viewing a property record
**Then** they can see exactly which agent/phase populated each section
**And** confidence levels are displayed (High/Medium/Low)

**Prerequisites:** E1.S2

**Technical Notes:**
- Add `ProvenanceMetadata` dataclass with source, confidence, fetched_at
- Confidence mapping: County Assessor=0.95, Google Maps=0.90, GreatSchools=0.90, Zillow/Redfin=0.85, Image Assessment=0.80
- Implement `ProvenanceTracker` service
- Each data section (county_data, listing_data, location_data, image_assessment) has its own provenance

**Definition of Done:**
- [ ] ProvenanceMetadata dataclass implemented
- [ ] All data writes include provenance metadata
- [ ] Confidence levels properly calibrated
- [ ] Lineage query capability implemented
- [ ] Unit tests for provenance tracking

---

### Story 1.4: Pipeline State Checkpointing

**As a** system user,
**I want** pipeline progress checkpointed after each phase,
**So that** I never lose completed work if the pipeline fails.

**Acceptance Criteria:**

**Given** a pipeline phase completes successfully
**When** the checkpoint is written
**Then** `work_items.json` is updated with phase status "completed"
**And** `completed_at` timestamp is recorded
**And** a backup is created before writing

**Given** multiple properties are being processed
**When** viewing work_items.json
**Then** each property has its own phase status tracking
**And** a summary section shows overall progress counts
**And** `last_checkpoint` timestamp reflects the most recent save

**Given** a checkpoint write fails
**When** reviewing the state
**Then** the previous checkpoint is still valid
**And** no partial writes corrupt the state file

**Prerequisites:** E1.S2

**Technical Notes:**
- Implement `WorkItemsRepository` for work_items.json
- State structure per Architecture: session, current_phase, work_items[], summary
- Phase statuses: pending, in_progress, completed, failed, skipped
- Checkpoint after each property-phase completion, not just phase completion
- 30-minute timeout for in_progress items (auto-reset to pending on resume)

**Definition of Done:**
- [ ] WorkItemsRepository with checkpoint operations
- [ ] Per-property phase tracking
- [ ] Summary calculation logic
- [ ] Backup-before-write pattern
- [ ] Unit tests for state transitions

---

### Story 1.5: Pipeline Resume Capability

**As a** system user,
**I want** to resume interrupted pipeline runs from the last checkpoint,
**So that** I don't re-run completed work after failures.

**Acceptance Criteria:**

**Given** a pipeline was interrupted
**When** running with `--resume` flag
**Then** state is loaded from work_items.json
**And** items stuck in "in_progress" for >30 minutes are reset to "pending"
**And** only pending items are processed
**And** completed items are skipped

**Given** state file is corrupted
**When** attempting to resume
**Then** validation errors are reported clearly
**And** user is advised to use `--fresh` with warning about data loss
**And** the estimate of data loss is provided

**Given** successful resume completes
**When** reviewing results
**Then** completed and resumed items are merged correctly
**And** no duplicate entries exist
**And** final summary reflects total processing

**Prerequisites:** E1.S4

**Technical Notes:**
- Implement `resume_pipeline()` function in `src/phx_home_analysis/pipeline/`
- Timeout detection: compare `started_at` with current time
- Validation: check session_id consistency, schema version
- Merge strategy: preserve existing enrichment data, add new
- CLI flag: `--resume` (default behavior if state exists)

**Definition of Done:**
- [ ] Resume logic with stuck item detection
- [ ] State validation with clear error messages
- [ ] Merge without duplicates
- [ ] Integration test simulating interruption and resume
- [ ] Documentation of resume behavior

---

### Story 1.6: Transient Error Recovery

**As a** system user,
**I want** automatic retry with exponential backoff for transient errors,
**So that** temporary API failures don't require manual intervention.

**Acceptance Criteria:**

**Given** an API request fails with a transient error (429, 503, timeout)
**When** the retry logic activates
**Then** the request is retried with exponential backoff (1s, 2s, 4s, 8s, 16s)
**And** maximum 5 retries are attempted
**And** each retry is logged with attempt number

**Given** all retries are exhausted
**When** the error persists
**Then** the item is marked as "failed" in work_items.json
**And** error details are recorded (error type, message, timestamp)
**And** the pipeline continues with next item (no full abort)
**And** user receives actionable troubleshooting guidance

**Given** a non-transient error occurs (400, 401, 404)
**When** the error is detected
**Then** no retry is attempted
**And** the error is logged with clear categorization
**And** appropriate action is suggested (e.g., "Check API token" for 401)

**Prerequisites:** E1.S5

**Technical Notes:**
- Implement `@retry_with_backoff` decorator
- Transient errors: 429 (rate limit), 503 (service unavailable), 504 (timeout), ConnectionError
- Non-transient: 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found)
- Use `tenacity` library for retry logic
- Error categorization in `src/phx_home_analysis/errors/`

**Definition of Done:**
- [ ] Retry decorator with exponential backoff
- [ ] Error categorization (transient vs non-transient)
- [ ] Per-item failure tracking without pipeline abort
- [ ] Actionable error messages
- [ ] Unit tests for retry scenarios

---

## Epic 2: Property Data Acquisition

**User Value:** Gather complete, authoritative property data from multiple sources (County Assessor, Zillow/Redfin, Google Maps, GreatSchools) to enable comprehensive analysis.

**PRD Coverage:** FR1-6, FR58-62
**Architecture References:** Integration Architecture, Stealth Browser Strategy, API Cost Estimation

---

### Story 2.1: Batch Analysis CLI Entry Point

**As a** system user,
**I want** to initiate batch property analysis via a single CLI command,
**So that** I can analyze multiple properties efficiently.

**Acceptance Criteria:**

**Given** a CSV file with property listings exists
**When** running `python scripts/phx_home_analyzer.py --all`
**Then** all properties in the CSV are queued for analysis
**And** progress is displayed with property count and current item
**And** ETA is estimated based on average processing time

**Given** the command includes `--test` flag
**When** the analysis runs
**Then** only the first 5 properties are processed
**And** output indicates test mode is active

**Given** the command includes `--dry-run` flag
**When** the analysis runs
**Then** no external API calls are made
**And** the pipeline validates input data and configuration
**And** estimated processing time is displayed

**Given** invalid input data is detected
**When** validation fails
**Then** specific errors are listed with row numbers
**And** the pipeline does not proceed until errors are fixed

**Prerequisites:** E1.S1, E1.S4

**Technical Notes:**
- Use argparse for CLI argument parsing
- Input file: `data/phx_homes.csv` (address, price, beds, baths, sqft)
- Flags: `--all`, `--test`, `--resume`, `--strict`, `--dry-run`, `--json`
- Progress display using `rich` library with spinner and progress bar
- ETA calculation: rolling average of last 5 properties

**Definition of Done:**
- [ ] CLI entry point with all flags implemented
- [ ] CSV validation with clear error messages
- [ ] Progress display with ETA
- [ ] Test mode limiting to 5 properties
- [ ] Dry-run mode without external calls

---

### Story 2.2: Maricopa County Assessor API Integration

**As a** system user,
**I want** to fetch authoritative property data from Maricopa County Assessor,
**So that** I have reliable lot size, year built, and system information.

**Acceptance Criteria:**

**Given** a valid property address
**When** querying the County Assessor API
**Then** the following fields are retrieved: lot_sqft, year_built, garage_spaces, has_pool, sewer_type
**And** data is stored in `county_data` section with provenance metadata
**And** confidence level is set to 0.95 (authoritative source)

**Given** the property is not found in county records
**When** the query returns empty
**Then** the property is flagged with "county_data_missing" warning
**And** analysis continues with available data
**And** confidence level for missing fields is set to 0.0

**Given** API rate limit is hit (429 response)
**When** retry logic activates
**Then** exponential backoff is applied per E1.S6
**And** successful retry stores data normally

**Prerequisites:** E1.S3, E1.S6, E2.S7

**Technical Notes:**
- API endpoint: Maricopa County Assessor REST API
- Authentication: Bearer token from `MARICOPA_ASSESSOR_TOKEN` env var
- Rate limit: ~1 req/sec recommended
- Implement `CountyAssessorClient` in `src/phx_home_analysis/services/county_data/`
- Field mapping from API response to domain model

**Definition of Done:**
- [ ] CountyAssessorClient with authentication
- [ ] Field mapping and data extraction
- [ ] Provenance metadata attached
- [ ] Error handling for missing properties
- [ ] Integration test with mocked API

---

### Story 2.3: Zillow/Redfin Listing Extraction

**As a** system user,
**I want** to extract listing data from Zillow and Redfin using stealth browsers,
**So that** I have current price, HOA, and property details.

**Acceptance Criteria:**

**Given** a valid property address
**When** extracting from Zillow
**Then** the following fields are retrieved: price, beds, baths, sqft, hoa_fee, listing_url, images[]
**And** data is stored in `listing_data` section with provenance
**And** nodriver (stealth Chrome) is used as primary extraction method

**Given** Zillow extraction fails (anti-bot detection)
**When** fallback is triggered
**Then** curl-cffi with browser TLS fingerprints is attempted
**And** if curl-cffi fails, Playwright MCP is attempted as final fallback
**And** successful extraction from any method stores data normally

**Given** proxy rotation is required
**When** requests are made
**Then** User-Agent is rotated from a pool of 20+ browser signatures
**And** residential proxy is used with random IP selection
**And** delays between requests are randomized (2-5 seconds)

**Given** a property listing is not found
**When** all extraction methods fail
**Then** property is flagged with "listing_not_found" status
**And** analysis continues without listing data
**And** confidence for listing fields is set to 0.0

**Prerequisites:** E2.S1, E2.S7

**Technical Notes:**
- Primary: nodriver for stealth Chrome automation (PerimeterX bypass)
- Fallback 1: curl-cffi with browser TLS fingerprints
- Fallback 2: Playwright MCP via browser_navigate
- Implement in `scripts/extract_images.py` and `src/phx_home_analysis/services/listing_extraction/`
- User-Agent pool in `config/user_agents.txt`
- Proxy config from environment variables

**Definition of Done:**
- [ ] nodriver extraction with stealth configuration
- [ ] curl-cffi fallback implementation
- [ ] Playwright MCP fallback
- [ ] User-Agent and proxy rotation
- [ ] Image URL extraction and download
- [ ] Integration test with mock server

---

### Story 2.4: Property Image Download and Caching

**As a** system user,
**I want** property images downloaded and cached locally,
**So that** visual assessment can be performed offline.

**Acceptance Criteria:**

**Given** listing extraction returns image URLs
**When** images are downloaded
**Then** images are saved to `data/property_images/{normalized_address}/`
**And** filenames are `img_001.jpg`, `img_002.jpg`, etc.
**And** original URL is preserved in `images_manifest.json`

**Given** an image download fails
**When** the error is non-transient
**Then** the failed URL is logged
**And** download continues with remaining images
**And** manifest records which images are missing

**Given** images already exist in cache
**When** re-running extraction
**Then** existing images are preserved (not re-downloaded)
**And** only new images are fetched
**And** manifest is updated with current state

**Given** cache cleanup is requested
**When** running with `--clean-images` flag
**Then** images older than 14 days are removed
**And** manifest is updated to reflect removal

**Prerequisites:** E2.S3

**Technical Notes:**
- Image directory: `data/property_images/{normalized_address}/`
- Manifest: `images_manifest.json` with URL -> filename mapping
- Use httpx for async image downloads
- Respect rate limits with semaphore (max 5 concurrent downloads)
- Image formats: jpg, png, webp (convert to jpg for consistency)

**Definition of Done:**
- [ ] Image download with manifest tracking
- [ ] Cache hit detection (skip existing)
- [ ] Parallel downloads with rate limiting
- [ ] Cache cleanup functionality
- [ ] Unit tests for download and caching

---

### Story 2.5: Google Maps API Geographic Data

**As a** system user,
**I want** geographic data from Google Maps API,
**So that** I have accurate geocoding, distances, and orientation.

**Acceptance Criteria:**

**Given** a valid property address
**When** querying Google Maps Geocoding API
**Then** latitude and longitude are retrieved
**And** formatted address is standardized
**And** data is cached to minimize API costs

**Given** geocoded coordinates are available
**When** calculating distances
**Then** distance to work location is computed (from config)
**And** distance to nearest supermarket is computed
**And** distance to nearest park is computed
**And** results are stored in `location_data` section

**Given** satellite imagery is analyzed
**When** determining sun orientation
**Then** backyard direction is inferred (N/E/S/W)
**And** orientation is stored with confidence level
**And** north-facing = 25pts, east = 18.75pts, south = 12.5pts, west = 0pts (per Architecture)

**Prerequisites:** E2.S7

**Technical Notes:**
- APIs: Geocoding API, Distance Matrix API, Places API (nearby search)
- API key from `GOOGLE_MAPS_API_KEY` env var
- Cache responses in `data/api_cache/google_maps/` with 7-day TTL
- Orientation determination: Use satellite imagery via map-analyzer agent
- Cost estimate: ~$0.05-0.10 per property

**Definition of Done:**
- [ ] Geocoding with response caching
- [ ] Distance calculations to POIs
- [ ] Orientation determination logic
- [ ] API cost tracking
- [ ] Integration test with mocked API

---

### Story 2.6: GreatSchools API School Ratings

**As a** system user,
**I want** school ratings from GreatSchools API,
**So that** I can assess neighborhood education quality.

**Acceptance Criteria:**

**Given** geocoded property coordinates
**When** querying GreatSchools API
**Then** elementary, middle, and high school ratings are retrieved (1-10 scale)
**And** school names and distances are included
**And** data is cached with 30-day TTL (ratings change infrequently)

**Given** school catchment data is available
**When** determining assigned schools
**Then** the specific assigned schools are identified (not just nearby)
**And** ratings reflect assigned schools, not just closest

**Given** GreatSchools API is unavailable
**When** fallback is triggered
**Then** nearby schools are identified via Google Places
**And** ratings are marked as "unverified" with lower confidence (0.5)

**Prerequisites:** E2.S5, E2.S7

**Technical Notes:**
- API: GreatSchools API with free tier (1000 requests/day)
- API key from `GREATSCHOOLS_API_KEY` env var
- Cache in `data/api_cache/greatschools/` with 30-day TTL
- School rating formula: (elementary * 0.3) + (middle * 0.3) + (high * 0.4) = composite
- Confidence: 0.90 for GreatSchools, 0.50 for Google Places fallback

**Definition of Done:**
- [ ] GreatSchools API client
- [ ] Assigned school determination
- [ ] Composite rating calculation
- [ ] Response caching with TTL
- [ ] Fallback to Google Places

---

### Story 2.7: API Integration Infrastructure

**As a** system user,
**I want** robust API integration with authentication, rate limiting, and caching,
**So that** external data sources are accessed reliably and cost-efficiently.

**Acceptance Criteria:**

**Given** an API requires authentication
**When** the request is made
**Then** credentials are loaded from environment variables
**And** no credentials are logged or exposed in errors
**And** 401 errors suggest checking API token

**Given** API rate limits exist
**When** approaching the limit
**Then** requests are throttled proactively
**And** 429 responses trigger exponential backoff
**And** rate limit headers are respected when available

**Given** API responses are cacheable
**When** a cache-eligible request is made
**Then** cache is checked before making external request
**And** cache hits avoid external calls
**And** cache entries have configurable TTL (default 7 days)
**And** cache hit rate is logged for cost optimization

**Prerequisites:** E1.S6

**Technical Notes:**
- Implement `APIClient` base class with authentication, retry, caching
- Credentials from environment: `*_API_KEY`, `*_TOKEN` patterns
- Cache location: `data/api_cache/{service_name}/`
- Cache key: hash of request URL + params
- Rate limit tracking: per-service counters with reset windows

**Definition of Done:**
- [ ] APIClient base class with auth support
- [ ] Rate limiting with proactive throttling
- [ ] Response caching with configurable TTL
- [ ] Cache hit rate logging
- [ ] Unit tests for all integration patterns

---

## Epic 3: Kill-Switch Filtering System

**User Value:** Instantly eliminate properties that fail non-negotiable criteria (HOA, beds, baths, sqft, lot, garage, sewer) before any scoring, saving time on obviously unsuitable properties.

**PRD Coverage:** FR9-14
**Architecture References:** ADR-04 (All Kill-Switch Criteria Are HARD), Kill-Switch Architecture

---

### Story 3.1: HARD Kill-Switch Criteria Implementation

**As a** system user,
**I want** HARD kill-switch criteria that instantly reject properties,
**So that** non-negotiable deal-breakers are caught immediately.

**Acceptance Criteria:**

**Given** a property with any HARD criterion failing
**When** kill-switch evaluation runs
**Then** verdict is immediately "FAIL"
**And** the specific failed criterion is identified
**And** no further criteria are evaluated after first HARD failure

**Given** the 7 HARD criteria per PRD
**When** evaluating a property
**Then** HOA must be exactly $0 (any positive value = FAIL)
**And** Bedrooms must be >= 4
**And** Bathrooms must be >= 2.0
**And** House SQFT must be > 1800
**And** Lot Size must be > 8000 sqft
**And** Garage must have >= 1 indoor space
**And** Sewer must be "city" (not "septic" or "unknown")

**Given** a property passes all HARD criteria
**When** evaluation completes
**Then** verdict is "PASS"
**And** all criteria results are recorded with actual values

**Prerequisites:** E1.S1

**Technical Notes:**
- Implement `KillSwitchFilter` in `src/phx_home_analysis/services/kill_switch/`
- Each criterion is a separate class (HoaKillSwitch, BedroomsKillSwitch, etc.)
- Return `CriterionResult(passed: bool, value: Any, note: str)`
- Per Architecture: all 7 criteria are HARD (instant fail), no SOFT in PRD

**Definition of Done:**
- [ ] KillSwitchFilter orchestrating all 7 criteria
- [ ] Individual criterion classes with evaluation logic
- [ ] Short-circuit on first HARD failure
- [ ] Unit tests for each criterion with boundary cases
- [ ] Integration test for full evaluation flow

---

### Story 3.2: SOFT Kill-Switch Severity System

**As a** system user,
**I want** a SOFT severity system for future flexibility,
**So that** I can add non-critical preferences that accumulate.

**Acceptance Criteria:**

**Given** SOFT criteria are defined (future use)
**When** evaluation runs
**Then** severity scores are accumulated for each violation
**And** total severity is compared against threshold (default 3.0)
**And** severity >= 3.0 results in FAIL verdict
**And** severity 1.5-3.0 results in WARNING verdict
**And** severity < 1.5 results in PASS verdict

**Given** the PRD specifies all criteria as HARD
**When** current system runs
**Then** no SOFT criteria are active
**And** the severity system is available for future configuration

**Given** a SOFT criterion is added via config
**When** it's evaluated
**Then** severity weight is applied if criterion fails
**And** weight comes from configuration file

**Prerequisites:** E3.S1

**Technical Notes:**
- Implement `SoftSeverityEvaluator` in `src/phx_home_analysis/services/kill_switch/`
- Severity thresholds: FAIL >= 3.0, WARNING 1.5-3.0, PASS < 1.5
- Currently no SOFT criteria per PRD (all are HARD)
- Structure allows future addition via config/kill_switch.csv
- Example future SOFT: "Pool" (severity 0.5 if no pool wanted but present)

**Definition of Done:**
- [ ] SoftSeverityEvaluator with accumulation logic
- [ ] Threshold-based verdict determination
- [ ] Configuration-driven criterion loading
- [ ] Unit tests with simulated SOFT criteria
- [ ] Documentation for adding future SOFT criteria

---

### Story 3.3: Kill-Switch Verdict Evaluation

**As a** system user,
**I want** a clear verdict (PASS/FAIL/WARNING) for each property,
**So that** I can quickly filter properties.

**Acceptance Criteria:**

**Given** kill-switch evaluation completes
**When** generating the verdict
**Then** result includes overall verdict (PASS/FAIL/WARNING)
**And** result includes list of failed criteria (if any)
**And** result includes severity score (if SOFT criteria exist)
**And** result includes evaluation timestamp

**Given** a property fails one or more criteria
**When** reviewing the result
**Then** all failed criteria are listed (not just first)
**And** actual values are shown alongside requirements
**And** the most impactful failure is highlighted

**Given** verdict needs to be displayed
**When** formatting for output
**Then** PASS = green checkmark (🟢)
**And** WARNING = yellow circle (🟡)
**And** FAIL = red circle (🔴)
**And** emoji + text for accessibility

**Prerequisites:** E3.S1, E3.S2

**Technical Notes:**
- Implement `KillSwitchResult` dataclass with verdict, failed_criteria, severity, details, evaluated_at
- Verdict enum: PASS, WARNING, FAIL
- Store in `kill_switch` section of property record
- Formatting utilities in `src/phx_home_analysis/reporters/`

**Definition of Done:**
- [ ] KillSwitchResult dataclass
- [ ] Verdict determination logic
- [ ] Multi-failure tracking
- [ ] Formatted output with emojis
- [ ] Unit tests for verdict scenarios

---

### Story 3.4: Kill-Switch Failure Explanations

**As a** system user,
**I want** detailed explanations for kill-switch failures,
**So that** I understand exactly why a property was rejected.

**Acceptance Criteria:**

**Given** a property fails kill-switch
**When** generating the explanation
**Then** explanation includes criterion name and requirement
**And** explanation includes actual value found
**And** explanation includes consequence (e.g., "This property has HOA of $150/month")
**And** explanation is human-readable (not technical jargon)

**Given** multiple criteria fail
**When** generating explanations
**Then** each failure has its own explanation
**And** failures are ordered by severity/impact
**And** a summary sentence is provided ("Failed 2 of 7 criteria")

**Given** explanation needs to be shown in deal sheet
**When** formatting for HTML
**Then** failures are displayed as warning cards
**And** each card has severity-appropriate color (red border)
**And** UX pattern from ux-design-specification.md is followed

**Prerequisites:** E3.S3

**Technical Notes:**
- Implement `KillSwitchExplainer` in `src/phx_home_analysis/services/kill_switch/`
- Consequence mapping: HOA → "$X/month adds to ownership cost", Sewer → "Septic requires $X maintenance"
- Templates for each criterion's explanation
- Integration with Warning Card component from UX spec

**Definition of Done:**
- [ ] Explanation generation for each criterion
- [ ] Multi-failure summary
- [ ] Consequence mapping
- [ ] HTML formatting for deal sheets
- [ ] Unit tests for explanation content

---

### Story 3.5: Kill-Switch Configuration Management

**As a** system user,
**I want** to update kill-switch criteria via configuration files,
**So that** I can adjust non-negotiables without code changes.

**Acceptance Criteria:**

**Given** kill-switch criteria are defined in CSV
**When** the configuration is loaded
**Then** all criteria are parsed with: name, type (HARD/SOFT), threshold, severity, description
**And** invalid configurations are rejected with clear error messages
**And** changes are applied without restart (hot-reload in dev mode)

**Given** a new criterion is added to CSV
**When** the system reloads
**Then** the new criterion is evaluated for all properties
**And** existing data is not affected (non-destructive)

**Given** a criterion threshold is changed
**When** re-evaluation runs
**Then** all properties are re-evaluated with new threshold
**And** verdict changes are logged
**And** score deltas are tracked

**Prerequisites:** E1.S1, E3.S3

**Technical Notes:**
- Configuration file: `config/kill_switch.csv`
- CSV columns: name, type, operator, threshold, severity, description
- Operators: ==, !=, >=, <=, >, <, in, not_in
- Validation: Pydantic model for criterion definition
- Hot-reload: watch file changes in dev mode

**Definition of Done:**
- [ ] CSV parsing and validation
- [ ] Criterion model with operators
- [ ] Hot-reload capability
- [ ] Re-evaluation on config change
- [ ] Unit tests for configuration parsing

---

## Epic 4: Property Scoring Engine

**User Value:** Rank properties by comprehensive quality score (605 points across Location, Systems, Interior) with transparent breakdowns and tier classification.

**PRD Coverage:** FR15-20, FR25, FR27, FR48
**Architecture References:** ADR-03 (605-Point Scoring System), Scoring System Architecture

---

### Story 4.1: Three-Dimension Score Calculation

**As a** system user,
**I want** property scores calculated across three dimensions,
**So that** I can see balanced quality assessment.

**Acceptance Criteria:**

**Given** a property with complete data
**When** scoring is calculated
**Then** Section A (Location & Environment) is scored out of 250 points
**And** Section B (Lot & Systems) is scored out of 175 points
**And** Section C (Interior & Features) is scored out of 180 points
**And** total score is the sum of all sections (max 605)

**Given** a property with partial data
**When** scoring is calculated
**Then** missing data results in 0 points for that strategy (not penalty)
**And** confidence level reflects data completeness
**And** warning indicates which data is missing

**Given** scoring is complete
**When** storing the result
**Then** breakdown includes section subtotals
**And** breakdown includes percentage of max
**And** scored_at timestamp is recorded

**Prerequisites:** E1.S2, E2.S7

**Technical Notes:**
- Implement `PropertyScorer` in `src/phx_home_analysis/services/scoring/`
- Use `ScoringWeights` dataclass from `src/phx_home_analysis/config/scoring_weights.py`
- Total: 250 + 175 + 180 = 605 pts (Architecture authoritative)
- Store in `scoring` section of property record

**Definition of Done:**
- [ ] PropertyScorer with section calculation
- [ ] ScoreBreakdown dataclass
- [ ] Partial data handling
- [ ] Unit tests for scoring calculation
- [ ] Integration with data layer

---

### Story 4.2: 22-Strategy Scoring Implementation

**As a** system user,
**I want** 22 scoring strategies with configurable weights,
**So that** I have comprehensive quality assessment.

**Acceptance Criteria:**

**Given** Section A (Location - 250 pts)
**When** strategies are applied
**Then** school_district (42 pts): GreatSchools rating x 4.2
**And** quietness (30 pts): Distance to highways
**And** crime_index (47 pts): Weighted crime score
**And** supermarket (23 pts): Distance to grocery
**And** parks_walkability (23 pts): Parks and sidewalks
**And** sun_orientation (25 pts): N=25, E=18.75, S=12.5, W=0
**And** flood_risk (23 pts): FEMA zone scoring
**And** walk_transit (22 pts): Walk/Transit/Bike scores
**And** air_quality (15 pts): AQI scoring

**Given** Section B (Systems - 175 pts)
**When** strategies are applied
**Then** roof_condition (45 pts): Age-based scoring
**And** backyard_utility (35 pts): Usable sqft
**And** plumbing_electrical (35 pts): Year-based scoring
**And** pool_condition (20 pts): Equipment age
**And** cost_efficiency (35 pts): Monthly cost scoring
**And** solar_status (5 pts): Owned/Loan/None/Leased

**Given** Section C (Interior - 180 pts)
**When** strategies are applied
**Then** kitchen_layout (40 pts): Visual assessment
**And** master_suite (35 pts): Visual assessment
**And** natural_light (30 pts): Visual assessment
**And** high_ceilings (25 pts): Height scoring
**And** fireplace (20 pts): Type scoring
**And** laundry_area (20 pts): Location scoring
**And** aesthetics (10 pts): Visual assessment

**Prerequisites:** E4.S1

**Technical Notes:**
- Implement each strategy as separate class in `src/phx_home_analysis/services/scoring/strategies/`
- Strategy base class with `score(property: Property) -> float` returning 0-10 scale
- Scale by weight: `raw_score * (weight / 10)` = weighted points
- Arizona context: HVAC lifespan 10-15 years, pool costs $250-400/month

**Definition of Done:**
- [ ] 22 strategy classes implemented
- [ ] Weight configuration from scoring_weights.yaml
- [ ] 0-10 raw scale with weight scaling
- [ ] Arizona-specific factors applied
- [ ] Unit tests for each strategy

---

### Story 4.3: Tier Classification System

**As a** system user,
**I want** properties classified into tiers,
**So that** I can quickly identify the best options.

**Acceptance Criteria:**

**Given** a property score is calculated
**When** tier classification runs
**Then** score > 484 (80% of 605) = UNICORN tier
**And** score 363-484 (60-80% of 605) = CONTENDER tier
**And** score < 363 (<60% of 605) = PASS tier

**Given** tier is assigned
**When** displaying in deal sheet
**Then** UNICORN shows 🦄 emoji with green badge
**And** CONTENDER shows 🥊 emoji with amber badge
**And** PASS shows ⏭️ emoji with gray badge

**Given** tier thresholds need adjustment
**When** configuration is updated
**Then** new thresholds are applied
**And** all properties are re-classified
**And** tier changes are logged

**Prerequisites:** E4.S1

**Technical Notes:**
- Implement `TierClassifier` in `src/phx_home_analysis/services/scoring/`
- Thresholds from Architecture: 484 (80%), 363 (60%) of 605
- Tier enum: UNICORN, CONTENDER, PASS
- Badge colors from UX spec: green, amber, gray
- Store tier in `scoring.tier` field

**Definition of Done:**
- [ ] TierClassifier with threshold logic
- [ ] Tier enum with display formatting
- [ ] Badge emoji and color mapping
- [ ] Configurable thresholds
- [ ] Unit tests for tier boundaries

---

### Story 4.4: Score Breakdown Generation

**As a** system user,
**I want** detailed score breakdowns,
**So that** I can see exactly how points were earned.

**Acceptance Criteria:**

**Given** scoring is complete
**When** generating breakdown
**Then** each section shows points earned / max possible
**And** each strategy within section shows points earned / weight
**And** strategies are ordered by impact (highest first)

**Given** breakdown is displayed
**When** viewing in deal sheet
**Then** sections use Score Gauge component (progress bar)
**And** strategies are expandable via Collapsible Details
**And** source data is shown for each strategy

**Given** user wants to understand a score
**When** drilling into a strategy
**Then** raw input data is shown
**And** calculation logic is explained
**And** confidence level is displayed

**Prerequisites:** E4.S2, E4.S3

**Technical Notes:**
- Implement `ScoreBreakdownGenerator` in `src/phx_home_analysis/services/scoring/`
- Return structure: sections[] -> strategies[] -> { points, max, source_data, calculation }
- Integration with Score Gauge and Collapsible Details from UX spec
- Format for both JSON (data) and HTML (display)

**Definition of Done:**
- [ ] Breakdown generation at strategy level
- [ ] Impact-ordered display
- [ ] Source data linkage
- [ ] HTML formatting for deal sheets
- [ ] Unit tests for breakdown structure

---

### Story 4.5: Scoring Weight Adjustment and Re-Scoring

**As a** system user,
**I want** to adjust scoring weights and re-score without re-analysis,
**So that** I can explore different priorities quickly.

**Acceptance Criteria:**

**Given** scoring weights are in YAML configuration
**When** weights are modified
**Then** total of all weights still equals 605 (validation)
**And** section totals are recalculated
**And** changes are logged with before/after

**Given** weights are changed
**When** re-scoring runs
**Then** all properties are re-scored with new weights
**And** no new data fetching occurs (uses cached data)
**And** processing completes in < 5 minutes for 100 properties

**Given** a property's score changes
**When** comparing old vs new
**Then** delta is calculated per section
**And** tier changes are highlighted
**And** re-ranking is generated

**Prerequisites:** E4.S4

**Technical Notes:**
- Implement `RescoringService` in `src/phx_home_analysis/services/scoring/`
- Validation: sum of weights must equal 605
- Load existing enrichment data (no new API calls)
- Performance: in-memory scoring, batch JSON write
- CLI: `python scripts/phx_home_analyzer.py --rescore`

**Definition of Done:**
- [ ] Weight validation (total = 605)
- [ ] Re-scoring from cached data
- [ ] Performance < 5 min for 100 properties
- [ ] Delta calculation
- [ ] CLI command for re-scoring

---

### Story 4.6: Score Delta Tracking

**As a** system user,
**I want** to see score changes when priorities shift,
**So that** I can understand the impact of my changes.

**Acceptance Criteria:**

**Given** re-scoring has occurred
**When** viewing delta report
**Then** each property shows old score, new score, and delta
**And** tier changes are highlighted (e.g., "Contender → Unicorn")
**And** properties are sorted by absolute delta (biggest changes first)

**Given** section-level deltas are needed
**When** drilling into a property
**Then** delta is shown for each of 3 sections
**And** delta is shown for each strategy
**And** largest contributors to change are identified

**Given** delta report is generated
**When** displaying in deal sheet
**Then** old/new scores are shown side-by-side
**And** changes use green (+) / red (-) coloring
**And** tier change uses arrow notation (🥊 → 🦄)

**Prerequisites:** E4.S5

**Technical Notes:**
- Implement `ScoreDeltaTracker` in `src/phx_home_analysis/services/scoring/`
- Store previous scores in `scoring.previous` before overwrite
- Delta calculation: new - old (positive = improvement)
- Report format: CSV and JSON outputs
- Integration with deal sheet comparison view

**Definition of Done:**
- [ ] Previous score preservation
- [ ] Multi-level delta calculation
- [ ] Tier change detection
- [ ] Report generation (CSV, JSON)
- [ ] Deal sheet integration

---

## Epic 5: Multi-Agent Pipeline Orchestration

**User Value:** Coordinate automated multi-phase property analysis using specialized Claude agents with appropriate model selection, parallel execution, and reliable state management.

**PRD Coverage:** FR28-33
**Architecture References:** Multi-Agent Architecture, Phase Dependencies

---

### Story 5.1: Pipeline Orchestrator CLI

**As a** system user,
**I want** to execute the complete pipeline via single CLI command,
**So that** I can analyze properties without manual phase coordination.

**Acceptance Criteria:**

**Given** the `/analyze-property` command is invoked
**When** running with `--all` flag
**Then** all properties in CSV are processed through all phases
**And** progress is displayed with phase and property indicators
**And** ETA is updated based on actual phase durations

**Given** the command is invoked with a specific address
**When** running `/analyze-property "123 Main St"`
**Then** only that property is processed
**And** existing data for that property is overwritten
**And** completion status is displayed

**Given** pipeline status is queried
**When** running with `--status` flag
**Then** current phase is displayed
**And** property counts by status are shown (completed, in_progress, pending, failed)
**And** time elapsed and ETA are shown

**Prerequisites:** E1.S4, E1.S5

**Technical Notes:**
- Implement in `.claude/commands/analyze-property.md`
- Orchestrator in `src/phx_home_analysis/pipeline/orchestrator.py`
- Status display using `rich` library tables
- Flags: `--all`, `--test`, `--resume`, `--status`, `--strict`, `--skip-phase=N`

**Definition of Done:**
- [ ] analyze-property slash command
- [ ] Orchestrator with phase management
- [ ] Progress display with ETA
- [ ] Status query capability
- [ ] Unit tests for orchestrator logic

---

### Story 5.2: Sequential Phase Coordination

**As a** system user,
**I want** phases to execute in proper sequence,
**So that** each phase has the data it needs from previous phases.

**Acceptance Criteria:**

**Given** the pipeline starts
**When** executing phases
**Then** Phase 0 (County Assessor) runs first for all properties
**And** Phase 1 (Listing + Map) runs after Phase 0 completes
**And** Phase 2 (Images) runs after Phase 1 completes
**And** Phase 3 (Synthesis) runs after Phase 2 completes

**Given** a phase fails for a property
**When** the pipeline continues
**Then** that property is marked as "failed" for that phase
**And** subsequent phases are skipped for that property
**And** other properties continue processing

**Given** a phase is skipped via `--skip-phase`
**When** the pipeline runs
**Then** that phase is not executed
**And** dependencies are still validated
**And** warning is shown if data will be incomplete

**Prerequisites:** E5.S1

**Technical Notes:**
- Phase sequence: 0 → 1a+1b (parallel) → 2 → 3 → 4
- Implement `PhaseCoordinator` in `src/phx_home_analysis/pipeline/`
- Each phase is independently executable for testing
- Skip capability for debugging/partial runs

**Definition of Done:**
- [ ] PhaseCoordinator with sequence logic
- [ ] Per-property phase tracking
- [ ] Failure handling without full abort
- [ ] Skip capability with warnings
- [ ] Integration test for full sequence

---

### Story 5.3: Agent Spawning with Model Selection

**As a** system user,
**I want** specialized agents spawned with appropriate Claude models,
**So that** I get optimal cost-capability balance.

**Acceptance Criteria:**

**Given** Phase 1 needs agents
**When** spawning listing-browser
**Then** Claude Haiku model is selected (fast, cost-effective)
**And** skills are loaded: listing-extraction, property-data, state-management, kill-switch

**Given** Phase 1 needs agents
**When** spawning map-analyzer
**Then** Claude Haiku model is selected
**And** skills are loaded: map-analysis, property-data, state-management, arizona-context, scoring

**Given** Phase 2 needs agents
**When** spawning image-assessor
**Then** Claude Sonnet model is selected (multi-modal vision required)
**And** skills are loaded: image-assessment, property-data, state-management, arizona-context-lite, scoring

**Given** an agent spawn fails
**When** error is detected
**Then** failure is logged with error details
**And** property is marked as failed for that phase
**And** retry is not automatic (user must resume)

**Prerequisites:** E5.S2

**Technical Notes:**
- Agent definitions in `.claude/agents/listing-browser.md`, `map-analyzer.md`, `image-assessor.md`
- Model selection per Architecture: Haiku for data, Sonnet for vision
- Spawn via Claude Code CLI or Task tool
- Skills loaded via frontmatter in agent files

**Definition of Done:**
- [ ] Agent definition files with model selection
- [ ] Skill loading validation
- [ ] Spawn error handling
- [ ] Cost tracking per model
- [ ] Integration test for agent spawning

---

### Story 5.4: Phase Prerequisite Validation

**As a** system user,
**I want** mandatory prerequisite validation before agent spawning,
**So that** agents have the data they need to succeed.

**Acceptance Criteria:**

**Given** Phase 2 is about to start
**When** prerequisite validation runs
**Then** script `validate_phase_prerequisites.py` is executed
**And** exit code 0 = can_spawn true, proceed
**And** exit code 1 = can_spawn false, BLOCK

**Given** prerequisites fail
**When** validation returns
**Then** missing data is listed (e.g., "images not downloaded")
**And** reasons are explained
**And** agent is NOT spawned
**And** user is prompted to fix issues

**Given** validation passes
**When** agent is spawned
**Then** all required data is confirmed present
**And** spawn proceeds normally
**And** validation result is logged

**Prerequisites:** E5.S3

**Technical Notes:**
- Implement `scripts/validate_phase_prerequisites.py`
- Output JSON: `{"can_spawn": bool, "missing_data": [], "reasons": []}`
- Phase 2 requires: images downloaded, Phase 1 complete
- Phase 3 requires: Phase 2 complete for all properties
- MANDATORY: Never spawn Phase 2 without validation passing

**Definition of Done:**
- [ ] Prerequisite validation script
- [ ] JSON output format
- [ ] Phase-specific requirements
- [ ] Blocking behavior on failure
- [ ] Integration test for validation

---

### Story 5.5: Parallel Phase 1 Execution

**As a** system user,
**I want** Phase 1 sub-tasks to run in parallel,
**So that** listing and map analysis happen concurrently.

**Acceptance Criteria:**

**Given** Phase 1 starts
**When** agents are spawned
**Then** listing-browser and map-analyzer run in parallel
**And** both share access to work_items.json (atomic writes)
**And** completion is tracked independently

**Given** one Phase 1 agent completes before the other
**When** waiting for Phase 2
**Then** the phase waits for BOTH agents to complete
**And** progress shows completion status of each
**And** timeout warning after 10 minutes if one is stuck

**Given** one Phase 1 agent fails
**When** the other succeeds
**Then** partial data is preserved
**And** property is marked with partial Phase 1 status
**And** Phase 2 may proceed with warnings

**Prerequisites:** E5.S4

**Technical Notes:**
- Use async/await for parallel execution
- Atomic writes to work_items.json with file locking
- Phase 1a: listing-browser, Phase 1b: map-analyzer
- Coordination via shared state file, not message passing
- Timeout: 10 minutes per property

**Definition of Done:**
- [ ] Parallel agent spawning
- [ ] Completion synchronization
- [ ] Partial success handling
- [ ] Timeout detection
- [ ] Integration test for parallel execution

---

### Story 5.6: Multi-Agent Output Aggregation

**As a** system user,
**I want** multi-agent outputs aggregated into unified records,
**So that** all data is consolidated per property.

**Acceptance Criteria:**

**Given** multiple agents have written data for a property
**When** aggregation runs
**Then** county_data section comes from Phase 0
**And** listing_data section comes from listing-browser
**And** location_data section comes from map-analyzer
**And** image_assessment section comes from image-assessor

**Given** conflicting data exists (e.g., sqft from listing vs county)
**When** merging records
**Then** county data is preferred for: lot_sqft, year_built, garage_spaces
**And** listing data is preferred for: price, beds, baths, sqft
**And** conflict is logged with both values

**Given** aggregation completes
**When** writing to enrichment_data.json
**Then** atomic write with backup
**And** metadata.last_updated reflects aggregation time
**And** metadata.pipeline_version is recorded

**Prerequisites:** E5.S5

**Technical Notes:**
- Implement `DataAggregator` in `src/phx_home_analysis/pipeline/`
- Merge strategy per field documented in Architecture
- Conflict resolution: county > listing > image for physical attributes
- Provenance preserved: each section retains original source

**Definition of Done:**
- [ ] DataAggregator with merge logic
- [ ] Conflict resolution rules
- [ ] Provenance preservation
- [ ] Atomic write on aggregation
- [ ] Unit tests for merge scenarios

---

## Epic 6: Visual Analysis & Risk Intelligence

**User Value:** Assess property condition through image analysis and proactively surface hidden risks (foundation issues, HVAC age, solar leases) with Arizona-specific context.

**PRD Coverage:** FR21-24, FR26-27
**Architecture References:** image-assessor Agent, Section C Scoring, Risk Intelligence

---

### Story 6.1: Property Image Visual Assessment

**As a** system user,
**I want** visual assessment of property images,
**So that** interior and exterior condition is scored.

**Acceptance Criteria:**

**Given** property images are downloaded
**When** image-assessor agent runs
**Then** Section C scores are generated for: kitchen, master, natural_light, ceilings, fireplace, laundry, aesthetics
**And** each score is 0-10 scale
**And** scores are multiplied by weights from scoring_weights.yaml

**Given** an image shows kitchen
**When** visual assessment runs
**Then** evaluation considers: layout (open vs closed), island presence, appliance quality, pantry, counter space
**And** score reflects overall kitchen quality
**And** notes are captured for significant observations

**Given** insufficient images for a category
**When** scoring that category
**Then** score defaults to 5.0 (neutral)
**And** confidence is set to LOW
**And** warning indicates missing image data

**Prerequisites:** E2.S4, E5.S3

**Technical Notes:**
- image-assessor uses Claude Sonnet (vision model)
- Prompt engineering for consistent 0-10 scoring
- Store in `image_assessment` section with assessed_at timestamp
- Skills: image-assessment, arizona-context-lite
- ~$0.02 per image for API cost

**Definition of Done:**
- [ ] Image assessment prompts for each category
- [ ] 0-10 scoring with weight scaling
- [ ] Confidence levels based on image availability
- [ ] Notes capture for observations
- [ ] Integration with Section C scoring

---

### Story 6.2: Proactive Warning Generation

**As a** system user,
**I want** proactive warnings for hidden risks,
**So that** I'm informed before emotional investment.

**Acceptance Criteria:**

**Given** property data is complete
**When** warning analysis runs
**Then** warnings are generated for: HVAC age, roof condition, foundation concerns, solar leases, pool equipment age, orientation impact
**And** each warning has severity (High/Medium/Low)
**And** each warning has consequence description

**Given** a warning is generated
**When** displaying in deal sheet
**Then** format follows Warning Card component from UX spec
**And** color-coded border (red=high, amber=medium, gray=low)
**And** consequence is in plain language

**Given** warning precision is measured
**When** compared to inspection findings
**Then** precision >= 80% (<=20% false positive rate)
**And** warnings include recommended actions

**Prerequisites:** E4.S2, E6.S1

**Technical Notes:**
- Implement `WarningGenerator` in `src/phx_home_analysis/services/risk/`
- Warning types: HVAC_AGE, ROOF_CONDITION, FOUNDATION, SOLAR_LEASE, POOL_EQUIPMENT, ORIENTATION
- Severity thresholds from configuration
- Consequence templates in `config/warning_templates.yaml`

**Definition of Done:**
- [ ] WarningGenerator with risk detection
- [ ] Severity classification
- [ ] Consequence descriptions
- [ ] Warning Card formatting
- [ ] Unit tests for warning scenarios

---

### Story 6.3: Risk-to-Consequence Mapping

**As a** system user,
**I want** risks mapped to tangible consequences,
**So that** I understand the real impact.

**Acceptance Criteria:**

**Given** a risk is identified
**When** consequence mapping runs
**Then** dollar cost estimate is provided (min-max range)
**And** quality of life impact is described
**And** resale impact is assessed
**And** Arizona-specific adjustments are applied

**Given** HVAC age risk is identified
**When** consequence is generated
**Then** replacement cost: $7K-$12K
**And** timeline: based on age and AZ 10-15 year lifespan
**And** budget recommendation: reserve $X by year Y

**Given** solar lease risk is identified
**When** consequence is generated
**Then** liability estimate: $15K-$25K transfer cost
**And** financing impact: 60% of buyers can't get loans
**And** recommendation: negotiate lease buyout or walk

**Prerequisites:** E6.S2

**Technical Notes:**
- Implement `ConsequenceMapper` in `src/phx_home_analysis/services/risk/`
- Cost estimates from Arizona market research
- Template-based consequence generation
- Cost accuracy target: within ±30% of actual

**Definition of Done:**
- [ ] ConsequenceMapper with cost estimates
- [ ] Quality of life impact descriptions
- [ ] Resale impact assessments
- [ ] Arizona-specific cost calibration
- [ ] Validation against market data

---

### Story 6.4: Warning Confidence Levels

**As a** system user,
**I want** confidence levels on warnings,
**So that** I know how much to trust each alert.

**Acceptance Criteria:**

**Given** a warning is generated
**When** confidence is assigned
**Then** HIGH (90%+) for authoritative sources (county, FEMA)
**And** MEDIUM (70-90%) for listing/visual data
**And** LOW (<70%) for inferred data

**Given** data is older than 14 days
**When** confidence is calculated
**Then** confidence is automatically downgraded one level
**And** warning indicates data freshness concern

**Given** confidence is displayed
**When** viewing in deal sheet
**Then** badge shows HIGH/MEDIUM/LOW with color coding
**And** source is attributed
**And** fetch date is visible

**Prerequisites:** E6.S3

**Technical Notes:**
- Confidence calibration per Architecture: County=0.95, Maps=0.90, Schools=0.90, Listing=0.85, Image=0.80
- Age-based degradation: >14 days = -0.15, >30 days = -0.30
- Display: High=green, Medium=amber, Low=gray
- Source attribution always visible

**Definition of Done:**
- [ ] Confidence calculation logic
- [ ] Age-based degradation
- [ ] Source attribution
- [ ] Display formatting
- [ ] Unit tests for confidence scenarios

---

### Story 6.5: Foundation Issue Identification

**As a** system user,
**I want** potential foundation issues identified via visual analysis,
**So that** I can budget for inspections.

**Acceptance Criteria:**

**Given** exterior images are available
**When** foundation assessment runs
**Then** visual cracks are detected and classified (Minor/Moderate/Severe)
**And** crack patterns are analyzed (vertical, horizontal, stair-step)
**And** image references are included

**Given** foundation concern is identified
**When** warning is generated
**Then** severity classification is provided
**And** recommendation includes "Get structural engineer inspection"
**And** cost estimate for inspection ($300-$500) is included

**Given** assessment accuracy is measured
**When** compared to professional inspections
**Then** recall >= 90% (miss rate <= 10%)
**And** precision >= 60% (over-flagging acceptable)

**Prerequisites:** E6.S1

**Technical Notes:**
- Foundation assessment via image-assessor with specific prompts
- Crack classification: vertical (usually settling), horizontal (pressure), stair-step (foundation movement)
- Conservative approach: over-flag rather than under-flag
- Skills: image-assessment, arizona-context-lite

**Definition of Done:**
- [ ] Foundation crack detection prompts
- [ ] Severity classification
- [ ] Crack pattern analysis
- [ ] Inspection recommendations
- [ ] Validation against inspection reports

---

### Story 6.6: HVAC Replacement Timeline Estimation

**As a** system user,
**I want** HVAC replacement timeline estimates,
**So that** I can budget for near-term expenses.

**Acceptance Criteria:**

**Given** HVAC system age is known
**When** timeline estimation runs
**Then** categories are assigned: Immediate (>=13 yrs), Near-term (10-12 yrs), Mid-term (5-9 yrs), Long-term (<5 yrs)
**And** Arizona climate factor is applied (10-15 year lifespan vs 20+ nationally)
**And** replacement cost estimate: $7K-$12K

**Given** HVAC age is unknown
**When** estimation runs
**Then** year_built is used as proxy
**And** confidence is set to LOW
**And** warning recommends "Verify HVAC age during tour"

**Given** timeline is displayed
**When** viewing in deal sheet
**Then** budget recommendation is included
**And** timeline is visual (progress bar or icon)
**And** Arizona context is explained

**Prerequisites:** E6.S4

**Technical Notes:**
- HVAC lifespan in Phoenix: 10-15 years (per PRD and Architecture)
- National average: 15-20 years (not applicable in AZ)
- Cost calibration from local HVAC contractors
- Timeline accuracy target: ±2 years

**Definition of Done:**
- [ ] HVAC age-based timeline
- [ ] Arizona lifespan adjustment
- [ ] Cost estimation
- [ ] Proxy from year_built
- [ ] Visual timeline display

---

## Epic 7: Deal Sheet Generation & Reports

**User Value:** Produce actionable deal sheets with score breakdowns, tier badges, warnings, and tour checklists that enable confident property decisions in under 2 minutes.

**PRD Coverage:** FR40-45, FR52-57
**Architecture References:** Presentation Layer, UX Design Specification

---

### Story 7.1: Deal Sheet HTML Generation

**As a** system user,
**I want** comprehensive HTML deal sheets,
**So that** I can review properties on mobile during tours.

**Acceptance Criteria:**

**Given** property analysis is complete
**When** deal sheet is generated
**Then** HTML file is created at `docs/artifacts/deal_sheets/{address}.html`
**And** file is mobile-responsive (readable on 5-inch screen)
**And** file works offline (no external dependencies)

**Given** deal sheet is opened
**When** viewing on mobile
**Then** tier badge and verdict are visible above fold
**And** score summary is visible without scrolling
**And** top 3 warnings are visible
**And** full details are in collapsible sections

**Given** deal sheet needs regeneration
**When** running with `--regenerate` flag
**Then** existing deal sheets are overwritten
**And** new data is incorporated
**And** generation timestamp is updated

**Prerequisites:** E4.S4, E6.S2

**Technical Notes:**
- Use Jinja2 templating with Tailwind CSS (per UX spec)
- Templates in `docs/templates/`
- Components: Property Card, Tier Badge, Verdict Card, Score Gauge, Warning Card
- Offline: Tailwind via CDN in dev, compiled in production
- Mobile-first: single column default, expand on tablet/desktop

**Definition of Done:**
- [ ] Jinja2 templates for deal sheets
- [ ] Tailwind CSS integration
- [ ] Mobile-responsive layout
- [ ] Offline capability
- [ ] Unit tests for template rendering

---

### Story 7.2: Deal Sheet Content Structure

**As a** system user,
**I want** deal sheets with complete property intelligence,
**So that** I have all information needed for decisions.

**Acceptance Criteria:**

**Given** a deal sheet is generated
**When** reviewing content
**Then** header shows: address, price, tier badge, kill-switch verdict
**And** summary shows: 3-section score breakdown with gauges
**And** warnings show: up to 5 warnings with severity and consequences
**And** details show: complete data table with source attribution

**Given** the 2-minute scan UX goal
**When** structuring content
**Then** critical info (tier, verdict, warnings) is above fold
**And** progressive disclosure via `<details>` elements
**And** print stylesheet expands all sections

**Given** accessibility requirements
**When** generating HTML
**Then** semantic HTML structure (article, header, section)
**And** ARIA labels on badges and icons
**And** color + emoji + text redundancy
**And** 4.5:1 contrast ratio on text

**Prerequisites:** E7.S1

**Technical Notes:**
- Follow UX Design Specification for component patterns
- Property Card Container as main layout
- Collapsible Details for progressive disclosure
- Print CSS: expand all `<details>` automatically
- Accessibility: WCAG 2.1 Level AA target

**Definition of Done:**
- [ ] Complete content structure
- [ ] Progressive disclosure implementation
- [ ] Print stylesheet
- [ ] Accessibility compliance
- [ ] Manual review of generated output

---

### Story 7.3: Score Explanation Narratives

**As a** system user,
**I want** natural language score explanations,
**So that** I understand WHY properties scored as they did.

**Acceptance Criteria:**

**Given** a property score is generated
**When** explanation is requested
**Then** narrative describes key scoring factors
**And** language is plain (no technical jargon)
**And** comparisons are made ("This scored 487 vs average of 450")

**Given** section breakdown is explained
**When** narrative is generated
**Then** top 3 contributors are highlighted per section
**And** Arizona context is mentioned where relevant
**And** specific data points are cited

**Given** explanation length is managed
**When** generating narrative
**Then** summary is 2-3 sentences
**And** detail is expandable
**And** key insight is highlighted

**Prerequisites:** E7.S2

**Technical Notes:**
- Implement `NarrativeGenerator` in `src/phx_home_analysis/reporters/`
- Templates for each scoring dimension
- Comparative language: "above average", "top 10%", etc.
- GPT-style generation using Claude for natural language

**Definition of Done:**
- [ ] Narrative generation for each section
- [ ] Plain language output
- [ ] Comparative context
- [ ] Length management
- [ ] Unit tests for narrative quality

---

### Story 7.4: Visual Comparisons (Radar & Scatter)

**As a** system user,
**I want** visual comparison charts,
**So that** I can quickly compare multiple properties.

**Acceptance Criteria:**

**Given** multiple properties are analyzed
**When** radar chart is generated
**Then** each property shows 3-dimension polygon (Location, Systems, Interior)
**And** up to 5 properties can be overlaid
**And** legend identifies each property by address

**Given** batch analysis is complete
**When** Value Spotter scatter plot is generated
**Then** X-axis = price, Y-axis = total score
**And** properties are color-coded by tier
**And** "value" properties (high score, low price) are highlighted

**Given** visualizations are requested
**When** generating charts
**Then** output is SVG for scalability
**And** charts work in HTML deal sheets
**And** print-friendly (no interactive elements required)

**Prerequisites:** E4.S4

**Technical Notes:**
- Use Plotly for chart generation
- Radar chart: 3 dimensions with percentage scale
- Scatter plot: quadrants for value identification
- Output: SVG embedded in HTML
- Alternative: matplotlib for static images

**Definition of Done:**
- [ ] Radar chart generation
- [ ] Scatter plot generation
- [ ] Multi-property overlays
- [ ] SVG output for HTML embedding
- [ ] Print compatibility

---

### Story 7.5: Risk Checklists for Property Tours

**As a** system user,
**I want** property-specific tour checklists,
**So that** I know what to verify during physical visits.

**Acceptance Criteria:**

**Given** a property has warnings
**When** checklist is generated
**Then** each warning becomes a verification item
**And** items are prioritized by severity
**And** specific things to look for are listed

**Given** standard inspection items exist
**When** checklist is generated
**Then** standard items are included (HVAC unit, water heater, electrical panel, etc.)
**And** Arizona-specific items are included (pool equipment, solar panels, desert landscaping)
**And** items can be checked off during tour

**Given** checklist is printed
**When** viewing output
**Then** format is optimized for 8.5x11 paper
**And** checkboxes are present for each item
**And** space for notes is provided

**Prerequisites:** E6.S2

**Technical Notes:**
- Implement `ChecklistGenerator` in `src/phx_home_analysis/reporters/`
- Output: HTML + printable version
- Store in `docs/risk_checklists/{address}_checklist.txt`
- Include QR code linking to full deal sheet

**Definition of Done:**
- [ ] Checklist generation from warnings
- [ ] Standard inspection items
- [ ] Arizona-specific items
- [ ] Print-optimized format
- [ ] QR code integration

---

### Story 7.6: Deal Sheet Regeneration After Re-Scoring

**As a** system user,
**I want** deal sheets regenerated after re-scoring,
**So that** reports reflect updated priorities.

**Acceptance Criteria:**

**Given** re-scoring has occurred
**When** regeneration runs
**Then** all deal sheets are updated with new scores
**And** tier badges reflect new classifications
**And** generation timestamp is updated

**Given** score deltas exist
**When** regenerated deal sheet is viewed
**Then** old vs new scores are shown
**And** tier changes are highlighted
**And** change explanation is included

**Given** selective regeneration is needed
**When** running with `--address` flag
**Then** only specified property is regenerated
**And** other deal sheets are preserved
**And** progress indicates which file was updated

**Prerequisites:** E4.S6, E7.S1

**Technical Notes:**
- Implement regeneration in deal sheet generator
- Delta display: side-by-side scores, change indicators
- Selective: `python -m scripts.deal_sheets --address "123 Main St"`
- Batch: `python -m scripts.deal_sheets --all`

**Definition of Done:**
- [ ] Full batch regeneration
- [ ] Selective regeneration by address
- [ ] Delta display in regenerated sheets
- [ ] Timestamp management
- [ ] Integration test for regeneration

---

## Summary

### Epic Breakdown Statistics

| Metric | Value |
|--------|-------|
| Total Epics | 7 |
| Total Stories | 42 |
| P0 Stories | 35 |
| P1 Stories | 7 |
| FR Coverage | 62/62 (100%) |

### Recommended Sprint Sequence

**Sprint 1: Foundation**
- Epic 1: Foundation & Data Infrastructure (6 stories)
- Result: Reliable data storage, configuration, state management

**Sprint 2: Data Acquisition**
- Epic 2: Property Data Acquisition (7 stories)
- Result: Complete property data from all sources

**Sprint 3: Filtering & Scoring**
- Epic 3: Kill-Switch Filtering System (5 stories)
- Epic 4: Property Scoring Engine (6 stories)
- Result: Properties filtered and scored

**Sprint 4: Pipeline & Agents**
- Epic 5: Multi-Agent Pipeline Orchestration (6 stories)
- Result: Automated multi-phase analysis

**Sprint 5: Risk Intelligence**
- Epic 6: Visual Analysis & Risk Intelligence (6 stories)
- Result: Property condition assessment and warnings

**Sprint 6: Reports**
- Epic 7: Deal Sheet Generation & Reports (6 stories)
- Result: Actionable deal sheets for property tours

### Requirements That Could Not Be Mapped

**None.** All 62 functional requirements (FR1-FR62) are mapped to at least one story.

### Dependencies Summary

```
Epic 1 (Foundation) → All other epics
Epic 2 (Data) → Epic 3, 4, 5, 6
Epic 3 (Kill-Switch) → Epic 7 (deal sheets)
Epic 4 (Scoring) → Epic 7 (deal sheets)
Epic 5 (Pipeline) → Coordinates Epics 2, 6
Epic 6 (Risk) → Epic 7 (deal sheets)
Epic 7 (Reports) → End of pipeline
```

---

**Document Version:** 1.0
**Generated:** 2025-12-03
**Author:** PM Agent (John)
**Status:** Ready for Sprint Planning

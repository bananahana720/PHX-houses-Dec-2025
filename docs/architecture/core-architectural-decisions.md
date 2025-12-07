# Core Architectural Decisions

### ADR-01: Domain-Driven Design (DDD)

**Status:** Accepted

**Context:** System has complex domain logic (scoring, kill-switches, Arizona-specific factors) that must remain stable as infrastructure changes.

**Decision:** Implement DDD with clear layer separation:
- Domain Layer: Entities, value objects, enums
- Service Layer: Business logic orchestration
- Repository Layer: Data persistence abstraction
- Pipeline Layer: Workflow coordination
- Presentation Layer: Output formatting

**Consequences:**
- (+) Business logic testable in isolation
- (+) Infrastructure changes don't affect domain
- (+) Clear dependency direction (inward)
- (-) More boilerplate than simple approaches
- (-) Requires discipline to maintain boundaries

### ADR-02: JSON File Storage (Not Database)

**Status:** Accepted

**Context:** Personal tool with <1000 properties. Needs crash recovery without database complexity.

**Decision:** Use JSON files with atomic writes and backup-before-modify pattern.

**File Structure:**
- `data/phx_homes.csv` - Source listings (input)
- `data/enrichment_data.json` - Enriched property data (LIST of dicts)
- `data/work_items.json` - Pipeline state tracking
- `data/extraction_state.json` - Image extraction state

**Consequences:**
- (+) Simple, human-readable, git-diffable
- (+) No database setup or maintenance
- (+) Crash recovery via atomic writes
- (-) O(n) lookup by address (acceptable for <1000)
- (-) No concurrent write safety (single-user system)

### ADR-03: 605-Point Scoring System (Reconciliation)

**Status:** Accepted

**Context:** Discovered discrepancy between `scoring_weights.py` (605 pts) and `constants.py` (600 pts assertion).

**Analysis:**
```
ScoringWeights dataclass actual values:
- Section A: 42+30+47+23+23+25+23+22+15 = 250 pts
- Section B: 45+35+35+20+35+5 = 175 pts
- Section C: 40+35+30+25+20+20+10 = 180 pts
- TOTAL: 605 pts

constants.py assertion:
- Section A: 230, Section B: 180, Section C: 190 = 600 pts
```

**Decision:** `ScoringWeights` dataclass is authoritative. Total = **605 points**.

**Action Required:** Update `constants.py` assertion to match actual weights:
- `SCORE_SECTION_A_TOTAL = 250`
- `SCORE_SECTION_B_TOTAL = 175`
- `SCORE_SECTION_C_TOTAL = 180`
- `MAX_POSSIBLE_SCORE = 605`

**Tier Thresholds (updated):**
- Unicorn: >484 pts (80% of 605)
- Contender: 363-484 pts (60-80% of 605)
- Pass: <363 pts (<60% of 605)

### ADR-04: Kill-Switch Criteria Classification (5 HARD + 4 SOFT)

**Status:** Superseded (2025-12-07)

**Original Context:** PRD specified 8 non-negotiable criteria. Original decision was all HARD.

**Superseded By:** Buyer flexibility requirements led to severity accumulation system.

**Current Implementation:**

| Classification | Criteria | Behavior |
|----------------|----------|----------|
| **HARD** (5) | HOA=$0, Solar≠lease, Beds≥4, Baths≥2, Sqft>1800 | Instant FAIL |
| **SOFT** (4) | Sewer=city, Year≤2023, Garage≥2, Lot 7k-15k | Severity weighted |

**Severity System:**
- Sewer (septic): 2.5
- Year (>2023): 2.0
- Garage (<2): 1.5
- Lot (outside range): 1.0

**Verdict:** FAIL if any HARD fails OR severity ≥ 3.0

**Rationale:** Buyer can accept minor compromises (e.g., 1-car garage) but not combinations (e.g., septic + 1-car garage = 4.0 → FAIL).

**Consequences:**
- (+) More nuanced filtering than binary pass/fail
- (+) Allows acceptable properties that miss single SOFT criterion
- (+) Prevents properties with multiple deficiencies
- (-) Requires severity accumulation logic
- (-) May allow borderline properties at 2.5-3.0 threshold

**References:**
- Implementation: `src/phx_home_analysis/services/kill_switch/filter.py:92-142`
- Documentation: `docs/architecture/kill-switch-architecture.md`

### ADR-05: Multi-Agent Model Selection

**Status:** Accepted

**Context:** Need to balance cost efficiency with capability requirements.

**Decision:**

| Agent | Model | Justification |
|-------|-------|---------------|
| listing-browser | Claude Haiku | Fast, cheap, structured data extraction |
| map-analyzer | Claude Haiku | Geographic data doesn't need vision |
| image-assessor | Claude Sonnet | Requires multi-modal vision capability |

**Cost Analysis (per 100 properties):**
- Haiku: ~$0.25/1M tokens = $2-5/100 properties
- Sonnet: ~$3.00/1M tokens = $15-30/100 properties (vision)
- Total: ~$20-50/100 properties (within $90/month budget)

### ADR-06: Stealth Browser Strategy

**Status:** Accepted

**Context:** Zillow/Redfin use PerimeterX bot detection. Standard Playwright blocked.

**Decision:** Primary: `nodriver` (stealth Chrome). Fallback: `curl-cffi` (TLS fingerprinting).

**Stack:**
1. `nodriver` - Stealth browser automation, bypasses PerimeterX
2. `curl-cffi` - HTTP client with browser TLS fingerprints
3. `Playwright` - Fallback for less aggressive sites (Realtor.com)

**Maintenance:** Weekly monitoring for anti-bot detection updates.

### ADR-07: Testing Framework & Infrastructure

**Status:** Accepted

**Context:** PHX Houses pipeline requires comprehensive testing to validate complex domain logic (kill-switches, scoring, multi-agent orchestration), ensure data integrity across pipeline phases, and support crash recovery mechanisms. With 2,636 tests (2,596 active, 40 deselected) across unit, integration, and service layers, the testing framework must balance speed, isolation, and realistic workflow validation while supporting both synchronous and asynchronous code patterns.

**Decision:** Implement pytest-based testing framework with fixture-driven dependency injection, boundary-focused validation, and protocol mocking:

**Testing Stack:**
- **Framework:** pytest 9.0.1 with asyncio support (pytest-asyncio 1.3.0)
- **HTTP Mocking:** httpx + respx 0.22.0 for async-compatible API testing
- **Coverage:** pytest-cov 7.0.0 targeting ~90% for new code, >95% for domain/kill-switches
- **Total Tests:** 2,636 tests (2,596 active, 40 deselected; unit: 1,800+, integration: 19, services: 87)
- **Execution Time:** Collection ~1.8s, full execution ~4-5s

**Test Organization:**
```
tests/
├── conftest.py              # Shared fixtures (property, enrichment, config)
├── unit/                    # Isolated component tests
│   ├── domain/             # Entities, value objects, enums
│   ├── services/           # Business logic (scoring, kill-switch, image extraction)
│   └── repositories/       # Data access patterns
└── integration/            # Multi-component workflows
    └── conftest.py         # Integration-specific fixtures (browser mocks, HTTP stubs)
```

**Core Testing Patterns:**

1. **Fixture-Based Dependency Injection** - Use pytest fixtures instead of manual mocking:
   ```python
   @pytest.fixture
   def sample_property():
       return Property(street="123 Main", beds=4, hoa_fee=0, ...)

   def test_kill_switch(sample_property):
       assert NoHoaKillSwitch().check(sample_property) is True
   ```

2. **Boundary Testing** - Validate exact thresholds for kill-switches and scoring:
   - Lot size: 6,999 sqft (fail) vs 7,000 sqft (pass)
   - Bathrooms: 1.9 (fail) vs 2.0 (pass)
   - Year: 2023 (pass) vs 2024 (fail)
   - HOA: $0 (pass) vs $1 (fail)

3. **Protocol Mocking** - Mock interfaces/protocols, not concrete classes:
   - Mock `AsyncMock()` for browser automation (nodriver Tab)
   - Use `respx.mock` for HTTP responses (not manual httpx stubs)
   - Mock external APIs (County Assessor, Google Maps), not internal domain logic

4. **Test Isolation** - Each test manages own state:
   - Use `tmp_path` fixture for file operations (no shared state)
   - Integration tests create separate work_items.json per test
   - Fixtures are function-scoped (default), not session-scoped

5. **Async Testing** - Support async/await with pytest-asyncio:
   ```python
   @pytest.mark.asyncio
   @respx.mock
   async def test_http_call():
       respx.get("https://api.test.com").mock(return_value=httpx.Response(200, json={...}))
       async with client:
           result = await client.get("/endpoint")
   ```
   **Note:** Ensure consistent `@pytest.mark.asyncio` marker usage to avoid event loop conflicts

**Anti-Patterns to Avoid:**
- ❌ Mocking internal methods (test at service boundaries only)
- ❌ Test interdependencies (each test must be independently runnable)
- ❌ Hardcoded test data (use fixtures for consistency)
- ❌ Floating-point equality (`score == 37.5` → use `abs(score - 37.5) < 0.01`)
- ❌ Testing implementation details (focus on public contracts)

**CI/CD Gates (must pass before merge):**
- Lint and format: `ruff check` + `ruff format`
- Type-checking: `mypy src/`
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- Security scan: `pip-audit --strict`

**Consequences:**
- (+) Fixture-driven DI ensures test consistency and reduces duplication
- (+) Boundary testing catches off-by-one errors in kill-switch thresholds
- (+) Protocol mocking enables fast unit tests without external dependencies
- (+) httpx + respx provides async-compatible HTTP mocking for modern Python
- (+) Test isolation prevents cascading failures and flaky tests
- (-) Large test suite requires ~4-5s execution time (acceptable for CI/CD)
- (-) Async tests require careful fixture scoping to avoid event loop conflicts
- (-) pytest-asyncio adds complexity compared to synchronous-only tests

**See also:** ADR-08 (Package Organization references DDD testing patterns)

### ADR-08: Package Organization & Domain-Driven Design

**Status:** Accepted

**Context:** The PHX Houses pipeline has grown to 120+ Python modules across multiple domains (scoring, kill-switch, image extraction, data persistence). Without clear package organization and dependency rules, the codebase risks becoming a tightly-coupled monolith with circular imports, duplicated logic, and business rules leaking into infrastructure layers. The system needs explicit layer boundaries that enforce dependency direction (inward toward domain) while supporting independent testing, refactoring, and future agent-based extensions.

**Decision:** Implement strict layered architecture with domain-driven design (DDD) principles:

**Layer Structure (dependency flows inward):**
```
presentation/ ──┐
pipeline/       │
repositories/   ├──> services/ ──> domain/ (core)
utils/          │
config/        ──┘
```

**Package Organization:**
- `domain/` - Pure business logic with zero external dependencies
  - `entities.py` - Property, EnrichmentData (160+ fields), FieldProvenance
  - `value_objects.py` - Address, Score, ScoreBreakdown (605-point), RiskAssessment
  - `enums.py` - Tier, Orientation, SolarStatus, SewerType, RiskLevel, PhaseStatus
  - NO imports from services, repositories, or pipeline layers

- `services/` - Business logic orchestration (depends on domain only)
  - `scoring/` - PropertyScorer, 19 scoring strategies total (17 active: 9 Location, 6 Systems, 7 Interior; 2 deprecated)
  - `kill_switch/` - KillSwitchFilter, 7 HARD criteria implementations
  - `image_extraction/` - ImageExtractor, deduplicator, state tracking
  - `quality/` - Provenance tracking, confidence metrics
  - Each service imports from `domain/` but never from `repositories/` or `pipeline/`

- `repositories/` - Data persistence abstraction (depends on domain)
  - `base.py` - PropertyRepository, EnrichmentRepository interfaces
  - `csv_repository.py` - CsvPropertyRepository (50 fields)
  - `json_repository.py` - JsonEnrichmentRepository (120+ fields, atomic writes)
  - `work_items_repository.py` - Pipeline state, job queue, retry tracking

- `pipeline/` - Workflow coordination (depends on services + domain)
  - `phase_coordinator.py` - Multi-phase orchestration, batch checkpointing
  - `orchestrator.py` - AnalysisPipeline (load → filter → score → report)
  - `resume.py` - Crash recovery, stale item reset

- `presentation/` - Output formatting (depends on domain)
  - `reporters/` - ConsoleReporter, HtmlReporter
  - `visualizations/` - Radar charts, scatter plots

**Naming Conventions:**
- Services: `*Service`, `*Scorer`, `*Filter` suffixes (e.g., `PropertyScorer`, `KillSwitchFilter`)
- Repositories: `*Repository` suffix (e.g., `JsonEnrichmentRepository`)
- Entities: Descriptive names without suffix (e.g., `Property`, `EnrichmentData`)
- Value Objects: Descriptive names (e.g., `Address`, `Score`, `ScoreBreakdown`)
- Enums: `*Type`, `*Status`, `*Level` suffixes (e.g., `SewerType`, `PhaseStatus`, `RiskLevel`)

**Import Rules (enforced):**
1. **Domain layer**: NO imports from services, repositories, pipeline, or presentation
2. **Services layer**: May import from `domain/` and `config/` ONLY
3. **Repositories layer**: May import from `domain/`, `validation/`, `config/` ONLY
4. **Pipeline layer**: May import from `services/`, `repositories/`, `domain/`, `config/`
5. **Presentation layer**: May import from `domain/`, `config/` ONLY
6. **Circular imports**: PROHIBITED at all layers
7. **Cross-service imports**: DISCOURAGED (use pipeline layer for orchestration)

**Consequences:**
- (+) Business logic isolated in domain layer, fully testable without infrastructure
- (+) Clear dependency direction prevents circular imports and coupling
- (+) Services can be tested with mock repositories (dependency injection)
- (+) Infrastructure changes (CSV → database) don't affect domain or services
- (+) Multi-agent pipeline can compose services without duplicating logic
- (-) Requires discipline to maintain boundaries (prevented via code review)
- (-) More verbose imports (`from ...domain.entities import Property`)
- (-) Cannot directly call repository methods from services (must inject via constructor)

**Note:** Consider `import-linter` for automated boundary enforcement in CI/CD

**See also:** ADR-07 (Testing references DDD patterns)

### ADR-09: Software Architecture Patterns

**Status:** Accepted

**Context:** The PHX Houses pipeline requires a maintainable, testable, and extensible architecture for evaluating properties across multiple phases (county data, listing extraction, image assessment, scoring, reporting). The system must support crash recovery, batch processing, multi-agent coordination, and domain-driven separation of concerns.

**Decision:** Implement the following software architecture patterns:

**1. Repository Pattern**
- Abstract base classes define contracts (`PropertyRepository`, `EnrichmentRepository`)
- Concrete implementations handle persistence (`JsonEnrichmentRepository`, `CsvPropertyRepository`)
- Enables testing with mock repositories without infrastructure dependencies

**2. Strategy Pattern for Scorers**
- Abstract `ScoringStrategy` base class defines interface (`name`, `category`, `weight`, `calculate_base_score`)
- 19 total strategies (17 active, 2 deprecated): Location (9), Systems (6), Interior (7)
  - **Deprecated:** `QuietnessScorer` (replaced by `NoiseLevelScorer`), `SafetyScorer` (replaced by `CrimeIndexScorer`)
  - **Note:** Deprecated strategies scheduled for removal in next major version after full data migration
- Strategies composed via `ALL_STRATEGIES` registry
- Dynamic scoring via `PropertyScorer` orchestrator applies all registered strategies

**3. Protocol-Based Dependency Injection**
- `Protocol` classes define interfaces (e.g., `AssessorClientProtocol`, `LineageTrackerProtocol`)
- Runtime-checkable protocols via `@runtime_checkable` decorator
- Implementations injected via constructor parameters or pytest fixtures
- Enables loose coupling and easy mocking for unit tests

**4. Pipeline Pattern for Workflows**
- Multi-stage workflows with clear phase boundaries (Phase 0-4)
- `PhaseCoordinator` manages phase sequencing, batch execution, checkpointing
- `ResumePipeline` provides crash recovery via state validation and stale item reset
- Work items tracked in `work_items.json` with atomic writes

**5. Error Handling Strategy**
- Custom exception hierarchy with base exceptions (`TransientError`, `PermanentError`, `DataLoadError`, `DataSaveError`)
- Error classification via `is_transient_error()` function
- HTTP status codes classified: 5xx + 429 = transient (retry), 4xx = permanent (fail)
- Fail-fast philosophy with clear, actionable error messages
- All errors logged; no silent failures

**6. Async Patterns with Retry Logic**
- `async def` for all I/O-bound operations (HTTP requests, file I/O, browser automation)
- `@retry_with_backoff` decorator for async functions with exponential backoff
- Configurable retry parameters: `max_retries=5`, `min_delay=1.0s`, `max_delay=60.0s`, `jitter=0.5`
- Jitter prevents thundering herd during concurrent retries

**7. Configuration Management**
- YAML-based configuration (`config/scoring_weights.yaml`, `config/buyer_criteria.yaml`)
- Pydantic-based dataclasses for validation (`AppConfig`, `BuyerProfile`, `ScoringWeights`)
- Environment variable overrides via `.env` file
- No hardcoded values in code; all configuration externalized

**8. Composition Over Inheritance**
- Prefer composition for behavior reuse (e.g., `PropertyScorer` composes multiple `ScoringStrategy` instances)
- Use `Protocol` classes for interface definitions instead of abstract base classes where appropriate
- Avoid deep inheritance hierarchies (max depth: 2 levels)
- Dataclasses with `@dataclass` decorator for immutable data structures

**Consequences:**
- (+) Business logic testable in isolation via dependency injection
- (+) Infrastructure changes don't affect domain layer
- (+) Extensible: new strategies/extractors added via registration pattern
- (+) Clear separation of concerns improves maintainability
- (+) Crash recovery enables long-running batch processes
- (+) Transient error handling reduces false failures
- (-) More boilerplate than simple procedural approaches
- (-) Requires discipline to maintain architectural boundaries
- (-) Learning curve for developers unfamiliar with DDD patterns

### ADR-10: Pipeline & Orchestration Patterns

**Status:** Accepted

**Context:** Multi-phase property analysis pipeline requires coordinated execution across 5 distinct phases (County API → Listing/Map → Images → Synthesis → Reports) with crash recovery, state persistence, and multi-agent coordination. Need to balance throughput, cost (Haiku vs Opus model selection), and reliability across 100+ properties while handling transient failures (rate limits, bot detection, API errors) and maintaining data consistency.

**Decision:** Implement hierarchical orchestration with three levels:

**1. Top-Level Pipeline** (`AnalysisPipeline`): Batch orchestration for all properties
- 8-stage linear workflow: load CSV → load enrichment → merge → kill-switch → score → classify → sort → save
- Atomic JSON saves with backup-before-modify pattern
- CachedDataManager for efficient enrichment data access
- Synchronous execution with explicit checkpointing

**2. Phase Coordinator** (`PhaseCoordinator`): Per-property multi-phase state machine
- **Phase enumeration:**
  ```python
  class Phase(IntEnum):
      COUNTY = 0
      LISTING = 1  # Parallel with MAP
      MAP = 1      # Parallel with LISTING
      IMAGES = 2
      SYNTHESIS = 3
      REPORT = 4
  ```
- Phase sequence: 0(County) → 1a(Listing)||1b(Map) → 2(Images) → 3(Synthesis) → 4(Reports)
- State tracking via `work_items.json` with fields: `status`, `current_phase`, `phase_status`, `retry_count`, `error_message`, `updated_at`
- Parallel phase support: Phase 1a and 1b execute concurrently (both value=1)
- MAX_RETRIES=3 per phase with exponential backoff
- Prerequisite validation before spawning dependent phases (Phase 2 requires Phase 1 complete + images downloaded)

**3. Service Orchestrators**: Domain-specific coordination
- `LocationDataOrchestrator`: Coordinates 9 location data sources (crime, schools, walkscore, flood, etc.) with per-source and per-ZIP state tracking
- `ImageExtractionOrchestrator`: Multi-source image extraction (PhoenixMLS → Zillow → Redfin fallback)
  - **Circuit breaker:** Planned implementation (3 failures → 5min timeout, currently partial)
- Sequential execution to avoid browser concurrency issues

**State Management Strategy:**
- **Primary state files (10+ including backups):**
  - `enrichment_data.json`: Master property data (LIST format), atomic writes
  - `work_items.json`: Pipeline progress tracking (per-property, per-phase status)
  - `extraction_state.json`: Image extraction state (completed/failed properties, last checked timestamp)
  - `address_folder_lookup.json`: Address → content-addressed folder mapping
  - `url_tracker.json`: URL-level tracking for incremental extraction
  - `image_manifest.json`: Image metadata and lineage
  - `hash_index.json`: Content hash deduplication index
  - `pipeline_runs.json`: Run history and metadata
  - Plus backup files (.backup.json, dated backups) for crash recovery

**Error Recovery Patterns:**
- **Transient errors** (5xx, 429, network): Exponential backoff with jitter (1s min, 60s max, 0.5 jitter factor)
- **Source fallback**: PhoenixMLS → Zillow → Redfin (automatic failover on SourceUnavailableError)
- **Circuit breaker**: 3 consecutive failures → disable source for 5min → half-open test → resume
- **Checkpoint/Resume**: Load work_items.json on startup, reset items stale >30min to in_progress
- **Per-property isolation**: One property failure does not block batch

**Model Tier Selection:**
- **Haiku 4.5**: Fast extraction tasks (listing-browser, map-analyzer) - ~$0.25/1M tokens
- **Opus 4.5**: Vision/assessment tasks (image-assessor) - ~$3.00/1M tokens
- Cost optimization: $20-50/100 properties (within $90/month budget)

**Multi-Agent Handoff:**
- Agents return structured data; orchestrator updates `enrichment_data.json`
- Agents read-only for state files; orchestrator owns writes (prevents race conditions)
- Prerequisite validation script gates Phase 2 spawning

**Consequences:**
- (+) Crash recovery via persistent state enables resume after failures
- (+) Per-property error isolation prevents cascade failures
- (+) Circuit breaker prevents resource waste on failing sources (when fully implemented)
- (+) Model tier selection optimizes cost vs capability trade-offs
- (+) Atomic writes with backup-before-modify prevent data corruption
- (+) Parallel Phase 1a/1b reduces total pipeline time by ~40%
- (+) Source fallback ensures data acquisition despite individual source failures
- (-) Three levels of orchestration adds architectural complexity
- (-) Sequential service execution limits throughput (nodriver browser concurrency limitation)
- (-) State file proliferation (10+ JSON files) requires careful reconciliation
- (-) 30min stale timeout may reset legitimately long-running operations

**See also:** data-source-integration-architecture.md (for source fallback details)

### ADR-11: Entity Model & Schema Conventions

**Status:** Accepted

**Context:** PHX Houses pipeline requires a comprehensive property data model with 160+ fields from multiple sources (Assessor API, MLS, AI vision), strict validation for 7 HARD kill-switch criteria, and evolving schema requirements across phases. Need conventions for field naming, validation, serialization, provenance tracking, and schema versioning to maintain data integrity and enable safe evolution.

**Decision:** Use Pydantic V2 as the authoritative validation framework with the following conventions:

**1. Pydantic V2 as Primary Validation Layer**
- All data models inherit from `pydantic.BaseModel`
- Field validators (`@field_validator`) for business rules
- Model validators (`@model_validator`) for cross-field constraints
- `model_validate()` for deserialization, `model_dump(mode="json")` for serialization
- JSON schema generation via `model_json_schema()` for documentation

**2. Schema Organization**
- `PropertySchema`: Core listing data (85 fields) with kill-switch validation
- `EnrichmentDataSchema`: Extended property data (160+ fields) including crime, flood, schools, demographics
- `ImageEntryV2`: Image manifest entries with lineage tracking
- `ConfigSchemas`: Application configuration with 605-point scoring weights
- Separate schemas per domain concern (property, images, config, queue jobs)

**3. Field Naming Conventions**
- `snake_case` for all Python attributes
- Descriptive names with units: `lot_size_sqft`, `hoa_fee_monthly_usd`, `commute_minutes`
- Boolean fields: `has_pool`, `fireplace_present`, `flood_insurance_required`
- List fields: `*_list` suffix (e.g., `kitchen_features`, `exterior_features_list`)
- Metadata fields: `_` prefix (e.g., `_schema_metadata`, `_last_updated`)

**4. Schema Versioning**
- **Two separate versioning mechanisms:**
  - **PropertySchema (Pydantic):** Validation schema with `schema_version: str = "2.0.0"` field for structural validation
  - **EnrichmentData (domain entity):** Tracks schema metadata via `_schema_metadata` field for data migration and evolution
- `SchemaVersion` enum (V1_0, V2_0) in `services/schema/versioning.py` with migration support
- `SchemaMigrator` class handles backward-compatible migrations between data file versions
- `SchemaMetadata` dataclass tracks: version, created_at, migrated_at, migrated_from
- Migration script: `scripts/migrate_schema.py --to latest --backup`
- **Note:** Schema version tracked via `_schema_metadata` field in EnrichmentData, separate from PropertySchema validation

**5. Field-Level Provenance**
- `FieldProvenance` dataclass: `data_source`, `confidence` (0.0-1.0), `fetched_at`, `agent_id`, `phase`, `derived_from`
- Source confidence levels: Assessor (0.95), MLS (0.90), CSV (0.90), Web (0.75), AI (0.70)
- Provenance stored in `EnrichmentData._field_provenance: dict[str, FieldProvenance]`
- Methods: `set_field_provenance()`, `get_field_provenance()`, `get_low_confidence_fields()`

**6. Validation Patterns**
- Required vs Optional: `Field(...)` vs `Field(None)` or `| None` type hint
- Default values: `Field(default=...)` for optional fields with sensible defaults
- Constraints: `ge`, `le`, `min_length`, `pattern` for bounds checking
- Enums for constrained values: `SewerTypeSchema`, `SolarStatusSchema`, `OrientationSchema`, `Tier`
- Custom validators: ISO timestamp validation, MLS number format, address structure
- Cross-field validators: `pool_equipment_age` requires `has_pool=True`

**7. Serialization**
- `model_dump(mode="json")` for JSON output (handles datetime, Decimal, Enum)
- `model_dump(exclude_unset=True)` to omit null fields
- `model_dump(exclude={'_field_provenance'})` to exclude computed/derived fields from storage
- `extra="allow"` in `model_config` for metadata fields (`_last_updated`, `_last_county_sync`)
- Atomic writes via `atomic_json_save()` for crash recovery

**8. Enums with Business Logic**
- Domain enums in `domain/enums.py`: `Tier`, `Orientation`, `SolarStatus`, `SewerType`, `RiskLevel`, `FloodZone`
- Validation enums in `validation/schemas.py`: `SewerTypeSchema`, `SolarStatusSchema`, `OrientationSchema`
- Enums include properties: `.color`, `.label`, `.score`, `.css_class` for visualization
- Use `str, Enum` for string enums to ensure serialization compatibility

**9. Key Models**
- `PropertySchema`: Core domain entity (beds, baths, sqft, price, HOA, garage, sewer)
- `EnrichmentDataSchema`: Extended data (crime, flood, schools, demographics, 70+ PhoenixMLS fields)
- `ScoreBreakdown`: 605-point scoring (location: 250, systems: 175, interior: 180)
- `KillSwitchResult`: 7 HARD criteria evaluation with failure reasons
- `ImageEntryV2`: Image lineage (property_hash, content_hash, run_id, phash/dhash)

**10. Model Configuration**
- `str_strip_whitespace=True`: Normalize string inputs
- `validate_assignment=True`: Re-validate on field mutation
- `extra="forbid"`: Reject unknown fields (config schemas)
- `extra="allow"`: Accept unknown fields (enrichment data for forward compatibility)
- `populate_by_name=True`: Support field aliases (e.g., `pass_` aliased from `pass`)

**Consequences:**
- (+) Type safety: Pydantic catches validation errors at runtime before data persistence
- (+) Self-documenting: Field descriptions and constraints embedded in schema definitions
- (+) Schema evolution: Versioning enables safe migrations with backward compatibility (see `services/schema/versioning.py`)
- (+) Data lineage: Field provenance tracks source, confidence, and timestamps for quality assessment
- (+) Kill-switch validation: Pydantic validators enforce 7 HARD criteria
- (+) Serialization: Built-in JSON schema generation and model_dump() handle complex types
- (+) Quality gates: Confidence scoring per field enables quality metrics
- (+) Clean separation: PropertySchema (Pydantic validation) separate from EnrichmentData (domain entity with metadata)
- (-) Performance overhead: Pydantic validation adds 10-20ms per property (acceptable for <1000 properties)
- (-) Learning curve: Pydantic V2 validators differ from V1
- (-) Migration complexity: Adding/removing fields requires schema version bump and migration script
- (-) Memory usage: Storing provenance metadata increases JSON file size by ~15%

**See also:** schema-evolution-plan.md (migration strategy and timeline)

---

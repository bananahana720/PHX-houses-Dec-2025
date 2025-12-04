---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---

# tests/integration

## Purpose

Integration test suite validating multi-component workflows end-to-end. Tests verify complete pipeline execution from data loading through scoring, kill-switch filtering, error recovery, and report generation without mocking internal services.

## Contents

| Test File | Purpose | Test Count |
|-----------|---------|-----------|
| `test_pipeline.py` | Complete AnalysisPipeline workflow: load → enrich → filter → score → report | ~8 tests |
| `test_kill_switch_chain.py` | Kill-switch filter chain with HARD/SOFT criteria accumulation | ~6 tests |
| `test_deal_sheets_simple.py` | Deal sheet HTML generation from scored properties | ~4 tests |
| `test_crash_recovery.py` | Crash recovery: corrupt JSON, missing files, backup restore | ~3 tests |
| `test_transient_error_recovery.py` | Transient error retry logic with exponential backoff, work_items tracking | ~4 tests |
| `test_proxy_extension.py` | Proxy extension for stealth browser image extraction | ~2 tests |

## Key Test Scenarios

### test_pipeline.py (31 tests)
**Focus:** Complete end-to-end workflow validation

**Test Classes:**
- `TestFullPipeline` - Full pipeline with complete data (kill-switch → score)
- `TestPipelineWithIncompleteData` - Incomplete/missing field handling
- `TestMixedPropertyBatches` - Mixed pass/fail/unicorn properties
- `TestCsvExport` - Ranked CSV output with correct column ordering

**Key Scenarios:**
- Property with all enrichment data passes kill-switch and scores >0
- Properties with missing optional fields handled gracefully
- Kill-switch filter separates pass/fail properties correctly
- Scoring produces results in expected range (0-600 points)
- CSV export preserves data and ranks by score

**Fixtures Used:** sample_property, sample_unicorn_property, sample_failed_property, sample_property_minimal

### test_kill_switch_chain.py (27 tests)
**Focus:** Kill-switch severity system validation (HARD vs SOFT criteria, accumulation, thresholds)

**Test Classes:**
- `TestHardCriteria` - HOA, min bedrooms, min bathrooms (instant fail)
- `TestSoftCriteriaAccumulation` - Sewer (2.5), year (2.0), garage (1.5), lot (1.0)
- `TestSeverityThresholds` - Verdict rules (FAIL ≥3.0, WARNING ≥1.5, PASS <1.5)
- `TestBoundaryConditions` - Exact threshold validation (2.9 vs 3.0)

**Kill-Switch Criteria Reference:**
- **HARD (instant fail):** HOA > $0, beds < 4, baths < 2.0
- **SOFT (severity accumulation):**
  - City sewer (not septic): 2.5
  - Year built < 2024: 2.0
  - Garage spaces < 2: 1.5
  - Lot size not 7k-15k sqft: 1.0

**Severity Verdict Logic:**
- **FAIL:** Any HARD fail OR total severity ≥ 3.0
- **WARNING:** Total severity 1.5-3.0
- **PASS:** Total severity < 1.5

**Key Test Patterns:**
- Single HARD failure → FAIL (no accumulation)
- Multiple SOFT failures accumulate (2.5 + 1.5 = 4.0 → FAIL)
- Boundary testing: 2.9 severity → PASS, 3.0 severity → FAIL
- Property with 3 SOFT failures (sewer 2.5 + year 2.0 + garage 1.5 = 6.0) → FAIL

### test_crash_recovery.py (13 tests)
**Focus:** Data integrity and atomic write validation

**Test Classes:**
- `TestAtomicWrites` - Write-to-temp + atomic rename prevents corruption
- `TestBackupCreation` - Backup created before write with timestamp
- `TestBackupRestore` - Restore from backup on corruption/missing file
- `TestNormalizedAddressRecovery` - Recompute normalized_address if missing

**Atomic Write Pattern:**
1. Write data to temp file (enrichment_data.json.tmp)
2. Atomic rename temp → target (Path.replace() on Windows, rename on POSIX)
3. On crash: Either old file intact or new file complete (never partial)

**Backup Features:**
- Auto-created before write (if create_backup=True)
- Timestamped filename: `enrichment_data.20251203_143000.bak.json`
- Multiple versions per file possible
- restore_from_backup() finds most recent valid backup

**Key Scenarios:**
- Create new file and save (no pre-existing backup)
- Second save creates backup of first (timestamp differs)
- Corrupted file detected and backed up
- restore_from_backup() restores most recent backup
- Missing normalized_address computed and reapplied on load

### test_deal_sheets_simple.py (5 tests)
**Focus:** Data loading and enrichment merge validation

**Test Functions:**
- Load CSV listings (phx_homes.csv format)
- Load JSON enrichment (enrichment_data.json format)
- Merge enrichment into properties (field preservation)
- CSV column ordering (address → listing → county → features → scores → analysis)
- Data type conversions and None handling

**Data Merge Pattern:**
1. Load CSV properties (full_address as key)
2. Load JSON enrichment (indexed by address)
3. Match properties to enrichment by normalized address
4. Merge enrichment fields into Property entity
5. Verify original CSV fields retained after merge

## Test Architecture & Patterns

### Fixture-Based Test Data
- `sample_property` - Standard 4bd/2ba, passes kill-switches
- `sample_unicorn_property` - High-scoring 5bd/3.5ba
- `sample_failed_property` - HOA $200/mo (fails kill-switch)
- `sample_property_minimal` - Minimal data (all None optionals)
- `sample_properties` - Collection of 6 varied properties

### Arrange-Act-Assert Pattern
All tests follow clear structure:
1. **Arrange:** Set up test data (property, enrichment, repositories)
2. **Act:** Execute code being tested (filter, score, save/load)
3. **Assert:** Verify results match expected (verdict, score range, field values)

### Error Handling Testing
- Invalid JSON format → DataLoadError with clear message
- Missing CSV columns → DataLoadError
- File not found → Creates template or raises error
- Type coercion failures → ValueError with context

## Test Organization

**Fixtures:** Shared fixtures in conftest.py (properties, enrichment data, temp files)
**Parametrization:** Tests use `@pytest.mark.parametrize` for multi-scenario coverage
**Async Tests:** Async tests decorated with `@pytest.mark.asyncio`
**Mocking:** External APIs mocked (GreatSchools, WalkScore, FEMA); internal services real

## Tasks

- [x] Document integration test structure and test files
- [x] Map test organization: fixtures, parametrization, async patterns
- [x] Extract test counts per file (27 total integration tests)
- [x] Document error recovery test scenarios (crash recovery, transient retry)
- [ ] Add performance benchmarks for large batches P:M
- [ ] Implement CI/CD gates for integration test coverage P:H

## Learnings

- **Real vs Mock:** Integration tests use real repositories (CSV/JSON), services (kill-switch/scoring), but mock external APIs (GreatSchools, FEMA, WalkScore)
- **State management validation:** Test work_items.json state transitions (pending → done/failed) through complete workflows
- **Crash recovery coverage:** Tests verify atomic writes, backup creation, restore from backup with corrupted/missing files
- **Error propagation:** Transient errors retry with backoff; permanent errors fail immediately; all failures logged to work_items.json

## Refs

- Pipeline integration: `test_pipeline.py:1-50` (full workflow)
- Kill-switch chain: `test_kill_switch_chain.py:1-100` (HARD/SOFT accumulation)
- Crash recovery: `test_crash_recovery.py:1-80` (corruption/restore)
- Transient retry: `test_transient_error_recovery.py:1-150` (exponential backoff, work_items tracking)

## Deps

← Imports from:
  - `src/phx_home_analysis/pipeline/` - AnalysisPipeline orchestrator
  - `src/phx_home_analysis/services/` - Kill-switch, scoring services
  - `data/*.json, data/*.csv` - Test data files
  - `conftest.py` - Shared pytest fixtures

→ Imported by:
  - CI/CD pipeline (pytest command)
  - Manual testing before releases
  - Regression detection on API changes

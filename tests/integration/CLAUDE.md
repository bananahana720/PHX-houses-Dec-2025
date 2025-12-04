---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# tests/integration

## Purpose

Integration tests validating multi-component workflows in the PHX property analysis pipeline, including end-to-end property processing, kill-switch filtering with severity accumulation, crash recovery, and data loading. Tests the complete data flow from CSV/JSON loading through enrichment, filtering, and scoring.

## Contents

| Path | Purpose |
|------|---------|
| `test_pipeline.py` | End-to-end pipeline: properties through filtering → scoring (31 tests) |
| `test_kill_switch_chain.py` | Kill-switch severity system: HARD criteria, SOFT accumulation, thresholds (27 tests) |
| `test_crash_recovery.py` | Data integrity: atomic writes, backups, JSON corruption recovery (13 tests) |
| `test_deal_sheets_simple.py` | Data loading: CSV, JSON enrichment merge, field preservation (5 tests) |
| `test_proxy_extension.py` | Proxy extension integration: builder, auth, BrowserPool (4 test functions) |
| `README.md` | Comprehensive integration test guide with severity reference and execution instructions |

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

## Tasks

- [x] Map integration test coverage (5 test modules, 50+ tests) `P:H`
- [x] Identify kill-switch severity system patterns (HARD vs SOFT, thresholds) `P:H`
- [x] Catalog component dependencies (KillSwitchFilter, PropertyScorer, repositories) `P:H`
- [ ] Add property-based tests with Hypothesis for boundary conditions `P:M`
- [ ] Expand crash recovery tests for concurrent writes `P:M`

## Learnings

- **Kill-switch two-tier verdict system critical:** HARD criteria cause instant FAIL; SOFT criteria accumulate severity with WARNING (≥1.5) / FAIL (≥3.0) thresholds
- **Severity accumulation is complex:** Multiple SOFT failures must test exact boundaries (2.9 vs 3.0); single criterion failures pass below 1.5; no double-counting
- **Crash recovery requires atomic writes:** Backups created on second save; corruption handled via restore_from_backup(); normalized_address recomputed if missing
- **Pipeline orchestration tests:** Properties flow unchanged through filter→score chain; scoring works on both passed/failed properties; no state mutation between steps
- **Data merge preservation critical:** CSV original fields retained after enrichment merge; fixtures enable test data reuse; address matching uses normalization for robustness

## Refs

- Kill-switch severity config: `src/phx_home_analysis/services/kill_switch/constants.py:1-89`
- KillSwitchVerdict enum: `src/phx_home_analysis/services/kill_switch/__init__.py:1-20`
- Severity thresholds: `test_kill_switch_chain.py:15-65`
- Atomic write patterns: `test_crash_recovery.py:217-272`
- Pipeline integration: `test_pipeline.py:23-50`
- Fixture data: `tests/conftest.py:1-638`
- Test documentation: `README.md` (execution guide, severity reference)

## Deps

← Imports from:
- `src.phx_home_analysis.domain.entities` (Property, EnrichmentData)
- `src.phx_home_analysis.services.kill_switch.filter` (KillSwitchFilter, KillSwitchVerdict)
- `src.phx_home_analysis.services.scoring` (PropertyScorer)
- `src.phx_home_analysis.repositories.json_repository` (JsonEnrichmentRepository)
- `scripts.deal_sheets.data_loader` (load_ranked_csv, merge_enrichment_data)
- Standard library: json, pathlib, tempfile, csv

→ Imported by:
- CI/CD pipeline (pytest gates on PR)
- Manual testing before Phase 2 spawn
- Regression testing before releases
- Pre-commit hook validation

---

**Focus Areas**: End-to-end workflow validation, kill-switch severity system, crash recovery with atomic writes, data integrity on corrupted files, multi-source data merge.

**Test Count**: 80 tests across 5 modules (31 pipeline, 27 kill-switch, 13 crash recovery, 5 deal sheets, 4 proxy)

**Execution Time**: ~0.5-1.0 seconds total

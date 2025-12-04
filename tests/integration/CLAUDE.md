---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/integration

## Purpose
Integration tests validating multi-component workflows in the PHX property analysis pipeline, including end-to-end property processing, kill-switch filtering with severity accumulation, crash recovery, and data loading.

## Contents
| Path | Purpose |
|------|---------|
| `test_pipeline.py` | End-to-end pipeline: properties through filtering → scoring (31 tests) |
| `test_kill_switch_chain.py` | Kill-switch severity system: HARD criteria, SOFT accumulation, thresholds (27 tests) |
| `test_crash_recovery.py` | Data integrity: atomic writes, backups, JSON corruption recovery (13 tests) |
| `test_deal_sheets_simple.py` | Data loading: CSV, JSON enrichment merge, field preservation (5 tests) |
| `test_proxy_extension.py` | Proxy extension integration: builder, auth, BrowserPool (4 test functions) |
| `README.md` | Test guide with severity reference, fixture info, execution instructions |

## Key Test Scenarios

### test_pipeline.py (31 tests)
- Full pipeline with complete data (kill-switch → score)
- Incomplete/missing data handling
- Mixed property batches (pass/fail/unicorn)
- CSV export with ranked columns
- Fixture dependencies: sample_property, sample_unicorn_property, sample_failed_property

### test_kill_switch_chain.py (27 tests)
- HARD criteria (HOA, min beds, min baths) cause instant FAIL
- SOFT criteria severity accumulation (sewer 2.5 + year 2.0 + garage 1.5 + lot 1.0)
- Verdict thresholds: FAIL (≥3.0), WARNING (1.5-3.0), PASS (<1.5)
- Boundary testing: exact threshold validation
- Multiple SOFT failures: 2.9 PASS, 3.0+ FAIL

### test_crash_recovery.py (13 tests)
- Atomic writes prevent data corruption on crash/power loss
- Backup creation on second save (timestamped filenames)
- Corruption detection and recovery (restore_from_backup)
- Normalized address recomputation if missing
- JSON format handling (list vs dict) during recovery

### test_deal_sheets_simple.py (5 tests)
- Load CSV listings (phx_homes.csv format)
- Load JSON enrichment (enrichment_data.json format)
- Merge enrichment into properties (field preservation)
- CSV column ordering (address → listing → county → features)
- Data type conversions and None handling

## Tasks
- [x] Map integration test coverage (5 test modules, 50+ tests)
- [x] Identify kill-switch severity system patterns (HARD vs SOFT, thresholds)
- [x] Catalog component dependencies (KillSwitchFilter, PropertyScorer, JsonRepository)
- [ ] Add property-based tests with Hypothesis for boundary conditions P:M

## Learnings
- **Kill-switch two-tier verdict system:** HARD criteria cause instant FAIL; SOFT criteria accumulate severity with WARNING (≥1.5) / FAIL (≥3.0) thresholds
- **Severity accumulation is critical:** Multiple SOFT failures must test exact boundaries (2.9 vs 3.0); single criterion failures pass below 1.5
- **Crash recovery requires atomic writes:** Backups created on second save; corruption handled via restore_from_backup(); normalized_address recomputed if missing
- **Pipeline orchestration tests:** Properties flow unchanged through filter→score chain; scoring works on both passed/failed properties
- **Data merge preservation:** CSV original fields retained after enrichment merge; fixtures enable test data reuse

## Refs
- Kill-switch severity config: `src/phx_home_analysis/services/kill_switch/constants.py:1-89`
- KillSwitchVerdict enum: `src/phx_home_analysis/services/kill_switch/__init__.py:1-20`
- Severity thresholds: `test_kill_switch_chain.py:15-65`
- Atomic write patterns: `test_crash_recovery.py:217-272`
- Pipeline integration: `test_pipeline.py:23-50`
- Fixture data: `tests/conftest.py:1-638`

## Deps
← Imports from:
  - `src.phx_home_analysis.domain.entities` (Property, EnrichmentData)
  - `src.phx_home_analysis.services.kill_switch.filter` (KillSwitchFilter, KillSwitchVerdict)
  - `src.phx_home_analysis.services.scoring` (PropertyScorer)
  - `src.phx_home_analysis.repositories.json_repository` (JsonEnrichmentRepository)
  - `scripts.deal_sheets.data_loader` (load_ranked_csv, merge_enrichment_data)

→ Imported by:
  - CI/CD pipeline (pytest gates)
  - Manual testing before Phase 2 spawn
  - Regression testing before releases

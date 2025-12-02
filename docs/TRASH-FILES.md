test_scorer.py - moved to TRASH/ - temporary test script for scorer verification
test_zillow_extractor.py - moved to TRASH/ - temporary validation script
scripts/update_lookup.py - moved to TRASH/ - temporary script for creating address_folder_lookup.json
test_dashboard.html - moved to TRASH/ - temporary test file for dashboard development
scripts/proxy_listing_extractor.py - moved to TRASH/ - superseded by extract_images.py (nodriver/curl_cffi approach)
scripts/gen_9832_deal_sheet.py - moved to TRASH/ - one-off script for specific property (9832 N 29th St)
MapConfig.py - moved to TRASH/ - unused config class (zero field references found) - deleted 2025-12-01
test_injection_fix.py - moved to TRASH/ - temporary security test verification script

## Cleanup Wave - 2025-12-02

### Corrupted/Artifact Files (TRASH/corrupted/)
=0.35 - moved to TRASH/corrupted/ - corrupted pip artifact
=0.7.0 - moved to TRASH/corrupted/ - corrupted pip artifact
=2.5.0 - moved to TRASH/corrupted/ - corrupted pip artifact
=4.12.0 - moved to TRASH/corrupted/ - corrupted pip artifact
nul - moved to TRASH/corrupted/ - Windows NUL device redirect

### Temporary Files (TRASH/temp/)
tmp_assessment.json - moved to TRASH/temp/ - temporary assessment data
temp_folder.txt - moved to TRASH/temp/ - temporary file reference
extraction_log.txt - moved to TRASH/temp/ - extraction work log
extraction_run.log - moved to TRASH/temp/ - extraction run log
server.log - moved to TRASH/temp/ - empty server log
image_assessment_result.json - moved to TRASH/temp/ - temporary assessment output

### Test Artifacts (TRASH/test_artifacts/)
test_redfin_image.jpg - moved to TRASH/test_artifacts/ - test image
zillow_test.png - moved to TRASH/test_artifacts/ - test image
test_redfin_manual.py - moved to TRASH/test_artifacts/ - one-off manual test
test_redfin_interactive.py - moved to TRASH/test_artifacts/ - one-off manual test

### Duplicate Files (TRASH/duplicates/)
scripts/enrichment_data.json - moved to TRASH/duplicates/ - duplicate of data/enrichment_data.json
scripts/orientation_estimates.json - moved to TRASH/duplicates/ - duplicate of data/orientation_estimates.json

## Reorganized Files - 2025-12-02

### Moved to docs/artifacts/implementation-notes/
- CONSTANTS_CLEANUP_SUMMARY.md
- CONSTANTS_QUICK_REFERENCE.txt
- DELIVERABLES.md
- DEPENDENCY_PINNING_SUMMARY.md
- DEPRECATION_CHECKLIST.md
- DEPRECATION_INDEX.md
- DEPRECATION_SUMMARY.md
- EXTERNALIZE_SUMMARY.md
- IMPLEMENTATION_COMPLETE.md
- INTEGRATION_TEST_SUMMARY.md
- LSH_OPTIMIZATION_SUMMARY.md
- LSH_QUICK_REFERENCE.md
- PERFORMANCE_COMPARISON.md
- PROXY_EXTENSION_IMPLEMENTATION.md
- SECURITY_FIX_SUMMARY.md
- VERIFICATION_REPORT.txt

### Moved to docs/
- CHANGELOG
- CODE_REFERENCE.md
- CONFIG_EXTERNALIZATION_INDEX.md
- SECURITY_INDEX.md
- SECURITY_QUICK_REFERENCE.txt
- SECURITY_SETUP.md

### Moved to scripts/
- extract_county_batch.py
- generate_extraction_report.py

### Moved to tests/
- test_extension_only.py → tests/unit/test_proxy_extension_builder.py
- test_proxy_extension.py → tests/integration/test_proxy_extension.py
- test_lsh_performance.py → tests/benchmarks/test_lsh_performance.py

## Schema Migration Test Files - 2025-12-02

test_v1_data.json - moved to TRASH/ - temporary test file for schema migration testing
test_v1_outdated.json - moved to TRASH/ - temporary test file for schema migration testing

## File Organization Cleanup - 2025-12-02

### Cache Directories (TRASH/cache_backup/)
.venv.bak/ - moved to TRASH/cache_backup/ - 482MB backup virtual environment (unused)
.pytest_cache/ - moved to TRASH/cache_backup/ - pytest cache (auto-regenerates)
.mypy_cache/ - moved to TRASH/cache_backup/ - mypy cache (auto-regenerates)
.ruff_cache/ - moved to TRASH/cache_backup/ - ruff cache (auto-regenerates)
nul - moved to TRASH/ - Windows NUL device artifact

### Deprecated Scripts (TRASH/deprecated/)
scripts/deal_sheets.py - moved to TRASH/deprecated/ - superseded by scripts/deal_sheets/ module (explicit deprecation notice)
scripts/extract_location_data.py - moved to TRASH/deprecated/ - superseded by map-analyzer agent

### Migration Scripts (TRASH/migrations/) - One-time migrations complete
scripts/migrate_to_work_items.py - moved to TRASH/migrations/ - state migration from extraction_state.json complete
scripts/consolidate_geodata.py - moved to TRASH/migrations/ - geocoding consolidation complete
scripts/geocode_homes.py - moved to TRASH/migrations/ - Nominatim geocoding complete, data in enrichment_data.json
scripts/sun_orientation_analysis.py - moved to TRASH/migrations/ - orientation now handled by map-analyzer agent

### Analysis Artifacts (TRASH/analysis_artifacts/)
scripts/show_best_values.py - moved to TRASH/analysis_artifacts/ - one-off CSV analysis script
scripts/generate_extraction_report.py - moved to TRASH/analysis_artifacts/ - test report generator

### Deleted Scripts (git rm - no longer needed)
scripts/verify_security_setup.py - DELETED - pre-commit hooks handle verification
scripts/demo_reporters.py - DELETED - demo/example code only, no production value
scripts/extract_county_batch.py - DELETED - not runnable, just hardcoded data/comments
scripts/cost_breakdown_analysis.py - DELETED - one-off CSV analysis, no integration

### Root Files Removed (git rm)
toolkit.json - DELETED - duplicate of .claude/knowledge/toolkit.json
ruff_errors.json - DELETED - generated linting output
data/enrichment_data.json.bak - DELETED - backup file
data/enrichment_data.json.pre_schema_version.bak - DELETED - backup file
data/property_images/metadata/extraction_state.json.bak - DELETED - backup file
data/property_images/metadata/image_manifest.json.bak - DELETED - backup file
docs/SECURITY_AUDIT_REPORT.md.bak - DELETED - backup file

### Documentation Moved to docs/artifacts/
CONSOLIDATION_SUMMARY.md, DEDUPLICATOR_TEST_USAGE.md, DEDUPLICATOR_UNIT_TESTS_SUMMARY.md,
DELIVERABLE_SUMMARY.md, DELIVERABLES.md, DELIVERY_SUMMARY.md, FINAL_SUMMARY.txt,
INDEX_DEDUPLICATOR_TESTS.md, INTEGRATION_VERIFICATION_REPORT.md, STANDARDIZER_TEST_DELIVERY.md,
TEST_COVERAGE_SUMMARY.txt, TEST_DELIVERABLES_INDEX.md, TEST_SUITE_OVERVIEW.txt,
TESTING_QUICK_START.md, URL_VALIDATOR_TEST_REFERENCE.md, VERIFICATION_SUMMARY.txt,
README_TESTING.md - all moved from root to docs/artifacts/

### Directories Consolidated
raw_exports/ - moved to data/raw_exports/
risk_checklists/ - moved to docs/risk_checklists/
templates/ - moved to docs/templates/
deal_sheets/ - DELETED (superseded by reports/deal_sheets/)

### Generic Templates Removed from .claude/
.claude/agents/: ai-engineer.md, code-reviewer.md, data-scientist.md, debugger.md, django-pro.md,
  error-detective.md, fastapi-pro.md, ml-engineer.md, mlops-engineer.md, prompt-engineer.md,
  python-pro.md, test-automator.md - DELETED (not project-specific)
.claude/commands/: ai-assistant.md, config-validate.md, deps-audit.md, error-analysis.md,
  error-trace.md, langchain-agent.md, ml-pipeline.md, prompt-optimize.md, python-scaffold.md,
  refactor-clean.md, smart-debug.md, tech-debt.md - DELETED (not project-specific)

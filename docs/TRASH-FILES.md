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

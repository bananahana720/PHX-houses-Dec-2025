# Test Design: Epic 2-7 Live Data Testing

**Version:** 1.0
**Date:** 2025-12-04
**Author:** Murat (Master Test Architect)
**Status:** Draft - Pending Review

---

## Executive Summary

This test design addresses the need for **live data testing** across Epics 2-7 of the PHX Houses pipeline. The current test suite relies heavily on mocks, which hides real-world failures from:

- Bot detection (PerimeterX, Cloudflare)
- API rate limiting and quota exhaustion
- Schema drift in external APIs
- Multi-agent orchestration race conditions
- Data quality degradation over time

### Test Coverage Overview

| Category | Tests | Purpose |
|----------|-------|---------|
| **Live API Integration** | 76 | Real external API validation |
| **E2E Pipeline** | 35 | Full phase orchestration |
| **Total** | **111** | Comprehensive coverage |

### Key Deliverables

1. **76 Live API Integration Tests** - Validate County Assessor, GreatSchools, WalkScore, FEMA, Zillow/Redfin, Google Maps
2. **35 E2E Pipeline Tests** - Validate Phase 0→1→2→3→4 orchestration
3. **Observability Framework** - Telemetry, checkpoints, quality gates, dashboard

---

## Table of Contents

1. [Risk Assessment](#1-risk-assessment)
2. [Live API Integration Tests](#2-live-api-integration-tests)
3. [E2E Pipeline Tests](#3-e2e-pipeline-tests)
4. [Metrics & Checkpoint Framework](#4-metrics--checkpoint-framework)
5. [Implementation Plan](#5-implementation-plan)
6. [Success Criteria](#6-success-criteria)

---

## 1. Risk Assessment

### Current State: Mock-Heavy, Live-Light

| Category | Coverage | Risk |
|----------|----------|------|
| County Assessor | 10 live tests | LOW |
| GreatSchools API | Mock only | **HIGH** |
| WalkScore/FEMA | Mock only | **HIGH** |
| Zillow/Redfin extraction | Mock only | **CRITICAL** |
| Image assessment (Sonnet) | Mock only | **HIGH** |
| Multi-agent orchestration | No end-to-end | **CRITICAL** |
| Phase prerequisites | No validation tests | **HIGH** |

### Mock Risk Matrix

| Epic | Mock-Only Scenarios | Live Test Gap |
|------|---------------------|---------------|
| **E2: Data Acquisition** | 14 | PerimeterX bypass, API rate limits, image format variations |
| **E3: Kill-Switch** | 8 | Boundary values, hot-reload, CSV edge cases |
| **E4: Scoring** | 12 | Partial data, tier boundaries, re-scoring performance |
| **E5: Orchestration** | 18 | Agent spawning, parallel coordination, conflict resolution |
| **E6: Visual Analysis** | 14 | Sonnet scoring accuracy, foundation crack detection |
| **E7: Deal Sheets** | 12 | Mobile rendering, offline capability, chart accuracy |

---

## 2. Live API Integration Tests

### 2.1 County Assessor API (Maricopa County)

**Expand from 10 → 25 tests**

| Test ID | Name | Type | Risk if Mocked |
|---------|------|------|----------------|
| LIVE_COUNTY_001 | authentication_valid_token | positive | Token format changes |
| LIVE_COUNTY_002 | authentication_expired_token | negative | Token refresh failures |
| LIVE_COUNTY_003 | schema_validation_all_required_fields | positive | Schema drift undetected |
| LIVE_COUNTY_004 | rate_limiting_burst_protection | boundary | Rate limit violations |
| LIVE_COUNTY_005 | data_accuracy_known_property | positive | Data drift undetected |
| LIVE_COUNTY_006 | error_handling_malformed_address | negative | Error handling bugs |
| LIVE_COUNTY_007 | error_handling_address_not_found | negative | 404 handling |
| LIVE_COUNTY_008 | performance_single_request_sla | performance | Timeout config wrong |
| LIVE_COUNTY_009 | timeout_handling_slow_response | boundary | Hangs in production |
| LIVE_COUNTY_010 | network_error_handling_dns_failure | negative | Network recovery bugs |
| LIVE_COUNTY_011 | batch_extraction_50_properties_performance | performance | Rate limits kill batches |
| LIVE_COUNTY_012 | edge_case_new_subdivision_no_data | edge | New construction crashes |
| LIVE_COUNTY_013 | edge_case_po_box_address_rejection | negative | PO Box slips through |
| LIVE_COUNTY_014 | edge_case_commercial_property_rejection | edge | Commercial scored wrong |
| LIVE_COUNTY_015 | edge_case_condo_unit_number_handling | edge | Unit number parsing |
| LIVE_COUNTY_016 | token_refresh_near_expiration | boundary | Auth failures |
| LIVE_COUNTY_017 | token_refresh_during_batch_operation | boundary | Mid-batch auth breaks |
| LIVE_COUNTY_018 | response_schema_drift_new_field | edge | Forward compatibility |
| LIVE_COUNTY_019 | response_schema_drift_field_rename | negative | Breaking changes |
| LIVE_COUNTY_020 | partial_data_missing_garage_spaces | edge | Null handling bugs |
| LIVE_COUNTY_021 | partial_data_missing_pool_indicator | edge | Pipeline null crashes |
| LIVE_COUNTY_022 | data_freshness_recent_sale_updated_year | positive | Stale data undetected |
| LIVE_COUNTY_023 | geographic_boundary_scottsdale_adjacent | edge | Boundary misclassified |
| LIVE_COUNTY_024 | concurrent_requests_race_condition | boundary | Cache corruption |
| LIVE_COUNTY_025 | ssl_certificate_validation | positive | MITM vulnerability |

### 2.2 GreatSchools API

**NEW: 10 tests**

| Test ID | Name | Type | Risk if Mocked |
|---------|------|------|----------------|
| LIVE_SCHOOLS_001 | school_assignment_lookup_known_address | positive | School boundaries change |
| LIVE_SCHOOLS_002 | composite_score_calculation_validation | positive | Formula drift |
| LIVE_SCHOOLS_003 | rate_limiting_daily_quota | boundary | Quota exhaustion |
| LIVE_SCHOOLS_004 | fallback_to_google_places_when_unavailable | edge | Fallback logic untested |
| LIVE_SCHOOLS_005 | data_freshness_rating_change_mid_year | edge | Stale ratings |
| LIVE_SCHOOLS_006 | missing_school_assignment_charter_enrollment | edge | Charter handling |
| LIVE_SCHOOLS_007 | school_boundary_change_annual_update | edge | Boundary updates |
| LIVE_SCHOOLS_008 | distance_calculation_accuracy | positive | Proximity scoring wrong |
| LIVE_SCHOOLS_009 | private_school_exclusion | positive | Private schools included |
| LIVE_SCHOOLS_010 | api_version_deprecation_warning | edge | API deprecation missed |

### 2.3 WalkScore & FEMA APIs

**NEW: 8 tests**

| Test ID | Name | Type | Risk if Mocked |
|---------|------|------|----------------|
| LIVE_WALK_001 | walkscore_validation_downtown_phoenix | positive | Walkability miscategorized |
| LIVE_WALK_002 | walkscore_validation_suburban_low_score | positive | Suburban over-scored |
| LIVE_WALK_003 | walkscore_data_age_degradation | edge | Stale data full confidence |
| LIVE_WALK_004 | walkscore_rate_limiting_behavior | boundary | Rate limit handling |
| LIVE_FEMA_001 | fema_flood_zone_query_known_zone_X | positive | Flood zones misclassified |
| LIVE_FEMA_002 | fema_flood_zone_query_high_risk_zone_A | positive | High-risk missed |
| LIVE_FEMA_003 | fema_data_not_available_new_area | edge | Unmapped areas treated safe |
| LIVE_FEMA_004 | fema_map_update_effective_date | edge | Map revisions missed |

### 2.4 Zillow/Redfin Extraction

**NEW: 15 tests (CRITICAL)**

| Test ID | Name | Type | Risk if Mocked |
|---------|------|------|----------------|
| LIVE_SCRAPE_001 | nodriver_perimeter_x_bypass_success | positive | Bot detection undetected |
| LIVE_SCRAPE_002 | nodriver_blocked_fallback_to_curl_cffi | edge | Fallback chain untested |
| LIVE_SCRAPE_003 | curl_cffi_blocked_fallback_to_playwright | edge | Cascade failures |
| LIVE_SCRAPE_004 | user_agent_rotation_20_signatures | positive | UA rotation ineffective |
| LIVE_SCRAPE_005 | image_url_extraction_accuracy | positive | Wrong image selector |
| LIVE_SCRAPE_006 | image_download_bulk_25_photos | performance | Download failures |
| LIVE_SCRAPE_007 | field_extraction_price_beds_baths_hoa | positive | Selector drift |
| LIVE_SCRAPE_008 | listing_status_active_pending_sold | positive | Status detection broken |
| LIVE_SCRAPE_009 | selector_drift_detection_price_field | negative | Silent breakage |
| LIVE_SCRAPE_010 | captcha_detection_and_retry | edge | Captcha handling broken |
| LIVE_SCRAPE_011 | rate_limiting_zillow_5_requests_per_minute | boundary | Account blocks |
| LIVE_SCRAPE_012 | redfin_vs_zillow_data_consistency | positive | Data discrepancies |
| LIVE_SCRAPE_013 | mobile_viewport_scraping | edge | Mobile layout breaks |
| LIVE_SCRAPE_014 | javascript_rendered_content_extraction | positive | JS content missed |
| LIVE_SCRAPE_015 | proxy_rotation_to_avoid_ip_ban | edge | IP bans undetected |

### 2.5 Google Maps APIs

**NEW: 8 tests**

| Test ID | Name | Type | Risk if Mocked |
|---------|------|------|----------------|
| LIVE_GMAPS_001 | geocoding_accuracy_phoenix_address | positive | Geocoding errors propagate |
| LIVE_GMAPS_002 | distance_matrix_grocery_proximity | positive | Proximity scoring wrong |
| LIVE_GMAPS_003 | distance_matrix_highway_access | positive | Commute scoring wrong |
| LIVE_GMAPS_004 | distance_matrix_school_proximity | positive | Cross-API inconsistency |
| LIVE_GMAPS_005 | satellite_imagery_sun_orientation_inference | positive | Orientation speculative |
| LIVE_GMAPS_006 | api_cost_tracking_per_property | performance | Budget overruns |
| LIVE_GMAPS_007 | rate_limiting_quota_enforcement | boundary | Quota exhaustion |
| LIVE_GMAPS_008 | geocoding_ambiguous_address_resolution | edge | Wrong coordinates |

---

## 3. E2E Pipeline Tests

### 3.1 Happy Path (5 tests)

| Test ID | Name | Phases | Validates |
|---------|------|--------|-----------|
| E2E_HP_001 | single_property_complete_flow | 0-4 | Full pipeline single property |
| E2E_HP_002 | batch_5_properties_all_pass_kill_switch | 0-4 | Batch processing, parallel Phase 1 |
| E2E_HP_003 | batch_10_properties_mixed_tiers | 0-4 | Tier distribution accuracy |
| E2E_HP_004 | resume_from_checkpoint_phase_2 | 2-4 | Checkpoint recovery |
| E2E_HP_005 | skip_phase_1_validation | 0,2-4 | Skip-phase flag handling |

### 3.2 Failure Scenarios (10 tests)

| Test ID | Name | Phases | Validates |
|---------|------|--------|-----------|
| E2E_PF_001 | phase_0_county_api_down | 0 | API failure handling |
| E2E_PF_002 | phase_1a_zillow_blocked_fallback_redfin | 1 | Fallback chain |
| E2E_PF_003 | phase_1a_zillow_and_redfin_both_fail | 1 | Cascade failure handling |
| E2E_PF_004 | phase_1b_maps_quota_exceeded | 1 | Cache fallback |
| E2E_PF_005 | phase_2_no_images_available | 2 | Prerequisite blocking |
| E2E_PF_006 | phase_2_prerequisite_validation_fails | 2 | Gate enforcement |
| E2E_PF_007 | phase_3_scoring_exception | 3 | Exception handling |
| E2E_PF_008 | phase_4_disk_full_partial_report | 4 | I/O error handling |
| E2E_PF_009 | retry_logic_3_attempts_exponential_backoff | 0-2 | Retry mechanism |
| E2E_PF_010 | agent_timeout_10_min_level_3_skip | 2 | Timeout handling |

### 3.3 Multi-Agent Orchestration (8 tests)

| Test ID | Name | Validates |
|---------|------|-----------|
| E2E_OR_001 | parallel_phase_1_listing_and_map_spawn | Parallel agent spawning |
| E2E_OR_002 | parallel_completion_data_aggregation | Data merge after parallel completion |
| E2E_OR_003 | one_phase_1_agent_fails_other_succeeds | Partial phase success |
| E2E_OR_004 | agent_conflict_resolution_county_vs_listing | Data source prioritization |
| E2E_OR_005 | atomic_state_write_no_corruption | Concurrent write safety |
| E2E_OR_006 | agent_spawn_correct_model_haiku_vs_sonnet | Model routing |
| E2E_OR_007 | skill_loading_agents_load_correct_skills | Skill system |
| E2E_OR_008 | output_budget_enforcement_agents_respect_max_tokens | Token budget |

### 3.4 State Management (7 tests)

| Test ID | Name | Validates |
|---------|------|-----------|
| E2E_SM_001 | atomic_write_backup_temp_rename_pattern | Atomic file writes |
| E2E_SM_002 | crash_recovery_resume_from_orphaned_in_progress | Crash recovery |
| E2E_SM_003 | data_consistency_work_items_matches_enrichment_data | Cross-file consistency |
| E2E_SM_004 | address_normalization_same_address_all_state_files | Address normalization |
| E2E_SM_005 | checkpoint_validation_phase_n_minus_1_complete | Prerequisite enforcement |
| E2E_SM_006 | stale_data_detection_items_over_10_min_in_progress | Stale item detection |
| E2E_SM_007 | concurrent_write_prevention_file_locking | File locking |

### 3.5 Kill-Switch Integration (5 tests)

| Test ID | Name | Validates |
|---------|------|-----------|
| E2E_KS_001 | hard_fail_phase_0_hoa_fee_200 | HOA kill-switch |
| E2E_KS_002 | hard_fail_phase_0_sqft_1500 | Sqft kill-switch |
| E2E_KS_003 | all_8_hard_criteria_test_each_criterion | All 8 HARD criteria |
| E2E_KS_004 | multi_failure_tracking_property_fails_3_criteria | Multi-failure logging |
| E2E_KS_005 | kill_switch_before_scoring_verdict_determined_early | Early verdict |

---

## 4. Metrics & Checkpoint Framework

### 4.1 Component Overview

| Component | Purpose | Location |
|-----------|---------|----------|
| **CheckpointManager** | Per-phase telemetry with Pydantic validation | `src/phx_home_analysis/telemetry/checkpoint_manager.py` |
| **APIMonitor** | External API latency/error tracking | `src/phx_home_analysis/telemetry/api_monitor.py` |
| **AgentTracker** | LLM cost/token tracking | `src/phx_home_analysis/telemetry/agent_tracker.py` |
| **QualityTracker** | Completeness/confidence per property | `src/phx_home_analysis/telemetry/quality_tracker.py` |
| **RetroactiveDetector** | Kill-switch verdict flip detection | `src/phx_home_analysis/telemetry/retroactive_detector.py` |
| **PrePhase2Gate** | Block Phase 2 if images missing | `src/phx_home_analysis/gates/pre_phase_2.py` |
| **PrePhase3Gate** | Warn if scoring data incomplete | `src/phx_home_analysis/gates/pre_phase_3.py` |
| **PostBatchGate** | Block if error rate >5% | `src/phx_home_analysis/gates/post_batch.py` |
| **Dashboard Generator** | Real-time Plotly visualization | `scripts/generate_dashboard.py` |
| **Quality Report** | AI-friendly JSON for LLM analysis | `scripts/generate_quality_report.py` |

### 4.2 Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API error rate | 5% | 10% | Pause batch, investigate |
| Completeness | 80% | 60% | Flag for review |
| API latency | 5s | 10s | Check rate limits |
| Phase duration | 5 min | 10 min | Investigate slow operation |
| Cost per spawn | $0.10 | $0.20 | Review token usage |
| Data staleness | 12h | 24h | Trigger re-extraction |

### 4.3 Checkpoint Schema

```yaml
property_checkpoint:
  property_id: "123_main_st"
  address: "123 Main St Phoenix AZ 85001"
  pipeline_status: "phase_2_complete"

  phases:
    phase_0:
      status: "complete"
      started_at: "2025-12-04T10:00:00Z"
      completed_at: "2025-12-04T10:01:15Z"
      duration_sec: 75
      data_captured:
        lot_size: 10000
        year_built: 2015
        confidence: 0.95
      validation_results: [...]
      kill_switch_evaluated: {...}
      errors: []
      warnings: []
      next_phase_ready: true
```

### 4.4 Quality Grade Calculation

```
quality_score = (completeness_pct * 0.6) + (confidence_avg * 100 * 0.4)

EXCELLENT: score >= 95
GOOD:      80 <= score < 95
FAIR:      60 <= score < 80
POOR:      score < 60
```

---

## 5. Implementation Plan

### Phase 1: Core Telemetry (Week 1)

- [ ] Implement `CheckpointManager` with Pydantic schemas
- [ ] Add `checkpoint.start_phase()` / `complete_phase()` to pipeline scripts
- [ ] Validate telemetry JSON writes correctly
- [ ] Unit tests for checkpoint CRUD operations

### Phase 2: API & Agent Tracking (Week 2)

- [ ] Implement `APIMonitor` context manager
- [ ] Implement `AgentTracker` context manager
- [ ] Integrate monitors into Phase 1-2 workflows
- [ ] Validate latency/cost metrics captured
- [ ] Unit tests for telemetry collection

### Phase 3: Quality Gates (Week 3)

- [ ] Implement `PrePhase2Gate`, `PrePhase3Gate`, `PostBatchGate`
- [ ] Integrate gates into `/analyze-property` command
- [ ] Validate gates block on failures
- [ ] Unit tests for gate logic

### Phase 4: Live API Tests - Tier 1 (Week 4)

- [ ] County Assessor expansion (15 new tests)
- [ ] Zillow/Redfin extraction (15 new tests)
- [ ] Set up test data fixtures
- [ ] CI integration for `-m live` tests

### Phase 5: Live API Tests - Tier 2 (Week 5)

- [ ] GreatSchools API (10 tests)
- [ ] WalkScore/FEMA (8 tests)
- [ ] Google Maps (8 tests)
- [ ] Cost tracking validation

### Phase 6: E2E Pipeline Tests (Week 6)

- [ ] Happy path tests (5)
- [ ] Failure scenarios (10)
- [ ] Orchestration tests (8)
- [ ] State management tests (7)
- [ ] Kill-switch integration (5)

### Phase 7: Dashboard & Reporting (Week 7)

- [ ] Implement `generate_dashboard.py` with Plotly
- [ ] Implement `generate_quality_report.py`
- [ ] Test LLM analysis workflow
- [ ] Documentation in `CLAUDE.md`

---

## 6. Success Criteria

### Test Coverage Targets

| Category | Tests | Code Coverage |
|----------|-------|---------------|
| County Assessor | 25 | 95%+ |
| GreatSchools | 10 | 90%+ |
| WalkScore/FEMA | 8 | 85%+ |
| Zillow/Redfin | 15 | 100% fallback chain |
| Google Maps | 8 | 90%+ |
| E2E Pipeline | 35 | 90%+ |

### Quality Gates

| Gate | Threshold | Action on Fail |
|------|-----------|----------------|
| Pass Rate | >= 95% | Block deployment |
| Performance SLA | Within spec | Alert + investigate |
| Cost per property | < $0.10 | Budget review |
| Detection Rate | 100% schema drift | Alert in 24hr |

### Risk Mitigation

| Risk | Before | After |
|------|--------|-------|
| Bot detection | CRITICAL (9/10) | LOW (2/10) |
| Rate limiting | HIGH (8/10) | LOW (2/10) |
| Schema drift | HIGH (8/10) | MEDIUM (3/10) |
| Cost overruns | MEDIUM (6/10) | LOW (1/10) |
| Data accuracy | MEDIUM (5/10) | LOW (2/10) |

---

## Appendix A: File Locations

| Component | File Path |
|-----------|-----------|
| Checkpoint manager | `src/phx_home_analysis/telemetry/checkpoint_manager.py` |
| API monitor | `src/phx_home_analysis/telemetry/api_monitor.py` |
| Agent tracker | `src/phx_home_analysis/telemetry/agent_tracker.py` |
| Quality tracker | `src/phx_home_analysis/telemetry/quality_tracker.py` |
| Retroactive detector | `src/phx_home_analysis/telemetry/retroactive_detector.py` |
| Quality gates | `src/phx_home_analysis/gates/` |
| Dashboard generator | `scripts/generate_dashboard.py` |
| Quality report generator | `scripts/generate_quality_report.py` |
| Telemetry data | `data/pipeline_telemetry.json` |
| Quality reports | `reports/quality_report_{batch_id}.json` |
| Dashboard HTML | `reports/dashboard.html` |
| Live API tests | `tests/live/` |
| E2E pipeline tests | `tests/integration/test_e2e_pipeline.py` |

---

## Appendix B: Test Execution

### Run Live Tests Only

```bash
# Run all live tests (requires API keys)
pytest tests/live/ -m live -v

# Run specific API tests
pytest tests/live/test_county_assessor_live.py -v
pytest tests/live/test_zillow_redfin_live.py -v

# Run with cost limit
pytest tests/live/ --cost-limit=5.00
```

### Run E2E Pipeline Tests

```bash
# Smoke tests (every commit)
pytest tests/integration/ -m "tier0" --maxfail=2

# Full E2E suite (pre-release)
pytest tests/integration/test_e2e_pipeline.py -v
```

### Generate Dashboard

```bash
# Auto-refresh every 30s during batch
watch -n 30 python scripts/generate_dashboard.py

# Open in browser
open reports/dashboard.html
```

### Generate Quality Report

```bash
# After batch completion
python scripts/generate_quality_report.py

# Feed to LLM for analysis
cat reports/quality_report_*.json | claude "Analyze and suggest improvements"
```

---

**Document Status:** Draft
**Last Updated:** 2025-12-04
**Next Review:** Before Epic 2-7 implementation sprint

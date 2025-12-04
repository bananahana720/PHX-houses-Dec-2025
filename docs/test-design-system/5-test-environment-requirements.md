# 5. Test Environment Requirements

### 5.1 Fixtures

| Fixture | Purpose | Location |
|---------|---------|----------|
| `sample_property.json` | Single property with all fields populated | `tests/fixtures/` |
| `sample_enrichment_data.json` | 5-property enrichment dataset | `tests/fixtures/` |
| `sample_work_items.json` | Pipeline state at various phases | `tests/fixtures/` |
| `kill_switch_edge_cases.csv` | Boundary condition test data | `tests/fixtures/` |
| `scoring_scenarios.json` | Pre-calculated scoring test cases | `tests/fixtures/` |

### 5.2 Mocks

| Mock | Purpose | Implementation |
|------|---------|----------------|
| `MockCountyAssessorClient` | Bypass County API in tests | respx fixture |
| `MockGreatSchoolsClient` | Bypass GreatSchools API | respx fixture |
| `MockGoogleMapsClient` | Bypass Google Maps API | respx fixture |
| `MockBrowserExtractor` | Bypass stealth browser | Mock class returning fixture data |
| `MockImageDownloader` | Bypass image downloads | Return pre-cached test images |

### 5.3 Configuration

| Config | Test Value | Production Value |
|--------|------------|------------------|
| `MARICOPA_ASSESSOR_TOKEN` | `test-token-123` | (from .env) |
| `GOOGLE_MAPS_API_KEY` | `test-key-456` | (from .env) |
| Test data directory | `tests/fixtures/data/` | `data/` |
| Cache TTL | 0 (disabled) | 7 days |

### 5.4 Test Directory Structure

```
tests/
+-- conftest.py                    # Shared fixtures
+-- unit/
|   +-- test_kill_switch.py        # Kill-switch criteria tests
|   +-- test_scorer.py             # Scoring strategy tests
|   +-- test_domain.py             # Entity/value object tests
|   +-- test_repositories.py       # Repository tests
|   +-- test_validation.py         # Schema validation tests
|   +-- services/
|       +-- test_job_queue.py      # Job queue tests
|       +-- test_zillow_extractor_validation.py
+-- integration/
|   +-- test_pipeline.py           # Pipeline orchestration
|   +-- test_kill_switch_chain.py  # Full kill-switch flow
|   +-- test_deal_sheets_simple.py # Report generation
+-- e2e/
|   +-- test_cli_commands.py       # CLI smoke tests (new)
|   +-- test_full_pipeline.py      # End-to-end runs (new)
+-- fixtures/
|   +-- sample_property.json
|   +-- sample_enrichment_data.json
|   +-- sample_work_items.json
|   +-- kill_switch_edge_cases.csv
+-- benchmarks/
    +-- test_lsh_performance.py
```

---

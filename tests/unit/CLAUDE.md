---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# tests/unit

## Purpose

Comprehensive unit tests for PHX Home Analysis pipeline covering domain models, services, kill-switch logic, scoring, and data repositories in isolation. Tests 189+ test classes across 20+ test modules with focus on critical domain logic, kill-switches, and scoring algorithms. Enables fast feedback loop and regression prevention.

## Contents

| Path | Purpose |
|------|---------|
| `test_domain.py` | Domain entities, enums, value objects (9 classes, ~67 tests) |
| `test_kill_switch.py` | Kill-switch criteria filtering (10 classes, ~75 tests) |
| `test_scorer.py` | Property scoring system and tier classification (8 classes, ~46 tests) |
| `test_repositories.py` | CSV/JSON data repository patterns (11 classes, ~50+ tests) |
| `test_validation.py` | Pydantic schema validation and constraints (14 classes) |
| `test_config_schemas.py` | Configuration schema validation for YAML configs (14 classes) |
| `test_config_loader.py` | Configuration loading and merging (8 classes) |
| `test_cost_estimation.py` | Monthly cost calculations (19 classes) |
| `test_county_pipeline.py` | County API data extraction pipeline (9 classes) |
| `test_ai_enrichment.py` | AI enrichment service tests (6 classes) |
| `test_quality_metrics.py` | Data quality scoring and tracking (6 classes) |
| `test_state_manager.py` | Checkpoint/recovery state management (2 classes) |
| `test_extraction_stats.py` | Extraction statistics tracking (3 classes) |
| `test_deduplicator.py` | Address deduplication logic (10 classes) |
| `test_standardizer.py` | Address standardization (13 classes) |
| `test_url_validator.py` | URL validation and sanitization (16 classes) |
| `test_logging_utils.py` | Logging utility functions (2 classes) |
| `test_processing_pool.py` | Parallel processing pool |
| `test_proxy_extension_builder.py` | Proxy extension building |
| `test_lib_kill_switch.py` | Kill-switch library integration (18 classes) |
| `services/test_job_queue.py` | Job queue service lifecycle and executor (5 classes) |
| `services/test_zillow_extractor_validation.py` | Zillow data validation (6 classes) |
| `utils/test_address_utils.py` | Address utility functions (2 classes, ~15 tests) |

## Test Categories

### Core Domain Tests (test_domain.py)
**Focus:** Domain entities, enums, value objects, computed properties

**Test Classes (9):**
- `TestPropertyEntity` - Main Property entity with 150+ fields
- `TestEnrichmentDataEntity` - EnrichmentData mirror structure
- `TestAddressValueObject` - Immutable Address with formatting
- `TestScoreValueObject` - Score validation and weighted calculation
- `TestScoreBreakdownValueObject` - 600-point section aggregation
- `TestTierEnum` - Tier classification colors, labels, from_score()
- `TestOrientationEnum` - Arizona-specific cooling costs, base_score
- `TestEnums` - SolarStatus, SewerType, RiskLevel, ImageStatus
- `TestComputedProperties` - price_per_sqft, has_hoa, age_years, is_unicorn

**Coverage:** Enums (9), value objects (7), entities (2), computed properties (12+)

### Kill-Switch Tests (test_kill_switch.py, test_lib_kill_switch.py)
**Focus:** Kill-switch criteria filtering, severity accumulation, thresholds

**Test Classes (28):**
- `TestNoHoaKillSwitch` - HOA must be $0
- `TestMinBedroomsKillSwitch` - Beds >= 4
- `TestMinBathroomsKillSwitch` - Baths >= 2.0
- `TestCitySewerKillSwitch` - City sewer vs septic (severity 2.5)
- `TestNoNewBuildKillSwitch` - Year built < 2024 (severity 2.0)
- `TestMinGarageKillSwitch` - Garage >= 2 spaces (severity 1.5)
- `TestLotSizeKillSwitch` - 7k-15k sqft range (severity 1.0)
- `TestKillSwitchFilter` - Combined filter with verdict
- Additional: Boundary testing, severity accumulation, verdict logic

**Coverage Targets:**
- HARD criteria: instant fail on any violation
- SOFT criteria: severity thresholds (FAIL ≥3.0, WARNING ≥1.5, PASS <1.5)
- Boundary testing: 6999 vs 7000 sqft, 2023 vs 2024, 1.9 vs 2.0 baths, $0 vs $1 HOA

### Scoring Tests (test_scorer.py)
**Focus:** Property scoring system, 600-point allocation, tier classification

**Test Classes (8):**
- `TestPropertyScorer` - Main scorer orchestration
- `TestLocationScoring` - School district, quietness, crime, grocery, parks, orientation, flood, walk score
- `TestSystemsScoring` - Roof, plumbing, pool, backyard, cost efficiency
- `TestInteriorScoring` - Kitchen, master suite, light, ceilings, fireplace, laundry, aesthetics
- `TestScoreBreakdown` - Section totals and 600-point total
- `TestTierClassification` - Unicorn (>480), Contender (360-480), Pass (<360), Failed
- `TestComputedScores` - Price per sqft, quality metrics

**Coverage:** 7 location strategies, 4 systems strategies, 7 interior strategies, aggregation, tier assignment

### Repository Tests (test_repositories.py)
**Focus:** CSV/JSON data persistence, CRUD operations, type coercion, caching

**Test Classes (11):**
- `TestCsvPropertyRepository` - Load/parse CSV, caching, errors
- `TestJsonEnrichmentRepository` - JSON load/save, atomic writes, validation
- `TestRepositoryErrorHandling` - Missing files, invalid JSON, type errors
- `TestCaching` - Lazy load behavior, cache invalidation
- `TestTypeCoercion` - Parse int, float, bool, enum, list from strings
- `TestAtomicWrites` - Write-to-temp pattern
- `TestBackupManagement` - Timestamp-based backup creation
- `TestAddressMatching` - Normalized address lookup
- Plus: Template creation, format flexibility, merge operations

**Coverage:** 50+ fields, CSV parsing, JSON validation, error paths, caching semantics

### Configuration Tests (test_config_schemas.py, test_config_loader.py)
**Focus:** Pydantic schemas, YAML loading, validation, environment overrides

**Test Classes (22):**
- `TestScoringWeightsSchema` - 600-point system validation
- `TestBuyerCriteriaSchema` - Buyer profile constraints
- `TestKillSwitchCriteriaSchema` - HARD/SOFT criteria weights
- `TestAppConfigSchema` - Full app configuration
- `TestLocationCriteria` - School, crime, quietness configs
- `TestYearBuiltCriterion` - Year thresholds and severity
- `TestLotSizeCriterion` - Lot size range and severity
- Plus: Tier thresholds, section configs, validation rules

**Coverage:** Schema validation, constraints, cross-field rules, default values, error messages

### Data Processing Tests
**Focus:** Quality metrics, deduplication, standardization, extraction stats

**Test Files:**
- `test_quality_metrics.py` (6 classes) - Completeness (60%) + confidence (40%), quality tiers
- `test_deduplicator.py` (10 classes) - Address fuzzy matching, LSH deduplication
- `test_standardizer.py` (13 classes) - Address canonicalization, direction abbreviations
- `test_url_validator.py` (16 classes) - URL validation and sanitization
- `test_extraction_stats.py` (3 classes) - Statistics tracking and reporting
- `test_county_pipeline.py` (9 classes) - County API data extraction phases
- `test_ai_enrichment.py` (6 classes) - LLM enrichment service

### Utility Tests (utils/test_address_utils.py)
**Focus:** Address normalization and matching

**Test Classes (2):**
- `TestNormalizeAddress` - Lowercase, punctuation removal, whitespace handling
- `TestAddressesMatch` - Case-insensitive, punctuation-insensitive comparison

**Coverage:** 15+ tests covering edge cases (empty, whitespace-only, complex addresses)

### Infrastructure Tests
**Focus:** Service layer, proxy management, state management

**Test Files:**
- `services/test_job_queue.py` (5 classes) - Job queue lifecycle, executor
- `services/test_zillow_extractor_validation.py` (6 classes) - Zillow data validation
- `test_logging_utils.py` (2 classes) - Logging utilities
- `test_state_manager.py` (2 classes) - Checkpoint/recovery
- `test_processing_pool.py` - Parallel processing
- `test_proxy_extension_builder.py` - Proxy extension building

## Test Execution & Coverage

**Total Tests:** 189+ test classes across 20+ modules (estimated 1000+ test methods)

**Execution:**
```bash
pytest tests/unit/ -v                           # All tests with verbose output
pytest tests/unit/test_kill_switch.py -v        # Specific test file
pytest tests/unit/ -k "boundary" -v             # Pattern matching
pytest tests/unit/ --cov=src --cov-report=term-missing  # Coverage report
```

**Performance:**
- Unit tests only: ~0.2-0.3 seconds
- Average per test: ~1ms
- Target coverage: 80%+ line coverage, 95%+ for critical paths (kill-switch, scoring)

## Key Testing Patterns

### Boundary Testing (Kill-Switch Critical)
```python
def test_lot_size_boundary_6999_fails():
    property.lot_sqft = 6999
    assert not lot_size_kill_switch.check(property)

def test_lot_size_boundary_7000_passes():
    property.lot_sqft = 7000
    assert lot_size_kill_switch.check(property)
```

### Severity Accumulation (Multiple Soft Failures)
```python
def test_severity_accumulation_sewer_2_5_plus_year_2_0_equals_4_5_fails():
    property.sewer_type = SewerType.SEPTIC  # 2.5
    property.year_built = 2024              # 2.0
    filter = KillSwitchFilter()
    verdict = filter.filter_properties([property])
    assert verdict.severity_total == 4.5
    assert verdict.verdict == KillSwitchVerdict.FAIL
```

### Type Validation
```python
def test_invalid_base_score_raises_error():
    with pytest.raises(ValueError):
        Score(criterion="Test", base_score=10.1, weight=50)
```

### Fixture-Based Test Data
```python
def test_with_fixture(sample_property):
    assert sample_property.beds == 4
    assert sample_property.hoa_fee == 0
```

## Tasks

- [x] Map all unit test modules and coverage areas `P:H`
- [x] Document test patterns (boundary, fixtures, assertions) `P:H`
- [x] Identify critical path test coverage (kill-switch, scoring) `P:H`
- [ ] Add property-based testing with Hypothesis for kill-switch boundaries `P:M`
- [ ] Expand Arizona-specific solar/pool edge cases `P:M`
- [ ] Add performance regression tests for large batches `P:L`

## Learnings

- **Boundary testing critical for kill-switches:** Lot size 6999 vs 7000, year 2023 vs 2024, baths 1.9 vs 2.0 require exact validation
- **Severity accumulation complex:** SOFT criteria add (2.5 + 1.5 = 4.0), thresholds are inclusive (≥3.0 fails), tests must validate totals not individual sums
- **Fixture isolation essential:** Property fixtures function-scoped, mutations don't affect other tests; enables parallel execution
- **Floating-point comparison:** Use `abs(a - b) < epsilon` not `==` for scores/costs
- **Enum case sensitivity:** SewerType.CITY vs "city" requires explicit conversion; tests validate both directions
- **None handling everywhere:** Domain logic gracefully handles None/missing values; tests cover None, empty, and populated states
- **CSV parsing robustness:** Windows line endings, path escaping, type coercion from strings all require careful testing

## Refs

- Kill-switch criteria: `src/phx_home_analysis/config/constants.py:1-80`
- Scoring weights: `src/phx_home_analysis/config/scoring_weights.py:1-150`
- Domain models: `src/phx_home_analysis/domain/entities.py:1-400`
- Enums: `src/phx_home_analysis/domain/enums.py:1-200`
- Value objects: `src/phx_home_analysis/domain/value_objects.py:1-450`
- Kill-switch filter: `src/phx_home_analysis/services/kill_switch/filter.py:1-100`
- Scoring orchestrator: `src/phx_home_analysis/services/scoring/scorer.py:1-150`
- Shared fixtures: `tests/conftest.py:1-638`

## Deps

← Imports from:
- pytest 9.0.1+, pytest-cov 7.0.0+, pytest-asyncio 1.3.0+, respx 0.22.0+
- conftest.py (shared fixtures: sample_property, sample_unicorn_property, mock_config)
- Standard library: json, pathlib, tempfile, typing

→ Imported by:
- CI/CD pipeline (must pass before PR merge)
- Pre-commit hooks (optional mypy)
- Local development (pytest, coverage)

---

**Test Count**: 189+ test classes, estimated 1000+ test methods
**Execution Time**: ~0.2-0.3 seconds
**Target Coverage**: 80%+ line, 95%+ critical paths (kill-switch, scoring)

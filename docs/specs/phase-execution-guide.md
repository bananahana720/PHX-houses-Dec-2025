# PHX Houses Scoring System Improvement - Phase Execution Guide

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

## Executive Summary

This document provides a session-by-session execution guide for implementing the scoring system improvements across multiple future Claude Code sessions. Each phase includes clear entry/exit criteria, verification checkpoints, and rollback procedures.

**Total Timeline:** 7 waves across 10-12 sessions (4-6 hours per session)

---

## Session Planning Matrix

| Wave | Sessions | Estimated Hours | Can Pause Mid-Wave? | Dependencies |
|------|----------|-----------------|---------------------|--------------|
| Wave 0 | 1 | 4-6 | ✓ Yes (after baseline) | None |
| Wave 1 | 2 | 6-8 | ✓ Yes (after tests pass) | Wave 0 complete |
| Wave 2 | 2-3 | 8-10 | ✓ Yes (after each calculator) | Wave 1 complete |
| Wave 3 | 1-2 | 4-6 | ✓ Yes (after schemas done) | Wave 0 complete (parallel) |
| Wave 4 | 2 | 6-8 | ✗ No (complete atomically) | Wave 3 complete |
| Wave 5 | 1-2 | 4-6 | ✓ Yes (after lineage done) | Wave 3, 4 complete |
| Wave 6 | 1-2 | 6-8 | ✓ Yes (after docs updated) | All prior waves |

---

## Wave 0: Baseline & Pre-Processing

### Session 0.1: Quality Baseline (2-3 hours)

**Entry Criteria:**
- Access to `data/phx_homes.csv`
- Access to `data/enrichment_data.json`
- All existing tests passing

**Tasks:**
1. Create `scripts/quality_baseline.py`
2. Run baseline measurement
3. Review output, identify gaps
4. Save `data/quality_baseline.json`

**Commands:**
```bash
# Create baseline script
# (Use implementation-spec.md Wave 0.1 code)

# Run baseline
python scripts/quality_baseline.py

# Verify output
cat data/quality_baseline.json
```

**Exit Criteria:**
- [ ] Script runs without errors
- [ ] Console report displays field completeness
- [ ] `data/quality_baseline.json` created
- [ ] Identified fields <95% documented

**Verification:**
```bash
# Check file exists
ls -lh data/quality_baseline.json

# Validate JSON structure
python -c "import json; json.load(open('data/quality_baseline.json'))"
```

**Rollback:** Delete `scripts/quality_baseline.py` and `data/quality_baseline.json`

---

### Session 0.2: Data Normalizer (2-3 hours)

**Entry Criteria:**
- Session 0.1 complete
- Quality gaps identified

**Tasks:**
1. Create `src/phx_home_analysis/validation/normalizer.py`
2. Create `tests/validation/test_normalizer.py`
3. Run tests, achieve 100% coverage

**Commands:**
```bash
# Create normalizer module
# (Use implementation-spec.md Wave 0.2 code)

# Run tests
pytest tests/validation/test_normalizer.py -v --cov

# Check coverage
pytest tests/validation/test_normalizer.py --cov-report=html
```

**Exit Criteria:**
- [ ] All normalizer tests pass
- [ ] 100% code coverage achieved
- [ ] Address normalization works for common variations
- [ ] Type inference handles strings, numbers, booleans

**Verification:**
```python
# Manual verification in Python REPL
from src.phx_home_analysis.validation.normalizer import normalize_address, generate_property_hash

# Test cases
assert normalize_address("123 N Main St") == "123 North Main Street"
assert generate_property_hash("123 N Main St") == generate_property_hash("123 North Main Street")
```

**Rollback:** Delete normalizer files, remove from git

---

### Session 0.3: Regression Baseline (1-2 hours)

**Entry Criteria:**
- Sessions 0.1, 0.2 complete
- Current system functional

**Tasks:**
1. Create `tests/regression/test_baseline.py`
2. Run regression tests
3. Save output for post-Wave 6 comparison

**Commands:**
```bash
# Create regression tests
# (Use implementation-spec.md Wave 0.3 code)

# Run and save results
pytest tests/regression/test_baseline.py -v | tee tests/regression/baseline_results.txt

# Store in git for comparison
git add tests/regression/
git commit -m "Add regression baseline for scoring improvements"
```

**Exit Criteria:**
- [ ] Regression tests capture current behavior
- [ ] Output saved to `baseline_results.txt`
- [ ] Committed to version control

**Verification:**
```bash
# Verify file exists and has content
wc -l tests/regression/baseline_results.txt  # Should have >50 lines
```

**Rollback:** Delete `tests/regression/` directory

---

### Wave 0 Summary

**Total Sessions:** 3 (6-8 hours)
**Pause Points:** After each session
**Critical Path:** Session 0.1 → 0.2 → 0.3

**Prerequisites for Wave 1:**
- [ ] Quality baseline established
- [ ] Data normalizer functional
- [ ] Regression baseline captured

---

## Wave 1: Kill-Switch Threshold

### Session 1.1: Weighted Threshold Logic (3-4 hours)

**Entry Criteria:**
- Wave 0 complete
- All existing tests passing
- Familiarity with `scripts/lib/kill_switch.py`

**Tasks:**
1. Update `scripts/lib/kill_switch.py` with weighted logic
2. Add `HARD_SEVERITY` and `SEVERITY_WEIGHTS` constants
3. Create `evaluate_kill_switches_weighted()` function
4. Maintain backward compatibility

**Commands:**
```bash
# Backup current file
cp scripts/lib/kill_switch.py scripts/lib/kill_switch.py.bak

# Edit file
# (Use implementation-spec.md Wave 1.1 code)

# Run existing tests (should still pass)
pytest tests/ -k kill_switch -v

# Verify backward compatibility
python -c "
from scripts.lib.kill_switch import evaluate_kill_switches
data = {'beds': 4, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 2, 'lot_sqft': 8000, 'year_built': 2010}
passed, failures, results = evaluate_kill_switches(data)
print(f'Passed: {passed}, Failures: {len(failures)}')
"
```

**Exit Criteria:**
- [ ] New constants added
- [ ] `evaluate_kill_switches_weighted()` implemented
- [ ] Backward compatibility maintained
- [ ] Existing tests pass

**Verification:**
```python
# Test new weighted logic
from scripts.lib.kill_switch import evaluate_kill_switches_weighted

# HARD failure test
data_hard_fail = {'beds': 3, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 2, 'lot_sqft': 8000, 'year_built': 2010}
verdict = evaluate_kill_switches_weighted(data_hard_fail)
assert verdict.verdict == 'FAIL', "HARD failure not working"

# SOFT warning test
data_soft_warn = {'beds': 4, 'baths': 2, 'hoa_fee': 0, 'sewer_type': 'city', 'garage_spaces': 1, 'lot_sqft': 8000, 'year_built': 2010}
verdict = evaluate_kill_switches_weighted(data_soft_warn)
assert verdict.verdict == 'WARNING', "SOFT warning not working"

print("✓ Weighted threshold logic working correctly")
```

**Rollback:**
```bash
# Restore backup
mv scripts/lib/kill_switch.py.bak scripts/lib/kill_switch.py
```

---

### Session 1.2: Unit Tests (2-3 hours)

**Entry Criteria:**
- Session 1.1 complete
- Weighted threshold logic implemented

**Tasks:**
1. Create `tests/services/kill_switch/test_weighted_threshold.py`
2. Test all HARD criteria
3. Test SOFT threshold scenarios
4. Test example scenarios from plan

**Commands:**
```bash
# Create test file
# (Use implementation-spec.md Wave 1.1 tests)

# Run tests
pytest tests/services/kill_switch/test_weighted_threshold.py -v

# Check coverage
pytest tests/services/kill_switch/ --cov=scripts.lib.kill_switch --cov-report=term-missing
```

**Exit Criteria:**
- [ ] All test classes pass (TestHardCriteria, TestSoftCriteriaThreshold, TestExampleScenarios)
- [ ] 95%+ code coverage for kill_switch.py
- [ ] All documented scenarios verified

**Verification:**
```bash
# Run full test suite
pytest tests/ -v

# Ensure no regressions
pytest tests/regression/test_baseline.py -v
```

**Rollback:** Delete test file, restore kill_switch.py from backup

---

### Session 1.3: Deal Sheets Integration (2-3 hours)

**Entry Criteria:**
- Sessions 1.1, 1.2 complete
- All tests passing

**Tasks:**
1. Update `scripts/deal_sheets/renderer.py`
2. Add verdict badge rendering
3. Update `scripts/deal_sheets/templates.py` with CSS
4. Generate sample deal sheet

**Commands:**
```bash
# Backup deal sheets
cp scripts/deal_sheets/renderer.py scripts/deal_sheets/renderer.py.bak
cp scripts/deal_sheets/templates.py scripts/deal_sheets/templates.py.bak

# Edit files
# (Use implementation-spec.md Wave 1.2 code)

# Generate test deal sheet
python -m scripts.deal_sheets --single "4732 W Davis Rd, Glendale, AZ 85306"

# Open in browser to verify
open deal_sheets/4732_W_Davis_Rd_Glendale_AZ_85306.html
```

**Exit Criteria:**
- [ ] Deal sheets display verdict badges (PASS/WARNING/FAIL)
- [ ] [H]/[S] markers visible
- [ ] Severity score displayed
- [ ] CSS styling applied (green/yellow/red)
- [ ] Manual visual verification passed

**Verification:**
- Open generated HTML in browser
- Verify verdict badge color
- Check [H]/[S] markers present
- Confirm severity score displays for WARNING/FAIL

**Rollback:**
```bash
mv scripts/deal_sheets/renderer.py.bak scripts/deal_sheets/renderer.py
mv scripts/deal_sheets/templates.py.bak scripts/deal_sheets/templates.py
```

---

### Wave 1 Summary

**Total Sessions:** 3 (7-10 hours)
**Pause Points:** After each session
**Critical Path:** Session 1.1 → 1.2 → 1.3

**Prerequisites for Wave 2:**
- [ ] Weighted threshold logic working
- [ ] All tests passing
- [ ] Deal sheets display verdicts correctly

---

## Wave 2: Cost Estimation Module

### Session 2.1: Rate Provider (2-3 hours)

**Entry Criteria:**
- Wave 1 complete
- Understanding of AZ cost factors

**Tasks:**
1. Create `src/phx_home_analysis/services/cost_estimation/` directory
2. Create `rate_provider.py` with RateProvider class
3. Implement rate caching (7-day TTL)
4. Add initial rate values (manual entry)

**Commands:**
```bash
# Create directory
mkdir -p src/phx_home_analysis/services/cost_estimation

# Create __init__.py
touch src/phx_home_analysis/services/cost_estimation/__init__.py

# Create rate_provider.py
# (Use implementation-spec.md Wave 2.1 code)

# Test rate provider
python -c "
from src.phx_home_analysis.services.cost_estimation.rate_provider import RateProvider
rp = RateProvider()
print('Mortgage rates:', rp.get_mortgage_rates())
print('Insurance rates:', rp.get_insurance_rates())
print('Utility rates:', rp.get_utility_rates())
"
```

**Exit Criteria:**
- [ ] RateProvider class created
- [ ] Caching works (7-day TTL)
- [ ] All three rate types available
- [ ] Manual test successful

**Verification:**
```bash
# Verify cache file created
ls -lh src/phx_home_analysis/services/cost_estimation/rate_cache.json

# Check cache contents
cat src/phx_home_analysis/services/cost_estimation/rate_cache.json
```

**Rollback:** Delete `cost_estimation/` directory

---

### Session 2.2: Component Calculators (3-4 hours)

**Entry Criteria:**
- Session 2.1 complete
- Rate provider functional

**Tasks:**
1. Create `calculators.py` with 6 calculator classes
2. Implement MortgageCalculator, InsuranceCalculator, etc.
3. Create unit tests for each calculator

**Commands:**
```bash
# Create calculators.py
# (Use implementation-spec.md Wave 2.2 code - not shown above, but follows pattern)

# Create tests
mkdir -p tests/services/cost_estimation
touch tests/services/cost_estimation/__init__.py
# Create test_calculators.py

# Run tests
pytest tests/services/cost_estimation/test_calculators.py -v
```

**Exit Criteria:**
- [ ] All 6 calculators implemented
- [ ] Unit tests pass for each
- [ ] Edge cases handled (0 values, None values)

**Verification:**
```python
# Manual calculator tests
from src.phx_home_analysis.services.cost_estimation.calculators import MortgageCalculator

calc = MortgageCalculator(interest_rate=0.07, term_years=30)
monthly = calc.calculate(price=450000, down_payment=50000)
print(f"Monthly mortgage: ${monthly:.2f}")  # Should be ~$2,662
```

**Rollback:** Delete `calculators.py` and test files

---

### Session 2.3: Cost Estimator Integration (3-4 hours)

**Entry Criteria:**
- Sessions 2.1, 2.2 complete
- All calculators tested

**Tasks:**
1. Create `estimator.py` with CostEstimator class
2. Integrate all calculators
3. Add MonthlyCostEstimate dataclass
4. Create CostEfficiencyScorer strategy

**Commands:**
```bash
# Create estimator.py
# Create CostEfficiencyScorer in strategies/systems.py

# Update scoring_weights.py (Section B: 160→180)
# Pool: 30→20, CostEfficiency: NEW 40

# Test integration
python -c "
from src.phx_home_analysis.services.cost_estimation.estimator import CostEstimator
from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository

repo = CsvPropertyRepository('data/phx_homes.csv')
props = repo.find_all()

estimator = CostEstimator()
for prop in props[:3]:
    estimate = estimator.estimate(prop)
    print(f'{prop.short_address}: ${estimate.total:.2f}/month')
"
```

**Exit Criteria:**
- [ ] CostEstimator aggregates all components
- [ ] MonthlyCostEstimate dataclass complete
- [ ] CostEfficiencyScorer added to scoring engine
- [ ] Section B weights updated (180 pts total)

**Verification:**
```bash
# Run full scoring pipeline
python scripts/phx_home_analyzer.py --limit 5

# Check that cost efficiency scores appear in output
```

**Rollback:**
```bash
# Restore scoring_weights.py
git checkout src/phx_home_analysis/config/scoring_weights.py

# Delete cost estimation files
rm -rf src/phx_home_analysis/services/cost_estimation/
```

---

### Session 2.4: Deal Sheets Cost Display (2-3 hours)

**Entry Criteria:**
- Sessions 2.1-2.3 complete
- Cost estimation working

**Tasks:**
1. Update deal sheets renderer to display monthly costs
2. Add $4k warning badge
3. Add cost breakdown section
4. Generate sample deal sheets

**Commands:**
```bash
# Update renderer.py
# Add render_cost_section() function

# Add CSS for cost warning badge

# Generate deal sheets
python -m scripts.deal_sheets --limit 5

# Open samples in browser
open deal_sheets/*.html
```

**Exit Criteria:**
- [ ] Monthly cost displayed in deal sheets
- [ ] $4k warning badge appears when total >$4k
- [ ] Cost breakdown shows all 6 components
- [ ] Visual styling matches design

**Verification:**
- Manually inspect deal sheets for properties with >$4k/month
- Verify warning badge displays
- Check cost breakdown accuracy against manual calculation

**Rollback:**
```bash
git checkout scripts/deal_sheets/
```

---

### Wave 2 Summary

**Total Sessions:** 4 (10-14 hours)
**Pause Points:** After sessions 2.1, 2.2, 2.3
**Critical Path:** 2.1 → 2.2 → 2.3 → 2.4

**Prerequisites for Wave 3:**
- [ ] Cost estimation module complete
- [ ] CostEfficiencyScorer integrated
- [ ] Deal sheets display costs correctly

---

## Wave 3: Data Validation Layer

### Session 3.1: Pydantic Schemas (3-4 hours)

**Entry Criteria:**
- Wave 0 complete (can run parallel to Wave 1-2)
- Understanding of Property entity structure

**Tasks:**
1. Create `src/phx_home_analysis/validation/schemas.py`
2. Define PropertyData Pydantic model
3. Add validators for cross-field checks
4. Create unit tests

**Commands:**
```bash
# Create schemas.py
# (Follow PropertyData model structure)

# Create tests
touch tests/validation/test_schemas.py

# Run tests
pytest tests/validation/test_schemas.py -v
```

**Exit Criteria:**
- [ ] PropertyData model validates all fields
- [ ] Type enforcement works (int, float, enums)
- [ ] Range validation works (beds >= 0, year_built <= 2025)
- [ ] Cross-field checks work (pool_age requires has_pool)

**Verification:**
```python
# Test validation
from src.phx_home_analysis.validation.schemas import PropertyData

# Valid data
valid = PropertyData(
    address="123 Main St",
    beds=4,
    baths=2.5,
    lot_sqft=8000,
    year_built=2010
)
print("✓ Valid data accepted")

# Invalid data (should raise ValidationError)
try:
    invalid = PropertyData(address="123 Main St", beds=-1, baths=2)
    assert False, "Should have raised ValidationError"
except Exception as e:
    print(f"✓ Invalid data rejected: {e}")
```

**Rollback:** Delete `validation/schemas.py`

---

### Session 3.2: Repository Integration (2-3 hours)

**Entry Criteria:**
- Session 3.1 complete
- Pydantic schemas working

**Tasks:**
1. Update `csv_repository.py` to validate on load
2. Update `json_repository.py` to validate on load
3. Add error handling for validation failures
4. Test with actual data files

**Commands:**
```bash
# Update repositories
# Add validation in _load() methods

# Test with real data
python -c "
from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository

repo = CsvPropertyRepository('data/phx_homes.csv')
props = repo.find_all()
print(f'Loaded {len(props)} properties (validation successful)')
"
```

**Exit Criteria:**
- [ ] CSV repository validates on load
- [ ] JSON repository validates on load
- [ ] Validation errors logged, not crashed
- [ ] Real data loads successfully

**Verification:**
```bash
# Run full pipeline with validation
python scripts/phx_home_analyzer.py --validate

# Check logs for validation warnings
grep -i "validation" logs/*.log
```

**Rollback:**
```bash
git checkout src/phx_home_analysis/repositories/
```

---

### Wave 3 Summary

**Total Sessions:** 2 (5-7 hours)
**Pause Points:** After session 3.1
**Critical Path:** 3.1 → 3.2

**Prerequisites for Wave 4:**
- [ ] Pydantic validation working
- [ ] Repositories integrated
- [ ] Validation errors handled gracefully

---

## Wave 4: AI-Assisted Triage

### Session 4.1: Field Inferencer (4-5 hours)

**Entry Criteria:**
- Wave 3 complete
- Claude API key configured
- Understanding of field inference requirements

**Tasks:**
1. Create `src/phx_home_analysis/services/ai_enrichment/field_inferencer.py`
2. Implement triage tagging system
3. Create prompt templates for common field types
4. Add confidence scoring

**Commands:**
```bash
# Create directory
mkdir -p src/phx_home_analysis/services/ai_enrichment

# Create field_inferencer.py
# Implement FieldInferencer class

# Test on sample missing field
python -c "
from src.phx_home_analysis.services.ai_enrichment.field_inferencer import FieldInferencer

inferencer = FieldInferencer()
result = inferencer.infer_field(
    address='123 Main St, Phoenix, AZ',
    field_name='orientation',
    context={'has_street_view': True}
)
print(f'Inferred: {result.inferred_value}, Confidence: {result.confidence}')
"
```

**Exit Criteria:**
- [ ] FieldInferencer class created
- [ ] Triage tagging works
- [ ] Prompt templates defined
- [ ] Confidence scoring implemented
- [ ] Claude Haiku integration tested

**Verification:**
- Run inference on 3-5 properties with missing fields
- Verify confidence scores reasonable (high/medium/low)
- Check cost (<$0.01 per inference with Haiku)

**Rollback:** Delete `ai_enrichment/` directory

---

### Session 4.2: Integration & Testing (2-3 hours)

**Entry Criteria:**
- Session 4.1 complete
- Field inferencer working

**Tasks:**
1. Integrate with validation pipeline
2. Create workflow: validation fail → triage tag → AI inference
3. Test on properties with missing critical fields
4. Document inference results

**Commands:**
```bash
# Run enrichment with AI triage
python scripts/enrich_properties.py --ai-triage --limit 10

# Review inference results
cat data/ai_inferences.json

# Verify quality improvement
python scripts/quality_check.py
```

**Exit Criteria:**
- [ ] AI triage integrated into pipeline
- [ ] Inference results saved to data file
- [ ] Quality metrics improved (measure vs baseline)
- [ ] Cost tracking functional

**Verification:**
```bash
# Compare quality before/after
python scripts/quality_baseline.py  # Re-run to see improvement
```

**Rollback:**
```bash
git checkout src/phx_home_analysis/services/
rm data/ai_inferences.json
```

---

### Wave 4 Summary

**Total Sessions:** 2 (6-8 hours)
**Pause Points:** NONE (complete Wave 4 atomically)
**Critical Path:** 4.1 → 4.2 (sequential)

**Prerequisites for Wave 5:**
- [ ] Field inferencer working
- [ ] AI triage integrated
- [ ] Quality improvement measurable

---

## Wave 5: Quality Metrics & Lineage

### Session 5.1: Lineage Tracking (3-4 hours)

**Entry Criteria:**
- Waves 3, 4 complete
- Understanding of data sources

**Tasks:**
1. Create `data/field_lineage.json` structure
2. Update repositories to track lineage on write
3. Add FieldLineage dataclass to domain
4. Implement lineage display in deal sheets

**Commands:**
```bash
# Create lineage tracking module
# Update repositories to populate lineage

# Run pipeline to generate lineage data
python scripts/phx_home_analyzer.py

# Inspect lineage
cat data/field_lineage.json | jq '.[] | select(.address == "123 Main St")'
```

**Exit Criteria:**
- [ ] Lineage tracked for all fields
- [ ] Source attribution correct (csv/api/manual/ai_inference)
- [ ] Confidence levels assigned
- [ ] Timestamps recorded

**Verification:**
```python
# Verify lineage structure
import json
lineage = json.load(open('data/field_lineage.json'))
sample = lineage[0]
assert 'address' in sample
assert 'lot_sqft' in sample
assert sample['lot_sqft']['source'] in ['csv', 'api', 'manual', 'ai_inference', 'default']
```

**Rollback:** Delete `data/field_lineage.json`, restore repositories

---

### Session 5.2: Quality Calculator & CI Gate (2-3 hours)

**Entry Criteria:**
- Session 5.1 complete
- Lineage data populated

**Tasks:**
1. Create `scripts/quality_check.py`
2. Implement quality score calculator
3. Add CI/CD quality gate (fail if <95%)
4. Generate quality dashboard

**Commands:**
```bash
# Create quality_check.py
# Calculate: (Completeness × 0.6) + (High Conf % × 0.4)

# Run quality check
python scripts/quality_check.py --report

# Test CI gate
python scripts/quality_check.py --ci-gate
# Should exit 0 if >=95%, exit 1 if <95%
```

**Exit Criteria:**
- [ ] Quality score calculated correctly
- [ ] CI gate functional (exit codes correct)
- [ ] Quality dashboard generated
- [ ] Target 95% achieved (or gap documented)

**Verification:**
```bash
# Compare to baseline
diff data/quality_baseline.json data/quality_current.json

# Should show improvement in completeness and confidence
```

**Rollback:** Delete `scripts/quality_check.py`

---

### Wave 5 Summary

**Total Sessions:** 2 (5-7 hours)
**Pause Points:** After session 5.1
**Critical Path:** 5.1 → 5.2

**Prerequisites for Wave 6:**
- [ ] Lineage tracking operational
- [ ] Quality metrics at or near 95%
- [ ] CI gate functional

---

## Wave 6: Documentation & Integration

### Session 6.1: Update Skill Files (2-3 hours)

**Entry Criteria:**
- All prior waves complete
- System functional end-to-end

**Tasks:**
1. Update `.claude/skills/kill-switch/SKILL.md`
2. Update `.claude/skills/scoring/SKILL.md`
3. Create `.claude/skills/cost-efficiency/SKILL.md`
4. Update `CLAUDE.md` with new weights

**Commands:**
```bash
# Update kill-switch skill
# Replace "all must pass" with weighted threshold documentation

# Update scoring skill
# Add CostEfficiencyScorer (40 pts)
# Update Section B total (180 pts)

# Create new cost-efficiency skill
touch .claude/skills/cost-efficiency/SKILL.md
# Document cost estimation module usage

# Update project CLAUDE.md
# Update scoring system table
```

**Exit Criteria:**
- [ ] All skill files updated
- [ ] New cost-efficiency skill created
- [ ] CLAUDE.md reflects new weights
- [ ] Examples updated with new logic

**Verification:**
```bash
# Verify skill files parse correctly
rg "Section B.*180" .claude/skills/scoring/SKILL.md
rg "weighted threshold" .claude/skills/kill-switch/SKILL.md
```

**Rollback:**
```bash
git checkout .claude/
```

---

### Session 6.2: Integration Tests (3-4 hours)

**Entry Criteria:**
- Session 6.1 complete
- Documentation updated

**Tasks:**
1. Create `tests/integration/test_kill_switch_pipeline.py`
2. Create `tests/integration/test_cost_scoring_integration.py`
3. Create `tests/integration/test_quality_validation.py`
4. Run full integration suite

**Commands:**
```bash
# Create integration tests
mkdir -p tests/integration

# Test kill-switch pipeline
pytest tests/integration/test_kill_switch_pipeline.py -v

# Test cost scoring integration
pytest tests/integration/test_cost_scoring_integration.py -v

# Test quality validation
pytest tests/integration/test_quality_validation.py -v

# Run full suite
pytest tests/ -v --tb=short
```

**Exit Criteria:**
- [ ] All integration tests pass
- [ ] End-to-end workflow verified
- [ ] No regressions detected

**Verification:**
```bash
# Compare to regression baseline
pytest tests/regression/test_baseline.py -v

# Should show intentional changes only (tier assignments due to new weights)
```

**Rollback:** Delete `tests/integration/` directory

---

### Session 6.3: End-to-End Verification (2-3 hours)

**Entry Criteria:**
- Sessions 6.1, 6.2 complete
- All tests passing

**Tasks:**
1. Run full pipeline on all properties
2. Generate all deal sheets
3. Compare before/after metrics
4. Document improvements
5. Final commit

**Commands:**
```bash
# Run full analysis
python scripts/phx_home_analyzer.py --all

# Generate all deal sheets
python -m scripts.deal_sheets --all

# Generate comparison report
python scripts/compare_before_after.py

# Review improvements
cat reports/improvement_summary.txt
```

**Exit Criteria:**
- [ ] All 25 properties processed successfully
- [ ] Deal sheets generated for all
- [ ] Quality score >=95% (or documented gap)
- [ ] Tier assignments validated
- [ ] No critical bugs

**Final Verification Checklist:**
- [ ] Kill-switch verdicts correct (PASS/WARNING/FAIL)
- [ ] [H]/[S] markers displaying
- [ ] Severity scores accurate
- [ ] Monthly costs displayed
- [ ] $4k warnings showing when applicable
- [ ] Cost efficiency scores in breakdown
- [ ] Section B totals 180 pts (not 160)
- [ ] Data quality improved vs baseline
- [ ] Field lineage tracked
- [ ] All tests passing

**Final Commit:**
```bash
# Stage all changes
git add .

# Commit with detailed message
git commit -m "Complete scoring system improvements (Waves 0-6)

- Implement weighted threshold kill-switch (3 HARD, 4 SOFT)
- Add cost estimation module (40-pt scoring criterion)
- Establish data quality validation (>95% target)
- Integrate AI-assisted triage for missing fields
- Add field lineage tracking
- Update documentation and skills

Closes #[issue-number]"

# Push to remote
git push origin main
```

**Rollback (Complete):**
```bash
# Nuclear option: revert all commits
git log --oneline  # Find commit before Wave 0
git revert --no-commit <commit-hash>..HEAD
git commit -m "Revert scoring improvements"
```

---

### Wave 6 Summary

**Total Sessions:** 3 (7-10 hours)
**Pause Points:** After sessions 6.1, 6.2
**Critical Path:** 6.1 → 6.2 → 6.3

**Final Deliverables:**
- [ ] All code changes committed
- [ ] Documentation updated
- [ ] Tests passing (unit + integration + regression)
- [ ] Quality metrics at or near 95%
- [ ] System functional end-to-end

---

## Cross-Session Continuity

### Starting a New Session

**Before starting any session:**

1. **Check wave status:**
```bash
# Review last session's progress
cat docs/specs/phase-execution-guide.md | grep "Exit Criteria" -A 10

# Verify which files were modified
git status
```

2. **Review entry criteria:**
- Read entry criteria for planned session
- Verify prerequisites met
- Check for any blockers

3. **Load context:**
- Read relevant implementation spec sections
- Review architecture diagram for context
- Check related skill files if applicable

### During Session

**Maintain progress tracking:**

```bash
# Create session log
echo "Session: Wave X.Y - $(date)" >> docs/session_log.txt
echo "Tasks: [list tasks]" >> docs/session_log.txt

# Log progress periodically
echo "✓ Completed: [task]" >> docs/session_log.txt
```

### Ending a Session Mid-Wave

**If pausing mid-wave:**

1. **Complete current task to logical checkpoint**
2. **Run tests to ensure stability:**
```bash
pytest tests/ -v --tb=short
```

3. **Commit work in progress:**
```bash
git add .
git commit -m "WIP: Wave X.Y partial - [what was completed]

Next: [what remains]"
```

4. **Document stopping point:**
```bash
echo "STOPPED: Wave X.Y after [task]" >> docs/session_log.txt
echo "NEXT: Resume with [next task]" >> docs/session_log.txt
```

5. **Update checklist:**
Mark completed items in relevant wave checklist

### Resuming After Pause

**To resume:**

1. **Review session log:**
```bash
tail -20 docs/session_log.txt
```

2. **Check git status:**
```bash
git log --oneline -5
git diff HEAD
```

3. **Verify tests still passing:**
```bash
pytest tests/ -v
```

4. **Continue from last checkpoint**

---

## Troubleshooting Guide

### Common Issues

#### Issue: Tests Failing After Code Change

**Symptoms:** Pytest exits with errors after modifying code

**Solution:**
```bash
# Identify failing test
pytest tests/ -v --tb=short

# Check if regression
pytest tests/regression/test_baseline.py -v

# If intentional change, update test expectations
# If unintentional, use git diff to review changes

# Rollback if needed
git checkout <file>
```

#### Issue: Import Errors

**Symptoms:** `ModuleNotFoundError` when running scripts

**Solution:**
```bash
# Verify PYTHONPATH
echo $PYTHONPATH

# Add project root if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use uv run
uv run python scripts/[script].py
```

#### Issue: Quality Score Not Improving

**Symptoms:** Quality check shows <95% after Wave 5

**Solution:**
1. Run quality report to identify gaps:
```bash
python scripts/quality_check.py --report --verbose
```

2. Check which fields are incomplete:
```bash
python scripts/quality_baseline.py  # Compare to original
```

3. Focus AI triage on low-completeness fields:
```bash
python scripts/enrich_properties.py --ai-triage --fields lot_sqft,orientation
```

#### Issue: Deal Sheets Not Displaying Correctly

**Symptoms:** HTML rendering broken or missing sections

**Solution:**
1. Check for template syntax errors
2. Verify data being passed to renderer
3. Test with minimal property:
```python
from scripts.deal_sheets.renderer import render_property_sheet
test_prop = {
    'address': '123 Test St',
    'beds': 4,
    'baths': 2,
    # ... minimal fields
}
html = render_property_sheet(test_prop)
print(html[:500])  # Check first 500 chars
```

#### Issue: Cost Estimation Producing Unrealistic Values

**Symptoms:** Monthly costs wildly incorrect (e.g., $10k/month for $400k home)

**Solution:**
1. Verify rate provider values:
```python
from src.phx_home_analysis.services.cost_estimation.rate_provider import RateProvider
rp = RateProvider()
rates = rp.get_mortgage_rates()
print(f"30yr rate: {rates.thirty_year_fixed}")  # Should be ~0.07 (7%)
```

2. Check calculator logic:
```python
from src.phx_home_analysis.services.cost_estimation.calculators import MortgageCalculator
calc = MortgageCalculator(interest_rate=0.07, term_years=30)
monthly = calc.calculate(price=400000, down_payment=50000)
print(f"${monthly:.2f}")  # Should be ~$2,330
```

3. Manually verify formula if needed

---

## Success Metrics

### After Wave 0:
- [ ] Quality baseline established (<90% → measure actual)
- [ ] Data normalizer functional
- [ ] Regression baseline captured

### After Wave 1:
- [ ] Kill-switch verdicts displaying (PASS/WARNING/FAIL)
- [ ] [H]/[S] markers distinguishing criteria
- [ ] Severity scores accurate

### After Wave 2:
- [ ] Monthly costs displayed in deal sheets
- [ ] $4k warnings appearing when applicable
- [ ] Cost efficiency contributing to scores (40 pts)

### After Wave 3:
- [ ] Pydantic validation catching errors
- [ ] Invalid data rejected gracefully
- [ ] Validation errors logged

### After Wave 4:
- [ ] AI inference functional for missing fields
- [ ] Confidence scores assigned
- [ ] Cost per inference <$0.01

### After Wave 5:
- [ ] Quality score >=95% (or documented gap <2%)
- [ ] Field lineage tracked for all properties
- [ ] CI gate functional

### After Wave 6:
- [ ] All documentation updated
- [ ] All tests passing (unit + integration + regression)
- [ ] End-to-end workflow functional

---

## Document Version Control

- v1.0 (2025-12-01): Initial phase execution guide
- Next Review: After Wave 3 completion

**Related Documents:**
- `docs/architecture/scoring-improvement-architecture.md` - System architecture
- `docs/specs/implementation-spec.md` - Detailed implementation guide
- `docs/specs/reference-index.md` - Research document catalog

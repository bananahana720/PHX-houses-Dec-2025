# Wave 2: Cost Estimation Module

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

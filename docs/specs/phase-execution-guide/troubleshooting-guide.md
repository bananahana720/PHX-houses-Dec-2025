# Troubleshooting Guide

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

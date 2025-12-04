# Rate Data & External Sources

### 9. Mortgage Rate Sources

**Provider:** Various financial institutions
**Update Frequency:** Weekly (7-day cache in RateProvider)
**Current Rates (2025-12-01):** To be fetched

**Sources:**
- Freddie Mac Primary Mortgage Market Survey
- Bankrate.com national averages
- Local AZ lenders (Chase, Wells Fargo, PNC)

**Data Structure:**
```python
MortgageRates(
    thirty_year_fixed=0.070,  # 7.0% APR
    fifteen_year_fixed=0.065,  # 6.5% APR
    source='Freddie Mac PMMS',
    last_updated='2025-12-01T10:00:00Z'
)
```

**Usage:**
- Wave 2: RateProvider.get_mortgage_rates()
- Monthly update: Refresh rate cache manually if needed

---

### 10. Homeowner's Insurance Rates (Arizona)

**Provider:** Insurance industry averages
**Update Frequency:** Quarterly
**Current Rates (2025 estimates):**

**Base Annual Premiums:**
- Low end: $1,500/year ($125/month)
- High end: $2,500/year ($208/month)
- Average: $2,000/year ($167/month)

**Adjustment Factors:**
- Sqft: +$0.50 per sqft above 1,500
- Pool: +$300/year ($25/month)
- Year built <1980: +$200-400/year
- Replacement cost value: Base × (property_value / 300,000)

**Sources:**
- Insurance Information Institute
- Arizona Department of Insurance
- Local insurers (State Farm, Allstate, USAA)

**Usage:**
- Wave 2: InsuranceCalculator.calculate()

---

### 11. Utility Rates (SRP/APS)

**Providers:** SRP (Salt River Project), APS (Arizona Public Service)
**Update Frequency:** Annual rate adjustments (typically May 1)

**Electric Rates (2025):**
- Summer (May-Oct): $0.14/kWh
- Winter (Nov-Apr): $0.11/kWh
- Base charge: $15/month
- Typical usage: 1,200-2,500 kWh/month (depends on sqft, cooling)

**Water Rates:**
- Base: $80-120/month (typical single-family)
- Tiered pricing above baseline

**Gas Rates:**
- Base: $30-80/month (if applicable)
- Minimal usage in AZ (heating less critical)

**Sources:**
- SRP.net rate schedules
- APS.com rate schedules
- Arizona Corporation Commission filings

**Usage:**
- Wave 2: UtilityCalculator.calculate()

**Estimation Formula:**
```python
# Electric
monthly_kwh = sqft × cooling_factor × season_factor
cooling_factor = 1.0 + (0.3 if has_pool else 0.0)
season_factor = 1.8 (summer) | 1.0 (winter)
monthly_cost = (monthly_kwh × rate_per_kwh) + base_charge

# Example: 2,000 sqft, no pool, summer
monthly_kwh = 2000 × 1.0 × 1.8 = 3,600 kWh
monthly_cost = (3600 × 0.14) + 15 = $519/month
```

---

# Kill-Switch Test Coverage

### Test Classes Identified: 10

1. **TestNoHoaKillSwitch** (7 tests)
   - Passes when hoa_fee = 0
   - Fails when hoa_fee > 0
   - Handles None values
   - Boundary cases

2. **TestCitySewerKillSwitch** (7 tests)
   - Passes for city sewer
   - Fails for septic/private
   - Severity scoring

3. **TestMinGarageKillSwitch** (7 tests)
   - Passes for garage >= 2
   - Fails for garage < 2
   - Boundary at garage=2

4. **TestMinBedroomsKillSwitch** (7 tests)
   - Passes for beds >= 4
   - Fails for beds < 4
   - Boundary at beds=4

5. **TestMinBathroomsKillSwitch** (8 tests)
   - Passes for baths >= 2.0
   - Fails for baths < 2.0
   - Boundary at baths=2.0

6. **TestLotSizeKillSwitch** (11 tests)
   - Passes for 7000-15000 sqft
   - Fails for <7000 or >15000 sqft
   - Exact boundary testing (6999 vs 7000)

7. **TestNoNewBuildKillSwitch** (8 tests)
   - Passes for year < 2024
   - Fails for year >= 2024
   - Boundary at year=2024

8. **TestKillSwitchFilter** (13 tests)
   - Integration of all criteria
   - HARD failures stop filter
   - SOFT failures accumulate severity

9. **TestKillSwitchEdgeCases** (8 tests)
   - None/missing data handling
   - Type conversions
   - Empty collections

10. **TestSeverityThresholdOOP** (Multiple tests)
    - Severity calculation (2.5, 1.5, etc.)
    - Threshold accumulation
    - HARD vs SOFT criteria distinction

**Total Kill-Switch Tests: 75+ (comprehensive)**

---

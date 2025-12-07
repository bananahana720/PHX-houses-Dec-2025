# Kill-Switch Architecture

## Kill-Switch Criteria (5 HARD + 4 SOFT)

The kill-switch system uses two types of criteria to filter properties based on buyer requirements:

### HARD Criteria (5 - Instant Fail)

HARD criteria are non-negotiable requirements. If ANY HARD criterion fails, the property is immediately marked as FAIL without further evaluation.

| Criterion | Requirement | Implementation | PRD Reference |
|-----------|-------------|----------------|---------------|
| HOA | Must be $0 | `property.hoa_fee == 0` | FR9-FR11 |
| Solar Lease | Must NOT have solar lease | `property.solar_lease != True` | FR9 |
| Bedrooms | >= 4 | `property.beds >= 4` | FR9-FR11 |
| Bathrooms | >= 2 | `property.baths >= 2.0` | FR9-FR11 |
| House SQFT | > 1800 | `property.sqft > 1800` | FR9 (NEW) |

### SOFT Criteria (4 - Severity Accumulation)

SOFT criteria are flexible preferences. Each failed SOFT criterion adds a severity weight to a running total. Properties FAIL if total severity >= 3.0, receive WARNING if severity >= 1.5.

| Criterion | Requirement | Severity Weight | Implementation | PRD Reference |
|-----------|-------------|-----------------|----------------|---------------|
| Sewer | City only | 2.5 | `property.sewer_type == SewerType.CITY` | FR9 (upgraded) |
| Year Built | <= 2023 | 2.0 | `property.year_built <= 2023` | FR9 |
| Garage | >= 2 indoor spaces | 1.5 | `property.garage_spaces >= 2 and indoor` | FR9 (clarified) |
| Lot Size | 7k-15k sqft | 1.0 | `7000 <= property.lot_sqft <= 15000` | FR9 (upgraded) |

## Severity Accumulation System

SOFT criteria use weighted severity scores instead of instant failure. The system accumulates severity points for each failed SOFT criterion and determines the verdict based on threshold rules.

### Severity Weights

Each SOFT criterion contributes a specific severity score when its requirement is not met:

| Criterion | Condition | Severity |
|-----------|-----------|----------|
| Sewer | Not city (septic/unknown) | 2.5 |
| Year Built | >2023 (new construction) | 2.0 |
| Garage | <2 indoor spaces | 1.5 |
| Lot Size | <7k or >15k sqft | 1.0 |

### Verdict Thresholds

The final verdict is determined by the accumulated severity score:

- **FAIL**: severity >= 3.0 (too many issues accumulated)
- **WARNING**: severity >= 1.5 and < 3.0 (approaching fail threshold)
- **PASS**: severity < 1.5 (minor or no issues)

### Example Scenarios

#### Scenario 1: Septic + 1-car garage = FAIL
```
Septic tank (2.5) + 1-car garage (1.5) = 4.0 severity
Verdict: FAIL (severity >= 3.0)
```

#### Scenario 2: Septic only = WARNING
```
Septic tank (2.5)
Verdict: WARNING (1.5 <= severity < 3.0)
```

#### Scenario 3: Small lot + 1-car garage = WARNING
```
Small lot (1.0) + 1-car garage (1.5) = 2.5 severity
Verdict: WARNING (1.5 <= severity < 3.0)
```

#### Scenario 4: New build + 1-car garage = FAIL
```
New build 2024 (2.0) + 1-car garage (1.5) = 3.5 severity
Verdict: FAIL (severity >= 3.0)
```

#### Scenario 5: Small lot only = PASS
```
Small lot (1.0)
Verdict: PASS (severity < 1.5)
```

## Verdict Logic

The filter evaluates properties in two phases:

### Phase 1: Check HARD Criteria

```python
# Check each HARD criterion - instant fail if any violated
has_hard_failure = False

if property.hoa_fee and property.hoa_fee > 0:
    has_hard_failure = True
    failed_criteria.append("hoa")

if property.solar_lease:
    has_hard_failure = True
    failed_criteria.append("solar_lease")

if property.beds is None or property.beds < 4:
    has_hard_failure = True
    failed_criteria.append("beds")

if property.baths is None or property.baths < 2.0:
    has_hard_failure = True
    failed_criteria.append("baths")

if property.sqft is None or property.sqft <= 1800:
    has_hard_failure = True
    failed_criteria.append("sqft")
```

### Phase 2: Accumulate SOFT Severity

```python
# Accumulate severity from SOFT criteria
severity_score = 0.0

if property.sewer_type != SewerType.CITY:
    severity_score += 2.5
    failed_criteria.append("sewer")

if property.year_built and property.year_built > 2023:
    severity_score += 2.0
    failed_criteria.append("year")

if property.garage_spaces is None or property.garage_spaces < 2:
    severity_score += 1.5
    failed_criteria.append("garage")

if property.lot_sqft is None or property.lot_sqft < 7000 or property.lot_sqft > 15000:
    severity_score += 1.0
    failed_criteria.append("lot")
```

### Phase 3: Determine Final Verdict

```python
# Calculate verdict
if has_hard_failure:
    verdict = KillSwitchVerdict.FAIL
elif severity_score >= 3.0:
    verdict = KillSwitchVerdict.FAIL
elif severity_score >= 1.5:
    verdict = KillSwitchVerdict.WARNING
else:
    verdict = KillSwitchVerdict.PASS

return KillSwitchResult(
    verdict=verdict,
    failed_criteria=failed_criteria,
    severity_score=severity_score,
    details=self._build_details(property, failed_criteria)
)
```

## Implementation Reference

- **Constants**: `src/phx_home_analysis/config/constants.py:45-75`
- **Filter Logic**: `src/phx_home_analysis/services/kill_switch/filter.py:92-142`
- **Severity Thresholds**: FAIL >= 3.0, WARNING >= 1.5 (defined in `config/constants.py`)

---

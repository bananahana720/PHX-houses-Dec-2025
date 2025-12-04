# Kill-Switch Architecture

### All 7 Criteria Are HARD (per PRD)

| Criterion | Requirement | Implementation | PRD Reference |
|-----------|-------------|----------------|---------------|
| HOA | Must be $0 | `property.hoa_fee == 0` | FR9-FR11 |
| Bedrooms | >= 4 | `property.beds >= 4` | FR9-FR11 |
| Bathrooms | >= 2 | `property.baths >= 2.0` | FR9-FR11 |
| House SQFT | > 1800 | `property.sqft > 1800` | FR9 (NEW) |
| Lot Size | > 8000 | `property.lot_sqft > 8000` | FR9 (upgraded) |
| Garage | Indoor required | `property.garage_spaces >= 1` | FR9 (clarified) |
| Sewer | City only | `property.sewer_type == SewerType.CITY` | FR9 (upgraded) |

### Verdict Logic

```python
def evaluate(self, property: Property) -> KillSwitchResult:
    """Evaluate property against all 7 HARD criteria."""

    failed_criteria = []

    # Check each criterion
    if property.hoa_fee and property.hoa_fee > 0:
        failed_criteria.append("hoa")

    if property.beds is None or property.beds < 4:
        failed_criteria.append("beds")

    if property.baths is None or property.baths < 2.0:
        failed_criteria.append("baths")

    if property.sqft is None or property.sqft <= 1800:
        failed_criteria.append("sqft")

    if property.lot_sqft is None or property.lot_sqft <= 8000:
        failed_criteria.append("lot")

    if property.garage_spaces is None or property.garage_spaces < 1:
        failed_criteria.append("garage")

    if property.sewer_type != SewerType.CITY:
        failed_criteria.append("sewer")

    # Determine verdict
    if len(failed_criteria) == 0:
        verdict = KillSwitchVerdict.PASS
    else:
        verdict = KillSwitchVerdict.FAIL

    return KillSwitchResult(
        verdict=verdict,
        failed_criteria=failed_criteria,
        details=self._build_details(property, failed_criteria)
    )
```

### Soft Severity System (Retained for Future Use)

While all PRD criteria are HARD, the soft severity system remains available for future flexibility:

```python
class SoftSeverityEvaluator:
    """Evaluate soft criteria with severity accumulation (future use)."""

    SEVERITY_FAIL_THRESHOLD = 3.0
    SEVERITY_WARNING_THRESHOLD = 1.5

    soft_criteria = {
        # Currently unused per PRD, but available for future
        # 'example_soft': {'threshold': 100, 'severity': 1.5}
    }

    def evaluate(self, property: Property) -> float:
        total_severity = 0.0
        # Add soft criteria evaluations here if needed
        return total_severity
```

---

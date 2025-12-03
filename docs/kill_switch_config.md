# Kill Switch Configuration

## Overview

The kill switch system now supports externalized configuration via YAML files. This allows you to customize buyer criteria without modifying Python code.

## Configuration File

Location: `config/buyer_criteria.yaml`

### Structure

```yaml
hard_criteria:
  hoa_fee: 0        # Must be zero (no HOA)
  min_beds: 4       # Minimum bedrooms
  min_baths: 2      # Minimum bathrooms

soft_criteria:
  sewer_type:
    required: "city"
    severity: 2.5

  year_built:
    max: "current_year"  # Special token - uses datetime.now().year
    severity: 2.0

  garage_spaces:
    min: 2
    severity: 1.5

  lot_sqft:
    min: 7000
    max: 15000
    severity: 1.0

thresholds:
  severity_fail: 3.0      # Total severity >= this = FAIL
  severity_warning: 1.5   # Total severity >= this = WARNING
```

## Usage

### Using Default Criteria (Hardcoded)

```python
from scripts.lib.kill_switch import KillSwitchFilter

# Uses hardcoded defaults
filter = KillSwitchFilter()
verdict, severity, failures, results = filter.evaluate(property_data)
```

### Using Custom YAML Config

```python
from scripts.lib.kill_switch import KillSwitchFilter

# Load from YAML config
filter = KillSwitchFilter(config_path='config/buyer_criteria.yaml')
verdict, severity, failures, results = filter.evaluate(property_data)

# Print configuration summary
print(filter.get_summary())
```

### Backward Compatibility

The existing module-level functions continue to work without changes:

```python
from scripts.lib.kill_switch import evaluate_kill_switches, apply_kill_switch

# Old-style usage still works
verdict, severity, failures, results = evaluate_kill_switches(property_data)

# Property dataclass usage still works
prop = apply_kill_switch(prop)
```

## Severity System

### Hard Criteria
- **Instant fail** if not met
- No severity calculation
- Examples: HOA fees, minimum beds/baths

### Soft Criteria
- Each failure adds severity weight
- Total severity determines verdict:
  - `< 1.5`: PASS
  - `>= 1.5 and < 3.0`: WARNING
  - `>= 3.0`: FAIL

### Examples

| Failures | Severity | Verdict |
|----------|----------|---------|
| None | 0.0 | PASS |
| Garage only | 1.5 | WARNING |
| Garage + Lot size | 2.5 | WARNING |
| Sewer + Garage | 4.0 | FAIL |
| Sewer + Year built | 4.5 | FAIL |
| Any HARD criterion | N/A | FAIL |

## Testing

Run the test script to verify configuration:

```bash
python scripts/test_kill_switch_config.py
```

## Special Tokens

- `"current_year"`: Evaluates to `datetime.now().year` at runtime
- Useful for year_built criteria to avoid hardcoding the year

## Customization

To modify buyer criteria:

1. Edit `config/buyer_criteria.yaml`
2. Adjust hard criteria values (min_beds, min_baths, hoa_fee)
3. Adjust soft criteria requirements and severity weights
4. Adjust thresholds (severity_fail, severity_warning)
5. Save and re-run your analysis

No code changes required!

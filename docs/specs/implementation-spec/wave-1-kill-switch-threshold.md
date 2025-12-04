# Wave 1: Kill-Switch Threshold

**Priority:** P0
**Estimated Effort:** 6-8 hours
**Dependencies:** Wave 0 complete

### Objectives

1. Implement weighted severity threshold system
2. Distinguish HARD vs SOFT criteria
3. Update kill-switch filter orchestration
4. Add verdict badges to deal sheets

### 1.1 Update Kill-Switch Criteria Module

**File:** `scripts/lib/kill_switch.py` (MODIFY)

**Changes:**

1. Add severity constants
2. Add HARD/SOFT distinction to criteria
3. Implement weighted threshold logic
4. Update `KillSwitchResult` dataclass

**Implementation:**

```python
# Add after imports (line 28)
from typing import Literal

# Add severity constants (after line 29)
HARD_SEVERITY = float('inf')  # Instant fail

SEVERITY_WEIGHTS = {
    'septic': 2.5,
    'garage': 1.5,
    'lot_size': 1.0,
    'year_built': 2.0
}

THRESHOLD_FAIL = 3.0
THRESHOLD_WARNING = 1.5

# Replace KillSwitchResult dataclass (line 49-56)
@dataclass
class KillSwitchResult:
    """Result of evaluating kill switches (enhanced for weighted thresholds)."""

    # Individual criterion results
    name: str
    passed: bool
    description: str
    actual_value: Any = None
    criterion_type: Literal['HARD', 'SOFT'] = 'SOFT'
    severity: float = 0.0

    @property
    def is_hard_failure(self) -> bool:
        """Check if this is a HARD criterion failure."""
        return self.criterion_type == 'HARD' and not self.passed


@dataclass
class KillSwitchVerdict:
    """Overall verdict from evaluating all kill switches."""

    verdict: Literal['PASS', 'WARNING', 'FAIL']
    severity_score: float
    hard_failures: list[str]
    soft_failures: list[tuple[str, float]]  # (criterion, severity)
    warnings: list[str]
    all_results: list[KillSwitchResult]

    @property
    def is_failed(self) -> bool:
        return self.verdict == 'FAIL'

    @property
    def has_warnings(self) -> bool:
        return self.verdict == 'WARNING' or len(self.warnings) > 0


# Update KILL_SWITCH_CRITERIA (line 152-195)
KILL_SWITCH_CRITERIA = {
    # HARD CRITERIA (instant fail)
    "beds": {
        "field": "beds",
        "check": _check_beds,
        "description": "Minimum 4 bedrooms",
        "requirement": "At least 4 bedrooms",
        "type": "HARD",
        "severity": HARD_SEVERITY,
    },
    "baths": {
        "field": "baths",
        "check": _check_baths,
        "description": "Minimum 2 bathrooms",
        "requirement": "At least 2 bathrooms",
        "type": "HARD",
        "severity": HARD_SEVERITY,
    },
    "hoa": {
        "field": "hoa_fee",
        "check": _check_hoa,
        "description": "NO HOA fees allowed",
        "requirement": "Must be $0/month or None",
        "type": "HARD",
        "severity": HARD_SEVERITY,
    },

    # SOFT CRITERIA (weighted threshold)
    "sewer": {
        "field": "sewer_type",
        "check": _check_sewer,
        "description": "City sewer preferred",
        "requirement": "No septic systems (preferred)",
        "type": "SOFT",
        "severity": SEVERITY_WEIGHTS['septic'],
    },
    "garage": {
        "field": "garage_spaces",
        "check": _check_garage,
        "description": "Minimum 2-car garage preferred",
        "requirement": "At least 2 garage spaces (preferred)",
        "type": "SOFT",
        "severity": SEVERITY_WEIGHTS['garage'],
    },
    "lot_size": {
        "field": "lot_sqft",
        "check": _check_lot_size,
        "description": "Lot size 7,000-15,000 sqft preferred",
        "requirement": "Between 7,000 and 15,000 sqft (preferred)",
        "type": "SOFT",
        "severity": SEVERITY_WEIGHTS['lot_size'],
    },
    "year_built": {
        "field": "year_built",
        "check": _check_year_built,
        "description": "No new builds preferred (< 2024)",
        "requirement": "Built before 2024 (preferred)",
        "type": "SOFT",
        "severity": SEVERITY_WEIGHTS['year_built'],
    },
}
```

**Add new evaluation function with weighted threshold:**

```python
# Add after existing evaluate_kill_switches function (line 248)
def evaluate_kill_switches_weighted(
    data: Union[Dict[str, Any], "PropertyLike"],
) -> KillSwitchVerdict:
    """Evaluate kill switches using weighted threshold system.

    HARD criteria (Beds, Baths, HOA) cause instant failure.
    SOFT criteria (Septic, Garage, Lot, Year) accumulate severity points.

    Verdict logic:
    - Any HARD failure → FAIL
    - SOFT severity >= 3.0 → FAIL
    - SOFT severity >= 1.5 → WARNING
    - Otherwise → PASS

    Args:
        data: Property data as dict or object with attributes

    Returns:
        KillSwitchVerdict with detailed verdict information
    """
    hard_failures: list[str] = []
    soft_failures: list[tuple[str, float]] = []
    warnings: list[str] = []
    all_results: list[KillSwitchResult] = []
    severity_score = 0.0

    for name, criteria in KILL_SWITCH_CRITERIA.items():
        field_name = criteria["field"]

        # Get value from dict or object
        if isinstance(data, dict):
            value = data.get(field_name)
        else:
            value = getattr(data, field_name, None)

        # Evaluate criterion
        passed, actual_str = criteria["check"](value)

        result = KillSwitchResult(
            name=name,
            passed=passed,
            description=criteria["description"],
            actual_value=actual_str,
            criterion_type=criteria["type"],
            severity=criteria["severity"],
        )
        all_results.append(result)

        if not passed:
            if criteria["type"] == "HARD":
                # HARD failure - instant disqualification
                hard_failures.append(
                    f"[H] {name}: {criteria['description']} ({actual_str})"
                )
            else:
                # SOFT failure - accumulate severity
                severity_score += criteria["severity"]
                soft_failures.append((name, criteria["severity"]))

                failure_msg = (
                    f"[S] {name}: {criteria['description']} "
                    f"({actual_str}, severity {criteria['severity']})"
                )

                if severity_score >= THRESHOLD_FAIL:
                    hard_failures.append(failure_msg)  # Will cause FAIL
                elif severity_score >= THRESHOLD_WARNING:
                    warnings.append(failure_msg)  # WARNING status

    # Determine verdict
    if len(hard_failures) > 0:
        verdict = 'FAIL'
    elif severity_score >= THRESHOLD_FAIL:
        verdict = 'FAIL'
    elif severity_score >= THRESHOLD_WARNING:
        verdict = 'WARNING'
    else:
        verdict = 'PASS'

    return KillSwitchVerdict(
        verdict=verdict,
        severity_score=severity_score,
        hard_failures=hard_failures,
        soft_failures=soft_failures,
        warnings=warnings,
        all_results=all_results,
    )
```

**Backward compatibility wrapper:**

```python
# Update existing evaluate_kill_switches to use new logic (line 203-248)
def evaluate_kill_switches(
    data: Union[Dict[str, Any], "PropertyLike"],
) -> Tuple[bool, List[str], List[KillSwitchResult]]:
    """Evaluate all kill switches (backward compatible wrapper).

    This function maintains API compatibility with existing code while
    using the new weighted threshold system internally.

    Args:
        data: Property data as dict or object with attributes

    Returns:
        Tuple of:
        - passed: True if verdict is PASS (WARNING counts as passed)
        - failure_messages: List of failure messages
        - results: List of KillSwitchResult for detailed inspection
    """
    verdict = evaluate_kill_switches_weighted(data)

    # Backward compatibility:
    # - PASS → passed=True, failures=[]
    # - WARNING → passed=True, failures=warnings (soft failures)
    # - FAIL → passed=False, failures=hard_failures

    if verdict.verdict == 'PASS':
        return True, [], verdict.all_results
    elif verdict.verdict == 'WARNING':
        return True, verdict.warnings, verdict.all_results
    else:  # FAIL
        return False, verdict.hard_failures, verdict.all_results
```

**Unit Tests:**

**File:** `tests/services/kill_switch/test_weighted_threshold.py` (NEW)

```python
"""Unit tests for weighted threshold kill-switch logic."""

import pytest
from scripts.lib.kill_switch import (
    evaluate_kill_switches_weighted,
    THRESHOLD_FAIL,
    THRESHOLD_WARNING,
    SEVERITY_WEIGHTS,
)


class TestHardCriteria:
    """Test HARD criteria cause instant failure."""

    def test_beds_hard_failure(self):
        """Test beds < 4 causes FAIL."""
        data = {
            'beds': 3,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'city',
            'garage_spaces': 2,
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'FAIL'
        assert len(verdict.hard_failures) > 0
        assert any('[H] beds' in f for f in verdict.hard_failures)

    def test_baths_hard_failure(self):
        """Test baths < 2 causes FAIL."""
        data = {
            'beds': 4,
            'baths': 1.5,
            'hoa_fee': 0,
            'sewer_type': 'city',
            'garage_spaces': 2,
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'FAIL'
        assert any('[H] baths' in f for f in verdict.hard_failures)

    def test_hoa_hard_failure(self):
        """Test HOA > $0 causes FAIL."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 100,
            'sewer_type': 'city',
            'garage_spaces': 2,
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'FAIL'
        assert any('[H] hoa' in f for f in verdict.hard_failures)


class TestSoftCriteriaThreshold:
    """Test SOFT criteria weighted threshold logic."""

    def test_single_soft_failure_below_warning(self):
        """Test single SOFT failure below warning threshold."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'city',
            'garage_spaces': 2,
            'lot_sqft': 6500,  # SOFT fail (1.0 severity)
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'PASS'
        assert verdict.severity_score == SEVERITY_WEIGHTS['lot_size']
        assert verdict.severity_score < THRESHOLD_WARNING

    def test_severity_warning_threshold(self):
        """Test severity at warning threshold."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'city',
            'garage_spaces': 1,  # SOFT fail (1.5 severity)
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'WARNING'
        assert verdict.severity_score == SEVERITY_WEIGHTS['garage']
        assert THRESHOLD_WARNING <= verdict.severity_score < THRESHOLD_FAIL

    def test_severity_fail_threshold(self):
        """Test severity exceeding fail threshold."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'septic',  # SOFT fail (2.5 severity)
            'garage_spaces': 1,      # SOFT fail (1.5 severity)
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        total_severity = SEVERITY_WEIGHTS['septic'] + SEVERITY_WEIGHTS['garage']
        assert verdict.verdict == 'FAIL'
        assert verdict.severity_score == total_severity
        assert verdict.severity_score >= THRESHOLD_FAIL


class TestExampleScenarios:
    """Test example scenarios from plan document."""

    def test_septic_alone_warning(self):
        """Test septic alone → WARNING (2.5 pts)."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'septic',  # 2.5 severity
            'garage_spaces': 2,
            'lot_sqft': 8000,
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'WARNING'
        assert verdict.severity_score == 2.5

    def test_septic_plus_new_build_fail(self):
        """Test septic + new build → FAIL (4.5 pts)."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'septic',    # 2.5 severity
            'garage_spaces': 2,
            'lot_sqft': 8000,
            'year_built': 2024,        # 2.0 severity
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'FAIL'
        assert verdict.severity_score == 4.5

    def test_small_lot_pass(self):
        """Test lot 6,500 sqft alone → PASS (1.0 pts)."""
        data = {
            'beds': 4,
            'baths': 2.5,
            'hoa_fee': 0,
            'sewer_type': 'city',
            'garage_spaces': 2,
            'lot_sqft': 6500,  # 1.0 severity
            'year_built': 2010,
        }
        verdict = evaluate_kill_switches_weighted(data)

        assert verdict.verdict == 'PASS'
        assert verdict.severity_score == 1.0
```

**Success Criteria:**
- All tests pass
- Backward compatible: existing code still works
- New `evaluate_kill_switches_weighted` function works correctly
- [H] and [S] markers distinguish HARD vs SOFT failures

---

### 1.2 Update Deal Sheets Renderer

**File:** `scripts/deal_sheets/renderer.py` (MODIFY)

**Changes:**

1. Display kill-switch verdict (PASS/WARNING/FAIL)
2. Show [H]/[S] markers for criteria
3. Display severity score
4. Add color coding (green/yellow/red)

**Find the kill-switch rendering section (likely around line 150-200) and update:**

```python
# Add import at top
from scripts.lib.kill_switch import evaluate_kill_switches_weighted

# Replace existing kill-switch display logic with:
def render_kill_switch_section(property_data: dict) -> str:
    """Render enhanced kill-switch section with verdict."""
    verdict = evaluate_kill_switches_weighted(property_data)

    # Verdict badge
    badge_colors = {
        'PASS': 'green',
        'WARNING': 'yellow',
        'FAIL': 'red',
    }
    badge_color = badge_colors[verdict.verdict]
    verdict_line = f"<div class='verdict-badge {badge_color}'>{verdict.verdict}</div>"

    if verdict.severity_score > 0:
        verdict_line += f" <span class='severity'>Severity: {verdict.severity_score:.1f}/3.0</span>"

    # Individual criteria
    criteria_lines = []
    for result in verdict.all_results:
        marker = '[H]' if result.criterion_type == 'HARD' else '[S]'
        status = '✓' if result.passed else '✗'
        color_class = 'pass' if result.passed else 'fail'

        line = (
            f"<div class='criterion {color_class}'>"
            f"  <span class='marker'>{marker}</span> "
            f"  <span class='status'>{status}</span> "
            f"  <span class='name'>{result.name.upper()}</span>: "
            f"  <span class='value'>{result.actual_value}</span>"
        )

        if not result.passed and result.criterion_type == 'SOFT':
            line += f" <span class='severity-badge'>(+{result.severity})</span>"

        line += "</div>"
        criteria_lines.append(line)

    html = f"""
    <section class='kill-switch-section'>
      <h2>Kill-Switch Evaluation</h2>
      {verdict_line}

      <div class='criteria-list'>
        {''.join(criteria_lines)}
      </div>

      {_render_warnings(verdict) if verdict.has_warnings else ''}
      {_render_failures(verdict) if verdict.is_failed else ''}
    </section>
    """

    return html


def _render_warnings(verdict) -> str:
    """Render WARNING section."""
    if not verdict.warnings:
        return ""

    warning_items = '\n'.join([f"<li>{w}</li>" for w in verdict.warnings])
    return f"""
    <div class='warning-box'>
      <h3>⚠️ Warnings</h3>
      <p>Property has soft criterion violations. Buyer should review:</p>
      <ul>{warning_items}</ul>
      <p><strong>Severity Score: {verdict.severity_score:.1f}/3.0</strong> (threshold: 1.5)</p>
    </div>
    """


def _render_failures(verdict) -> str:
    """Render FAIL section."""
    if not verdict.hard_failures:
        return ""

    failure_items = '\n'.join([f"<li>{f}</li>" for f in verdict.hard_failures])
    return f"""
    <div class='failure-box'>
      <h3>❌ Disqualified</h3>
      <p>Property fails kill-switch criteria:</p>
      <ul>{failure_items}</ul>
      {f"<p><strong>Severity Score: {verdict.severity_score:.1f}/3.0</strong> (threshold: 3.0)</p>" if verdict.soft_failures else ""}
    </div>
    """
```

**Add CSS styling:**

**File:** `scripts/deal_sheets/templates.py` (MODIFY - add to CSS section)

```css
/* Kill-Switch Verdict Badges */
.verdict-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1.2em;
  margin-bottom: 16px;
}

.verdict-badge.green {
  background-color: #4CAF50;
  color: white;
}

.verdict-badge.yellow {
  background-color: #FFC107;
  color: black;
}

.verdict-badge.red {
  background-color: #F44336;
  color: white;
}

.severity {
  font-size: 0.9em;
  color: #666;
  margin-left: 12px;
}

/* Criterion List */
.criteria-list {
  margin: 16px 0;
}

.criterion {
  padding: 8px;
  margin: 4px 0;
  border-left: 3px solid #ddd;
  font-family: monospace;
}

.criterion.pass {
  background-color: #E8F5E9;
  border-left-color: #4CAF50;
}

.criterion.fail {
  background-color: #FFEBEE;
  border-left-color: #F44336;
}

.criterion .marker {
  font-weight: bold;
  color: #333;
  background-color: #eee;
  padding: 2px 6px;
  border-radius: 3px;
  margin-right: 8px;
}

.criterion .status {
  font-size: 1.2em;
  margin-right: 8px;
}

.criterion .severity-badge {
  background-color: #FF9800;
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 0.85em;
  margin-left: 8px;
}

/* Warning and Failure Boxes */
.warning-box, .failure-box {
  margin: 20px 0;
  padding: 16px;
  border-radius: 6px;
}

.warning-box {
  background-color: #FFF9C4;
  border: 2px solid #FFC107;
}

.failure-box {
  background-color: #FFCDD2;
  border: 2px solid #F44336;
}

.warning-box h3, .failure-box h3 {
  margin-top: 0;
}
```

**Success Criteria:**
- Deal sheets display verdict badges (PASS/WARNING/FAIL)
- [H]/[S] markers visible for each criterion
- Severity score displayed for WARNING/FAIL
- Color coding matches verdict

---

### Wave 1 Deliverables Checklist

- [ ] `scripts/lib/kill_switch.py` updated with weighted threshold logic
- [ ] `evaluate_kill_switches_weighted()` function works correctly
- [ ] Backward compatibility maintained (`evaluate_kill_switches()` still works)
- [ ] `tests/services/kill_switch/test_weighted_threshold.py` passes (all scenarios)
- [ ] Deal sheets display verdict badges with [H]/[S] markers
- [ ] CSS styling applied for color coding
- [ ] Manual testing: Generate deal sheet for sample property, verify display

---

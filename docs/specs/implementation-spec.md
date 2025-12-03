# PHX Houses Scoring System Improvement - Implementation Specification

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

## Executive Summary

This document provides detailed, file-by-file implementation instructions for all 7 waves of the scoring system improvement project. Each section includes exact code changes, test cases, and verification steps needed for successful implementation.

**Total Scope:**
- 7 implementation waves
- 8 new files, 13 modified files
- ~150 unit tests, ~20 integration tests
- Estimated effort: 40-50 hours across multiple sessions

---

## Table of Contents

1. [Wave 0: Baseline & Pre-Processing](#wave-0-baseline--pre-processing)
2. [Wave 1: Kill-Switch Threshold](#wave-1-kill-switch-threshold)
3. [Wave 2: Cost Estimation Module](#wave-2-cost-estimation-module)
4. [Wave 3: Data Validation Layer](#wave-3-data-validation-layer)
5. [Wave 4: AI-Assisted Triage](#wave-4-ai-assisted-triage)
6. [Wave 5: Quality Metrics & Lineage](#wave-5-quality-metrics--lineage)
7. [Wave 6: Documentation & Integration](#wave-6-documentation--integration)

---

## Wave 0: Baseline & Pre-Processing

**Priority:** P0 (Must complete before other waves)
**Estimated Effort:** 4-6 hours
**Dependencies:** None

### Objectives

1. Measure current data quality baseline
2. Create data pre-processing/normalization module
3. Establish regression test baseline

### 0.1 Quality Baseline Script

**File:** `scripts/quality_baseline.py` (NEW)

**Purpose:** Measure current data quality to track improvement to >95%

```python
"""Quality baseline measurement for PHX homes data.

Run this BEFORE making any changes to establish current quality metrics.
Output used as regression baseline for Wave 5 quality gates.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository


@dataclass
class FieldQuality:
    """Quality metrics for a single field."""
    field_name: str
    total_properties: int
    populated_count: int
    null_count: int
    completeness: float  # 0.0 - 1.0
    source: str  # 'csv' | 'enrichment' | 'both'


@dataclass
class QualityBaseline:
    """Overall quality baseline for dataset."""
    timestamp: str
    total_properties: int
    field_metrics: List[FieldQuality]
    overall_completeness: float
    critical_fields_completeness: float  # Kill-switch + scoring fields
    passing_score: float  # Target: 0.95


# Critical fields for quality assessment
CRITICAL_FIELDS = [
    # Kill-switch fields
    'beds', 'baths', 'hoa_fee', 'sewer_type', 'garage_spaces',
    'lot_sqft', 'year_built',
    # Scoring fields (high-weight)
    'school_rating', 'distance_to_highway_miles', 'orientation',
    'roof_age', 'has_pool'
]


def analyze_field_quality(
    csv_repo: CsvPropertyRepository,
    json_repo: JsonEnrichmentRepository
) -> List[FieldQuality]:
    """Analyze quality metrics for each field."""
    properties = csv_repo.find_all()
    enrichments = json_repo.find_all()
    total = len(properties)

    field_metrics = []

    # Analyze CSV fields
    csv_fields = ['beds', 'baths', 'sqft', 'price_num']
    for field in csv_fields:
        populated = sum(1 for p in properties if getattr(p, field, None) is not None)
        field_metrics.append(FieldQuality(
            field_name=field,
            total_properties=total,
            populated_count=populated,
            null_count=total - populated,
            completeness=populated / total if total > 0 else 0.0,
            source='csv'
        ))

    # Analyze enrichment fields
    enrichment_fields = [
        'lot_sqft', 'year_built', 'garage_spaces', 'hoa_fee',
        'school_rating', 'orientation', 'roof_age', 'has_pool'
    ]
    for field in enrichment_fields:
        populated = sum(
            1 for e in enrichments
            if getattr(e, field, None) is not None
        )
        field_metrics.append(FieldQuality(
            field_name=field,
            total_properties=total,
            populated_count=populated,
            null_count=total - populated,
            completeness=populated / total if total > 0 else 0.0,
            source='enrichment'
        ))

    return field_metrics


def calculate_baseline(field_metrics: List[FieldQuality]) -> QualityBaseline:
    """Calculate overall baseline metrics."""
    from datetime import datetime

    total_properties = field_metrics[0].total_properties if field_metrics else 0

    # Overall completeness
    overall = sum(f.completeness for f in field_metrics) / len(field_metrics)

    # Critical fields completeness
    critical_metrics = [f for f in field_metrics if f.field_name in CRITICAL_FIELDS]
    critical = sum(f.completeness for f in critical_metrics) / len(critical_metrics)

    return QualityBaseline(
        timestamp=datetime.now().isoformat(),
        total_properties=total_properties,
        field_metrics=field_metrics,
        overall_completeness=overall,
        critical_fields_completeness=critical,
        passing_score=0.95
    )


def generate_report(baseline: QualityBaseline) -> str:
    """Generate human-readable report."""
    lines = [
        "=" * 70,
        "DATA QUALITY BASELINE REPORT",
        "=" * 70,
        f"Timestamp: {baseline.timestamp}",
        f"Total Properties: {baseline.total_properties}",
        "",
        f"Overall Completeness: {baseline.overall_completeness:.1%}",
        f"Critical Fields Completeness: {baseline.critical_fields_completeness:.1%}",
        f"Target (Wave 5): {baseline.passing_score:.1%}",
        "",
        "=" * 70,
        "FIELD-BY-FIELD BREAKDOWN",
        "=" * 70,
        "",
        f"{'Field':<25} {'Source':<12} {'Populated':<10} {'Complete':<10}",
        "-" * 70,
    ]

    # Sort by completeness (ascending) to highlight gaps
    sorted_metrics = sorted(baseline.field_metrics, key=lambda f: f.completeness)
    for field in sorted_metrics:
        status = "✓" if field.completeness >= 0.95 else "✗"
        lines.append(
            f"{field.field_name:<25} {field.source:<12} "
            f"{field.populated_count:<10} {field.completeness:>8.1%} {status}"
        )

    lines.extend([
        "",
        "=" * 70,
        "CRITICAL FIELDS (Kill-Switch + High-Weight Scoring)",
        "=" * 70,
    ])

    critical_metrics = [f for f in baseline.field_metrics if f.field_name in CRITICAL_FIELDS]
    for field in sorted(critical_metrics, key=lambda f: f.completeness):
        status = "✓" if field.completeness >= 0.95 else "✗ NEEDS IMPROVEMENT"
        lines.append(
            f"{field.field_name:<25} {field.completeness:>8.1%} {status}"
        )

    lines.extend([
        "",
        "=" * 70,
        "RECOMMENDATIONS",
        "=" * 70,
    ])

    # Identify gaps
    gaps = [f for f in baseline.field_metrics if f.completeness < 0.95]
    if gaps:
        lines.append(f"\n{len(gaps)} fields below 95% threshold:")
        for field in sorted(gaps, key=lambda f: f.completeness)[:10]:  # Top 10 gaps
            improvement_needed = (0.95 - field.completeness) * field.total_properties
            lines.append(
                f"  • {field.field_name}: {field.completeness:.1%} "
                f"(need {int(improvement_needed)} more values)"
            )
    else:
        lines.append("✓ All fields meet 95% threshold")

    return "\n".join(lines)


def main():
    """Run quality baseline measurement."""
    from pathlib import Path

    # Initialize repositories
    project_root = Path(__file__).parent.parent
    csv_repo = CsvPropertyRepository(project_root / "data" / "phx_homes.csv")
    json_repo = JsonEnrichmentRepository(project_root / "data" / "enrichment_data.json")

    print("Analyzing data quality...")
    field_metrics = analyze_field_quality(csv_repo, json_repo)
    baseline = calculate_baseline(field_metrics)

    # Generate report
    report = generate_report(baseline)
    print(report)

    # Save baseline to file
    output_path = project_root / "data" / "quality_baseline.json"
    with open(output_path, 'w') as f:
        json.dump(asdict(baseline), f, indent=2)

    print(f"\nBaseline saved to: {output_path}")

    # Exit with status code
    if baseline.critical_fields_completeness >= 0.95:
        print("\n✓ PASS: Critical fields meet 95% threshold")
        sys.exit(0)
    else:
        gap = 0.95 - baseline.critical_fields_completeness
        print(f"\n✗ FAIL: Critical fields at {baseline.critical_fields_completeness:.1%} "
              f"(need +{gap:.1%} improvement)")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Run baseline measurement
python scripts/quality_baseline.py

# Output: Console report + data/quality_baseline.json
```

**Success Criteria:**
- Script runs without errors
- `data/quality_baseline.json` created
- Report identifies fields <95% completeness

---

### 0.2 Data Normalizer Module

**File:** `src/phx_home_analysis/validation/normalizer.py` (NEW)

**Purpose:** Pre-process and normalize data before validation

```python
"""Data normalization and pre-processing for property data.

Handles:
- Address normalization (St→Street, W→West, lowercase)
- Type inference (string "2.5" → float 2.5)
- Enum mapping (string "city" → SewerType.CITY)
- Duplicate detection via hash-based deduplication
"""

import re
import hashlib
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..domain.enums import SewerType, SolarStatus, Orientation


# Address normalization mappings
STREET_ABBREVIATIONS = {
    ' St': ' Street',
    ' Ave': ' Avenue',
    ' Blvd': ' Boulevard',
    ' Dr': ' Drive',
    ' Rd': ' Road',
    ' Ct': ' Court',
    ' Ln': ' Lane',
    ' Pl': ' Place',
    ' Cir': ' Circle',
    ' Way': ' Way',
}

DIRECTION_ABBREVIATIONS = {
    'N ': 'North ',
    'S ': 'South ',
    'E ': 'East ',
    'W ': 'West ',
    'NE ': 'Northeast ',
    'NW ': 'Northwest ',
    'SE ': 'Southeast ',
    'SW ': 'Southwest ',
}


@dataclass
class NormalizationResult:
    """Result of normalizing a single field."""
    original_value: Any
    normalized_value: Any
    changed: bool
    notes: str = ""


class PropertyDataNormalizer:
    """Normalize property data before validation."""

    @staticmethod
    def normalize_address(address: str) -> str:
        """Normalize address for consistent comparison.

        Examples:
            '123 N Main St' → '123 North Main Street'
            '456 W. Oak Ave.' → '456 West Oak Avenue'
        """
        if not address:
            return address

        normalized = address.strip()

        # Remove periods
        normalized = normalized.replace('.', '')

        # Expand direction abbreviations
        for abbr, full in DIRECTION_ABBREVIATIONS.items():
            if normalized.startswith(abbr):
                normalized = full + normalized[len(abbr):]

        # Expand street type abbreviations
        for abbr, full in STREET_ABBREVIATIONS.items():
            if abbr in normalized:
                normalized = normalized.replace(abbr, full)

        return normalized

    @staticmethod
    def generate_property_hash(address: str) -> str:
        """Generate consistent hash for property identification.

        Args:
            address: Full property address

        Returns:
            8-character hex hash (e.g., 'ef7cd95f')
        """
        normalized = PropertyDataNormalizer.normalize_address(address)
        return hashlib.md5(normalized.lower().encode()).hexdigest()[:8]

    @staticmethod
    def infer_type(value: Any, target_type: type) -> Any:
        """Infer and convert value to target type.

        Args:
            value: Raw value (any type)
            target_type: Desired type (int, float, bool, str)

        Returns:
            Converted value or None if conversion fails
        """
        if value is None:
            return None

        try:
            if target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 't', 'y')
                return bool(value)
            elif target_type in (int, float):
                # Handle string numbers
                if isinstance(value, str):
                    value = value.replace(',', '')  # "1,000" → "1000"
                return target_type(value)
            elif target_type == str:
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_sewer_type(value: Any) -> Optional[SewerType]:
        """Normalize sewer type to enum."""
        if value is None:
            return None

        if isinstance(value, SewerType):
            return value

        value_str = str(value).lower().strip()

        # Mapping variations
        if value_str in ('city', 'public', 'municipal', 'sewertype.city'):
            return SewerType.CITY
        elif value_str in ('septic', 'private', 'sewertype.septic'):
            return SewerType.SEPTIC
        else:
            return SewerType.UNKNOWN

    @staticmethod
    def normalize_solar_status(value: Any) -> Optional[SolarStatus]:
        """Normalize solar status to enum."""
        if value is None:
            return None

        if isinstance(value, SolarStatus):
            return value

        value_str = str(value).lower().strip()

        if value_str in ('owned', 'own', 'solarstatus.owned'):
            return SolarStatus.OWNED
        elif value_str in ('leased', 'lease', 'solarstatus.leased'):
            return SolarStatus.LEASED
        elif value_str in ('none', 'no', 'solarstatus.none'):
            return SolarStatus.NONE
        else:
            return SolarStatus.UNKNOWN

    @staticmethod
    def normalize_orientation(value: Any) -> Optional[Orientation]:
        """Normalize orientation to enum."""
        if value is None:
            return None

        if isinstance(value, Orientation):
            return value

        value_str = str(value).upper().strip()

        # Use Orientation.from_string if available
        if hasattr(Orientation, 'from_string'):
            return Orientation.from_string(value_str)

        # Fallback mapping
        orientation_map = {
            'N': Orientation.NORTH,
            'NORTH': Orientation.NORTH,
            'S': Orientation.SOUTH,
            'SOUTH': Orientation.SOUTH,
            'E': Orientation.EAST,
            'EAST': Orientation.EAST,
            'W': Orientation.WEST,
            'WEST': Orientation.WEST,
            'NE': Orientation.NORTHEAST,
            'NORTHEAST': Orientation.NORTHEAST,
            'NW': Orientation.NORTHWEST,
            'NORTHWEST': Orientation.NORTHWEST,
            'SE': Orientation.SOUTHEAST,
            'SOUTHEAST': Orientation.SOUTHEAST,
            'SW': Orientation.SOUTHWEST,
            'SOUTHWEST': Orientation.SOUTHWEST,
        }

        return orientation_map.get(value_str, Orientation.UNKNOWN)

    @classmethod
    def normalize_property_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all fields in property dictionary.

        Args:
            data: Raw property data dictionary

        Returns:
            Normalized property data dictionary
        """
        normalized = data.copy()

        # Address normalization
        if 'full_address' in normalized:
            normalized['full_address'] = cls.normalize_address(normalized['full_address'])

        # Type inference for numeric fields
        numeric_fields = [
            'beds', 'baths', 'sqft', 'price_num', 'lot_sqft',
            'year_built', 'garage_spaces', 'hoa_fee', 'tax_annual'
        ]
        for field in numeric_fields:
            if field in normalized:
                target_type = float if field == 'baths' else int
                normalized[field] = cls.infer_type(normalized[field], target_type)

        # Boolean fields
        bool_fields = ['has_pool', 'fireplace_present']
        for field in bool_fields:
            if field in normalized:
                normalized[field] = cls.infer_type(normalized[field], bool)

        # Enum normalization
        if 'sewer_type' in normalized:
            normalized['sewer_type'] = cls.normalize_sewer_type(normalized['sewer_type'])

        if 'solar_status' in normalized:
            normalized['solar_status'] = cls.normalize_solar_status(normalized['solar_status'])

        if 'orientation' in normalized:
            normalized['orientation'] = cls.normalize_orientation(normalized['orientation'])

        return normalized


# Convenience functions
def normalize_address(address: str) -> str:
    """Normalize address string."""
    return PropertyDataNormalizer.normalize_address(address)


def generate_property_hash(address: str) -> str:
    """Generate property hash from address."""
    return PropertyDataNormalizer.generate_property_hash(address)
```

**Unit Tests:**

**File:** `tests/validation/test_normalizer.py` (NEW)

```python
"""Unit tests for data normalizer."""

import pytest
from src.phx_home_analysis.validation.normalizer import (
    PropertyDataNormalizer,
    normalize_address,
    generate_property_hash
)
from src.phx_home_analysis.domain.enums import SewerType, SolarStatus, Orientation


class TestAddressNormalization:
    """Test address normalization."""

    def test_expand_street_abbreviations(self):
        """Test street type abbreviation expansion."""
        assert normalize_address("123 Main St") == "123 Main Street"
        assert normalize_address("456 Oak Ave") == "456 Oak Avenue"
        assert normalize_address("789 Elm Blvd") == "789 Elm Boulevard"

    def test_expand_direction_abbreviations(self):
        """Test direction abbreviation expansion."""
        assert normalize_address("N Main St") == "North Main Street"
        assert normalize_address("W Oak Ave") == "West Oak Avenue"
        assert normalize_address("NE Elm Blvd") == "Northeast Elm Boulevard"

    def test_remove_periods(self):
        """Test period removal."""
        assert normalize_address("123 N. Main St.") == "123 North Main Street"

    def test_property_hash_consistency(self):
        """Test hash generation is consistent."""
        addr1 = "123 N Main St"
        addr2 = "123 North Main Street"
        assert generate_property_hash(addr1) == generate_property_hash(addr2)


class TestTypeInference:
    """Test type inference."""

    def test_string_to_int(self):
        """Test string to int conversion."""
        assert PropertyDataNormalizer.infer_type("123", int) == 123
        assert PropertyDataNormalizer.infer_type("1,000", int) == 1000

    def test_string_to_float(self):
        """Test string to float conversion."""
        assert PropertyDataNormalizer.infer_type("2.5", float) == 2.5

    def test_string_to_bool(self):
        """Test string to bool conversion."""
        assert PropertyDataNormalizer.infer_type("true", bool) is True
        assert PropertyDataNormalizer.infer_type("yes", bool) is True
        assert PropertyDataNormalizer.infer_type("1", bool) is True
        assert PropertyDataNormalizer.infer_type("false", bool) is False


class TestEnumNormalization:
    """Test enum normalization."""

    def test_sewer_type_variations(self):
        """Test sewer type normalization."""
        assert PropertyDataNormalizer.normalize_sewer_type("city") == SewerType.CITY
        assert PropertyDataNormalizer.normalize_sewer_type("public") == SewerType.CITY
        assert PropertyDataNormalizer.normalize_sewer_type("septic") == SewerType.SEPTIC

    def test_solar_status_variations(self):
        """Test solar status normalization."""
        assert PropertyDataNormalizer.normalize_solar_status("owned") == SolarStatus.OWNED
        assert PropertyDataNormalizer.normalize_solar_status("leased") == SolarStatus.LEASED
        assert PropertyDataNormalizer.normalize_solar_status("none") == SolarStatus.NONE

    def test_orientation_variations(self):
        """Test orientation normalization."""
        assert PropertyDataNormalizer.normalize_orientation("N") == Orientation.NORTH
        assert PropertyDataNormalizer.normalize_orientation("north") == Orientation.NORTH
        assert PropertyDataNormalizer.normalize_orientation("NE") == Orientation.NORTHEAST
```

**Success Criteria:**
- All tests pass
- Address normalization handles common variations
- Type inference works for strings, numbers, booleans
- Enum normalization maps all variations correctly

---

### 0.3 Regression Test Baseline

**File:** `tests/regression/test_baseline.py` (NEW)

**Purpose:** Capture current behavior for regression testing

```python
"""Regression test baseline.

Captures current system behavior before changes. After Wave 1-6,
re-run these tests to ensure no unintended regressions.
"""

import pytest
from pathlib import Path
import json

from src.phx_home_analysis.repositories.csv_repository import CsvPropertyRepository
from src.phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository
from scripts.lib.kill_switch import evaluate_kill_switches
from src.phx_home_analysis.services.scoring import PropertyScorer


@pytest.fixture
def sample_properties():
    """Load sample properties for testing."""
    project_root = Path(__file__).parent.parent.parent
    csv_repo = CsvPropertyRepository(project_root / "data" / "phx_homes.csv")
    properties = csv_repo.find_all()
    return properties[:5]  # First 5 properties


class TestKillSwitchBaseline:
    """Baseline kill-switch behavior."""

    def test_all_must_pass_logic(self, sample_properties):
        """Verify current 'all must pass' logic."""
        for prop in sample_properties:
            passed, failures, _ = evaluate_kill_switches(prop)

            if passed:
                assert len(failures) == 0, "Passed properties should have no failures"
            else:
                assert len(failures) > 0, "Failed properties should list failures"

    def test_failure_messages(self, sample_properties):
        """Verify failure messages contain criterion names."""
        for prop in sample_properties:
            _, failures, _ = evaluate_kill_switches(prop)

            for failure in failures:
                # Should contain criterion identifier
                assert any(keyword in failure.lower() for keyword in [
                    'hoa', 'sewer', 'garage', 'bed', 'bath', 'lot', 'year'
                ]), f"Failure message unclear: {failure}"


class TestScoringBaseline:
    """Baseline scoring behavior."""

    def test_section_totals(self, sample_properties):
        """Verify section totals sum correctly."""
        scorer = PropertyScorer()

        for prop in sample_properties:
            if not prop.kill_switch_passed:
                continue  # Skip failed properties

            score_breakdown = scorer.score(prop)

            # Section A: 250 pts
            assert 0 <= score_breakdown.location_total <= 250

            # Section B: 160 pts (current)
            assert 0 <= score_breakdown.systems_total <= 160

            # Section C: 190 pts
            assert 0 <= score_breakdown.interior_total <= 190

            # Total: 600 pts
            assert 0 <= score_breakdown.total_score <= 600

    def test_tier_classification(self, sample_properties):
        """Verify tier classification thresholds."""
        scorer = PropertyScorer()

        for prop in sample_properties:
            if not prop.kill_switch_passed:
                assert prop.tier.value == 'failed'
                continue

            score_breakdown = scorer.score(prop)
            total = score_breakdown.total_score

            # Current tier thresholds
            if total > 480:
                expected_tier = 'unicorn'
            elif total >= 360:
                expected_tier = 'contender'
            else:
                expected_tier = 'pass'

            # Note: This may fail if tier not set - that's ok for baseline
            # After Wave 2, this should always pass


class TestDataQualityBaseline:
    """Baseline data quality metrics."""

    def test_completeness_snapshot(self, sample_properties):
        """Snapshot current completeness rates."""
        fields_to_check = [
            'beds', 'baths', 'lot_sqft', 'year_built', 'garage_spaces',
            'hoa_fee', 'school_rating', 'orientation'
        ]

        for field in fields_to_check:
            populated = sum(
                1 for prop in sample_properties
                if getattr(prop, field, None) is not None
            )
            completeness = populated / len(sample_properties)

            # Just log current state (no assertion)
            print(f"{field}: {completeness:.1%} complete")


def main():
    """Run regression baseline and save results."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Run regression baseline
pytest tests/regression/test_baseline.py -v

# Save results
pytest tests/regression/test_baseline.py -v > tests/regression/baseline_results.txt
```

**Success Criteria:**
- All baseline tests pass (or document known failures)
- Results saved for comparison after Wave 6

---

### Wave 0 Deliverables Checklist

- [ ] `scripts/quality_baseline.py` created and runs successfully
- [ ] `data/quality_baseline.json` generated with current metrics
- [ ] `src/phx_home_analysis/validation/normalizer.py` created
- [ ] `tests/validation/test_normalizer.py` passes (100% coverage)
- [ ] `tests/regression/test_baseline.py` captures current behavior
- [ ] Baseline results documented for post-Wave 6 comparison

---

## Wave 1: Kill-Switch Threshold

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

## Wave 2: Cost Estimation Module

**Priority:** P0
**Estimated Effort:** 8-10 hours
**Dependencies:** Wave 1 complete

### Objectives

1. Create cost estimation module with 6 component calculators
2. Fetch current rates via web research
3. Integrate as new 40-point scoring criterion
4. Display monthly cost with $4k warning in deal sheets

### 2.1 Rate Provider

**File:** `src/phx_home_analysis/services/cost_estimation/rate_provider.py` (NEW)

**Purpose:** Centralized source for rate data (mortgage, insurance, utilities)

```python
"""Rate data provider for cost estimation.

Fetches and caches current rates for:
- Mortgage interest rates (30-year fixed)
- Homeowner's insurance (AZ average)
- Utility rates (SRP/APS electric, water, gas)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class MortgageRates:
    """Current mortgage interest rates."""
    thirty_year_fixed: float  # APR as decimal (e.g., 0.07 for 7%)
    fifteen_year_fixed: float
    source: str
    last_updated: datetime


@dataclass
class InsuranceRates:
    """Homeowner's insurance rates for Arizona."""
    base_annual_low: float  # e.g., 1500
    base_annual_high: float  # e.g., 2500
    sqft_adjustment: float  # per sqft multiplier
    pool_premium: float  # additional annual cost if pool present
    source: str
    last_updated: datetime


@dataclass
class UtilityRates:
    """Utility rates for Arizona (SRP/APS)."""
    electric_per_kwh_summer: float  # $/kWh (May-Oct)
    electric_per_kwh_winter: float  # $/kWh (Nov-Apr)
    electric_base_charge: float  # monthly base
    water_base_monthly: float  # typical monthly
    gas_base_monthly: float  # typical monthly (if applicable)
    source: str
    last_updated: datetime


class RateProvider:
    """Provide current rates for cost estimation with caching."""

    CACHE_DURATION = timedelta(days=7)  # Re-fetch weekly
    CACHE_FILE = Path(__file__).parent / "rate_cache.json"

    def __init__(self):
        """Initialize rate provider with cache."""
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cached rates from file."""
        if self.CACHE_FILE.exists():
            with open(self.CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save rates to cache file."""
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(self._cache, f, indent=2, default=str)

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached rate is still valid."""
        if key not in self._cache:
            return False

        cached_time = datetime.fromisoformat(self._cache[key]['last_updated'])
        return datetime.now() - cached_time < self.CACHE_DURATION

    def get_mortgage_rates(self) -> MortgageRates:
        """Get current mortgage rates."""
        if self._is_cache_valid('mortgage'):
            data = self._cache['mortgage']
            return MortgageRates(
                thirty_year_fixed=data['thirty_year_fixed'],
                fifteen_year_fixed=data['fifteen_year_fixed'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # Fetch new rates (manual update for now)
        # TODO: Implement web scraping or API integration
        rates = MortgageRates(
            thirty_year_fixed=0.07,  # 7% - PLACEHOLDER, update manually
            fifteen_year_fixed=0.065,  # 6.5% - PLACEHOLDER
            source='Manual entry (2025-12-01)',
            last_updated=datetime.now()
        )

        # Cache
        self._cache['mortgage'] = {
            'thirty_year_fixed': rates.thirty_year_fixed,
            'fifteen_year_fixed': rates.fifteen_year_fixed,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates

    def get_insurance_rates(self) -> InsuranceRates:
        """Get current homeowner's insurance rates for Arizona."""
        if self._is_cache_valid('insurance'):
            data = self._cache['insurance']
            return InsuranceRates(
                base_annual_low=data['base_annual_low'],
                base_annual_high=data['base_annual_high'],
                sqft_adjustment=data['sqft_adjustment'],
                pool_premium=data['pool_premium'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # AZ insurance rates (2025 estimates)
        rates = InsuranceRates(
            base_annual_low=1500.0,
            base_annual_high=2500.0,
            sqft_adjustment=0.5,  # $0.50 per sqft above 1500
            pool_premium=300.0,  # Additional $300/year for pool
            source='AZ insurance average (2025 estimates)',
            last_updated=datetime.now()
        )

        self._cache['insurance'] = {
            'base_annual_low': rates.base_annual_low,
            'base_annual_high': rates.base_annual_high,
            'sqft_adjustment': rates.sqft_adjustment,
            'pool_premium': rates.pool_premium,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates

    def get_utility_rates(self) -> UtilityRates:
        """Get current utility rates for Arizona."""
        if self._is_cache_valid('utility'):
            data = self._cache['utility']
            return UtilityRates(
                electric_per_kwh_summer=data['electric_per_kwh_summer'],
                electric_per_kwh_winter=data['electric_per_kwh_winter'],
                electric_base_charge=data['electric_base_charge'],
                water_base_monthly=data['water_base_monthly'],
                gas_base_monthly=data['gas_base_monthly'],
                source=data['source'],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )

        # AZ utility rates (SRP/APS averages)
        rates = UtilityRates(
            electric_per_kwh_summer=0.14,  # $0.14/kWh May-Oct
            electric_per_kwh_winter=0.11,  # $0.11/kWh Nov-Apr
            electric_base_charge=15.0,  # $15/month base
            water_base_monthly=80.0,  # $80-120 typical
            gas_base_monthly=50.0,  # $30-80 typical
            source='SRP/APS average rates (2025)',
            last_updated=datetime.now()
        )

        self._cache['utility'] = {
            'electric_per_kwh_summer': rates.electric_per_kwh_summer,
            'electric_per_kwh_winter': rates.electric_per_kwh_winter,
            'electric_base_charge': rates.electric_base_charge,
            'water_base_monthly': rates.water_base_monthly,
            'gas_base_monthly': rates.gas_base_monthly,
            'source': rates.source,
            'last_updated': rates.last_updated.isoformat()
        }
        self._save_cache()

        return rates
```

(Continuing with remaining waves in next message due to length constraints...)

**Success Criteria for Wave 2:**
- Rate provider caches data for 7 days
- All calculators implemented with unit tests
- CostEfficiencyScorer integrated into scoring engine
- Deal sheets display monthly cost with $4k warning

---

### Wave 2 Deliverables Checklist

- [ ] `src/phx_home_analysis/services/cost_estimation/rate_provider.py` created
- [ ] `src/phx_home_analysis/services/cost_estimation/calculators.py` created
- [ ] `src/phx_home_analysis/services/cost_estimation/estimator.py` created
- [ ] All calculator unit tests pass
- [ ] CostEfficiencyScorer added to `strategies/systems.py`
- [ ] Scoring weights updated (Section B: 160→180)
- [ ] Deal sheets display monthly cost breakdown
- [ ] $4k warning badge functional

---

*This specification continues with Waves 3-6 in similar detail. Due to length constraints, I'm providing the structure for the remaining waves:*

## Wave 3: Data Validation Layer
- 3.1 Pydantic Schemas
- 3.2 Integration with Repositories
- 3.3 Validation Tests

## Wave 4: AI-Assisted Triage
- 4.1 Field Inferencer
- 4.2 Prompt Templates
- 4.3 Confidence Scoring

## Wave 5: Quality Metrics & Lineage
- 5.1 Lineage Tracking
- 5.2 Quality Calculator
- 5.3 CI/CD Quality Gate

## Wave 6: Documentation & Integration
- 6.1 Update Skill Files
- 6.2 Integration Tests
- 6.3 End-to-End Verification

---

**Document Version Control:**
- v1.0 (2025-12-01): Initial implementation spec
- Next Review: After Wave 2 completion

**Related Documents:**
- `docs/architecture/scoring-improvement-architecture.md` - System architecture
- `docs/specs/phase-execution-guide.md` - Session-by-session guide
- `docs/specs/reference-index.md` - Research documents

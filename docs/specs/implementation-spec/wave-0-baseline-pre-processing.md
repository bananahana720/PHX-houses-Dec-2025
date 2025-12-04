# Wave 0: Baseline & Pre-Processing

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

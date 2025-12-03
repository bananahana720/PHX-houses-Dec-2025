# PHX Houses Dec 2025 - Refactoring Analysis Report

**Generated:** 2025-11-29
**Total Files Analyzed:** 12 Python scripts
**Total Lines of Code:** ~4,500 LOC

---

## 1. Analysis Summary

### Overall Assessment
The codebase is a **data analysis pipeline** for evaluating Phoenix home listings. While functional, it exhibits several code quality issues that reduce maintainability and testability. The primary concerns are:

1. **Heavy Code Duplication** across scripts (data loading, path handling, formatting)
2. **Tight Coupling** between data loading, business logic, and output generation
3. **Hardcoded Configuration** scattered throughout files
4. **Missing Abstractions** for common patterns (repositories, formatters)
5. **No Test Coverage** (0% detected)

### Code Quality Metrics

| Script | Lines | Complexity | Issues | Priority |
|--------|-------|------------|--------|----------|
| `phx_home_analyzer.py` | 575 | 8 | 12 | HIGH |
| `risk_report.py` | 675 | 12 | 15 | HIGH |
| `renovation_gap.py` | 647 | 10 | 11 | HIGH |
| `data_quality_report.py` | 416 | 8 | 8 | MEDIUM |
| `golden_zone_map.py` | 298 | 6 | 7 | MEDIUM |
| `radar_charts.py` | 253 | 5 | 6 | MEDIUM |
| `sun_orientation_analysis.py` | 343 | 6 | 7 | MEDIUM |
| `value_spotter.py` | 265 | 4 | 5 | LOW |
| `geocode_homes.py` | 166 | 4 | 4 | LOW |
| `deal_sheets.py` | ~1000 | 14 | 18 | HIGH |
| `cost_breakdown_analysis.py` | 120 | 3 | 3 | LOW |
| `show_best_values.py` | 30 | 1 | 1 | LOW |

---

## 2. Code Smells Identified

### Critical (Fix Immediately)

#### 2.1 Massive Duplication: Data Loading Functions
**Impact:** 10+ files duplicate identical patterns

**Before (repeated in 10 files):**
```python
# renovation_gap.py:81-88
def load_csv_data(csv_path: Path) -> List[Dict]:
    properties = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

# risk_report.py:193-200 - IDENTICAL
def load_ranked_properties(file_path: str) -> List[Dict]:
    properties = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties
```

**After (shared repository):**
```python
# repositories/property_repository.py
class PropertyRepository:
    """Centralized data access for property data."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load_ranked_csv(self) -> List[Dict]:
        """Load ranked properties from CSV."""
        return self._load_csv(self.base_dir / 'phx_homes_ranked.csv')

    def load_enrichment_json(self) -> Dict[str, Dict]:
        """Load enrichment data indexed by address."""
        return self._load_json_indexed(
            self.base_dir / 'enrichment_data.json',
            key='full_address'
        )

    def _load_csv(self, path: Path) -> List[Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def _load_json_indexed(self, path: Path, key: str) -> Dict[str, Dict]:
        with open(path, 'r', encoding='utf-8') as f:
            return {item[key]: item for item in json.load(f)}
```

---

#### 2.2 Hardcoded Paths and Magic Numbers
**Impact:** Configuration spread across 12 files, hard to modify

**Before (scattered across files):**
```python
# radar_charts.py:18-22
WORKING_DIR = Path(r"C:\Users\Andrew\Downloads\PHX-houses-Dec-2025")
CSV_FILE = WORKING_DIR / "phx_homes_ranked.csv"
JSON_FILE = WORKING_DIR / "enrichment_data.json"

# golden_zone_map.py:18-26
PHOENIX_CENTER = (33.55, -112.05)
GROCERY_RADIUS_MILES = 1.5
HIGHWAY_BUFFER_MILES = 1.0

# phx_home_analyzer.py:267-297
# Magic numbers for weights scattered in function
section_a = [
    (5, score_school_district),  # Why 5?
    (5, score_quietness),        # Why 5?
```

**After (centralized configuration):**
```python
# config/settings.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ProjectPaths:
    base_dir: Path

    @property
    def ranked_csv(self) -> Path:
        return self.base_dir / "reports" / "csv" / "phx_homes_ranked.csv"

    @property
    def enrichment_json(self) -> Path:
        return self.base_dir / "data" / "enrichment_data.json"

@dataclass(frozen=True)
class MapConfig:
    phoenix_center: tuple = (33.55, -112.05)
    default_zoom: int = 10
    grocery_radius_miles: float = 1.5
    highway_buffer_miles: float = 1.0

@dataclass(frozen=True)
class ScoringWeights:
    """Scoring weights with documentation."""
    # Section A: Location (max 150 pts)
    school_district: int = 5  # GreatSchools 1-10 × 5 = max 50
    quietness: int = 5        # Highway distance scoring × 5 = max 50
    safety: int = 5           # Manual assessment × 5 = max 50
    # ... etc

# Usage
config = ProjectPaths(Path(__file__).parent.parent)
```

---

#### 2.3 Long Functions (>50 lines)
**Impact:** Hard to test, hard to understand, hard to modify

**Files with long functions:**
- `risk_report.py:268-437` - `generate_html_report()` = 169 lines
- `renovation_gap.py:159-411` - `generate_html_report()` = 252 lines
- `phx_home_analyzer.py:267-319` - `calculate_weighted_score()` = 52 lines
- `data_quality_report.py:210-405` - `generate_report()` = 195 lines

**Before (renovation_gap.py:159-252 - excerpt):**
```python
def generate_html_report(results: List[Dict], output_path: Path):
    """Generate interactive HTML report with sortable table."""

    html = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Renovation Gap Report - Phoenix Homes</title>
        <style>
            # 150+ lines of inline CSS
        </style>
    </head>
    <body>
        # Complex template with placeholders
    </body>
    </html>
    """

    # Calculate summary statistics
    total_properties = len(results)
    renovations = [r['total_renovation'] for r in results]
    # ... 50+ more lines of data processing

    # Generate table rows
    table_rows = []
    for result in results:
        # ... 30+ lines per row

    # Replace placeholders
    html = html.replace('{{TOTAL_PROPERTIES}}', str(total_properties))
    # ... 10 more replacements

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
```

**After (decomposed with template):**
```python
# templates/renovation_report.html (external file)
# Contains all HTML/CSS template code

# reports/html_generator.py
class HtmlReportGenerator:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )

    def generate_renovation_report(
        self,
        results: List[Dict],
        output_path: Path
    ) -> None:
        template = self.env.get_template('renovation_report.html')
        context = self._build_context(results)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template.render(context))

    def _build_context(self, results: List[Dict]) -> Dict:
        stats = self._calculate_statistics(results)
        rows = [self._format_row(r) for r in results]
        return {'stats': stats, 'rows': rows}

    def _calculate_statistics(self, results: List[Dict]) -> Dict:
        renovations = [r['total_renovation'] for r in results]
        return {
            'total_properties': len(results),
            'avg_renovation': sum(renovations) / len(renovations),
            'min_renovation': min(renovations),
            'max_renovation': max(renovations),
        }
```

---

### High (Schedule This Sprint)

#### 2.4 Primitive Obsession: Risk Levels
**Impact:** String comparisons scattered, easy to typo, no type safety

**Before (risk_report.py:27-42):**
```python
class RiskCategory:
    """Risk assessment levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    POSITIVE = "POSITIVE"
    UNKNOWN = "UNKNOWN"

# Usage scattered:
if risk_level == RiskCategory.HIGH:
    score += RiskScores.HIGH
elif risk_level == RiskCategory.MEDIUM:
    score += RiskScores.MEDIUM
```

**After (proper enum with behavior):**
```python
from enum import Enum, auto
from dataclasses import dataclass

class RiskLevel(Enum):
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    POSITIVE = auto()
    UNKNOWN = auto()

    @property
    def score(self) -> int:
        """Risk score contribution."""
        return {
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 1,
            RiskLevel.LOW: 0,
            RiskLevel.POSITIVE: 0,
            RiskLevel.UNKNOWN: 1,
        }[self]

    @property
    def css_class(self) -> str:
        """CSS class for HTML rendering."""
        return f"risk-{self.name.lower()}"

    @property
    def color(self) -> str:
        """Badge color for reports."""
        return {
            RiskLevel.HIGH: '#dc3545',
            RiskLevel.MEDIUM: '#ffc107',
            RiskLevel.LOW: '#28a745',
            RiskLevel.POSITIVE: '#007bff',
            RiskLevel.UNKNOWN: '#6c757d',
        }[self]

@dataclass
class RiskAssessment:
    """Container for risk assessment result."""
    level: RiskLevel
    description: str

    @property
    def score(self) -> int:
        return self.level.score
```

---

#### 2.5 Missing Abstraction: Scoring System
**Impact:** Scoring logic duplicated, weights hardcoded, hard to test

**Before (phx_home_analyzer.py:113-265):**
```python
# 15 separate scoring functions with identical signatures
def score_school_district(prop: Property) -> Tuple[float, str]:
    if prop.school_rating is None:
        return 5.0, "Unknown - needs lookup"
    return prop.school_rating, f"GreatSchools: {prop.school_rating}/10"

def score_quietness(prop: Property) -> Tuple[float, str]:
    if prop.distance_to_highway_miles is None:
        return 5.0, "Unknown - needs assessment"
    if prop.distance_to_highway_miles > 2:
        return 10.0, "Far from highway"
    # ... more thresholds
```

**After (Strategy Pattern):**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ScoreResult:
    """Scoring result with explanation."""
    score: float  # 0-10 scale
    note: str
    max_weighted: float  # Score × weight

class ScoringStrategy(ABC):
    """Base class for all scoring strategies."""

    @abstractmethod
    def calculate(self, prop: Property) -> ScoreResult:
        """Calculate score for property."""
        pass

    @property
    @abstractmethod
    def weight(self) -> int:
        """Weight multiplier for this score."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Category for grouping (location, systems, interior)."""
        pass

class SchoolDistrictScorer(ScoringStrategy):
    """Scores based on GreatSchools rating."""

    weight = 5
    category = "location"

    def calculate(self, prop: Property) -> ScoreResult:
        if prop.school_rating is None:
            return ScoreResult(5.0, "Unknown - needs lookup", 25.0)
        return ScoreResult(
            prop.school_rating,
            f"GreatSchools: {prop.school_rating}/10",
            prop.school_rating * self.weight
        )

class HighwayDistanceScorer(ScoringStrategy):
    """Scores based on distance from highway noise."""

    weight = 5
    category = "location"
    thresholds = [
        (2.0, 10.0, "Far from highway"),
        (1.0, 7.0, "Moderate distance"),
        (0.5, 5.0, "Near highway"),
        (0.0, 3.0, "Very close to highway"),
    ]

    def calculate(self, prop: Property) -> ScoreResult:
        if prop.distance_to_highway_miles is None:
            return ScoreResult(5.0, "Unknown - needs assessment", 25.0)

        for min_dist, score, note in self.thresholds:
            if prop.distance_to_highway_miles > min_dist:
                return ScoreResult(score, note, score * self.weight)

        return ScoreResult(3.0, "Very close to highway", 15.0)

# Scoring engine using all strategies
class PropertyScorer:
    """Aggregates all scoring strategies."""

    def __init__(self, strategies: List[ScoringStrategy]):
        self.strategies = strategies

    def score(self, prop: Property) -> Dict[str, float]:
        results = {}
        for strategy in self.strategies:
            result = strategy.calculate(prop)
            results[strategy.__class__.__name__] = result

        # Group by category
        categories = {}
        for name, result in results.items():
            cat = next(s.category for s in self.strategies
                       if s.__class__.__name__ == name)
            categories.setdefault(cat, 0)
            categories[cat] += result.max_weighted

        return {
            'details': results,
            'location': categories.get('location', 0),
            'systems': categories.get('systems', 0),
            'interior': categories.get('interior', 0),
            'total': sum(categories.values()),
        }
```

---

### Medium (Next Quarter)

#### 2.6 Data Class Property Using List Default
**Severity:** Potential bug source

**Before (phx_home_analyzer.py:69):**
```python
@dataclass
class Property:
    # ... fields ...
    kill_switch_failures: List[str] = field(default_factory=list)
```
This is correctly using `field(default_factory=list)` - no change needed.

---

#### 2.7 Missing Error Handling
**Impact:** Scripts crash on missing files

**Before (multiple files):**
```python
def load_enrichment_data(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as f:
        return json.load(f)
```

**After:**
```python
class DataLoadError(Exception):
    """Raised when data cannot be loaded."""
    pass

def load_enrichment_data(filepath: Path) -> List[Dict]:
    if not filepath.exists():
        raise DataLoadError(f"Enrichment file not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in {filepath}: {e}")

    if not isinstance(data, list):
        raise DataLoadError(f"Expected list in {filepath}, got {type(data)}")

    return data
```

---

#### 2.8 Global Module-Level Execution
**Impact:** Cannot import without side effects

**Before (value_spotter.py:14-206):**
```python
# All code runs at module level!
csv_path = Path(__file__).parent / "phx_homes_ranked.csv"
df = pd.read_csv(csv_path)  # Executes on import!

# ... 200 lines of processing ...

fig.write_html(str(output_html))  # Side effect on import!
```

**After:**
```python
def main():
    """Generate value spotter visualization."""
    csv_path = Path(__file__).parent / "phx_homes_ranked.csv"
    json_path = Path(__file__).parent / "enrichment_data.json"

    data = ValueSpotterData.load(csv_path, json_path)
    chart = ValueSpotterChart(data)
    chart.save(output_html, output_png)

if __name__ == "__main__":
    main()
```

---

## 3. SOLID Violations

### 3.1 Single Responsibility Principle (SRP)

**Violations Found:**

| File | Class/Function | Responsibilities |
|------|----------------|------------------|
| `phx_home_analyzer.py:main()` | Main pipeline | Loading, filtering, scoring, output, printing |
| `risk_report.py` | Module | Risk assessment, HTML generation, CSV export, checklist generation |
| `renovation_gap.py` | Module | Cost estimation, HTML generation, CSV export, console output |

**Recommendation:** Extract responsibilities:
```
scripts/
├── analyzers/
│   ├── kill_switch_filter.py
│   ├── property_scorer.py
│   └── risk_assessor.py
├── loaders/
│   ├── csv_loader.py
│   └── json_loader.py
├── reporters/
│   ├── html_reporter.py
│   ├── csv_reporter.py
│   └── console_reporter.py
└── main.py  (orchestration only)
```

---

### 3.2 Open/Closed Principle (OCP)

**Violation in phx_home_analyzer.py:83-91:**
```python
KILL_SWITCH_CRITERIA = {
    "hoa": {"check": lambda p: p.hoa_fee == 0 or p.hoa_fee is None, ...},
    "sewer": {"check": lambda p: p.sewer_type == "city" or ..., ...},
    # Adding new criteria requires modifying this dict
}
```

**Recommendation:** Use plugin pattern:
```python
class KillSwitch(ABC):
    @abstractmethod
    def check(self, prop: Property) -> bool: pass

    @abstractmethod
    def description(self) -> str: pass

class NoHoaKillSwitch(KillSwitch):
    def check(self, prop: Property) -> bool:
        return prop.hoa_fee == 0 or prop.hoa_fee is None

    def description(self) -> str:
        return "Must be NO HOA"

# Register kill switches
kill_switches = [
    NoHoaKillSwitch(),
    CitySwerKillSwitch(),
    # New ones can be added without modifying existing code
]
```

---

### 3.3 Dependency Inversion Principle (DIP)

**Violation:** High-level modules depend on low-level details.

**Before:**
```python
def main():
    # Hardcoded file paths - depends on filesystem structure
    input_csv = base_dir / "phx_homes.csv"

    # Hardcoded output format - depends on CSV library
    generate_ranked_csv(properties, str(output_ranked))
```

**After:**
```python
class PropertyRepository(ABC):
    @abstractmethod
    def load_listings(self) -> List[Property]: pass

    @abstractmethod
    def save_rankings(self, properties: List[Property]) -> None: pass

class CsvPropertyRepository(PropertyRepository):
    def __init__(self, input_path: Path, output_path: Path):
        self.input_path = input_path
        self.output_path = output_path

    def load_listings(self) -> List[Property]:
        # CSV-specific loading
        pass

# main.py - depends on abstraction
def run_analysis(repo: PropertyRepository):
    properties = repo.load_listings()
    # ... processing ...
    repo.save_rankings(properties)
```

---

## 4. Refactoring Plan

### Phase 1: Immediate Fixes (High Impact, Low Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Extract shared data loaders | All | 2 hrs | HIGH |
| Centralize configuration | All | 2 hrs | HIGH |
| Fix value_spotter.py global execution | 1 | 0.5 hrs | MEDIUM |
| Add type hints to missing functions | 5 | 1 hr | MEDIUM |

### Phase 2: Structural Improvements (Medium Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Extract HTML templates to files | 3 | 4 hrs | HIGH |
| Implement Repository pattern | All | 4 hrs | HIGH |
| Create RiskLevel enum | 1 | 1 hr | MEDIUM |
| Decompose long functions | 4 | 3 hrs | HIGH |

### Phase 3: Architecture Enhancement (Higher Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Implement Strategy pattern for scoring | 1 | 4 hrs | MEDIUM |
| Create plugin system for kill switches | 1 | 2 hrs | LOW |
| Add comprehensive error handling | All | 3 hrs | MEDIUM |
| Add unit tests (target 80% coverage) | All | 8 hrs | HIGH |

---

## 5. Proposed Architecture

```
phx_home_analysis/
├── config/
│   ├── __init__.py
│   ├── settings.py         # All configuration
│   └── weights.py          # Scoring weights
├── domain/
│   ├── __init__.py
│   ├── entities.py         # Property dataclass
│   ├── enums.py            # RiskLevel, Tier, etc.
│   └── value_objects.py    # Address, Score, etc.
├── repositories/
│   ├── __init__.py
│   ├── base.py             # Abstract repository
│   ├── csv_repository.py   # CSV implementation
│   └── json_repository.py  # JSON implementation
├── services/
│   ├── __init__.py
│   ├── kill_switch.py      # Kill switch filter
│   ├── scorer.py           # Property scoring
│   ├── risk_assessor.py    # Risk assessment
│   └── renovation_estimator.py
├── reporters/
│   ├── __init__.py
│   ├── html_reporter.py    # HTML generation
│   ├── csv_reporter.py     # CSV export
│   └── console_reporter.py # Terminal output
├── visualizations/
│   ├── __init__.py
│   ├── radar_chart.py
│   ├── golden_zone_map.py
│   └── value_spotter.py
├── templates/
│   ├── risk_report.html
│   └── renovation_report.html
├── tests/
│   ├── test_kill_switch.py
│   ├── test_scorer.py
│   └── test_risk_assessor.py
└── main.py                 # CLI entry point
```

---

## 6. Before/After Metrics Comparison

### Current State
- **Total LOC:** ~4,500
- **Duplicate Code:** ~25% (data loading, formatting)
- **Functions >20 lines:** 35
- **Functions >50 lines:** 8
- **Test Coverage:** 0%
- **Cyclomatic Complexity (max):** 14 (deal_sheets.py)
- **Type Hint Coverage:** ~60%

### Target State (After Refactoring)
- **Total LOC:** ~3,500 (reduction through DRY)
- **Duplicate Code:** <5%
- **Functions >20 lines:** <10
- **Functions >50 lines:** 0
- **Test Coverage:** >80%
- **Cyclomatic Complexity (max):** <10
- **Type Hint Coverage:** 100%

---

## 7. Priority Matrix

```
                    HIGH IMPACT
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │  Extract shared    │  Decompose long    │
    │  data loaders      │  functions         │
    │                    │                    │
    │  Centralize        │  Add unit tests    │
    │  configuration     │                    │
LOW ├────────────────────┼────────────────────┤ HIGH
EFFORT                   │                    EFFORT
    │                    │                    │
    │  Fix global        │  Strategy pattern  │
    │  execution         │  for scoring       │
    │                    │                    │
    │  Add type hints    │  Full repository   │
    │                    │  pattern           │
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
                    LOW IMPACT
```

---

## 8. Recommended Next Steps

1. **Immediate (This Week):**
   - Create `config/settings.py` with centralized paths
   - Extract `repositories/property_repository.py` with shared loaders
   - Fix `value_spotter.py` to use `if __name__ == "__main__"`

2. **Short-Term (This Month):**
   - Extract HTML templates to external files
   - Decompose functions >50 lines
   - Add `RiskLevel` enum with encapsulated behavior

3. **Medium-Term (This Quarter):**
   - Implement full Repository pattern
   - Add unit test suite targeting 80% coverage
   - Create Strategy pattern for scoring system

---

## 9. Code Quality Checklist

- [ ] All methods <20 lines
- [ ] All classes <200 lines
- [ ] No method has >3 parameters
- [ ] Cyclomatic complexity <10
- [ ] No nested loops >2 levels
- [ ] All names are descriptive
- [ ] No commented-out code
- [ ] Consistent formatting
- [ ] Type hints on all functions
- [ ] Error handling comprehensive
- [ ] Tests achieve >80% coverage
- [ ] No hardcoded paths
- [ ] No duplicate code blocks >5 lines

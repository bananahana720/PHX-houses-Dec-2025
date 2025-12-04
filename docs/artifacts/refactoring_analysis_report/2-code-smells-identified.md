# 2. Code Smells Identified

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

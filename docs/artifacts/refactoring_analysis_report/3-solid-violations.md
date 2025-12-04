# 3. SOLID Violations

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

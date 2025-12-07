---
name: validate-repository-pattern
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/phx_home_analysis/(services|application)/.*\.py$
  - field: new_text
    operator: regex_match
    pattern: (open\(|json\.load|json\.dump|Path\(.*\.json)(?!.*tmp_path|.*fixture)
action: warn
---

## ⚠️ Direct File Access Detected in Service/Application Layer

**You are accessing JSON files directly instead of using the Repository pattern.**

### ADR-09: Repository Pattern (MANDATORY)
Per `docs/architecture/core-architectural-decisions.md` ADR-09:

> "All data access MUST go through abstract Repository interfaces"

### ❌ Direct Access (Antipattern)
```python
# BAD: Direct file operations in services
with open("data/enrichment_data.json") as f:
    data = json.load(f)

# BAD: Path operations for data files
path = Path("data/work_items.json")
data = json.loads(path.read_text())
```

### ✅ Repository Pattern (Correct)
```python
# GOOD: Use repository interface
from phx_home_analysis.repositories import JsonEnrichmentRepository

class MyService:
    def __init__(self, repo: EnrichmentRepositoryProtocol):
        self.repo = repo

    def process(self, address: str) -> EnrichmentData:
        return self.repo.get_by_address(address)
```

### Available Repositories
| Data Type | Repository | Interface |
|-----------|------------|-----------|
| Enrichment | `JsonEnrichmentRepository` | `EnrichmentRepositoryProtocol` |
| Work Items | `WorkItemsRepository` | `WorkItemsRepositoryProtocol` |
| Lineage | `LineageRepository` | `LineageRepositoryProtocol` |
| Cache | `ResponseCache` | `CacheProtocol` |

### Why Repository Pattern Matters
1. **Testability**: Mock repositories in tests without file I/O
2. **Atomic writes**: `_safe_write()` prevents data corruption
3. **Schema validation**: Pydantic models validate on read/write
4. **Provenance tracking**: Automatic field lineage updates
5. **Abstraction**: Swap JSON for DB without changing services

### Exception: Tests
Direct file access IS allowed in tests using `tmp_path` fixture:
```python
def test_something(tmp_path: Path):
    test_file = tmp_path / "test_data.json"
    test_file.write_text('{"key": "value"}')  # OK in tests
```

**Refactor to use a repository interface before proceeding.**

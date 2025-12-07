---
name: enforce-ddd-layers
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/phx_home_analysis/.*\.py$
  - field: new_text
    operator: regex_match
    pattern: from\s+phx_home_analysis\.(domain|repositories|services|application|infrastructure)
action: warn
---

## ⚠️ Cross-Layer Import Detected

**You are adding an import that may violate DDD layer boundaries.**

### ADR-08: 5-Layer Architecture (MANDATORY)
Per `docs/architecture/core-architectural-decisions.md` ADR-08:

```
┌─────────────────────────────────────┐
│          PRESENTATION              │ → CLI commands, deal sheets
├─────────────────────────────────────┤
│          APPLICATION               │ → Orchestrators, use cases
├─────────────────────────────────────┤
│           SERVICES                 │ → Business logic, scoring
├─────────────────────────────────────┤
│          DOMAIN                    │ → Entities, value objects
├─────────────────────────────────────┤
│        INFRASTRUCTURE              │ → Repositories, external APIs
└─────────────────────────────────────┘
```

### Allowed Import Directions
| Layer | May Import From |
|-------|-----------------|
| `presentation/` | application, services, domain |
| `application/` | services, domain, infrastructure (interfaces) |
| `services/` | domain, infrastructure (interfaces) |
| `domain/` | **NOTHING** (pure entities) |
| `infrastructure/` | domain only |

### ❌ Violations to Avoid
```python
# BAD: Domain importing from services
from phx_home_analysis.services.scoring import calculate_score

# BAD: Services importing from application
from phx_home_analysis.application.orchestrator import PipelineOrchestrator

# BAD: Infrastructure importing from services
from phx_home_analysis.services.kill_switch import check_criteria
```

### ✅ Correct Patterns
```python
# GOOD: Services importing from domain
from phx_home_analysis.domain.entities import EnrichmentData

# GOOD: Application importing from services
from phx_home_analysis.services.scoring import ScoringService

# GOOD: Using Protocol interfaces for DI
from phx_home_analysis.domain.protocols import RepositoryProtocol
```

### Dependency Injection (ADR-09)
Use Protocol-based interfaces to avoid concrete dependencies:
```python
from typing import Protocol

class ScoringProtocol(Protocol):
    def calculate(self, data: EnrichmentData) -> PropertyScore: ...
```

**If this import is intentional, ensure it follows the layer hierarchy.**

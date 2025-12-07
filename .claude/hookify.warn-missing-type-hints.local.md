---
name: warn-missing-type-hints
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: def\s+\w+\([^)]*\)\s*:(?!\s*#)
action: warn
---

## ⚠️ Python Function Missing Type Hints

**A function definition without complete type annotations was detected.**

### ADR-11 Type Annotation Requirements
Per `docs/architecture/core-architectural-decisions.md` ADR-11:

**Required format:**
```python
def function_name(param: Type, other: Type = default) -> ReturnType:
    """Docstring."""
    ...
```

### Protocol-Based DI (ADR-09)
Use `typing.Protocol` for dependency injection interfaces:
```python
from typing import Protocol

class RepositoryProtocol(Protocol):
    def get(self, id: str) -> Entity | None: ...
    def save(self, entity: Entity) -> None: ...
```

### Pydantic V2 Model Patterns
For domain entities:
```python
from pydantic import BaseModel, Field

class PropertyScore(BaseModel):
    """Property scoring result."""
    total_score: int = Field(..., ge=0, le=605)
    tier: Literal["UNICORN", "CONTENDER", "PASS"]
    confidence: float = Field(..., ge=0.0, le=1.0)
```

### Quick Fixes

**Simple parameters:**
```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```

**With defaults:**
```python
def fetch(url: str, timeout: int = 30) -> dict[str, Any]:
    ...
```

**Complex types:**
```python
from typing import Callable
from collections.abc import Iterable

def process(
    items: Iterable[str],
    callback: Callable[[str], None] | None = None,
) -> list[str]:
    ...
```

### Exceptions
- `*args` and `**kwargs` may use `*args: Any`
- Magic methods like `__init__` return `None` (implicit ok)
- Legacy code migrations can add hints incrementally

**Run `mypy src/phx_home_analysis/` to catch type errors.**

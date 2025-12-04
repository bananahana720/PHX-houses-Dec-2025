# Code Style

### Linting and Formatting

```bash
# Run ruff linter
ruff check src/ scripts/ tests/

# Run ruff formatter
ruff format src/ scripts/ tests/

# Run mypy type checker
mypy src/ scripts/
```

### Style Guidelines

1. **Type Hints**
   - Always use type hints for function signatures
   - Use `| None` instead of `Optional[T]`
   - Use `list[T]` instead of `List[T]` (Python 3.11+)

   ```python
   # Good
   def score(self, property: Property) -> float:
       pass

   def load_all(self) -> list[Property]:
       pass

   # Bad
   def score(self, property):  # No type hints
       pass
   ```

2. **Docstrings**
   - Use Google style docstrings
   - Include Args, Returns, Raises sections

   ```python
   def score(self, property: Property) -> float:
       """Calculate property score.

       Args:
           property: Property entity with all data

       Returns:
           Score value 0-10

       Raises:
           ValueError: If property is invalid
       """
       pass
   ```

3. **Naming Conventions**
   - Classes: `PascalCase`
   - Functions/methods: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`
   - Private methods: `_leading_underscore`

4. **Line Length**
   - Maximum 100 characters
   - Break long lines at logical points

5. **Imports**
   - Organized by: stdlib, third-party, local
   - Sorted alphabetically within each group
   - Use absolute imports

   ```python
   # Good
   import json
   from pathlib import Path

   import pandas as pd
   from pydantic import BaseModel

   from src.phx_home_analysis.domain.entities import Property

   # Bad
   from pathlib import Path
   import json  # Wrong order
   from ..domain.entities import Property  # Relative import
   ```

---

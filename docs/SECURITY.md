# Security Guidelines

This document outlines security practices for the PHX Home Analysis project.

## Dependency Management

### Pinned Versions

All dependencies are pinned to specific versions to ensure reproducibility and prevent unexpected breaking changes. This is defined in `pyproject.toml`:

```toml
[project]
dependencies = [
    "pandas==2.3.3",
    "pydantic==2.12.5",
    # ... etc
]

[project.optional-dependencies]
dev = [
    "pytest==9.0.1",
    "pip-audit==2.7.3",  # Security scanner
    # ... etc
]
```

### Lock File

The `uv.lock` file provides reproducible installation across all environments:

```bash
uv pip install -r requirements.txt  # Uses uv.lock
```

## Vulnerability Scanning

### Running Security Checks

Execute the security check script to scan for known vulnerabilities:

```bash
python scripts/security_check.py
```

Or directly with pip-audit:

```bash
pip-audit --strict
```

### Pre-commit Hooks

Install pre-commit hooks to automatically scan for vulnerabilities before commits:

```bash
pre-commit install
pre-commit run --all-files
```

The `.pre-commit-config.yaml` includes:
- **ruff**: Fast Python linting and formatting
- **mypy**: Static type checking
- **pip-audit**: Dependency vulnerability scanner (runs in strict mode)

## Secrets Management

### What NOT to Commit

Never commit the following files:

- `.env` files (environment variables)
- `*.pem`, `*.key` files (private keys)
- `*.cert`, `*.p12`, `*.pfx` (certificates)
- `secrets.json`, `credentials.json` (API credentials)
- Any files with personal/API tokens

### Using Environment Variables

Store sensitive data as environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

api_token = os.getenv("MARICOPA_ASSESSOR_TOKEN")
```

The `.env` file is listed in `.gitignore` and will never be committed.

## Dependency Updates

### Safe Update Process

1. Update pinned version in `pyproject.toml`
2. Run: `uv lock`
3. Run security scan: `python scripts/security_check.py`
4. Run tests: `pytest`
5. Commit with message: `chore: update {package} to {version}`

### Checking for Vulnerabilities

Before updating a dependency:

```bash
# Check for known issues with a specific version
pip-audit --vulnerability-id {CVE-ID}

# See all known issues
pip-audit --desc
```

## Code Security Best Practices

### Input Validation

Always validate user input using Pydantic models:

```python
from pydantic import BaseModel, validator

class PropertyRequest(BaseModel):
    address: str
    price: float

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

### SQL Injection Prevention

Use parameterized queries with SQLAlchemy:

```python
# Good: Parameterized query
stmt = select(Property).where(Property.address == address)

# Bad: String concatenation
stmt = f"SELECT * FROM properties WHERE address = '{address}'"
```

### Type Hints

Use type hints throughout for better static analysis:

```python
def process_properties(
    properties: list[Property],
    threshold: float = 0.8
) -> dict[str, Property]:
    """Process properties with type safety."""
    return {p.address: p for p in properties if p.score > threshold}
```

## Reporting Security Issues

If you discover a security vulnerability, please report it privately:

1. Do NOT create a public GitHub issue
2. Email: [security contact]
3. Include:
   - Description of vulnerability
   - Affected versions
   - Proof of concept (if applicable)
   - Proposed fix (if available)

## CI/CD Security

### GitHub Actions

- Secrets are stored in GitHub Secrets, not in code
- Workflows use pinned action versions
- Dependabot alerts are enabled

### Artifact Security

- Temporary artifacts are cleaned up after use
- Production secrets are never logged
- Build artifacts are signed when deployed

## Monitoring and Alerts

### Dependabot

GitHub Dependabot monitors for:
- Dependency updates
- Security vulnerabilities
- Version deprecation

### Regular Audits

Run security audits:
- After major dependency updates
- Monthly (or as part of CI/CD)
- Before production deployments

## Additional Resources

- [OWASP Python Security](https://owasp.org/www-community/attacks/Python_Code_Injection)
- [Bandit - Python Security Linter](https://bandit.readthedocs.io/)
- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [Pydantic Security](https://docs.pydantic.dev/latest/concepts/validators/)

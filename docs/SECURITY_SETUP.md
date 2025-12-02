# Security Setup for PHX Home Analysis

This document provides instructions for setting up and maintaining security for the project.

## What Has Been Configured

The following security improvements have been implemented:

### 1. Pinned Dependencies
All dependencies in `pyproject.toml` have been pinned to specific versions using the `==` operator:

**Production Dependencies (13 packages):**
- `pandas==2.3.3`
- `pydantic==2.12.5`
- `jinja2==3.1.6`
- `plotly==6.5.0`
- `folium==0.20.0`
- `Pillow==12.0.0`
- `imagehash==4.3.2`
- `httpx==0.28.1`
- `playwright==1.56.0`
- `beautifulsoup4==4.14.3`
- `python-dotenv==1.2.1`
- `nodriver==0.48.1`
- `curl-cffi==0.13.0`

**Development Dependencies (7 packages):**
- `pytest==9.0.1`
- `pytest-cov==7.0.0`
- `pytest-asyncio==1.3.0`
- `ruff==0.14.7`
- `mypy==1.19.0`
- `respx==0.22.0`
- `pip-audit==2.7.3` (NEW: Security vulnerability scanner)

### 2. Security Scripts

#### `scripts/security_check.py`
Runs pip-audit in strict mode to scan for known vulnerabilities.

**Usage:**
```bash
python scripts/security_check.py
```

#### `scripts/verify_security_setup.py`
Validates that all security configurations are properly set up.

**Usage:**
```bash
python scripts/verify_security_setup.py
```

**Output:**
```
[✓] All security checks passed!
✓ Pinned Dependencies: PASS
✓ Dev Dependencies (pip-audit): PASS
✓ Security Check Script: PASS
✓ .gitignore Patterns: PASS
✓ .pre-commit-config.yaml: PASS
✓ SECURITY.md Documentation: PASS
✓ GitHub Actions Workflow: PASS
```

### 3. Updated Files

#### `.gitignore`
Added security patterns to prevent committing sensitive files:
- `*.pem`, `*.key` - Private keys
- `*.cert`, `*.p12`, `*.pfx` - Certificates
- `secrets.json`, `credentials.json` - API credentials
- `.pip-audit-cache/` - Security cache

#### `.pre-commit-config.yaml` (NEW)
Configured pre-commit hooks for:
- **ruff**: Fast Python linting (v0.14.7)
- **mypy**: Static type checking (v1.19.0)
- **pip-audit**: Dependency vulnerability scanner (v2.7.3)

#### `.github/workflows/security.yml` (NEW)
GitHub Actions workflow for automated security scanning:
- Runs on: `push`, `pull_request`, and daily schedule (2 AM UTC)
- Executes pip-audit, ruff, and mypy
- Includes dependency review for PRs

#### `docs/SECURITY.md` (NEW)
Comprehensive security documentation including:
- Dependency management guidelines
- Vulnerability scanning procedures
- Secrets management best practices
- Code security patterns
- Reporting procedures
- CI/CD security

## Initial Setup Instructions

### 1. Install Development Dependencies

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 2. Install Pre-commit Hooks

```bash
pre-commit install
```

This will run security checks before each commit.

### 3. Run Initial Security Verification

```bash
# Verify all configurations are correct
python scripts/verify_security_setup.py

# Run security scan
python scripts/security_check.py
```

### 4. Update Dependencies Safely

When updating dependencies:

```bash
# 1. Update version in pyproject.toml
# 2. Update lock file
uv lock

# 3. Run security scan
python scripts/security_check.py

# 4. Run tests
pytest

# 5. Commit changes
git add pyproject.toml uv.lock
git commit -m "chore: update pandas to 2.4.0"
```

## Ongoing Security Maintenance

### Daily Development

The pre-commit hooks will automatically check for:
- Code quality issues (ruff)
- Type errors (mypy)
- Dependency vulnerabilities (pip-audit)

Just commit normally - security checks run automatically.

### Weekly

Run full security audit:
```bash
python scripts/security_check.py
```

### Monthly

Check for available security updates:
```bash
# List available updates
uv pip list --outdated

# Check for vulnerabilities in specific packages
pip-audit --desc
```

### Before Production Deployment

```bash
# Run complete verification
python scripts/verify_security_setup.py

# Run security scan with detailed output
pip-audit

# Run all tests
pytest --cov

# Run type checking
mypy src/

# Run linting
ruff check .
```

## GitHub Actions Workflow

The `.github/workflows/security.yml` workflow automatically:

1. **On Every Push/PR:**
   - Installs dependencies
   - Runs pip-audit (strict mode)
   - Runs ruff linting
   - Runs mypy type checking

2. **Daily at 2 AM UTC:**
   - Full security scan
   - Dependency updates check

3. **On PRs:**
   - Dependency review (fails on moderate+ severity)

Workflow status is visible in:
- Pull request checks
- GitHub Actions tab
- Commit status

## Troubleshooting

### Issue: pip-audit not found

**Solution:**
```bash
uv pip install pip-audit==2.7.3
```

### Issue: Pre-commit hooks failing

**View the issue:**
```bash
pre-commit run --all-files --verbose
```

**Fix and retry:**
```bash
# Auto-fix with ruff
ruff check . --fix

# Then re-run
pre-commit run --all-files
```

### Issue: Version conflicts when updating

**Solution:**
```bash
# Clear and rebuild lock file
rm uv.lock
uv lock

# Or sync with existing dependencies
uv pip sync --upgrade
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Pinned dependencies |
| `uv.lock` | Lock file for reproducible installs |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |
| `.gitignore` | Files to never commit |
| `.github/workflows/security.yml` | GitHub Actions workflow |
| `scripts/security_check.py` | Manual security scan |
| `scripts/verify_security_setup.py` | Verify setup |
| `docs/SECURITY.md` | Security documentation |

## References

- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [Pre-commit Framework](https://pre-commit.com/)
- [PEP 508 - Dependency specification](https://www.python.org/dev/peps/pep-0508/)
- [OWASP Python Security](https://owasp.org/)

## Questions or Issues?

Refer to `docs/SECURITY.md` for detailed guidelines, or check:
- `.pre-commit-config.yaml` for tool configurations
- `.github/workflows/security.yml` for CI/CD setup
- `scripts/verify_security_setup.py` for validation checks

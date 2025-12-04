# Configuration Files

### Project Configuration
- `pyproject.toml` - Python project metadata, dependencies, tool configs
- `uv.lock` - Dependency lock file (uv package manager)
- `.python-version` - Python version pinning (3.11+)

### Environment Variables
- `.env` - API keys, proxy settings (gitignored)
- `.env.example` - Template for environment variables

### Git Configuration
- `.gitignore` - Ignored files and directories
- `.pre-commit-config.yaml` - Pre-commit hook configuration

### Tool Configuration (in pyproject.toml)
- `[tool.pytest.ini_options]` - Pytest settings
- `[tool.ruff]` - Ruff linter/formatter settings
- `[tool.mypy]` - Mypy type checker settings

---

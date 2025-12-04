# Recommended Actions

### Critical (Must Fix Before Next Test Run)

1. **Rebuild Virtual Environment**
   ```bash
   # Remove corrupted venv safely
   cd C:\Users\Andrew\.vscode\PHX-houses-Dec-2025
   mv .venv VENV_BACKUP_20251203

   # Create fresh venv with uv
   uv venv --python 3.12
   uv sync --all-extras
   ```

2. **Verify Package Installation**
   ```bash
   python -c "import pydantic; import pytest; print('OK')"
   ```

3. **Run Full Test Suite**
   ```bash
   pytest tests/ -v --tb=short
   ```

### High Priority

1. **Run Test Coverage Report**
   ```bash
   pytest tests/ --cov=src --cov-report=html
   ```

2. **Validate New Tests Execute**
   ```bash
   pytest tests/archived/ -v  # New test files
   pytest tests/unit/test_scorer.py -v
   pytest tests/integration/test_kill_switch_chain.py -v
   ```

3. **Check for Import Errors**
   ```bash
   pytest tests/ --collect-only  # Lists all discoverable tests
   ```

### Medium Priority

1. **Update Test Documentation**
   - Add new test files to `tests/CLAUDE.md`
   - Document new test classes and methods
   - Update test count (now 1063+)

2. **Benchmark Previous Baseline**
   - Compare new test execution time
   - Identify any performance regressions
   - Document baseline for future comparisons

3. **Review Archived Tests**
   - Determine if any should be integrated back
   - Clean up verification-only scripts
   - Consolidate with active test suite

---

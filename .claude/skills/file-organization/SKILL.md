# File Organization Skill

Enforces proper file placement standards for project organization.

## Project Structure Rules

### Root Directory (KEEP CLEAN)

**Allowed in root:**
- `README.md` - Project overview
- `CLAUDE.md` - AI assistant instructions
- `TRASH-FILES.md` - Trash file registry
- `pyproject.toml` - Python project config
- `uv.lock` - Dependency lock
- `.env` - Environment variables
- `.gitignore` - Git ignore rules
- `.mcp.json` - MCP server config
- `.pre-commit-config.yaml` - Pre-commit hooks

**NOT allowed in root:**
- Python scripts (`*.py`) → `scripts/` or `tests/`
- Test files (`test_*.py`) → `tests/`
- Implementation summaries (`*_SUMMARY.md`) → `docs/artifacts/`
- Temporary files (`tmp_*`, `*.log`) → delete or `TRASH/`
- Data files (`*.json`, `*.csv`) → `data/`

### Directory Structure

```
PHX-houses-Dec-2025/
├── .claude/              # AI assistant configuration
│   ├── agents/           # Agent definitions
│   ├── commands/         # Slash commands
│   ├── skills/           # Skill modules (like this one)
│   └── settings.json     # Project permissions
├── src/                  # Source code (package)
│   └── phx_home_analysis/
├── scripts/              # CLI scripts and utilities
│   ├── lib/              # Shared script libraries
│   ├── deal_sheets/      # Deal sheet package
│   └── benchmarks/       # Performance benchmarks
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── services/         # Service-specific tests
│   ├── benchmarks/       # Performance tests
│   └── fixtures/         # Test fixtures
├── data/                 # Data files
│   ├── property_images/  # Downloaded images
│   ├── metadata/         # Pipeline state files
│   └── *.csv, *.json     # Core data files
├── docs/                 # Documentation
│   ├── artifacts/        # Generated docs
│   │   └── implementation-notes/  # Work session artifacts
│   ├── specs/            # Specifications
│   └── architecture/     # Architecture docs
├── config/               # Configuration files
├── reports/              # Generated reports
│   └── deal_sheets/      # Property deal sheets
└── TRASH/                # Deleted files (recoverable)
    ├── corrupted/        # Corrupted/artifact files
    ├── temp/             # Temporary files
    ├── duplicates/       # Duplicate files
    └── test_artifacts/   # One-off test files
```

## File Placement Rules

### New Python Scripts
```
Location Decision:
- Is it a test? → tests/
- Is it a benchmark? → tests/benchmarks/ or scripts/benchmarks/
- Is it a CLI tool? → scripts/
- Is it package code? → src/phx_home_analysis/
```

### New Documentation
```
Location Decision:
- Is it a work session artifact? → docs/artifacts/implementation-notes/
- Is it a reference guide? → docs/
- Is it API documentation? → docs/specs/
- Is it architecture docs? → docs/architecture/
```

### New Data Files
```
Location Decision:
- Is it property data? → data/
- Is it metadata? → data/metadata/ or data/property_images/metadata/
- Is it a template? → data/templates/
- Is it geocoding? → data/geocoding/
```

## Anti-Patterns to Avoid

1. **Root file sprawl**: Never create files in root except allowed ones
2. **Orphan test files**: All test_*.py must be in tests/
3. **Scattered summaries**: All *_SUMMARY.md go to docs/artifacts/
4. **Duplicate data**: Don't copy data files between directories
5. **Temp file commits**: Never commit tmp_*, *.log, or extraction_*.txt

## Cleanup Protocol

When encountering misplaced files:

1. **Identify file type** (script, test, doc, data, temp)
2. **Determine correct location** using rules above
3. **Move file** to proper directory
4. **Update TRASH-FILES.md** if moving to TRASH
5. **Verify imports** if file is imported elsewhere

## Usage

Load this skill when:
- Creating new files
- Generating documentation
- Adding scripts or tools
- Creating artifacts or reports
- Any file creation task

This skill ensures consistent project structure and prevents file sprawl.

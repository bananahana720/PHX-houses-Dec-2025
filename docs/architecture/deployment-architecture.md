# Deployment Architecture

### Local Development Environment

```bash
# Requirements
- Python 3.11+ (target 3.12)
- Chrome/Chromium (for nodriver)
- Git

# Setup
git clone <repo>
cd PHX-houses-Dec-2025
uv sync

# Environment
cp .env.example .env
# Edit .env with your API keys

# Verify
python -c "from src.phx_home_analysis import __version__; print(__version__)"
```

### Execution Model

```bash
# Full pipeline (all properties)
/analyze-property --all

# Single property
/analyze-property "4732 W Davis Rd, Glendale, AZ 85306"

# Test mode (first 5 properties)
/analyze-property --test

# Resume after failure
/analyze-property --all --resume

# Manual script execution
python scripts/phx_home_analyzer.py
python scripts/extract_county_data.py --all
python scripts/extract_images.py --all
python -m scripts.deal_sheets
```

### Directory Structure

```
PHX-houses-Dec-2025/
├── .claude/                  # Claude Code configuration
│   ├── agents/               # Agent definitions
│   ├── commands/             # Slash commands
│   ├── skills/               # Domain expertise modules
│   └── hooks/                # Pre-commit hooks
├── data/                     # Data files
│   ├── phx_homes.csv         # Source listings
│   ├── enrichment_data.json  # Enriched data (LIST!)
│   ├── work_items.json       # Pipeline state
│   └── property_images/      # Downloaded images
├── docs/                     # Documentation
│   ├── architecture.md       # This document
│   ├── prd.md                # Product requirements
│   └── ux-design-specification.md
├── scripts/                  # Executable scripts
│   ├── phx_home_analyzer.py  # Main scoring script
│   ├── extract_county_data.py
│   ├── extract_images.py
│   └── deal_sheets/          # Report generation
├── src/phx_home_analysis/    # Core library
│   ├── config/               # Configuration
│   ├── domain/               # Entities, value objects, enums
│   ├── repositories/         # Data persistence
│   ├── services/             # Business logic
│   ├── pipeline/             # Orchestration
│   ├── reporters/            # Output formatters
│   └── validation/           # Data validation
└── tests/                    # Test suite
    ├── unit/
    ├── integration/
    └── fixtures/
```

---
